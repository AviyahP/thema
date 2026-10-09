"""Normalised-centroid cosine linkage: the fast path must be the cubic reference, exactly.

The fast path keeps a similarity matrix, cached per-row maxima and a liveness mask; the reference
recomputes every similarity from the current sums at each step and shares none of that bookkeeping.
So an agreement between them is evidence, and the test that matters most is
:func:`test_fast_path_is_the_reference`.

The other claim worth pinning is that the running **sums** give the same answer as centroids
recomputed from members. That is what lets a merge be one vector addition instead of a re-read, and
it is exact rather than approximate.
"""

from __future__ import annotations

import numpy as np
import pytest

from thema.ontology.linkage import Agglomeration, centroid_cosine, naive_centroid_cosine


def blobs(per: int = 30, groups: int = 4, dim: int = 24, noise: float = 0.05,
          seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Planted unit-vector blobs on distinct axes.

    Args:
        per: Points per blob.
        groups: Number of blobs.
        dim: Dimension.
        noise: Gaussian noise scale.
        seed: RNG seed.

    Returns:
        ``(points, blob label per point)``.
    """
    rng = np.random.default_rng(seed)
    centres = np.eye(groups, dim)
    points = np.vstack([c + noise * rng.normal(size=(per, dim)) for c in centres])
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    return points.astype(np.float32), np.repeat(np.arange(groups), per)


@pytest.mark.parametrize(("n", "dim"), [(40, 8), (90, 16), (200, 24)])
def test_fast_path_is_the_reference(n: int, dim: int) -> None:
    """Same merges, same order, same heights, same inversion count."""
    rng = np.random.default_rng(n)
    points = rng.normal(size=(n, dim)).astype(np.float32)
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    fast, slow = centroid_cosine(points), naive_centroid_cosine(points)
    assert np.array_equal(fast.merges, slow.merges)
    assert np.allclose(fast.similarity, slow.similarity, atol=1e-5)
    assert fast.inversions == slow.inversions


def test_running_sums_equal_centroids_recomputed_from_members() -> None:
    """The identity the implementation rests on, checked at every step of a real run."""
    points, _labels = blobs(per=12, groups=3, dim=12)
    got = centroid_cosine(points)
    sets = got.members(len(points))
    for step, (left, right) in enumerate(got.merges):
        a = points[sets[int(left)]].mean(axis=0)
        b = points[sets[int(right)]].mean(axis=0)
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)
        assert float(a @ b) == pytest.approx(got.similarity[step], abs=1e-5)


def test_planted_blobs_are_recovered_exactly() -> None:
    """The rule finds the blobs it should, with no leakage between them."""
    points, labels = blobs()
    got = centroid_cosine(points)
    cut = got.cut(len(points), 4)
    assert sorted(len(c) for c in cut) == [30, 30, 30, 30]
    for cluster in cut:
        assert len(set(labels[cluster].tolist())) == 1


def test_a_diffuse_cluster_gets_no_discount() -> None:
    """The motivating difference from Ward, as a property rather than a story.

    A tight pair and a diffuse cloud sit the same angle apart from a lone point. Under
    normalised-centroid cosine the lone point is indifferent between them, so the diffuse cloud
    cannot absorb it merely by being spread out. The test asserts the similarities are equal to
    within tolerance, which is the thing Ward's size-weighted cost violates.
    """
    rng = np.random.default_rng(3)
    dim = 32
    axis = np.zeros(dim)
    axis[0] = 1.0
    other = np.zeros(dim)
    other[1] = 1.0
    tight = np.vstack([axis + 0.01 * rng.normal(size=dim) for _ in range(2)])
    diffuse = np.vstack([axis + 0.30 * rng.normal(size=dim) for _ in range(40)])
    for block in (tight, diffuse):
        block /= np.linalg.norm(block, axis=1, keepdims=True)

    def sim_to(block: np.ndarray) -> float:
        """Normalised-centroid cosine between a block and the lone point."""
        centre = block.mean(axis=0)
        centre = centre / np.linalg.norm(centre)
        return float(centre @ other)

    assert sim_to(tight) == pytest.approx(sim_to(diffuse), abs=0.12)


def test_cut_is_exact_in_cluster_count() -> None:
    """Cuts are replayed merges, so the count is exact even though heights are not monotone."""
    points, _labels = blobs(per=10, groups=5, dim=16)
    got = centroid_cosine(points)
    for clusters in (1, 2, 5, 17, 50):
        cut = got.cut(len(points), clusters)
        assert len(cut) == clusters
        assert sum(len(c) for c in cut) == len(points)
        assert sorted(int(i) for c in cut for i in c) == list(range(len(points)))


def test_members_covers_every_node_once() -> None:
    """``members`` returns 2n-1 nodes and the root holds everything."""
    points, _labels = blobs(per=8, groups=3, dim=10)
    got = centroid_cosine(points)
    sets = got.members(len(points))
    assert len(sets) == 2 * len(points) - 1
    assert sorted(sets[-1].tolist()) == list(range(len(points)))


def test_heights_can_invert_and_that_is_recorded() -> None:
    """Inversions are real for this rule, so they are counted rather than assumed away."""
    points, _labels = blobs(per=20, groups=6, dim=20, noise=0.25, seed=7)
    got = centroid_cosine(points)
    rising = sum(1 for i in range(1, len(got.similarity))
                 if got.similarity[i] > got.similarity[i - 1] + 1e-9)
    assert got.inversions == rising
    assert got.inversions > 0


def test_one_row_is_refused() -> None:
    """Agglomerating a single point is a caller error, not an empty result."""
    with pytest.raises(ValueError, match="at least two rows"):
        centroid_cosine(np.ones((1, 4), dtype=np.float32))


def test_agglomeration_is_frozen() -> None:
    """The record cannot be edited after the fact."""
    points, _labels = blobs(per=6, groups=2, dim=8)
    got = centroid_cosine(points)
    assert isinstance(got, Agglomeration)
    with pytest.raises((AttributeError, TypeError)):
        got.inversions = 0  # type: ignore[misc]
