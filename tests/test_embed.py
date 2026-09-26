"""The vector transforms Ward depends on.

`centre_and_renormalise` is the clustering input as of the 2026-09-26 amendment. The first two
tests exist because the amendment rests on them: mean subtraction alone is inert on a Ward tree,
and the renormalisation is what makes the change real. If the first ever failed, the 21 Sep
decision to centre for cohesion only would have been silently changing every build.
"""

import numpy as np
from scipy.spatial.distance import pdist

from thema.cluster import distances
from thema.embed import centre_and_renormalise


def test_centring_alone_cannot_change_a_ward_tree() -> None:
    """Squared Euclidean distance is translation-invariant, so the subtraction is inert on its own.

    Recorded as a test because the amendment rests on it: if mean subtraction moved distances, the
    21 Sep decision to centre for cohesion only would have silently changed every build.
    """
    rng = np.random.default_rng(0)
    x = rng.normal(size=(60, 8))
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    shifted = x - x.mean(axis=0, keepdims=True)
    assert np.allclose(distances(x), pdist(shifted, metric="euclidean"), atol=1e-12)


def test_renormalising_after_centring_does_change_distances() -> None:
    """And this is the step that makes it a new decision rather than a no-op."""
    rng = np.random.default_rng(1)
    x = rng.normal(size=(60, 8))
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    centred, mean = centre_and_renormalise(x)
    assert np.allclose(np.linalg.norm(centred, axis=1), 1.0)
    assert mean.shape == (8,)
    assert not np.allclose(distances(x), distances(centred), atol=1e-6)


def test_centring_reduces_hubness_on_an_anisotropic_fixture() -> None:
    """A shared dominant direction creates hubs; removing it should reduce the worst count."""
    rng = np.random.default_rng(2)
    bias = np.zeros(8)
    bias[0] = 3.0
    x = rng.normal(size=(300, 8)) + bias          # every point shares one strong direction
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    centred, _mean = centre_and_renormalise(x)

    def worst_hub(mat: np.ndarray, k: int = 10) -> int:
        g = mat @ mat.T
        np.fill_diagonal(g, -2.0)
        top = np.argpartition(-g, k, axis=1)[:, :k]
        return int(np.bincount(top.ravel(), minlength=len(mat)).max())

    assert worst_hub(centred) < worst_hub(x)
