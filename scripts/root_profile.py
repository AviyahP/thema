#!/usr/bin/env python3
"""What the biggest roots of a build are made of: source mix, and their largest children.

A root is a top-level theme, so its source mix answers a question the shape table cannot: whether
the coarsest structure is a real mixture of the four collections or one source's taxonomy wearing a
theme's name. The largest children with example member names make it readable without naming having
run.

Usage::

    uv run scripts/root_profile.py data/ontology/v0.3/recurrent_dag_10770_r1-200 --top 4
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

csv.field_size_limit(1 << 30)


def read(directory: Path) -> tuple[dict[str, list[str]], dict[str, list[dict]]]:
    """A build's parents and its member rows.

    Args:
        directory: A build directory.

    Returns:
        Node to parents, and node to member rows (key, source, name).
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, list[dict]] = defaultdict(list)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(
                {"key": row["key"], "source": row.get("source", ""), "name": row.get("name", "")}
            )
    return parents, dict(members)


def main(argv: list[str] | None = None) -> int:
    """Profile the largest roots.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--top", type=int, default=4)
    parser.add_argument("--children", type=int, default=10)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    parents, members = read(args.build)
    kids: dict[str, list[str]] = defaultdict(list)
    for node, ps in parents.items():
        for parent in ps:
            kids[parent].append(node)
    roots = [n for n, ps in parents.items() if not ps]
    ranked = sorted(roots, key=lambda n: -len(members.get(n, ())))[: args.top]

    overall = Counter(r["source"] for rows in members.values() for r in rows)
    total = sum(overall.values())
    print(f"ROOT PROFILE  {args.build.name}: {len(roots)} roots, showing the {len(ranked)} largest")
    print("  universe source mix across all member rows: "
          + ", ".join(f"{s} {c / max(total, 1):.0%}" for s, c in overall.most_common()))

    report = []
    for root in ranked:
        rows = members.get(root, [])
        mix = Counter(r["source"] for r in rows)
        children = sorted(kids.get(root, []), key=lambda n: -len(members.get(n, ())))
        print(f"\n  {root}: {len(rows):,} members, {len(kids.get(root, []))} children")
        print("    sources: "
              + ", ".join(f"{s} {c:,} ({c / max(len(rows), 1):.0%})" for s, c in mix.most_common()))
        kid_report = []
        for child in children[: args.children]:
            crows = members.get(child, [])
            examples = [r["name"] for r in crows if r["name"]][:2]
            print(f"      {child}  {len(crows):>5,} members   "
                  + ("; ".join(e[:48] for e in examples) if examples else "(no names)"))
            kid_report.append({"node": child, "members": len(crows), "examples": examples})
        report.append({
            "root": root, "members": len(rows), "children": len(kids.get(root, [])),
            "sources": dict(mix), "largest_children": kid_report,
        })

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "build": str(args.build), "roots": len(roots),
            "universe_sources": dict(overall), "top_roots": report,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
