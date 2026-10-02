#!/usr/bin/env python3
"""Build and persist Ward trees for the 10,770, so a later parameter change is a re-cut.

The expensive part of a `recurrent_dag` build is the trees: one Ward linkage per subsample, over
8,616 of 10,770 points. Everything downstream -- the size cap, the inclusion cutoff, the support
floors, the consensus -- is a decision about how to CUT those trees, and none of it changes the
trees themselves. So the trees are built once and written to disk, and every later question is
answered by re-cutting rather than rebuilding.

**A tree is persisted WITHOUT a size cap.** A cap decides which dendrogram nodes become candidate
clusters, which is a cut-time choice; baking it in would force a rebuild the first time the cap
moved. The recorded clusters are therefore every node at or above ``min_size``, and the cap is
applied when the run is read.

Scramble sides go in the same cache `calibrate_inclusion.py` already uses, keyed on space, universe
digest and seed, so a side is never computed twice.

Usage::

    uv run scripts/build_trees_10770.py --rows 1-400
    uv run scripts/build_trees_10770.py --scrambles
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.cluster import distances
from thema.embed import centre_and_renormalise
from thema.ontology.recurrent import Run, null_embeddings, tree_from_subset
from thema.ontology.universe import load_embedded

#: Smallest dendrogram node worth recording. NOT the size cap -- this is the floor the spec declares
#: and it does not change; the cap is a ceiling applied at cut time.
MIN_SIZE = 3

#: Scramble seeds. 10 calibration + 5 held-out, the counts `amendment-2026-09-24c` declares for the
#: 10,770 and that the stability study projected as adequate (worst stratum 7). Recorded here
#: because the earlier calibration's seeds were not, and that cost a 60-side recomputation.
CALIBRATION_SEEDS = tuple(range(3001, 3011))
HELDOUT_SEEDS = tuple(range(4001, 4006))


def peak_mb() -> float:
    """Peak resident memory of this process in MB.

    ``ru_maxrss`` is BYTES on macOS and KILOBYTES on Linux. Guessing from the magnitude reported
    963 MB as "919248 MB", so the unit is taken from the platform rather than inferred.

    Returns:
        Megabytes.
    """
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / (1024 * 1024) if sys.platform == "darwin" else raw / 1024


def tree_path(root: Path, space: str, universe: str, label: str) -> Path:
    """Where one run's tree is stored.

    Args:
        root: The versioned ontology directory.
        space: ``centred`` or ``raw``.
        universe: Universe digest.
        label: ``row00001`` for a real subsample, ``seed03001`` for a scramble.

    Returns:
        The ``.npz`` path.
    """
    return root / "trees" / f"{space}_{universe}" / f"{label}.npz"


def save_run(path: Path, run: Run) -> int:
    """Persist one run's record.

    Every array the matching loop needs is stored, so a reader never re-derives anything: the
    ancestor chains and sizes were the measured hot spot, not the linkage.

    Args:
        path: Destination.
        run: The :class:`thema.ontology.recurrent.Run` to write.

    Returns:
        Bytes written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".part.npz")
    np.savez_compressed(
        part,
        present=run.present,
        clusters=run.clusters,
        parent=run.parent,
        leaf_cluster=run.leaf_cluster,
        sizes=run.sizes,
        chain_indptr=run.chain_indptr,
        chain_idx=run.chain_idx,
    )
    part.replace(path)
    return path.stat().st_size


def rows_of(spec: str) -> list[int]:
    """Parse a 1-based inclusive row range like ``1-400``.

    Args:
        spec: The range.

    Returns:
        Row numbers.

    Raises:
        ValueError: If the range is malformed or descending.
    """
    low, _, high = spec.partition("-")
    first, last = int(low), int(high or low)
    if first < 1 or last < first:
        raise ValueError(f"bad row range {spec!r}")
    return list(range(first, last + 1))


def build(
    label_rows: Sequence[tuple[str, np.ndarray]],
    matrix: np.ndarray,
    n: int,
    full: np.ndarray,
    root: Path,
    space: str,
    universe: str,
    what: str,
) -> dict:
    """Build and persist a sequence of trees, skipping any already on disk.

    Args:
        label_rows: ``(label, sorted subset indices)`` per tree.
        matrix: The universe in the clustering space.
        n: Universe size.
        full: Condensed distances over all ``n`` points.
        root: Versioned ontology directory.
        space: Clustering space.
        universe: Universe digest.
        what: For the log line.

    Returns:
        Wall seconds, bytes written, trees built and trees already present.
    """
    built = skipped = written = 0
    start = time.perf_counter()
    for index, (label, subset) in enumerate(label_rows, 1):
        path = tree_path(root, space, universe, label)
        if path.is_file():
            skipped += 1
            continue
        run = tree_from_subset(matrix, n, subset, MIN_SIZE, "ward", full)
        written += save_run(path, run)
        built += 1
        if built % 10 == 0 or index == len(label_rows):
            per = (time.perf_counter() - start) / built
            left = (len(label_rows) - index) * per
            print(f"    {what} {index}/{len(label_rows)}  {built} built, {skipped} cached  "
                  f"{per:.1f}s each, ~{left / 60:.0f} min left, peak {peak_mb():.0f} MB",
                  flush=True)
    return {
        "seconds": round(time.perf_counter() - start, 1),
        "bytes": written,
        "built": built,
        "cached": skipped,
    }


def main(argv: list[str] | None = None) -> int:
    """Build trees for the real subsamples and/or the scramble sides.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", choices=("centred", "raw"), default="centred")
    parser.add_argument("--rows", default="", help="1-based inclusive range, e.g. 1-400")
    parser.add_argument("--scrambles", action="store_true")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    universe = json.loads((root / "universe.json").read_text())["universe_digest"]
    n = len(embedded.keys)
    matrix = embedded.vectors
    if args.space == "centred":
        matrix, _mean = centre_and_renormalise(matrix)
    matrix = np.ascontiguousarray(matrix.astype(np.float32))

    print(f"BUILDING TREES  {n:,} pathways, {args.space}, universe {universe}, "
          f"min_size {MIN_SIZE}, NO size cap baked in", flush=True)

    start = time.perf_counter()
    full = distances(matrix)
    print(f"  shared distance matrix: {time.perf_counter() - start:.1f}s, "
          f"{full.nbytes / 1e9:.2f} GB, peak {peak_mb():.0f} MB", flush=True)

    log: dict[str, object] = {
        "space": args.space,
        "universe_digest": universe,
        "n": n,
        "min_size": MIN_SIZE,
        "size_cap": None,
        "distance_matrix_seconds": round(time.perf_counter() - start, 1),
        "distance_matrix_bytes": int(full.nbytes),
    }

    if args.rows:
        indices = np.load(root / "subsamples" / "indices.npy")
        wanted = rows_of(args.rows)
        if max(wanted) > len(indices):
            print(f"only {len(indices):,} subsample rows persisted", flush=True)
            return 1
        pairs = [(f"row{r:05d}", np.sort(indices[r - 1])) for r in wanted]
        print(f"  real subsamples: rows {wanted[0]}-{wanted[-1]}, "
              f"{len(pairs[0][1]):,} points each", flush=True)
        log["real"] = build(pairs, matrix, n, full, root, args.space, universe, "row")

    if args.scrambles:
        log["scrambles"] = {"calibration": list(CALIBRATION_SEEDS),
                            "heldout": list(HELDOUT_SEEDS)}
        indices = np.load(root / "subsamples" / "indices.npy")
        # Every scramble side uses the SAME subsample sequence as the real side, so a difference
        # between them is the permutation and nothing else.
        rows = [np.sort(indices[r]) for r in range(100)]
        per = []
        for seed in (*CALIBRATION_SEEDS, *HELDOUT_SEEDS):
            scrambled = np.ascontiguousarray(null_embeddings(matrix, seed).astype(np.float32))
            sfull = distances(scrambled)
            pairs = [(f"seed{seed:05d}_row{i + 1:05d}", r) for i, r in enumerate(rows)]
            got = build(pairs, scrambled, n, sfull, root, args.space, universe, f"seed {seed}")
            got["seed"] = seed
            per.append(got)
            del scrambled, sfull
            print(f"  seed {seed}: {got['seconds']}s, {got['built']} built, "
                  f"{got['cached']} cached, {got['bytes'] / 1e6:.0f} MB", flush=True)
        log["scramble_sides"] = per

    out = root / "trees" / f"{args.space}_{universe}" / "build_log.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    merged = json.loads(out.read_text()) if out.is_file() else []
    merged.append(log)
    out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    disk = sum(p.stat().st_size for p in (root / "trees").rglob("*.npz"))
    print(f"\n  total on disk: {disk / 1e9:.2f} GB in "
          f"{len(list((root / 'trees').rglob('*.npz'))):,} trees")
    print(f"  peak memory: {peak_mb():.0f} MB")
    print(f"  log -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
