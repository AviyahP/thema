#!/usr/bin/env python3
"""v0.4 §1: assemble the ablation table and apply the declared KEEP/REMOVE rule.

The rule, from §0: a v0.3 stage is KEPT only if removing it

1. worsens a cell beyond the 2-point margin with a paired CI excluding zero, OR
2. pushes held-out FDR (scrambles 4001-4002) over the v0.3 caps, OR
3. drops stability between run halves by more than 2 points.

Otherwise it is REMOVED. **Decisions use the TUNING half of the curated sets only.** Theme count is
reported for every arm, and a recall gain arriving with a large rise in theme count is flagged
rather than credited -- which matters here because removing completion triples the families through
the gate.

Usage::

    uv run scripts/v04_ablation_table.py --out TABLE.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#: v0.3's declared caps, and the stability tolerance.
MAX_FDR_OVERALL = 0.01
MAX_FDR_STRATUM = 0.02
STABILITY_DROP = 0.02

#: Which ablation removes which stage, in the brief's order.
ORDER: tuple[tuple[str, str], ...] = (
    ("no_size_cap", "size cap"),
    ("TOL", "TOL extras-only rule -> symmetric Jaccard theta"),
    ("no_stray", "STRAY"),
    ("no_completion", "completion"),
    ("flat_merge", "greedy seed absorption -> flat merge at theta"),
    ("single_floor", "per-size floors -> a single floor"),
    ("partial_containment", "strict containment -> partial >= 0.9 (report-only)"),
)

#: Ablations whose floors were re-solved because the gate's input changed.
RECALIBRATED = frozenset({"no_size_cap", "no_completion", "flat_merge"})


def stability(left: Path, right: Path) -> float | None:
    """Worse-direction final-theme match between two half-builds.

    Args:
        left: The rows 1-100 build.
        right: The rows 101-200 build.

    Returns:
        The worse-direction share at Jaccard >= 0.70, or None if either half is missing.
    """
    if not (left / "nodes.tsv").is_file() or not (right / "nodes.tsv").is_file():
        return None
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch) / "m.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "theme_match.py"),
             str(left), str(right), "--out", str(out)],
            capture_output=True, text=True, check=False)
        if not out.is_file():
            return None
        got = json.loads(out.read_text())
    key = f"share_ge_{got.get('theta', 0.7):.2f}"
    both = [got[d][key] for d in ("forward", "backward") if key in got.get(d, {})]
    return min(both) if both else None


def main(argv: list[str] | None = None) -> int:
    """Build the table and decide each stage.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--scores", type=Path, required=True,
                        help="the v04_score.py JSON for the TUNING half")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    base = args.data / "ontology"
    ablate = base / "v0.3" / "ablate"
    scored = json.loads(args.scores.read_text())["arms"]

    report: dict = {"rule": "KEEP if removal worsens a cell beyond the margin with the CI "
                            "excluding 0, or breaks the FDR caps, or drops stability by > 2 points",
                    "caps": {"fdr_overall": MAX_FDR_OVERALL, "fdr_stratum": MAX_FDR_STRATUM,
                             "stability_drop": STABILITY_DROP},
                    "half": "tuning", "stages": {}}

    base_floors = json.loads((ablate / "baseline" / "floors.json").read_text())
    base_fdr = base_floors["confirmed"]["overall_fdr"]
    base_stab = stability(base / "v0.4" / "ablate_baseline_r1-100",
                          base / "v0.4" / "ablate_baseline_r101-200")
    base_themes = scored.get("baseline", {}).get("themes")
    print(f"BASELINE  held-out FDR {base_fdr}  stability "
          f"{'n/a' if base_stab is None else f'{base_stab:.3f}'}  themes {base_themes}")

    print(f"\n  {'stage removed':<46}{'themes':>8}{'FDR':>9}{'worst':>8}"
          f"{'stab':>7}  verdict")
    for name, label in ORDER:
        if name == "TOL":
            # A no-op by construction: the frozen build already runs the symmetric theta branch and
            # TOL is inert in it. Recorded rather than measured, so a spurious zero effect is not
            # read as evidence the stage is removable.
            report["stages"][name] = {
                "stage": label, "measured": False,
                "verdict": "ALREADY ABSENT",
                "why": "v0.3 runs the symmetric theta branch; TOL is inert, so there is nothing "
                       "to remove. Established 5 Oct, DECISIONS.md.",
            }
            print(f"  {label:<46}{'--':>8}{'--':>9}{'--':>8}{'--':>7}  ALREADY ABSENT")
            continue

        floors_path = ablate / name / "floors.json"
        if not floors_path.is_file():
            print(f"  {label:<46}{'not built':>8}")
            report["stages"][name] = {"stage": label, "verdict": "NOT BUILT"}
            continue
        floors = json.loads(floors_path.read_text())
        fdr = floors["confirmed"]["overall_fdr"]
        worst = max((e.get("heldout_fdr") for e in floors["confirmed"]["strata"]
                     if e.get("heldout_fdr") is not None), default=None)
        stab = stability(base / "v0.4" / f"ablate_{name}_r1-100",
                         base / "v0.4" / f"ablate_{name}_r101-200")
        row = scored.get(name, {})
        themes = row.get("themes")
        worsened = row.get("worsened_beyond_margin", [])

        reasons = []
        if fdr is not None and fdr > MAX_FDR_OVERALL:
            reasons.append(f"held-out FDR {fdr} over {MAX_FDR_OVERALL}")
        if worst is not None and worst > MAX_FDR_STRATUM:
            reasons.append(f"worst stratum {worst} over {MAX_FDR_STRATUM}")
        if stab is not None and base_stab is not None and base_stab - stab > STABILITY_DROP:
            reasons.append(f"stability {stab:.3f} against {base_stab:.3f}")
        if worsened:
            reasons.append(f"{len(worsened)} cell(s) worse beyond the margin")
        verdict = "KEPT" if reasons else "REMOVED"
        flag = ""
        if themes and base_themes and themes > 1.5 * base_themes:
            flag = f"  FLAG: {themes / base_themes:.1f}x the theme count"
        report["stages"][name] = {
            "stage": label, "measured": True, "recalibrated": name in RECALIBRATED,
            "themes": themes, "heldout_fdr": fdr, "worst_stratum": worst,
            "stability": stab, "worsened_cells": worsened,
            "verdict": verdict, "reasons": reasons, "theme_count_flag": bool(flag),
        }
        print(f"  {label:<46}{(themes or 0):>8,}"
              f"{(fdr if fdr is not None else float('nan')):>9.5f}"
              f"{(worst if worst is not None else float('nan')):>8.4f}"
              f"{(stab if stab is not None else float('nan')):>7.3f}  {verdict}{flag}")
        for reason in reasons:
            print(f"      because: {reason}")

    kept = [n for n, v in report["stages"].items()
            if v.get("verdict") == "KEPT"]
    removed = [n for n, v in report["stages"].items() if v.get("verdict") == "REMOVED"]
    report["kept"] = kept
    report["removed"] = removed
    print(f"\n  KEPT:    {', '.join(kept) or 'none'}")
    print(f"  REMOVED: {', '.join(removed) or 'none'}")
    print(f"  floors were re-solved for: {', '.join(sorted(RECALIBRATED))} "
          f"(their gate input changed); the others reuse v0.3's cached sides")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
