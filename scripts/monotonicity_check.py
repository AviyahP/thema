#!/usr/bin/env python3
"""Does thematic clustering preserve gene containment?

Curated hierarchies are built on containment: a parent's gene set contains its child's. If THEMA's
descriptions-and-distances machinery does not respect that, the ontology is a grouping of wordings
rather than of biology. This script tests monotonicity in the four places it can fail, separately,
because they do not stand or fall together:

1. the curation itself -- how exactly does parent contain child in the ground truth?
2. the built DAG -- does every edge satisfy parent genes >= child genes?
3. the grouping -- are co-themed pathways gene-related, against a random-pair baseline?
4. the distances -- does embedding distance grow with containment depth, and is the direction of
   a containment pair recoverable from text at all?

Read-only. No API spend. Usage::

    uv run scripts/monotonicity_check.py
    uv run scripts/monotonicity_check.py --build data/ontology/v0.4/ablate_baseline
"""

from __future__ import annotations

import argparse
import csv
import itertools
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.ontology.universe import load_embedded

#: Theme sizes the within-theme pair census runs over; the band the eval protocol reports on.
THEME_BAND = (3, 10)
#: Random pairs drawn for the co-theming baseline.
RANDOM_PAIRS = 20000


def gene_sets(pathways: Path) -> dict[str, frozenset[str]]:
    """Map every pathway key to its gene set."""
    col = PathwayCollection.from_tsv_text(pathways.read_text())
    return {p.key: frozenset(p.genes) for p in col.pathways}


def curated_edges(relation: Path, genes: dict[str, frozenset[str]]) -> list[tuple[str, str]]:
    """Reactome (child, parent) pairs where both sides carry genes."""
    rel = read_reactome_relation(relation.read_text().splitlines())
    out = [(f"reactome:{c}", f"reactome:{p}") for c, ps in rel.items() for p in ps]
    return [(c, p) for c, p in out if genes.get(c) and genes.get(p)]


def members(build: Path) -> dict[str, set[str]]:
    """Node -> member pathway keys."""
    out: dict[str, set[str]] = defaultdict(set)
    with (build / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out[row["node"]].add(row["key"])
    return out


def check_curation(edges: list[tuple[str, str]], genes: dict[str, frozenset[str]]) -> None:
    """1. How monotone is the ground truth?"""
    contains = sum(1 for c, p in edges if genes[c] <= genes[p])
    share = np.median([len(genes[c] & genes[p]) / len(genes[c]) for c, p in edges])
    print("1. THE CURATION ITSELF")
    print(f"   Reactome parent-child edges with genes on both sides: {len(edges):,}")
    print(f"   parent genes contain child genes: {100 * contains / len(edges):.1f}%")
    print(f"   median share of the child's genes present in the parent: {share:.2f}")


def check_dag(build: Path, genes: dict[str, frozenset[str]]) -> None:
    """2. Is every built edge monotone, and does the parent actually generalise?"""
    mem = members(build)
    pool = {n: frozenset().union(*(genes.get(k, frozenset()) for k in ks)) for n, ks in mem.items()}
    with (build / "edges.tsv").open() as handle:
        edges = [(r["child"], r["parent"]) for r in csv.DictReader(handle, delimiter="\t")]
    empty = frozenset()
    ok = sum(1 for c, p in edges if pool.get(c, empty) <= pool.get(p, empty))
    adds = sum(1 for c, p in edges if pool.get(c, empty) < pool.get(p, empty))
    print(f"2. THE BUILT DAG  ({build})")
    print(f"   edges: {len(edges):,}")
    print(f"   parent genes contain child genes: {100 * ok / len(edges):.1f}%")
    print("   parent adds at least one gene (a strict generalisation): "
          f"{100 * adds / len(edges):.1f}%")


def check_grouping(build: Path, genes: dict[str, frozenset[str]], seed: int) -> None:
    """3. Are co-themed pathways gene-related, against a random-pair baseline?"""
    lo, hi = THEME_BAND
    zero = nested = total = 0
    jaccard: list[float] = []
    for keys in members(build).values():
        if not lo <= len(keys) <= hi:
            continue
        for a, b in itertools.combinations(sorted(keys), 2):
            ga, gb = genes.get(a, frozenset()), genes.get(b, frozenset())
            if not ga or not gb:
                continue
            total += 1
            inter = len(ga & gb)
            if not inter:
                zero += 1
            elif ga <= gb or gb <= ga:
                nested += 1
            jaccard.append(inter / len(ga | gb))
    rng = np.random.default_rng(seed)
    keys = [k for k, g in genes.items() if g]
    draw = zip(rng.choice(len(keys), RANDOM_PAIRS), rng.choice(len(keys), RANDOM_PAIRS),
               strict=True)
    pairs = [(keys[i], keys[j]) for i, j in draw if i != j]
    rzero = sum(1 for a, b in pairs if not genes[a] & genes[b])
    print(f"3. THE GROUPING  (within-theme pairs, themes of {lo}-{hi})")
    print(f"   pairs: {total:,}")
    print(f"   share no gene:          {100 * zero / total:.1f}%   "
          f"(random pairs: {100 * rzero / len(pairs):.1f}%)")
    print(f"   one gene set nests in the other: {100 * nested / total:.1f}%")
    print(f"   median gene Jaccard:    {np.median(jaccard):.3f}")


def check_distances(
    edges: list[tuple[str, str]],
    genes: dict[str, frozenset[str]],
    vectors: np.ndarray,
    pos: dict[str, int],
    folds: int,
) -> None:
    """4. Do distances grow with containment depth, and is direction recoverable?"""
    parents: dict[str, list[str]] = defaultdict(list)
    for child, parent in edges:
        parents[child].append(parent)
    chains = {
        (c, p, g)
        for c, ps in parents.items()
        for p in ps
        for g in parents.get(p, [])
        if all(k in pos and genes.get(k) for k in (c, p, g)) and genes[c] <= genes[p] <= genes[g]
    }
    order = sorted(chains)
    child = vectors[[pos[c] for c, _, _ in order]]
    mid = vectors[[pos[p] for _, p, _ in order]]
    top = vectors[[pos[g] for _, _, g in order]]
    near = 1 - np.einsum("ij,ij->i", child, mid)
    far = 1 - np.einsum("ij,ij->i", child, top)
    closer = int((near < far).sum())
    test = binomtest(closer, len(order), 0.5)
    print("4. THE DISTANCES")
    print(f"   chains child < parent < grandparent in genes: {len(order):,}")
    print(f"   d(child,parent) < d(child,grandparent): {100 * closer / len(order):.1f}%"
          f"   p = {test.pvalue:.2e}   (chance 50%)")
    print(f"   mean distance to parent {near.mean():.3f}, to grandparent {far.mean():.3f}")

    pairs = [(c, p) for c, p in edges if c in pos and p in pos and genes[c] < genes[p]]
    delta = vectors[[pos[p] for _, p in pairs]] - vectors[[pos[c] for c, _ in pairs]]
    features = np.vstack([delta, -delta])
    labels = np.r_[np.ones(len(delta)), np.zeros(len(delta))]
    scores = cross_val_score(
        LogisticRegression(max_iter=2000), features, labels, cv=folds, scoring="accuracy"
    )
    centre = vectors.mean(0)
    centre /= np.linalg.norm(centre)
    broad = vectors[[pos[p] for _, p in pairs]] @ centre
    narrow = vectors[[pos[c] for c, _ in pairs]] @ centre
    general = broad > narrow
    print(f"   strictly-containing pairs: {len(pairs):,}")
    print(f"   direction, linear probe ({folds}-fold):  {100 * scores.mean():.1f}%"
          f" +/- {100 * scores.std():.1f}%")
    print(f"   direction, nearer-the-centroid rule:  {100 * general.mean():.1f}%")
    print("   direction, the parent has more genes:  100.0%  (true by construction)")


def main(argv: list[str] | None = None) -> int:
    """Run the four monotonicity checks and print them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path,
                        default=Path("data/ontology/v0.3/recurrent_dag_10770"))
    parser.add_argument("--pathways", type=Path, default=Path("data/pathways.tsv"))
    parser.add_argument("--embeddings", type=Path, default=Path("data/ontology/v0.3"))
    parser.add_argument("--relation", type=Path,
                        default=Path("data/raw/ReactomePathwaysRelation.txt"))
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    genes = gene_sets(args.pathways)
    edges = curated_edges(args.relation, genes)
    embedded = load_embedded(args.embeddings, args.pathways)
    pos = {k: i for i, k in enumerate(embedded.keys)}

    check_curation(edges, genes)
    print()
    check_dag(args.build, genes)
    print()
    check_grouping(args.build, genes, args.seed)
    print()
    check_distances(edges, genes, embedded.vectors, pos, args.folds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
