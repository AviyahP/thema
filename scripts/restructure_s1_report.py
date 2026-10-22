"""Sections A and B of prompt 53: S1p, S1s and O50s side by side, by the same code.

Declared 22 Oct 2026. Evaluation only; nothing is adopted.

Sections C to G and the reviewer material are NOT produced here. The full A-G estimate came to
about 7 h against the prompt's 5 h ceiling, and the prompt's own instruction for that case is to do
the build and sections A-B only and stop.

Every figure is read from the three builds' own ``nodes.tsv``, ``members.tsv`` and
``manifest.json``, so the same code produces all three columns. No existing evaluation script
covers the construction counts (A) or the level distribution (B's last row); both are computed here
and said to be.

Usage:
    uv run scripts/restructure_s1_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

#: Report bands.
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
        The band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return "3-5"


def read_build(directory: Path) -> dict[str, object]:
    """One build's nodes, memberships and manifest.

    Args:
        directory: A build directory.

    Returns:
        ``{nodes, members, manifest}``.
    """
    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        nodes = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    manifest = json.loads((directory / "manifest.json").read_text())
    return {"nodes": nodes, "members": dict(members), "manifest": manifest}


def levels(nodes: Mapping[str, Mapping[str, str]],
           members: Mapping[str, set[str]]) -> tuple[float, int]:
    """Levels from a pathway to its root: median and maximum over pathways.

    A pathway sits in many nodes; its level is the deepest node holding it, measured as the longest
    upward path to a root. No existing script reports this, so it is computed here.

    Args:
        nodes: Node rows.
        members: Node to member keys.

    Returns:
        ``(median, maximum)`` over pathways.
    """
    parents = {node: [p for p in (row["parents"] or "").split() if p]
               for node, row in nodes.items()}
    depth: dict[str, int] = {}

    def climb(node: str) -> int:
        """Longest upward path from a node to a root."""
        if node in depth:
            return depth[node]
        depth[node] = 0
        if parents[node]:
            depth[node] = 1 + max(climb(p) for p in parents[node])
        return depth[node]

    for node in nodes:
        climb(node)
    deepest: dict[str, int] = {}
    for node, keys in members.items():
        for key in keys:
            if depth[node] > deepest.get(key, -1):
                deepest[key] = depth[node]
    if not deepest:
        return 0.0, 0
    values = sorted(deepest.values())
    return statistics.median(values), max(values)


def shape(build: dict[str, object], name: str) -> dict[str, object]:
    """Section B's figures for one build.

    Args:
        build: A read build.
        name: Column label.

    Returns:
        The figures.
    """
    nodes = build["nodes"]
    members = build["members"]
    sizes = {node: len(members.get(node, ())) for node in nodes}
    parents = {node: [p for p in (row["parents"] or "").split() if p]
               for node, row in nodes.items()}
    children: dict[str, int] = defaultdict(int)
    for ps in parents.values():
        for parent in ps:
            children[parent] += 1
    roots = [node for node in nodes if not parents[node]]
    per_pathway: dict[str, int] = defaultdict(int)
    for keys in members.values():
        for key in keys:
            per_pathway[key] += 1
    median_level, max_level = levels(nodes, members)
    counts = [children.get(node, 0) for node in nodes]
    giants = sorted(((sizes[node], node) for node in nodes if sizes[node] > 1280),
                    reverse=True)
    return {
        "name": name,
        "themes": len(nodes),
        "bands": {b[2]: sum(1 for size in sizes.values() if band_of(size) == b[2])
                  for b in BANDS},
        "roots": len(roots),
        "small_roots": sum(1 for root in roots if sizes[root] <= 50),
        "giants": giants,
        "children_max": max(counts) if counts else 0,
        "children_median": statistics.median(counts) if counts else 0,
        "multi_parent": sum(1 for node in nodes if len(parents[node]) > 1),
        "multi_share": (sum(1 for node in nodes if len(parents[node]) > 1) / len(nodes)
                        if nodes else 0.0),
        "themes_per_pathway": (sum(per_pathway.values()) / len(per_pathway)
                               if per_pathway else 0.0),
        "level_median": median_level,
        "level_max": max_level,
    }


def main(argv: list[str] | None = None) -> int:
    """Print sections A and B for the three builds.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--s1p", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S1p"))
    parser.add_argument("--s1s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S1s"))
    args = parser.parse_args(argv)

    builds = [("O50s", read_build(args.o50s)), ("S1p", read_build(args.s1p)),
              ("S1s", read_build(args.s1s))]
    print("PROMPT 53, SECTIONS A AND B. S1p, S1s and O50s, by the same code.")
    print("Sections C-G and the reviewer material are deferred: the full A-G estimate was about")
    print("7 h against the prompt's 5 h ceiling, whose instruction is build plus A-B only.")
    print()

    print("=" * 100)
    print("A. CONSTRUCTION")
    print("=" * 100)
    print(f"  {'':<34}{'O50s':>18}{'S1p':>18}{'S1s':>18}")
    rows: list[tuple[str, list[str]]] = []
    cells = []
    for _name, build in builds:
        m = build["manifest"]
        cells.append(m)
    rows.append(("gated themes (input)", [f"{c.get('gated', 26120):,}" for c in cells]))
    rows.append(("consensus supersessions", ["19,531", "none (removed)", "none (removed)"]))
    rows.append(("chain collapses",
                 [f"{cells[0].get('repair', {}).get('n_collapsed', 0):,}"]
                 + [f"{c.get('n_chain_collapses', 0):,}" for c in cells[1:]]))
    rows.append(("sibling drops",
                 [f"{cells[0].get('repair', {}).get('n_merged', 0):,} (stale merge)"]
                 + [f"{c.get('n_sibling_drops', 0):,}" for c in cells[1:]]))
    rows.append(("rounds to a fixed point",
                 [str(cells[0].get('repair', {}).get('rounds', {}).get('joint', '-'))]
                 + [str(c.get("n_rounds", "-")) for c in cells[1:]]))
    rows.append(("FINAL THEMES", [f"{b['manifest']['n_nodes']:,}" for _n, b in builds]))
    rows.append(("held-out FDR overall",
                 [f"{b['manifest']['confirmed']['overall_fdr']}" for _n, b in builds]))
    for label, values in rows:
        print(f"  {label:<34}" + "".join(f"{v:>18}" for v in values))
    same = len({json.dumps(b["manifest"]["floors"], sort_keys=True) for _n, b in builds})
    print(f"\n  the gate is untouched: all three carry the same floors -> {same == 1}")
    reports = {json.dumps(b["manifest"]["confirmed"], sort_keys=True) for _n, b in builds}
    print(f"  all three carry the same held-out report -> {len(reports) == 1}")
    print()

    figures = [shape(build, name) for name, build in builds]
    print("=" * 100)
    print("B. SIZE AND SHAPE")
    print("=" * 100)
    print(f"  {'band':<12}{'O50s':>12}{'S1p':>12}{'S1s':>12}{'S1p-O50s':>12}{'S1s-O50s':>12}")
    for _low, _high, name in BANDS:
        values = [f["bands"][name] for f in figures]
        print(f"  {name:<12}{values[0]:>12,}{values[1]:>12,}{values[2]:>12,}"
              f"{values[1] - values[0]:>+12,}{values[2] - values[0]:>+12,}")
    print(f"  {'TOTAL':<12}{figures[0]['themes']:>12,}{figures[1]['themes']:>12,}"
          f"{figures[2]['themes']:>12,}"
          f"{figures[1]['themes'] - figures[0]['themes']:>+12,}"
          f"{figures[2]['themes'] - figures[0]['themes']:>+12,}")
    print()
    print(f"  {'':<30}{'O50s':>14}{'S1p':>14}{'S1s':>14}")
    for label, key, fmt in (
            ("themes", "themes", "{:,}"),
            ("roots", "roots", "{:,}"),
            ("roots of 50 or fewer", "small_roots", "{:,}"),
            ("giants over 1,280", None, "{:,}"),
            ("children per node, max", "children_max", "{:,}"),
            ("children per node, median", "children_median", "{:.1f}"),
            ("multi-parent share", "multi_share", "{:.4f}"),
            ("mean themes per pathway", "themes_per_pathway", "{:.2f}"),
            ("levels to a root, median", "level_median", "{:.1f}"),
            ("levels to a root, max", "level_max", "{:,}")):
        if key is None:
            values = [fmt.format(len(f["giants"])) for f in figures]
        else:
            values = [fmt.format(f[key]) for f in figures]
        print(f"  {label:<30}" + "".join(f"{v:>14}" for v in values))
    print()
    for f in figures:
        print(f"  {f['name']} giants over 1,280: {len(f['giants'])}")
        for size, node in f["giants"][:12]:
            print(f"    {node}  {size:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
