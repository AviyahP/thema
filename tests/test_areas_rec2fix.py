"""The corrected areas layer: the unit bookkeeping, and the six tests prompt 37 mandates.

The part worth testing is the thing rec2 got wrong. ``consensus`` can be run on pathway sets and
still leave an area's pathway set exactly equal to the union of its units' pathways, because every
stage is union-closed. What rec2 got wrong was the units, in two ways that pull in opposite
directions, which is why its stored sets disagreed for 188 of 343 areas:

* it credited a **superseded** candidate's units to the winner, although a supersede drops the loser
  and leaves the winner's membership untouched;
* it took each source's **final** unit set rather than the set as it stood when the absorption
  happened, so a later absorption by the source leaked backwards into the grower.

:func:`areas_rec2fix.fold_units` fixes both, and the randomised tests here are the proof: the
invariant holds through consensus and the joint fixed point, and both of rec2's rules break it.
"""

from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

import areas_rec2fix as fixmod
import recursive_top_O50 as rt
from thema.ontology import bitset as bits
from thema.ontology.consensus import consensus
from thema.ontology.repair import repair_joint

FROZEN = Path("data/ontology/frozen/working-O50-2026-10-14")
BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix")

#: The two rules the combined structure is held to, which are O50's own.
THETA_SAME = rt.THETA_SAME
COLLAPSE_SHARE = rt.COLLAPSE_SHARE


def _case(rng: np.random.Generator) -> tuple[list[set[int]], list[np.ndarray], list[float], int]:
    """One random case: unit pathway sets, candidate unit bitsets, supports, pathway count."""
    n_units = int(rng.integers(6, 20))
    n_paths = int(rng.integers(10, 40))
    unit_paths = [set(rng.choice(n_paths, size=int(rng.integers(1, 6)), replace=False).tolist())
                  for _ in range(n_units)]
    n_cand = int(rng.integers(4, 16))
    blocks = []
    for _ in range(n_cand):
        rows = sorted(set(rng.choice(n_units, size=int(rng.integers(2, max(3, n_units // 2))),
                                     replace=False).tolist()))
        blocks.append(bits.pack(rows, n_units))
    return unit_paths, blocks, [float(x) for x in rng.random(n_cand)], n_paths


def _run(unit_paths, unit_blocks, support, n_paths, theta):
    """Consensus plus the joint fixed point on union sets, with the corrected fold."""
    width = bits.words_for(n_paths) * bits.WORD
    raw = [sorted({p for u in bits.unpack(b) for p in unit_paths[u]}) for b in unit_blocks]
    path_blocks = [bits.pack(p, width) for p in raw]
    inclusions = [{p: 1.0 for p in ps} for ps in raw]
    verdict = consensus(path_blocks, support, inclusions, width, stray=0.0, jaccard=theta)
    folded = fixmod.fold_units(len(unit_blocks), verdict.inherited, unit_blocks, len(unit_paths))
    return verdict, folded


def test_the_invariant_holds_through_consensus_and_the_fixed_point() -> None:
    """An area's pathway set is the union of its units' pathways, at both stages."""
    checked = 0
    for seed in (7, 11, 101):
        rng = np.random.default_rng(seed)
        for _ in range(60):
            unit_paths, unit_blocks, support, n_paths = _case(rng)
            for theta in (0.5, 0.7):
                verdict, folded = _run(unit_paths, unit_blocks, support, n_paths, theta)
                accepted = list(verdict.accepted)
                units = [set(bits.unpack(folded[c])) for c in accepted]
                for position, candidate in enumerate(accepted):
                    held = set(bits.unpack(verdict.members[position]))
                    union = {p for u in units[position] for p in unit_paths[u]}
                    assert held == union, (
                        f"seed {seed} theta {theta} candidate {candidate}: "
                        f"{len(held)} pathways against a union of {len(union)}")
                    checked += 1
                repaired = repair_joint(
                    verdict.members, [support[c] for c in accepted],
                    [{p: 1.0 for p in bits.unpack(b)} for b in verdict.members],
                    COLLAPSE_SHARE, theta, rt.SURVIVOR)
                dead = set(repaired.collapsed) | set(repaired.merged)
                alive = [i for i in range(len(accepted)) if i not in dead]
                assert len(alive) == len(repaired.members)
                for position, row in enumerate(alive):
                    held = set(bits.unpack(repaired.members[position]))
                    union = {p for u in units[row] for p in unit_paths[u]}
                    assert held == union
    assert checked > 1000, f"only {checked} areas checked"


def test_crediting_a_superseded_candidates_units_breaks_the_invariant() -> None:
    """rec2's first mistake: a supersede drops the loser, so its units belong to nobody."""
    broken = 0
    rng = np.random.default_rng(7)
    for _ in range(300):
        unit_paths, unit_blocks, support, n_paths = _case(rng)
        verdict, folded = _run(unit_paths, unit_blocks, support, n_paths, 0.5)
        if not verdict.superseded:
            continue
        accepted = list(verdict.accepted)
        rec2 = [set(bits.unpack(folded[c])) for c in accepted]
        beat = dict(verdict.superseded)
        for dropped, winner in beat.items():
            target, seen = winner, {dropped}
            while target in beat and target not in seen:
                seen.add(target)
                target = beat[target]
            if target in accepted:
                rec2[accepted.index(target)] |= set(bits.unpack(unit_blocks[dropped]))
        for position in range(len(accepted)):
            held = set(bits.unpack(verdict.members[position]))
            union = {p for u in rec2[position] for p in unit_paths[u]}
            broken += held != union
    assert broken, "the superseded credit never showed; the fixture is not exercising it"


def test_taking_the_sources_final_unit_set_breaks_the_invariant() -> None:
    """rec2's second mistake: the fold must use the set as it stood, not the final one."""
    broken = 0
    rng = np.random.default_rng(11)
    for _ in range(400):
        unit_paths, unit_blocks, support, n_paths = _case(rng)
        verdict, _ = _run(unit_paths, unit_blocks, support, n_paths, 0.5)
        if not verdict.inherited:
            continue
        # The closure fold: expand to a fixed point instead of walking the events in order.
        edge = {c: {c} for c in range(len(unit_blocks))}
        for event in verdict.inherited:
            edge[event.parent].add(event.source)
        changed = True
        while changed:
            changed = False
            for c in edge:
                grow = {s for m in edge[c] for s in edge[m]}
                if grow - edge[c]:
                    edge[c] |= grow
                    changed = True
        for position, candidate in enumerate(verdict.accepted):
            rows = {u for s in edge[candidate] for u in bits.unpack(unit_blocks[s])}
            held = set(bits.unpack(verdict.members[position]))
            broken += held != {p for u in rows for p in unit_paths[u]}
    assert broken, "the closure fold never over-credited; the fixture is not exercising it"


def test_fold_units_is_the_identity_with_no_inheritance() -> None:
    blocks = [bits.pack([0, 1], 4), bits.pack([2], 4)]
    got = fixmod.fold_units(2, [], blocks, 4)
    assert [sorted(bits.unpack(b)) for b in got] == [[0, 1], [2]]


def test_containment_is_strict_and_asymmetric() -> None:
    blocks = [bits.pack([0], 4), bits.pack([0, 1], 4), bits.pack([0, 1], 4),
              bits.pack([2, 3], 4)]
    got = fixmod.containment(blocks)
    assert got[0][1] and got[0][2]           # {0} strictly inside {0,1}
    assert not got[1][2] and not got[2][1]   # equal sets are not containment either way
    assert not got[1][0]
    assert not got[3].any()


def test_direct_edges_drop_the_transitive_one() -> None:
    blocks = [bits.pack([0], 8), bits.pack([0, 1], 8), bits.pack([0, 1, 2], 8)]
    closure = fixmod.containment(blocks)
    assert closure[0][1] and closure[0][2] and closure[1][2]
    direct = fixmod.direct_edges(closure)
    assert direct[0][1] and direct[1][2]
    assert not direct[0][2], "0 < 1 < 2, so the 0 to 2 edge is not direct"


needs_build = pytest.mark.skipif(
    not (BUILD / "levels.json").exists(),
    reason="rec2fix is not built; run scripts/areas_rec2fix.py")


@pytest.fixture(scope="module")
def built() -> dict:
    """The build, its view and the sets every mandated test is measured on."""
    payload = json.loads((BUILD / "levels.json").read_text())
    comb = payload["combined"]
    level2 = payload["level2"]
    kind = dict(zip(comb["ids"], comb["kinds"], strict=True))
    units = {node: set(rows) for node, rows
             in zip(comb["ids"], comb["units_per_node"], strict=True)}
    unit_keys = {node: set(keys) for node, keys
                 in zip(payload["unit_ids"], payload["unit_pathways"], strict=True)}
    area_keys = {node: set(keys) for node, keys
                 in zip(level2["node_ids"], level2["pathway_members"], strict=True)}
    held = {node: (area_keys[node] if kind[node] == "area" else unit_keys[node])
            for node in comb["ids"]}
    return {
        "payload": payload, "comb": comb, "kind": kind, "units": units,
        "unit_keys": unit_keys, "area_keys": area_keys, "held": held,
        "view": list(comb["view"]),
    }


def _rows(path: Path) -> list[dict[str, str]]:
    """One TSV, as rows."""
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


@needs_build
def test_every_areas_pathway_set_equals_the_union_of_its_units(built: dict) -> None:
    """Mandated test 1."""
    checked = 0
    for node, keys in built["area_keys"].items():
        union = {key for unit in built["units"][node] for key in built["unit_keys"][unit]}
        assert keys == union, (
            f"{node}: {len(keys)} pathways against a union of {len(union)} over "
            f"{len(built['units'][node])} units")
        checked += 1
    assert checked > 300, f"only {checked} areas checked"


@needs_build
def test_every_edge_is_strict_containment(built: dict) -> None:
    """Mandated test 2."""
    held = built["held"]
    edges = _rows(BUILD / "area_edges.tsv")
    assert edges
    for row in edges:
        child, parent = row["child"], row["parent"]
        assert held[child] < held[parent], (
            f"{child} ({len(held[child])}) is not strictly inside {parent} "
            f"({len(held[parent])})")


@needs_build
def test_every_strict_containment_is_reachable_through_the_edges(built: dict) -> None:
    """Mandated test 3: the closure is exactly the containments, and the edges generate it."""
    held, view = built["held"], built["view"]
    closure = {(row["child"], row["parent"]) for row in _rows(BUILD / "closure.tsv")}
    truth = {(c, p) for c, p in itertools.permutations(view, 2) if held[c] < held[p]}
    assert closure == truth, (
        f"closure.tsv has {len(closure)} pairs against {len(truth)} real strict containments; "
        f"{len(truth - closure)} missing, {len(closure - truth)} spurious")
    direct: dict[str, set[str]] = {node: set() for node in view}
    for row in _rows(BUILD / "area_edges.tsv"):
        direct[row["child"]].add(row["parent"])
    reach: dict[str, set[str]] = {}

    def above(node: str) -> set[str]:
        """Everything reachable upwards from a node through direct edges."""
        if node in reach:
            return reach[node]
        reach[node] = set()
        out: set[str] = set()
        for parent in direct[node]:
            out |= {parent} | above(parent)
        reach[node] = out
        return out

    for child, parent in truth:
        assert parent in above(child), f"{child} < {parent} is not reachable through the edges"


@needs_build
def test_no_two_non_nested_nodes_are_at_or_above_the_same_theme_cutoff(built: dict) -> None:
    """Mandated test 4."""
    held, view = built["held"], built["view"]
    index: dict[str, list[str]] = {}
    for node in view:
        for key in held[node]:
            index.setdefault(key, []).append(node)
    for left in view:
        a = held[left]
        for right in {o for key in a for o in index[key]}:
            if right <= left:
                continue
            b = held[right]
            if a < b or b < a:
                continue
            union = len(a | b)
            assert not union or len(a & b) / union < THETA_SAME, (
                f"{left} ({len(a)}) and {right} ({len(b)}) are not nested and sit at "
                f"J = {len(a & b) / union:.3f}")


@needs_build
def test_no_parent_child_pair_is_at_or_above_the_collapse_share(built: dict) -> None:
    """Mandated test 5."""
    held = built["held"]
    for row in _rows(BUILD / "closure.tsv"):
        child, parent = held[row["child"]], held[row["parent"]]
        share = len(child) / len(parent)
        assert share < COLLAPSE_SHARE, (
            f"{row['child']} is {share:.3f} of {row['parent']}, at or above "
            f"{COLLAPSE_SHARE}")


@needs_build
def test_children_counts_come_from_direct_edges_only(built: dict) -> None:
    """Mandated test 6."""
    direct: dict[str, list[str]] = {node: [] for node in built["view"]}
    for row in _rows(BUILD / "area_edges.tsv"):
        direct[row["parent"]].append(row["child"])
    stated = built["comb"]["children"]
    assert set(stated) == set(direct)
    for node, kids in direct.items():
        assert sorted(stated[node]) == sorted(kids), f"{node}: children disagree with the edges"
    closure_kids: dict[str, int] = {node: 0 for node in built["view"]}
    for row in _rows(BUILD / "closure.tsv"):
        closure_kids[row["parent"]] += 1
    worst = max(len(k) for k in direct.values())
    assert worst <= 60, f"a node has {worst} direct children"
    assert max(closure_kids.values()) > worst, (
        "the closure should be strictly more generous than the direct edges, else the "
        "transitive reduction did nothing")


@needs_build
def test_no_giant_area_is_in_the_view(built: dict) -> None:
    """Aviyah's giant rule, as recorded with prompt 37."""
    held = built["held"]
    giants = set(built["comb"]["giants"])
    assert giants, "there should be giant areas to drop"
    for node in giants:
        assert len(held[node]) > fixmod.GIANT_AREA
        assert node not in set(built["view"])
    for node in built["view"]:
        if built["kind"][node] == "area":
            assert len(held[node]) <= fixmod.GIANT_AREA


@needs_build
def test_the_view_covers_every_unit_and_every_giant_only_theme(built: dict) -> None:
    payload = built["payload"]
    view = set(built["view"])
    roots = set(built["comb"]["roots"])
    gone = set(built["comb"]["collapsed"]) | set(built["comb"]["merged"])
    for unit in payload["unit_ids"]:
        placed = bool([p for p in built["comb"]["parents"].get(unit, [])])
        assert placed or unit in roots or unit in gone, f"{unit} is in no structure at all"
        assert unit in view or unit in gone
    for theme in payload["giant_only"]:
        assert theme in payload["unit_ids"]
