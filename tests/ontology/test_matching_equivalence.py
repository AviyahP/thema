"""The two matching implementations must agree exactly, on a fixture computed by hand.

``score`` has two implementations: the original per-(grouping, run) ancestor walk and the sparse
matrix formulation that replaced it. The matrix version exists only for speed, so the standard it
is held to is not "reasonable" but "identical". This module pins both against an answer worked out
on paper, then asserts they agree on randomly generated builds.

The fixture is small enough to verify by hand and still exercises every branch that matters: the
origin shortcut, a real Jaccard decision, a cover tie broken by cluster size, and a theta that
flips half the answers.
"""

import numpy as np
import pytest

from thema.ontology import bitset as bits
from thema.ontology import recurrent
from thema.ontology.recurrent import DEFAULTS, Prepared, Run, prepare, score

N = 10


def _run(present: list[int], clusters: list[list[int]]) -> Run:
    """Build one run from explicit cluster member lists.

    Args:
        present: The pathways this run drew.
        clusters: The recorded clusters, each a member list, smallest-first within a chain.

    Returns:
        The run record, with parents, leaf pointers, sizes and chains derived.
    """
    packed = np.vstack([bits.pack(c, N) for c in clusters])
    sets = [set(c) for c in clusters]
    parent = np.full(len(clusters), -1, dtype=np.int64)
    for i, a in enumerate(sets):
        containing = [
            (len(b), j) for j, b in enumerate(sets) if j != i and a < b
        ]
        if containing:
            parent[i] = min(containing)[1]
    leaf = np.full(N, -1, dtype=np.int64)
    for pathway in range(N):
        holders = [(len(s), j) for j, s in enumerate(sets) if pathway in s]
        if holders:
            leaf[pathway] = min(holders)[1]
    indptr = np.zeros(N + 1, dtype=np.int64)
    chain: list[int] = []
    for pathway in range(N):
        at = int(leaf[pathway])
        this: list[int] = []
        while at != -1:
            this.append(at)
            at = int(parent[at])
        chain.extend(this)
        indptr[pathway + 1] = indptr[pathway] + len(this)
    return Run(
        present=bits.pack(present, N),
        clusters=packed,
        parent=parent,
        leaf_cluster=leaf,
        sizes=bits.count_rows(packed),
        chain_indptr=indptr,
        chain_idx=np.asarray(chain, dtype=np.int64),
    )


def _prepared(records: list[Run], min_shared: int) -> Prepared:
    """Assemble a Prepared from hand-built runs, the way :func:`prepare` does.

    Args:
        records: The runs.
        min_shared: Eligibility floor.

    Returns:
        The prepared object.
    """
    groupings, origins, cluster_pool = recurrent._dedup(records, N)
    present = np.vstack([r.present for r in records])
    overlap = np.bitwise_count(groupings[:, None, :] & present[None, :, :]).sum(axis=2)
    mask = overlap >= min_shared
    return Prepared(
        records, present, groupings, origins, mask, mask.sum(axis=1),
        overlap.astype(np.int32), cluster_pool, recurrent.Timing(),
    )


@pytest.fixture
def worked_example() -> Prepared:
    """Two runs whose whole matching outcome is worked out in the module docstring table."""
    first = _run([0, 1, 2, 3, 4, 5, 6, 7], [[0, 1, 2], [3, 4]])
    second = _run([0, 1, 2, 3, 4, 5, 6, 9], [[0, 1, 2, 3], [4, 5]])
    return _prepared([first, second], min_shared=2)


# Pool order is run 0's clusters then run 1's new ones: A={0,1,2}, F={3,4}, E={0,1,2,3}, G={4,5}.
#
#   A judged by run 1: shared |A & p1| = 3, best candidate E (cover 3), extras |E & p0 & ~A| = 1,
#                      union 4, Jaccard 0.75.
#   E judged by run 0: shared 4, candidates A (cover 3) and F (cover 1), best A, extras 0,
#                      union 4, Jaccard 0.75.
#   F judged by run 1: shared 2, candidates E (cover 1) and G (cover 1) -- A TIE, broken toward
#                      the smaller cluster, so G. extras |G & p0 & ~F| = 1, union 3, Jaccard 1/3.
#   G judged by run 0: shared 2, only candidate F (cover 1), extras 1, union 3, Jaccard 1/3.
#
# Each grouping is also found in its own origin run by definition.
BY_HAND = {
    0.70: {"A": 1.0, "F": 0.5, "E": 1.0, "G": 0.5},
    0.80: {"A": 0.5, "F": 0.5, "E": 0.5, "G": 0.5},
}


@pytest.mark.parametrize("theta", [0.70, 0.80])
@pytest.mark.parametrize("matching", ["tree", "matrix"])
def test_both_implementations_return_the_hand_computed_support(worked_example, theta, matching):
    settings = {**DEFAULTS, "runs": 2, "min_size": 2, "min_shared": 2, "tol": 0.15,
                "theta": theta, "matching": matching}
    pool = score(worked_example, settings)

    expected = BY_HAND[theta]
    assert [round(float(v), 6) for v in pool.support] == [
        expected["A"], expected["F"], expected["E"], expected["G"]
    ]


def test_the_cover_tie_is_broken_toward_the_smaller_cluster(worked_example):
    """F is covered equally by E (size 4) and G (size 2); the rule must pick G."""
    settings = {**DEFAULTS, "runs": 2, "min_size": 2, "min_shared": 2, "tol": 0.15,
                "theta": 0.30, "matching": "matrix"}
    chosen = score(worked_example, settings).copies[1][1]
    assert sorted(bits.unpack(chosen)) == [4, 5]

    settings["matching"] = "tree"
    assert sorted(bits.unpack(score(worked_example, settings).copies[1][1])) == [4, 5]


def _blobs(groups: int, per_group: int, seed: int) -> np.ndarray:
    """Well-separated unit vectors, so the resampled runs recover real structure."""
    rng = np.random.default_rng(seed)
    centres = np.eye(groups) * 4.0
    x = np.vstack([centres[g] + rng.normal(0, 0.35, (per_group, groups)) for g in range(groups)])
    return x / np.linalg.norm(x, axis=1, keepdims=True)


@pytest.mark.parametrize("theta", [None, 0.70, 0.85])
def test_the_two_implementations_agree_on_a_generated_build(theta):
    x = _blobs(groups=6, per_group=14, seed=7)
    settings = {**DEFAULTS, "runs": 12, "min_size": 3, "min_shared": 3, "tol": 0.15,
                "subsample": 0.8}
    if theta is not None:
        settings["theta"] = theta
    ready = prepare(x, len(x), settings, seed=3)

    tree = score(ready, {**settings, "matching": "tree"})
    matrix = score(ready, {**settings, "matching": "matrix"})

    assert np.array_equal(tree.groupings, matrix.groupings)
    assert np.array_equal(tree.eligible, matrix.eligible)
    assert np.array_equal(tree.support, matrix.support, equal_nan=True)
    assert [sorted(c) for c in tree.copies] == [sorted(c) for c in matrix.copies]
    for left, right in zip(tree.copies, matrix.copies, strict=True):
        for run_index, block in left.items():
            assert np.array_equal(block, right[run_index])
