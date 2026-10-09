#!/usr/bin/env python3
"""Solve the re-gate grid's floors: the same calibration, with and without the 0.33 minimum.

``build_10770.solve`` returns, per stratum, a calibrated ``floor`` and an ``effective`` threshold
set to ``max(DECLARED_M, floor)`` with ``DECLARED_M = 0.33``. That 0.33 is a **fixed minimum
inherited from the 1,850-pathway freeze** -- the master spec's §10.6 offered m in {0.25, 0.33, 0.50}
as candidate thresholds, 0.33 was chosen then, and when per-size calibration arrived later the old
constant was kept as a floor under the floors. So wherever calibration lands below 0.33 the gate
ignores it: on ``thema_L`` the solved floors are 0.285 at 6-6, 0.19 at 7-9 and **0.025 at 10+**, all
three overridden to 0.33. Every theme of ten or more members is therefore gated about thirteen times
more strictly than its own calibration requires, which is the hypothesis this grid tests.

Two floor sets per arm, from one calibration so the only difference is the minimum:

- **current** -- ``effective = max(0.33, floor)``, what every build so far has used;
- **calibrated** -- ``effective = floor``, the calibration alone.

Both are confirmed on the held-out scrambles **once**, and nothing is re-solved afterwards. Floors
are never chosen by what the held-out side does.

Usage::

    uv run scripts/regate_floors.py
    uv run scripts/regate_floors.py --arms L
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Ten calibration seeds and two held-out, as the grid declares.
CALIBRATION = tuple(range(3001, 3011))
HELDOUT = (4001, 4002)
#: The "-cal8" arms' calibration target. Added 8 Oct 2026 **before any structure result was seen,
#: after seeing MS-cal's held-out FDR of 0.01009**. ``solve`` takes the FIRST threshold whose
#: CALIBRATION FDR is at or under the target, so at a target of 0.01 the calibration estimate sits
#: flush against the cap and the held-out estimate -- an independent draw -- lands above it about
#: half the time. Solving to 0.008 leaves headroom. The HELD-OUT caps are unchanged at 0.01 overall
#: and 0.02 per stratum, and the per-stratum calibration target is unchanged.
CAL8_TARGET = 0.008
#: Where each arm's cached side material lives.
STORES = {"L": "calibration", "M5": "calibration_M5", "MS": "calibration_MS"}


def rows_of(path: Path) -> list[tuple[int, float]]:
    """``(size, support)`` rows from a cached side.

    Args:
        path: The side's ``.npz``.

    Returns:
        One row per candidate.
    """
    with np.load(path) as handle:
        blocks, supports = handle["blocks"], handle["supports"]
    sizes = np.bitwise_count(blocks).sum(axis=1).astype(np.int64)
    return list(zip(sizes.tolist(), [round(float(s), 6) for s in supports], strict=True))


def solve_to(real: list[tuple[int, float]], nulls: list[list[tuple[int, float]]],
             target: float) -> list[dict]:
    """``build_10770.solve`` with the calibration target as a parameter.

    A faithful copy of that loop, which hardcodes :data:`~build_10770.MAX_FDR_OVERALL`. The copy is
    checked rather than trusted: :func:`main` asserts that ``solve_to(..., MAX_FDR_OVERALL)`` equals
    ``solve(...)`` exactly before using it at any other target, so a drift between the two is caught
    on every run rather than discovered in a result.

    Args:
        real: The real side's rows.
        nulls: One list of rows per calibration scramble.
        target: Calibration FDR a stratum's floor must reach.

    Returns:
        Per stratum: bounds, the solved floor, the effective threshold and the counts behind it.
    """
    from build_10770 import DECLARED_M, STRATA, stratum_of

    out = []
    for index, (low, high) in enumerate(STRATA):
        r = [s for size, s in real if stratum_of(size) == index]
        per = [[s for size, s in rows if stratum_of(size) == index] for rows in nulls]
        chosen: tuple[float | None, float, int] = (None, 0.0, 0)
        for cut in sorted({s for rows in per for s in rows}):
            f = sum(sum(1 for s in rows if s >= cut) for rows in per) / max(len(per), 1)
            keep = sum(1 for s in r if s >= cut)
            if keep and f / keep <= target:
                chosen = (cut, f, keep)
                break
        if chosen[0] is None:
            total = sum(len(rows) for rows in per) / max(len(per), 1)
            chosen = (0.0, total, len(r)) if total == 0 else (None, total, len(r))
        floor, f_at, r_at = chosen
        out.append({
            "stratum": f"{low}-{high}" if high < 10**9 else f"{low}+",
            "real": len(r),
            "floor": floor,
            "effective": None if floor is None else max(DECLARED_M, floor),
            "calibration_fdr": None if floor is None or not r_at else round(f_at / r_at, 5),
        })
    return out


def without_minimum(solved: list[dict]) -> list[dict]:
    """The same floors with the 0.33 minimum removed.

    Args:
        solved: Output of ``build_10770.solve``.

    Returns:
        A copy whose ``effective`` is the calibrated floor itself.
    """
    out = copy.deepcopy(solved)
    for entry in out:
        entry["effective"] = entry["floor"]
    return out


def main(argv: list[str] | None = None) -> int:
    """Solve and confirm both floor sets for every arm.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import DECLARED_M, MAX_FDR_OVERALL, MAX_FDR_STRATUM, confirm, solve

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--arms", default="L,M5,MS")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    out_dir = args.out or (root / "regate")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"RE-GATE FLOORS  {len(CALIBRATION)} calibration seeds {CALIBRATION[0]}-"
          f"{CALIBRATION[-1]}, held out {list(HELDOUT)}, DECLARED_M = {DECLARED_M}")
    summary: dict[str, object] = {"calibration": list(CALIBRATION), "heldout": list(HELDOUT),
                                  "declared_m": DECLARED_M, "arms": {}}

    for arm in args.arms.split(","):
        arm = arm.strip()
        store = root / STORES[arm]
        missing = [s for s in (*CALIBRATION, *HELDOUT)
                   if not (store / f"seed{s:05d}.npz").is_file()]
        if missing or not (store / "real.npz").is_file():
            print(f"  {arm}: missing sides {missing or ['real']}; skipping")
            continue
        clock = time.perf_counter()
        real = rows_of(store / "real.npz")
        cal = [rows_of(store / f"seed{s:05d}.npz") for s in CALIBRATION]
        held = [rows_of(store / f"seed{s:05d}.npz") for s in HELDOUT]
        current = solve(real, cal)
        # Prove the parameterised copy before relying on it at a different target.
        mirror = solve_to(real, cal, MAX_FDR_OVERALL)
        if json.dumps(mirror, sort_keys=True) != json.dumps(current, sort_keys=True):
            raise ValueError(
                "solve_to disagrees with build_10770.solve at the declared target; the copy has "
                "drifted and no floor from it can be trusted")
        calibrated = without_minimum(current)
        cal8 = without_minimum(solve_to(real, cal, CAL8_TARGET))

        entry: dict[str, object] = {}
        for rule, floors in (("current", current), ("calibrated", calibrated),
                             ("cal8", cal8)):
            checked = confirm(real, held, floors)
            per = {e["stratum"]: e["heldout_fdr"] for e in checked["strata"]}
            over = {k: v for k, v in per.items()
                    if v is not None and float(v) > MAX_FDR_STRATUM}
            overall_bad = (checked["overall_fdr"] is not None
                           and float(checked["overall_fdr"]) > MAX_FDR_OVERALL)
            record = {
                "arm": arm, "rule": rule,
                "source": (f"solved on {len(CALIBRATION)} seeds {list(CALIBRATION)}, confirmed "
                           f"once on {list(HELDOUT)}; effective = "
                           + ("max(0.33, floor)" if rule == "current"
                              else f"floor, no minimum, calibration target "
                                   f"{CAL8_TARGET if rule == 'cal8' else MAX_FDR_OVERALL}")),
                "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
                "declared_m": DECLARED_M if rule == "current" else None,
                "calibration_target": CAL8_TARGET if rule == "cal8" else MAX_FDR_OVERALL,
                "added": ("declared 8 Oct 2026 before any structure result was seen, after seeing "
                          "MS-cal's held-out FDR of 0.01009" if rule == "cal8" else None),
                "solved": floors, "confirmed": checked,
                "per_stratum_heldout_fdr": per, "over_cap": over,
                "overall_over_cap": overall_bad,
                "seconds": round(time.perf_counter() - clock, 1),
            }
            path = out_dir / f"floors_{arm}_{rule}.json"
            path.write_text(json.dumps(record, indent=2, default=float) + "\n",
                            encoding="utf-8")
            entry[rule] = {"overall_fdr": checked["overall_fdr"], "over_cap": over,
                           "floors": {e["stratum"]: e["effective"] for e in floors},
                           "path": str(path)}
            flag = ("" if not over and not overall_bad
                    else "   CAP FAILURE: " + ", ".join(f"{k} {v}" for k, v in sorted(over.items()))
                    + (" overall" if overall_bad else ""))
            print(f"  {arm:<3} {rule:<11} overall {checked['overall_fdr']}  "
                  + " ".join(f"{e['stratum']}:{e['effective']}" for e in floors) + flag,
                  flush=True)
        summary["arms"][arm] = entry

    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"  -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
