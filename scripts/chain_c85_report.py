#!/usr/bin/env python3
"""Measure the 0.85 chain-collapse arm against the frozen baseline. Read-only apart from one TSV.

The rule -- threshold 0.85 and keep-the-higher-support survivor -- is **POST-HOC**: it was chosen
after seeing the n00150 lattice and the 550-pair survivor measurement. The five success criteria it
is scored against were **declared before the builds ran** (DECISIONS, 9 Oct 2026) and are reported
here as pass or fail with their numbers. A failing criterion is reported, never argued away.

Sections follow the brief: reproducibility between two independent builds (criterion d), the
comparison against the frozen baseline, the DAG check, and the criteria table.

Usage::

    uv run scripts/chain_c85_report.py
    uv run scripts/chain_c85_report.py --new thema_L_x2_c85 --before-b thema_L_repair
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#: Size bands, as every other leaves report uses them.
BANDS: tuple[tuple[int, int], ...] = (
    (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 300), (301, 1000), (1001, 10**9))
#: Support bands for the reproducibility breakdown, as the brief names them.
SUPPORT_BANDS: tuple[tuple[float, float, str], ...] = (
    (0.0, 0.1, "< 0.1"), (0.1, 0.3, "0.1-0.3"), (0.3, 0.5, "0.3-0.5"), (0.5, 1.01, ">= 0.5"))
#: The match threshold the reproducibility statistic is stated over.
MATCH = 0.70
#: The declared chain-collapse share of this arm.
SHARE = 0.85
#: A root at or above this many members is a giant bag, not a theme.
GIANT = 1000
#: The baseline's plausibility, which criterion (e) must not fall below.
BASELINE_PLAUSIBLE = 0.977


def band_of(size: int) -> str:
    """Size band label for a theme size.

    Args:
        size: Member count.

    Returns:
        The band label.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10**9 else f"{low}+"
    return "other"


def support_band(support: float) -> str:
    """Support band label.

    Args:
        support: Theme support.

    Returns:
        The band label.
    """
    for low, high, name in SUPPORT_BANDS:
        if low <= support < high:
            return name
    return ">= 0.5"


def read(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, float]]:
    """Members, parent edges and support for a built ontology.

    Args:
        path: A build directory.

    Returns:
        ``(node -> members, child -> parents, node -> support)``.
    """
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    parents: dict[str, set[str]] = defaultdict(set)
    with (path / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
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
        keys: The member set to match.
        other: The other build's node to members.
        holders: The other build's inverted index.

    Returns:
        ``(node, jaccard)``, or ``("", 0.0)`` if nothing overlaps.
    """
    best = ("", 0.0)
    for node in {o for key in keys for o in holders.get(key, ())}:
        inter = len(keys & other[node])
        union = len(keys) + len(other[node]) - inter
        if union and inter / union > best[1]:
            best = (node, inter / union)
    return best


def containment_pairs(members: dict[str, set[str]],
                      share: float) -> list[tuple[str, str, float]]:
    """Strict-containment pairs at or above a size ratio.

    Checks **every** containment pair, not only the DAG's direct edges, which is what the collapse
    rule itself considers and therefore what criterion (a) must be measured over.

    Args:
        members: Node to members.
        share: The ratio to report at or above.

    Returns:
        ``(child, parent, ratio)`` for each qualifying pair.
    """
    holders = index(members)
    out: list[tuple[str, str, float]] = []
    for child, keys in members.items():
        for parent in {o for key in keys for o in holders.get(key, ())}:
            if parent == child or not keys < members[parent]:
                continue
            ratio = len(keys) / len(members[parent])
            if ratio >= share:
                out.append((child, parent, ratio))
    return out


def depths(members: dict[str, set[str]], parents: dict[str, set[str]]) -> dict[str, int]:
    """Longest path from each node up to a root.

    Args:
        members: Node to members, for the node list.
        parents: Child to parents.

    Returns:
        Node to depth, roots at 0.
    """
    memo: dict[str, int] = {}

    def depth(node: str) -> int:
        if node in memo:
            return memo[node]
        memo[node] = 0                      # guard against a cycle rather than recursing forever
        above = parents.get(node, ())
        memo[node] = 1 + max((depth(p) for p in above), default=-1) if above else 0
        return memo[node]

    for node in members:
        depth(node)
    return memo


def ancestors(node: str, parents: dict[str, set[str]]) -> set[str]:
    """Every ancestor of a node.

    Args:
        node: Starting node.
        parents: Child to parents.

    Returns:
        All ancestors.
    """
    seen: set[str] = set()
    stack = [node]
    while stack:
        for parent in parents.get(stack.pop(), ()):
            if parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return seen


def reproducibility(a_dir: Path, b_dir: Path, excluded: set[str], title: str) -> dict[str, float]:
    """Share of A's themes matched at the threshold in B, overall and by support band.

    Uses the **projected** comparison -- B's sets with the excluded inputs removed -- because the
    two builds stand over universes differing by exactly those keys.

    Args:
        a_dir: The build whose themes are counted.
        b_dir: The independent build matched against.
        excluded: Excluded input keys, removed from B's sets.
        title: Label for the printed block.

    Returns:
        ``{"overall": share, band: share, ...}``.
    """
    a_mem, _a_par, a_sup = read(a_dir)
    b_mem, _b_par, _b_sup = read(b_dir)
    projected = {node: keys - excluded for node, keys in b_mem.items()}
    holders = index(projected)
    matched: Counter[str] = Counter()
    total: Counter[str] = Counter()
    hits = 0
    for node, keys in a_mem.items():
        band = support_band(a_sup[node])
        total[band] += 1
        total["overall"] += 1
        if best_match(keys, projected, holders)[1] >= MATCH:
            matched[band] += 1
            matched["overall"] += 1
            hits += 1
    print(f"  {title}")
    print(f"    {a_dir.name} ({len(a_mem):,} themes) against {b_dir.name} ({len(b_mem):,}), "
          f"projected")
    print(f"      {'support band':<14}{'themes':>9}{'matched':>10}{'share':>9}")
    for _low, _high, name in SUPPORT_BANDS:
        if total[name]:
            print(f"      {name:<14}{total[name]:>9,}{matched[name]:>10,}"
                  f"{100 * matched[name] / total[name]:>8.1f}%")
    print(f"      {'OVERALL':<14}{total['overall']:>9,}{matched['overall']:>10,}"
          f"{100 * hits / total['overall']:>8.1f}%")
    out = {"overall": hits / total["overall"]}
    out.update({name: (matched[name] / total[name] if total[name] else float("nan"))
                for _low, _high, name in SUPPORT_BANDS})
    return out


def main(argv: list[str] | None = None) -> int:
    """Run every measurement and print the criteria table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--baseline", type=Path,
                        default=Path("data/ontology/frozen/baseline-2026-10-09"))
    parser.add_argument("--new", default="thema_L_x2_c85")
    parser.add_argument("--before-a", default="thema_L_x2")
    parser.add_argument("--before-b", default="thema_L_repair")
    parser.add_argument("--after-a", default="thema_L_x2_c85")
    parser.add_argument("--after-b", default="thema_L_repair_c85")
    parser.add_argument("--fan", default="n00150",
                        help="the fan's node id in thema_L_repair, mapped by member set")
    parser.add_argument("--fan-build", default="thema_L_repair")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    new_dir = root / args.new
    base_mem, base_par, base_sup = read(args.baseline)
    new_mem, new_par, new_sup = read(new_dir)
    repair_map = json.loads((new_dir / "repair_map.json").read_text())
    with Path("data/excluded_inputs.tsv").open() as handle:
        excluded = {row["key"] for row in csv.DictReader(handle, delimiter="\t")}

    print(f"CHAIN COLLAPSE {SHARE}, survivor {repair_map['survivor']} -- POST-HOC RULE")
    print(f"  baseline {args.baseline}  ({len(base_mem):,} themes)")
    print(f"  new      {new_dir}  ({len(new_mem):,} themes)\n")

    # ---------------------------------------------------------------- 3. reproducibility
    print("=" * 78)
    print("3. REPRODUCIBILITY BETWEEN TWO INDEPENDENT BUILDS (criterion d)")
    print("=" * 78)
    before = reproducibility(root / args.before_a, root / args.before_b, excluded,
                             "BEFORE the rule")
    print()
    after = reproducibility(root / args.after_a, root / args.after_b, excluded,
                            "AFTER the rule")
    print(f"\n  overall {100 * before['overall']:.1f}% -> {100 * after['overall']:.1f}%  "
          f"({100 * (after['overall'] - before['overall']):+.1f} points)")

    # ---------------------------------------------------------------- 4. against the baseline
    print("\n" + "=" * 78)
    print("4. AGAINST THE FROZEN BASELINE")
    print("=" * 78)
    base_by_set = {frozenset(keys): node for node, keys in base_mem.items()}
    new_by_set = {frozenset(keys): node for node, keys in new_mem.items()}
    survived = {node: base_by_set[frozenset(keys)]
                for node, keys in new_mem.items() if frozenset(keys) in base_by_set}
    removed = [node for node, keys in base_mem.items() if frozenset(keys) not in new_by_set]
    invented = [node for node in new_mem if node not in survived]

    print(f"\n  themes 8,740 -> {len(new_mem):,}  ({len(new_mem) - len(base_mem):+,})")
    print(f"    baseline themes with no identical theme in the new build: {len(removed):,}")
    print(f"    new themes identical to a baseline theme:                 {len(survived):,}")
    print(f"    new themes NOT identical to any baseline theme:           {len(invented):,}")

    print("\n  themes removed, by size band")
    counts = Counter(band_of(len(base_mem[n])) for n in removed)
    base_bands = Counter(band_of(len(v)) for v in base_mem.values())
    new_bands = Counter(band_of(len(v)) for v in new_mem.values())
    print(f"    {'band':<10}{'baseline':>10}{'new':>8}{'delta':>8}{'removed':>9}")
    for low, high in BANDS:
        name = f"{low}-{high}" if high < 10**9 else f"{low}+"
        print(f"    {name:<10}{base_bands.get(name, 0):>10,}{new_bands.get(name, 0):>8,}"
              f"{new_bands.get(name, 0) - base_bands.get(name, 0):>+8,}"
              f"{counts.get(name, 0):>9,}")

    kept = Counter(event["kept"] for event in repair_map["collapsed"])
    print(f"\n  collapse direction, from {new_dir.name}/repair_map.json")
    print(f"    collapse events: {len(repair_map['collapsed']):,}")
    print(f"      child kept  (the parent was absorbed): {kept['child']:,}")
    print(f"      parent kept (the child was absorbed):  {kept['parent']:,}")
    print(f"    stale merges afterwards: {len(repair_map['merged']):,}")

    # How decisive the survivor rule was. A tiny margin means the rule is near a coin flip, and a
    # coin flip resolved differently in two independent builds costs reproducibility.
    margins = sorted(abs(e["victim_support"] - e["keeper_support"])
                     for e in repair_map["collapsed"])
    tiny = sum(1 for m in margins if m < 0.05)
    ties = sum(1 for m in margins if m == 0.0)
    print("    support margin between the two nodes of each collapsed pair")
    print(f"      median {statistics.median(margins):.3f}, "
          f"mean {statistics.mean(margins):.3f}")
    print(f"      exact ties (parent kept by the rule): {ties:,} "
          f"({100 * ties / len(margins):.1f}%)")
    print(f"      margin under 0.05:                    {tiny:,} "
          f"({100 * tiny / len(margins):.1f}%)")

    gone = [base_sup[n] for n in removed]
    stay = [base_sup[base] for base in survived.values()]
    print("\n  support of baseline themes, removed against surviving")
    print(f"    removed   n={len(gone):,}  mean {statistics.mean(gone):.4f}  "
          f"median {statistics.median(gone):.4f}")
    print(f"    surviving n={len(stay):,}  mean {statistics.mean(stay):.4f}  "
          f"median {statistics.median(stay):.4f}")

    # parents, and whether a lost parent reappears one level up
    base_anc = {node: ancestors(node, base_par) for node in survived.values()}
    changed = reattached = 0
    exceptions: list[tuple[str, str]] = []
    multi_checked = 0
    for new_node, base_node in survived.items():
        was = {frozenset(base_mem[p]) for p in base_par.get(base_node, ())}
        now = {frozenset(new_mem[p]) for p in new_par.get(new_node, ())}
        if was != now:
            changed += 1
        gained_anc = sum(1 for s in now - was
                         if any(frozenset(base_mem[a]) == s for a in base_anc[base_node]))
        if gained_anc:
            reattached += 1
        if len(base_par.get(base_node, ())) < 2:
            continue
        multi_checked += 1
        for parent in base_par[base_node]:
            target = frozenset(base_mem[parent])
            if target in now:
                continue
            # The declared exception: the lost parent was chain-collapsed with another parent.
            partner = any(
                (target < other and len(target) >= SHARE * len(other))
                or (other < target and len(other) >= SHARE * len(target))
                for other in now)
            if not partner:
                exceptions.append((base_node, parent))

    print("\n  parents of surviving themes")
    print(f"    themes whose parent set changed at all:          {changed:,} of {len(survived):,}")
    print(f"    of which gained a baseline ANCESTOR as a parent: {reattached:,} "
          f"(re-attached one level up)")

    # Why a parent was lost, and whether the facet is still above the theme further up. This does
    # not soften criterion (b) -- it is reported as a failure either way -- it says what happened.
    still_exists = still_above = 0
    for base_node, parent in exceptions:
        target = frozenset(base_mem[parent])
        new_node = next(n for n, b in survived.items() if b == base_node)
        if target in new_by_set:
            still_exists += 1
            if new_by_set[target] in ancestors(new_node, new_par):
                still_above += 1
    print(f"\n    of the {len(exceptions):,} lost parents (criterion b exceptions):")
    print(f"      the parent theme still exists in the new build:     {still_exists:,}")
    print(f"      and is still an ANCESTOR of the theme, one level up: {still_above:,}")
    print(f"      the parent theme is gone entirely (absorbed):       "
          f"{len(exceptions) - still_exists:,}")

    # pathways and their levels
    base_levels = Counter(k for n, v in base_mem.items() if len(v) < GIANT for k in v)
    new_levels = Counter(k for n, v in new_mem.items() if len(v) < GIANT for k in v)
    every = set(base_levels) | set(new_levels)
    lost = {k: base_levels[k] - new_levels[k] for k in every if new_levels[k] < base_levels[k]}
    stranded = sorted(k for k in every if base_levels[k] > 0 and new_levels[k] == 0)
    print(f"\n  pathway levels (themes under {GIANT:,} members holding each pathway)")
    print(f"    pathways that lost at least one level: {len(lost):,} of {len(every):,}")
    if lost:
        print(f"      median levels lost {statistics.median(lost.values()):.0f}, "
              f"max {max(lost.values())}")
    print(f"    pathways left with NO theme under {GIANT:,}: {len(stranded)}"
          + (f"  {stranded[:8]}" if stranded else ""))

    print("\n  depth distribution (longest path to a root)")
    base_depth = Counter(depths(base_mem, base_par).values())
    new_depth = Counter(depths(new_mem, new_par).values())
    print(f"    {'depth':<8}{'baseline':>10}{'new':>8}")
    for level in sorted(set(base_depth) | set(new_depth)):
        print(f"    {level:<8}{base_depth.get(level, 0):>10,}{new_depth.get(level, 0):>8,}")

    # ---------------------------------------------------------------- the fan
    print("\n  the fan around " + args.fan)
    fan_mem, fan_par, _fan_sup = read(root / args.fan_build)
    # The fan build stands over the wider universe, so its sets must be projected -- the excluded
    # inputs removed -- before they can be looked up in the baseline or the new build at all.
    def projected_set(node: str) -> frozenset[str]:
        """The fan build's member set with the excluded inputs removed."""
        return frozenset(fan_mem[node] - excluded)

    fan_set = projected_set(args.fan)
    base_fan = base_by_set.get(fan_set)
    new_fan = new_by_set.get(fan_set)
    print(f"    {args.fan} in {args.fan_build}: {len(fan_set)} members, "
          f"{len(fan_par.get(args.fan, ())):,} parents")
    print(f"    the same member set is {base_fan} in the baseline and "
          f"{new_fan or 'ABSENT'} in the new build")
    if base_fan and new_fan:
        was = sorted(base_par.get(base_fan, ()), key=lambda n: -len(base_mem[n]))
        now = sorted(new_par.get(new_fan, ()), key=lambda n: -len(new_mem[n]))
        print(f"    parents before ({len(was)}):")
        for parent in was:
            target = frozenset(base_mem[parent])
            match = new_by_set.get(target)
            print(f"      {parent:<9} {len(base_mem[parent]):>3} members  "
                  f"support {base_sup[parent]:.3f}  "
                  f"ratio {len(fan_set) / len(base_mem[parent]):.3f}  -> "
                  f"{match or 'GONE'}")
        print(f"    parents after ({len(now)}):")
        for parent in now:
            print(f"      {parent:<9} {len(new_mem[parent]):>3} members  "
                  f"support {new_sup[parent]:.3f}  "
                  f"ratio {len(fan_set) / len(new_mem[parent]):.3f}")
        fan_parents = sorted(fan_par.get(args.fan, ()), key=lambda n: -len(fan_mem[n]))
        # The reviewer's node ids are from the wider universe, so exact set identity almost never
        # holds across the exclusion rebuild. Each is tracked by its BEST match in both builds: if
        # the baseline and the new build give the same partner at the same Jaccard, this rule
        # changed nothing here.
        base_holders_fan, new_holders_fan = index(base_mem), index(new_mem)
        print(f"    PROVENANCE: the reviewer counted {len(fan_parents)} parents in "
              f"{args.fan_build}, over the wider universe. The fan node's own set survives the "
              f"projection exactly, but its parents do not, so the count read as "
              f"{len(fan_parents)} there and {len(was)} in the baseline. That change is the "
              f"EXCLUSION REBUILD, before this rule. Each is tracked below by best match.")
        print(f"      {'node':<9}{'size':>5}  {'baseline':<10}{'J':>6}   {'new':<10}{'J':>6}  rule")
        tracked = [("parent", node) for node in fan_parents]
        tracked += [(route, node) for route, named in (
            ("route A", ("n00918", "n03842", "n08023", "n04419", "n02115")),
            ("route B", ("n03423",)),
            ("route C", ("n07791",))) for node in named]
        unchanged = 0
        for what, node in tracked:
            if node not in fan_mem:
                print(f"      {node:<9}  absent in {args.fan_build}")
                continue
            target = projected_set(node)
            b_node, b_jac = best_match(target, base_mem, base_holders_fan)
            n_node, n_jac = best_match(target, new_mem, new_holders_fan)
            same = abs(b_jac - n_jac) < 1e-9
            unchanged += same
            print(f"      {node:<9}{len(target):>5}  {b_node or '-':<10}{b_jac:>6.3f}   "
                  f"{n_node or '-':<10}{n_jac:>6.3f}  "
                  f"{'unchanged' if same else 'CHANGED'}  ({what})")
        print(f"    {unchanged} of {len(tracked)} tracked nodes match the baseline and the new "
              f"build at the SAME Jaccard: the 0.85 rule did not touch this fan.")
        was_anc, now_anc = ancestors(base_fan, base_par), ancestors(new_fan, new_par)
        print(f"    ancestors: {len(was_anc)} -> {len(now_anc)}")
        was_roots = sorted(a for a in was_anc if not base_par.get(a))
        now_roots = sorted(a for a in now_anc if not new_par.get(a))
        print(f"    roots reached: {len(was_roots)} -> {len(now_roots)}")
        print(f"      before {was_roots}")
        print(f"      after  {now_roots}")

    # ---------------------------------------------------------------- carried verdicts
    print("\n  plausibility, verdicts carried from the baseline by identical member set")
    verdicts = json.loads((args.baseline / "all_verdicts_x2.json").read_text())
    carried = Counter(verdicts[base]["verdict"] for base in survived.values() if base in verdicts)
    total = sum(carried.values())
    okay = carried["coherent"] + carried["umbrella"]
    print(f"    carried onto {total:,} of {len(new_mem):,} new themes "
          f"({100 * total / len(new_mem):.1f}%); {len(invented):,} are unjudged")
    for name, count in carried.most_common():
        print(f"      {name:<18}{count:>6,}{100 * count / total:>8.2f}%")
    print(f"    coherent or umbrella: {okay:,} of {total:,} = {100 * okay / total:.1f}%")

    # ---------------------------------------------------------------- the mapping
    destination = new_dir / "match_to_baseline.tsv"
    base_holders = index(base_mem)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["new_node", "baseline_node", "identical",
                                            "jaccard", "new_size"])
        writer.writeheader()
        for node in sorted(new_mem):
            keys = new_mem[node]
            if node in survived:
                writer.writerow({"new_node": node, "baseline_node": survived[node],
                                 "identical": "yes", "jaccard": 1.0, "new_size": len(keys)})
                continue
            match, score = best_match(keys, base_mem, base_holders)
            writer.writerow({"new_node": node, "baseline_node": match, "identical": "no",
                             "jaccard": round(score, 4), "new_size": len(keys)})
    print(f"\n  -> {destination}")

    # ---------------------------------------------------------------- 5. the DAG
    print("\n" + "=" * 78)
    print("5. DAG CHECK")
    print("=" * 78)
    bad_edges = [(child, parent) for child, above in new_par.items() for parent in above
                 if not new_mem[child] < new_mem[parent]]
    depth_map = depths(new_mem, new_par)
    cyclic = [node for node, above in new_par.items()
              if any(depth_map[p] >= depth_map[node] for p in above)]
    duplicates = len(new_mem) - len(new_by_set)
    print(f"    edges: {sum(len(v) for v in new_par.values()):,}")
    print(f"    edges violating strict containment: {len(bad_edges)}")
    print(f"    nodes whose parent is not strictly shallower (cycle evidence): {len(cyclic)}")
    print(f"    duplicate member sets: {duplicates}")
    valid = not (bad_edges or cyclic or duplicates)
    print("    VERDICT: "
          + ("valid DAG with strict containment" if valid else "INVALID"))

    # ---------------------------------------------------------------- 6. criteria
    print("\n" + "=" * 78)
    print("6. CRITERIA, DECLARED BEFORE THE BUILDS RAN")
    print("=" * 78)
    left = containment_pairs(new_mem, SHARE)
    a_pass = not left
    b_pass = not exceptions
    c_pass = not stranded
    d_pass = after["overall"] > before["overall"]
    e_pass = okay / total >= BASELINE_PLAUSIBLE
    rows = [
        ("a", "no containment pair at ratio >= 0.85 remains",
         f"{len(left)} such pairs", a_pass),
        ("b", "every multi-parent baseline theme keeps all parents",
         f"{len(exceptions)} exceptions over {multi_checked:,} multi-parent themes", b_pass),
        ("c", f"no pathway loses all themes under {GIANT:,}",
         f"{len(stranded)} stranded pathways", c_pass),
        ("d", "reproducibility at J >= 0.7 is higher after the rule",
         f"{100 * before['overall']:.1f}% -> {100 * after['overall']:.1f}%", d_pass),
        ("e", f"carried plausibility >= {100 * BASELINE_PLAUSIBLE:.1f}%",
         f"{100 * okay / total:.1f}%", e_pass)]
    for key, what, number, ok in rows:
        print(f"    ({key}) {'PASS' if ok else 'FAIL'}  {what}")
        print(f"         {number}")
    print(f"\n    ALL FIVE: {'PASS' if all(r[3] for r in rows) else 'FAIL'}")
    if left:
        print("\n    criterion (a), the first 10 surviving pairs:")
        for child, parent, ratio in sorted(left, key=lambda t: -t[2])[:10]:
            print(f"      {child} ({len(new_mem[child])}) in {parent} "
                  f"({len(new_mem[parent])}) ratio {ratio:.3f}")
    if exceptions:
        print(f"\n    criterion (b), the {len(exceptions)} exceptions "
              f"(baseline theme, parent lost):")
        for node, parent in exceptions[:25]:
            print(f"      {node} lost {parent} ({len(base_mem[parent])} members, "
                  f"ratio {len(base_mem[node]) / len(base_mem[parent]):.3f})")
        if len(exceptions) > 25:
            print(f"      ... and {len(exceptions) - 25} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
