#!/usr/bin/env python3
"""Test R stage 1: regenerate each needed Ward tree, ASSERT it matches, keep the heights.

EXPLORATORY -- Test R, `docs/spec/test-R-2026-10-07.md`. The persisted trees store cluster bitsets
and not merge heights, and the heights are what every gap score is built on. So each tree is rebuilt
from its recorded sample with the same two functions `tree_from_subset` uses, in the same order, and
the result is **asserted equal to the persisted tree** on both `present` and `clusters`. A single
mismatch stops the run: a height taken from a tree that is not the tree the build used would be
measuring a different dendrogram.

Heights go in NEW files beside the trees, named `*.heights.npz`. Nothing existing is modified, so no
cached side's provenance fingerprint moves.

Usage::

    uv run scripts/test_r_heights.py --sides real,3001,3002,3003,4001,4002,4003,4004,4005
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


def main(argv: list[str] | None = None) -> int:
    """Regenerate and persist heights for each requested side.

    Args:
        argv: Command-line arguments.

    Returns:
        0 on success, 1 if any tree failed its assertion.
    """
    from build_trees_10770 import peak_mb
    from thema.cluster import distances
    from thema.embed import centre_and_renormalise
    from thema.ontology import bitset as bits
    from thema.ontology import gap
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--sides", default="real,3001,3002,3003,4001,4002,4003,4004,4005")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    n, universe = meta["n_embedded"], meta["universe_digest"]
    trees = root / "trees" / f"{args.space}_{universe}"
    indices = np.load(root / "subsamples" / "indices.npy")
    embedded = load_embedded(root, args.data / "pathways.tsv")
    base, _mean = centre_and_renormalise(embedded.vectors)
    base = np.ascontiguousarray(base.astype(np.float32))
    out_dir = trees / "heights"
    out_dir.mkdir(parents=True, exist_ok=True)

    sides = [s.strip() for s in args.sides.split(",") if s.strip()]
    print(f"TEST R stage 1  heights for {len(sides)} sides "
          f"x {args.runs} trees, n={n:,}", flush=True)
    print(f"  -> {out_dir}  (new files; nothing existing is modified)", flush=True)

    checked = 0
    for side in sides:
        seed = None if side == "real" else int(side)
        label = (lambda r: f"row{r:05d}") if seed is None else (
            lambda r, s=seed: f"seed{s:05d}_row{r:05d}")
        target = out_dir / f"{side}_n{args.runs:03d}.npz"
        if target.is_file():
            print(f"  {side}: heights already present, not overwritten", flush=True)
            continue
        clock = time.perf_counter()
        matrix = base if seed is None else np.ascontiguousarray(
            null_embeddings(base, seed).astype(np.float32)
        )
        full = distances(matrix)
        setup = time.perf_counter() - clock

        heights: list[np.ndarray] = []
        merges: list[np.ndarray] = []
        start = time.perf_counter()
        for r in range(1, args.runs + 1):
            subset = np.sort(indices[r - 1])
            tree = gap.build(matrix, n, subset, full=full)
            path = trees / f"{label(r)}.npz"
            with np.load(path) as handle:
                stored_present = handle["present"]
                stored_clusters = handle["clusters"]
            if not np.array_equal(bits.pack(subset.tolist(), n), stored_present):
                print(f"\n  STOP: {label(r)} present differs from the persisted tree", flush=True)
                return 1
            if not np.array_equal(tree.nodes[tree.recorded], stored_clusters):
                print(f"\n  STOP: {label(r)} cluster sets differ from the persisted tree "
                      f"({len(tree.recorded):,} regenerated vs {len(stored_clusters):,} stored)",
                      flush=True)
                return 1
            checked += 1
            # Only the merges need storing: leaf heights are 0 and the parent structure is
            # reproducible from the merge order, so this is the smallest faithful record.
            take = len(subset)
            heights.append(tree.height[take:].astype(np.float32))
            merges.append(tree.parent.astype(np.int32))
        np.savez_compressed(target, **{f"h{r:05d}": h for r, h in enumerate(heights, start=1)},
                            **{f"p{r:05d}": p for r, p in enumerate(merges, start=1)})
        print(f"  {side}: {args.runs} trees asserted and stored, "
              f"setup {setup:.0f}s + {time.perf_counter() - start:.0f}s, "
              f"{target.stat().st_size / 1e6:.0f} MB, peak {peak_mb():.0f} MB", flush=True)
        del full, matrix

    print(f"\n  {checked:,} trees regenerated and ASSERTED equal to the persisted trees "
          f"on both present and clusters", flush=True)
    print(f"  peak {peak_mb():.0f} MB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
