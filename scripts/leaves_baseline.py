#!/usr/bin/env python3
"""Baseline (a): the full-universe v0.4 build, restricted to its universe-L members.

This answers the question the leaves build has to beat: *does building on the leaves do anything
that simply hiding the summaries afterwards would not?* Take v0.4's themes, drop every member that
is a curated summary, keep what still has at least three members, and deduplicate -- restriction
collapses distinct themes onto the same leaf set whenever they differed only in which summaries they
held, and counting those twice would inflate the theme count and deflate precision for free.

The DAG is re-stacked over the survivors rather than inherited. Restriction changes which sets
contain which, so v0.4's edges are not edges of the restricted build.

Usage::

    uv run scripts/leaves_baseline.py
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#: Smallest theme that survives restriction, matching v0.4's own MIN_SIZE.
MIN_SIZE = 3


def main(argv: list[str] | None = None) -> int:
    """Restrict the full-universe build to L and export it.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export
    from thema.ontology.base import Node, Ontology
    from thema.ontology.recurrent import hasse
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--source", type=Path,
                        default=Path("data/ontology/v0.4/thema_10770"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--directory", default="restricted_v04")
    args = parser.parse_args(argv)

    clock = time.perf_counter()
    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    index_of = {key: i for i, key in enumerate(keys)}

    members: dict[str, set[str]] = defaultdict(set)
    support: dict[str, float] = {}
    with (args.source / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    with (args.source / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row["node"] if "node" in row else row["id"]] = float(row.get("support", 1.0))

    restricted: dict[frozenset[int], float] = {}
    collapsed = dropped = 0
    for node, keyset in members.items():
        rows = frozenset(index_of[k] for k in keyset if k in index_of)
        if len(rows) < MIN_SIZE:
            dropped += 1
            continue
        best = support.get(node, 1.0)
        if rows in restricted:
            collapsed += 1
            restricted[rows] = max(restricted[rows], best)
        else:
            restricted[rows] = best

    print(f"BASELINE (a)  {args.source.name} restricted to L")
    print(f"  {len(members):,} themes -> {len(restricted):,} distinct leaf sets of >= {MIN_SIZE}")
    print(f"  {dropped:,} fell below {MIN_SIZE} members after restriction, "
          f"{collapsed:,} collapsed onto a leaf set already present")

    order = sorted(restricted, key=lambda s: (-restricted[s], sorted(s)))
    blocks = [bits.pack(sorted(s), len(keys)) for s in order]
    parents_of = hasse(blocks)
    ids = [f"n{i:05d}" for i in range(len(order))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents_of[i]),
             members=tuple((keys[p], 1.0) for p in sorted(rows)),
             support=round(restricted[rows], 6))
        for i, rows in enumerate(order))
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = sum(1 for node in nodes if len(node.parents) > 1)
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {"n_nodes": len(nodes), "n_roots": len(roots), "n_multi_parent": multi,
             "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
             "n_unplaced": len(unplaced), "n_root_only": len(placed - in_nonroot),
             "n_effectively_unplaced": len(unplaced) + len(placed - in_nonroot)}
    print(f"  themes {shape['n_nodes']:,}  roots {shape['n_roots']:,}  "
          f"multi-parent {shape['multi_parent_share']:.1%}  "
          f"effectively unplaced {shape['n_effectively_unplaced']:,}", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {"method": "v0.4-restricted-to-L", "source_build": str(args.source),
                "universe": "L", "n": len(keys), "min_size": MIN_SIZE,
                "source_themes": len(members), "dropped_below_min_size": dropped,
                "collapsed_duplicates": collapsed,
                "note": "baseline (a) of the leaves experiment: hiding the summaries after the "
                        "fact, rather than building without them. Edges re-stacked over the "
                        "restricted sets, not inherited from the source build.",
                "seconds": round(time.perf_counter() - clock, 1),
                "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method="v0.4-restricted-to-L", params=manifest, nodes=nodes,
                 unplaced=unplaced, manifest=manifest),
        args.data / "ontology", args.version, genes, manifest, dry_run=False,
        info=info, directory=args.directory)
    print(f"  -> {written}  ({time.perf_counter() - clock:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
