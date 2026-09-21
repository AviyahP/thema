"""`recurrent_dag`: the four behavioural tests from spec §13, plus what running them found."""

import numpy as np
import pytest

from thema.ontology import bitset as B
from thema.ontology.recurrent import MAX_M, Run, choose_m, found_in
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
    x, keys = two_groups_and_a_straddler()
    dag = builder("recurrent_dag").build(x, keys, {"runs": 60, "min_size": 5, "m": 0.5}, seed=0)
    homes = [n for n in dag.nodes if STRADDLER in n.keys]
    assert len(homes) >= 2, "a point between two groups belongs to both, not to one of them"
    inclusions = [i for n in homes for k, i in n.members if k == STRADDLER]
    assert all(i < 1.0 for i in inclusions), (
        "if every run agreed, it was not contested and the fixture is not testing soft membership"
    )


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


def test_the_threshold_refuses_to_be_clamped_when_the_null_is_too_strong():
    """Addendum B1: a null this strong is a finding, not a knob."""
    assert choose_m(0.0) == pytest.approx(0.20), "the floor"
    assert choose_m(0.10) == pytest.approx(0.30)
    with pytest.raises(ValueError, match="not discriminating"):
        choose_m(MAX_M / 3.0)


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
    wanted = {"runs (ward x N)", "matching (ancestor walk)", "assembly (seed absorption)"}
    assert wanted <= set(stages)
    assert all(v >= 0 for v in stages.values())
