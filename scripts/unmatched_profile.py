#!/usr/bin/env python3
"""Which themes failed to find a partner across disjoint tree blocks, broken down by size.

**POST HOC, and it decides nothing.** Run after rung 2 had already failed its declared mark, on the
per-theme scores that run produced. The mark is a single number over all themes; this only asks
where the misses sit. A breakdown chosen after seeing the result cannot license a different
threshold, a different population, or a different verdict -- that is the defect
`amendment-2026-09-24b` withdrew and the one behind the withdrawn straddler claim.

Usage::

    uv run scripts/unmatched_profile.py rung2_per_theme.tsv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

csv.field_size_limit(1 << 30)

#: Size bands. The floor strata of the build, so the breakdown lines up with how support is gated.
BANDS: tuple[tuple[int, int], ...] = (
    (3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (10, 19), (20, 49), (50, 199), (200, 10**9),
)

#: The declared matching threshold. Not a parameter of this script.
THETA = 0.70


def main(argv: list[str] | None = None) -> int:
    """Break the unmatched themes out by size.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path, help="the --dump TSV from theme_match.py")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    rows = []
    with args.dump.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append((row["direction"], int(row["members"]), float(row["best_jaccard"])))

    print("UNMATCHED THEMES, POST HOC -- rung 2, and this decides nothing")
    report = {}
    for direction in ("forward", "backward"):
        picked = [(m, j) for d, m, j in rows if d == direction]
        sizes = np.array([m for m, _ in picked])
        best = np.array([j for _, j in picked])
        missed = best < THETA
        print(f"\n  {direction}: {len(picked):,} themes, {int(missed.sum()):,} with no partner at "
              f"Jaccard >= {THETA} ({missed.mean():.1%})")
        print(f"    {'members':<10} {'themes':>8} {'unmatched':>10} {'rate':>7} "
              f"{'median best J':>14} {'share of misses':>16}")
        bands = []
        for low, high in BANDS:
            mask = (sizes >= low) & (sizes <= high)
            if not mask.any():
                continue
            label = f"{low}-{high}" if high < 10**9 else f"{low}+"
            miss_here = int((missed & mask).sum())
            print(f"    {label:<10} {int(mask.sum()):>8,} {miss_here:>10,} "
                  f"{miss_here / mask.sum():>6.1%} {np.median(best[mask]):>14.3f} "
                  f"{miss_here / max(int(missed.sum()), 1):>15.1%}")
            bands.append({
                "band": label, "themes": int(mask.sum()), "unmatched": miss_here,
                "rate": round(float(miss_here / mask.sum()), 4),
                "median_best_jaccard": round(float(np.median(best[mask])), 4),
                "share_of_all_misses": round(float(miss_here / max(int(missed.sum()), 1)), 4),
            })
        report[direction] = {
            "themes": len(picked), "unmatched": int(missed.sum()),
            "unmatched_rate": round(float(missed.mean()), 4), "bands": bands,
        }
        near = int(((best >= 0.60) & (best < THETA)).sum())
        share = near / max(int(missed.sum()), 1)
        print(f"    of the {int(missed.sum()):,} misses, {near:,} ({share:.0%}) sit at best "
              f"Jaccard 0.60-0.70")
        report[direction]["misses_between_0.60_and_0.70"] = near

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "post_hoc": True, "decides_nothing": True, "theta": THETA, "directions": report,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
