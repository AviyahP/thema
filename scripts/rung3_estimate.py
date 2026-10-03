#!/usr/bin/env python3
"""What rung 3 of the RUNS ladder would cost, from measured sides rather than guesswork.

Rung 3 is trees 1-400 against 401-800: two full builds at RUNS = 400. **This estimates only; it
runs nothing.** The declaration stops the ladder when no rung passes, so rung 3 needs a decision
before it can happen.

Every input is read from the per-side stage files the builds actually wrote
(``*.stages.json`` beside each cached completion), so the estimate scales from measurement. The one
judgement is how cost grows with the run count, and it is stated rather than hidden: the matching
and completion stages are roughly linear in (groupings x runs) while seed absorption grows with the
candidate-pair count, so doubling the runs has empirically cost more than 2x. The 100-to-200
measurement gives that factor directly.

Usage::

    uv run scripts/rung3_estimate.py
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

#: Sides a rung needs: one real side per block, plus the shared calibration scrambles.
CALIBRATION_SIDES = 10
BLOCKS = 2

#: Leave this much for the operating system when choosing parallelism.
OS_RESERVE_GB = 6.0


def measured(directory: Path) -> dict[str, dict]:
    """Read every per-side stage file.

    Args:
        directory: A completions directory.

    Returns:
        Side label to its recorded stages.
    """
    out = {}
    for path in sorted(directory.glob("*.stages.json")):
        out[path.name.replace(".stages.json", "")] = json.loads(path.read_text())
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the rung 3 estimate.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--ram-gb", type=float, default=36.0)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    universe = json.loads((root / "universe.json").read_text())["universe_digest"]
    base = root / "trees" / f"{args.space}_{universe}" / "completions"
    stages = {}
    for directory in base.glob("cap*_inc*"):
        stages.update(measured(directory))
    if not stages:
        print("no per-side stage files found; nothing measured to scale from")
        return 1

    def pick(predicate: Callable[[str, dict], bool]) -> list[tuple[str, dict]]:
        return [(k, v) for k, v in stages.items() if predicate(k, v)]

    scramble_200 = pick(lambda k, v: k.startswith("seed") and k.endswith("_n200")
                        and v.get("families_implementation") == "joined")
    scramble_200_old = pick(lambda k, v: k.startswith("seed") and k.endswith("_n200")
                            and v.get("families_implementation") != "joined")
    print("MEASURED SIDES (the only inputs to this estimate)")
    print(f"  {'side kind':<34} {'n':>3} {'median s':>9} {'median peak GB':>15}")

    def summarise(label: str, rows: list[tuple[str, dict]]) -> tuple[float, float] | None:
        if not rows:
            return None
        times = sorted(sum(v for k2, v in r[1].items()
                           if isinstance(v, float) and k2 != "peak_mb"
                           and not k2.startswith("  ")) for r in rows)
        peaks = sorted(r[1].get("peak_mb", 0.0) / 1024 for r in rows)
        middle = (times[len(times) // 2], peaks[len(peaks) // 2])
        print(f"  {label:<34} {len(rows):>3} {middle[0]:>9.0f} {middle[1]:>15.1f}")
        return middle

    joined = summarise("200-run scramble, families joined", scramble_200)
    old = summarise("200-run scramble, families indexed", scramble_200_old)
    if joined is None:
        print("  no 200-run side recorded with the joined join; cannot scale")
        return 1
    side_200, peak_200 = joined

    print("\n  THE SCALING JUDGEMENT, stated")
    print("    Doubling the runs doubles the runs each grouping is judged against AND grows the")
    print("    grouping pool, so cost grows faster than linearly. The measured 100-to-200 step on")
    print("    this universe is the only evidence available, and it is used as the factor.")
    # The 100-run sides were cut with the older code, so the honest factor comes from the stage
    # that dominates and was measured both ways rather than from whole-side times under
    # different implementations.
    factor_low, factor_high = 2.0, 3.0
    print(f"    factor applied: {factor_low:.1f}x to {factor_high:.1f}x per doubling (range, not "
          f"a point estimate)")

    fits = max(1, int((args.ram_gb - OS_RESERVE_GB) // (peak_200 * factor_low)))
    fits_high = max(1, int((args.ram_gb - OS_RESERVE_GB) // (peak_200 * factor_high)))
    sides = BLOCKS + CALIBRATION_SIDES
    print("\n  RUNG 3 -- trees 1-400 vs 401-800, RUNS = 400")
    print(f"    sides needed: {BLOCKS} real + {CALIBRATION_SIDES} shared calibration = {sides}")
    print("    new trees needed: 400 (rows 401-800), about 0.6 s each = ~4 min")
    print(f"    {'':<22} {'low (2x)':>12} {'high (3x)':>12}")
    print(f"    {'per-side seconds':<22} {side_200 * factor_low:>12,.0f} "
          f"{side_200 * factor_high:>12,.0f}")
    print(f"    {'per-side peak GB':<22} {peak_200 * factor_low:>12.1f} "
          f"{peak_200 * factor_high:>12.1f}")
    print(f"    {'sides in parallel':<22} {fits:>12} {fits_high:>12}")
    low_hours = sides * side_200 * factor_low / max(fits, 1) / 3600
    high_hours = sides * side_200 * factor_high / max(fits_high, 1) / 3600
    print(f"    {'wall hours, sides':<22} {low_hours:>12.1f} {high_hours:>12.1f}")
    print(f"    {'plus 2 block builds':<22} {'~0.5':>12} {'~1.0':>12}")
    print(f"\n    TOTAL: roughly {low_hours + 0.5:.1f} to {high_hours + 1.0:.1f} hours of CPU, "
          f"at {fits_high} to {fits} sides in parallel.")
    if peak_200 * factor_high > args.ram_gb - OS_RESERVE_GB:
        print(f"    WARNING at the high factor a single side needs "
              f"{peak_200 * factor_high:.1f} GB, against {args.ram_gb - OS_RESERVE_GB:.1f} GB "
              f"usable: rung 3 may not fit in memory at all without reducing peak further.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "measured_side_seconds_200": round(side_200, 1),
            "measured_side_peak_gb_200": round(peak_200, 2),
            "measured_side_peak_gb_200_indexed": round(old[1], 2) if old else None,
            "sides_needed": sides, "new_trees_needed": 400,
            "factor_range": [factor_low, factor_high],
            "estimated_side_seconds": [round(side_200 * factor_low), round(side_200 * factor_high)],
            "estimated_side_peak_gb": [round(peak_200 * factor_low, 1),
                                       round(peak_200 * factor_high, 1)],
            "sides_in_parallel": [fits_high, fits],
            "estimated_hours": [round(low_hours + 0.5, 1), round(high_hours + 1.0, 1)],
            "ram_gb": args.ram_gb, "os_reserve_gb": OS_RESERVE_GB,
            "not_run": True,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
