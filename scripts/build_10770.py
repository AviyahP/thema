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

Usage::

    uv run scripts/build_10770.py --runs 200 --dry-run
    uv run scripts/build_10770.py --runs 200
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from cut_trees import CAP_SHARE, MIN_SIZE, THETA, TOL, cap_for, load_run
from thema.data.pathways import PathwayCollection
from thema.ontology import bitset as bits
from thema.ontology import export
from thema.ontology.base import Node, Ontology
from thema.ontology.consensus import DEFAULT_JACCARD, DEFAULT_STRAY, consensus
from thema.ontology.recurrent import (
    DEFAULTS,
    families,
    family_members,
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


def cut_side(
    trees: Path, labels: Sequence[str], n: int, cap: int, cutoff: float
) -> Material:
    """Cut one side and complete every grouping, BEFORE any support gate.

    Args:
        trees: The tree directory.
        labels: Tree file stems, in run order.
        n: Universe size.
        cap: Size cap, applied to every tree.
        cutoff: Inclusion cutoff for completion.

    Returns:
        The side's completed families.
    """
    runs = [load_run(trees / f"{label}.npz", n, cap) for label in labels]
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE, "theta": THETA}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)
    words = ready.present.shape[1] * bits.WORD
    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members([grouping], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= cutoff)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
    blocks, supports, selections = [], [], []
    for seed_grouping, family in families(list(completed), completed, pool):
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        _candidate, selection = family_members([seed_grouping], pool, ready.present, words)
        blocks.append(completed[seed_grouping])
        supports.append(float(support))
        selections.append(selection)
    stacked = (np.vstack(blocks) if blocks
               else np.zeros((0, ready.present.shape[1]), dtype=np.uint64))
    return Material(stacked, np.asarray(supports, dtype=np.float64), tuple(selections))


def side_cached(
    trees: Path, labels: Sequence[str], n: int, cap: int, cutoff: float, label: str
) -> tuple[Material, bool]:
    """Cut one side, or read it back if this exact cut is already on disk.

    Args:
        trees: The tree directory.
        labels: Tree file stems, in run order.
        n: Universe size.
        cap: Size cap.
        cutoff: Inclusion cutoff.
        label: Side name, e.g. ``real200`` or ``seed03001``.

    Returns:
        The material, and whether it came from disk.

    Raises:
        FileNotFoundError: If a tree this side needs is not persisted.
    """
    path = trees / "completions" / cut_key(cap, cutoff) / f"{label}.npz"
    if path.is_file():
        return load_material(path), True
    missing = [lab for lab in labels if not (trees / f"{lab}.npz").is_file()]
    if missing:
        raise FileNotFoundError(f"{label}: {len(missing)} trees not persisted, e.g. {missing[0]}")
    material = cut_side(trees, labels, n, cap, cutoff)
    save_material(path, material)
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
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--directory", default="recurrent_dag_10770")
    parser.add_argument("--dry-run", action="store_true",
                        help="solve and confirm the floors, then stop before the gate")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    print(f"BUILD  {n:,} pathways, {args.space}, cap {CAP_SHARE:.4%} = {cap:,}, "
          f"inclusion {INCLUSION_CUT}, runs {args.runs}", flush=True)
    print(f"  completions -> {trees / 'completions' / cut_key(cap, INCLUSION_CUT)}", flush=True)

    clock = time.perf_counter()
    real, cached = side_cached(
        trees, [f"row{r:05d}" for r in range(1, args.runs + 1)], n, cap, INCLUSION_CUT,
        f"real{args.runs:03d}",
    )
    print(f"  real side: {len(real.blocks):,} families "
          f"({'cached' if cached else f'{time.perf_counter() - clock:.0f}s'})", flush=True)

    cal, held = [], []
    for which, seeds, into in (("calibration", CALIBRATION_SEEDS, cal),
                               ("held-out", HELDOUT_SEEDS, held)):
        for seed in seeds:
            start = time.perf_counter()
            material, got = side_cached(
                trees, [f"seed{seed:05d}_row{r:05d}" for r in range(1, 101)],
                n, cap, INCLUSION_CUT, f"seed{seed:05d}",
            )
            into.append(material.rows())
            print(f"  {which} {seed}: {len(material.blocks):,} families "
                  f"({'cached' if got else f'{time.perf_counter() - start:.0f}s'})", flush=True)

    real_rows = real.rows()
    solved = solve(real_rows, cal)
    report = confirm(real_rows, held, solved)
    report = {
        "space": args.space, "universe_digest": universe, "n": n, "runs": args.runs,
        "size_cap_share": CAP_SHARE, "size_cap": cap, "inclusion_cut": INCLUSION_CUT,
        "declared_m": DECLARED_M, "strata": report["strata"],
        "calibration_seeds": list(CALIBRATION_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "overall_fdr": report["overall_fdr"], "overall_real": report["overall_real"],
        "overall_null": report["overall_null"],
    }
    print(f"\n  {'stratum':<9} {'real':>7} {'floor':>10} {'effective':>10} "
          f"{'cal FDR':>9} {'held FDR':>9}")
    for entry in report["strata"]:
        fl = "none" if entry["floor"] is None else f"{entry['floor']:.6f}"
        ef = "DROP" if entry["effective"] is None else f"{entry['effective']:.6f}"
        print(f"  {entry['stratum']:<9} {entry['real']:>7,} {fl:>10} {ef:>10} "
              f"{str(entry['calibration_fdr']):>9} {str(entry.get('heldout_fdr')):>9}")
    print(f"\n  overall held-out FDR {report['overall_fdr']} against {MAX_FDR_OVERALL}")
    out = trees / "completions" / cut_key(cap, INCLUSION_CUT) / "floors.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"  floors -> {out}")
    bad = [e for e in report["strata"]
           if e.get("heldout_fdr") is not None and e["heldout_fdr"] > MAX_FDR_STRATUM]
    if report["overall_fdr"] is None or report["overall_fdr"] > MAX_FDR_OVERALL or bad:
        print(f"  ERROR CAPS NOT MET -- overall {report['overall_fdr']}, "
              f"strata over {MAX_FDR_STRATUM}: {[e['stratum'] for e in bad]}")
        print("  NOTHING FROZEN. Nothing re-solved.", flush=True)
        return 1

    if args.dry_run:
        print("\n  --dry-run: stopping before the gate")
        return 0

    # From here on nothing is cut again: the gate, the consensus and the Hasse pass all run off the
    # persisted real-side material.
    thresholds = {index: entry["effective"] for index, entry in enumerate(report["strata"])}
    sizes = np.bitwise_count(real.blocks).sum(axis=1).astype(np.int64)
    gated = [
        (real.blocks[i], float(real.supports[i]), real.selections[i])
        for i in range(len(real.blocks))
        if round(float(real.supports[i]), SUPPORT_DECIMALS) >= thresholds[stratum_of(int(sizes[i]))]
    ]
    print(f"  families through the gate: {len(gated):,} of {len(real.blocks):,}", flush=True)

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
    settings = {**DEFAULTS, "runs": args.runs, "tol": TOL, "min_size": MIN_SIZE, "theta": THETA}
    manifest = {
        "space": f"{args.space}-renormalised",
        "universe_digest": universe,
        "n": n,
        "runs": args.runs,
        "theta": THETA,
        "tol": TOL,
        "min_size": MIN_SIZE,
        "inclusion_threshold": INCLUSION_CUT,
        "declared_m": DECLARED_M,
        "size_cap_share": CAP_SHARE,
        "size_cap": cap,
        "size_cap_rule": "2x the largest curated top-level share, excluding Reactome Disease",
        "floors": [[e["stratum"], e["floor"], e["effective"]] for e in report["strata"]],
        "calibration": (
            f"{len(CALIBRATION_SEEDS)} calibration + {len(HELDOUT_SEEDS)} held-out scrambles, "
            f"seeds {CALIBRATION_SEEDS[0]}-{CALIBRATION_SEEDS[-1]} and "
            f"{HELDOUT_SEEDS[0]}-{HELDOUT_SEEDS[-1]}; overall held-out FDR "
            f"{report['overall_fdr']}"
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
                 dry_run=False, info=info, directory=args.directory)
    print(f"  -> {root / args.directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
