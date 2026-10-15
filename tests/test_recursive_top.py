"""The recursive top level: the units it chooses, and the shape of what comes back.

The unit rule is the part worth testing, because it is where a mistake would be invisible: a theme
whose only parents are giants is a root of the real hierarchy even though the DAG gives it a parent,
and treating it as parented is exactly the error that hides the missing area layer. The rest of the
level-2 pipeline is v0.4's own code, already tested elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import recursive_top_O50 as rt

FROZEN = Path("data/ontology/frozen/working-O50-2026-10-14")
REC = Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec")
SPACE = Path("data/ontology/v0.4-leaves-x2")


def build(rows: list[tuple[str, str, list[str]]]) -> tuple[dict, dict]:
    """A tiny build from ``(node, parents, members)`` triples."""
    nodes = {node: {"node": node, "parents": parents} for node, parents, _ in rows}
    members = {node: set(keys) for node, _, keys in rows}
    return nodes, members


def test_a_theme_whose_only_parent_is_a_giant_is_a_unit() -> None:
    giant = [f"p{i}" for i in range(rt.GIANT + 1)]
    nodes, members = build([
        ("g", "", giant),
        ("child", "g", ["p1", "p2", "p3"]),
        ("rooted", "", ["p4", "p5", "p6"]),
        ("under_real", "rooted", ["p4", "p5"]),
    ])
    units, giants, giant_only, loose = rt.units_of(nodes, members)
    assert giants == {"g"}
    assert units == ["child", "rooted"], "the giant-parented theme is a unit, its real child is not"
    assert giant_only == ["child"]
    # Everything the giant holds and no non-giant theme does is loose, by construction: here that
    # is p0 and p7 onwards, since only p1-p6 sit in "child" or "rooted".
    assert set(loose) == set(giant) - {"p1", "p2", "p3", "p4", "p5", "p6"}


def test_a_pathway_in_no_nongiant_theme_becomes_its_own_unit() -> None:
    giant = [f"p{i}" for i in range(rt.GIANT + 1)]
    nodes, members = build([("g", "", [*giant, "lonely"]), ("t", "g", ["p1", "p2", "p3"])])
    _units, _giants, _giant_only, loose = rt.units_of(nodes, members)
    assert "lonely" in loose, "a pathway only a giant holds would otherwise be dropped"


def test_a_giant_is_never_a_unit() -> None:
    giant = [f"p{i}" for i in range(rt.GIANT + 1)]
    nodes, members = build([("g", "", giant)])
    units, giants, _giant_only, _loose = rt.units_of(nodes, members)
    assert giants == {"g"} and units == []


def test_exactly_one_thousand_members_is_not_a_giant() -> None:
    # The rule is "more than 1,000", so the boundary is worth pinning.
    keys = [f"p{i}" for i in range(rt.GIANT)]
    nodes, members = build([("edge", "", keys)])
    _units, giants, _giant_only, _loose = rt.units_of(nodes, members)
    assert not giants


def test_centroids_are_unit_vectors_and_order_follows_the_units() -> None:
    keys = ["a", "b", "c"]
    vectors = np.array([[1.0, 0.0], [0.0, 2.0], [-1.0, 0.0]], dtype=np.float32)
    got = rt.unit_centroids([{"a"}, {"b"}, {"a", "c"}], keys, vectors)
    assert got.shape == (3, 2)
    assert np.allclose(np.linalg.norm(got[:2], axis=1), 1.0)
    assert np.allclose(got[0], [1.0, 0.0]) and np.allclose(got[1], [0.0, 1.0]), (
        "rows are normalised before the mean, so the length-2 row does not dominate"
    )
    assert np.linalg.norm(got[2]) < 1e-6 or np.allclose(np.linalg.norm(got[2]), 1.0), (
        "a and c cancel; the row is either zero-safe or renormalised, never NaN"
    )
    assert np.isfinite(got).all()


def test_a_unit_with_no_vector_is_refused() -> None:
    with pytest.raises(ValueError, match="no member with a vector"):
        rt.unit_centroids([{"missing"}], ["a"], np.eye(1, 2, dtype=np.float32))


def test_the_subsample_scheme_is_reproducible_and_shared() -> None:
    first = rt.subsample_rows(100, 5)
    again = rt.subsample_rows(100, 5)
    assert all(np.array_equal(a, b) for a, b in zip(first, again, strict=True))
    assert all(len(row) == 80 for row in first), "80% of 100"
    assert all(np.all(np.diff(row) > 0) for row in first), "sorted, no repeats"


# ------------------------------------------------------------------ against the real build

real = pytest.mark.skipif(
    not (REC / "levels.json").exists() or not (FROZEN / "nodes.tsv").exists(),
    reason="the recursive build or the O50 freeze is not in this checkout",
)


@pytest.fixture(scope="module")
def levels() -> dict:
    return json.loads((REC / "levels.json").read_text())


@real
def test_the_real_units_are_the_declared_count(levels: dict) -> None:
    assert len(levels["unit_ids"]) == 661
    assert levels["nongiant_roots"] == 184
    assert len(levels["giant_only"]) == 476
    assert levels["loose"] == ["btm:M205"], "the one pathway no non-giant theme holds"
    assert len(levels["giants"]) == 4


@real
def test_the_giants_are_absent_from_everything_the_recursion_wrote(levels: dict) -> None:
    giants = set(levels["giants"])
    assert not giants & set(levels["unit_ids"]), "a giant must never be a unit"
    for entry in levels["levels"]:
        for held in entry["child_unit_ids"]:
            assert not giants & set(held), "a giant must never be joined to an area"
    edges = (REC / "area_edges.tsv").read_text().splitlines()[1:]
    assert not any(line.split("\t")[1] in giants for line in edges)


@real
def test_every_unit_is_covered_and_the_areas_hold_only_real_pathways(levels: dict) -> None:
    covered = {u for e in levels["levels"] for held in e["child_unit_ids"] for u in held}
    assert covered == set(levels["unit_ids"]), "every unit must land in at least one area"
    every = {k for keys in levels["unit_pathways"] for k in keys}
    for entry in levels["levels"]:
        for held in entry["pathway_members"]:
            assert set(held) <= every


@real
def test_an_areas_pathways_are_exactly_its_units_union(levels: dict) -> None:
    by_id = dict(zip(levels["unit_ids"], levels["unit_pathways"], strict=True))
    for entry in levels["levels"]:
        for position, held in enumerate(entry["child_unit_ids"]):
            want = sorted({k for unit in held for k in by_id[unit]})
            assert entry["pathway_members"][position] == want


@real
def test_the_recursion_stopped_inside_the_declared_root_window(levels: dict) -> None:
    top = levels["levels"][-1]
    assert rt.MIN_ROOTS <= len(top["roots"]) <= rt.MAX_ROOTS
    assert len(levels["levels"]) == 1, "30 roots at level 2, so no second level was needed"


@real
def test_the_manifest_records_the_configuration_and_adopts_nothing() -> None:
    manifest = json.loads((REC / "manifest.json").read_text())
    assert manifest["theta_match"] == 0.70
    assert manifest["theta_same"] == 0.50
    assert manifest["collapse_share"] == 0.85
    assert manifest["joint_fixed_point"] is True
    assert manifest["floor_target"] == 0.008
    assert manifest["floor_minimum"] == "none"
    assert manifest["runs"] == 200 and manifest["subsample"] == 0.8
    assert "adopts nothing" in manifest["declared"]
