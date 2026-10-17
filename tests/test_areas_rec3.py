"""The operator T and its size-weighted Ward: what makes the weighting exact, and the harness.

Three things here are proofs rather than spot checks.

**Weighted Ward is Ward.** With every weight 1, :func:`areas_rec3.ward_weighted` reproduces
scipy's ``ward`` -- the merge pairs, the merge counts and the heights -- so arm E is the ordinary
algorithm. With integer weights it reproduces scipy's ``ward`` on the **replicated point set**,
``w`` coincident copies of each centroid, which is the definition of Ward continued from fixed
clusters. That is what turns "constrained, size-weighted" from a description into a checkable
claim.

**The structure reproduces O50's own DAG.** Running :func:`areas_rec3.containment` and
:func:`areas_rec3.direct_edges` over all 4,602 frozen O50 nodes must give back O50's own
``edges.tsv``, edge for edge. If strict containment and the transitive reduction were wrong in any
way, that would not hold.

**The item rule is the unit rule.** :func:`areas_rec3.items_of` applied to the level-0 structure
must agree with ``recursive_top_O50.units_of``, the rule rec2 and rec2fix used, derived a
completely different way.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import pdist

import areas_rec3 as rec3
import recursive_top_O50 as rt
from thema.ontology import bitset as bits

FROZEN = Path("data/ontology/frozen/working-O50-2026-10-14")
BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec3")


def _unit(rng: np.random.Generator, n: int, dim: int = 12) -> np.ndarray:
    """``n`` random unit vectors."""
    x = rng.normal(size=(n, dim))
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def test_unit_weights_give_the_plain_euclidean_distance() -> None:
    rng = np.random.default_rng(1)
    x = _unit(rng, 25)
    assert np.allclose(rec3.ward_condensed(x, np.ones(25)), pdist(x, metric="euclidean"))


def test_ward_condensed_refuses_degenerate_input() -> None:
    with pytest.raises(ValueError, match="at least two items"):
        rec3.ward_condensed(np.zeros((1, 4)), [1])
    with pytest.raises(ValueError, match="positive"):
        rec3.ward_condensed(np.eye(3)[:, :4], [1, 0, 2])


@pytest.mark.parametrize("n", [5, 8, 20, 60, 150, 400])
def test_unit_weights_reproduce_scipy_ward(n: int) -> None:
    """Arm E is the ordinary algorithm, merge for merge."""
    rng = np.random.default_rng(100 + n)
    condensed = pdist(_unit(rng, n), metric="euclidean")
    mine = rec3.ward_weighted(condensed, np.ones(n))
    theirs = linkage(condensed, method="ward")
    assert np.array_equal(mine[:, :2].astype(np.int64), theirs[:, :2].astype(np.int64))
    assert np.array_equal(mine[:, 3].astype(np.int64), theirs[:, 3].astype(np.int64))
    assert np.abs(mine[:, 2] - theirs[:, 2]).max() < 1e-12


@pytest.mark.parametrize("seed", range(12))
def test_integer_weights_reproduce_ward_on_the_replicated_point_set(seed: int) -> None:
    """Size-weighted Ward IS Ward continued from fixed clusters, not an approximation of it."""
    rng = np.random.default_rng(500 + seed)
    m = int(rng.integers(4, 11))
    weights = rng.integers(1, 7, size=m)
    centroids = _unit(rng, m, dim=6)
    mine = rec3.ward_weighted(rec3.ward_condensed(centroids, weights), weights)
    replicated = linkage(pdist(np.repeat(centroids, weights, axis=0)), method="ward")
    zero = int((replicated[:, 2] < 1e-12).sum())
    assert zero == int(weights.sum()) - m, "the coincident copies should merge first, at height 0"
    tail = replicated[zero:]
    assert len(tail) == m - 1
    assert np.allclose(mine[:, 2], tail[:, 2], atol=1e-9)


def test_a_heavier_item_pulls_a_merge_later_than_an_equal_weighted_one() -> None:
    """The weighting has to change something, or the arms would be the same build."""
    centroids = np.array([[1.0, 0.0], [0.96, 0.28], [-1.0, 0.0]])
    centroids /= np.linalg.norm(centroids, axis=1, keepdims=True)
    equal = rec3.ward_weighted(rec3.ward_condensed(centroids, [1, 1, 1]), [1, 1, 1])
    heavy = rec3.ward_weighted(rec3.ward_condensed(centroids, [1, 1, 60]), [1, 1, 60])
    assert equal[0, 2] < heavy[-1, 2]
    assert heavy[0, 2] == pytest.approx(equal[0, 2]), "the close pair still merges first"
    assert heavy[-1, 2] > equal[-1, 2], "pulling in the heavy item must cost more"


def test_containment_is_strict_and_the_reduction_drops_the_middle_man() -> None:
    blocks = [bits.pack([0], 8), bits.pack([0, 1], 8), bits.pack([0, 1, 2], 8),
              bits.pack([0, 1], 8)]
    closure = rec3.containment(blocks)
    assert closure[0][1] and closure[0][2] and closure[1][2]
    assert not closure[1][3] and not closure[3][1], "equal sets are not containment either way"
    direct = rec3.direct_edges(closure)
    assert direct[0][1] and direct[1][2]
    assert not direct[0][2]


def test_the_reduction_is_blocked_without_changing_the_answer() -> None:
    rng = np.random.default_rng(9)
    blocks = [bits.pack(sorted(rng.choice(40, size=int(rng.integers(2, 20)), replace=False)
                               .tolist()), 40) for _ in range(60)]
    closure = rec3.containment(blocks)
    assert np.array_equal(rec3.direct_edges(closure, block=7),
                          rec3.direct_edges(closure, block=1024))


needs_frozen = pytest.mark.skipif(
    not (FROZEN / "nodes.tsv").exists(), reason="the frozen O50 is not present")


@pytest.fixture(scope="module")
def o50() -> dict:
    """The frozen O50, its pathway index and its bitsets."""
    nodes, members = rt.read_build(FROZEN)
    keys = sorted({key for one in members.values() for key in one})
    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD
    ids = sorted(nodes)
    blocks = [bits.pack(sorted(index[key] for key in members[node]), width) for node in ids]
    return {"nodes": nodes, "members": members, "keys": keys, "ids": ids, "blocks": blocks}


@needs_frozen
def test_the_structure_reproduces_o50s_own_dag(o50: dict) -> None:
    """The harness proof: strict containment plus the reduction gives O50's edges back."""
    closure = rec3.containment(o50["blocks"])
    edges = rec3.direct_edges(closure)
    ids = o50["ids"]
    mine = {(ids[c], ids[p]) for c, p in zip(*np.nonzero(edges), strict=True)}
    with (FROZEN / "edges.tsv").open(encoding="utf-8") as handle:
        theirs = {(row["child"], row["parent"]) for row in csv.DictReader(handle, delimiter="\t")}
    assert len(theirs) == 7525, "the frozen edge count moved; the proof below is against it"
    assert mine == theirs, (
        f"{len(theirs - mine)} O50 edges missing, {len(mine - theirs)} spurious")


@needs_frozen
def test_the_item_rule_agrees_with_the_unit_rule(o50: dict) -> None:
    closure = rec3.containment(o50["blocks"])
    held = {node: set(one) for node, one in o50["members"].items()}
    picked, loose = rec3.items_of(o50["ids"], held, closure, o50["keys"])
    declared, _, _, declared_loose = rt.units_of(o50["nodes"], o50["members"])
    assert sorted(picked) == sorted(declared)
    assert loose == declared_loose
    assert len(picked) + len(loose) == 661


@needs_frozen
def test_o50_already_satisfies_both_rules_the_structure_applies(o50: dict) -> None:
    """Recorded before the build: the rules over the whole set can only act on areas."""
    from thema.ontology.repair import assert_no_chain_pair, stale_pairs
    assert stale_pairs(o50["blocks"], rt.THETA_SAME) == []
    assert_no_chain_pair(o50["blocks"], rt.COLLAPSE_SHARE)


@needs_frozen
@pytest.mark.parametrize("runs", [12])
def test_side_weighted_with_unit_weights_equals_the_existing_scipy_side(
    o50: dict, runs: int
) -> None:
    """End to end: arm E's recurrence material is the one the existing code produces."""
    from thema.ontology.universe import CENTRED, load_centred
    space = Path("data/ontology/v0.4-leaves-x2")
    if not (space / CENTRED).exists():
        pytest.skip("the x2 space is not present")
    keys, vectors = load_centred(space, Path("data/pathways.tsv"))
    declared, _, _, loose = rt.units_of(o50["nodes"], o50["members"])
    members = [o50["members"][n] for n in declared] + [{k} for k in loose]
    n = len(members)
    centroids = rt.unit_centroids(members, keys, vectors)
    rows = rt.subsample_rows(n, runs)
    mine = rec3.side_weighted(centroids, np.ones(n), n, rows, rt.THETA_MATCH).rows()
    theirs = rt.side(centroids, n, rows, rt.THETA_MATCH).rows()
    assert mine == theirs, f"{len(mine)} candidates against {len(theirs)}"


def _arm_dirs() -> list[Path]:
    """Whichever arms are built."""
    return [BUILD / arm for arm in ("W", "E") if (BUILD / arm / "levels.json").exists()]


needs_build = pytest.mark.skipif(
    not _arm_dirs(), reason="rec3 is not built; run scripts/areas_rec3.py")

ARMS = [p.name for p in _arm_dirs()] or ["W"]


def _rows(path: Path) -> list[dict[str, str]]:
    """One TSV, as rows."""
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


@pytest.fixture(scope="module")
def built() -> dict[str, dict]:
    """Each built arm: its node sets, its edges and its closure."""
    out: dict[str, dict] = {}
    for path in _arm_dirs():
        payload = json.loads((path / "levels.json").read_text())
        nodes, members = rt.read_build(FROZEN)
        held = {node: set(one) for node, one in members.items()}
        held.update({node: set(keys) for node, keys in payload["area_members"].items()})
        out[path.name] = {"path": path, "payload": payload, "held": held,
                          "alive": payload["final"]["alive"]}
    return out


def _item_keys(item: str, held: dict[str, set[str]]) -> set[str]:
    """An item's pathway set: a node's members, or the one pathway a loose item is.

    Args:
        item: An item id, either a node id or ``loose:<pathway key>``.
        held: Node id to pathway keys.

    Returns:
        The item's pathways.
    """
    if item.startswith("loose:"):
        return {item[len("loose:"):]}
    return held[item]


@needs_build
@pytest.mark.parametrize("arm", ARMS)
def test_every_areas_pathway_set_is_the_union_of_its_items(arm: str, built: dict) -> None:
    """The invariant T is built on. An arm that admitted nothing has no areas to check."""
    got = built[arm]
    held, payload = got["held"], got["payload"]
    alive = set(got["alive"])
    checked = 0
    for node, items in payload["area_items"].items():
        if node not in alive:
            continue
        union = {key for item in items for key in _item_keys(item, held)}
        assert held[node] == union, f"{arm}/{node}: {len(held[node])} against {len(union)}"
        checked += 1
    admitted = sum(entry["n_areas"] for entry in payload["levels"])
    if not admitted:
        assert checked == 0, f"{arm} admitted no area, so there should be none to check"
        return
    assert checked, f"{arm} admitted {admitted} areas but none survived to be checked"


@needs_build
@pytest.mark.parametrize("arm", ARMS)
def test_every_edge_is_strict_containment(arm: str, built: dict) -> None:
    got = built[arm]
    held = got["held"]
    edges = _rows(got["path"] / "edges.tsv")
    assert edges
    for row in edges:
        assert held[row["child"]] < held[row["parent"]], (
            f"{arm}: {row['child']} is not strictly inside {row['parent']}")


@needs_build
@pytest.mark.parametrize("arm", ARMS)
def test_the_closure_is_exactly_the_containments_and_the_edges_generate_it(
    arm: str, built: dict
) -> None:
    got = built[arm]
    held, alive = got["held"], got["alive"]
    closure = {(row["child"], row["parent"])
               for row in _rows(got["path"] / "closure.tsv")}
    sizes = {node: len(held[node]) for node in alive}
    index: dict[str, set[str]] = {}
    for node in alive:
        for key in held[node]:
            index.setdefault(key, set()).add(node)
    truth = set()
    for child in alive:
        for parent in {o for key in held[child] for o in index[key]}:
            if parent != child and sizes[parent] > sizes[child] and held[child] < held[parent]:
                truth.add((child, parent))
    assert closure == truth, (
        f"{arm}: closure.tsv has {len(closure)} pairs against {len(truth)} containments")
    direct: dict[str, set[str]] = {node: set() for node in alive}
    for row in _rows(got["path"] / "edges.tsv"):
        direct[row["child"]].add(row["parent"])
    reach: dict[str, set[str]] = {}

    def above(node: str) -> set[str]:
        """Everything reachable upwards through direct edges."""
        if node not in reach:
            reach[node] = set()
            reach[node] = {p for parent in direct[node] for p in {parent} | above(parent)}
        return reach[node]

    for child, parent in truth:
        assert parent in above(child), f"{arm}: {child} < {parent} is unreachable"


@needs_build
@pytest.mark.parametrize("arm", ARMS)
def test_no_two_non_nested_nodes_are_twins_and_no_chain_pair_survives(
    arm: str, built: dict
) -> None:
    got = built[arm]
    held, alive = got["held"], got["alive"]
    index: dict[str, set[str]] = {}
    for node in alive:
        for key in held[node]:
            index.setdefault(key, set()).add(node)
    for left in alive:
        a = held[left]
        for right in {o for key in a for o in index[key]}:
            if right == left:
                continue
            b = held[right]
            if a < b:
                assert len(a) / len(b) < rt.COLLAPSE_SHARE, (
                    f"{arm}: {left} is {len(a) / len(b):.3f} of {right}")
                continue
            if b < a:
                continue
            union = len(a | b)
            assert not union or len(a & b) / union < rt.THETA_SAME, (
                f"{arm}: {left} and {right} are twins at {len(a & b) / union:.3f}")


@needs_build
@pytest.mark.parametrize("arm", ARMS)
def test_children_counts_come_from_the_direct_edges(arm: str, built: dict) -> None:
    got = built[arm]
    direct: dict[str, list[str]] = {node: [] for node in got["alive"]}
    for row in _rows(got["path"] / "edges.tsv"):
        direct[row["parent"]].append(row["child"])
    stated = got["payload"]["final"]["children"]
    assert set(stated) == set(direct)
    for node, kids in direct.items():
        assert sorted(stated[node]) == sorted(kids), f"{arm}/{node}: children disagree"
    rows = _rows(got["path"] / "nodes.tsv")
    for row in rows:
        assert int(row["n_children"]) == len(direct[row["node"]])


@needs_build
@pytest.mark.parametrize("arm", ARMS)
def test_the_items_of_each_level_are_maximal_non_giants(arm: str, built: dict) -> None:
    got = built[arm]
    held = got["held"]
    for entry in got["payload"]["levels"]:
        for item in entry["item_ids"]:
            key = item.removeprefix("loose:")
            size = len(held[key]) if key in held else 1
            assert size <= rec3.GIANT, f"{arm} level {entry['level']}: {item} is a giant"
