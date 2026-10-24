"""Arm K: finding cores in the Ward trees. Prompt 59, declared 23 Oct 2026.

Exploratory; **no ontology is built** and nothing is adopted.

Prompt 58 showed why cores taken from J >= 0.70 copies cannot work: from 25 pathways up the median
cluster is found in one run of 200, its own, so its "core" is the whole cluster. Arm K looks in the
trees instead. A core need not appear as a cluster on its own; it has to keep coming back *inside*
clusters that are mostly the core.

**The test.** For a set K and a run r: K is judged in r if at least 3 of K's pathways were drawn.
Take the smallest cluster of r's tree holding all of K's drawn pathways -- their lowest common
ancestor -- and r FINDS K if K's drawn pathways make up at least 70% of that cluster.
``Support(K) = finds / judges``.

**Why the candidates are cluster intersections.** A set found in two runs lies inside both
enclosing clusters, and each of those clusters is at most ``|K| / 0.7`` in size. So every set that
can be found twice is contained in ``C1 & C2`` for clusters from two different runs, each at least
70% covered by the intersection. That makes the intersections an exact superset of the findable
cores, which is why step 2 enumerates them rather than guessing.

**The size window is exact, not a heuristic.** A qualifying pair needs ``|I| >= 0.7 * max(|C1|,
|C2|)`` and ``|I| <= min``, so ``max / min <= 1 / 0.7``. Clusters outside that ratio cannot qualify
and are never compared. Overlap counts come from chunked sparse products, as in prompt 58, and are
verified against an explicit double loop on a random sample.

Usage:
    uv run scripts/tree_cores.py --candidates
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_COVER = 0.70
MIN_SIZE = 3
SEED = 20261023
SAMPLE = 2000
CHUNK = 256

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return BANDS[0][2]


def load_clusters(args: argparse.Namespace) -> dict[str, object]:
    """Every cluster of 3+ pathways from all 200 real runs, with its run and size.

    Args:
        args: Parsed arguments.

    Returns:
        ``{stack, sizes, runs, order, present, n, runs_list}``.
    """
    from cut_trees import load_run
    from thema.ontology.v04 import NO_CAP

    meta = json.loads((args.space_root / "universe.json").read_text())
    n = meta["n_embedded"]
    root = (args.trees if getattr(args, "trees", None)
            else args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}")
    clock = time.perf_counter()
    blocks, sizes, runs, present, records = [], [], [], [], []
    for r in range(1, args.runs + 1):
        run = load_run(root / f"row{r:05d}.npz", n, NO_CAP)
        keep = np.flatnonzero(np.asarray(run.sizes) >= MIN_SIZE)
        blocks.append(np.asarray(run.clusters)[keep])
        sizes.append(np.asarray(run.sizes)[keep])
        runs.append(np.full(len(keep), r - 1, dtype=np.int32))
        present.append(np.asarray(run.present))
        records.append(run)
    stack = np.vstack(blocks)
    size = np.concatenate(sizes).astype(np.int64)
    run_of = np.concatenate(runs)
    print(f"  {len(stack):,} clusters of {MIN_SIZE}+ over {args.runs} runs "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"stack": stack, "sizes": size, "runs": run_of, "present": np.vstack(present),
            "n": n, "records": records, "meta": meta}


def to_csr(stack: np.ndarray, n: int) -> object:
    """Sparse incidence matrix for a stack of bitsets.

    Args:
        stack: ``(m, words)`` bitsets.
        n: Universe size.

    Returns:
        A ``scipy.sparse.csr_matrix`` of ones.
    """
    from scipy import sparse

    from thema.ontology import bitset as bits

    rows = [np.fromiter(bits.unpack(stack[i]), dtype=np.int32) for i in range(len(stack))]
    indptr = np.zeros(len(rows) + 1, dtype=np.int64)
    np.cumsum([len(r) for r in rows], out=indptr[1:])
    indices = np.concatenate(rows) if rows else np.zeros(0, np.int32)
    return sparse.csr_matrix((np.ones(len(indices), dtype=np.int32), indices, indptr),
                             shape=(len(rows), n), dtype=np.int32)


def qualifying(csr: object, stack: np.ndarray, sizes: np.ndarray, runs: np.ndarray,
               cover: float, report: bool = True
               ) -> tuple[int, dict[bytes, np.ndarray], dict[str, int]]:
    """Every qualifying cluster pair, and the distinct intersections they produce.

    Candidates are keyed on a 128-bit digest of the intersection and stored as sparse member
    arrays, not as the 87-word bitsets they came from. At the five million candidates the prompt
    allows, the bitset form would be about 3.5 GB; the sparse form is under 400 MB. A 128-bit
    digest over at most five million keys has a collision probability around 1e-26.

    Args:
        csr: Cluster-by-pathway matrix, in ascending size order.
        stack: Matching bitsets, same order.
        sizes: Matching sizes, ascending.
        runs: Matching run ids.
        cover: The share of the larger cluster the intersection must make up.
        report: Print progress.

    Returns:
        ``(qualifying pairs, {intersection bytes: size}, pairs by band of the larger)``.
    """
    from thema.ontology import bitset as bits

    transposed = csr.T.tocsc()
    total = 0
    seen: dict[bytes, np.ndarray] = {}
    by_band: dict[str, int] = defaultdict(int)
    clock = time.perf_counter()
    for start in range(0, len(sizes), CHUNK):
        stop = min(start + CHUNK, len(sizes))
        # Exact window: a partner must satisfy max/min <= 1/cover, so only clusters whose
        # size lies in [cover * smallest, largest / cover] can qualify in this chunk.
        low = int(np.searchsorted(sizes, int(np.ceil(cover * sizes[start])), side="left"))
        high = int(np.searchsorted(sizes, int(np.floor(sizes[stop - 1] / cover)), side="right"))
        block = (csr[start:stop] @ transposed[:, low:high]).tocoo()
        if not len(block.data):
            continue
        left = block.row + start
        right = block.col + low
        inter = block.data.astype(np.int64)
        keep = (left < right) & (runs[left] != runs[right]) & (inter >= MIN_SIZE)
        if not keep.any():
            continue
        left, right, inter = left[keep], right[keep], inter[keep]
        bigger = np.maximum(sizes[left], sizes[right])
        keep = inter * 100 >= int(cover * 100) * bigger
        if not keep.any():
            continue
        left, right, bigger = left[keep], right[keep], bigger[keep]
        total += int(len(left))
        for big, count in zip(*np.unique(bigger, return_counts=True), strict=True):
            by_band[band_of(int(big))] += int(count)
        # Vectorised: the intersections for the whole chunk at once, deduplicated inside the chunk
        # before anything is hashed. The per-pair Python loop this replaces was the bottleneck --
        # at cover 0.50 there are an order of magnitude more qualifying pairs.
        shared = np.unique(stack[left] & stack[right], axis=0)
        for row in range(len(shared)):
            digest = hashlib.blake2b(shared[row].tobytes(), digest_size=16).digest()
            if digest not in seen:
                seen[digest] = np.fromiter(bits.unpack(shared[row]), dtype=np.int32)
        if report and (start // CHUNK) % 200 == 0:
            print(f"      {stop:,}/{len(sizes):,}  pairs {total:,}  distinct {len(seen):,}  "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return total, seen, dict(by_band)


def brute(stack: np.ndarray, sizes: np.ndarray, runs: np.ndarray,
          pick: np.ndarray, cover: float) -> tuple[int, int]:
    """The same count by an explicit double loop over a sample.

    Args:
        stack: Bitsets.
        sizes: Sizes.
        runs: Run ids.
        pick: Row indices in the sample.
        cover: The share of the larger cluster the intersection must make up.

    Returns:
        ``(qualifying pairs, distinct intersections)``.
    """
    rows = [int(i) for i in pick]
    pairs = 0
    seen: set[bytes] = set()
    for position, a in enumerate(rows):
        for b in rows[position + 1:]:
            if runs[a] == runs[b]:
                continue
            shared = stack[a] & stack[b]
            size = int(np.bitwise_count(shared).sum())
            if size < MIN_SIZE:
                continue
            if size * 100 >= int(cover * 100) * max(int(sizes[a]), int(sizes[b])):
                pairs += 1
                seen.add(shared.tobytes())
    return pairs, len(seen)


def main(argv: list[str] | None = None) -> int:
    """Step 2: the candidate census, with its verification.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/tree_cores_2026-10-23"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--cover", type=float, default=DEFAULT_COVER,
                        help="the share of the enclosing cluster a core must make up")
    parser.add_argument("--trees", type=Path, default=None,
                        help="tree directory to read instead of the cached real one, for a "
                             "scramble side. Must hold row00001.npz upwards.")
    parser.add_argument("--candidates", action="store_true",
                        help="run step 2 and stop, which is the prompt's own decision point")
    parser.add_argument("--score", action="store_true",
                        help="step 3: judge and find every cached candidate in every run")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    if args.score:
        return step_three(args)

    print("PROMPT 59 ARM K: cores found in the Ward trees.")
    print(f"  a run FINDS K when K's drawn pathways are >= {args.cover:.0%} of their cluster")
    print("  scramble TREES are not cached for the x2 universe, so step 6's floors cannot be")
    print("  solved; the prompt forbids building them. 'found in at least 2 runs' is the")
    print("  labelled placeholder.")
    got = load_clusters(args)
    order = np.argsort(got["sizes"], kind="stable")
    stack = got["stack"][order]
    sizes = got["sizes"][order]
    runs = got["runs"][order]
    clock = time.perf_counter()
    csr = to_csr(stack, got["n"])
    print(f"  incidence matrix {csr.shape[0]:,} x {csr.shape[1]:,}, {csr.nnz:,} nonzeros "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)

    pairs, seen, by_band = qualifying(csr, stack, sizes, runs, args.cover)
    cand_bands: dict[str, int] = defaultdict(int)
    for members in seen.values():
        cand_bands[band_of(len(members))] += 1
    print()
    print(f"  QUALIFYING CLUSTER PAIRS   {pairs:,}")
    print(f"  DISTINCT CANDIDATES        {len(seen):,}")
    print(f"  {'band':<12}{'pairs (larger)':>16}{'distinct candidates':>22}")
    for _lo, _hi, band in BANDS:
        if by_band.get(band) or cand_bands.get(band):
            print(f"  {band:<12}{by_band.get(band, 0):>16,}{cand_bands.get(band, 0):>22,}")

    rng = np.random.default_rng(SEED)
    take = min(SAMPLE, len(sizes))
    pick = np.sort(rng.choice(len(sizes), size=take, replace=False))
    sub_csr = to_csr(stack[pick], got["n"])
    fast_pairs, fast_seen, _b = qualifying(sub_csr, stack[pick], sizes[pick], runs[pick],
                                           args.cover, report=False)
    slow_pairs, slow_distinct = brute(stack, sizes, runs, pick, args.cover)
    agree = (fast_pairs == slow_pairs) and (len(fast_seen) == slow_distinct)
    print()
    print(f"  VERIFICATION on {take:,} clusters (seed {SEED}): sparse "
          f"({fast_pairs:,} pairs, {len(fast_seen):,} distinct) vs brute "
          f"({slow_pairs:,}, {slow_distinct:,}) -> {'IDENTICAL' if agree else 'MISMATCH'}")

    (args.out / "candidates_census.json").write_text(json.dumps({
        "cover": args.cover, "min_size": MIN_SIZE, "runs": args.runs,
        "clusters": int(len(sizes)),
        "qualifying_pairs": pairs, "distinct_candidates": len(seen),
        "pairs_by_band": by_band, "candidates_by_band": dict(cand_bands),
        "verification": {"sample": int(take), "seed": SEED,
                         "sparse_pairs": fast_pairs, "brute_pairs": slow_pairs,
                         "sparse_distinct": len(fast_seen), "brute_distinct": slow_distinct,
                         "identical": bool(agree)},
        "scramble_trees_cached": False,
    }, indent=1) + "\n", encoding="utf-8")
    members = list(seen.values())
    ptr = np.zeros(len(members) + 1, dtype=np.int64)
    np.cumsum([len(m) for m in members], out=ptr[1:])
    np.savez_compressed(args.out / "candidates.npz",
                        flat=np.concatenate(members).astype(np.int32), indptr=ptr)
    print(f"  -> {args.out / 'candidates.npz'}  ({len(members):,} candidates)")
    if len(seen) > 5_000_000:
        print("\n  OVER THE DECLARED BOUND of 5,000,000 distinct candidates: stopping after the")
        print("  counts, as the prompt directs.")
    print(f"  -> {args.out / 'candidates_census.json'}")
    return 0 if agree else 2


def score_all(flat: np.ndarray, indptr: np.ndarray, got: dict, args: argparse.Namespace,
              cover: float, chunk: int = 150_000) -> dict[str, np.ndarray]:
    """Step 3: judge and find every candidate in every run.

    **The test is restated so it needs no ancestor walk.** The LCA of a candidate's drawn pathways
    is the *smallest* cluster containing them, so it maximises ``|drawn| / |C|`` over every cluster
    that contains them. Hence

        ``|drawn| >= cover * |LCA|``  iff  ``some cluster C has drawn <= C and
                                             |drawn| >= cover * |C|``

    and the existential form is one sparse product per run. Walking each candidate's chain instead
    would be 1.8e8 Python iterations.

    The per-run restriction to drawn pathways is built **vectorised** -- a mask over the flat member
    array plus a ``reduceat`` -- for the same reason: looping over candidates to build each run's
    matrix would itself be 1.9e8 iterations.

    Args:
        flat: Concatenated member indices of every candidate.
        indptr: Segment boundaries into ``flat``.
        got: The cluster material.
        args: Parsed arguments.
        cover: The share of the enclosing cluster a core must make up.
        chunk: Candidate rows per sparse product.

    Returns:
        ``{judged, found, support}`` per candidate.
    """
    from scipy import sparse

    from cut_trees import load_run
    from thema.ontology import bitset as bits
    from thema.ontology.v04 import NO_CAP

    n = got["n"]
    meta = got["meta"]
    root = (args.trees if getattr(args, "trees", None)
            else args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}")
    total = len(indptr) - 1
    judged = np.zeros(total, dtype=np.int32)
    found = np.zeros(total, dtype=np.int32)
    clock = time.perf_counter()
    for r in range(1, args.runs + 1):
        run = load_run(root / f"row{r:05d}.npz", n, NO_CAP)
        drawn = np.zeros(n, dtype=bool)
        drawn[np.fromiter(bits.unpack(np.asarray(run.present)), dtype=np.int64)] = True
        sel = np.flatnonzero(np.asarray(run.sizes) >= MIN_SIZE)
        c_sizes = np.asarray(run.sizes)[sel].astype(np.int64)
        c_t = to_csr(np.asarray(run.clusters)[sel], n).T.tocsc()

        alive = drawn[flat]
        counts = np.add.reduceat(alive.astype(np.int64), indptr[:-1])
        ptr = np.zeros(total + 1, dtype=np.int64)
        np.cumsum(counts, out=ptr[1:])
        kept = flat[alive]
        csr = sparse.csr_matrix(
            (np.ones(len(kept), dtype=np.int32), kept, ptr), shape=(total, n), dtype=np.int32)
        judged += (counts >= MIN_SIZE).astype(np.int32)
        rows = np.flatnonzero(counts >= MIN_SIZE)
        for start in range(0, len(rows), chunk):
            part = rows[start:start + chunk]
            block = (csr[part] @ c_t).tocoo()
            if not len(block.data):
                continue
            need = counts[part][block.row]
            hit = (block.data.astype(np.int64) == need) & (
                need * 100 >= int(cover * 100) * c_sizes[block.col])
            if hit.any():
                found[part[np.unique(block.row[hit])]] += 1
        if r % 20 == 0:
            print(f"      run {r}/{args.runs}  ({time.perf_counter() - clock:.0f}s)", flush=True)
    support = np.where(judged > 0, found / np.maximum(judged, 1), 0.0)
    return {"judged": judged, "found": found, "support": support}


#: Runs-found buckets the report uses.
RUN_BUCKETS: tuple[tuple[int, int, str], ...] = (
    (2, 2, "2"), (3, 4, "3-4"), (5, 9, "5-9"), (10, 19, "10-19"),
    (20, 49, "20-49"), (50, 10**9, "50+"),
)


def step_three(args: argparse.Namespace) -> int:
    """Score every cached candidate and report the support distribution.

    Args:
        args: Parsed arguments.

    Returns:
        0, or 2 if the by-construction invariant fails.
    """
    with np.load(args.out / "candidates.npz") as handle:
        flat, indptr = handle["flat"], handle["indptr"]
    sizes = np.diff(indptr)
    print("PROMPT 59 ARM K, STEP 3: judge and find every candidate in all 200 runs.")
    print(f"  {len(sizes):,} candidates, {len(flat):,} member slots")
    got = load_clusters(args)
    scored = score_all(flat, indptr, got, args, args.cover)
    judged, found, support = scored["judged"], scored["found"], scored["support"]

    # Every candidate is C1 & C2 with |K| >= 0.7|C1| and >= 0.7|C2|, and K is wholly drawn in both
    # of those runs, so the LCA there is inside C1 (or C2) and at least 70% covered. Finding fewer
    # than two runs would mean the test and the candidate rule disagree.
    floor_two = int((found >= 2).sum())
    print(f"\n  found in at least 2 runs: {floor_two:,} of {len(sizes):,} "
          f"= {floor_two / len(sizes):.2%}")
    print("  BY CONSTRUCTION this must be every candidate: K is wholly drawn in each of its two")
    print("  originating runs and its LCA there sits in a cluster it covers at "
          f">= {args.cover:.0%}. So the")
    print("  2-run placeholder retains everything and CANNOT be used as a cutoff.")
    if floor_two != len(sizes):
        print(f"  INVARIANT FAILED: {len(sizes) - floor_two:,} candidates found in fewer than 2")
        return 2

    print()
    print("=" * 104)
    print("B. RUNS FOUND, BY BAND")
    print("=" * 104)
    header = f"  {'band':<12}{'candidates':>12}"
    for _lo, _hi, name in RUN_BUCKETS:
        header += f"{name:>10}"
    print(header + f"{'med runs':>10}{'med support':>13}")
    rows_out = []
    for _lo, _hi, band in BANDS:
        rows = np.flatnonzero(np.array([band_of(int(s)) for s in sizes]) == band)
        if not len(rows):
            continue
        line = f"  {band:<12}{len(rows):>12,}"
        cells = {}
        for low, high, name in RUN_BUCKETS:
            count = int(((found[rows] >= low) & (found[rows] <= high)).sum())
            cells[name] = count
            line += f"{count:>10,}"
        med_runs = float(np.median(found[rows]))
        med_sup = float(np.median(support[rows]))
        rows_out.append({"band": band, "candidates": int(len(rows)), "buckets": cells,
                         "median_runs": med_runs, "median_support": med_sup,
                         "median_judged": float(np.median(judged[rows]))})
        print(line + f"{med_runs:>10.0f}{med_sup:>13.4f}")
    line = f"  {'ALL':<12}{len(sizes):>12,}"
    for low, high, _name in RUN_BUCKETS:
        line += f"{int(((found >= low) & (found <= high)).sum()):>10,}"
    print(line + f"{float(np.median(found)):>10.0f}{float(np.median(support)):>13.4f}")
    print()
    print(f"  {'band':<12}{'>=0.05':>10}{'>=0.10':>10}{'>=0.33':>10}{'med judged':>12}")
    for record in rows_out:
        rows = np.flatnonzero(np.array([band_of(int(s)) for s in sizes]) == record["band"])
        line = f"  {record['band']:<12}"
        for threshold in (0.05, 0.10, 0.33):
            share = float((support[rows] >= threshold).mean())
            line += f"{share:>10.1%}"
        print(line + f"{record['median_judged']:>12.0f}")

    np.savez_compressed(args.out / "scored.npz", judged=judged, found=found, support=support,
                        sizes=sizes)
    (args.out / "step3.json").write_text(json.dumps({
        "candidates": int(len(sizes)), "found_at_least_2": floor_two,
        "by_band": rows_out,
        "median_runs_overall": float(np.median(found)),
        "median_support_overall": float(np.median(support)),
        "note": ("every candidate is found in at least 2 runs by construction, so the 2-run "
                 "placeholder retains all of them and is not usable as a cutoff"),
    }, indent=1) + "\n", encoding="utf-8")
    print(f"\n  -> {args.out / 'scored.npz'} and step3.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
