#!/usr/bin/env python3
"""Test R stage 2: the candidate pool and gap scores for ONE side.

EXPLORATORY -- Test R. Run per side so memory stays bounded and sides can be done one at a time.

`G_loo` needs only the trees, but `h_full` is defined over "runs where g is found", which is the
matching's verdict and is not cached: the completion caches hold member bitsets and support, not
which run found what. So the pool is recomputed with the build's own `prepare` and `score`, and the
matched copy in each run is mapped back to its full-dendrogram node -- exactly, because the
recording rule is reproducible and `load_run`'s cap filter is too.

Usage::

    uv run scripts/test_r_pool.py --side real
    uv run scripts/test_r_pool.py --side 3001
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Sizes the gap score is defined on, and the support floor the fixed cut uses.
MIN_SIZE, MAX_SIZE = 3, 9
SUPPORT_CUT = 0.33


def main(argv: list[str] | None = None) -> int:
    """Score one side.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from cut_trees import MIN_SIZE as RUN_MIN_SIZE
    from cut_trees import THETA, TOL, cap_for, load_run
    from thema.cluster import distances
    from thema.embed import centre_and_renormalise
    from thema.ontology import bitset as bits
    from thema.ontology import gap
    from thema.ontology.recurrent import DEFAULTS, null_embeddings, prepare, score
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--side", required=True, help="real, or a scramble seed like 3001")
    parser.add_argument("--all-sizes", action="store_true",
                        help="score every size, not just 3-9. Report item 5 needs this")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    n, universe = meta["n_embedded"], meta["universe_digest"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    seed = None if args.side == "real" else int(args.side)
    label = (lambda r: f"row{r:05d}") if seed is None else (
        lambda r, s=seed: f"seed{s:05d}_row{r:05d}")
    hi = 10**9 if args.all_sizes else MAX_SIZE
    out = args.out or (trees / "heights" / f"scores_{args.side}_n{args.runs:03d}"
                       f"{'_all' if args.all_sizes else ''}.npz")
    if out.is_file():
        print(f"  {out} exists; not overwritten")
        return 0

    clock = time.perf_counter()
    runs = [load_run(trees / f"{label(r)}.npz", n, cap) for r in range(1, args.runs + 1)]
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": RUN_MIN_SIZE,
                "theta": THETA, "families": "joined"}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)
    pool_time = time.perf_counter() - clock
    print(f"TEST R stage 2  side {args.side}: pool {len(pool.groupings):,} groupings "
          f"in {pool_time:.0f}s, peak {peak_mb():.0f} MB", flush=True)

    sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int64)
    support = np.nan_to_num(pool.support, nan=-1.0)
    wanted = np.flatnonzero((sizes >= MIN_SIZE) & (sizes <= hi) & (support >= SUPPORT_CUT))
    print(f"  size {MIN_SIZE}-{'inf' if args.all_sizes else hi} and support >= {SUPPORT_CUT}: "
          f"{len(wanted):,} groupings", flush=True)

    # Rebuild each run's dendrogram and map its capped recorded clusters back to nodes.
    embedded = load_embedded(root, args.data / "pathways.tsv")
    base, _m = centre_and_renormalise(embedded.vectors)
    base = np.ascontiguousarray(base.astype(np.float32))
    matrix = base if seed is None else np.ascontiguousarray(
        null_embeddings(base, seed).astype(np.float32))
    full = distances(matrix)
    indices = np.load(root / "subsamples" / "indices.npy")

    clock = time.perf_counter()
    dendros: list[gap.Dendrogram] = []
    node_of_copy: list[dict[bytes, int]] = []
    for r in range(1, args.runs + 1):
        subset = np.sort(indices[r - 1])
        tree = gap.build(matrix, n, subset, full=full)
        with np.load(trees / f"{label(r)}.npz") as handle:
            stored = handle["clusters"]
            stored_sizes = handle["sizes"]
        if not np.array_equal(tree.nodes[tree.recorded], stored):
            print(f"  STOP: {label(r)} differs from the persisted tree", flush=True)
            return 1
        keep = np.flatnonzero(stored_sizes <= cap)
        dendros.append(tree)
        node_of_copy.append({
            tree.nodes[tree.recorded[j]].tobytes(): int(tree.recorded[j]) for j in keep.tolist()
        })
    del full
    print(f"  {args.runs} dendrograms rebuilt and asserted in "
          f"{time.perf_counter() - clock:.0f}s, peak {peak_mb():.0f} MB", flush=True)

    clock = time.perf_counter()
    members = [np.asarray(bits.unpack(pool.groupings[g]), dtype=np.int64) for g in wanted.tolist()]
    packed = pool.groupings[wanted]
    found: list[dict[int, int]] = []
    for g in wanted.tolist():
        hits: dict[int, int] = {}
        for run, copy in pool.copies[g].items():
            node = node_of_copy[run].get(copy.tobytes())
            if node is not None:
                hits[run] = node
        found.append(hits)
    scored = gap.score_side(dendros, members, packed, found, n)
    print(f"  scored in {time.perf_counter() - clock:.0f}s, peak {peak_mb():.0f} MB", flush=True)

    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out, groupings=packed, sizes=sizes[wanted], support=support[wanted],
        h_full=scored["h_full"], g_loo=scored["g_loo"], g_life=scored["g_life"],
        loo_runs=scored["loo_runs"], pool_total=np.array([len(pool.groupings)]),
        pool_seconds=np.array([pool_time]),
    )
    finite = int(np.isfinite(scored["g_loo"]).sum())
    print(f"  G_loo finite for {finite:,} of {len(wanted):,}; "
          f"median loo_runs {int(np.median(scored['loo_runs']))}", flush=True)
    print(f"  -> {out}  peak {peak_mb():.0f} MB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
