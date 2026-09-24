"""Traversal orders for a DAG of themes: bottom-up for naming, top-down for disambiguation.

Naming runs bottom-up because top-down cannot scale -- a root of 253 members would be named from
a sample of them, while a parent named from its children's names has bounded input at every level.
Disambiguation then runs top-down, because a name is checked against parents that must already be
final.

Both orders are computed here rather than in the runner so the runner cannot get them subtly
wrong, and so the DAG's awkward cases -- several parents, a node reachable at two depths -- are
handled once.
"""

from collections.abc import Mapping, Sequence


def children_of(parents: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
    """Invert a child-to-parents mapping.

    Args:
        parents: Node id to its parent ids.

    Returns:
        Node id to its child ids, sorted. Nodes with no children are present and empty.
    """
    kids: dict[str, list[str]] = {node: [] for node in parents}
    for child, ps in parents.items():
        for parent in ps:
            if parent in kids:
                kids[parent].append(child)
    return {node: sorted(cs) for node, cs in kids.items()}


def height(parents: Mapping[str, Sequence[str]]) -> dict[str, int]:
    """Longest distance from each node DOWN to a leaf.

    Args:
        parents: Node id to its parent ids.

    Returns:
        Node id to its height. Leaves are 0.

    Height, not depth-from-root, is what orders naming: a node may be reachable at several depths
    in a DAG, but it can only be named once every child is named, and height is exactly that
    condition. Nodes of the same height can be named in one batch because none depends on another.
    """
    kids = children_of(parents)
    memo: dict[str, int] = {}

    def walk(node: str, seen: frozenset[str] = frozenset()) -> int:
        if node in memo:
            return memo[node]
        if node in seen:  # a cycle cannot occur under strict containment; refuse to hang if it does
            return 0
        cs = kids.get(node, [])
        memo[node] = 0 if not cs else 1 + max(walk(c, seen | {node}) for c in cs)
        return memo[node]

    for node in parents:
        walk(node)
    return memo


def naming_order(parents: Mapping[str, Sequence[str]]) -> list[list[str]]:
    """Nodes grouped into batches, leaves first, each batch safe to run concurrently.

    Args:
        parents: Node id to its parent ids.

    Returns:
        A list of levels; every node in a level has all its children in earlier levels.
    """
    h = height(parents)
    levels: dict[int, list[str]] = {}
    for node, value in h.items():
        levels.setdefault(value, []).append(node)
    return [sorted(levels[k]) for k in sorted(levels)]


def disambiguation_order(parents: Mapping[str, Sequence[str]]) -> list[list[str]]:
    """Nodes grouped into batches, roots first, for the top-down pass.

    Args:
        parents: Node id to its parent ids.

    Returns:
        A list of levels; every node in a level has all its parents in earlier levels.

    Depth here is the LONGEST path from a root, so a node with two parents at different depths is
    checked only after both are final -- otherwise it could be compared against a parent name that
    the pass was about to change.
    """
    memo: dict[str, int] = {}

    def walk(node: str, seen: frozenset[str] = frozenset()) -> int:
        if node in memo:
            return memo[node]
        if node in seen:
            return 0
        ps = [p for p in parents.get(node, ()) if p in parents]
        memo[node] = 0 if not ps else 1 + max(walk(p, seen | {node}) for p in ps)
        return memo[node]

    for node in parents:
        walk(node)
    levels: dict[int, list[str]] = {}
    for node, value in memo.items():
        levels.setdefault(value, []).append(node)
    return [sorted(levels[k]) for k in sorted(levels)]


def siblings_of(
    node: str, parents: Mapping[str, Sequence[str]], kids: Mapping[str, Sequence[str]]
) -> list[str]:
    """Every node sharing a parent with this one, under ANY of its parents.

    Args:
        node: The node.
        parents: Node id to its parent ids.
        kids: Node id to its child ids.

    Returns:
        Sibling ids, sorted, excluding the node itself. In a DAG a node has siblings under each of
        its parents and a name must be distinguishable from all of them -- being distinct under one
        parent while colliding under another is not distinct.
    """
    out: set[str] = set()
    for parent in parents.get(node, ()):
        out.update(kids.get(parent, ()))
    out.discard(node)
    return sorted(out)
