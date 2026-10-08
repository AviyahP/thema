"""Run v0.3's pipeline with ONE stage switched off. EXPLORATORY, for the v0.4 ablation.

Every stage is reached by composing the frozen functions with different arguments plus a little new
glue, so `recurrent.py`, `cut_trees.py` and the naming code are untouched and no cached side's
provenance moves. What each switch does, and why it is reachable without an edit:

- **size cap** -- `load_run` already takes the cap as an argument, so removing it is passing a large
  one. The half-draw rule inside the persisted tree then becomes the binding limit.
- **TOL extras-only** -- NOT IMPLEMENTED AS A SWITCH, because it is a no-op: the frozen build runs
  the symmetric theta branch and `TOL` is inert in it. Recorded rather than measured.
- **STRAY** -- `consensus` takes it as an argument; off is `stray=0.0`.
- **completion** -- skip `family_members_fast` and let a family's members be the seed grouping's own
  bitset, which is what "no completion" means.
- **seed absorption** -- replace the greedy variant join with a single pass that merges groupings
  whose Jaccard reaches theta, so no grouping is absorbed into a family it only partly matches.
- **per-size floors** -- solve one threshold over all sizes instead of one per stratum.
- **strict containment** -- replace exact subset edges with partial containment at a share.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from thema.ontology import bitset as bits

#: Partial-containment share for the report-only Hasse variant.
PARTIAL_SHARE = 0.9


@dataclass(frozen=True, slots=True)
class Switches:
    """Which v0.3 stage is off. All True is v0.3.

    Attributes:
        size_cap: Apply the 29.0133% cap at cut time.
        stray: Let consensus inherit stray members.
        completion: Complete a family to the union of its matched copies.
        absorption: Use greedy seed absorption rather than a flat merge at theta.
        per_size_floors: Solve one floor per size stratum rather than one overall.
        strict_containment: Exact subset edges rather than partial containment.
    """

    size_cap: bool = True
    stray: bool = True
    completion: bool = True
    absorption: bool = True
    per_size_floors: bool = True
    strict_containment: bool = True

    def label(self) -> str:
        """Which stage is off, as a short name.

        Returns:
            The switched-off stage, or ``"v0.3"``.
        """
        for field, name in (("size_cap", "no size cap"), ("stray", "no STRAY"),
                            ("completion", "no completion"),
                            ("absorption", "flat merge at theta"),
                            ("per_size_floors", "single floor"),
                            ("strict_containment", "partial containment")):
            if not getattr(self, field):
                return name
        return "v0.3"


def flat_merge(groupings: np.ndarray, support: np.ndarray, theta: float) -> list[list[int]]:
    """Merge groupings whose Jaccard reaches theta, in one pass, highest support first.

    The ablation of greedy seed absorption. v0.3 picks a seed and pulls in every variant *of the
    seed's own set*; this takes each grouping in support order and attaches it to the best existing
    family it matches, so nothing is absorbed transitively.

    **Compared only against seeds that share a member, via an inverted index.** The first version
    compared every grouping against every seed so far, and on the real side that took 2,593 seconds
    against v0.3's 55 -- a 47x slowdown that was entirely the implementation. Two filters do the
    work: a candidate must share a pathway, and Jaccard >= theta forces
    ``theta * |A| <= |B| <= |A| / theta``, so most candidates are rejected on size alone.

    Args:
        groupings: ``(g, words)`` bitsets.
        support: Support per grouping.
        theta: Match threshold.

    Returns:
        One list of grouping indices per family, seed first.
    """
    total = int(groupings.shape[0])
    if not total:
        return []
    members = [np.asarray(bits.unpack(g), dtype=np.int64) for g in groupings]
    sizes = np.array([len(m) for m in members], dtype=np.int64)
    width = int(groupings.shape[1]) * bits.WORD
    order = np.argsort(-np.nan_to_num(support, nan=-1.0), kind="stable")

    # pathway -> the seeds holding it, grown as seeds are created.
    holders: list[list[int]] = [[] for _ in range(width)]
    seeds: list[int] = []
    families: list[list[int]] = []
    seed_of: dict[int, int] = {}
    taken = np.zeros(total, dtype=bool)

    for index in order.tolist():
        if taken[index]:
            continue
        own = members[index]
        size = int(sizes[index])
        counts: dict[int, int] = {}
        for pathway in own.tolist():
            for seed in holders[pathway]:
                counts[seed] = counts.get(seed, 0) + 1
        best_seed, best_jaccard = -1, 0.0
        low, high = theta * size, size / theta
        for seed, overlap in counts.items():
            other = int(sizes[seed])
            if other < low or other > high:
                continue
            jaccard = overlap / (size + other - overlap)
            if jaccard > best_jaccard:
                best_seed, best_jaccard = seed, jaccard
        if best_seed >= 0 and best_jaccard >= theta:
            families[seed_of[best_seed]].append(index)
            taken[index] = True
            continue
        seed_of[index] = len(families)
        seeds.append(index)
        families.append([index])
        taken[index] = True
        for pathway in own.tolist():
            holders[pathway].append(index)
    return families


def partial_edges(blocks: list[np.ndarray], share: float = PARTIAL_SHARE) -> list[tuple[int, ...]]:
    """Parents by partial containment: at least ``share`` of the child sits inside the parent.

    The report-only alternative to strict Hasse. Transitive edges are dropped the same way, so the
    result is still a reduction rather than every ancestor.

    Args:
        blocks: Member bitsets.
        share: Fraction of the child that must be inside the parent.

    Returns:
        Per node, its parents.
    """
    if not blocks:
        return []
    stacked = np.vstack(blocks)
    sizes = np.bitwise_count(stacked).sum(axis=1).astype(np.int64)
    total = len(blocks)
    inside: list[set[int]] = [set() for _ in range(total)]
    for child in range(total):
        overlap = np.bitwise_count(stacked & stacked[child]).sum(axis=1).astype(np.int64)
        covered = overlap / max(int(sizes[child]), 1)
        bigger = sizes > sizes[child]
        inside[child] = {int(p) for p in np.flatnonzero((covered >= share) & bigger).tolist()}
    out: list[tuple[int, ...]] = []
    for child in range(total):
        parents = inside[child]
        # Keep only the nearest: drop any parent that another parent is itself inside.
        nearest = {p for p in parents if not any(q in inside[p] for q in parents if q != p)}
        out.append(tuple(sorted(nearest, key=lambda p: int(sizes[p]))))
    return out


def single_floor(
    real: list[tuple[int, float]], nulls: list[list[tuple[int, float]]], target: float
) -> float | None:
    """One support threshold over all sizes, at the given FDR target.

    Args:
        real: ``(size, support)`` rows for the real side.
        nulls: One row list per calibration scramble.
        target: FDR to reach.

    Returns:
        The threshold, or None if none reaches the target.
    """
    values = sorted({s for _size, s in real} | {s for rows in nulls for _size, s in rows})
    for cut in values:
        keep = sum(1 for _size, s in real if s >= cut)
        if not keep:
            return None
        null = sum(sum(1 for _size, s in rows if s >= cut) for rows in nulls) / max(len(nulls), 1)
        if null / keep <= target:
            return float(cut)
    return None
