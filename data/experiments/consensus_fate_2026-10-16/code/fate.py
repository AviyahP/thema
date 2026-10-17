#!/usr/bin/env python3
"""Where do the large first-pass candidates go? The O50 pipeline, instrumented.

Declared 16 Oct 2026. **Read-only and adopts nothing.** It rebuilds the frozen O50 by composing the
same library functions the build calls, recording what each stage removed and what removed it, and
it **asserts the result is byte-identical to the frozen build** before reporting anything.

The pipeline, in the order it actually runs -- which is not quite the order the prompt lists:

1. **completion** (inside ``v04.material``): every grouping the matcher scored becomes a candidate
   bitset, keeping pathways present in at least ``INCLUSION_CUT`` of the copies that could hold
   them, then dropped if under ``MIN_SIZE``.
2. **absorption** (the twin rule, ``recurrent.families``): greedy seed absorption at ``THETA``.
   A non-seed grouping is absorbed into its seed and never reaches the gate.
3. **family support**: a seed whose family support is NaN is dropped.
4. **gate**: family support at or above the stratum's floor.
5. **consensus** at ``theta_same`` 0.50: a candidate is *superseded* by an accepted one, or accepted
   itself. Nothing else removes a candidate here.
6. **the joint fixed point**: ``[chain collapse 0.85, stale merge 0.50]`` repeated until neither
   changes anything. Both only ever drop, keeping the survivor's membership.
7. **final**: 4,602 themes.

So the prompt's "gate; families; consensus; stale; collapse" is reported as
"completion; absorption; gate; consensus; collapse; stale" -- absorption runs *before* the gate, and
collapse and stale alternate rather than following one another once. Both facts are stated in the
report rather than smoothed over.

Nothing is reimplemented: ``prepare``, ``score``, ``family_members_fast``, ``families``,
``family_support``, ``gate``, ``consensus``, ``collapse_chains`` and ``merge_stale`` are the
build's own. The one piece of library *structure* re-expressed here is ``material``'s loop over
groupings, because the instrumentation has to sit inside it -- and the identity check below is what
proves the re-expression faithful: the candidate set it produces must equal the cached real side
bit for bit, and the final themes must equal the frozen build's members table row for row.

Usage::

    uv run python data/experiments/consensus_fate_2026-10-16/code/fate.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

#: The size bands the report is cut into.
BANDS = ((51, 100), (101, 200), (201, 500), (501, 1000), (1001, 10 ** 9))

#: Candidates at or above this size are tracked individually.
TRACK_FROM = 51

#: Two candidates this close are one group, for step 4's dedup.
SAME_GROUP = 0.90

#: Step 4 looks at this band.
STEP4 = (201, 1000)


def band_of(size: int) -> str:
    """The band label a size falls in.

    Args:
        size: Pathway count.

    Returns:
        The band label, or ``"1-50"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
    return "1-50"


def jaccard(a: set[int] | set[str], b: set[int] | set[str]) -> float:
    """Jaccard of two sets.

    Args:
        a: One set.
        b: The other.

    Returns:
        The index, 0.0 if both are empty.
    """
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def instrumented_material(runs: Sequence[object], n: int, theta_match: float, report: bool = True
                          ) -> dict[str, object]:
    """``v04.material``, with the completion and absorption stages recorded.

    Args:
        runs: Loaded per-run records, in run order.
        n: Universe size.
        theta_match: Recurrence threshold.
        report: Print progress.

    Returns:
        The candidate material plus the per-grouping fate of completion and absorption.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import (
        families,
        family_members_fast,
        family_support,
        prepare,
        score,
    )
    from thema.ontology.v04 import INCLUSION_CUT, MIN_SIZE, settings_for

    clock = time.perf_counter()
    conf = settings_for(len(runs), legacy=False, theta_match=theta_match)
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, conf, 0, records=list(runs))
    pool = score(ready, conf)
    words = ready.present.shape[1] * bits.WORD
    if report:
        print(f"    pool: {len(pool.groupings):,} groupings "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    completed: dict[int, np.ndarray] = {}
    votes: dict[int, dict[int, float]] = {}
    unscored = 0
    too_small: dict[int, int] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            unscored += 1
            continue
        candidate, inclusion = family_members_fast([grouping], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(candidate)
                         if inclusion.get(p, 0.0) >= INCLUSION_CUT)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
            votes[grouping] = inclusion
        else:
            too_small[grouping] = len(members)
    if report:
        print(f"    completed: {len(completed):,} candidates "
              f"({unscored:,} unscored, {len(too_small):,} under MIN_SIZE) "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    grouped = families(list(completed), completed, pool, None, conf)
    absorbed_into: dict[int, int] = {}
    for seed, family in grouped:
        for member in family:
            if member != seed:
                absorbed_into[member] = seed
    if report:
        print(f"    absorption: {len(grouped):,} seeds, {len(absorbed_into):,} absorbed "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    blocks, supports, selections, seeds = [], [], [], []
    nan_support: list[int] = []
    for seed, family in grouped:
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            nan_support.append(seed)
            continue
        blocks.append(completed[seed])
        supports.append(float(support))
        selections.append(votes[seed])
        seeds.append(seed)
    if report:
        print(f"    family support: {len(blocks):,} candidates "
              f"({len(nan_support):,} dropped for NaN support) "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {
        "blocks": np.vstack(blocks) if blocks
        else np.zeros((0, ready.present.shape[1]), np.uint64),
        "supports": np.array(supports, dtype=np.float64),
        "selections": tuple(selections),
        "seeds": seeds,
        "completed": completed,
        "absorbed_into": absorbed_into,
        "nan_support": nan_support,
        "pool_support": pool.support,
        "n_pool": int(len(pool.groupings)),
        "n_unscored": unscored,
        "n_too_small": len(too_small),
        "seconds": round(time.perf_counter() - clock, 1),
    }


def main(argv: list[str] | None = None) -> int:
    """Rebuild O50 instrumented, prove it identical, then write the fate tables."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=ROOT / "data/ontology/frozen/working-O50-2026-10-14")
    parser.add_argument("--space", type=Path, default=ROOT / "data/ontology/v0.4-leaves-x2")
    parser.add_argument("--rec2fix", type=Path,
                        default=ROOT / "data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix")
    parser.add_argument("--out", type=Path, default=HERE.parent)
    parser.add_argument("--runs", type=int, default=200)
    args = parser.parse_args(argv)

    from cut_trees import load_run
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.repair import repair_joint
    from thema.ontology.universe import load_embedded
    from thema.ontology.v04 import NO_CAP, THETA_MATCH, gate

    meta = json.loads((args.space / "universe.json").read_text())
    n = meta["n_embedded"]
    trees = args.space / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    manifest = json.loads((args.frozen / "manifest.json").read_text())
    solved = manifest["floors"]
    theta_same = float(manifest["theta_same"])
    share = float(manifest["repair"]["collapse_share"])
    survivor = manifest["repair"]["survivor"]
    print(f"O50 PIPELINE, INSTRUMENTED. n={n:,}, theta_match={THETA_MATCH}, "
          f"theta_same={theta_same}, collapse={share}, survivor={survivor}")
    print("  floors " + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved), flush=True)

    clock = time.perf_counter()
    runs = [load_run(trees / f"row{r:05d}.npz", n, NO_CAP) for r in range(1, args.runs + 1)]
    print(f"  {len(runs)} cached trees loaded ({time.perf_counter() - clock:.0f}s)", flush=True)
    got = instrumented_material(runs, n, THETA_MATCH)
    del runs

    # PROOF 1: the candidate material must be the cached real side, bit for bit.
    cached = args.space / "calibration" / "real.npz"
    if cached.is_file():
        with np.load(cached) as handle:
            same_blocks = np.array_equal(handle["blocks"], got["blocks"])
            same_support = np.array_equal(handle["supports"], got["supports"])
        print(f"  PROOF 1, against {cached.name}: blocks identical {same_blocks}, "
              f"supports identical {same_support}", flush=True)
        if not (same_blocks and same_support):
            raise SystemExit("the instrumented material is not the cached real side")
    else:
        print("  PROOF 1 SKIPPED: no cached real side to compare with", flush=True)

    rows = list(zip(np.bitwise_count(got["blocks"]).sum(axis=1).astype(np.int64).tolist(),
                    [round(float(s), 6) for s in got["supports"]], strict=True))
    keep = np.flatnonzero(gate(rows, solved)).tolist()
    words = got["blocks"].shape[1] * bits.WORD
    blocks = [got["blocks"][i] for i in keep]
    supports = [float(got["supports"][i]) for i in keep]
    inclusions = [got["selections"][i] for i in keep]
    print(f"  gate: {len(keep):,} of {len(rows):,} candidates", flush=True)

    verdict = consensus(blocks, supports, inclusions, words, stray=0.0, jaccard=theta_same)
    accepted = list(verdict.accepted)
    members = [verdict.members[i] for i in range(len(accepted))]
    print(f"  consensus at {theta_same}: {len(keep):,} -> {len(accepted):,} "
          f"({len(verdict.superseded):,} superseded)", flush=True)

    repaired = repair_joint(members, [supports[c] for c in accepted],
                            [inclusions[c] for c in accepted], share, theta_same, survivor)
    print(f"  joint fixed point at {share}/{theta_same}: {len(accepted):,} -> "
          f"{len(repaired.members):,} ({len(repaired.collapsed):,} collapsed, "
          f"{len(repaired.merged):,} merged)", flush=True)

    # PROOF 2: the final themes must be the frozen build's, member for member.
    keys = list(load_embedded(args.space, ROOT / "data" / "pathways.tsv").keys)
    mine = {frozenset(keys[b] for b in bits.unpack(block)) for block in repaired.members}
    frozen: dict[str, set[str]] = {}
    with (args.frozen / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            frozen.setdefault(row["node"], set()).add(row["key"])
    theirs = {frozenset(one) for one in frozen.values()}
    print(f"  PROOF 2, against the frozen members table: {len(mine):,} themes against "
          f"{len(theirs):,}; identical as sets: {mine == theirs}", flush=True)
    if mine != theirs:
        raise SystemExit(f"{len(theirs - mine)} frozen themes missing, "
                         f"{len(mine - theirs)} spurious")
    return finish({
        "args": args, "got": got, "keep": keep, "rows": rows, "blocks": blocks,
        "supports": supports, "verdict": verdict, "accepted": accepted, "repaired": repaired,
        "keys": keys, "frozen": frozen, "clock": clock, "solved": solved,
    })


def finish(state: dict[str, object]) -> int:
    """Assemble fate.tsv, then hand on to the tables.

    Args:
        state: Everything the instrumented run produced, keyed by stage.

    Returns:
        0.
    """
    from thema.ontology import bitset as bits

    args = state["args"]
    got, keep, blocks = state["got"], state["keep"], state["blocks"]
    verdict, accepted, repaired = state["verdict"], state["accepted"], state["repaired"]
    keys, frozen = state["keys"], state["frozen"]
    args.out.mkdir(parents=True, exist_ok=True)
    completed = got["completed"]
    absorbed_into = got["absorbed_into"]
    nan_support = set(got["nan_support"])
    seed_at = {seed: i for i, seed in enumerate(got["seeds"])}
    gate_at = {candidate: p for p, candidate in enumerate(keep)}
    accept_at = {position: a for a, position in enumerate(accepted)}
    dead = set(repaired.collapsed) | set(repaired.merged)
    alive = [a for a in range(len(accepted)) if a not in dead]
    by_set = {frozenset(one): node for node, one in frozen.items()}
    floor_of = {entry["stratum"]: entry["effective"] for entry in
                json.loads((args.frozen / "manifest.json").read_text())["floors"]}
    from build_10770 import STRATA, stratum_of

    def label(index: int) -> str:
        """The stratum label a size falls in."""
        low, high = STRATA[stratum_of(index)]
        return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"

    sets = {g: set(bits.unpack(block)) for g, block in completed.items()}
    members = [verdict.members[i] for i in range(len(accepted))]
    member_sets = [set(bits.unpack(block)) for block in members]
    final_id = {}
    for j, a in enumerate(alive):
        node = by_set.get(frozenset(keys[b] for b in bits.unpack(repaired.members[j])), "")
        final_id[a] = node

    tracked = sorted(g for g, one in sets.items() if len(one) >= TRACK_FROM)
    out_rows = []
    for g in tracked:
        own = sets[g]
        row = {"grouping": g, "size": len(own), "band": band_of(len(own)),
               "pool_support": round(float(got["pool_support"][g]), 6),
               "family_support": "", "stratum": label(len(own)),
               "floor": floor_of.get(label(len(own)), ""),
               "fate": "", "removed_at": "", "removed_by": "", "removed_by_size": "",
               "jaccard": "", "final_node": ""}
        if g in absorbed_into:
            seed = absorbed_into[g]
            row.update(fate="absorbed", removed_at="absorption", removed_by=f"g{seed}",
                       removed_by_size=len(sets[seed]),
                       jaccard=round(jaccard(own, sets[seed]), 4))
            out_rows.append(row)
            continue
        if g in nan_support:
            row.update(fate="nan_support", removed_at="family support")
            out_rows.append(row)
            continue
        i = seed_at[g]
        row["family_support"] = round(float(got["supports"][i]), 6)
        if i not in gate_at:
            row.update(fate="gated_out", removed_at="gate")
            out_rows.append(row)
            continue
        p = gate_at[i]
        if p in verdict.superseded:
            winner = verdict.superseded[p]
            other = member_sets[accept_at[winner]] if winner in accept_at else set(
                bits.unpack(blocks[winner]))
            row.update(fate="superseded", removed_at="consensus",
                       removed_by=f"c{winner}", removed_by_size=len(other),
                       jaccard=round(jaccard(set(bits.unpack(blocks[p])), other), 4))
            out_rows.append(row)
            continue
        a = accept_at[p]
        if a in repaired.collapsed or a in repaired.merged:
            which = "collapse" if a in repaired.collapsed else "stale merge"
            keeper = repaired.collapsed.get(a, repaired.merged.get(a))
            row.update(fate="collapsed" if which == "collapse" else "merged", removed_at=which,
                       removed_by=final_id.get(keeper) or f"a{keeper}",
                       removed_by_size=len(member_sets[keeper]),
                       jaccard=round(jaccard(member_sets[a], member_sets[keeper]), 4),
                       size=len(member_sets[a]), band=band_of(len(member_sets[a])))
            out_rows.append(row)
            continue
        row.update(fate="final", removed_at="", final_node=final_id.get(a, ""),
                   size=len(member_sets[a]), band=band_of(len(member_sets[a])))
        out_rows.append(row)

    fields = ["grouping", "size", "band", "stratum", "floor", "pool_support", "family_support",
              "fate", "removed_at", "removed_by", "removed_by_size", "jaccard", "final_node"]
    with (args.out / "fate.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"\n  fate.tsv: {len(out_rows):,} candidates of {TRACK_FROM}+ pathways tracked",
          flush=True)
    state.update(out_rows=out_rows, member_sets=member_sets, alive=alive, final_id=final_id)
    return tables(state)


def tables(state: dict[str, object]) -> int:
    """The survival table and the most-supported losses, then hand on to step 4.

    Args:
        state: Everything the instrumented run produced, keyed by stage.

    Returns:
        0.
    """
    out_rows = state["out_rows"]
    labels = [f"{low}-{high}" if high < 10 ** 9 else f"{low}+" for low, high in BANDS]
    order = ["completed", "after absorption", "after family support", "after the gate",
             "after consensus", "after collapse and stale (final)"]
    counts: dict[str, Counter[str]] = {step: Counter() for step in order}
    for row in out_rows:
        reached = {
            "absorbed": ["completed"],
            "nan_support": ["completed", "after absorption"],
            "gated_out": ["completed", "after absorption", "after family support"],
            "superseded": order[:4],
            "collapsed": order[:5],
            "merged": order[:5],
            "final": order,
        }[row["fate"]]
        for step in reached:
            counts[step][row["band"]] += 1
    print("\n" + "=" * 78)
    print(f"SURVIVAL BY STEP AND BAND, candidates of {TRACK_FROM}+ pathways")
    print("=" * 78)
    print(f"  {'step':<36}" + "".join(f"{one:>12}" for one in labels) + f"{'total':>9}")
    for step in order:
        print(f"  {step:<36}"
              + "".join(f"{counts[step].get(one, 0):>12,}" for one in labels)
              + f"{sum(counts[step].values()):>9,}")
    print("\n  removed at each step, by band")
    print(f"  {'step':<36}" + "".join(f"{one:>12}" for one in labels) + f"{'total':>9}")
    for step, nxt in zip(order, order[1:], strict=False):
        lost = {one: counts[step].get(one, 0) - counts[nxt].get(one, 0) for one in labels}
        print(f"  {'-> lost at ' + nxt.replace('after ', ''):<36}"
              + "".join(f"{lost[one]:>12,}" for one in labels)
              + f"{sum(lost.values()):>9,}")
    print("\n  by fate")
    fates = Counter((row["fate"], row["band"]) for row in out_rows)
    print(f"  {'fate':<36}" + "".join(f"{one:>12}" for one in labels) + f"{'total':>9}")
    for fate in ("absorbed", "nan_support", "gated_out", "superseded", "collapsed", "merged",
                 "final"):
        line = {one: fates.get((fate, one), 0) for one in labels}
        if not sum(line.values()):
            continue
        print(f"  {fate:<36}" + "".join(f"{line[one]:>12,}" for one in labels)
              + f"{sum(line.values()):>9,}")

    print("\n  SUPPORT OF THE CANDIDATES THE GATE REMOVED, by band")
    print("  The 10+ floor is the same 0.025126 for every band here, because a candidate of 51 or")
    print("  more pathways is always in the 10+ stratum. Support 0.005 is one run in 200.")
    print(f"  {'band':<10}{'gated out':>11}{'floor':>11}{'min':>9}{'median':>9}{'max':>9}"
          f"{'at or over the floor':>22}")
    for one in labels:
        out = [r for r in out_rows if r["band"] == one and r["fate"] == "gated_out"]
        if not out:
            continue
        values = sorted(float(r["family_support"]) for r in out)
        floor = float(out[0]["floor"])
        middle = values[len(values) // 2]
        print(f"  {one:<10}{len(out):>11,}{floor:>11}{values[0]:>9.4f}{middle:>9.4f}"
              f"{values[-1]:>9.4f}{sum(1 for v in values if v >= floor):>22,}")

    for low, high in ((201, 500), (501, 1000)):
        name = f"{low}-{high}"
        print("\n" + "=" * 78)
        print(f"THE 20 MOST-SUPPORTED REMOVED CANDIDATES OF {name} PATHWAYS")
        print("=" * 78)
        pool = [r for r in out_rows if r["band"] == name and r["fate"] != "final"]
        pool.sort(key=lambda r: -(float(r["family_support"]) if r["family_support"] != ""
                                  else float(r["pool_support"])))
        print(f"  {len(pool)} removed of "
              f"{sum(1 for r in out_rows if r['band'] == name)} in the band")
        print(f"  {'grouping':<11}{'size':>6}{'support':>10}{'floor':>11}   "
              f"{'removed at':<16}{'removed by':<14}{'by size':>9}{'J':>8}")
        for row in pool[:20]:
            support = row["family_support"] if row["family_support"] != "" else row["pool_support"]
            print(f"  g{row['grouping']:<10}{row['size']:>6}{str(support):>10}"
                  f"{str(row['floor']):>11}   {row['removed_at']:<16}"
                  f"{str(row['removed_by']):<14}{str(row['removed_by_size']):>9}"
                  f"{str(row['jaccard']):>8}")
    return step4(state)


def step4(state: dict[str, object]) -> int:
    """Do the lost large candidates match what the areas pass rebuilds?

    Args:
        state: Everything the instrumented run produced, keyed by stage.

    Returns:
        0.
    """
    from thema.ontology import bitset as bits

    args, out_rows, got = state["args"], state["out_rows"], state["got"]
    keep, blocks, member_sets = state["keep"], state["blocks"], state["member_sets"]
    accepted, repaired = state["accepted"], state["repaired"]
    keys, frozen, clock = state["keys"], state["frozen"], state["clock"]
    low, high = STEP4
    gate_at = {candidate: p for p, candidate in enumerate(keep)}
    seed_at = {seed: i for i, seed in enumerate(got["seeds"])}
    accept_at = {position: a for a, position in enumerate(accepted)}
    completed = got["completed"]

    # The candidates the prompt asks for: 201-1,000, through the gate, and removed afterwards.
    wanted = []
    for row in out_rows:
        if row["fate"] not in ("superseded", "collapsed", "merged"):
            continue
        g = row["grouping"]
        i = seed_at.get(g)
        if i is None or i not in gate_at:
            continue
        p = gate_at[i]
        a = accept_at.get(p)
        held = (member_sets[a] if a is not None else set(bits.unpack(blocks[p])))
        if low <= len(held) <= high:
            wanted.append((row, {keys[b] for b in held}))
    wanted.sort(key=lambda pair: -len(pair[1]))
    groups: list[tuple[dict, set[str]]] = []
    for row, held in wanted:
        if any(jaccard(held, other) >= SAME_GROUP for _, other in groups):
            continue
        groups.append((row, held))
    print("\n" + "=" * 78)
    print(f"STEP 4: THE REMOVED {low}-{high} CANDIDATES THAT PASSED THE GATE")
    print("=" * 78)
    print(f"  {len(wanted)} removed candidates in the band, "
          f"{len(groups)} distinct groups at J >= {SAME_GROUP}")

    fix_areas: dict[str, set[str]] = {}
    path = args.rec2fix / "area_members.tsv"
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            for r in csv.DictReader(handle, delimiter="\t"):
                fix_areas.setdefault(r["node"], set()).add(r["key"])
    print(f"  rec2fix areas read: {len(fix_areas)}  ({path})")
    o50 = {node: set(one) for node, one in frozen.items()}

    def best(target: set[str], pool: dict[str, set[str]]) -> tuple[str, float]:
        """The pool member with the highest Jaccard against a target."""
        name, score = "", 0.0
        for node, held in pool.items():
            value = jaccard(target, held)
            if value > score:
                name, score = node, value
        return name, score

    def buckets(values: Sequence[float]) -> str:
        """The declared three-way distribution."""
        hi = sum(1 for v in values if v >= 0.7)
        mid = sum(1 for v in values if 0.5 <= v < 0.7)
        lo = sum(1 for v in values if v < 0.5)
        total = max(len(values), 1)
        return (f">=0.7: {hi} ({hi / total:.0%})   0.5-0.7: {mid} ({mid / total:.0%})   "
                f"<0.5: {lo} ({lo / total:.0%})")

    print(f"\n  {'group':<11}{'size':>6}{'support':>10}   {'removed at':<16}"
          f"{'best rec2fix area':<18}{'J':>7}   {'best O50 node':<14}{'J':>7}")
    to_area, to_o50 = [], []
    for row, held in groups:
        area, av = best(held, fix_areas) if fix_areas else ("", 0.0)
        node, nv = best(held, o50)
        to_area.append(av)
        to_o50.append(nv)
        support = row["family_support"] if row["family_support"] != "" else row["pool_support"]
        print(f"  g{row['grouping']:<10}{len(held):>6}{str(support):>10}   "
              f"{row['removed_at']:<16}{area:<18}{av:>7.3f}   {node:<14}{nv:>7.3f}")
    print(f"\n  best J to any rec2fix area   {buckets(to_area)}")
    print(f"  best J to any O50 node       {buckets(to_o50)}")

    print("\n" + "=" * 78)
    print(f"IN REVERSE: EACH rec2fix AREA OF {low}-{high} PATHWAYS")
    print("=" * 78)
    gated = {f"c{p}": {keys[b] for b in bits.unpack(block)} for p, block in enumerate(blocks)}
    removed_pool = {f"g{row['grouping']}": held for row, held in wanted}
    band_areas = {node: held for node, held in fix_areas.items() if low <= len(held) <= high}
    print(f"  {len(band_areas)} of {len(fix_areas)} rec2fix areas are in the band; "
          f"{len(gated)} gated candidates, {len(removed_pool)} removed ones to match against")
    print(f"  {'area':<12}{'size':>6}  {'best gated':<12}{'J':>7}  {'best removed':<12}{'J':>7}"
          f"  {'best final O50':<14}{'J':>7}")
    ag, ar, an = [], [], []
    for node, held in sorted(band_areas.items(), key=lambda kv: -len(kv[1])):
        g_name, g_val = best(held, gated)
        r_name, r_val = best(held, removed_pool) if removed_pool else ("", 0.0)
        n_name, n_val = best(held, o50)
        ag.append(g_val)
        ar.append(r_val)
        an.append(n_val)
        print(f"  {node:<12}{len(held):>6}  {g_name:<12}{g_val:>7.3f}  {r_name:<12}{r_val:>7.3f}"
              f"  {n_name:<14}{n_val:>7.3f}")
    print(f"\n  best J to any gated first-pass candidate   {buckets(ag)}")
    print(f"  best J to any removed candidate            {buckets(ar)}")
    print(f"  best J to any final O50 theme              {buckets(an)}")

    summary = {
        "n_pool": got["n_pool"], "n_completed": len(completed),
        "n_absorbed": len(got["absorbed_into"]), "n_nan_support": len(got["nan_support"]),
        "n_candidates": len(got["supports"]), "n_gated": len(keep),
        "n_after_consensus": len(accepted), "n_final": len(repaired.members),
        "n_collapsed": len(repaired.collapsed), "n_merged": len(repaired.merged),
        "tracked_from": TRACK_FROM, "n_tracked": len(out_rows),
        "step4": {
            "band": list(STEP4), "n_removed_in_band": len(wanted), "n_groups": len(groups),
            "same_group_jaccard": SAME_GROUP,
            "removed_to_rec2fix_area": {"ge_0.7": sum(1 for v in to_area if v >= 0.7),
                                        "0.5_0.7": sum(1 for v in to_area if 0.5 <= v < 0.7),
                                        "lt_0.5": sum(1 for v in to_area if v < 0.5)},
            "removed_to_o50_node": {"ge_0.7": sum(1 for v in to_o50 if v >= 0.7),
                                    "0.5_0.7": sum(1 for v in to_o50 if 0.5 <= v < 0.7),
                                    "lt_0.5": sum(1 for v in to_o50 if v < 0.5)},
            "n_band_areas": len(band_areas),
            "area_to_gated": {"ge_0.7": sum(1 for v in ag if v >= 0.7),
                              "0.5_0.7": sum(1 for v in ag if 0.5 <= v < 0.7),
                              "lt_0.5": sum(1 for v in ag if v < 0.5)},
            "area_to_removed": {"ge_0.7": sum(1 for v in ar if v >= 0.7),
                                "0.5_0.7": sum(1 for v in ar if 0.5 <= v < 0.7),
                                "lt_0.5": sum(1 for v in ar if v < 0.5)},
            "area_to_final_o50": {"ge_0.7": sum(1 for v in an if v >= 0.7),
                                  "0.5_0.7": sum(1 for v in an if 0.5 <= v < 0.7),
                                  "lt_0.5": sum(1 for v in an if v < 0.5)},
        },
        "seconds": round(time.perf_counter() - clock, 1),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                           encoding="utf-8")
    with (args.out / "step4_groups.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["grouping", "size", "support", "removed_at", "best_rec2fix_area",
                        "j_area", "best_o50_node", "j_o50"])
        writer.writeheader()
        for (row, held), av, nv in zip(groups, to_area, to_o50, strict=True):
            area = best(held, fix_areas)[0] if fix_areas else ""
            node = best(held, o50)[0]
            writer.writerow({
                "grouping": f"g{row['grouping']}", "size": len(held),
                "support": row["family_support"] or row["pool_support"],
                "removed_at": row["removed_at"], "best_rec2fix_area": area,
                "j_area": round(av, 4), "best_o50_node": node, "j_o50": round(nv, 4)})
    with (args.out / "step4_areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["area", "size", "best_gated", "j_gated", "best_removed", "j_removed",
                        "best_o50", "j_o50"])
        writer.writeheader()
        for node, held in sorted(band_areas.items(), key=lambda kv: -len(kv[1])):
            g_name, g_val = best(held, gated)
            r_name, r_val = best(held, removed_pool) if removed_pool else ("", 0.0)
            n_name, n_val = best(held, o50)
            writer.writerow({"area": node, "size": len(held), "best_gated": g_name,
                             "j_gated": round(g_val, 4), "best_removed": r_name,
                             "j_removed": round(r_val, 4), "best_o50": n_name,
                             "j_o50": round(n_val, 4)})
    print(f"\n  -> {args.out}  ({summary['seconds']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
