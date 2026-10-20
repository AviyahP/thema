#!/usr/bin/env python3
"""The match threshold calibrated per size stratum (O50s-M). Declared 19 Oct 2026. Adopts nothing.

O50s calibrated a *floor* per size stratum and left the *match* threshold at 0.70 everywhere. The
reviewer's 18-19 Oct diagnostics say that is the wrong way round above about 20 pathways: at
J >= 0.70 nearly every theme has support 0.02-0.04 because its edges wobble, while the same themes
recur in a large share of runs at J >= 0.50 (median 0.29 at 20-50, 0.41 at 51-200, 0.95 at
201-1,000). But 0.50 everywhere failed on 8 Oct at 3-6 pathways, where noise recurs. So the
threshold has to depend on size, exactly as the floors already do.

**What changes: THETA_MATCH only, per stratum, chosen from {0.50, 0.60, 0.70}.** THETA_MERGE stays
0.70 for absorption and consensus, the strata are O50s's thirteen, and the floor solver is prompt
43's -- target 0.008, with the rule-of-three substitution where no scrambled candidate is observed.

**One design choice the spec does not pin down.** A candidate's completed membership depends on
theta, not only its support: ``Pool.copies`` is the matched cluster per run and completion is built
from the copies. The frozen matcher's ``match_split`` handles a two-theta split by scoring one pool
twice and swapping ``pool.support`` **by the grouping's size**, keeping the base pass's membership.
That cannot express thirteen strata keyed on **candidate** size, which is what the floors use. So
each theta is run as a **complete, independent material**, and a stratum takes its candidates from
its own chosen theta. The consequence is stated rather than hidden: step 1's "real count passing"
and the arm's gated set are **the same objects**, which is what makes the calibration transfer to
the build, and two near-identical candidates from different thetas can land in different strata,
which consensus at twin 0.50 then merges.

The sweep is 2.3 h, so **every side's rows are cached per theta and the run resumes from disk**.

Usage::

    uv run scripts/match_per_stratum.py --sides      # step 1's material, resumable
    uv run scripts/match_per_stratum.py --solve      # steps 1-2: the per-stratum table
    uv run scripts/match_per_stratum.py --arm M
    uv run scripts/match_per_stratum.py --arm Mm
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The thetas the sweep considers, lowest first.
THETAS = (0.50, 0.60, 0.70)

#: O50s's strata, unchanged.
STRATA: tuple[tuple[int, int], ...] = (
    (3, 3), (4, 4), (5, 5), (6, 6), (7, 9),
    (10, 19), (20, 39), (40, 79), (80, 159), (160, 319), (320, 639), (640, 1279),
    (1280, 10 ** 9))

#: Calibration target, and the rule-of-three numerator, as prompt 43 declared them.
TARGET = 0.008
RULE_OF_THREE = 3.0

#: Arm Mm's extra floor, the original declared m, in every stratum of 10 or more.
DECLARED_M = 0.33
MM_FROM = 10

#: The scramble seeds.
CALIBRATION = tuple(range(3001, 3011))
HELDOUT = tuple(range(4001, 4007))

#: Caps, unchanged.
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01

#: Absorption and consensus stay here.
THETA_MERGE = 0.70


def label(low: int, high: int) -> str:
    """A stratum's label.

    Args:
        low: Lower edge, inclusive.
        high: Upper edge, inclusive.

    Returns:
        ``"low-high"``, or ``"low+"`` for the open top stratum.
    """
    return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"


def stratum_of(size: int) -> int:
    """Index of the stratum a candidate of this size falls in.

    Args:
        size: Candidate size in pathways.

    Returns:
        Index into :data:`STRATA`, or -1 below the smallest.
    """
    for index, (low, high) in enumerate(STRATA):
        if low <= size <= high:
            return index
    return -1


def one_side(trees: Path, labels: Sequence[str], n: int, theta: float,
             report: bool = True) -> dict[str, object]:
    """One side's complete material at one theta: the candidates, their sizes and supports.

    ``prepare`` is theta-free, so it is computed once per side by the caller and handed in; this
    does the theta-dependent remainder -- score, completion, greedy seed absorption at
    :data:`THETA_MERGE`, and the family support -- which is what makes a three-theta sweep cost
    three tails rather than three whole materials.

    Args:
        trees: The tree directory.
        labels: Tree stems in run order.
        n: Universe size.
        theta: The match threshold for this pass.
        report: Print progress.

    Returns:
        ``blocks``, ``sizes``, ``supports`` and ``selections`` for every candidate.
    """
    from cut_trees import load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import (
        families,
        family_members_fast,
        family_support,
        prepare,
        score,
    )
    from thema.ontology.v04 import INCLUSION_CUT, MIN_SIZE, NO_CAP, settings_for

    clock = time.perf_counter()
    runs = [load_run(trees / f"{one}.npz", n, NO_CAP) for one in labels]
    merge_conf = settings_for(len(runs), legacy=False, theta_match=THETA_MERGE)
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, merge_conf, 0, records=list(runs))
    del runs
    words = ready.present.shape[1] * bits.WORD
    pool = score(ready, settings_for(len(labels), legacy=False, theta_match=theta))

    completed: dict[int, np.ndarray] = {}
    votes: dict[int, dict[int, float]] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members_fast([grouping], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(candidate)
                         if inclusion.get(p, 0.0) >= INCLUSION_CUT)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
            votes[grouping] = inclusion
    # Absorption stays at THETA_MERGE, as the spec requires: only matching and support move.
    grouped = families(list(completed), completed, pool, None, merge_conf)
    blocks, supports, selections = [], [], []
    for seed, family in grouped:
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        blocks.append(completed[seed])
        supports.append(float(support))
        selections.append(votes[seed])
    stack = (np.vstack(blocks) if blocks
             else np.zeros((0, ready.present.shape[1]), np.uint64))
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    if report:
        print(f"      theta {theta}: {len(blocks):,} candidates "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"blocks": stack, "sizes": sizes,
            "supports": np.round(np.array(supports, dtype=np.float64), 6),
            "selections": tuple(selections)}


def side_cache(out: Path, name: str, theta: float) -> Path:
    """Where one side's rows at one theta are cached.

    Args:
        out: The sweep's directory.
        name: ``"real"`` or ``"seedNNNNN"``.
        theta: The match threshold.

    Returns:
        The ``.npz`` path.
    """
    return out / "sides" / f"{name}_t{int(round(theta * 100)):03d}.npz"


def sweep(args: argparse.Namespace) -> int:
    """Step 1's material: every side at every theta, cached and resumable.

    Only ``(size, support)`` is kept for the scramble sides, which is all the floor solver and the
    held-out check read. The real side keeps its blocks and inclusion votes too, because the arms
    have to build from them.

    Args:
        args: Parsed arguments.

    Returns:
        0.
    """
    meta = json.loads((args.x2 / "universe.json").read_text())
    x2_trees = args.x2 / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    leaves = json.loads((args.leaves / "universe.json").read_text())
    l_trees = args.leaves / "trees" / f"leaves_centred_{leaves['universe_digest']}"
    (args.out / "sides").mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[str, Path, list[str], int]] = [
        ("real", x2_trees, [f"row{r:05d}" for r in range(1, args.runs + 1)], meta["n_embedded"])]
    for seed in (*CALIBRATION, *HELDOUT):
        jobs.append((f"seed{seed:05d}", l_trees,
                     [f"seed{seed:05d}_row{r:05d}" for r in range(1, args.runs + 1)],
                     leaves["n_embedded"]))
    todo = sum(1 for name, _, _, _ in jobs for theta in THETAS
               if not side_cache(args.out, name, theta).is_file())
    print(f"SWEEP: {len(jobs)} sides x {len(THETAS)} thetas = {len(jobs) * len(THETAS)} passes; "
          f"{todo} still to compute", flush=True)
    clock = time.perf_counter()
    for name, trees, labels, n in jobs:
        if all(side_cache(args.out, name, theta).is_file() for theta in THETAS):
            continue
        print(f"  {name} ({n:,} pathways)", flush=True)
        for theta in THETAS:
            path = side_cache(args.out, name, theta)
            if path.is_file():
                print(f"      theta {theta}: cached", flush=True)
                continue
            got = one_side(trees, labels, n, theta)
            if name == "real":
                np.savez_compressed(path, sizes=got["sizes"], supports=got["supports"],
                                    blocks=got["blocks"])
                votes = args.out / "sides" / f"real_t{int(round(theta * 100)):03d}_votes.json"
                votes.write_text(json.dumps(
                    [{str(k): v for k, v in vote.items()} for vote in got["selections"]])
                    + "\n", encoding="utf-8")
            else:
                np.savez_compressed(path, sizes=got["sizes"], supports=got["supports"])
            del got
            print(f"        -> {path.name}  ({time.perf_counter() - clock:.0f}s cumulative)",
                  flush=True)
    print(f"  sweep complete ({time.perf_counter() - clock:.0f}s)", flush=True)
    return 0


def rows_of(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """``(sizes, supports)`` from a cached side.

    Args:
        path: The cached ``.npz``.

    Returns:
        The two arrays.

    Raises:
        FileNotFoundError: If the side is not cached.
    """
    if not path.is_file():
        raise FileNotFoundError(f"{path} is not cached; run --sides first")
    with np.load(path) as handle:
        return handle["sizes"], handle["supports"]


def solve_stratum(real: np.ndarray, nulls: Sequence[np.ndarray],
                  target: float = TARGET) -> dict[str, object]:
    """Prompt 43's floor solver for one stratum at one theta.

    Args:
        real: The stratum's real supports.
        nulls: The stratum's scrambled supports, one array per seed.
        target: The calibration FDR the floor must reach.

    Returns:
        The floor, the real count it keeps, the calibration FDR and whether the bound decided it.
    """
    seeds = max(len(nulls), 1)
    pooled = np.concatenate(nulls) if nulls else np.zeros(0)
    out: dict[str, object] = {"floor": None, "effective": None, "real": int(len(real)),
                              "calibration_fdr": None, "bounded": False}
    if not len(real):
        return out
    for cut in sorted(set(pooled.tolist()) | set(real.tolist())):
        keep = int(np.count_nonzero(real >= cut))
        if not keep:
            continue
        total = int(np.count_nonzero(pooled >= cut))
        bounded = total == 0
        mean = RULE_OF_THREE / seeds if bounded else total / seeds
        if mean / keep <= target:
            out.update(floor=round(float(cut), 6), effective=round(float(cut), 6),
                       real=keep, calibration_fdr=round(mean / keep, 8), bounded=bounded)
            return out
    return out


def choose(args: argparse.Namespace) -> dict[str, object]:
    """Steps 1 and 2: solve every stratum at every theta, then pick one theta per stratum.

    The declared rule: the theta that admits the most real candidates at calibration FDR at or
    below the target, and the **higher** theta on a tie.

    Args:
        args: Parsed arguments.

    Returns:
        The per-stratum table and the chosen thetas.
    """
    real = {theta: rows_of(side_cache(args.out, "real", theta)) for theta in THETAS}
    nulls = {theta: [rows_of(side_cache(args.out, f"seed{s:05d}", theta))
                     for s in CALIBRATION] for theta in THETAS}
    held = {theta: [rows_of(side_cache(args.out, f"seed{s:05d}", theta))
                    for s in HELDOUT] for theta in THETAS}
    table = []
    for index, (low, high) in enumerate(STRATA):
        name = label(low, high)
        per: dict[float, dict[str, object]] = {}
        for theta in THETAS:
            sizes, supports = real[theta]
            mine = supports[(sizes >= low) & (sizes <= high)]
            nl = [sup[(sz >= low) & (sz <= high)] for sz, sup in nulls[theta]]
            per[theta] = solve_stratum(mine, nl)
        # The declared selection: most real candidates admitted, higher theta on a tie.
        best = max(THETAS, key=lambda t: (per[t]["real"] if per[t]["effective"] is not None
                                          else -1, t))
        if per[best]["effective"] is None:
            best = max(THETAS)
        entry = {"stratum": name, "low": low, "index": index,
                 "chosen_theta": best if per[best]["effective"] is not None else None,
                 "per_theta": {str(t): per[t] for t in THETAS},
                 "admitted": {str(t): (per[t]["real"] if per[t]["effective"] is not None else 0)
                              for t in THETAS}}
        entry.update({k: per[best][k] for k in
                      ("floor", "effective", "real", "calibration_fdr", "bounded")})
        table.append(entry)
    return {"table": table, "held": held, "real": real, "nulls": nulls}


def show_table(table: Sequence[Mapping[str, object]]) -> None:
    """Step 1 and 2's table: the per-stratum sweep and the chosen theta.

    Args:
        table: What :func:`choose` produced.
    """
    print("\n" + "=" * 112)
    print("STEPS 1-2: THE MATCH THRESHOLD SWEEP, AND THE CHOSEN THETA PER STRATUM")
    print("=" * 112)
    print(f"  {'stratum':<9}" + "".join(f"{'adm@' + str(t):>11}" for t in THETAS)
          + f"{'CHOSEN':>8}{'floor':>11}{'real':>8}{'calib FDR':>12}{'bound':>7}")
    for entry in table:
        cells = "".join(f"{entry['admitted'][str(t)]:>11,}" for t in THETAS)
        chosen = entry["chosen_theta"]
        print(f"  {entry['stratum']:<9}{cells}"
              + f"{(str(chosen) if chosen else 'none'):>8}"
              + f"{str(entry['effective']):>11}{entry['real']:>8,}"
              + f"{str(entry['calibration_fdr']):>12}"
              + f"{('yes' if entry['bounded'] else ''):>7}")
    picked = [e["chosen_theta"] for e in table if e["chosen_theta"]]
    from collections import Counter
    print(f"\n  chosen thetas: {dict(Counter(picked))}; "
          f"{sum(1 for e in table if e['chosen_theta'] is None)} stratum/strata admit nothing")


def gate_arm(args: argparse.Namespace, table: Sequence[Mapping[str, object]],
             arm: str) -> dict[str, object]:
    """Assemble one arm's gated material: per stratum, its chosen theta's candidates.

    Args:
        args: Parsed arguments.
        table: The per-stratum table.
        arm: ``"M"`` or ``"Mm"``.

    Returns:
        The gated blocks, supports, inclusion votes and the effective floors.
    """
    from thema.ontology import bitset as bits

    blocks: list[np.ndarray] = []
    supports: list[float] = []
    votes: list[dict[int, float]] = []
    per_theta: dict[float, dict[str, object]] = {}
    for theta in THETAS:
        path = side_cache(args.out, "real", theta)
        with np.load(path) as handle:
            per_theta[theta] = {"sizes": handle["sizes"], "supports": handle["supports"],
                                "blocks": handle["blocks"]}
        raw = json.loads(
            (args.out / "sides" / f"real_t{int(round(theta * 100)):03d}_votes.json").read_text())
        per_theta[theta]["votes"] = [{int(k): v for k, v in one.items()} for one in raw]
    effective: list[dict[str, object]] = []
    for entry in table:
        low, high = STRATA[entry["index"]]
        floor = entry["effective"]
        if arm == "Mm" and floor is not None and low >= MM_FROM:
            floor = max(float(floor), DECLARED_M)
        record = {**{k: entry[k] for k in
                     ("stratum", "chosen_theta", "calibration_fdr", "bounded")},
                  "effective": floor, "floor": entry["effective"],
                  "m_applied": bool(arm == "Mm" and floor is not None and low >= MM_FROM
                                    and floor != entry["effective"])}
        if floor is None or entry["chosen_theta"] is None:
            record["real"] = 0
            effective.append(record)
            continue
        got = per_theta[entry["chosen_theta"]]
        take = np.flatnonzero((got["sizes"] >= low) & (got["sizes"] <= high)
                              & (got["supports"] >= float(floor)))
        for i in take.tolist():
            blocks.append(got["blocks"][i])
            supports.append(float(got["supports"][i]))
            votes.append(got["votes"][i])
        record["real"] = int(len(take))
        effective.append(record)
    words = per_theta[THETAS[0]]["blocks"].shape[1] * bits.WORD
    print(f"  arm {arm}: {len(blocks):,} candidates through the gate "
          f"(per stratum: {[r['real'] for r in effective]})", flush=True)
    return {"blocks": blocks, "supports": supports, "votes": votes, "effective": effective,
            "words": words}


def confirm_arm(args: argparse.Namespace, effective: Sequence[Mapping[str, object]]
                ) -> dict[str, object]:
    """The held-out check: each stratum's own chosen theta, read once.

    Args:
        args: Parsed arguments.
        effective: The arm's per-stratum floors.

    Returns:
        Per-stratum held-out rates and the overall rate.
    """
    held: dict[float, list[tuple[np.ndarray, np.ndarray]]] = {
        theta: [rows_of(side_cache(args.out, f"seed{s:05d}", theta)) for s in HELDOUT]
        for theta in THETAS}
    real = {theta: rows_of(side_cache(args.out, "real", theta)) for theta in THETAS}
    per: list[dict[str, object]] = []
    total_f = total_r = 0.0
    for index, record in enumerate(effective):
        low, high = STRATA[index]
        floor = record["effective"]
        theta = record["chosen_theta"]
        if floor is None or theta is None:
            per.append({**record, "heldout_fdr": None, "heldout_real": 0})
            continue
        sizes, supports = real[theta]
        r = int(np.count_nonzero((sizes >= low) & (sizes <= high)
                                 & (supports >= float(floor))))
        f = sum(int(np.count_nonzero((sz >= low) & (sz <= high) & (sup >= float(floor))))
                for sz, sup in held[theta]) / max(len(HELDOUT), 1)
        total_f += f
        total_r += r
        per.append({**record, "heldout_null": round(f, 2), "heldout_real": r,
                    "heldout_fdr": round(f / r, 5) if r else None})
    return {"strata": per,
            "overall_fdr": round(total_f / total_r, 5) if total_r else None,
            "overall_real": int(total_r), "overall_null": round(total_f, 2)}


def build_arm(args: argparse.Namespace, table: Sequence[Mapping[str, object]],
              arm: str) -> int:
    """Gate, consensus, the joint fixed point and the export, with O50s's own downstream code.

    Args:
        args: Parsed arguments.
        table: The per-stratum table.
        arm: ``"M"`` or ``"Mm"``.

    Returns:
        0.
    """
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.consensus import consensus
    from thema.ontology.recurrent import hasse
    from thema.ontology.repair import repair_joint
    from thema.ontology.universe import load_embedded

    clock = time.perf_counter()
    gated = gate_arm(args, table, arm)
    confirmed = confirm_arm(args, gated["effective"])
    over = {e["stratum"]: e["heldout_fdr"] for e in confirmed["strata"]
            if e["heldout_fdr"] is not None and e["heldout_fdr"] > CAP_STRATUM}
    print(f"  held-out overall {confirmed['overall_fdr']} (cap {CAP_OVERALL})"
          + (f"; OVER the per-stratum cap: {over}" if over
             else f"; every stratum inside {CAP_STRATUM}"), flush=True)

    verdict = consensus(gated["blocks"], gated["supports"], gated["votes"], gated["words"],
                        stray=0.0, jaccard=0.50)
    accepted = list(verdict.accepted)
    members = [verdict.members[i] for i in range(len(accepted))]
    print(f"  consensus at 0.5: {len(gated['blocks']):,} -> {len(accepted):,} "
          f"({len(verdict.superseded):,} superseded)", flush=True)
    repaired = repair_joint(members, [gated["supports"][c] for c in accepted],
                            [gated["votes"][c] for c in accepted], 0.85, 0.50, "support")
    print(f"  joint fixed point at 0.85/0.5: {len(accepted):,} -> {len(repaired.members):,} "
          f"({len(repaired.collapsed):,} collapsed, {len(repaired.merged):,} merged)", flush=True)

    meta = json.loads((args.x2 / "universe.json").read_text())
    keys = list(load_embedded(args.x2, args.data / "pathways.tsv").keys)
    parents = hasse(repaired.members)
    ids = [f"n{i:05d}" for i in range(len(repaired.members))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents[i]),
             members=tuple((keys[p], round(float(repaired.inclusions[i].get(p, 1.0)), 4))
                           for p in sorted(bits.unpack(block))),
             support=round(repaired.supports[i], 6))
        for i, block in enumerate(repaired.members))
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
        **v04.parameters(meta["n_embedded"]),
        "method": f"v0.4-leaves, O50s strata with the match threshold per stratum (arm {arm})",
        "arm": arm, "universe": "L minus the declared exclusions", "n": meta["n_embedded"],
        "theta_match": "per stratum, from {0.50, 0.60, 0.70}",
        "theta_match_per_stratum": {e["stratum"]: e["chosen_theta"] for e in table},
        "theta_merge": THETA_MERGE, "theta_same": 0.50, "joint_fixed_point": True,
        "strata": [list(s) for s in STRATA],
        "declared_m": DECLARED_M if arm == "Mm" else None,
        "m_from_size": MM_FROM if arm == "Mm" else None,
        "floors": list(gated["effective"]), "confirmed": confirmed,
        "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
        "caps": {"per_stratum": CAP_STRATUM, "overall": CAP_OVERALL},
        "calibration_target": TARGET, "rule_of_three_numerator": RULE_OF_THREE,
        "selection_rule": "most real candidates admitted at calibration FDR <= target; "
                          "the higher theta on a tie",
        "repair": {"collapse_share": 0.85, "survivor": "support", "merge_jaccard": 0.50,
                   "joint_fixed_point": True,
                   "n_collapsed": len(repaired.collapsed), "n_merged": len(repaired.merged),
                   "rounds": repaired.rounds},
        "n_gated": len(gated["blocks"]), "n_after_consensus": len(accepted),
        "leaves_digest": meta["leaves_digest"], "universe_digest": meta["universe_digest"],
        "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", "0.4-leaves", genes, manifest,
        dry_run=False, info=info, directory=f"thema_L_x2_O50s_{arm}")
    print(f"  -> {written}  ({time.perf_counter() - clock:.0f}s, peak {peak_mb():.0f} MB)",
          flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the sweep, the per-stratum selection, or one arm."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--x2", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--leaves", type=Path, default=Path("data/ontology/v0.4-leaves"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/match_per_stratum_2026-10-19"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--sides", action="store_true",
                        help="step 1's material: every side at every theta, cached and resumable")
    parser.add_argument("--solve", action="store_true",
                        help="steps 1-2: solve every stratum at every theta and choose")
    parser.add_argument("--arm", choices=("M", "Mm"), default=None)
    args = parser.parse_args(argv)

    if args.sides:
        return sweep(args)
    if args.solve or args.arm:
        got = choose(args)
        table = got["table"]
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "strata.json").write_text(
            json.dumps({"thetas": list(THETAS), "strata": [list(s) for s in STRATA],
                        "target": TARGET, "rule_of_three_numerator": RULE_OF_THREE,
                        "selection_rule": "most real admitted at FDR <= target, higher theta on "
                                          "a tie",
                        "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
                        "table": table}, indent=2) + "\n", encoding="utf-8")
        if args.solve:
            show_table(table)
            print(f"\n  -> {args.out / 'strata.json'}")
            return 0
        show_table(table)
        return build_arm(args, table, args.arm)
    parser.error("pass --sides, --solve or --arm")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
