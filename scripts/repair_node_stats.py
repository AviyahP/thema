#!/usr/bin/env python3
"""Per-node support-at-0.5 and gene coherence for every theme in a build. Read-only.

Three consumers need the same two numbers per node -- the giants report, the giants-removed
counterfactual, and the browsable export -- so they are computed once here and cached.

**Support at Jaccard 0.5** is the share of the 200 real runs holding a node matching the theme at
0.50 on present members, against the build's own 0.70. The gap says whether a low-support theme is
absent or merely shifting: a theme at 0.04 that reaches 0.92 at the looser threshold is present in
nine runs out of ten in a slightly different form each time.

**Gene coherence** is mean pairwise gene Jaccard over the theme's members against a **size-matched**
null, because mean pairwise overlap falls with set size for combinatorial reasons alone and an
unmatched null would make every large theme look incoherent.

Usage::

    uv run scripts/repair_node_stats.py --build thema_L_repair
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.pathways import PathwayCollection
from thema.ontology import bitset as bits
from thema.ontology.universe import load_embedded

SOFT_THETA = 0.50
NULL_DRAWS = 10
MAX_PAIRS = 3000
SEED = 0
NEAREST = 10


def mean_pair_jaccard(keys: list[str], genes: dict[str, frozenset[str]],
                      rng: np.random.Generator) -> float | None:
    """Mean pairwise gene Jaccard, sampling pairs above :data:`MAX_PAIRS`.

    Args:
        keys: Member pathway keys.
        genes: Pathway key to gene set.
        rng: For sampling in a large theme.

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
    out = []
    for a, b in pairs:
        union = len(genes[a] | genes[b])
        out.append(len(genes[a] & genes[b]) / union if union else 0.0)
    return float(np.mean(out))


def soft_support(query: np.ndarray, runs: list, theta: float) -> float:
    """Share of runs holding a node matching ``query`` at ``theta`` on present members.

    Args:
        query: The theme's member bitset.
        runs: Loaded per-run records.
        theta: Match threshold.

    Returns:
        The share over eligible runs, or nan when no run drew three of its members.
    """
    hit = eligible = 0
    for run in runs:
        present = query & run.present
        size = bits.count(present)
        if size < 3:
            continue
        eligible += 1
        node, best = int(run.leaf_cluster[bits.unpack(present)[0]]), 0.0
        while node != -1:
            inter = bits.count(present & run.clusters[node])
            union = size + int(run.sizes[node]) - inter
            if union:
                best = max(best, inter / union)
            node = int(run.parent[node])
        if best >= theta:
            hit += 1
    return hit / eligible if eligible else float("nan")


def main(argv: list[str] | None = None) -> int:
    """Compute and cache per-node stats."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--build-version", default=None,
                        help="the version directory the BUILD lives under, when it differs from "
                             "--version (which supplies the universe, vectors and trees). An "
                             "exclusion rebuild reads one universe and is written beside another")
    parser.add_argument("--space", default="leaves_centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    from cut_trees import load_run

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    n = meta["n_embedded"]
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    index_of = {k: i for i, k in enumerate(keys)}
    vectors = np.ascontiguousarray(
        np.load(root / "vectors_leaves_centred.npy").astype(np.float32))
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    names = {p.key: p.name for p in collection.pathways}
    sources = {p.key: p.source for p in collection.pathways}

    path = (args.data / "ontology" / f"v{args.build_version}" / args.build
            if args.build_version else root / args.build)
    members: dict[str, list[str]] = defaultdict(list)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row.get("node") or row.get("id")] = float(row.get("support") or 0.0)
    parents: dict[str, list[str]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)
    if (path / "edges.tsv").is_file():
        with (path / "edges.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                parents[row["child"]].append(row["parent"])
                children[row["parent"]].append(row["child"])

    trees = root / "trees" / f"{args.space}_{meta['universe_digest']}"
    runs = [load_run(trees / f"row{r:05d}.npz", n, 10**9) for r in range(1, args.runs + 1)]
    width = ((n + bits.WORD - 1) // bits.WORD) * bits.WORD
    rng = np.random.default_rng(SEED)

    order = sorted(members, key=lambda node: -len(members[node]))
    out: dict[str, dict] = {}
    for position, node in enumerate(order, 1):
        keyset = members[node]
        block = bits.pack(sorted(index_of[k] for k in keyset), width)
        soft = soft_support(block, runs, SOFT_THETA)
        observed = mean_pair_jaccard(keyset, genes, rng)
        draws = []
        for _ in range(NULL_DRAWS):
            sample = [keys[i] for i in rng.choice(len(keys), len(keyset), replace=False)]
            value = mean_pair_jaccard(sample, genes, rng)
            if value is not None:
                draws.append(value)
        null = float(np.mean(draws)) if draws else None
        idx = [index_of[k] for k in keyset]
        centre = vectors[idx].mean(axis=0)
        norm = np.linalg.norm(centre)
        centre = centre / (norm if norm else 1.0)
        nearest = [keyset[i] for i in np.argsort(-(vectors[idx] @ centre))[:NEAREST]]
        out[node] = {
            "size": len(keyset), "support": round(support.get(node, 0.0), 4),
            "support_at_0.5": None if np.isnan(soft) else round(soft, 4),
            "coherence_observed": None if observed is None else round(observed, 6),
            "coherence_null": None if null is None else round(null, 6),
            "coherence_ratio": (round(observed / null, 2)
                                if observed is not None and null else None),
            "n_children": len(children.get(node, [])),
            "n_parents": len(parents.get(node, [])),
            "children": sorted(children.get(node, []),
                               key=lambda c: -len(members[c])),
            "parents": sorted(parents.get(node, [])),
            "sources": {s: sum(1 for k in keyset if sources.get(k) == s)
                        for s in sorted({sources.get(k, "?") for k in keyset})},
            "nearest": [names.get(k, k) for k in nearest],
        }
        if position % 2000 == 0:
            print(f"  {position:,}/{len(order):,}", flush=True)

    destination = args.out or (path / "node_stats.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"build": args.build, "n_leaves": n,
                                       "soft_theta": SOFT_THETA, "nodes": out},
                                      indent=1, default=float) + "\n", encoding="utf-8")
    print(f"  {len(out):,} nodes -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
