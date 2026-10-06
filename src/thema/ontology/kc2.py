"""KC2: KC with an ABSOLUTE closeness bar instead of a percentile. EXPLORATORY.

KC failed its null check for one reason, and it was structural rather than a bad parameter.
"Close" was defined as the q-th percentile of the pairwise centroid cosines at each level, so it
admitted 1% of pairs **whatever the data was**: on the real matrix the 99th percentile is 0.307, on
a scramble it is 0.086. A cosine of 0.086 between two random centroids is not closeness in any
meaningful sense, but it is that matrix's 99th percentile, and 1% of 58 million pairs is enough for
greedy near-cliques to find thousands of groups. A relative threshold is scale-free by construction,
and scale-free is exactly what cannot reject a null.

KC2 changes one thing: ``close`` is ``cosine >= c`` for a single absolute ``c``, identical at every
level. Everything else -- the fine level, the units, the near-clique join share, the overlap step --
is KC's, imported rather than copied so the two cannot drift.

New module: nothing existing is modified.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

#: The sweep the brief declares, and the ratio it is solved to.
C_GRID: tuple[float, ...] = (0.100, 0.125, 0.150, 0.175, 0.200, 0.225, 0.250,
                             0.275, 0.300, 0.325, 0.350, 0.375, 0.400)
TARGET_RATIO = 0.01


def close_graph_absolute(points: np.ndarray, c: float) -> sparse.csr_matrix:
    """The close graph at an absolute cosine bar.

    One pass rather than the two a percentile needed, because the threshold is known in advance --
    which is the whole point: a bar that does not consult the data cannot be moved by the data.

    Args:
        points: ``(u, dim)`` unit vectors.
        c: Absolute cosine threshold.

    Returns:
        The symmetric adjacency with no self-loops.
    """
    u = int(points.shape[0])
    if u < 2:
        return sparse.csr_matrix((u, u), dtype=np.int8)
    rows, cols = [], []
    block = 2048
    for start in range(0, u, block):
        stop = min(start + block, u)
        sim = points[start:stop] @ points.T
        sim[np.arange(stop - start), np.arange(start, stop)] = -np.inf
        r, col = np.nonzero(sim >= c)
        rows.append(r + start)
        cols.append(col)
    r = np.concatenate(rows) if rows else np.zeros(0, dtype=np.int64)
    col = np.concatenate(cols) if cols else np.zeros(0, dtype=np.int64)
    graph = sparse.csr_matrix((np.ones(len(r), dtype=np.int8), (r, col)), shape=(u, u))
    graph = graph.maximum(graph.T)
    graph.setdiag(0)
    graph.eliminate_zeros()
    return graph.tocsr()


def levels_at(units: list[np.ndarray], vectors: np.ndarray, c: float,
              share: float, max_levels: int) -> list[list[np.ndarray]]:
    """Run the recursive near-clique step at an absolute bar.

    Args:
        units: Starting units, each a sorted pathway-index array.
        vectors: The ``(n, dim)`` centred unit-vector matrix.
        c: Absolute cosine threshold.
        share: Join share.
        max_levels: Level cap.

    Returns:
        One list of merged groups per level that produced any.
    """
    from thema.ontology.kc import MIN_SIZE, centroids, near_cliques

    out: list[list[np.ndarray]] = []
    current = units
    for _level in range(max_levels):
        if len(current) < 2:
            break
        graph = close_graph_absolute(centroids(current, vectors), c)
        if not graph.nnz:
            break
        groups = near_cliques(graph, share)
        if not groups:
            break
        merged = [np.unique(np.concatenate([current[u] for u in g])) for g in groups]
        merged = [m for m in merged if len(m) >= MIN_SIZE]
        if not merged:
            break
        out.append(merged)
        joined = {u for g in groups for u in g}
        current = merged + [current[i] for i in range(len(current)) if i not in joined]
    return out
