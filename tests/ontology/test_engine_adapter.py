"""The engine adapter must be a GENERALISATION of the Ward path, not a parallel one.

`run_from_candidates` is what lets a non-Ward engine supply candidates. If it merely produced
"something workable" for flat partitions while Ward kept its own path, the regression in the engine
brief's §1.2 would prove nothing: byte-identity would follow from Ward never going through the new
code. So the test here is the strong one -- fed Ward's own candidates and nested structure, the
adapter must reproduce `_one_run`'s Run field for field.
"""

from __future__ import annotations

import numpy as np

from thema.ontology import bitset as bits
from thema.ontology.recurrent import Run, _one_run, run_from_candidates


def _blobs(groups: int = 6, per: int = 9, dim: int = 8, seed: int = 0) -> np.ndarray:
    """Unit-length points in well-separated blobs, the fixture idiom used across the suite.

    Args:
        groups: Number of blobs.
        per: Points per blob.
        dim: Dimensionality.
        seed: RNG seed.

    Returns:
        An ``(groups * per, dim)`` unit-vector matrix.
    """
    rng = np.random.default_rng(seed)
    centres = np.eye(groups, dim)
    x = np.repeat(centres, per, axis=0) + 0.05 * rng.standard_normal((groups * per, dim))
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def _same(left: Run, right: Run) -> None:
    """Assert two runs are equal in every field.

    Args:
        left: One run.
        right: The other.
    """
    for field in ("present", "clusters", "parent", "leaf_cluster", "sizes",
                  "chain_indptr", "chain_idx"):
        a, b = getattr(left, field), getattr(right, field)
        assert a.shape == b.shape, field
        assert np.array_equal(a, b), field


def test_adapter_reproduces_the_ward_run_exactly() -> None:
    """Ward candidates through the general constructor give the identical Run."""
    x = _blobs()
    n = x.shape[0]
    for seed in (0, 1, 2, 7):
        ward = _one_run(x, n, 0.8, 3, seed)
        adapted = run_from_candidates(ward.present, ward.clusters, n, parent=ward.parent)
        _same(ward, adapted)


def test_chain_is_an_inverted_index_not_a_tree_walk() -> None:
    """A FLAT partition gets a correct per-pathway candidate list, one entry each."""
    n = 12
    parts = [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9, 10, 11]]
    candidates = np.vstack([bits.pack(p, n) for p in parts])
    present = bits.pack(range(n), n)
    run = run_from_candidates(present, candidates, n)

    assert np.array_equal(run.parent, np.full(3, -1))
    for pathway, expect in enumerate([0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2]):
        got = run.chain_idx[run.chain_indptr[pathway] : run.chain_indptr[pathway + 1]]
        assert got.tolist() == [expect], pathway
        assert int(run.leaf_cluster[pathway]) == expect


def test_overlapping_candidates_are_ordered_smallest_first() -> None:
    """A pooled arm's candidates overlap without nesting; order is (size, index) ascending."""
    n = 10
    # Deliberately given largest-first, so a stable sort alone would not produce the right order.
    candidates = np.vstack([
        bits.pack([0, 1, 2, 3, 4, 5], n),
        bits.pack([0, 1, 2], n),
        bits.pack([2, 3, 4, 5, 6], n),
    ])
    run = run_from_candidates(bits.pack(range(n), n), candidates, n)

    assert run.sizes.tolist() == [6, 3, 5]
    assert run.chain_idx[run.chain_indptr[0] : run.chain_indptr[1]].tolist() == [1, 0]
    assert run.chain_idx[run.chain_indptr[2] : run.chain_indptr[3]].tolist() == [1, 2, 0]
    assert int(run.leaf_cluster[2]) == 1
    # Pathway 7 is in nothing: no entries, and -1.
    assert run.chain_indptr[7] == run.chain_indptr[8]
    assert int(run.leaf_cluster[7]) == -1


def test_a_pathway_in_no_candidate_is_not_placed() -> None:
    """HDBSCAN leaves noise points out entirely; that must not become a phantom membership."""
    n = 8
    candidates = np.vstack([bits.pack([0, 1, 2], n)])
    run = run_from_candidates(bits.pack(range(n), n), candidates, n)
    assert int(run.chain_indptr[-1]) == 3
    assert run.leaf_cluster.tolist() == [0, 0, 0, -1, -1, -1, -1, -1]


def test_empty_candidate_set() -> None:
    """A run that proposed nothing is representable, since a scramble side often will."""
    n, words = 6, bits.words_for(6)
    empty = np.zeros((0, words), np.uint64)
    run = run_from_candidates(bits.pack(range(n), n), empty, n)
    assert run.clusters.shape == (0, words)
    assert int(run.chain_indptr[-1]) == 0
    assert run.leaf_cluster.tolist() == [-1] * n


def test_containment_in_a_larger_candidate_is_not_recurrence() -> None:
    """Amendment 4 restates a rule; this checks the code actually implements it.

    A grouping that merely sits INSIDE a much larger community has not recurred. The two-sided
    Jaccard is what enforces it: cover is high but the larger candidate's extras inflate the union,
    so the ratio falls below theta. Without this, a run whose only candidate is one huge community
    would "find" every grouping it happens to contain, and a coarse engine would score as perfectly
    recurrent.
    """
    from thema.ontology.recurrent import DEFAULTS, prepare, score

    n = 60
    target = list(range(10))
    # Run 0 proposes the grouping itself. Runs 1-4 propose only a 50-member community containing it.
    runs = [
        run_from_candidates(bits.pack(range(n), n),
                            np.vstack([bits.pack(target, n)]), n),
        *[
            run_from_candidates(bits.pack(range(n), n),
                                np.vstack([bits.pack(range(50), n)]), n)
            for _ in range(4)
        ],
    ]
    settings = {**DEFAULTS, "runs": len(runs), "tol": 0.15, "min_size": 3, "theta": 0.70}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)

    sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int64)
    small = [i for i, size in enumerate(sizes.tolist()) if size == len(target)]
    assert small, "the 10-member grouping must be in the pool"
    # Found in its own run only: 1 of 5 eligible runs. Jaccard against the 50-member community is
    # 10/50 = 0.2, far below theta.
    assert pool.support[small[0]] == 1.0 / len(runs), (
        f"containment counted as recurrence: support {pool.support[small[0]]}"
    )


def test_a_genuine_near_copy_does_count() -> None:
    """The counterpart: the rule must not reject everything that is not identical."""
    from thema.ontology.recurrent import DEFAULTS, prepare, score

    n = 60
    target = list(range(10))
    # 9 of 10 shared plus one extra is Jaccard 9/11 = 0.818, above theta.
    runs = [
        run_from_candidates(bits.pack(range(n), n), np.vstack([bits.pack(target, n)]), n),
        run_from_candidates(bits.pack(range(n), n),
                            np.vstack([bits.pack(list(range(9)) + [11], n)]), n),
    ]
    settings = {**DEFAULTS, "runs": len(runs), "tol": 0.15, "min_size": 3, "theta": 0.70}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)

    sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int64)
    small = [i for i, size in enumerate(sizes.tolist()) if size == len(target)]
    assert pool.support[small[0]] == 1.0, "a near copy at Jaccard 0.818 must be found in both runs"
