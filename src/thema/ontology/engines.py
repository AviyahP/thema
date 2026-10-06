"""Clustering engines a THEMA run can use to propose candidate groupings.

THEMA's framework is resampling recurrence: cluster an 80% draw, keep what recurs across draws,
order what survives by containment. **Ward is one engine inside that framework, not the framework
itself.** This module holds the alternatives declared in DECISIONS.md, 6 Oct 2026, so the question
"is Ward the right engine?" can be answered by swapping one function.

Every engine returns the same thing: candidate groupings as row-index lists over the SAMPLE, plus an
optional nested structure. :func:`thema.ontology.recurrent.run_from_candidates` turns those into a
``Run`` the rest of the pipeline cannot distinguish from a Ward one, and the pipeline's selection
rule -- the run's candidate with the greatest overlap with the grouping's shared members -- already
works for flat partitions, so nothing downstream changes.

What every engine is given and what it must not do:

- **The sample is not the engine's business.** It is read from the persisted tree for that run, so
  every arm sees the identical 200 draws of 8,616 pathways. An engine receives the sample's vectors
  and returns indices into them.
- **Size limits are applied by the caller**, identically for every arm: ``min_size`` 3 and the
  declared 29.0133% cap (3,125 at 10,770). An engine returns everything it found.
- **Determinism is the engine's business.** Every seed is fixed and derived from the run index, so
  a side re-cut a year later is the same side.
"""

from __future__ import annotations

import numpy as np

#: kNN graph parameter shared by the graph engines (B, C, D), declared 6 Oct.
KNN_K = 15

#: Arm B/C resolution ladder, AS AMENDED 6 Oct before any build: 10 values log-spaced over
#: [0.001, 100], and EVERY RUN GETS THE WHOLE LADDER. Candidates are the communities of all ten
#: splits, so a grouping is found in a run if any split of that run matches it.
#:
#: The amendment replaced one-resolution-per-run, and the probe that prompted it is worth keeping
#: next to the constant: under the original rule a run drawn at the bottom of the ladder proposed
#: NOTHING -- resolution 0.0014 gives one community above the 3,125 cap -- while still counting in
#: every grouping's eligibility denominator. About 40% of a log-spaced 0.001-100 ladder sits below
#: 0.1, so support would have been driven down by construction.
#:
#: The TOP was raised from 100 to 300 by amendment 3's setup check, run on the real 10,770 before
#: any arm was built: at 100 the median community is 12 members against the required <= 5, at 300 it
#: is 3, and at 1,000 it is a single pathway. 300 is the smallest widening that passes. Four of the
#: ten rungs still give one community of the whole draw, which the cap removes, so the arm
#: effectively runs on six -- which amendment 4 then fixed by raising the BOTTOM.
#:
#: The BOTTOM is 0.0669433, set by amendment 4 before any result existed: the largest resolution at
#: which the largest community is still >= 3,125, read off the span check's own grid. Below it every
#: rung gives one community of the whole draw, which the cap removes, so those rungs cost time and
#: propose nothing. Raising the bottom tightens the spacing between USEFUL rungs from 4.06x to
#: 2.545x, which matters because a group whose natural scale falls between two rungs is never
#: proposed at all -- a setup artefact that would hit the 51-500 band, and arm B2, hardest.
RESOLUTION_LO = 0.0669433
RESOLUTION_HI = 300.0
RESOLUTION_COUNT = 10

#: Arm B2: a community must reach this Jaccard against a community of an ADJACENT rung to count as
#: persistent. 0.75 is HiDeF's tau, used because it is HiDeF's and not because anything here was
#: tuned to it.
PERSISTENCE_TAU = 0.75

#: Arm G: bisecting spherical k-means. A cluster at or above this is split in two; below it is a
#: leaf. Candidates are every cluster of >= 3, so the floor sits one short of twice the minimum.
BISECT_MIN_SPLIT = 6
BISECT_MIN_SIZE = 3

#: Arm E (HDBSCAN) is **DROPPED** by the 6 Oct amendment, before any build: UMAP fitted on all
#: pathways leaks across resamples and would inflate the stability gate. The two functions below
#: are kept so the dropped arm stays legible rather than vanishing from the record, and nothing
#: declared calls them.
UMAP_COMPONENTS = 20
UMAP_NEIGHBOURS = 15
UMAP_MIN_DIST = 0.0
UMAP_METRIC = "cosine"
UMAP_SEED = 0

#: Arm E: HDBSCAN.
HDBSCAN_MIN_CLUSTER = 3
HDBSCAN_MIN_SAMPLES = 3


def resolution_ladder() -> np.ndarray:
    """The Leiden resolution ladder every run is given, as amended 6 Oct.

    Returns:
        A ``(RESOLUTION_COUNT,)`` array of resolutions, ascending. The same ladder for every run,
        so no run is handicapped by where it happened to land.
    """
    return np.logspace(np.log10(RESOLUTION_LO), np.log10(RESOLUTION_HI), RESOLUTION_COUNT)


def knn_graph(vectors: np.ndarray, k: int = KNN_K) -> tuple[np.ndarray, np.ndarray]:
    """Symmetric kNN graph on cosine similarity: the union of the directed edges.

    The union, not the intersection: an intersection graph on 8,616 points at k=15 fragments into
    many small components, and the engines below would then be clustering the components rather
    than the data.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        k: Neighbours per point, excluding itself.

    Returns:
        ``(edges, weights)`` with ``edges`` of shape ``(e, 2)`` holding ``i < j`` once each, and
        ``weights`` the cosine similarities, clipped at 0 so no negative weight reaches a
        modularity objective that is not defined for them.
    """
    m = vectors.shape[0]
    take = min(k + 1, m)
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -np.inf)
    neighbours = np.argpartition(-similarity, take - 1, axis=1)[:, : take - 1]
    rows = np.repeat(np.arange(m, dtype=np.int64), neighbours.shape[1])
    cols = neighbours.ravel().astype(np.int64)
    weight = similarity[rows, cols]
    # Fold each directed edge onto i < j and keep one copy: the union of the two directions.
    low = np.minimum(rows, cols)
    high = np.maximum(rows, cols)
    key = low * np.int64(m) + high
    order = np.argsort(key, kind="stable")
    key, low, high, weight = key[order], low[order], high[order], weight[order]
    first = np.ones(len(key), dtype=bool)
    first[1:] = key[1:] != key[:-1]
    edges = np.column_stack([low[first], high[first]])
    return edges, np.clip(weight[first], 0.0, None).astype(np.float64)


def _igraph_from(vectors: np.ndarray, k: int) -> object:
    """The weighted kNN graph as an igraph object.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        k: Neighbours per point.

    Returns:
        An ``igraph.Graph`` with a ``weight`` edge attribute.
    """
    import igraph

    edges, weight = knn_graph(vectors, k)
    graph = igraph.Graph(n=int(vectors.shape[0]), edges=[tuple(e) for e in edges.tolist()])
    graph.es["weight"] = weight.tolist()
    return graph


def leiden_communities(
    vectors: np.ndarray,
    resolutions: np.ndarray,
    seed: int,
    k: int = KNN_K,
) -> list[list[int]]:
    """Arm B: Leiden splits of the sample's kNN graph at EVERY resolution on the ladder.

    Amended 6 Oct, before any build. The original rule gave each run a single resolution and let
    the ladder live across runs; the probe showed that makes a run's contribution an accident of
    where it landed, and a run at the bottom of the ladder contributes nothing at all. Each run now
    gets the whole ladder and proposes the union of all ten splits, so a mid-size community is
    available to be matched in every run rather than in the ~15% that happened to be asked at the
    right granularity.

    The graph is built ONCE per run and reused across the ten splits -- it does not depend on the
    resolution, and on 8,616 points it is the expensive part.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        resolutions: The ladder, from :func:`resolution_ladder`.
        seed: igraph RNG seed, the run index.
        k: Neighbours per point.

    Returns:
        Communities as lists of row indices into ``vectors``, pooled over the ladder and
        deduplicated. Unfiltered by size.
    """
    return _dedup_rungs(leiden_rungs(vectors, resolutions, seed, k))


def leiden_rungs(
    vectors: np.ndarray,
    resolutions: np.ndarray,
    seed: int,
    k: int = KNN_K,
) -> list[list[tuple[int, ...]]]:
    """One Leiden partition per rung of the ladder, kept separate.

    Arms B and B2 are the same Leiden runs read two ways, so both go through this. The graph does
    not depend on the resolution and is built once per run, which on 8,616 points is the expensive
    part.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        resolutions: The ladder, ascending.
        seed: igraph RNG seed, the run index.
        k: Neighbours per point.

    Returns:
        Per rung, that partition's communities as sorted tuples.
    """
    import leidenalg

    graph = _igraph_from(vectors, k)
    rungs: list[list[tuple[int, ...]]] = []
    for resolution in np.asarray(resolutions, dtype=float).tolist():
        found = leidenalg.find_partition(
            graph,
            leidenalg.RBConfigurationVertexPartition,
            weights="weight",
            resolution_parameter=float(resolution),
            seed=int(seed),
        )
        rungs.append([tuple(sorted(community)) for community in found])
    return rungs


def _dedup_rungs(rungs: list[list[tuple[int, ...]]]) -> list[list[int]]:
    """Pool every rung's communities, keeping each distinct one once.

    Adjacent rungs agree on most communities. Keeping both copies would not change what matching
    finds -- a run finds a grouping if ANY of its candidates matches -- but it would misreport how
    much the arm proposes.

    Args:
        rungs: Per-rung community lists.

    Returns:
        The distinct communities, as member lists.
    """
    seen: set[tuple[int, ...]] = set()
    out: list[list[int]] = []
    for rung in rungs:
        for community in rung:
            if community not in seen:
                seen.add(community)
                out.append(list(community))
    return out


def leiden_persistent(
    vectors: np.ndarray,
    resolutions: np.ndarray,
    seed: int,
    k: int = KNN_K,
    tau: float = PERSISTENCE_TAU,
) -> list[list[int]]:
    """Arm B2: only the communities that persist across two ADJACENT rungs of the run's ladder.

    Added by amendment 2, before any build. This is HiDeF's persistence criterion applied inside a
    run, where arm B hands the whole unfiltered sweep to recurrence instead. **The comparison is
    the point**: if B2 and B score alike, persistence-within-a-run is redundant given
    recurrence-across-runs; if B2 is better, recurrence alone admits sweep artefacts.

    "Adjacent" means consecutive rungs only. A community matching something two rungs away but
    nothing next door has not persisted through the sweep, it has reappeared, and treating those the
    same would make the filter weaker than HiDeF's rather than the same strength.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        resolutions: The ladder, ascending.
        seed: igraph RNG seed, the run index.
        k: Neighbours per point.
        tau: Jaccard a community must reach against a neighbouring rung. HiDeF's 0.75.

    Returns:
        The surviving communities, deduplicated, as member lists.
    """
    rungs = leiden_rungs(vectors, resolutions, seed, k)
    kept: list[list[tuple[int, ...]]] = []
    for index, rung in enumerate(rungs):
        neighbours = [
            community
            for offset in (-1, 1)
            if 0 <= index + offset < len(rungs)
            for community in rungs[index + offset]
        ]
        as_sets = [set(community) for community in neighbours]
        survivors = []
        for community in rung:
            members = set(community)
            best = max(
                (len(members & other) / len(members | other) for other in as_sets if other),
                default=0.0,
            )
            if best >= tau:
                survivors.append(community)
        kept.append(survivors)
    return _dedup_rungs(kept)


def infomap_modules(vectors: np.ndarray, seed: int, k: int = KNN_K) -> list[list[int]]:
    """Arm H: every module at every level of a hierarchical Infomap run.

    Added by the 6 Oct amendment. Infomap's multilevel solution is a tree of modules, and taking
    every level is the analogue of "every merge" for the linkage arms -- the whole hierarchy is
    offered to recurrence rather than one flat cut of it.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        seed: Infomap RNG seed, the run index.
        k: Neighbours per point.

    Returns:
        Module member lists at every level, deduplicated. Unfiltered by size.
    """
    from infomap import Infomap

    edges, weight = knn_graph(vectors, k)
    model = Infomap(silent=True, num_trials=1, seed=int(seed))
    for (left, right), w in zip(edges.tolist(), weight.tolist(), strict=True):
        model.add_link(int(left), int(right), float(w))
    result = model.run()
    # A node's path is its position in the module tree, e.g. (2, 1, 5). Every PREFIX of that path
    # names an enclosing module, so collecting prefixes collects the hierarchy.
    #
    # `result.nodes()` rather than `model.nodes`: the latter is deprecated and removed in Infomap
    # 3.0, and a build that stops working on a dependency bump is a build that cannot be reproduced.
    groups: dict[tuple[int, ...], list[int]] = {}
    nodes = result.nodes() if hasattr(result, "nodes") else model.nodes
    for node in nodes:
        path = tuple(node.path)
        for depth in range(1, len(path)):
            groups.setdefault(path[:depth], []).append(int(node.node_id))
    seen: set[tuple[int, ...]] = set()
    out: list[list[int]] = []
    for key in sorted(groups):
        members = tuple(sorted(groups[key]))
        if members not in seen:
            seen.add(members)
            out.append(list(members))
    return out


def bisecting_spherical_kmeans(
    vectors: np.ndarray, seed: int
) -> tuple[list[list[int]], np.ndarray]:
    """Arm G: recursive 2-way spherical k-means, every cluster of >= 3 a candidate.

    Added by the 6 Oct amendment. Spherical k-means is k-means on the unit sphere -- centroids are
    renormalised, so the objective is cosine similarity rather than Euclidean distance, which is
    the geometry the embedding is scored on everywhere else in THEMA. Bisecting gives a binary
    hierarchy, so unlike Leiden this arm supplies a nested structure the containment DAG can use.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        seed: Fixes k-means++ initialisation; the run index.

    Returns:
        ``(members, parent)``: every cluster of at least :data:`BISECT_MIN_SIZE` members, and for
        each the index of the cluster that was split to produce it, or -1 for the root.
    """
    from sklearn.cluster import KMeans

    m = int(vectors.shape[0])
    members: list[list[int]] = [list(range(m))]
    parent: list[int] = [-1]
    queue = [0]
    while queue:
        at = queue.pop()
        rows = members[at]
        if len(rows) < BISECT_MIN_SPLIT:
            continue
        block = np.asarray(vectors[rows], dtype=np.float64)
        # Seeded per cluster as well as per run, so the recursion is reproducible rather than
        # dependent on the order the queue happened to reach this cluster.
        labels = KMeans(
            n_clusters=2, init="k-means++", n_init=3, random_state=int(seed) * 7919 + at
        ).fit_predict(_spherical(block))
        left = [rows[i] for i in np.flatnonzero(labels == 0).tolist()]
        right = [rows[i] for i in np.flatnonzero(labels == 1).tolist()]
        if not left or not right:
            continue
        for side in (left, right):
            members.append(side)
            parent.append(at)
            if len(side) >= BISECT_MIN_SPLIT:
                queue.append(len(members) - 1)
    keep = [i for i, group in enumerate(members) if len(group) >= BISECT_MIN_SIZE]
    renumber = {old: new for new, old in enumerate(keep)}
    nested = np.full(len(keep), -1, dtype=np.int64)
    for new, old in enumerate(keep):
        up = parent[old]
        while up >= 0 and up not in renumber:
            up = parent[up]
        nested[new] = renumber.get(up, -1) if up >= 0 else -1
    return [sorted(members[i]) for i in keep], nested


def _spherical(block: np.ndarray) -> np.ndarray:
    """Re-normalise rows to unit length, which is what makes k-means spherical.

    Args:
        block: An ``(m, dim)`` matrix.

    Returns:
        The same matrix with unit rows; a zero row is left as it is.
    """
    lengths = np.linalg.norm(block, axis=1, keepdims=True)
    return block / np.where(lengths == 0.0, 1.0, lengths)


def linkage_candidates(z: np.ndarray, m: int) -> tuple[list[list[int]], np.ndarray]:
    """Every merge of a linkage matrix, as member lists plus the nested parent structure.

    Shared by arm F (average linkage) and by any engine that produces a scipy-style linkage. The
    leaves are not candidates -- a single pathway is not a grouping -- so only the ``m - 1`` merges
    are returned.

    Args:
        z: An ``(m - 1, 4)`` scipy linkage matrix over ``m`` points.
        m: Number of points.

    Returns:
        ``(members, parent)``: ``members[i]`` is merge ``i``'s member list, and ``parent[i]`` is the
        merge that consumed merge ``i``, or -1 for a root.
    """
    members: list[list[int]] = [[leaf] for leaf in range(m)]
    parent = np.full(2 * m - 1, -1, dtype=np.int64)
    for i in range(m - 1):
        left, right = int(z[i, 0]), int(z[i, 1])
        members.append(members[left] + members[right])
        parent[left] = parent[right] = m + i
    # Re-index from "all nodes" to "merges only": merge i is node m + i.
    merge_parent = np.where(parent[m:] < 0, -1, parent[m:] - m).astype(np.int64)
    return members[m:], merge_parent


def average_linkage(vectors: np.ndarray) -> tuple[list[list[int]], np.ndarray]:
    """Arm F: average-linkage (UPGMA) merges on cosine distance.

    Cosine distance, not the Euclidean-on-unit-vectors that Ward requires. Average linkage has no
    Ward-style variance objective to violate, so the distance the embedding is actually scored on
    elsewhere in THEMA is the one used here.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.

    Returns:
        ``(members, parent)`` as in :func:`linkage_candidates`.
    """
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import pdist

    m = int(vectors.shape[0])
    condensed = pdist(np.asarray(vectors, dtype=np.float64), metric="cosine")
    return linkage_candidates(linkage(condensed, method="average"), m)


def paris_candidates(vectors: np.ndarray, k: int = KNN_K) -> tuple[list[list[int]], np.ndarray]:
    """Arm D: scikit-network's Paris on the sample's kNN graph.

    Args:
        vectors: ``(m, dim)`` unit vectors for one sample.
        k: Neighbours per point.

    Returns:
        ``(members, parent)`` as in :func:`linkage_candidates`.
    """
    from scipy import sparse
    from sknetwork.hierarchy import Paris

    m = int(vectors.shape[0])
    edges, weight = knn_graph(vectors, k)
    adjacency = sparse.csr_matrix(
        (np.concatenate([weight, weight]),
         (np.concatenate([edges[:, 0], edges[:, 1]]),
          np.concatenate([edges[:, 1], edges[:, 0]]))),
        shape=(m, m),
    )
    return linkage_candidates(np.asarray(Paris().fit_predict(adjacency)), m)


def umap_embedding(matrix: np.ndarray) -> np.ndarray:
    """Arm E: the UMAP embedding, fitted on a FULL matrix.

    Fitted once on all 10,770, and once per scramble seed on that seed's full matrix -- never per
    run. **This is the arm's declared limitation**: the embedding has seen every pathway, so an 80%
    draw perturbs this arm less than it perturbs the others, and its stability is not comparable to
    theirs on equal terms.

    Args:
        matrix: The ``(n, dim)`` full-universe unit-vector matrix.

    Returns:
        An ``(n, UMAP_COMPONENTS)`` embedding.
    """
    import umap

    reducer = umap.UMAP(
        n_components=UMAP_COMPONENTS,
        n_neighbors=UMAP_NEIGHBOURS,
        min_dist=UMAP_MIN_DIST,
        metric=UMAP_METRIC,
        random_state=UMAP_SEED,
    )
    return np.asarray(reducer.fit_transform(np.asarray(matrix, dtype=np.float32)))


def hdbscan_candidates(points: np.ndarray) -> list[list[int]]:
    """Arm E: every condensed-tree cluster of an HDBSCAN run, not just the flat selection.

    The flat ``labels_`` would give one partition and discard the hierarchy HDBSCAN built, which is
    the part THEMA's containment DAG can use. The condensed tree's clusters are taken instead, which
    is the analogue of "every merge" for the other hierarchical arms.

    Args:
        points: ``(m, components)`` UMAP coordinates for one sample.

    Returns:
        Candidate member lists (row indices into ``points``), unfiltered by size.
    """
    import hdbscan

    model = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER,
        min_samples=HDBSCAN_MIN_SAMPLES,
        gen_min_span_tree=False,
    ).fit(np.asarray(points, dtype=np.float64))
    tree = model.condensed_tree_.to_numpy()
    m = int(points.shape[0])
    # A condensed-tree row is (parent, child, lambda, child_size); a child below m is a point.
    children: dict[int, list[int]] = {}
    for parent, child, _lam, _size in tree:
        children.setdefault(int(parent), []).append(int(child))
    leaves: dict[int, list[int]] = {}

    def descend(node: int) -> list[int]:
        if node < m:
            return [node]
        if node in leaves:
            return leaves[node]
        out: list[int] = []
        for child in children.get(node, []):
            out.extend(descend(child))
        leaves[node] = out
        return out

    import sys

    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limit, 10 * m + 1000))
    try:
        return [descend(node) for node in sorted(children) if node >= m]
    finally:
        sys.setrecursionlimit(limit)
