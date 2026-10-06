"""Arm K: clusters from a mutual-rank graph ladder, scored by support and lifetime.

The idea Test R pointed at. Test R measured that a per-group **lifetime** -- how long a group
survives as the clustering coarsens -- separates real from scrambled at AUROC 0.929 to 0.991, better
than support alone at every size, while the leave-one-out gap score was anti-predictive. Arm K
generalises that from Ward merge heights to a ladder of mutual-rank graphs, where "coarsening" is
admitting weaker edges rather than climbing a dendrogram. **No tree is built.**

Mutual rank rather than raw cosine, because a fixed similarity threshold is the thing that makes a
kNN graph fragment unevenly: dense regions keep everything and sparse ones lose all their edges.
``r(i, j) = max(rank of j among i's neighbours, rank of i among j's)`` is symmetric by construction
and scale-free across regions, so one ladder of integer cutoffs means the same thing everywhere.

This is a NEW module: `recurrent.py`, `cut_trees.py` and `engines.py` are untouched, so no cached
side's provenance fingerprint moves.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

#: Neighbours computed once per universe. The ladder never asks for more than this.
K_MAX = 100

#: The declared ladder, and the notional rung after the last one, which a lifetime needs when a
#: group survives to the top.
LADDER: tuple[int, ...] = (3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 32, 40, 50, 64, 80, 100)
NEXT_AFTER_LAST = 128

#: Cluster size limits: the declared minimum and the 29.0133% cap at 10,770.
MIN_SIZE = 3
MAX_SIZE = 3125

#: Edge keep probability per run, and the matching threshold.
KEEP = 0.8
THETA = 0.70


def neighbours(vectors: np.ndarray, k_max: int = K_MAX) -> np.ndarray:
    """Exact cosine nearest neighbours, closest first, excluding self.

    Exact rather than approximate: at 10,770 points the full similarity matrix is 116 million
    entries and costs seconds, so there is no reason to accept an approximation whose errors would
    sit at the rank boundaries the ladder is built on.

    Args:
        vectors: ``(n, dim)`` unit vectors.
        k_max: Neighbours per point.

    Returns:
        An ``(n, k_max)`` array of neighbour indices, rank 0 being the closest.
    """
    n = int(vectors.shape[0])
    take = min(k_max, n - 1)
    out = np.empty((n, take), dtype=np.int32)
    block = 2048
    for start in range(0, n, block):
        stop = min(start + block, n)
        sim = vectors[start:stop] @ vectors.T
        sim[np.arange(stop - start), np.arange(start, stop)] = -np.inf
        part = np.argpartition(-sim, take - 1, axis=1)[:, :take]
        order = np.argsort(-np.take_along_axis(sim, part, axis=1), axis=1)
        out[start:stop] = np.take_along_axis(part, order, axis=1)
    return out


def mutual_rank_edges(near: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Every mutual edge and its mutual rank.

    An edge exists only when each point is within the other's ``k_max`` neighbours; its rank is the
    worse of the two positions, so the ladder admits an edge at ``k`` only once BOTH endpoints agree
    it is that close.

    Args:
        near: ``(n, k_max)`` neighbour indices, closest first.

    Returns:
        ``(edges, rank)`` with ``edges`` of shape ``(e, 2)`` holding ``i < j`` once each, and
        ``rank`` the 1-based mutual rank.
    """
    n, k = near.shape
    rows = np.repeat(np.arange(n, dtype=np.int64), k)
    cols = near.ravel().astype(np.int64)
    rank = np.tile(np.arange(1, k + 1, dtype=np.int64), n)
    # A sparse matrix of directed ranks makes the reciprocal lookup one transpose.
    directed = sparse.csr_matrix((rank, (rows, cols)), shape=(n, n))
    back = directed.T.tocsr()
    both = directed.multiply(back > 0).tocoo()
    keep = both.row < both.col
    i, j = both.row[keep], both.col[keep]
    forward = np.asarray(directed[i, j]).ravel()
    reverse = np.asarray(back[i, j]).ravel()
    return np.column_stack([i, j]), np.maximum(forward, reverse)


def shared_neighbour_counts(near: np.ndarray, edges: np.ndarray, k: int) -> np.ndarray:
    """How many of their ``k`` nearest neighbours each edge's endpoints share.

    Used only by K-snn, which is not part of the naive run; kept here so the two arms share one
    definition when the full run resumes.

    Args:
        near: ``(n, k_max)`` neighbour indices.
        edges: ``(e, 2)`` endpoint pairs.
        k: Neighbourhood size.

    Returns:
        Shared count per edge.
    """
    n = near.shape[0]
    rows = np.repeat(np.arange(n, dtype=np.int64), k)
    cols = near[:, :k].ravel().astype(np.int64)
    membership = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int32), (rows, cols)), shape=(n, n)
    )
    left, right = membership[edges[:, 0]], membership[edges[:, 1]]
    return np.asarray(left.multiply(right).sum(axis=1)).ravel()


def components(n: int, edges: np.ndarray) -> np.ndarray:
    """Connected-component label per node.

    Args:
        n: Node count.
        edges: ``(e, 2)`` endpoint pairs.

    Returns:
        A label per node.
    """
    if not len(edges):
        return np.arange(n, dtype=np.int32)
    graph = sparse.coo_matrix(
        (np.ones(len(edges), dtype=np.int8), (edges[:, 0], edges[:, 1])), shape=(n, n)
    )
    _count, labels = sparse.csgraph.connected_components(graph, directed=False)
    return labels


def clusters_of(labels: np.ndarray, low: int = MIN_SIZE, high: int = MAX_SIZE) -> list[np.ndarray]:
    """Components within the size limits, as sorted member arrays.

    Args:
        labels: Component label per node.
        low: Smallest cluster kept.
        high: Largest cluster kept.

    Returns:
        One sorted index array per kept component.
    """
    order = np.argsort(labels, kind="stable")
    sorted_labels = labels[order]
    starts = np.flatnonzero(np.r_[True, sorted_labels[1:] != sorted_labels[:-1]])
    bounds = np.r_[starts, len(labels)]
    out = []
    for begin, end in zip(bounds[:-1], bounds[1:], strict=True):
        if low <= end - begin <= high:
            out.append(np.sort(order[begin:end]))
    return out


def ladder_runs(
    edges: np.ndarray,
    rank: np.ndarray,
    n: int,
    runs: int,
    ladder: tuple[int, ...] = LADDER,
    keep: float = KEEP,
) -> list[list[list[np.ndarray]]]:
    """Every run's clusters at every rung.

    Each run drops a fixed fraction of the mutual edges; every pathway stays present, so unlike the
    Ward arms there is no subsample and nothing is ever unseen. The perturbation is the graph, not
    the population.

    Args:
        edges: ``(e, 2)`` endpoint pairs.
        rank: Mutual rank per edge.
        n: Node count.
        runs: How many runs.
        ladder: The rungs.
        keep: Edge keep probability.

    Returns:
        ``out[run][rung]`` is the list of clusters at that rung.
    """
    out: list[list[list[np.ndarray]]] = []
    for seed in range(1, runs + 1):
        rng = np.random.default_rng(seed)
        alive = rng.random(len(edges)) < keep
        kept_edges, kept_rank = edges[alive], rank[alive]
        per_rung: list[list[np.ndarray]] = []
        for k in ladder:
            within = kept_rank <= k
            per_rung.append(clusters_of(components(n, kept_edges[within])))
        out.append(per_rung)
    return out


def rungs_of(ladder: tuple[int, ...]) -> int:
    """How many rungs the ladder has.

    Args:
        ladder: The rungs.

    Returns:
        The count.
    """
    return len(ladder)


def score(
    per_run: list[list[list[np.ndarray]]], n: int, ladder: tuple[int, ...] = LADDER
) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Deduplicate the candidates, then score support and lifetime.

    Support is the share of runs in which SOME cluster at SOME rung matches the candidate at
    Jaccard >= theta. Containment in a larger cluster does not count, which the Jaccard test
    enforces on its own: a group inside a cluster twice its size scores 0.5.

    Lifetime is the median, over the runs that found it, of the rung after the last matching rung
    divided by the first matching rung, taken over the LONGEST consecutive stretch of matching
    rungs. A group that appears, vanishes and reappears is credited only with its longest unbroken
    stretch.

    Args:
        per_run: Output of :func:`ladder_runs`.
        n: Node count.
        ladder: The rungs.

    Returns:
        ``(members, support, lifetime)``, one entry per distinct candidate.
    """
    index: dict[bytes, int] = {}
    members: list[np.ndarray] = []
    for run in per_run:
        for rung in run:
            for cluster in rung:
                key = cluster.astype(np.int32).tobytes()
                if key not in index:
                    index[key] = len(members)
                    members.append(cluster)
    total = len(members)
    rungs = rungs_of(ladder)
    hit = np.zeros((total, len(per_run), rungs), dtype=bool)
    if not total:
        return members, np.zeros(0), np.zeros(0)

    # The join as two sparse products rather than a Python scan over members. Overlap between every
    # candidate and every cluster is one matrix product restricted to pairs that share a pathway,
    # and the Jaccard test is then arithmetic on its data array. The first version looped over
    # (cluster, member, holder) and at 100 runs that is some 600 million dict operations -- the same
    # trap Test R fell into and the same fix.
    candidate_rows = np.repeat(np.arange(total, dtype=np.int64),
                               [len(m) for m in members])
    candidate_cols = np.concatenate([m for m in members]).astype(np.int64)
    sizes = np.array([len(m) for m in members], dtype=np.int64)
    matrix = sparse.csr_matrix(
        (np.ones(len(candidate_rows), dtype=np.int32), (candidate_rows, candidate_cols)),
        shape=(total, n),
    )

    # Every (run, rung) cluster, flattened, with its slot so a match can be written straight back.
    flat: list[np.ndarray] = []
    slots: list[int] = []
    for run_index, run in enumerate(per_run):
        for rung_index, rung in enumerate(run):
            for cluster in rung:
                flat.append(cluster)
                slots.append(run_index * rungs + rung_index)
    chunk = 4096
    for begin in range(0, len(flat), chunk):
        piece = flat[begin : begin + chunk]
        rows = np.repeat(np.arange(len(piece), dtype=np.int64), [len(c) for c in piece])
        cols = np.concatenate(piece).astype(np.int64)
        block = sparse.csr_matrix(
            (np.ones(len(rows), dtype=np.int32), (rows, cols)), shape=(len(piece), n)
        )
        product = (block @ matrix.T).tocoo()
        if not product.nnz:
            continue
        own = np.array([len(c) for c in piece], dtype=np.int64)[product.row]
        other = sizes[product.col]
        overlap = product.data.astype(np.int64)
        union = own + other - overlap
        good = (union > 0) & (overlap / np.maximum(union, 1) >= THETA)
        if not good.any():
            continue
        where = np.array(slots[begin : begin + chunk], dtype=np.int64)[product.row[good]]
        hit[product.col[good], where // rungs, where % rungs] = True

    after = np.array(list(ladder[1:]) + [NEXT_AFTER_LAST], dtype=np.float64)
    first = np.array(ladder, dtype=np.float64)
    support = hit.any(axis=2).mean(axis=1)
    lifetime = np.full(total, np.nan)
    for position in range(total):
        ratios = []
        for run_index in range(len(per_run)):
            mask = hit[position, run_index]
            if not mask.any():
                continue
            best_len = best_start = best_end = 0
            length = 0
            for rung_index, present in enumerate(mask.tolist()):
                if present:
                    length += 1
                    if length > best_len:
                        best_len, best_end = length, rung_index
                        best_start = rung_index - length + 1
                else:
                    length = 0
            ratios.append(after[best_end] / first[best_start])
        if ratios:
            lifetime[position] = float(np.median(ratios))
    return members, support, lifetime
