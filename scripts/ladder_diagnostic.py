#!/usr/bin/env python3
"""Where does the RUNS ladder's failure sit -- in the noise tail, or in the structure we keep?

**POST HOC. Run after the declared ladder measurement had already FAILED, and it cannot turn that
failure into a pass.** The declared question was "what share of groupings in one block of runs has a
Jaccard >= 0.70 partner in a disjoint block", with a pass mark of 90% fixed before the run. That
measurement is the record. This script does not re-ask it and does not change its threshold.

What it adds is *where* the unmatched groupings are. Every grouping a Ward tree records at or above
`min_size` enters the pool, including the thousands of three- and four-member clusters a single
subsample throws up and no other run reproduces. Those are exactly what the support gate exists to
remove, and they are counted in the declared share. So the share is broken out by the grouping's own
support and by its size, using the SAME sample, seed and threshold -- no new parameter.

Read it as a diagnosis of the failure, not as an alternative to it.

Usage::

    uv run scripts/ladder_diagnostic.py --pair 1
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from cut_trees import CAP_SHARE, MIN_SIZE, SAMPLE, SAMPLE_SEED, THETA, TOL, cap_for, load_run
from thema.ontology.recurrent import DEFAULTS, prepare, score

#: The pairs the subsample manifest reserves, in the declared order.
PAIRS: tuple[tuple[tuple[int, int], tuple[int, int]], ...] = (
    ((1, 100), (101, 200)),
    ((1, 200), (201, 400)),
)

#: Support bands the matched share is broken out over. The declared m, 0.33, is one of the edges so
#: the gate's own cut is visible; the bands are otherwise plain deciles and are not tuned.
BANDS: tuple[tuple[float, float], ...] = (
    (0.0, 0.1), (0.1, 0.2), (0.2, 0.33), (0.33, 0.5), (0.5, 0.75), (0.75, 1.01),
)

#: Size bands, matching the floor strata of the build.
SIZES: tuple[tuple[int, int], ...] = ((3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (10, 10**9))


def pool_of(trees: Path, low: int, high: int, n: int, cap: int) -> tuple[np.ndarray, np.ndarray]:
    """Cut a block of runs and return its eligible groupings with their support.

    Args:
        trees: The tree directory.
        low: First run, 1-based inclusive.
        high: Last run, inclusive.
        n: Universe size.
        cap: Size cap.

    Returns:
        ``(g, words)`` grouping bitsets and their support, in the same order.
    """
    runs = [load_run(trees / f"row{r:05d}.npz", n, cap) for r in range(low, high + 1)]
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE, "theta": THETA}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)
    keep = ~np.isnan(pool.support)
    return ready.groupings[keep], pool.support[keep]


def best_jaccard(left: np.ndarray, right: np.ndarray, picked: np.ndarray) -> np.ndarray:
    """Best Jaccard against the whole right-hand pool, for each picked left grouping.

    Args:
        left: ``(a, words)`` grouping bitsets.
        right: ``(b, words)`` grouping bitsets.
        picked: Indices into ``left``.

    Returns:
        One best Jaccard per picked grouping.
    """
    sizes_right = np.bitwise_count(right).sum(axis=1).astype(np.int64)
    out = np.zeros(len(picked))
    for position, index in enumerate(picked):
        block = left[index]
        size = int(np.bitwise_count(block).sum())
        inter = np.bitwise_count(right & block).sum(axis=1).astype(np.int64)
        union = size + sizes_right - inter
        out[position] = np.max(np.where(union > 0, inter / np.maximum(union, 1), 0.0))
    return out


def main(argv: list[str] | None = None) -> int:
    """Break the failed ladder share out by support and by size.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--pair", type=int, default=1, choices=(1, 2))
    parser.add_argument("--trees", type=Path, default=None,
                        help="a tree directory to read instead of the versioned one, for the "
                             "1,850 control; --n must be given with it")
    parser.add_argument("--n", type=int, default=0, help="universe size, with --trees")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe = meta["universe_digest"]
    if args.trees is not None:
        if not args.n:
            parser.error("--trees requires --n")
        trees, n = args.trees, args.n
    else:
        n = meta["n_embedded"]
        trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    (al, ah), (bl, bh) = PAIRS[args.pair - 1]
    print(f"DIAGNOSTIC (post hoc)  {al}-{ah} vs {bl}-{bh}, {n:,} pathways, {args.space}, "
          f"cap {CAP_SHARE:.4%} = {cap:,}, theta {THETA}", flush=True)

    clock = time.perf_counter()
    left, support = pool_of(trees, al, ah, n, cap)
    right, _rsupport = pool_of(trees, bl, bh, n, cap)
    print(f"  pools: {len(left):,} vs {len(right):,} eligible groupings "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)

    rng = np.random.default_rng(SAMPLE_SEED)
    picked = (rng.choice(len(left), size=SAMPLE, replace=False) if SAMPLE < len(left)
              else np.arange(len(left)))
    clock = time.perf_counter()
    best = best_jaccard(left, right, picked)
    sizes = np.bitwise_count(left[picked]).sum(axis=1).astype(np.int64)
    sup = support[picked]
    matched = best >= THETA
    print(f"  sampled {len(picked):,} of the left pool, each against all {len(right):,} "
          f"({time.perf_counter() - clock:.0f}s)")
    print(f"  OVERALL matched {matched.mean():.1%} -- the declared figure, FAILED at 90%\n")

    print("  BY THE GROUPING'S OWN SUPPORT")
    print(f"  {'support':<12} {'sampled':>8} {'share of pool':>14} {'matched':>9} "
          f"{'median best J':>14}")
    for low, high in BANDS:
        mask = (sup >= low) & (sup < high)
        if not mask.any():
            continue
        print(f"  {f'{low:.2f}-{high:.2f}':<12} {int(mask.sum()):>8,} "
              f"{mask.mean():>13.1%} {matched[mask].mean():>9.1%} "
              f"{np.median(best[mask]):>14.3f}")
    gate = sup >= 0.33
    print(f"\n  at or above the declared m = 0.33: {int(gate.sum()):,} of {len(picked):,} "
          f"sampled ({gate.mean():.1%}), matched {matched[gate].mean():.1%}"
          if gate.any() else "\n  nothing sampled at or above m = 0.33")

    print("\n  BY SIZE")
    print(f"  {'members':<10} {'sampled':>8} {'share of pool':>14} {'matched':>9} "
          f"{'median support':>15}")
    for low, high in SIZES:
        mask = (sizes >= low) & (sizes <= high)
        if not mask.any():
            continue
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        print(f"  {label:<10} {int(mask.sum()):>8,} {mask.mean():>13.1%} "
              f"{matched[mask].mean():>9.1%} {np.median(sup[mask]):>15.3f}")

    out = trees.parent / f"ladder_diagnostic_n{n}_pair{args.pair}.json"
    out.write_text(json.dumps({
        "post_hoc": True,
        "declared_measurement_failed": True,
        "note": "Breaks the FAILED declared share out by support and size. Not a re-measurement.",
        "space": args.space, "universe_digest": universe, "n": n,
        "cap_share": CAP_SHARE, "cap": cap, "theta": THETA, "tol": TOL, "min_size": MIN_SIZE,
        "left": f"{al}-{ah}", "right": f"{bl}-{bh}",
        "n_left": int(len(left)), "n_right": int(len(right)),
        "sample": int(len(picked)), "sample_seed": SAMPLE_SEED,
        "overall_matched": round(float(matched.mean()), 4),
        "by_support": [
            {"band": f"{low:.2f}-{high:.2f}",
             "sampled": int(((sup >= low) & (sup < high)).sum()),
             "matched": (round(float(matched[(sup >= low) & (sup < high)].mean()), 4)
                         if ((sup >= low) & (sup < high)).any() else None)}
            for low, high in BANDS
        ],
        "by_size": [
            {"band": f"{low}-{high}" if high < 10**9 else f"{low}+",
             "sampled": int(((sizes >= low) & (sizes <= high)).sum()),
             "matched": (round(float(matched[(sizes >= low) & (sizes <= high)].mean()), 4)
                         if ((sizes >= low) & (sizes <= high)).any() else None)}
            for low, high in SIZES
        ],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\n  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
