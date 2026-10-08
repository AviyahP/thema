#!/usr/bin/env python3
"""The checks the reviewer's 8 Oct notes require, answering them one at a time.

``docs/spec/2026-10-08-reviewer-monotonicity-notes.md`` accepts the numbers in
``docs/status/2026-10-08-monotonicity.md`` but argues the note answered a different question.
This script runs the four measurements that reply to it:

A. **Placement of curated parents** (reviewer §2b, critique b). The reviewer's central claim: a
   curated parent is not placed at or above its child, so its genes scatter. Re-measured here
   independently rather than quoted, because a result this decisive should not rest on one run.

B. **Leaf-leaf co-theming** (critique e). The note's 84.5%-share-a-gene figure pools curated
   parent-child pairs, which share genes by construction, with ordinary pairs. Split them.

C. **The direction probe, properly controlled** (critique c). Folds grouped by top-level branch so
   one parent cannot appear on both sides of a split; train on one source and test on the other,
   both ways; and a description-length control to show how much is style rather than content.

D. **GO monotonicity** (critique f). The note was Reactome only. GO's ``part_of`` and the three
   ``regulates`` relations do not imply gene containment the way Reactome's unions do, so GO is
   measured separately and its containment rate is reported rather than assumed.

Read-only. No API spend. Usage::

    uv run scripts/monotonicity_followup.py
    uv run scripts/monotonicity_followup.py --build data/ontology/v0.4/thema_10770
"""

from __future__ import annotations

import argparse
import csv
import itertools
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_score

from thema.data.descriptions import read as read_descriptions
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
from thema.ontology.universe import load_embedded

#: Theme-size band the within-theme census runs over.
THEME_BAND = (3, 10)
#: Random pairs for each baseline.
RANDOM_PAIRS = 40000
#: Folds for the grouped cross-validation.
FOLDS = 5


def members_of(build: Path) -> dict[str, set[str]]:
    """Node to member pathway keys.

    Args:
        build: A built ontology directory.

    Returns:
        Node id to member keys.
    """
    out: dict[str, set[str]] = defaultdict(set)
    with (build / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out[row["node"]].add(row["key"])
    return out


def parents_of(build: Path) -> dict[str, set[str]]:
    """Node to parent node ids.

    Args:
        build: A built ontology directory.

    Returns:
        Child node id to parent ids.
    """
    out: dict[str, set[str]] = defaultdict(set)
    with (build / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out[row["child"]].add(row["parent"])
    return out


def depths(parents: dict[str, set[str]], nodes: list[str]) -> dict[str, int]:
    """Longest path from a root to each node.

    Args:
        parents: Child to parents.
        nodes: Every node id.

    Returns:
        Node id to depth, roots at 0.
    """
    memo: dict[str, int] = {}

    def walk(node: str, seen: frozenset[str]) -> int:
        """Depth of one node.

        Args:
            node: Node id.
            seen: Ancestors on the current path, to stop a cycle.

        Returns:
            The depth.
        """
        if node in memo:
            return memo[node]
        ups = [p for p in parents.get(node, ()) if p not in seen]
        memo[node] = 0 if not ups else 1 + max(walk(p, seen | {node}) for p in ups)
        return memo[node]

    sys.setrecursionlimit(100000)
    return {node: walk(node, frozenset()) for node in nodes}


def curated_pairs(
    genes: dict[str, frozenset[str]], data: Path
) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Curated (child, parent) pairs from both sources, and each pathway's top-level branch.

    The branch label is what groups the cross-validation folds: it is the pathway's highest
    curated ancestor, so a parent appearing in many pairs cannot straddle a split.

    Args:
        genes: Pathway key to gene set.
        data: The data directory.

    Returns:
        Pairs, and key to branch label.
    """
    rel = read_reactome_relation((data / "raw" / "ReactomePathwaysRelation.txt").read_text()
                                .splitlines())
    up: dict[str, set[str]] = {f"reactome:{c}": {f"reactome:{p}" for p in ps}
                              for c, ps in rel.items()}
    obo = go_edges((data / "raw" / "go-basic.obo").read_text().splitlines(), PRIMARY_RELATIONS)
    for child, ups in obo.items():
        up[f"go:{child}"] = {f"go:{p}" for p in ups}

    pairs = [(c, p) for c, ps in up.items() for p in ps
             if genes.get(c) and genes.get(p)]

    branch: dict[str, str] = {}

    def top(key: str, seen: frozenset[str]) -> str:
        """The highest ancestor of a key.

        Args:
            key: Pathway key.
            seen: Keys on the current path.

        Returns:
            A branch label.
        """
        if key in branch:
            return branch[key]
        ups = sorted(p for p in up.get(key, ()) if p not in seen)
        branch[key] = key if not ups else top(ups[0], seen | {key})
        return branch[key]

    for key in list(up) + [p for _c, p in pairs]:
        top(key, frozenset())
    return pairs, branch


def check_placement(build: Path, name: str, pairs: list[tuple[str, str]],
                    genes: dict[str, frozenset[str]], seed: int) -> None:
    """A. Is a curated parent placed at or above its child?

    Args:
        build: A built ontology directory.
        name: Label for the build.
        pairs: Curated (child, parent) pairs.
        genes: Pathway key to gene set.
        seed: RNG seed for the matched null.
    """
    mem = members_of(build)
    ups = parents_of(build)
    deep = depths(ups, list(mem))
    entry: dict[str, int] = {}
    deepest: dict[str, int] = {}
    for node, keys in mem.items():
        for key in keys:
            size = len(keys)
            if key not in entry or size < entry[key]:
                entry[key] = size
            if key not in deepest or deep[node] > deepest[key]:
                deepest[key] = deep[node]

    shared = [(c, p) for c, p in pairs
              if c in entry and p in entry and genes[c] < genes[p]]
    together = [(c, p) for c, p in shared
                if any(c in keys and p in keys for keys in mem.values())]
    by_entry = sum(1 for c, p in together if entry[p] >= entry[c])
    by_depth = sum(1 for c, p in together if deepest[p] <= deepest[c])
    strict_entry = sum(1 for c, p in together if entry[p] > entry[c])
    # The statistic that settles it. An aggregate excess over random can be made entirely of ties,
    # which carry no direction. Among pairs that are NOT tied, the parent being the higher one is a
    # coin flip if placement is direction-blind, whatever the tie rate is.
    wrong_entry = sum(1 for c, p in together if entry[p] < entry[c])
    untied = strict_entry + wrong_entry

    rng = np.random.default_rng(seed)
    keys = sorted(entry)
    draw = [(keys[i], keys[j]) for i, j in
            zip(rng.choice(len(keys), RANDOM_PAIRS), rng.choice(len(keys), RANDOM_PAIRS),
                strict=True) if i != j]
    null_entry = sum(1 for a, b in draw if entry[b] >= entry[a]) / len(draw)
    null_depth = sum(1 for a, b in draw if deepest[b] <= deepest[a]) / len(draw)

    print(f"  {name}")
    print(f"    curated pairs with both pathways placed: {len(shared):,};"
          f" sharing a theme: {len(together):,}")
    if together:
        print(f"    parent at or above child, by entry size: {100 * by_entry / len(together):.1f}%"
              f"   (matched random {100 * null_entry:.1f}%)")
        print(f"    parent at or above child, by depth:      {100 * by_depth / len(together):.1f}%"
              f"   (matched random {100 * null_depth:.1f}%)")
        print(f"    parent STRICTLY above child, by entry:   "
              f"{100 * strict_entry / len(together):.1f}%"
              f"   (tied: {100 * (len(together) - untied) / len(together):.1f}%)")
        if untied:
            print(f"    AMONG UNTIED PAIRS, parent is the higher one: "
                  f"{100 * strict_entry / untied:.1f}%  of {untied:,}   (chance 50%)")


def check_leaf_pairs(build: Path, name: str, pairs: list[tuple[str, str]],
                     genes: dict[str, frozenset[str]], seed: int) -> None:
    """B. Co-theming gene overlap, with curated relatives split out.

    Args:
        build: A built ontology directory.
        name: Label for the build.
        pairs: Curated (child, parent) pairs.
        genes: Pathway key to gene set.
        seed: RNG seed.
    """
    related = {frozenset(pair) for pair in pairs}
    lo, hi = THEME_BAND
    counts = {"related": [0, 0], "unrelated": [0, 0]}
    for keys in members_of(build).values():
        if not lo <= len(keys) <= hi:
            continue
        for a, b in itertools.combinations(sorted(keys), 2):
            ga, gb = genes.get(a, frozenset()), genes.get(b, frozenset())
            if not ga or not gb:
                continue
            bucket = "related" if frozenset((a, b)) in related else "unrelated"
            counts[bucket][0] += 1
            if ga & gb:
                counts[bucket][1] += 1
    rng = np.random.default_rng(seed)
    keys = [k for k, g in genes.items() if g]
    draw = [(keys[i], keys[j]) for i, j in
            zip(rng.choice(len(keys), RANDOM_PAIRS), rng.choice(len(keys), RANDOM_PAIRS),
                strict=True) if i != j]
    null = sum(1 for a, b in draw if genes[a] & genes[b]) / len(draw)
    print(f"  {name}")
    for bucket, (total, overlap) in counts.items():
        if total:
            label = ("curated parent-child pairs" if bucket == "related"
                     else "pairs with no curated relation")
            print(f"    {label:<32} {total:>8,} pairs   share a gene "
                  f"{100 * overlap / total:>5.1f}%")
    print(f"    {'random pairs':<32} {len(draw):>8,} pairs   share a gene {100 * null:>5.1f}%")


def check_probe(pairs: list[tuple[str, str]], branch: dict[str, str],
                genes: dict[str, frozenset[str]], vectors: np.ndarray,
                pos: dict[str, int], texts: dict[str, str]) -> None:
    """C. The direction probe with the reviewer's three controls.

    Args:
        pairs: Curated (child, parent) pairs.
        branch: Pathway key to top-level branch.
        genes: Pathway key to gene set.
        vectors: Embedding matrix.
        pos: Key to row index.
        texts: Key to description.
    """
    use = [(c, p) for c, p in pairs
           if c in pos and p in pos and genes[c] < genes[p]]
    child = np.array([pos[c] for c, _p in use])
    parent = np.array([pos[p] for _c, p in use])
    delta = vectors[parent] - vectors[child]
    groups = np.array([hash(branch.get(p, p)) for _c, p in use])
    source = np.array([0 if c.startswith("reactome:") else 1 for c, _p in use])

    features = np.vstack([delta, -delta])
    labels = np.r_[np.ones(len(delta)), np.zeros(len(delta))]
    paired = np.r_[groups, groups]
    paired_source = np.r_[source, source]

    print(f"  pairs: {len(use):,}  (Reactome {int((source == 0).sum()):,},"
          f" GO {int((source == 1).sum()):,})")
    folds = min(FOLDS, len(set(groups.tolist())))
    scores = cross_val_score(LogisticRegression(max_iter=3000), features, labels,
                             cv=GroupKFold(n_splits=folds), groups=paired, scoring="accuracy")
    print(f"    grouped by top-level branch ({folds} folds): "
          f"{100 * scores.mean():.1f}% +/- {100 * scores.std():.1f}%")

    for train, test, label in ((0, 1, "train Reactome -> test GO"),
                               (1, 0, "train GO -> test Reactome")):
        tr, te = paired_source == train, paired_source == test
        if tr.sum() < 50 or te.sum() < 50:
            print(f"    {label}: too few pairs")
            continue
        model = LogisticRegression(max_iter=3000).fit(features[tr], labels[tr])
        print(f"    {label}: {100 * model.score(features[te], labels[te]):.1f}%")

    length = np.array([[len(texts.get(p, "")) - len(texts.get(c, ""))] for c, p in use],
                      dtype=np.float64)
    lf = np.vstack([length, -length])
    ls = cross_val_score(LogisticRegression(max_iter=3000), lf, labels,
                         cv=GroupKFold(n_splits=folds), groups=paired, scoring="accuracy")
    print(f"    description length alone: {100 * ls.mean():.1f}%  "
          f"(the style control; the gap to the full probe is what the vectors add)")

    span = np.abs(length[:, 0])
    tight = span <= np.percentile(span, 25)
    if tight.sum() >= 100:
        tf = np.vstack([delta[tight], -delta[tight]])
        tl = np.r_[np.ones(int(tight.sum())), np.zeros(int(tight.sum()))]
        tg = np.r_[groups[tight], groups[tight]]
        n_folds = min(FOLDS, len(set(tg.tolist())))
        ts = cross_val_score(LogisticRegression(max_iter=3000), tf, tl,
                             cv=GroupKFold(n_splits=n_folds), groups=tg, scoring="accuracy")
        print(f"    length-matched quartile ({int(tight.sum()):,} pairs): "
              f"{100 * ts.mean():.1f}%")
    print("    LABEL: supervised on the answer key. Not usable in construction.")


def check_go_monotonicity(genes: dict[str, frozenset[str]], data: Path) -> None:
    """D. Does GO's primary closure imply gene containment?

    Args:
        genes: Pathway key to gene set.
        data: The data directory.
    """
    obo = go_edges((data / "raw" / "go-basic.obo").read_text().splitlines(), PRIMARY_RELATIONS)
    rows = [(f"go:{c}", f"go:{p}") for c, ps in obo.items() for p in ps]
    rows = [(c, p) for c, p in rows if genes.get(c) and genes.get(p)]
    if not rows:
        print("  no GO edges with genes on both sides")
        return
    contains = sum(1 for c, p in rows if genes[c] <= genes[p])
    overlap = sum(1 for c, p in rows if genes[c] & genes[p])
    share = np.median([len(genes[c] & genes[p]) / len(genes[c]) for c, p in rows])
    print(f"  GO edges over the primary closure with genes on both sides: {len(rows):,}")
    print(f"    parent genes contain child genes: {100 * contains / len(rows):.1f}%")
    print(f"    parent and child share a gene:    {100 * overlap / len(rows):.1f}%")
    print(f"    median share of the child's genes in the parent: {share:.2f}")


def main(argv: list[str] | None = None) -> int:
    """Run the four follow-up checks.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--build", type=Path, action="append", default=[])
    parser.add_argument("--embeddings", type=Path, default=Path("data/ontology/v0.3"))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    builds = args.build or [
        Path("data/ontology/v0.3/recurrent_dag_10770"),
        Path("data/ontology/v0.4/thema_10770"),
        Path("data/ontology/v0.3/hidef_grid_k5_maxres800"),
    ]
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    pairs, branch = curated_pairs(genes, args.data)
    embedded = load_embedded(args.embeddings, args.data / "pathways.tsv")
    pos = {k: i for i, k in enumerate(embedded.keys)}
    texts = read_descriptions(args.data / "pathway_descriptions.tsv")

    print("A. PLACEMENT: is a curated parent put at or above its child?")
    print("   (the reviewer's central claim, re-measured here rather than quoted)")
    for build in builds:
        if (build / "members.tsv").is_file():
            check_placement(build, build.name, pairs, genes, args.seed)
    print()
    print("B. CO-THEMING, with curated relatives split out from the rest")
    for build in builds:
        if (build / "members.tsv").is_file():
            check_leaf_pairs(build, build.name, pairs, genes, args.seed)
    print()
    print("C. THE DIRECTION PROBE, with the reviewer's controls")
    check_probe(pairs, branch, genes, embedded.vectors, pos, texts)
    print()
    print("D. GO MONOTONICITY over the primary closure")
    check_go_monotonicity(genes, args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
