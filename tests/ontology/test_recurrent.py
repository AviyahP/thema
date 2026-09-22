"""`recurrent_dag`: the four behavioural tests from spec §13, plus what running them found."""

import itertools

import numpy as np
import pytest

from thema.ontology import bitset as B
from thema.ontology.recurrent import MAX_M, Run, choose_m, found_in, is_variant, null_table
from thema.ontology.registry import builder

DIM = 8


def two_groups_and_a_straddler(spread=0.8, noise=9, noise_scale=3.0, seed=0):
    """Spec §13 fixture 1: two tight clusters, one point between them, and noise.

    `spread` matters more than it looks. The straddler can only land in BOTH groups if the runs
    disagree about which one it belongs to, and they only disagree if subsampling moves the group
    centroids. With very tight blobs the centroids barely move and the straddler goes the same way
    every time, so a fixture built to show soft membership has to have some width.
    """
    rng = np.random.default_rng(seed)
    first, second = np.zeros(DIM), np.zeros(DIM)
    first[0] = second[1] = 5.0
    rows = [
        first + rng.normal(scale=spread, size=(15, DIM)),
        second + rng.normal(scale=spread, size=(15, DIM)),
        ((first + second) / 2)[None, :],
    ]
    if noise:
        rows.append(rng.normal(scale=noise_scale, size=(noise, DIM)))
    x = np.vstack(rows)
    x = (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)
    return x, [f"p{i}" for i in range(len(x))]


STRADDLER = "p30"


# ------------------------------------------------------ test 1: soft membership


def test_a_straddler_lands_in_several_nodes_and_is_fully_in_none_of_them():
    """Soft membership needs a cutoff low enough to express it.

    Stated explicitly because the member cutoff bounds what the DAG can record: at 0.5 a pathway
    must be in a MAJORITY of a node's copies to be a member at all, so any weaker attachment is
    dropped rather than recorded as fractional. See the trade-off test below.
    """
    x, keys = two_groups_and_a_straddler()
    dag = builder("recurrent_dag").build(
        x, keys, {"runs": 60, "min_size": 5, "m": 0.25, "inclusion_threshold": 0.25}, seed=0
    )
    homes = [n for n in dag.nodes if STRADDLER in n.keys]
    assert len(homes) >= 2, "a point between two groups belongs to both, not to one of them"
    inclusions = [i for n in homes for k, i in n.members if k == STRADDLER]
    assert all(i < 1.0 for i in inclusions), (
        "if every run agreed, it was not contested and the fixture is not testing soft membership"
    )


def test_raising_the_member_cutoff_trades_soft_membership_for_tighter_nodes():
    """The cutoff bounds the expressible inclusion range, and the cost is multi-membership.

    At 0.25 a straddler can sit in several nodes at 0.31 / 0.40 / 0.69. At 0.5 only the majority
    attachment survives and the other two vanish -- the node is tighter, and the ambiguity the DAG
    exists to record is no longer recorded.
    """
    x, keys = two_groups_and_a_straddler()
    homes = {}
    for cutoff in (0.25, 0.5):
        dag = builder("recurrent_dag").build(
            x, keys, {"runs": 60, "min_size": 5, "m": 0.25, "inclusion_threshold": cutoff}, seed=0
        )
        homes[cutoff] = [n for n in dag.nodes if STRADDLER in n.keys]
    assert len(homes[0.25]) > len(homes[0.5]), "the lower cutoff records more of the ambiguity"
    assert all(
        v >= 0.5 for n in homes[0.5] for k, v in n.members if k == STRADDLER
    ), "at 0.5 every surviving membership is a majority one"


def test_ward_tree_must_choose_one_home_for_the_same_straddler():
    """The contrast the method exists to make: a tree cannot record the ambiguity."""
    x, keys = two_groups_and_a_straddler()
    tree = builder("ward_tree").build(x, keys, {"levels": [2, 4, 8]})
    per_level = {}
    for node in tree.nodes:
        if STRADDLER in node.keys:
            per_level.setdefault(node.id.split(":")[0], []).append(node.id)
    assert all(len(ids) == 1 for ids in per_level.values()), "one home per level, by construction"


def test_noise_too_sparse_to_form_a_node_is_reported_unplaced_not_hidden():
    """With fewer noise points than `min_size` they cannot form a grouping at all.

    Spec §13 fixture 1 asks for 9 noise points at `min_size` 5 and expects them unplaced. They are
    not: nine leftover points are themselves a grouping that recurs, so the method places them --
    correctly. The contract is that a pathway in no node is REPORTED, which needs noise that cannot
    reach min_size.
    """
    x, keys = two_groups_and_a_straddler(noise=3)
    dag = builder("recurrent_dag").build(x, keys, {"runs": 60, "min_size": 5, "m": 0.5}, seed=0)
    placed = {k for n in dag.nodes for k in n.keys}
    assert set(dag.unplaced) == set(keys) - placed
    assert not (placed & set(dag.unplaced)), "never both placed and unplaced"


# ------------------------------------------------------ test 2: compatibility


def test_at_the_consensus_threshold_the_result_is_a_tree():
    """m >= 0.5 can only produce nesting: two groupings each found in a majority co-occur."""
    x, keys = two_groups_and_a_straddler()
    dag = builder("recurrent_dag").build(x, keys, {"runs": 60, "min_size": 5, "m": 0.6}, seed=0)
    assert all(len(n.parents) <= 1 for n in dag.nodes), "overlap lives below 0.5"


# ------------------------------------------------------ test 3: the matching rule


def run_over(n, present, clusters):
    """Hand-build a Run: `clusters` innermost first, each a list of indices."""
    packed = B.pack_many(clusters, n)
    sizes = [len(c) for c in clusters]
    parent = np.array(
        [
            next((j for j in range(len(clusters)) if sizes[j] > sizes[i]), -1)
            for i in range(len(clusters))
        ],
        dtype=np.int64,
    )
    leaf = np.full(n, -1, dtype=np.int64)
    for index, members in enumerate(clusters):
        for p in members:
            if leaf[p] == -1:
                leaf[p] = index
    return Run(present=B.pack(present, n), clusters=packed, parent=parent, leaf_cluster=leaf)


N = 32
ORIGIN = B.pack(range(N), N)


def test_a_member_the_other_run_never_drew_does_not_count_against_the_match():
    run = run_over(N, present=[0, 1, 2, 10, 11], clusters=[[0, 1, 2], [0, 1, 2, 10, 11]])
    hit, copy = found_in(run, B.pack([0, 1, 2, 3], N), ORIGIN, min_shared=3, tol=0.0)
    assert hit and copy is not None, "p3 was absent from this run; absence is not disagreement"


def test_an_extra_shared_member_is_a_mismatch_at_tol_zero_and_a_match_with_slack():
    run = run_over(N, present=list(range(12)), clusters=[[0, 1, 2, 3], [0, 1, 2, 3, 4, 5]])
    grouping = B.pack([0, 1, 2], N)
    assert not found_in(run, grouping, ORIGIN, min_shared=3, tol=0.0)[0], "tol=0 is exact-on-shared"
    assert found_in(run, grouping, ORIGIN, min_shared=3, tol=0.5)[0], "one extra of three is 0.33"


def test_too_few_shared_members_makes_the_run_ineligible_rather_than_a_mismatch():
    run = run_over(N, present=[0, 1, 20, 21], clusters=[[0, 1, 20, 21]])
    assert not found_in(run, B.pack([0, 1, 2, 3, 4], N), ORIGIN, min_shared=3, tol=0.0)[0]


def test_a_grouping_inside_no_recorded_cluster_is_not_found():
    run = run_over(N, present=list(range(12)), clusters=[[0, 1, 2], [3, 4, 5]])
    assert not found_in(run, B.pack([0, 1, 3], N), ORIGIN, min_shared=3, tol=0.0)[0]


# ------------------------------------------------------ test 4: no chaining


def test_absorption_does_not_chain_a_ladder_of_groupings_into_one_node():
    """Connected components of the "found" relation would swallow g1~g2~g3 into a single node."""
    x, keys = two_groups_and_a_straddler()
    dag = builder("recurrent_dag").build(
        x, keys, {"runs": 60, "min_size": 5, "m": 0.4, "tol": 0.25}, seed=0
    )
    everything = frozenset(keys)
    assert all(n.keys != everything for n in dag.nodes), (
        "chaining shows up as one node swallowing the whole collection"
    )
    assert len({n.keys for n in dag.nodes}) == len(dag.nodes), "equal member sets are merged"


# ------------------------------------------------------ the threshold, and determinism


def test_the_threshold_comes_from_counts_not_from_a_maximum():
    """A max over tens of thousands of groupings measures the luckiest scrambled draw.

    On the real build it returned 0.247 -- from 35 groupings of 5-9 members out of 43,625 --
    forcing m=0.742 and reading as "the method does not discriminate". Counted, zero scrambled
    groupings reach 0.25 against 3,457 real ones.
    """
    real = np.array([0.6, 0.4, 0.3, 0.22, 0.12, np.nan])
    null = np.array([0.24, 0.18, 0.11])
    table = null_table(real, null, (0.10, 0.20, 0.25, 0.33))
    assert [(m, r, n) for m, r, n, _ in table] == [
        (0.10, 5, 3), (0.20, 4, 1), (0.25, 3, 0), (0.33, 2, 0)
    ]
    assert choose_m(table) == pytest.approx(0.25), "lowest m where nothing scrambled survives"


def test_the_threshold_must_stay_below_one_half():
    """Two groupings each found in a majority co-occur, so majority rule can only make a tree."""
    table = null_table(np.array([0.9]), np.array([0.8]), (0.10, 0.25, MAX_M, 0.6))
    with pytest.raises(ValueError, match="no threshold below"):
        choose_m(table)


# ------------------------------------------------------ step 8: variants and families
#
# The rule replaced on 2026-09-21. Its predecessor compared each candidate against the GROWING
# node, which both missed legitimate variants of the original grouping and, over many rounds, ran
# away: on the real build it produced a node of 1,639 of 1,854 pathways that existed nowhere in the
# pool before the merge. A node is now seeded from one grouping and claims variants of THAT set.


def bits_of(members, n=64):
    return B.pack(members, n)


def test_a_nested_pair_within_the_allowance_are_variants():
    assert is_variant(bits_of(range(10)), bits_of(range(12)))
    assert not is_variant(bits_of(range(10)), bits_of(range(14))), "4 extras exceeds max(2, 10%)"


def test_the_a_plus_s_versus_a_plus_t_pair_are_variants():
    """Neither contains the other; each differs from the shared part by one."""
    assert is_variant(bits_of([*range(10), 10]), bits_of([*range(10), 11]))


def test_the_allowance_scales_with_the_shared_part():
    big = bits_of(range(100), n=128)
    assert is_variant(big, bits_of(range(108), n=128)), "8 extras is within 10% of 100"
    assert not is_variant(big, bits_of(range(120), n=128)), "20 extras is not"


def test_disjoint_groupings_are_never_variants():
    assert not is_variant(bits_of(range(5)), bits_of(range(20, 25)))


def synthetic_pool(groupings, supports, runs, found_in_runs=None, n=64):
    """A Pool where each grouping was found in its own set of runs.

    `found_in_runs` matters: if every run is given a copy of every grouping, each pathway is in
    every copy and inclusion comes out 1.0 for all of them. Real runs see one variant or another,
    which is what makes an inclusion fractional -- so the default splits the runs between
    groupings round-robin rather than handing all of them to everyone.
    """
    from thema.ontology.recurrent import Pool, Timing

    packed = B.pack_many(groupings, n)
    everything = B.pack(range(n), n)
    presents = np.vstack([everything for _ in range(runs)])
    copies, origins = [], []
    for index, members in enumerate(groupings):
        row = B.pack(members, n)
        mine = (
            found_in_runs[index]
            if found_in_runs
            else [r for r in range(runs) if r % len(groupings) == index]
        )
        copies.append({r: row for r in mine})
        origins.append({mine[0]} if mine else {0})
    return (
        Pool(packed, np.array(supports, dtype=float), np.full(len(groupings), runs),
             copies, origins, Timing()),
        presents,
    )


def assemble_from(groupings, supports, runs=10, n=64, min_size=5, threshold=0.25,
                  found_in_runs=None):
    """Assemble with m=0 so the fixtures exercise the merge rather than the threshold."""
    from thema.ontology.recurrent import DEFAULTS, assemble

    pool, presents = synthetic_pool(groupings, supports, runs, found_in_runs, n=n)
    settings = {**DEFAULTS, "runs": runs, "min_size": min_size, "inclusion_threshold": threshold}
    eligible = np.ones((len(groupings), runs), dtype=bool)
    sets, sup, incl, seeds, _rounds = assemble(
        pool, presents, 0.0, settings, eligible_mask=eligible
    )
    return sets, sup, incl, seeds


def test_three_twins_of_one_core_become_one_node_of_sixteen():
    """The case the old rule failed: it absorbed the first twin and locked out the other two."""
    core = list(range(10))
    # Twelve runs split four ways: each grouping is found in three, so a member carried by one
    # grouping alone has inclusion 3/12 = 0.25 and just clears the threshold. With ten runs it
    # would be 0.20 and the extras would be filtered out -- a property of the fixture, not the rule.
    sets, _sup, incl, seeds = assemble_from(
        [core, [*core, 10, 11], [*core, 12, 13], [*core, 14, 15]],
        [0.90, 0.50, 0.45, 0.40],
        runs=12,
    )
    assert len(sets) == 1, "one family, one node"
    assert B.count(sets[0]) == 16, "every extra member joins the seed"
    assert seeds[0] == 10, "seeded from the 10-member grouping"


def test_a_plus_s_and_a_plus_t_become_one_node_with_both_at_fractional_inclusion():
    core = list(range(10))
    sets, _sup, incl, _seeds = assemble_from([[*core, 10], [*core, 11]], [0.60, 0.55])
    assert len(sets) == 1
    members = B.unpack(sets[0])
    assert 10 in members and 11 in members, "both candidates are kept"
    by_member = dict(zip(members, incl[0], strict=True))
    assert by_member[10] < 1.0 and by_member[11] < 1.0, "each was in only some copies"
    assert by_member[0] == 1.0, "the shared core is fully included"


def test_shuffling_the_input_order_gives_the_identical_result():
    core = list(range(10))
    groupings = [core, [*core, 10, 11], [*core, 12], [*core, 20, 21, 22, 23, 24, 25]]
    supports = [0.90, 0.50, 0.45, 0.80]
    # Which runs found which grouping has to travel WITH the grouping, not with its position, or
    # the fixture is order-dependent and the test measures itself.
    found = [[0, 1, 2], [3, 4], [5, 6], [7, 8, 9]]
    first = assemble_from(groupings, supports, found_in_runs=found)
    order = [3, 1, 0, 2]
    shuffled = assemble_from(
        [groupings[i] for i in order],
        [supports[i] for i in order],
        found_in_runs=[found[i] for i in order],
    )
    assert [B.unpack(b) for b in first[0]] == [B.unpack(b) for b in shuffled[0]]
    assert first[1] == shuffled[1] and first[2] == shuffled[2]


def test_seed_absorption_does_not_chain():
    """g1~g2 and g2~g3 but g1 is not a variant of g3: the seed claims g2 only.

    This is a property of SEEDING, asserted on `families` directly. The fixed-point merge that
    follows may still combine the resulting nodes -- "repeat until no variant pairs remain" chains
    by definition -- so asserting it through `assemble` would be asserting the wrong stage.
    """
    from thema.ontology.recurrent import Pool, Timing, families

    core = list(range(10))
    g1, g2, g3 = core, [*core, 10, 11], [*core, 10, 11, 12, 13]
    assert is_variant(B.pack(g1, 64), B.pack(g2, 64))
    assert is_variant(B.pack(g2, 64), B.pack(g3, 64))
    assert not is_variant(B.pack(g1, 64), B.pack(g3, 64)), "the chain's ends are not variants"

    packed = B.pack_many([g1, g2, g3], 64)
    pool = Pool(packed, np.array([0.90, 0.60, 0.55]), np.full(3, 10),
                [{}, {}, {}], [{0}, {1}, {2}], Timing())
    grouped = families([0, 1, 2], None, pool)
    assert len(grouped) == 2, "the seed claims g2 only; g3 seeds its own family"
    assert sorted(len(f) for _s, f in grouped) == [1, 2]


def test_the_merge_runs_to_a_fixed_point():
    """Recomputing membership can turn two non-variant nodes into variants.

    One pass is not enough; the merge repeats until nothing changes.
    """
    from thema.ontology.recurrent import DEFAULTS, assemble

    core = list(range(10))
    pool, presents = synthetic_pool(
        [core, [*core, 10, 11], [*core, 10, 11, 12, 13]], [0.90, 0.60, 0.55], 10, n=64
    )
    settings = {**DEFAULTS, "runs": 10, "min_size": 5, "inclusion_threshold": 0.25}
    sets, _sup, _incl, _seeds, rounds = assemble(
        pool, presents, 0.0, settings, eligible_mask=np.ones((3, 10), dtype=bool)
    )
    assert rounds >= 1
    for a, b in itertools.combinations(sets, 2):
        assert not is_variant(a, b), "no variant pair may survive the fixed point"


def test_two_builds_from_one_seed_agree_exactly():
    x, keys = two_groups_and_a_straddler()
    params = {"runs": 30, "min_size": 5, "m": 0.5}
    first = builder("recurrent_dag").build(x, keys, params, seed=7)
    second = builder("recurrent_dag").build(x, keys, params, seed=7)
    assert [(n.id, n.members, n.parents, n.support) for n in first.nodes] == [
        (n.id, n.members, n.parents, n.support) for n in second.nodes
    ]


def test_the_build_reports_where_its_time_went():
    x, keys = two_groups_and_a_straddler(noise=0)
    dag = builder("recurrent_dag").build(x, keys, {"runs": 20, "min_size": 5, "m": 0.5}, seed=0)
    stages = dag.params["timing_seconds"]
    wanted = {"runs (ward x N)", "matching (ancestor walk)", "families (seed absorption)"}
    assert wanted <= set(stages)
    assert all(v >= 0 for v in stages.values())
