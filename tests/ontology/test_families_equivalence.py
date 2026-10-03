"""The families implementations must agree exactly, on a fixture computed by hand.

``families`` groups near-identical groupings so their evidence counts once. The ``indexed`` and
``joined`` versions exist only for speed, so the standard is identical output -- the same seeds, the
same family lists in the same order, not merely the same partition. ``pairwise`` is the reference.

The fixture below is small enough to verify on paper and covers the three cases that decide
whether a reimplementation is faithful: a **tie in support broken by size**, a variant sitting at
**exactly** the ``max(2, 10%)`` boundary, and a grouping **already claimed by an earlier seed**.
"""

import numpy as np
import pytest

from thema.ontology import bitset as bits
from thema.ontology.recurrent import Pool, Timing, families, is_variant

N = 64


def _pool(sets: list[list[int]], support: list[float]) -> Pool:
    """A Pool carrying nothing but the groupings and support that families() reads."""
    packed = np.vstack([bits.pack(s, N) for s in sets])
    return Pool(
        groupings=packed,
        support=np.array(support, dtype=float),
        eligible=np.full(len(sets), 100, dtype=np.int64),
        copies=[{} for _ in sets],
        origins=[{0} for _ in sets],
        timing=Timing(),
    )


def test_the_allowance_boundary_is_inclusive() -> None:
    """At |A n B| = 30 the allowance is 3: three extras qualify, four do not."""
    shared = list(range(30))
    a = bits.pack(shared + [30, 31, 32], N)
    b = bits.pack(shared + [40, 41, 42], N)
    assert bits.count(a & b) == 30
    assert is_variant(a, b), "3 == max(2, int(0.10 * 30)) must qualify"
    c = bits.pack(shared + [40, 41, 42, 43], N)
    assert not is_variant(a, c), "4 > 3 must not"


@pytest.fixture
def worked_example() -> tuple[Pool, list[int]]:
    """Five groupings whose absorption is worked out in the comment below."""
    shared = list(range(30))
    sets = [
        shared + [30, 31, 32],          # 0: seed A, size 33
        shared + [40, 41, 42],          # 1: variant of A at the exact boundary, size 33
        shared + [40, 41, 42, 43],      # 2: NOT a variant of A (4 extras), size 34
        list(range(50, 55)),            # 3: disjoint, size 5
        list(range(50, 55)) + [55],     # 4: variant of 3, size 6
    ]
    #   support ties at 0.90 for groupings 0 and 2; the tie breaks on SIZE, and 2 is larger (34),
    #   so grouping 2 seeds first. 2 claims nothing: it is not a variant of A (4 extras), and IS a
    #   variant of 1 -- so 1 IS CLAIMED BY AN EARLIER SEED and is unavailable to A.
    #   Then 0 seeds and finds 1 already claimed, so its family is itself alone.
    #   Then 3 seeds and claims 4.
    return _pool(sets, [0.90, 0.80, 0.90, 0.50, 0.40]), [0, 1, 2, 3, 4]


BY_HAND = [(2, [2, 1]), (0, [0]), (3, [3, 4])]


@pytest.mark.parametrize("mode", ["pairwise", "indexed", "joined"])
def test_both_implementations_return_the_hand_computed_families(worked_example, mode) -> None:
    pool, candidates = worked_example
    got = families(candidates, None, pool, settings={"families": mode})
    assert got == BY_HAND


def _blobs(groups: int, per_group: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centres = np.eye(groups) * 4.0
    x = np.vstack([centres[g] + rng.normal(0, 0.35, (per_group, groups)) for g in range(groups)])
    return x / np.linalg.norm(x, axis=1, keepdims=True)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_all_implementations_agree_on_a_generated_pool(seed) -> None:
    """Random overlapping sets, including nested pairs and near-misses at the boundary."""
    rng = np.random.default_rng(seed)
    sets = []
    for _ in range(400):
        base = sorted(rng.choice(N, size=int(rng.integers(3, 40)), replace=False).tolist())
        sets.append(base)
        if len(base) > 4:  # a near-variant, sometimes inside the allowance and sometimes not
            drop = int(rng.integers(0, 6))
            sets.append(base[: len(base) - drop] if drop else base[:-1])
    pool = _pool(sets, rng.random(len(sets)).round(2).tolist())
    candidates = list(range(len(sets)))
    pairwise = families(candidates, None, pool, settings={"families": "pairwise"})
    indexed = families(candidates, None, pool, settings={"families": "indexed"})
    joined = families(candidates, None, pool, settings={"families": "joined"})
    assert indexed == pairwise
    assert joined == pairwise


@pytest.mark.parametrize("seed", [11, 12, 13])
def test_joined_agrees_on_pools_built_to_stress_the_prefix_filter(seed) -> None:
    """Sets sharing only COMMON pathways, where a rarest-first prefix is least discriminating.

    The two-sided prefix filter is only exact because variants must share a prefix element. A pool
    whose overlaps sit entirely in frequently-held pathways is where a wrong prefix bound would
    start dropping real variants, so it is the case worth generating.
    """
    rng = np.random.default_rng(seed)
    common = list(range(8))
    sets = []
    for _ in range(300):
        rare = rng.choice(range(8, N), size=int(rng.integers(1, 6)), replace=False).tolist()
        sets.append(sorted(common + rare))
        sets.append(sorted(common[:-1] + rare))
    pool = _pool(sets, rng.random(len(sets)).round(2).tolist())
    candidates = list(range(len(sets)))
    assert (families(candidates, None, pool, settings={"families": "joined"})
            == families(candidates, None, pool, settings={"families": "pairwise"}))


@pytest.mark.parametrize("seed", [21, 22, 23])
def test_joined_agrees_when_grouping_IDS_ARE_NOT_CONTIGUOUS(seed) -> None:
    """Grouping ids are the keys of the completed dict and are sparse, not 0..n-1.

    This is the case the other tests could not see: they pass ``range(len(sets))``, where a
    grouping's id equals its row in the stacked block, so confusing the two is invisible. On a real
    side the ids are sparse, and an id-versus-row mix-up in the candidate filter dropped exactly one
    variant out of 161,852 families -- found only at full scale. Sparse ids are now the default
    assumption of the test suite.
    """
    rng = np.random.default_rng(seed)
    sets = []
    for _ in range(300):
        base = sorted(rng.choice(N, size=int(rng.integers(3, 30)), replace=False).tolist())
        sets.append(base)
        if len(base) > 4:
            sets.append(base[:-1])
    pool = _pool(sets, rng.random(len(sets)).round(2).tolist())
    # Only every third grouping is a candidate, so ids run 0, 3, 6, ... and never equal their row.
    candidates = list(range(0, len(sets), 3))
    # Guard against this test quietly becoming the contiguous case again.
    assert candidates != list(range(len(candidates)))
    assert any(g != row for row, g in enumerate(candidates))
    member_bits = {g: pool.groupings[g] for g in candidates}
    reference = families(candidates, member_bits, pool, settings={"families": "pairwise"})
    for mode in ("indexed", "joined"):
        assert families(candidates, member_bits, pool, settings={"families": mode}) == reference
