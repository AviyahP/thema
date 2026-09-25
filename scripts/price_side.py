"""Time ONE side of a build, stage by stage, so a run is priced by measurement not extrapolation.

Peak resident memory is reported per stage because concurrency at scale is memory-bound rather than
CPU-bound: at 10,770 a side peaks at 8.6 GB, so the twelve-way concurrency that is comfortable at
1,850 would need ~104 GB. Scaling a timing from a smaller universe has been wrong here by 2x and
by 39%, which is why this measures rather than extrapolates.
"""

import argparse
import resource
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.ontology import bitset as bits
from thema.ontology.recurrent import (
    DEFAULTS,
    families,
    family_members,
    family_support,
    null_embeddings,
    prepare,
    score,
)
from thema.ontology.universe import load_embedded

INCLUSION_CUT = 0.25
MIN_SIZE = 3
THETA = 0.70
RUNS = 100


def peak_gb() -> float:
    """Peak resident set size so far, in GB (macOS reports bytes)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9


def main(argv: Sequence[str] | None = None) -> int:
    """Time one side and print the stage breakdown."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.3", help="versioned artifact directory")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--tag", default="real", help='"real", or a scramble index')
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    embedded = load_embedded(
        args.data / "ontology" / f"v{args.version}", args.data / "pathways.tsv"
    )
    n = len(embedded.keys)
    matrix = (
        embedded.vectors
        if args.tag == "real"
        else null_embeddings(embedded.vectors, int(args.tag))
    )
    settings = {
        **DEFAULTS, "runs": args.runs, "tol": 0.15, "linkage": "ward",
        "min_size": MIN_SIZE, "theta": THETA,
    }
    print(f"  n = {n:,}   runs = {args.runs}   tag = {args.tag}", flush=True)

    start = time.perf_counter()
    ready = prepare(matrix, n, settings, seed=args.seed)
    prepare_seconds = time.perf_counter() - start
    print(f"  prepare      {prepare_seconds:8.1f}s   peak {peak_gb():5.2f} GB", flush=True)
    for stage, seconds in ready.timing.stages.items():
        print(f"      {stage:<28} {seconds:8.1f}s", flush=True)

    start = time.perf_counter()
    pool = score(ready, settings)
    match_seconds = time.perf_counter() - start
    print(f"  matching     {match_seconds:8.1f}s   peak {peak_gb():5.2f} GB   "
          f"{len(pool.groupings):,} groupings", flush=True)

    words = ready.present.shape[1] * bits.WORD
    start = time.perf_counter()
    completed = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members([grouping], pool, ready.present, words)
        members = sorted(
            p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= INCLUSION_CUT
        )
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
    completion_seconds = time.perf_counter() - start
    print(f"  completion   {completion_seconds:8.1f}s   peak {peak_gb():5.2f} GB   "
          f"{len(completed):,} completed", flush=True)

    start = time.perf_counter()
    grouped = families(list(completed), completed, pool)
    families_seconds = time.perf_counter() - start
    print(f"  families     {families_seconds:8.1f}s   peak {peak_gb():5.2f} GB   "
          f"{len(grouped):,} families", flush=True)

    start = time.perf_counter()
    scored = sum(
        1
        for _seed, family in grouped
        if not np.isnan(family_support(family, pool, ready.eligible_mask))
    )
    support_seconds = time.perf_counter() - start
    print(f"  fam support  {support_seconds:8.1f}s   {scored:,} scored", flush=True)

    total = (
        prepare_seconds + match_seconds + completion_seconds
        + families_seconds + support_seconds
    )
    print(f"  ---- TOTAL   {total:8.1f}s = {total/60:.1f} min   PEAK {peak_gb():.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
