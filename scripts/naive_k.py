#!/usr/bin/env python3
"""Naive arm K: fixed cutoffs, no calibration, one sanity build on a scramble. EXPLORATORY.

A direction probe before committing ~20 h to the full Arm K and E1-E4 run. Arm K only, no K-snn, no
transfer, no HiDeF grid. **Cutoffs are chosen in advance and not fitted**: support >= 0.33 and
lifetime >= 2, meaning the group survives while k at least doubles.

The scramble build is the early-stop test. If scramble seed 3001 produces more than 5% as many
themes as the real build, the direction is bad and the run stops there.

Usage::

    uv run scripts/naive_k.py --side real
    uv run scripts/naive_k.py --side 3001
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: The declared fixed cutoffs. Chosen before running; not fitted to anything.
SUPPORT_CUT = 0.33
LIFETIME_CUT = 2.0

#: Runs, and the bands the report uses.
RUNS = 100
BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))


def main(argv: list[str] | None = None) -> int:
    """Build naive K for one side.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from thema.embed import centre_and_renormalise
    from thema.ontology import bitset as bits
    from thema.ontology import mutualrank as mr
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--side", default="real")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    n = len(embedded.keys)
    seed = None if args.side == "real" else int(args.side)
    base, _mean = centre_and_renormalise(embedded.vectors)
    base = np.ascontiguousarray(base.astype(np.float32))
    matrix = base if seed is None else np.ascontiguousarray(
        null_embeddings(base, seed).astype(np.float32))

    marks: dict[str, float] = {}
    print(f"NAIVE K  side {args.side}, n={n:,}, {args.runs} runs, ladder {mr.LADDER}", flush=True)
    print(f"  cutoffs chosen in advance: support >= {SUPPORT_CUT}, "
          f"lifetime >= {LIFETIME_CUT}", flush=True)

    clock = time.perf_counter()
    near = mr.neighbours(matrix, mr.K_MAX)
    marks["knn"] = time.perf_counter() - clock
    clock = time.perf_counter()
    edges, rank = mr.mutual_rank_edges(near)
    marks["mutual rank edges"] = time.perf_counter() - clock
    print(f"  kNN {marks['knn']:.0f}s; {len(edges):,} mutual edges "
          f"({marks['mutual rank edges']:.0f}s), peak {peak_mb():.0f} MB", flush=True)

    clock = time.perf_counter()
    per_run = mr.ladder_runs(edges, rank, n, args.runs)
    marks["ladder runs"] = time.perf_counter() - clock
    total_clusters = sum(len(rung) for run in per_run for rung in run)
    print(f"  ladder: {total_clusters:,} clusters over {args.runs} runs x {len(mr.LADDER)} rungs "
          f"({marks['ladder runs']:.0f}s), peak {peak_mb():.0f} MB", flush=True)

    clock = time.perf_counter()
    members, support, lifetime = mr.score(per_run, n)
    marks["support and lifetime"] = time.perf_counter() - clock
    print(f"  {len(members):,} distinct candidates, scored in "
          f"{marks['support and lifetime']:.0f}s, peak {peak_mb():.0f} MB", flush=True)

    keep = np.flatnonzero((support >= SUPPORT_CUT) & np.isfinite(lifetime)
                          & (lifetime >= LIFETIME_CUT))
    sup_only = np.flatnonzero(support >= SUPPORT_CUT)
    print(f"  gate: {len(sup_only):,} pass support alone, {len(keep):,} also pass lifetime",
          flush=True)

    out = args.out or (root / "naive_k" / f"{args.side}.npz")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"  {out} exists; not overwritten")
        return 0
    # EVERY candidate is saved, not just the gated ones, so a different lifetime cutoff is a
    # re-read rather than a rebuild. The build is 9 seconds, but the point is that the three
    # cutoffs 1.5, 2 and 3 are then scored on identical candidates.
    words = bits.words_for(n)
    packed = (np.vstack([bits.pack(m.tolist(), n) for m in members])
              if members else np.zeros((0, words), dtype=np.uint64))
    np.savez_compressed(
        out, members=packed, support=support, lifetime=lifetime,
        sizes=np.array([len(m) for m in members], dtype=np.int64),
        support_only=np.array([len(sup_only)]),
        timing=np.array([marks[k] for k in
                         ("knn", "mutual rank edges", "ladder runs", "support and lifetime")]),
    )
    print(f"  -> {out}", flush=True)
    report = {"side": args.side, "n": n, "runs": args.runs, "ladder": list(mr.LADDER),
              "support_cut": SUPPORT_CUT, "lifetime_cut": LIFETIME_CUT,
              "mutual_edges": int(len(edges)), "clusters_seen": int(total_clusters),
              "candidates": int(len(members)), "pass_support": int(len(sup_only)),
              "pass_both": int(len(keep)),
              "timing_seconds": {k: round(v, 1) for k, v in marks.items()},
              "peak_mb": round(peak_mb(), 1)}
    (out.with_suffix(".json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"  peak {peak_mb():.0f} MB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
