#!/usr/bin/env python3
"""LABELLED DIAGNOSTIC, not decisive: what would a looser theta do to arm A's middle?

Declared by amendment 2 of the engine brief: for arm A, count the 51-500 candidates that would pass
the support gate at theta 0.60 and 0.50, against the declared 0.70.

**This decides nothing and cannot.** theta is fixed at 0.70 for every arm in the engine search, and
the 5 Oct report established why the middle is thin: 80.6% of a mid-size grouping's failed checks
are MISSING MEMBERS, meaning its members scatter across the other run's clusters. A lower theta
forgives exactly that kind of failure, so the question "how much of the middle is theta costing?"
has a number, and the number is worth knowing before anyone proposes changing theta on purpose.

The floors are NOT re-solved at the loosened theta, and that is the diagnostic's main limitation,
stated rather than buried: a lower theta raises support on the scrambled null too, so the real
floors at theta 0.60 would be higher than the stored ones and fewer candidates would pass than this
reports. **Every count here is therefore an upper bound.** Re-solving would mean ten more scramble
sides per theta, which the budget does not have and the declaration does not ask for.

Usage::

    uv run scripts/theta_diagnostic.py --thetas 0.70,0.60,0.50
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: The band the diagnostic is about.
MID = (51, 500)


def main(argv: list[str] | None = None) -> int:
    """Count mid-size candidates passing the stored floors at several thetas.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import DEFAULT_ENGINE_WORKERS, INCLUSION_CUT, cut_key
    from build_trees_10770 import peak_mb
    from cut_trees import MIN_SIZE, TOL, cap_for, load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import DEFAULTS, family_members_fast, prepare, score

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--thetas", default="0.70,0.60,0.50")
    parser.add_argument("--floors", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    thetas = [float(t) for t in args.thetas.split(",")]
    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    floors_path = args.floors or (
        trees / "completions" / cut_key(cap, INCLUSION_CUT)
        / f"floors_r1-{args.runs}_n{args.runs}.json"
    )
    stored = json.loads(floors_path.read_text())
    floors = {band: float(eff) for band, _raw, eff in stored["floors"]}
    print(f"THETA DIAGNOSTIC  arm A, {args.runs} runs, band {MID[0]}-{MID[1]}, "
          f"floors from {floors_path.name}")
    print("  effective thresholds: "
          + ", ".join(f"{b}:{v}" for b, v in floors.items()))
    print("  LABELLED DIAGNOSTIC, NOT DECISIVE. Floors are NOT re-solved at the loosened "
          "thetas,\n  so every count below is an UPPER BOUND.", flush=True)

    clock = time.perf_counter()
    runs = [load_run(trees / f"row{r:05d}.npz", n, cap) for r in range(1, args.runs + 1)]
    print(f"\n  {len(runs)} runs loaded ({time.perf_counter() - clock:.0f}s)", flush=True)

    def band_of(size: int) -> str:
        """Which floor stratum a grouping of this size falls in.

        Args:
            size: Member count.

        Returns:
            The stratum label.
        """
        for label in ("3-3", "4-4", "5-5", "6-6"):
            if size == int(label.split("-")[0]):
                return label
        return "7-9" if size <= 9 else "10+"

    report: dict = {"band": list(MID), "runs": args.runs, "floors_from": str(floors_path),
                    "floors_resolved_at_theta": None, "upper_bound": True, "thetas": {}}
    for theta in thetas:
        start = time.perf_counter()
        settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE,
                    "theta": theta, "families": "joined"}
        ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
        pool = score(ready, settings)
        words = ready.present.shape[1] * bits.WORD

        sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int64)
        mid = np.flatnonzero((sizes >= MID[0]) & (sizes <= MID[1]))
        support = np.nan_to_num(pool.support, nan=-1.0)
        passing = [
            int(g) for g in mid.tolist()
            if support[g] >= floors[band_of(int(sizes[g]))]
        ]
        # The gate is applied to COMPLETED families, so the candidate count above is the pool view;
        # completing the passers gives the number that would actually reach consensus.
        completed = 0
        if passing:
            for g in passing:
                full, inclusion = family_members_fast([g], pool, ready.present, words)
                members = [p for p in bits.unpack(full)
                           if inclusion.get(p, 0.0) >= INCLUSION_CUT]
                if MID[0] <= len(members) <= MID[1]:
                    completed += 1
        report["thetas"][f"{theta:.2f}"] = {
            "pool": int(len(pool.groupings)),
            "mid_candidates": int(len(mid)),
            "mid_passing_floors": len(passing),
            "mid_passing_and_still_mid_after_completion": completed,
            "seconds": round(time.perf_counter() - start, 1),
        }
        print(f"\n  theta {theta:.2f}:  pool {len(pool.groupings):,}   "
              f"{MID[0]}-{MID[1]} candidates {len(mid):,}   "
              f"pass the floors {len(passing):,}   "
              f"still {MID[0]}-{MID[1]} after completion {completed:,}   "
              f"({time.perf_counter() - start:.0f}s)", flush=True)

    base = report["thetas"].get("0.70")
    if base is not None:
        print(f"\n  against theta 0.70's {base['mid_passing_floors']:,}:")
        for key, got in report["thetas"].items():
            if key == "0.70":
                continue
            delta = got["mid_passing_floors"] - base["mid_passing_floors"]
            factor = (got["mid_passing_floors"] / base["mid_passing_floors"]
                      if base["mid_passing_floors"] else float("inf"))
            print(f"    theta {key}: {got['mid_passing_floors']:,} "
                  f"({delta:+,}, {factor:.1f}x) -- UPPER BOUND")
    print(f"\n  peak {peak_mb():.0f} MB (workers {DEFAULT_ENGINE_WORKERS} unused: arm A is Ward)")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
