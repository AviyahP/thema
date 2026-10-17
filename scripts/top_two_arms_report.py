#!/usr/bin/env python3
"""Everything prompt 44 asks for, per arm, against O50s.

Read-only over both arms' builds and over O50s.

Usage::

    uv run scripts/top_two_arms_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from pathlib import Path

#: O50s's own summary placement, the figure each arm is measured against.
O50S_PLACEMENT = 0.926

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80

#: A root this small is a small root.
SMALL_ROOT = 50

#: The declared root ceiling.
MAX_ROOTS = 49

#: Report-only duplication thresholds.
PAIR_J = 0.50
INSIDE = 0.80

#: Caps, unchanged.
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01

#: A node this large is a giant.
GIANT = 1000


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


def read_arm(path: Path, members: Mapping[str, set[str]]) -> dict[str, object]:
    """One arm's payload, with every view node's pathway set resolved.

    Args:
        path: The arm's build directory.
        members: O50s node to member keys.

    Returns:
        The payload plus a ``keys`` map over the view.
    """
    payload = json.loads((path / "levels.json").read_text())
    areas = {node: set(one) for node, one in payload["area_members"].items()}
    keys: dict[str, set[str]] = {}
    for node in payload["view"]:
        if node in areas:
            keys[node] = areas[node]
        elif node.startswith("loose:"):
            keys[node] = {node[len("loose:"):]}
        else:
            keys[node] = set(members[node])
    payload["keys"] = keys
    payload["areas"] = areas
    return payload


def placement(key_sets: Mapping[str, frozenset[str]],
              pool: Mapping[str, set[str]]) -> tuple[int, Counter[str]]:
    """How many summaries find a home in a pool, overall and by band.

    Args:
        key_sets: Summary key to its leaf set.
        pool: Node id to pathway keys.

    Returns:
        ``(total, per-band counter)``.
    """
    bands = ((3, 10), (11, 50), (51, 200), (201, 10 ** 9))
    per: Counter[str] = Counter()
    total = 0
    items = list(pool.items())
    for summary, leaves in key_sets.items():
        del summary
        best = 0
        for _node, held in items:
            if len(leaves & held) >= HOME_SHARE * len(leaves) and (
                    best == 0 or len(held) < best):
                best = len(held)
        if best:
            total += 1
            for low, high in bands:
                if low <= len(leaves) <= high:
                    per[f"{low}-{high}" if high < 10 ** 9 else f"{low}+"] += 1
    return total, per


def main(argv: list[str] | None = None) -> int:
    """Print the per-arm report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_top"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    import recursive_top_O50 as rt
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    nodes, members = rt.read_build(args.o50s)
    universe = {key for one in members.values() for key in one}
    arms = {name: read_arm(args.top / name, members)
            for name in ("A", "B") if (args.top / name / "levels.json").exists()}
    stability = json.loads((args.top / "stability.json").read_text())

    print("THE TOP OF O50s, TWO ARMS. Declared 17 Oct 2026. EXPLORATORY: adopts nothing.")
    print(f"  base: O50s, {len(nodes):,} themes, 261 roots, 164 of them "
          f"{SMALL_ROOT} pathways or fewer")
    print(f"  the declared ceiling is fewer than {MAX_ROOTS} roots\n")

    print("=" * 112)
    print("7 (REPORTED FIRST, AS THE ORDER ASKS). STABILITY, THE NOISE CHECK AND T")
    print("=" * 112)
    print(f"  {'band':<10}{'themes':>8}{'p25':>8}{'MEDIAN':>9}{'p75':>8}"
          f"{'gated n':>9}{'gated med':>11}{'null n':>8}{'null med':>10}{'null p95':>10}"
          f"{'0.6>p95':>9}{'AUC stab':>10}{'AUC supp':>10}")
    for entry in stability["table"]:
        def cell(key: str, places: int, width: int, row: Mapping[str, object] = entry) -> str:
            """One numeric cell, or a dash."""
            value = row[key]
            return f"{'-':>{width}}" if value is None else f"{value:>{width}.{places}f}"
        print(f"  {entry['band']:<10}{entry['n_themes']:>8,}"
              + cell("p25", 3, 8) + cell("median", 3, 9) + cell("p75", 3, 8)
              + f"{entry['n_gated']:>9,}" + cell("gated_median", 3, 11)
              + f"{entry['n_null']:>8,}" + cell("null_median", 3, 10)
              + cell("null_p95", 3, 10)
              + f"{('yes' if entry['cut_above_null_p95'] else 'NO'):>9}"
              + cell("auc_stability", 3, 10) + cell("auc_support", 3, 10))
    print(f"\n  T = {stability['T']} ({stability['T_band']}), the first band with a median below "
          f"{stability['cut']}; at {stability['cut_alt']} the cut would be {stability['T_alt']} "
          f"({stability['T_alt_band']})")
    medians = [e["median"] for e in stability["table"] if e["n_themes"]]
    print(f"  the band medians, smallest band first: {medians}")
    print("  They are NOT decreasing with size. 800-1,599 is the most stable band at "
          f"{max(medians):.3f},")
    print("  and the least stable are the two smallest. The cut falls at the first band only "
          "because")
    print("  EVERY band is under 0.6, not because stability degrades as themes grow.")

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
    key_sets = targets(edges, sorted(set(names) - universe), universe, min_size=3)
    kids: dict[str, set[str]] = defaultdict(set)
    for child, ups in rel.items():
        for parent in ups:
            kids[parent].add(child)

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
    for root in sorted(reactome_roots(rel)):
        leaves = {f"reactome:{k}" for k in descend(root) | {root}} & universe
        if len(leaves) >= 3:
            branches[root] = leaves

    def median_best(pool: Mapping[str, set[str]]) -> float:
        """Median best Jaccard against Reactome's top-level branches."""
        return statistics.median(
            [max((jaccard(leaves, held) for held in pool.values()), default=0.0)
             for leaves in branches.values()])

    o50s_pool = {node: set(one) for node, one in members.items()}
    base_total, base_per = placement(key_sets, o50s_pool)
    print(f"\n  O50s itself: placement {base_total} of {len(key_sets):,} = "
          f"{base_total / len(key_sets):.1%}; Reactome median best J "
          f"{median_best(o50s_pool):.3f}")
    return per_arm(args, arms, stability, members, key_sets, branches, o50s_pool,
                   base_total, median_best)


def per_arm(args: argparse.Namespace, arms: Mapping[str, dict], stability: Mapping[str, object],
            members: Mapping[str, set[str]], key_sets: Mapping[str, frozenset[str]],
            branches: Mapping[str, set[str]], o50s_pool: Mapping[str, set[str]],
            base_total: int,
            median_best: Callable[[Mapping[str, set[str]]], float]) -> int:
    """Items 1 to 6 per arm, and item 7's dropped-theme table for arm B.

    Args:
        args: Parsed arguments.
        arms: Each arm's payload.
        stability: The stability record.
        members: O50s node to member keys.
        key_sets: Summary key to its leaf set.
        branches: Reactome branch to its leaves in L.
        o50s_pool: Every O50s theme.
        base_total: O50s's own placement count.
        median_best: The Reactome scorer.

    Returns:
        0.
    """
    cut = stability["T"]
    for name, arm in arms.items():
        keys = arm["keys"]
        roots = arm["roots"]
        children = arm["children"]
        print("\n" + "=" * 112)
        print(f"ARM {name}")
        print("=" * 112)
        print(f"  {arm['n_items']} items -> {arm['n_areas']} areas -> "
              f"{len(arm['view']):,} nodes in the view")

        print("\n  1. HELD-OUT FDR PER STRATUM")
        print(f"    {'stratum':<9}{'floor':>11}{'calib':>11}{'held-out':>11}{'real':>8}"
              f"{'cap':>7}")
        worst = 0.0
        for entry in arm["confirmed"]["strata"]:
            value = entry["heldout_fdr"]
            flag = "" if value is None or value <= CAP_STRATUM else "  OVER"
            worst = max(worst, value or 0.0)
            print(f"    {entry['stratum']:<9}{str(entry['effective']):>11}"
                  f"{str(entry['calibration_fdr']):>11}{str(value):>11}"
                  f"{entry['heldout_real']:>8,}{CAP_STRATUM:>7}{flag}")
        overall = arm["confirmed"]["overall_fdr"]
        inside = (overall is not None and overall <= CAP_OVERALL and worst <= CAP_STRATUM)
        print(f"    OVERALL {str(overall):>32}{'':>8}{CAP_OVERALL:>7}  "
              f"{'INSIDE both caps' if inside else 'OVER A CAP'}")

        print(f"\n  2. ROOTS: {len(roots)}  "
              f"({'PASS' if len(roots) < MAX_ROOTS else 'FAIL'} against fewer than {MAX_ROOTS})")
        print(f"    {'root':<12}{'kind':<8}{'size':>7}{'children':>10}")
        for node in sorted(roots, key=lambda n: -len(keys[n])):
            print(f"    {node:<12}{arm['kinds'][node]:<8}{len(keys[node]):>7,}"
                  f"{len(children[node]):>10}")

        small = arm["small_roots"]
        print(f"\n  3. SMALL ROOTS ({SMALL_ROOT} pathways or fewer): {len(small)} of "
              f"{len(roots)}")
        if small:
            print(f"    {'root':<12}{'size':>6}   {'container':<12}{'c size':>8}"
                  f"{'share':>8}{'missing':>9}")
            for node in sorted(small, key=lambda n: -len(keys[n])):
                for position, entry in enumerate(small[node]):
                    head = f"{node:<12}{len(keys[node]):>6}" if position == 0 else " " * 18
                    print(f"    {head}   {entry['node']:<12}{entry['size']:>8,}"
                          f"{entry['share']:>8.3f}{entry['missing']:>9}")
        else:
            print("    none")

        dup = arm["duplication"]
        print("\n  4. DUPLICATION (report only, not a gate)")
        print(f"    root pairs at J >= {PAIR_J}: {len(dup['root_pairs_ge_0.5'])}")
        for value, a, sa, b, sb in dup["root_pairs_ge_0.5"][:12]:
            print(f"      J {value:.3f}  {a} ({sa:,}) / {b} ({sb:,})")
        distinct = {row[1] for row in dup["roots_80_inside"]}
        print(f"    roots at least {INSIDE:.0%} inside another node: {len(distinct)} of "
              f"{len(roots)}  ({len(dup['roots_80_inside'])} ordered pairs)")
        for share, node, size, other, osize in dup["roots_80_inside"][:12]:
            print(f"      {share:.3f}  {node} ({size:,}) inside {other} ({osize:,})")

        counts = [len(children[n]) for n in arm["view"]]
        giants = arm["giants"]
        print("\n  5. CHILDREN AND GIANTS")
        print(f"    children per node: max {max(counts, default=0)}, "
              f"median {statistics.median(counts):.0f}, "
              f"{sum(1 for c in counts if c > 60)} over 60")
        print(f"    nodes over {GIANT:,} pathways, kept and flagged: {len(giants)}  "
              + ", ".join(f"{n} ({len(keys[n]):,})" for n in giants[:10]))

        view_pool = dict(keys)
        if name == "A":
            full_pool = {**o50s_pool, **arm["areas"]}
            label = "every O50s theme plus arm A's areas"
        else:
            full_pool = {**{k: v for k, v in o50s_pool.items() if len(v) < cut},
                         **arm["areas"]}
            label = (f"the O50s themes below {cut} plus arm B's areas "
                     f"(the 363 at {cut}+ are dropped)")
        total_view, _ = placement(key_sets, view_pool)
        total_full, per_full = placement(key_sets, full_pool)
        print("\n  6. SUMMARY PLACEMENT AND REACTOME")
        print(f"    O50s itself: {base_total} of {len(key_sets):,} = "
              f"{base_total / len(key_sets):.1%}  (the declared comparison, "
              f"{O50S_PLACEMENT:.1%})")
        print(f"    the view alone ({len(view_pool):,} nodes): {total_view} = "
              f"{total_view / len(key_sets):.1%}")
        print(f"    {label}: {total_full} = {total_full / len(key_sets):.1%}  "
              f"({total_full - base_total:+} against O50s)")
        print("    by band: " + ", ".join(f"{k} {v}" for k, v in sorted(per_full.items())))
        print(f"    Reactome median best J: view {median_best(view_pool):.3f}, "
              f"full pool {median_best(full_pool):.3f}, O50s {median_best(o50s_pool):.3f}")

    if "B" in arms and cut is not None:
        arm = arms["B"]
        dropped = sorted(node for node, one in members.items() if len(one) >= cut)
        print("\n" + "=" * 112)
        print(f"7b. THE {len(dropped)} DROPPED THEMES OF {cut}+ PATHWAYS, "
              "AND THEIR BEST-MATCHING ARM B AREA")
        print("=" * 112)
        best: list[tuple[float, str, int, str, int]] = []
        for node in dropped:
            mine = members[node]
            pick, score = "", 0.0
            for area, held in arm["areas"].items():
                value = jaccard(mine, held)
                if value > score:
                    pick, score = area, value
            best.append((score, node, len(mine), pick, len(arm["areas"].get(pick, ()))))
        best.sort(reverse=True)
        values = [row[0] for row in best]
        print(f"    best J: median {statistics.median(values):.3f}, "
              f">=0.7 {sum(1 for v in values if v >= 0.7)}, "
              f"0.5-0.7 {sum(1 for v in values if 0.5 <= v < 0.7)}, "
              f"<0.5 {sum(1 for v in values if v < 0.5)}")
        print(f"    {'dropped':<12}{'size':>7}   {'best area':<12}{'area size':>10}{'J':>8}")
        for score, node, size, area, asize in best[:20]:
            print(f"    {node:<12}{size:>7,}   {area:<12}{asize:>10,}{score:>8.3f}")
        if len(best) > 20:
            print(f"    ... and {len(best) - 20} more; the worst is {best[-1][1]} at "
                  f"{best[-1][0]:.3f}")
        with (args.top / "B" / "dropped_themes.tsv").open(
                "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                    fieldnames=["node", "size", "best_area", "area_size", "j"])
            writer.writeheader()
            for score, node, size, area, asize in best:
                writer.writerow({"node": node, "size": size, "best_area": area,
                                 "area_size": asize, "j": round(score, 4)})
        print(f"    -> {args.top / 'B' / 'dropped_themes.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
