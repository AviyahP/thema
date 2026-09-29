#!/usr/bin/env python3
"""How many scrambles does a support floor need? Measured, not assumed.

A floor is solved from counts: the smallest support where mean scrambled families over real ones
falls to the target. With few scrambles that mean is a noisy estimate, so the floor wobbles. This
measures the wobble as a function of how many scrambles the solve is given, by resampling the
calibration sides that :mod:`calibrate_inclusion` has already cached -- no clustering is re-run.

Two quantities are reported per stratum, and the second is the one that matters:

- **floor spread** -- the interquartile range of the solved floor across resamples of size ``k``.
  Interpretable but not actionable; a floor can move a lot in a region where no family sits.
- **retained-theme spread** -- how many real families the resulting threshold admits. This is what a
  build actually inherits, and ``docs/spec/addendum-2026-09-21.md`` already declares the branch:
  *leave-one-out retained-theme counts spanning more than 20% means the estimate is unstable and the
  band is dropped*. That criterion is applied here rather than invented.

Usage::

    uv run scripts/floor_stability.py --inclusion 0.50
    uv run scripts/floor_stability.py --inclusion 0.50 --project 10770
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections.abc import Sequence
from pathlib import Path

import numpy as np

CACHE = Path("data/experiments/scramble_sides")

#: Strata, matching scripts/calibrate_inclusion.py. Not re-derived here.
STRATA: tuple[tuple[int, int], ...] = ((3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (10, 10**9))

#: The declared instability branch: leave-one-out retained counts spanning more than this share of
#: the median means the band is dropped. From addendum-2026-09-21, not chosen here.
LOO_SPAN_LIMIT = 0.20

DECLARED_M = 0.33

#: Resamples per size. Enough that the reported quartiles are themselves stable.
DRAWS = 200


def stratum_of(size: int) -> int:
    """Index of the stratum a family of this size falls in.

    Args:
        size: Completed family size.

    Returns:
        Index into :data:`STRATA`.

    Raises:
        ValueError: If no stratum covers the size.
    """
    for index, (low, high) in enumerate(STRATA):
        if low <= size <= high:
            return index
    raise ValueError(f"no stratum covers size {size}")


def load(space: str, universe: str, seeds: Sequence[int], cutoff: float) -> list[list]:
    """Read cached family rows for the given seeds at one cutoff.

    Args:
        space: Clustering space.
        universe: Universe digest, the cache subdirectory suffix.
        seeds: Scramble seeds.
        cutoff: Inclusion cutoff.

    Returns:
        One list of ``(size, support)`` per seed.

    Raises:
        FileNotFoundError: If a side is not cached. It refuses rather than silently using fewer.
    """
    out = []
    for seed in seeds:
        path = CACHE / f"{space}_{universe}" / f"seed{seed:05d}.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"{path} -- run scripts/calibrate_inclusion.py first"
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        key = f"{cutoff:g}"
        if key not in raw:
            raise FileNotFoundError(f"{path} holds no cutoff {key}")
        out.append([(int(a), float(b)) for a, b in raw[key]])
    return out


def by_stratum(rows: list, index: int) -> np.ndarray:
    """The supports of one stratum's families, sorted ascending.

    Args:
        rows: A side's ``(size, support)`` rows.
        index: Stratum index.

    Returns:
        Sorted supports, for ``searchsorted``.
    """
    return np.sort(np.array([s for size, s in rows if stratum_of(size) == index], dtype=float))


def solve_one(
    real: np.ndarray, nulls: Sequence[np.ndarray], max_fdr: float
) -> tuple[float | None, int]:
    """Solve one stratum's floor, and report how many real families it admits.

    Counting is vectorised: every side is a sorted array, so the number at or above a candidate
    is a ``searchsorted``. The naive form rescanned every side per candidate and made the resampling
    study intractable at the 10+ stratum, which holds 17,478 real families.

    Args:
        real: The real side's supports for this stratum, sorted.
        nulls: One sorted array per calibration scramble.
        max_fdr: The FDR the stratum must meet.

    Returns:
        ``(floor, retained)``. ``floor`` is ``None`` when no candidate meets the target.
    """
    if not len(real):
        return None, 0
    candidates = np.unique(np.concatenate(nulls)) if any(len(a) for a in nulls) else None
    if candidates is None:
        return 0.0, int(len(real) - np.searchsorted(real, DECLARED_M, side="left"))
    # mean scrambled count at or above each candidate, and real count at or above each
    f = np.zeros(len(candidates))
    for arr in nulls:
        f += len(arr) - np.searchsorted(arr, candidates, side="left")
    f /= max(len(nulls), 1)
    keep = len(real) - np.searchsorted(real, candidates, side="left")
    ok = (keep > 0) & (f <= max_fdr * keep)
    if not ok.any():
        return None, 0
    floor = float(candidates[int(np.argmax(ok))])
    effective = max(DECLARED_M, floor)
    return floor, int(len(real) - np.searchsorted(real, effective, side="left"))


def main(argv: list[str] | None = None) -> int:
    """Report floor stability against the number of scrambles.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", default="centred")
    parser.add_argument("--inclusion", type=float, default=0.50)
    parser.add_argument("--max-fdr", type=float, default=0.01)
    parser.add_argument(
        "--calibration-seeds", type=int, nargs="+",
        default=[*range(1, 21), *range(1000, 1020)],
    )
    # 39 is LEAVE-ONE-OUT, which is the criterion the addendum actually declares. k equal to the
    # number of cached sides is deliberately absent: there is one way to draw n from n, so its
    # spread is zero by construction and reporting it as stability would be circular.
    parser.add_argument("--sizes", type=int, nargs="+", default=[5, 10, 20, 30, 39])
    parser.add_argument("--draws", type=int, default=DRAWS)
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument(
        "--project", type=int, default=0,
        help="project the requirement to a universe of this many pathways",
    )
    args = parser.parse_args(argv)

    universes = sorted(p.name for p in CACHE.glob(f"{args.space}_*")) if CACHE.is_dir() else []
    if not universes:
        print(f"no cached sides under {CACHE} for space {args.space}")
        return 1
    universe = universes[0].split("_", 1)[1]

    real_rows = load(args.space, universe, [0], args.inclusion)[0]
    null_rows = load(args.space, universe, args.calibration_seeds, args.inclusion)
    # Bucket once, up front. Every resample then reuses these arrays.
    real_by = [by_stratum(real_rows, i) for i in range(len(STRATA))]
    nulls_by = [[by_stratum(rows, i) for rows in null_rows] for i in range(len(STRATA))]
    nulls = null_rows
    rng = random.Random(args.seed)
    n_avail = len(nulls)
    print(f"FLOOR STABILITY  {args.space}, inclusion {args.inclusion}, FDR <= {args.max_fdr}")
    print(f"  {n_avail} cached calibration scrambles, {args.draws} resamples per size, "
          f"nothing re-clustered\n")

    full = {
        i: solve_one(real_by[i], nulls_by[i], args.max_fdr) for i in range(len(STRATA))
    }

    for index, (low, high) in enumerate(STRATA):
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        floor_full, kept_full = full[index]
        print(f"  stratum {label:<6}  all {n_avail}: floor "
              f"{'none' if floor_full is None else f'{floor_full:.4f}'}, "
              f"retains {kept_full} real families")
        print(f"    {'k':>4} {'floor p25':>10} {'median':>9} {'p75':>9} {'IQR':>8} "
              f"{'retained IQR':>13} {'span/median':>12}")
        for k in args.sizes:
            if k >= n_avail + 1:
                continue
            if k == n_avail:
                print(f"    {k:>4}   skipped: one draw from {n_avail}, spread is zero by "
                      "construction")
                continue
            floors, kept = [], []
            picks = range(len(nulls))
            for _ in range(args.draws):
                sub = [nulls_by[index][j] for j in rng.sample(list(picks), k)]
                f, t = solve_one(real_by[index], sub, args.max_fdr)
                if f is not None:
                    floors.append(f)
                    kept.append(t)
            if not floors:
                print(f"    {k:>4}   no candidate met the target in any resample")
                continue
            q = statistics.quantiles(floors, n=4) if len(floors) > 3 else [min(floors)] * 3
            kq = statistics.quantiles(kept, n=4) if len(kept) > 3 else [min(kept)] * 3
            med = statistics.median(kept)
            span = (max(kept) - min(kept)) / med if med else float("inf")
            flag = "  UNSTABLE" if span > LOO_SPAN_LIMIT else ""
            print(f"    {k:>4} {q[0]:>10.4f} {statistics.median(floors):>9.4f} {q[2]:>9.4f} "
                  f"{q[2]-q[0]:>8.4f} {kq[2]-kq[0]:>13.1f} {span:>11.1%}{flag}")
        print()

    print(f"  The declared branch: leave-one-out retained counts spanning more than "
          f"{LOO_SPAN_LIMIT:.0%} of the")
    print("  median means the estimate is unstable and the band is DROPPED "
          "(addendum-2026-09-21).")

    if args.project:
        base = 1850
        print(f"\n  PROJECTION TO {args.project:,} PATHWAYS")
        print("  A floor is solved from COUNTS, so its precision follows the number of null")
        print("  families a stratum holds, not the number of scrambles. The pool grows with the")
        print("  universe, so each scramble carries proportionally more evidence.")
        ratio = args.project / base
        print(f"    universe ratio                     {ratio:.2f}x")
        for index, (low, high) in enumerate(STRATA):
            label = f"{low}-{high}" if high < 10**9 else f"{low}+"
            per_side = statistics.mean(len(a) for a in nulls_by[index])
            need = None
            for k in sorted(args.sizes):
                if k > n_avail:
                    continue
                kept = []
                for _ in range(args.draws):
                    sub = [nulls_by[index][j] for j in rng.sample(range(len(nulls)), k)]
                    f, t = solve_one(real_by[index], sub, args.max_fdr)
                    if f is not None:
                        kept.append(t)
                if kept:
                    med = statistics.median(kept)
                    if med and (max(kept) - min(kept)) / med <= LOO_SPAN_LIMIT:
                        need = k
                        break
            at_scale = "n/a" if need is None else f"{max(1, round(need / ratio))}"
            print(f"    stratum {label:<6} {per_side:>8.0f} null families/side at 1,850   "
                  f"stable at k={need if need else '>40'}   projected k={at_scale}")
        print("\n  The projection assumes precision scales with null-family COUNT, which is the")
        print("  same assumption amendment-2026-09-24c used to declare 10+5 at 10,770. It is an")
        print("  extrapolation and has not been checked at that scale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
