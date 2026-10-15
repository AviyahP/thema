#!/usr/bin/env python3
"""The recursive top level: THEMA applied to its own themes, on the adopted O50 build.

Declared 15 Oct 2026 before any result, copied verbatim into DECISIONS. **Adopts nothing.**

O50 has no area layer. Four roots are giant grab-bags holding 97% of the pathways, 476 themes have
only giants as parents, and the other 184 roots are mostly small -- 168 of them 50 members or fewer.
So for a fifth of the pathways the largest real theme above them has 50 members or fewer, and there
is nothing between a theme and a bag.

This runs **the same algorithm one level up**: the units are the themes that have no non-giant
parent, each represented by the normalised mean of its members' vectors, and level 2 is the O50
configuration unchanged -- 200 Ward runs on 80% subsamples, recurrence matching 0.70, one same-theme
cutoff of 0.50 in consensus and the stale pass, the joint fixed point with chain collapse at 0.85,
strict containment, and floors calibrated on **unit** scrambles to a 0.008 target. A hand-chosen k
was the 8 Oct one-off; here k comes from the data.

**The giants are never units and never joined.** They stay in the O50 freeze only. The frozen build
is read-only input; nothing here writes to ``data/ontology/frozen/``.

Usage::

    uv run scripts/recursive_top_O50.py --estimate     # units and a timed estimate, no build
    uv run scripts/recursive_top_O50.py                # build, map back, write the report data
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import numpy as np

#: A theme this large is a grab-bag: never a unit, never joined to the combined DAG.
GIANT = 1000

#: Level 2's configuration, which is O50's.
RUNS = 200
SUBSAMPLE = 0.8
THETA_MATCH = 0.70
THETA_SAME = 0.50
COLLAPSE_SHARE = 0.85
SURVIVOR = "support"

#: Floors are calibrated on unit scrambles, to the cal8 target, with no 0.33 minimum.
CALIBRATION_SEEDS = tuple(range(3001, 3011))
HELDOUT_SEEDS = (4001, 4002)
FLOOR_TARGET = 0.008

#: The subsample scheme, the same one universe L uses: one sorted draw per row from a single
#: generator seeded once, so row i is tree i on every side, real and scrambled alike.
MASTER_SEED = 20261015

#: Where the recursion stops: a top level between these is what the declaration asks for.
MIN_ROOTS = 20
MAX_ROOTS = 60

#: Guard on the recursion, far above any plausible number of levels.
MAX_LEVELS = 6


def read_build(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
    """A build's node rows and member sets.

    Args:
        path: A build directory.

    Returns:
        ``(nodes, members)``.
    """
    with (path / "nodes.tsv").open(encoding="utf-8") as handle:
        nodes = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return nodes, dict(members)


def units_of(
    nodes: dict[str, dict[str, str]], members: dict[str, set[str]]
) -> tuple[list[str], set[str], list[str], list[str]]:
    """The level-2 units: every non-giant theme with no non-giant parent, plus loose pathways.

    A theme whose only parents are giants is a root of the real hierarchy even though the DAG gives
    it a parent, which is exactly why there is no area layer to begin with.

    Args:
        nodes: Node rows.
        members: Node to member keys.

    Returns:
        ``(unit_themes, giants, giant_only, loose_pathways)``.
    """
    giants = {node for node, keys in members.items() if len(keys) > GIANT}
    parents = {node: set(row["parents"].split()) for node, row in nodes.items()}
    unit_themes = sorted(
        node for node in nodes if node not in giants and not (parents[node] - giants)
    )
    giant_only = sorted(
        node for node in nodes
        if node not in giants and parents[node] and not (parents[node] - giants)
    )
    held = {key for node, keys in members.items() if node not in giants for key in keys}
    every = {key for keys in members.values() for key in keys}
    return unit_themes, giants, giant_only, sorted(every - held)


def unit_centroids(
    unit_members: Sequence[set[str]], keys: Sequence[str], vectors: np.ndarray
) -> np.ndarray:
    """One unit vector per unit: the normalised mean of its members' normalised rows.

    Rows are normalised first and the mean normalised after, which is the order the build's own
    member centroids use; a mean of unnormalised rows weights long vectors more.

    Args:
        unit_members: Member keys per unit.
        keys: Embedding row keys, in row order.
        vectors: The matrix those keys index.

    Returns:
        An ``(n_units, dim)`` float32 array of unit vectors.

    Raises:
        ValueError: If a unit has no member with a vector, which would leave a zero row that Ward
            cannot use and that ``distances`` refuses.
    """
    matrix = np.asarray(vectors, dtype=np.float32)
    matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
    row_of = {key: index for index, key in enumerate(keys)}
    out = np.zeros((len(unit_members), matrix.shape[1]), dtype=np.float32)
    for position, member_keys in enumerate(unit_members):
        rows = [row_of[key] for key in sorted(member_keys) if key in row_of]
        if not rows:
            raise ValueError(f"unit {position} has no member with a vector")
        centre = matrix[rows].mean(0)
        out[position] = centre / (np.linalg.norm(centre) + 1e-9)
    return out


def subsample_rows(n: int, runs: int, subsample: float = SUBSAMPLE) -> list[np.ndarray]:
    """The subsample sequence, drawn once and shared by every side.

    Args:
        n: Number of units.
        runs: How many rows.
        subsample: Fraction drawn.

    Returns:
        One sorted index array per row.
    """
    take = int(np.ceil(subsample * n))
    rng = np.random.default_rng(MASTER_SEED)
    return [np.sort(rng.choice(n, take, replace=False)) for _ in range(runs)]


def side(
    matrix: np.ndarray, n: int, rows: Sequence[np.ndarray], theta_match: float
) -> object:
    """One side's material: trees over the given subsamples, then match, complete and absorb.

    Args:
        matrix: The unit-vector matrix for this side.
        n: Number of units.
        rows: The shared subsample sequence.
        theta_match: Recurrence threshold.

    Returns:
        A ``v04.Material``.
    """
    from thema.cluster import distances
    from thema.ontology.recurrent import tree_from_subset
    from thema.ontology.v04 import MIN_SIZE, material

    full = distances(matrix)
    runs = [tree_from_subset(matrix, n, row, MIN_SIZE, "ward", full) for row in rows]
    return material(runs, n, theta_match=theta_match)


def build_level(
    matrix: np.ndarray,
    n: int,
    runs: int,
    *,
    theta_match: float = THETA_MATCH,
    theta_same: float = THETA_SAME,
    collapse_share: float = COLLAPSE_SHARE,
    target: float = FLOOR_TARGET,
    calibration: Sequence[int] = CALIBRATION_SEEDS,
    heldout: Sequence[int] = HELDOUT_SEEDS,
    report: bool = True,
) -> dict[str, object]:
    """Run the O50 configuration on one matrix of units, floors and all.

    Args:
        matrix: Unit vectors.
        n: Number of units.
        runs: Tree count per side.
        theta_match: Recurrence threshold.
        theta_same: The one same-theme cutoff, for consensus and the stale pass alike.
        collapse_share: Chain-collapse share.
        target: Calibration FDR target for the floors.
        calibration: Scramble seeds the floors are solved on.
        heldout: Scramble seeds the floors are confirmed on, read once.
        report: Print progress.

    Returns:
        ``members``, ``supports``, ``parents``, ``floors``, ``confirmed`` and timings.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from build_10770 import confirm
    from regate_floors import solve_to, without_minimum
    from thema.ontology.recurrent import hasse, null_embeddings
    from thema.ontology.repair import repair_joint
    from thema.ontology.v04 import build as v04_build

    clock = time.perf_counter()
    rows = subsample_rows(n, runs)
    real = side(matrix, n, rows, theta_match)
    real_rows = real.rows()
    real_seconds = time.perf_counter() - clock
    if report:
        print(f"    real side: {len(real_rows):,} candidates ({real_seconds:.0f}s)", flush=True)

    scramble_rows: list[list[tuple[int, float]]] = []
    heldout_rows: list[list[tuple[int, float]]] = []
    for label, seeds, sink in (("calibration", calibration, scramble_rows),
                               ("held out", heldout, heldout_rows)):
        for seed in seeds:
            got = side(np.ascontiguousarray(null_embeddings(matrix, seed)), n, rows, theta_match)
            sink.append(got.rows())
            del got
        if report:
            print(f"    {label}: {len(seeds)} scramble side(s) "
                  f"({time.perf_counter() - clock:.0f}s cumulative)", flush=True)

    solved = without_minimum(solve_to(real_rows, scramble_rows, target))
    confirmed = confirm(real_rows, heldout_rows, solved)
    if report:
        print("    floors " + ", ".join(
            f"{entry['stratum']}:{entry['effective']}" for entry in solved), flush=True)

    built = v04_build(real, solved, theta_same=theta_same)
    repaired = repair_joint(built.members, built.supports, built.inclusions,
                            collapse_share, theta_same, SURVIVOR)
    parents = hasse(repaired.members)
    if report:
        print(f"    {len(built.members):,} after consensus -> {len(repaired.members):,} "
              f"after the joint fixed point", flush=True)
    return {
        "members": repaired.members,
        "supports": repaired.supports,
        "parents": parents,
        "floors": solved,
        "confirmed": confirmed,
        "n_candidates": len(real_rows),
        "n_after_consensus": len(built.members),
        "seconds": round(time.perf_counter() - clock, 1),
        "real_side_seconds": round(real_seconds, 1),
        "repair": {
            "n_collapsed": len(repaired.collapsed),
            "n_merged": len(repaired.merged),
            "rounds": repaired.rounds,
        },
    }


def unpack(blocks: Sequence[np.ndarray]) -> list[list[int]]:
    """Member indices per node.

    Args:
        blocks: Member bitsets.

    Returns:
        Sorted index lists.
    """
    from thema.ontology import bitset as bits

    return [sorted(bits.unpack(block)) for block in blocks]


def main(argv: list[str] | None = None) -> int:
    """Build the recursive top, or just estimate it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--space", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--data", type=Path, default=Path("data"),
                        help="the data directory, for the pathways table the loader verifies "
                             "the embeddings against")
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec"))
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--estimate", action="store_true",
                        help="report the units and a timed estimate, then stop")
    args = parser.parse_args(argv)

    nodes, members = read_build(args.frozen)
    unit_themes, giants, giant_only, loose = units_of(nodes, members)
    unit_ids = list(unit_themes) + [f"loose:{key}" for key in loose]
    unit_members = [members[node] for node in unit_themes] + [{key} for key in loose]
    n = len(unit_ids)

    print(f"UNITS from {args.frozen}")
    print(f"  themes {len(members):,}; giants over {GIANT:,} members: {len(giants)} "
          f"{sorted((len(members[g]) for g in giants), reverse=True)}")
    nongiant_roots = len(unit_themes) - len(giant_only)
    print(f"  units = {nongiant_roots} non-giant roots + {len(giant_only)} giant-only themes "
          f"+ {len(loose)} loose pathway(s) = {n}")
    sizes = sorted(len(keys) for keys in unit_members)
    print(f"  unit sizes in pathways: min {sizes[0]}, median {sizes[len(sizes) // 2]}, "
          f"max {sizes[-1]}; {sum(1 for s in sizes if s <= 50)} are 50 or fewer")
    covered = {key for keys in unit_members for key in keys}
    print(f"  pathways covered by the units: {len(covered):,} of "
          f"{len({k for v in members.values() for k in v}):,}")

    from thema.ontology.universe import load_centred

    keys, vectors = load_centred(args.space, args.data / "pathways.tsv")
    centroids = unit_centroids(unit_members, keys, vectors)
    print(f"  unit centroids: {centroids.shape} {centroids.dtype}; "
          f"row norms in [{np.linalg.norm(centroids, axis=1).min():.6f}, "
          f"{np.linalg.norm(centroids, axis=1).max():.6f}]")

    if args.estimate:
        clock = time.perf_counter()
        rows = subsample_rows(n, args.runs)
        probe = side(centroids, n, rows, THETA_MATCH)
        one = time.perf_counter() - clock
        sides = 1 + len(CALIBRATION_SEEDS) + len(HELDOUT_SEEDS)
        print("\nTIMED ESTIMATE (one real side actually run)")
        print(f"  one side: {one:.1f}s for {len(probe.rows()):,} candidates")
        print(f"  {sides} sides at level 2: {sides * one / 60:.1f} min")
        print(f"  plus consensus, repair, mapping and the report: call it "
              f"{(sides * one * 1.4 + 120) / 60:.0f} min")
        print(f"  a second level, if the top has over {MAX_ROOTS} roots, costs much less: "
              f"the unit count falls by about 7x")
        print("  WELL UNDER the 3 h ceiling." if sides * one * 1.4 + 120 < 10800
              else "  OVER the 3 h ceiling: STOP.")
        return 0

    print(f"\nLEVEL 2: {n} units, {args.runs} runs, theta_match {THETA_MATCH}, "
          f"same-theme {THETA_SAME}, collapse {COLLAPSE_SHARE}, joint fixed point", flush=True)
    levels: list[dict[str, object]] = []
    level_units = unit_ids
    level_unit_members = unit_members
    level_matrix = centroids
    level = 2
    while level <= MAX_LEVELS:
        got = build_level(level_matrix, len(level_units), args.runs)
        index_members = unpack(got["members"])  # type: ignore[arg-type]
        node_ids = [f"a{level}_{i:05d}" for i in range(len(index_members))]
        pathway_members = [
            sorted({key for i in rows for key in level_unit_members[i]})
            for rows in index_members
        ]
        roots = [i for i, above in enumerate(got["parents"]) if not above]  # type: ignore
        levels.append({
            "level": level,
            "n_units_in": len(level_units),
            "node_ids": node_ids,
            "unit_members": index_members,
            "pathway_members": pathway_members,
            "parents": [list(a) for a in got["parents"]],  # type: ignore[arg-type]
            "supports": [float(s) for s in got["supports"]],  # type: ignore
            "floors": got["floors"],
            "confirmed": got["confirmed"],
            "n_candidates": got["n_candidates"],
            "n_after_consensus": got["n_after_consensus"],
            "seconds": got["seconds"],
            "repair": got["repair"],
            "roots": roots,
            "child_unit_ids": [[level_units[i] for i in rows] for rows in index_members],
        })
        print(f"  level {level}: {len(node_ids)} nodes, {len(roots)} roots, "
              f"{got['seconds']}s", flush=True)
        if len(roots) <= MAX_ROOTS:
            print(f"  {len(roots)} roots is within {MIN_ROOTS}-{MAX_ROOTS}: stop recursing",
                  flush=True)
            break
        print(f"  {len(roots)} roots is over {MAX_ROOTS}: recursing on the roots only", flush=True)
        level_units = [node_ids[i] for i in roots]
        level_unit_members = [set(pathway_members[i]) for i in roots]
        level_matrix = unit_centroids(level_unit_members, keys, vectors)
        level += 1

    # ---- the combined DAG: the O50 nodes, plus the areas, plus area -> unit edges. The giants
    # are deliberately absent: they stay in the O50 freeze and are never joined here.
    args.out.mkdir(parents=True, exist_ok=True)
    o50_parents = {node: set(row["parents"].split()) for node, row in nodes.items()}
    unit_set = set(unit_ids)
    area_rows: list[dict[str, object]] = []
    area_members: list[tuple[str, str]] = []
    area_edges: list[tuple[str, str]] = []
    for entry in levels:
        ids = entry["node_ids"]
        for position, node_id in enumerate(ids):
            kids = [ids[j] for j, above in enumerate(entry["parents"]) if position in above]
            area_rows.append({
                "node": node_id,
                "level": entry["level"],
                "size": len(entry["pathway_members"][position]),
                "n_units": len(entry["child_unit_ids"][position]),
                "support": round(entry["supports"][position], 6),
                "parents": " ".join(ids[j] for j in entry["parents"][position]),
                "children": " ".join(kids),
            })
            for key in entry["pathway_members"][position]:
                area_members.append((node_id, key))
            # An area's edges go to the units it holds, but only to units it does not reach
            # through another area: a transitive edge would contradict the Hasse convention the
            # rest of the build follows.
            for child in entry["child_unit_ids"][position]:
                if child in unit_set or any(child == other for other in ids):
                    area_edges.append((node_id, child))

    with (args.out / "areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "level", "size", "n_units", "support", "parents", "children"])
        writer.writeheader()
        writer.writerows(area_rows)
    with (args.out / "area_members.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("node\tkey\n")
        for node_id, key in area_members:
            handle.write(f"{node_id}\t{key}\n")
    with (args.out / "area_edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for parent, child in area_edges:
            handle.write(f"{parent}\t{child}\n")
    # The O50 side of the combined DAG, copied so the folder stands alone, giants excluded.
    with (args.out / "o50_nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "support", "parents", "children"])
        writer.writeheader()
        for node, row in sorted(nodes.items()):
            if node in giants:
                continue
            writer.writerow({
                "node": node, "size": len(members[node]), "support": row["support"],
                "parents": " ".join(sorted(o50_parents[node] - giants)),
                "children": " ".join(
                    sorted(c for c in row["children"].split() if c not in giants)),
            })
    manifest = {
        "method": "v0.4 recursive top",
        "built_from": str(args.frozen),
        "declared": "DECISIONS, 2026-10-15, before any result; adopts nothing",
        "giants_excluded": sorted(giants),
        "n_units": n,
        "units": {"nongiant_roots": nongiant_roots, "giant_only": len(giant_only),
                  "loose_pathways": len(loose)},
        "unit_representation": "normalised mean of the members' L2-normalised rows in "
                               "vectors_leaves_centred (x2 universe)",
        "runs": args.runs, "subsample": SUBSAMPLE, "master_seed": MASTER_SEED,
        "theta_match": THETA_MATCH, "theta_same": THETA_SAME,
        "collapse_share": COLLAPSE_SHARE, "survivor": SURVIVOR,
        "joint_fixed_point": True, "containment": "strict",
        "floor_target": FLOOR_TARGET, "floor_minimum": "none",
        "calibration_seeds": list(CALIBRATION_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "levels": [
            {"level": e["level"], "n_units_in": e["n_units_in"], "n_nodes": len(e["node_ids"]),
             "n_roots": len(e["roots"]), "floors": e["floors"], "confirmed": e["confirmed"],
             "n_candidates": e["n_candidates"], "n_after_consensus": e["n_after_consensus"],
             "seconds": e["seconds"], "repair": e["repair"]}
            for e in levels
        ],
        "n_areas": len(area_rows),
        "n_area_edges": len(area_edges),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                            encoding="utf-8")
    payload = {
        "frozen": str(args.frozen),
        "space": str(args.space),
        "giants": sorted(giants),
        "giant_only": giant_only,
        "nongiant_roots": nongiant_roots,
        "loose": loose,
        "unit_ids": unit_ids,
        "unit_pathways": [sorted(keys) for keys in unit_members],
        "levels": [
            {k: v for k, v in entry.items() if k not in ("unit_members",)}
            for entry in levels
        ],
    }
    (args.out / "levels.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    print(f"\n  -> {args.out / 'levels.json'}")
    print("  sizes per level: " + ", ".join(
        f"L{e['level']} {len(e['node_ids'])} nodes" for e in levels))
    print(f"  children per node, top level: max "
          f"{max((len(r) for r in levels[-1]['child_unit_ids']), default=0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
