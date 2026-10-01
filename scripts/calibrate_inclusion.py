#!/usr/bin/env python3
"""Re-solve the per-size support floors at several inclusion cutoffs, and report each one's FDR.

The floors in ``scripts/build_consensus.py`` were solved on scrambles at inclusion 0.25. The cutoff
is applied at COMPLETION -- before families form and before the support gate -- so a build at any
other cutoff runs those floors against a family population they were not solved for, and its FDR is
unknown rather than inherited. This script solves the floors again at each cutoff under the declared
procedure of ``docs/spec/addendum-2026-09-21.md``:

- F(s, c) = mean over the CALIBRATION scrambles of scrambled families of size stratum s with
  support >= c
- R(s, c) = real families of size stratum s with support >= c
- the floor is the smallest c with F/R <= ``--max-fdr``, evaluated at every distinct support value
  present in the null, with no grid and no rounding
- the solved floors are then confirmed ONCE on the HELD-OUT scrambles, which took no part in
  solving them

Each side's ``prepare`` and ``score`` are INDEPENDENT of the cutoff -- the run pool and the
support scores come from raw grouping sets -- so every side is built once and assembled at every
cutoff. That is what makes three calibrations cost one calibration's compute.

Usage::

    uv run scripts/calibrate_inclusion.py --cutoffs 0.25 0.33 0.50
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from thema.embed import centre_and_renormalise
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

#: The size strata the floors are solved in, as ``(low, high)``. These are the amendment's strata
#: and are NOT re-derived here: re-choosing strata against the data being cut is the defect that
#: ``amendment-2026-09-24b.md`` withdrew.
STRATA: tuple[tuple[int, int], ...] = ((3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (10, 10**9))

#: Scrambles that solve the floors, and scrambles that only confirm them.
#:
#: THE ORIGINAL SEEDS ARE NOT RECORDED ANYWHERE IN THE REPO. The frozen manifest says "20
#: calibration + 10 held-out scrambles ... overall held-out FDR 0.0051" and neither the
#: amendment nor the manifest names the seeds, and no committed script drove that run. 0.0051 is a
#: mean over ten
#: PARTICULAR scrambles, so a different ten gives a different number: an exact reproduction is not
#: available, and a close one is evidence the procedure agrees, not proof the seeds matched.
#:
#: The default follows the only convention the surviving artefacts imply -- the real side is seed 0,
#: so the scrambles are 1 onward -- and both sets are overridable so the question can be settled if
#: the originals ever turn up.
CALIBRATION_SEEDS = tuple(range(1, 21))
HELDOUT_SEEDS = tuple(range(21, 31))

MIN_SIZE = 3
RUNS = 100
THETA = 0.70
DECLARED_M = 0.33
SUPPORT_DECIMALS = 6


def stratum_of(size: int) -> int:
    """Index of the stratum a family of this size falls in.

    Args:
        size: Completed family size.

    Returns:
        Index into :data:`STRATA`.

    Raises:
        ValueError: If no stratum covers the size.
    """
    for index, (low, high) in enumerate(STRATA):
        if low <= size <= high:
            return index
    raise ValueError(f"no stratum covers size {size}")


def side(matrix: np.ndarray, n: int, cutoffs: Sequence[float], seed: int) -> dict[float, list]:
    """Build one side and return its families' ``(size, support)`` at every cutoff.

    ``prepare`` and ``score`` run ONCE; only completion, family formation and support depend on the
    cutoff, and those are cheap.

    Args:
        matrix: The side's unit-vector matrix, already in the clustering space.
        n: Universe size.
        cutoffs: Inclusion cutoffs to assemble at.
        seed: Master seed for the subsamples.

    Returns:
        Cutoff to a list of ``(size, support)``, one entry per family, BEFORE any support gate.
    """
    settings = {
        **DEFAULTS, "runs": RUNS, "tol": 0.15, "linkage": "ward",
        "min_size": MIN_SIZE, "theta": THETA,
    }
    ready = prepare(matrix, n, settings, seed=seed)
    pool = score(ready, settings)
    words = ready.present.shape[1] * bits.WORD
    out: dict[float, list] = {}
    for cut in cutoffs:
        completed: dict[int, np.ndarray] = {}
        for grouping in range(len(pool.groupings)):
            if np.isnan(pool.support[grouping]):
                continue
            candidate, inclusion = family_members([grouping], pool, ready.present, words)
            members = sorted(
                p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= cut
            )
            if len(members) >= MIN_SIZE:
                completed[grouping] = bits.pack(members, words)
        rows = []
        for seed_grouping, family in families(list(completed), completed, pool):
            support = family_support(family, pool, ready.eligible_mask)
            if np.isnan(support):
                continue
            rows.append((bits.count(completed[seed_grouping]),
                         round(float(support), SUPPORT_DECIMALS)))
        out[cut] = rows
    return out


#: Set in each worker process by :func:`_init`, so the matrix is sent once per process rather than
#: once per task. A scramble side is ~70 s and the sides are independent, so the calibration is
#: embarrassingly parallel; sequentially it is 37 minutes.
_MATRIX: np.ndarray | None = None
_N = 0
_CUTOFFS: tuple[float, ...] = ()
_SPACE = ""
_UNIVERSE = ""


#: Where each side's solved family rows are kept, so a side is never computed twice.
CACHE_DIR = Path("data/experiments/scramble_sides")


def cache_key(space: str, universe: str, seed: int) -> Path:
    """Path holding one side's rows.

    Keyed on the clustering SPACE and a digest of the universe as well as the seed, because a floor
    solved against different vectors is a different number and must never be served from here.

    Args:
        space: ``centred`` or ``raw``.
        universe: Digest of the matrix the sides were built from.
        seed: Scramble seed; 0 is the real side.

    Returns:
        The file path.
    """
    return CACHE_DIR / f"{space}_{universe}" / f"seed{seed:05d}.json"


def cache_load(path: Path, cutoffs: Sequence[float]) -> dict[float, list] | None:
    """Read a cached side, but only if it holds EVERY cutoff asked for.

    A partial hit is treated as a miss: serving three cutoffs from cache and computing the fourth
    separately would silently mix two runs of the pipeline in one calibration.

    Args:
        path: From :func:`cache_key`.
        cutoffs: The cutoffs required.

    Returns:
        Cutoff to rows, or ``None`` on any miss.
    """
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    got = {float(k): [(int(a), float(b)) for a, b in v] for k, v in raw.items()}
    return got if all(c in got for c in cutoffs) else None


def cache_store(path: Path, rows: dict[float, list]) -> None:
    """Write a side's rows, merging with anything already there.

    Merging rather than overwriting means a later run at a new cutoff ADDS to the file instead of
    discarding the cutoffs already solved, which is the whole point of the cache.

    Args:
        path: From :func:`cache_key`.
        rows: Cutoff to ``(size, support)`` rows.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    merged: dict[str, list] = {}
    if path.is_file():
        try:
            merged = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            merged = {}
    merged.update({f"{c:g}": [[int(a), float(b)] for a, b in v] for c, v in rows.items()})
    part = path.with_suffix(".part")
    part.write_text(json.dumps(merged), encoding="utf-8")
    part.replace(path)


def _init(
    matrix: np.ndarray, n: int, cutoffs: tuple[float, ...], space: str, universe: str
) -> None:
    """Seed one worker process with the shared inputs.

    Args:
        matrix: The real matrix, already in the clustering space.
        n: Universe size.
        cutoffs: Inclusion cutoffs to assemble at.
        space: Clustering space, part of the cache key.
        universe: Digest of the matrix, part of the cache key.
    """
    global _MATRIX, _N, _CUTOFFS, _SPACE, _UNIVERSE
    _MATRIX, _N, _CUTOFFS = matrix, n, cutoffs
    _SPACE, _UNIVERSE = space, universe


def _null_side(seed: int) -> dict[float, list]:
    """Build one scrambled side in a worker.

    Args:
        seed: The scramble seed. The permutation is computed here so 30 matrices are never pickled.

    Returns:
        Cutoff to ``(size, support)`` rows.
    """
    assert _MATRIX is not None
    path = cache_key(_SPACE, _UNIVERSE, seed)
    hit = cache_load(path, _CUTOFFS)
    if hit is not None:
        return {c: hit[c] for c in _CUTOFFS}
    rows = side(null_embeddings(_MATRIX, seed), _N, _CUTOFFS, seed=0)
    cache_store(path, rows)
    return rows


def solve(real: list, nulls: list[list], max_fdr: float) -> list[dict]:
    """Solve one floor per stratum at ``max_fdr``.

    Args:
        real: The real side's ``(size, support)`` rows.
        nulls: One list of rows per calibration scramble.
        max_fdr: The FDR each stratum must meet.

    Returns:
        Per stratum: its bounds, the solved floor, the effective threshold, and the counts the
        solution rests on. ``floor`` is ``None`` when no candidate meets the target, which means the
        stratum cannot be admitted and the build must say so.
    """
    out = []
    for index, (low, high) in enumerate(STRATA):
        r = [s for size, s in real if stratum_of(size) == index]
        per_null = [[s for size, s in rows if stratum_of(size) == index] for rows in nulls]
        candidates = sorted({s for rows in per_null for s in rows})
        chosen = None
        for c in candidates:
            f = sum(sum(1 for s in rows if s >= c) for rows in per_null) / max(len(per_null), 1)
            keep = sum(1 for s in r if s >= c)
            if keep and f / keep <= max_fdr:
                chosen = (c, f, keep)
                break
        if chosen is None:
            # Nothing in the null reaches a level the real side survives: either the stratum is
            # clean at every candidate, or it cannot be admitted. Distinguish the two.
            f_all = sum(len(rows) for rows in per_null) / max(len(per_null), 1)
            chosen = (0.0, f_all, len(r)) if f_all == 0 else (None, f_all, len(r))
        floor, f_at, r_at = chosen
        out.append({
            "stratum": f"{low}-{high}" if high < 10**9 else f"{low}+",
            "real": len(r), "null_mean": round(f_at, 2),
            "floor": floor,
            "effective": None if floor is None else max(DECLARED_M, floor),
            "real_kept": r_at,
            "fdr": None if floor is None or not r_at else round(f_at / r_at, 5),
        })
    return out


def confirm(real: list, nulls: list[list], solved: list[dict]) -> dict:
    """Apply solved floors to the held-out scrambles, which took no part in solving them.

    Args:
        real: The real side's rows.
        nulls: One list of rows per held-out scramble.
        solved: Output of :func:`solve`.

    Returns:
        Overall held-out FDR and the per-stratum counts behind it.
    """
    per = []
    total_f = total_r = 0.0
    for index, entry in enumerate(solved):
        threshold = entry["effective"]
        if threshold is None:
            per.append({**entry, "heldout_null": None, "heldout_fdr": None})
            continue
        r = sum(1 for size, s in real if stratum_of(size) == index and s >= threshold)
        f = sum(
            sum(1 for size, s in rows if stratum_of(size) == index and s >= threshold)
            for rows in nulls
        ) / max(len(nulls), 1)
        total_f += f
        total_r += r
        per.append({**entry, "heldout_null": round(f, 2), "heldout_real": r,
                    "heldout_fdr": round(f / r, 5) if r else None})
    return {"strata": per, "overall_fdr": round(total_f / total_r, 5) if total_r else None,
            "overall_real": int(total_r), "overall_null": round(total_f, 2)}


def _runs(seeds: Sequence[int]) -> str:
    """Render a seed list as contiguous ranges, so a pooled set does not read as one huge range.

    Args:
        seeds: The seeds.

    Returns:
        For example ``"1-20, 1000-1019 (40)"``. Printing first-last of a pooled list said "1-1019",
        which reads as a thousand scrambles rather than forty.
    """
    ordered = sorted(seeds)
    spans: list[list[int]] = []
    for s in ordered:
        if spans and s == spans[-1][1] + 1:
            spans[-1][1] = s
        else:
            spans.append([s, s])
    parts = [f"{a}" if a == b else f"{a}-{b}" for a, b in spans]
    return f"{', '.join(parts)} ({len(ordered)})"


def main(argv: list[str] | None = None) -> int:
    """Solve and confirm floors at each cutoff.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.2")
    parser.add_argument("--cutoffs", type=float, nargs="+", default=[0.25, 0.33, 0.50])
    parser.add_argument("--max-fdr", type=float, default=0.01)
    parser.add_argument(
        "--calibration-seeds", type=int, nargs="+", default=list(CALIBRATION_SEEDS),
        help="scramble seeds that SOLVE the floors (default: %(default)s)",
    )
    parser.add_argument(
        "--heldout-seeds", type=int, nargs="+", default=list(HELDOUT_SEEDS),
        help="scramble seeds that only CONFIRM them (default: %(default)s)",
    )
    parser.add_argument("--space", choices=("centred", "raw"), default="centred")
    parser.add_argument(
        "--workers", type=int, default=max(1, min(10, (os.cpu_count() or 2) - 2)),
        help="concurrent scramble sides (default: %(default)s)",
    )
    parser.add_argument("--out", type=Path, default=Path("data/experiments/inclusion_floors.json"))
    args = parser.parse_args(argv)

    embedded = load_embedded(
        args.data / "ontology" / f"v{args.version}", args.data / "pathways.tsv"
    )
    n = len(embedded.keys)
    matrix = embedded.vectors
    if args.space == "centred":
        matrix, _mean = centre_and_renormalise(matrix)
        matrix = np.ascontiguousarray(matrix.astype(np.float32))

    print(f"CALIBRATING  {n:,} pathways, {args.space}, cutoffs {args.cutoffs}, "
          f"FDR <= {args.max_fdr}", flush=True)
    print(f"  {len(args.calibration_seeds)} calibration + {len(args.heldout_seeds)} held-out "
          "scrambles, each assembled at every cutoff", flush=True)
    print(f"  calibration seeds {_runs(args.calibration_seeds)}", flush=True)
    print(f"  held-out seeds    {_runs(args.heldout_seeds)}", flush=True)
    print("  The ORIGINAL seeds are not recorded in the repo, so 0.0051 cannot be reproduced\n"
          "  exactly -- see CALIBRATION_SEEDS.", flush=True)

    universe = hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest()[:16]
    real_path = cache_key(args.space, universe, 0)
    real = cache_load(real_path, args.cutoffs)
    if real is None:
        print("  real side ...", end="", flush=True)
        real = side(matrix, n, args.cutoffs, seed=0)
        cache_store(real_path, real)
        print(" done", flush=True)
    else:
        print("  real side ... cached", flush=True)
    real = {c: real[c] for c in args.cutoffs}

    cutoffs = tuple(args.cutoffs)
    # From the ARGUMENTS, not the constants. The parallel rewrite read the constants while the
    # banner printed the arguments, so --calibration-seeds and --heldout-seeds were silently inert
    # and the banner would have misreported any override.
    every = [*args.calibration_seeds, *args.heldout_seeds]
    cached = sum(
        1 for s in every if cache_load(cache_key(args.space, universe, s), args.cutoffs) is not None
    )
    print(f"  {len(every)} scrambled sides on {args.workers} workers "
          f"({cached} already cached, {len(every) - cached} to compute) ...", flush=True)
    with ProcessPoolExecutor(
        max_workers=args.workers,
        initializer=_init,
        initargs=(matrix, n, cutoffs, args.space, universe),
    ) as pool:
        done = list(pool.map(_null_side, every))
    cal = done[: len(args.calibration_seeds)]
    held = done[len(args.calibration_seeds) :]

    report = {}
    for cut in args.cutoffs:
        solved = solve(real[cut], [c[cut] for c in cal], args.max_fdr)
        report[f"{cut:.2f}"] = confirm(real[cut], [h[cut] for h in held], solved)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\n  -> {args.out}")
    for cut, got in report.items():
        print(f"\n  inclusion {cut}:  held-out FDR {got['overall_fdr']}  "
              f"({got['overall_real']} real, {got['overall_null']} scrambled)")
        print(f"    {'stratum':<9} {'real':>6} {'floor':>9} {'effective':>10} "
              f"{'cal FDR':>8} {'held FDR':>9}")
        for e in got["strata"]:
            fl = "none" if e["floor"] is None else f"{e['floor']:.6f}"
            ef = "DROP" if e["effective"] is None else f"{e['effective']:.6f}"
            print(f"    {e['stratum']:<9} {e['real']:>6} {fl:>9} {ef:>10} "
                  f"{str(e['fdr']):>8} {str(e['heldout_fdr']):>9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
