#!/usr/bin/env python3
"""Every figure prompt 38 asks for: each arm against O50 and against rec2fix with its giants in.

Reads the builds and prints nothing it did not measure. The rec2fix build is read only, never
written.

Usage::

    uv run scripts/areas_rec3_report.py
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

GIANT = 1000
HOME_SHARE = 0.80

#: The declared criteria for arm W.
MIN_ROOTS = 20
MAX_ROOTS = 60
MAX_CHILDREN = 60
O50_PLACEMENT = 0.853
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01
REPORT_J = 0.30
BANDS = ((1, 10), (11, 50), (51, 200), (201, 1000), (1001, 10 ** 9))


def band_of(size: int) -> str:
    """The band label a size falls in.

    Args:
        size: Member count.

    Returns:
        The band label, or ``"none"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
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


def home(leaf_set: frozenset[str], pool: Mapping[str, set[str]]) -> str:
    """The smallest node holding :data:`HOME_SHARE` of a summary's leaves, if any.

    Args:
        leaf_set: The summary's leaves in L.
        pool: Node id to pathway keys.

    Returns:
        The node id, or the empty string.
    """
    best, size = "", 0
    for node_id, keys in pool.items():
        if len(leaf_set & keys) >= HOME_SHARE * len(leaf_set):
            if not best or len(keys) < size:
                best, size = node_id, len(keys)
    return best


def arm_pool(path: Path, members: Mapping[str, set[str]]) -> dict[str, object]:
    """One arm's final structure, with every node's pathway set.

    Args:
        path: The arm's directory.
        members: O50 node to member keys.

    Returns:
        The arm's payload, node sets, alive list, roots and children.
    """
    payload = json.loads((path / "levels.json").read_text())
    held = {node: set(one) for node, one in members.items()}
    held.update({node: set(keys) for node, keys in payload["area_members"].items()})
    alive = payload["final"]["alive"]
    return {
        "arm": payload["arm"], "payload": payload, "held": held, "alive": alive,
        "pool": {node: held[node] for node in alive},
        "roots": payload["final"]["roots"],
        "children": payload["final"]["children"],
        "parents": payload["final"]["parents"],
        "kind": payload["kind"], "level_of": payload["level_of"],
        "area_items": payload["area_items"], "levels": payload["levels"],
    }


def main(argv: list[str] | None = None) -> int:
    """Print the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--build", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec3"))
    parser.add_argument("--rec2fix", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    import recursive_top_O50 as rt

    nodes, members = rt.read_build(args.frozen)
    allk = {key for one in members.values() for key in one}
    o50_giants = {node for node in members if len(members[node]) > GIANT}
    arms = {name: arm_pool(args.build / name, members)
            for name in ("W", "E") if (args.build / name / "levels.json").exists()}
    if not arms:
        raise SystemExit("no arm is built")

    fix = json.loads((args.rec2fix / "levels.json").read_text())
    fix_areas = {node: set(keys) for node, keys
                 in zip(fix["level2"]["node_ids"], fix["level2"]["pathway_members"], strict=True)}
    # rec2fix WITH ITS GIANTS IN, and against the same node set shape as rec3: every O50 node,
    # giants included, plus all 343 of its areas. That is the comparison the prompt asks for.
    pool_fix = {**{n: set(v) for n, v in members.items()}, **fix_areas}
    pool_o50 = {n: set(v) for n, v in members.items()}

    print("AREAS AS ONE OPERATOR (rec3). Declared 16 Oct 2026 before any result.")
    print("Arm W is size-weighted and primary; arm E is equal weight and an ablation only.\n")

    print("=" * 78)
    print("LEVEL 0: THE FROZEN O50, AS IS")
    print("=" * 78)
    print(f"  {len(nodes):,} nodes, {len(o50_giants)} giants "
          f"{sorted((n, len(members[n])) for n in o50_giants)}")
    print(f"  {len(allk):,} pathways; the structure reproduces O50's own 7,525 edges exactly "
          f"(tests/test_areas_rec3.py)")

    for name, arm in arms.items():
        print("\n" + "=" * 78)
        print(f"ARM {name}: PER LEVEL")
        print("=" * 78)
        for entry in arm["levels"]:
            print(f"  LEVEL {entry['level']}: {entry['n_items']} items, "
                  f"sizes {triple(entry['item_sizes'])}, "
                  f"double counting {entry['double_counting']:.2f}x")
            print(f"    candidates {entry['n_candidates']:,} -> gate {entry['n_gated']:,} -> "
                  f"consensus {entry['n_after_consensus']:,} -> {entry['n_areas']} areas "
                  f"({entry['seconds']:.0f}s)")
            if entry["n_areas"]:
                bands = Counter(band_of(s) for s in entry["area_sizes"])
                print("    areas by size band: " + ", ".join(
                    f"{band_of(low if high < 10 ** 9 else low)}={bands.get(band_of(low), 0)}"
                    for low, high in BANDS))
                print(f"    area sizes {triple(entry['area_sizes'])} pathways; "
                      f"{entry['repair']['n_collapsed']} collapsed, "
                      f"{entry['repair']['n_merged']} merged inside T")
                print(f"    structure after this level: {entry.get('n_nodes', 0):,} nodes, "
                      f"{entry.get('n_roots', 0)} roots, "
                      f"{entry.get('n_direct_edges', 0):,} direct edges, "
                      f"children max {entry.get('children_max', 0)}")
            print("    held-out FDR per stratum, with the real-candidate count")
            print(f"      {'stratum':<9}{'floor':>10}{'calib':>10}{'held-out':>10}{'real':>7}"
                  f"{'cap':>7}")
            for stratum in entry["confirmed"]["strata"]:
                value = stratum["heldout_fdr"]
                flag = "" if value is None or value <= CAP_STRATUM else "  OVER"
                print(f"      {stratum['stratum']:<9}{str(stratum['effective']):>10}"
                      f"{str(stratum['calibration_fdr']):>10}{str(value):>10}"
                      f"{stratum['heldout_real']:>7}{CAP_STRATUM:>7}{flag}")
            overall = entry["confirmed"]["overall_fdr"]
            print(f"      OVERALL {str(overall):>31}{'':>14}{CAP_OVERALL:>7}"
                  f"{'  OVER' if overall is not None and overall > CAP_OVERALL else ''}")
        print(f"  stopped because {arm['payload']['stopped_because']}")

    for name, arm in arms.items():
        held, alive = arm["held"], arm["alive"]
        roots, children = arm["roots"], arm["children"]
        counts = [len(children[n]) for n in alive]
        print("\n" + "=" * 78)
        print(f"ARM {name}: THE STRUCTURE")
        print("=" * 78)
        kinds = Counter(arm["kind"][n] for n in alive)
        print(f"  {len(alive):,} nodes ({kinds['o50']} O50, {kinds['area']} areas); "
              f"{arm['payload']['final']['n_direct_edges']:,} direct edges, "
              f"{arm['payload']['final']['n_closure_pairs']:,} containment pairs")
        print(f"  ROOTS: {len(roots)}  "
              f"({Counter(arm['kind'][r] for r in roots)['area']} areas, "
              f"{Counter(arm['kind'][r] for r in roots)['o50']} O50 nodes)")
        over = sum(1 for c in counts if c > MAX_CHILDREN)
        print(f"  direct children per node: max {max(counts, default=0)}, "
              f"median {statistics.median(counts):.0f}, {over} over {MAX_CHILDREN}")
        print(f"  root sizes {triple([len(held[r]) for r in roots])} pathways")
        print(f"  the rules over the whole set: {len(arm['payload']['final']['collapsed'])} "
              f"collapsed, {len(arm['payload']['final']['merged'])} merged")
        for event in arm["payload"]["final"]["events"][:20]:
            print(f"    {event['rule']:<9} {event['victim']:<13}({event['victim_size']:>5}) "
                  f"into {event['keeper']:<13}({event['keeper_size']:>5})")
        print("\n  every root, largest first")
        print(f"  {'root':<14}{'kind':<7}{'level':>6}{'pathways':>10}{'items':>7}"
              f"{'children':>10}")
        counted = arm["payload"]["items_count"]
        shown = sorted(roots, key=lambda n: -len(held[n]))
        for node in shown[:80]:
            print(f"  {node:<14}{arm['kind'][node]:<7}{arm['level_of'][node]:>6}"
                  f"{len(held[node]):>10}{counted.get(node, 1):>7}{len(children[node]):>10}")
        if len(shown) > 80:
            print(f"  ... and {len(shown) - 80} more roots, all in nodes.tsv")

        big = sorted((n for n in alive if len(held[n]) > GIANT), key=lambda n: -len(held[n]))
        print(f"\n  nodes over {GIANT:,} pathways: {len(big)} "
              f"({sum(1 for n in big if arm['kind'][n] == 'area')} of them NEW areas)")
        print(f"  {'node':<14}{'kind':<7}{'level':>6}{'pathways':>10}{'share':>8}{'items':>7}")
        for node in big:
            print(f"  {node:<14}{arm['kind'][node]:<7}{arm['level_of'][node]:>6}"
                  f"{len(held[node]):>10}{len(held[node]) / len(allk):>7.1%}"
                  f"{counted.get(node, 1):>7}")

        print("\n  how many areas each item over 200 pathways joins")
        joins: dict[str, list[str]] = defaultdict(list)
        for area, items in arm["area_items"].items():
            if area not in set(alive):
                continue
            for item in items:
                joins[item].append(area)
        wide = sorted((i for i in joins if len(held.get(i.removeprefix('loose:'), ())) > 200),
                      key=lambda i: -len(held[i]))
        for item in wide:
            print(f"    {item:<14}{len(held[item]):>5} pathways joins {len(joins[item])} area(s): "
                  f"{' '.join(sorted(joins[item]))}")
        every = [len(v) for v in joins.values()]
        if not every:
            print("    no item joined any area: this arm built none")
        else:
            print(f"    over all {len(joins)} items that joined anything: "
                  f"median {statistics.median(every):.0f}, max {max(every, default=0)}")

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
    pools = {"O50": pool_o50, "rec2fix+g": pool_fix}
    pools.update({name: arm["pool"] for name, arm in arms.items()})
    print(f"  curated summaries with 3+ leaf descendants in L: {len(key_sets):,}")
    print(f"    with a node holding {HOME_SHARE:.0%} of their leaves:")
    totals = {}
    for label, pool in pools.items():
        got = sum(1 for s in key_sets.values() if home(s, pool))
        totals[label] = got
        print(f"      {label:<12}{got:>6} = {got / len(key_sets):.1%}")
    print(f"    {'summary band':<16}{'n':>6}" + "".join(f"{label:>11}" for label in pools))
    for low, high in ((3, 10), (11, 50), (51, 200), (201, 10 ** 9)):
        band = {k: s for k, s in key_sets.items() if low <= len(s) <= high}
        if not band:
            continue
        label = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
        print(f"    {label:<16}{len(band):>6}" + "".join(
            f"{sum(1 for s in band.values() if home(s, pool)):>11}" for pool in pools.values()))

    print("\n" + "=" * 78)
    print("AGREEMENT WITH REACTOME TOP-LEVEL PATHWAYS (best Jaccard)")
    print("=" * 78)
    kids: dict[str, set[str]] = defaultdict(set)
    for child, ups in rel.items():
        for parent in ups:
            kids[parent].add(child)
    # read_reactome_relation keys EVERY node, roots carrying an empty parent list, so the roots are
    # the nodes nothing claims as a child, which is what reactome_roots returns.
    from thema.data.hierarchy import reactome_roots
    tops = sorted(reactome_roots(rel))

    def descend(root: str) -> set[str]:
        """Every Reactome pathway under a top-level branch."""
        seen, stack = set(), [root]
        while stack:
            node = stack.pop()
            for kid in kids.get(node, ()):
                if kid not in seen:
                    seen.add(kid)
                    stack.append(kid)
        return seen

    branches = {}
    for root in tops:
        leaves = {f"reactome:{k}" for k in descend(root) | {root}} & allk
        if len(leaves) >= 3:
            branches[root] = leaves
    print(f"  {len(tops)} Reactome top-level pathways, {len(branches)} with 3+ leaves in L")
    print(f"  {'reactome top':<44}{'leaves':>7}"
          + "".join(f"  {label:<15}{'J':>7}" for label in pools))
    medians: dict[str, list[float]] = {label: [] for label in pools}
    for root, leaves in sorted(branches.items(), key=lambda kv: -len(kv[1])):
        cells = []
        for label, pool in pools.items():
            best, score = "", 0.0
            for node_id, keys in pool.items():
                value = jaccard(leaves, keys)
                if value > score:
                    best, score = node_id, value
            medians[label].append(score)
            cells.append(f"  {best[:14]:<15}{score:>7.3f}")
        print(f"  {names.get(f'reactome:{root}', root)[:42]:<44}{len(leaves):>7}"
              + "".join(cells))
    print(f"  {'MEDIAN best Jaccard':<44}{'':>7}"
          + "".join(f"  {'':<15}{statistics.median(v):>7.3f}" for v in medians.values()))

    for name, arm in arms.items():
        held, roots = arm["held"], arm["roots"]
        root_keys = {r: held[r] for r in roots}
        print("\n" + "=" * 78)
        print(f"ARM {name}: ROOT PAIRS AT PATHWAY JACCARD {REPORT_J} OR MORE")
        print("=" * 78)
        pairs = list(itertools.combinations(sorted(root_keys.items()), 2))
        over = sorted(((jaccard(ka, kb), a, b, len(ka), len(kb), len(ka & kb))
                       for (a, ka), (b, kb) in pairs if jaccard(ka, kb) >= REPORT_J),
                      reverse=True)
        highest = max((jaccard(ka, kb) for (_, ka), (_, kb) in pairs), default=0.0)
        print(f"  {len(over)} of {len(pairs):,} pairs; the highest is {highest:.3f}")
        for value, a, b, sa, sb, shared in over[:60]:
            print(f"    J {value:.3f}  {a} ({sa}) / {b} ({sb}), sharing {shared}"
                  f"{'   OVER 0.50' if value >= 0.50 else ''}")
        per: Counter[str] = Counter()
        for keys in root_keys.values():
            for key in keys:
                per[key] += 1
        print(f"  pathways in no root: {len(allk) - len(per):,}; roots per pathway median "
              f"{statistics.median(list(per.values())) if per else 0:.0f}, "
              f"max {max(per.values(), default=0)}")

    print("\n" + "=" * 78)
    print("W AGAINST E")
    print("=" * 78)
    if len(arms) == 2:
        w, e = arms["W"], arms["E"]
        rowspec: list[tuple[str, object, object]] = [
            ("levels run", len(w["levels"]), len(e["levels"])),
            ("level 1 candidates", f"{w['levels'][0]['n_candidates']:,}",
             f"{e['levels'][0]['n_candidates']:,}"),
            ("level 1 through the gate", f"{w['levels'][0]['n_gated']:,}",
             f"{e['levels'][0]['n_gated']:,}"),
            ("level 1 areas", w["levels"][0]["n_areas"], e["levels"][0]["n_areas"]),
            ("level 1 area sizes", triple(w["levels"][0]["area_sizes"]),
             triple(e["levels"][0]["area_sizes"])),
            ("nodes in the structure", f"{len(w['alive']):,}", f"{len(e['alive']):,}"),
            ("ROOTS", len(w["roots"]), len(e["roots"])),
            ("root sizes", triple([len(w["held"][r]) for r in w["roots"]]),
             triple([len(e["held"][r]) for r in e["roots"]])),
            ("children max", max((len(w["children"][n]) for n in w["alive"]), default=0),
             max((len(e["children"][n]) for n in e["alive"]), default=0)),
            ("children median",
             f"{statistics.median([len(w['children'][n]) for n in w['alive']]):.0f}",
             f"{statistics.median([len(e['children'][n]) for n in e['alive']]):.0f}"),
            ("new areas over 1,000",
             sum(1 for n in w["alive"] if w["kind"][n] == "area" and len(w["held"][n]) > GIANT),
             sum(1 for n in e["alive"] if e["kind"][n] == "area" and len(e["held"][n]) > GIANT)),
            ("summary placement", f"{totals['W'] / len(key_sets):.1%}",
             f"{totals['E'] / len(key_sets):.1%}"),
            ("Reactome median best J", f"{statistics.median(medians['W']):.3f}",
             f"{statistics.median(medians['E']):.3f}"),
            ("rules over the set, collapsed", len(w["payload"]["final"]["collapsed"]),
             len(e["payload"]["final"]["collapsed"])),
            ("rules over the set, merged", len(w["payload"]["final"]["merged"]),
             len(e["payload"]["final"]["merged"])),
            ("seconds", w["payload"]["seconds"], e["payload"]["seconds"]),
            ("stopped because",
             "nothing under the floors" if not w["levels"][-1]["n_areas"]
             else f"{len(w['roots'])} roots reached",
             "nothing under the floors" if not e["levels"][-1]["n_areas"]
             else f"{len(e['roots'])} roots reached"),
        ]
        print(f"  {'':<30}{'W (size-weighted)':>26}{'E (equal)':>26}")
        for label, a, b in rowspec:
            print(f"  {label:<30}{str(a):>26}{str(b):>26}")
        same = sum(1 for node, keys in w["payload"]["area_members"].items()
                   if any(set(keys) == set(other)
                          for other in e["payload"]["area_members"].values()))
        print(f"\n  areas identical between the arms: {same} of "
              f"{len(w['payload']['area_members'])} W areas and "
              f"{len(e['payload']['area_members'])} E areas")
    else:
        print("  only one arm is built")

    print("\n" + "=" * 78)
    print("CRITERIA FOR ARM W, DECLARED BEFORE THE BUILD")
    print("=" * 78)
    w = arms.get("W")
    if w is None:
        print("  arm W is not built")
        return 0
    counts = [len(w["children"][n]) for n in w["alive"]]
    # A level that admitted nothing has no FDR to be inside the caps. Reporting that as a pass
    # would be the one way to make an empty build look like it met a criterion, so an empty level
    # fails this criterion and says why: no floor exists at any cut, which is the opposite of a
    # calibrated one. See null_diagnostic.txt in the build folder.
    admitted = sum(entry["n_areas"] for entry in w["levels"])
    solved = all(any(f["effective"] is not None for f in entry["floors"])
                 for entry in w["levels"])
    fdr_ok = bool(admitted) and solved and all(
        (entry["confirmed"]["overall_fdr"] is None
         or entry["confirmed"]["overall_fdr"] <= CAP_OVERALL)
        and all(s["heldout_fdr"] is None or s["heldout_fdr"] <= CAP_STRATUM
                for s in entry["confirmed"]["strata"])
        for entry in w["levels"])
    worst = max((s["heldout_fdr"] for entry in w["levels"]
                 for s in entry["confirmed"]["strata"] if s["heldout_fdr"] is not None),
                default=0.0)
    placement = totals["W"] / len(key_sets)
    # The bar is O50's own placement, measured here the same way, not the rounded figure.
    bar = totals["O50"] / len(key_sets)
    new_big = [n for n in w["alive"]
               if w["kind"][n] == "area" and len(w["held"][n]) > GIANT]
    checks = [
        ("held-out FDR within the caps at every level",
         (f"worst stratum {worst}, every overall "
          f"{[e['confirmed']['overall_fdr'] for e in w['levels']]}") if admitted else
         ("no floor exists at any cut in any stratum, so nothing was admitted and there is no "
          "FDR to be inside the caps: see null_diagnostic.txt"), fdr_ok),
        (f"{MIN_ROOTS}-{MAX_ROOTS} roots, giants included", f"{len(w['roots'])} roots",
         MIN_ROOTS <= len(w["roots"]) <= MAX_ROOTS),
        (f"no node with more than {MAX_CHILDREN} direct children",
         f"max {max(counts, default=0)}", max(counts, default=0) <= MAX_CHILDREN),
        (f"summary placement at least O50's own {bar:.1%}",
         f"{placement:.1%}" + ("  (tied, because arm W built nothing: the pool IS O50)"
                               if not admitted else ""),
         placement >= bar - 1e-9),
    ]
    for what, number, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        {number}")
    print(f"\n  THE FOUR ccode OWNS: {'PASS' if all(c[2] for c in checks) else 'FAIL'}")
    print(f"  Reviewer checks: C6 intruder test at 70% or more, and the 15 Oct giant reading plus "
          f"intruder test on each of the {len(new_big)} new node(s) over {GIANT:,} pathways "
          f"{sorted(new_big)}. NOT judged here.")
    print("  Whether the top is intuitive is Aviyah's.")
    print("  ADOPTED: nothing by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
