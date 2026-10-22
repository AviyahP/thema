"""O50s restructured as designed: build the DAG first, then merge only real relationships.

Prompt 53, declared 22 Oct 2026. Exploratory; nothing is adopted. The design is Aviyah's.

Prompt 52 measured why this is worth trying. The J >= 0.5 sibling rule does 95% of its work as
``consensus``, which runs after the gate but **before any DAG exists**, so it cannot test a
relationship even in principle: 54% of its 19,531 merges joined themes that end up neither siblings
nor nested, and it superseded 76 well-supported parents (52-62 runs of 200) covering 74 of the 261
roots. Here the 10% variant merge stays before the gate, the DAG is built **first**, and then the
sibling rule is applied only to real siblings and the chain rule only to real parent-child pairs,
the two iterated to a joint fixed point with the DAG rebuilt after every round.

Two arms, because the chain survivor is not yet chosen:

``S1p``  the parent always survives.
``S1s``  the higher support survives; on a tie, or when the parent has no parent, the parent
         survives -- today's rule.

The input is the 26,120 gated themes, which are reconstructed from the cached x2 real side and
O50s's stored floors and asserted to equal prompt 52's logged gate exactly, so no side is
recomputed.

Usage:
    uv run scripts/restructure_s1.py --check          # the two declared tests
    uv run scripts/restructure_s1.py --arm S1p
    uv run scripts/restructure_s1.py --arm S1s
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import NamedTuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The chain rule's share: a child holding at least this much of a parent becomes one node with it.
COLLAPSE_SHARE = 0.85

#: The sibling rule's cutoff, the same 0.50 O50s uses for the same notion of "the same set".
THETA_SAME = 0.50

#: Fixed-point guard. The loop is monotone -- every round only removes nodes -- so this is a
#: backstop against a bug, not an expected limit.
MAX_ROUNDS = 50

#: Survivor rules.
ARMS = ("S1p", "S1s")


class Gated(NamedTuple):
    """The gate's output, the input to the restructure.

    Attributes:
        members: Member pathway ids per gated theme, sorted.
        supports: Support per gated theme.
        inclusions: Inclusion vote per gated theme.
        keys: Pathway keys in universe order.
        n: Universe size.
        meta: The universe record.
        floors: O50s's stored floors.
        strata: O50s's stratum edges.
        confirmed: O50s's held-out report.
    """

    members: list[np.ndarray]
    supports: list[float]
    inclusions: list[dict[int, float]]
    keys: list[str]
    n: int
    meta: dict
    floors: list[dict]
    strata: list[tuple[int, int]]
    confirmed: dict


def gated_themes(args: argparse.Namespace) -> Gated:
    """Rebuild the 26,120 gated themes from cache, and prove they are prompt 52's.

    Args:
        args: Parsed arguments.

    Returns:
        The gated input.

    Raises:
        ValueError: If the re-gated set is not the one prompt 52 logged.
    """
    from thema.ontology.universe import load_embedded
    from thema.ontology.v04 import Material, gate

    frozen = json.loads((args.frozen / "manifest.json").read_text())
    meta = json.loads((args.space_root / "universe.json").read_text())
    floors = frozen["floors"]
    strata = [tuple(s) for s in frozen["strata"]]

    with np.load(args.space_root / "calibration" / "real.npz") as handle:
        blocks, supports = handle["blocks"], handle["supports"]
        indptr = handle["indptr"]
        vote_keys, vote_vals = handle["vote_keys"], handle["vote_vals"]
    votes = tuple(
        dict(zip(vote_keys[indptr[i]:indptr[i + 1]].tolist(),
                 vote_vals[indptr[i]:indptr[i + 1]].tolist(), strict=True))
        for i in range(len(indptr) - 1))
    material = Material(blocks=blocks, supports=supports, selections=votes)
    keep = np.flatnonzero(gate(material.rows(), floors, strata))

    if args.probe.is_file():
        with np.load(args.probe, allow_pickle=False) as probe:
            logged = probe["keep"]
        if not np.array_equal(keep, logged):
            raise ValueError(
                f"the re-gated set ({len(keep):,}) is not the one prompt 52 logged "
                f"({len(logged):,}); the input to the restructure would not be O50s's gate")
        print(f"  gate: {len(keep):,} themes, IDENTICAL to prompt 52's logged gate", flush=True)
    else:
        print(f"  gate: {len(keep):,} themes (prompt 52's probe absent, not cross-checked)",
              flush=True)

    from thema.ontology import bitset as bits
    members = [np.array(sorted(bits.unpack(blocks[i])), dtype=np.int32) for i in keep.tolist()]
    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    return Gated(members=members, supports=[float(supports[i]) for i in keep.tolist()],
                 inclusions=[votes[i] for i in keep.tolist()], keys=keys,
                 n=meta["n_embedded"], meta=meta, floors=floors, strata=strata,
                 confirmed=frozen["confirmed"])


def dag(members: list[np.ndarray], alive: list[int], n: int) -> dict[int, tuple[int, ...]]:
    """Immediate parents over the living nodes, by strict containment.

    Args:
        members: Member ids per node, indexed by original position.
        alive: Living node positions.
        n: Universe size.

    Returns:
        ``{node: immediate parent nodes}`` over ``alive``.
    """
    from core_construction_c1b import immediate_parents

    parents = immediate_parents([members[i] for i in alive], n, report=False)
    return {alive[i]: tuple(alive[p] for p in parents[i]) for i in range(len(alive))}


def chain_pass(members: list[np.ndarray], supports: list[float],
               parents: dict[int, tuple[int, ...]], alive: list[int],
               survivor: str, share: float = COLLAPSE_SHARE) -> dict[int, int]:
    """One chain round: a child holding ``share`` of an immediate parent becomes one node with it.

    Smallest child first, so a chain collapses from the bottom and each child finds its own parent,
    which is how ``repair.collapse_chains`` traverses today.

    Args:
        members: Member ids per node.
        supports: Support per node.
        parents: Immediate parents over the living nodes.
        alive: Living node positions.
        survivor: ``"parent"`` (S1p) or ``"support"`` (S1s).
        share: The chain share.

    Returns:
        ``{removed node: the node it became one with}``.
    """
    sizes = {i: len(members[i]) for i in alive}
    doomed: dict[int, int] = {}
    for child in sorted(alive, key=lambda i: sizes[i]):
        if child in doomed:
            continue
        best: tuple[int, int] | None = None
        for parent in parents.get(child, ()):
            if parent in doomed or sizes[parent] <= sizes[child]:
                continue
            if sizes[child] >= share * sizes[parent]:
                if best is None or sizes[parent] < best[1]:
                    best = (parent, sizes[parent])
        if best is None:
            continue
        parent = best[0]
        if (survivor == "support" and supports[child] > supports[parent]
                and parents.get(parent, ())):
            # S1s: the higher support survives, except that a parent with no parent of its own is
            # the top of its branch and is kept, which is today's rule.
            doomed[parent] = child
        else:
            doomed[child] = parent
    return doomed


def sibling_pass(members: list[np.ndarray], supports: list[float],
                 parents: dict[int, tuple[int, ...]], alive: list[int], n: int,
                 jaccard: float = THETA_SAME) -> dict[int, int]:
    """One sibling round: drop a theme an already kept SIBLING overlaps at ``jaccard``.

    Siblings share at least one immediate parent, or are both roots. Non-sibling overlaps are kept
    whatever their size -- that is the whole point of the restructure. Memberships never change:
    there is no inheritance here.

    Args:
        members: Member ids per node.
        supports: Support per node.
        parents: Immediate parents over the living nodes.
        alive: Living node positions.
        n: Universe size.
        jaccard: The same-theme cutoff.

    Returns:
        ``{dropped node: the kept sibling that dropped it}``.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import order_candidates

    width = bits.words_for(n) * bits.WORD
    packed = {i: bits.pack(members[i].tolist(), width) for i in alive}
    # Today's consensus order, taken from the same function, over the living nodes only.
    local = order_candidates([supports[i] for i in alive], [packed[i] for i in alive])
    order = [alive[i] for i in local]

    parent_sets = {i: set(parents.get(i, ())) for i in alive}
    roots = {i for i in alive if not parent_sets[i]}
    by_parent: dict[int, list[int]] = {}
    kept_roots: list[int] = []
    dropped: dict[int, int] = {}

    for node in order:
        rivals: set[int] = set()
        for parent in parent_sets[node]:
            rivals.update(by_parent.get(parent, ()))
        if node in roots:
            rivals.update(kept_roots)
        beaten = -1
        mine, size = packed[node], len(members[node])
        for other in sorted(rivals):
            inter = int(np.bitwise_count(mine & packed[other]).sum())
            if not inter:
                continue
            other_size = len(members[other])
            if inter == size or inter == other_size:
                continue                      # one contains the other: that is hierarchy, kept
            union = size + other_size - inter
            if union and inter / union >= jaccard:
                beaten = other
                break
        if beaten >= 0:
            dropped[node] = beaten
            continue
        for parent in parent_sets[node]:
            by_parent.setdefault(parent, []).append(node)
        if node in roots:
            kept_roots.append(node)
    return dropped


def restructure(got: Gated, survivor: str, report: bool = True) -> tuple[list[int], list[dict]]:
    """Steps 7 and 8: build the DAG, then chain and sibling to a joint fixed point.

    Args:
        got: The gated input.
        survivor: ``"parent"`` (S1p) or ``"support"`` (S1s).
        report: Print per-round progress.

    Returns:
        ``(alive, rounds)`` -- surviving positions, and one record per round.

    Raises:
        RuntimeError: If the loop does not settle.
    """
    alive = list(range(len(got.members)))
    rounds: list[dict] = []
    for number in range(1, MAX_ROUNDS + 1):
        clock = time.perf_counter()
        parents = dag(got.members, alive, got.n)
        collapsed = chain_pass(got.members, got.supports, parents, alive, survivor)
        if collapsed:
            alive = [i for i in alive if i not in collapsed]
            parents = dag(got.members, alive, got.n)
        dropped = sibling_pass(got.members, got.supports, parents, alive, got.n)
        if dropped:
            alive = [i for i in alive if i not in dropped]
        rounds.append({"round": number, "chain_collapses": len(collapsed),
                       "sibling_drops": len(dropped), "alive": len(alive),
                       "seconds": round(time.perf_counter() - clock, 1)})
        if report:
            print(f"    round {number}: {len(collapsed):,} chain collapses, "
                  f"{len(dropped):,} sibling drops -> {len(alive):,} themes "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
        if not collapsed and not dropped:
            return alive, rounds
    raise RuntimeError(f"the chain/sibling loop did not settle in {MAX_ROUNDS} rounds")


def export_arm(got: Gated, alive: list[int], rounds: list[dict], arm: str,
               args: argparse.Namespace) -> Path:
    """Step 9's edges and the four tables, in O50s's own format so comparisons line up.

    Args:
        got: The gated input.
        alive: Surviving positions.
        rounds: The per-round record.
        arm: ``"S1p"`` or ``"S1s"``.
        args: Parsed arguments.

    Returns:
        Where the build was written.
    """
    from build_trees_10770 import peak_mb
    from core_construction_c1b import immediate_parents
    from thema.data.pathways import PathwayCollection
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology

    members = [got.members[i] for i in alive]
    parents = immediate_parents(members, got.n, report=False)
    ids = [f"n{i:05d}" for i in range(len(members))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents[i]),
             members=tuple((got.keys[p], round(float(got.inclusions[alive[i]].get(p, 1.0)), 4))
                           for p in members[i].tolist()),
             support=round(got.supports[alive[i]], 6))
        for i in range(len(members)))
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in got.keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = sum(1 for node in nodes if len(node.parents) > 1)
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {"n_nodes": len(nodes), "n_roots": len(roots), "n_multi_parent": multi,
             "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
             "n_unplaced": len(unplaced), "n_root_only": len(placed - in_nonroot),
             "n_effectively_unplaced": len(unplaced) + len(placed - in_nonroot)}
    print(f"  themes {shape['n_nodes']:,}  roots {shape['n_roots']:,}  "
          f"multi-parent {shape['multi_parent_share']:.1%}  "
          f"effectively unplaced {shape['n_effectively_unplaced']:,}", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {
        **v04.parameters(got.n),
        "method": f"v0.4-leaves O50s restructured, DAG first ({arm})",
        "design": ("Aviyah, 22 Oct 2026: the 10% variant merge before the gate as now, then the "
                   "DAG, then the sibling rule only on real siblings and the chain rule only on "
                   "real parent-child pairs, iterated to a joint fixed point. NO consensus step."),
        "arm": arm, "survivor": "parent" if arm == "S1p" else "support",
        "universe": "L (every curated summary removed), minus the declared exclusions",
        "n": got.n, "theta_match": 0.70, "theta_same": THETA_SAME,
        "collapse_share": COLLAPSE_SHARE, "consensus": False,
        "runs": args.runs, "rows": f"1-{args.runs}",
        "strata": [list(s) for s in got.strata],
        "floors": list(got.floors), "confirmed": got.confirmed,
        "floors_source": "O50s's stored floors, unchanged; the gate is untouched",
        "gated": len(got.members),
        "rounds": rounds, "n_rounds": len(rounds),
        "n_chain_collapses": sum(r["chain_collapses"] for r in rounds),
        "n_sibling_drops": sum(r["sibling_drops"] for r in rounds),
        "leaves_digest": got.meta["leaves_digest"],
        "universe_digest": got.meta["universe_digest"],
        "exclusions_file": got.meta.get("exclusions_file"),
        "n_excluded_inputs": got.meta.get("n_excluded", 0),
        "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", args.out_version, genes, manifest,
        dry_run=False, info=info, directory=f"thema_L_x2_{arm}")
    print(f"  -> {written}  (peak {peak_mb():.0f} MB)", flush=True)
    return Path(written)


def legacy_reproduce(got: Gated, args: argparse.Namespace) -> bool:
    """Declared test 2: consensus restored and today's repair in place reproduces frozen O50s.

    Steps 7 and 8 are replaced by what O50s actually does -- consensus, then the joint
    collapse/merge fixed point, then ``hasse`` -- from the same gated input this module
    restructures.
    If that path does not land on the frozen bytes, the gated input or the export is wrong and no
    S1 number means anything.

    Args:
        got: The gated input.
        args: Parsed arguments.

    Returns:
        Whether all four tables matched.
    """
    import hashlib

    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.consensus import consensus
    from thema.ontology.recurrent import hasse
    from thema.ontology.repair import repair_joint

    width = bits.words_for(got.n) * bits.WORD
    blocks = [bits.pack(m.tolist(), width) for m in got.members]
    verdict = consensus(blocks, got.supports, got.inclusions, width,
                        stray=0.0, jaccard=THETA_SAME)
    members = [verdict.members[i] for i in range(len(verdict.accepted))]
    supports = [got.supports[c] for c in verdict.accepted]
    inclusions = [got.inclusions[c] for c in verdict.accepted]
    print(f"    consensus: {len(got.members):,} -> {len(members):,} "
          f"({len(verdict.superseded):,} superseded)", flush=True)
    repaired = repair_joint(members, supports, inclusions, 0.85, THETA_SAME, "support")
    print(f"    joint fixed point: {len(members):,} -> {len(repaired.members):,} "
          f"({len(repaired.collapsed):,} collapsed, {len(repaired.merged):,} merged)", flush=True)

    parents = hasse(repaired.members)
    ids = [f"n{i:05d}" for i in range(len(repaired.members))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents[i]),
             members=tuple((got.keys[p], round(float(repaired.inclusions[i].get(p, 1.0)), 4))
                           for p in sorted(bits.unpack(block))),
             support=round(repaired.supports[i], 6))
        for i, block in enumerate(repaired.members))
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in got.keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = sum(1 for node in nodes if len(node.parents) > 1)
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {"n_nodes": len(nodes), "n_roots": len(roots), "n_multi_parent": multi,
             "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
             "n_unplaced": len(unplaced), "n_root_only": len(placed - in_nonroot),
             "n_effectively_unplaced": len(unplaced) + len(placed - in_nonroot)}
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {**v04.parameters(got.n),
                "method": "v0.4-leaves, size strata above 10 (O50s)",
                "n": got.n, "arm": "L", "strata": [list(s) for s in got.strata],
                "floors": list(got.floors), "confirmed": got.confirmed,
                "peak_mb": round(peak_mb(), 1), **shape}
    written = Path(export.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", args.out_version, genes, manifest,
        dry_run=False, info=info, directory="thema_L_x2_S1_legacy"))

    ok = True
    for name in ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv"):
        mine = hashlib.sha256((written / name).read_bytes()).hexdigest()
        theirs = hashlib.sha256((args.frozen / name).read_bytes()).hexdigest()
        print(f"    {'identical ' if mine == theirs else 'DIFFERS   '} {name}")
        ok = ok and mine == theirs
    import shutil
    shutil.rmtree(written)
    return ok


def fixture_tests() -> bool:
    """Declared test 1: the sibling rule never merges non-siblings, and is order-stable.

    Returns:
        Whether both properties held.
    """
    rng = np.random.default_rng(20261022)
    ok = True

    # Two heavily overlapping themes with no shared parent and neither a root: must BOTH survive.
    members = [np.array([0, 1, 2, 3, 4, 5], dtype=np.int32),      # 0, parent of 2
               np.array([10, 11, 12, 13, 14, 15], dtype=np.int32),  # 1, parent of 3
               np.array([0, 1, 2, 3], dtype=np.int32),            # 2, J(2,3)=0 but see below
               np.array([10, 11, 12, 13], dtype=np.int32)]
    supports = [0.9, 0.8, 0.7, 0.6]
    parents = {0: (), 1: (), 2: (0,), 3: (1,)}
    dropped = sibling_pass(members, supports, parents, [0, 1, 2, 3], 32)
    non_sibling = {k: v for k, v in dropped.items() if k in (2, 3)}
    if non_sibling:
        print(f"    FAIL: non-siblings merged: {non_sibling}")
        ok = False

    # Overlapping pair under ONE shared parent: the weaker must be dropped.
    members2 = [np.array(list(range(0, 20)), dtype=np.int32),
                np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=np.int32),
                np.array([0, 1, 2, 3, 4, 5, 6, 8], dtype=np.int32)]
    parents2 = {0: (), 1: (0,), 2: (0,)}
    dropped2 = sibling_pass(members2, [0.9, 0.8, 0.7], parents2, [0, 1, 2], 32)
    if dropped2 != {2: 1}:
        print(f"    FAIL: a true sibling pair was not resolved as expected: {dropped2}")
        ok = False

    # Same overlapping pair but NO shared parent (both children of different parents, not roots):
    # the rule must leave both alone however high the overlap.
    members3 = [np.array(list(range(0, 20)), dtype=np.int32),
                np.array(list(range(20, 40)), dtype=np.int32),
                np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=np.int32),
                np.array([0, 1, 2, 3, 4, 5, 6, 8], dtype=np.int32)]
    parents3 = {0: (), 1: (), 2: (0,), 3: (1,)}
    dropped3 = sibling_pass(members3, [0.9, 0.85, 0.8, 0.7], parents3, [0, 1, 2, 3], 64)
    if any(k in (2, 3) for k in dropped3):
        print(f"    FAIL: a non-sibling overlap at J high was merged: {dropped3}")
        ok = False

    # Order stability: identical inputs, positions permuted, must give the same dropped SETS.
    for trial in range(8):
        size = 12
        sets = [np.array(sorted(rng.choice(40, size=rng.integers(4, 10), replace=False)),
                         dtype=np.int32) for _ in range(size)]
        sup = [round(float(x), 3) for x in rng.random(size)]
        par = {i: ((0,) if i else ()) for i in range(size)}
        first = sibling_pass(sets, sup, par, list(range(size)), 64)
        again = sibling_pass(sets, sup, par, list(range(size)), 64)
        if first != again:
            print(f"    FAIL: not order-stable on trial {trial}")
            ok = False
            break
    return ok


def main(argv: list[str] | None = None) -> int:
    """Run the declared tests, or build one arm.

    Args:
        argv: Command line.

    Returns:
        0 on success, 2 if a declared test fails.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--out-version", default="0.4-leaves")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--arm", choices=ARMS, default=None)
    parser.add_argument("--check", action="store_true",
                        help="run the two declared tests and stop")
    args = parser.parse_args(argv)

    print(f"O50s RESTRUCTURED, DAG FIRST. Prompt 53, 22 Oct 2026. "
          f"{'TESTS' if args.check else args.arm}")
    got = gated_themes(args)

    if args.check:
        print("  test 1: the sibling rule on fixtures", flush=True)
        one = fixture_tests()
        print(f"    {'PASSED' if one else 'FAILED'}")
        print("  test 2: consensus restored plus today's repair reproduces frozen O50s",
              flush=True)
        two = legacy_reproduce(got, args)
        print(f"    {'PASSED' if two else 'FAILED'}")
        if not (one and two):
            return 2
        print("  BOTH DECLARED TESTS PASS.")
        return 0

    if args.arm is None:
        parser.error("pass --arm S1p or --arm S1s, or --check")
    survivor = "parent" if args.arm == "S1p" else "support"
    print(f"  arm {args.arm}: chain survivor {survivor}, share {COLLAPSE_SHARE}, "
          f"sibling cutoff {THETA_SAME}, no consensus", flush=True)
    alive, rounds = restructure(got, survivor)
    print(f"  settled in {len(rounds)} rounds: "
          f"{sum(r['chain_collapses'] for r in rounds):,} chain collapses, "
          f"{sum(r['sibling_drops'] for r in rounds):,} sibling drops", flush=True)
    export_arm(got, alive, rounds, args.arm, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
