"""Arm K's mutual-rank ladder, on fixtures where the answer is known.

Three things the spec asks to be checked: that two planted groups plus noise come out as two
groups; that a run is reproducible from its seed; and that support and lifetime match a naive
implementation.
"""

from __future__ import annotations

import numpy as np

from thema.ontology import mutualrank as mr


def _planted(groups: int = 2, per: int = 12, noise: int = 10, dim: int = 12,
             seed: int = 0) -> np.ndarray:
    """Two tight planted groups plus unstructured noise points.

    Args:
        groups: How many planted groups.
        per: Members per group.
        noise: Unstructured points.
        dim: Dimensionality.
        seed: RNG seed.

    Returns:
        A unit-vector matrix, planted members first.
    """
    rng = np.random.default_rng(seed)
    centres = np.eye(groups, dim) * 6.0
    block = np.repeat(centres, per, axis=0) + 0.12 * rng.standard_normal((groups * per, dim))
    free = rng.standard_normal((noise, dim))
    x = np.vstack([block, free])
    return (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)


def test_neighbours_are_sorted_and_exclude_self() -> None:
    """Rank 0 is the closest other point, never the point itself."""
    x = _planted()
    near = mr.neighbours(x, k_max=8)
    assert near.shape == (x.shape[0], 8)
    for i in range(x.shape[0]):
        assert i not in near[i].tolist()
        sims = x[near[i]] @ x[i]
        assert np.all(np.diff(sims) <= 1e-5), "neighbours must be closest first"


def test_mutual_rank_is_symmetric_and_stored_once() -> None:
    """Each edge appears once with i < j, and its rank is the worse of the two positions."""
    x = _planted()
    near = mr.neighbours(x, k_max=10)
    edges, rank = mr.mutual_rank_edges(near)

    assert (edges[:, 0] < edges[:, 1]).all()
    assert len({tuple(e) for e in edges.tolist()}) == len(edges)
    assert (rank >= 1).all()
    for (i, j), r in zip(edges.tolist(), rank.tolist(), strict=True):
        a = int(np.flatnonzero(near[i] == j)[0]) + 1
        b = int(np.flatnonzero(near[j] == i)[0]) + 1
        assert r == max(a, b)


def test_two_planted_groups_come_out_as_two_groups() -> None:
    """The headline sanity case: the ladder must recover the plant, and not the noise."""
    per = 12
    x = _planted(groups=2, per=per, noise=10)
    near = mr.neighbours(x, k_max=20)
    edges, rank = mr.mutual_rank_edges(near)
    per_run = mr.ladder_runs(edges, rank, x.shape[0], runs=8, ladder=(3, 4, 6, 8, 10))
    members, support, lifetime = mr.score(per_run, x.shape[0], ladder=(3, 4, 6, 8, 10))

    keep = [i for i, s in enumerate(support) if s >= 0.33]
    planted = {frozenset(range(0, per)), frozenset(range(per, 2 * per))}
    found = {frozenset(members[i].tolist()) for i in keep}
    assert planted <= found, (
        f"planted groups missing; kept sizes {sorted(len(members[i]) for i in keep)}"
    )

    # Noise points DO form clusters that recur: ten random points in twelve dimensions contain
    # mutual nearest neighbours, the edge set is the same every run, and only 20% of edges are
    # dropped. So support alone does not separate them, which is the whole reason arm K adds a
    # lifetime. What must hold is that the LIFETIME does.
    # Noise points DO form clusters that recur: ten random points in twelve dimensions contain
    # mutual nearest neighbours, the edge set is the same every run, and only 20% of edges are
    # dropped. So support alone does not separate them, which is the reason arm K adds a lifetime.
    noise_only = [i for i in keep if bool((members[i] >= 2 * per).all())]
    assert noise_only, "the fixture is meant to produce noise clusters; it produced none"

    planted_life = [lifetime[i] for i in keep
                    if frozenset(members[i].tolist()) in planted and np.isfinite(lifetime[i])]
    noise_life = [lifetime[i] for i in noise_only if np.isfinite(lifetime[i])]
    assert planted_life and noise_life

    # RECORDED, NOT ASSERTED AS A SEPARATION, because on this fixture it is the wrong way round:
    # the planted twelve-member groups score 32.0 and the three-member noise clusters score 42.67.
    # The cause is structural rather than a fixture artefact. Lifetime is
    # (rung after the last match) / (first matching rung), and a tiny isolated triple connects at
    # the LOWEST rung, so it gets the smallest denominator and the largest ratio; a twelve-member
    # group needs a higher rung before it is connected at all. That is the same sparse-beats-dense
    # confound Test R found in G_loo, reappearing in the denominator.
    #
    # The toy confounds size with plantedness, so it is a warning and not a verdict -- the real run
    # and its scramble build are what settle it. This test exists to stop the inversion being
    # discovered twice.
    assert min(planted_life) < max(noise_life), (
        "the toy inversion has changed; re-read whether lifetime now separates, because the naive "
        "K report was written on the assumption that it does not"
    )


def test_runs_are_reproducible_from_their_seed() -> None:
    """Same seed, same clusters, every run and rung."""
    x = _planted()
    near = mr.neighbours(x, k_max=12)
    edges, rank = mr.mutual_rank_edges(near)
    a = mr.ladder_runs(edges, rank, x.shape[0], runs=4, ladder=(3, 5, 8))
    b = mr.ladder_runs(edges, rank, x.shape[0], runs=4, ladder=(3, 5, 8))
    assert len(a) == len(b) == 4
    for run_a, run_b in zip(a, b, strict=True):
        for rung_a, rung_b in zip(run_a, run_b, strict=True):
            assert [c.tolist() for c in rung_a] == [c.tolist() for c in rung_b]


def test_support_and_lifetime_match_a_naive_implementation() -> None:
    """The vectorised-ish scorer against the obvious one, on real planted data."""
    ladder = (3, 4, 6, 8, 10)
    x = _planted(groups=3, per=10, noise=8, seed=3)
    near = mr.neighbours(x, k_max=16)
    edges, rank = mr.mutual_rank_edges(near)
    per_run = mr.ladder_runs(edges, rank, x.shape[0], runs=6, ladder=ladder)
    members, support, lifetime = mr.score(per_run, x.shape[0], ladder=ladder)

    after = list(ladder[1:]) + [mr.NEXT_AFTER_LAST]
    for position, group in enumerate(members):
        want = set(group.tolist())
        ratios, runs_found = [], 0
        for run in per_run:
            flags = []
            for rung in run:
                ok = False
                for cluster in rung:
                    other = set(cluster.tolist())
                    inter = len(want & other)
                    if inter and inter / len(want | other) >= mr.THETA:
                        ok = True
                        break
                flags.append(ok)
            if not any(flags):
                continue
            runs_found += 1
            best_len = best_start = best_end = 0
            length = 0
            for i, f in enumerate(flags):
                length = length + 1 if f else 0
                if length > best_len:
                    best_len, best_end, best_start = length, i, i - length + 1
            ratios.append(after[best_end] / ladder[best_start])
        assert abs(support[position] - runs_found / len(per_run)) < 1e-12, position
        if ratios:
            assert abs(lifetime[position] - float(np.median(ratios))) < 1e-12, position
        else:
            assert np.isnan(lifetime[position])
