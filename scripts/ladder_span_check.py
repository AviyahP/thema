#!/usr/bin/env python3
"""Does the Leiden resolution ladder actually span fine to broad? SETUP CHECK, before any build.

Amendment 3 makes granularity coverage a requirement rather than a hope, and gives it a test on the
real data: at the **top** rung the median community must be <= 5 members, and at the **bottom** rung
the largest community must be >= 3,125 (the declared size cap). Together those say the ladder
reaches finer than the finest band the scores ask about and coarser than the cap, so no band is out
of reach because the ladder could not get there.

If either fails the range is widened -- keeping 10 log-spaced rungs -- until both hold, and the
final range is recorded in DECISIONS.md as a setup check made before any result existed.

Usage::

    uv run scripts/ladder_span_check.py --lo 0.001 --hi 100
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: What the ladder must reach, from amendment 3.
MEDIAN_AT_TOP = 5
LARGEST_AT_BOTTOM = 3125


def main(argv: list[str] | None = None) -> int:
    """Check one candidate range, on real samples.

    Args:
        argv: Command-line arguments.

    Returns:
        0 if the range passes, 1 if it does not.
    """
    from build_10770 import engine_vectors
    from cut_trees import cap_for
    from thema.ontology import bitset as bits
    from thema.ontology import engines

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--lo", type=float, default=engines.RESOLUTION_LO)
    parser.add_argument("--hi", type=float, default=engines.RESOLUTION_HI)
    parser.add_argument("--rungs", type=int, default=engines.RESOLUTION_COUNT)
    parser.add_argument("--runs", type=int, default=2, help="how many real runs to check on")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    n, universe = meta["n_embedded"], meta["universe_digest"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    vectors = engine_vectors(root, args.data, args.space, "leiden", None, {})
    assert vectors is not None
    ladder = np.logspace(np.log10(args.lo), np.log10(args.hi), args.rungs)

    print(f"LADDER SPAN CHECK  {args.rungs} rungs over [{args.lo:g}, {args.hi:g}], "
          f"n={n:,}, cap {cap:,}", flush=True)
    print(f"  requirement: median <= {MEDIAN_AT_TOP} at the TOP rung, "
          f"largest >= {LARGEST_AT_BOTTOM:,} at the BOTTOM rung", flush=True)

    per_run = []
    for index in range(1, args.runs + 1):
        with np.load(trees / f"row{index:05d}.npz") as handle:
            sample = np.asarray(bits.unpack(handle["present"]), dtype=np.int64)
        block = vectors[sample]
        clock = time.perf_counter()
        rungs = engines.leiden_rungs(block, ladder, index)
        sizes = [np.array([len(c) for c in rung], dtype=np.int64) for rung in rungs]
        per_run.append(sizes)
        print(f"\n  run {index} ({len(sample):,} points, {time.perf_counter() - clock:.1f}s)")
        print(f"    {'rung':>5} {'resolution':>12} {'communities':>12} {'median':>8} "
              f"{'largest':>9} {'>= 3 members':>13}")
        for rung, (resolution, s) in enumerate(zip(ladder.tolist(), sizes, strict=True)):
            print(f"    {rung:>5} {resolution:>12.5g} {len(s):>12,} "
                  f"{int(np.median(s)):>8} {int(s.max()):>9,} "
                  f"{int((s >= 3).sum()):>13,}")

    # The gate is on the worst run, not the average: a ladder that only spans on a lucky sample has
    # not spanned.
    top_medians = [float(np.median(sizes[-1])) for sizes in per_run]
    bottom_largest = [int(sizes[0].max()) for sizes in per_run]
    top_ok = max(top_medians) <= MEDIAN_AT_TOP
    bottom_ok = min(bottom_largest) >= LARGEST_AT_BOTTOM

    print(f"\n  TOP rung    (resolution {ladder[-1]:g}): median community "
          f"{', '.join(f'{m:g}' for m in top_medians)} -- "
          f"need <= {MEDIAN_AT_TOP} -- {'PASS' if top_ok else 'FAIL'}")
    print(f"  BOTTOM rung (resolution {ladder[0]:g}): largest community "
          f"{', '.join(f'{b:,}' for b in bottom_largest)} -- "
          f"need >= {LARGEST_AT_BOTTOM:,} -- {'PASS' if bottom_ok else 'FAIL'}")
    verdict = "PASS" if (top_ok and bottom_ok) else "FAIL"
    print(f"\n  RANGE [{args.lo:g}, {args.hi:g}]: {verdict}", flush=True)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "lo": args.lo, "hi": args.hi, "rungs": args.rungs,
            "runs_checked": args.runs,
            "median_at_top": top_medians, "largest_at_bottom": bottom_largest,
            "requirement": {"median_at_top": MEDIAN_AT_TOP,
                            "largest_at_bottom": LARGEST_AT_BOTTOM},
            "top_ok": top_ok, "bottom_ok": bottom_ok, "verdict": verdict,
            "per_rung": [
                {"resolution": float(r),
                 "communities": [int(len(s)) for s in [sizes[i]]][0],
                 "median": float(np.median(sizes[i])), "largest": int(sizes[i].max())}
                for sizes in per_run[:1] for i, r in enumerate(ladder.tolist())
            ],
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
