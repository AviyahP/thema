"""Areas on the O50s roots: the unit rule, the containment invariant and the giants.

Three things are worth asserting rather than reporting. The unit rule must take **every** O50s root
including the giants and must cover the universe, or the design is not the one declared. The
containment invariant -- nothing wholly inside another node without descending from it -- is the one
arm A broke silently, so it is a named test. And an area must actually be able to contain a giant,
which is the open question prompt 45 ended on and the reason the giants are units here.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

import areas_on_roots as aor

BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas")
O50S = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s")
REVIEW = Path("data/experiments/areas_on_roots_2026-10-18")


def test_jaccard_and_the_empty_case() -> None:
    assert aor.jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)
    assert aor.jaccard(set(), set()) == 0.0
    assert aor.jaccard({"a"}, set()) == 0.0


def test_the_area_bands_cover_every_size() -> None:
    assert aor.band_of(1) == "1-50"
    assert aor.band_of(50) == "1-50"
    assert aor.band_of(51) == "51-200"
    assert aor.band_of(1000) == "501-1000"
    assert aor.band_of(1001) == "1001+"
    assert aor.band_of(10 ** 7) == "1001+"


def test_the_unit_rule_takes_every_root_including_the_giants() -> None:
    nodes = {
        "big": {"parents": "", "support": "1.0"},
        "mid": {"parents": "big", "support": "1.0"},
        "other": {"parents": "   ", "support": "1.0"},
    }
    members = {"big": {"p1", "p2", "p3"}, "mid": {"p1"}, "other": {"p4"}}
    ids, held = aor.units_of_roots(nodes, members)
    assert ids == ["big", "other"], "a root is a node no edge claims as a child"
    assert held == [{"p1", "p2", "p3"}, {"p4"}]


def test_the_unit_rule_refuses_roots_that_do_not_cover_the_universe() -> None:
    """A remainder would mean inventing a unit, which is not the declared design."""
    nodes = {"a": {"parents": "", "support": "1.0"}, "b": {"parents": "a", "support": "1.0"}}
    members = {"a": {"p1"}, "b": {"p1"}, "orphan": {"p9"}}
    with pytest.raises(ValueError, match="would need a unit of their own"):
        aor.units_of_roots(nodes, members)


def test_structure_finds_the_roots_and_reduces_the_edges() -> None:
    held = {"top": {"p1", "p2", "p3"}, "mid": {"p1", "p2"}, "leaf": {"p1"},
            "side": {"p4"}}
    built = aor.structure(held, ["p1", "p2", "p3", "p4"])
    assert sorted(built["roots"]) == ["side", "top"]
    assert built["parents"]["leaf"] == ["mid"], "the top is reached through the middle"
    assert built["parents"]["mid"] == ["top"]
    assert sorted(built["children"]["top"]) == ["mid"]


def test_the_sanity_check_catches_a_non_descendant_container() -> None:
    """Hand the checker a structure whose edges are missing, and it must notice."""
    held = {"top": {"p1", "p2"}, "leaf": {"p1"}}
    built = aor.structure(held, ["p1", "p2"])
    assert aor.sanity(built, held)["violations"] == 0
    broken = dict(built)
    broken["parents"] = {"top": [], "leaf": []}
    got = aor.sanity(broken, held)
    assert got["violations"] == 1
    assert got["examples"][0] == {"child": "leaf", "child_size": 1,
                                 "parent": "top", "parent_size": 2}


needs_build = pytest.mark.skipif(
    not (BUILD / "build.json").exists(),
    reason="the build has not run; run scripts/areas_on_roots.py")


@pytest.fixture(scope="module")
def built() -> dict:
    """The build, with O50s's own nodes and members."""
    import recursive_top_O50 as rt

    nodes, members = rt.read_build(O50S)
    return {"record": json.loads((BUILD / "build.json").read_text()),
            "nodes": nodes, "members": members}


@needs_build
def test_the_units_are_the_261_o50s_roots(built: dict) -> None:
    ids, held = aor.units_of_roots(built["nodes"], built["members"])
    assert len(ids) == 261
    giants = {n for n, v in built["members"].items() if len(v) > aor.GIANT}
    assert len(giants) == 5
    assert giants <= set(ids), "every giant is a unit here, unlike rec2fix"
    assert sum(1 for one in held if len(one) <= aor.SMALL_ROOT) == 164


@needs_build
def test_o50s_is_untouched(built: dict) -> None:
    """No theme is removed or edited: the structure is O50s plus areas, nothing else."""
    record = built["record"]
    assert record["n_o50s_themes"] == len(built["members"]) == 5658
    with (BUILD / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    assert len(rows) == len(built["members"]) + record["n_areas"]
    for node, one in built["members"].items():
        assert node in rows, node
        assert int(rows[node]["size"]) == len(one), node


@needs_build
def test_nothing_is_wholly_inside_a_non_ancestor(built: dict) -> None:
    """The named regression test: the invariant arm A broke."""
    assert built["record"]["sanity"]["violations"] == 0
    assert built["record"]["sanity"]["examples"] == []


@needs_build
def test_every_giant_is_contained_by_an_area(built: dict) -> None:
    """Prompt 45's open question, answered here because the giants are units."""
    record = built["record"]
    giants = set(record["giants"])
    assert len(giants) == 5
    covered = {g for gs in record["areas_with_a_giant"].values() for g in gs}
    assert covered == giants, f"uncontained: {sorted(giants - covered)}"
    areas = {n: set(v) for n, v in record["area_members"].items()}
    for area, held in record["areas_with_a_giant"].items():
        for giant in held:
            assert built["members"][giant] <= areas[area], f"{giant} not inside {area}"


@needs_build
def test_no_giant_and_no_o50s_theme_is_left_at_the_top(built: dict) -> None:
    record = built["record"]
    assert all(row["kind"] == "area" for row in record["root_rows"])
    assert len(record["roots"]) == 12


@needs_build
def test_the_held_out_check_is_inside_both_caps(built: dict) -> None:
    confirmed = built["record"]["confirmed"]
    assert confirmed["overall_fdr"] <= aor.CAP_OVERALL
    for entry in confirmed["strata"]:
        if entry["heldout_fdr"] is not None:
            assert entry["heldout_fdr"] <= aor.CAP_STRATUM, entry["stratum"]


@needs_build
def test_a_stratum_with_no_floor_admitted_nothing(built: dict) -> None:
    """Three strata got no floor; a floor-less stratum must admit nothing, never everything."""
    empty = [e for e in built["record"]["confirmed"]["strata"] if e["effective"] is None]
    assert empty, "this build has strata with no floor, and the test documents it"
    for entry in empty:
        assert entry["heldout_real"] == 0, entry["stratum"]


@needs_build
def test_every_area_is_the_union_of_its_units(built: dict) -> None:
    record = built["record"]
    for area, units in record["area_units"].items():
        union: set[str] = set()
        for unit in units:
            union |= set(built["members"][unit])
        assert set(record["area_members"][area]) == union, area


@needs_build
def test_the_reviewer_tables_match_the_build(built: dict) -> None:
    record = built["record"]
    if not (REVIEW / "roots.tsv").exists():
        pytest.skip("the reviewer tables are not written")
    with (REVIEW / "roots.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert {r["node"] for r in rows} == set(record["roots"])
    for row in rows:
        assert len(row["members"].split()) == int(row["size"])
    with (REVIEW / "small_roots.tsv").open(encoding="utf-8") as handle:
        small = list(csv.DictReader(handle, delimiter="\t"))
    assert small == [], "there are no small roots, so the table is a header only"
    with (REVIEW / "areas.tsv").open(encoding="utf-8") as handle:
        areas = list(csv.DictReader(handle, delimiter="\t"))
    assert len(areas) == record["n_areas"] == 66
    for row in areas:
        assert len(row["members"].split()) == int(row["size"])
        assert len(row["units"].split()) == int(row["n_units"])
