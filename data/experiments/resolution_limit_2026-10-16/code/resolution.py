#!/usr/bin/env python3
"""The first pass's resolution limit: the largest cluster size it can still tell from noise.

Declared 16 Oct 2026. **Read-only and adopts nothing.**

The question is a measured threshold rather than a chosen one. For each size bin, how well can the
first pass separate real candidates from scrambled ones *using only that bin's own candidates*? The
answer is the bin's best achievable false-discovery rate: walk every support cut the scrambles
offer, and take the smallest ``(mean scrambled at or above the cut) / (real at or above the cut)``.
A bin
whose best FDR never reaches the 0.008 calibration target cannot be separated from noise at all, at
any threshold, and the clusters in it are not vouched for by the method.

**T** is the upper edge of the largest bin that keeps at least 5 real candidates at a within-bin FDR
of 0.008 or better, with every smaller bin also meeting it.

Two arms, because O50's floors and O50's candidates do not come from the same universe:

* **arm x2** -- the real candidates are O50's own, from universe L minus the 23 exclusions
  (5,539 pathways, space ``leaves_centred_x2``, 99,951 candidates). This is the side ``fate.tsv``
  tracks and the side O50's gate is applied to, so it is the primary arm.
* **arm L** -- the real candidates are the pre-exclusion universe L side (5,559 pathways, space
  ``leaves_centred``, 100,564 candidates). This is the side the cal8 floors were actually *solved*
  from: its per-stratum counts are 804 / 1,090 / 1,455 / 2,193 / 8,026 / 86,996, which is exactly
  what ``floors_L_cal8.json`` records. It is the consistency check, and it pairs with the scrambles
  with no universe mismatch at all.

The scrambles are the same in both arms, because there is only one cached set: seeds 3001-3010 on
universe L, which are the ten the cal8 floors were solved on. If T agrees between the arms then the
23 exclusions do not move it and nothing turns on the choice.

Usage::

    uv run python data/experiments/resolution_limit_2026-10-16/code/resolution.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

#: The declared bins, in doublings.
BINS = ((10, 19), (20, 39), (40, 79), (80, 159), (160, 319), (320, 639), (640, 1279),
        (1280, 10 ** 9))

#: The declared finer split across the break.
FINER = ((80, 119), (120, 159), (160, 239), (240, 319))

#: The calibration target a bin has to reach on its own.
TARGET = 0.008

#: A bin has to keep at least this many real candidates at the target.
MIN_KEPT = 5

#: The calibration scrambles the cal8 floors were solved on.
SEEDS = tuple(range(3001, 3011))


def label(low: int, high: int) -> str:
    """A bin's label.

    Args:
        low: Lower edge, inclusive.
        high: Upper edge, inclusive.

    Returns:
        ``"low-high"``, or ``"low+"`` for the open top bin.
    """
    return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"


def side_rows(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """``(sizes, supports)`` for one cached side, supports rounded as ``Material.rows`` rounds them.

    Args:
        path: The cached ``.npz``.

    Returns:
        Member counts and supports, aligned.

    Raises:
        FileNotFoundError: If the side is not cached.
    """
    if not path.is_file():
        raise FileNotFoundError(f"{path} is not cached")
    with np.load(path) as handle:
        sizes = np.bitwise_count(handle["blocks"]).sum(axis=1).astype(np.int64)
        supports = np.round(handle["supports"].astype(np.float64), 6)
    return sizes, supports


def walk(real: np.ndarray, pooled: np.ndarray, seeds: int, cuts: list[float]
         ) -> dict[str, object]:
    """Best achievable rate over a cut ladder, and the most a bin keeps at the target.

    Args:
        real: The bin's real supports.
        pooled: The bin's scrambled supports, all seeds pooled.
        seeds: How many seeds were pooled.
        cuts: The ladder, ascending.

    Returns:
        ``best_fdr``, ``best_cut``, ``best_kept``, ``target_cut`` and ``kept_at_target``.
    """
    best: tuple[float, float, int] | None = None
    target: tuple[float, int] | None = None
    for cut in cuts:
        null = float(np.count_nonzero(pooled >= cut)) / max(seeds, 1)
        keep = int(np.count_nonzero(real >= cut))
        if not keep:
            continue
        rate = null / keep
        if best is None or rate < best[0]:
            best = (rate, float(cut), keep)
        if target is None and rate <= TARGET:
            target = (float(cut), keep)
    return {
        "best_fdr": round(best[0], 8) if best else None,
        "best_cut": best[1] if best else None,
        "best_kept": best[2] if best else 0,
        "target_cut": target[0] if target else None,
        "kept_at_target": target[1] if target else 0,
    }


def bin_report(real: np.ndarray, nulls: list[np.ndarray]) -> dict[str, object]:
    """Everything one bin has to say, on both cut ladders.

    Two ladders, because they answer different questions and disagree sharply above 40 pathways:

    * **the solver's ladder** -- the scrambles' own support values, which is what
      ``regate_floors.solve_to`` walks. In every bin from 40-79 upward the scrambles produce exactly
      **one** distinct support, 0.005, so this ladder has a single rung and cannot discriminate at
      all. That is a property of the ladder, not of the bin.
    * **the full ladder** -- every support value present in the bin, real or scrambled. This is the
      honest answer to "is there a cut that separates them", and a cut just above the scrambles'
      maximum is available to it.

    Because the scrambles' maximum is so low in the large bins, the full ladder's best rate is
    usually an observed **zero** null count. A zero count over ten seeds is not proof of a zero
    rate, so ``bound_fdr`` applies the rule of three -- a 95% upper bound of ``3 / seeds`` on the
    mean null count -- and divides by the real count kept. That bound, not the zero, is what the
    verdict uses.

    Args:
        real: Supports of the bin's real candidates.
        nulls: One array of the bin's scrambled supports per seed.

    Returns:
        The bin's counts, percentiles and both ladders' verdicts.
    """
    pooled = np.concatenate(nulls) if nulls else np.zeros(0)
    seeds = max(len(nulls), 1)
    out: dict[str, object] = {
        "n_real": int(len(real)),
        "n_null_mean": round(len(pooled) / seeds, 1),
        "real_median": round(float(np.median(real)), 4) if len(real) else None,
        "real_p90": round(float(np.percentile(real, 90)), 4) if len(real) else None,
        "real_max": round(float(real.max()), 4) if len(real) else None,
        "null_median": round(float(np.median(pooled)), 4) if len(pooled) else None,
        "null_p90": round(float(np.percentile(pooled, 90)), 4) if len(pooled) else None,
        "null_max": round(float(pooled.max()), 4) if len(pooled) else None,
        "null_distinct": len(set(pooled.tolist())),
        "kept_above_null_max": 0, "bound_fdr": None,
    }
    if not len(real) or not len(pooled):
        for prefix in ("solver", "full"):
            out.update({f"{prefix}_{k}": None for k in
                        ("best_fdr", "best_cut", "best_kept", "target_cut", "kept_at_target")})
        return out
    solver = walk(real, pooled, seeds, sorted(set(pooled.tolist())))
    full = walk(real, pooled, seeds,
                sorted(set(pooled.tolist()) | set(real.tolist())))
    out.update({f"solver_{k}": v for k, v in solver.items()})
    out.update({f"full_{k}": v for k, v in full.items()})
    above = int(np.count_nonzero(real > pooled.max()))
    out["kept_above_null_max"] = above
    if above:
        out["bound_fdr"] = round((3.0 / seeds) / above, 8)
    return out


def resolution(bins: tuple[tuple[int, int], ...], real: tuple[np.ndarray, np.ndarray],
               nulls: list[tuple[np.ndarray, np.ndarray]]) -> list[dict[str, object]]:
    """One row per bin.

    Args:
        bins: The bin edges.
        real: ``(sizes, supports)`` for the real side.
        nulls: ``(sizes, supports)`` per scramble seed.

    Returns:
        One report per bin, with the bin's label and edges added.
    """
    sizes, supports = real
    out = []
    for low, high in bins:
        take = (sizes >= low) & (sizes <= high)
        null_bins = [sup[(sz >= low) & (sz <= high)] for sz, sup in nulls]
        row = {"bin": label(low, high), "low": low, "high": high if high < 10 ** 9 else None}
        row.update(bin_report(supports[take], null_bins))
        out.append(row)
    return out


def threshold(rows: list[dict[str, object]], ladder: str) -> dict[str, object]:
    """T on one ladder: the largest bin meeting the target, with every smaller bin meeting it.

    A bin counts as meeting it only if it keeps at least :data:`MIN_KEPT` real candidates at a
    within-bin FDR of :data:`TARGET` or better **and**, where that rate rests on a zero null count,
    the rule-of-three bound also clears the target. The second condition is what stops an observed
    zero over ten seeds from being read as proof.

    Args:
        rows: Bin reports in ascending size order.
        ladder: ``"solver"`` or ``"full"``.

    Returns:
        ``T``, the bin that sets it, and the first bin that fails.
    """
    passing: list[dict[str, object]] = []
    for row in rows:
        kept = row.get(f"{ladder}_kept_at_target") or 0
        bound = row["bound_fdr"]
        honest = bound is None or bound <= TARGET or kept < MIN_KEPT
        if kept < MIN_KEPT or not honest:
            return {"ladder": ladder,
                    "T": passing[-1]["high"] if passing else None,
                    "last_passing_bin": passing[-1]["bin"] if passing else None,
                    "first_failing_bin": row["bin"],
                    "first_failing_kept": kept,
                    "first_failing_best_fdr": row.get(f"{ladder}_best_fdr"),
                    "n_passing": len(passing)}
        passing.append(row)
    # Every bin passed, including the open top one, so there is no upper edge to report: the
    # method separates real from scrambled at every size it produces. Said as "unbounded" rather
    # than as a null, which would read as a failure.
    return {"ladder": ladder, "T": None, "T_unbounded": True,
            "last_passing_bin": passing[-1]["bin"] if passing else None,
            "first_failing_bin": None, "first_failing_kept": None,
            "first_failing_best_fdr": None, "n_passing": len(passing)}


def cell(value: float | None, width: int, places: int) -> str:
    """One right-aligned numeric cell, or a dash.

    Args:
        value: The number, or None.
        width: Field width.
        places: Decimal places.

    Returns:
        The formatted cell.
    """
    return f"{'-':>{width}}" if value is None else f"{value:>{width}.{places}f}"


def show(title: str, rows: list[dict[str, object]]) -> None:
    """Print one bin table, both ladders side by side.

    Args:
        title: Table heading.
        rows: Bin reports.
    """
    print("\n" + "=" * 118)
    print(title)
    print("=" * 118)
    print(f"  {'bin':<10}{'real':>8}{'null/seed':>11}{'r med':>8}{'r p90':>8}{'r max':>8}"
          f"{'n med':>8}{'n max':>8}{'n vals':>8}"
          f"{'SOLVER fdr':>12}{'keeps':>7}"
          f"{'FULL fdr':>10}{'at cut':>8}{'keeps':>8}"
          f"{'3/10 bound':>12}")
    for row in rows:
        print(f"  {row['bin']:<10}{row['n_real']:>8,}{row['n_null_mean']:>11,.1f}"
              + cell(row["real_median"], 8, 3) + cell(row["real_p90"], 8, 3)
              + cell(row["real_max"], 8, 3)
              + cell(row["null_median"], 8, 3) + cell(row["null_max"], 8, 3)
              + f"{row['null_distinct']:>8,}"
              + cell(row["solver_best_fdr"], 12, 5)
              + f"{row['solver_kept_at_target'] or 0:>7,}"
              + cell(row["full_best_fdr"], 10, 5) + cell(row["full_target_cut"], 8, 3)
              + f"{row['full_kept_at_target'] or 0:>8,}"
              + cell(row["bound_fdr"], 12, 6))


def main(argv: list[str] | None = None) -> int:
    """Measure the resolution limit on both arms and report T."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--x2", type=Path,
                        default=ROOT / "data/ontology/v0.4-leaves-x2/calibration")
    parser.add_argument("--l", type=Path,
                        default=ROOT / "data/ontology/v0.4-leaves/calibration")
    parser.add_argument("--fate", type=Path,
                        default=ROOT / "data/experiments/consensus_fate_2026-10-16/fate.tsv")
    parser.add_argument("--out", type=Path, default=HERE.parent)
    args = parser.parse_args(argv)
    clock = time.perf_counter()

    print("THE FIRST PASS'S RESOLUTION LIMIT. Declared 16 Oct 2026. Read-only; adopts nothing.")
    print(f"  target FDR {TARGET} within a bin, at least {MIN_KEPT} real candidates kept")
    scrambles = [args.l / f"seed{seed:05d}.npz" for seed in SEEDS]
    missing = [p.name for p in scrambles if not p.is_file()]
    print(f"  scrambles: seeds {SEEDS[0]}-{SEEDS[-1]} in {args.l}"
          + (f" -- MISSING {missing}" if missing else " -- all 10 CACHED, not recomputed"))
    nulls = [side_rows(path) for path in scrambles]
    print(f"  {sum(len(s) for s, _ in nulls):,} scrambled candidates over {len(nulls)} seeds, "
          f"mean {sum(len(s) for s, _ in nulls) / len(nulls):,.0f} per seed "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)

    arms = {}
    for name, path, note in (
        ("x2", args.x2 / "real.npz", "O50's own real side, universe L minus the 23 exclusions"),
        ("L", args.l / "real.npz", "the side the cal8 floors were solved from, universe L"),
    ):
        sizes, supports = side_rows(path)
        arms[name] = (sizes, supports)
        print(f"  arm {name}: {len(sizes):,} real candidates, max size {sizes.max():,}  ({note})")

    # The real side and fate.tsv must be the same object on the rows fate.tsv tracks.
    tracked: list[tuple[int, float]] = []
    with args.fate.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["family_support"]:
                tracked.append((int(row["size"]), float(row["family_support"])))
    sizes, supports = arms["x2"]
    from collections import Counter
    mine = Counter((int(s), round(float(v), 6)) for s, v in zip(sizes.tolist(),
                                                               supports.tolist(), strict=True)
                   if s >= 51)
    theirs = Counter((s, round(v, 6)) for s, v in tracked)
    overlap = sum((theirs & mine).values())
    print(f"  CHECK against fate.tsv: {len(tracked):,} tracked rows carry a family support; "
          f"{overlap:,} of them match a real-side candidate exactly on (size, support)")
    if overlap < len(tracked) * 0.99:
        raise SystemExit("fate.tsv and the cached real side disagree; stop")
    return report(args, arms, nulls, clock)


def report(args: argparse.Namespace, arms: dict[str, tuple[np.ndarray, np.ndarray]],
           nulls: list[tuple[np.ndarray, np.ndarray]], clock: float) -> int:
    """Print both arms, both bin sets, both ladders and T; write the tables.

    Args:
        args: Parsed arguments.
        arms: ``(sizes, supports)`` per arm.
        nulls: ``(sizes, supports)`` per scramble seed.
        clock: Start time.

    Returns:
        0.
    """
    args.out.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, object]] = {}
    all_rows = []
    for arm in ("x2", "L"):
        coarse = resolution(BINS, arms[arm], nulls)
        fine = resolution(FINER, arms[arm], nulls)
        show(f"ARM {arm}: DOUBLINGS", coarse)
        show(f"ARM {arm}: THE FINER SPLIT ACROSS THE BREAK", fine)
        got = {which: threshold(coarse, which) for which in ("solver", "full")}
        print(f"\n  ARM {arm}")
        for which in ("solver", "full"):
            entry = got[which]
            tail = ("" if entry["first_failing_bin"] is None else
                    f"; first failing {entry['first_failing_bin']} keeping "
                    f"{entry['first_failing_kept']} at best FDR "
                    f"{entry['first_failing_best_fdr']}")
            shown = ("UNBOUNDED, every bin passes" if entry.get("T_unbounded")
                     else str(entry["T"]))
            print(f"    T on the {which} ladder = {shown} "
                  f"(last passing bin {entry['last_passing_bin']}{tail})")
        moved = {}
        for which in ("solver", "full"):
            limit = got[which]["T"] or 0
            bad = [r["bin"] for r in fine
                   if (r.get(f"{which}_kept_at_target") or 0) < MIN_KEPT and r["low"] <= limit]
            moved[which] = bad
            print(f"    the finer split on the {which} ladder: "
                  + ", ".join(f"{r['bin']} keeps {r.get(f'{which}_kept_at_target') or 0}"
                              for r in fine)
                  + (f"  -> MOVES T, {bad} fails inside the passing range" if bad
                     else "  -> does not move T"))
        results[arm] = {"coarse": coarse, "finer": fine, "threshold": got,
                        "finer_fails_inside": moved}
        for which, rows in (("doublings", coarse), ("finer", fine)):
            for row in rows:
                all_rows.append({"arm": arm, "bin_set": which, **row})

    print("\n" + "=" * 118)
    print("T")
    print("=" * 118)
    for which, what in (("solver", "the ladder the floor solver actually walks"),
                        ("full", "every support value present in the bin")):
        def read(arm: str, ladder: str = which) -> str:
            """T for one arm, or the unbounded case said in words."""
            entry = results[arm]["threshold"][ladder]
            return "UNBOUNDED" if entry.get("T_unbounded") else str(entry["T"])
        a, b = read("x2"), read("L")
        print(f"  {which:<7} ladder ({what})")
        print(f"          arm x2: T = {a:<12} arm L: T = {b:<12} "
              f"{'AGREE' if a == b else 'DISAGREE'}")
    print("\n  The two ladders answer different questions and the gap between them IS the finding:")
    print("  from 40 pathways up, the scrambles produce exactly ONE distinct support, 0.005 -- a")
    print("  grouping found in one subsample of 200 and never in two. The solver's ladder has a")
    print("  single rung there and cannot discriminate at all, which is why it reports no floor.")
    print("  A cut just above 0.005 separates the two populations cleanly in every large bin:")
    for row in results["x2"]["coarse"]:
        if row["low"] >= 40:
            print(f"    {row['bin']:<10}{row['kept_above_null_max']:>7,} real candidates above "
                  f"the scrambles' maximum, rule-of-three bound "
                  f"{row['bound_fdr'] if row['bound_fdr'] is not None else '-'}")

    fields = ["arm", "bin_set", "bin", "low", "high", "n_real", "n_null_mean", "real_median",
              "real_p90", "real_max", "null_median", "null_p90", "null_max", "null_distinct",
              "solver_best_fdr", "solver_best_cut", "solver_best_kept", "solver_target_cut",
              "solver_kept_at_target", "full_best_fdr", "full_best_cut", "full_best_kept",
              "full_target_cut", "full_kept_at_target", "kept_above_null_max", "bound_fdr"]
    with (args.out / "bins.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: ("" if row.get(k) is None else row[k]) for k in fields})
    (args.out / "summary.json").write_text(json.dumps({
        "target": TARGET, "min_kept": MIN_KEPT, "seeds": list(SEEDS),
        "bins": [list(b) for b in BINS], "finer": [list(b) for b in FINER],
        "scrambles_cached": True,
        "n_scrambled_mean_per_seed": round(sum(len(s) for s, _ in nulls) / len(nulls), 1),
        "arms": {arm: {"n_real": int(len(arms[arm][0])),
                       "max_size": int(arms[arm][0].max()),
                       "T_solver": results[arm]["threshold"]["solver"]["T"],
                       "T_full": results[arm]["threshold"]["full"]["T"],
                       "threshold": results[arm]["threshold"],
                       "finer_fails_inside": results[arm]["finer_fails_inside"]}
                 for arm in ("x2", "L")},
        "arms_agree": {
            which: (results["x2"]["threshold"][which]["T"]
                    == results["L"]["threshold"][which]["T"])
            for which in ("solver", "full")},
        "T_solver": results["x2"]["threshold"]["solver"]["T"],
        "T_full": results["x2"]["threshold"]["full"]["T"],
        "T_full_unbounded": bool(results["x2"]["threshold"]["full"].get("T_unbounded")),
        "seconds": round(time.perf_counter() - clock, 1),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\n  -> {args.out}  ({time.perf_counter() - clock:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
