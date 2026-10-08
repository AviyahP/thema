#!/usr/bin/env python3
"""v0.4: gate, consensus, containment and export for one ablation. EXPLORATORY.

A separate file from `v04_ablate.py` on purpose. The ablation chain runs that script once per
side, each a fresh process, so editing it mid-run would have the next side pick up changed code --
the exact failure that corrupted a cached side on 2 Oct. This reads what the chain has already
written and never touches it.

Stages after the gate, and which switch each answers to:

- **gate** -- support at or above the stratum's effective floor, from the ablation's
  own floors.json.
- **consensus** -- greedy merge at theta; `no_stray` sets stray to 0 so nothing is inherited.
- **containment** -- strict Hasse, or partial containment at 0.9 for the report-only variant.

Usage::

    uv run scripts/v04_build.py --ablation baseline
    uv run scripts/v04_build.py --ablation baseline --rows 1-100
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


def gate(rows: list[tuple[int, float]], solved: list[dict]) -> np.ndarray:
    """Which families clear their stratum's effective floor.

    Args:
        rows: ``(size, support)`` per family.
        solved: Per-stratum entries with an ``effective`` threshold.

    Returns:
        Boolean mask over families.
    """
    from build_10770 import stratum_of

    need = []
    for size, _support in rows:
        index = stratum_of(size)
        entry = solved[index] if 0 <= index < len(solved) else None
        value = None if entry is None else entry.get("effective")
        need.append(np.inf if value is None else float(value))
    return np.array([s >= t for (_size, s), t in zip(rows, need, strict=True)])


def main(argv: list[str] | None = None) -> int:
    """Build and export one ablation.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import INCLUSION_CUT, side_cached
    from build_trees_10770 import peak_mb
    from cut_trees import MIN_SIZE, THETA, TOL, cap_for
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export
    from thema.ontology.ablate import PARTIAL_SHARE, Switches, partial_edges
    from thema.ontology.base import Node, Ontology
    from thema.ontology.consensus import DEFAULT_JACCARD, DEFAULT_STRAY, consensus
    from thema.ontology.recurrent import hasse
    from thema.ontology.universe import load_embedded
    from v04_ablate import ABLATIONS, NEEDS_OWN_SIDES, NO_CAP

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--ablation", required=True, choices=sorted(ABLATIONS))
    parser.add_argument("--rows", default="", help="e.g. 1-100 for a stability half")
    parser.add_argument("--out-version", default="0.4")
    parser.add_argument("--directory", default="")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    switches = Switches(**ABLATIONS[args.ablation])
    cap = cap_for(n) if switches.size_cap else NO_CAP
    store = root / "ablate" / args.ablation
    own = args.ablation in NEEDS_OWN_SIDES
    first, last = (1, args.runs)
    if args.rows:
        low, _, high = args.rows.partition("-")
        first, last = int(low), int(high or low)
    half = bool(args.rows)
    directory = args.directory or (
        f"ablate_{args.ablation}" + (f"_r{first}-{last}" if half else ""))

    solved = json.loads((store / "floors.json").read_text())["solved"]
    marks: dict[str, float] = {}

    clock = time.perf_counter()
    if own:
        if half:
            from v04_ablate import side_material

            labels = [f"row{r:05d}" for r in range(first, last + 1)]
            got = side_material(trees, labels, n, cap, switches, INCLUSION_CUT, {})
            blocks, supports = got["blocks"], got["supports"]
        else:
            with np.load(store / "real.npz") as handle:
                blocks, supports = handle["blocks"], handle["supports"]
    else:
        label = (f"real_r{first:05d}-{last:05d}")
        material, _cached = side_cached(
            trees, [f"row{r:05d}" for r in range(first, last + 1)], n, cap, INCLUSION_CUT,
            label, fast=True, families_mode="joined", allow_stale=True)
        blocks, supports = material.blocks, material.supports
    marks["side material"] = time.perf_counter() - clock

    sizes = np.bitwise_count(blocks).sum(axis=1).astype(np.int64)
    rows = list(zip(sizes.tolist(), [round(float(s), 6) for s in supports], strict=True))
    keep = np.flatnonzero(gate(rows, solved))
    print(f"{args.ablation}{' rows ' + args.rows if half else ''}: "
          f"{len(keep):,} of {len(rows):,} families through the gate", flush=True)
    if not len(keep):
        print("  nothing passes; writing nothing")
        return 0

    clock = time.perf_counter()
    words = blocks.shape[1] * bits.WORD
    gated = [blocks[i] for i in keep.tolist()]
    gated_support = [float(supports[i]) for i in keep.tolist()]
    inclusions = [{p: 1.0 for p in bits.unpack(b)} for b in gated]
    verdict = consensus(gated, gated_support, inclusions, words,
                        stray=DEFAULT_STRAY if switches.stray else 0.0,
                        jaccard=DEFAULT_JACCARD)
    kept = [(verdict.members[i], gated_support[c]) for i, c in enumerate(verdict.accepted)]
    marks["consensus"] = time.perf_counter() - clock
    print(f"  after consensus: {len(kept):,} nodes, {len(verdict.superseded)} superseded",
          flush=True)

    clock = time.perf_counter()
    member_blocks = [b for b, _s in kept]
    parents_of = (hasse(member_blocks) if switches.strict_containment
                  else partial_edges(member_blocks, PARTIAL_SHARE))
    marks["containment"] = time.perf_counter() - clock

    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    ids = [f"n{i:05d}" for i in range(len(kept))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents_of[i]),
             members=tuple((keys[p], 1.0) for p in sorted(bits.unpack(block))),
             support=round(sup, 6))
        for i, (block, sup) in enumerate(kept))
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = sum(1 for node in nodes if len(node.parents) > 1)
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {"n_nodes": len(nodes), "n_roots": len(roots), "n_multi_parent": multi,
             "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
             "n_unplaced": len(unplaced), "n_root_only": len(placed - in_nonroot),
             "n_effectively_unplaced": len(unplaced) + len(placed - in_nonroot)}
    print(f"  nodes {shape['n_nodes']:,}  roots {shape['n_roots']:,}  "
          f"multi-parent {shape['multi_parent_share']:.1%}  "
          f"effectively unplaced {shape['n_effectively_unplaced']:,}", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {"method": "v0.4-ablation", "ablation": args.ablation,
                "switches": ABLATIONS[args.ablation], "exploratory": True,
                "n": n, "rows": f"{first}-{last}", "runs": last - first + 1,
                "size_cap": None if not switches.size_cap else cap,
                "inclusion_cut": INCLUSION_CUT if switches.completion else None,
                "theta": THETA, "tol": TOL, "min_size": MIN_SIZE,
                "stray": DEFAULT_STRAY if switches.stray else 0.0,
                "containment": "strict" if switches.strict_containment
                else f"partial>={PARTIAL_SHARE}",
                "floors": solved, "universe_digest": universe,
                "seconds": {k: round(v, 1) for k, v in marks.items()},
                "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method="v0.4-ablation", params=manifest, nodes=nodes,
                 unplaced=unplaced, manifest=manifest),
        args.data / "ontology", args.out_version, genes, manifest,
        dry_run=False, info=info, directory=directory)
    print(f"  -> {written}  ({sum(marks.values()):.0f}s, peak {peak_mb():.0f} MB)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
