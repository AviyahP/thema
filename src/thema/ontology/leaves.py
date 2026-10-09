"""Universe L: the atomic pathways, with every curated summary removed.

A curated parent is a summary by construction. A Reactome parent's gene set is the union of its
children's, and GO propagates annotations upward, so 58% of the GO terms and 29% of the Reactome
pathways in the universe are internal nodes carrying no genes of their own. Clustering them
alongside their own children is what produces the placement failure in
``docs/status/2026-10-08-monotonicity.md``: general pathways cluster with other general pathways
instead of sitting above their specifics.

This module builds the universe with those summaries taken out, so a build can be tested on
whether its themes *recreate* the summaries rather than competing with them.

**Leakage.** The curated hierarchy is read here for exactly one purpose: to mark which pathways are
summaries. It never decides how the remaining pathways group, and the targets it defines are the
answer key, not an input. A build on L sees only descriptions and never the relation files.
"""

from __future__ import annotations

from collections.abc import Iterable

#: Sources with no internal hierarchy at all; every member is atomic and is always kept.
FLAT_SOURCES: frozenset[str] = frozenset({"hallmark", "btm"})


def ancestors(edges: dict[str, set[str]], key: str) -> set[str]:
    """Everything reachable from a key by following child-to-parent edges.

    Args:
        edges: Child key to its parent keys.
        key: Where to start.

    Returns:
        The reachable ancestors, excluding ``key`` unless a cycle returns to it.
    """
    seen: set[str] = set()
    stack = list(edges.get(key, ()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))
    return seen


def internal(edges: dict[str, set[str]], universe: Iterable[str]) -> set[str]:
    """Which universe pathways have at least one universe descendant.

    A pathway is internal exactly when some *other* pathway in the universe reaches it by climbing
    child-to-parent edges. Computed by accumulating ancestors over the universe rather than
    descendants per candidate: the edges point upward, so one pass up from every member marks every
    internal node, where one pass down per candidate would re-walk shared ancestors thousands of
    times.

    Args:
        edges: Child key to its parent keys, over the same key space as ``universe``.
        universe: The pathway keys in play.

    Returns:
        The internal keys, as a subset of ``universe``.
    """
    present = set(universe)
    marked: set[str] = set()
    for key in present:
        marked |= ancestors(edges, key) - {key}
    return marked & present


def leaf_universe(
    universe: Iterable[str], edges: dict[str, set[str]], sources: dict[str, str]
) -> tuple[list[str], dict[str, int]]:
    """Universe L: every pathway that is not a curated summary.

    Args:
        universe: The full universe keys.
        edges: Child key to parent keys, over Reactome and GO together.
        sources: Pathway key to its source name.

    Returns:
        ``(L in sorted order, counts per source and in total)``.
    """
    present = sorted(universe)
    marked = internal(edges, present)
    kept = [k for k in present if sources.get(k, "") in FLAT_SOURCES or k not in marked]
    counts: dict[str, int] = {}
    for key in present:
        source = sources.get(key, "?")
        counts[f"{source}_universe"] = counts.get(f"{source}_universe", 0) + 1
        if key in marked:
            counts[f"{source}_internal"] = counts.get(f"{source}_internal", 0) + 1
    for key in kept:
        source = sources.get(key, "?")
        counts[f"{source}_leaves"] = counts.get(f"{source}_leaves", 0) + 1
    counts["n_universe"] = len(present)
    counts["n_internal"] = len(marked)
    counts["n_leaves"] = len(kept)
    return kept, counts


def targets(
    edges: dict[str, set[str]], internal_keys: Iterable[str], leaves: Iterable[str],
    min_size: int = 3
) -> dict[str, frozenset[str]]:
    """The answer key: each summary's leaf descendants in L.

    Args:
        edges: Child key to parent keys.
        internal_keys: The summaries that were removed.
        leaves: Universe L.
        min_size: Smallest target kept.

    Returns:
        Summary key to its leaf set, for summaries with at least ``min_size`` leaves.
    """
    wanted = set(internal_keys)
    out: dict[str, set[str]] = {key: set() for key in wanted}
    for leaf in leaves:
        for up in ancestors(edges, leaf):
            if up in out:
                out[up].add(leaf)
    return {key: frozenset(value) for key, value in out.items() if len(value) >= min_size}
