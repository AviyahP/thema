#!/usr/bin/env python3
"""Prove the vectorised completion byte-identical to the original, and price the difference.

Completion runs over the whole grouping pool, so it is the stage a build spends most of its time in
and the stage a wrong answer would corrupt silently. This checks the replacement two ways and makes
no claim the checks do not support:

1. **Candidate-for-candidate, float-for-float**, over every eligible grouping of a REAL pool at the
   requested scale -- not a tolerance, because an inclusion is rounded and exported.
2. **Against the cached side on disk**, byte-for-byte: the fast path re-cuts a side whose `.npz` was
   written by the original, and the two files are compared as bytes.

The stage split is measured in the same pass, so the speed-up is reported per SIDE and not just per
completion -- a 5x faster completion is not a 5x faster side.

**prepare and score run ONCE** and both implementations consume the same pool. Timing two full sides
would double the expensive part and compare two different CPU loads.

Usage::

    uv run scripts/verify_completion.py --universe 0.2 --runs 100          # the 1,850
    uv run scripts/verify_completion.py --side real_r00001-00100           # a cached 10,770 side
    uv run scripts/verify_completion.py --side seed03001_n100
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from build_10770 import (
    INCLUSION_CUT,
    Material,
    cut_key,
    load_material,
    save_material,
)
from build_trees_10770 import peak_mb
from cut_trees import MIN_SIZE, THETA, TOL, cap_for, load_run
from thema.embed import centre_and_renormalise
from thema.ontology import bitset as bits
from thema.ontology.recurrent import (
    DEFAULTS,
    Pool,
    Prepared,
    families,
    family_members,
    family_members_fast,
    family_support,
    prepare,
    score,
)
from thema.ontology.universe import load_embedded


def labels_for(side: str, runs: int) -> list[str]:
    """Tree stems a cached side name refers to.

    Args:
        side: ``real_r00001-00100`` or ``seed03001_n100``.
        runs: Ignored for a real side; the side name carries its own length.

    Returns:
        Tree file stems, in run order.

    Raises:
        ValueError: If the side name is not one of the two recognised shapes.
    """
    if side.startswith("real_r"):
        low, _, high = side[len("real_r"):].partition("-")
        return [f"row{r:05d}" for r in range(int(low), int(high) + 1)]
    if side.startswith("seed") and "_n" in side:
        seed, _, count = side.partition("_n")
        return [f"{seed}_row{r:05d}" for r in range(1, int(count) + 1)]
    raise ValueError(f"unrecognised side name {side!r}")


def complete_all(
    pool: Pool, present: np.ndarray, words: int, cutoff: float, fast: bool
) -> tuple[dict[int, np.ndarray], float]:
    """Run completion over the whole pool with one implementation.

    Args:
        pool: The scored pool.
        present: ``(runs, words)`` present bitsets.
        words: Universe size in bits.
        cutoff: Inclusion cutoff.
        fast: Use the vectorised path.

    Returns:
        The completed groupings, and the wall seconds it took.
    """
    which = family_members_fast if fast else family_members
    clock = time.perf_counter()
    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = which([grouping], pool, present, words)
        members = sorted(p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= cutoff)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
    return completed, time.perf_counter() - clock


def material_of(
    pool: Pool,
    ready: Prepared,
    words: int,
    completed: dict[int, np.ndarray],
    fast: bool,
    grouped: list[tuple[int, list[int]]] | None = None,
) -> Material:
    """Assemble a side's material from an already-completed pool.

    Args:
        pool: The scored pool.
        ready: The prepared runs.
        words: Universe size in bits.
        completed: Completed groupings.
        fast: Which implementation to use for the selection pass.
        grouped: Families already computed, to use instead of recomputing them.

    Returns:
        The material.
    """
    which = family_members_fast if fast else family_members
    blocks, supports, selections = [], [], []
    for seed_grouping, family in (grouped if grouped is not None
                                  else families(list(completed), completed, pool)):
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        _candidate, selection = which([seed_grouping], pool, ready.present, words)
        blocks.append(completed[seed_grouping])
        supports.append(float(support))
        selections.append(selection)
    stacked = (np.vstack(blocks) if blocks
               else np.zeros((0, ready.present.shape[1]), dtype=np.uint64))
    return Material(stacked, np.asarray(supports, dtype=np.float64), tuple(selections))


def main(argv: list[str] | None = None) -> int:
    """Verify and price the vectorised completion.

    Args:
        argv: Command-line arguments.

    Returns:
        0 if the two implementations agree exactly, 1 if they do not.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--side", default="", help="a cached 10,770 side to re-cut and compare")
    parser.add_argument("--universe", default="", help="a version to build a pool from directly")
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--families", action="store_true",
                        help="also compare the families implementations and rebuild the cached "
                             "side with the joined join, comparing the .npz as bytes")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if bool(args.side) == bool(args.universe):
        parser.error("give exactly one of --side or --universe")

    stages: dict[str, float] = {}
    if args.universe:
        # No persisted trees at this version, so prepare() does its own Ward runs. That is the
        # point: this is the 1,850 pool as the frozen build's own pipeline produces it.
        root = args.data / "ontology" / f"v{args.universe}"
        embedded = load_embedded(root, args.data / "pathways.tsv")
        n = len(embedded.keys)
        matrix, _mean = centre_and_renormalise(embedded.vectors)
        matrix = np.ascontiguousarray(matrix.astype(np.float32))
        settings = {**DEFAULTS, "runs": args.runs, "tol": TOL,
                    "min_size": MIN_SIZE, "theta": THETA}
        print(f"VERIFY  universe v{args.universe}, {n:,} pathways, {args.runs} runs, "
              f"inclusion {INCLUSION_CUT}", flush=True)
        clock = time.perf_counter()
        ready = prepare(matrix, n, settings, 0)
        stages["prepare (incl. ward)"] = time.perf_counter() - clock
        cached = None
    else:
        root = args.data / "ontology" / f"v{args.version}"
        meta = json.loads((root / "universe.json").read_text())
        universe, n = meta["universe_digest"], meta["n_embedded"]
        trees = root / "trees" / f"centred_{universe}"
        cap = cap_for(n)
        labels = labels_for(args.side, args.runs)
        print(f"VERIFY  side {args.side}, {n:,} pathways, {len(labels)} runs, cap {cap:,}, "
              f"inclusion {INCLUSION_CUT}", flush=True)
        clock = time.perf_counter()
        runs = [load_run(trees / f"{label}.npz", n, cap) for label in labels]
        stages["load trees + cap"] = time.perf_counter() - clock
        settings = {**DEFAULTS, "runs": len(runs), "tol": TOL,
                    "min_size": MIN_SIZE, "theta": THETA}
        clock = time.perf_counter()
        ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
        stages["prepare (dedup + eligibility)"] = time.perf_counter() - clock
        cached = trees / "completions" / cut_key(cap, INCLUSION_CUT) / f"{args.side}.npz"

    clock = time.perf_counter()
    pool = score(ready, settings)
    stages["matching (support)"] = time.perf_counter() - clock
    words = ready.present.shape[1] * bits.WORD
    eligible = int(np.count_nonzero(~np.isnan(pool.support)))
    print(f"  {len(pool.groupings):,} groupings, {eligible:,} eligible", flush=True)

    if args.families:
        fast_only, fast_seconds = complete_all(
            pool, ready.present, words, INCLUSION_CUT, fast=True
        )
        print(f"  completion FAST      {fast_seconds:8.1f}s   {len(fast_only):,} completed",
              flush=True)
        modes, grouped, seconds = ("indexed", "joined"), {}, {}
        for mode in modes:
            clock = time.perf_counter()
            grouped[mode] = families(
                list(fast_only), fast_only, pool, settings={"families": mode}
            )
            seconds[mode] = time.perf_counter() - clock
            print(f"  families {mode:<8}    {seconds[mode]:8.1f}s   "
                  f"{len(grouped[mode]):,} families", flush=True)
        agree = grouped["indexed"] == grouped["joined"]
        print(f"  families IDENTICAL (seeds and lists, in order): {agree}", flush=True)
        if not agree:
            a, b = grouped["indexed"], grouped["joined"]
            print(f"    lengths {len(a):,} vs {len(b):,}")
            for i, (x, y) in enumerate(zip(a, b, strict=False)):
                if x != y:
                    print(f"    first difference at {i}: {x[0]} -> {len(x[1])} members "
                          f"vs {y[0]} -> {len(y[1])} members")
                    break
        ok = agree
        if cached is not None and cached.is_file():
            material = material_of(pool, ready, words, fast_only, fast=True,
                                   grouped=grouped["joined"])
            scratch = cached.with_suffix(".verify.npz")
            save_material(scratch, material)
            same = scratch.read_bytes() == cached.read_bytes()
            scratch.unlink()
            print(f"  cached side reproduced BYTE-FOR-BYTE with joined families: {same}",
                  flush=True)
            ok = ok and same
        print("\n  STAGE TIMES  load/prepare/matching/completion + families")
        for stage, value in stages.items():
            print(f"    {stage:<34} {value:8.1f}s")
        print(f"    {'completion (fast)':<34} {fast_seconds:8.1f}s")
        for mode in modes:
            print(f"    {'families (' + mode + ')':<34} {seconds[mode]:8.1f}s")
        base = sum(stages.values()) + fast_seconds
        print(f"\n    side, families indexed  {base + seconds['indexed']:7.1f}s")
        print(f"    side, families joined   {base + seconds['joined']:7.1f}s   "
              f"({seconds['indexed'] / max(seconds['joined'], 1e-9):.1f}x on the stage, "
              f"{(base + seconds['indexed']) / max(base + seconds['joined'], 1e-9):.2f}x per side)")
        print(f"    peak {peak_mb():.0f} MB")
        print(f"\n  VERDICT: {'IDENTICAL' if ok else 'NOT IDENTICAL -- do not use'}")
        return 0 if ok else 1

    slow, slow_seconds = complete_all(pool, ready.present, words, INCLUSION_CUT, fast=False)
    print(f"  completion ORIGINAL  {slow_seconds:8.1f}s   {len(slow):,} completed", flush=True)
    fast, fast_seconds = complete_all(pool, ready.present, words, INCLUSION_CUT, fast=True)
    print(f"  completion FAST      {fast_seconds:8.1f}s   {len(fast):,} completed", flush=True)

    same_keys = list(slow) == list(fast)
    same_values = same_keys and all(np.array_equal(slow[k], fast[k]) for k in slow)
    print(f"  completed sets identical: keys {same_keys}, bitsets {same_values}")

    byte_identical = None
    if cached is not None and cached.is_file():
        material = material_of(pool, ready, words, fast, fast=True)
        scratch = cached.with_suffix(".verify.npz")
        save_material(scratch, material)
        byte_identical = scratch.read_bytes() == cached.read_bytes()
        if not byte_identical:
            was = load_material(cached)
            print(f"    bytes differ; blocks equal: "
                  f"{np.array_equal(was.blocks, material.blocks)}, supports equal: "
                  f"{np.array_equal(was.supports, material.supports)}, selections equal: "
                  f"{was.selections == material.selections}")
        scratch.unlink()
        print(f"  cached side reproduced BYTE-FOR-BYTE: {byte_identical}")

    total = sum(stages.values())
    print("\n  PARTIAL STAGE SPLIT -- load, prepare, matching, completion ONLY.")
    print("  It does NOT include families (seed absorption) or the family-support and selection")
    print("  pass, which together are the larger half of a real side: this sums to ~93-99s where")
    print("  rung 1 measured whole sides at 195s (real) and 281-339s (scramble). The selection")
    print("  pass calls the same completion function, so it speeds up too -- which means the")
    print("  per-side figure below is computed on a PARTIAL denominator and is neither the true")
    print("  speed-up nor a bound on it. The full split comes from an instrumented side.")
    width = max(len(k) for k in stages)
    for stage, seconds in stages.items():
        print(f"    {stage:<{width}} {seconds:8.1f}s")
    print(f"    {'completion (original)':<{width}} {slow_seconds:8.1f}s")
    was_total = total + slow_seconds
    now_total = total + fast_seconds
    print(f"\n    these four stages, ORIGINAL  {was_total:7.1f}s  "
          f"(completion is {slow_seconds / was_total:.0%} of the four)")
    print(f"    these four stages, FAST      {now_total:7.1f}s")
    print(f"    SPEED-UP ON THE COMPLETION STAGE: "
          f"{slow_seconds / max(fast_seconds, 1e-9):.1f}x  <- the measured result")
    print(f"    (partial four-stage ratio {was_total / max(now_total, 1e-9):.2f}x; not a "
          f"per-side figure)")

    ok = same_values and (byte_identical is not False)
    print(f"\n  VERDICT: {'IDENTICAL' if ok else 'NOT IDENTICAL -- use the original'}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "side": args.side or f"universe v{args.universe}",
            "groupings": len(pool.groupings), "eligible": eligible,
            "completed": len(slow),
            "completion_seconds_original": round(slow_seconds, 2),
            "completion_seconds_fast": round(fast_seconds, 2),
            "stage_seconds": {k: round(v, 2) for k, v in stages.items()},
            "four_stages_seconds_original": round(was_total, 2),
            "four_stages_seconds_fast": round(now_total, 2),
            "speedup_four_stages_partial": round(was_total / max(now_total, 1e-9), 3),
            "speedup_four_stages_is_not_per_side": (
                "excludes families and the selection pass, which are the larger half of a side"
            ),
            "speedup_stage": round(slow_seconds / max(fast_seconds, 1e-9), 3),
            "completed_sets_identical": bool(same_values),
            "cached_side_byte_identical": byte_identical,
            "verdict": "identical" if ok else "not identical",
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
