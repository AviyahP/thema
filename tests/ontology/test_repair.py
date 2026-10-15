"""The two repair fixes, on hand-built cases where the right answer is checkable by eye.

The property that matters most is :func:`test_strict_containment_is_never_merged`: a theme strictly
inside another is hierarchy, and merging it would delete the edge the DAG exists to draw. Both fixes
spare it, exactly as ``consensus.classify`` does, and a regression there would quietly flatten the
ontology rather than fail loudly.
"""

from __future__ import annotations

import random

import numpy as np
import pytest

from thema.ontology import bitset as bits
from thema.ontology.repair import (
    assert_no_chain_pair,
    assert_no_stale_pair,
    collapse_chains,
    merge_stale,
    repair,
    repair_joint,
    stale_pairs,
)

WIDTH = 64


def pack(*members: int) -> np.ndarray:
    """A bitset over ``WIDTH`` bits.

    Args:
        members: Member indices.

    Returns:
        The packed bitset.
    """
    return bits.pack(sorted(members), WIDTH)


def votes(n: int) -> list[dict[int, float]]:
    """``n`` empty inclusion votes.

    Args:
        n: How many.

    Returns:
        One dict per theme.
    """
    return [{} for _ in range(n)]


def sets_of(blocks: list[np.ndarray]) -> list[set[int]]:
    """Member sets, for comparing results.

    Args:
        blocks: Member bitsets.

    Returns:
        One set per theme.
    """
    return [set(bits.unpack(b)) for b in blocks]


def test_strict_containment_is_never_merged() -> None:
    """A child strictly inside a parent is hierarchy, at any Jaccard, under both fixes."""
    parent = pack(*range(10))
    child = pack(*range(7))          # Jaccard 0.7, strictly inside
    got = merge_stale([parent, child], [0.9, 0.8], votes(2))
    assert len(got.members) == 2
    assert not got.merged
    # Collapse spares it too at 90%, because 7/10 is below the share.
    kept = collapse_chains([parent, child], [0.9, 0.8], votes(2), share=0.90)
    assert len(kept.members) == 2


def test_identical_themes_are_merged_keeping_the_higher_support() -> None:
    """Identical sets are the defect the fix exists for."""
    block = pack(1, 2, 3, 4)
    got = merge_stale([block, block.copy()], [0.4, 0.9], votes(2))
    assert len(got.members) == 1
    assert got.supports == [0.9]
    assert got.merged_kind[0] == "identical"


def test_non_nested_overlap_above_the_threshold_is_merged() -> None:
    """Neither contains the other and the Jaccard clears 0.70, so the weaker goes."""
    a = pack(1, 2, 3, 4, 5, 6, 7, 8)
    b = pack(1, 2, 3, 4, 5, 6, 7, 9)          # 7 shared of 9 union = 0.777
    got = merge_stale([a, b], [0.9, 0.5], votes(2))
    assert len(got.members) == 1
    assert sets_of(got.members) == [{1, 2, 3, 4, 5, 6, 7, 8}]
    assert got.merged_kind[1] == "overlap"


def test_non_nested_overlap_below_the_threshold_coexists() -> None:
    """Below 0.70 the two are different themes and both stay."""
    a = pack(1, 2, 3, 4, 5, 6)
    b = pack(1, 2, 3, 7, 8, 9)                 # 3 shared of 9 union = 0.333
    got = merge_stale([a, b], [0.9, 0.5], votes(2))
    assert len(got.members) == 2


def test_collapse_merges_a_child_at_or_above_the_share() -> None:
    """A child holding 90% of its parent is the same theme; the parent's membership survives."""
    parent = pack(*range(10))
    child = pack(*range(9))                    # 9/10 = exactly the declared share
    got = collapse_chains([parent, child], [0.5, 0.8], votes(2), share=0.90)
    assert sets_of(got.members) == [set(range(10))]
    assert got.collapsed == {1: 0}
    assert got.supports == [0.8], "the higher support must win"
    assert got.collapsed_supports[0] == 0.8, "both supports must be recorded"


def test_collapse_keeps_the_parent_membership_not_the_union() -> None:
    """Nothing is invented: the surviving set is the parent's own, unchanged."""
    parent = pack(*range(10))
    child = pack(*range(9))
    got = collapse_chains([parent, child], [0.9, 0.1], votes(2), share=0.90)
    assert sets_of(got.members) == [set(range(10))]
    assert got.supports == [0.9]


def test_collapse_runs_down_a_whole_chain() -> None:
    """Collapsing one link must collapse the rest, not stop after a round."""
    chain = [pack(*range(n)) for n in (12, 11, 10, 9)]
    got = collapse_chains(chain, [0.9, 0.8, 0.7, 0.6], votes(4), share=0.90)
    assert sets_of(got.members) == [set(range(12))]
    assert len(got.collapsed) == 3
    assert got.rounds["collapse"] >= 2


def test_collapse_at_80_percent_is_more_aggressive_than_90() -> None:
    """The reported alternative behaves as its name says; neither is chosen here."""
    parent = pack(*range(10))
    child = pack(*range(8))                    # 0.8: collapsed at 80%, kept at 90%
    assert len(collapse_chains([parent, child], [0.9, 0.5], votes(2), share=0.90).members) == 2
    assert len(collapse_chains([parent, child], [0.9, 0.5], votes(2), share=0.80).members) == 1


def test_repair_leaves_no_stale_pair_and_the_guard_agrees() -> None:
    """The end-to-end fix is checked by the same predicate the build asserts."""
    blocks = [pack(*range(10)), pack(*range(10)), pack(*range(9)),
              pack(1, 2, 3, 4, 5, 6, 7, 20), pack(50, 51, 52)]
    got = repair(blocks, [0.9, 0.4, 0.8, 0.7, 0.6], votes(5))
    assert_no_stale_pair(got.members)
    assert not stale_pairs(got.members)


def test_the_guard_raises_on_an_unrepaired_build() -> None:
    """The assertion is real: an identical pair must be refused."""
    block = pack(1, 2, 3)
    with pytest.raises(ValueError, match="stale pair"):
        assert_no_stale_pair([block, block.copy()])


def test_repair_is_order_collapse_then_merge() -> None:
    """Collapsing can create an identical pair, which the merge pass must then remove.

    Two parents of 10, each with its own 9-member near-copy child. Collapsing both children leaves
    two identical 10-member themes -- a pair that did not exist before the collapse. If the fixes
    ran in the other order, that pair would survive into the build.
    """
    parent = pack(*range(10))
    got = repair([parent, pack(*range(9)), parent.copy(), pack(*range(1, 10))],
                 [0.9, 0.85, 0.5, 0.45], votes(4))
    assert len(got.members) == 1
    assert sets_of(got.members) == [set(range(10))]
    assert_no_stale_pair(got.members)


def test_empty_input_is_handled() -> None:
    """No themes in, no themes out, and no exception."""
    got = repair([], [], [])
    assert got.members == []


# The support survivor rule, declared 9 Oct 2026 for the 0.85 arm. The rule is POST-HOC; these
# tests only check it does what it says, not that it is the right rule.


def test_support_rule_keeps_the_higher_support_child() -> None:
    # grandparent 0-9, parent 0-8, child 0-7: child/parent = 8/9 = 0.889, parent has a parent.
    members = [pack(*range(10)), pack(*range(9)), pack(*range(8))]
    got = collapse_chains(members, [0.9, 0.2, 0.8], votes(3), 0.85, "support")
    assert sets_of(got.members) == [set(range(10)), set(range(8))], (
        "the child outscores the parent 0.8 to 0.2, so the child's membership should survive"
    )
    assert got.collapsed == {1: 2}, "the parent should be absorbed into the child"
    assert got.collapsed_supports[2] == pytest.approx(0.2), "the parent's support is recorded"
    assert got.supports[1] == pytest.approx(0.8), "the higher support is kept"


def test_support_rule_keeps_the_parent_when_the_parent_is_top_level() -> None:
    # Same pair, but now the parent is a root: no live theme strictly contains it.
    members = [pack(*range(9)), pack(*range(8))]
    got = collapse_chains(members, [0.2, 0.8], votes(2), 0.85, "support")
    assert sets_of(got.members) == [set(range(9))], (
        "the parent is top level, so it survives even though the child scores higher"
    )
    assert got.collapsed == {1: 0}
    assert got.supports[0] == pytest.approx(0.8), "the higher support is still kept"


def test_support_rule_keeps_the_parent_on_a_tie() -> None:
    # The grandparent is deliberately too big to qualify (9/12 = 0.75), so the chain stops after
    # one link and the tie-break is what the result shows.
    members = [pack(*range(12)), pack(*range(9)), pack(*range(8))]
    got = collapse_chains(members, [0.9, 0.5, 0.5], votes(3), 0.85, "support")
    assert sets_of(got.members) == [set(range(12)), set(range(9))], (
        "equal supports keep the parent, as declared"
    )
    assert got.collapsed == {2: 1}


def test_parent_rule_is_unchanged_by_the_new_argument() -> None:
    members = [pack(*range(10)), pack(*range(9)), pack(*range(8))]
    supports = [0.9, 0.2, 0.8]
    default = collapse_chains(members, supports, votes(3), 0.85)
    named = collapse_chains(members, supports, votes(3), 0.85, "parent")
    assert sets_of(default.members) == sets_of(named.members)
    assert default.collapsed == named.collapsed == {2: 1, 1: 0}, (
        "keep-the-parent collapses the whole chain into the grandparent"
    )


def test_keeping_the_child_can_break_the_chain_and_collapse_fewer_nodes() -> None:
    # 10 / 9 / 8 with supports 0.9 / 0.2 / 0.8. Keep-the-parent walks the whole chain into the
    # grandparent, two collapses, one survivor. Keep-the-higher-support absorbs the middle into the
    # child, and the surviving child is then only 8/10 = 0.80 of the grandparent, below 0.85, so the
    # chain stops: one collapse, two survivors. The rule is not merely a relabelling of the victim.
    members = [pack(*range(10)), pack(*range(9)), pack(*range(8))]
    supports = [0.9, 0.2, 0.8]
    keep_parent = collapse_chains(members, supports, votes(3), 0.85, "parent")
    keep_support = collapse_chains(members, supports, votes(3), 0.85, "support")
    assert len(keep_parent.collapsed) == 2 and len(keep_support.collapsed) == 1
    assert sets_of(keep_parent.members) == [set(range(10))]
    assert sets_of(keep_support.members) == [set(range(10)), set(range(8))]


def test_no_qualifying_pair_survives_either_rule() -> None:
    # Criterion (a) of the 0.85 arm, as a property: the fixed point leaves no strictly contained
    # child at or above the share. Collapse terminates only when no live pair qualifies.
    members = [pack(*range(20)), pack(*range(18)), pack(*range(17)),
               pack(*range(16)), pack(0, 1, 2, 3)]
    supports = [0.3, 0.9, 0.4, 0.8, 0.6]
    for rule in ("parent", "support"):
        got = collapse_chains(members, supports, votes(5), 0.85, rule)
        alive = sets_of(got.members)
        for child in alive:
            for parent in alive:
                if child < parent:
                    assert len(child) < 0.85 * len(parent), (
                        f"{rule} left a pair at ratio {len(child) / len(parent):.3f}"
                    )


def test_an_unknown_survivor_rule_is_refused() -> None:
    members = [pack(0, 1, 2)]
    with pytest.raises(ValueError, match="survivor must be one of"):
        collapse_chains(members, [1.0], votes(1), 0.85, "whichever")


def test_repair_threads_the_survivor_rule_through() -> None:
    members = [pack(*range(10)), pack(*range(9)), pack(*range(8))]
    got = repair(members, [0.9, 0.2, 0.8], votes(3), 0.85, 0.70, "support")
    assert sets_of(got.members) == [set(range(10)), set(range(8))]


def test_every_surviving_set_was_an_input_set_under_either_rule() -> None:
    # Collapse only ever drops nodes, so a survivor is always one of the originals. That is what
    # makes carrying verdicts from the baseline sound.
    members = [pack(*range(12)), pack(*range(11)), pack(*range(10)), pack(0, 1, 2)]
    before = sets_of(members)
    for rule in ("parent", "support"):
        got = collapse_chains(members, [0.4, 0.9, 0.5, 0.3], votes(4), 0.85, rule)
        for survivor in sets_of(got.members):
            assert survivor in before, f"{rule} invented a new member set"


# The joint fixed point, declared 12 Oct 2026 for the overlap arm. The single-pass repair() is
# unchanged and its tests above still hold; these cover the new loop's contract.
#
# Worth knowing before reading them: because the merge SUPERSEDES the weaker theme rather than
# unioning the pair, no sub-pass ever changes a member set, so the set of qualifying pairs is fixed
# from the start and both sub-passes are already internally fixed points. The loop can therefore
# only change WHICH theme survives, through the support a collapse carries over and through the
# top-level test, never how many invariant violations remain. A 8,000-fixture random search found no
# case where it disagrees with the single pass at all. That is why the arm has an O70 control: it
# measures on real data whether iterating does anything, separately from lowering the cutoff.


def test_the_joint_loop_matches_the_single_pass_when_one_round_settles_it() -> None:
    members = [pack(*range(10)), pack(*range(9)), pack(0, 1, 2)]
    supports = [0.9, 0.5, 0.3]
    once = repair(members, supports, votes(3), 0.85, 0.70)
    joint = repair_joint(members, supports, votes(3), 0.85, 0.70)
    assert sets_of(once.members) == sets_of(joint.members)
    assert joint.rounds["joint"] == 2, "one productive round, then one that changes nothing"


def test_the_joint_loop_is_idempotent() -> None:
    members = [pack(*range(20)), pack(*range(18)), pack(*range(17)), pack(*range(10)),
               pack(*list(range(8)) + [20, 21]), pack(0, 1, 2)]
    supports = [0.3, 0.9, 0.4, 0.8, 0.6, 0.2]
    once = repair_joint(members, supports, votes(6), 0.85, 0.50)
    twice = repair_joint(once.members, once.supports, once.inclusions, 0.85, 0.50)
    assert sets_of(twice.members) == sets_of(once.members)
    assert not twice.collapsed and not twice.merged, "a settled build has nothing left to do"


def test_the_joint_loop_never_removes_fewer_than_the_single_pass() -> None:
    rng = random.Random(20261012)
    for _trial in range(300):
        count = rng.randint(3, 6)
        members = [
            pack(*rng.sample(range(14), rng.randint(3, 9))) for _i in range(count)
        ]
        supports = [round(rng.random(), 3) for _i in range(count)]
        for survivor in ("parent", "support"):
            once = repair(members, supports, votes(count), 0.85, 0.50, survivor)
            joint = repair_joint(members, supports, votes(count), 0.85, 0.50, survivor)
            assert len(joint.members) <= len(once.members)


def test_the_joint_loop_leaves_no_pair_either_rule_would_remove() -> None:
    members = [pack(*range(20)), pack(*range(18)), pack(*range(17)), pack(*range(10)),
               pack(*list(range(8)) + [20, 21]), pack(0, 1, 2)]
    supports = [0.3, 0.9, 0.4, 0.8, 0.6, 0.2]
    got = repair_joint(members, supports, votes(6), 0.85, 0.50)
    alive = sets_of(got.members)
    for left in alive:
        for right in alive:
            if left is right:
                continue
            if left < right:
                assert len(left) < 0.85 * len(right), "a containment pair survived"
            elif not (right < left):
                union = len(left | right)
                assert not union or len(left & right) / union < 0.50, "an overlap pair survived"


def test_the_joint_loop_asserts_both_invariants() -> None:
    nested = [pack(*range(10)), pack(*range(9))]
    with pytest.raises(ValueError, match="containment pair survives"):
        assert_no_chain_pair(nested, 0.85)
    overlap = [pack(0, 1, 2, 3), pack(0, 1, 2, 4)]
    with pytest.raises(ValueError, match="stale pair"):
        assert_no_stale_pair(overlap, 0.50)


def test_provenance_is_keyed_on_the_original_positions() -> None:
    members = [pack(*range(6)), pack(*list(range(5)) + [6]), pack(*range(7))]
    got = repair_joint(members, [0.9, 0.4, 0.8], votes(3), 0.85, 0.50)
    assert sets_of(got.members) == [set(range(7))], "both children collapse into the parent"
    assert got.collapsed == {0: 2, 1: 2}, "keyed on input positions, not on round-local ones"
    assert got.collapsed_supports[2] == pytest.approx(0.9), "the absorbed support is recorded"


def test_a_lower_cutoff_merges_strictly_more() -> None:
    members = [pack(0, 1, 2, 3, 4, 5), pack(0, 1, 2, 3, 6, 7), pack(10, 11, 12)]
    supports = [0.9, 0.4, 0.5]
    high = repair_joint(members, supports, votes(3), 0.85, 0.70)
    low = repair_joint(members, supports, votes(3), 0.85, 0.50)
    assert len(high.members) == 3, "J = 4/8 = 0.5 is below 0.70"
    assert len(low.members) == 2, "and at or above 0.50"
