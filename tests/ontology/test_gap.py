"""Test R's gap machinery, on a tree whose answers are known by hand.

EXPLORATORY code, but the arithmetic still has to be right: an LCA by binary lifting is easy to
get subtly wrong in a way that produces plausible scores, and `climb_to_outsider` has a fast path
that skips the membership test whenever a node is bigger than the grouping. Both are checked here
against a four-point dendrogram small enough to verify by reading it. A final test checks the
vectorised `score_side` against a naive reference.
"""

from __future__ import annotations

import numpy as np

from thema.ontology import bitset as bits
from thema.ontology.gap import build, climb_to_outsider, lca, leaf_index, smallest_containing


def _four_points() -> tuple[np.ndarray, np.ndarray]:
    """Two pairs, far apart and DELIBERATELY ASYMMETRIC: Ward merges (0,1), then (2,3), then both.

    The asymmetry matters: with two identically tight pairs the first two merge heights are exactly
    equal, and a test asserting strictly increasing heights fails on the fixture rather than on the
    code. Pair (0,1) is the tighter one.

    Returns:
        The ``(4, 2)`` unit-vector matrix and the subset ``[0, 1, 2, 3]``.
    """
    x = np.array([[1.0, 0.01], [1.0, -0.01], [-1.0, 0.05], [-1.0, -0.05]])
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    return x.astype(np.float32), np.arange(4)


def test_dendrogram_shape_heights_and_parents() -> None:
    """Leaves, merges, heights and parents are where reading the tree says they are."""
    x, subset = _four_points()
    tree = build(x, 4, subset)

    assert tree.nodes.shape[0] == 7, "2m-1 nodes for m=4"
    assert tree.sizes.tolist() == [1, 1, 1, 1, 2, 2, 4]
    assert tree.height[:4].tolist() == [0.0, 0.0, 0.0, 0.0], "leaves have no merge height"
    assert tree.height[4] < tree.height[5] < tree.height[6], "merges arrive in increasing height"
    assert tree.parent[6] == -1, "the last merge is the root"
    assert tree.parent[0] == tree.parent[1] == 4
    assert tree.parent[2] == tree.parent[3] == 5
    assert tree.parent[4] == tree.parent[5] == 6
    assert tree.depth[6] == 0 and tree.depth[4] == 1 and tree.depth[0] == 2


def test_lca_including_when_one_node_is_the_ancestor_of_the_other() -> None:
    """The pairwise cases, and the one a naive lift gets wrong."""
    x, subset = _four_points()
    tree = build(x, 4, subset)

    assert lca(tree, np.array([0]), np.array([1]))[0] == 4
    assert lca(tree, np.array([2]), np.array([3]))[0] == 5
    assert lca(tree, np.array([0]), np.array([2]))[0] == 6
    assert lca(tree, np.array([1]), np.array([3]))[0] == 6
    # An ancestor paired with its own descendant must return the ancestor, not its parent.
    assert lca(tree, np.array([4]), np.array([0]))[0] == 4
    assert lca(tree, np.array([0]), np.array([4]))[0] == 4
    assert lca(tree, np.array([6]), np.array([3]))[0] == 6
    # A node with itself.
    assert lca(tree, np.array([5]), np.array([5]))[0] == 5
    # Vectorised over several pairs at once, same answers.
    got = lca(tree, np.array([0, 2, 0, 4]), np.array([1, 3, 2, 0]))
    assert got.tolist() == [4, 5, 6, 4]


def test_smallest_containing() -> None:
    """Folding the LCA over a set gives the smallest node holding all of it."""
    x, subset = _four_points()
    tree = build(x, 4, subset)

    assert smallest_containing(tree, np.array([0, 1])) == 4
    assert smallest_containing(tree, np.array([2, 3])) == 5
    assert smallest_containing(tree, np.array([0, 1, 2])) == 6
    assert smallest_containing(tree, np.array([0])) == 0, "one leaf is its own smallest node"


def test_climb_to_outsider_walks_past_subsets_and_stops_at_the_first_outsider() -> None:
    """The core of G_loo: how far up before something not in the grouping arrives."""
    x, subset = _four_points()
    tree = build(x, 4, subset)
    inside = bits.pack([0, 1, 2], 4)

    # Start at {0,1}, which is a SUBSET of the grouping, so the walk must not stop there.
    assert climb_to_outsider(tree, 4, inside) == 6, "node 4 is inside the grouping; climb"
    assert np.isclose(tree.height[6], tree.height.max())
    # Start at a leaf inside the grouping: same destination.
    assert climb_to_outsider(tree, 0, inside) == 6
    # A node that already holds an outsider is returned immediately.
    assert climb_to_outsider(tree, 5, inside) == 5, "node 5 holds pathway 3, an outsider"
    assert climb_to_outsider(tree, 6, inside) == 6


def test_climb_returns_minus_one_when_the_grouping_is_everything() -> None:
    """No outsider exists, so there is no height to report rather than a wrong one."""
    x, subset = _four_points()
    tree = build(x, 4, subset)
    assert climb_to_outsider(tree, 4, bits.pack([0, 1, 2, 3], 4)) == -1


def test_the_fast_path_and_the_membership_test_agree() -> None:
    """A node bigger than the grouping is assumed to hold an outsider; check that holds."""
    x, subset = _four_points()
    tree = build(x, 4, subset)
    for node in range(7):
        for group in ([0, 1], [0, 1, 2], [2, 3], [0, 2]):
            inside = bits.pack(group, 4)
            big = int(tree.sizes[node]) > len(group)
            covered = int(np.bitwise_count(tree.nodes[node] & inside).sum())
            has_outsider = covered < int(tree.sizes[node])
            if big:
                assert has_outsider, f"node {node} larger than {group} but no outsider"


def test_leaf_index_marks_undrawn_pathways() -> None:
    """A pathway the run did not draw must be -1, not 0."""
    x, _subset = _four_points()
    tree = build(x, 4, np.array([0, 2, 3]))
    got = leaf_index(tree, 4)
    assert got.tolist() == [0, -1, 1, 2]


def test_recorded_matches_the_persisted_recording_rule() -> None:
    """The nodes Test R locates are the nodes the trees recorded."""
    rng = np.random.default_rng(0)
    x = rng.standard_normal((40, 6))
    x = (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)
    tree = build(x, 40, np.arange(40))
    take = 40
    expect = np.flatnonzero((tree.sizes >= 3) & (tree.sizes <= take // 2))
    assert tree.recorded.tolist() == expect.tolist()
    assert all(3 <= tree.sizes[i] <= take // 2 for i in tree.recorded.tolist())


def _reference_scores(trees, members, packed, found, n):
    """A slow, obvious implementation of the three scores, for the vectorised one to match.

    This is deliberately written the naive way -- one grouping, one run, one walk at a time, using
    only `smallest_containing` and `climb_to_outsider` -- because the fast version inverts the loops
    and batches every grouping per run, and that is the kind of rewrite that silently changes an
    answer.

    Args:
        trees: One dendrogram per run.
        members: Per grouping, its universe indices.
        packed: Grouping bitsets.
        found: Per grouping, run to node.
        n: Universe size.

    Returns:
        The same dict `score_side` returns.
    """
    total = len(members)
    h_full = np.full(total, np.nan)
    g_loo = np.full(total, np.nan)
    g_life = np.full(total, np.nan)
    loo_runs = np.zeros(total, dtype=np.int64)
    for i in range(total):
        heights, lifes = [], []
        for run, node in found[i].items():
            tree = trees[run]
            h = float(tree.height[node])
            heights.append(h)
            up = int(tree.parent[node])
            if up >= 0 and h > 0.0:
                lifes.append(float(tree.height[up]) / h)
        if heights:
            h_full[i] = float(np.median(heights))
        if lifes:
            g_life[i] = float(np.median(lifes))
    for i in range(total):
        if not np.isfinite(h_full[i]) or h_full[i] <= 0.0:
            continue
        ratios = []
        for _run, tree in enumerate(trees):
            local = leaf_index(tree, n)
            where = local[members[i]]
            if int((where < 0).sum()) != 1:
                continue
            node = smallest_containing(tree, where[where >= 0])
            node = climb_to_outsider(tree, node, packed[i])
            if node < 0:
                continue
            ratios.append(float(tree.height[node]) / h_full[i])
        loo_runs[i] = len(ratios)
        if ratios:
            g_loo[i] = float(np.median(ratios))
    return {"h_full": h_full, "g_loo": g_loo, "g_life": g_life, "loo_runs": loo_runs}


def test_vectorised_score_side_matches_the_obvious_implementation() -> None:
    """The fast run-major version must give the same numbers as the naive one.

    Built on random blobs with real 80% draws, so the groupings genuinely differ in which runs miss
    exactly one member -- the case the batching has to get right.
    """
    from thema.ontology.gap import score_side

    rng = np.random.default_rng(7)
    n, dim = 64, 8
    centres = rng.standard_normal((8, dim))
    x = np.repeat(centres, n // 8, axis=0) + 0.25 * rng.standard_normal((n, dim))
    x = (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)

    trees, draws = [], []
    for _run in range(12):
        subset = np.sort(rng.choice(n, size=int(0.8 * n), replace=False))
        draws.append(subset)
        trees.append(build(x, n, subset))

    # Groupings of mixed size, so the padding and the left-packing both get exercised.
    members, packed, found = [], [], []
    for size in (3, 3, 4, 5, 7, 9, 4, 6):
        g = np.sort(rng.choice(n, size=size, replace=False))
        members.append(g)
        packed.append(bits.pack(g.tolist(), n))
        hits = {}
        for run, tree in enumerate(trees):
            where = leaf_index(tree, n)[g]
            if (where >= 0).all():
                hits[run] = smallest_containing(tree, where)
        found.append(hits)
    packed = np.vstack(packed)

    fast = score_side(trees, members, packed, found, n)
    slow = _reference_scores(trees, members, packed, found, n)

    for field in ("h_full", "g_loo", "g_life"):
        a, b = fast[field], slow[field]
        assert np.array_equal(np.isnan(a), np.isnan(b)), f"{field}: NaN pattern differs"
        ok = ~np.isnan(a)
        assert np.allclose(a[ok], b[ok]), f"{field}: {a[ok]} vs {b[ok]}"
    assert fast["loo_runs"].tolist() == slow["loo_runs"].tolist()
    # The fixture must actually exercise G_loo, or the test proves nothing.
    assert int(fast["loo_runs"].sum()) > 0
    assert np.isfinite(fast["g_loo"]).any()
