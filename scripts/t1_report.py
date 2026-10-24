"""Sections A to E of prompt 57: T1 next to O50s, by the same code.

Declared 23 Oct 2026. Evaluation only; nothing is adopted. Readings, stability, recall and the other
evaluation sections are not run, as the prompt says.

Two definitions are stated here because the prompt leaves them open and the choice changes the
numbers:

* **"losing more than 10% / 25% of its members"** is measured against the theme's size **as it left
  the gate**, before any trimming, since that is the membership the flip edited.
* **"trimmed by more than one parent"** is counted as a theme with two or more *direct* trim events.
  A theme cannot be trimmed twice by the same partner -- once it loses its single stray it is nested
  in that partner and rule 2 cannot fire on the pair again -- so the count of direct events is
  exactly the count of distinct parents that trimmed it.
* **"O50s edges that survive"** maps each O50s node to its best T1 counterpart at J >= 0.9 and asks
  whether that pair is an edge in T1. Edges whose endpoints have no counterpart cannot survive and
  are reported separately rather than silently counted as lost.

Usage:
    uv run scripts/t1_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return BANDS[0][2]


def read_build(directory: Path) -> dict[str, object]:
    """Nodes, memberships, edges and manifest.

    Args:
        directory: A build directory.

    Returns:
        The build.
    """
    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    parents = {r["node"]: tuple(p for p in (r["parents"] or "").split() if p) for r in rows}
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    with (directory / "edges.tsv").open(encoding="utf-8") as handle:
        edges = [(r["child"], r["parent"]) for r in csv.DictReader(handle, delimiter="\t")]
    return {"ids": [r["node"] for r in rows], "parents": parents, "members": dict(members),
            "edges": edges,
            "manifest": json.loads((directory / "manifest.json").read_text())}


def levels(ids: Sequence[str], parents: Mapping[str, tuple[str, ...]],
           members: Mapping[str, set[str]]) -> tuple[float, int]:
    """Levels from a pathway to its root: median and maximum.

    Args:
        ids: Node ids.
        parents: Immediate parents.
        members: Node to member keys.

    Returns:
        ``(median, maximum)``.
    """
    depth: dict[str, int] = {}

    def climb(node: str) -> int:
        """Longest upward path to a root."""
        if node in depth:
            return depth[node]
        depth[node] = 0
        if parents[node]:
            depth[node] = 1 + max(climb(p) for p in parents[node])
        return depth[node]

    for node in ids:
        climb(node)
    deepest: dict[str, int] = {}
    for node, keys in members.items():
        for key in keys:
            if depth[node] > deepest.get(key, -1):
                deepest[key] = depth[node]
    values = sorted(deepest.values())
    return (statistics.median(values), max(values)) if values else (0.0, 0)


def best_counterpart(left: dict[str, set[str]], right: dict[str, set[str]]
                     ) -> dict[str, tuple[str, float]]:
    """For each left theme, its best-matching right theme and the Jaccard.

    Args:
        left: Themes to score.
        right: Themes to score against.

    Returns:
        Left id to ``(right id, jaccard)``.
    """
    index: dict[str, list[str]] = defaultdict(list)
    for node, keys in right.items():
        for key in keys:
            index[key].append(node)
    out: dict[str, tuple[str, float]] = {}
    for node, keys in left.items():
        counts: dict[str, int] = defaultdict(int)
        for key in keys:
            for other in index.get(key, ()):
                counts[other] += 1
        best, score = "", 0.0
        for other, inter in counts.items():
            union = len(keys) + len(right[other]) - inter
            value = inter / union if union else 0.0
            if value > score:
                best, score = other, value
        out[node] = (best, score)
    return out


def main(argv: list[str] | None = None) -> int:
    """Print sections A to E.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from restructure_s1 import gated_themes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--t1", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_T1"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--acct", type=Path,
                        default=Path("data/experiments/trim_T1_2026-10-23"))
    parser.add_argument("--runs", type=int, default=200)
    args = parser.parse_args(argv)

    got = gated_themes(args)
    gate_size = {i: len(got.members[i]) for i in range(len(got.members))}
    acct = json.loads((args.acct / "accounting.json").read_text())
    trimmed = json.loads((args.acct / "trimmed.json").read_text())
    o50s, t1 = read_build(args.frozen), read_build(args.t1)

    print("PROMPT 57, SECTIONS A TO E. T1 next to O50s, same code.")
    print("  readings, stability, recall and the other evaluation sections are not run.")
    print()
    print("=" * 104)
    print("A. EDITS: WHAT THE FLIP DID, AND WHAT IT CHANGED DOWNSTREAM")
    print("=" * 104)
    direct = acct["direct"]
    ind = acct["indirect"]
    print(f"  {'':<44}{'O50s':>14}{'T1':>14}")
    print(f"  {'rule-2 events':<44}{ind['rules_off'].get('inherited', 0):>14,}"
          f"{ind['rules_on'].get('inherited', 0):>14,}")
    print(f"  {'members ADDED by rule 2':<44}{acct['inherited_off']:>14,}{0:>14,}")
    print(f"  {'members REMOVED by rule 2':<44}{0:>14,}"
          f"{direct['members_removed'] + direct['propagated_removals']:>14,}")
    print(f"  {'  of which the pair-s own smaller theme':<44}{'-':>14}"
          f"{direct['members_removed']:>14,}")
    print(f"  {'  of which downward propagation':<44}{'-':>14}"
          f"{direct['propagated_removals']:>14,}")
    print(f"  {'themes edited directly':<44}{'-':>14}"
          f"{direct['distinct_themes_edited']:>14,}")
    print(f"  {'themes propagated into':<44}{'-':>14}"
          f"{direct['distinct_themes_propagated_into']:>14,}")
    print(f"  {'themes dropped for falling under 3':<44}{0:>14,}"
          f"{direct['themes_dropped_under_min']:>14,}")

    per_theme: dict[int, int] = defaultdict(int)
    direct_events: dict[int, int] = defaultdict(int)
    for row in trimmed:
        per_theme[row["theme"]] += 1
        if not row["propagated"]:
            direct_events[row["theme"]] += 1
    multi = sum(1 for t, n in direct_events.items() if n > 1)
    print(f"  {'themes trimmed by more than one parent':<44}{'-':>14}{multi:>14,}")
    print()
    print("  themes losing more than 10% and more than 25% of their gate-exit members.")
    print("  NOTE: these rows count every theme the flip edited, INCLUDING the "
          f"{direct['themes_dropped_under_min']:,} that were")
    print("  then dropped for falling under 3, so they must not be added to the dropped column.")
    print(f"  {'band':<12}{'themes trimmed':>16}{'>10% lost':>12}{'>25% lost':>12}"
          f"{'dropped <3':>12}")
    over10: dict[str, int] = defaultdict(int)
    over25: dict[str, int] = defaultdict(int)
    touched: dict[str, int] = defaultdict(int)
    for theme, lost in per_theme.items():
        size = gate_size.get(theme, 0)
        if not size:
            continue
        band = band_of(size)
        touched[band] += 1
        if lost / size > 0.10:
            over10[band] += 1
        if lost / size > 0.25:
            over25[band] += 1
    for _lo, _hi, band in BANDS:
        if not touched[band]:
            continue
        print(f"  {band:<12}{touched[band]:>16,}{over10[band]:>12,}{over25[band]:>12,}"
              f"{'-':>12}")
    print(f"  {'ALL':<12}{sum(touched.values()):>16,}{sum(over10.values()):>12,}"
          f"{sum(over25.values()):>12,}{direct['themes_dropped_under_min']:>12,}")
    print()
    print("  INDIRECT: later rules whose outcome the flip changed")
    print(f"  {'':<28}{'O50s':>12}{'T1':>12}{'change':>12}")
    for label, a, b in (
            ("rule 1 nested", ind["rules_off"].get("nested", 0), ind["rules_on"].get("nested", 0)),
            ("rule 3 superseded", ind["superseded_off"], ind["superseded_on"]),
            ("rule 4 coexist", ind["rules_off"].get("coexist", 0),
             ind["rules_on"].get("coexist", 0)),
            ("after consensus", ind["after_consensus_off"], ind["after_consensus_on"]),
            ("chain collapses", ind["collapsed_off"], ind["collapsed_on"]),
            ("stale merges", ind["stale_off"], ind["stale_on"]),
            ("final themes", ind["final_off"], ind["final_on"])):
        print(f"  {label:<28}{a:>12,}{b:>12,}{b - a:>+12,}")
    print()
    json.dump({"over10": dict(over10), "over25": dict(over25), "touched": dict(touched),
               "trimmed_by_multiple_parents": multi},
              (args.acct / "section_a.json").open("w"), indent=1)

    # --- B. shape ------------------------------------------------------------------------------
    print("=" * 104)
    print("B. SHAPE")
    print("=" * 104)
    builds = (("O50s", o50s), ("T1", t1))
    sizes = {name: {n: len(b["members"].get(n, ())) for n in b["ids"]} for name, b in builds}
    print(f"  {'band':<12}{'O50s':>12}{'T1':>12}{'change':>12}")
    for _lo, _hi, band in BANDS:
        a = sum(1 for s in sizes["O50s"].values() if band_of(s) == band)
        c = sum(1 for s in sizes["T1"].values() if band_of(s) == band)
        if not (a or c):
            continue
        print(f"  {band:<12}{a:>12,}{c:>12,}{c - a:>+12,}")
    print(f"  {'TOTAL':<12}{len(o50s['ids']):>12,}{len(t1['ids']):>12,}"
          f"{len(t1['ids']) - len(o50s['ids']):>+12,}")
    print()
    stats = {}
    for name, b in builds:
        kids: dict[str, int] = defaultdict(int)
        for ups in b["parents"].values():
            for parent in ups:
                kids[parent] += 1
        counts = [kids.get(n, 0) for n in b["ids"]]
        roots = [n for n in b["ids"] if not b["parents"][n]]
        per: dict[str, int] = defaultdict(int)
        for keys in b["members"].values():
            for key in keys:
                per[key] += 1
        med, mx = levels(b["ids"], b["parents"], b["members"])
        multi_p = sum(1 for n in b["ids"] if len(b["parents"][n]) > 1)
        stats[name] = [len(b["ids"]), len(roots),
                       sum(1 for r in roots if sizes[name][r] <= 50),
                       sum(1 for n in b["ids"] if sizes[name][n] > 1280),
                       max(counts) if counts else 0,
                       statistics.median(counts) if counts else 0,
                       multi_p / len(b["ids"]), med, mx, len(b["edges"])]
    labels = ("themes", "roots", "roots of 50 or fewer", "giants over 1,280",
              "children per node, max", "children per node, median", "multi-parent share",
              "levels to a root, median", "levels to a root, max", "edges")
    fmts = ("{:,}", "{:,}", "{:,}", "{:,}", "{:,}", "{:.1f}", "{:.4f}", "{:.1f}", "{:,}", "{:,}")
    print(f"  {'':<32}{'O50s':>14}{'T1':>14}")
    for i, (label, fmt) in enumerate(zip(labels, fmts, strict=True)):
        print(f"  {label:<32}" + "".join(f"{fmt.format(stats[n][i]):>14}" for n, _b in builds))
    print()
    to_t1 = best_counterpart(o50s["members"], t1["members"])
    giants = sorted(((sizes["O50s"][n], n) for n in o50s["ids"] if sizes["O50s"][n] > 1280),
                    reverse=True)
    print("  each O50s giant and its best T1 counterpart")
    print(f"  {'O50s giant':<12}{'size':>9}   {'best T1':<12}{'T1 size':>9}{'J':>8}")
    for size, node in giants:
        other, score = to_t1[node]
        print(f"  {node:<12}{size:>9,}   {other:<12}"
              f"{len(t1['members'].get(other, ())):>9,}{score:>8.3f}")
    t1_giants = sorted(((sizes["T1"][n], n) for n in t1["ids"] if sizes["T1"][n] > 1280),
                       reverse=True)
    print(f"  T1 giants over 1,280: {len(t1_giants)}"
          + ("  " + ", ".join(f"{n} {s:,}" for s, n in t1_giants) if t1_giants else ""))
    good = {n: m for n, (m, j) in to_t1.items() if j >= 0.9}
    t1_edges = {(c, p) for c, p in t1["edges"]}
    both = [(c, p) for c, p in o50s["edges"] if c in good and p in good]
    survive = sum(1 for c, p in both if (good[c], good[p]) in t1_edges)
    print(f"\n  O50s edges {len(o50s['edges']):,}; both endpoints have a T1 counterpart at "
          f"J >= 0.9 for {len(both):,}; of those {survive:,} are still an edge in T1 "
          f"= {survive / len(both):.1%}" if both else "")
    print(f"  the other {len(o50s['edges']) - len(both):,} cannot survive: at least one endpoint "
          "has no counterpart at J >= 0.9")
    print()

    # --- C. placement --------------------------------------------------------------------------
    print("=" * 104)
    print("C. PLACEMENT")
    print("=" * 104)
    universe = set(got.keys)
    placed = {name: {k for keys in b["members"].values() for k in keys} for name, b in builds}
    print(f"  {'':<48}{'O50s':>14}{'T1':>14}")
    print(f"  {'pathways in at least one theme':<48}"
          + "".join(f"{len(placed[n]):>14,}" for n, _b in builds))
    print(f"  {'  share of ' + str(len(universe)) + ' pathways':<48}"
          + "".join(f"{len(placed[n]) / len(universe):>14.2%}" for n, _b in builds))
    per_pathway = {}
    for name, b in builds:
        per: dict[str, int] = defaultdict(int)
        for keys in b["members"].values():
            for key in keys:
                per[key] += 1
        per_pathway[name] = sum(per.values()) / len(per) if per else 0.0
    print(f"  {'mean themes per pathway':<48}"
          + "".join(f"{per_pathway[n]:>14.2f}" for n, _b in builds))
    removed_keys = {got.keys[row["member"]] for row in trimmed}
    still = {k for k in removed_keys if k in placed["T1"]}
    print(f"\n  distinct pathways T1 removed from at least one theme: {len(removed_keys):,}")
    print(f"  of those, still in another T1 theme: {len(still):,} = "
          f"{len(still) / len(removed_keys):.1%}" if removed_keys else "")
    print(f"  in NO T1 theme at all: {len(removed_keys) - len(still):,}")
    print()

    # --- D. agreement --------------------------------------------------------------------------
    print("=" * 104)
    print("D. AGREEMENT: O50s THEMES WITH A T1 COUNTERPART AT J >= 0.9")
    print("=" * 104)
    print(f"  {'band':<12}{'O50s themes':>13}{'matched':>10}{'share':>9}")
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for node in o50s["ids"]:
        band = band_of(sizes["O50s"][node])
        tally[band][0] += 1
        if to_t1[node][1] >= 0.9:
            tally[band][1] += 1
    for _lo, _hi, band in BANDS:
        if not tally[band][0]:
            continue
        n, m = tally[band]
        print(f"  {band:<12}{n:>13,}{m:>10,}{m / n:>9.1%}")
    tot = sum(v[0] for v in tally.values())
    mat = sum(v[1] for v in tally.values())
    print(f"  {'ALL':<12}{tot:>13,}{mat:>10,}{mat / tot:>9.1%}")
    print()

    # --- E. the gate ---------------------------------------------------------------------------
    print("=" * 104)
    print("E. HELD-OUT FDR AT THE GATE (unchanged; confirm)")
    print("=" * 104)
    same_floors = (json.dumps(o50s["manifest"]["floors"], sort_keys=True)
                   == json.dumps(t1["manifest"]["floors"], sort_keys=True))
    same_conf = (json.dumps(o50s["manifest"]["confirmed"], sort_keys=True)
                 == json.dumps(t1["manifest"]["confirmed"], sort_keys=True))
    print(f"  O50s held-out FDR overall  {o50s['manifest']['confirmed']['overall_fdr']}")
    print(f"  T1   held-out FDR overall  {t1['manifest']['confirmed']['overall_fdr']}")
    print(f"  identical floors: {same_floors}; identical held-out report: {same_conf}")
    print(f"  gated themes, both: {len(got.members):,} -- the gate is untouched by construction")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
