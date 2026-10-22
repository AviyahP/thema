#!/usr/bin/env python3
"""O50 with size strata above 10 (O50s). Declared 17 Oct 2026, before any result.

**This build adopts nothing by itself.** It is the frozen O50 configuration with **only the floors
changed**, which is why the gate's stratification is now a parameter rather than a constant.

Prompt 41 measured why the change is worth making. The 10+ stratum pools every size from 10 to 2,809
under one floor, 0.025126, and that floor is set by the small end: a scrambled grouping of 10-19
pathways reaches support 0.170 across 80 distinct values, so the floor has to clear that noise. From
40 pathways up the scrambles are degenerate -- every one of them has support exactly 0.005, found in
one subsample of 200 and never in two -- yet 6,453 real candidates sit above that, at a
rule-of-three FDR bound under 0.0032. Large clusters were being judged by small-cluster noise.

What changes, and nothing else:

* strata 3-3, 4-4, 5-5, 6-6 and 7-9 keep their frozen cal8 floors, unchanged;
* 10+ becomes eight doubling strata, 10-19 through 1,280+;
* each new stratum is solved on its own candidates, with the cut ladder drawn from **real or
  scrambled** support values and a rule-of-three substitution where the scrambled count is zero.

Everything downstream is the frozen build's own code: ``v04.build`` for the gate and consensus,
``repair.repair_joint`` for the joint fixed point, ``export.write`` for the tables.

**The guard is ``--verify``**: run with the frozen six strata and the frozen cal8 floors and this
script must reproduce the frozen O50's four tables byte for byte, and its strata-aware held-out
check must reproduce ``build_10770.confirm`` exactly. Without that, a re-expressed gate could drift
and the comparison with O50 would be measuring the drift.

Usage::

    uv run scripts/o50s_build.py --verify
    uv run scripts/o50s_build.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The declared stratification: the frozen five, then 10+ split into doublings.
O50S_STRATA: tuple[tuple[int, int], ...] = (
    (3, 3), (4, 4), (5, 5), (6, 6), (7, 9),
    (10, 19), (20, 39), (40, 79), (80, 159), (160, 319), (320, 639), (640, 1279),
    (1280, 10 ** 9))

#: How many leading strata keep their frozen cal8 floors untouched.
FROZEN_SMALL = 5

#: Calibration target a new stratum's floor must reach.
TARGET = 0.008

#: Rule-of-three numerator: with no scrambled candidate observed at a cut, the 95% upper bound on
#: the mean count is this over the number of seeds. The spec names it as 3/10 per seed.
RULE_OF_THREE = 3.0

#: Held-out caps, unchanged from v0.4.
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01

#: The scramble seeds. Calibration is the cal8 set; held-out adds 4006, built 17 Oct 2026.
CALIBRATION = tuple(range(3001, 3011))
HELDOUT = tuple(range(4001, 4007))

#: The four tables ``--verify`` compares.
TABLES = ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv")


def label(low: int, high: int) -> str:
    """A stratum's label, in the frozen build's style.

    Args:
        low: Lower edge, inclusive.
        high: Upper edge, inclusive.

    Returns:
        ``"low-high"``, or ``"low+"`` for an open top stratum.
    """
    return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"


def rows_of(path: Path) -> list[tuple[int, float]]:
    """``(size, support)`` per candidate for one cached side.

    Rounded the way ``Material.rows`` rounds, so a cut compares equal to the value the build sees.

    Args:
        path: The cached ``.npz``.

    Returns:
        One row per candidate.

    Raises:
        FileNotFoundError: If the side is not cached.
    """
    if not path.is_file():
        raise FileNotFoundError(f"{path} is not cached")
    with np.load(path) as handle:
        sizes = np.bitwise_count(handle["blocks"]).sum(axis=1).astype(np.int64)
        supports = handle["supports"]
    return list(zip(sizes.tolist(), [round(float(s), 6) for s in supports], strict=True))


def solve_stratum(real: Sequence[float], nulls: Sequence[Sequence[float]],
                  target: float = TARGET) -> dict[str, object]:
    """One new stratum's floor, by the declared rule.

    The cut ladder is every distinct support value present in the stratum, **real or scrambled** --
    not only the scrambled ones, which is the choice prompt 41 showed matters: above 40 pathways the
    scrambles carry a single value, so a scrambled-only ladder has one rung and can never reach the
    target. Where no scrambled candidate is observed at or above a cut, the mean count is replaced
    by the rule-of-three bound, so an observed zero is never read as a zero rate.

    Args:
        real: The stratum's real supports.
        nulls: The stratum's scrambled supports, one list per seed.
        target: The calibration FDR the floor must reach.

    Returns:
        A ``solved`` entry: the floor, the real count it keeps, the calibration FDR, and whether
        the bound was used.
    """
    seeds = max(len(nulls), 1)
    pooled = np.array([s for one in nulls for s in one], dtype=np.float64)
    mine = np.array(list(real), dtype=np.float64)
    out: dict[str, object] = {"floor": None, "effective": None, "real": int(len(mine)),
                              "calibration_fdr": None, "bounded": False, "n_cuts": 0,
                              "null_per_seed": round(len(pooled) / seeds, 1),
                              "null_max": round(float(pooled.max()), 6) if len(pooled) else None}
    if not len(mine):
        return out
    ladder = sorted(set(pooled.tolist()) | set(mine.tolist()))
    out["n_cuts"] = len(ladder)
    for cut in ladder:
        keep = int(np.count_nonzero(mine >= cut))
        if not keep:
            continue
        total = int(np.count_nonzero(pooled >= cut))
        bounded = total == 0
        mean = RULE_OF_THREE / seeds if bounded else total / seeds
        rate = mean / keep
        if rate <= target:
            out.update(floor=round(float(cut), 6), effective=round(float(cut), 6),
                       real=keep, calibration_fdr=round(rate, 8), bounded=bounded)
            return out
    return out


def confirm_with(real: Sequence[tuple[int, float]],
                 nulls: Sequence[Sequence[tuple[int, float]]],
                 solved: Sequence[dict],
                 strata: Sequence[tuple[int, int]]) -> dict[str, object]:
    """``build_10770.confirm`` with the stratification as a parameter.

    Field for field the same arithmetic, and ``--verify`` asserts the two agree exactly on the
    frozen six strata, so this is a parameterisation rather than a second opinion.

    Args:
        real: The real side's rows.
        nulls: One list of rows per held-out scramble.
        solved: The solved floors, aligned with ``strata``.
        strata: The stratum edges.

    Returns:
        Per-stratum held-out rates and the overall rate.
    """
    from thema.ontology.v04 import stratum_of

    per: list[dict] = []
    total_f = total_r = 0.0
    for index, entry in enumerate(solved):
        threshold = entry["effective"]
        if threshold is None:
            per.append({**entry, "heldout_fdr": None, "heldout_real": 0})
            continue
        r = sum(1 for size, s in real
                if stratum_of(size, strata) == index and s >= threshold)
        f = sum(sum(1 for size, s in rows
                    if stratum_of(size, strata) == index and s >= threshold)
                for rows in nulls) / max(len(nulls), 1)
        total_f += f
        total_r += r
        per.append({**entry, "heldout_null": round(f, 2), "heldout_real": r,
                    "heldout_fdr": round(f / r, 5) if r else None})
    return {"strata": per,
            "overall_fdr": round(total_f / total_r, 5) if total_r else None,
            "overall_real": int(total_r),
            "overall_null": round(total_f, 2)}


def sha256(path: Path) -> str:
    """The file's digest.

    Args:
        path: The file.

    Returns:
        Hex digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_build(real: object, solved: Sequence[dict], strata: Sequence[tuple[int, int]],
                confirmed: dict, args: argparse.Namespace, meta: dict, n: int,
                directory: str, probe: dict | None = None) -> Path:
    """Gate, consensus, the joint fixed point and the export -- all the frozen build's own code.

    Args:
        real: The real side's material.
        solved: The floors, aligned with ``strata``.
        strata: The stratum edges the gate reads.
        confirmed: The held-out report, for the manifest.
        args: Parsed arguments.
        meta: The universe record.
        n: Universe size.
        directory: Output directory name under the version.
        probe: Analysis hook, passed straight to :func:`thema.ontology.v04.build` and then filled
            with the post-consensus members and the repair result. **Write-only and additive**:
            left at ``None`` this function behaves exactly as before.

    Returns:
        Where the build was written.
    """
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.recurrent import hasse
    from thema.ontology.repair import repair_joint
    from thema.ontology.universe import load_embedded

    clock = time.perf_counter()
    built = v04.build(real, solved, theta_same=args.theta_same, strata=strata, probe=probe)
    print(f"  {built.gated:,} of {len(real.supports):,} through the gate; "
          f"{len(built.members):,} after consensus ({built.superseded} superseded) "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)
    repaired = repair_joint(built.members, built.supports, built.inclusions,
                            args.collapse_share, args.theta_same, args.survivor)
    print(f"  joint fixed point at {args.collapse_share}/{args.theta_same}, survivor "
          f"{args.survivor}: {len(built.members):,} -> {len(repaired.members):,} "
          f"({len(repaired.collapsed):,} collapsed, {len(repaired.merged):,} merged)", flush=True)
    sizes_before = [len(bits.unpack(block)) for block in built.members]
    repair_map = {
        "collapse_share": args.collapse_share, "survivor": args.survivor,
        "collapsed": [
            {"victim_size": sizes_before[v], "keeper_size": sizes_before[k],
             "victim_support": round(float(built.supports[v]), 6),
             "keeper_support": round(float(built.supports[k]), 6),
             "kept": "child" if sizes_before[k] < sizes_before[v] else "parent"}
            for v, k in sorted(repaired.collapsed.items())],
        "merged": [
            {"dropped_size": sizes_before[d], "kept_size": sizes_before[k],
             "kind": repaired.merged_kind[d]}
            for d, k in sorted(repaired.merged.items())]}
    if probe is not None:
        # Neither repair sub-pass mutates a membership -- both only ever drop rows -- so the
        # post-consensus members, indexed by repair_joint's ORIGINAL positions, give both member
        # sets of every collapse and every stale merge without instrumenting repair at all.
        probe["consensus_members"] = list(built.members)
        probe["consensus_supports"] = list(built.supports)
        probe["repaired"] = repaired
    built = v04.Built(members=repaired.members, supports=repaired.supports,
                      inclusions=repaired.inclusions, parents=hasse(repaired.members),
                      superseded=built.superseded + len(repaired.merged)
                      + len(repaired.collapsed), gated=built.gated)

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
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
    print(f"  themes {shape['n_nodes']:,}  roots {shape['n_roots']:,}  "
          f"multi-parent {shape['multi_parent_share']:.1%}  "
          f"effectively unplaced {shape['n_effectively_unplaced']:,}", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {
        **v04.parameters(n),
        "method": "v0.4-leaves, size strata above 10 (O50s)",
        "universe": "L (every curated summary removed), minus the declared exclusions",
        "n": n, "arm": "L", "theta_match": 0.70,
        "theta_merge": args.theta_same, "theta_same": args.theta_same,
        "joint_fixed_point": True, "match_split": None,
        "rows": f"1-{args.runs}", "runs": args.runs,
        "strata": [list(s) for s in strata],
        "strata_source": ("the frozen six" if len(strata) == 6 else
                          f"the frozen {FROZEN_SMALL} plus {len(strata) - FROZEN_SMALL} "
                          "doubling strata, declared 17 Oct 2026"),
        "floors": list(solved), "confirmed": confirmed,
        "floors_source": (
            f"strata 1-{FROZEN_SMALL} are the frozen cal8 floors, unchanged; the rest solved on "
            f"{len(CALIBRATION)} cached calibration scrambles {list(CALIBRATION)} with the cut "
            f"ladder drawn from real OR scrambled supports and a rule-of-three substitution where "
            f"the scrambled count is zero, to target {TARGET}; confirmed once on "
            f"{list(HELDOUT)}") if len(strata) > 6 else "the frozen cal8 floors, unchanged",
        "calibration_target": TARGET, "rule_of_three_numerator": RULE_OF_THREE,
        "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
        "caps": {"per_stratum": CAP_STRATUM, "overall": CAP_OVERALL},
        "leaves_digest": meta["leaves_digest"], "universe_digest": meta["universe_digest"],
        "exclusions_file": meta.get("exclusions_file"),
        "n_excluded_inputs": meta.get("n_excluded", 0), "matched_theme_cut": None,
        "repair": {"collapse_share": args.collapse_share, "survivor": args.survivor,
                   "merge_jaccard": args.theta_same, "joint_fixed_point": True,
                   "n_collapsed": len(repaired.collapsed), "n_merged": len(repaired.merged),
                   "n_merged_identical": sum(1 for k in repaired.merged_kind.values()
                                             if k == "identical"),
                   "n_merged_overlap": sum(1 for k in repaired.merged_kind.values()
                                           if k == "overlap"),
                   "second_supports": {str(k): v
                                       for k, v in repaired.collapsed_supports.items()},
                   "rounds": repaired.rounds},
        "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", args.out_version, genes, manifest,
        dry_run=False, info=info, directory=directory)
    (Path(written) / "repair_map.json").write_text(json.dumps(repair_map, indent=1) + "\n",
                                                   encoding="utf-8")
    print(f"  -> {written}  (peak {peak_mb():.0f} MB)", flush=True)
    return Path(written)


def dump_probe(probe: dict, path: Path) -> None:
    """Write the merge provenance the probe collected.

    Analysis output only. The build does not read it, and ``--verify`` passing with the probe on is
    the evidence that collecting it changes nothing.

    Args:
        probe: The filled probe dict.
        path: Destination ``.npz``.
    """
    import numpy as np

    verdict = probe["verdict"]
    dropped = sorted(verdict.superseded)
    position = {candidate: i for i, candidate in enumerate(verdict.accepted)}
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        keep=np.asarray(probe["keep"], dtype=np.int64),
        gated_supports=np.asarray(probe["gated_supports"], dtype=np.float64),
        accepted=np.asarray(verdict.accepted, dtype=np.int64),
        # consensus: the dropped candidate, what beat it, and the block AS COMPARED
        sup_dropped=np.asarray(dropped, dtype=np.int64),
        sup_kept=np.asarray([verdict.superseded[d] for d in dropped], dtype=np.int64),
        sup_kept_position=np.asarray([position[verdict.superseded[d]] for d in dropped],
                                     dtype=np.int64),
        sup_blocks=(np.vstack([verdict.superseded_blocks[d] for d in dropped]) if dropped
                    else np.zeros((0, 1), dtype=np.uint64)),
        sup_against=(np.vstack([verdict.superseded_against[d] for d in dropped]) if dropped
                     else np.zeros((0, 1), dtype=np.uint64)),
        # the post-consensus stack: repair_joint's ORIGINAL index space
        consensus_members=np.vstack(probe["consensus_members"]),
        consensus_supports=np.asarray(probe["consensus_supports"], dtype=np.float64),
        collapse_victim=np.asarray(sorted(probe["repaired"].collapsed), dtype=np.int64),
        collapse_keeper=np.asarray([probe["repaired"].collapsed[v]
                                    for v in sorted(probe["repaired"].collapsed)], dtype=np.int64),
        merge_dropped=np.asarray(sorted(probe["repaired"].merged), dtype=np.int64),
        merge_kept=np.asarray([probe["repaired"].merged[d]
                               for d in sorted(probe["repaired"].merged)], dtype=np.int64),
        merge_kind=np.asarray([probe["repaired"].merged_kind[d]
                               for d in sorted(probe["repaired"].merged)], dtype="U10"),
    )
    print(f"  probe -> {path}  ({len(dropped):,} consensus, "
          f"{len(probe['repaired'].collapsed):,} collapse, "
          f"{len(probe['repaired'].merged):,} stale)", flush=True)


def main(argv: list[str] | None = None) -> int:
    """Solve the new strata and build O50s, or verify the harness against the frozen O50."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"),
                        help="the x2 universe: the real side the gate is applied to")
    parser.add_argument("--scramble-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves/calibration"),
                        help="where the cached scramble sides live. They are universe L, which is "
                             "where the frozen cal8 floors were solved too")
    parser.add_argument("--out-version", default="0.4-leaves")
    parser.add_argument("--directory", default="thema_L_x2_O50s")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--theta-same", type=float, default=0.50)
    parser.add_argument("--collapse-share", type=float, default=0.85)
    parser.add_argument("--survivor", default="support")
    parser.add_argument("--keep-verify", action="store_true",
                        help="keep the --verify build instead of removing it. It is a duplicate "
                             "of the frozen O50 by construction, so it is removed by default")
    parser.add_argument("--probe", type=Path, default=None,
                        help="write the merge provenance to this .npz: the gate's kept candidates, "
                             "every consensus supersession with the dropped block, the "
                             "post-consensus members, and the repair maps. Analysis only -- it "
                             "changes nothing about the build, which is what --verify proves")
    parser.add_argument("--verify", action="store_true",
                        help="build with the FROZEN six strata and the frozen cal8 floors; the "
                             "four tables must match the frozen O50 byte for byte, and the "
                             "strata-aware held-out check must match build_10770.confirm")
    args = parser.parse_args(argv)

    from build_10770 import confirm
    from leaves_build import side
    from thema.ontology.v04 import STRATA

    probe: dict | None = {} if args.probe else None

    meta = json.loads((args.space_root / "universe.json").read_text())
    n = meta["n_embedded"]
    frozen_manifest = json.loads((args.frozen / "manifest.json").read_text())
    cal8 = frozen_manifest["floors"]
    trees = args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    print(f"O50s: the frozen O50 with size strata above 10. n={n:,}, "
          f"{'VERIFY' if args.verify else 'BUILD'}")

    clock = time.perf_counter()
    real = side(trees, [f"row{r:05d}" for r in range(1, args.runs + 1)], n,
                args.space_root / "calibration" / "real.npz", 0.70, None)
    real_rows = real.rows()
    print(f"  real side: {len(real_rows):,} candidates "
          f"({time.perf_counter() - clock:.0f}s, cached)", flush=True)

    if args.verify:
        held = [rows_of(args.scramble_root / f"seed{s:05d}.npz") for s in (4001, 4002)]
        mine = confirm_with(real_rows, held, cal8, STRATA)
        theirs = confirm(real_rows, held, cal8)
        same = json.dumps(mine, sort_keys=True) == json.dumps(theirs, sort_keys=True)
        print(f"  PROOF 1, confirm_with against build_10770.confirm on the frozen six strata: "
              f"identical {same}")
        if not same:
            raise SystemExit("the strata-aware held-out check does not reproduce confirm")
        written = write_build(real, cal8, STRATA, mine, args, meta, n,
                              f"{args.directory}_verify", probe=probe)
        bad = []
        for name in TABLES:
            if sha256(written / name) != sha256(args.frozen / name):
                bad.append(name)
            else:
                print(f"  identical  {name}")
        if bad:
            raise SystemExit(f"NOT identical: {bad}")
        print("  PROOF 2 PASSED. With the frozen strata and floors this harness reproduces the "
              "frozen O50 byte for byte.")
        if probe is not None:
            dump_probe(probe, args.probe)
        if args.keep_verify:
            print(f"  kept at {written}")
        else:
            import shutil
            shutil.rmtree(written)
            print(f"  removed {written} (pass --keep-verify to keep it): it is a byte-for-byte "
                  "duplicate of the frozen O50")
        return 0

    nulls = [rows_of(args.scramble_root / f"seed{s:05d}.npz") for s in CALIBRATION]
    held = [rows_of(args.scramble_root / f"seed{s:05d}.npz") for s in HELDOUT]
    print(f"  calibration: {len(nulls)} cached scrambles {list(CALIBRATION)}, "
          f"mean {sum(len(one) for one in nulls) / len(nulls):,.0f} candidates per seed")
    print(f"  held out: {len(held)} scrambles {list(HELDOUT)}, "
          f"4006 built 17 Oct 2026; the rest cached", flush=True)

    from thema.ontology.v04 import stratum_of
    solved: list[dict] = []
    for index, (low, high) in enumerate(O50S_STRATA):
        name = label(low, high)
        if index < FROZEN_SMALL:
            entry = dict(cal8[index])
            entry.update(stratum=name, bounded=False, source="frozen cal8, unchanged")
            solved.append(entry)
            continue
        mine = [s for size, s in real_rows if stratum_of(size, O50S_STRATA) == index]
        per = [[s for size, s in rows if stratum_of(size, O50S_STRATA) == index]
               for rows in nulls]
        entry = solve_stratum(mine, per)
        entry.update(stratum=name, source="solved 17 Oct 2026")
        solved.append(entry)
    print("  floors " + ", ".join(
        f"{e['stratum']}:{e['effective']}" + ("*" if e.get("bounded") else "")
        for e in solved) + "   (* = the rule-of-three bound decided the cut)", flush=True)

    confirmed = confirm_with(real_rows, held, solved, O50S_STRATA)
    over = {e["stratum"]: e["heldout_fdr"] for e in confirmed["strata"]
            if e["heldout_fdr"] is not None and e["heldout_fdr"] > CAP_STRATUM}
    print(f"  held-out FDR overall {confirmed['overall_fdr']} (cap {CAP_OVERALL})"
          + (f"; OVER the per-stratum cap: {over}" if over
             else f"; every stratum inside {CAP_STRATUM}"), flush=True)

    written = write_build(real, solved, O50S_STRATA, confirmed, args, meta, n, args.directory,
                          probe=probe)
    (written / "floors_o50s.json").write_text(json.dumps({
        "strata": [list(s) for s in O50S_STRATA], "frozen_small": FROZEN_SMALL,
        "calibration_target": TARGET, "rule_of_three_numerator": RULE_OF_THREE,
        "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
        "caps": {"per_stratum": CAP_STRATUM, "overall": CAP_OVERALL},
        "solved": solved, "confirmed": confirmed,
        "over_cap": over, "overall_over_cap": bool(
            confirmed["overall_fdr"] is not None
            and confirmed["overall_fdr"] > CAP_OVERALL),
        "seconds": round(time.perf_counter() - clock, 1),
    }, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"  floors -> {written / 'floors_o50s.json'}")
    if probe is not None:
        dump_probe(probe, args.probe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
