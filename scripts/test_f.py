#!/usr/bin/env python3
"""Test F: do the scramble floors earn their cost? Steps 2, 3, 4 and 6.

The question the protocol asks, and the reason it runs first: the manifests show the solved floors
bind only on small themes -- arm A raises the declared 0.33 minimum for sizes 3-5 only, arm B drops
sizes 3-4 and raises 5-9 -- so for everything larger the fixed 0.33 already decides. If a fixed cut
holds the same FDR, the 15 scramble sides per build are pure cost, and every later build in the
protocol gets cheaper.

**Every FDR here comes from the build's own `confirm()`**, not a reimplementation. The fixed cut is
expressed as a `solved`-shaped list with the same threshold in every stratum, which is exactly how
the build itself applies a floor, so the comparison is between two thresholds and nothing else.

**Step 2 is a declared SECOND READ of held-out seeds 4001-4005.** The protocol allows it and
labels it: no threshold is fitted at the fixed cut, so every seed is valid test data for it, and
the cut was declared in the protocol rather than chosen after seeing the FDR. Step 4's 3-seed
floors ARE fitted, on 3001-3003, and are confirmed on 4001-4005 -- the same held-out set a third
time, and reported as such.

Step 5 (transfer to new universes) is deferred to E1/E2: it needs universes that do not exist.

Usage::

    uv run scripts/test_f.py --arm A=ward --arm B=leiden
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Theme-size bands the protocol reports per.
BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))

#: The declared fixed cut.
FIXED_CUT = 0.33

#: The three seeds step 4 solves from, and the held-out five.
THREE = (3001, 3002, 3003)


def load_rows(path: Path) -> list[tuple[int, float]]:
    """Read one cached side's (size, support) rows.

    Args:
        path: The side's ``.npz``.

    Returns:
        One ``(size, support)`` pair per family.
    """
    with np.load(path) as handle:
        blocks = handle["blocks"]
        supports = handle["supports"]
    sizes = np.bitwise_count(blocks).sum(axis=1).astype(np.int64)
    return list(zip(sizes.tolist(), supports.tolist(), strict=True))


def band_counts(directory: Path) -> dict[str, int]:
    """Themes per size band for a built ontology.

    Args:
        directory: A build directory.

    Returns:
        Band label to theme count, plus the total and the over-500 tail.
    """
    import csv
    from collections import defaultdict

    sizes: dict[str, int] = defaultdict(int)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            sizes[row["node"]] += 1
    out = {f"{lo}-{hi}": 0 for lo, hi in BANDS}
    out["501+"] = 0
    for size in sizes.values():
        for lo, hi in BANDS:
            if lo <= size <= hi:
                out[f"{lo}-{hi}"] += 1
                break
        else:
            if size > 500:
                out["501+"] += 1
    out["total"] = len(sizes)
    return out


def main(argv: list[str] | None = None) -> int:
    """Run steps 2, 3, 4 and 6.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import (
        CALIBRATION_SEEDS,
        HELDOUT_SEEDS,
        INCLUSION_CUT,
        MAX_FDR_OVERALL,
        MAX_FDR_STRATUM,
        STRATA,
        confirm,
        engine_cut_key,
        solve,
        stratum_of,
    )
    from build_trees_10770 import peak_mb
    from cut_trees import cap_for

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--arm", action="append", default=[], help="NAME=engine")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)

    report: dict = {
        "fixed_cut": FIXED_CUT, "runs": args.runs,
        "max_fdr_overall": MAX_FDR_OVERALL, "max_fdr_stratum": MAX_FDR_STRATUM,
        "calibration_seeds": list(CALIBRATION_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "three_seeds": list(THREE),
        "step5": "deferred to E1/E2: needs universes that do not exist",
        "arms": {},
    }
    print(f"TEST F  n={n:,}, cap {cap:,}, inclusion {INCLUSION_CUT}, "
          f"fixed cut {FIXED_CUT}, {args.runs} runs", flush=True)
    print(f"  FDR caps: {MAX_FDR_OVERALL} overall, {MAX_FDR_STRATUM} per stratum", flush=True)

    for spec in args.arm:
        name, engine = spec.split("=", 1)
        key = engine_cut_key(cap, INCLUSION_CUT, engine)
        side_dir = trees / "completions" / key
        clock = time.perf_counter()
        real = load_rows(side_dir / f"real_r00001-{args.runs:05d}.npz")
        cal = [load_rows(side_dir / f"seed{s:05d}_n{args.runs:03d}.npz") for s in CALIBRATION_SEEDS]
        held = [load_rows(side_dir / f"seed{s:05d}_n{args.runs:03d}.npz") for s in HELDOUT_SEEDS]
        print(f"\n{'=' * 104}\nARM {name}  engine {engine}  "
              f"({len(real):,} real families, {len(cal)} calibration + {len(held)} held-out sides, "
              f"loaded in {time.perf_counter() - clock:.0f}s)\n{'=' * 104}", flush=True)

        got: dict = {"engine": engine, "real_families": len(real)}

        # ---- STEP 2: FDR at the fixed cut, on all 15 sides.
        fixed = [
            {"stratum": f"{low}-{high}" if high < 10**9 else f"{low}+",
             "real": sum(1 for size, _s in real if stratum_of(size) == index),
             "floor": None, "effective": FIXED_CUT, "calibration_fdr": None}
            for index, (low, high) in enumerate(STRATA)
        ]
        all15 = confirm(real, cal + held, fixed)
        cal_only = confirm(real, cal, fixed)
        held_only = confirm(real, held, fixed)
        print(f"\n  STEP 2 -- FDR at the FIXED CUT {FIXED_CUT}, every stratum, no calibration")
        print(f"    {'stratum':<9}{'real':>8}{'all 15':>10}{'3001-3010':>12}"
              f"{'4001-4005':>12}   verdict")
        for a, c, h in zip(all15["strata"], cal_only["strata"], held_only["strata"], strict=True):
            def show(v: float | None) -> str:
                """Format an FDR or a dash.

                Args:
                    v: The FDR or None.

                Returns:
                    A fixed-width string.
                """
                return "   --" if v is None else f"{v:.5f}"
            bad = a["heldout_fdr"] is not None and a["heldout_fdr"] > MAX_FDR_STRATUM
            print(f"    {a['stratum']:<9}{a['real']:>8,}{show(a['heldout_fdr']):>10}"
                  f"{show(c['heldout_fdr']):>12}{show(h['heldout_fdr']):>12}   "
                  f"{'OVER ' + str(MAX_FDR_STRATUM) if bad else 'ok'}")
        print(f"    overall, all 15 sides: {all15['overall_fdr']} against {MAX_FDR_OVERALL}  "
              f"({all15['overall_real']:,} real, {all15['overall_null']} null)")
        print(f"    4001-4005 alone (SECOND READ, labelled): {held_only['overall_fdr']}")
        worst = max((s["heldout_fdr"] for s in all15["strata"]
                     if s["heldout_fdr"] is not None), default=None)
        passes = (all15["overall_fdr"] is not None
                  and all15["overall_fdr"] <= MAX_FDR_OVERALL
                  and worst is not None and worst <= MAX_FDR_STRATUM)
        got["step2"] = {"all15": all15, "calibration_only": cal_only, "heldout_only": held_only,
                        "worst_stratum": worst, "passes": bool(passes)}
        print(f"    => fixed cut {'PASSES' if passes else 'FAILS'} "
              f"(overall {all15['overall_fdr']}, worst stratum {worst})")

        # ---- STEP 4: three seeds instead of ten.
        ten = solve(real, cal)
        three = solve(real, [cal[list(CALIBRATION_SEEDS).index(s)] for s in THREE])
        ten_held = confirm(real, held, ten)
        three_held = confirm(real, held, three)
        print(f"\n  STEP 4 -- floors from 3 seeds {THREE} beside the 10-seed floors")
        print(f"    {'stratum':<9}{'10-seed':>10}{'eff':>8}{'held FDR':>10}"
              f"{'3-seed':>10}{'eff':>8}{'held FDR':>10}")
        for t, h3, th, hh in zip(ten, three, ten_held["strata"], three_held["strata"],
                                 strict=True):
            def f(v: float | None, spec: str = ".3f") -> str:
                """Format a floor or a dash.

                Args:
                    v: The value or None.
                    spec: Format spec.

                Returns:
                    A string.
                """
                return "DROP" if v is None else format(v, spec)
            print(f"    {t['stratum']:<9}{f(t['floor']):>10}{f(t['effective']):>8}"
                  f"{f(th['heldout_fdr'], '.5f'):>10}"
                  f"{f(h3['floor']):>10}{f(h3['effective']):>8}"
                  f"{f(hh['heldout_fdr'], '.5f'):>10}")
        w3 = max((s["heldout_fdr"] for s in three_held["strata"]
                  if s["heldout_fdr"] is not None), default=None)
        three_ok = (three_held["overall_fdr"] is not None
                    and three_held["overall_fdr"] <= MAX_FDR_OVERALL
                    and w3 is not None and w3 <= MAX_FDR_STRATUM)
        print(f"    10-seed overall held-out FDR {ten_held['overall_fdr']}, "
              f"3-seed {three_held['overall_fdr']} (worst stratum {w3})")
        print(f"    => 3 seeds {'PASS' if three_ok else 'FAIL'} the held-out caps")
        got["step4"] = {"ten_seed": ten, "three_seed": three,
                        "ten_heldout": ten_held, "three_heldout": three_held,
                        "three_worst_stratum": w3, "three_passes": bool(three_ok)}

        report["arms"][name] = got

    # ---- STEP 6: HiDeF on scrambled data.
    print(f"\n{'=' * 104}\nSTEP 6 -- HiDeF on scrambled data, from the existing null builds"
          f"\n{'=' * 104}")
    hidef: dict = {}
    real_hidef = root / "hidef_10770_k15"
    real_bands = band_counts(real_hidef) if (real_hidef / "members.tsv").is_file() else None
    for seed in (4001, 4002):
        d = root / f"hidef_null_seed{seed}_k15"
        if not (d / "members.tsv").is_file():
            print(f"  seed {seed}: build missing")
            continue
        hidef[str(seed)] = band_counts(d)
    if hidef and real_bands:
        print(f"    {'band':<10}{'real':>8}" + "".join(f"{'null ' + s:>12}" for s in hidef)
              + f"{'mean null':>11}{'implied FDR':>13}")
        for band in [f"{lo}-{hi}" for lo, hi in BANDS] + ["501+", "total"]:
            nulls = [hidef[s][band] for s in hidef]
            mean = sum(nulls) / len(nulls)
            r = real_bands[band]
            fdr = f"{mean / r:.5f}" if r else "   --"
            print(f"    {band:<10}{r:>8,}" + "".join(f"{v:>12,}" for v in nulls)
                  + f"{mean:>11.1f}{fdr:>13}")
    report["step6"] = {"real": real_bands, "nulls": hidef}

    print(f"\n  peak {peak_mb():.0f} MB")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
