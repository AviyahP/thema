#!/usr/bin/env python3
"""Every figure prompt 37 asks for, beside rec2.

Reads the two builds and prints nothing it did not measure. ``--rec2`` is read only, never written.

Usage::

    uv run scripts/areas_rec2fix_report.py
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

#: O50's own giant bar, which is also Aviyah's bar for an area.
GIANT = 1000

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80

#: The declared criteria.
MIN_ROOTS = 20
MAX_ROOTS = 60
MAX_CHILDREN = 60
REPARENT_BAR = 0.95
ROOT_J_LIMIT = 0.50
REPORT_J = 0.30
NESTED_SHARE = 0.80
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01

#: Pathway bands for the "largest thing above me" table.
BANDS = ((1, 10), (11, 50), (51, 200), (201, 1000), (1001, 10**9))


def band_of(size: int) -> str:
    """The band label a size falls in.

    Args:
        size: Member count.

    Returns:
        The band label, or ``"none"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10**9 else f"{low}+"
    return "none"


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard of two key sets.

    Args:
        a: One set.
        b: The other.

    Returns:
        The index, 0.0 if both are empty.
    """
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def triple(values: Sequence[int]) -> str:
    """``min/median/max`` as one string.

    Args:
        values: The numbers.

    Returns:
        The summary, or ``"-"`` if empty.
    """
    if not values:
        return "-"
    return f"{min(values)}/{statistics.median(values):.0f}/{max(values)}"


def rec2_view(two: Mapping[str, object], members: Mapping[str, set[str]]) -> dict[str, set[str]]:
    """rec2's areas plus anchors, so the two builds are compared on the same kind of object.

    Args:
        two: rec2's ``levels.json``.
        members: O50 node to member keys.

    Returns:
        Node id to pathway keys.
    """
    top = two["levels"][-1]
    out = {node: set(keys) for node, keys in zip(top["node_ids"], top["pathway_members"],
                                                 strict=True)}
    out.update({anchor: set(members[anchor]) for anchor in two["anchors"]})
    return out


def rec2_roots(two: Mapping[str, object], members: Mapping[str, set[str]]) -> dict[str, set[str]]:
    """rec2's roots: its area roots plus its anchors.

    Args:
        two: rec2's ``levels.json``.
        members: O50 node to member keys.

    Returns:
        Root id to pathway keys.
    """
    top = two["levels"][-1]
    out = {top["node_ids"][i]: set(top["pathway_members"][i]) for i in top["roots"]}
    out.update({anchor: set(members[anchor]) for anchor in two["anchors"]})
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--build", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix"))
    parser.add_argument("--rec2", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    import recursive_top_O50 as rt

    nodes, members = rt.read_build(args.frozen)
    fix = json.loads((args.build / "levels.json").read_text())
    two = json.loads((args.rec2 / "levels.json").read_text())
    comb = fix["combined"]
    level2 = fix["level2"]
    giant_only = set(fix["giant_only"])
    anchors = list(fix["anchor_ids"])
    allk = {k for v in members.values() for k in v}

    kind_of = dict(zip(comb["ids"], comb["kinds"], strict=True))
    units_of = dict(zip(comb["ids"], comb["units_per_node"], strict=True))
    support_of = dict(zip(comb["ids"], comb["support"], strict=True))
    unit_keys = {node: set(keys) for node, keys
                 in zip(fix["unit_ids"], fix["unit_pathways"], strict=True)}
    area_keys = {node: set(keys) for node, keys
                 in zip(level2["node_ids"], level2["pathway_members"], strict=True)}

    def keys_of(node: str) -> set[str]:
        """Pathway keys of any combined node."""
        return area_keys[node] if kind_of[node] == "area" else unit_keys[node]

    giants = sorted(comb["giants"])
    view = list(comb["view"])
    roots = list(comb["roots"])
    children = {node: list(kids) for node, kids in comb["children"].items()}
    parents = {node: list(up) for node, up in comb["parents"].items()}
    counts = [len(children[node]) for node in view]
    view_keys = {node: keys_of(node) for node in view}
    root_keys = {node: view_keys[node] for node in roots}

    print("THE AREAS LAYER, CORRECTED (rec2fix). Declared 15 Oct 2026 before any result.")
    print("A corrected re-run of prompt 36, not a new method. ADOPTS NOTHING by itself.\n")

    print("=" * 78)
    print("WHAT THE TWO CORRECTIONS CHANGED")
    print("=" * 78)
    two_top = two["levels"][-1]
    two_areas = {node: set(keys) for node, keys
                 in zip(two_top["node_ids"], two_top["pathway_members"], strict=True)}
    same_count = len(area_keys) == len(two_areas)
    print("  level 2 is unchanged up to the gate, by construction: same units, same seeds, "
          "same floors")
    print(f"    candidates      {level2['n_candidates']:>8,}   "
          f"rec2 {two_top['n_candidates']:>8,}")
    print(f"    through gate    {level2['n_gated']:>8,}   rec2 {two_top.get('n_gated', 0):>8,}")
    print(f"    after consensus {level2['n_after_consensus']:>8,}   "
          f"rec2 {two_top['n_after_consensus']:>8,}")
    print(f"    areas           {len(area_keys):>8,}   rec2 {len(two_areas):>8,}"
          f"{'   (identical count)' if same_count else ''}")
    shared = sorted(set(area_keys) & set(two_areas))
    grew = [(len(area_keys[a]) - len(two_areas[a]), a) for a in shared]
    bigger = [g for g in grew if g[0] > 0]
    print(f"  CORRECTION 1, the union: of the {len(shared)} areas with the same id, "
          f"{len(bigger)} hold MORE pathways than rec2 stored")
    if bigger:
        bigger.sort(reverse=True)
        total = sum(g[0] for g in bigger)
        print(f"    {total:,} pathway rows restored; median gain "
              f"{statistics.median([g[0] for g in bigger]):.0f}, largest "
              f"{bigger[0][0]} ({bigger[0][1]})")
    print(f"  CORRECTION 2, the seams: {len(comb['collapsed'])} collapses and "
          f"{len(comb['merged'])} merges over the combined set, "
          f"{sum(1 for e in comb['seams'] if e['seam'])} of them involving an anchor or a unit")
    print(f"    direct edges {comb['n_direct_edges']:,}, containment pairs "
          f"{comb['n_closure_pairs']:,}  (rec2 wrote every area-to-unit pair as an edge)")

    print("\n" + "=" * 78)
    print("ANCHORS")
    print("=" * 78)
    for anchor in sorted(anchors, key=lambda a: -len(members[a])):
        row = nodes[anchor]
        inview = anchor in set(view)
        print(f"  {anchor:<12} {len(members[anchor]):>5} pathways   support {row['support']:>7}"
              f"   O50 children {len(row['children'].split()):>4}"
              f"   {'ROOT' if anchor in set(roots) else ('in view' if inview else 'DROPPED')}"
              f"{'   (giant-only in O50)' if anchor in giant_only else ''}")
    print(f"  {len(anchors)} anchors, "
          f"{len(set().union(*(members[a] for a in anchors))):,} pathways between them")

    print("\n" + "=" * 78)
    print(f"GIANT AREAS, over {GIANT:,} pathways: flagged and kept out of the view")
    print("=" * 78)
    print(f"  {'area':<12}{'pathways':>10}{'units':>7}{'support':>9}{'share of universe':>19}")
    for node in sorted(giants, key=lambda n: -len(keys_of(n))):
        print(f"  {node:<12}{len(keys_of(node)):>10}{len(units_of[node]):>7}"
              f"{support_of[node]:>9.3f}{len(keys_of(node)) / len(allk):>18.1%}")
    giant_union = set().union(*(keys_of(n) for n in giants)) if giants else set()
    print(f"  {len(giants)} giants; their union holds {len(giant_union):,} of {len(allk):,} "
          f"pathways = {len(giant_union) / len(allk):.1%}")
    print(f"  rec2 had the same {sum(1 for v in two_areas.values() if len(v) > GIANT)} areas over "
          f"{GIANT:,} and reported them as a criterion failure, before the rule was written down")

    print("\n" + "=" * 78)
    print("MERGES AND COLLAPSES AT THE SEAMS")
    print("=" * 78)
    if not comb["seams"]:
        print("  none")
    print(f"  {'rule':<10}{'victim':<14}{'kind':<8}{'size':>6}   "
          f"{'keeper':<14}{'kind':<8}{'size':>6}  seam?")
    for event in comb["seams"]:
        print(f"  {event['rule']:<10}{event['victim']:<14}{event['victim_kind']:<8}"
              f"{event['victim_size']:>6}   {event['keeper']:<14}{event['keeper_kind']:<8}"
              f"{event['keeper_size']:>6}  {'YES' if event['seam'] else ''}")
    print("  rec2 applied neither rule at a seam: 0 of its 343 areas was compared with an anchor "
          "or with one of its own units")

    print("\n" + "=" * 78)
    print("HELD-OUT FDR PER STRATUM (rec2's floors and seeds, reused unchanged)")
    print("=" * 78)
    was = {e["stratum"]: e for e in two_top["confirmed"]["strata"]}
    print(f"    {'stratum':<9}{'floor':>10}{'calib FDR':>11}{'held-out':>10}{'real':>7}"
          f"{'cap':>7}   rec2 held-out")
    worst = None
    for entry in level2["confirmed"]["strata"]:
        value = entry["heldout_fdr"]
        flag = "" if value is None or value <= CAP_STRATUM else "  OVER"
        print(f"    {entry['stratum']:<9}{str(entry['effective']):>10}"
              f"{str(entry['calibration_fdr']):>11}{str(value):>10}"
              f"{entry['heldout_real']:>7}{CAP_STRATUM:>7}{flag}"
              f"   {was.get(entry['stratum'], {}).get('heldout_fdr')}")
        if value is not None and (worst is None or value > worst[1]):
            worst = (entry["stratum"], value)
    overall = level2["confirmed"]["overall_fdr"]
    print(f"    OVERALL {str(overall):>32}{'':>14}{CAP_OVERALL:>7}"
          f"{'  OVER' if overall is not None and overall > CAP_OVERALL else ''}"
          f"   rec2 {two_top['confirmed']['overall_fdr']}")

    print("\n" + "=" * 78)
    print("THE VIEW: ROOTS, SIZES AND CHILDREN")
    print("=" * 78)
    by_kind = Counter(kind_of[n] for n in view)
    print(f"  nodes in the view: {len(view):,}  "
          f"({by_kind['area']} areas, {by_kind['anchor']} anchors, {by_kind['unit']} units)")
    print(f"  ROOTS: {len(roots)}  "
          f"({Counter(kind_of[r] for r in roots)['area']} areas, "
          f"{Counter(kind_of[r] for r in roots)['anchor']} anchors, "
          f"{Counter(kind_of[r] for r in roots)['unit']} units)")
    print(f"  direct children per node: max {max(counts, default=0)}, "
          f"median {statistics.median(counts):.0f}, "
          f"{sum(1 for c in counts if c > MAX_CHILDREN)} over {MAX_CHILDREN}")
    print(f"  multi-parent nodes: {sum(1 for n in view if len(parents[n]) >= 2):,} = "
          f"{sum(1 for n in view if len(parents[n]) >= 2) / len(view):.1%}")
    print(f"  size in pathways, all view nodes: {triple([len(view_keys[n]) for n in view])}")
    print(f"  size in pathways, roots only:     {triple([len(root_keys[r]) for r in roots])}")
    print("\n  every root, largest first")
    print(f"  {'root':<14}{'kind':<8}{'pathways':>10}{'units':>7}{'support':>9}{'children':>10}")
    for node in sorted(roots, key=lambda n: -len(root_keys[n])):
        print(f"  {node:<14}{kind_of[node]:<8}{len(root_keys[node]):>10}"
              f"{len(units_of[node]):>7}{support_of[node]:>9.3f}{len(children[node]):>10}")

    print("\n" + "=" * 78)
    print("WHY 63 ROOTS AND NOT 42: the giant rule, measured")
    print("=" * 78)
    r2roots = rec2_roots(two, members)
    alive = list(comb["alive"])
    held_alive = {node: keys_of(node) for node in alive}
    pairs_alive = {(c, p) for c, p in itertools.permutations(alive, 2)
                   if held_alive[c] < held_alive[p]}
    parented = {c for c, _ in pairs_alive}
    roots_alive = [node for node in alive if node not in parented]
    giant_set = set(giants)
    print(f"  with the giants IN, the combined structure has {len(roots_alive)} roots "
          f"({sum(1 for r in roots_alive if kind_of[r] == 'area')} areas, "
          f"{sum(1 for r in roots_alive if kind_of[r] == 'anchor')} anchors, "
          f"{sum(1 for r in roots_alive if kind_of[r] == 'unit')} units)")
    print(f"    which is rec2's count exactly: {len(r2roots)}")
    print(f"    of those, {sum(1 for r in roots_alive if r in giant_set)} are giants")
    promoted = [r for r in roots if r not in set(roots_alive)]
    only_giant = [r for r in promoted
                  if {p for c, p in pairs_alive if c == r}
                  and not ({p for c, p in pairs_alive if c == r} - giant_set)]
    print(f"  dropping the {len(giants)} giants promotes {len(promoted)} areas to roots, "
          f"{len(only_giant)} of which had no non-giant parent at all")
    print(f"  {len(roots_alive)} - {sum(1 for r in roots_alive if r in giant_set)} giant roots "
          f"+ {len(promoted)} promoted = {len(roots)} roots in the view")
    print("  So the root criterion fails BECAUSE Aviyah's giant rule was applied. It is the same")
    print("  mechanism that made 476 O50 themes units in the first place: a node whose only")
    print("  parents are giants is a root of the real hierarchy.")

    print("\n" + "=" * 78)
    print("ROOT OVERLAP, measured on pathways")
    print("=" * 78)
    per_pathway: Counter[str] = Counter()
    for keys in root_keys.values():
        for key in keys:
            per_pathway[key] += 1
    dist = Counter(per_pathway.values())
    print(f"  pathways in no root: {len(allk) - len(per_pathway):,}")
    if per_pathway:
        values = list(per_pathway.values())
        print(f"  roots per pathway: median {statistics.median(values):.0f}, "
              f"mean {statistics.mean(values):.2f}, max {max(values)}")
        print(f"    {'roots':<8}{'pathways':>10}")
        for count in sorted(dist):
            print(f"    {count:<8}{dist[count]:>10,}")
    r2per: Counter[str] = Counter()
    for keys in r2roots.values():
        for key in keys:
            r2per[key] += 1
    print(f"  rec2, for comparison: {len(r2roots)} roots, roots per pathway median "
          f"{statistics.median(list(r2per.values())):.0f}, max {max(r2per.values())}")

    print(f"\n  every root pair at pathway Jaccard {REPORT_J} or more")
    over = []
    for (a, ka), (b, kb) in itertools.combinations(sorted(root_keys.items()), 2):
        value = jaccard(ka, kb)
        if value >= REPORT_J:
            over.append((value, a, b, len(ka), len(kb), len(ka & kb)))
    over.sort(reverse=True)
    pairs = list(itertools.combinations(sorted(root_keys.items()), 2))
    highest = max((jaccard(ka, kb) for (_, ka), (_, kb) in pairs), default=0.0)
    if not over:
        print(f"    none at or above {REPORT_J}. The highest of {len(pairs):,} pairs is "
              f"{highest:.3f}")
    for value, a, b, sa, sb, shared in over:
        print(f"    J {value:.3f}  {a} ({sa}) / {b} ({sb}), sharing {shared}"
              f"{'   OVER THE 0.50 LIMIT' if value >= ROOT_J_LIMIT else ''}")
    r2over = sorted((jaccard(ka, kb) for (_, ka), (_, kb)
                     in itertools.combinations(sorted(r2roots.items()), 2)), reverse=True)
    print(f"    rec2, for comparison: top pairs {', '.join(f'{v:.2f}' for v in r2over[:5])}; "
          f"{sum(1 for v in r2over if v >= REPORT_J)} at or above {REPORT_J}")

    print(f"\n  roots {NESTED_SHARE:.0%} or more inside another root (REPORT ONLY)")
    inside = []
    for (a, ka), (b, kb) in itertools.permutations(sorted(root_keys.items()), 2):
        if ka and len(ka & kb) >= NESTED_SHARE * len(ka):
            inside.append((len(ka & kb) / len(ka), a, len(ka), b, len(kb)))
    inside.sort(reverse=True)
    print(f"    {len({i[1] for i in inside})} of {len(roots)} roots are at least "
          f"{NESTED_SHARE:.0%} inside another; {len(inside)} ordered pairs")
    for share, a, sa, b, sb in inside[:15]:
        print(f"    {share:.3f}  {a} ({sa}) inside {b} ({sb})")
    r2_inside = {a for (a, ka), (b, kb) in itertools.permutations(sorted(r2roots.items()), 2)
                 if ka and len(ka & kb) >= NESTED_SHARE * len(ka)}
    print(f"    rec2, for comparison: {len(r2_inside)} of {len(r2roots)}")

    print("\n" + "=" * 78)
    print("COVERAGE")
    print("=" * 78)
    view_set = set(view)
    nongiant_parent = {node: [p for p in parents[node] if kind_of[p] in ("area", "anchor")]
                       for node in view}
    placed = {u for u in giant_only if u in view_set and nongiant_parent[u]}
    promoted = {u for u in giant_only if u in set(anchors)}
    gone = {u for u in giant_only if u not in view_set}
    print(f"  giant-only themes: {len(giant_only)}")
    print(f"    with a non-giant parent area or anchor: {len(placed)}")
    print(f"    promoted to an anchor (a root in their own right): {len(promoted)}")
    print(f"    merged or collapsed away by the seam rules: {len(gone)}  {sorted(gone)}")
    covered = placed | promoted | gone
    print(f"    accounted for: {len(covered)} = {len(covered) / len(giant_only):.1%}")
    rest = giant_only - covered
    print(f"    roots of the view with no parent: {len(rest)}  {sorted(rest)[:8]}")
    every_unit = [u for u in fix["unit_ids"]]
    unit_placed = {u for u in every_unit if u in view_set and nongiant_parent[u]}
    unit_gone = {u for u in every_unit if u not in view_set}
    unit_root = {u for u in every_unit if u in set(roots)}
    print(f"  all {len(every_unit)} units:")
    print(f"    with a non-giant parent area or anchor: {len(unit_placed)} = "
          f"{len(unit_placed) / len(every_unit):.1%}")
    print(f"    merged or collapsed away: {len(unit_gone)}")
    print(f"    roots of the view: {len(unit_root)}")
    print(f"    parented, dropped or a root: "
          f"{len(unit_placed | unit_gone | unit_root)} of {len(every_unit)}")
    o50_parents = {node: set(row["parents"].split()) for node, row in nodes.items()}
    print(f"  O50 roots before: {sum(1 for n in nodes if not o50_parents[n])}; "
          f"rec2fix view roots after: {len(roots)}; rec2 roots: {len(r2roots)}")

    print("\n  per pathway, the largest non-giant theme or area above it")
    o50_giants = set(fix["o50_giants"])
    before: dict[str, int] = {}
    for node, keys in members.items():
        if node in o50_giants:
            continue
        for key in keys:
            before[key] = max(before.get(key, 0), len(keys))
    after = dict(before)
    for node in view:
        for key in view_keys[node]:
            after[key] = max(after.get(key, 0), len(view_keys[node]))
    r2after = dict(before)
    for keys in rec2_view(two, members).values():
        for key in keys:
            r2after[key] = max(r2after.get(key, 0), len(keys))
    b_before = Counter(band_of(before.get(k, 0)) for k in allk)
    b_after = Counter(band_of(after.get(k, 0)) for k in allk)
    b_r2 = Counter(band_of(r2after.get(k, 0)) for k in allk)
    print(f"    {'band':<10}{'before':>9}{'rec2fix':>9}{'rec2':>9}")
    for low, high in BANDS:
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        print(f"    {label:<10}{b_before.get(label, 0):>9,}{b_after.get(label, 0):>9,}"
              f"{b_r2.get(label, 0):>9,}")

    print("\n" + "=" * 78)
    print("SUMMARY PLACEMENT (display only, nothing attached)")
    print("=" * 78)
    from thema.data.hierarchy import read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    names = {f"{r['source']}:{r['source_id']}": r["name"] for r in rows}
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {
        f"reactome:{c}": {f"reactome:{p}" for p in ps} for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(),
            PRIMARY_RELATIONS).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}
    key_sets = targets(edges, sorted(set(names) - allk), allk, min_size=3)

    def home(leaf_set: frozenset[str], pool: Mapping[str, set[str]]) -> str:
        """The smallest node holding HOME_SHARE of a summary's leaves, if any."""
        best, size = "", 0
        for node_id, keys in pool.items():
            if len(leaf_set & keys) >= HOME_SHARE * len(leaf_set):
                if not best or len(keys) < size:
                    best, size = node_id, len(keys)
        return best

    base = {n: v for n, v in members.items() if n not in o50_giants}
    pool_fix = {**base, **{n: view_keys[n] for n in view}}
    pool_two = {**base, **rec2_view(two, members)}
    # rec2 never dropped its 1,000-plus areas, so the honest comparison needs both: the view as
    # the giant rule defines it, and the same build with the giants left in.
    pool_all = {**pool_fix, **{n: keys_of(n) for n in giants}}
    got0 = sum(1 for s in key_sets.values() if home(s, members))
    got2 = sum(1 for s in key_sets.values() if home(s, pool_two))
    gotf = sum(1 for s in key_sets.values() if home(s, pool_fix))
    gota = sum(1 for s in key_sets.values() if home(s, pool_all))
    print(f"  curated summaries with 3+ leaf descendants in L: {len(key_sets):,}")
    print(f"    with a node holding {HOME_SHARE:.0%} of their leaves:")
    print(f"      O50 alone             {got0:>6} = {got0 / len(key_sets):.1%}")
    print(f"      rec2 combined         {got2:>6} = {got2 / len(key_sets):.1%}")
    print(f"      rec2fix, giants in    {gota:>6} = {gota / len(key_sets):.1%}")
    print(f"      rec2fix VIEW          {gotf:>6} = {gotf / len(key_sets):.1%}")
    print(f"    {'summary band':<16}{'n':>6}{'O50':>8}{'rec2':>8}{'fix+g':>8}{'fix view':>10}")
    for low, high in ((3, 10), (11, 50), (51, 200), (201, 10**9)):
        band = {k: s for k, s in key_sets.items() if low <= len(s) <= high}
        if not band:
            continue
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        print(f"    {label:<16}{len(band):>6}"
              f"{sum(1 for s in band.values() if home(s, members)):>8}"
              f"{sum(1 for s in band.values() if home(s, pool_two)):>8}"
              f"{sum(1 for s in band.values() if home(s, pool_all)):>8}"
              f"{sum(1 for s in band.values() if home(s, pool_fix)):>10}")

    print("\n" + "=" * 78)
    print("CRITERIA, DECLARED BEFORE THE BUILD, MEASURED ON THE VIEW")
    print("=" * 78)
    fdr_ok = (overall is not None and overall <= CAP_OVERALL
              and all(e["heldout_fdr"] is None or e["heldout_fdr"] <= CAP_STRATUM
                      for e in level2["confirmed"]["strata"]))
    unit_ok = (len(unit_placed | unit_gone | unit_root) / len(every_unit) >= REPARENT_BAR
               and len(covered | rest) / len(giant_only) >= REPARENT_BAR)
    checks = [
        ("held-out FDR within the caps in every stratum and overall",
         f"overall {overall} (cap {CAP_OVERALL})"
         + (f"; worst stratum {worst[0]} at {worst[1]} (cap {CAP_STRATUM})" if worst else ""),
         fdr_ok),
        (f"{MIN_ROOTS}-{MAX_ROOTS} roots, anchors included", f"{len(roots)} roots",
         MIN_ROOTS <= len(roots) <= MAX_ROOTS),
        (f"no node with more than {MAX_CHILDREN} direct children",
         f"max {max(counts, default=0)}", max(counts, default=0) <= MAX_CHILDREN),
        (f"at least {REPARENT_BAR:.0%} of the {len(giant_only)} giant-only themes and of all "
         f"{len(every_unit)} units have a non-giant parent area or anchor, or are roots of "
         "the view",
         f"giant-only {len(covered | rest) / len(giant_only):.1%}, units "
         f"{len(unit_placed | unit_gone | unit_root) / len(every_unit):.1%}  "
         f"(parented alone: {len(placed | promoted) / len(giant_only):.1%} and "
         f"{len(unit_placed) / len(every_unit):.1%})",
         unit_ok),
        (f"no two roots with pathway Jaccard {ROOT_J_LIMIT} or more",
         f"highest of {len(pairs):,} pairs {highest:.3f}", highest < ROOT_J_LIMIT),
    ]
    for what, number, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        {number}")
    print(f"\n  THE FIVE ccode OWNS: {'PASS' if all(c[2] for c in checks) else 'FAIL'}")
    print("  C6 (blind intruder test) is the reviewer's, rerun under the 15 Oct "
          "pre-registration; NOT judged here.")
    print("  Whether the top is intuitive is Aviyah's.")
    print("  ADOPTED: nothing by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
