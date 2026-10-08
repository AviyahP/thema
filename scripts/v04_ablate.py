#!/usr/bin/env python3
"""v0.4 §1: run v0.3 with one stage switched off, cut sides and build. EXPLORATORY.

One (ablation, side) per invocation so sides can be done one at a time within a memory budget, and
so a run that dies loses one side rather than a whole arm. Sides are cached per ablation.

Every stage is reached by composing the frozen functions with different arguments plus the glue in
`thema.ontology.ablate`, so `recurrent.py`, `cut_trees.py` and the naming code are untouched.

Usage::

    uv run scripts/v04_ablate.py --ablation baseline --side real
    uv run scripts/v04_ablate.py --ablation no_size_cap --side seed03001 --build
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Which ablation turns which switch off. "baseline" is v0.3 at three-seed floors.
ABLATIONS: dict[str, dict[str, bool]] = {
    "baseline": {},
    "no_size_cap": {"size_cap": False},
    "no_stray": {"stray": False},
    "no_completion": {"completion": False},
    "flat_merge": {"absorption": False},
    "single_floor": {"per_size_floors": False},
    "partial_containment": {"strict_containment": False},
}

#: Ablations whose GATE INPUT changes, so the floors must be re-solved from fresh scramble sides.
NEEDS_OWN_SIDES: frozenset[str] = frozenset({"no_size_cap", "no_completion", "flat_merge"})

#: Three-seed calibration and the two held-out seeds the rule names.
CALIBRATION = (3001, 3002, 3003)
HELDOUT = (4001, 4002)
NO_CAP = 10**9


def side_material(trees: Path, labels: list[str], n: int, cap: int, switches: object,
                  cutoff: float, marks: dict[str, float]) -> dict:
    """Cut one side under the given switches, returning the gate's input.

    **The stage ORDER is v0.3's, and getting it wrong was the one real bug in this work.** v0.3
    completes every grouping FIRST, drops those whose completed membership falls below ``min_size``,
    and only then runs seed absorption over the COMPLETED bitsets. My first version absorbed raw
    groupings and completed afterwards, which gave 259,924 families against v0.3's 161,852 -- a 60%
    inflation from an ordering difference, caught by validating against the frozen material rather
    than trusting the composition. Each switch now removes exactly one stage and leaves the order
    alone.

    Args:
        trees: The tree directory.
        labels: Tree stems in run order.
        n: Universe size.
        cap: Size cap, or a large number when the cap is off.
        switches: The ablation switches.
        cutoff: Inclusion cutoff for completion.
        marks: Filled with per-stage wall seconds.

    Returns:
        ``blocks``, ``supports`` and the pool size.
    """
    from cut_trees import MIN_SIZE, THETA, TOL, load_run
    from thema.ontology import bitset as bits
    from thema.ontology.ablate import flat_merge
    from thema.ontology.recurrent import (
        DEFAULTS,
        families,
        family_members_fast,
        family_support,
        prepare,
        score,
    )

    clock = time.perf_counter()
    runs = [load_run(trees / f"{label}.npz", n, cap) for label in labels]
    marks["load trees"] = time.perf_counter() - clock
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE,
                "theta": THETA, "families": "joined"}
    clock = time.perf_counter()
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)
    marks["prepare and match"] = time.perf_counter() - clock
    words = ready.present.shape[1] * bits.WORD

    # STAGE: completion. Off means a grouping's membership is its own bitset, unchanged, with the
    # same min_size filter applied so only the completion is removed and not the filter with it.
    clock = time.perf_counter()
    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        if switches.completion:
            candidate, inclusion = family_members_fast([grouping], pool, ready.present, words)
            members = sorted(p for p in bits.unpack(candidate)
                             if inclusion.get(p, 0.0) >= cutoff)
        else:
            members = sorted(bits.unpack(pool.groupings[grouping]))
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
    marks["completion" if switches.completion else "no completion"] = \
        time.perf_counter() - clock

    # STAGE: seed absorption. Off means a flat merge at theta over the same completed bitsets, so
    # nothing is absorbed transitively into a family it only partly matches.
    clock = time.perf_counter()
    if switches.absorption:
        grouped = families(list(completed), completed, pool, None, settings)
    else:
        order = list(completed)
        stacked = np.vstack([completed[g] for g in order])
        support = np.array([np.nan_to_num(pool.support[g], nan=-1.0) for g in order])
        grouped = [(order[fam[0]], [order[i] for i in fam])
                   for fam in flat_merge(stacked, support, THETA)]
    marks["families"] = time.perf_counter() - clock

    clock = time.perf_counter()
    blocks, supports = [], []
    for seed_grouping, family in grouped:
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        blocks.append(completed[seed_grouping])
        supports.append(float(support))
    marks["family support"] = time.perf_counter() - clock
    return {"blocks": np.vstack(blocks) if blocks
            else np.zeros((0, ready.present.shape[1]), np.uint64),
            "supports": np.array(supports, dtype=np.float64),
            "pool": int(len(pool.groupings))}


def main(argv: list[str] | None = None) -> int:
    """Cut one side, or build, for one ablation.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import INCLUSION_CUT, MAX_FDR_OVERALL, STRATA, confirm, solve, stratum_of
    from build_trees_10770 import peak_mb
    from cut_trees import cap_for
    from thema.ontology.ablate import Switches, single_floor

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--ablation", required=True, choices=sorted(ABLATIONS))
    parser.add_argument("--side", default="")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    switches = Switches(**ABLATIONS[args.ablation])
    cap = cap_for(n) if switches.size_cap else NO_CAP
    own = args.ablation in NEEDS_OWN_SIDES
    store = root / "ablate" / args.ablation
    store.mkdir(parents=True, exist_ok=True)

    def labels_for(side: str) -> list[str]:
        """Tree stems for a side.

        Args:
            side: ``real`` or ``seedNNNNN``.

        Returns:
            The stems in run order.
        """
        if side == "real":
            return [f"row{r:05d}" for r in range(1, args.runs + 1)]
        seed = int(side[4:])
        return [f"seed{seed:05d}_row{r:05d}" for r in range(1, args.runs + 1)]

    def material(side: str) -> dict:
        """Cached side material for this ablation, or v0.3's cache when unchanged.

        Args:
            side: The side name.

        Returns:
            ``blocks`` and ``supports``.
        """
        if not own:
            from build_10770 import side_cached
            label = (f"real_r00001-{args.runs:05d}" if side == "real"
                     else f"seed{int(side[4:]):05d}_n{args.runs:03d}")
            got, _cached = side_cached(
                trees, labels_for(side), n, cap, INCLUSION_CUT, label,
                fast=True, families_mode="joined", allow_stale=True)
            return {"blocks": got.blocks, "supports": got.supports}
        path = store / f"{side}.npz"
        if path.is_file():
            with np.load(path) as handle:
                return {"blocks": handle["blocks"], "supports": handle["supports"]}
        marks: dict[str, float] = {}
        clock = time.perf_counter()
        got = side_material(trees, labels_for(side), n, cap, switches, INCLUSION_CUT, marks)
        np.savez_compressed(path, blocks=got["blocks"], supports=got["supports"])
        (store / f"{side}.stages.json").write_text(json.dumps(
            {"seconds": {k: round(v, 1) for k, v in marks.items()},
             "total_seconds": round(time.perf_counter() - clock, 1),
             "n_families": int(len(got["supports"])), "n_pool": got["pool"],
             "peak_mb": round(peak_mb(), 1)}, indent=2) + "\n", encoding="utf-8")
        print(f"  {args.ablation}/{side}: {len(got['supports']):,} families in "
              f"{time.perf_counter() - clock:.0f}s, peak {peak_mb():.0f} MB", flush=True)
        return got

    if args.side:
        material(args.side)
        return 0

    if not args.build:
        parser.error("give --side to cut one side, or --build")

    def rows(got: dict) -> list[tuple[int, float]]:
        """``(size, support)`` rows.

        Args:
            got: Side material.

        Returns:
            One row per family.
        """
        sizes = np.bitwise_count(got["blocks"]).sum(axis=1).astype(np.int64)
        return list(zip(sizes.tolist(), [round(float(s), 6) for s in got["supports"]],
                        strict=True))

    clock = time.perf_counter()
    real = material("real")
    cal = [rows(material(f"seed{s:05d}")) for s in CALIBRATION]
    held = [rows(material(f"seed{s:05d}")) for s in HELDOUT]
    real_rows = rows(real)
    if switches.per_size_floors:
        solved = solve(real_rows, cal)
    else:
        one = single_floor(real_rows, cal, MAX_FDR_OVERALL)
        solved = [{"stratum": f"{low}-{high}" if high < 10**9 else f"{low}+",
                   "real": sum(1 for size, _s in real_rows if stratum_of(size) == index),
                   "floor": one, "effective": one, "calibration_fdr": None}
                  for index, (low, high) in enumerate(STRATA)]
    checked = confirm(real_rows, held, solved)
    print(f"  {args.ablation}: floors "
          + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved))
    print(f"  held-out FDR {checked['overall_fdr']} on {list(HELDOUT)}", flush=True)
    (store / "floors.json").write_text(json.dumps(
        {"ablation": args.ablation, "switches": ABLATIONS[args.ablation],
         "own_sides": own, "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
         "solved": solved, "confirmed": checked,
         "seconds": round(time.perf_counter() - clock, 1)},
        indent=2, default=float) + "\n", encoding="utf-8")
    print(f"  -> {store / 'floors.json'}  ({time.perf_counter() - clock:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
