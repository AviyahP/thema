#!/usr/bin/env python3
"""Step 1 of the one-linkage experiment: one tree per engine on all 5,559 leaves, no resampling.

Three merge rules on identical input, to see whether the missing middle is Ward's cost function or
missing signal:

- **W** Ward on Euclidean distance over unit vectors, the reference THEMA uses;
- **C** normalised-centroid cosine, the proposed single rule for every level;
- **A** average linkage on cosine distance (UPGMA), as a control for "any non-Ward rule would do".

Everything reported here is a property of ONE tree with no resampling, so none of it is a recurrence
claim and none of it is a build. Its only job is to decide whether Step 2 is worth running, against
the criterion declared in the brief.

Gene coherence uses **mean pairwise gene Jaccard** against **size-matched** random sets. The
size-matching is not optional: mean pairwise Jaccard falls with set size for purely combinatorial
reasons, so an unmatched null would make every large node look incoherent and every small one look
good.

Usage::

    uv run scripts/one_linkage_step1.py
    uv run scripts/one_linkage_step1.py --engines C --cuts 30
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection, partition_universe
from thema.ontology.evalsets import PRIMARY_RELATIONS, SECONDARY_RELATIONS, go_edges
from thema.ontology.leaves import internal, targets
from thema.ontology.linkage import centroid_cosine
from thema.ontology.universe import load_embedded

#: Node-size bands.
BANDS: tuple[tuple[int, int], ...] = (
    (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 300), (301, 1000), (1001, 10**9))
#: Curated-target bands for recall.
TARGET_BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))
#: A child holding more than this share of its parent is a chain link, not a branch.
CHAIN_SHARE = 0.70
#: Cluster counts to cut at, and how many names to show per cluster.
CUTS = (20, 30, 50)
NEAREST = 7
#: Gene coherence sampling.
COHERENCE_SAMPLE = 150
NULL_DRAWS = 10
MAX_PAIRS = 4000
MATCH = 0.5
SEED = 0
#: Largest node a leaf is credited to, for the "largest node of N or fewer" diagnostic.
PLACEMENT_CAP = 1000
#: Step 1's declared criterion.
MID_BAND = (51, 1000)
DOMINANCE_CUT = 30
DOMINANCE_SHARE = 0.25


def band_of(size: int, bands: tuple[tuple[int, int], ...] = BANDS) -> str:
    """Band label for a size.

    Args:
        size: Member count.
        bands: Band bounds.

    Returns:
        The label, or ``"other"``.
    """
    for low, high in bands:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10**9 else f"{low}+"
    return "other"


_TREES: dict[str, np.ndarray] = {}


def scipy_tree(engine: str, vectors: np.ndarray) -> np.ndarray:
    """The scipy linkage matrix for W or A, built once and reused.

    Args:
        engine: ``"W"`` or ``"A"``.
        vectors: ``(n, dim)`` unit rows.

    Returns:
        The ``(n-1, 4)`` linkage matrix.
    """
    if engine in _TREES:
        return _TREES[engine]
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import squareform

    if engine == "W":
        from thema.cluster import distances

        _TREES[engine] = linkage(distances(vectors), method="ward")
    else:
        grid = 1.0 - (vectors @ vectors.T)
        np.fill_diagonal(grid, 0.0)
        _TREES[engine] = linkage(squareform(np.clip(grid, 0.0, None), checks=False),
                                 method="average")
    return _TREES[engine]


def ward_nodes(vectors: np.ndarray) -> tuple[list[np.ndarray], float, int]:
    """Ward tree over unit vectors, as node member arrays.

    Args:
        vectors: ``(n, dim)`` unit rows.

    Returns:
        ``(member arrays for all 2n-1 nodes, seconds, inversions)``.
    """
    clock = time.perf_counter()
    tree = scipy_tree("W", vectors)
    sets: list[np.ndarray] = [np.array([i], dtype=np.int64) for i in range(len(vectors))]
    for left, right, _height, _size in tree:
        sets.append(np.concatenate([sets[int(left)], sets[int(right)]]))
    heights = tree[:, 2]
    inversions = int(sum(1 for i in range(1, len(heights))
                         if heights[i] < heights[i - 1] - 1e-9))
    return sets, time.perf_counter() - clock, inversions


def average_nodes(vectors: np.ndarray) -> tuple[list[np.ndarray], float, int]:
    """UPGMA on cosine distance, as node member arrays.

    Args:
        vectors: ``(n, dim)`` unit rows.

    Returns:
        ``(member arrays, seconds, inversions)``.
    """
    clock = time.perf_counter()
    tree = scipy_tree("A", vectors)
    sets: list[np.ndarray] = [np.array([i], dtype=np.int64) for i in range(len(vectors))]
    for left, right, _height, _size in tree:
        sets.append(np.concatenate([sets[int(left)], sets[int(right)]]))
    heights = tree[:, 2]
    inversions = int(sum(1 for i in range(1, len(heights))
                         if heights[i] < heights[i - 1] - 1e-9))
    return sets, time.perf_counter() - clock, inversions


def node_children(merges: np.ndarray, n: int) -> dict[int, list[int]]:
    """Direct children per internal node.

    Args:
        merges: ``(left, right)`` per merge.
        n: Number of leaves.

    Returns:
        Node id to its two children.
    """
    return {n + t: [int(left), int(right)] for t, (left, right) in enumerate(merges)}


def collapsed_children(children: dict[int, list[int]], sizes: dict[int, int],
                       root: int) -> dict[int, list[int]]:
    """Child lists with chain links collapsed into their parent.

    Args:
        children: Node to its direct children.
        sizes: Node to member count.
        root: The root node id.

    Returns:
        Node to its children after collapsing.
    """
    out: dict[int, list[int]] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        if node not in children:
            continue
        collected: list[int] = []
        frontier = list(children[node])
        while frontier:
            child = frontier.pop()
            if (child in children
                    and sizes[child] > CHAIN_SHARE * sizes[node]):
                frontier.extend(children[child])
            else:
                collected.append(child)
        out[node] = collected
        stack.extend(c for c in collected if c in children)
    return out


def mean_pair_jaccard(keys: list[str], genes: dict[str, frozenset[str]],
                      rng: np.random.Generator) -> float | None:
    """Mean pairwise gene Jaccard over a node's members.

    Args:
        keys: Member pathway keys.
        genes: Pathway key to gene set.
        rng: For sampling pairs in a large node.

    Returns:
        The mean, or None if fewer than two members carry genes.
    """
    have = [k for k in keys if genes.get(k)]
    if len(have) < 2:
        return None
    total = len(have) * (len(have) - 1) // 2
    if total <= MAX_PAIRS:
        pairs = list(itertools.combinations(have, 2))
    else:
        left = rng.integers(0, len(have), MAX_PAIRS)
        right = rng.integers(0, len(have), MAX_PAIRS)
        pairs = [(have[i], have[j]) for i, j in zip(left, right, strict=True) if i != j]
    if not pairs:
        return None
    values = []
    for a, b in pairs:
        ga, gb = genes[a], genes[b]
        union = len(ga | gb)
        values.append(len(ga & gb) / union if union else 0.0)
    return float(np.mean(values))


def coherence(sets: list[np.ndarray], n: int, keys: list[str],
              genes: dict[str, frozenset[str]]) -> dict[str, dict]:
    """Mean pairwise gene Jaccard per band against a size-matched null.

    Args:
        sets: Member arrays for all nodes.
        n: Number of leaves.
        keys: Pathway key per leaf index.
        genes: Pathway key to gene set.

    Returns:
        Per band, observed, null and ratio.
    """
    rng = np.random.default_rng(SEED)
    by_band: dict[str, list[int]] = defaultdict(list)
    for node in range(n, len(sets)):
        by_band[band_of(len(sets[node]))].append(node)
    out: dict[str, dict] = {}
    for low, high in BANDS:
        band = f"{low}-{high}" if high < 10**9 else f"{low}+"
        nodes = by_band.get(band, [])
        if not nodes:
            continue
        pick = ([nodes[i] for i in rng.choice(len(nodes), COHERENCE_SAMPLE, replace=False)]
                if len(nodes) > COHERENCE_SAMPLE else nodes)
        real, null = [], []
        for node in pick:
            member_keys = [keys[i] for i in sets[node]]
            got = mean_pair_jaccard(member_keys, genes, rng)
            if got is None:
                continue
            real.append(got)
            draws = []
            for _ in range(NULL_DRAWS):
                sample = [keys[i] for i in
                          rng.choice(len(keys), len(member_keys), replace=False)]
                value = mean_pair_jaccard(sample, genes, rng)
                if value is not None:
                    draws.append(value)
            if draws:
                null.append(float(np.mean(draws)))
        if not real or not null:
            continue
        r, u = float(np.mean(real)), float(np.mean(null))
        out[band] = {"n_nodes": len(nodes), "n_sampled": len(real),
                     "observed": round(r, 5), "null": round(u, 5),
                     "ratio": round(r / u, 2) if u else None}
    return out


def curated_recall(sets: list[np.ndarray], n: int, target_sets: list[set[int]],
                   target_bands: list[str], target_sources: list[str]) -> dict:
    """Recall of curated targets at Jaccard > 0.5 by any node of the tree.

    Args:
        sets: Member arrays for all nodes.
        n: Number of leaves.
        target_sets: Curated leaf sets.
        target_bands: Band per target.
        target_sources: Source per target.

    Returns:
        Per source and band, recall and the denominator.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(target_sets):
        for member in members:
            holders[member].append(index)
    hit = np.zeros(len(target_sets), dtype=bool)
    for node in range(n, len(sets)):
        members = set(sets[node].tolist())
        for candidate in {c for m in members for c in holders[m]}:
            if hit[candidate]:
                continue
            other = target_sets[candidate]
            inter = len(members & other)
            if inter and inter / (len(members) + len(other) - inter) > MATCH:
                hit[candidate] = True
    out: dict[str, dict] = {}
    for source in ("reactome", "go"):
        cells: dict[str, dict] = {}
        for low, high in TARGET_BANDS:
            band = f"{low}-{high}"
            idx = [i for i, (b, s) in enumerate(zip(target_bands, target_sources, strict=True))
                   if b == band and s == source]
            if idx:
                cells[band] = {"recall": round(float(hit[idx].mean()), 4), "n": len(idx)}
        out[source] = cells
    return out


def main(argv: list[str] | None = None) -> int:
    """Run Step 1 for every engine.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--engines", default="W,C,A")
    parser.add_argument("--relations", choices=("primary", "secondary"), default="secondary")
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/one_linkage/step1.json"))
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    vectors = np.ascontiguousarray(
        np.load(root / "vectors_leaves_centred.npy").astype(np.float32))
    if vectors.shape[0] != n:
        raise ValueError(f"{vectors.shape[0]} vectors for {n} keys")

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    names = {p.key: p.name for p in collection.pathways}
    sources = {p.key: p.source for p in collection.pathways}
    kept, _excluded = partition_universe(collection)
    universe = {p.key for p in kept}

    relations = PRIMARY_RELATIONS if args.relations == "primary" else SECONDARY_RELATIONS
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {f"reactome:{c}": {f"reactome:{p}" for p in ps}
                                  for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(), relations).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}
    index_of = {k: i for i, k in enumerate(keys)}
    key_sets = targets(edges, internal(edges, universe), keys, min_size=3)
    order = sorted(key_sets)
    target_sets = [{index_of[k] for k in key_sets[t]} for t in order]
    target_bands = [band_of(len(s), TARGET_BANDS) for s in target_sets]
    target_sources = [sources.get(t, "?") for t in order]

    print(f"ONE LINKAGE, step 1: {n:,} leaves, {len(target_sets):,} curated targets "
          f"({args.relations} closure)")
    report: dict[str, object] = {"n": n, "relations": args.relations, "seed": SEED,
                                 "bands": [list(b) for b in BANDS],
                                 "chain_share": CHAIN_SHARE, "cuts": list(CUTS),
                                 "engines": {}}

    for engine in args.engines.split(","):
        engine = engine.strip()
        if engine == "W":
            sets, seconds, inversions = ward_nodes(vectors)
            merges = np.array([[0, 0]])
            agg = None
        elif engine == "A":
            sets, seconds, inversions = average_nodes(vectors)
            merges = np.array([[0, 0]])
            agg = None
        elif engine == "C":
            agg = centroid_cosine(vectors)
            sets, seconds, inversions = agg.members(n), agg.seconds, agg.inversions
            merges = agg.merges
        else:
            print(f"  unknown engine {engine!r}")
            continue

        sizes = {node: len(sets[node]) for node in range(len(sets))}
        counts = Counter(band_of(sizes[node]) for node in range(n, len(sets)))
        mid = sum(1 for node in range(n, len(sets))
                  if MID_BAND[0] <= sizes[node] <= MID_BAND[1])

        # Children come from the tree that produced the nodes, never guessed from sizes.
        if engine == "C":
            children = node_children(merges, n)
        else:
            children = {n + t: [int(row[0]), int(row[1])]
                        for t, row in enumerate(scipy_tree(engine, vectors))}

        collapsed = collapsed_children(children, sizes, len(sets) - 1)
        kid_counts = [len(v) for v in collapsed.values() if v]
        raw_counts = [len(v) for v in children.values()]

        placement = Counter()
        best_node = np.full(n, -1, dtype=np.int64)
        for node in range(len(sets) - 1, n - 1, -1):
            if sizes[node] > PLACEMENT_CAP:
                continue
            for leaf in sets[node]:
                if best_node[leaf] < 0:
                    best_node[leaf] = node
        for leaf in range(n):
            placement[band_of(sizes[int(best_node[leaf])]) if best_node[leaf] >= 0
                      else "none"] += 1

        cuts: dict[str, list] = {}
        for clusters in CUTS:
            if engine == "C":
                groups = agg.cut(n, clusters)
            else:
                from scipy.cluster.hierarchy import fcluster

                labels = fcluster(scipy_tree(engine, vectors), clusters,
                                  criterion="maxclust")
                groups = sorted((np.flatnonzero(labels == c) for c in np.unique(labels)),
                                key=len, reverse=True)
            entries = []
            for group in groups:
                centre = vectors[group].mean(axis=0)
                norm = np.linalg.norm(centre)
                centre = centre / (norm if norm else 1.0)
                nearest = group[np.argsort(-(vectors[group] @ centre))][:NEAREST]
                entries.append({
                    "size": int(len(group)),
                    "share": round(len(group) / n, 4),
                    "sources": dict(sorted(Counter(sources.get(keys[i], "?")
                                                   for i in group).items())),
                    "nearest": [names.get(keys[i], keys[i]) for i in nearest]})
            cuts[str(clusters)] = entries

        entry = {
            "seconds": round(seconds, 2), "inversions": inversions,
            "n_nodes": len(sets) - n,
            "bands": {(f"{lo}-{hi}" if hi < 10**9 else f"{lo}+"): counts.get(
                f"{lo}-{hi}" if hi < 10**9 else f"{lo}+", 0) for lo, hi in BANDS},
            "nodes_51_to_1000": mid,
            "children_median_raw": float(np.median(raw_counts)) if raw_counts else None,
            "children_median_collapsed": float(np.median(kid_counts)) if kid_counts else None,
            "children_max_collapsed": int(max(kid_counts)) if kid_counts else None,
            "leaf_placement": dict(sorted(placement.items())),
            "coherence": coherence(sets, n, keys, genes),
            "curated_recall": curated_recall(sets, n, target_sets, target_bands,
                                             target_sources),
            "cuts": cuts,
        }
        report["engines"][engine] = entry
        print(f"  {engine}: {seconds:.1f}s, {inversions:,} inversions, "
              f"{mid:,} nodes of 51-1000, median children "
              f"{entry['children_median_raw']:.0f} raw / "
              f"{entry['children_median_collapsed']:.0f} collapsed", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
