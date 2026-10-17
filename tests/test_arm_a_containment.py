"""Arm A's containment fix: the bug, the two views and the propagation rule.

The bug is worth a regression test by name, because it was invisible in arm A's own numbers: five
anchors came out as roots while O50s itself places them inside a giant, and nothing in arm A's
structure could be their parent because ``units_of`` never lets a giant be a unit and rec2fix never
re-adds the giants. The fix is in the arm A assembly only, so ``areas_rec2fix``'s defaults and tests
are untouched.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import arm_a_containment as fix

TOP = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_top")
O50S = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s")
REVIEW = Path("data/experiments/top_two_arms_2026-10-17")

#: The five roots the bug produced, and the giant each belongs under.
BUG = {"n00225": "n01419", "n03971": "n01419", "n04999": "n01419",
       "n04528": "n01843", "n05000": "n03878"}


def test_the_missing_bins_cover_every_count() -> None:
    assert fix.bin_of(0) == "0"
    assert fix.bin_of(1) == "1-5"
    assert fix.bin_of(5) == "1-5"
    assert fix.bin_of(6) == "6-20"
    assert fix.bin_of(20) == "6-20"
    assert fix.bin_of(21) == "21+"
    assert fix.bin_of(10 ** 6) == "21+"


def test_containment_is_strict_and_the_reduction_drops_the_middle_man() -> None:
    groups = {"a": {"p0"}, "b": {"p0", "p1"}, "c": {"p0", "p1", "p2"}, "d": {"p0", "p1"}}
    ids, stack, sizes = fix.pack_all(groups, ["p0", "p1", "p2"])
    closure = fix.containment(stack, sizes)
    at = {node: i for i, node in enumerate(ids)}
    assert closure[at["a"]][at["b"]] and closure[at["a"]][at["c"]]
    assert not closure[at["b"]][at["d"]], "equal sets are not containment either way"
    direct = fix.direct_edges(closure)
    assert direct[at["a"]][at["b"]]
    assert not direct[at["a"]][at["c"]], "a < b < c, so the a to c edge is not direct"


def test_the_reduction_is_blocked_without_changing_the_answer() -> None:
    rng = np.random.default_rng(5)
    groups = {f"n{i}": {f"p{j}" for j in
                        rng.choice(30, size=int(rng.integers(2, 14)), replace=False)}
              for i in range(50)}
    keys = sorted({k for v in groups.values() for k in v})
    _ids, stack, sizes = fix.pack_all(groups, keys)
    closure = fix.containment(stack, sizes)
    assert np.array_equal(fix.direct_edges(closure, block=3),
                          fix.direct_edges(closure, block=4096))


def test_propagation_pulls_a_near_contained_node_under_its_parent() -> None:
    """Five missing pathways at 98% or better: the parent and its ancestors gain them."""
    parent = {f"p{i}" for i in range(200)}
    grandparent = parent | {f"q{i}" for i in range(50)}
    child = {f"p{i}" for i in range(195)} | {"x0", "x1"}
    groups = {"child": child, "parent": parent, "grand": grandparent}
    grown, record = fix.propagate(groups, report=False)
    assert record["pathways_added"] == 4, "two missing, into the parent and the grandparent"
    assert {"x0", "x1"} <= grown["parent"], "the parent gained what it lacked"
    assert {"x0", "x1"} <= grown["grand"], "and so did its ancestor, keeping containment"
    assert grown["child"] == child, "the child is untouched"
    assert grown["child"] < grown["parent"] < grown["grand"]
    assert record["events"][0]["parent"] == "parent", "the SMALLEST container wins"


def test_propagation_refuses_too_many_missing_pathways() -> None:
    parent = {f"p{i}" for i in range(200)}
    child = {f"p{i}" for i in range(190)} | {f"x{i}" for i in range(6)}
    grown, record = fix.propagate({"child": child, "parent": parent}, report=False)
    assert record["pathways_added"] == 0
    assert grown["parent"] == parent


def test_propagation_refuses_a_share_below_the_bar() -> None:
    parent = {f"p{i}" for i in range(200)}
    # 95% inside, and only 5 missing, but the share bar is 98%.
    child = {f"p{i}" for i in range(95)} | {"x0", "x1", "x2", "x3", "x4"}
    grown, record = fix.propagate({"child": child, "parent": parent}, report=False)
    assert len(child - parent) <= fix.MAX_MISSING
    assert len(child & parent) / len(child) < fix.NEAR
    assert record["pathways_added"] == 0
    assert grown["parent"] == parent


def test_propagation_leaves_a_node_that_already_has_a_parent_alone() -> None:
    parent = {f"p{i}" for i in range(100)}
    child = {f"p{i}" for i in range(50)}
    grown, record = fix.propagate({"child": child, "parent": parent}, report=False)
    assert record["pathways_added"] == 0
    assert grown == {"child": child, "parent": parent}


needs_builds = pytest.mark.skipif(
    not (TOP / "A1" / "view.json").exists() or not (TOP / "A" / "levels.json").exists(),
    reason="arm A or A1 is not built")


@pytest.fixture(scope="module")
def built() -> dict:
    """Arm A, A1 and A2, with O50s's members."""
    import recursive_top_O50 as rt

    _nodes, members = rt.read_build(O50S)
    return {
        "members": members,
        "A": json.loads((TOP / "A" / "levels.json").read_text()),
        "A1": json.loads((TOP / "A1" / "view.json").read_text()),
        "A2": json.loads((TOP / "A2" / "view.json").read_text()),
    }


@needs_builds
def test_the_node_set_adds_the_giants_and_holds_the_seam_victims_out(built: dict) -> None:
    held, kind, dead = fix.node_set(built["A"], built["members"])
    giants = {n for n, v in built["members"].items() if len(v) > fix.GIANT}
    assert len(giants) == 5
    assert giants <= set(held), "every O50s giant is in the structure now"
    assert set(dead) == set(built["A"]["collapsed"]) | set(built["A"]["merged"])
    assert len(dead) == 7
    for node in dead:
        assert node not in held, f"{node} was removed by the rules and must stay removed"
    assert len(held) == len(built["members"]) + len(built["A"]["area_members"]) - len(dead)


@needs_builds
def test_the_bug_is_fixed_no_root_is_wholly_inside_another_node(built: dict) -> None:
    """The regression test: A1's 0-missing bin must be empty."""
    assert built["A1"]["near_bins"].get("0", 0) == 0
    assert all(row["missing"] > 0 for row in built["A1"]["near"])
    # And the five named anchors are no longer roots.
    roots = {row["node"] for row in built["A1"]["root_rows"]}
    for anchor in BUG:
        assert anchor not in roots, f"{anchor} is still a root"


@needs_builds
def test_each_bug_case_now_sits_under_the_giant_o50s_puts_it_under(built: dict) -> None:
    with (TOP / "A1" / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    closure: dict[str, set[str]] = {}
    with (TOP / "A1" / "edges.tsv").open(encoding="utf-8") as handle:
        direct: dict[str, set[str]] = {}
        for row in csv.DictReader(handle, delimiter="\t"):
            direct.setdefault(row["child"], set()).add(row["parent"])

    def above(node: str) -> set[str]:
        """Everything reachable upwards."""
        if node not in closure:
            closure[node] = set()
            closure[node] = {p for parent in direct.get(node, ())
                             for p in {parent} | above(parent)}
        return closure[node]

    for anchor, giant in BUG.items():
        assert anchor in rows, anchor
        assert giant in above(anchor), f"{anchor} should sit under {giant}"


@needs_builds
def test_the_five_giants_are_the_new_roots(built: dict) -> None:
    before = set(built["A"]["roots"])
    after = {row["node"] for row in built["A1"]["root_rows"]}
    giants = {n for n, v in built["members"].items() if len(v) > fix.GIANT}
    assert before - after == set(BUG), "exactly the five bug cases stop being roots"
    assert after - before == giants, "and exactly the five giants become roots"
    assert len(after) == len(before), "so the count is unchanged at 47"


@needs_builds
def test_no_reclustering_the_floors_are_arm_as_own(built: dict) -> None:
    cached = json.loads((TOP / "areas_A_848items_200runs.json").read_text())
    for name in ("A1", "A2"):
        assert built[name]["floors"] == built["A"]["floors"]
        assert built[name]["confirmed"] == built["A"]["confirmed"]
    assert cached["floors"] == built["A"]["floors"]
    assert cached["confirmed"] == built["A"]["confirmed"]


@needs_builds
def test_a2_clears_the_small_missing_bins_and_records_what_it_added(built: dict) -> None:
    a2 = built["A2"]
    assert a2["near_bins"].get("0", 0) == 0
    assert a2["near_bins"].get("1-5", 0) == 0, "the rule exists to empty this bin"
    assert a2["propagation"]["pathways_added"] > 0
    assert a2["n_roots"] < built["A1"]["n_roots"]
    for event in a2["propagation"]["events"]:
        assert len(event["missing"]) <= fix.MAX_MISSING


@needs_builds
def test_a2s_propagated_members_carry_evidence_score_zero() -> None:
    path = TOP / "A2" / "propagated_members.tsv"
    if not path.exists():
        pytest.skip("A2 wrote no propagated members")
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert rows
    for row in rows:
        assert float(row["inclusion"]) == fix.PROPAGATED_INCLUSION


@needs_builds
def test_the_reviewer_table_matches_a1(built: dict) -> None:
    path = REVIEW / "A1" / "roots.tsv"
    if not path.exists():
        pytest.skip("the reviewer table is not written")
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert {r["node"] for r in rows} == {r["node"] for r in built["A1"]["root_rows"]}
    for row in rows:
        assert len(row["members"].split()) == int(row["size"])
        assert row["kind"] in ("area", "anchor", "unit", "giant", "theme")
