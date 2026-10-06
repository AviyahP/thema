#!/usr/bin/env python3
"""KC: fine level from one mutual-rank filtration, then recursive near-cliques. EXPLORATORY.

Primary settings, declared before running: lifetime threshold solved to a scramble/real ratio of
0.01 on seeds 3001-3003; closeness percentile q = 99; join share 0.80; up to 6 levels.

Usage::

    uv run scripts/kc.py --side real
    uv run scripts/kc.py --side 3001 --t 1.75
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))


def band_of(size: int) -> str:
    """Band label for a theme size.

    Args:
        size: Member count.

    Returns:
        The label, or ``"500+"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "500+"


def run_side(matrix: np.ndarray, n: int, t: float, q: float, share: float,
             max_levels: int, marks: dict[str, float]) -> dict:
    """The whole KC pipeline for one matrix.

    Args:
        matrix: The ``(n, dim)`` centred unit-vector matrix.
        n: Node count.
        t: Lifetime threshold for the fine level.
        q: Closeness percentile.
        share: Join share.
        max_levels: Level cap.
        marks: Filled with per-step wall seconds.

    Returns:
        The fine level, the units, the per-level groups and every theme.
    """
    from thema.ontology import kc
    from thema.ontology import mutualrank as mr

    clock = time.perf_counter()
    near = mr.neighbours(matrix, mr.K_MAX)
    edges, rank = mr.mutual_rank_edges(near)
    marks["knn and mutual-rank edges"] = time.perf_counter() - clock

    clock = time.perf_counter()
    per_rung = kc.filtration(edges, rank, n)
    marks["filtration"] = time.perf_counter() - clock

    clock = time.perf_counter()
    fine = kc.fine_level(per_rung, n)
    marks["fine lifetimes"] = time.perf_counter() - clock

    alive = np.isfinite(fine.lifetime)
    keep = np.flatnonzero(alive & (fine.lifetime >= t))
    kept = [fine.members[i] for i in keep.tolist()]

    clock = time.perf_counter()
    leaves = kc.minimal(kept, n)
    covered = {int(p) for i in leaves for p in kept[i].tolist()}
    units = [kept[i] for i in leaves]
    units += [np.array([p], dtype=np.int64) for p in range(n) if p not in covered]
    marks["units"] = time.perf_counter() - clock

    clock = time.perf_counter()
    levels: list[list[np.ndarray]] = []
    thresholds: list[float] = []
    current = units
    for _level in range(max_levels):
        if len(current) < 2:
            break
        points = kc.centroids(current, matrix)
        graph, threshold = kc.close_graph(points, q)
        groups = kc.near_cliques(graph, share)
        if not groups:
            break
        merged = [np.unique(np.concatenate([current[u] for u in g])) for g in groups]
        merged = [m for m in merged if len(m) >= kc.MIN_SIZE]
        if not merged:
            break
        levels.append(merged)
        thresholds.append(threshold)
        joined = {u for g in groups for u in g}
        current = merged + [current[i] for i in range(len(current)) if i not in joined]
    marks["levels"] = time.perf_counter() - clock

    every = [m for m in kept] + [m for level in levels for m in level]
    seen: dict[bytes, int] = {}
    themes: list[np.ndarray] = []
    for m in every:
        key = m.astype(np.int32).tobytes()
        if key not in seen:
            seen[key] = len(themes)
            themes.append(m)
    return {"fine_kept": kept, "units": units, "levels": levels,
            "thresholds": thresholds, "themes": themes,
            "fine_candidates": len(fine.members),
            "lifetime": fine.lifetime, "sizes": np.array([len(m) for m in fine.members])}


def main(argv: list[str] | None = None) -> int:
    """Build KC for one side.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from thema.embed import centre_and_renormalise
    from thema.ontology import bitset as bits
    from thema.ontology import kc
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--side", default="real")
    parser.add_argument("--t", type=float, default=None, help="lifetime threshold")
    parser.add_argument("--q", type=float, default=kc.Q_PERCENTILE)
    parser.add_argument("--share", type=float, default=kc.JOIN_SHARE)
    parser.add_argument("--max-levels", type=int, default=kc.MAX_LEVELS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    n = len(embedded.keys)
    seed = None if args.side == "real" else int(args.side)
    base, _mean = centre_and_renormalise(embedded.vectors)
    base = np.ascontiguousarray(base.astype(np.float32))
    matrix = base if seed is None else np.ascontiguousarray(
        null_embeddings(base, seed).astype(np.float32))

    if args.out.exists():
        print(f"  {args.out} exists; not overwritten")
        return 0
    marks: dict[str, float] = {}
    print(f"KC  side {args.side}, n={n:,}, t={args.t}, q={args.q}, share={args.share}, "
          f"max levels {args.max_levels}", flush=True)
    got = run_side(matrix, n, args.t if args.t is not None else 0.0,
                   args.q, args.share, args.max_levels, marks)

    bands: dict[str, int] = {}
    for theme in got["themes"]:
        label = band_of(len(theme))
        bands[label] = bands.get(label, 0) + 1
    print(f"  fine: {got['fine_candidates']:,} candidates, {len(got['fine_kept']):,} kept at "
          f"t >= {args.t}; {len(got['units']):,} units", flush=True)
    for index, level in enumerate(got["levels"], start=1):
        print(f"  level {index}: {len(level):,} groups "
              f"(close threshold {got['thresholds'][index - 1]:.4f})", flush=True)
    print(f"  themes total {len(got['themes']):,}  bands {bands}", flush=True)
    for step, seconds in marks.items():
        print(f"    {step:<28}{seconds:>8.1f}s", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    packed = (np.vstack([bits.pack(m.tolist(), n) for m in got["themes"]])
              if got["themes"] else np.zeros((0, bits.words_for(n)), dtype=np.uint64))
    fine_packed = (np.vstack([bits.pack(m.tolist(), n) for m in got["fine_kept"]])
                   if got["fine_kept"] else np.zeros((0, bits.words_for(n)), dtype=np.uint64))
    level_of = np.concatenate(
        [np.zeros(len(got["fine_kept"]), dtype=np.int64)]
        + [np.full(len(level), index, dtype=np.int64)
           for index, level in enumerate(got["levels"], start=1)]
    ) if got["themes"] else np.zeros(0, dtype=np.int64)
    np.savez_compressed(
        args.out, themes=packed, fine=fine_packed,
        lifetime=got["lifetime"], sizes=got["sizes"],
        level_of_raw=level_of,
        n_units=np.array([len(got["units"])]),
        thresholds=np.array(got["thresholds"], dtype=np.float64),
        timing=np.array([marks.get(k, 0.0) for k in
                         ("knn and mutual-rank edges", "filtration", "fine lifetimes",
                          "units", "levels")]),
    )
    (args.out.with_suffix(".json")).write_text(json.dumps({
        "side": args.side, "n": n, "t": args.t, "q": args.q, "share": args.share,
        "fine_candidates": int(got["fine_candidates"]), "fine_kept": len(got["fine_kept"]),
        "units": len(got["units"]),
        "levels": [len(level) for level in got["levels"]],
        "close_thresholds": [round(v, 5) for v in got["thresholds"]],
        "themes": len(got["themes"]), "bands": bands,
        "timing_seconds": {k: round(v, 1) for k, v in marks.items()},
        "peak_mb": round(peak_mb(), 1),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"  -> {args.out}  peak {peak_mb():.0f} MB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
