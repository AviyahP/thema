#!/usr/bin/env python3
"""Part 5: the lattice above one fan, and whether merging the fan would resolve it. Read-only.

``n00150`` has six parents whose pairwise Jaccard is 0.47-0.69 -- all below the 0.70 merge. The
reviewer found that the fragmentation does not resolve upward: no node within three levels holds all
six, and about twenty small overlapping ancestors each cover one to four of them. This measures that
lattice, estimates what merging the six into their union would leave, and compares the support of
everything sitting above a fan against everything else of the same size.

The last comparison is **size-matched**, because support falls with theme size on its own: an
unmatched comparison would show fan ancestors looking weak when they are merely large.

Usage::

    uv run scripts/fan_ancestors.py --stats STATS.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

FOCUS = "n00150"
LEVELS = 3
FAN_SLACK = 5
FAN_PARENTS = 3
MERGE_JACCARD = 0.70


def main(argv: list[str] | None = None) -> int:
    """Report the lattice above the focus fan, and the fan-ancestor support comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--focus", default=FOCUS)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    path = root / args.build
    stats = json.loads(args.stats.read_text())["nodes"]

    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row.get("node") or row.get("id")] = float(row.get("support") or 0.0)
    parents: dict[str, set[str]] = defaultdict(set)
    with (path / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
    sizes = {node: len(keys) for node, keys in members.items()}

    def gist(node: str, n: int = 3) -> str:
        """Nearest member names."""
        return "; ".join((stats.get(node, {}).get("nearest") or [])[:n])

    focus = args.focus
    six = sorted(parents[focus], key=lambda p: -support.get(p, 0.0))
    print(f"PART 5: the lattice above {focus} ({sizes[focus]} members, "
          f"support {support.get(focus, 0):.3f}) and its {len(six)} parents")
    print(f"  the {len(six)} parents: "
          + ", ".join(f"{p} ({sizes[p]}, {support.get(p, 0):.3f})" for p in six))

    # Ancestors within LEVELS, by shortest hop count, and which of the six each covers.
    frontier = {p: 1 for p in six}
    seen = dict(frontier)
    for _ in range(LEVELS - 1):
        nxt: dict[str, int] = {}
        for node, depth in frontier.items():
            for up in parents.get(node, ()):
                if up not in seen or seen[up] > depth + 1:
                    seen[up] = depth + 1
                    nxt[up] = depth + 1
        frontier = nxt
    ancestors = {a: d for a, d in seen.items() if a not in six}
    rows = []
    for a in sorted(ancestors, key=lambda x: (sizes[x], x)):
        covers = [p for p in six if members[p] <= members[a]]
        rows.append({"node": a, "level": ancestors[a], "size": sizes[a],
                     "support": round(support.get(a, 0.0), 4),
                     "covers": len(covers), "covers_which": covers,
                     "gist": gist(a)})
    print(f"\n  {len(rows)} distinct ancestors within {LEVELS} levels of the six parents")
    print(f"  {'node':<9}{'lvl':>4}{'size':>7}{'supp':>8}{'covers':>8}  nearest the centroid")
    for r in rows:
        print(f"  {r['node']:<9}{r['level']:>4}{r['size']:>7,}{r['support']:>8.3f}"
              f"{r['covers']:>6}/{len(six)}  {r['gist'][:72]}")
    full = [r for r in rows if r["covers"] == len(six)]
    print(f"  ancestors covering ALL {len(six)}: "
          f"{[r['node'] for r in full] if full else 'NONE'}")

    # If the six were merged into their union, how many of those ancestors stay distinct?
    union = set().union(*(members[p] for p in six))
    print(f"\n  if the {len(six)} parents become their union ({len(union)} members):")
    survivors, absorbed = [], []
    for r in rows:
        a = r["node"]
        inter = len(members[a] & union)
        j = inter / (len(members[a]) + len(union) - inter)
        close = j >= MERGE_JACCARD
        others = [o["node"] for o in rows if o["node"] != a
                  and (lambda i: i / (len(members[a]) + len(members[o["node"]]) - i)
                       >= MERGE_JACCARD)(len(members[a] & members[o["node"]]))]
        (absorbed if (close or others) else survivors).append(
            {"node": a, "size": r["size"], "jaccard_to_union": round(j, 3),
             "near_others": others})
    print(f"    ancestors still distinct (Jaccard < {MERGE_JACCARD} to the union AND to every "
          f"other ancestor): {len(survivors)} of {len(rows)}")
    print(f"    ancestors that would themselves become near-duplicates: {len(absorbed)}")
    for a in absorbed[:6]:
        print(f"      {a['node']} ({a['size']}) J={a['jaccard_to_union']:.2f} to the union"
              + (f", and near {len(a['near_others'])} other ancestor(s)"
                 if a["near_others"] else ""))

    # Support of nodes above ANY fan, against size-matched others.
    fans = {node: ups for node, ups in parents.items()
            if len(ups) >= FAN_PARENTS
            and all(sizes[p] - sizes[node] <= FAN_SLACK for p in ups)}
    above: set[str] = set()
    frontier = {p for ups in fans.values() for p in ups}
    while frontier:
        above |= frontier
        frontier = {up for node in frontier for up in parents.get(node, ())} - above
    others = set(members) - above - set(fans)
    print(f"\n  SUPPORT of nodes above a fan vs size-matched others "
          f"({len(above):,} above a fan, {len(others):,} others)")
    bands = ((3, 10), (11, 20), (21, 50), (51, 300), (301, 10**9))
    print(f"  {'size band':<12}{'n above':>9}{'median':>9}{'n other':>9}{'median':>9}{'delta':>9}")
    comparison = {}
    for low, high in bands:
        a = [support.get(n, 0.0) for n in above if low <= sizes[n] <= high]
        b = [support.get(n, 0.0) for n in others if low <= sizes[n] <= high]
        if not a or not b:
            continue
        band = f"{low}-{high}" if high < 10**9 else f"{low}+"
        ma, mb = float(np.median(a)), float(np.median(b))
        comparison[band] = {"n_above": len(a), "median_above": round(ma, 4),
                            "n_other": len(b), "median_other": round(mb, 4),
                            "delta": round(ma - mb, 4)}
        print(f"  {band:<12}{len(a):>9,}{ma:>9.3f}{len(b):>9,}{mb:>9.3f}{ma - mb:>+9.3f}")

    report = {"focus": focus, "focus_size": sizes[focus],
              "focus_support": support.get(focus),
              "parents": [{"node": p, "size": sizes[p], "support": support.get(p)}
                          for p in six],
              "union_size": len(union),
              "ancestors_within_3_levels": rows,
              "ancestors_covering_all": [r["node"] for r in full],
              "after_merging_the_parents": {"still_distinct": survivors,
                                            "would_be_absorbed": absorbed},
              "fan_ancestor_support_vs_size_matched": comparison,
              "n_nodes_above_a_fan": len(above)}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
