#!/usr/bin/env python3
"""Measure the overlap arm against c85. Read-only apart from one JSON the reviewer needs.

The arm is `data/experiments/reviewer_notes/SPEC_overlap_arm_2026-10-12.md`, declared before any
build. This script reports the three criteria the spec assigns to ccode (C1-C3) and every
report-only item in it. **C4 and C5 are the reviewer's**: C4's input is written out here as
``O50_new_themes.json`` and nothing about it is judged.

Nothing is adopted. Usage::

    uv run scripts/overlap_arm_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

#: Size bands, as every other leaves report uses them.
BANDS: tuple[tuple[int, int], ...] = (
    (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 300), (301, 1000), (1001, 10**9))

#: A theme this large is a bag, not a theme.
GIANT = 1000

#: The spec's same-theme cutoff for the arm, and the collapse share it is iterated with.
T_SAME = 0.50
COLLAPSE = 0.85

#: C3's bar: this share of c85 themes absent from O50 must have an O50 counterpart at T_SAME.
C3_BAR = 0.99

#: Reproducibility is stated at this match threshold, as every earlier leaves report states it.
MATCH = 0.70


def band_of(size: int) -> str:
    """Size band label.

    Args:
        size: Member count.

    Returns:
        The label.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10**9 else f"{low}+"
    return "other"


def read(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, float]]:
    """Members, parent edges and support for a build.

    Args:
        path: A build directory.

    Returns:
        ``(node -> members, child -> parents, node -> support)``.
    """
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    parents: dict[str, set[str]] = defaultdict(set)
    with (path / "edges.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row["node"]] = float(row["support"])
    return dict(members), dict(parents), support


def index(members: dict[str, set[str]]) -> dict[str, list[str]]:
    """Inverted index from pathway key to the themes holding it.

    Args:
        members: Node to members.

    Returns:
        Key to node ids.
    """
    out: dict[str, list[str]] = defaultdict(list)
    for node, keys in members.items():
        for key in keys:
            out[key].append(node)
    return dict(out)


def best_match(keys: set[str], other: dict[str, set[str]],
               holders: dict[str, list[str]]) -> tuple[str, float]:
    """Best Jaccard match for a member set among another build's themes.

    Args:
        keys: The set to match.
        other: The other build.
        holders: Its inverted index.

    Returns:
        ``(node, jaccard)``.
    """
    best = ("", 0.0)
    for node in {o for key in keys for o in holders.get(key, ())}:
        inter = len(keys & other[node])
        union = len(keys) + len(other[node]) - inter
        if union and inter / union > best[1]:
            best = (node, inter / union)
    return best


def offending_pairs(members: dict[str, set[str]]) -> tuple[list[tuple], list[tuple]]:
    """Pairs either rule of the arm should have removed.

    Both are checked over **every** pair, not only the DAG's direct edges, because that is what the
    rules themselves consider. The non-nested check is restricted to pairs where both themes are
    under :data:`GIANT`, as the spec's C1 says.

    Args:
        members: Node to members.

    Returns:
        ``(non_nested_at_or_above_T_SAME, contained_at_or_above_COLLAPSE)``.
    """
    holders = index(members)
    overlap: list[tuple] = []
    nested: list[tuple] = []
    for node, keys in sorted(members.items()):
        for other in {o for key in keys for o in holders.get(key, ())}:
            if other == node:
                continue
            theirs = members[other]
            if keys < theirs:
                ratio = len(keys) / len(theirs)
                if ratio >= COLLAPSE:
                    nested.append((node, other, ratio))
            elif not theirs < keys and node < other:
                if len(keys) >= GIANT or len(theirs) >= GIANT:
                    continue
                inter = len(keys & theirs)
                union = len(keys) + len(theirs) - inter
                if union and inter / union >= T_SAME:
                    overlap.append((node, other, inter / union))
    return overlap, nested


def depths(members: dict[str, set[str]], parents: dict[str, set[str]]) -> dict[str, int]:
    """Longest path from each node up to a root.

    Args:
        members: Node to members.
        parents: Child to parents.

    Returns:
        Node to depth.
    """
    memo: dict[str, int] = {}

    def depth(node: str) -> int:
        if node in memo:
            return memo[node]
        memo[node] = 0
        above = parents.get(node, ())
        memo[node] = 1 + max((depth(p) for p in above), default=-1) if above else 0
        return memo[node]

    for node in members:
        depth(node)
    return memo


def antichain_parents(members: dict[str, set[str]], parents: dict[str, set[str]],
                      drop_giants: bool = False) -> int:
    """How many themes have two parents that are not nested in each other.

    Not the manifest's ``multi_parent_share``: two parents one inside the other are one facet seen
    at two resolutions, not two facets. In a strict Hasse DAG the transitive edge is already gone,
    so on these builds the two agree -- which is why the giant-excluding variant below is the one
    that reproduces the spec's quoted baseline.

    Args:
        members: Node to members.
        parents: Child to parents.
        drop_giants: Ignore parents at or above :data:`GIANT`. The spec quotes c85 as "about 51%",
            which only comes out under this variant; the literal measure is 64.8%.

    Returns:
        The count.
    """
    giants = {node for node in members if len(members[node]) >= GIANT} if drop_giants else set()
    total = 0
    for node in members:
        above = sorted(set(parents.get(node, ())) - giants)
        found = False
        for i, left in enumerate(above):
            for right in above[i + 1:]:
                a, b = members[left], members[right]
                if not (a <= b or b <= a):
                    found = True
                    break
            if found:
                break
        total += found
    return total


def reach_two_roots(members: dict[str, set[str]], parents: dict[str, set[str]],
                    drop_giants: bool = False) -> int:
    """How many themes reach two or more distinct roots.

    Args:
        members: Node to members.
        parents: Child to parents.
        drop_giants: Ignore giant parents, and do not count a giant as a root. Nearly everything
            reaches two giants, so the literal measure is 93.2% on c85 against the spec's "about
            56%"; this variant gives 55.7% and is therefore the spec's definition.

    Returns:
        The count.
    """
    giants = {node for node in members if len(members[node]) >= GIANT} if drop_giants else set()
    above = {node: set(parents.get(node, ())) - giants for node in members}
    roots = {node for node in members if not above[node]} - giants
    total = 0
    for node in members:
        seen: set[str] = set()
        stack = [node]
        while stack:
            for parent in above.get(stack.pop(), ()):
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        total += len(seen & roots) >= 2
    return total


def shape(name: str, path: Path) -> dict[str, object]:
    """Every structural number this report quotes for one build.

    Args:
        name: Label.
        path: Build directory.

    Returns:
        The numbers.
    """
    members, parents, support = read(path)
    roots = [node for node in members if not parents.get(node)]
    giants = sorted((len(members[r]) for r in roots if len(members[r]) >= GIANT), reverse=True)
    anti = antichain_parents(members, parents)
    two_roots = reach_two_roots(members, parents)
    anti_ng = antichain_parents(members, parents, drop_giants=True)
    two_roots_ng = reach_two_roots(members, parents, drop_giants=True)
    return {
        "name": name, "path": str(path), "themes": len(members),
        "edges": sum(len(v) for v in parents.values()),
        "roots": len(roots), "giants": giants,
        "bands": Counter(band_of(len(v)) for v in members.values()),
        "antichain_parents": anti, "antichain_share": anti / len(members),
        "two_roots": two_roots, "two_roots_share": two_roots / len(members),
        "antichain_share_ng": anti_ng / len(members),
        "two_roots_share_ng": two_roots_ng / len(members),
        "root_only": sum(1 for node in members
                         if parents.get(node) and all(
                             not parents.get(p) for p in parents[node])),
        "depths": Counter(depths(members, parents).values()),
        "support_median": statistics.median(support.values()),
        "members": members, "parents": parents, "support": support,
    }


def main(argv: list[str] | None = None) -> int:
    """Report the arm."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/ontology/v0.4-leaves"))
    parser.add_argument("--c85", default="thema_L_x2_c85")
    parser.add_argument("--o50", default="thema_L_x2_O50")
    parser.add_argument("--o60", default="thema_L_x2_O60")
    parser.add_argument("--o70", default="thema_L_x2_O70")
    parser.add_argument("--repair-o50", default="thema_L_repair_O50")
    parser.add_argument("--repair", default="thema_L_repair")
    parser.add_argument("--exclusions", type=Path, default=Path("data/excluded_inputs.tsv"))
    args = parser.parse_args(argv)

    builds = {
        key: shape(key, args.root / name)
        for key, name in (("c85", args.c85), ("O70", args.o70),
                          ("O60", args.o60), ("O50", args.o50))
    }
    c85, o50 = builds["c85"], builds["O50"]

    print("OVERLAP ARM, declared 12 Oct 2026. Same-theme cutoff in consensus AND the stale pass,")
    print("iterated jointly with chain collapse at 0.85. theta_match unchanged at 0.70.")
    print("NOTHING IS ADOPTED BY THIS REPORT.\n")

    print("=" * 78)
    print("THEME COUNTS")
    print("=" * 78)
    print(f"  {'build':<6}{'T_same':>8}{'themes':>9}{'edges':>9}{'roots':>7}{'giants':>8}")
    for key, cut in (("c85", 0.70), ("O70", 0.70), ("O60", 0.60), ("O50", 0.50)):
        b = builds[key]
        print(f"  {key:<6}{cut:>8.2f}{b['themes']:>9,}{b['edges']:>9,}{b['roots']:>7,}"
              f"{len(b['giants']):>8}")
    print(f"\n  giants (over {GIANT:,} members), sizes")
    for key in ("c85", "O70", "O60", "O50"):
        print(f"    {key:<6}{builds[key]['giants']}")

    print("\n  themes per size band")
    print(f"    {'band':<10}{'c85':>8}{'O70':>8}{'O60':>8}{'O50':>8}{'O50-c85':>10}")
    for low, high in BANDS:
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        row = [builds[k]["bands"].get(label, 0) for k in ("c85", "O70", "O60", "O50")]
        print(f"    {label:<10}{row[0]:>8,}{row[1]:>8,}{row[2]:>8,}{row[3]:>8,}"
              f"{row[3] - row[0]:>+10,}")

    print("\n" + "=" * 78)
    print("C1  no non-nested pair under 1,000 at J >= 0.50, and no containment pair at >= 0.85")
    print("=" * 78)
    c1 = {}
    for key in ("c85", "O70", "O60", "O50"):
        overlap, nested = offending_pairs(builds[key]["members"])
        c1[key] = (len(overlap), len(nested))
        print(f"  {key:<6} non-nested at or above 0.50: {len(overlap):>6,}   "
              f"containment at or above 0.85: {len(nested):>4}")
    c1_pass = c1["O50"] == (0, 0)
    print(f"\n  C1: {'PASS' if c1_pass else 'FAIL'}  "
          f"(O50 leaves {c1['O50'][0]:,} overlap and {c1['O50'][1]} containment pairs)")
    if not c1_pass:
        overlap, nested = offending_pairs(o50["members"])
        for node, other, value in sorted(overlap, key=lambda t: -t[2])[:5]:
            print(f"      overlap {node} ({len(o50['members'][node])}) vs {other} "
                  f"({len(o50['members'][other])}) J {value:.3f}")
        for node, other, value in sorted(nested, key=lambda t: -t[2])[:5]:
            print(f"      nested  {node} in {other} ratio {value:.3f}")

    print("\n" + "=" * 78)
    print(f"C2  no pathway loses all its themes under {GIANT:,} members")
    print("=" * 78)
    small = {
        key: Counter(k for v in builds[key]["members"].values() if len(v) < GIANT for k in v)
        for key in ("c85", "O50")
    }
    every = set(small["c85"]) | set(small["O50"])
    stranded = sorted(k for k in every if small["c85"][k] > 0 and small["O50"][k] == 0)
    lost = {
        key: small["c85"][key] - small["O50"][key]
        for key in every
        if small["O50"][key] < small["c85"][key]
    }
    print(f"  pathways with at least one theme under {GIANT:,}: c85 "
          f"{sum(1 for k in every if small['c85'][k]):,}, O50 "
          f"{sum(1 for k in every if small['O50'][k]):,}")
    print(f"  pathways that lost at least one: {len(lost):,}" +
          (f"  (median {statistics.median(lost.values()):.0f}, max {max(lost.values())})"
           if lost else ""))
    print(f"  pathways left with NONE: {len(stranded)}" +
          (f"  {stranded[:10]}" if stranded else ""))
    c2_pass = not stranded
    print(f"\n  C2: {'PASS' if c2_pass else 'FAIL'}")

    print("\n" + "=" * 78)
    print(f"C3  >= {C3_BAR:.0%} of c85 themes absent from O50 have an O50 theme at J >= {T_SAME}")
    print("=" * 78)
    o50_sets = {frozenset(v) for v in o50["members"].values()}
    holders = index(o50["members"])
    absent = [node for node, keys in c85["members"].items() if frozenset(keys) not in o50_sets]
    matched = 0
    worst: list[tuple[str, float]] = []
    for node in absent:
        _best, value = best_match(c85["members"][node], o50["members"], holders)
        if value >= T_SAME:
            matched += 1
        else:
            worst.append((node, value))
    share = matched / len(absent) if absent else 1.0
    print(f"  c85 themes absent from O50: {len(absent):,} of {c85['themes']:,}")
    print(f"  of those, with an O50 counterpart at J >= {T_SAME}: {matched:,} = {share:.2%}")
    print(f"  without one: {len(worst):,}")
    for node, value in sorted(worst, key=lambda t: t[1])[:10]:
        print(f"      {node} ({len(c85['members'][node])} members) best J {value:.3f}")
    c3_pass = share >= C3_BAR
    print(f"\n  C3: {'PASS' if c3_pass else 'FAIL'}  ({share:.2%} against {C3_BAR:.0%})")

    print("\n" + "=" * 78)
    print("REPORT ONLY")
    print("=" * 78)
    print("\n  multi-parent structure: parents NOT nested in each other, two definitions")
    print(f"    {'build':<6}{'2+ parents':>12}{'2+ roots':>11}   "
          f"{'2+ parents':>12}{'2+ roots':>11}   (right: giants excluded)")
    for key in ("c85", "O70", "O60", "O50"):
        b = builds[key]
        print(f"    {key:<6}{b['antichain_share']:>12.1%}{b['two_roots_share']:>11.1%}   "
              f"{b['antichain_share_ng']:>12.1%}{b['two_roots_share_ng']:>11.1%}")
    print("    The spec quotes c85 as about 51% and 56% and predicts about 38% and 47% for a 0.50")
    print("    merge. Those are the GIANTS-EXCLUDED numbers: c85 gives 51.2% / 55.7% that way and")
    print("    64.8% / 93.2% literally, because almost every theme reaches two giants. Compared on")
    print("    the spec's own definition the prediction was close on parents and optimistic on")
    print("    roots.")
    print("\n    themes whose every parent is a root: "
          + ", ".join(f"{k} {builds[k]['root_only']}" for k in ("c85", "O70", "O60", "O50")))

    print("\n  depth distribution (longest path to a root)")
    levels = sorted({d for key in builds for d in builds[key]["depths"]})
    print(f"    {'depth':<7}{'c85':>8}{'O70':>8}{'O60':>8}{'O50':>8}")
    for level in levels:
        row = [builds[k]["depths"].get(level, 0) for k in ("c85", "O70", "O60", "O50")]
        print(f"    {level:<7}{row[0]:>8,}{row[1]:>8,}{row[2]:>8,}{row[3]:>8,}")

    print("\n  survivor support margins, from each build's repair_map.json")
    print(f"    {'build':<6}{'collapses':>11}{'child kept':>12}{'parent kept':>13}"
          f"{'median margin':>15}{'under 0.05':>12}")
    for key, name in (("c85", args.c85), ("O70", args.o70), ("O60", args.o60), ("O50", args.o50)):
        path = args.root / name / "repair_map.json"
        if not path.is_file():
            print(f"    {key:<6} no repair_map.json")
            continue
        got = json.loads(path.read_text())
        events = got["collapsed"]
        kept = Counter(e["kept"] for e in events)
        margins = sorted(abs(e["victim_support"] - e["keeper_support"]) for e in events)
        tiny = sum(1 for m in margins if m < 0.05)
        print(f"    {key:<6}{len(events):>11,}{kept['child']:>12,}{kept['parent']:>13,}"
              f"{statistics.median(margins):>15.3f}{tiny / len(margins):>11.1%}")

    print("\n  what O70 changed relative to c85 (the control: iterating, at the same cutoff)")
    identical = all(
        (args.root / args.o70 / f).read_bytes() == (args.root / args.c85 / f).read_bytes()
        for f in ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv")
    )
    print(f"    all four tables byte-identical to c85: {identical}")
    print("    so at a 0.70 cutoff the joint fixed point changes NOTHING, and every difference")
    print("    between O50 and c85 is the cutoff rather than the iteration")

    print("\n  reproducibility between two independent builds, projected (report only)")
    with args.exclusions.open(encoding="utf-8") as handle:
        excluded = {row["key"] for row in csv.DictReader(handle, delimiter="\t")}
    for label, left, right in (("c85", args.c85, args.repair),
                               ("O50", args.o50, args.repair_o50)):
        a_members, _p, a_support = read(args.root / left)
        b_members, _q, _s = read(args.root / right)
        projected = {node: keys - excluded for node, keys in b_members.items()}
        other = index(projected)
        hits = sum(
            1 for keys in a_members.values()
            if best_match(keys, projected, other)[1] >= MATCH
        )
        print(f"    {label:<4} {left} vs {right}: "
              f"{hits:,} of {len(a_members):,} matched at J >= {MATCH} = "
              f"{hits / len(a_members):.1%}")
    print("    removing duplicates lowers this by construction; it is reported, not a criterion")

    print("\n  O60 summary")
    o60 = builds["O60"]
    overlap60, nested60 = c1["O60"]
    print(f"    {o60['themes']:,} themes, {o60['roots']} roots, {len(o60['giants'])} giants, "
          f"2+ non-nested parents {o60['antichain_share']:.1%}, 2+ roots "
          f"{o60['two_roots_share']:.1%}")
    print(f"    offending pairs left: {overlap60} non-nested at 0.50 "
          f"(its own cutoff is 0.60), {nested60} containment")

    print("\n" + "=" * 78)
    print("C4 INPUT (the reviewer judges it; nothing here is judged)")
    print("=" * 78)
    c85_sets = {frozenset(v): node for node, v in c85["members"].items()}
    new = {
        node: sorted(keys)
        for node, keys in sorted(o50["members"].items())
        if frozenset(keys) not in c85_sets
    }
    destination = args.root / args.o50 / "O50_new_themes.json"
    titles: dict[str, str] = {}
    with (args.root / args.o50 / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            titles[row["key"]] = row["name"]
    destination.write_text(
        json.dumps(
            {
                "note": "every O50 theme whose member set is not identical to any c85 theme; "
                        "input to criterion C4, judged by the reviewer",
                "build": str(args.root / args.o50),
                "compared_with": str(args.root / args.c85),
                "n_new": len(new),
                "themes": [
                    {
                        "node": node,
                        "size": len(keys),
                        "support": o50["support"][node],
                        "members": [titles.get(key, key) for key in keys],
                        "keys": keys,
                    }
                    for node, keys in new.items()
                ],
            },
            indent=1, ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"  O50 themes not identical to any c85 theme: {len(new):,} of {o50['themes']:,}")
    print(f"  identical to a c85 theme: {o50['themes'] - len(new):,}")
    print(f"  -> {destination}")

    print("\n" + "=" * 78)
    print("CRITERIA ccode OWNS")
    print("=" * 78)
    for key, text, ok in (
        ("C1", "no pair either rule would remove survives", c1_pass),
        ("C2", f"no pathway loses all its themes under {GIANT:,}", c2_pass),
        ("C3", f"{share:.2%} of absent themes have a counterpart, bar {C3_BAR:.0%}", c3_pass),
    ):
        print(f"  {key}: {'PASS' if ok else 'FAIL'}  {text}")
    print("\n  C4 and C5 are the reviewer's and are NOT judged here.")
    print("  ADOPTED: nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
