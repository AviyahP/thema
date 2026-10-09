#!/usr/bin/env python3
"""Build THEMA v0.4 on universe L, checking the stored floors before trusting them.

The spec's step 3: reuse v0.4's stored 3-seed floors and confirm them on ONE held-out scramble of L
(seed 4001). If held-out FDR exceeds 0.01 overall or 0.02 in any stratum, recalibrate on L from
seeds 3001-3003 and say so. That order matters -- the stored floors are the cheap hypothesis and
checking them is how Test R's "calibrate once" claim gets tested on a new universe rather than
assumed.

A separate script from ``v04_run.py`` rather than an option on it, because the logic is different:
``v04_run.py --calibrate`` solves floors unconditionally, while this checks first and solves only on
failure. ``v04_run.py`` is left untouched so v0.4 stays byte-identical, which
``--all-stages-on --verify`` re-proves.

Usage::

    uv run scripts/leaves_build.py
    uv run scripts/leaves_build.py --rows 1-100 --directory thema_L_r1-100
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#: Calibration and held-out seeds, as the spec names them. ONE held-out side, not two.
CALIBRATION = (3001, 3002, 3003)
HELDOUT = (4001,)
#: The fallback the theta brief declares: ten calibration seeds checked on two held-out sides, used
#: only when the three-seed solve fails a cap. Three seeds average six null counts per stratum; ten
#: average thirty, which is what the 5-5 stratum needed and did not get on thema_L.
CALIBRATION_WIDE = tuple(range(3001, 3011))
HELDOUT_WIDE = (4001, 4002)

#: The recurrence-threshold arms, declared 8 Oct 2026 before any result.
#:
#: ``thema_L`` is the published v0.4 setting, 0.70 everywhere. ``M5`` lowers it for every cluster.
#: ``MS`` lowers it only at or above 50 members, on the reviewer's finding that small clusters recur
#: at 0.70 but clusters of 60-2,000 do not. ``match_split`` is ``(size, below, at_or_above)``.
ARMS: dict[str, dict[str, object]] = {
    "L": {"theta_match": 0.70, "match_split": None, "directory": "thema_L"},
    "M5": {"theta_match": 0.50, "match_split": None, "directory": "thema_L_M5"},
    "MS": {"theta_match": 0.70, "match_split": (50, 0.70, 0.50),
           "directory": "thema_L_MS"},
}


def heldout_rates(checked: dict) -> tuple[dict[str, float | None], dict[str, float]]:
    """Per-stratum held-out FDRs, and which of them exceed the per-stratum cap.

    ``confirm()`` writes ``heldout_fdr`` as **None** in two legitimate cases: the stratum has no
    solved floor, so the gate admits nothing from it; or the floor admits zero real discoveries.
    Neither can breach an FDR cap -- a stratum contributing nothing contributes no false discoveries
    either -- so None is carried through as "undefined" and excluded from the comparison rather than
    coerced. It is still reported, because a size class that admits nothing is a real property of
    the build.

    A **missing** key is different and raises. Reading a key that does not exist and defaulting to
    0.0 is what made an earlier gate report "worst stratum 0.0, PASS" on a build whose 5-5 stratum
    was at 0.02715.

    Args:
        checked: The output of ``build_10770.confirm``.

    Returns:
        ``(stratum -> FDR or None, stratum -> FDR)`` where the second holds only the breaches.
    """
    strata = checked.get("strata") or []
    if not strata:
        raise ValueError(f"confirm() returned no strata: keys {sorted(checked)}")
    missing = [e.get("stratum", "?") for e in strata if "heldout_fdr" not in e]
    if missing:
        raise ValueError(f"no heldout_fdr for strata {missing}; keys {sorted(strata[0])}")
    rates = {e["stratum"]: (None if e["heldout_fdr"] is None else float(e["heldout_fdr"]))
             for e in strata}
    from build_10770 import MAX_FDR_STRATUM as cap

    return rates, {k: v for k, v in rates.items() if v is not None and v > cap}


def side(trees: Path, labels: list[str], n: int, cache: Path | None,
         theta_match: float, match_split: tuple[int, float, float] | None) -> object:
    """Material for one side of L, cached with its inclusion votes.

    The cache is per arm, because the recurrence threshold changes both the support scores and
    which groupings become family seeds. Reusing thema_L's cached sides for an arm with a different
    ``theta_match`` would silently score the new arm on the old arm's material -- the failure mode
    the fingerprint checks elsewhere in this repo exist to prevent.

    Args:
        trees: L's tree directory.
        labels: Tree stems in run order.
        n: Size of L.
        cache: Where to read or write the ``.npz``, or None to always compute.
        theta_match: Recurrence threshold.
        match_split: ``(size, below, at_or_above)`` for a per-size threshold, or None.

    Returns:
        A :class:`~thema.ontology.v04.Material`.
    """
    import numpy as np

    from cut_trees import load_run
    from thema.ontology.v04 import NO_CAP, Material, material
    from v04_run import save_side

    if cache is not None and cache.is_file():
        with np.load(cache) as handle:
            if "indptr" in handle:
                indptr = handle["indptr"]
                vote_keys, vote_vals = handle["vote_keys"], handle["vote_vals"]
                votes = tuple(
                    dict(zip(vote_keys[indptr[i]:indptr[i + 1]].tolist(),
                             vote_vals[indptr[i]:indptr[i + 1]].tolist(), strict=True))
                    for i in range(len(indptr) - 1))
                return Material(blocks=handle["blocks"], supports=handle["supports"],
                                selections=votes)
    runs = [load_run(trees / f"{label}.npz", n, NO_CAP) for label in labels]
    got = material(runs, n, theta_match=theta_match, match_split=match_split)
    if cache is not None:
        save_side(cache, got)
    return got


def main(argv: list[str] | None = None) -> int:
    """Check the floors on L, recalibrate if they fail, then build.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_10770 import MAX_FDR_OVERALL, MAX_FDR_STRATUM, confirm, solve
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.recurrent import hasse
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--out-version", default=None,
                        help="write the build under this version instead of --version, so an "
                             "exclusion rebuild can sit beside the build it is compared with")
    parser.add_argument("--space", default="leaves_centred")
    parser.add_argument("--stored-floors", type=Path,
                        default=Path("data/ontology/v0.4/calibration/floors.json"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--rows", default="")
    parser.add_argument("--directory", default="")
    parser.add_argument("--match-themes", type=int, default=0)
    parser.add_argument("--force-recalibrate", action="store_true",
                        help="solve on L even if the stored floors pass; for the record only")
    parser.add_argument("--arm", choices=sorted(ARMS), default="L",
                        help="recurrence-threshold arm; L is v0.4's 0.70 everywhere")
    parser.add_argument("--side", default="",
                        help="compute and cache ONE side for this arm, then stop. "
                             "'real' or 'seedNNNNN'. Side material is a pure function of the "
                             "trees and the arm's thresholds, so a side cached this way is the "
                             "same bytes a build would have written")
    parser.add_argument("--repair", action="store_true",
                        help="apply repair route (a): collapse chains at --collapse-share, then "
                             "re-apply the 0.70 merge on final memberships to a fixed point")
    parser.add_argument("--collapse-share", type=float, default=None,
                        help="chain-collapse share; the declared rule is 0.90")
    parser.add_argument("--floors-file", type=Path, default=None,
                        help="build from these floors instead of calibrating. Used by the re-gate "
                             "grid, which solves several floor sets from one set of cached sides")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    n = meta["n_embedded"]
    trees = root / "trees" / f"{args.space}_{meta['universe_digest']}"
    arm = ARMS[args.arm]
    theta_match = float(arm["theta_match"])
    match_split = arm["match_split"]
    store = root / ("calibration" if args.arm == "L" else f"calibration_{args.arm}")
    store.mkdir(parents=True, exist_ok=True)
    floors_file = store / "floors.json"

    first, last = (1, args.runs)
    if args.rows:
        low, _, high = args.rows.partition("-")
        first, last = int(low), int(high or low)
    half = bool(args.rows)

    def material_for(labels: list[str], cache: Path | None) -> object:
        """One side under this arm's thresholds."""
        return side(trees, labels, n, cache, theta_match, match_split)

    if args.side:
        clock = time.perf_counter()
        labels = ([f"row{r:05d}" for r in range(1, args.runs + 1)] if args.side == "real"
                  else [f"{args.side}_row{r:05d}" for r in range(1, args.runs + 1)])
        got = material_for(labels, store / f"{args.side}.npz")
        print(f"ARM {args.arm} side {args.side}: {len(got.supports):,} candidates "
              f"({time.perf_counter() - clock:.0f}s) -> {store / (args.side + '.npz')}",
              flush=True)
        return 0

    clock = time.perf_counter()
    real = material_for([f"row{r:05d}" for r in range(first, last + 1)],
                        None if half else store / "real.npz")
    split = "" if match_split is None else (
        f", split at {match_split[0]} members -> {match_split[2]}")
    print(f"ARM {args.arm}: theta_match {theta_match}{split}", flush=True)
    print(f"  L real side: {len(real.supports):,} candidate themes from {n:,} pathways "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)

    if args.floors_file is not None:
        record = json.loads(args.floors_file.read_text())
        solved = record["solved"]
        print(f"  floors from {args.floors_file} ({record.get('source', 'given')})", flush=True)
    elif half and floors_file.is_file():
        record = json.loads(floors_file.read_text())
        solved = record["solved"]
    elif floors_file.is_file() and not args.force_recalibrate:
        record = json.loads(floors_file.read_text())
        solved = record["solved"]
        print(f"  floors from {floors_file} ({record['source']})", flush=True)
    elif args.arm != "L":
        # The arms have no stored floors to inherit: changing the recurrence threshold changes the
        # support distribution, so v0.4's floors are not a hypothesis about this arm at all. Solve
        # on three seeds, check once on 4001, and widen to ten seeds checked on 4001+4002 only if a
        # cap fails -- which is the declared fallback, not a reaction to the number.
        def solve_and_check(cal_seeds: tuple[int, ...], held_seeds: tuple[int, ...]) -> tuple:
            """Floors from these calibration seeds, checked on these held-out seeds."""
            cal = [material_for([f"seed{s:05d}_row{r:05d}" for r in range(1, args.runs + 1)],
                                store / f"seed{s:05d}.npz") for s in cal_seeds]
            held = [material_for([f"seed{s:05d}_row{r:05d}" for r in range(1, args.runs + 1)],
                                 store / f"seed{s:05d}.npz") for s in held_seeds]
            got = solve(real.rows(), [c.rows() for c in cal])
            got_check = confirm(real.rows(), [h.rows() for h in held], got)
            fdrs, cap_over = heldout_rates(got_check)
            return got, got_check, fdrs, cap_over

        solved, confirmed, per, over = solve_and_check(CALIBRATION, HELDOUT)
        print(f"  {len(CALIBRATION)} seeds {list(CALIBRATION)}, held out {list(HELDOUT)}: "
              f"overall FDR {confirmed['overall_fdr']} (cap {MAX_FDR_OVERALL})", flush=True)
        print("    per stratum: " + ", ".join(
            f"{k} {'admits nothing' if v is None else v}" for k, v in sorted(per.items())),
              flush=True)
        used_cal, used_held = CALIBRATION, HELDOUT
        source = (f"solved on L from seeds {list(CALIBRATION)}, confirmed on {list(HELDOUT)}")
        narrow = {"calibration": list(CALIBRATION), "heldout": list(HELDOUT),
                  "per_stratum_heldout_fdr": per, "over_cap": over,
                  "overall_fdr": confirmed["overall_fdr"]}
        if over or confirmed["overall_fdr"] > MAX_FDR_OVERALL:
            print("    over the per-stratum cap: "
                  + ", ".join(f"{k} {v}" for k, v in sorted(over.items()))
                  + " -> widening to the declared 10-seed fallback", flush=True)
            solved, confirmed, per, over = solve_and_check(CALIBRATION_WIDE, HELDOUT_WIDE)
            used_cal, used_held = CALIBRATION_WIDE, HELDOUT_WIDE
            source = (f"solved on L from the declared 10-seed fallback {list(CALIBRATION_WIDE)}, "
                      f"confirmed on {list(HELDOUT_WIDE)}, because the 3-seed solve left "
                      + ", ".join(f"{k} {v}" for k, v in sorted(narrow["over_cap"].items()))
                      + f" over the {MAX_FDR_STRATUM} per-stratum cap")
            print(f"  10 seeds: overall FDR {confirmed['overall_fdr']}", flush=True)
            print("    per stratum: " + ", ".join(
                f"{k} {'admits nothing' if v is None else v}" for k, v in sorted(per.items())),
                  flush=True)
            if over:
                print("    STILL over the cap: "
                      + ", ".join(f"{k} {v}" for k, v in sorted(over.items()))
                      + " -- reported, and no further floor is chosen, because picking one by what "
                        "the held-out side does is fitting to the held-out side", flush=True)
        record = {"n": n, "arm": args.arm, "theta_match": theta_match,
                  "match_split": list(match_split) if match_split else None,
                  "source": source, "three_seed_attempt": narrow,
                  "calibration": list(used_cal), "heldout": list(used_held),
                  "per_stratum_heldout_fdr": per, "over_cap": over,
                  "solved": solved, "confirmed": confirmed,
                  "leaves_digest": meta["leaves_digest"],
                  "seconds": round(time.perf_counter() - clock, 1)}
        floors_file.write_text(json.dumps(record, indent=2, default=float) + "\n",
                               encoding="utf-8")
        print("  floors " + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved))
        print(f"  -> {floors_file}", flush=True)
    else:
        stored = json.loads(args.stored_floors.read_text())["solved"]
        held = [material_for([f"seed{s:05d}_row{r:05d}" for r in range(1, args.runs + 1)],
                             store / f"seed{s:05d}.npz") for s in HELDOUT]
        checked = confirm(real.rows(), [h.rows() for h in held], stored)
        per, over = heldout_rates(checked)
        rated = {k: v for k, v in per.items() if v is not None}
        worst_stratum, worst = (max(rated.items(), key=lambda kv: kv[1]) if rated
                                else ("none rated", 0.0))
        passed = (checked["overall_fdr"] <= MAX_FDR_OVERALL and not over
                  and not args.force_recalibrate)
        print(f"  STORED v0.4 floors on L, held out seed {HELDOUT[0]}: "
              f"overall FDR {checked['overall_fdr']} (cap {MAX_FDR_OVERALL}), "
              f"worst stratum {worst_stratum} at {round(worst, 5)} (cap {MAX_FDR_STRATUM})",
              flush=True)
        if over:
            print("    over the per-stratum cap: "
                  + ", ".join(f"{k} {v}" for k, v in sorted(over.items())), flush=True)
        print(f"    -> {'PASS, reused unchanged' if passed else 'FAIL, recalibrating on L'}",
              flush=True)
        if passed:
            solved, source = stored, (f"v0.4's stored floors, reused unchanged; confirmed on L's "
                                      f"held-out scramble {HELDOUT[0]}")
            confirmed = checked
        else:
            cal = [material_for([f"seed{s:05d}_row{r:05d}" for r in range(1, args.runs + 1)],
                                store / f"seed{s:05d}.npz") for s in CALIBRATION]
            solved = solve(real.rows(), [c.rows() for c in cal])
            confirmed = confirm(real.rows(), [h.rows() for h in held], solved)
            source = (f"recalibrated on L from seeds {list(CALIBRATION)} because the stored v0.4 "
                      f"floors failed their held-out check on L: overall "
                      f"{checked['overall_fdr']}, and stratum/strata over the "
                      f"{MAX_FDR_STRATUM} per-stratum cap: "
                      + ", ".join(f"{k} {v}" for k, v in sorted(over.items())))
            print(f"  recalibrated: held-out FDR {confirmed['overall_fdr']}", flush=True)
        record = {"n": n, "source": source, "stored_floors": str(args.stored_floors),
                  "stored_check": checked, "stored_per_stratum_heldout_fdr": per,
                  "stored_over_cap": over, "calibration": list(CALIBRATION),
                  "heldout": list(HELDOUT), "solved": solved, "confirmed": confirmed,
                  "leaves_digest": meta["leaves_digest"],
                  "seconds": round(time.perf_counter() - clock, 1)}
        floors_file.write_text(json.dumps(record, indent=2, default=float) + "\n",
                               encoding="utf-8")
        print("  floors " + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved))
        print(f"  -> {floors_file}", flush=True)

    clock = time.perf_counter()
    built = v04.build(real, solved)
    repaired = None
    if args.repair:
        from thema.ontology.repair import COLLAPSE_SHARE, MERGE_JACCARD, repair, stale_pairs

        share = COLLAPSE_SHARE if args.collapse_share is None else args.collapse_share
        before = len(stale_pairs(built.members, MERGE_JACCARD))
        repaired = repair(built.members, built.supports, built.inclusions, share, MERGE_JACCARD)
        print(f"  REPAIR, collapse share {share}: {len(built.members):,} themes -> "
              f"{len(repaired.members):,}", flush=True)
        print(f"    fix 2, chain collapse: {len(repaired.collapsed):,} absorbed into their parent "
              f"in {repaired.rounds.get('collapse', 0)} round(s); "
              f"{len(repaired.collapsed_supports):,} kept a second support", flush=True)
        kinds = repaired.merged_kind.values()
        print(f"    fix 1, stale merges: {len(repaired.merged):,} dropped "
              f"({sum(1 for k in kinds if k == 'identical'):,} identical, "
              f"{sum(1 for k in kinds if k == 'overlap'):,} non-nested) in "
              f"{repaired.rounds.get('merge', 0)} round(s)", flush=True)
        print(f"    stale pairs before {before:,}, after 0 (asserted)", flush=True)
        # Re-stack containment over the surviving sets; the old edges referred to dropped nodes.
        built = v04.Built(
            members=repaired.members, supports=repaired.supports,
            inclusions=repaired.inclusions, parents=hasse(repaired.members),
            superseded=built.superseded + len(repaired.merged) + len(repaired.collapsed),
            gated=built.gated)
    if args.match_themes and args.match_themes < len(built.members):
        from thema.ontology.recurrent import hasse as restack

        order = sorted(range(len(built.members)), key=lambda i: -built.supports[i])
        keep = sorted(order[:args.match_themes])
        members = [built.members[i] for i in keep]
        built = v04.Built(members=members, supports=[built.supports[i] for i in keep],
                          inclusions=[built.inclusions[i] for i in keep], parents=restack(members),
                          superseded=built.superseded, gated=built.gated)
        print(f"  matched cut: kept the {len(members):,} highest-support themes", flush=True)
    print(f"  {built.gated:,} of {len(real.supports):,} through the gate; "
          f"{len(built.members):,} themes after consensus ({built.superseded} superseded)  "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)

    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
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
    manifest = {**v04.parameters(n), "universe": "L (every curated summary removed)", "n": n,
                "arm": args.arm, "theta_match": theta_match,
                "match_split": list(match_split) if match_split else None,
                "rows": f"{first}-{last}", "runs": last - first + 1, "floors": solved,
                "floors_source": record["source"], "leaves_digest": meta["leaves_digest"],
                "universe_digest": meta["universe_digest"],
                "exclusions_file": meta.get("exclusions_file"),
                "n_excluded_inputs": meta.get("n_excluded", 0),
                "matched_theme_cut": args.match_themes or None,
                "repair": None if repaired is None else {
                    "collapse_share": (args.collapse_share
                                       if args.collapse_share is not None else 0.90),
                    "merge_jaccard": 0.70,
                    "n_collapsed": len(repaired.collapsed),
                    "n_merged": len(repaired.merged),
                    "n_merged_identical": sum(1 for k in repaired.merged_kind.values()
                                              if k == "identical"),
                    "n_merged_overlap": sum(1 for k in repaired.merged_kind.values()
                                            if k == "overlap"),
                    "second_supports": {str(k): v
                                        for k, v in repaired.collapsed_supports.items()},
                    "rounds": repaired.rounds},
                "peak_mb": round(peak_mb(), 1), **shape}
    directory = args.directory or (
        str(arm["directory"]) + (f"_r{first}-{last}" if half else ""))
    written = export.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", args.out_version or args.version, genes, manifest,
        dry_run=False, info=info, directory=directory)
    print(f"  -> {written}  (peak {peak_mb():.0f} MB)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
