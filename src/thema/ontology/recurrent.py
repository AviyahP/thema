"""``recurrent_dag`` -- groupings that survive resampling become nodes, ordered by containment.

Ward on one sample gives a tree, and a tree has to put every pathway in exactly one place. That is
an artefact of the method, not a finding about biology: a pathway that genuinely sits between two
themes is assigned to one of them and the ambiguity disappears from the output.

This method asks a different question. Cluster 100 random 80% subsets. A grouping counts as real
only if the same set of pathways comes back together in at least ``m`` of the runs that could have
seen it. Groupings that recur are the nodes; where the runs kept disagreeing about which of two
themes a pathway belongs to, it is in both. Ordering the nodes by containment gives a DAG with
several roots and no fixed levels, rather than a tree with one.

Implemented from ``docs/spec/thema-master-spec.md`` §10, with these decisions applied:

- **Addendum B1.** If ``3 x null_max >= 0.5`` the build FAILS and reports ``null_max``. It is not
  clamped: that outcome means resampling produces recurrent structure by chance, so the method is
  not discriminating on this data. A finding, not a knob.
- **Addendum B4.** v0.2 is the 1,854-pathway build; ``numba`` stays deferred. Pure numpy, and the
  build reports where its time went so any optimisation argues from measurement.
- **§10.6's null needs re-normalising.** Permuting each embedding dimension independently destroys
  row unit-length, and ``cluster.distances`` refuses non-unit input -- correctly, since Ward on
  non-Euclidean input is silently meaningless. The columns are permuted and the rows re-normalised;
  the manifest records that this was done.

The expensive stages -- runs, matching, support -- do not depend on ``m``. :meth:`RecurrentDag.pool`
computes them once so several thresholds can be assembled from one pass.
"""

import hashlib
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.cluster.hierarchy import linkage

from thema.cluster import distances
from thema.ontology import bitset as bits
from thema.ontology.base import (
    Node,
    Ontology,
    check_distinct_members,
    check_invariants,
)

#: Defaults from spec §10.1. Every one is recorded in the manifest, set or not.
DEFAULTS: dict[str, object] = {
    "runs": 100,
    "subsample": 0.80,
    "min_size": 5,
    "min_shared": 3,
    "tol": 0.0,
    # Twin merge (addendum-2026-09-21 step 8). A pair is nested twins when one contains the other
    # and they differ by at most max(TWIN_FLOOR, TWIN_FRACTION x |smaller|).
    # A member must appear in a MAJORITY of the matched copies. At 0.25 a pathway seen in a
    # quarter of them was kept, which let weakly-attached material accumulate on a theme.
    "inclusion_threshold": 0.5,
    "embedder_split": False,
    # Which linkage each resampled run uses. Ward is the default and the one every measurement so
    # far was taken under; exposed so a different criterion can be run through the identical
    # pipeline rather than compared across two different ones.
    "linkage": "ward",
}

#: `m` must be below 0.5. Two groupings each found in a majority of runs co-occur in some run, where
#: they are clusters of one Ward tree and therefore nested or disjoint -- majority rule can only
#: produce a tree. Overlap lives below 0.5.
MAX_M = 0.5

#: Twin merge tolerance (step 8): a nested pair are twins if they differ by at most
#: ``max(TWIN_FLOOR, TWIN_FRACTION x |smaller|)`` members.
TWIN_FLOOR = 2
TWIN_FRACTION = 0.10

#: The floor under the null-derived threshold (§10.6).
MIN_M = 0.20

#: Groupings judged per vectorised eligibility chunk. Keeps the intermediate at a few hundred MB.
CHUNK = 4096


@dataclass
class Timing:
    """Wall time per stage, so optimisation arguments start from measurement.

    Attributes:
        stages: Stage name to seconds, in the order they ran.
    """

    stages: dict[str, float] = field(default_factory=dict)

    def record(self, name: str, seconds: float) -> None:
        """Add a stage's duration, summing repeats."""
        self.stages[name] = self.stages.get(name, 0.0) + seconds

    def render(self) -> list[str]:
        """One line per stage, longest first, with its share of the total."""
        total = sum(self.stages.values()) or 1.0
        rows = sorted(self.stages.items(), key=lambda kv: -kv[1])
        return [f"  {name:<22} {sec:8.1f}s  {sec / total:5.1%}" for name, sec in rows] + [
            f"  {'TOTAL':<22} {total:8.1f}s"
        ]


@dataclass(frozen=True, slots=True)
class Run:
    """One resampled Ward run.

    Attributes:
        present: Bitset of the pathways this run drew.
        clusters: ``(c, words)`` bitsets -- every dendrogram node with >= ``min_size`` members.
        parent: For each recorded cluster, the index of the smallest recorded cluster strictly
            containing it, or -1. Ancestor walks climb this.
        leaf_cluster: For each pathway index, the smallest recorded cluster containing it, or -1
            for a pathway this run did not draw or which no recorded cluster holds.
    """

    present: np.ndarray
    clusters: np.ndarray
    parent: np.ndarray
    leaf_cluster: np.ndarray


@dataclass(frozen=True, slots=True)
class Prepared:
    """Everything that does not depend on ``tol``: the runs, the pool, and eligibility.

    Splitting this out is what makes a tol sweep affordable. ``tol`` enters only the found/not-found
    decision, so the 100 Ward runs, the dedup and the per-(grouping, run) eligibility popcount are
    computed once and reused across every tol.

    Attributes:
        records: The resampled runs.
        present: ``(runs, words)`` present bitsets.
        groupings: ``(g, words)`` distinct grouping bitsets.
        origins: Per grouping, the runs it came from.
        eligible_mask: ``(g, runs)`` -- whether a run had enough of a grouping to judge it.
        eligible_count: Per grouping, how many runs were eligible.
        timing: Wall time per stage.
    """

    records: list[Run]
    present: np.ndarray
    groupings: np.ndarray
    origins: list[set[int]]
    eligible_mask: np.ndarray
    eligible_count: np.ndarray
    timing: Timing


@dataclass(frozen=True, slots=True)
class Pool:
    """Every candidate grouping, deduplicated, with its support. Independent of ``m``.

    Attributes:
        groupings: ``(g, words)`` bitsets, one row per distinct grouping.
        support: Support in ``[0, 1]`` per grouping.
        eligible: How many runs were eligible to judge each grouping.
        copies: Per grouping, ``{run index: the cluster bitset that run matched it to}``.
        origins: Per grouping, the runs it came from.
        timing: Wall time per stage.
    """

    groupings: np.ndarray
    support: np.ndarray
    eligible: np.ndarray
    copies: list[dict[int, np.ndarray]]
    origins: list[set[int]]
    timing: Timing


def _seeds(seed: int, runs: int) -> list[int]:
    """Derive one reproducible seed per run from the master seed.

    Args:
        seed: The master seed.
        runs: How many runs.

    Returns:
        A seed per run. Derived by hashing rather than by ``seed + r`` so that two master seeds one
        apart do not produce runs that are mostly the same draws.
    """
    return [
        int.from_bytes(hashlib.sha256(f"{seed}:{r}".encode()).digest()[:8], "big") % (2**32)
        for r in range(runs)
    ]


def _one_run(
    x: np.ndarray,
    n: int,
    subsample: float,
    min_size: int,
    seed: int,
    method: str = "ward",
) -> Run:
    """Draw a subset, cluster it, and record every grouping of at least ``min_size``.

    Args:
        x: The full ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        subsample: Fraction of pathways to draw.
        min_size: Smallest grouping worth recording.
        seed: This run's seed.
        method: Linkage criterion. Ward is only legitimate on Euclidean distances, which
            :func:`thema.cluster.distances` enforces by refusing non-unit vectors; average and
            complete carry no such requirement.

    Returns:
        The run's record.
    """
    rng = np.random.default_rng(seed)
    take = int(np.ceil(subsample * n))
    subset = np.sort(rng.choice(n, size=take, replace=False))
    words = bits.words_for(n)

    present = bits.pack(subset.tolist(), n)
    z = linkage(distances(x[subset]), method=method)

    # Bitsets for every dendrogram node: leaves 0..take-1, internal take..2*take-2. Merges arrive
    # in increasing order, so a node's children are always built before it.
    total = 2 * take - 1
    node_bits = np.zeros((total, words), dtype=np.uint64)
    for local, global_index in enumerate(subset):
        node_bits[local][global_index // bits.WORD] = np.uint64(1) << np.uint64(
            int(global_index) % bits.WORD
        )
    tree_parent = np.full(total, -1, dtype=np.int64)
    for i in range(take - 1):
        left, right = int(z[i, 0]), int(z[i, 1])
        node_bits[take + i] = node_bits[left] | node_bits[right]
        tree_parent[left] = tree_parent[right] = take + i

    sizes = bits.count_rows(node_bits)
    # Every dendrogram node between min_size and HALF the run's draw. Nodes near the top of a tree
    # recur because they contain almost everything, not because they share meaning: a node over
    # half the draw is defined by its complement, and its enrichment test is uninformative. This
    # replaces the earlier full-draw exclusion, which it includes.
    recorded = np.flatnonzero((sizes >= min_size) & (sizes <= take // 2))
    where = {int(node): index for index, node in enumerate(recorded)}

    # Climb the dendrogram to the nearest recorded ancestor, for recorded clusters and for leaves.
    def nearest_recorded(start: int) -> int:
        node = start
        while node != -1 and node not in where:
            node = int(tree_parent[node])
        return where.get(node, -1) if node != -1 else -1

    parent = np.array(
        [nearest_recorded(int(tree_parent[node])) for node in recorded], dtype=np.int64
    )
    leaf_cluster = np.full(n, -1, dtype=np.int64)
    for local, global_index in enumerate(subset):
        leaf_cluster[global_index] = nearest_recorded(local)

    return Run(
        present=present,
        clusters=node_bits[recorded].copy(),
        parent=parent,
        leaf_cluster=leaf_cluster,
    )


def _dedup(runs: list[Run], n: int) -> tuple[np.ndarray, list[set[int]]]:
    """Collapse identical groupings across runs into one candidate each (§10.3).

    A grouping that is stable appears in many runs with exactly the same members, once every member
    was present in both. Deduplicating first is the single biggest saving in the whole method: it
    removes most of the pool before anything is judged against 99 runs.

    Args:
        runs: The resampled runs.
        n: Universe size.

    Returns:
        The distinct grouping bitsets, and the set of runs each came from.
    """
    seen: dict[bytes, int] = {}
    rows: list[np.ndarray] = []
    origins: list[set[int]] = []
    for index, run in enumerate(runs):
        for cluster in run.clusters:
            identity = bits.key(cluster)
            at = seen.get(identity)
            if at is None:
                seen[identity] = len(rows)
                rows.append(cluster)
                origins.append({index})
            else:
                origins[at].add(index)
    stacked = np.vstack(rows) if rows else np.zeros((0, bits.words_for(n)), dtype=np.uint64)
    return stacked, origins


def _best_overlap(run: Run, target: np.ndarray) -> int:
    """Find the recorded cluster of ``run`` overlapping ``target`` most.

    Walks the ancestor chains of every member of ``target`` and takes the cluster covering the most
    of it, breaking ties toward the smaller cluster since that carries fewer extras.

    This replaces the smallest-CONTAINING cluster the one-sided rule looked for. That rule returned
    "not found" whenever no cluster held every shared member, so its extras test never ran on any
    grouping whose members scatter even slightly -- on the immune groupings, 99 runs out of 100.

    Args:
        run: The run to search.
        target: The grouping's members that this run drew.

    Returns:
        The index into ``run.clusters``, or -1 when no recorded cluster holds any of them.
    """
    seen: set[int] = set()
    for p in bits.unpack(target):
        at = int(run.leaf_cluster[p])
        while at != -1 and at not in seen:
            seen.add(at)
            at = int(run.parent[at])
    best, best_cover, best_size = -1, -1, 0
    for candidate in seen:
        cover = bits.count(run.clusters[candidate] & target)
        size = bits.count(run.clusters[candidate])
        if cover > best_cover or (cover == best_cover and size < best_size):
            best, best_cover, best_size = candidate, cover, size
    return best


def found_in(
    run: Run,
    grouping: np.ndarray,
    origin_present: np.ndarray,
    min_shared: int,
    tol: float,
    theta: float | None = None,
) -> tuple[bool, np.ndarray | None]:
    """Decide whether one run found a grouping, and which of its clusters is the copy (§10.4).

    Extracted so the rule can be tested directly against hand-built runs rather than only through a
    whole build.

    Args:
        run: The run being asked.
        grouping: The grouping's member bitset.
        origin_present: The ``present`` bitset of the grouping's origin run. Members the origin run
            never had do not count either way.
        min_shared: Below this many shared members the run is not eligible to judge at all.
        tol: Extra shared members allowed, as a fraction of the shared size. ``0`` is
            exact-on-shared. Ignored when ``theta`` is given.
        theta: Jaccard threshold. When set, the rule becomes ``|A n C| / |A u C| >= theta``
            applied identically at every size, replacing the proportional tolerance. The
            tolerance rule computes ``tol * shared`` as a float and compares it against integer
            counts, so its effective slack is ``floor(0.15 * size)`` -- ZERO for sizes 3 to 6 and
            3 members at size 20. "Recurs" therefore means exact repetition at small sizes and
            15% drift at large ones, which is a rounding artefact rather than a decision.
            Jaccard is continuous and size-uniform. See docs/spec/amendment-2026-09-24.md.

    Returns:
        Whether it was found, and the matched cluster bitset when it was. ``(False, None)`` covers
        both "not eligible" and "eligible but not found"; :func:`build_pool` checks eligibility
        separately because it vectorises that step.
    """
    g_s = grouping & run.present
    shared_count = bits.count(g_s)
    if shared_count < min_shared:
        return False, None
    at = _best_overlap(run, g_s)
    if at == -1:
        return False, None
    cluster = run.clusters[at]
    allowed = tol * shared_count
    # TWO-SIDED. Missing: members this run drew but placed outside the cluster. Extras: cluster
    # members the origin run drew that the grouping lacks. The one-sided rule tested only the
    # second, and only after demanding the first be zero -- so a grouping whose members scatter was
    # rejected before its extras were ever counted.
    missing = shared_count - bits.count(cluster & g_s)
    extras = bits.count(cluster & origin_present & ~grouping)
    if theta is not None:
        # |A n C| = shared - missing;  |A u C| = shared + extras, both restricted to what the
        # origin run had, exactly as the tolerance rule restricts them.
        union = shared_count + extras
        return (union > 0 and (shared_count - missing) / union >= theta), cluster
    return (missing <= allowed and extras <= allowed), cluster


def _first_set_bit(block: np.ndarray) -> int:
    """The lowest index set in a bitset, or -1 if it is empty.

    Args:
        block: A ``uint64`` bitset.

    Returns:
        The index, or -1.
    """
    nonzero = np.flatnonzero(block)
    if not len(nonzero):
        return -1
    word_index = int(nonzero[0])
    word = int(block[word_index])
    return word_index * bits.WORD + (word & -word).bit_length() - 1


def prepare(
    x: np.ndarray, n: int, settings: dict[str, object], seed: int, timing: Timing | None = None
) -> Prepared:
    """Do everything that does not depend on ``tol`` (§10.2, §10.3, and eligibility from §10.5).

    Args:
        x: The ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        settings: Parameters, already defaulted.
        seed: Master seed.
        timing: Collector to record stage durations into; one is made if absent.

    Returns:
        The runs, the deduplicated pool, and the eligibility matrix.
    """
    clock = timing if timing is not None else Timing()
    runs = int(settings["runs"])  # type: ignore[arg-type]
    min_size = int(settings["min_size"])  # type: ignore[arg-type]
    min_shared = int(settings["min_shared"])  # type: ignore[arg-type]

    start = time.perf_counter()
    method = str(settings.get("linkage", "ward"))
    records = [
        _one_run(x, n, float(settings["subsample"]), min_size, s, method)  # type: ignore[arg-type]
        for s in _seeds(seed, runs)
    ]
    clock.record("runs (ward x N)", time.perf_counter() - start)

    start = time.perf_counter()
    groupings, origins = _dedup(records, n)
    clock.record("dedup", time.perf_counter() - start)

    present = np.vstack([r.present for r in records])
    total = len(groupings)
    eligible_count = np.zeros(total, dtype=np.int64)

    # Eligibility is a pure popcount and vectorises over every (grouping, run) pair at once; the
    # ancestor walk does not. Filtering first is what keeps the walk off most of the pairs.
    start = time.perf_counter()
    eligibility: list[np.ndarray] = []
    for begin in range(0, total, CHUNK):
        block = groupings[begin : begin + CHUNK]
        overlap = np.bitwise_count(block[:, None, :] & present[None, :, :]).sum(axis=2)
        eligibility.append(overlap >= min_shared)
        eligible_count[begin : begin + CHUNK] = (overlap >= min_shared).sum(axis=1)
    eligible_mask = np.vstack(eligibility) if eligibility else np.zeros((0, runs), dtype=bool)
    clock.record("eligibility", time.perf_counter() - start)
    return Prepared(records, present, groupings, origins, eligible_mask, eligible_count, clock)


def score(ready: Prepared, settings: dict[str, object]) -> Pool:
    """Decide found/not-found for every eligible pair and turn it into support (§10.4-§10.5).

    The only tol-dependent stage. Everything it needs was computed by :func:`prepare`.

    Args:
        ready: The tol-independent work.
        settings: Parameters, already defaulted; ``tol``, ``min_shared`` and optional ``theta``
            are read here. ``theta`` switches matching to Jaccard and supersedes ``tol``.

    Returns:
        The scored pool.
    """
    clock = ready.timing
    records, groupings, origins = ready.records, ready.groupings, ready.origins
    eligible_mask, eligible_count = ready.eligible_mask, ready.eligible_count
    runs = len(records)
    min_shared = int(settings["min_shared"])  # type: ignore[arg-type]
    tol = float(settings["tol"])  # type: ignore[arg-type]
    theta_raw = settings.get("theta")
    theta = None if theta_raw is None else float(theta_raw)  # type: ignore[arg-type]
    total = len(groupings)
    found_count = np.zeros(total, dtype=np.int64)
    copies: list[dict[int, np.ndarray]] = [{} for _ in range(total)]

    start = time.perf_counter()
    for g in range(total):
        target_all = groupings[g]
        for s in np.flatnonzero(eligible_mask[g]):
            run = records[int(s)]
            if int(s) in origins[g]:
                # Found in its own origin run by definition (§10.4).
                found_count[g] += 1
                copies[g][int(s)] = target_all
                continue
            hit, copy = found_in(
                run, target_all, _origin_present(records, origins[g]), min_shared, tol, theta
            )
            if hit and copy is not None:
                found_count[g] += 1
                copies[g][int(s)] = copy
    clock.record("matching (ancestor walk)", time.perf_counter() - start)

    with np.errstate(invalid="ignore", divide="ignore"):
        support = np.where(eligible_count > 0, found_count / np.maximum(eligible_count, 1), 0.0)
    # A grouping too small for most runs to judge is not evaluable, and is dropped rather than
    # scored on a handful of runs (§10.5).
    support = np.where(eligible_count >= runs / 2, support, np.nan)
    return Pool(groupings, support, eligible_count, copies, origins, clock)


def build_pool(
    x: np.ndarray, n: int, settings: dict[str, object], seed: int, timing: Timing | None = None
) -> Pool:
    """Prepare and score in one call, for a single ``tol``.

    Args:
        x: The ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        settings: Parameters, already defaulted.
        seed: Master seed.
        timing: Collector for stage durations.

    Returns:
        The scored pool.
    """
    return score(prepare(x, n, settings, seed, timing), settings)


def _origin_present(records: list[Run], origins: set[int]) -> np.ndarray:
    """The ``present`` bitset of a grouping's origin run.

    ``shared`` in §10.4 is ``present[r] & present[s]`` -- members run *r* never had do not count
    either way. A deduplicated grouping has several origin runs; any of them saw every one of its
    members, so the first is representative and the choice is made deterministic by sorting.

    Args:
        records: The runs.
        origins: The runs this grouping came from.

    Returns:
        The origin run's present bitset.
    """
    return records[min(origins)].present


def null_table(
    real: np.ndarray, null: np.ndarray, thresholds: Sequence[float]
) -> list[tuple[float, int, int, float]]:
    """Count real and scrambled groupings passing each threshold (addendum-2026-09-21 step 7).

    Replaces ``3 x max(null support)``. Over tens of thousands of groupings a maximum is an
    extreme-value statistic: it measures the luckiest scrambled draw, not whether the method
    discriminates. On the 1,854 build it returned 0.247 -- from 35 groupings of 5-9 members out of
    43,625 -- forcing a threshold of 0.742, above the 0.5 ceiling, and reading as "this method does
    not work". Counted instead, zero scrambled groupings reach 0.25 against 3,457 real ones.

    Args:
        real: Support per real grouping; NaN for groupings too small to evaluate.
        null: Support per scrambled grouping.
        thresholds: The ``m`` values to count at.

    Returns:
        Per threshold: ``(m, real passing, null passing, null/real)``.
    """
    out: list[tuple[float, int, int, float]] = []
    for m in thresholds:
        r = int(np.sum(~np.isnan(real) & (real >= m)))
        n = int(np.sum(~np.isnan(null) & (null >= m)))
        out.append((float(m), r, n, (n / r) if r else float("nan")))
    return out


def choose_m(table: Sequence[tuple[float, int, int, float]], max_fdr: float = 0.0) -> float:
    """Pick the lowest threshold whose scrambled count is at or below ``max_fdr`` (step 7).

    Args:
        table: The output of :func:`null_table`, ascending in ``m``.
        max_fdr: Highest tolerable scrambled/real ratio. ``0.0`` means no scrambled grouping at all.

    Returns:
        The lowest qualifying ``m``.

    Raises:
        ValueError: If no threshold below :data:`MAX_M` qualifies. ``m`` must stay under 0.5, since
            two groupings each found in a majority of runs co-occur in some run, where they are
            clusters of one Ward tree and therefore nested or disjoint -- majority rule can only
            produce a tree, and overlap lives below 0.5.
    """
    for m, real, _null, ratio in sorted(table):
        if m < MAX_M and real > 0 and ratio <= max_fdr:
            return m
    raise ValueError(
        f"no threshold below {MAX_M} reaches a scrambled ratio of {max_fdr}; "
        f"table: {[(m, r, n) for m, r, n, _ in sorted(table)]}"
    )


def _node_from(
    pool: Pool, g: int, records_present: np.ndarray, n_bits: int
) -> tuple[np.ndarray, dict[int, float]]:
    """Build one node's candidate members and their inclusions, from a grouping's copies.

    The majority-inclusion step across copies (step 8's "existing" step): a pathway's inclusion is
    how many copies of this grouping held it, over how many copies came from runs that drew it.
    Never the union of copies -- with ``tol > 0`` each copy can carry a different extra member, and
    the union bloats by up to ``tol`` again.

    Args:
        pool: The scored pool.
        g: The grouping index.
        records_present: ``(runs, words)`` present bitsets.
        n_bits: Universe size in bits.

    Returns:
        The candidate bitset, and inclusion per candidate index.
    """
    copy_bits = [pool.groupings[g], *pool.copies[g].values()]
    copy_runs = np.array([min(pool.origins[g]), *pool.copies[g].keys()], dtype=np.int64)
    candidates = copy_bits[0].copy()
    for block in copy_bits[1:]:
        candidates = candidates | block
    stack = np.vstack(copy_bits)
    inclusions: dict[int, float] = {}
    for p in bits.unpack(candidates):
        word, bit = p // bits.WORD, np.uint64(1) << np.uint64(p % bits.WORD)
        holds = int(np.count_nonzero(stack[:, word] & bit))
        could = int(np.count_nonzero(records_present[copy_runs][:, word] & bit))
        inclusions[p] = min(holds / could, 1.0) if could else 0.0
    return bits.pack(list(inclusions), n_bits), inclusions


def is_variant(a: np.ndarray, b: np.ndarray) -> bool:
    """Whether two groupings are variants of one another.

    Each must differ from their shared part by at most ``max(TWIN_FLOOR, TWIN_FRACTION x |A n B|)``.
    That single rule covers both shapes the measurement found: a nested pair, where one side's
    difference is empty, and the ``A+s`` / ``A+t`` pair, where the runs could not decide which of
    two candidates fills one slot and neither contains the other.

    Args:
        a: One grouping's member bitset.
        b: The other's.

    Returns:
        True when both differences fit the allowance.
    """
    shared = bits.count(a & b)
    if not shared:
        return False
    allowed = max(TWIN_FLOOR, int(TWIN_FRACTION * shared))
    return bits.count(a & ~b) <= allowed and bits.count(b & ~a) <= allowed


def families(
    candidates: Sequence[int],
    member_bits: dict[int, np.ndarray] | None,
    pool: Pool,
    timing: Timing | None = None,
) -> list[tuple[int, list[int]]]:
    """Group groupings into variant families by seed absorption, without chaining.

    Run over the WHOLE pool, before any threshold. A theme that the runs describe slightly
    differently each time splits its evidence across several groupings, and thresholding first
    discards each fragment for being individually weak. Pooling the fragments into a family and
    thresholding the family is what keeps them.

    Each unclaimed grouping in rank order becomes a seed and claims every unclaimed grouping that
    is a variant **of the seed's own set**. Nothing is re-checked against the growing family: a
    seed that absorbs one variant and then compares the next against the grown set both misses
    legitimate variants of the original and, over many rounds, runs away.

    Args:
        candidates: Grouping indices to organise.
        member_bits: Bitset per candidate, or None to use the raw grouping bitsets.
        pool: The scored pool, for support and the raw bitsets.
        timing: Collector for stage durations.

    Returns:
        ``(seed, family including the seed)``, in rank order.
    """
    clock = timing if timing is not None else Timing()
    start = time.perf_counter()
    of = (lambda g: member_bits[g]) if member_bits is not None else (lambda g: pool.groupings[g])
    sizes = {g: bits.count(of(g)) for g in candidates}
    support = np.nan_to_num(pool.support, nan=0.0)
    ranked = sorted(candidates, key=lambda g: (-support[g], -sizes[g], bits.key(of(g))))
    by_size = sorted(candidates, key=lambda g: sizes[g])
    order_of = {g: i for i, g in enumerate(by_size)}
    claimed: set[int] = set()
    out: list[tuple[int, list[int]]] = []
    for seed in ranked:
        if seed in claimed:
            continue
        claimed.add(seed)
        seed_bits = of(seed)
        seed_size = sizes[seed]
        # Variants differ from the shared part by at most the allowance on each side, so their
        # sizes cannot differ by more than twice it. Walking only that window is what keeps this
        # off the 800 million pairs a 40,000-grouping pool would otherwise need.
        slack = max(TWIN_FLOOR, int(TWIN_FRACTION * seed_size)) * 2
        family = [seed]
        index = order_of[seed]
        for step in (-1, 1):
            at = index + step
            while 0 <= at < len(by_size):
                other = by_size[at]
                if abs(sizes[other] - seed_size) > slack:
                    break
                if other not in claimed and is_variant(seed_bits, of(other)):
                    claimed.add(other)
                    family.append(other)
                at += step
        out.append((seed, family))
    clock.record("families (seed absorption)", time.perf_counter() - start)
    return out


def family_support(family: Sequence[int], pool: Pool, eligible_mask: np.ndarray) -> float:
    """Support of a family: runs that found any member over runs able to judge any member.

    A theme described slightly differently in different runs has its evidence split across several
    groupings. Scoring the family rather than each grouping is what stops that split from looking
    like weakness.

    Args:
        family: Grouping indices in the family.
        pool: The scored pool.
        eligible_mask: ``(groupings, runs)`` -- whether a run could judge a grouping.

    Returns:
        Support in ``[0, 1]``, or 0.0 when no run could judge the family.
    """
    found: set[int] = set()
    for g in family:
        found |= set(pool.copies[g])
        found |= pool.origins[g]
    eligible = int(np.count_nonzero(eligible_mask[list(family)].any(axis=0)))
    return (len(found) / eligible) if eligible else 0.0


def grouping_members(
    g: int, pool: Pool, records_present: np.ndarray, n_bits: int, threshold: float
) -> tuple[np.ndarray, dict[int, float]]:
    """Complete one grouping's membership from its own copies, before any merging.

    A grouping's bitset holds only what its ORIGIN run drew -- roughly 80% of its true membership,
    since the other 20% was never available to that run to be grouped. Computing inclusion over the
    grouping's own copies restores the rest: a pathway found alongside this grouping in a quarter of
    the runs that drew it is a member, whether or not the origin run happened to see it.

    Doing this BEFORE the variant merge is what lets the merge compare completed member sets rather
    than partial ones, so two groupings that describe the same theme are recognised as variants
    even when their origin runs saw different subsets of it.

    Args:
        g: The grouping index.
        pool: The scored pool.
        records_present: ``(runs, words)`` present bitsets.
        n_bits: Universe size in bits.
        threshold: Smallest inclusion a member may have.

    Returns:
        The member bitset and inclusion per member.
    """
    copies = {**{r: pool.groupings[g] for r in pool.origins[g]}, **pool.copies[g]}
    if not copies:
        return bits.empty(n_bits), {}
    runs = np.array(sorted(copies), dtype=np.int64)
    stack = np.vstack([copies[int(r)] for r in runs])
    candidates = stack[0].copy()
    for block in stack[1:]:
        candidates = candidates | block

    inclusions: dict[int, float] = {}
    for p in bits.unpack(candidates):
        word, bit = p // bits.WORD, np.uint64(1) << np.uint64(p % bits.WORD)
        holds = int(np.count_nonzero(stack[:, word] & bit))
        could = int(np.count_nonzero(records_present[runs][:, word] & bit))
        value = min(holds / could, 1.0) if could else 0.0
        if value >= threshold:
            inclusions[p] = value
    return bits.pack(list(inclusions), n_bits), inclusions


def family_members(
    family: list[int], pool: Pool, records_present: np.ndarray, n_bits: int
) -> tuple[np.ndarray, dict[int, float]]:
    """Compute one family's members and their inclusions from the runs' copies.

    For every run where any family member was found, that run's copy is one vote. A pathway's
    inclusion is the share of those votes that held it, counted only over runs that actually drew
    it -- a run that never saw a pathway cannot be evidence either way.

    Args:
        family: Grouping indices in the family.
        pool: The scored pool.
        records_present: ``(runs, words)`` present bitsets.
        n_bits: Universe size in bits.

    Returns:
        The candidate bitset and inclusion per candidate index.
    """
    # One copy per run: where several family members were found in the same run, their copies are
    # variants of each other, and the union is what that run actually saw of the family.
    per_run: dict[int, np.ndarray] = {}
    for g in family:
        for run, copy in pool.copies[g].items():
            per_run[run] = copy if run not in per_run else (per_run[run] | copy)
        for run in pool.origins[g]:
            if run not in per_run:
                per_run[run] = pool.groupings[g]
    if not per_run:
        return bits.empty(n_bits), {}

    runs = np.array(sorted(per_run), dtype=np.int64)
    stack = np.vstack([per_run[int(r)] for r in runs])
    candidates = stack[0].copy()
    for block in stack[1:]:
        candidates = candidates | block

    inclusions: dict[int, float] = {}
    for p in bits.unpack(candidates):
        word, bit = p // bits.WORD, np.uint64(1) << np.uint64(p % bits.WORD)
        holds = int(np.count_nonzero(stack[:, word] & bit))
        could = int(np.count_nonzero(records_present[runs][:, word] & bit))
        inclusions[p] = min(holds / could, 1.0) if could else 0.0
    return candidates, inclusions


def assemble(
    pool: Pool,
    records_present: np.ndarray,
    m: float,
    settings: dict[str, object],
    timing: Timing | None = None,
    eligible_mask: np.ndarray | None = None,
    collect: list[dict[str, object]] | None = None,
    grouped: list[tuple[int, list[int]]] | None = None,
) -> tuple[list[np.ndarray], list[float], list[list[float]], list[int], int]:
    """Families first, then the threshold, then membership merged to a fixed point.

    The order was settled by measurement, each step answering a specific failure:

    1. **Families across the whole pool**, before any threshold. A theme the runs describe slightly
       differently splits its evidence across several groupings; thresholding first discards each
       fragment for being individually weak.
    2. **``m`` applies to FAMILY support** -- runs that found any member over runs able to judge
       any member.
    3. **Membership from the family's pooled copies**, which restores the ~25% a single origin run
       never drew.
    4. **Merge to a fixed point.** Two families whose seeds were not variants can still produce
       final member sets that are, because membership is computed after the merge. One pass leaves
       those behind; repeating until nothing changes is what makes the variant count actually zero.

    Args:
        pool: The scored pool.
        records_present: ``(runs, words)`` present bitsets.
        m: Support threshold, applied to family support.
        settings: Parameters, already defaulted.
        timing: Collector for stage durations.
        eligible_mask: ``(groupings, runs)`` eligibility; required for family support.
        collect: If given, cleared and filled with one dict per returned node, in the same order,
            holding ``family`` (the grouping indices) and ``inclusions`` (EVERY candidate's
            inclusion, including those below ``inclusion_threshold``). The return value carries
            only surviving members, so a pathway the cutoff drops is otherwise unrecoverable
            without recomputing the build; ``near_members.tsv`` is written from this.
        grouped: Precomputed variant families, as :func:`families` returns them. Families do not
            depend on ``m``, so a threshold sweep that recomputes them per value pays for the most
            expensive stage of the build once per point for no gain. Omitted, they are computed.

    Returns:
        Member bitsets, node supports, inclusion values aligned to each bitset's set bits, each
        node's seed size (the raw grouping it was seeded from), and how many merge rounds ran.
    """
    clock = timing if timing is not None else Timing()
    threshold = float(settings["inclusion_threshold"])  # type: ignore[arg-type]
    min_size = int(settings["min_size"])  # type: ignore[arg-type]
    n_bits = records_present.shape[1] * bits.WORD
    if eligible_mask is None:
        raise ValueError("family support needs the eligibility mask")

    if grouped is None:
        evaluable = [g for g in range(len(pool.groupings)) if not np.isnan(pool.support[g])]
        grouped = families(evaluable, None, pool, clock)

    start = time.perf_counter()
    kept = [
        (seed, family)
        for seed, family in grouped
        if family_support(family, pool, eligible_mask) >= m
    ]
    clock.record("family threshold", time.perf_counter() - start)

    start = time.perf_counter()
    raw_sizes = bits.count_rows(pool.groupings) if len(pool.groupings) else np.zeros(0, np.int64)
    nodes: list[dict[str, object]] = []
    for seed, family in kept:
        candidates, inclusions = family_members(family, pool, records_present, n_bits)
        members = sorted(p for p in bits.unpack(candidates) if inclusions.get(p, 0.0) >= threshold)
        if len(members) < min_size:
            continue
        nodes.append(
            {
                "bits": bits.pack(members, n_bits),
                "family": list(family),
                "support": family_support(family, pool, eligible_mask),
                "seed_size": int(raw_sizes[seed]),
                "incl": {p: inclusions[p] for p in members},
                "all_incl": dict(inclusions),
            }
        )

    # Merge to a fixed point: recomputing membership can turn two non-variant nodes into variants.
    rounds = 0
    while True:
        rounds += 1
        pairs_found = False
        order = sorted(range(len(nodes)), key=lambda i: -float(nodes[i]["support"]))  # type: ignore[arg-type]
        merged_into: dict[int, int] = {}
        gone: set[int] = set()
        for a in order:
            if a in gone:
                continue
            for b in order:
                if b == a or b in gone or a in gone:
                    continue
                if is_variant(nodes[a]["bits"], nodes[b]["bits"]):  # type: ignore[arg-type]
                    merged_into.setdefault(a, a)
                    nodes[a]["family"] = list(nodes[a]["family"]) + list(nodes[b]["family"])  # type: ignore[operator]
                    gone.add(b)
                    pairs_found = True
        if not pairs_found:
            break
        rebuilt: list[dict[str, object]] = []
        for index, node in enumerate(nodes):
            if index in gone:
                continue
            family = list(node["family"])  # type: ignore[arg-type]
            candidates, inclusions = family_members(family, pool, records_present, n_bits)
            members = sorted(
                p for p in bits.unpack(candidates) if inclusions.get(p, 0.0) >= threshold
            )
            if len(members) < min_size:
                continue
            rebuilt.append(
                {
                    "bits": bits.pack(members, n_bits),
                    "family": family,
                    "support": family_support(family, pool, eligible_mask),
                    "seed_size": node["seed_size"],
                    "incl": {p: inclusions[p] for p in members},
                    "all_incl": dict(inclusions),
                }
            )
        nodes = rebuilt
        if rounds > 20:
            break
    clock.record("membership + fixed-point merge", time.perf_counter() - start)

    final: dict[bytes, dict[str, object]] = {}
    for node in nodes:
        identity = bits.key(node["bits"])  # type: ignore[arg-type]
        if identity not in final or float(node["support"]) > float(final[identity]["support"]):  # type: ignore[arg-type]
            final[identity] = node
    ordered = sorted(
        final.values(),
        key=lambda node: (-bits.count(node["bits"]), bits.key(node["bits"])),  # type: ignore[arg-type]
    )
    if collect is not None:
        collect.clear()
        collect.extend(
            {"family": list(node["family"]), "inclusions": dict(node["all_incl"])}  # type: ignore[arg-type]
            for node in ordered
        )
    return (
        [node["bits"] for node in ordered],  # type: ignore[misc]
        [float(node["support"]) for node in ordered],  # type: ignore[arg-type]
        [[node["incl"][p] for p in bits.unpack(node["bits"])] for node in ordered],  # type: ignore[index]
        [int(node["seed_size"]) for node in ordered],  # type: ignore[arg-type]
        rounds,
    )


def hasse(member_sets: list[np.ndarray], timing: Timing | None = None) -> list[tuple[int, ...]]:
    """Order nodes by strict containment, keeping only the immediate parents (§10.8).

    A is a parent of B iff ``members(B) < members(A)`` strictly and no C sits between them. Acyclic
    by construction -- strict inclusion is a strict partial order -- and asserted anyway by
    :func:`thema.ontology.base.check_invariants`.

    Args:
        member_sets: Node member bitsets, largest first.
        timing: Collector for stage durations.

    Returns:
        Per node, the indices of its immediate parents.
    """
    clock = timing if timing is not None else Timing()
    start = time.perf_counter()
    parents: list[tuple[int, ...]] = []
    for b, inner in enumerate(member_sets):
        candidates = [
            a
            for a, outer in enumerate(member_sets)
            if a != b and bits.is_strict_subset(inner, outer)
        ]
        # Keep the minimal candidates: drop any that strictly contains another candidate.
        minimal = [
            a
            for a in candidates
            if not any(
                other != a and bits.is_strict_subset(member_sets[other], member_sets[a])
                for other in candidates
            )
        ]
        parents.append(tuple(sorted(minimal)))
    clock.record("edges (hasse)", time.perf_counter() - start)
    return parents


#: The thresholds the null is counted at when `m` is not given.
NULL_THRESHOLDS = (0.10, 0.15, 0.20, 0.25, 0.33, 0.50)


def null_embeddings(x: np.ndarray, seed: int) -> np.ndarray:
    """Permute each dimension independently across pathways, then re-normalise the rows.

    Permuting destroys the structure while keeping each dimension's marginal distribution. It also
    destroys row unit-length, and ``cluster.distances`` refuses non-unit input -- correctly, since
    Ward on non-Euclidean input is silently meaningless -- so the rows are re-normalised
    (addendum-2026-09-21 step 7). The manifest records that this was done.

    Args:
        x: The real ``(n, dim)`` unit-vector matrix.
        seed: Master seed.

    Returns:
        A structure-free matrix of unit vectors.
    """
    rng = np.random.default_rng(seed)
    shuffled = np.array(x, dtype=np.float64, copy=True)
    for column in range(shuffled.shape[1]):
        rng.shuffle(shuffled[:, column])
    lengths = np.linalg.norm(shuffled, axis=1, keepdims=True)
    return (shuffled / np.where(lengths == 0, 1.0, lengths)).astype(np.float32)


def null_counts(
    x: np.ndarray,
    n: int,
    settings: dict[str, object],
    seed: int,
    thresholds: Sequence[float] = NULL_THRESHOLDS,
) -> list[tuple[float, int, int, float]]:
    """Count real and scrambled groupings passing each threshold.

    Args:
        x: The real ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        settings: Parameters, already defaulted.
        seed: Master seed; the same one, so the null sees the same draws.
        thresholds: The ``m`` values to count at.

    Returns:
        Per threshold: ``(m, real passing, null passing, null/real)``.
    """
    def family_supports(matrix: np.ndarray) -> np.ndarray:
        ready = prepare(matrix, n, settings, seed)
        pool = score(ready, settings)
        evaluable = [g for g in range(len(pool.groupings)) if not np.isnan(pool.support[g])]
        return np.array(
            [
                family_support(family, pool, ready.eligible_mask)
                for _seed, family in families(evaluable, None, pool)
            ]
        )

    # The null must go through the SAME procedure as the real data. Counting scrambled GROUPINGS
    # against real FAMILIES would compare a fragmented null with a pooled signal and understate
    # the false-discovery rate by exactly the amount the pooling buys.
    return null_table(family_supports(x), family_supports(null_embeddings(x, seed)), thresholds)


def null_support(x: np.ndarray, n: int, settings: dict[str, object], seed: int) -> float:
    """The highest support any grouping reaches on structure-free embeddings.

    Retained only for the record. **Do not threshold on this** -- over tens of thousands of
    groupings a maximum measures the luckiest scrambled draw, not whether the method discriminates.
    Use :func:`null_counts` and :func:`choose_m`.

    Each dimension is permuted independently across pathways, which destroys the structure while
    keeping each dimension's marginal distribution. That also destroys row unit-length, and
    ``cluster.distances`` refuses non-unit input -- correctly, since Ward on non-Euclidean input is
    silently meaningless -- so the rows are re-normalised afterwards. The manifest records that.

    Args:
        x: The real ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        settings: Parameters, already defaulted.
        seed: Master seed; the same one, so the null sees the same draws.

    Returns:
        ``null_max``, the highest support reached. 0.0 when nothing was evaluable.
    """
    pool = build_pool(null_embeddings(x, seed), n, settings, seed)
    finite = pool.support[~np.isnan(pool.support)]
    return float(finite.max()) if len(finite) else 0.0


class RecurrentDag:
    """Ward over resampled subsets; groupings that recur become nodes, ordered by containment."""

    method = "recurrent_dag"

    def build(
        self,
        x: np.ndarray,
        keys: Sequence[str],
        params: dict[str, object] | None = None,
        seed: int = 0,
    ) -> Ontology:
        """Build one ontology at one support threshold.

        Args:
            x: An ``(n, dim)`` array of unit vectors.
            keys: The pathway key per row, in row order.
            params: Overrides for :data:`DEFAULTS`. ``m`` may be given directly; if it is absent,
                the null run determines it and its cost is paid here.
            seed: Master seed. Per-run seeds are derived from it and recorded.

        Returns:
            The ontology, with timings and ``null_max`` in ``params``.

        Raises:
            ValueError: If the null-derived threshold reaches :data:`MAX_M` (addendum B1), or if
                the result violates an invariant.
        """
        settings = {**DEFAULTS, **(params or {})}
        n = len(keys)
        clock = Timing()

        m = settings.get("m")
        table = None
        if m is None:
            start = time.perf_counter()
            table = null_counts(x, n, settings, seed)
            clock.record("null run", time.perf_counter() - start)
            m = choose_m(table)

        ready = prepare(x, n, settings, seed, clock)
        pool = score(ready, settings)
        present = ready.present
        member_sets, supports, inclusions, seed_sizes, _rounds = assemble(
            pool, present, float(m), settings, clock, ready.eligible_mask
        )
        parents = hasse(member_sets, clock)

        nodes = tuple(
            Node(
                id=f"n{index:04d}",
                parents=tuple(f"n{p:04d}" for p in parent_indices),
                members=tuple(
                    (keys[p], round(inclusion, 4))
                    for p, inclusion in zip(bits.unpack(member_bits), node_inclusions, strict=True)
                ),
                support=round(support, 4),
            )
            for index, (member_bits, support, node_inclusions, parent_indices) in enumerate(
                zip(member_sets, supports, inclusions, parents, strict=True)
            )
        )
        placed = {key for node in nodes for key in node.keys}
        ontology = Ontology(
            method=self.method,
            params={
                **settings,
                "m": float(m),
                "null_table": None if table is None else [list(row) for row in table],
                "seed": seed,
                "run_seeds_sha256": hashlib.sha256(
                    ",".join(str(s) for s in _seeds(seed, int(settings["runs"]))).encode()
                ).hexdigest(),
                "null_renormalised": True,
                "pool_size": int(len(pool.groupings)),
                "seed_sizes": seed_sizes,
                "timing_seconds": dict(clock.stages),
            },
            nodes=nodes,
            unplaced=tuple(sorted(set(keys) - placed)),
        )
        check_invariants(ontology, keys, min_size=int(settings["min_size"]))  # type: ignore[arg-type]
        check_distinct_members(ontology)
        return ontology
