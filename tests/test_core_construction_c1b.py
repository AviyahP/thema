"""C1b: the mutual core rule, the p solver and the per-stratum thresholds.

Two properties of the merge are declared and are asserted here on fixtures, because both are easy
to lose and invisible in aggregate counts. **It never chains**: if A claims B because each one's
core sits inside the other's members, C is judged against A's own core and members, never against
the family A and B have grown into. **It is order-stable**: identical inputs give identical
families, which is what makes a build reproducible at all.

The third declared test -- that flat 0.70, p = 0.5, no core step and the twin rule restored
reproduces O50s's pre-gate families -- needs the 200 cached trees and is
``scripts/core_construction_c1b.py --reproduce``; it passed at 99,951 candidates, membership
identical.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

import core_construction_c1b as c1b

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_the_copy_minimum_is_retired() -> None:
    """The amendment of 20 Oct 2026 removed it; the constant survives only as a name."""
    assert not hasattr(c1b, "MIN_COPIES")
    assert c1b.MIN_COPIES_RETIRED == 10


def test_the_thresholds_are_prompt_47s_choice() -> None:
    """0.70 below 10 pathways, 0.50 for 10-19, 0.60 for 20-39, 0.50 from 40 up."""
    assert len(c1b.THETA) == len(c1b.STRATA)
    assert c1b.theta_for(3) == 0.70
    assert c1b.theta_for(9) == 0.70
    assert c1b.theta_for(10) == 0.50
    assert c1b.theta_for(19) == 0.50
    assert c1b.theta_for(20) == 0.60
    assert c1b.theta_for(39) == 0.60
    assert c1b.theta_for(40) == 0.50
    assert c1b.theta_for(5000) == 0.50
    assert sorted(set(c1b.THETA)) == [0.50, 0.60, 0.70]


def test_the_strata_are_o50ss_thirteen() -> None:
    import o50s_build as o50s

    assert c1b.STRATA == o50s.O50S_STRATA
    assert c1b.stratum_of(2) == -1
    assert c1b.label(1280, 10 ** 9) == "1280+"


def test_the_p_grid_is_the_declared_sweep() -> None:
    assert c1b.PS[0] == 0.10
    assert c1b.PS[-1] == 0.85
    assert len(c1b.PS) == 16
    assert all(round(b - a, 10) == 0.05 for a, b in zip(c1b.PS, c1b.PS[1:], strict=False))
    assert c1b.P_NONE == 0.90 == c1b.CORE, "p = 0.9 means members equal the core"


def test_mask_round_trips_run_indices() -> None:
    mask = c1b.mask_of([0, 63, 64, 199])
    assert int(np.bitwise_count(mask).sum()) == 4
    assert mask[0] & np.uint64(1)
    assert mask[3] & (np.uint64(1) << np.uint64(199 % 64))


def _merge(cores: list[list[int]], members: list[list[int]],
           support: list[float] | None = None) -> list[list[int]]:
    """Run the rule on a fixture."""
    n = 1 + max((p for one in members for p in one), default=0)
    return c1b.merge_mutual(
        [np.array(c, dtype=np.int32) for c in cores],
        [np.array(m, dtype=np.int32) for m in members],
        np.array(support if support else [1.0] * len(cores), dtype=np.float64),
        np.array([len(m) for m in members], dtype=np.int64), n, report=False)


def test_the_rule_claims_a_mutual_pair() -> None:
    """Each one's core inside the other's members, so they are one theme."""
    fams = _merge(cores=[[1, 2], [1, 2]], members=[[1, 2, 3], [1, 2, 4]])
    assert len(fams) == 1
    assert sorted(fams[0]) == [0, 1]


def test_the_rule_refuses_a_one_sided_pair() -> None:
    """B's core is inside A's members, but A's core is not inside B's: not the same theme."""
    fams = _merge(cores=[[1, 2, 5], [1, 2]], members=[[1, 2, 5], [1, 2, 3]])
    assert len(fams) == 2, "the rule is mutual, so a one-sided containment is not enough"


def test_the_rule_never_chains() -> None:
    """A-B mutual and B-C mutual, but A-C not: C must NOT join A's family.

    The seed is A. B qualifies against A. C qualifies against B but not against A, and because the
    comparison is always with the seed's own core and members, C is left for its own family.
    """
    cores = [[1], [1], [1]]
    members = [[1, 2], [1, 2, 3], [1, 3]]
    # A = 0 (core {1}, members {1,2}); C = 2 (core {1}, members {1,3}).
    # core(C) = {1} is inside members(A); core(A) = {1} is inside members(C) -- so with these sets
    # A and C would in fact be mutual. Use sets where they are not.
    cores = [[1, 2], [1, 2], [1, 3]]
    members = [[1, 2, 9], [1, 2, 3, 9], [1, 3, 9]]
    fams = _merge(cores, members, support=[3.0, 2.0, 1.0])
    seeded = {family[0]: sorted(family) for family in fams}
    assert 0 in seeded, "the highest-support grouping seeds first"
    assert 2 not in seeded[0], "C is judged against the seed, not against the grown family"
    assert any(2 in family for family in fams)
    assert sum(len(family) for family in fams) == 3, "every grouping lands in exactly one family"


def test_the_rule_is_order_stable_for_identical_inputs() -> None:
    cores = [[1, 2], [1, 2], [4, 5], [4, 5], [7]]
    members = [[1, 2, 3], [1, 2, 8], [4, 5, 6], [4, 5, 9], [7, 10]]
    first = _merge(cores, members)
    for _ in range(5):
        assert _merge(cores, members) == first


def test_the_rank_order_decides_which_grouping_seeds() -> None:
    """Support descending, then size descending -- today's order."""
    cores = [[1, 2], [1, 2]]
    members = [[1, 2, 3], [1, 2, 3, 4]]
    low_first = _merge(cores, members, support=[0.1, 0.9])
    assert low_first[0][0] == 1, "the higher-support grouping seeds"
    tied = _merge(cores, members, support=[0.5, 0.5])
    assert tied[0][0] == 1, "on a tie the larger member set seeds"


def test_every_grouping_lands_in_exactly_one_family() -> None:
    rng = np.random.default_rng(7)
    for _ in range(20):
        count = int(rng.integers(3, 12))
        cores, members = [], []
        for _ in range(count):
            core = sorted(rng.choice(12, size=int(rng.integers(1, 4)), replace=False).tolist())
            extra = sorted(rng.choice(12, size=int(rng.integers(0, 4)), replace=False).tolist())
            cores.append(core)
            members.append(sorted(set(core) | set(extra)))
        fams = _merge(cores, members)
        seen = [g for family in fams for g in family]
        assert sorted(seen) == list(range(count))
        assert len(seen) == len(set(seen))


def test_a_grouping_with_an_empty_core_stands_alone() -> None:
    fams = _merge(cores=[[], [1]], members=[[1, 2], [1, 2]])
    assert len(fams) == 2, "an empty core claims nobody"


def test_solve_p_takes_the_lowest_cut_reaching_the_target() -> None:
    """R(p) and N(p) are counts of extras; p is the lowest cut whose ratio reaches 0.008."""
    real = np.zeros((len(c1b.STRATA), len(c1b.PS)), dtype=np.int64)
    null = np.zeros_like(real)
    # In stratum 0: at p = 0.10 the ratio is 10/1000 = 0.01 (too high); at 0.15 it is 5/1000.
    real[0, 0] = 1000
    real[0, 1] = 1000
    null[0, 0] = 10
    null[0, 1] = 5
    table = c1b.solve_p(real, [null])
    assert table[0]["p"] == 0.15
    assert table[0]["ratio"] == pytest.approx(0.005)
    assert table[0]["real_at_p"] == 1000


def test_solve_p_falls_back_to_the_core_when_no_cut_qualifies() -> None:
    real = np.ones((len(c1b.STRATA), len(c1b.PS)), dtype=np.int64) * 100
    null = np.ones_like(real) * 50
    table = c1b.solve_p(real, [null])
    assert all(entry["p"] == c1b.P_NONE for entry in table), "members fall back to the core"
    assert all(entry["ratio"] is None for entry in table)


def test_solve_floors_uses_the_rule_of_three_on_an_observed_zero() -> None:
    real = [(15, 0.5)] * 100
    nulls = [[(15, 0.1)] for _ in range(10)]
    solved = c1b.solve_floors(real, nulls)
    entry = solved[c1b.stratum_of(15)]
    assert entry["effective"] == 0.5
    assert entry["bounded"] is True
    assert entry["calibration_fdr"] == pytest.approx(0.3 / 100)


def test_a_floorless_stratum_contributes_nothing_to_the_held_out_rate() -> None:
    solved = [{"stratum": c1b.label(*s), "effective": None} for s in c1b.STRATA]
    got = c1b.confirm_floors([(15, 0.9)], [[(15, 0.9)]], solved)
    assert got["overall_fdr"] is None
    assert all(e["heldout_fdr"] is None for e in got["strata"])
    assert all(e["heldout_real"] == 0 for e in got["strata"])


def test_every_grouping_gets_a_core_however_few_copies() -> None:
    """The amendment of 20 Oct: the 10-copy minimum is retired.

    The grouping with 3 copies no longer short-circuits to its own set -- its core is the majority
    of those copies, so the 0.2 pathway is excluded just as it is for the 50-copy grouping.
    """
    side = {
        "indptr": np.array([0, 3, 6], dtype=np.int64),
        "keys": np.array([1, 2, 3, 4, 5, 6], dtype=np.int32),
        "vals": np.array([1.0, 0.95, 0.2, 1.0, 0.95, 0.2], dtype=np.float32),
        "sizes": np.array([15, 15], dtype=np.int32),
        "n_copies": np.array([50, 3], dtype=np.int64),
        "own": [np.array([1, 2, 3], dtype=np.int32), np.array([4, 5, 6], dtype=np.int32)],
    }
    p = [0.5] * len(c1b.STRATA)
    got = c1b.core_and_members(side, p)
    assert sorted(got["cores"][0].tolist()) == [1, 2]
    assert sorted(got["cores"][1].tolist()) == [4, 5], "the 3-copy grouping gets a core too"
    assert sorted(got["members"][1].tolist()) == [4, 5], "0.2 is below p, so it is not a member"


def test_a_single_copy_grouping_has_its_own_set_as_its_core() -> None:
    """The amendment and the retired rule agree here, which is worth pinning down.

    One copy is the grouping's own appearance, which ``family_members`` already counts, so every
    member sits at inclusion 1.0 and the core is the whole set.
    """
    side = {
        "indptr": np.array([0, 3], dtype=np.int64),
        "keys": np.array([7, 8, 9], dtype=np.int32),
        "vals": np.array([1.0, 1.0, 1.0], dtype=np.float32),
        "sizes": np.array([3], dtype=np.int32),
        "n_copies": np.array([1], dtype=np.int64),
        "own": [np.array([7, 8, 9], dtype=np.int32)],
    }
    got = c1b.core_and_members(side, [0.5] * len(c1b.STRATA))
    assert sorted(got["cores"][0].tolist()) == [7, 8, 9]
    assert sorted(got["members"][0].tolist()) == [7, 8, 9]
    assert int(got["core_exact"][0]) == 3


def test_core_and_members_admits_an_extra_that_clears_p() -> None:
    side = {
        "indptr": np.array([0, 3], dtype=np.int64),
        "keys": np.array([1, 2, 3], dtype=np.int32),
        "vals": np.array([1.0, 0.95, 0.6], dtype=np.float32),
        "sizes": np.array([15], dtype=np.int32),
        "n_copies": np.array([50], dtype=np.int64),
        "own": [np.array([1, 2, 3], dtype=np.int32)],
    }
    p = [0.5] * len(c1b.STRATA)
    got = c1b.core_and_members(side, p)
    assert sorted(got["members"][0].tolist()) == [1, 2, 3]
    assert sorted(got["cores"][0].tolist()) == [1, 2]
    assert int(got["core_exact"][0]) == 1, "only pathway 1 is at inclusion 1.0"


def test_extras_histogram_counts_every_grouping_after_the_amendment() -> None:
    """The retired minimum used to exclude groupings under 10 copies from the sweep entirely."""
    few = {
        "indptr": np.array([0, 2], dtype=np.int64),
        "keys": np.array([5, 6], dtype=np.int32),
        "vals": np.array([1.0, 0.4], dtype=np.float32),
        "sizes": np.array([15], dtype=np.int32),
        "n_copies": np.array([2], dtype=np.int64),
        "own": [np.array([5, 6], dtype=np.int32)],
    }
    row = c1b.extras_histogram(few)[c1b.stratum_of(15)]
    assert row[0] == 1, "a 2-copy grouping now contributes its extras"
    assert row[c1b.PS.index(0.40)] == 1
    assert row[c1b.PS.index(0.45)] == 0


def test_extras_histogram_counts_only_sub_core_inclusions() -> None:
    side = {
        "indptr": np.array([0, 4], dtype=np.int64),
        "keys": np.array([1, 2, 3, 4], dtype=np.int32),
        "vals": np.array([1.0, 0.5, 0.3, 0.11], dtype=np.float32),
        "sizes": np.array([15], dtype=np.int32),
        "n_copies": np.array([50], dtype=np.int64),
        "own": [np.array([1, 2, 3, 4], dtype=np.int32)],
    }
    got = c1b.extras_histogram(side)
    row = got[c1b.stratum_of(15)]
    assert row[0] == 3, "at p = 0.10 all three extras count; the 1.0 is core, not an extra"
    assert row[c1b.PS.index(0.50)] == 1
    assert row[-1] == 0, "none reaches 0.85"


@pytest.mark.parametrize("seed", range(8))
def test_immediate_parents_agrees_with_hasse(seed: int) -> None:
    """The substitution C1b makes for scale must compute the same relation.

    ``hasse`` walks every ordered pair in Python, which at 73,484 themes is hours of work.
    ``immediate_parents`` takes each theme's candidates from the holders of its rarest member and
    keeps the minimal supersets. Same definition, so the two must agree exactly.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import hasse

    rng = np.random.default_rng(900 + seed)
    n = 40
    count = int(rng.integers(8, 30))
    members = []
    for _ in range(count):
        size = int(rng.integers(1, 10))
        members.append(np.sort(rng.choice(n, size=size, replace=False)).astype(np.int32))
    width = bits.words_for(n) * bits.WORD
    blocks = [bits.pack(sorted(m.tolist()), width) for m in members]
    assert c1b.immediate_parents(members, n, report=False) == hasse(blocks)


def test_immediate_parents_handles_nesting_and_equal_sets() -> None:
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import hasse

    members = [np.array([0], dtype=np.int32), np.array([0, 1], dtype=np.int32),
               np.array([0, 1, 2], dtype=np.int32), np.array([0, 1], dtype=np.int32)]
    width = bits.words_for(8) * bits.WORD
    blocks = [bits.pack(sorted(m.tolist()), width) for m in members]
    got = c1b.immediate_parents(members, 8, report=False)
    assert got == hasse(blocks)
    assert got[0] == (1, 3), "both equal-sized supersets are immediate parents"
    assert got[1] == (2,) and got[3] == (2,)
    assert got[2] == ()


# An NpzFile decompresses the whole array on every subscript, and a slice of the result keeps that
# copy alive as its base. So `handle["keys"][a:b] for i in ...` holds one full copy per slice: the
# real side's cache turned 0.6 GB of members into an 18 GB peak and was killed three times before
# the cause was found. It is invisible in the output -- the arrays are correct -- so only a source
# check catches it, and it must walk the AST: the offending expression nests brackets, so a regex
# over the comprehension text misses exactly the case that matters.
def npz_handles_subscripted_in_comprehensions(source: str) -> list[str]:
    """Every ``handle["k"][...]`` that sits inside a comprehension, as source segments."""
    tree = ast.parse(source)
    found: list[str] = []
    comprehensions = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
    for node in ast.walk(tree):
        if not isinstance(node, comprehensions):
            continue
        for inner in ast.walk(node):
            if (isinstance(inner, ast.Subscript)
                    and isinstance(inner.value, ast.Subscript)
                    and isinstance(inner.value.value, ast.Name)
                    and inner.value.value.id == "handle"):
                found.append(ast.get_source_segment(source, inner) or "handle[...][...]")
    return found


def test_the_guard_fails_on_the_code_that_caused_the_kill() -> None:
    """The pre-fix expression, verbatim. A guard unproven against the bug is not a guard."""
    bad = ('def f(handle, indptr):\n'
           '    return [handle["keys"][indptr[i]:indptr[i + 1]]\n'
           '            for i in range(len(indptr) - 1)]\n')
    assert npz_handles_subscripted_in_comprehensions(bad) != []
    good = ('def f(handle, indptr):\n'
            '    keys = handle["keys"]\n'
            '    return [keys[indptr[i]:indptr[i + 1]] for i in range(len(indptr) - 1)]\n')
    assert npz_handles_subscripted_in_comprehensions(good) == []


def test_no_npz_handle_is_subscripted_inside_a_comprehension() -> None:
    source = (REPO_ROOT / "scripts" / "core_construction_c1b.py").read_text()
    offenders = npz_handles_subscripted_in_comprehensions(source)
    assert offenders == [], (
        "hoist the array out of the comprehension; each subscript decompresses it afresh "
        f"and every slice pins a copy: {offenders}"
    )


def test_the_real_side_cache_round_trips_to_the_same_memberships() -> None:
    """Writing the streamed real-side cache and reading it back must change nothing."""
    rng = np.random.default_rng(11)
    sizes = rng.integers(3, 9, size=40)
    members = [np.sort(rng.choice(200, size=int(s), replace=False)).astype(np.int32)
               for s in sizes]
    inclusion = [rng.random(int(s)).astype(np.float32) for s in sizes]

    indptr = np.zeros(len(members) + 1, dtype=np.int64)
    np.cumsum([len(m) for m in members], out=indptr[1:])
    keys = np.concatenate(members)
    vals = np.concatenate(inclusion)

    back_m = [keys[indptr[i]:indptr[i + 1]] for i in range(len(indptr) - 1)]
    back_v = [vals[indptr[i]:indptr[i + 1]] for i in range(len(indptr) - 1)]
    assert [m.tolist() for m in back_m] == [m.tolist() for m in members]
    assert [v.tolist() for v in back_v] == [v.tolist() for v in inclusion]
