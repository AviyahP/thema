"""One merge rule from the leaves to the top: normalised-centroid cosine linkage.

Ward's cost of merging A and B is ``|A||B|/(|A|+|B|) * ||c_A - c_B||^2`` over **unnormalised** mean
vectors. A large diffuse cluster has a short mean, near the origin, so the cost of absorbing a small
B into it is about ``|B| * ||c_B||^2`` whatever B is about -- the big cluster's own content barely
enters. Small groups are therefore taken into blobs one at a time, which is what produces roots with
a hundred-odd children and no middle level.

:func:`centroid_cosine` replaces that with one rule used at every level: merge the pair whose
**normalised** centroids are most similar,

    sim(A, B) = cos(c_A / ||c_A||, c_B / ||c_B||)

so a cluster's direction matters and its diffuseness cannot buy it merges. Equivalently this is the
mean pairwise cosine between A and B divided by the tightness of each, which is why it does not
reward a cluster for being spread out.

**The implementation keeps unnormalised sums**, never means. With ``s_A = sum of A's vectors``,

    cos(c_A, c_B) = (s_A . s_B) / (||s_A|| ||s_B||)        and     s_{A+B} = s_A + s_B

so a merge is one vector addition and the similarity is exact at every step -- no drift, and no
re-reading of a cluster's members. ``tests/ontology/test_linkage.py`` checks that against centroids
recomputed from scratch.

**Heights are not monotone and must not be used as a hierarchy.** Merging A and B can leave the new
cluster *more* similar to some C than A and B were to each other, so the next merge may happen at a
higher similarity than the last. :func:`centroid_cosine` counts those inversions and returns the
count; the containment DAG orders nodes by membership, never by height.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Agglomeration:
    """A full merge sequence, as the order it happened in.

    Attributes:
        merges: ``(left, right)`` cluster ids per step, in merge order. Ids below ``n`` are leaves;
            step ``t`` creates id ``n + t``.
        similarity: The similarity each merge happened at, aligned with ``merges``.
        inversions: How many merges happened at a HIGHER similarity than the merge before them.
        seconds: Wall time.
    """

    merges: np.ndarray
    similarity: np.ndarray
    inversions: int
    seconds: float

    def members(self, n: int) -> list[np.ndarray]:
        """Member leaf indices for every node, leaves first then each merge.

        Args:
            n: Number of leaves.

        Returns:
            ``2n - 1`` arrays; index ``i < n`` is leaf ``i``, index ``n + t`` is merge ``t``.
        """
        out: list[np.ndarray] = [np.array([i], dtype=np.int64) for i in range(n)]
        for left, right in self.merges:
            out.append(np.concatenate([out[int(left)], out[int(right)]]))
        return out

    def cut(self, n: int, clusters: int) -> list[np.ndarray]:
        """Replay the merges until ``clusters`` clusters remain.

        A cut is exact here rather than a threshold on a height, which matters because the heights
        are not monotone: there is no similarity at which "the tree has 30 clusters".

        Args:
            n: Number of leaves.
            clusters: How many clusters to stop at.

        Returns:
            Member arrays, largest first.
        """
        alive = {i: np.array([i], dtype=np.int64) for i in range(n)}
        steps = max(0, n - clusters)
        for position, (left, right) in enumerate(self.merges[:steps]):
            joined = np.concatenate([alive.pop(int(left)), alive.pop(int(right))])
            alive[n + position] = joined
        return sorted(alive.values(), key=len, reverse=True)


def centroid_cosine(vectors: np.ndarray) -> Agglomeration:
    """Agglomerate by normalised-centroid cosine, highest similarity first.

    The similarity matrix is held in full and each row keeps its own best partner, so a step costs
    one pass over the ``k`` cached maxima rather than a scan of ``k^2`` entries. Only rows whose
    best partner was just consumed are recomputed. That turns the obvious cubic loop into roughly
    quadratic work, which is what makes 200 trees per side affordable rather than only one.

    Args:
        vectors: ``(n, dim)`` unit rows.

    Returns:
        The merge sequence.

    Raises:
        ValueError: If fewer than two rows are given.
    """
    import time

    clock = time.perf_counter()
    n = int(vectors.shape[0])
    if n < 2:
        raise ValueError(f"need at least two rows to agglomerate, got {n}")

    sums = np.array(vectors, dtype=np.float32, copy=True)
    norms = np.linalg.norm(sums, axis=1)
    unit = sums / np.where(norms[:, None] == 0, 1.0, norms[:, None])
    sim = (unit @ unit.T).astype(np.float32)
    np.fill_diagonal(sim, -np.inf)

    alive = np.ones(n, dtype=bool)
    ids = np.arange(n, dtype=np.int64)
    best = sim.max(axis=1)
    partner = sim.argmax(axis=1)

    merges = np.zeros((n - 1, 2), dtype=np.int64)
    heights = np.zeros(n - 1, dtype=np.float64)
    inversions = 0

    for step in range(n - 1):
        masked = np.where(alive, best, -np.inf)
        left = int(np.argmax(masked))
        right = int(partner[left])
        value = float(sim[left, right])
        merges[step] = (ids[left], ids[right])
        heights[step] = value
        if step and value > heights[step - 1] + 1e-9:
            inversions += 1

        # Merge into `left`: the sum is exact, so the new row is exact too.
        sums[left] += sums[right]
        alive[right] = False
        ids[left] = n + step
        sim[right, :] = -np.inf
        sim[:, right] = -np.inf

        norm_left = float(np.linalg.norm(sums[left]))
        if norm_left == 0.0:
            row = np.full(n, -np.inf, dtype=np.float32)
        else:
            live = np.flatnonzero(alive)
            other = sums[live]
            other_norm = np.linalg.norm(other, axis=1)
            row = np.full(n, -np.inf, dtype=np.float32)
            safe = np.where(other_norm == 0, 1.0, other_norm)
            row[live] = (other @ sums[left]) / (safe * norm_left)
        row[left] = -np.inf
        sim[left, :] = row
        sim[:, left] = row

        # Any row whose best partner was just consumed, or that now faces a changed row, is stale.
        stale = np.flatnonzero(alive & ((partner == right) | (partner == left)))
        for index in stale:
            best[index] = sim[index].max()
            partner[index] = int(sim[index].argmax())
        best[left] = sim[left].max()
        partner[left] = int(sim[left].argmax())
        # A row not otherwise stale may still have gained a better partner in `left`.
        gained = np.flatnonzero(alive & (row > best))
        for index in gained:
            if index == left:
                continue
            best[index] = row[index]
            partner[index] = left
        best[right] = -np.inf

    return Agglomeration(merges=merges, similarity=heights, inversions=inversions,
                         seconds=time.perf_counter() - clock)


def naive_centroid_cosine(vectors: np.ndarray) -> Agglomeration:
    """The obvious cubic version, kept callable as the reference for :func:`centroid_cosine`.

    It recomputes every pairwise similarity from the current sums at every step, so it shares no
    bookkeeping with the fast path and a disagreement between them is a real disagreement.

    Args:
        vectors: ``(n, dim)`` unit rows.

    Returns:
        The merge sequence.
    """
    import time

    clock = time.perf_counter()
    n = int(vectors.shape[0])
    sums = {i: np.array(vectors[i], dtype=np.float64) for i in range(n)}
    label = {i: i for i in range(n)}
    merges = np.zeros((n - 1, 2), dtype=np.int64)
    heights = np.zeros(n - 1, dtype=np.float64)
    inversions = 0
    for step in range(n - 1):
        keys = sorted(sums)
        stack = np.vstack([sums[k] for k in keys])
        norm = np.linalg.norm(stack, axis=1, keepdims=True)
        unit = stack / np.where(norm == 0, 1.0, norm)
        grid = unit @ unit.T
        np.fill_diagonal(grid, -np.inf)
        a, b = np.unravel_index(int(np.argmax(grid)), grid.shape)
        ka, kb = keys[int(a)], keys[int(b)]
        value = float(grid[a, b])
        merges[step] = (label[ka], label[kb])
        heights[step] = value
        if step and value > heights[step - 1] + 1e-9:
            inversions += 1
        sums[ka] = sums[ka] + sums[kb]
        label[ka] = n + step
        del sums[kb], label[kb]
    return Agglomeration(merges=merges, similarity=heights, inversions=inversions,
                         seconds=time.perf_counter() - clock)


def run_from_merges(
    merges: np.ndarray, n: int, subset: np.ndarray, min_size: int
) -> object:
    """A :class:`~thema.ontology.recurrent.Run` from any merge sequence, not only Ward's.

    ``recurrent.tree_from_subset`` calls scipy's ``linkage`` itself, so there is no way to hand it a
    tree built by another rule. This does the identical bookkeeping over a supplied merge sequence
    instead. The sequence must use scipy's convention -- ids below ``take`` are the subset's own
    leaves in order, step ``t`` creates id ``take + t`` -- which is what :func:`centroid_cosine`
    emits.

    **Heights are never read**, here or in ``tree_from_subset``: the record is built from the merge
    structure alone, which is why a rule with non-monotone heights can be plugged in at all.

    ``tests/ontology/test_linkage.py`` feeds Ward's own merges through this and asserts the result
    is field-for-field identical to ``tree_from_subset``'s, so the duplication is checked rather
    than trusted.

    Args:
        merges: ``(take - 1, 2)`` child id pairs, in merge order.
        n: Universe size.
        subset: Sorted global indices this run drew.
        min_size: Smallest cluster worth recording.

    Returns:
        The run's record.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import Run

    take = len(subset)
    words = bits.words_for(n)
    present = bits.pack(subset.tolist(), n)

    total = 2 * take - 1
    node_bits = np.zeros((total, words), dtype=np.uint64)
    for local, global_index in enumerate(subset):
        node_bits[local][global_index // bits.WORD] = np.uint64(1) << np.uint64(
            int(global_index) % bits.WORD)
    tree_parent = np.full(total, -1, dtype=np.int64)
    for step in range(take - 1):
        left, right = int(merges[step, 0]), int(merges[step, 1])
        node_bits[take + step] = node_bits[left] | node_bits[right]
        tree_parent[left] = tree_parent[right] = take + step

    sizes = bits.count_rows(node_bits)
    recorded = np.flatnonzero((sizes >= min_size) & (sizes <= take // 2))
    where = {int(node): index for index, node in enumerate(recorded)}

    def nearest_recorded(start: int) -> int:
        """Climb to the nearest recorded ancestor, or -1."""
        node = start
        while node != -1 and node not in where:
            node = int(tree_parent[node])
        return where.get(node, -1) if node != -1 else -1

    parent = np.array([nearest_recorded(int(tree_parent[node])) for node in recorded],
                      dtype=np.int64)
    leaf_cluster = np.full(n, -1, dtype=np.int64)
    for local, global_index in enumerate(subset):
        leaf_cluster[global_index] = nearest_recorded(local)

    clusters = node_bits[recorded].copy()
    cluster_sizes = sizes[recorded].astype(np.int64)

    chains: list[list[int]] = [[] for _ in range(n)]
    for global_index in subset:
        node = leaf_cluster[global_index]
        while node != -1:
            chains[global_index].append(int(node))
            node = int(parent[node])
    lengths = np.array([len(c) for c in chains], dtype=np.int64)
    chain_indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(lengths, out=chain_indptr[1:])
    chain_idx = np.fromiter((c for chain in chains for c in chain), dtype=np.int64,
                            count=int(chain_indptr[-1]))
    return Run(present=present, clusters=clusters, parent=parent,
               leaf_cluster=leaf_cluster, sizes=cluster_sizes,
               chain_indptr=chain_indptr, chain_idx=chain_idx)
