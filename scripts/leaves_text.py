#!/usr/bin/env python3
"""Test T: can THEMA's TEXT place a held-out summary on the theme that recreates it?

Every summary was removed before the build, so no theme ever saw it. Test T asks whether its own
description vector is enough to find the theme that corresponds to it -- which is what the display
layer would have to do in practice, and the one direction question that does not need the curated
hierarchy as an input. The hierarchy is only the judge.

- **T1** places each summary on the highest-cosine theme and scores
  Jaccard(summary's leaf set, that theme's members), with three reference points the spec names:
  a **ceiling** that places by gene overlap instead of text, a **floor** that picks a random theme
  of the same size, and the same text procedure run on the two baselines.
- **T2** restricts to summaries that some theme *does* recreate (Jaccard > 0.5) and asks how often
  the text ranking puts that theme first, or in its top five. T1 can only be as good as the build;
  T2 isolates the ranking from the build's own ceiling.

Reported, not decisive, as declared. No API cost. Usage::

    uv run scripts/leaves_text.py --arm L=thema_L --arm restricted=restricted_v04
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection, partition_universe
from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges, split_half
from thema.ontology.leaves import internal, targets
from thema.ontology.universe import load_embedded

BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))
MATCH = 0.5
#: Random-theme draws for the floor, and the seed the spec fixes.
FLOOR_DRAWS = 100
SEED = 0
#: Smallest theme eligible to receive a placement.
MIN_THEME = 3


def band_of(size: int) -> str:
    """Band label for a leaf-set size.

    Args:
        size: Leaf count.

    Returns:
        The label, or ``"other"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "other"


def jaccard(a: set[int], b: set[int]) -> float:
    """Jaccard of two index sets.

    Args:
        a: One set.
        b: The other.

    Returns:
        The Jaccard, 0 when both are empty.
    """
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)


def main(argv: list[str] | None = None) -> int:
    """Run T1 and T2 on every arm.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--full-version", default="0.3")
    parser.add_argument("--arm", action="append", default=[])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    leaves = load_embedded(root, args.data / "pathways.tsv")
    keys = list(leaves.keys)
    index_of = {key: i for i, key in enumerate(keys)}
    raw = leaves.vectors
    centre = raw.mean(axis=0)

    def project(vectors: np.ndarray) -> np.ndarray:
        """Centre on L's mean and renormalise, the transformation every build used.

        Args:
            vectors: Raw MedCPT rows.

        Returns:
            Unit rows in L's centred space.
        """
        out = vectors - centre
        norm = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norm == 0, 1.0, norm)

    leaf_space = project(raw)
    full = load_embedded(args.data / "ontology" / f"v{args.full_version}",
                         args.data / "pathways.tsv")
    full_row = {key: i for i, key in enumerate(full.keys)}

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    kept, _excluded = partition_universe(collection)
    universe = {p.key for p in kept}
    sources = {p.key: p.source for p in collection.pathways}
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}

    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {f"reactome:{c}": {f"reactome:{p}" for p in ps}
                                  for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(),
            PRIMARY_RELATIONS).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}

    marked = internal(edges, universe)
    key_sets = targets(edges, marked, keys, min_size=3)
    target_keys = sorted(key_sets)
    sets = [{index_of[k] for k in key_sets[tk]} for tk in target_keys]
    bands = [band_of(len(s)) for s in sets]
    in_band = [i for i, b in enumerate(bands) if b != "other"]
    _tuning, test = split_half([sets[i] for i in in_band], [bands[i] for i in in_band], seed=0)
    picked = [in_band[i] for i in test if target_keys[in_band[i]] in full_row]

    print(f"TEST T  text placement of held-out summaries, TEST half, n(L)={len(keys):,}")
    print(f"  summaries placed: {len(picked):,} (every one has a description vector and was "
          "never in any build)")

    report: dict[str, object] = {"n_placed": len(picked), "match": MATCH, "seed": SEED,
                                 "arms": {}}
    probe = project(full.vectors[[full_row[target_keys[i]] for i in picked]])

    for spec in args.arm:
        name, _, where = spec.partition("=")
        path = root / where
        if not (path / "members.tsv").is_file():
            print(f"  {name}: no build at {path}")
            continue
        members: dict[str, set[int]] = defaultdict(set)
        with (path / "members.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["key"] in index_of:
                    members[row["node"]].add(index_of[row["key"]])
        themes = [s for s in (members[k] for k in sorted(members)) if len(s) >= MIN_THEME]
        centroids = np.vstack([leaf_space[sorted(t)].mean(axis=0) for t in themes])
        norm = np.linalg.norm(centroids, axis=1, keepdims=True)
        centroids = centroids / np.where(norm == 0, 1.0, norm)
        theme_genes = [frozenset().union(*(genes.get(keys[i], frozenset()) for i in t))
                       for t in themes]
        sizes = np.array([len(t) for t in themes])

        cos = probe @ centroids.T
        order = np.argsort(-cos, axis=1)
        rng = np.random.default_rng(SEED)
        rows: list[dict] = []
        for position, i in enumerate(picked):
            leaf_set = sets[i]
            top = int(order[position, 0])
            text_j = jaccard(leaf_set, themes[top])
            own = genes.get(target_keys[i], frozenset())
            ceiling = max((len(own & g) / len(own | g) if own | g else 0.0)
                          for g in theme_genes) if own else 0.0
            same = np.flatnonzero(sizes == len(themes[top]))
            pool = same if len(same) else np.arange(len(themes))
            floor = float(np.mean([jaccard(leaf_set, themes[int(c)])
                                   for c in rng.choice(pool, FLOOR_DRAWS)]))
            recoverable = max(jaccard(leaf_set, t) for t in themes)
            hit = [j for j, t in enumerate(themes) if jaccard(leaf_set, t) > MATCH]
            rank = None
            if hit:
                places = {int(t): r for r, t in enumerate(order[position])}
                rank = min(places[j] for j in hit)
            rows.append({"band": bands[i], "source": sources.get(target_keys[i], "?"),
                         "text": text_j, "ceiling": ceiling, "floor": floor,
                         "best_possible": recoverable, "rank": rank})

        entry: dict[str, object] = {"themes": len(themes), "path": str(path), "bands": {}}
        for low, high in BANDS:
            band = f"{low}-{high}"
            sel = [r for r in rows if r["band"] == band]
            if not sel:
                continue
            entry["bands"][band] = {
                "n": len(sel),
                "median_text_jaccard": round(float(np.median([r["text"] for r in sel])), 4),
                "share_text_above_0.5": round(float(np.mean([r["text"] > MATCH
                                                             for r in sel])), 4),
                "median_gene_ceiling": round(float(np.median([r["ceiling"]
                                                              for r in sel])), 4),
                "median_random_floor": round(float(np.median([r["floor"] for r in sel])), 4),
                "median_best_possible": round(float(np.median([r["best_possible"]
                                                               for r in sel])), 4)}
        for source in ("reactome", "go"):
            sel = [r for r in rows if r["source"] == source]
            if sel:
                entry[f"{source}_median_text_jaccard"] = round(
                    float(np.median([r["text"] for r in sel])), 4)
        recovered = [r for r in rows if r["rank"] is not None]
        entry["T2"] = {
            "n_recovered": len(recovered),
            "top1": round(float(np.mean([r["rank"] == 0 for r in recovered])), 4)
            if recovered else None,
            "top5": round(float(np.mean([r["rank"] < 5 for r in recovered])), 4)
            if recovered else None}
        report["arms"][name] = entry
        print(f"  {name:<16} themes {len(themes):>6,}   "
              f"T2 recovered {len(recovered):,}  "
              f"top1 {entry['T2']['top1']}  top5 {entry['T2']['top5']}", flush=True)

    print()
    print("  T1: median Jaccard of the TEXT-placed theme against the summary's leaf set")
    print(f"    {'arm':<16}{'band':>10}{'n':>7}{'text':>8}{'gene ceil':>11}"
          f"{'rand floor':>12}{'best poss':>11}{'>0.5':>8}")
    for name, entry in report["arms"].items():
        for band, cell in entry["bands"].items():
            print(f"    {name:<16}{band:>10}{cell['n']:>7,}{cell['median_text_jaccard']:>8.3f}"
                  f"{cell['median_gene_ceiling']:>11.3f}{cell['median_random_floor']:>12.3f}"
                  f"{cell['median_best_possible']:>11.3f}"
                  f"{cell['share_text_above_0.5']:>8.3f}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"    -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
