#!/usr/bin/env python3
"""The 10,770 confirmatory build, from persisted trees: completion, floors, gate, consensus, Hasse.

Every expensive stage is already on disk. The trees were built once without a size cap, and this
re-cuts them under the declared cap, completes each grouping at the declared inclusion cutoff,
solves the support floors on the calibration scrambles, confirms them ONCE on the held-out
scrambles, applies the recurrence gate, reconciles with greedy consensus and draws strict Hasse
edges. Changing the cap or the cutoff re-runs this; it never rebuilds a tree.

**Per-run completions are persisted**, keyed on (space, universe, cap, cutoff, side). Re-running at
the same cap and cutoff reads them back instead of re-cutting; changing either parameter writes a
new key rather than overwriting, so an earlier cut stays reproducible. The real side additionally
persists the material the gate needs -- member bitsets, support, and the per-family inclusion vote
-- so the gate, the consensus and the Hasse pass can be re-run without touching a tree.

**The floors are solved under the same cap they are applied under.** Real and scrambled trees go
through the identical `load_run`, so a cap that removes a candidate removes it on both sides.

**The held-out scrambles are touched ONCE, and only with ``--confirm-heldout``.** The RUNS ladder
runs four builds before the confirmatory one, and if each of them confirmed against the held-out
set then "confirmed once" would be false by the time it mattered. Ladder builds therefore solve
floors on the 10 calibration scrambles and stop; the 5 held-out scrambles are read only by the
confirmatory build.

Usage::

    uv run scripts/build_10770.py --rows 1-100                     # one ladder block
    uv run scripts/build_10770.py --runs 200 --confirm-heldout     # the confirmatory build
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from build_trees_10770 import peak_mb
from cut_trees import CAP_SHARE, MIN_SIZE, THETA, TOL, cap_for, load_run
from thema.data.pathways import PathwayCollection
from thema.ontology import bitset as bits
from thema.ontology import export, recurrent
from thema.ontology.base import Node, Ontology
from thema.ontology.consensus import DEFAULT_JACCARD, DEFAULT_STRAY, consensus
from thema.ontology.recurrent import (
    DEFAULTS,
    families,
    family_members,
    family_members_fast,
    family_support,
    hasse,
    prepare,
    score,
)
from thema.ontology.universe import load_embedded

#: Declared rule, unchanged from the 1,850 freeze.
DECLARED_M = 0.33
INCLUSION_CUT = 0.50
SUPPORT_DECIMALS = 6

#: The size strata the floors are solved in. The amendment's strata; NOT re-derived here, because
#: re-choosing strata against the data being cut is the defect amendment-2026-09-24b withdrew.
STRATA: tuple[tuple[int, int], ...] = ((3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (10, 10**9))

#: Error caps, declared: overall held-out FDR and the per-stratum ceiling.
MAX_FDR_OVERALL = 0.01
MAX_FDR_STRATUM = 0.02

#: Scramble seeds, as recorded by the tree builder.
CALIBRATION_SEEDS = tuple(range(3001, 3011))
HELDOUT_SEEDS = tuple(range(4001, 4006))


@dataclass(frozen=True)
class Material:
    """One side's completed families: what the gate, the consensus and the Hasse pass consume.

    Attributes:
        blocks: ``(families, words)`` completed member bitsets.
        supports: Support per family.
        selections: Per family, the inclusion vote it was completed from.
    """

    blocks: np.ndarray
    supports: np.ndarray
    selections: tuple[dict[int, float], ...]

    def rows(self) -> list[tuple[int, float]]:
        """The ``(size, support)`` rows the floors are solved from.

        Returns:
            One row per family.
        """
        if not len(self.blocks):
            return []
        sizes = np.bitwise_count(self.blocks).sum(axis=1).astype(np.int64)
        return [(int(s), round(float(v), SUPPORT_DECIMALS))
                for s, v in zip(sizes, self.supports, strict=True)]


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


def cut_key(cap: int, cutoff: float) -> str:
    """Directory name for one (cap, cutoff) cut.

    Args:
        cap: Size cap in pathways.
        cutoff: Inclusion cutoff.

    Returns:
        A name that changes whenever either parameter does, so a new cut never overwrites an old
        one and an old one stays reproducible.
    """
    return f"cap{cap}_inc{int(round(cutoff * 100)):03d}"


def save_material(path: Path, material: Material) -> int:
    """Persist one side's completed families.

    The inclusion votes are stored CSR-style rather than as JSON objects: there is one entry per
    (family, candidate pathway) pair, which at 200 runs is millions of pairs.

    Args:
        path: Destination ``.npz``.
        material: What to write.

    Returns:
        Bytes written.
    """
    indptr = np.zeros(len(material.selections) + 1, dtype=np.int64)
    idx: list[int] = []
    val: list[float] = []
    for position, selection in enumerate(material.selections):
        for pathway, inclusion in selection.items():
            idx.append(pathway)
            val.append(inclusion)
        indptr[position + 1] = len(idx)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".part.npz")
    np.savez_compressed(
        part,
        blocks=material.blocks,
        supports=material.supports,
        sel_indptr=indptr,
        sel_idx=np.asarray(idx, dtype=np.int32),
        sel_val=np.asarray(val, dtype=np.float64),
    )
    part.replace(path)
    return path.stat().st_size


def load_material(path: Path) -> Material:
    """Read back a persisted side.

    Args:
        path: The ``.npz`` written by :func:`save_material`.

    Returns:
        The side's material.
    """
    with np.load(path) as handle:
        indptr = handle["sel_indptr"]
        idx = handle["sel_idx"]
        val = handle["sel_val"]
        selections = tuple(
            dict(zip(idx[indptr[i]:indptr[i + 1]].tolist(),
                     val[indptr[i]:indptr[i + 1]].tolist(), strict=True))
            for i in range(len(indptr) - 1)
        )
        return Material(handle["blocks"], handle["supports"], selections)


def implementation_fingerprint(fast: bool, families: str = "joined") -> dict[str, object]:
    """What a cached side's bytes depend on, beyond the declared parameters.

    **This exists because of a real failure.** On 2 Oct a module edit landed while a long side-
    cutting loop was running. Each side is a fresh process, so it imported whatever
    ``recurrent.py`` said at the moment it started -- and one side was computed with an unverified
    matching change, producing 40,809 families where the same scramble gives roughly 450,000. The
    file looked exactly like a valid cache entry. Nothing recorded which code wrote it.

    Args:
        fast: Whether the vectorised completion is in use.
        families: Which families implementation is in use.

    Returns:
        The fingerprint to store beside a side and to check on a cache hit.
    """
    source = Path(recurrent.__file__).read_bytes()
    return {
        "recurrent_sha256_16": hashlib.sha256(source).hexdigest()[:16],
        "completion": "fast" if fast else "original",
        "families": families,
        "matching": str(DEFAULTS.get("matching", "matrix")),
        "size_filter": bool(DEFAULTS.get("size_filter", False)),
        "theta": THETA,
        "tol": TOL,
        "min_size": MIN_SIZE,
    }


def cut_side(
    trees: Path,
    labels: Sequence[str],
    n: int,
    cap: int,
    cutoff: float,
    fast: bool = False,
    report: dict | None = None,
    families_mode: str = "joined",
) -> Material:
    """Cut one side and complete every grouping, BEFORE any support gate.

    Args:
        trees: The tree directory.
        labels: Tree file stems, in run order.
        n: Universe size.
        cap: Size cap, applied to every tree.
        cutoff: Inclusion cutoff for completion.
        fast: Use the vectorised completion. Byte-identical to the original by test; see
            :func:`thema.ontology.recurrent.family_members_fast`.
        families_mode: Which families implementation to use. ``"joined"`` is verified
            byte-identical to ``"indexed"`` at both scales; see DECISIONS.md, 2 Oct.
        report: If given, filled with per-stage wall seconds. The stage split was not recoverable
            from any existing log -- ``prepare`` and ``score`` collect their own timings and nothing
            printed them -- so it is collected here.

    Returns:
        The side's completed families.
    """
    complete = family_members_fast if fast else family_members
    marks: dict[str, float] = {}
    clock = time.perf_counter()
    runs = [load_run(trees / f"{label}.npz", n, cap) for label in labels]
    marks["load trees + cap"] = time.perf_counter() - clock

    clock = time.perf_counter()
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE,
                "theta": THETA, "families": families_mode}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    marks["prepare (dedup + eligibility)"] = time.perf_counter() - clock
    marks.update({f"  .. {k}": v for k, v in ready.timing.stages.items()})

    clock = time.perf_counter()
    pool = score(ready, settings)
    marks["matching (support)"] = time.perf_counter() - clock
    marks.update({f"  .. {k}": v for k, v in pool.timing.stages.items()
                  if k not in ready.timing.stages})

    words = ready.present.shape[1] * bits.WORD
    clock = time.perf_counter()
    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = complete([grouping], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= cutoff)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
    marks["completion"] = time.perf_counter() - clock

    clock = time.perf_counter()
    grouped = families(list(completed), completed, pool, settings=settings)
    marks["families (seed absorption)"] = time.perf_counter() - clock

    clock = time.perf_counter()
    blocks, supports, selections = [], [], []
    for seed_grouping, family in grouped:
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        _candidate, selection = complete([seed_grouping], pool, ready.present, words)
        blocks.append(completed[seed_grouping])
        supports.append(float(support))
        selections.append(selection)
    marks["family support + selection"] = time.perf_counter() - clock

    if report is not None:
        report.update(marks)
        report["groupings"] = len(pool.groupings)
        report["eligible"] = int(np.count_nonzero(~np.isnan(pool.support)))
        report["completed"] = len(completed)
        report["families"] = len(blocks)
        report["completion_implementation"] = "fast" if fast else "original"
        report["families_implementation"] = families_mode
        report["peak_mb"] = round(peak_mb(), 1)
    stacked = (np.vstack(blocks) if blocks
               else np.zeros((0, ready.present.shape[1]), dtype=np.uint64))
    return Material(stacked, np.asarray(supports, dtype=np.float64), tuple(selections))


def side_cached(
    trees: Path,
    labels: Sequence[str],
    n: int,
    cap: int,
    cutoff: float,
    label: str,
    fast: bool = False,
    families_mode: str = "joined",
    allow_stale: bool = False,
) -> tuple[Material, bool]:
    """Cut one side, or read it back if this exact cut is already on disk.

    Args:
        trees: The tree directory.
        labels: Tree file stems, in run order.
        n: Universe size.
        cap: Size cap.
        cutoff: Inclusion cutoff.
        label: Side name, e.g. ``real200`` or ``seed03001``.
        fast: Use the vectorised completion.
        families_mode: Which families implementation to use.
        allow_stale: Reuse a cached side written by a different implementation. Only legitimate
            when the two have been proved byte-identical; the mismatch is still printed.

    Returns:
        The material, and whether it came from disk.

    Raises:
        FileNotFoundError: If a tree this side needs is not persisted.
    """
    path = trees / "completions" / cut_key(cap, cutoff) / f"{label}.npz"
    mark = path.with_suffix(".provenance.json")
    if path.is_file():
        want = implementation_fingerprint(fast, families_mode)
        if not mark.is_file():
            print(f"    WARNING {label}: cached before provenance was recorded; cannot prove "
                  f"which code wrote it", flush=True)
        else:
            got = json.loads(mark.read_text())
            differs = {k: (got.get(k), want[k]) for k in want if got.get(k) != want[k]}
            if differs and not allow_stale:
                raise RuntimeError(
                    f"{label} was cached by a DIFFERENT implementation and will not be reused: "
                    + "; ".join(f"{k} was {a!r}, now {b!r}" for k, (a, b) in differs.items())
                    + ". Delete it and recut, or pass --allow-stale-cache if the two have been "
                    "proved byte-identical."
                )
            if differs:
                # Printed every time, never suppressed: reusing a side written by other code is
                # only sound because the two were proved byte-identical, and the claim should be
                # visible in the log of any run that relies on it.
                print(f"    --allow-stale-cache: reusing {label} across an implementation change ("
                      + "; ".join(f"{k} {a!r} -> {b!r}" for k, (a, b) in differs.items())
                      + "), proved byte-identical; see DECISIONS.md 2 Oct", flush=True)
        return load_material(path), True
    missing = [lab for lab in labels if not (trees / f"{lab}.npz").is_file()]
    if missing:
        raise FileNotFoundError(f"{label}: {len(missing)} trees not persisted, e.g. {missing[0]}")
    report: dict = {}
    material = cut_side(trees, labels, n, cap, cutoff, fast=fast, report=report,
                        families_mode=families_mode)
    save_material(path, material)
    mark.write_text(
        json.dumps(implementation_fingerprint(fast, families_mode), indent=2) + "\n",
        encoding="utf-8",
    )
    stages = path.with_suffix(".stages.json")
    stages.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    timed = {k: v for k, v in report.items() if isinstance(v, float) and k != "peak_mb"}
    width = max(len(k) for k in timed)
    for stage, seconds in timed.items():
        print(f"      {stage:<{width}} {seconds:8.1f}s", flush=True)
    total = sum(v for k, v in timed.items() if not k.startswith("  "))
    print(f"      {'TOTAL':<{width}} {total:8.1f}s   peak "
          f"{report.get('peak_mb', 0):.0f} MB", flush=True)
    return material, False


def solve(
    real: Sequence[tuple[int, float]], nulls: Sequence[Sequence[tuple[int, float]]]
) -> list[dict]:
    """Solve one floor per stratum at :data:`MAX_FDR_OVERALL`.

    Args:
        real: The real side's rows.
        nulls: One list of rows per calibration scramble.

    Returns:
        Per stratum: bounds, the solved floor, the effective threshold and the counts behind it.
    """
    out = []
    for index, (low, high) in enumerate(STRATA):
        r = [s for size, s in real if stratum_of(size) == index]
        per = [[s for size, s in rows if stratum_of(size) == index] for rows in nulls]
        chosen: tuple[float | None, float, int] = (None, 0.0, 0)
        for c in sorted({s for rows in per for s in rows}):
            f = sum(sum(1 for s in rows if s >= c) for rows in per) / max(len(per), 1)
            keep = sum(1 for s in r if s >= c)
            if keep and f / keep <= MAX_FDR_OVERALL:
                chosen = (c, f, keep)
                break
        if chosen[0] is None:
            total = sum(len(rows) for rows in per) / max(len(per), 1)
            chosen = (0.0, total, len(r)) if total == 0 else (None, total, len(r))
        floor, f_at, r_at = chosen
        out.append({
            "stratum": f"{low}-{high}" if high < 10**9 else f"{low}+",
            "real": len(r),
            "floor": floor,
            "effective": None if floor is None else max(DECLARED_M, floor),
            "calibration_fdr": None if floor is None or not r_at else round(f_at / r_at, 5),
        })
    return out


def confirm(
    real: Sequence[tuple[int, float]],
    nulls: Sequence[Sequence[tuple[int, float]]],
    solved: Sequence[dict],
) -> dict:
    """Apply the solved floors ONCE to the held-out scrambles.

    Nothing is re-solved after this, by declaration: a floor adjusted against the held-out set is
    not a held-out set.

    Args:
        real: The real side's rows.
        nulls: One list of rows per held-out scramble.
        solved: Output of :func:`solve`.

    Returns:
        Per-stratum held-out rates and the overall rate.
    """
    per, total_f, total_r = [], 0.0, 0.0
    for index, entry in enumerate(solved):
        threshold = entry["effective"]
        if threshold is None:
            per.append({**entry, "heldout_fdr": None, "heldout_real": 0})
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
    return {
        "strata": per,
        "overall_fdr": round(total_f / total_r, 5) if total_r else None,
        "overall_real": int(total_r),
        "overall_null": round(total_f, 2),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the confirmatory build.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=0,
                        help="shorthand for --rows 1-N")
    parser.add_argument("--rows", default="",
                        help="1-based inclusive block of persisted trees, e.g. 101-200")
    parser.add_argument("--scramble-rows", type=int, default=0,
                        help="trees per scramble side; defaults to the build's own run count, "
                             "which is what the declaration requires")
    parser.add_argument("--confirm-heldout", action="store_true",
                        help="read the 5 held-out scrambles. THE CONFIRMATORY BUILD ONLY -- a "
                             "held-out set confirmed against more than once is not held out")
    parser.add_argument("--floors-from", type=Path, default=None,
                        help="load floors from a stored floors.json instead of cutting the 10 "
                             "calibration scramble sides. The floors are a property of the null at "
                             "a given (space, universe, cap, cutoff, run count), so re-deriving "
                             "them for an identical configuration recomputes a constant")
    parser.add_argument("--check-heldout", type=int, default=0,
                        help="with --floors-from, cut ONE held-out scramble side of this seed and "
                             "report its FDR against the stored floors. A cheap standing check "
                             "that the stored null still describes this configuration")
    parser.add_argument("--allow-stale-cache", action="store_true",
                        help="reuse a cached side written by a different implementation. ONLY "
                             "after the two have been proved byte-identical")
    parser.add_argument("--cut-side", default="",
                        help="cut exactly ONE side into the completion cache and exit, so sides "
                             "can be fanned out across processes within a memory budget")
    parser.add_argument("--families", choices=("indexed", "joined"), default="joined",
                        help="'joined' is the exact set-similarity join, verified byte-identical "
                             "at both scales; see DECISIONS.md 2 Oct")
    parser.add_argument("--completion", choices=("original", "fast"), default="original",
                        help="'fast' is the vectorised completion, verified byte-identical; see "
                             "DECISIONS.md 2 Oct")
    parser.add_argument("--directory", default="")
    parser.add_argument("--dry-run", action="store_true",
                        help="solve the floors, then stop before the gate")
    args = parser.parse_args(argv)

    if bool(args.rows) == bool(args.runs):
        parser.error("give exactly one of --rows A-B or --runs N")
    if args.runs:
        first, last = 1, args.runs
    else:
        low, _, high = args.rows.partition("-")
        first, last = int(low), int(high or low)
    if first < 1 or last < first:
        parser.error(f"bad row range {args.rows or args.runs!r}")
    runs = last - first + 1
    scramble_rows = args.scramble_rows or runs
    directory = args.directory or f"recurrent_dag_10770_r{first}-{last}"

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    print(f"BUILD  {n:,} pathways, {args.space}, cap {CAP_SHARE:.4%} = {cap:,}, "
          f"inclusion {INCLUSION_CUT}, trees {first}-{last} ({runs} runs), "
          f"scramble sides {scramble_rows} trees, completion {args.completion}, "
          f"families {args.families}", flush=True)
    print(f"  completions -> {trees / 'completions' / cut_key(cap, INCLUSION_CUT)}", flush=True)
    print(f"  -> {root / directory}", flush=True)

    if args.cut_side:
        from verify_completion import labels_for
        clock = time.perf_counter()
        material, got = side_cached(
            trees, labels_for(args.cut_side, runs), n, cap, INCLUSION_CUT, args.cut_side,
            fast=args.completion == "fast", families_mode=args.families,
            allow_stale=args.allow_stale_cache,
        )
        print(f"  {args.cut_side}: {len(material.blocks):,} families "
              f"({'cached' if got else f'{time.perf_counter() - clock:.0f}s'})", flush=True)
        return 0

    clock = time.perf_counter()
    real, cached = side_cached(
        trees, [f"row{r:05d}" for r in range(first, last + 1)], n, cap, INCLUSION_CUT,
        f"real_r{first:05d}-{last:05d}", fast=args.completion == "fast",
        families_mode=args.families, allow_stale=args.allow_stale_cache,
    )
    print(f"  real side: {len(real.blocks):,} families "
          f"({'cached' if cached else f'{time.perf_counter() - clock:.0f}s'})", flush=True)

    # The scramble side's RUN COUNT is part of its cache key: a floor for a 200-run build must
    # come from a 200-run null, and a 100-run side under the same name would silently supply the
    # wrong one.
    # With stored floors the calibration sides are not cut AT ALL -- that is the whole point of
    # --floors-from. The first version loaded the floors but still cut all ten sides first, which
    # saved nothing; the provenance guard caught it by refusing sides written by older code.
    wanted = [] if args.floors_from is not None else [("calibration", CALIBRATION_SEEDS)]
    if args.confirm_heldout:
        wanted.append(("held-out", HELDOUT_SEEDS))
    cal, held = [], []
    for which, seeds in wanted:
        into = cal if which == "calibration" else held
        for seed in seeds:
            start = time.perf_counter()
            material, got = side_cached(
                trees, [f"seed{seed:05d}_row{r:05d}" for r in range(1, scramble_rows + 1)],
                n, cap, INCLUSION_CUT, f"seed{seed:05d}_n{scramble_rows:03d}",
                fast=args.completion == "fast", families_mode=args.families,
                allow_stale=args.allow_stale_cache,
            )
            into.append(material.rows())
            print(f"  {which} {seed}: {len(material.blocks):,} families "
                  f"({'cached' if got else f'{time.perf_counter() - start:.0f}s'})", flush=True)

    real_rows = real.rows()
    if args.floors_from is not None:
        stored = json.loads(args.floors_from.read_text())
        # The floors only transfer to an IDENTICAL configuration. Anything else and the stored
        # null is describing a different population, so this refuses rather than warning.
        want = {"n": n, "runs": runs, "scramble_rows": scramble_rows,
                "size_cap": cap, "inclusion_cut": INCLUSION_CUT,
                "universe_digest": universe, "space": args.space}
        differs = {k: (stored.get(k), v) for k, v in want.items() if stored.get(k) != v}
        if differs:
            print("  STORED FLOORS DO NOT APPLY to this configuration and will not be used: "
                  + "; ".join(f"{k} stored {a!r}, now {b!r}" for k, (a, b) in differs.items()))
            return 1
        solved = [
            {"stratum": e["stratum"], "real": e["real"], "floor": e["floor"],
             "effective": e["effective"], "calibration_fdr": e.get("calibration_fdr")}
            for e in stored["strata"]
        ]
        print(f"  floors LOADED from {args.floors_from}")
        print(f"    calibration seeds {stored.get('calibration_seeds')}, "
              f"solved at FDR <= {MAX_FDR_OVERALL}")
        print("    effective thresholds: "
              + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved))
    else:
        solved = solve(real_rows, cal)
    confirmed = confirm(real_rows, held, solved) if args.confirm_heldout else None
    checked = None
    if args.check_heldout:
        # ONE held-out side, against the floors as loaded. This is a check, not a calibration:
        # nothing is re-solved from it, so it cannot launder a stored floor into a fitted one.
        start = time.perf_counter()
        side, got = side_cached(
            trees,
            [f"seed{args.check_heldout:05d}_row{r:05d}"
             for r in range(1, scramble_rows + 1)],
            n, cap, INCLUSION_CUT,
            f"seed{args.check_heldout:05d}_n{scramble_rows:03d}",
            fast=args.completion == "fast", families_mode=args.families,
            allow_stale=args.allow_stale_cache,
        )
        checked = confirm(real_rows, [side.rows()], solved)
        print(f"\n  HELD-OUT CHECK, seed {args.check_heldout} "
              f"({'cached' if got else f'{time.perf_counter() - start:.0f}s'}): "
              f"overall FDR {checked['overall_fdr']} against {MAX_FDR_OVERALL}")
        for entry in checked["strata"]:
            print(f"    {entry['stratum']:<9} held FDR {str(entry.get('heldout_fdr')):>9} "
                  f"(real {entry.get('heldout_real', 0):,}, null {entry.get('heldout_null', 0)})")
        bad_check = [e["stratum"] for e in checked["strata"]
                     if e.get("heldout_fdr") is not None
                     and e["heldout_fdr"] > MAX_FDR_STRATUM]
        verdict = (checked["overall_fdr"] is not None
                   and checked["overall_fdr"] <= MAX_FDR_OVERALL and not bad_check)
        print(f"  CHECK {'PASSES' if verdict else 'FAILS'}"
              + (f" -- strata over {MAX_FDR_STRATUM}: {bad_check}" if bad_check else "")
              + "  (nothing re-solved from it)")
    report = {
        "space": args.space, "universe_digest": universe, "n": n,
        "rows": f"{first}-{last}", "runs": runs, "scramble_rows": scramble_rows,
        "size_cap_share": CAP_SHARE, "size_cap": cap, "inclusion_cut": INCLUSION_CUT,
        "declared_m": DECLARED_M,
        "strata": confirmed["strata"] if confirmed else solved,
        "calibration_seeds": list(CALIBRATION_SEEDS),
        "heldout_confirmed": bool(args.confirm_heldout),
        "floors_from": str(args.floors_from) if args.floors_from else None,
        "heldout_check_seed": args.check_heldout or None,
        "heldout_check": checked,
        "heldout_seeds": list(HELDOUT_SEEDS) if args.confirm_heldout else [],
        "overall_fdr": confirmed["overall_fdr"] if confirmed else None,
        "overall_real": confirmed["overall_real"] if confirmed else None,
        "overall_null": confirmed["overall_null"] if confirmed else None,
    }
    print(f"\n  {'stratum':<9} {'real':>7} {'floor':>10} {'effective':>10} "
          f"{'cal FDR':>9} {'held FDR':>9}")
    for entry in report["strata"]:
        fl = "none" if entry["floor"] is None else f"{entry['floor']:.6f}"
        ef = "DROP" if entry["effective"] is None else f"{entry['effective']:.6f}"
        print(f"  {entry['stratum']:<9} {entry['real']:>7,} {fl:>10} {ef:>10} "
              f"{str(entry['calibration_fdr']):>9} {str(entry.get('heldout_fdr')):>9}")
    out = (trees / "completions" / cut_key(cap, INCLUSION_CUT)
           / f"floors_r{first}-{last}_n{scramble_rows}.json")
    # NO-OVERWRITE. A floors file is a calibration record, and a run that LOADED its floors has
    # nothing new to say about them -- writing anyway destroyed the held-out confirmation stored in
    # this very file once, replacing overall_fdr 0.00285 with null. A run that solved its own floors
    # may still write, and only where no file exists.
    if args.floors_from is not None:
        print(f"  floors NOT rewritten: they were loaded, not solved ({out.name} left as it was)")
    elif out.exists():
        print(f"  floors NOT rewritten: {out} already exists and is a calibration record")
    else:
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  floors -> {out}")

    if args.confirm_heldout:
        print(f"\n  overall held-out FDR {report['overall_fdr']} against {MAX_FDR_OVERALL}")
        bad = [e for e in report["strata"]
               if e.get("heldout_fdr") is not None and e["heldout_fdr"] > MAX_FDR_STRATUM]
        if report["overall_fdr"] is None or report["overall_fdr"] > MAX_FDR_OVERALL or bad:
            print(f"  ERROR CAPS NOT MET -- overall {report['overall_fdr']}, "
                  f"strata over {MAX_FDR_STRATUM}: {[e['stratum'] for e in bad]}")
            print("  NOTHING FROZEN. Nothing re-solved.", flush=True)
            return 1
    else:
        print("\n  held-out NOT read: this is a ladder block, and the held-out set is confirmed "
              "against\n  exactly once, by the confirmatory build.", flush=True)

    if args.dry_run:
        print("\n  --dry-run: stopping before the gate")
        return 0

    # From here on nothing is cut again: the gate, the consensus and the Hasse pass all run off the
    # persisted real-side material.
    thresholds = {index: entry["effective"] for index, entry in enumerate(report["strata"])}
    # A stratum whose floor could not be solved is INADMISSIBLE: no support level in it reaches the
    # declared FDR, so nothing in it passes. Comparing a support against None used to raise, which
    # is how the TF-IDF control arm crashed instead of reporting that every stratum was dropped.
    dropped = [report["strata"][i]["stratum"] for i, t in thresholds.items() if t is None]
    if dropped:
        print(f"  STRATA DROPPED, no floor meets FDR {MAX_FDR_OVERALL} in them: "
              f"{', '.join(dropped)}", flush=True)
        print("  Nothing in a dropped stratum can pass the gate.", flush=True)
    sizes = np.bitwise_count(real.blocks).sum(axis=1).astype(np.int64)
    gated = [
        (real.blocks[i], float(real.supports[i]), real.selections[i])
        for i in range(len(real.blocks))
        if thresholds[stratum_of(int(sizes[i]))] is not None
        and round(float(real.supports[i]), SUPPORT_DECIMALS)
        >= thresholds[stratum_of(int(sizes[i]))]
    ]
    print(f"  families through the gate: {len(gated):,} of {len(real.blocks):,}", flush=True)
    if not gated:
        print("  NO FAMILY PASSES THE GATE. This arm produces no ontology: its scrambled nulls\n"
              "  yield recurrent families as readily as its real data, at every support level and\n"
              "  in every size stratum. Writing the empty result rather than failing, because\n"
              "  an arm indistinguishable from its own null IS the measurement.", flush=True)

    words = real.blocks.shape[1] * bits.WORD
    verdict = consensus(
        [b for b, _s, _i in gated], [s for _b, s, _i in gated], [i for _b, _s, i in gated],
        words, stray=DEFAULT_STRAY, jaccard=DEFAULT_JACCARD,
    )
    kept = [
        (verdict.members[i], gated[c][1], gated[c][2]) for i, c in enumerate(verdict.accepted)
    ]
    print(f"  after consensus: {len(kept):,} nodes, {len(verdict.superseded)} superseded",
          flush=True)

    parents_of = hasse([b for b, _s, _i in kept])
    ids = [f"n{i:05d}" for i in range(len(kept))]
    nodes = tuple(
        Node(
            id=ids[i],
            parents=tuple(ids[p] for p in parents_of[i]),
            members=tuple(
                (keys[p], round(float(inc.get(p, 1.0)), 4)) for p in sorted(bits.unpack(block))
            ),
            support=round(sup, 6),
        )
        for i, (block, sup, inc) in enumerate(kept)
    )
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    root_only = tuple(sorted(placed - in_nonroot))
    print(f"  nodes {len(nodes):,}  roots {len(roots):,}  placed {len(placed):,}  "
          f"unplaced {len(unplaced):,}  root-only {len(root_only):,}  "
          f"effectively unplaced {len(unplaced) + len(root_only):,}", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    settings = {**DEFAULTS, "runs": runs, "tol": TOL, "min_size": MIN_SIZE, "theta": THETA}
    manifest = {
        "space": f"{args.space}-renormalised",
        "universe_digest": universe,
        "n": n,
        "rows": f"{first}-{last}",
        "runs": runs,
        "scramble_rows": scramble_rows,
        "heldout_confirmed": bool(args.confirm_heldout),
        "theta": THETA,
        "tol": TOL,
        "min_size": MIN_SIZE,
        "inclusion_threshold": INCLUSION_CUT,
        "declared_m": DECLARED_M,
        "size_cap_share": CAP_SHARE,
        "size_cap": cap,
        "size_cap_rule": "2x the largest curated top-level share, excluding Reactome Disease",
        "completion_implementation": args.completion,
        "families_implementation": args.families,
        "floors": [[e["stratum"], e["floor"], e["effective"]] for e in report["strata"]],
        "calibration": (
            f"{len(CALIBRATION_SEEDS)} calibration scrambles, seeds "
            f"{CALIBRATION_SEEDS[0]}-{CALIBRATION_SEEDS[-1]}, {scramble_rows} trees each"
            + (f"; {len(HELDOUT_SEEDS)} held-out, seeds {HELDOUT_SEEDS[0]}-"
               f"{HELDOUT_SEEDS[-1]}, overall held-out FDR {report['overall_fdr']}"
               if args.confirm_heldout else "; held-out NOT read (ladder block)")
        ),
        "completions": str(trees / "completions" / cut_key(cap, INCLUSION_CUT)),
        "n_unplaced": len(unplaced),
        "n_root_only": len(root_only),
        "n_effectively_unplaced": len(unplaced) + len(root_only),
        "descriptions_digest": meta.get("descriptions_digest", ""),
    }
    ontology = Ontology(
        method="recurrent_dag",
        params={**settings, "m": "per-size, see manifest.floors"},
        nodes=nodes,
        unplaced=unplaced,
        manifest=manifest,
    )
    export.write(ontology, args.data / "ontology", args.version, genes, manifest,
                 dry_run=False, info=info, directory=directory)
    print(f"  -> {root / directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
