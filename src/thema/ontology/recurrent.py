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
    "inclusion_threshold": 0.5,
    "embedder_split": False,
}

#: `m` must be below 0.5. Two groupings each found in a majority of runs co-occur in some run, where
#: they are clusters of one Ward tree and therefore nested or disjoint -- majority rule can only
#: produce a tree. Overlap lives below 0.5.
MAX_M = 0.5

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


def _one_run(x: np.ndarray, n: int, subsample: float, min_size: int, seed: int) -> Run:
    """Draw a subset, cluster it, and record every grouping of at least ``min_size``.

    Args:
        x: The full ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        subsample: Fraction of pathways to draw.
        min_size: Smallest grouping worth recording.
        seed: This run's seed.

    Returns:
        The run's record.
    """
    rng = np.random.default_rng(seed)
    take = int(np.ceil(subsample * n))
    subset = np.sort(rng.choice(n, size=take, replace=False))
    words = bits.words_for(n)

    present = bits.pack(subset.tolist(), n)
    z = linkage(distances(x[subset]), method="ward")

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
    # Every dendrogram node of at least min_size, EXCEPT the root. A grouping equal to everything
    # the run drew recurs at support 1.0 by construction and says nothing about which pathways
    # belong together; kept, it reappears as a node holding every pathway -- precisely the "all
    # themes" root addendum A3 removes. The spec's §10.2 does not exclude it; this does.
    recorded = np.flatnonzero((sizes >= min_size) & (sizes < take))
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


def _smallest_superset(run: Run, target: np.ndarray, any_member: int) -> int:
    """Find the smallest recorded cluster of ``run`` containing every bit of ``target`` (§10.4).

    Walks up from the smallest cluster holding one arbitrary member. Clusters on one root path are
    nested, so the first superset reached is the smallest one.

    Args:
        run: The run to search.
        target: The bitset that must be contained.
        any_member: The index of one pathway in ``target``.

    Returns:
        The index into ``run.clusters``, or -1 when no recorded cluster contains it.
    """
    at = int(run.leaf_cluster[any_member])
    while at != -1:
        if bits.contains(run.clusters[at], target):
            return at
        at = int(run.parent[at])
    return -1


def found_in(
    run: Run,
    grouping: np.ndarray,
    origin_present: np.ndarray,
    min_shared: int,
    tol: float,
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
            exact-on-shared.

    Returns:
        Whether it was found, and the matched cluster bitset when it was. ``(False, None)`` covers
        both "not eligible" and "eligible but not found"; :func:`build_pool` checks eligibility
        separately because it vectorises that step.
    """
    g_s = grouping & run.present
    shared_count = bits.count(g_s)
    if shared_count < min_shared:
        return False, None
    anchor = _first_set_bit(g_s)
    if anchor < 0:
        return False, None
    at = _smallest_superset(run, g_s, anchor)
    if at == -1:
        return False, None
    shared = run.present & origin_present
    extra = bits.count(run.clusters[at] & shared) - shared_count
    return (extra <= tol * shared_count), run.clusters[at]


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
    records = [
        _one_run(x, n, float(settings["subsample"]), min_size, s)  # type: ignore[arg-type]
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
        settings: Parameters, already defaulted; ``tol`` and ``min_shared`` are read here.

    Returns:
        The scored pool.
    """
    clock = ready.timing
    records, groupings, origins = ready.records, ready.groupings, ready.origins
    eligible_mask, eligible_count = ready.eligible_mask, ready.eligible_count
    runs = len(records)
    min_shared = int(settings["min_shared"])  # type: ignore[arg-type]
    tol = float(settings["tol"])  # type: ignore[arg-type]
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
                run, target_all, _origin_present(records, origins[g]), min_shared, tol
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


def choose_m(null_max: float) -> float:
    """Set the support threshold from the null (§10.6, addendum B1).

    Args:
        null_max: The highest support any grouping reached on permuted embeddings.

    Returns:
        ``max(MIN_M, 3 * null_max)``.

    Raises:
        ValueError: If that lands at or above :data:`MAX_M`. The threshold is NOT clamped: a null
            that produces recurrent structure this strong means the method is not discriminating
            on this data, and that is a finding to report rather than a knob to turn.
    """
    proposed = max(MIN_M, 3.0 * null_max)
    if proposed >= MAX_M:
        raise ValueError(
            f"null_max={null_max:.3f} gives m={proposed:.3f}, at or above {MAX_M}. Resampling "
            "produces recurrent structure by chance at this strength, so the method is not "
            "discriminating on this data. Reported, not clamped."
        )
    return proposed


def assemble(
    pool: Pool,
    records_present: np.ndarray,
    m: float,
    settings: dict[str, object],
    timing: Timing | None = None,
) -> tuple[list[np.ndarray], list[float], list[list[float]]]:
    """Merge robust groupings into nodes by seed absorption (§10.7).

    Not connected components of the "found" relation: with ``tol > 0`` that chains, and one node
    swallows a ladder of distinct groupings.

    Args:
        pool: The scored pool.
        records_present: ``(runs, words)`` present bitsets.
        m: Support threshold.
        settings: Parameters, already defaulted.
        timing: Collector for stage durations.

    Returns:
        Member bitsets, node supports, and per-node inclusion values aligned to the member bitset's
        set bits in ascending index order.
    """
    clock = timing if timing is not None else Timing()
    start = time.perf_counter()
    threshold = float(settings["inclusion_threshold"])  # type: ignore[arg-type]
    min_size = int(settings["min_size"])  # type: ignore[arg-type]

    robust = [g for g in np.flatnonzero(pool.support >= m) if not np.isnan(pool.support[g])]
    # Deterministic order: support desc, then size desc, then the bitset itself.
    sizes = bits.count_rows(pool.groupings) if len(pool.groupings) else np.zeros(0, dtype=np.int64)
    robust.sort(key=lambda g: (-pool.support[g], -int(sizes[g]), bits.key(pool.groupings[g])))

    consumed: set[int] = set()
    by_identity: dict[bytes, tuple[np.ndarray, float, list[float]]] = {}
    for g in robust:
        if g in consumed:
            continue
        consumed.add(g)
        # The node's copies: the seed itself, plus whatever each run that found it matched it to.
        copy_bits = [pool.groupings[g]] + list(pool.copies[g].values())
        copy_runs = [min(pool.origins[g])] + list(pool.copies[g].keys())
        for other in robust:
            if other not in consumed and bits.key(pool.groupings[other]) in {
                bits.key(c) for c in copy_bits
            }:
                consumed.add(other)

        # Membership is the inclusion rule, never the union of copies: with tol > 0 each copy can
        # carry a different extra member, and the union bloats by up to tol again.
        candidates = copy_bits[0].copy()
        for block in copy_bits[1:]:
            candidates = candidates | block
        stack = np.vstack(copy_bits)
        runs_of_copy = np.array(copy_runs, dtype=np.int64)
        members: list[int] = []
        inclusions: list[float] = []
        for p in bits.unpack(candidates):
            word, bit = p // bits.WORD, np.uint64(1) << np.uint64(p % bits.WORD)
            holds = int(np.count_nonzero(stack[:, word] & bit))
            could = int(
                np.count_nonzero(records_present[runs_of_copy][:, word] & bit)
            )
            inclusion = holds / could if could else 0.0
            if inclusion >= threshold:
                members.append(p)
                inclusions.append(min(inclusion, 1.0))
        if len(members) < min_size:
            continue
        member_bits = bits.pack(members, records_present.shape[1] * bits.WORD)
        identity = bits.key(member_bits)
        support = float(pool.support[g])
        kept = by_identity.get(identity)
        # Nodes whose member sets come out identical are merged, keeping the higher support.
        if kept is None or support > kept[1]:
            by_identity[identity] = (member_bits, support, inclusions)

    ordered = sorted(
        by_identity.values(), key=lambda item: (-bits.count(item[0]), bits.key(item[0]))
    )
    clock.record("assembly (seed absorption)", time.perf_counter() - start)
    return (
        [item[0] for item in ordered],
        [item[1] for item in ordered],
        [item[2] for item in ordered],
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


def null_support(x: np.ndarray, n: int, settings: dict[str, object], seed: int) -> float:
    """The highest support any grouping reaches on structure-free embeddings (§10.6).

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
    rng = np.random.default_rng(seed)
    shuffled = np.array(x, dtype=np.float64, copy=True)
    for column in range(shuffled.shape[1]):
        rng.shuffle(shuffled[:, column])
    lengths = np.linalg.norm(shuffled, axis=1, keepdims=True)
    shuffled = (shuffled / np.where(lengths == 0, 1.0, lengths)).astype(np.float32)
    pool = build_pool(shuffled, n, settings, seed)
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

        null_max = settings.get("null_max")
        m = settings.get("m")
        if m is None:
            start = time.perf_counter()
            null_max = null_support(x, n, settings, seed)
            clock.record("null run", time.perf_counter() - start)
            m = choose_m(float(null_max))

        pool = build_pool(x, n, settings, seed, clock)
        present = np.vstack(
            [_one_run(x, n, float(settings["subsample"]), int(settings["min_size"]), s).present
             for s in _seeds(seed, int(settings["runs"]))]
        )
        member_sets, supports, inclusions = assemble(pool, present, float(m), settings, clock)
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
                "null_max": None if null_max is None else float(null_max),
                "seed": seed,
                "run_seeds_sha256": hashlib.sha256(
                    ",".join(str(s) for s in _seeds(seed, int(settings["runs"]))).encode()
                ).hexdigest(),
                "null_renormalised": True,
                "pool_size": int(len(pool.groupings)),
                "timing_seconds": dict(clock.stages),
            },
            nodes=nodes,
            unplaced=tuple(sorted(set(keys) - placed)),
        )
        check_invariants(ontology, keys, min_size=int(settings["min_size"]))  # type: ignore[arg-type]
        check_distinct_members(ontology)
        return ontology
