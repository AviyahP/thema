"""KC: a fine level from one mutual-rank filtration, then recursive near-cliques. EXPLORATORY.

Two changes from naive K, both aimed at the thing naive K could not produce -- a middle.

**The fine level drops resampling entirely.** Naive K ran 100 edge-dropout runs and scored
support; that gate removed 87% of its mid-size candidates at a median support of 0.020, because
mid-size components of a sparse graph do not survive edge dropout. Here there is ONE filtration
over the full graph and no support at all: a group is kept on its **lifetime**,
``death_k / birth_k``, a property of the single nested sequence of graphs rather than of a
resampling distribution.

**The middle is then built rather than hoped for.** Instead of asking the fine engine to propose
51-500 member groups as well, KC takes the fine themes as units and merges them recursively by
centroid proximity, requiring a unit to be close to most of a group rather than to one member. That
is a near-clique condition, and it stops a chain of pairwise-close units fusing into one blob.

New module: `recurrent.py`, `cut_trees.py`, `engines.py` and `mutualrank.py` are untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

#: The ladder, and the notional rung after the last one, for a group alive at the top.
LADDER: tuple[int, ...] = (3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 32, 40, 50, 64, 80, 100)
NEXT_AFTER_LAST = 128

#: Matching threshold, and the fine level's size limits.
THETA = 0.70
MIN_SIZE = 3
MAX_SIZE = 3125

#: Level-step defaults. PRIMARY settings, declared before running.
Q_PERCENTILE = 99.0
JOIN_SHARE = 0.80
MAX_LEVELS = 6


@dataclass(frozen=True, slots=True)
class Fine:
    """The fine level: every candidate with its birth, death and lifetime.

    Attributes:
        members: Per candidate, its sorted pathway indices.
        birth: The first rung at which a component matched it.
        death: The first rung after that at which none did; ``NEXT_AFTER_LAST`` if it survived.
        lifetime: ``death / birth``.
    """

    members: list[np.ndarray]
    birth: np.ndarray
    death: np.ndarray
    lifetime: np.ndarray


def filtration(edges: np.ndarray, rank: np.ndarray, n: int,
               ladder: tuple[int, ...] = LADDER) -> list[list[np.ndarray]]:
    """Connected components at every rung of the FULL graph. No sampling.

    Args:
        edges: ``(e, 2)`` endpoint pairs.
        rank: Mutual rank per edge.
        n: Node count.
        ladder: The rungs.

    Returns:
        One list of components per rung, each within the size limits.
    """
    from thema.ontology.mutualrank import clusters_of, components

    out = []
    for k in ladder:
        within = rank <= k
        out.append(clusters_of(components(n, edges[within]), MIN_SIZE, MAX_SIZE))
    return out


def fine_level(per_rung: list[list[np.ndarray]], n: int,
               ladder: tuple[int, ...] = LADDER) -> Fine:
    """Birth, death and lifetime for every component seen anywhere in the filtration.

    "Alive" is contiguous from birth by construction of the measure: the group is matched at every
    rung from its first to its last, and the first rung where nothing matches it is its death. A
    group matched again after a gap is credited only to its first unbroken stretch, the same rule
    naive K used, which keeps the two comparable.

    Args:
        per_rung: Components per rung.
        n: Node count.
        ladder: The rungs.

    Returns:
        The fine level.
    """
    index: dict[bytes, int] = {}
    members: list[np.ndarray] = []
    for rung in per_rung:
        for component in rung:
            key = component.astype(np.int32).tobytes()
            if key not in index:
                index[key] = len(members)
                members.append(component)
    total = len(members)
    rungs = len(ladder)
    if not total:
        return Fine([], np.zeros(0), np.zeros(0), np.zeros(0))

    hit = np.zeros((total, rungs), dtype=bool)
    sizes = np.array([len(m) for m in members], dtype=np.int64)
    rows = np.repeat(np.arange(total, dtype=np.int64), sizes)
    cols = np.concatenate(members).astype(np.int64)
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int32), (rows, cols)), shape=(total, n)
    )
    for rung_index, rung in enumerate(per_rung):
        if not rung:
            continue
        block_rows = np.repeat(np.arange(len(rung), dtype=np.int64),
                               [len(c) for c in rung])
        block = sparse.csr_matrix(
            (np.ones(len(block_rows), dtype=np.int32),
             (block_rows, np.concatenate(rung).astype(np.int64))),
            shape=(len(rung), n),
        )
        product = (block @ matrix.T).tocoo()
        if not product.nnz:
            continue
        own = np.array([len(c) for c in rung], dtype=np.int64)[product.row]
        overlap = product.data.astype(np.int64)
        union = own + sizes[product.col] - overlap
        good = (union > 0) & (overlap / np.maximum(union, 1) >= THETA)
        hit[product.col[good], rung_index] = True

    steps = np.array(ladder, dtype=np.float64)
    after = np.array(list(ladder[1:]) + [NEXT_AFTER_LAST], dtype=np.float64)
    birth = np.full(total, np.nan)
    death = np.full(total, np.nan)
    for position in range(total):
        mask = hit[position]
        where = np.flatnonzero(mask)
        if not len(where):
            continue
        start = int(where[0])
        end = start
        while end + 1 < rungs and mask[end + 1]:
            end += 1
        birth[position] = steps[start]
        death[position] = after[end]
    return Fine(members, birth, death, death / birth)


def minimal(kept: list[np.ndarray], n: int) -> list[int]:
    """Which kept themes contain no other kept theme.

    These are the units the level step starts from: a theme strictly containing another kept theme
    is already represented by it, and using both would let the same pathways drive two units.

    Args:
        kept: Kept theme member arrays.
        n: Node count.

    Returns:
        Indices of the minimal themes.
    """
    if not kept:
        return []
    sizes = np.array([len(m) for m in kept], dtype=np.int64)
    rows = np.repeat(np.arange(len(kept), dtype=np.int64), sizes)
    matrix = sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int32),
         (rows, np.concatenate(kept).astype(np.int64))), shape=(len(kept), n)
    )
    overlap = (matrix @ matrix.T).tocoo()
    contains_other = np.zeros(len(kept), dtype=bool)
    for i, j, v in zip(overlap.row, overlap.col, overlap.data, strict=True):
        if i != j and v == sizes[j] and sizes[j] < sizes[i]:
            contains_other[i] = True
    return np.flatnonzero(~contains_other).tolist()


def centroids(units: list[np.ndarray], vectors: np.ndarray) -> np.ndarray:
    """Unit centroids: the mean of the members' centred vectors, renormalised.

    Args:
        units: Per unit, its pathway indices.
        vectors: The ``(n, dim)`` centred unit-vector matrix.

    Returns:
        A ``(u, dim)`` unit-vector matrix.
    """
    out = np.vstack([vectors[u].mean(axis=0) for u in units])
    lengths = np.linalg.norm(out, axis=1, keepdims=True)
    return (out / np.where(lengths == 0.0, 1.0, lengths)).astype(np.float32)


def close_graph(points: np.ndarray, q: float = Q_PERCENTILE) -> tuple[sparse.csr_matrix, float]:
    """The "close" graph: pairs at or above the q-th percentile of ALL pairwise cosines.

    The threshold is recomputed at every level rather than fixed, because the units change: level
    one compares mostly single pathways and level three compares groups of groups, and a cosine that
    is unremarkable among the former is extreme among the latter.

    Args:
        points: ``(u, dim)`` unit vectors.
        q: Percentile.

    Returns:
        The symmetric adjacency, and the threshold used.
    """
    u = int(points.shape[0])
    if u < 2:
        return sparse.csr_matrix((u, u), dtype=np.int8), 1.0
    block = 2048
    # Two passes: one to find the threshold, one to keep only what clears it, so the full
    # pairwise matrix never has to be held.
    sample: list[np.ndarray] = []
    for start in range(0, u, block):
        stop = min(start + block, u)
        sim = points[start:stop] @ points.T
        for row in range(stop - start):
            sample.append(sim[row, start + row + 1:])
    flat = np.concatenate(sample) if sample else np.zeros(0, dtype=np.float32)
    threshold = float(np.percentile(flat, q)) if len(flat) else 1.0
    del sample, flat

    rows, cols = [], []
    for start in range(0, u, block):
        stop = min(start + block, u)
        sim = points[start:stop] @ points.T
        sim[np.arange(stop - start), np.arange(start, stop)] = -np.inf
        r, c = np.nonzero(sim >= threshold)
        rows.append(r + start)
        cols.append(c)
    r = np.concatenate(rows) if rows else np.zeros(0, dtype=np.int64)
    c = np.concatenate(cols) if cols else np.zeros(0, dtype=np.int64)
    graph = sparse.csr_matrix(
        (np.ones(len(r), dtype=np.int8), (r, c)), shape=(u, u)
    )
    graph = graph.maximum(graph.T)
    graph.setdiag(0)
    graph.eliminate_zeros()
    return graph.tocsr(), threshold


def near_cliques(graph: sparse.csr_matrix, share: float = JOIN_SHARE) -> list[list[int]]:
    """Group units greedily, densest first, each joiner close to at least ``share`` of the group.

    The share condition is what makes these near-cliques rather than components. Without it a chain
    of pairwise-close units fuses into one group, which is exactly how a graph method loses the
    middle: everything becomes one blob a rung too early.

    Overlaps are added afterwards, so a unit close to most of two groups belongs to both, which is
    what gives the DAG genuine multi-parent structure rather than a partition.

    Args:
        graph: Symmetric close adjacency.
        share: Fraction of a group a joiner must be close to.

    Returns:
        One member list per group of two or more units.
    """
    u = graph.shape[0]
    degree = np.asarray(graph.sum(axis=1)).ravel()
    order = np.argsort(-degree, kind="stable")
    neighbours = [graph.indices[graph.indptr[i]:graph.indptr[i + 1]] for i in range(u)]
    taken = np.zeros(u, dtype=bool)
    groups: list[list[int]] = []

    for seed in order.tolist():
        if taken[seed] or not len(neighbours[seed]):
            continue
        group = [seed]
        in_group = {seed}
        for candidate in sorted(neighbours[seed].tolist(), key=lambda x: -degree[x]):
            if taken[candidate] or candidate in in_group:
                continue
            close_to = sum(1 for member in group
                           if candidate in set(neighbours[member].tolist()))
            if close_to / len(group) >= share:
                group.append(candidate)
                in_group.add(candidate)
        if len(group) >= 2:
            for member in group:
                taken[member] = True
            groups.append(sorted(group))

    # Overlaps: a unit close to at least `share` of a group it is not in joins it too.
    for position, group in enumerate(groups):
        as_set = set(group)
        counts = np.zeros(u, dtype=np.int64)
        for member in group:
            counts[neighbours[member]] += 1
        extra = np.flatnonzero(counts / len(group) >= share)
        groups[position] = sorted(as_set | {int(e) for e in extra.tolist() if e not in as_set})
    return groups
