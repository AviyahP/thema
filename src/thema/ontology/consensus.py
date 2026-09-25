r"""Greedy consensus over voted clusters, so accepted themes are mutually compatible.

The confirmatory build accepted every family that passed the per-size gate and handed the lot to
``hasse``. Nothing checked that the accepted sets were compatible, and 39 roots came out -- eleven
of them near-nested pairs severed by one member landing on opposite sides of the 0.25 cutoff in two
different vote populations. ``n0610`` (302) and ``n0431`` (342) share 301 members; ``Signaling by
MST1`` scored 0.269 in one vote and 0.229 in the other, so the smaller set is not a subset and gets
no parent.

``hasse`` is correct and stays strict. ``families`` is correct. What was missing is the step every
consensus method in phylogenetics has: reconcile the accepted clusters with one another before
drawing the hierarchy. That is majority-rule / greedy consensus -- Bryant 2003, "A classification
of consensus methods for phylogenetics"; Felsenstein 2004, *Inferring Phylogenies* ch. 30. The
classical rule is exact set compatibility: nested or disjoint. This module extends it to FUZZY
voted clusters, whose boundaries are decided by a threshold on a vote and are therefore soft by
construction.

**The resolution is asymmetric, and that is the whole point.** When a small theme nearly nests in a
large one, the LARGE theme grows to contain it. The earlier attempt rejected the loser of each
conflict, and on this data that inverted the hierarchy: support is anti-correlated with size
(Spearman -0.583 over the 844 candidates -- median support 0.94 at sizes 3-5 against 0.49 at 100+),
because a large theme recurs approximately while a small tight one recurs exactly. Seating by
support then let 6- and 12-member themes evict the 953- and 503-member umbrellas above them,
tripling the roots and stranding 87 pathways. Classical consensus assumes support is comparable
across clusters; here it is confounded with size, so nothing may be discarded for having low
support. Growing the larger set respects the confound: no theme is ever rejected for being big.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np

from thema.ontology import bitset as bits

#: A smaller theme may sit outside a larger one by at most this share of itself and still be read
#: as a sub-theme of it rather than a separate theme. DECLARED BEFORE THE RUN.
DEFAULT_STRAY = 0.10

#: Two themes neither of which contains the other are the SAME theme at or above this Jaccard.
#: The same value as the matching rule's theta, and declared for the same reason: one notion of
#: "these are the same set" across the method.
DEFAULT_JACCARD = 0.70

#: Absolute floor on strays: a single member outside is noise at any size, so a 3-member theme with
#: one stray is a sub-theme even though 1/3 far exceeds :data:`DEFAULT_STRAY`.
STRAY_FLOOR = 1


class Rule(StrEnum):
    """Which rule decided a pair. Tested in this order."""

    NESTED = "nested"            # 1. B strictly inside A; hasse draws it
    INHERITED = "inherited"      # 2. B is a sub-theme; A grows to contain it
    SUPERSEDED = "superseded"    # 3. same theme, neither contains; lower support is dropped
    COEXIST = "coexist"          # 4. multi-parent, spec section 10.8


@dataclass
class Inheritance:
    """One member a parent gained so a sub-theme could nest.

    Attributes:
        parent: Candidate index of the theme that grew.
        member: The pathway index added.
        source: Candidate index of the sub-theme it came from.
        inclusion: The member's inclusion in the sub-theme's own vote.
        propagated: False for the direct parent, True for an ancestor that gained it in turn.
    """

    parent: int
    member: int
    source: int
    inclusion: float
    propagated: bool


@dataclass
class Outcome:
    """What consensus did.

    Attributes:
        accepted: Candidate indices that became nodes, in acceptance order.
        members: Final member bitset per accepted node, aligned with ``accepted``.
        superseded: ``{dropped candidate: the candidate that beat it}``.
        inherited: Every member added to a parent, in order.
        rules: Count per :class:`Rule`.
        grew: ``{accepted candidate: how many members it gained}``.
    """

    accepted: list[int]
    members: list[np.ndarray]
    superseded: dict[int, int] = field(default_factory=dict)
    inherited: list[Inheritance] = field(default_factory=list)
    rules: dict[str, int] = field(default_factory=dict)
    grew: dict[int, int] = field(default_factory=dict)


def order_candidates(support: Sequence[float], member_sets: Sequence[np.ndarray]) -> list[int]:
    """Decreasing support, then larger size, then bitset key.

    Order decides only rule 3 -- which of two same-themes is kept -- but it must still be total and
    reproducible.

    Args:
        support: Support per candidate.
        member_sets: Member bitset per candidate.

    Returns:
        Candidate indices in processing order.
    """
    sizes = [bits.count(block) for block in member_sets]
    return sorted(
        range(len(member_sets)),
        key=lambda i: (-float(support[i]), -sizes[i], bits.key(member_sets[i])),
    )


def classify(
    left: np.ndarray, right: np.ndarray, stray: float, jaccard: float
) -> tuple[Rule, bool]:
    """Which rule a pair falls under, and whether ``left`` is the larger of the two.

    Args:
        left: One member bitset.
        right: The other.
        stray: Stray share threshold.
        jaccard: Same-theme threshold.

    Returns:
        The rule, and True when ``left`` plays the role of A (the larger).
    """
    size_left, size_right = bits.count(left), bits.count(right)
    left_is_a = size_left >= size_right
    a, b = (left, right) if left_is_a else (right, left)
    size_a, size_b = (size_left, size_right) if left_is_a else (size_right, size_left)

    out_of_a = bits.count(b & ~a)   # |B \ A|
    out_of_b = bits.count(a & ~b)   # |A \ B|
    if size_b == 0 or size_a == 0:
        return Rule.COEXIST, left_is_a
    # Rule 1 is STRICT containment. Identical sets fall to rule 3, where one is superseded --
    # accepting both would put two nodes with the same members into hasse, which draws no edge
    # between them and leaves both as roots.
    if out_of_a == 0 and out_of_b > 0:
        return Rule.NESTED, left_is_a

    strays_b = out_of_a / size_b
    strays_a = out_of_b / size_a
    if (strays_b <= stray or out_of_a <= STRAY_FLOOR) and strays_a > stray:
        return Rule.INHERITED, left_is_a

    union = size_a + size_b - bits.count(a & b)
    if union and bits.count(a & b) / union >= jaccard:
        return Rule.SUPERSEDED, left_is_a
    return Rule.COEXIST, left_is_a


def _propagate(
    out: Outcome,
    grown: int,
    before: np.ndarray,
    added: np.ndarray,
    source: int,
    inclusions: Sequence[dict[int, float]],
) -> None:
    """Give every accepted ancestor of a grown theme the members it gained.

    An ancestor is an accepted set that strictly contained the grown set BEFORE the addition. If it
    did not also gain them it would stop containing its own descendant, which is the very defect
    this pass exists to remove. Additions only, so the worklist drains.

    Args:
        out: The outcome being built; mutated in place.
        grown: Position in ``out.members`` of the theme that just grew.
        before: That theme's member bitset before the addition.
        added: The members it gained.
        source: Candidate index the members came from.
        inclusions: Per candidate, its own vote.
    """
    work = [(grown, before)]
    seen = {grown}
    while work:
        position, previous = work.pop()
        for other in range(len(out.members)):
            if other in seen:
                continue
            block = out.members[other]
            # Strictly contained the previous set, and is missing some of what was added.
            if bits.count(previous & ~block) == 0 and bits.count(block & ~previous) > 0:
                missing = added & ~block
                if bits.count(missing) == 0:
                    continue
                was = block.copy()
                out.members[other] = block | missing
                candidate = out.accepted[other]
                out.grew[candidate] = out.grew.get(candidate, 0) + bits.count(missing)
                for member in bits.unpack(missing):
                    out.inherited.append(
                        Inheritance(candidate, member, source,
                                    float(inclusions[source].get(member, 0.0)), True)
                    )
                seen.add(other)
                work.append((other, was))


def consensus_pairwise(
    member_sets: Sequence[np.ndarray],
    support: Sequence[float],
    inclusions: Sequence[dict[int, float]],
    n_bits: int,
    stray: float = DEFAULT_STRAY,
    jaccard: float = DEFAULT_JACCARD,
    max_rounds: int = 50,
) -> Outcome:
    """Greedy consensus, one pair at a time. The reference implementation.

    Deliberately the plain version: it defines the semantics the vectorised one is proved against,
    as the ancestor walk defined matching and the size-window walk defined families.

    Args:
        member_sets: Candidate member bitsets.
        support: Support per candidate.
        inclusions: Per candidate, its own vote, for recording what an inheritance cost.
        n_bits: Bitset width.
        stray: Stray share threshold. Declared, not tuned.
        jaccard: Same-theme threshold. Declared, not tuned.
        max_rounds: Fixed-point guard per newcomer.

    Returns:
        What consensus did.
    """
    out = Outcome(accepted=[], members=[])
    counts: dict[str, int] = {rule.value: 0 for rule in Rule}

    for candidate in order_candidates(support, member_sets):
        block = member_sets[candidate].copy()
        dropped_for = -1
        rounds = 0

        while True:
            rounds += 1
            changed = False
            for position in range(len(out.members)):
                accepted_block = out.members[position]
                rule, newcomer_is_a = classify(block, accepted_block, stray, jaccard)
                if rule is Rule.SUPERSEDED:
                    # Processing order is decreasing support, so the seated theme has at least as
                    # much support and keeps its place.
                    dropped_for = out.accepted[position]
                    break
                if rule is not Rule.INHERITED:
                    continue
                if newcomer_is_a:
                    added = accepted_block & ~block
                    block = block | added
                    for member in bits.unpack(added):
                        out.inherited.append(
                            Inheritance(candidate, member, out.accepted[position],
                                        float(inclusions[out.accepted[position]].get(member, 0.0)),
                                        False)
                        )
                    out.grew[candidate] = out.grew.get(candidate, 0) + bits.count(added)
                else:
                    added = block & ~accepted_block
                    was = accepted_block.copy()
                    out.members[position] = accepted_block | added
                    grown_candidate = out.accepted[position]
                    out.grew[grown_candidate] = out.grew.get(grown_candidate, 0) + bits.count(added)
                    for member in bits.unpack(added):
                        out.inherited.append(
                            Inheritance(grown_candidate, member, candidate,
                                        float(inclusions[candidate].get(member, 0.0)), False)
                        )
                    _propagate(out, position, was, added, candidate, inclusions)
                counts[Rule.INHERITED.value] += 1
                changed = True
                break
            if dropped_for >= 0 or not changed or rounds >= max_rounds:
                break

        if dropped_for >= 0:
            out.superseded[candidate] = dropped_for
            counts[Rule.SUPERSEDED.value] += 1
            continue
        out.accepted.append(candidate)
        out.members.append(block)

    counts[Rule.NESTED.value] = len(out.accepted)
    out.rules = counts
    return out


def _rules_against(
    block: np.ndarray,
    accepted_stack: np.ndarray,
    accepted_sizes: np.ndarray,
    shared: np.ndarray,
    stray: float,
    jaccard: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Classify a newcomer against every accepted theme at once.

    One boolean mask per rule, resolved by :func:`np.select` in the documented order so the earlier
    rule wins exactly as the pairwise ``if`` chain does. Every quantity comes from the intersection
    counts and the row sums; no bitset arithmetic is needed to decide a rule.

    Args:
        block: The newcomer's current member bitset.
        accepted_stack: ``(k, words)`` accepted bitsets, in acceptance order.
        accepted_sizes: Member count per accepted theme.
        shared: ``|X n Y|`` per accepted theme.
        stray: Stray share threshold.
        jaccard: Same-theme threshold.

    Returns:
        A rule code per accepted theme, and a mask that is True where the NEWCOMER is the larger.
    """
    size = bits.count(block)
    newcomer_is_a = size >= accepted_sizes
    size_a = np.where(newcomer_is_a, size, accepted_sizes)
    size_b = np.where(newcomer_is_a, accepted_sizes, size)
    # |B \ A| and |A \ B| follow from the sizes and the intersection.
    out_of_a = size_b - shared
    out_of_b = size_a - shared

    with np.errstate(invalid="ignore", divide="ignore"):
        strays_b = np.where(size_b > 0, out_of_a / np.maximum(size_b, 1), 1.0)
        strays_a = np.where(size_a > 0, out_of_b / np.maximum(size_a, 1), 1.0)
        union = size_a + size_b - shared
        similarity = np.where(union > 0, shared / np.maximum(union, 1), 0.0)

    empty = (size_a == 0) | (size_b == 0)
    nested = (out_of_a == 0) & (out_of_b > 0)
    sub_theme = ((strays_b <= stray) | (out_of_a <= STRAY_FLOOR)) & (strays_a > stray)
    same = similarity >= jaccard

    code = np.select(
        [empty, nested, sub_theme, same],
        [_COEXIST, _NESTED, _INHERITED, _SUPERSEDED],
        default=_COEXIST,
    )
    return code.astype(np.int64), newcomer_is_a


_NESTED, _INHERITED, _SUPERSEDED, _COEXIST = 0, 1, 2, 3
_RULE_ORDER = (Rule.NESTED, Rule.INHERITED, Rule.SUPERSEDED, Rule.COEXIST)


def consensus(
    member_sets: Sequence[np.ndarray],
    support: Sequence[float],
    inclusions: Sequence[dict[int, float]],
    n_bits: int,
    stray: float = DEFAULT_STRAY,
    jaccard: float = DEFAULT_JACCARD,
    max_rounds: int = 50,
    method: str = "vector",
) -> Outcome:
    """Greedy consensus over voted clusters.

    ``method="pairwise"`` runs :func:`consensus_pairwise`, the reference, kept callable so the two
    can be proved identical.

    Args:
        member_sets: Candidate member bitsets.
        support: Support per candidate.
        inclusions: Per candidate, its own vote.
        n_bits: Bitset width.
        stray: Stray share threshold. Declared before the run.
        jaccard: Same-theme threshold. Declared before the run.
        max_rounds: Fixed-point guard per newcomer.
        method: ``"vector"`` or ``"pairwise"``.

    Returns:
        What consensus did.

    Raises:
        ValueError: If ``method`` is neither.
    """
    if method == "pairwise":
        return consensus_pairwise(
            member_sets, support, inclusions, n_bits, stray, jaccard, max_rounds
        )
    if method != "vector":
        raise ValueError(f"method must be 'vector' or 'pairwise', not {method!r}")

    out = Outcome(accepted=[], members=[])
    counts: dict[str, int] = {rule.value: 0 for rule in Rule}
    if not member_sets:
        out.rules = counts
        return out

    words = member_sets[0].shape[0]
    stack = np.zeros((0, words), dtype=np.uint64)
    sizes = np.zeros(0, dtype=np.int64)

    for candidate in order_candidates(support, member_sets):
        block = member_sets[candidate].copy()
        dropped_for = -1
        rounds = 0

        while True:
            rounds += 1
            changed = False
            if len(sizes):
                shared = np.bitwise_count(block[None, :] & stack).sum(axis=1).astype(np.int64)
                code, newcomer_is_a = _rules_against(
                    block, stack, sizes, shared, stray, jaccard
                )
                acting = np.flatnonzero((code == _INHERITED) | (code == _SUPERSEDED))
                if len(acting):
                    position = int(acting[0])
                    if code[position] == _SUPERSEDED:
                        dropped_for = out.accepted[position]
                    else:
                        accepted_block = stack[position]
                        if bool(newcomer_is_a[position]):
                            added = accepted_block & ~block
                            block = block | added
                            source = out.accepted[position]
                            for member in bits.unpack(added):
                                out.inherited.append(
                                    Inheritance(candidate, member, source,
                                                float(inclusions[source].get(member, 0.0)), False)
                                )
                            out.grew[candidate] = out.grew.get(candidate, 0) + bits.count(added)
                        else:
                            added = block & ~accepted_block
                            was = accepted_block.copy()
                            out.members[position] = accepted_block | added
                            stack[position] = out.members[position]
                            sizes[position] = bits.count(out.members[position])
                            grown = out.accepted[position]
                            out.grew[grown] = out.grew.get(grown, 0) + bits.count(added)
                            for member in bits.unpack(added):
                                out.inherited.append(
                                    Inheritance(grown, member, candidate,
                                                float(inclusions[candidate].get(member, 0.0)),
                                                False)
                                )
                            _propagate(out, position, was, added, candidate, inclusions)
                            # Only the rows the propagation touched need refreshing.
                            for index in range(len(out.members)):
                                stack[index] = out.members[index]
                                sizes[index] = bits.count(out.members[index])
                        counts[Rule.INHERITED.value] += 1
                        changed = True
            if dropped_for >= 0 or not changed or rounds >= max_rounds:
                break

        if dropped_for >= 0:
            out.superseded[candidate] = dropped_for
            counts[Rule.SUPERSEDED.value] += 1
            continue
        out.accepted.append(candidate)
        out.members.append(block)
        stack = np.vstack([stack, block[None, :]])
        sizes = np.append(sizes, bits.count(block))

    counts[Rule.NESTED.value] = len(out.accepted)
    out.rules = counts
    return out
