"""The invariants every builder's output must satisfy.

These fail the build rather than warning, because each violation produces a structure that reads as
a correct ontology everywhere downstream -- the demo, the statistics, the evaluation.
"""

import pytest

from thema.ontology.base import (
    Node,
    Ontology,
    check_distinct_members,
    check_invariants,
    check_single_parent,
)


def node(ident, members, parents=(), support=1.0):
    return Node(id=ident, parents=tuple(parents), members=tuple((m, 1.0) for m in members),
                support=support)


def ontology(*nodes, unplaced=(), method="ward_tree"):
    return Ontology(method=method, params={}, nodes=tuple(nodes), unplaced=tuple(unplaced))


KEYS = ["a", "b", "c", "d"]


def test_a_well_formed_tree_passes():
    o = ontology(node("top", "abcd"), node("left", "ab", ["top"]), node("right", "cd", ["top"]))
    check_invariants(o, KEYS, min_size=None)
    check_single_parent(o)
    assert [n.id for n in o.roots] == ["top"]
    assert set(o.edges) == {("left", "top"), ("right", "top")}


# ------------------------------------------------------ containment
#
# The predicate is NON-strict, and getting this wrong is not theoretical: requiring a strict subset
# turned 66 nodes of the real v0.1 tree into roots, which would have rendered 76 top-level themes
# instead of ten. A cut that does not split its parent repeats its membership, and §9.4 calls that
# parent "the node at the previous level that contains it".


def test_a_child_repeating_its_parents_membership_is_allowed():
    o = ontology(node("top", "abcd"), node("same", "abcd", ["top"]))
    check_invariants(o, KEYS, min_size=None)
    assert [n.id for n in o.roots] == ["top"], "the child must stay a child, not become a root"


def test_a_child_with_a_member_its_parent_lacks_is_refused():
    o = ontology(node("top", "ab"), node("kid", "abc", ["top"]), unplaced="d")
    with pytest.raises(ValueError, match="not contained in"):
        check_invariants(o, KEYS, min_size=None)


def test_equal_member_sets_are_refused_only_where_the_method_forbids_them():
    """ward_tree repeats a membership legitimately; recurrent_dag merges instead (§10.7)."""
    o = ontology(node("one", "abcd"), node("two", "abcd", ["one"]))
    check_invariants(o, KEYS, min_size=None)
    with pytest.raises(ValueError, match="identical members"):
        check_distinct_members(o)


# ------------------------------------------------------ the rest of §7.3


def test_every_pathway_must_be_placed_or_recorded_unplaced():
    o = ontology(node("top", "abc"))
    with pytest.raises(ValueError, match="not recorded as unplaced"):
        check_invariants(o, KEYS, min_size=None)
    check_invariants(ontology(node("top", "abc"), unplaced="d"), KEYS, min_size=None)


def test_a_pathway_cannot_be_both_placed_and_unplaced():
    o = ontology(node("top", "abcd"), unplaced="d")
    with pytest.raises(ValueError, match="both placed and listed unplaced"):
        check_invariants(o, KEYS, min_size=None)


def test_a_node_holding_a_key_the_build_never_saw_is_refused():
    o = ontology(node("top", "abcde"))
    with pytest.raises(ValueError, match="never given to the build"):
        check_invariants(o, KEYS, min_size=None)


def test_min_size_is_enforced_when_the_method_applies_one():
    o = ontology(node("top", "abcd"), node("tiny", "a", ["top"]))
    check_invariants(o, KEYS, min_size=None)
    with pytest.raises(ValueError, match="below min_size"):
        check_invariants(o, KEYS, min_size=2)


def test_a_missing_parent_is_refused():
    o = ontology(node("kid", "abcd", ["nowhere"]))
    with pytest.raises(ValueError, match="parent that does not exist"):
        check_invariants(o, KEYS, min_size=None)


def test_a_cycle_is_refused_even_though_containment_makes_one_impossible():
    """Asserted rather than assumed: a cycle means the containment computation is wrong."""
    o = ontology(node("x", "abcd", ["y"]), node("y", "abcd", ["x"]))
    with pytest.raises(ValueError, match="cycle"):
        check_invariants(o, KEYS, min_size=None)


def test_more_than_one_parent_is_refused_for_a_tree_and_fine_for_a_dag():
    o = ontology(
        node("p1", "abcd"), node("p2", "abcd"), node("kid", "ab", ["p1", "p2"]), method="x"
    )
    check_invariants(o, KEYS, min_size=None)
    with pytest.raises(ValueError, match="must be a forest"):
        check_single_parent(o)


def test_settled_separates_agreed_members_from_contested_ones():
    n = Node(id="n", parents=(), members=(("a", 1.0), ("b", 0.6)), support=0.8)
    assert n.keys == {"a", "b"}
    assert n.settled == {"a"}


def test_unplaced_says_why_a_pathway_is_absent() -> None:
    """A pathway with no description must be REPORTED, not silently missing.

    Two different things put a pathway outside the ontology and they are not the same finding:
    the method saw it and could not place it recurrently, or it never reached the method because
    no description exists. Before the ``reason`` column the second was invisible -- an undescribed
    pathway never entered the embedded key set, so it was in neither the nodes nor ``unplaced``.
    """
    from thema.ontology import export
    from thema.ontology.base import Node, Ontology

    ontology = Ontology(
        method="recurrent_dag",
        params={},
        nodes=(Node(id="n0", parents=(), members=(("a", 1.0), ("b", 1.0)), support=1.0),),
        unplaced=("c", "d"),
    )
    tables = export.rows_for(ontology, {}, None, undescribed={"d"})
    assert tables["unplaced"] == [
        ("c", export.REASON_NOT_RECURRENT),
        ("d", export.REASON_NO_DESCRIPTION),
    ]


def test_unplaced_defaults_to_not_recurrent_when_nothing_is_undescribed() -> None:
    """Omitting ``undescribed`` must not silently relabel every unplaced pathway."""
    from thema.ontology import export
    from thema.ontology.base import Node, Ontology

    ontology = Ontology(
        method="recurrent_dag",
        params={},
        nodes=(Node(id="n0", parents=(), members=(("a", 1.0),), support=1.0),),
        unplaced=("z",),
    )
    assert export.rows_for(ontology, {})["unplaced"] == [("z", export.REASON_NOT_RECURRENT)]
