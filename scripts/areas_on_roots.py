#!/usr/bin/env python3
"""Areas on the O50s roots. Declared 18 Oct 2026, before any result. Exploratory; adopts nothing.

Aviyah's design, as against prompt 44's arm A. Three things differ and they are the whole point:

* **The units are the 261 O50s roots, the five giants included**, each as one unit. No giant drop
  and no anchors, so **a giant is a unit and an area can contain one** -- the open question prompt
  45 ended on, since arm A's areas never contained a giant because none was ever offered to them.
* **The structure is the whole unchanged O50s DAG plus the areas.** Arm A's structure was areas plus
  anchors plus units, 1,212 nodes, and that is what left five anchors with no possible parent. Here
  every O50s theme is present, so containment is complete by construction.
* **The twin and chain rules run inside the areas pass only.** The spec asks for nothing but strict
  containment and a transitive reduction over the whole set, so **O50s itself is left untouched** --
  no seam victims and nothing to hold out.

Everything else is rec2fix's: 200 runs on 80% subsamples, Ward, recurrence 0.70 on unit sets, union
pathway sets, consensus, the joint fixed point at twin 0.50 and chain 0.85 on union sets, floors on
20 unit scrambles checked once on four held-out seeds.

Usage::

    uv run scripts/areas_on_roots.py
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: A node this large is a giant, O50s's own bar.
GIANT = 1000

#: A root this small is a small root.
SMALL_ROOT = 50

#: Report-only duplication thresholds.
PAIR_J = 0.50
INSIDE = 0.80

#: The declared root ceiling.
MAX_ROOTS = 49

#: Caps, unchanged.
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80

#: Area size bands for the report.
AREA_BANDS = ((1, 50), (51, 200), (201, 500), (501, 1000), (1001, 10 ** 9))


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


def band_of(size: int, bands: Sequence[tuple[int, int]] = AREA_BANDS) -> str:
    """The band label a size falls in.

    Args:
        size: Member count.
        bands: The band edges.

    Returns:
        The band label.
    """
    for low, high in bands:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
    return "?"


def units_of_roots(nodes: Mapping[str, Mapping[str, str]],
                   members: Mapping[str, set[str]]) -> tuple[list[str], list[set[str]]]:
    """The units: every O50s root, giants included, each as one unit.

    A root is a node no edge claims as a child. The giants are roots in O50s and are **kept**, which
    is the difference from ``recursive_top_O50.units_of`` and the reason an area can contain one
    here.

    Args:
        nodes: O50s node rows.
        members: O50s node to member keys.

    Returns:
        ``(ids, member sets)``.

    Raises:
        ValueError: If the roots do not cover the universe, which would mean a unit has to be
            invented for the remainder and the design would no longer be the one declared.
    """
    ids = sorted(node for node, row in nodes.items() if not row["parents"].strip())
    held = [set(members[node]) for node in ids]
    covered = set().union(*held) if held else set()
    every = {key for one in members.values() for key in one}
    if covered != every:
        raise ValueError(
            f"the {len(ids)} roots cover {len(covered):,} of {len(every):,} pathways; "
            f"{len(every - covered)} would need a unit of their own")
    return ids, held


def structure(held: Mapping[str, set[str]], keys: Sequence[str]) -> dict[str, object]:
    """Strict containment over every pair, then the transitive reduction.

    Args:
        held: Node id to pathway keys.
        keys: Every pathway key, in bit order.

    Returns:
        The ids, the closure, the direct edges, the roots and the parent and child maps.
    """
    import arm_a_containment as ac

    ids, stack, sizes = ac.pack_all(dict(held), keys)
    closure = ac.containment(stack, sizes)
    edges = ac.direct_edges(closure)
    roots = [ids[i] for i in range(len(ids)) if not closure[i].any()]
    parents = {ids[c]: [ids[p] for p in np.flatnonzero(edges[c])] for c in range(len(ids))}
    children: dict[str, list[str]] = {node: [] for node in ids}
    for child, above in parents.items():
        for parent in above:
            children[parent].append(child)
    return {"ids": ids, "closure": closure, "edges": edges, "roots": roots,
            "parents": parents, "children": children, "sizes": sizes}


def sanity(built: Mapping[str, object], held: Mapping[str, set[str]]) -> dict[str, object]:
    """Report item 8: nothing is wholly inside another node without descending from it.

    With strict containment over every pair and a transitive reduction, the closure **is** the
    descendant relation, so the count must be zero. Checking it is the point: it is the invariant
    arm A broke, and it broke silently.

    Args:
        built: What :func:`structure` returned.
        held: Node id to pathway keys.

    Returns:
        The count of violations and up to ten examples.
    """
    ids = built["ids"]
    closure = built["closure"]
    direct = built["parents"]
    reach: dict[str, set[str]] = {}

    def above(node: str) -> set[str]:
        """Everything reachable upwards through the direct edges."""
        if node not in reach:
            reach[node] = set()
            reach[node] = {p for parent in direct[node] for p in {parent} | above(parent)}
        return reach[node]

    bad: list[dict[str, object]] = []
    for position, child in enumerate(ids):
        ancestors = above(child)
        for other in np.flatnonzero(closure[position]):
            parent = ids[other]
            if parent not in ancestors:
                bad.append({"child": child, "child_size": len(held[child]),
                            "parent": parent, "parent_size": len(held[parent])})
    return {"violations": len(bad), "examples": bad[:10]}


def main(argv: list[str] | None = None) -> int:
    """Build the areas on the O50s roots, assemble one structure and write the report inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--x2", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas"))
    parser.add_argument("--review", type=Path,
                        default=Path("data/experiments/areas_on_roots_2026-10-18"))
    parser.add_argument("--runs", type=int, default=200)
    args = parser.parse_args(argv)

    import areas_rec2fix as fix
    import recursive_top_O50 as rt
    from thema.ontology.universe import load_centred

    clock = time.perf_counter()
    nodes, members = rt.read_build(args.o50s)
    every = sorted({key for one in members.values() for key in one})
    giants = {node for node, one in members.items() if len(one) > GIANT}
    unit_ids, unit_held = units_of_roots(nodes, members)
    sizes = [len(one) for one in unit_held]
    print("AREAS ON THE O50s ROOTS. Declared 18 Oct 2026; exploratory, adopts nothing.")
    print(f"  units: {len(unit_ids)} O50s roots, the {len(giants)} giants included and clustered "
          f"like any other unit; NO anchors")
    print(f"  sizes {min(sizes)}/{int(np.median(sizes))}/{max(sizes)}; "
          f"{sum(1 for s in sizes if s <= SMALL_ROOT)} of {SMALL_ROOT} or fewer; "
          f"sum {sum(sizes):,} against {len(every):,} pathways "
          f"-> {sum(sizes) / len(every):.2f}x double counting", flush=True)

    cache = args.out / f"areas_roots_{len(unit_ids)}units_{args.runs}runs.json"
    if cache.is_file():
        got = json.loads(cache.read_text())
        print(f"  areas from {cache.name} ({len(got['pathway_members'])} areas, cached)",
              flush=True)
    else:
        keys, vectors = load_centred(args.x2, args.data / "pathways.tsv")
        centroids = rt.unit_centroids(unit_held, keys, vectors)
        got = fix.build_areas(centroids, unit_held, args.runs)
        args.out.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(got) + "\n", encoding="utf-8")
    areas = {f"a_{i:05d}": set(one)
             for i, one in enumerate(got["pathway_members"])}
    area_units = {f"a_{i:05d}": [unit_ids[u] for u in rows]
                  for i, rows in enumerate(got["unit_indices"])}
    area_support = {f"a_{i:05d}": float(s) for i, s in enumerate(got["supports"])}
    print(f"  {len(areas)} areas, sizes "
          f"{min(len(v) for v in areas.values())}/"
          f"{int(np.median([len(v) for v in areas.values()]))}/"
          f"{max(len(v) for v in areas.values())} pathways", flush=True)

    # The O50s DAG unchanged, plus the areas. Nothing of O50s is removed or edited.
    held: dict[str, set[str]] = {node: set(one) for node, one in members.items()}
    kind = {node: ("giant" if node in giants else "o50s") for node in held}
    for node, one in areas.items():
        held[node] = one
        kind[node] = "area"
    print(f"  one structure: {len(members):,} O50s themes (unchanged) + {len(areas)} areas "
          f"= {len(held):,} nodes", flush=True)
    built = structure(held, every)
    roots = built["roots"]
    children = built["children"]
    counts = [len(children[node]) for node in built["ids"]]
    checked = sanity(built, held)
    print(f"  {len(roots)} roots, {int(built['edges'].sum()):,} direct edges, "
          f"{int(built['closure'].sum()):,} containment pairs; "
          f"children max {max(counts, default=0)}, median {statistics.median(counts):.0f} "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)
    print(f"  SANITY: nodes wholly inside another without descending from it: "
          f"{checked['violations']}", flush=True)
    if checked["violations"]:
        raise SystemExit(f"{checked['violations']} containment violations; stop")
    return finish(args, got, areas, area_units, area_support, held, kind, giants, built,
                  members, every, clock)


def finish(args: argparse.Namespace, got: Mapping[str, object], areas: Mapping[str, set[str]],
           area_units: Mapping[str, list[str]], area_support: Mapping[str, float],
           held: Mapping[str, set[str]], kind: Mapping[str, str], giants: set[str],
           built: Mapping[str, object], members: Mapping[str, set[str]],
           every: Sequence[str], clock: float) -> int:
    """The report's figures, the build files and the reviewer's three tables.

    Args:
        args: Parsed arguments.
        got: What ``build_areas`` returned.
        areas: Area id to pathway keys.
        area_units: Area id to its unit ids.
        area_support: Area id to support.
        held: Every node's pathway keys.
        kind: Every node's kind.
        giants: The O50s giants.
        built: What :func:`structure` returned.
        members: O50s node to member keys.
        every: Every pathway key.
        clock: Start time.

    Returns:
        0.
    """
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    roots = built["roots"]
    parents, children, ids = built["parents"], built["children"], built["ids"]
    counts = [len(children[node]) for node in ids]

    small = [node for node in roots if len(held[node]) <= SMALL_ROOT]
    containing: dict[str, list[dict[str, object]]] = {}
    for node in small:
        mine = held[node]
        scored = sorted(
            ((len(mine & held[other]) / len(mine), other, len(held[other]),
              len(mine - held[other]))
             for other in ids if other != node and len(held[other]) > len(mine)),
            reverse=True)
        containing[node] = [{"node": o, "size": s, "share": round(share, 4), "missing": miss}
                            for share, o, s, miss in scored[:3]]

    pairs = list(itertools.combinations(sorted(roots), 2))
    dup = sorted(((round(jaccard(held[a], held[b]), 4), a, len(held[a]), b, len(held[b]))
                  for a, b in pairs if jaccard(held[a], held[b]) >= PAIR_J), reverse=True)
    bins: Counter[str] = Counter()
    mostly: list[dict[str, object]] = []
    for node in roots:
        mine = held[node]
        for other in ids:
            if other == node or len(held[other]) <= len(mine):
                continue
            share = len(mine & held[other]) / len(mine)
            if share >= INSIDE:
                missing = len(mine - held[other])
                label = ("0" if missing == 0 else "1-5" if missing <= 5
                         else "6-20" if missing <= 20 else "21+")
                bins[label] += 1
                mostly.append({"root": node, "root_size": len(mine), "other": other,
                               "other_size": len(held[other]), "share": round(share, 4),
                               "missing": missing})
    mostly.sort(key=lambda row: (-row["share"], row["root"]))

    big = sorted((n for n in areas if len(areas[n]) > GIANT), key=lambda n: -len(areas[n]))
    with_giant = {node: sorted(g for g in giants if members[g] <= areas[node])
                  for node in areas}
    holding = {node: gs for node, gs in with_giant.items() if gs}
    print(f"\n  areas over {GIANT:,} pathways: {len(big)}")
    for node in big:
        print(f"    {node}  {len(areas[node]):,} pathways, {len(area_units[node])} units"
              + (f", CONTAINS {', '.join(holding[node])}" if node in holding else ""))
    print(f"  areas containing a giant: {len(holding)} of {len(areas)}")
    for node, gs in sorted(holding.items(), key=lambda kv: -len(areas[kv[0]])):
        print(f"    {node} ({len(areas[node]):,}) contains "
              + ", ".join(f"{g} ({len(members[g]):,})" for g in gs))

    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    names = {f"{r['source']}:{r['source_id']}": r["name"] for r in rows}
    universe = set(every)
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

    def score(pool: Mapping[str, set[str]]) -> tuple[int, float]:
        """Summary placement and the Reactome median best Jaccard."""
        items = list(pool.values())
        total = sum(1 for leaves in key_sets.values()
                    if any(len(leaves & one) >= HOME_SHARE * len(leaves) for one in items))
        best = statistics.median([max((jaccard(leaves, one) for one in items), default=0.0)
                                  for leaves in branches.values()])
        return total, best

    o50s_only = {node: set(one) for node, one in members.items()}
    base_total, base_best = score(o50s_only)
    total, best = score(held)
    print(f"\n  summary placement: O50s {base_total:,} of {len(key_sets):,} = "
          f"{base_total / len(key_sets):.1%}; with the areas {total:,} = "
          f"{total / len(key_sets):.1%}  ({total - base_total:+})")
    print(f"  Reactome median best J: O50s {base_best:.3f}; with the areas {best:.3f}",
          flush=True)

    checked = sanity(built, held)
    record = {
        "o50s": str(args.o50s),
        "n_units": len({u for us in area_units.values() for u in us}),
        "n_o50s_themes": len(members), "n_areas": len(areas),
        "giants": sorted(giants),
        "area_members": {n: sorted(v) for n, v in areas.items()},
        "area_units": {n: list(v) for n, v in area_units.items()},
        "area_support": dict(area_support),
        "areas_with_a_giant": {n: gs for n, gs in holding.items()},
        "kind": dict(kind),
        "roots": sorted(roots, key=lambda n: -len(held[n])),
        "root_rows": [{"node": n, "kind": kind[n], "size": len(held[n]),
                       "n_children": len(children[n])}
                      for n in sorted(roots, key=lambda n: -len(held[n]))],
        "small_roots": containing,
        "duplication": {"root_pairs_ge_0.5": dup, "roots_80_inside": mostly[:300],
                        "n_roots_80_inside": len(mostly), "missing_bins": dict(bins)},
        "children_max": max(counts, default=0),
        "children_median": float(statistics.median(counts)) if counts else 0.0,
        "n_direct_edges": int(built["edges"].sum()),
        "n_closure_pairs": int(built["closure"].sum()),
        "area_bands": dict(Counter(band_of(len(v)) for v in areas.values())),
        "floors": got["floors"], "confirmed": got["confirmed"],
        "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
        "n_after_consensus": got["n_after_consensus"], "repair": got["repair"],
        "sanity": checked,
        "placement": total, "placement_share": round(total / len(key_sets), 4),
        "placement_o50s": base_total,
        "reactome_median_best_j": round(best, 4),
        "reactome_median_best_j_o50s": round(base_best, 4),
        "seconds": round(time.perf_counter() - clock, 1),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "build.json").write_text(json.dumps(record) + "\n", encoding="utf-8")
    with (args.out / "nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "kind", "size", "giant", "root",
                                            "n_parents", "n_children", "parents"])
        writer.writeheader()
        for node in ids:
            writer.writerow({
                "node": node, "kind": kind[node], "size": len(held[node]),
                "giant": "true" if len(held[node]) > GIANT else "",
                "root": "true" if node in set(roots) else "",
                "n_parents": len(parents[node]), "n_children": len(children[node]),
                "parents": " ".join(sorted(parents[node]))})
    with (args.out / "edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for child, above in sorted(parents.items()):
            for parent in sorted(above):
                handle.write(f"{parent}\t{child}\n")
    with (args.out / "area_members.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("node\tkey\n")
        for node in sorted(areas):
            for key in sorted(areas[node]):
                handle.write(f"{node}\t{key}\n")

    args.review.mkdir(parents=True, exist_ok=True)
    with (args.review / "roots.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "kind", "size", "n_children", "members"])
        writer.writeheader()
        for node in sorted(roots, key=lambda n: -len(held[n])):
            writer.writerow({"node": node, "kind": kind[node], "size": len(held[node]),
                             "n_children": len(children[node]),
                             "members": " ".join(sorted(held[node]))})
    with (args.review / "small_roots.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["root", "root_size", "root_members", "rank", "container",
                        "container_size", "share", "missing", "container_members"])
        writer.writeheader()
        for node in sorted(small, key=lambda n: -len(held[n])):
            for rank, entry in enumerate(containing[node], 1):
                writer.writerow({
                    "root": node, "root_size": len(held[node]),
                    "root_members": " ".join(sorted(held[node])),
                    "rank": rank, "container": entry["node"],
                    "container_size": entry["size"], "share": entry["share"],
                    "missing": entry["missing"],
                    "container_members": " ".join(sorted(held[entry["node"]]))})
    with (args.review / "areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "n_units", "support", "giant", "root",
                        "contains_giants", "units", "members"])
        writer.writeheader()
        for node in sorted(areas, key=lambda n: -len(areas[n])):
            writer.writerow({
                "node": node, "size": len(areas[node]), "n_units": len(area_units[node]),
                "support": round(area_support[node], 6),
                "giant": "true" if len(areas[node]) > GIANT else "",
                "root": "true" if node in set(roots) else "",
                "contains_giants": " ".join(holding.get(node, [])),
                "units": " ".join(area_units[node]),
                "members": " ".join(sorted(areas[node]))})
    print(f"\n  -> {args.out} and {args.review}  ({record['seconds']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
