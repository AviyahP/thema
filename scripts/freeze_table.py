#!/usr/bin/env python3
"""The freeze table for one build, in the shape `FROZEN.md` reports it for the frozen 1,850.

Every figure the 1,850 freeze states, computed from a build directory: shape, placement three ways,
straddlers, and test 2's comparison against the curated ontologies. Written because none of it was
in a committed script -- the 1,850's numbers were computed ad hoc -- and a confirmatory build has to
be reported the same way or the two are not comparable.

**Test 2 is informational and never a gate.** It asks whether our shape sits inside the range two
curated ontologies already occupy, not whether it matches either of them.

**Placement is reported three ways on purpose.** A root-only pathway has been placed by the letter
of the algorithm and told a reader almost nothing: it has a top-level bucket and no theme inside it.
Reporting only the strict count would hide most of what an inclusion cutoff costs.

Usage::

    uv run scripts/freeze_table.py data/ontology/v0.2/recurrent_dag_c50
    uv run scripts/freeze_table.py data/ontology/v0.3/recurrent_dag_10770 --floors FLOORS.json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import reactome_roots, read_reactome_relation

csv.field_size_limit(1 << 30)

GO_BP = "biological_process"


def read_build(directory: Path) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
    """Read a build's parents, members and unplaced list.

    Args:
        directory: A build directory.

    Returns:
        Node to parent ids, node to member keys, and the unplaced keys.
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, list[str]] = defaultdict(list)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    unplaced: list[str] = []
    path = directory / "unplaced.tsv"
    if path.is_file():
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            field = "key" if reader.fieldnames and "key" in reader.fieldnames else None
            for row in reader:
                unplaced.append(row[field] if field else next(iter(row.values())))
    return parents, dict(members), unplaced


def ancestors_of(parents: dict[str, list[str]]) -> dict[str, set[str]]:
    """Every node's transitive ancestors.

    Args:
        parents: Node to its direct parents.

    Returns:
        Node to all nodes above it.
    """
    out: dict[str, set[str]] = {}

    def walk(node: str) -> set[str]:
        if node in out:
            return out[node]
        out[node] = set()  # guards against a cycle rather than recursing forever
        got: set[str] = set()
        for parent in parents.get(node, ()):
            got.add(parent)
            got |= walk(parent)
        out[node] = got
        return got

    for node in parents:
        walk(node)
    return out


def depth_of(parents: dict[str, list[str]]) -> int:
    """Longest root-to-node path, counted in EDGES.

    Edges, not nodes: counting nodes gives 13 where the frozen 1,850's `FROZEN.md` records 12, and
    the edge convention reproduces all three of its depth figures -- ours 12, Reactome 11, GO 16.

    Args:
        parents: Node to its direct parents.

    Returns:
        The maximum depth in edges, 0 for a forest of roots only.
    """
    memo: dict[str, int] = {}

    def walk(node: str) -> int:
        if node in memo:
            return memo[node]
        memo[node] = 1
        ps = parents.get(node, ())
        memo[node] = 1 + max((walk(p) for p in ps), default=0)
        return memo[node]

    return max((walk(node) for node in parents), default=1) - 1


def straddlers(
    members: dict[str, list[str]], ancestors: dict[str, set[str]]
) -> int:
    """Pathways in two or more themes that are NOT nested in one another.

    **This definition does not reproduce the 1,850 freeze's recorded figure and is not claimed to.**
    `FROZEN.md` records 682 straddlers for that build; this counts 1,239 over the same directory.
    The recorded number was computed ad hoc with no committed script, and no variant tried --
    restricting homes by inclusion, to leaves, to non-roots, or to distinct roots -- lands on 682.
    So this is stated as the definition of record going forward and the discrepancy is logged in
    `docs/debt.md` rather than papered over by relabelling one number as the other.

    A pathway in a theme and in that theme's parent is not straddling: the hierarchy already
    accounts for it. Straddling is membership of two themes neither of which contains the other.

    **Every exported member row counts.** Re-filtering by inclusion here was wrong once before: it
    dropped the rows consensus had inherited, which made sets smaller, broke containment, and
    reported 1,044 straddlers where the true count was 852.

    Args:
        members: Node to member keys.
        ancestors: Node to its transitive ancestors.

    Returns:
        How many pathways straddle.
    """
    homes: dict[str, list[str]] = defaultdict(list)
    for node, keys in members.items():
        for key in keys:
            homes[key].append(node)
    count = 0
    for nodes in homes.values():
        if len(nodes) < 2:
            continue
        if any(
            b not in ancestors.get(a, ()) and a not in ancestors.get(b, ())
            for i, a in enumerate(nodes)
            for b in nodes[i + 1 :]
        ):
            count += 1
    return count


def curated_shape(raw: Path) -> dict[str, dict[str, float]]:
    """Roots share, max depth and multi-parent share of Reactome and GO BP.

    Computed rather than quoted, so test 2's reference moves if the source data does.

    Args:
        raw: ``data/raw``.

    Returns:
        Per ontology: ``nodes``, ``roots_share``, ``depth``, ``multi_parent_share``.
    """
    out: dict[str, dict[str, float]] = {}

    lines = (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    parents = read_reactome_relation(lines)
    roots = reactome_roots(parents)
    nodes = set(parents) | {p for ps in parents.values() for p in ps}
    full = {node: list(parents.get(node, ())) for node in nodes}
    out["reactome"] = {
        "nodes": len(nodes),
        "roots_share": len(roots) / max(len(nodes), 1),
        "depth": depth_of(full),
        "multi_parent_share": sum(1 for ps in full.values() if len(ps) > 1) / max(len(nodes), 1),
    }

    terms = parse_obo_terms((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines())
    bp = {t: term for t, term in terms.items()
          if term.namespace == GO_BP and not term.is_obsolete}
    full_go = {t: [p for p in term.parents if p in bp] for t, term in bp.items()}
    out["go_bp"] = {
        "nodes": len(bp),
        "roots_share": sum(1 for ps in full_go.values() if not ps) / max(len(bp), 1),
        "depth": depth_of(full_go),
        "multi_parent_share": sum(1 for ps in full_go.values() if len(ps) > 1) / max(len(bp), 1),
    }
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the freeze table for a build.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--floors", type=Path, default=None,
                        help="a floors.json to print the held-out FDR per stratum from")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    parents, members, unplaced = read_build(args.build)
    ancestors = ancestors_of(parents)
    kids: dict[str, list[str]] = defaultdict(list)
    for node, ps in parents.items():
        for parent in ps:
            kids[parent].append(node)
    roots = [n for n, ps in parents.items() if not ps]
    sizes = {n: len(members.get(n, ())) for n in parents}
    placed = {k for keys in members.values() for k in keys}
    in_nonroot = {k for n, keys in members.items() if parents.get(n) for k in keys}
    root_only = placed - in_nonroot
    multi = [n for n, ps in parents.items() if len(ps) > 1]
    largest_root = max((len(set(members.get(n, ())) -
                        {k for c in kids.get(n, ()) for k in members.get(c, ())})
                        for n in roots), default=0)

    manifest = {}
    path = args.build / "manifest.json"
    if path.is_file():
        manifest = json.loads(path.read_text())

    report = {
        "build": str(args.build),
        "runs": manifest.get("runs"),
        "rows": manifest.get("rows"),
        "inclusion_cut": manifest.get("inclusion_threshold"),
        "size_cap": manifest.get("size_cap"),
        "themes": len(parents),
        "roots": len(roots),
        "roots_share": round(len(roots) / max(len(parents), 1), 4),
        "multi_parent": len(multi),
        "multi_parent_share": round(len(multi) / max(len(parents), 1), 4),
        "max_depth": depth_of(parents),
        "median_theme_size": int(statistics.median(sizes.values())) if sizes else 0,
        "largest_theme": max(sizes.values(), default=0),
        "largest_root_direct_members": largest_root,
        "straddlers": straddlers(members, ancestors),
        "placed": len(placed),
        "unplaced_strict": len(unplaced),
        "root_only": len(root_only),
        "effectively_unplaced": len(unplaced) + len(root_only),
    }

    print(f"FREEZE TABLE  {args.build}")
    if manifest:
        print(f"  runs {report['runs']}, rows {report['rows']}, "
              f"inclusion {report['inclusion_cut']}, cap {report['size_cap']}")
    print("\n  SHAPE")
    for label, key, pct in (
        ("themes", "themes", None), ("roots", "roots", "roots_share"),
        ("themes with >1 parent", "multi_parent", "multi_parent_share"),
        ("max depth", "max_depth", None), ("median theme size", "median_theme_size", None),
        ("largest theme", "largest_theme", None),
        ("largest root, direct members", "largest_root_direct_members", None),
        ("straddlers (>=2 non-nested)", "straddlers", None),
    ):
        extra = f"  ({report[pct]:.1%})" if pct else ""
        print(f"    {label:<30} {report[key]:>8,}{extra}")

    print("\n  PLACEMENT, three ways")
    for label, key in (("pathways placed", "placed"), ("unplaced (strict)", "unplaced_strict"),
                       ("root-only", "root_only"),
                       ("effectively unplaced", "effectively_unplaced")):
        print(f"    {label:<30} {report[key]:>8,}")

    curated = curated_shape(args.data / "raw")
    report["test_2"] = curated
    print("\n  TEST 2 -- shape against curated ontologies (informational, never a gate)")
    print(f"    {'':<22} {'ours':>9} {'Reactome':>10} {'GO BP':>9}")
    print(f"    {'roots':<22} {report['roots_share']:>8.1%} "
          f"{curated['reactome']['roots_share']:>9.1%} {curated['go_bp']['roots_share']:>8.1%}")
    print(f"    {'max depth':<22} {report['max_depth']:>9} "
          f"{int(curated['reactome']['depth']):>10} {int(curated['go_bp']['depth']):>9}")
    print(f"    {'multi-parent':<22} {report['multi_parent_share']:>8.1%} "
          f"{curated['reactome']['multi_parent_share']:>9.1%} "
          f"{curated['go_bp']['multi_parent_share']:>8.1%}")
    # NO inside/outside verdict is printed. `FROZEN.md` records GO BP at 20% roots and 31%
    # multi-parent; computed here over all non-obsolete BP terms it is 0.0% and 50.8%, and neither
    # the full graph nor the graph induced on our own universe reproduces the recorded pair. Only
    # GO's DEPTH (16) and all three Reactome figures reproduce. A verdict on whether our 7.6% roots
    # sits inside the curated range depends entirely on which GO figure is used -- inside at 20%,
    # outside at 0.0% -- so the figures are reported and the verdict is withheld. See docs/debt.md.
    report["test_2_verdict_withheld"] = (
        "GO BP roots and multi-parent as recorded in FROZEN.md are not reproducible; "
        "an inside/outside verdict would turn on which figure is used"
    )
    print("    (no inside/outside verdict: FROZEN.md's GO roots 20% / multi-parent 31% are not")
    print("     reproducible from go-basic.obo, and the verdict would turn on them. docs/debt.md.)")

    if args.floors and args.floors.is_file():
        floors = json.loads(args.floors.read_text())
        report["floors"] = floors
        print("\n  HELD-OUT FDR PER STRATUM")
        print(f"    {'stratum':<9} {'floor':>10} {'effective':>10} {'real':>7} "
              f"{'null':>7} {'held FDR':>9}")
        for entry in floors.get("strata", []):
            fl = "none" if entry["floor"] is None else f"{entry['floor']:.6f}"
            ef = "DROP" if entry["effective"] is None else f"{entry['effective']:.6f}"
            print(f"    {entry['stratum']:<9} {fl:>10} {ef:>10} "
                  f"{entry.get('heldout_real', '-'):>7} "
                  f"{entry.get('heldout_null', '-'):>7} {str(entry.get('heldout_fdr')):>9}")
        print(f"    overall held-out FDR {floors.get('overall_fdr')}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
