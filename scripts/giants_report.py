#!/usr/bin/env python3
"""The eight giant roots of thema_L_repair, and what the build looks like without them. Read-only.

Part 1 describes each root of 1,000+ members: its own numbers, its direct children, how many of
those children are themselves mid-size themes of 51-300 members -- the band a usable middle would
live in -- and how many are **shared with another giant**, which is where the build's multi-parent
share comes from.

Part 2 removes the eight and reports what remains. This is a counterfactual computed on the cached
build, not a new build: a theme is dropped only if every root above it is a giant, so nothing is
orphaned silently, and the remaining roots are recomputed over the survivors.

Note the distinction the brief draws correctly: **nine** themes have 1,000+ members but **eight are
roots**. ``n01268`` (1,405 members) is a child of ``n02452`` and is not one of the giants.

Usage::

    uv run scripts/giants_report.py --stats STATS.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: A root of at least this many members is a "giant".
GIANT = 1000
#: The band a usable middle level would live in.
MIDDLE = (51, 300)
#: Bands for the leaf-placement table.
PLACEMENT_BANDS: tuple[tuple[int, int], ...] = (
    (3, 10), (11, 50), (51, 300), (301, 1000), (1001, 10**9))
#: Names shown per node.
TOP_NAMES = 10
CHILD_NAMES = 5


def label(low: int, high: int) -> str:
    """Band label."""
    return f"{low}-{high}" if high < 10**9 else f"{low}+"


def band_of(size: int) -> str:
    """Placement band for a size."""
    for low, high in PLACEMENT_BANDS:
        if low <= size <= high:
            return label(low, high)
    return "other"


def main(argv: list[str] | None = None) -> int:
    """Report the giants and the counterfactual."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    path = root / args.build
    stats = json.loads(args.stats.read_text())["nodes"]

    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    parents: dict[str, set[str]] = defaultdict(set)
    children: dict[str, set[str]] = defaultdict(set)
    with (path / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
            children[row["parent"]].add(row["child"])

    sizes = {node: len(keys) for node, keys in members.items()}
    roots = sorted((n for n in members if not parents.get(n)), key=lambda n: -sizes[n])
    giants = [n for n in roots if sizes[n] >= GIANT]
    over = [n for n, s in sizes.items() if s >= GIANT]

    print(f"PART 1: {len(giants)} giant ROOTS of {GIANT}+ members "
          f"({len(over)} themes are that large; "
          f"{', '.join(n for n in over if n not in giants)} "
          f"{'is' if len(over) - len(giants) == 1 else 'are'} not a root)")
    print()

    report: dict[str, object] = {"build": args.build, "giant_threshold": GIANT,
                                 "n_giant_roots": len(giants), "giants": {}}
    # Which children are shared with another giant.
    shared_counts: dict[str, int] = {}
    for node in set().union(*(children[g] for g in giants)) if giants else set():
        shared_counts[node] = sum(1 for g in giants if node in children[g])

    for giant in giants:
        s = stats.get(giant, {})
        kids = sorted(children[giant], key=lambda c: -sizes[c])
        mid = [c for c in kids if MIDDLE[0] <= sizes[c] <= MIDDLE[1]]
        shared = [c for c in kids if shared_counts.get(c, 0) > 1]
        entry = {
            "size": sizes[giant], "support": s.get("support"),
            "support_at_0.5": s.get("support_at_0.5"),
            "coherence_ratio": s.get("coherence_ratio"),
            "coherence_observed": s.get("coherence_observed"),
            "coherence_null": s.get("coherence_null"),
            "n_children": len(kids),
            "n_children_51_300": len(mid),
            "n_children_shared_with_another_giant": len(shared),
            "sources": s.get("sources"),
            "nearest": (s.get("nearest") or [])[:TOP_NAMES],
            "children": [
                {"node": c, "size": sizes[c],
                 "support": stats.get(c, {}).get("support"),
                 "support_at_0.5": stats.get(c, {}).get("support_at_0.5"),
                 "coherence_ratio": stats.get(c, {}).get("coherence_ratio"),
                 "n_giant_parents": shared_counts.get(c, 0),
                 "nearest": (stats.get(c, {}).get("nearest") or [])[:CHILD_NAMES]}
                for c in kids],
        }
        report["giants"][giant] = entry
        src = ", ".join(f"{k} {v}" for k, v in (entry["sources"] or {}).items())
        print(f"  === {giant}  n={entry['size']:,}  support={entry['support']:.3f}  "
              f"support@0.5={entry['support_at_0.5']:.3f}  "
              f"coherence={entry['coherence_ratio']}x  {len(kids)} children ===")
        print(f"      sources: {src}")
        print(f"      children of 51-300 members: {len(mid)}   "
              f"children shared with another giant: {len(shared)} of {len(kids)}")
        print(f"      nearest the centroid: {'; '.join(entry['nearest'][:TOP_NAMES])}")
        for c in entry["children"][:8]:
            flag = f"  [under {c['n_giant_parents']} giants]" if c["n_giant_parents"] > 1 else ""
            soft = c["support_at_0.5"] if c["support_at_0.5"] is not None else float("nan")
            print(f"        {c['node']} n={c['size']:>5,} s@0.5={soft:.3f} "
                  f"coh={c['coherence_ratio']}x{flag}")
            print(f"           {'; '.join(c['nearest'][:3])}")
        if len(kids) > 8:
            print(f"        ... {len(kids) - 8} further children")
        print()

    print("PART 2: the build with the eight giants removed")
    gone = set(giants)
    # A theme is dropped only if EVERY root above it is a giant: otherwise it still has a home.
    def roots_above(node: str, seen: frozenset[str]) -> set[str]:
        """Root ancestors of a node."""
        ups = [p for p in parents.get(node, ()) if p not in seen]
        if not ups:
            return {node}
        return set().union(*(roots_above(p, seen | {node}) for p in ups))

    sys.setrecursionlimit(100000)
    orphaned = set()
    for node in members:
        if node in gone:
            continue
        above = roots_above(node, frozenset())
        if above and above <= gone:
            orphaned.add(node)
    alive = {n for n in members if n not in gone}
    new_parents = {n: {p for p in parents.get(n, ()) if p in alive} for n in alive}
    new_roots = sorted((n for n in alive if not new_parents[n]), key=lambda n: -sizes[n])
    new_children: dict[str, list[str]] = defaultdict(list)
    for node, ups in new_parents.items():
        for parent in ups:
            new_children[parent].append(node)
    counts = [len(v) for v in new_children.values() if v]
    multi = sum(1 for n in alive if len(new_parents[n]) > 1)

    best: dict[str, int] = {}
    for node in sorted(alive, key=lambda n: -sizes[n]):
        if sizes[node] > 1000:
            continue
        for key in members[node]:
            if key not in best:
                best[key] = sizes[node]
    keys_all = {k for keys in members.values() for k in keys}
    placement = Counter(band_of(best[k]) if k in best else "none" for k in keys_all)

    print(f"  themes: {len(members):,} -> {len(alive):,} (8 giants removed)")
    print(f"  of the survivors, {len(orphaned):,} had ALL their roots among the giants and are "
          f"now top-level themselves")
    print(f"  roots: {len(roots)} -> {len(new_roots)}")
    print(f"  largest remaining roots: {[sizes[n] for n in new_roots[:12]]}")
    print(f"  children per node: median {np.median(counts):.0f}, max {max(counts):,}")
    print(f"  multi-parent: {100 * multi / len(alive):.1f}% (was "
          f"{100 * sum(1 for n in members if len(parents.get(n, ())) > 1) / len(members):.1f}%)")
    print("  leaves by the largest remaining theme of 1,000 or fewer:")
    for low, high in PLACEMENT_BANDS:
        band = label(low, high)
        if placement.get(band):
            print(f"    {band:>10}: {placement[band]:>6,} "
                  f"({100 * placement[band] / len(keys_all):.1f}%)")
    if placement.get("none"):
        print(f"    {'none':>10}: {placement['none']:>6,}")

    report["without_giants"] = {
        "themes_before": len(members), "themes_after": len(alive),
        "n_orphaned_to_top_level": len(orphaned),
        "roots_before": len(roots), "roots_after": len(new_roots),
        "largest_remaining_roots": [sizes[n] for n in new_roots[:20]],
        "children_median": float(np.median(counts)), "children_max": int(max(counts)),
        "multi_parent_share": round(multi / len(alive), 4),
        "leaf_placement": dict(sorted(placement.items())),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
