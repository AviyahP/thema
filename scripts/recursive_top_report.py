#!/usr/bin/env python3
"""Measure the recursive top level against the declaration. Read-only; adopts nothing.

Every figure the declaration of 15 Oct 2026 asks for, and the five criteria ccode owns. C6 is the
reviewer's blind intruder test and is not judged here; so is whether Aviyah finds the top intuitive.

Usage::

    uv run scripts/recursive_top_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

GIANT = 1000

#: Bands the declaration states the "largest non-giant ancestor" distribution over.
BANDS: tuple[tuple[int, int], ...] = (
    (1, 10), (11, 50), (51, 200), (201, 1000), (1001, 10**9))

#: The share of a summary's leaves a node must hold to count as its home.
HOME_SHARE = 0.80

#: The floors' held-out caps, which this configuration inherits from v0.4.
CAP_OVERALL = 0.01
CAP_STRATUM = 0.02

#: Criteria the declaration fixes.
MAX_CHILDREN = 60
MIN_ROOTS, MAX_ROOTS = 20, 60
REPARENT_BAR = 0.95


def band_of(size: int) -> str:
    """Band label for a size."""
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10**9 else f"{low}+"
    return "other"


def read_build(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
    """Node rows and member sets."""
    with (path / "nodes.tsv").open(encoding="utf-8") as handle:
        nodes = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return nodes, dict(members)


def largest_nongiant_ancestor(
    members: Mapping[str, set[str]],
    parents: Mapping[str, set[str]],
    giants: set[str],
) -> dict[str, int]:
    """For each pathway, the size of the largest non-giant theme containing it.

    Containment, not ancestry through edges: a theme that holds the pathway is above it whether or
    not the DAG draws a direct edge.

    Args:
        members: Node to members.
        parents: Node to parents, unused but kept for signature parity with the caller.
        giants: Themes to ignore.

    Returns:
        Pathway key to the largest non-giant holder's size, 0 if there is none.
    """
    del parents
    best: dict[str, int] = {}
    for node, keys in members.items():
        if node in giants:
            continue
        size = len(keys)
        for key in keys:
            if size > best.get(key, 0):
                best[key] = size
    return best


def coherence(
    member_keys: Sequence[str], genes: Mapping[str, frozenset[str]]
) -> float | None:
    """Mean pairwise Jaccard of the members' gene sets.

    Args:
        member_keys: The members.
        genes: Pathway key to its genes.

    Returns:
        The mean, or None when fewer than two members carry genes.
    """
    sets = [genes[key] for key in member_keys if genes.get(key)]
    if len(sets) < 2:
        return None
    total = 0.0
    pairs = 0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = len(sets[i] | sets[j])
            if union:
                total += len(sets[i] & sets[j]) / union
                pairs += 1
    return total / pairs if pairs else None


def main(argv: list[str] | None = None) -> int:
    """Print the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--rec", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec"))
    parser.add_argument("--space", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    nodes, members = read_build(args.frozen)
    levels = json.loads((args.rec / "levels.json").read_text())
    manifest = json.loads((args.rec / "manifest.json").read_text())
    giants = set(levels["giants"])
    giant_only = set(levels["giant_only"])
    unit_ids = levels["unit_ids"]
    o50_parents = {node: set(row["parents"].split()) for node, row in nodes.items()}

    print("RECURSIVE TOP LEVEL on O50. Declared 15 Oct 2026 before any result. ADOPTS NOTHING.\n")
    print("=" * 78)
    print("PER LEVEL")
    print("=" * 78)
    for entry in levels["levels"]:
        ids = entry["node_ids"]
        kids: dict[int, int] = Counter()
        for above in entry["parents"]:
            for parent in above:
                kids[parent] += 1
        counts = [kids.get(i, 0) for i in range(len(ids))]
        # In the combined DAG an area's children are its child areas PLUS the units it holds and
        # does not reach through a child area. That is what a reader clicking the area would see,
        # and it is the number the declaration's 60-child limit is about.
        held_by_kids = [
            {u for j, above in enumerate(entry["parents"]) if i in above
             for u in entry["child_unit_ids"][j]}
            for i in range(len(ids))
        ]
        combined_counts = [
            kids.get(i, 0) + len(set(entry["child_unit_ids"][i]) - held_by_kids[i])
            for i in range(len(ids))
        ]
        multi = sum(1 for above in entry["parents"] if len(above) >= 2)
        unit_sizes = sorted(len(r) for r in entry["child_unit_ids"])
        path_sizes = sorted(len(r) for r in entry["pathway_members"])
        print(f"\n  LEVEL {entry['level']}: {entry['n_units_in']} units in -> "
              f"{len(ids)} nodes, {len(entry['roots'])} roots")
        print(f"    candidates {entry['n_candidates']:,}; after consensus "
              f"{entry['n_after_consensus']}; after the joint fixed point {len(ids)}")
        print(f"    repair: {entry['repair']['n_collapsed']} collapsed, "
              f"{entry['repair']['n_merged']} merged, rounds {entry['repair']['rounds']}")
        print(f"    size in UNITS:     min {unit_sizes[0]}, median "
              f"{unit_sizes[len(unit_sizes) // 2]}, max {unit_sizes[-1]}")
        print(f"    size in PATHWAYS:  min {path_sizes[0]}, median "
              f"{path_sizes[len(path_sizes) // 2]}, max {path_sizes[-1]}")
        print(f"    multi-parent: {multi} of {len(ids)} = {multi / len(ids):.1%}")
        print(f"    children per node, areas only:  max {max(counts)}, median "
              f"{statistics.median(counts):.0f}")
        print(f"    children per node, COMBINED:    max {max(combined_counts)}, median "
              f"{statistics.median(combined_counts):.0f}  "
              f"({sum(1 for c in combined_counts if c > MAX_CHILDREN)} over {MAX_CHILDREN})")
        print(f"    {'stratum':<8}{'floor':>9}{'calib FDR':>11}{'held-out FDR':>14}"
              f"{'real':>7}{'cap':>7}")
        for stratum in entry["confirmed"]["strata"]:
            held = stratum["heldout_fdr"]
            flag = "" if held is None or held <= CAP_STRATUM else "  OVER THE CAP"
            print(f"    {stratum['stratum']:<8}{str(stratum['effective']):>9}"
                  f"{str(stratum['calibration_fdr']):>11}{str(held):>14}"
                  f"{stratum['heldout_real']:>7}{CAP_STRATUM:>7}{flag}")
        overall = entry["confirmed"]["overall_fdr"]
        over = overall is not None and overall > CAP_OVERALL
        print(f"    held-out OVERALL: {overall}  (cap {CAP_OVERALL})"
              + ("  OVER THE CAP" if over else ""))

    top = levels["levels"][-1]
    ids = top["node_ids"]
    roots = top["roots"]
    print("\n" + "=" * 78)
    print(f"THE TOP LEVEL: {len(roots)} roots")
    print("=" * 78)

    from thema.ontology.universe import load_centred

    keys, raw = load_centred(args.space, args.data / "pathways.tsv")
    vectors = np.asarray(raw, dtype=np.float32)
    vectors = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9)
    row_of = {key: i for i, key in enumerate(keys)}
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        names = {f"{r['source']}:{r['source_id']}": r["name"]
                 for r in csv.DictReader(handle, delimiter="\t")}
        genes: dict[str, frozenset[str]] = {}
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        for r in csv.DictReader(handle, delimiter="\t"):
            genes[f"{r['source']}:{r['source_id']}"] = (
                frozenset(r["genes"].split(";")) if r["genes"] not in ("", "-") else frozenset()
            )

    for position in sorted(roots, key=lambda i: -len(top["pathway_members"][i])):
        pathways = top["pathway_members"][position]
        rows = [row_of[k] for k in pathways if k in row_of]
        centre = vectors[rows].mean(0)
        centre = centre / (np.linalg.norm(centre) + 1e-9)
        near = sorted(((float(vectors[row_of[k]] @ centre), k) for k in pathways if k in row_of),
                      reverse=True)[:10]
        print(f"\n  {ids[position]}  {len(top['child_unit_ids'][position])} units, "
              f"{len(pathways)} pathways, support {top['supports'][position]:.3f}")
        print(f"    units: {', '.join(top['child_unit_ids'][position][:12])}"
              + (" ..." if len(top["child_unit_ids"][position]) > 12 else ""))
        for score, key in near:
            print(f"      {score:.3f}  {names.get(key, key)[:86]}")

    print("\n" + "=" * 78)
    print("COVERAGE")
    print("=" * 78)
    area_of_unit: dict[str, list[str]] = defaultdict(list)
    for entry in levels["levels"]:
        for position, node_id in enumerate(entry["node_ids"]):
            for unit in entry["child_unit_ids"][position]:
                area_of_unit[unit].append(node_id)
    reparented = sorted(unit for unit in giant_only if area_of_unit.get(unit))
    print(f"  giant-only themes with an area parent: {len(reparented):,} of {len(giant_only):,} "
          f"= {len(reparented) / len(giant_only):.1%}")
    orphaned = sorted(unit for unit in giant_only if not area_of_unit.get(unit))
    if orphaned:
        print(f"    without one: {len(orphaned)}  {orphaned[:10]}")
    every_unit_placed = sum(1 for unit in unit_ids if area_of_unit.get(unit))
    print(f"  all units with an area parent: {every_unit_placed:,} of {len(unit_ids):,}")

    o50_roots = [n for n in nodes if not o50_parents[n]]
    print(f"  roots before: {len(o50_roots)} ({len(giants)} giants + "
          f"{len(o50_roots) - len(giants)} non-giant)")
    print(f"  roots after, in the combined DAG: {len(roots)} areas "
          f"(the giants are not joined)")

    print("\n  per pathway, the largest non-giant theme above it")
    before = largest_nongiant_ancestor(members, o50_parents, giants)
    area_members: dict[str, set[str]] = {}
    for entry in levels["levels"]:
        for position, node_id in enumerate(entry["node_ids"]):
            area_members[node_id] = set(entry["pathway_members"][position])
    after = dict(before)
    for keys_held in area_members.values():
        size = len(keys_held)
        for key in keys_held:
            if size > after.get(key, 0):
                after[key] = size
    allk = {k for v in members.values() for k in v}
    b_before = Counter(band_of(before.get(k, 0)) for k in allk)
    b_after = Counter(band_of(after.get(k, 0)) for k in allk)
    print(f"    {'band':<10}{'before':>9}{'after':>9}{'change':>9}")
    for low, high in BANDS:
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        print(f"    {label:<10}{b_before.get(label, 0):>9,}{b_after.get(label, 0):>9,}"
              f"{b_after.get(label, 0) - b_before.get(label, 0):>+9,}")

    print("\n" + "=" * 78)
    print("GENE COHERENCE PER LEVEL, against size-matched random (report only)")
    print("=" * 78)
    rng = np.random.default_rng(20261015)
    pool = sorted(allk)
    for entry in levels["levels"]:
        real_vals, rand_vals = [], []
        for position in range(len(entry["node_ids"])):
            pathways = entry["pathway_members"][position]
            if len(pathways) < 2 or len(pathways) > 120:
                continue
            got = coherence(pathways, genes)
            if got is None:
                continue
            real_vals.append(got)
            drawn = [pool[i] for i in rng.choice(len(pool), len(pathways), replace=False)]
            fake = coherence(drawn, genes)
            if fake is not None:
                rand_vals.append(fake)
        if real_vals:
            print(f"  level {entry['level']}: n={len(real_vals)} nodes of 2-120 pathways; "
                  f"median coherence {statistics.median(real_vals):.4f} against "
                  f"{statistics.median(rand_vals):.4f} size-matched random ("
                  f"{statistics.median(real_vals) / max(statistics.median(rand_vals), 1e-9):.1f}x)")

    print("\n" + "=" * 78)
    print("AGREEMENT WITH REACTOME TOP-LEVEL PATHWAYS (secondary)")
    print("=" * 78)
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines()
    )
    children_of: dict[str, set[str]] = defaultdict(set)
    for child, ups in rel.items():
        for parent in ups:
            children_of[parent].add(child)
    # read_reactome_relation keys EVERY node, roots carrying an empty parent list, so the roots
    # are the nodes nothing claims as a child -- which is what reactome_roots returns. Subtracting
    # the key set instead gives the empty set, silently.
    tops = sorted(reactome_roots(rel))
    def descend(root: str) -> set[str]:
        seen, stack = set(), [root]
        while stack:
            node = stack.pop()
            for kid in children_of.get(node, ()):
                if kid not in seen:
                    seen.add(kid)
                    stack.append(kid)
        return seen
    print(f"  Reactome top-level pathways: {len(tops)}")
    print(f"  {'reactome top':<48}{'best area':<14}{'J':>7}{'leaves':>8}")
    scored = []
    for root in tops:
        leaves = {f"reactome:{k}" for k in descend(root) | {root}} & allk
        if len(leaves) < 3:
            continue
        best, score = "", 0.0
        for node_id, held in area_members.items():
            union = len(leaves | held)
            if union:
                value = len(leaves & held) / union
                if value > score:
                    best, score = node_id, value
        scored.append((score, root, best, len(leaves)))
    for score, root, best, size in sorted(scored, reverse=True):
        print(f"  {names.get(f'reactome:{root}', root)[:46]:<48}{best:<14}{score:>7.3f}{size:>8}")
    if scored:
        print(f"  median best Jaccard: {statistics.median([s for s, *_ in scored]):.3f}")

    print("\n" + "=" * 78)
    print("SUMMARY PLACEMENT (display only, nothing attached)")
    print("=" * 78)
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets
    edges: dict[str, set[str]] = {
        f"reactome:{c}": {f"reactome:{p}" for p in ps} for c, ps in rel.items()
    }
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(),
            PRIMARY_RELATIONS).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}
    summaries = sorted(set(names) - allk)
    key_sets = targets(edges, summaries, allk, min_size=3)
    print(f"  curated summaries with 3+ leaf descendants in L: {len(key_sets):,}")

    def home(leaf_set: frozenset[str], pool_members: Mapping[str, set[str]]) -> tuple[str, int]:
        best, size = "", 0
        for node_id, held in pool_members.items():
            if len(leaf_set & held) >= HOME_SHARE * len(leaf_set):
                if not best or len(held) < size:
                    best, size = node_id, len(held)
        return best, size

    o50_all = dict(members)
    combined = {**{n: v for n, v in members.items() if n not in giants}, **area_members}
    rows = []
    for key, leaf_set in key_sets.items():
        a, a_size = home(leaf_set, o50_all)
        b, b_size = home(leaf_set, combined)
        rows.append((key, len(leaf_set), a, a_size, b, b_size))
    print(f"  {'summary size band':<20}{'n':>6}{'home in O50':>13}{'on a giant':>12}"
          f"{'home combined':>15}{'on an area':>12}")
    for low, high in ((3, 10), (11, 50), (51, 200), (201, 10**9)):
        band = [r for r in rows if low <= r[1] <= high]
        if not band:
            continue
        in_o50 = sum(1 for r in band if r[2])
        on_giant = sum(1 for r in band if r[2] in giants)
        in_comb = sum(1 for r in band if r[4])
        on_area = sum(1 for r in band if r[4] in area_members)
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        print(f"  {label:<20}{len(band):>6}{in_o50:>13}{on_giant:>12}{in_comb:>15}{on_area:>12}")
    in_o50 = sum(1 for r in rows if r[2])
    on_giant = sum(1 for r in rows if r[2] in giants)
    in_comb = sum(1 for r in rows if r[4])
    on_area = sum(1 for r in rows if r[4] in area_members)
    print(f"  {'ALL':<20}{len(rows):>6}{in_o50:>13}{on_giant:>12}{in_comb:>15}{on_area:>12}")
    print(f"  share with a home: O50 {in_o50 / len(rows):.1%} "
          f"(of those, {on_giant / max(in_o50, 1):.1%} a giant); "
          f"combined {in_comb / len(rows):.1%} (of those, {on_area / max(in_comb, 1):.1%} an area)")

    print("\n" + "=" * 78)
    print("CRITERIA ccode OWNS")
    print("=" * 78)
    kids: dict[int, int] = Counter()
    for above in top["parents"]:
        for parent in above:
            kids[parent] += 1
    held_by_kids = [
        {u for j, above in enumerate(top["parents"]) if i in above
         for u in top["child_unit_ids"][j]}
        for i in range(len(ids))
    ]
    max_children = max(
        (kids.get(i, 0) + len(set(top["child_unit_ids"][i]) - held_by_kids[i])
         for i in range(len(ids))),
        default=0,
    )
    conf = top["confirmed"]
    rates = [(e["stratum"], e["heldout_fdr"]) for e in conf["strata"]
             if e["heldout_fdr"] is not None]
    worst = max(rates, key=lambda t: t[1]) if rates else None
    overall = conf["overall_fdr"]
    checks = [
        ("held-out FDR within the caps at level 2",
         f"overall {overall} (cap {CAP_OVERALL})"
         + (f", worst stratum {worst[0]} at {worst[1]} (cap {CAP_STRATUM})" if worst else ""),
         (overall is not None and overall <= CAP_OVERALL)
         and (worst is not None and worst[1] <= CAP_STRATUM)),
        (f"the top has {MIN_ROOTS}-{MAX_ROOTS} roots", f"{len(roots)} roots",
         MIN_ROOTS <= len(roots) <= MAX_ROOTS),
        (f"no node has more than {MAX_CHILDREN} children", f"max {max_children}",
         max_children <= MAX_CHILDREN),
        (f"at least {REPARENT_BAR:.0%} of the {len(giant_only)} giant-only themes get an area",
         f"{len(reparented) / len(giant_only):.1%}",
         len(reparented) / len(giant_only) >= REPARENT_BAR),
    ]
    for what, number, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")
        print(f"        {number}")
    print("\n  C6 (blind intruder test) is the reviewer's and is NOT judged here.")
    print("  Whether the top level is intuitive is Aviyah's.")
    print("  ADOPTED: nothing.")
    del manifest
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
