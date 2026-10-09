"""Repair route (a): close the stale-merge hole, and collapse chains in construction.

Two fixes, declared 8-9 Oct 2026 and applied after consensus rather than inside it.

**Why outside consensus.** ``consensus.py`` is load-bearing for v0.4's byte-identity proof against
the frozen ``recurrent_dag_10770``. Changing its merge loop in place would break the one guarantee
that makes v0.4 comparable to v0.3, so the repair runs as a post-pass over final memberships and
``consensus.py`` is untouched. ``scripts/v04_run.py --all-stages-on --verify`` still passes.

**Fix 1, stale merges.** Consensus compares only the *newcomer* against the accepted stack, so two
themes already side by side are never compared again after one of them grows by inheritance. In
``thema_L`` 822 themes grow and all ten surviving anomalies -- three identical pairs and seven
non-nested pairs above 0.70 -- involve a grown theme
(``docs/status/2026-10-08-twins-diagnosis.md``). :func:`merge_stale` applies the 0.70 rule again on
final memberships, **iterated to a fixed point**, and :func:`assert_no_stale_pair` checks that none
survives.

The rule mirrors ``consensus.classify`` exactly in what it spares: **strict containment is kept**,
because a theme strictly inside another is hierarchy and ``hasse`` draws the edge. Only identical
sets and non-nested overlaps at or above the threshold are merged.

**Fix 2, chain collapse.** A child holding at least ``COLLAPSE_SHARE`` of its parent's members is
the same theme with a little added, not a second theme. :func:`collapse_chains` merges the two into
one node: **the parent's membership is kept, the higher support is kept, and both supports are
recorded** so nothing is lost. Edges are re-linked so the collapsed child's own children become the
parent's, and strict containment still holds afterwards because every surviving set is unchanged.

The two are ordered: collapse first, then the stale-merge pass, because collapsing changes
memberships and could otherwise leave a fresh identical pair behind.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from thema.ontology import bitset as bits

#: A child holding at least this share of its parent is the same theme. 90% is the declared rule;
#: 80% is reported for comparison and the choice is not made from the results.
COLLAPSE_SHARE = 0.90
#: The merge threshold, the same 0.70 used for matching and for consensus.
MERGE_JACCARD = 0.70
#: Guard on the fixed-point loops: far above any real number of rounds.
MAX_ROUNDS = 50


@dataclass
class Repaired:
    """A repaired build.

    Attributes:
        members: Member bitset per surviving theme.
        supports: Support per surviving theme.
        inclusions: Inclusion vote per surviving theme.
        collapsed: ``{absorbed theme: the theme it merged into}``, from fix 2.
        collapsed_supports: ``{surviving theme: the absorbed theme's support}``, kept so the pair's
            second support is recorded rather than discarded.
        merged: ``{dropped theme: the theme that superseded it}``, from fix 1.
        merged_kind: ``{dropped theme: "identical" or "overlap"}``.
        rounds: Fixed-point rounds each fix needed.
    """

    members: list[np.ndarray]
    supports: list[float]
    inclusions: list[dict[int, float]]
    collapsed: dict[int, int] = field(default_factory=dict)
    collapsed_supports: dict[int, float] = field(default_factory=dict)
    merged: dict[int, int] = field(default_factory=dict)
    merged_kind: dict[int, str] = field(default_factory=dict)
    rounds: dict[str, int] = field(default_factory=dict)


def _sets(members: Sequence[np.ndarray]) -> list[set[int]]:
    """Member index sets for every theme.

    Args:
        members: Member bitsets.

    Returns:
        One index set per theme.
    """
    return [set(bits.unpack(block)) for block in members]


def _index(sets: Sequence[set[int]], alive: Sequence[int]) -> dict[int, list[int]]:
    """Inverted index from member to the live themes holding it.

    Args:
        sets: Member index sets.
        alive: Live theme positions.

    Returns:
        Member to theme positions.
    """
    out: dict[int, list[int]] = {}
    for position in alive:
        for member in sets[position]:
            out.setdefault(member, []).append(position)
    return out


def collapse_chains(
    members: Sequence[np.ndarray], supports: Sequence[float],
    inclusions: Sequence[dict[int, float]], share: float = COLLAPSE_SHARE
) -> Repaired:
    """Fix 2: merge a child holding at least ``share`` of its parent into the parent.

    Only strict containment counts as a parent-child pair, which is what the DAG's edges mean.
    Identical sets are left to :func:`merge_stale`, since neither is the other's parent.

    Iterated to a fixed point: absorbing a child can make a grandchild a near-copy of the surviving
    parent, and collapsing one link of a chain should collapse the whole chain.

    Args:
        members: Member bitsets.
        supports: Support per theme.
        inclusions: Inclusion vote per theme.
        share: The declared share, :data:`COLLAPSE_SHARE`.

    Returns:
        The surviving themes, with what was absorbed into what.
    """
    sets = _sets(members)
    alive = set(range(len(sets)))
    kept_support = {i: float(supports[i]) for i in alive}
    absorbed: dict[int, int] = {}
    second: dict[int, float] = {}
    rounds = 0
    while rounds < MAX_ROUNDS:
        rounds += 1
        holders = _index(sets, sorted(alive))
        doomed: dict[int, int] = {}
        # Smallest first, so a chain collapses from the bottom and each child finds its own parent.
        for child in sorted(alive, key=lambda i: len(sets[i])):
            if child in doomed:
                continue
            best: tuple[int, int] | None = None
            for parent in {p for m in sets[child] for p in holders.get(m, ())}:
                if parent == child or parent in doomed or parent not in alive:
                    continue
                if not sets[child] < sets[parent]:
                    continue
                if len(sets[child]) >= share * len(sets[parent]):
                    if best is None or len(sets[parent]) < best[1]:
                        best = (parent, len(sets[parent]))
            if best is not None:
                doomed[child] = best[0]
        if not doomed:
            break
        for child, parent in doomed.items():
            alive.discard(child)
            absorbed[child] = parent
            # The parent's membership is kept; the higher support wins and both are recorded.
            second[parent] = max(second.get(parent, 0.0), kept_support.pop(child))
            kept_support[parent] = max(kept_support[parent], second[parent])

    order = sorted(alive)
    return Repaired(
        members=[members[i] for i in order],
        supports=[kept_support[i] for i in order],
        inclusions=[dict(inclusions[i]) for i in order],
        collapsed=absorbed,
        collapsed_supports={i: second[i] for i in order if i in second},
        rounds={"collapse": rounds})


def stale_pairs(members: Sequence[np.ndarray],
                jaccard: float = MERGE_JACCARD) -> list[tuple[int, int, str, float]]:
    """Pairs the 0.70 rule should have merged and did not.

    Args:
        members: Member bitsets.
        jaccard: The merge threshold.

    Returns:
        ``(i, j, kind, jaccard)`` for identical and non-nested pairs at or above the threshold.
    """
    sets = _sets(members)
    holders = _index(sets, range(len(sets)))
    out: list[tuple[int, int, str, float]] = []
    for left in range(len(sets)):
        for right in {o for m in sets[left] for o in holders.get(m, ())}:
            if right <= left:
                continue
            a, b = sets[left], sets[right]
            inter = len(a & b)
            if not inter:
                continue
            union = len(a) + len(b) - inter
            if a == b:
                out.append((left, right, "identical", 1.0))
            elif not (a < b or b < a) and union and inter / union >= jaccard:
                out.append((left, right, "overlap", inter / union))
    return out


def merge_stale(
    members: Sequence[np.ndarray], supports: Sequence[float],
    inclusions: Sequence[dict[int, float]], jaccard: float = MERGE_JACCARD
) -> Repaired:
    """Fix 1: apply the 0.70 merge again on final memberships, to a fixed point.

    Strict containment is spared, exactly as ``consensus.classify`` spares it: that is hierarchy.
    Of an identical or non-nested overlapping pair, the **lower-support** theme is dropped, matching
    consensus's own tie-break of support then size.

    Args:
        members: Member bitsets.
        supports: Support per theme.
        inclusions: Inclusion vote per theme.
        jaccard: The merge threshold.

    Returns:
        The surviving themes, with what superseded what.
    """
    sets = _sets(members)
    alive = set(range(len(sets)))
    dropped: dict[int, int] = {}
    kind: dict[int, str] = {}
    rounds = 0
    while rounds < MAX_ROUNDS:
        rounds += 1
        order = sorted(alive, key=lambda i: (-float(supports[i]), -len(sets[i])))
        holders = _index(sets, order)
        changed = False
        for position in reversed(order):           # lowest support considered first for dropping
            if position not in alive:
                continue
            for other in {o for m in sets[position] for o in holders.get(m, ())}:
                if other == position or other not in alive:
                    continue
                a, b = sets[position], sets[other]
                if (float(supports[other]), len(b)) < (float(supports[position]), len(a)):
                    continue                        # only ever drop the weaker of the two
                inter = len(a & b)
                if not inter:
                    continue
                union = len(a) + len(b) - inter
                same = a == b
                if same or (not (a < b or b < a) and union and inter / union >= jaccard):
                    alive.discard(position)
                    dropped[position] = other
                    kind[position] = "identical" if same else "overlap"
                    changed = True
                    break
        if not changed:
            break

    order = sorted(alive)
    return Repaired(
        members=[members[i] for i in order],
        supports=[float(supports[i]) for i in order],
        inclusions=[dict(inclusions[i]) for i in order],
        merged=dropped, merged_kind=kind, rounds={"merge": rounds})


def assert_no_stale_pair(members: Sequence[np.ndarray],
                         jaccard: float = MERGE_JACCARD) -> None:
    """Refuse a build that still holds a pair fix 1 was meant to remove.

    Args:
        members: Member bitsets.
        jaccard: The merge threshold.

    Raises:
        ValueError: If any identical or non-nested pair at or above the threshold survives.
    """
    left = stale_pairs(members, jaccard)
    if left:
        kinds = {k for _i, _j, k, _v in left}
        raise ValueError(
            f"{len(left)} stale pair(s) survive the repair ({', '.join(sorted(kinds))}); "
            f"first is themes {left[0][0]} and {left[0][1]} at Jaccard {left[0][3]:.3f}")


def repair(
    members: Sequence[np.ndarray], supports: Sequence[float],
    inclusions: Sequence[dict[int, float]], share: float = COLLAPSE_SHARE,
    jaccard: float = MERGE_JACCARD
) -> Repaired:
    """Both fixes, in order: collapse chains, then merge what is stale.

    Collapse runs first because it changes memberships, and a collapse can leave two themes
    identical where they were merely similar before.

    Args:
        members: Member bitsets from consensus.
        supports: Support per theme.
        inclusions: Inclusion vote per theme.
        share: Chain-collapse share.
        jaccard: Merge threshold.

    Returns:
        The repaired build.
    """
    first = collapse_chains(members, supports, inclusions, share)
    second = merge_stale(first.members, first.supports, first.inclusions, jaccard)
    assert_no_stale_pair(second.members, jaccard)
    return Repaired(
        members=second.members, supports=second.supports, inclusions=second.inclusions,
        collapsed=first.collapsed, collapsed_supports=first.collapsed_supports,
        merged=second.merged, merged_kind=second.merged_kind,
        rounds={**first.rounds, **second.rounds})
