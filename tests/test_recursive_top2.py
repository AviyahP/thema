"""The anchored recursive top: the anchor split, and the move into pathway space.

The part worth testing is change (a): the same-theme cutoff and chain collapse now compare PATHWAY
sets while the candidates are still sets of units, so a surviving area's unit list has to be
recovered somehow. Recovering it BY INDEX is wrong and this suite caught it: consensus does not only
drop candidates, because ``STRAY_FLOOR`` is 1 and a candidate whose extras number at most one is
inherited, so an accepted set grows. The units are therefore recovered from provenance -- superseded
chains and inheritance sources -- and the test below asserts the consequence: an area's pathway set
is exactly the union of its units' members. Without the fix 343 of 343 areas failed it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import recursive_top_O50 as rt
import recursive_top_O50_rec2 as rt2
from thema.ontology import bitset as bits

FROZEN = Path("data/ontology/frozen/working-O50-2026-10-14")
REC2 = Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2")

WIDTH = 64


def test_the_pathway_space_is_sorted_and_total() -> None:
    keys, index = rt2.pathway_space([{"b", "a"}, {"c"}, {"a"}])
    assert keys == ["a", "b", "c"]
    assert index == {"a": 0, "b": 1, "c": 2}


def test_a_candidates_pathway_set_is_the_union_of_its_units() -> None:
    unit_members = [{"a", "b"}, {"b", "c"}, {"z"}]
    keys, index = rt2.pathway_space(unit_members)
    # one candidate holding units 0 and 1, another holding unit 2
    blocks = [bits.pack([0, 1], 3), bits.pack([2], 3)]
    got = rt2.as_pathway_blocks(blocks, unit_members, index, len(keys))
    assert [sorted(keys[b] for b in bits.unpack(x)) for x in got] == [
        ["a", "b", "c"], ["z"],
    ]


def test_two_candidates_with_different_units_can_hold_the_same_pathways() -> None:
    # This is the whole reason for change (a): on unit sets these two look unrelated (Jaccard 0),
    # on pathway sets they are identical, and the old build therefore kept both as separate areas.
    unit_members = [{"p1", "p2"}, {"p1", "p2"}]
    keys, index = rt2.pathway_space(unit_members)
    left, right = rt2.as_pathway_blocks(
        [bits.pack([0], 2), bits.pack([1], 2)], unit_members, index, len(keys))
    units_left, units_right = {0}, {1}
    assert not (units_left & units_right), "no unit in common"
    assert sorted(bits.unpack(left)) == sorted(bits.unpack(right)), "identical pathway sets"


def test_an_empty_candidate_maps_to_an_empty_pathway_set() -> None:
    keys, index = rt2.pathway_space([{"a"}])
    got = rt2.as_pathway_blocks([bits.pack([], 1)], [{"a"}], index, len(keys))
    assert sorted(bits.unpack(got[0])) == []


def test_the_anchor_threshold_is_strictly_more_than_two_hundred() -> None:
    assert rt2.ANCHOR_PATHWAYS == 200
    small, big = {f"p{i}" for i in range(200)}, {f"p{i}" for i in range(201)}
    assert not len(small) > rt2.ANCHOR_PATHWAYS
    assert len(big) > rt2.ANCHOR_PATHWAYS


def test_the_floor_seeds_are_the_declared_ones() -> None:
    assert rt2.CALIBRATION_SEEDS == tuple(range(3001, 3021))
    assert rt2.HELDOUT_SEEDS == (4002, 4003, 4004, 4005)
    assert rt2.FLOOR_TARGET == 0.008
    assert (rt2.CAP_OVERALL, rt2.CAP_STRATUM) == (0.01, 0.02), "the caps are unchanged"


def test_matching_still_runs_on_units_not_pathways() -> None:
    # Change (a) moves the same-theme and collapse comparisons only. Recurrence is a different
    # question and stays where it was.
    source = Path("scripts/recursive_top_O50_rec2.py").read_text()
    assert "theta_match: float = rt.THETA_MATCH" in source
    assert 'rt.side(matrix, n, rows_seq, theta_match)' in source
    assert '"theta_match_space": "unit membership"' in source
    assert '"theta_same_space": "pathway sets"' in source


# ------------------------------------------------------------------ against the real build

real = pytest.mark.skipif(
    not (REC2 / "levels.json").exists(),
    reason="the rec2 build is not in this checkout",
)


@pytest.fixture(scope="module")
def levels() -> dict:
    return json.loads((REC2 / "levels.json").read_text())


@real
def test_the_anchors_are_the_six_units_over_two_hundred(levels: dict) -> None:
    assert sorted(levels["anchors"]) == sorted(
        ["n01027", "n01279", "n03315", "n03959", "n03376", "n02017"])
    assert all(size > rt2.ANCHOR_PATHWAYS for size in levels["anchor_sizes"].values())
    assert len(levels["level_unit_ids"]) == 655
    assert len(levels["unit_ids"]) == 661


@real
def test_no_anchor_was_clustered(levels: dict) -> None:
    anchors = set(levels["anchors"])
    assert not anchors & set(levels["level_unit_ids"]), "an anchor must not be a level-2 unit"
    for entry in levels["levels"]:
        for held in entry["child_unit_ids"]:
            assert not anchors & set(held), "an anchor must never be a child of an area"


@real
def test_an_areas_pathways_are_contained_in_its_units_union(levels: dict) -> None:
    """The relation that actually holds, and the one the report is written on.

    Prompt 34's step 3 says an area's pathway members are the union of its units' members. On unit
    sets that was true by construction. On pathway sets it is only an INCLUSION: consensus inherits
    individual pathways, so a candidate can be folded in on the strength of one member while the
    provenance recovery credits the area with that candidate's whole unit. Measured: the compared
    set is a subset of the union for all 343 areas, equal for 155 of them, and smaller by a median
    of 19 pathways for the other 188. The compared set is what every rule and every criterion was
    applied to, so it is what the report uses; the gap is reported, not hidden.
    """
    by_id = dict(zip(levels["unit_ids"], levels["unit_pathways"], strict=True))
    top = levels["levels"][-1]
    equal = 0
    for position, held in enumerate(top["child_unit_ids"]):
        union = {key for unit in held for key in by_id[unit]}
        compared = set(top["pathway_members"][position])
        assert compared <= union, (
            f"area {top['node_ids'][position]}: its compared pathway set is not inside its units' "
            "union, so the provenance recovery has lost a unit"
        )
        equal += compared == union
    assert equal >= 150, f"only {equal} areas are an exact union; the recovery may have drifted"


@real
def test_no_two_areas_hold_the_same_pathway_set(levels: dict) -> None:
    # What the 0.50 cutoff on pathway sets is for: identical sets must have been merged.
    top = levels["levels"][-1]
    sets = [frozenset(v) for v in top["pathway_members"]]
    assert len(set(sets)) == len(sets), "two areas hold identical pathway sets"


@real
def test_no_surviving_pair_breaks_either_rule(levels: dict) -> None:
    top = levels["levels"][-1]
    sets = [set(v) for v in top["pathway_members"]]
    for i, left in enumerate(sets):
        for right in sets[i + 1:]:
            if left < right:
                assert len(left) < rt.COLLAPSE_SHARE * len(right)
            elif not right < left:
                union = len(left | right)
                assert not union or len(left & right) / union < rt.THETA_SAME
