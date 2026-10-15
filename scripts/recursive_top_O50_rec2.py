#!/usr/bin/env python3
"""Areas, second and last try: anchors, and overlap measured on pathways.

Declared 15 Oct 2026 before any result, copied verbatim into DECISIONS. **Adopts nothing.** If this
fails its criteria there is no third try, and the working view becomes O50 with the giants dropped
and about 660 flat roots.

Prompt 34 built areas and failed: two FDR strata over the cap, three roots holding 2,651-3,053
pathways, and a top level so overlapping that a pathway sat in a median of 3 of the 30 roots, with
five root pairs sharing at least half their pathways. The reviewer's two causes, and the two changes
they imply -- **both post hoc, and labelled so wherever they are reported**:

**(a) Overlap was measured on the wrong sets.** The same-theme cutoff ran on *unit* sets while units
themselves share pathways, so two areas built from different units could hold mostly the same
pathways. Here the cutoff (0.50, consensus and the stale pass) and chain collapse (0.85) run on
**pathway** sets -- the union of a candidate's units' members. Recurrence matching stays at 0.70 on
unit membership, because that is a different question: did this grouping of units recur.

**(b) Area-sized units were clustered as ordinary units.** The themes over 200 pathways have
generic centroids and joined several areas at once -- n01027 was in all three bag roots. Here every
unit over 200 pathways is an **anchor**: a finished area, a root, and not clustered at all.

Everything else is prompt 34's configuration, and its code is reused rather than copied:
:mod:`recursive_top_O50` supplies the unit rule, the centroids, the subsample scheme and the side
builder. Usage::

    uv run scripts/recursive_top_O50_rec2.py --estimate
    uv run scripts/recursive_top_O50_rec2.py
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

#: A unit this large is an anchor: a finished area, never clustered. POST HOC (reviewer, 15 Oct).
ANCHOR_PATHWAYS = 200

#: Floors: 20 calibration scrambles and 4 held out, to the cal8 target. POST HOC: prompt 34 used 10
#: and 2, and two strata breached the held-out cap on 13 and 96 real candidates. More seeds make the
#: held-out estimate less coarse; they do not loosen the caps, which are unchanged.
CALIBRATION_SEEDS = tuple(range(3001, 3021))
HELDOUT_SEEDS = (4002, 4003, 4004, 4005)
FLOOR_TARGET = 0.008

#: The caps, unchanged from v0.4.
CAP_OVERALL = 0.01
CAP_STRATUM = 0.02


def pathway_space(unit_members: Sequence[set[str]]) -> tuple[list[str], dict[str, int]]:
    """A stable index over every pathway any unit holds.

    Args:
        unit_members: Member keys per unit.

    Returns:
        ``(keys_in_index_order, key_to_index)``.
    """
    keys = sorted({key for held in unit_members for key in held})
    return keys, {key: i for i, key in enumerate(keys)}


def as_pathway_blocks(
    unit_blocks: Sequence[np.ndarray],
    unit_members: Sequence[set[str]],
    index: dict[str, int],
    width: int,
) -> list[np.ndarray]:
    """Each candidate's pathway bitset: the union of its units' members.

    This is change (a). The candidate still *is* a set of units -- that is what recurred -- but
    whether two candidates are the same theme, and whether one is nested in another, is decided on
    what they actually hold.

    Args:
        unit_blocks: One unit bitset per candidate.
        unit_members: Member keys per unit.
        index: Pathway key to bit position.
        width: Bitset width in bits.

    Returns:
        One pathway bitset per candidate.
    """
    from thema.ontology import bitset as bits

    out = []
    for block in unit_blocks:
        held: set[int] = set()
        for unit in bits.unpack(block):
            held.update(index[key] for key in unit_members[unit])
        out.append(bits.pack(sorted(held), width))
    return out


def build_level_on_pathways(
    matrix: np.ndarray,
    unit_members: Sequence[set[str]],
    runs: int,
    *,
    theta_match: float = rt.THETA_MATCH,
    theta_same: float = rt.THETA_SAME,
    collapse_share: float = rt.COLLAPSE_SHARE,
    report: bool = True,
) -> dict[str, object]:
    """Level 2, with the same-theme cutoff and chain collapse measured on pathway sets.

    The pipeline is prompt 34's up to the gate -- 200 Ward runs on 80% subsamples of units,
    recurrence matching on unit membership, the per-size floors -- and from the gate onwards every
    set comparison is on pathways.

    Both later stages only ever DROP candidates: consensus with ``stray=0`` keeps an accepted
    candidate's own bitset rather than unioning anything, and collapse and merge supersede. So a
    surviving area's unit membership is recovered by index, which is what makes it sound to run the
    comparisons in one space and report membership in the other.

    Args:
        matrix: Unit centroids for the units being clustered.
        unit_members: Member keys per unit, in the same order.
        runs: Trees per side.
        theta_match: Recurrence threshold, on unit membership.
        theta_same: The one same-theme cutoff, on pathway sets.
        collapse_share: Chain-collapse share, on pathway sets.
        report: Print progress.

    Returns:
        The level's areas, floors and timings.
    """
    from build_10770 import confirm
    from regate_floors import solve_to, without_minimum
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.recurrent import hasse, null_embeddings
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
    held: list[list[tuple[int, float]]] = []
    for label, seeds, sink in (("calibration", CALIBRATION_SEEDS, calib),
                               ("held out", HELDOUT_SEEDS, held)):
        for seed in seeds:
            got = rt.side(np.ascontiguousarray(null_embeddings(matrix, seed)), n,
                          rows_seq, theta_match)
            sink.append(got.rows())
            del got
        if report:
            print(f"    {label}: {len(seeds)} side(s) "
                  f"({time.perf_counter() - clock:.0f}s cumulative)", flush=True)

    solved = without_minimum(solve_to(real_rows, calib, FLOOR_TARGET))
    confirmed = confirm(real_rows, held, solved)
    if report:
        print("    floors " + ", ".join(
            f"{e['stratum']}:{e['effective']}" for e in solved), flush=True)

    keep = np.flatnonzero(gate(real_rows, solved)).tolist()
    unit_blocks = [real.blocks[i] for i in keep]
    supports = [float(real.supports[i]) for i in keep]
    inclusions = [real.selections[i] for i in keep]
    keys, index = pathway_space(unit_members)
    width = bits.words_for(len(keys)) * bits.WORD
    path_blocks = as_pathway_blocks(unit_blocks, unit_members, index, len(keys))
    if report:
        print(f"    {len(keep):,} through the gate; comparing on {len(keys):,} pathways "
              f"instead of {n} units", flush=True)

    verdict = consensus(path_blocks, supports, inclusions, width, stray=0.0, jaccard=theta_same)
    accepted = list(verdict.accepted)
    kept_path = [verdict.members[i] for i in range(len(accepted))]

    # Consensus does not only drop candidates: STRAY_FLOOR is 1, so a candidate whose extras beyond
    # an accepted one number at most one is INHERITED -- the accepted set grows by those members,
    # whatever `stray` is set to. In prompt 34 that growth happened in unit space and the area's
    # units were simply the grown set. Here it happens in pathway space, so a surviving area's unit
    # list has to be recovered from PROVENANCE instead of by index: its own units, plus the units of
    # every candidate superseded into it (followed transitively) and of every candidate whose
    # members it inherited. Taking the units by index alone makes the unit lists disagree with the
    # pathway sets, which a test catches.
    folded: dict[int, set[int]] = {c: {c} for c in accepted}
    beat = dict(verdict.superseded)
    for dropped, winner in beat.items():
        target = winner
        seen = {dropped}
        while target in beat and target not in seen:
            seen.add(target)
            target = beat[target]
        if target in folded:
            folded[target].add(dropped)
    for event in verdict.inherited:
        if event.parent in folded:
            folded[event.parent].add(event.source)
    kept_units = []
    for candidate in accepted:
        held: set[int] = set()
        for source in folded[candidate]:
            held.update(bits.unpack(unit_blocks[source]))
        kept_units.append(bits.pack(sorted(held), n))
    kept_support = [supports[c] for c in accepted]
    kept_incl = [inclusions[c] for c in accepted]
    if report:
        print(f"    consensus at {theta_same} on pathway sets: {len(keep):,} -> "
              f"{len(accepted):,}", flush=True)

    repaired = repair_joint(kept_path, kept_support, kept_incl, collapse_share, theta_same,
                            rt.SURVIVOR)
    dropped = set(repaired.collapsed) | set(repaired.merged)
    survivors = [i for i in range(len(accepted)) if i not in dropped]
    if len(survivors) != len(repaired.members):
        raise ValueError(
            f"cannot map {len(repaired.members)} repaired areas back to {len(survivors)} "
            "surviving positions; collapse or merge did not only drop rows"
        )
    final_units = [kept_units[i] for i in survivors]
    final_support = [repaired.supports[i] for i in range(len(repaired.members))]
    parents = hasse(repaired.members)
    if report:
        print(f"    joint fixed point at {collapse_share}/{theta_same} on pathway sets: "
              f"{len(accepted):,} -> {len(repaired.members):,}", flush=True)

    compared = [sorted(keys[b] for b in bits.unpack(block)) for block in repaired.members]
    units_each = [sorted(bits.unpack(block)) for block in final_units]
    # The two sets an area has: what every rule was applied to, and what its units actually hold.
    # They differ only by inherited strays, and the gap is reported rather than hidden.
    union_each = [sorted({k for u in rows for k in unit_members[u]}) for rows in units_each]
    gaps = [len(set(c) - set(u)) for c, u in zip(compared, union_each, strict=True)]
    if report:
        differing = sum(1 for g in gaps if g)
        print(f"    areas whose compared set exceeds their units' union: {differing} of "
              f"{len(gaps)}; median excess {int(np.median(gaps))}, max {max(gaps, default=0)}",
              flush=True)
    return {
        "pathway_members": compared,
        "units_union": union_each,
        "inherited_excess": gaps,
        "unit_indices": units_each,
        "supports": [float(s) for s in final_support],
        "parents": [list(a) for a in parents],
        "floors": solved,
        "confirmed": confirmed,
        "n_candidates": len(real_rows),
        "n_gated": len(keep),
        "n_after_consensus": len(accepted),
        "seconds": round(time.perf_counter() - clock, 1),
        "repair": {"n_collapsed": len(repaired.collapsed), "n_merged": len(repaired.merged),
                   "rounds": repaired.rounds},
    }


def main(argv: list[str] | None = None) -> int:
    """Build the anchored recursive top, or just estimate it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--space", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2"))
    parser.add_argument("--runs", type=int, default=rt.RUNS)
    parser.add_argument("--estimate", action="store_true")
    args = parser.parse_args(argv)

    from thema.ontology.universe import load_centred

    nodes, members = rt.read_build(args.frozen)
    unit_themes, giants, giant_only, loose = rt.units_of(nodes, members)
    unit_ids = list(unit_themes) + [f"loose:{key}" for key in loose]
    unit_members = [members[node] for node in unit_themes] + [{key} for key in loose]

    anchor_at = [i for i, held in enumerate(unit_members) if len(held) > ANCHOR_PATHWAYS]
    rest_at = [i for i, held in enumerate(unit_members) if len(held) <= ANCHOR_PATHWAYS]
    anchors = [unit_ids[i] for i in anchor_at]
    level_ids = [unit_ids[i] for i in rest_at]
    level_members = [unit_members[i] for i in rest_at]

    print(f"ANCHORED RECURSIVE TOP (rec2) from {args.frozen}")
    print(f"  units {len(unit_ids)}: {len(anchors)} anchors over {ANCHOR_PATHWAYS} pathways, "
          f"{len(level_ids)} clustered at level 2")
    for i in sorted(anchor_at, key=lambda j: -len(unit_members[j])):
        print(f"    ANCHOR {unit_ids[i]:<12} {len(unit_members[i]):>5} pathways")

    keys, vectors = load_centred(args.space, args.data / "pathways.tsv")
    centroids = rt.unit_centroids(level_members, keys, vectors)

    if args.estimate:
        clock = time.perf_counter()
        probe = rt.side(centroids, len(level_ids),
                        rt.subsample_rows(len(level_ids), args.runs), rt.THETA_MATCH)
        one = time.perf_counter() - clock
        sides = 1 + len(CALIBRATION_SEEDS) + len(HELDOUT_SEEDS)
        total = sides * one * 1.25 + 180
        print("\nTIMED ESTIMATE (one real side actually run)")
        print(f"  one side: {one:.1f}s for {len(probe.rows()):,} candidates")
        print(f"  {sides} sides: {sides * one / 60:.1f} min")
        print(f"  plus consensus and repair on {len({k for h in level_members for k in h}):,}-bit "
              f"pathway sets, mapping and the report: about {total / 60:.0f} min")
        print("  WELL UNDER the 3 h ceiling." if total < 10800 else "  OVER 3 h: STOP.")
        return 0

    print(f"\nLEVEL 2 on {len(level_ids)} units; same-theme {rt.THETA_SAME} and collapse "
          f"{rt.COLLAPSE_SHARE} on PATHWAY sets; matching {rt.THETA_MATCH} on units", flush=True)
    got = build_level_on_pathways(centroids, level_members, args.runs)
    node_ids = [f"b2_{i:05d}" for i in range(len(got["pathway_members"]))]
    child_units = [[level_ids[i] for i in rows] for rows in got["unit_indices"]]
    roots = [i for i, above in enumerate(got["parents"]) if not above]
    print(f"  level 2: {len(node_ids)} areas, {len(roots)} area roots, "
          f"{len(anchors)} anchors -> {len(roots) + len(anchors)} roots in all", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    anchor_rows = [
        {"node": unit_ids[i], "size": len(unit_members[i]),
         "support": nodes[unit_ids[i]]["support"] if unit_ids[i] in nodes else "",
         "children": nodes[unit_ids[i]]["children"] if unit_ids[i] in nodes else ""}
        for i in sorted(anchor_at, key=lambda j: -len(unit_members[j]))
    ]
    with (args.out / "anchors.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "size", "support", "children"])
        writer.writeheader()
        writer.writerows(anchor_rows)

    area_rows = []
    for position, node_id in enumerate(node_ids):
        kids = [node_ids[j] for j, above in enumerate(got["parents"]) if position in above]
        area_rows.append({
            "node": node_id, "level": 2,
            "size": len(got["pathway_members"][position]),
            "n_units": len(child_units[position]),
            "support": round(got["supports"][position], 6),
            "parents": " ".join(node_ids[j] for j in got["parents"][position]),
            "children": " ".join(kids),
        })
    with (args.out / "areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "level", "size", "n_units", "support", "parents", "children"])
        writer.writeheader()
        writer.writerows(area_rows)
    with (args.out / "area_members.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("node\tkey\n")
        for position, node_id in enumerate(node_ids):
            for key in got["pathway_members"][position]:
                handle.write(f"{node_id}\t{key}\n")
    with (args.out / "area_edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for position, node_id in enumerate(node_ids):
            for child in child_units[position]:
                handle.write(f"{node_id}\t{child}\n")
    o50_parents = {node: set(row["parents"].split()) for node, row in nodes.items()}
    with (args.out / "o50_nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "size", "support", "parents", "children"])
        writer.writeheader()
        for node, row in sorted(nodes.items()):
            if node in giants:
                continue
            writer.writerow({
                "node": node, "size": len(members[node]), "support": row["support"],
                "parents": " ".join(sorted(o50_parents[node] - giants)),
                "children": " ".join(
                    sorted(c for c in row["children"].split() if c not in giants))})

    payload = {
        "frozen": str(args.frozen), "giants": sorted(giants), "giant_only": giant_only,
        "nongiant_roots": len(unit_themes) - len(giant_only), "loose": loose,
        "anchors": anchors, "anchor_sizes": {unit_ids[i]: len(unit_members[i]) for i in anchor_at},
        "unit_ids": unit_ids,
        "unit_pathways": [sorted(held) for held in unit_members],
        "level_unit_ids": level_ids,
        "levels": [{
            "level": 2, "n_units_in": len(level_ids), "node_ids": node_ids,
            "pathway_members": got["pathway_members"],
            "units_union": got["units_union"],
            "inherited_excess": got["inherited_excess"],
            "child_unit_ids": child_units,
            "parents": got["parents"], "supports": got["supports"],
            "floors": got["floors"], "confirmed": got["confirmed"],
            "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
            "n_after_consensus": got["n_after_consensus"], "seconds": got["seconds"],
            "repair": got["repair"], "roots": roots,
        }],
    }
    (args.out / "levels.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    manifest = {
        "method": "v0.4 recursive top, anchored (rec2)",
        "built_from": str(args.frozen),
        "declared": "DECISIONS, 2026-10-15, before any result; adopts nothing",
        "post_hoc_changes": [
            f"anchors: every unit over {ANCHOR_PATHWAYS} pathways is a finished area",
            "the same-theme cutoff and chain collapse are measured on PATHWAY sets",
            f"{len(CALIBRATION_SEEDS)} calibration and {len(HELDOUT_SEEDS)} held-out scrambles",
        ],
        "giants_excluded": sorted(giants),
        "n_units": len(unit_ids), "n_anchors": len(anchors), "n_level2_units": len(level_ids),
        "anchors": {unit_ids[i]: len(unit_members[i]) for i in anchor_at},
        "runs": args.runs, "subsample": rt.SUBSAMPLE, "master_seed": rt.MASTER_SEED,
        "theta_match": rt.THETA_MATCH, "theta_match_space": "unit membership",
        "theta_same": rt.THETA_SAME, "theta_same_space": "pathway sets",
        "collapse_share": rt.COLLAPSE_SHARE, "collapse_space": "pathway sets",
        "survivor": rt.SURVIVOR, "joint_fixed_point": True, "containment": "strict, on pathways",
        "floor_target": FLOOR_TARGET, "floor_minimum": "none",
        "calibration_seeds": list(CALIBRATION_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "caps": {"per_stratum": CAP_STRATUM, "overall": CAP_OVERALL},
        "levels": [{"level": 2, "n_units_in": len(level_ids), "n_nodes": len(node_ids),
                    "n_area_roots": len(roots), "n_roots_with_anchors": len(roots) + len(anchors),
                    "floors": got["floors"], "confirmed": got["confirmed"],
                    "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
                    "n_after_consensus": got["n_after_consensus"],
                    "seconds": got["seconds"], "repair": got["repair"]}],
        "n_areas": len(node_ids),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                            encoding="utf-8")
    print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
