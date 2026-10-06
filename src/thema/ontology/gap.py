"""Per-group GAP scores from Ward merge heights. EXPLORATORY -- Test R, 7 Oct 2026.

The idea under test, in Aviyah's words: a random triple of nearest neighbours recurs across
resamples as well as a real group does, but when one of its members is missing an outsider refills
it almost at once, because there is no gap. A real group should have to climb further before an
outsider arrives.

**Nothing here is part of the declared protocol, and nothing here is imported by a build.** This
module is new so that `recurrent.py`, `cut_trees.py` and `engines.py` stay untouched and no cached
side's provenance fingerprint moves -- the heights it needs are computed inside
:func:`thema.ontology.recurrent.tree_from_subset` and thrown away, so they are recomputed here
rather than by changing what wrote the trees.

Three scores, all defined in `docs/spec/test-R-2026-10-07.md`:

- ``h_full`` -- the median, over runs where the grouping is found, of the height at which its
  cluster forms.
- ``G_loo`` (primary) -- over runs missing EXACTLY one member, the height at which an outsider first
  joins the remaining members, divided by ``h_full``.
- ``G_life`` (secondary) -- the classic lifetime, the parent's height over ``h_full``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.cluster.hierarchy import linkage

from thema.cluster import distances
from thema.ontology import bitset as bits
from thema.ontology.recurrent import condensed_subset

#: Recording rule the persisted trees used, reproduced here only to locate nodes, never to change
#: them: every dendrogram node between ``min_size`` and half the draw.
MIN_SIZE = 3


@dataclass(frozen=True, slots=True)
class Dendrogram:
    """One run's FULL Ward dendrogram, with the heights the persisted tree does not keep.

    Attributes:
        subset: Sorted universe indices this run drew, length ``m``.
        nodes: ``(2m-1, words)`` bitsets. Leaves ``0..m-1`` in ``subset`` order, merges ``m..2m-2``.
        sizes: Member count per node.
        height: Merge height per node; leaves are 0.0.
        parent: Immediate parent per node, -1 at the root.
        depth: Depth from the root, for the lifting table.
        up: ``(levels, 2m-1)`` binary-lifting ancestors, ``up[0]`` being ``parent`` with the root
            pointing at itself.
        recorded: Dendrogram node index of each cluster the persisted tree recorded, in its order.
    """

    subset: np.ndarray
    nodes: np.ndarray
    sizes: np.ndarray
    height: np.ndarray
    parent: np.ndarray
    depth: np.ndarray
    up: np.ndarray
    recorded: np.ndarray


def build(
    matrix: np.ndarray, n: int, subset: np.ndarray, full: np.ndarray | None = None
) -> Dendrogram:
    """Rebuild one run's dendrogram, keeping the heights.

    The linkage call and the condensed-distance gather are the same two functions
    :func:`thema.ontology.recurrent.tree_from_subset` uses, in the same order, so the node sets come
    out identical -- which the caller must ASSERT against the persisted tree rather than assume.

    Args:
        matrix: The full ``(n, dim)`` unit-vector matrix.
        n: Universe size.
        subset: Sorted indices this run drew.
        full: Condensed distances over all ``n`` points, to gather from instead of recomputing.

    Returns:
        The dendrogram.
    """
    take = int(len(subset))
    words = bits.words_for(n)
    condensed = condensed_subset(full, n, subset) if full is not None else distances(matrix[subset])
    z = linkage(condensed, method="ward")

    total = 2 * take - 1
    nodes = np.zeros((total, words), dtype=np.uint64)
    for local, index in enumerate(subset.tolist()):
        nodes[local][index // bits.WORD] = np.uint64(1) << np.uint64(index % bits.WORD)
    parent = np.full(total, -1, dtype=np.int64)
    height = np.zeros(total, dtype=np.float64)
    for i in range(take - 1):
        left, right = int(z[i, 0]), int(z[i, 1])
        nodes[take + i] = nodes[left] | nodes[right]
        parent[left] = parent[right] = take + i
        height[take + i] = float(z[i, 2])
    sizes = bits.count_rows(nodes)

    # Depth from the root, computed downward so a child is always after its parent: merges arrive in
    # increasing height, so the highest index is the root and a reverse sweep sees parents first.
    depth = np.zeros(total, dtype=np.int64)
    order = np.arange(total - 1, -1, -1)
    for node in order:
        up = parent[node]
        if up >= 0:
            depth[node] = depth[up] + 1
    # Binary lifting, so the LCA of many queries is answered with a handful of vectorised gathers
    # instead of a Python climb per pair. up[0] points the root at itself, which makes every lift a
    # plain gather with no boundary test.
    levels = max(1, int(np.ceil(np.log2(max(int(depth.max()), 1) + 1))) + 1)
    table = np.empty((levels, total), dtype=np.int64)
    table[0] = np.where(parent >= 0, parent, np.arange(total))
    for level in range(1, levels):
        table[level] = table[level - 1][table[level - 1]]

    recorded = np.flatnonzero((sizes >= MIN_SIZE) & (sizes <= take // 2))
    return Dendrogram(subset=subset, nodes=nodes, sizes=sizes, height=height, parent=parent,
                      depth=depth, up=table, recorded=recorded)


def lca(tree: Dendrogram, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Lowest common ancestor of two node arrays, vectorised.

    Args:
        tree: The dendrogram.
        a: Node indices.
        b: Node indices, same shape.

    Returns:
        The LCA of each pair.
    """
    x, y = np.asarray(a, dtype=np.int64).copy(), np.asarray(b, dtype=np.int64).copy()
    # Lift the deeper of each pair to its partner's depth, then lift both together.
    diff = tree.depth[x] - tree.depth[y]
    deeper = np.where(diff > 0, x, y)
    shallower = np.where(diff > 0, y, x)
    gap = np.abs(diff)
    for level in range(tree.up.shape[0]):
        step = (gap >> level) & 1
        deeper = np.where(step.astype(bool), tree.up[level][deeper], deeper)
    x, y = deeper, shallower
    for level in range(tree.up.shape[0] - 1, -1, -1):
        up_x, up_y = tree.up[level][x], tree.up[level][y]
        move = up_x != up_y
        x = np.where(move, up_x, x)
        y = np.where(move, up_y, y)
    return np.where(x == y, x, tree.up[0][x])


def smallest_containing(tree: Dendrogram, leaves: np.ndarray) -> int:
    """Smallest dendrogram node holding every given leaf.

    Args:
        tree: The dendrogram.
        leaves: Local leaf indices, at least one.

    Returns:
        The node index.
    """
    node = int(leaves[0])
    for other in leaves[1:].tolist():
        node = int(lca(tree, np.array([node]), np.array([other]))[0])
    return node


def climb_to_outsider(tree: Dendrogram, start: int, inside: np.ndarray) -> int:
    """Walk up from ``start`` to the first node holding a pathway outside ``inside``.

    The common case resolves without touching a bitset: a node larger than ``inside`` must contain
    an outsider, and the grouping has at most nine members, so only the smallest few nodes need the
    membership test at all.

    Args:
        tree: The dendrogram.
        start: Node to begin at.
        inside: Bitset of the grouping's members.

    Returns:
        The first node with an outsider, or -1 if the root has none.
    """
    node = int(start)
    limit = int(np.bitwise_count(inside).sum())
    while node >= 0:
        if int(tree.sizes[node]) > limit:
            return node
        covered = int(np.bitwise_count(tree.nodes[node] & inside).sum())
        if covered < int(tree.sizes[node]):
            return node
        node = int(tree.parent[node])
    return -1


def leaf_index(tree: Dendrogram, n: int) -> np.ndarray:
    """Map every universe index to its local leaf, or -1 when this run did not draw it.

    Args:
        tree: The dendrogram.
        n: Universe size.

    Returns:
        An ``(n,)`` array of local leaf indices.
    """
    out = np.full(n, -1, dtype=np.int64)
    out[tree.subset] = np.arange(len(tree.subset), dtype=np.int64)
    return out


def score_side(
    trees: list[Dendrogram],
    members: list[np.ndarray],
    packed: np.ndarray,
    found: list[dict[int, int]],
    n: int,
) -> dict[str, np.ndarray]:
    """The three scores for every grouping on one side, RUN-MAJOR and vectorised.

    The first version of this looped over (grouping, run) pairs and called the LCA on one-element
    arrays. At the real scale -- 73,483 groupings of size 3-9 against 200 runs -- that is about five
    million walks, each costing a few hundred NumPy calls on arrays of length one, and it would have
    taken hours. So the loop is inverted: one pass per run, with every grouping that qualifies in
    that run handled in a single batch. Seven vectorised LCA folds and a short vectorised climb per
    run replace the five million individual walks.

    Args:
        trees: One dendrogram per run, in run order.
        members: Per grouping, its universe indices.
        packed: ``(g, words)`` grouping bitsets.
        found: Per grouping, ``{run: dendrogram node}`` for the runs that found it.
        n: Universe size.

    Returns:
        ``h_full``, ``g_loo``, ``g_life`` and ``loo_runs``, one entry per grouping. A score with no
        contributing run is NaN.
    """
    total = len(members)
    width = max((len(m) for m in members), default=0)
    # Members padded to a rectangle so a run can test every grouping at once. -1 marks padding and
    # is distinguishable from "not drawn", which the local index also reports as -1, because the
    # padding mask is known separately.
    member_pad = np.full((total, width), -1, dtype=np.int64)
    sizes = np.zeros(total, dtype=np.int64)
    for i, m in enumerate(members):
        member_pad[i, : len(m)] = m
        sizes[i] = len(m)
    real = member_pad >= 0

    h_sum = [[] for _ in range(total)]
    life_sum = [[] for _ in range(total)]
    loo_sum = [[] for _ in range(total)]

    # h_full and G_life come from the runs that FOUND the grouping, which is the matching's verdict.
    for index in range(total):
        for run, node in found[index].items():
            tree = trees[run]
            h = float(tree.height[node])
            h_sum[index].append(h)
            up = int(tree.parent[node])
            if up >= 0 and h > 0.0:
                life_sum[index].append(float(tree.height[up]) / h)
    h_full = np.array([np.median(v) if v else np.nan for v in h_sum])
    g_life = np.array([np.median(v) if v else np.nan for v in life_sum])

    # G_loo needs no matching: which runs miss exactly one member is a property of the draw.
    for tree in trees:
        local = np.full(n, -1, dtype=np.int64)
        local[tree.subset] = np.arange(len(tree.subset), dtype=np.int64)
        where = np.where(real, local[np.clip(member_pad, 0, None)], -1)
        drawn = (where >= 0) & real
        missing = sizes - drawn.sum(axis=1)
        pick = np.flatnonzero((missing == 1) & np.isfinite(h_full) & (h_full > 0.0))
        if not len(pick):
            continue

        # The present members, left-packed so column j is the j-th present member of each grouping.
        block = where[pick]
        order = np.argsort(~(block >= 0), axis=1, kind="stable")
        packed_leaves = np.take_along_axis(block, order, axis=1)
        counts = drawn[pick].sum(axis=1)

        node = packed_leaves[:, 0].copy()
        for column in range(1, width):
            partner = packed_leaves[:, column]
            live = partner >= 0
            if not live.any():
                break
            candidate = lca(tree, node[live], partner[live])
            node[live] = candidate

        # Climb while the node is still a subset of the grouping. A node larger than the grouping
        # must hold an outsider, so only the smallest few need the membership test at all.
        limit = sizes[pick]
        alive = np.ones(len(pick), dtype=bool)
        for _step in range(width + 2):
            if not alive.any():
                break
            idx = np.flatnonzero(alive)
            small = tree.sizes[node[idx]] <= limit[idx]
            if not small.any():
                break
            check = idx[small]
            covered = np.bitwise_count(tree.nodes[node[check]] & packed[pick][check]).sum(axis=1)
            inside = covered >= tree.sizes[node[check]]
            move = check[inside]
            if not len(move):
                break
            up = tree.parent[node[move]]
            node[move] = np.where(up >= 0, up, node[move])
            alive[:] = False
            alive[move[up >= 0]] = True

        ratio = tree.height[node] / h_full[pick]
        ok = np.isfinite(ratio) & (counts >= 1)
        for position, g in enumerate(pick.tolist()):
            if ok[position]:
                loo_sum[g].append(float(ratio[position]))

    g_loo = np.array([np.median(v) if v else np.nan for v in loo_sum])
    loo_runs = np.array([len(v) for v in loo_sum], dtype=np.int64)
    return {"h_full": h_full, "g_loo": g_loo, "g_life": g_life, "loo_runs": loo_runs}
