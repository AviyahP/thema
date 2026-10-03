"""`family_members_fast` must agree with `family_members` exactly, not approximately.

The fast path is used to complete every grouping in a build, so a disagreement anywhere changes
member sets, inclusions, and therefore the exported ontology. Equality is asserted on the FLOATS,
not within a tolerance: an inclusion is rounded and exported, so a last-bit difference is a
different build.
"""

import numpy as np

from thema.ontology import bitset as bits
from thema.ontology.recurrent import (
    DEFAULTS,
    family_members,
    family_members_fast,
    prepare,
    score,
)


def _blobs(rng: np.random.Generator, n: int, dim: int, groups: int) -> np.ndarray:
    """Points in separated directions, so Ward finds real structure to resample.

    Args:
        rng: Random source.
        n: Point count.
        dim: Dimensions.
        groups: How many blobs.

    Returns:
        ``(n, dim)`` unit vectors.
    """
    centres = np.eye(groups, dim)
    pick = rng.integers(groups, size=n)
    x = centres[pick] * 6.0 + rng.normal(scale=0.6, size=(n, dim))
    return (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)


def _pool(seed: int, n: int = 90, runs: int = 12):
    """Build a real prepared pool from a synthetic universe.

    Args:
        seed: Master seed.
        n: Universe size.
        runs: Resampling runs.

    Returns:
        ``(ready, pool, n_bits)``.
    """
    rng = np.random.default_rng(seed)
    x = _blobs(rng, n, 8, 5)
    settings = {**DEFAULTS, "runs": runs, "tol": 0.15, "min_size": 3, "theta": 0.70}
    ready = prepare(x, n, settings, seed)
    return ready, score(ready, settings), ready.present.shape[1] * bits.WORD


def test_agrees_on_every_grouping_of_a_real_pool() -> None:
    """Candidate bitsets identical, inclusion dicts identical including key order."""
    ready, pool, words = _pool(7)
    checked = 0
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        slow_c, slow_i = family_members([grouping], pool, ready.present, words)
        fast_c, fast_i = family_members_fast([grouping], pool, ready.present, words)
        assert np.array_equal(slow_c, fast_c)
        assert list(slow_i) == list(fast_i)          # same candidate ORDER
        assert slow_i == fast_i                       # and the same floats
        checked += 1
    assert checked > 50, f"only {checked} groupings exercised"


def test_agrees_on_multi_grouping_families() -> None:
    """Completion uses single groupings, but the selection pass can pass a whole family."""
    ready, pool, words = _pool(11)
    evaluable = [g for g in range(len(pool.groupings)) if not np.isnan(pool.support[g])]
    families = [evaluable[i:i + 3] for i in range(0, min(len(evaluable), 60), 3)]
    for family in families:
        if len(family) < 2:
            continue
        slow_c, slow_i = family_members(family, pool, ready.present, words)
        fast_c, fast_i = family_members_fast(family, pool, ready.present, words)
        assert np.array_equal(slow_c, fast_c)
        assert slow_i == fast_i


def test_agrees_when_a_family_has_no_copies() -> None:
    """An empty family returns an empty bitset from both, not an error from either."""
    ready, pool, words = _pool(3)
    slow = family_members([], pool, ready.present, words)
    fast = family_members_fast([], pool, ready.present, words)
    assert np.array_equal(slow[0], fast[0])
    assert slow[1] == fast[1] == {}


def test_inclusions_are_bounded_and_never_negative() -> None:
    """The ratio is clamped at 1.0 in both, which is what the declared rule says."""
    ready, pool, words = _pool(5)
    for grouping in range(min(len(pool.groupings), 200)):
        if np.isnan(pool.support[grouping]):
            continue
        _c, inclusion = family_members_fast([grouping], pool, ready.present, words)
        assert all(0.0 <= v <= 1.0 for v in inclusion.values())
