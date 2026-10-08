#!/usr/bin/env python3
"""Run THEMA v0.4: calibrate once, build, and prove byte identity against the frozen v0.3.

This is the driver for :mod:`thema.ontology.v04`. It supplies the two things that module
deliberately does not import -- the floor solver and the held-out checker from
``scripts/build_10770.py`` -- loads the persisted trees, and writes the build.

Three modes:

``--all-stages-on --verify``
    The byte-identity proof. Restores every removed stage, cuts the real side with v0.3's size
    cap, builds, and compares the four tables against ``data/ontology/v0.3/recurrent_dag_10770``
    row by row. Any difference means this file is a reimplementation rather than a simplification,
    and the run fails. Nothing is written unless ``--write`` is given.

``--calibrate``
    Solve the per-size floors once from three calibration scrambles and confirm them once on the
    two held-out scrambles, then store them. Floors are a property of the space and the universe,
    not of a build, which is why they are stored rather than recomputed.

(default)
    Build v0.4 from the stored floors into ``data/ontology/v0.4/thema_10770/``.

Usage::

    uv run scripts/v04_run.py --all-stages-on --verify
    uv run scripts/v04_run.py --calibrate
    uv run scripts/v04_run.py
    uv run scripts/v04_run.py --rows 1-100 --directory thema_10770_r1-100
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Three calibration scrambles and the two held-out seeds, as the v0.4 brief names them.
CALIBRATION = (3001, 3002, 3003)
HELDOUT = (4001, 4002)
#: The frozen build the byte-identity test compares against.
FROZEN = "recurrent_dag_10770"
#: The tables that must match row for row. The manifest is excluded on purpose: it records the
#: method name and the provenance fingerprint, which differ by design.
TABLES = ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv")


def save_side(path: Path, got: object) -> None:
    """Cache one side, inclusion votes included, CSR-style.

    The votes are stored as three flat arrays rather than as JSON objects because there is one
    entry per member per candidate -- about 4 million at 200 runs -- and a dict per candidate is
    both slower to load and far larger on disk.

    Args:
        path: Destination ``.npz``.
        got: The material to store.
    """
    indptr = np.zeros(len(got.selections) + 1, dtype=np.int64)
    keys: list[int] = []
    vals: list[float] = []
    for position, selection in enumerate(got.selections):
        for pathway, inclusion in selection.items():
            keys.append(int(pathway))
            vals.append(float(inclusion))
        indptr[position + 1] = len(keys)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path, blocks=got.blocks, supports=got.supports, indptr=indptr,
        vote_keys=np.asarray(keys, dtype=np.int64),
        vote_vals=np.asarray(vals, dtype=np.float64))


def load_side(trees: Path, labels: list[str], n: int, cap: int, cached: Path | None,
              *, need_votes: bool = False) -> object:
    """Material for one side, from cache when the cache is the same computation.

    Args:
        trees: Tree directory.
        labels: Tree stems in run order.
        n: Universe size.
        cap: Size cap in pathways, or a large number for no cap.
        cached: An ``.npz`` to read, or write to after computing; None to always compute.
        need_votes: Refuse a cache that stored no inclusion votes.

    Returns:
        A :class:`~thema.ontology.v04.Material`.
    """
    from cut_trees import load_run
    from thema.ontology.v04 import Material, material

    if cached is not None and cached.is_file():
        with np.load(cached) as handle:
            votes: tuple[dict[int, float], ...] = ()
            if "indptr" in handle:
                indptr, vkeys, vvals = handle["indptr"], handle["vote_keys"], handle["vote_vals"]
                votes = tuple(
                    dict(zip(vkeys[indptr[i]:indptr[i + 1]].tolist(),
                             vvals[indptr[i]:indptr[i + 1]].tolist(), strict=True))
                    for i in range(len(indptr) - 1))
            if votes or not need_votes:
                return Material(blocks=handle["blocks"], supports=handle["supports"],
                                selections=votes)
            print(f"  {cached.name} holds no inclusion votes; recomputing", flush=True)
    runs = [load_run(trees / f"{label}.npz", n, cap) for label in labels]
    got = material(runs, n, legacy=cap < 10**8)
    if cached is not None:
        save_side(cached, got)
    return got


def compare(built: Path, frozen: Path) -> list[str]:
    """Row-by-row differences between two built directories.

    Args:
        built: The directory just written.
        frozen: The reference directory.

    Returns:
        Human-readable differences; empty means identical.
    """
    out: list[str] = []
    for name in TABLES:
        left, right = built / name, frozen / name
        if not right.is_file():
            out.append(f"{name}: missing from the reference")
            continue
        a = left.read_text(encoding="utf-8").splitlines()
        b = right.read_text(encoding="utf-8").splitlines()
        if a == b:
            continue
        if len(a) != len(b):
            out.append(f"{name}: {len(a):,} rows against {len(b):,}")
            continue
        bad = [i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]
        out.append(f"{name}: {len(bad):,} of {len(a):,} rows differ, first at line {bad[0] + 1}")
    return out


def main(argv: list[str] | None = None) -> int:
    """Calibrate, build or verify v0.4.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status; non-zero when a verification fails.
    """
    from build_10770 import INCLUSION_CUT, confirm, side_cached, solve
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3", help="where the trees and universe live")
    parser.add_argument("--out-version", default="0.4")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--rows", default="", help="e.g. 1-100 for a stability half")
    parser.add_argument("--directory", default="")
    parser.add_argument("--all-stages-on", action="store_true",
                        help="restore every removed stage; for the byte-identity proof")
    parser.add_argument("--verify", action="store_true",
                        help="compare the build against the frozen v0.3 and fail on a difference")
    parser.add_argument("--calibrate", action="store_true",
                        help="solve and store the floors, then stop")
    parser.add_argument("--write", action="store_true",
                        help="with --verify, also keep the directory that was built")
    parser.add_argument("--match-themes", type=int, default=0,
                        help="keep only the N highest-support themes, to match another build's "
                             "theme count; recorded in the manifest as a post hoc cut")
    args = parser.parse_args(argv)

    legacy = args.all_stages_on
    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = v04.cap_for(n) if legacy else v04.NO_CAP
    store = args.data / "ontology" / f"v{args.out_version}" / "calibration"
    store.mkdir(parents=True, exist_ok=True)
    floors_file = store / ("floors_all_stages_on.json" if legacy else "floors.json")

    first, last = (1, args.runs)
    if args.rows:
        low, _, high = args.rows.partition("-")
        first, last = int(low), int(high or low)
    half = bool(args.rows)

    def real_labels() -> list[str]:
        """Tree stems for the real side."""
        return [f"row{r:05d}" for r in range(first, last + 1)]

    def scramble_labels(seed: int) -> list[str]:
        """Tree stems for one scramble side."""
        return [f"seed{seed:05d}_row{r:05d}" for r in range(1, args.runs + 1)]

    # v0.4's side material is the same computation as the no_size_cap ablation's: side material
    # reads only completion, absorption and the cap, and v0.4 differs from that ablation only in
    # STRAY and containment, neither of which enters it. So the SCRAMBLE sides are reused from that
    # cache -- floor solving reads only (size, support), which is all that cache holds. The REAL
    # side is recomputed and cached here instead, because the build needs the inclusion votes and
    # the ablation chain never stored them.
    reuse = args.data / "ontology" / "v0.3" / "ablate" / "no_size_cap"

    clock = time.perf_counter()
    if legacy:
        # COMPUTE the side through v04.material rather than reading the frozen cache, then compare
        # against the cache. Reading the cache here would make the byte-identity test a test of the
        # gate and consensus only, leaving the matching, completion and absorption in this module
        # unproven -- which is most of it, and the part the stage-order bug was in.
        real = load_side(trees, real_labels(), n, cap,
                         None if half else store / "real_all_stages_on.npz", need_votes=True)
        got, _cached = side_cached(
            trees, real_labels(), n, cap, INCLUSION_CUT,
            f"real_r{first:05d}-{last:05d}", fast=True, families_mode="joined", allow_stale=True)
        same_rows = len(got.supports) == len(real.supports)
        same = same_rows and bool(np.array_equal(
            np.sort(real.blocks.view([("", real.blocks.dtype)] * real.blocks.shape[1]), axis=0),
            np.sort(got.blocks.view([("", got.blocks.dtype)] * got.blocks.shape[1]), axis=0)))
        print(f"  material against the frozen side: {len(real.supports):,} candidates against "
              f"{len(got.supports):,}  membership {'IDENTICAL' if same else 'DIFFERS'}", flush=True)
        if not same:
            print("  FAILED at the material stage; the build comparison would be meaningless.",
                  flush=True)
            return 1
    else:
        real = load_side(trees, real_labels(), n, cap,
                         None if half else store / "real.npz", need_votes=True)
    elapsed = time.perf_counter() - clock
    print(f"real side: {len(real.supports):,} candidate themes  ({elapsed:.0f}s)", flush=True)

    if args.calibrate:
        cal = [load_side(trees, scramble_labels(s), n, cap, reuse / f"seed{s:05d}.npz")
               for s in CALIBRATION]
        held = [load_side(trees, scramble_labels(s), n, cap, reuse / f"seed{s:05d}.npz")
                for s in HELDOUT]
        done = v04.calibrate(real, cal, held, solve, confirm)
        record = {"method": "v0.4-legacy-all-stages" if legacy else "v0.4",
                  "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
                  "reused_sides_from": str(reuse) if not legacy else None,
                  "universe_digest": universe, "n": n,
                  "size_cap": cap if legacy else None, **done,
                  "seconds": round(time.perf_counter() - clock, 1)}
        floors_file.write_text(json.dumps(record, indent=2, default=float) + "\n",
                               encoding="utf-8")
        print("  floors " + ", ".join(
            f"{e['stratum']}:{e['effective']}" for e in done["solved"]))
        print(f"  held-out FDR {done['confirmed']['overall_fdr']} on {list(HELDOUT)}")
        print(f"  -> {floors_file}", flush=True)
        return 0

    if legacy:
        # Byte identity means the SAME gate, so the floors must be v0.3's own, read from the frozen
        # manifest, not freshly solved ones. The frozen build stores them as
        # [stratum, floor, effective] triples rather than as the dicts the gate takes.
        frozen_manifest = json.loads(
            (args.data / "ontology" / "v0.3" / FROZEN / "manifest.json").read_text())
        solved = [{"stratum": stratum, "floor": floor, "effective": effective}
                  for stratum, floor, effective in frozen_manifest["floors"]]
        floors_file = args.data / "ontology" / "v0.3" / FROZEN / "manifest.json"
        print("  gate: v0.3's own floors from the frozen manifest  "
              + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved), flush=True)
    else:
        if not floors_file.is_file():
            parser.error(f"no floors at {floors_file}; run --calibrate first")
        solved = json.loads(floors_file.read_text())["solved"]

    clock = time.perf_counter()
    built = v04.build(real, solved, legacy=legacy)
    if args.match_themes and args.match_themes < len(built.members):
        # A post hoc cut for one comparison only: the same build, truncated to the highest-support
        # themes so a theme-count difference cannot be mistaken for a quality difference. The DAG
        # is re-stacked over the survivors rather than inherited, because dropping a node without
        # recomputing edges would leave its children pointing at nothing.
        from thema.ontology.recurrent import hasse as restack

        order = sorted(range(len(built.members)), key=lambda i: -built.supports[i])
        keep_set = sorted(order[:args.match_themes])
        members = [built.members[i] for i in keep_set]
        built = v04.Built(
            members=members, supports=[built.supports[i] for i in keep_set],
            inclusions=[built.inclusions[i] for i in keep_set], parents=restack(members),
            superseded=built.superseded, gated=built.gated)
        print(f"  matched cut: kept the {len(members):,} highest-support themes", flush=True)
    print(f"  {built.gated:,} of {len(real.supports):,} through the gate; "
          f"{len(built.members):,} nodes after consensus "
          f"({built.superseded} superseded)  ({time.perf_counter() - clock:.0f}s)", flush=True)

    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    ids = [f"n{i:05d}" for i in range(len(built.members))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in built.parents[i]),
             members=tuple((keys[p], round(float(built.inclusions[i].get(p, 1.0)), 4))
                           for p in sorted(bits.unpack(block))),
             support=round(built.supports[i], 6))
        for i, block in enumerate(built.members))
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = sum(1 for node in nodes if len(node.parents) > 1)
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {"n_nodes": len(nodes), "n_roots": len(roots), "n_multi_parent": multi,
             "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
             "n_unplaced": len(unplaced), "n_root_only": len(placed - in_nonroot),
             "n_effectively_unplaced": len(unplaced) + len(placed - in_nonroot)}
    print(f"  nodes {shape['n_nodes']:,}  roots {shape['n_roots']:,}  "
          f"multi-parent {shape['multi_parent_share']:.1%}  "
          f"effectively unplaced {shape['n_effectively_unplaced']:,}", flush=True)

    directory = args.directory or (
        ("thema_10770_all_stages_on" if legacy else "thema_10770")
        + (f"_r{first}-{last}" if half else ""))
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {**v04.parameters(n, legacy=legacy), "n": n, "rows": f"{first}-{last}",
                "runs": last - first + 1, "floors": solved, "floors_file": str(floors_file),
                "universe_digest": universe, "kept_stage_reasons": [s.why for s in v04.STAGES],
                "reused_sides_from": None if legacy or half else str(reuse),
                "matched_theme_cut": args.match_themes or None,
                "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method=manifest["method"], params=manifest, nodes=nodes,
                 unplaced=unplaced, manifest=manifest),
        args.data / "ontology", args.out_version, genes, manifest,
        dry_run=False, info=info, directory=directory)
    print(f"  -> {written}  (peak {peak_mb():.0f} MB)", flush=True)

    if args.verify:
        frozen = args.data / "ontology" / "v0.3" / FROZEN
        bad = compare(Path(written), frozen)
        print(f"\nBYTE IDENTITY against {frozen}:", flush=True)
        if bad:
            for line in bad:
                print(f"  DIFFERS  {line}")
            print("  FAILED. v0.4 is a reimplementation, not a simplification.", flush=True)
            return 1
        for name in TABLES:
            print(f"  identical  {name}")
        print("  PASSED. With every stage on, v0.4 reproduces the frozen build exactly.",
              flush=True)
        if not args.write:
            import shutil
            shutil.rmtree(written, ignore_errors=True)
            print(f"  removed {written} (pass --write to keep it)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
