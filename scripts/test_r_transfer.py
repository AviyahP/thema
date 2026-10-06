#!/usr/bin/env python3
"""Test R transfer: apply the 10,770 thresholds unchanged to a new universe. EXPLORATORY.

Spec: `docs/spec/test-R-2026-10-07.md`, the "Transfer: the speed question" section. The point Aviyah
names is the FAIR comparison -- if the **floors** transfer too, calibrate-once is already possible
without any gap score, and the gap score would have to earn its place against that rather than
against per-dataset calibration.

Builds a universe from a subset of the v0.3 rows, recentred and renormalised as the method would do,
draws 200 subsamples under the same 80% rule, builds its own Ward trees with heights, and scores the
real side plus scramble seeds 4001 and 4002. Nothing existing is read for its thresholds except the
numbers passed in on the command line.

Usage::

    uv run scripts/test_r_transfer.py --subset reactome --seeds 4001,4002
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Seed for the new universe's subsample draw. Fixed here so the trees are reproducible.
SUBSAMPLE_SEED = 20261007
SUBSAMPLE = 0.8


def main(argv: list[str] | None = None) -> int:
    """Build and score one transfer setting.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from cut_trees import CAP_SHARE, MIN_SIZE, THETA, TOL
    from thema.cluster import distances
    from thema.embed import centre_and_renormalise
    from thema.ontology import bitset as bits
    from thema.ontology import gap
    from thema.ontology.recurrent import (
        DEFAULTS,
        null_embeddings,
        prepare,
        run_from_candidates,
        score,
        tree_from_subset,
    )
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--subset", default="reactome", help="key prefix, or 'all'")
    parser.add_argument("--vectors", type=Path, default=None,
                        help="alternative embedding matrix over the SAME v0.3 rows")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--seeds", default="4001,4002")
    parser.add_argument("--name", default="")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    raw = embedded.vectors if args.vectors is None else np.load(args.vectors)
    if raw.shape[0] != len(keys):
        print(f"  STOP: {args.vectors} has {raw.shape[0]} rows, the v0.3 universe has {len(keys)}")
        return 1
    rows = (np.arange(len(keys)) if args.subset == "all"
            else np.array([i for i, k in enumerate(keys) if k.startswith(f"{args.subset}:")]))
    n = int(len(rows))
    name = args.name or f"{args.subset}_{n}"
    print(f"TEST R transfer  {name}: {n:,} rows of the v0.3 universe", flush=True)

    base, _mean = centre_and_renormalise(raw[rows])
    base = np.ascontiguousarray(base.astype(np.float32))
    cap = int(round(CAP_SHARE * n))
    take = int(np.ceil(SUBSAMPLE * n))
    rng = np.random.default_rng(SUBSAMPLE_SEED)
    draws = [np.sort(rng.choice(n, size=take, replace=False)) for _ in range(args.runs)]
    print(f"  cap {CAP_SHARE:.4%} = {cap:,}, draw {take:,} of {n:,}, "
          f"{args.runs} subsamples (seed {SUBSAMPLE_SEED})", flush=True)

    sides = ["real"] + [s.strip() for s in args.seeds.split(",") if s.strip()]
    report: dict = {"name": name, "n": n, "cap": cap, "take": take, "runs": args.runs,
                    "subsample_seed": SUBSAMPLE_SEED, "sides": {}}
    out_dir = root / "transfer" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    for side in sides:
        target = out_dir / f"scores_{side}_n{args.runs:03d}.npz"
        if target.is_file():
            print(f"  {side}: already scored, not overwritten", flush=True)
            continue
        seed = None if side == "real" else int(side)
        clock = time.perf_counter()
        matrix = base if seed is None else np.ascontiguousarray(
            null_embeddings(base, seed).astype(np.float32))
        full = distances(matrix)
        runs, dendros, node_of_copy = [], [], []
        for subset in draws:
            built = tree_from_subset(matrix, n, subset, MIN_SIZE, full=full)
            keep = np.flatnonzero(built.sizes <= cap)
            runs.append(run_from_candidates(built.present, built.clusters[keep], n))
            tree = gap.build(matrix, n, subset, full=full)
            if not np.array_equal(tree.nodes[tree.recorded], built.clusters):
                print(f"  STOP: {name} {side} regenerated tree differs", flush=True)
                return 1
            dendros.append(tree)
            node_of_copy.append({
                tree.nodes[tree.recorded[j]].tobytes(): int(tree.recorded[j])
                for j in keep.tolist()
            })
        trees_time = time.perf_counter() - clock
        del full

        clock = time.perf_counter()
        settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE,
                    "theta": THETA, "families": "joined"}
        ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
        pool = score(ready, settings)
        sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int64)
        support = np.nan_to_num(pool.support, nan=-1.0)
        wanted = np.flatnonzero((sizes >= 3) & (sizes <= 9) & (support >= 0.33))
        members = [np.asarray(bits.unpack(pool.groupings[g]), dtype=np.int64)
                   for g in wanted.tolist()]
        found = [
            {run: node_of_copy[run][copy.tobytes()]
             for run, copy in pool.copies[g].items() if copy.tobytes() in node_of_copy[run]}
            for g in wanted.tolist()
        ]
        scored = gap.score_side(dendros, members, pool.groupings[wanted], found, n)
        np.savez_compressed(
            target, groupings=pool.groupings[wanted], sizes=sizes[wanted],
            support=support[wanted], h_full=scored["h_full"], g_loo=scored["g_loo"],
            g_life=scored["g_life"], loo_runs=scored["loo_runs"],
        )
        report["sides"][side] = {
            "pool": int(len(pool.groupings)), "scored": int(len(wanted)),
            "trees_seconds": round(trees_time, 1),
            "pool_seconds": round(time.perf_counter() - clock, 1),
            "peak_mb": round(peak_mb(), 1),
        }
        print(f"  {side}: pool {len(pool.groupings):,}, scored {len(wanted):,}, "
              f"trees {trees_time:.0f}s + pool {time.perf_counter() - clock:.0f}s, "
              f"peak {peak_mb():.0f} MB", flush=True)
        del ready, pool, dendros, node_of_copy, runs

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"  -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
