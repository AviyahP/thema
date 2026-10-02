#!/usr/bin/env python3
"""The RUNS ladder on the 1,850, measured the same way as on the 10,770.

**A CONTROL, run because the 10,770 ladder FAILED.** `docs/status/OPEN.md` records "100 trees per
run: 89.1% of groupings match at >= 0.70. 200 gives 91.4%" from the 1,850 work, and no committed
script produced it (`docs/debt.md`). So when the 10,770 re-confirmation comes back far below that,
there are two possible explanations and they call for opposite decisions:

1. the 10,770 pool genuinely recurs less than the 1,850 pool did -- a finding about scale; or
2. the 89.1% measured a different quantity, and the 90% pass mark never applied to the share of the
   RAW grouping pool at all -- a finding about the pass mark.

This separates them. It runs the identical measurement -- same estimator, same sample size, same
seed, same theta, same tol, same min_size, same centred space, same cap share -- on the 1,850
universe. If the 1,850 also comes back far below 89%, explanation 2 holds.

**Nothing in the frozen 1,850 build is read or written.** The universe vectors are loaded through
the verifying loader and fresh trees are built into a scratch directory; the build's own nodes,
members, names and manifest are untouched.

Usage::

    uv run scripts/ladder_control_1850.py --out /tmp/ladder-control
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from build_trees_10770 import save_run
from cut_trees import (
    CAP_SHARE,
    MIN_SIZE,
    SAMPLE,
    SAMPLE_SEED,
    THETA,
    TOL,
    cap_for,
    jaccard_match,
    load_run,
)
from thema.cluster import distances
from thema.embed import centre_and_renormalise
from thema.ontology.recurrent import DEFAULTS, Run, prepare, score, tree_from_subset
from thema.ontology.universe import load_embedded

#: The subsample scheme of `data/ontology/v0.3/subsamples/manifest.json`, applied at this n. Same
#: master seed and same draw call, so the only difference from the 10,770 ladder is the universe.
MASTER_SEED = 20260925
SUBSAMPLE = 0.8
ROWS = 400

#: The pairs, as declared.
PAIRS: tuple[tuple[tuple[int, int], tuple[int, int]], ...] = (
    ((1, 100), (101, 200)),
    ((1, 200), (201, 400)),
)


def draw(n: int, rows: int) -> list[np.ndarray]:
    """Draw the subsample sequence, by the manifest's scheme.

    Args:
        n: Universe size.
        rows: How many rows.

    Returns:
        One sorted index array per row.
    """
    take = int(np.ceil(SUBSAMPLE * n))
    rng = np.random.default_rng(MASTER_SEED)
    return [np.sort(rng.choice(n, size=take, replace=False)) for _ in range(rows)]


def main(argv: list[str] | None = None) -> int:
    """Run the control.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.2", help="the 1,850 universe")
    parser.add_argument("--out", type=Path, required=True,
                        help="scratch directory for the result; no build directory is written")
    parser.add_argument("--pass-mark", type=float, default=0.90)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    n = len(embedded.keys)
    matrix, _mean = centre_and_renormalise(embedded.vectors)
    matrix = np.ascontiguousarray(matrix.astype(np.float32))
    cap = cap_for(n)
    print(f"CONTROL  the same ladder on {n:,} pathways, centred, cap {CAP_SHARE:.4%} = {cap:,}, "
          f"theta {THETA}, tol {TOL}, min_size {MIN_SIZE}", flush=True)

    clock = time.perf_counter()
    full = distances(matrix)
    rows = draw(n, ROWS)
    # The trees are written to the scratch directory and read back through `cut_trees.load_run`,
    # the SAME function the 10,770 ladder uses, rather than capped in memory here. A second,
    # in-memory capping path was written first and was wrong: it dropped clusters without
    # renumbering `leaf_cluster` and the ancestor chains, which point at cluster INDICES, so the
    # matching loop would have climbed the wrong chain on every tree where the cap bound.
    trees = args.out / "trees"
    binding = 0
    for row, subset in enumerate(rows, 1):
        path = trees / f"row{row:05d}.npz"
        if path.is_file():
            continue
        run = tree_from_subset(matrix, n, subset, MIN_SIZE, "ward", full)
        binding += bool((run.sizes > cap).any())
        save_run(path, run)
    print(f"  {ROWS} trees in {time.perf_counter() - clock:.0f}s; "
          f"{binding} of them have a cluster over the cap", flush=True)

    cache: dict[int, Run] = {}

    def pool_for(low: int, high: int) -> np.ndarray:
        runs = []
        for row in range(low, high + 1):
            if row not in cache:
                cache[row] = load_run(trees / f"row{row:05d}.npz", n, cap)
            runs.append(cache[row])
        settings = {**DEFAULTS, "runs": len(runs), "tol": TOL,
                    "min_size": MIN_SIZE, "theta": THETA}
        ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
        pool = score(ready, settings)
        return ready.groupings[~np.isnan(pool.support)]

    results = []
    for (al, ah), (bl, bh) in PAIRS:
        start = time.perf_counter()
        left, right = pool_for(al, ah), pool_for(bl, bh)
        forward, fe, fn = jaccard_match(left, right, THETA)
        backward, be, bn = jaccard_match(right, left, THETA)
        both = min(forward, backward)
        results.append({
            "left": f"{al}-{ah}", "right": f"{bl}-{bh}",
            "n_left": int(len(left)), "n_right": int(len(right)),
            "forward": round(forward, 4), "forward_se": round(fe, 5), "forward_n": fn,
            "backward": round(backward, 4), "backward_se": round(be, 5), "backward_n": bn,
            "worse_direction": round(both, 4),
            "seconds": round(time.perf_counter() - start, 1),
        })
        print(f"  {al}-{ah} vs {bl}-{bh}: {len(left):,} vs {len(right):,} groupings, "
              f"{fn:,} sampled per direction")
        print(f"      forward {forward:.1%} +/- {fe:.2%}   backward {backward:.1%} "
              f"+/- {be:.2%}   worse {both:.1%}   "
              f"{'PASS' if both >= args.pass_mark else 'FAIL'} vs {args.pass_mark:.0%}   "
              f"({time.perf_counter() - start:.0f}s)", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / "ladder_control_1850.json"
    out.write_text(json.dumps({
        "control_for": "the FAILED 10,770 RUNS re-confirmation",
        "touches_frozen_build": False,
        "n": n, "space": "centred", "cap_share": CAP_SHARE, "cap": cap,
        "theta": THETA, "tol": TOL, "min_size": MIN_SIZE,
        "master_seed": MASTER_SEED, "subsample": SUBSAMPLE, "rows": ROWS,
        "sample": SAMPLE, "sample_seed": SAMPLE_SEED,
        "trees_with_a_cluster_over_the_cap": binding,
        "pass_mark": args.pass_mark, "pairs": results,
        "recorded_1850_claim": "OPEN.md: 100 trees 89.1%, 200 trees 91.4% -- space and cutoff "
                               "unrecorded, no script, see docs/debt.md",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\n  -> {out}")
    worst = min(r["worse_direction"] for r in results)
    print(f"  worst direction on the 1,850: {worst:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
