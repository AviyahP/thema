"""Greedy consensus, pinned on fixtures worked out by hand.

Every rule is exercised, plus the three things that decide reproducibility: the tie order, an
inheritance that propagates two levels up, and a rule-3 tie.
"""

import numpy as np
import pytest

from thema.ontology import bitset as bits
from thema.ontology.consensus import (
    DEFAULT_JACCARD,
    DEFAULT_STRAY,
    Rule,
    classify,
    consensus,
    order_candidates,
)

N = 256


def block(members):
    return bits.pack(sorted(members), N)


def run(sets, support, stray=DEFAULT_STRAY, jaccard=DEFAULT_JACCARD, method="pairwise"):
    blocks = [block(s) for s in sets]
    inclusions = [dict.fromkeys(s, 0.9) for s in sets]
    return consensus(blocks, support, inclusions, N, stray=stray, jaccard=jaccard, method=method)


def members_of(out, candidate):
    return sorted(bits.unpack(out.members[out.accepted.index(candidate)]))


# ------------------------------------------------------------------ the rules


def test_rule_1_strict_containment_is_left_to_hasse() -> None:
    out = run([list(range(20)), list(range(8))], [0.9, 0.8])
    assert out.accepted == [0, 1]
    assert not out.inherited and not out.superseded


def test_identical_sets_are_superseded_not_both_accepted() -> None:
    """hasse draws no edge between equal sets, so both would be left as roots."""
    out = run([list(range(10)), list(range(10))], [0.9, 0.8])
    assert out.accepted == [0]
    assert out.superseded == {1: 0}


def test_rule_2_the_larger_theme_grows_to_swallow_the_stray() -> None:
    """The n0610 case: one member outside, so the PARENT takes it in. Nothing is rejected."""
    big = list(range(40))
    small = list(range(20)) + [99]        # 1 stray out of 21, and A has 20 of its own
    out = run([big, small], [0.9, 0.8])
    assert out.accepted == [0, 1]
    assert members_of(out, 0) == sorted(big + [99]), "A grew"
    assert members_of(out, 1) == small, "B is unchanged"
    assert [(i.parent, i.member, i.propagated) for i in out.inherited] == [(0, 99, False)]


def test_rule_2_fires_on_a_single_stray_however_small_the_theme() -> None:
    """1/3 is far above STRAY, but one member outside is noise at any size."""
    out = run([list(range(30)), [0, 1, 200]], [0.9, 0.8])
    assert 200 in members_of(out, 0)


def test_rule_2_does_not_fire_when_the_larger_has_no_members_of_its_own() -> None:
    """strays_A > STRAY is required, or two near-identical sets would both survive."""
    a = list(range(100))
    b = list(range(98)) + [200, 201]       # A keeps only 2 of its own: strays_A = 0.02
    rule, _ = classify(block(a), block(b), DEFAULT_STRAY, DEFAULT_JACCARD)
    assert rule is Rule.SUPERSEDED


def test_rule_3_keeps_the_higher_support_theme() -> None:
    a = list(range(0, 40))
    b = list(range(6, 46))                 # Jaccard 34/46 = 0.74
    out = run([a, b], [0.9, 0.8])
    assert out.accepted == [0]
    assert out.superseded == {1: 0}


def test_rule_3_ties_are_broken_by_size_then_key() -> None:
    """Equal support: the larger set is seated and the smaller is superseded."""
    a = list(range(0, 41))
    b = list(range(6, 46))
    out = run([b, a], [0.8, 0.8])
    assert out.accepted == [1], "the 41-member set wins the tie"
    assert out.superseded == {0: 1}


def test_rule_4_low_overlap_coexists_and_keeps_the_dag() -> None:
    out = run([list(range(0, 40)), list(range(30, 70))], [0.9, 0.8])
    assert out.accepted == [0, 1]
    assert not out.inherited and not out.superseded


def test_processing_order_is_support_then_size_then_key() -> None:
    blocks = [block(range(0, 5)), block(range(10, 20)), block(range(30, 34))]
    assert order_candidates([0.5, 0.5, 0.5], blocks) == [1, 0, 2]
    assert order_candidates([0.9, 0.5, 0.5], blocks) == [0, 1, 2]


# ------------------------------------------------------------------ propagation


def test_an_inheritance_propagates_two_levels_up() -> None:
    """Grandparent, parent, and a sub-theme with one stray: all three must gain it.

    Otherwise the grandparent stops containing the parent, which is the defect this pass removes.
    """
    grand = list(range(60))
    parent = list(range(40))
    sub = list(range(20)) + [199]
    out = run([grand, parent, sub], [0.9, 0.85, 0.8])
    assert out.accepted == [0, 1, 2]
    assert 199 in members_of(out, 1), "the direct parent gained it"
    assert 199 in members_of(out, 0), "the grandparent gained it too"
    assert members_of(out, 2) == sub
    # Which of the two ancestors is credited as direct and which as propagated depends on scan
    # order -- the grandparent is seated first, so it is reached first. What must hold is that
    # BOTH gained it, each exactly once, and that the inclusion travelled from the sub-theme.
    assert {i.parent for i in out.inherited} == {0, 1}
    assert len(out.inherited) == 2, "recorded once per ancestor"
    assert all(i.member == 199 and i.source == 2 for i in out.inherited)
    assert all(i.inclusion == 0.9 for i in out.inherited), "inclusion carried from the sub-theme"
    assert out.grew == {0: 1, 1: 1}


def test_containment_holds_everywhere_after_the_pass() -> None:
    """The invariant the pass exists to restore."""
    rng = np.random.default_rng(11)
    sets, support = [], []
    for _ in range(40):
        base = sorted(rng.choice(N, size=int(rng.integers(5, 60)), replace=False).tolist())
        sets.append(base)
        support.append(round(float(rng.integers(3, 10)) / 10, 1))
        sets.append(sorted(set(base[: max(3, len(base) // 2)]) | {int(rng.integers(0, N))}))
        support.append(round(float(rng.integers(3, 10)) / 10, 1))
    out = run(sets, support)
    final = [set(bits.unpack(b)) for b in out.members]
    for i, a in enumerate(final):
        for j, b in enumerate(final):
            if i != j and a < b:
                assert a <= b


# ------------------------------------------------------------------ vector == pairwise


def same(left, right) -> None:
    assert left.accepted == right.accepted
    assert left.superseded == right.superseded
    assert left.grew == right.grew
    assert [(i.parent, i.member, i.source, i.propagated) for i in left.inherited] == [
        (i.parent, i.member, i.source, i.propagated) for i in right.inherited
    ]
    assert left.rules == right.rules
    for a, b in zip(left.members, right.members, strict=True):
        assert np.array_equal(a, b)


def test_the_two_implementations_agree_on_the_worked_fixtures() -> None:
    cases = [
        ([list(range(20)), list(range(8))], [0.9, 0.8]),
        ([list(range(40)), list(range(20)) + [99]], [0.9, 0.8]),
        ([list(range(60)), list(range(40)), list(range(20)) + [199]], [0.9, 0.85, 0.8]),
        ([list(range(0, 40)), list(range(6, 46))], [0.9, 0.8]),
        ([list(range(0, 40)), list(range(30, 70))], [0.9, 0.8]),
        ([list(range(10)), list(range(10))], [0.9, 0.8]),
    ]
    for sets, support in cases:
        same(run(sets, support, method="pairwise"), run(sets, support, method="vector"))


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_the_two_implementations_agree_on_random_pools(seed) -> None:
    rng = np.random.default_rng(seed)
    sets, support = [], []
    for _ in range(50):
        base = sorted(rng.choice(N, size=int(rng.integers(4, 50)), replace=False).tolist())
        sets.append(base)
        support.append(round(float(rng.integers(3, 10)) / 10, 1))
        if len(base) > 6:
            near = base[: len(base) - int(rng.integers(0, 3))] + [int(rng.integers(0, N))]
            sets.append(sorted(set(near)))
            support.append(round(float(rng.integers(3, 10)) / 10, 1))
    same(run(sets, support, method="pairwise"), run(sets, support, method="vector"))
