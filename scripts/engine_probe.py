#!/usr/bin/env python3
"""Per-run candidate generation cost and pool size for each engine. BUDGETING ONLY.

A side is 200 runs through candidate generation, matching, completion and seed absorption, and
matching dominates. What matching costs is driven by how many candidates the runs propose, so this
measures exactly that -- per-run wall time and candidate count -- on a handful of runs, before any
arm is committed to a full side. It decides nothing: §0's gates and scores decide.

Usage::

    uv run scripts/engine_probe.py --engine leiden --runs 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


def main(argv: list[str] | None = None) -> int:
    """Probe one engine's per-run cost.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import INCLUSION_CUT, engine_resolutions, engine_vectors
    from build_trees_10770 import peak_mb
    from cut_trees import ENGINES, cap_for, load_engine_run, load_run

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--engine", choices=ENGINES, required=True)
    parser.add_argument("--runs", type=int, default=3, help="how many runs to time")
    parser.add_argument("--seed", type=int, default=0,
                        help="scramble seed to probe instead of the real side; 0 means real")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    seed = args.seed or None

    clock = time.perf_counter()
    cache: dict[tuple[str, int | None], np.ndarray] = {}
    vectors = engine_vectors(root, args.data, args.space, args.engine, seed, cache)
    setup = time.perf_counter() - clock
    resolutions = (engine_resolutions()
                   if args.engine in ("leiden", "leiden_persistent", "pooled")
                   else None)

    print(f"PROBE  engine {args.engine}, {'real' if seed is None else f'scramble {seed}'} side, "
          f"{args.runs} runs, n={n:,}, cap {cap:,}, inclusion {INCLUSION_CUT}", flush=True)
    print(f"  vector setup: {setup:.1f}s  (fitted/loaded once per side, not per run)", flush=True)

    times, counts, sizes = [], [], []
    for index in range(1, args.runs + 1):
        label = f"row{index:05d}" if seed is None else f"seed{seed:05d}_row{index:05d}"
        path = trees / f"{label}.npz"
        clock = time.perf_counter()
        if args.engine == "ward":
            run = load_run(path, n, cap)
        else:
            run = load_engine_run(path, n, cap, args.engine, vectors,
                                  run_index=index, resolutions=resolutions)
        elapsed = time.perf_counter() - clock
        times.append(elapsed)
        counts.append(int(run.clusters.shape[0]))
        sizes.extend(run.sizes.tolist())
        extra = "" if resolutions is None else f", ladder of {len(resolutions)}"
        print(f"  run {index:>3}: {elapsed:7.2f}s  {counts[-1]:>7,} candidates{extra}", flush=True)

    per_run = float(np.mean(times))
    mean_candidates = float(np.mean(counts))
    arr = np.asarray(sizes, dtype=np.int64)
    print(f"\n  per run: {per_run:.2f}s, {mean_candidates:,.0f} candidates")
    print(f"  candidate sizes: median {int(np.median(arr))}, "
          f"mean {arr.mean():.0f}, max {int(arr.max()) if len(arr) else 0}")
    for lo, hi in ((3, 10), (11, 50), (51, 200), (201, 500), (501, 3125)):
        share = float(np.mean((arr >= lo) & (arr <= hi))) if len(arr) else 0.0
        print(f"    {lo:>4}-{hi:<5} {share:6.1%}")
    print(f"  200-run candidate generation: {per_run * 200 / 60:.1f} min, "
          f"pool before dedup {mean_candidates * 200:,.0f}")
    print(f"  peak {peak_mb():.0f} MB", flush=True)

    report = {
        "engine": args.engine, "side": "real" if seed is None else f"seed{seed}",
        "runs_probed": args.runs, "setup_seconds": round(setup, 2),
        "per_run_seconds": round(per_run, 3),
        "mean_candidates": round(mean_candidates, 1),
        "candidates_200_runs": int(round(mean_candidates * 200)),
        "generation_200_runs_seconds": round(per_run * 200, 1),
        "size_median": int(np.median(arr)) if len(arr) else 0,
        "size_max": int(arr.max()) if len(arr) else 0,
        "peak_mb": round(peak_mb(), 1),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
