#!/usr/bin/env python3
"""The areas layer, corrected: union sets everywhere, and one structure over the whole top.

Declared 15 Oct 2026 before any result, copied verbatim into DECISIONS. **This is a corrected
re-run of prompt 36, not a new method**, and it adopts nothing by itself.

The reviewer audited rec2 and found two gaps between what prompt 34 declared and what rec2 did.
Both are fixed here and nothing else changes: the unit rule, the anchors, the 200 Ward runs, the
subsample scheme, the floors and all 25 scramble seeds are rec2's, reused rather than re-chosen.

**Gap 1: the pathway sets were not unions.** Prompt 34 said an area's pathways are the union of its
units' pathways. rec2 stored the set ``consensus`` returned and recovered the units from provenance,
and the two disagreed for 188 of 343 areas. The disagreement was in the *bookkeeping*, not in
``consensus``: see :func:`fold_units`. Here the two agree by construction and a test asserts it.

**Gap 2: the rules stopped at the seams.** rec2 applied the same-theme cutoff and chain collapse
among areas only. Anchors were never compared with each other or with areas, no area was ever
collapsed into one of its own units, 27 units sat strictly inside an area with no edge saying so,
and ``area_edges.tsv`` held every area-to-unit pair rather than the direct ones, which is what
inflated the children count to 181. Here there is **one node set** -- areas, anchors and units --
and the rules and the edges run over all of it.

**Aviyah's giant rule, recorded with the prompt**: an area over 1,000 pathways is a giant and is
kept out of the working view, exactly as O50's own giants are. rec2 reported its eight 1,000-plus
areas as a criterion failure because the rule was not yet written down.

Usage::

    uv run scripts/areas_rec2fix.py --estimate
    uv run scripts/areas_rec2fix.py
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

import recursive_top_O50 as rt
import recursive_top_O50_rec2 as r2

#: An area this large is a giant: flagged, and kept out of the view. Aviyah's rule, recorded 15 Oct.
GIANT_AREA = 1000


def fold_units(
    n_candidates: int, inherited: Sequence[object], unit_blocks: Sequence[np.ndarray], n_units: int
) -> list[np.ndarray]:
    """Each candidate's unit set after consensus, as unit bitsets.

    ``consensus`` can be run on pathway sets and still leave an area's pathways equal to the union
    of its units' pathways, because every stage is **union-closed**: an inherit sets the grower to
    ``own | other`` -- a full absorption of one candidate's set, never a partial addition -- and
    collapse and merge only ever drop a node, keeping the survivor's membership. Since
    ``paths(U1 | U2) == paths(U1) | paths(U2)``, a candidate that enters as the union of its units'
    pathways stays one.

    What has to match is the unit bookkeeping, and two details decide it:

    * **Event order.** A grower takes the source's unit set *as it stands at that moment*. Taking
      the source's final set over-credits: if A absorbs B and only later B absorbs C, A never
      received C's members, and crediting it C's units makes the union exceed the pathway set.
    * **Superseded candidates are not credited.** A superseded candidate is dropped and its winner's
      membership is untouched, so its units belong to nobody. rec2 credited them, which is what made
      its stored pathway set *smaller* than the union it reported for 188 areas.

    Checked on 4,000 randomised cases through consensus and the joint fixed point with no
    disagreement; :mod:`tests.test_areas_rec2fix` keeps that check.

    Args:
        n_candidates: How many candidates went into consensus.
        inherited: ``consensus``'s inheritance events, in order.
        unit_blocks: Unit bitset per candidate, as it entered.
        n_units: Bitset width in units.

    Returns:
        One unit bitset per candidate, aligned with ``unit_blocks``.
    """
    from thema.ontology import bitset as bits

    held = [set(bits.unpack(unit_blocks[c])) for c in range(n_candidates)]
    for event in inherited:
        held[event.parent] = held[event.parent] | held[event.source]
    return [bits.pack(sorted(rows), n_units) for rows in held]


def containment(blocks: Sequence[np.ndarray]) -> np.ndarray:
    """Strict-containment matrix: ``out[child, parent]`` is True iff child is strictly inside.

    Args:
        blocks: Member bitsets, all the same width.

    Returns:
        An ``(n, n)`` boolean matrix.
    """
    stack = np.vstack([block[None, :] for block in blocks])
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    n = len(blocks)
    out = np.zeros((n, n), dtype=bool)
    for child in range(n):
        inside = np.bitwise_count(stack[child][None, :] & ~stack).sum(axis=1) == 0
        out[child] = inside & (sizes > sizes[child])
    np.fill_diagonal(out, False)
    return out


def direct_edges(closure: np.ndarray) -> np.ndarray:
    """Transitive reduction of a strict-containment closure.

    ``closure[b, a]`` says a strictly contains b. An edge is direct iff no third node sits between
    the two, which is exactly ``closure & ~(closure @ closure)`` for a strict partial order.

    Args:
        closure: The containment closure.

    Returns:
        The direct edges, same shape.
    """
    via = (closure.astype(np.uint8) @ closure.astype(np.uint8)) > 0
    return closure & ~via


def build_areas(
    matrix: np.ndarray,
    unit_members: Sequence[set[str]],
    runs: int,
    *,
    theta_match: float = rt.THETA_MATCH,
    theta_same: float = rt.THETA_SAME,
    collapse_share: float = rt.COLLAPSE_SHARE,
    report: bool = True,
) -> dict[str, object]:
    """Level 2 on union pathway sets, with the unit bookkeeping that keeps them unions.

    Identical to rec2's level 2 up to the gate -- the same 200 Ward runs on 80% subsamples of
    units, recurrence matching on unit membership at ``theta_match``, the same 20 calibration and
    4 held-out scrambles and the same cal8 target -- so the candidates and the floors are rec2's.
    From the gate onwards every comparison is on pathway sets, and the unit set is carried through
    by :func:`fold_units` rather than recovered afterwards.

    Args:
        matrix: Unit centroids for the units being clustered.
        unit_members: Member keys per unit, in the same order.
        runs: Trees per side.
        theta_match: Recurrence threshold, on unit membership.
        theta_same: The one same-theme cutoff, on pathway sets.
        collapse_share: Chain-collapse share, on pathway sets.
        report: Print progress.

    Returns:
        The areas, their units, the floors and the timings.

    Raises:
        ValueError: If an area's pathway set is not the union of its units' pathways, or if collapse
            or merge did something other than drop rows.
    """
    from build_10770 import confirm
    from regate_floors import solve_to, without_minimum
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.repair import repair_joint
    from thema.ontology.v04 import gate

    n = len(unit_members)
    clock = time.perf_counter()
    rows_seq = rt.subsample_rows(n, runs)
    real = rt.side(matrix, n, rows_seq, theta_match)
    real_rows = real.rows()
    if report:
        print(f"    real side: {len(real_rows):,} candidates "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    calib: list[list[tuple[int, float]]] = []
    held_sides: list[list[tuple[int, float]]] = []
    for label, seeds, sink in (("calibration", r2.CALIBRATION_SEEDS, calib),
                               ("held out", r2.HELDOUT_SEEDS, held_sides)):
        for seed in seeds:
            got = rt.side(np.ascontiguousarray(null_embeddings(matrix, seed)), n,
                          rows_seq, theta_match)
            sink.append(got.rows())
            del got
        if report:
            print(f"    {label}: {len(seeds)} side(s) "
                  f"({time.perf_counter() - clock:.0f}s cumulative)", flush=True)

    solved = without_minimum(solve_to(real_rows, calib, r2.FLOOR_TARGET))
    confirmed = confirm(real_rows, held_sides, solved)
    if report:
        print("    floors " + ", ".join(
            f"{e['stratum']}:{e['effective']}" for e in solved), flush=True)

    keep = np.flatnonzero(gate(real_rows, solved)).tolist()
    unit_blocks = [real.blocks[i] for i in keep]
    supports = [float(real.supports[i]) for i in keep]
    inclusions = [real.selections[i] for i in keep]
    keys, index = r2.pathway_space(unit_members)
    width = bits.words_for(len(keys)) * bits.WORD
    path_blocks = r2.as_pathway_blocks(unit_blocks, unit_members, index, len(keys))
    if report:
        print(f"    {len(keep):,} through the gate; comparing on {len(keys):,} pathways "
              f"instead of {n} units", flush=True)

    verdict = consensus(path_blocks, supports, inclusions, width, stray=0.0, jaccard=theta_same)
    accepted = list(verdict.accepted)
    folded = fold_units(len(keep), verdict.inherited, unit_blocks, n)
    kept_path = [verdict.members[i] for i in range(len(accepted))]
    kept_units = [folded[c] for c in accepted]
    if report:
        print(f"    consensus at {theta_same} on union sets: {len(keep):,} -> "
              f"{len(accepted):,}", flush=True)

    repaired = repair_joint(kept_path, [supports[c] for c in accepted],
                            [inclusions[c] for c in accepted], collapse_share, theta_same,
                            rt.SURVIVOR)
    dropped = set(repaired.collapsed) | set(repaired.merged)
    survivors = [i for i in range(len(accepted)) if i not in dropped]
    if len(survivors) != len(repaired.members):
        raise ValueError(
            f"cannot map {len(repaired.members)} repaired areas back to {len(survivors)} "
            "surviving positions; collapse or merge did not only drop rows")
    if report:
        print(f"    joint fixed point at {collapse_share}/{theta_same} on union sets: "
              f"{len(accepted):,} -> {len(repaired.members):,}", flush=True)

    unit_rows = [sorted(bits.unpack(kept_units[i])) for i in survivors]
    paths = [sorted(keys[b] for b in bits.unpack(block)) for block in repaired.members]
    for position, (held, rows) in enumerate(zip(paths, unit_rows, strict=True)):
        union = sorted({key for row in rows for key in unit_members[row]})
        if held != union:
            raise ValueError(
                f"area {position}: pathway set of {len(held)} is not the union of its "
                f"{len(rows)} units, which hold {len(union)}")
    return {
        "pathway_members": paths,
        "unit_indices": unit_rows,
        "supports": [float(s) for s in repaired.supports],
        "floors": solved,
        "confirmed": confirmed,
        "n_candidates": len(real_rows),
        "n_gated": len(keep),
        "n_after_consensus": len(accepted),
        "seconds": round(time.perf_counter() - clock, 1),
        "repair": {"n_collapsed": len(repaired.collapsed), "n_merged": len(repaired.merged),
                   "rounds": repaired.rounds},
    }


def combine(
    area_paths: Sequence[Sequence[str]],
    area_units: Sequence[Sequence[int]],
    area_support: Sequence[float],
    unit_ids: Sequence[str],
    unit_members: Sequence[set[str]],
    unit_support: Sequence[float],
    anchor_at: Sequence[int],
    level_at: Sequence[int],
    *,
    theta_same: float = rt.THETA_SAME,
    collapse_share: float = rt.COLLAPSE_SHARE,
    report: bool = True,
) -> dict[str, object]:
    """One node set over areas, anchors and units, with the rules applied to every pair.

    This is gap 2. The combined set is every area, the 6 anchors and all 655 clustered units, and
    the two rules run over all of it to a joint fixed point: a non-nested pair at Jaccard
    ``theta_same`` or more is merged, and a parent whose child covers ``collapse_share`` of it
    collapses, both with O50's own survivor rule. Anchors and units are themselves units, so their
    pathway set is already a union of one and the invariant is trivially kept.

    Args:
        area_paths: Pathway keys per area.
        area_units: Unit indices per area, in the global unit space.
        area_support: Support per area.
        unit_ids: Every unit id, in the global unit space.
        unit_members: Member keys per unit, in the same space.
        unit_support: Support per unit.
        anchor_at: Global indices of the anchors.
        level_at: Global indices of the clustered units.
        theta_same: Merge cutoff.
        collapse_share: Collapse share.
        report: Print progress.

    Returns:
        The surviving nodes, the giants, the edges and what the rules did at the seams.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.repair import repair_joint

    keys = sorted({key for held in unit_members for key in held})
    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD

    ids: list[str] = []
    kinds: list[str] = []
    units: list[list[int]] = []
    held_sets: list[list[str]] = []
    support: list[float] = []
    for position, paths in enumerate(area_paths):
        ids.append(f"b2_{position:05d}")
        kinds.append("area")
        units.append(list(area_units[position]))
        held_sets.append(list(paths))
        support.append(float(area_support[position]))
    for kind, rows in (("anchor", anchor_at), ("unit", level_at)):
        for row in rows:
            ids.append(unit_ids[row])
            kinds.append(kind)
            units.append([row])
            held_sets.append(sorted(unit_members[row]))
            support.append(float(unit_support[row]))

    blocks = [bits.pack(sorted(index[key] for key in held), len(keys)) for held in held_sets]
    blocks = [bits.pack(sorted(bits.unpack(block)), width) for block in blocks]
    inclusions = [{b: 1.0 for b in bits.unpack(block)} for block in blocks]
    if report:
        print(f"  COMBINED SET: {len(ids):,} nodes -- {kinds.count('area')} areas, "
              f"{kinds.count('anchor')} anchors, {kinds.count('unit')} units; "
              f"rules at {collapse_share}/{theta_same} over every pair", flush=True)

    repaired = repair_joint(blocks, support, inclusions, collapse_share, theta_same, rt.SURVIVOR)
    dead = set(repaired.collapsed) | set(repaired.merged)
    alive = [i for i in range(len(ids)) if i not in dead]
    if len(alive) != len(repaired.members):
        raise ValueError("the combined repair did something other than drop rows")
    at = {node: position for position, node in enumerate(alive)}

    seams = [
        {"victim": ids[v], "victim_kind": kinds[v], "victim_size": len(held_sets[v]),
         "keeper": ids[k], "keeper_kind": kinds[k], "keeper_size": len(held_sets[k]),
         "rule": rule, "detail": repaired.merged_kind.get(v, ""),
         "seam": kinds[v] != "area" or kinds[k] != "area"}
        for rule, book in (("collapse", repaired.collapsed), ("merge", repaired.merged))
        for v, k in sorted(book.items())
    ]
    n_seam = sum(1 for event in seams if event["seam"])
    if report:
        print(f"    {len(repaired.collapsed)} collapsed, {len(repaired.merged)} merged -> "
              f"{len(alive):,} nodes; {n_seam} of them involve an anchor or a unit", flush=True)

    giant_at = {i for i in alive
                if kinds[i] == "area" and len(bits.unpack(repaired.members[at[i]])) > GIANT_AREA}
    giants = [i for i in alive if i in giant_at]
    view = [i for i in alive if i not in giant_at]
    view_blocks = [repaired.members[at[i]] for i in view]
    if report:
        print(f"    {len(giants)} giant areas over {GIANT_AREA} pathways flagged -> "
              f"{len(view):,} nodes in the view", flush=True)

    closure = containment(view_blocks) if view_blocks else np.zeros((0, 0), dtype=bool)
    edges = direct_edges(closure)
    return {
        "ids": ids, "kinds": kinds, "units": units, "support": support, "keys": keys,
        "alive": alive,
        "members": [sorted(keys[b] for b in bits.unpack(repaired.members[at[i]])) for i in alive],
        "giants": giants,
        "view": view,
        "closure": closure,
        "edges": edges,
        "seams": seams,
        "collapsed": {ids[v]: ids[k] for v, k in repaired.collapsed.items()},
        "merged": {ids[v]: ids[k] for v, k in repaired.merged.items()},
        "rounds": repaired.rounds,
    }


def main(argv: list[str] | None = None) -> int:
    """Build the corrected areas layer, or just estimate it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--space", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix"))
    parser.add_argument("--runs", type=int, default=rt.RUNS)
    parser.add_argument("--estimate", action="store_true")
    args = parser.parse_args(argv)

    from thema.ontology.universe import load_centred

    nodes, members = rt.read_build(args.frozen)
    unit_themes, o50_giants, giant_only, loose = rt.units_of(nodes, members)
    unit_ids = list(unit_themes) + [f"loose:{key}" for key in loose]
    unit_members = [members[node] for node in unit_themes] + [{key} for key in loose]
    unit_support = [float(nodes[node]["support"]) for node in unit_themes] + [0.0] * len(loose)

    anchor_at = [i for i, held in enumerate(unit_members) if len(held) > r2.ANCHOR_PATHWAYS]
    level_at = [i for i, held in enumerate(unit_members) if len(held) <= r2.ANCHOR_PATHWAYS]
    level_ids = [unit_ids[i] for i in level_at]
    level_members = [unit_members[i] for i in level_at]

    print(f"AREAS LAYER, CORRECTED (rec2fix) from {args.frozen}")
    print(f"  units {len(unit_ids)}: {len(anchor_at)} anchors over {r2.ANCHOR_PATHWAYS} pathways, "
          f"{len(level_at)} clustered at level 2")
    for i in sorted(anchor_at, key=lambda j: -len(unit_members[j])):
        print(f"    ANCHOR {unit_ids[i]:<12} {len(unit_members[i]):>5} pathways")

    keys, vectors = load_centred(args.space, args.data / "pathways.tsv")
    centroids = rt.unit_centroids(level_members, keys, vectors)

    if args.estimate:
        clock = time.perf_counter()
        probe = rt.side(centroids, len(level_ids),
                        rt.subsample_rows(len(level_ids), args.runs), rt.THETA_MATCH)
        one = time.perf_counter() - clock
        sides = 1 + len(r2.CALIBRATION_SEEDS) + len(r2.HELDOUT_SEEDS)
        total = sides * one * 1.25 + 300
        print("\nTIMED ESTIMATE (one real side actually run)")
        print(f"  one side: {one:.1f}s for {len(probe.rows()):,} candidates")
        print(f"  {sides} sides: {sides * one / 60:.1f} min")
        print(f"  plus consensus and repair on union sets, the combined structure over about "
              f"{len(level_ids) + len(anchor_at) + 350:,} nodes, and the report: "
              f"about {total / 60:.0f} min")
        print("  WELL UNDER the 3 h ceiling." if total < 10800 else "  OVER 3 h: STOP.")
        return 0

    clock = time.perf_counter()
    print(f"\nLEVEL 2 on {len(level_ids)} units; same-theme {rt.THETA_SAME} and collapse "
          f"{rt.COLLAPSE_SHARE} on UNION pathway sets; matching {rt.THETA_MATCH} on units",
          flush=True)
    got = build_areas(centroids, level_members, args.runs)
    area_units = [[level_at[i] for i in rows] for rows in got["unit_indices"]]
    print(f"  level 2: {len(got['pathway_members'])} areas", flush=True)

    print("\nTHE COMBINED STRUCTURE", flush=True)
    comb = combine(got["pathway_members"], area_units, got["supports"], unit_ids, unit_members,
                   unit_support, anchor_at, level_at)

    ids, kinds, units = comb["ids"], comb["kinds"], comb["units"]
    view, edges, closure = comb["view"], comb["edges"], comb["closure"]
    held = {ids[node]: comb["members"][p] for p, node in enumerate(comb["alive"])}
    parents_of = {ids[view[c]]: [ids[view[p]] for p in np.flatnonzero(edges[c])]
                  for c in range(len(view))}
    children_of: dict[str, list[str]] = {ids[node]: [] for node in view}
    for child, above in parents_of.items():
        for parent in above:
            children_of[parent].append(child)
    roots = [ids[node] for position, node in enumerate(view) if not edges[position].any()]
    counts = [len(children_of[ids[node]]) for node in view]
    median = int(np.median(counts)) if counts else 0
    print(f"  view: {len(view):,} nodes, {len(roots)} roots, "
          f"{int(edges.sum()):,} direct edges, {int(closure.sum()):,} containment pairs; "
          f"children max {max(counts, default=0)}, median {median}", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "anchors.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "size", "support", "children"])
        writer.writeheader()
        for i in sorted(anchor_at, key=lambda j: -len(unit_members[j])):
            node = unit_ids[i]
            writer.writerow({"node": node, "size": len(unit_members[i]),
                             "support": nodes[node]["support"] if node in nodes else "",
                             "children": nodes[node]["children"] if node in nodes else ""})

    giant_ids = {ids[node] for node in comb["giants"]}
    universe = len({key for one in unit_members for key in one})
    with (args.out / "giants.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "n_units", "support", "share_of_universe"])
        writer.writeheader()
        for node in sorted(comb["giants"], key=lambda i: -len(held[ids[i]])):
            writer.writerow({
                "node": ids[node], "size": len(held[ids[node]]), "n_units": len(units[node]),
                "support": round(comb["support"][node], 6),
                "share_of_universe": round(len(held[ids[node]]) / universe, 4)})

    with (args.out / "areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "kind", "level", "size", "n_units", "support", "giant",
                        "in_view", "parents", "children"])
        writer.writeheader()
        for node in comb["alive"]:
            name = ids[node]
            inview = name not in giant_ids
            writer.writerow({
                "node": name, "kind": kinds[node],
                "level": 2 if kinds[node] == "area" else 1,
                "size": len(held[name]), "n_units": len(units[node]),
                "support": round(comb["support"][node], 6),
                "giant": "true" if name in giant_ids else "",
                "in_view": "true" if inview else "",
                "parents": " ".join(sorted(parents_of.get(name, []))),
                "children": " ".join(sorted(children_of.get(name, [])))})

    with (args.out / "area_members.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("node\tkey\n")
        for node in comb["alive"]:
            if kinds[node] != "area":
                continue
            for key in held[ids[node]]:
                handle.write(f"{ids[node]}\t{key}\n")

    with (args.out / "area_edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for child in range(len(view)):
            for parent in np.flatnonzero(edges[child]):
                handle.write(f"{ids[view[parent]]}\t{ids[view[child]]}\n")
    with (args.out / "closure.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for child in range(len(view)):
            for parent in np.flatnonzero(closure[child]):
                handle.write(f"{ids[view[parent]]}\t{ids[view[child]]}\n")

    o50_parents = {node: set(row["parents"].split()) for node, row in nodes.items()}
    with (args.out / "o50_nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "size", "support", "parents", "children"])
        writer.writeheader()
        for node, row in sorted(nodes.items()):
            if node in o50_giants:
                continue
            writer.writerow({
                "node": node, "size": len(members[node]), "support": row["support"],
                "parents": " ".join(sorted(o50_parents[node] - o50_giants)),
                "children": " ".join(
                    sorted(c for c in row["children"].split() if c not in o50_giants))})

    payload = {
        "frozen": str(args.frozen), "o50_giants": sorted(o50_giants), "giant_only": giant_only,
        "loose": loose, "unit_ids": unit_ids,
        "unit_pathways": [sorted(one) for one in unit_members],
        "unit_support": unit_support,
        "anchor_ids": [unit_ids[i] for i in anchor_at],
        "level_unit_ids": level_ids,
        "level2": {
            "n_units_in": len(level_ids),
            "node_ids": [ids[i] for i, kind in enumerate(kinds) if kind == "area"],
            "pathway_members": got["pathway_members"],
            "unit_ids_per_area": [[unit_ids[u] for u in rows] for rows in area_units],
            "supports": got["supports"], "floors": got["floors"], "confirmed": got["confirmed"],
            "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
            "n_after_consensus": got["n_after_consensus"], "seconds": got["seconds"],
            "repair": got["repair"],
        },
        "combined": {
            "ids": ids, "kinds": kinds,
            "units_per_node": [[unit_ids[u] for u in rows] for rows in units],
            "support": comb["support"],
            "alive": [ids[i] for i in comb["alive"]],
            "giants": sorted(giant_ids),
            "view": [ids[i] for i in view],
            "roots": roots,
            "parents": parents_of, "children": children_of,
            "seams": comb["seams"], "collapsed": comb["collapsed"], "merged": comb["merged"],
            "rounds": comb["rounds"],
            "n_direct_edges": int(edges.sum()), "n_closure_pairs": int(closure.sum()),
        },
        "seconds": round(time.perf_counter() - clock, 1),
    }
    (args.out / "levels.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")

    manifest = {
        "method": "v0.4 areas layer, corrected (rec2fix)",
        "built_from": str(args.frozen),
        "declared": "DECISIONS, 2026-10-15, before any result; a corrected re-run of prompt 36",
        "corrections_to_rec2": [
            "an area's pathway set IS the union of its units' pathways, asserted after consensus "
            "and after the joint fixed point",
            "the units are carried through consensus in event order, and a superseded candidate's "
            "units are not credited to its winner",
            "one combined node set -- areas, anchors and units -- with the merge and collapse "
            "rules applied to every pair",
            "edges are the transitive reduction; the closure is written separately",
            f"areas over {GIANT_AREA} pathways are giants and are kept out of the view",
        ],
        "reused_from_rec2": [
            "the unit rule and the 661 units", "the 6 anchors over 200 pathways",
            f"{rt.RUNS} Ward runs at subsample {rt.SUBSAMPLE}, master seed {rt.MASTER_SEED}",
            f"{len(r2.CALIBRATION_SEEDS)} calibration and {len(r2.HELDOUT_SEEDS)} held-out "
            f"scrambles to the {r2.FLOOR_TARGET} target with no minimum",
        ],
        "o50_giants_excluded": sorted(o50_giants),
        "containment": "strict subset over all members, which is O50's own definition",
        "n_units": len(unit_ids), "n_anchors": len(anchor_at), "n_level2_units": len(level_at),
        "anchors": {unit_ids[i]: len(unit_members[i]) for i in anchor_at},
        "runs": args.runs, "subsample": rt.SUBSAMPLE, "master_seed": rt.MASTER_SEED,
        "theta_match": rt.THETA_MATCH, "theta_match_space": "unit membership",
        "theta_same": rt.THETA_SAME, "theta_same_space": "union pathway sets",
        "collapse_share": rt.COLLAPSE_SHARE, "collapse_space": "union pathway sets",
        "survivor": rt.SURVIVOR, "joint_fixed_point": True,
        "giant_area": GIANT_AREA,
        "floor_target": r2.FLOOR_TARGET, "floor_minimum": "none",
        "calibration_seeds": list(r2.CALIBRATION_SEEDS),
        "heldout_seeds": list(r2.HELDOUT_SEEDS),
        "caps": {"per_stratum": r2.CAP_STRATUM, "overall": r2.CAP_OVERALL},
        "level2": {"n_units_in": len(level_at), "n_areas": len(got["pathway_members"]),
                   "floors": got["floors"], "confirmed": got["confirmed"],
                   "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
                   "n_after_consensus": got["n_after_consensus"],
                   "seconds": got["seconds"], "repair": got["repair"]},
        "combined": {
            "n_nodes": len(ids), "n_alive": len(comb["alive"]), "n_giants": len(giant_ids),
            "n_view": len(view), "n_roots": len(roots),
            "n_collapsed": len(comb["collapsed"]), "n_merged": len(comb["merged"]),
            "n_seam_events": sum(1 for e in comb["seams"] if e["seam"]),
            "n_direct_edges": int(edges.sum()), "n_closure_pairs": int(closure.sum()),
            "children_max": max(counts, default=0),
            "rounds": comb["rounds"],
        },
        "seconds": round(time.perf_counter() - clock, 1),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                            encoding="utf-8")
    print(f"\n  -> {args.out}  ({time.perf_counter() - clock:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
