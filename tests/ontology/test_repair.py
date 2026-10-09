"""The two repair fixes, on hand-built cases where the right answer is checkable by eye.

The property that matters most is :func:`test_strict_containment_is_never_merged`: a theme strictly
inside another is hierarchy, and merging it would delete the edge the DAG exists to draw. Both fixes
spare it, exactly as ``consensus.classify`` does, and a regression there would quietly flatten the
ontology rather than fail loudly.
"""

from __future__ import annotations

import numpy as np
import pytest

from thema.ontology import bitset as bits
from thema.ontology.repair import (
    assert_no_stale_pair,
    collapse_chains,
    merge_stale,
    repair,
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
