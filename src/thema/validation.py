"""Statistics for the validation plan. Measurement only -- nothing here decides anything.

Each function computes what `docs/spec/validation-plan.md` declares and returns it. Pass conditions
live in the plan and are applied by the caller against the values reported here, so that a
condition can never be quietly adjusted to fit a result.
"""

from collections.abc import Mapping, Sequence

import numpy as np


def shape(
    parents: Mapping[str, Sequence[str]], sizes: Mapping[str, int]
) -> dict[str, float]:
    """Test 2: the shape statistics compared against full GO BP and full Reactome.

    Args:
        parents: Node id to its parent ids.
        sizes: Node id to member count.

    Returns:
        Node count, root fraction, max and median depth, median branching factor, multi-parent
        fraction, and the node-size quartiles.
    """
    nodes = list(parents)
    children: dict[str, list[str]] = {n: [] for n in nodes}
    for node, above in parents.items():
        for parent in above:
            children.setdefault(parent, []).append(node)

    depth: dict[str, int] = {}

    def at(node: str) -> int:
        if node in depth:
            return depth[node]
        above = parents[node]
        depth[node] = 0 if not above else 1 + max(at(p) for p in above)
        return depth[node]

    depths = [at(n) for n in nodes]
    branching = [len(children[n]) for n in nodes if children[n]]
    members = [sizes[n] for n in nodes]
    return {
        "nodes": len(nodes),
        "roots": sum(1 for n in nodes if not parents[n]),
        "root_fraction": sum(1 for n in nodes if not parents[n]) / max(len(nodes), 1),
        "max_depth": int(max(depths)) if depths else 0,
        "median_depth": float(np.median(depths)) if depths else 0.0,
        "median_branching": float(np.median(branching)) if branching else 0.0,
        "multi_parent_fraction": sum(1 for n in nodes if len(parents[n]) >= 2) / max(len(nodes), 1),
        "size_p25": float(np.percentile(members, 25)) if members else 0.0,
        "size_median": float(np.median(members)) if members else 0.0,
        "size_p75": float(np.percentile(members, 75)) if members else 0.0,
        "size_max": int(max(members)) if members else 0,
    }


def best_match(
    left: Sequence[frozenset[str]], right: Sequence[frozenset[str]]
) -> tuple[list[int], list[float]]:
    """Match each set on the left to its most similar set on the right, by Jaccard.

    A greedy best-match, not an assignment: two left themes may claim the same right theme. That is
    deliberate: test 9 asks "does this theme reappear", not "is there a bijection".

    Args:
        left: Member key sets.
        right: Member key sets.

    Returns:
        The matched index per left set (-1 when ``right`` is empty), and the Jaccard of each match.
    """
    matched: list[int] = []
    scores: list[float] = []
    for block in left:
        best, score = -1, 0.0
        for index, other in enumerate(right):
            union = len(block | other)
            if not union:
                continue
            similarity = len(block & other) / union
            if similarity > score:
                best, score = index, similarity
        matched.append(best)
        scores.append(score)
    return matched, scores


def seed_stability(
    first: Sequence[frozenset[str]], second: Sequence[frozenset[str]]
) -> dict[str, float]:
    """Test 9: how much of a build is the data rather than the subsample seed.

    Args:
        first: Member key sets from one master seed.
        second: Member key sets from another, everything else identical.

    Returns:
        Theme counts, the mean and median best-match Jaccard in both directions, the fraction of
        themes matching at 0.9 or better, and the member-level agreement over matched pairs.
    """
    _forward, forward = best_match(first, second)
    _back, backward = best_match(second, first)
    matched, scores = best_match(first, second)
    agreement = []
    for index, target in enumerate(matched):
        if target < 0:
            continue
        a, b = first[index], second[target]
        if a | b:
            agreement.append(len(a & b) / len(a | b))
    return {
        "themes_first": len(first),
        "themes_second": len(second),
        "mean_jaccard": float(np.mean(forward)) if forward else 0.0,
        "median_jaccard": float(np.median(forward)) if forward else 0.0,
        "mean_jaccard_reverse": float(np.mean(backward)) if backward else 0.0,
        "matched_at_0.9": sum(1 for s in forward if s >= 0.9) / max(len(forward), 1),
        "matched_at_0.7": sum(1 for s in forward if s >= 0.7) / max(len(forward), 1),
        "matched_at_0.5": sum(1 for s in forward if s >= 0.5) / max(len(forward), 1),
        "member_agreement": float(np.mean(agreement)) if agreement else 0.0,
    }
