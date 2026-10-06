#!/usr/bin/env python3
"""Turn the engine search's JSON outputs into the report's tables. No computation, no decisions.

Everything here is formatting. The numbers come from `engine_gates.py`, `engine_scores.py`,
`string_coherence.py` and `theta_diagnostic.py`, and this script must not be able to change one --
if a figure is missing it prints a dash, so a gap in the evidence shows up as a gap in the table
rather than as a plausible-looking number.

Amendment 3 item 2 asks for the four size bands SIDE BY SIDE and, per arm, an explicit statement of
whether it keeps arm A's fine-level (3-50) performance within the margin. Both are produced here.

Usage::

    uv run scripts/engine_report_tables.py --scores S.json --gates G.json --out tables.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

#: The bands, in the order the report shows them.
BANDS = ("3-10", "11-50", "51-200", "201-500")

#: The fine level amendment 3 asks about, as a pair of bands.
FINE = ("3-10", "11-50")

#: Declared equivalence margin.
MARGIN = 0.02


def dash(value: object, spec: str = ".4f") -> str:
    """Format a figure, or a dash when it is absent.

    Args:
        value: The figure or None.
        spec: Format spec for a present figure.

    Returns:
        The formatted string.
    """
    if value is None or not isinstance(value, (int, float)):
        return "—"
    return format(float(value), spec)


def theme_counts(base: Path, arms: dict[str, str]) -> dict[str, dict[str, int]]:
    """Themes per size band per arm, counted from the exported members.

    Args:
        base: ``data/ontology``.
        arms: Arm name to build path.

    Returns:
        Arm to band label to count, plus ``total`` and the over-500 tail.
    """
    edges = [(3, 10), (11, 50), (51, 200), (201, 500), (501, 3125)]
    out: dict[str, dict[str, int]] = {}
    for name, path in arms.items():
        members = base / path / "members.tsv"
        if not members.is_file():
            continue
        sizes: dict[str, int] = defaultdict(int)
        with members.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                sizes[row["node"]] += 1
        got: dict[str, int] = {f"{lo}-{hi}": 0 for lo, hi in edges}
        got[">3125"] = 0
        for size in sizes.values():
            for lo, hi in edges:
                if lo <= size <= hi:
                    got[f"{lo}-{hi}"] += 1
                    break
            else:
                if size > 3125:
                    got[">3125"] += 1
        got["total"] = len(sizes)
        out[name] = got
    return out


def main(argv: list[str] | None = None) -> int:
    """Write the tables.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--gates", type=Path, default=None)
    parser.add_argument("--string", type=Path, default=None)
    parser.add_argument("--theta", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    scores = json.loads(args.scores.read_text())
    arms = scores["arms"]
    auroc, recovery, ci = scores["auroc"], scores["recovery"], scores["ci"]
    verdict = scores["verdict"]
    lines: list[str] = []

    # ---- gates
    if args.gates and args.gates.is_file():
        gates = json.loads(args.gates.read_text())
        lines += ["## §3.1 Gates", "",
                  "| arm | engine | nodes | G1 overall FDR | G1 worst stratum | "
                  "G2 stability | G3 unplaced | G4 coherence | gates | eligible |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for name, got in gates["arms"].items():
            if not got.get("built"):
                lines.append(f"| **{name}** | — | *not built* | — | — | — | — | — | — | no |")
                continue
            flags = " ".join(
                f"{k}{'✓' if v else '✗'}" for k, v in (got.get("gates") or {}).items()
            )
            lines.append(
                f"| **{name}** | {got.get('engine', '—')} | {got.get('nodes') or 0:,} | "
                f"{dash(got.get('g1_overall_fdr'), '.5f')} | "
                f"{dash(got.get('g1_worst_stratum'))} | "
                f"{dash(got.get('g2_stability'), '.3f')} | "
                f"{dash(got.get('g3_unplaced_share'), '.4f')} | "
                f"{dash(got.get('g4_fraction'), '.3f')} | {flags} | "
                f"{'**yes**' if got.get('eligible') else 'no'} |"
            )
        thresholds = gates["thresholds"]
        lines += ["", f"Thresholds: G1 ≤ {thresholds['fdr_overall']} overall and "
                      f"≤ {thresholds['fdr_stratum']} per stratum; G2 within "
                      f"{thresholds['stability_slack']} of arm A; G3 ≤ "
                      f"{thresholds['unplaced_share']}; G4 within 0.05 of arm A.", ""]

    # ---- theme counts
    paths = {name: p for name, p in (
        ("A", "v0.3/recurrent_dag_10770"), ("B", "v0.3x_engines/leiden"),
        ("B2", "v0.3x_engines/leiden_persistent"), ("C", "v0.3x_engines/pooled"),
        ("G", "v0.3x_engines/bisect"), ("H", "v0.3x_engines/infomap"),
    ) if name in arms}
    counts = theme_counts(args.data / "ontology", paths)
    if counts:
        lines += ["## §3.6 Themes per size band (reported, not decisive)", "",
                  "| arm | 3–10 | 11–50 | 51–200 | 201–500 | 501–3,125 | >3,125 | total | "
                  "share 51–500 |", "|---|---|---|---|---|---|---|---|---|"]
        for name in arms:
            got = counts.get(name)
            if not got:
                continue
            mid = got["51-200"] + got["201-500"]
            share = mid / got["total"] if got["total"] else 0.0
            lines.append(
                f"| **{name}** | {got['3-10']:,} | {got['11-50']:,} | {got['51-200']:,} | "
                f"{got['201-500']:,} | {got['501-3125']:,} | {got['>3125']:,} | "
                f"{got['total']:,} | {share:.1%} |"
            )
        lines.append("")

    # ---- the 16 scores, four bands side by side
    lines += ["## §3.2 The 16 primary scores, all four bands side by side", "",
              "Band-restricted specificity AUROC. CIs are the **paired** cluster bootstrap over "
              f"curated parents, {scores['resamples']:,} resamples, seed {scores['seed']}, "
              f"stated as (arm − {scores['reference']}).", ""]
    for source in ("Reactome", "GO"):
        for gene in ("zero-gene", "pooled"):
            lines += [f"### {source} siblings, {gene}", "",
                      "| arm | " + " | ".join(BANDS) + " |", "|---|" + "---|" * len(BANDS)]
            for name in arms:
                cells = []
                for band in BANDS:
                    key = f"{source}|{gene}|{band}"
                    point = auroc.get(key, {}).get(name)
                    if point is None:
                        cells.append("—")
                        continue
                    text = f"{point:.4f}"
                    bounds = ci.get(key, {}).get(name)
                    if bounds:
                        text += f"<br><sub>[{bounds[0]:+.4f}, {bounds[1]:+.4f}]</sub>"
                    cells.append(text)
                lines.append(f"| **{name}** | " + " | ".join(cells) + " |")
            lines.append("")

    # ---- amendment 3 item 2: does each arm keep A's fine level?
    lines += ["## §3.3 Does each arm keep arm A's fine-level (3–50) performance?", "",
              f"Amendment 3 item 2. An arm **keeps** the fine level if, in every 3–10 and 11–50 "
              f"cell, it is not worse than A by more than the margin of {MARGIN} with the paired "
              "CI excluding zero. Eight cells per arm.", "",
              "| arm | fine cells worse than A beyond the margin | verdict |", "|---|---|---|"]
    for name in arms:
        if name == scores["reference"]:
            lines.append(f"| **{name}** | — | *the reference* |")
            continue
        breaches = []
        for source in ("Reactome", "GO"):
            for gene in ("zero-gene", "pooled"):
                for band in FINE:
                    key = f"{source}|{gene}|{band}"
                    point = auroc.get(key, {}).get(name)
                    ref = auroc.get(key, {}).get(scores["reference"])
                    bounds = ci.get(key, {}).get(name)
                    if None in (point, ref) or not bounds:
                        continue
                    if (point - ref) < -MARGIN and bounds[1] < 0.0:
                        breaches.append(f"{source} {gene} {band} ({point - ref:+.4f})")
        lines.append(
            f"| **{name}** | {', '.join(breaches) if breaches else 'none'} | "
            f"{'**KEEPS A’s fine level**' if not breaches else '**loses the fine level**'} |"
        )
    lines.append("")

    # ---- dominance and max-min
    lines += ["## §3.4 Dominance and max-min", "",
              f"Eligible: **{', '.join(verdict['eligible']) or 'NONE'}**", ""]
    if verdict["dominated"]:
        lines += ["| arm | dominated by |", "|---|---|"]
        lines += [f"| **{x}** | {', '.join(ys)} |" for x, ys in verdict["dominated"].items()]
    else:
        lines.append("No eligible arm is dominated.")
    lines += ["", "| arm | shortfall | worst cell |", "|---|---|---|"]
    for name in verdict["ranked"]:
        lines.append(f"| **{name}** | {verdict['shortfall'][name]:+.4f} | "
                     f"`{verdict['worst_cell'][name]}` |")
    lines += ["", "## §3.5 The verdict", ""]
    if verdict["winner"] is None:
        lines.append("> **Under the declared rule, no arm passes the gates.**")
    else:
        lines.append(f"> **Under the declared rule, the candidate is "
                     f"{verdict['winner']}.**")
        if len(verdict.get("tied_within_0.01", [])) > 1:
            lines.append("")
            lines.append(f"Tied within 0.01: {', '.join(verdict['tied_within_0.01'])} — "
                         "broken on knobs, then on wall time including calibration.")
    lines += ["", "The winner is a **candidate only**. Adoption waits for tests 5 and 6 against "
                  "THEMA v0.3 and HiDeF under a separately declared rule.", ""]

    # ---- recovery, reported only
    lines += ["## §3.7 Recovery by band (reported, not decisive)", "",
              "Share of sibling pairs with any shared theme inside the band.", ""]
    for source in ("Reactome", "GO"):
        lines += [f"### {source}, zero-gene", "",
                  "| arm | " + " | ".join(BANDS) + " |", "|---|" + "---|" * len(BANDS)]
        for name in arms:
            cells = [dash(recovery.get(f"{source}|zero-gene|{b}", {}).get(name), ".1%")
                     for b in BANDS]
            lines.append(f"| **{name}** | " + " | ".join(cells) + " |")
        lines.append("")

    # ---- G4 detail
    if args.string and args.string.is_file():
        g4 = json.loads(args.string.read_text())
        lines += ["## §3.8 G4 detail: STRING coherence per band", "",
                  f"STRING v12, combined score ≥ {g4['min_score']}, "
                  f"{g4['string_genes']:,} genes and {g4['string_edges']:,} edges. "
                  f"{g4['null_sets']} size-matched null sets, seed {g4['null_seed']}, "
                  f"p < {g4['alpha']}.", "",
                  "| arm | themes tested | overall | " + " | ".join(BANDS) + " |",
                  "|---|---|---|" + "---|" * len(BANDS)]
        for name, got in g4["arms"].items():
            cells = [dash((got["per_band"].get(b) or {}).get("fraction"), ".1%") for b in BANDS]
            lines.append(f"| **{name}** | {got['themes_tested']:,} | "
                         f"{got['fraction_p_lt_alpha']:.1%} | " + " | ".join(cells) + " |")
        lines.append("")

    # ---- theta diagnostic
    if args.theta and args.theta.is_file():
        diag = json.loads(args.theta.read_text())
        lines += ["## §3.9 LABELLED DIAGNOSTIC — arm A's middle at a looser theta", "",
                  "**Not decisive, and an UPPER BOUND**: the floors are not re-solved at the "
                  "loosened thetas, and a lower theta raises support on the scrambled null too, so "
                  "the real floors would be higher and fewer candidates would pass.", "",
                  "| theta | pool | 51–500 candidates | pass the floors | still 51–500 after "
                  "completion |", "|---|---|---|---|---|"]
        for key, got in diag["thetas"].items():
            lines.append(
                f"| {key} | {got['pool']:,} | {got['mid_candidates']:,} | "
                f"{got['mid_passing_floors']:,} | "
                f"{got['mid_passing_and_still_mid_after_completion']:,} |"
            )
        lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> {args.out} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
