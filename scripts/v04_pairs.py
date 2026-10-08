#!/usr/bin/env python3
"""Clarification 10: pair distance and near-pair agreement, with a labels-shuffled null.

A different question from set recovery, and a fairer one to an arm whose themes are the wrong size.
Whole-set recall asks whether a theme *is* a curated set; this asks whether two pathways the
curation puts close together are put close together by the ontology. A theme can match no curated
set at Jaccard > 0.5 and still get every pair right, and an arm emitting one huge theme can get the
pairs right for a trivial reason -- which is what the null is for.

For each same-source pair: ``d_curated`` is the size of the smallest curated set containing both,
``d_theme`` the size of the smallest theme containing both (same-source members), or ``inf``.
Near-pair recall at T is the share of pairs with ``d_curated <= T`` that also have
``d_theme <= T``; precision is the converse. The null shuffles the theme LABELS over pathways,
keeping every theme's size, so it measures what the shape of the ontology gets for free.

Usage::

    uv run scripts/v04_pairs.py --half test --arm v0.4=v0.4/thema_10770
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

#: How many same-source pairs to sample, and the seeds.
PAIRS = 200000
PAIR_SEED = 0
SHUFFLE_SEED = 0
SHUFFLES = 20


def smallest(pairs: np.ndarray, sets: list[set[int]], n: int) -> np.ndarray:
    """Size of the smallest set containing both members of each pair, else inf.

    Args:
        pairs: ``(p, 2)`` universe indices.
        sets: Candidate sets.
        n: Universe size.

    Returns:
        One size per pair.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(sets):
        for member in members:
            holders[member].append(index)
    sizes = np.array([len(s) for s in sets], dtype=np.int64) if sets else np.zeros(0, np.int64)
    out = np.full(len(pairs), np.inf)
    for position, (a, b) in enumerate(pairs.tolist()):
        best = np.inf
        for candidate in holders[a]:
            if b in sets[candidate]:
                value = float(sizes[candidate])
                if value < best:
                    best = value
        out[position] = best
    return out


def main(argv: list[str] | None = None) -> int:
    """Score near-pair agreement for each arm.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from thema.data.hierarchy import read_reactome_relation
    from thema.ontology.evalsets import (
        NEAR_THRESHOLDS,
        PRIMARY_RELATIONS,
        SECONDARY_RELATIONS,
        descendant_sets,
        go_edges,
        near_pair_scores,
        split_half,
    )
    from thema.ontology.universe import load_embedded
    from v04_score import band_of

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--half", choices=("tuning", "test", "all"), default="test")
    parser.add_argument("--relations", choices=("primary", "secondary"), default="primary")
    parser.add_argument("--arm", action="append", default=[])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    base = args.data / "ontology"
    root = base / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    position = {key: i for i, key in enumerate(keys)}
    relations = PRIMARY_RELATIONS if args.relations == "primary" else SECONDARY_RELATIONS

    curated: dict[str, list[set[int]]] = {}
    reactome = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text(
            encoding="utf-8").splitlines())
    curated["reactome"] = descendant_sets(
        {c: set(p) for c, p in reactome.items()}, position, "reactome:")
    curated["go"] = descendant_sets(
        go_edges((args.data / "raw" / "go-basic.obo").read_text(encoding="utf-8").splitlines(),
                 relations), position, "go:")

    rng = np.random.default_rng(PAIR_SEED)
    report: dict = {"half": args.half, "relations": args.relations,
                    "thresholds": list(NEAR_THRESHOLDS), "pairs_sampled": PAIRS,
                    "shuffles": SHUFFLES, "arms": {}}
    sampled: dict[str, np.ndarray] = {}
    kept_sets: dict[str, list[set[int]]] = {}
    for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
        sets = curated[source]
        bands = [band_of(len(s)) for s in sets]
        tuning, test = split_half(sets, bands, seed=0)
        pick = {"tuning": tuning, "test": test, "all": list(range(len(sets)))}[args.half]
        kept_sets[source] = [sets[i] for i in pick]
        rows = np.array([i for i, k in enumerate(keys) if k.startswith(prefix)], dtype=np.int64)
        a = rng.choice(rows, size=PAIRS)
        b = rng.choice(rows, size=PAIRS)
        keep = a != b
        sampled[source] = np.column_stack([a[keep], b[keep]])
        print(f"  {source}: {len(rows):,} pathways, {len(sampled[source]):,} pairs, "
              f"{len(kept_sets[source]):,} curated sets in the {args.half} half", flush=True)

    d_curated = {s: smallest(sampled[s], kept_sets[s], n) for s in sampled}
    for source, values in d_curated.items():
        for t in NEAR_THRESHOLDS:
            print(f"    {source}: {int((values <= t).sum()):,} pairs are near at T={t}", flush=True)

    for spec in args.arm:
        name, path = spec.split("=", 1)
        full = base / path
        if not (full / "members.tsv").is_file():
            print(f"  {name}: not built")
            continue
        grouped: dict[str, list[str]] = defaultdict(list)
        with (full / "members.tsv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                grouped[row["node"]].append(row["key"])
        row_out: dict = {"themes": len(grouped)}
        for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
            themes = [{position[k] for k in members if k.startswith(prefix)}
                      for members in grouped.values()]
            themes = [t for t in themes if len(t) >= 3]
            d_theme = smallest(sampled[source], themes, n)
            cell: dict = {}
            for t in NEAR_THRESHOLDS:
                cell[f"T{t}"] = near_pair_scores(d_curated[source], d_theme, t)
            # Null: shuffle which pathways carry which theme labels, keeping every theme's size.
            shuffle = np.random.default_rng(SHUFFLE_SEED)
            rows = np.array([i for i, k in enumerate(keys) if k.startswith(prefix)],
                            dtype=np.int64)
            null: dict[str, list[float]] = {f"T{t}": [] for t in NEAR_THRESHOLDS}
            for _ in range(SHUFFLES):
                perm = shuffle.permutation(rows)
                remap = dict(zip(rows.tolist(), perm.tolist(), strict=True))
                shuffled = [{remap[p] for p in t} for t in themes]
                d_null = smallest(sampled[source], shuffled, n)
                for t in NEAR_THRESHOLDS:
                    got = near_pair_scores(d_curated[source], d_null, t)
                    null[f"T{t}"].append(got["recall"] or 0.0)
            for t in NEAR_THRESHOLDS:
                cell[f"T{t}"]["null_recall_mean"] = round(float(np.mean(null[f"T{t}"])), 5)
            row_out[source] = cell
        report["arms"][name] = row_out
        line = f"  {name:<22} themes {len(grouped):>6,}  "
        for source in ("reactome", "go"):
            for t in NEAR_THRESHOLDS:
                c = row_out[source][f"T{t}"]
                r = "--" if c["recall"] is None else f"{c['recall']:.1%}"
                p = "--" if c["precision"] is None else f"{c['precision']:.1%}"
                line += f"{source[:2]}T{t} {r}/{p} (null {c['null_recall_mean']:.1%})  "
        print(line, flush=True)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
