"""The cap applied at cut time, and the sampled ladder estimator.

Both carry a conclusion that stopped a build, so both are tested directly: the cap because
renumbering a run's cluster indices wrongly would make the matching loop climb the wrong ancestor
chain in silence, and the estimator because a broken matcher and an unstable pool look identical
from the outside.
"""

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from cut_trees import CAP_SHARE, cap_for, jaccard_match  # noqa: E402


def _pack(members: list[int], words: int = 2) -> np.ndarray:
    """A bitset row holding the given pathway indices.

    Args:
        members: Pathway indices.
        words: Width in 64-bit words.

    Returns:
        A ``(words,)`` uint64 row.
    """
    row = np.zeros(words, dtype=np.uint64)
    for member in members:
        row[member // 64] |= np.uint64(1) << np.uint64(member % 64)
    return row


def test_cap_is_the_declared_share_of_the_universe() -> None:
    """2 x Reactome Signal Transduction's 469/3,233, which is 3,125 at 10,770."""
    assert CAP_SHARE == 2 * 469 / 3233
    assert cap_for(10770) == 3125
    assert cap_for(1850) == 537


def test_a_pool_matched_against_itself_is_total() -> None:
    """Every grouping is its own partner at Jaccard 1.0, so a self-match must read 100%.

    The floor of the estimator: a matcher that cannot find an identical bitset would report a pool
    as unstable no matter how stable it was.
    """
    pool = np.vstack([_pack([0, 1, 2]), _pack([3, 4, 5, 6]), _pack([64, 65, 100])])
    share, error, examined = jaccard_match(pool, pool, 0.70)
    assert share == 1.0
    assert error == 0.0  # exhaustive: the pool is smaller than the sample
    assert examined == 3


def test_disjoint_pools_match_nothing() -> None:
    """The ceiling of the estimator: no shared member means Jaccard 0."""
    left = np.vstack([_pack([0, 1, 2])])
    right = np.vstack([_pack([10, 11, 12]), _pack([20, 21, 22, 23])])
    share, _error, _examined = jaccard_match(left, right, 0.70)
    assert share == 0.0


def test_the_threshold_is_two_sided_on_the_same_pair() -> None:
    """A pair at a known Jaccard is counted at one threshold and not at a higher one.

    {0,1,2,3} against {0,1,2,3,4}: intersection 4, union 5, Jaccard 0.8. So it matches at 0.70 and
    does not at 0.90 -- which is what makes 0.70 a parameter of the result rather than a detail.
    """
    left = np.vstack([_pack([0, 1, 2, 3])])
    right = np.vstack([_pack([0, 1, 2, 3, 4])])
    assert jaccard_match(left, right, 0.70)[0] == 1.0
    assert jaccard_match(left, right, 0.90)[0] == 0.0


def test_an_empty_side_matches_nothing_rather_than_raising() -> None:
    """A scramble side can legitimately produce no eligible grouping."""
    pool = np.vstack([_pack([0, 1, 2])])
    empty = np.zeros((0, 2), dtype=np.uint64)
    assert jaccard_match(empty, pool, 0.70) == (0.0, 0.0, 0)
    assert jaccard_match(pool, empty, 0.70) == (0.0, 0.0, 0)


def test_sampling_is_reported_as_sampled() -> None:
    """Below the sample size the estimate is exact and its error is 0; above it, both change.

    The error is what keeps the figure honest, so an estimate must never come back claiming to be
    exhaustive when it drew a sample.
    """
    pool = np.vstack([_pack([i, i + 1, i + 2]) for i in range(0, 60, 3)])
    exact = jaccard_match(pool, pool, 0.70, sample=0)
    assert exact == (1.0, 0.0, len(pool))
    drawn = jaccard_match(pool, pool, 0.70, sample=5)
    assert drawn[2] == 5
    # A 100% share has zero variance even when sampled, so the sample SIZE is what proves it drew.
    assert drawn[2] < len(pool)
