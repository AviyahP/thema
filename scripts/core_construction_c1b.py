#!/usr/bin/env python3
"""C1b: the core-based construction, with copies matched per stratum. Declared 20 Oct 2026.

**Exploratory: nothing is adopted without Aviyah.** This replaces the withdrawn Part B of
`PROMPT_48_49.md` with one change, and the change is what makes the idea viable. Part B needed 10 or
more matched copies before a grouping could have a core; at a flat J >= 0.70 the median grouping has
exactly 10 copies and **only 51.5% reach 10**, so the core step would have been inert for half the
build. Matching at prompt 47's per-stratum thresholds -- 0.70 below 10 pathways, 0.50 for 10-19,
0.60 for 20-39, 0.50 from 40 up -- gives the mid-sized groupings copies to average over.

In O50s a theme is its 50%-inclusion member set, so groupings with the same recurring core but
different extras stay separate themes. C1b makes the **core** a theme's identity: a grouping's
core is the pathways present in at least 90% of its copies, its members are the core plus the
extras that clear a calibrated per-stratum cut ``p``, and two groupings are the same theme when
**each one's core lies inside the other's members** -- the mutual core rule, compared always
against the seed's own core and members so a family can never chain.

**Why the work is split in two phases.** ``prepare`` is threshold-free at 4 s a side, but ``score``
costs 80-87 s and the strata call for three different thresholds, so every side is scored three
times and each grouping takes the copies from its own stratum's pass. That is the whole cost of the
run. Since ``p`` cannot be known until the real and calibration extras have all been seen, phase 1
scores each side **once** and caches its per-grouping inclusion; phase 2 solves ``p`` and builds
members, the merge and the gate from the cache without scoring anything again.

Usage::

    uv run scripts/core_construction_c1b.py --reproduce   # the declared legacy check
    uv run scripts/core_construction_c1b.py --sides       # phase 1, resumable
    uv run scripts/core_construction_c1b.py --build       # phase 2
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

#: O50s's strata, unchanged.
STRATA: tuple[tuple[int, int], ...] = (
    (3, 3), (4, 4), (5, 5), (6, 6), (7, 9),
    (10, 19), (20, 39), (40, 79), (80, 159), (160, 319), (320, 639), (640, 1279),
    (1280, 10 ** 9))

#: Prompt 47's chosen match threshold per stratum: 0.70 below 10, 0.50 for 10-19, 0.60 for 20-39,
#: 0.50 from 40 up. Keyed by stratum index, so the table and the strata cannot drift apart.
THETA: tuple[float, ...] = (0.70, 0.70, 0.70, 0.70, 0.70,
                            0.50, 0.60, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50)

#: Inclusion at or above this is the core.
CORE = 0.90

#: The extras cut is searched over these values, lowest first; 0.9 means members equal the core.
PS: tuple[float, ...] = tuple(round(0.10 + 0.05 * i, 2) for i in range(16))
P_NONE = 0.90

#: RETIRED by the amendment of 20 Oct 2026. It was the minimum copy count before a grouping got a
#: core; every grouping now gets one however few copies it has, and its own appearance counts as a
#: copy exactly as ``family_members`` already counts it. Kept named so the change is legible.
MIN_COPIES_RETIRED = 10

#: Calibration target, and the rule-of-three numerator.
TARGET = 0.008
RULE_OF_THREE = 3.0

#: Smallest member set that survives.
MIN_SIZE = 3

#: The scramble seeds.
CALIBRATION = tuple(range(3001, 3011))
HELDOUT = tuple(range(4001, 4007))

#: Caps, unchanged.
CAP_STRATUM = 0.02
CAP_OVERALL = 0.01

#: Runs per side, and the words needed to hold one bit per run.
RUNS = 200
RUN_WORDS = (RUNS + 63) // 64


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
    """Index of the stratum a grouping of this size falls in.

    Args:
        size: Grouping size in pathways.

    Returns:
        Index into :data:`STRATA`, or -1 below the smallest.
    """
    for index, (low, high) in enumerate(STRATA):
        if low <= size <= high:
            return index
    return -1


def theta_for(size: int) -> float:
    """The match threshold a grouping of this size is scored at.

    Args:
        size: Grouping size in pathways.

    Returns:
        The threshold, or the smallest stratum's for sizes below it.
    """
    index = stratum_of(size)
    return THETA[index if index >= 0 else 0]


def mask_of(runs: Sequence[int]) -> np.ndarray:
    """Pack run indices into a fixed-width bitmask.

    Args:
        runs: Run indices.

    Returns:
        A :data:`RUN_WORDS`-word mask.
    """
    out = np.zeros(RUN_WORDS, dtype=np.uint64)
    for run in runs:
        out[run // 64] |= np.uint64(1) << np.uint64(run % 64)
    return out


def side_cache(out: Path, name: str) -> Path:
    """Where one side's per-grouping inclusion is cached.

    Args:
        out: The experiment directory.
        name: ``"real"`` or ``"seedNNNNN"``.

    Returns:
        The ``.npz`` path.
    """
    return out / "sides" / f"{name}.npz"


def inclusion_of(pool: object, ready: object, grouping: int, words: int
                 ) -> tuple[np.ndarray, np.ndarray]:
    """One grouping's inclusion, from its own matched copies.

    Inclusion of a pathway is copies holding it over copies from runs where it was in the
    subsample -- the same quantity ``family_members`` computes, so this delegates rather than
    reimplementing it.

    Args:
        pool: The scored pool.
        ready: The prepared material.
        grouping: Which grouping.
        words: Bitset width in bits.

    Returns:
        ``(pathway ids, inclusion values)``, sorted by pathway id.
    """
    from thema.ontology.recurrent import family_members_fast

    _candidate, inclusion = family_members_fast([grouping], pool, ready.present, words)
    if not inclusion:
        return (np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32))
    keys = np.fromiter(sorted(inclusion), dtype=np.int32, count=len(inclusion))
    return (keys, np.array([inclusion[int(k)] for k in keys], dtype=np.float32))


def build_side(trees: Path, labels: Sequence[str], n: int, out: Path, name: str,
               report: bool = True) -> None:
    """Phase 1 for one side: score at each threshold and cache the per-grouping inclusion.

    Only one pool is held at a time -- the pools carry a matched cluster per run per grouping and
    three at once would not fit comfortably -- so the loop is over thresholds, and each grouping's
    inclusion is taken from the pass its own stratum calls for. The grouping set itself comes from
    ``prepare`` and is identical across thresholds, which is what makes that safe.

    Args:
        trees: The tree directory.
        labels: Tree stems in run order.
        n: Universe size.
        out: The experiment directory.
        name: The side's name.
        report: Print progress.
    """
    from cut_trees import load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import prepare, score
    from thema.ontology.v04 import NO_CAP, settings_for

    clock = time.perf_counter()
    runs = [load_run(trees / f"{one}.npz", n, NO_CAP) for one in labels]
    base = settings_for(len(runs), legacy=False, theta_match=THETA[0])
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, base, 0, records=list(runs))
    del runs
    words = ready.present.shape[1] * bits.WORD
    total = len(ready.groupings) if hasattr(ready, "groupings") else None
    del total

    keys_all: list[np.ndarray] = []
    vals_all: list[np.ndarray] = []
    sizes = None
    found = None
    eligible = None
    done = 0
    for theta in sorted(set(THETA)):
        pool = score(ready, settings_for(len(labels), legacy=False, theta_match=theta))
        if sizes is None:
            sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int32)
            keys_all = [None] * len(sizes)
            vals_all = [None] * len(sizes)
            found = np.zeros((len(sizes), RUN_WORDS), dtype=np.uint64)
            eligible = np.zeros((len(sizes), RUN_WORDS), dtype=np.uint64)
        mine = np.flatnonzero(
            np.array([theta_for(int(s)) == theta for s in sizes], dtype=bool))
        for grouping in mine.tolist():
            if np.isnan(pool.support[grouping]):
                continue
            keys, vals = inclusion_of(pool, ready, grouping, words)
            keys_all[grouping] = keys
            vals_all[grouping] = vals
            found[grouping] = mask_of(sorted(pool.copies[grouping]))
            eligible[grouping] = mask_of(
                np.flatnonzero(ready.eligible_mask[grouping]).tolist())
            done += 1
        if report:
            print(f"      theta {theta}: {len(mine):,} groupings "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
        del pool

    keep = np.array([k is not None for k in keys_all], dtype=bool)
    order = np.flatnonzero(keep)
    lengths = np.array([len(keys_all[i]) for i in order], dtype=np.int64)
    indptr = np.zeros(len(order) + 1, dtype=np.int64)
    np.cumsum(lengths, out=indptr[1:])
    cache = side_cache(out, name)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache,
        grouping=order.astype(np.int32),
        sizes=sizes[order],
        indptr=indptr,
        keys=np.concatenate([keys_all[i] for i in order]) if len(order)
        else np.zeros(0, np.int32),
        vals=np.concatenate([vals_all[i] for i in order]) if len(order)
        else np.zeros(0, np.float32),
        found=found[order],
        eligible=eligible[order],
        n_groupings=np.array([len(sizes)], dtype=np.int64),
        n_pathways=np.array([n], dtype=np.int64))
    if report:
        print(f"    {name}: {done:,} scored groupings of {len(sizes):,}, "
              f"{indptr[-1]:,} inclusion entries -> {cache.name} "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)


def load_side(path: Path) -> dict[str, object]:
    """One side's cached inclusion.

    Args:
        path: The cached ``.npz``.

    Returns:
        The arrays, with ``copies`` derived from the found masks.

    Raises:
        FileNotFoundError: If the side is not cached.
    """
    if not path.is_file():
        raise FileNotFoundError(f"{path} is not cached; run --sides first")
    with np.load(path) as handle:
        got = {k: handle[k] for k in handle.files}
    got["n_copies"] = np.bitwise_count(got["found"]).sum(axis=1).astype(np.int64)
    got["n_eligible"] = np.bitwise_count(got["eligible"]).sum(axis=1).astype(np.int64)
    return got


def core_and_members(side: Mapping[str, object], p_by_stratum: Sequence[float]
                     ) -> dict[str, object]:
    """Steps 3 to 6: cores at 0.9, and members as core plus extras clearing the stratum's p.

    **Every grouping gets a core**, by the amendment of 20 Oct 2026, however few copies it has. A
    grouping seen once has one copy -- its own appearance, which ``family_members`` already counts
    -- so all its members sit at inclusion 1.0 and its core is its own set. For 2 to 9 copies the
    core is now a majority of those copies rather than the whole set, which is the amendment's
    substantive effect.

    Args:
        side: One side's inclusion.
        p_by_stratum: The extras cut per stratum.

    Returns:
        Per grouping: core keys, member keys, and the core size at 1.0.
    """
    indptr, keys, vals = side["indptr"], side["keys"], side["vals"]
    sizes = side["sizes"]
    cores: list[np.ndarray] = []
    members: list[np.ndarray] = []
    exact: list[int] = []
    for row in range(len(sizes)):
        lo, hi = int(indptr[row]), int(indptr[row + 1])
        k, v = keys[lo:hi], vals[lo:hi]
        index = stratum_of(int(sizes[row]))
        p = p_by_stratum[index if index >= 0 else 0]
        core = k[v >= CORE]
        extra = k[(v < CORE) & (v >= p)]
        cores.append(core)
        members.append(np.union1d(core, extra) if len(extra) else core)
        exact.append(int((v >= 1.0).sum()))
    return {"cores": cores, "members": members, "core_exact": np.array(exact, dtype=np.int32)}


def extras_histogram(side: Mapping[str, object]) -> np.ndarray:
    """Per stratum and per candidate p, how many extras clear it.

    Extras are the pathways below the core threshold. **Every grouping contributes**, by the
    amendment of 20 Oct 2026: the retired copy minimum used to exclude groupings under 10 copies
    from this sweep entirely, so both ``R(p)`` and ``N(p)`` are larger now and the solved p can
    move. That is the amendment's main effect on the build.

    Args:
        side: One side's cached inclusion.

    Returns:
        A ``(strata, len(PS))`` count matrix.
    """
    indptr, keys, vals = side["indptr"], side["keys"], side["vals"]
    sizes = side["sizes"]
    out = np.zeros((len(STRATA), len(PS)), dtype=np.int64)
    del keys
    for row in range(len(sizes)):
        index = stratum_of(int(sizes[row]))
        if index < 0:
            continue
        lo, hi = int(indptr[row]), int(indptr[row + 1])
        extra = vals[lo:hi][vals[lo:hi] < CORE]
        if not len(extra):
            continue
        out[index] += np.array([(extra >= p).sum() for p in PS], dtype=np.int64)
    return out


def solve_p(real: np.ndarray, nulls: Sequence[np.ndarray]) -> list[dict[str, object]]:
    """Step 5: the lowest p whose scrambled-to-real extras ratio reaches the target.

    Args:
        real: The real side's extras histogram.
        nulls: One histogram per calibration scramble.

    Returns:
        One entry per stratum, with the chosen p and the curve behind it.
    """
    mean = np.mean(np.stack(nulls), axis=0) if nulls else np.zeros_like(real)
    out: list[dict[str, object]] = []
    for index, (low, high) in enumerate(STRATA):
        row = {"stratum": label(low, high), "index": index, "p": P_NONE,
               "real_at_p": int(real[index][-1]), "null_at_p": float(mean[index][-1]),
               "ratio": None, "curve": []}
        for column, p in enumerate(PS):
            r = int(real[index][column])
            n = float(mean[index][column])
            ratio = (n / r) if r else None
            row["curve"].append({"p": p, "real": r, "null": round(n, 2),
                                 "ratio": round(ratio, 6) if ratio is not None else None})
            if row["p"] == P_NONE and r and ratio is not None and ratio <= TARGET:
                row.update(p=p, real_at_p=r, null_at_p=round(n, 2), ratio=round(ratio, 6))
        out.append(row)
    return out


def merge_mutual(cores: Sequence[np.ndarray], members: Sequence[np.ndarray],
                 support: np.ndarray, sizes: np.ndarray, n_pathways: int,
                 report: bool = True) -> list[list[int]]:
    """Step 7: the mutual core rule, in today's rank order.

    Each unclaimed grouping in rank order becomes a seed and claims every unclaimed ``g`` with
    ``core(g)`` inside ``members(seed)`` **and** ``core(seed)`` inside ``members(g)``. The
    comparison is always against the seed's own core and members, never the growing family, so a
    family cannot chain.

    The candidates for a seed are not every unclaimed grouping. ``core(seed)`` must lie inside
    ``members(g)``, so only groupings whose members hold **every** pathway of the seed's core can
    qualify -- and in particular the rarest one. Taking that pathway's holders from an inverted
    index turns a 7e10-comparison rule into one that resolves the real pool in seconds.

    Args:
        cores: Core pathway ids per grouping.
        members: Member pathway ids per grouping.
        support: Support per grouping, for the rank order.
        sizes: Member count per grouping, for the rank order's tie-break.
        n_pathways: Universe size.
        report: Print progress.

    Returns:
        One list of grouping rows per family, seed first.
    """
    from thema.ontology import bitset as bits

    clock = time.perf_counter()
    width = bits.words_for(n_pathways) * bits.WORD
    core_bits = np.vstack([bits.pack(sorted(c.tolist()), width)[None, :] for c in cores])
    mem_bits = np.vstack([bits.pack(sorted(m.tolist()), width)[None, :] for m in members])
    core_sz = np.bitwise_count(core_bits).sum(axis=1).astype(np.int64)
    mem_sz = np.bitwise_count(mem_bits).sum(axis=1).astype(np.int64)
    holders: list[list[int]] = [[] for _ in range(n_pathways)]
    for row in range(len(members)):
        for pathway in members[row].tolist():
            holders[pathway].append(row)
    index = [np.array(h, dtype=np.int64) for h in holders]
    freq = np.array([len(h) for h in index])
    # Today's rank order: support descending, then size descending.
    order = np.lexsort((-mem_sz, -support))
    claimed = np.zeros(len(members), dtype=bool)
    families: list[list[int]] = []
    for seed in order.tolist():
        if claimed[seed]:
            continue
        claimed[seed] = True
        family = [seed]
        if core_sz[seed]:
            rare = min(cores[seed].tolist(), key=lambda pathway: freq[pathway])
            cand = index[rare]
            cand = cand[~claimed[cand]]
            cand = cand[core_sz[cand] <= mem_sz[seed]]
            if len(cand):
                inside = np.bitwise_count(
                    core_bits[cand] & ~mem_bits[seed]).sum(axis=1) == 0
                back = np.bitwise_count(
                    core_bits[seed] & ~mem_bits[cand]).sum(axis=1) == 0
                take = cand[inside & back]
                claimed[take] = True
                family.extend(take.tolist())
        families.append(family)
    if report:
        print(f"    mutual core rule: {len(members):,} groupings -> {len(families):,} families "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return families


def pooled_inclusion(family: Sequence[int], pool: object, present: np.ndarray,
                     words: int) -> tuple[np.ndarray, np.ndarray]:
    """A merged theme's inclusion, from one pooled copy per run.

    **Deliberately not** ``family_members_fast``, which counts each matched copy separately. The
    spec pools a family's copies "one per run: the union of that run's copies", so a run where two
    of the family's groupings matched different clusters contributes **one** observation, not two.
    On a single-grouping family the two agree; on a merged one they do not, and the spec's version
    is the one that makes a merged theme's inclusion mean the same thing as an unmerged theme's.

    Args:
        family: Grouping rows in the family.
        pool: The scored pool.
        present: Per run, the bitset of pathways in its subsample.
        words: Bitset width in bits.

    Returns:
        ``(pathway ids, inclusion values)``, sorted by pathway id.
    """
    from thema.ontology import bitset as bits

    per_run: dict[int, np.ndarray] = {}
    for grouping in family:
        for run, copy in pool.copies[grouping].items():
            here = per_run.get(run)
            per_run[run] = copy.copy() if here is None else (here | copy)
    if not per_run:
        return (np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32))
    del words
    runs = sorted(per_run)
    pooled = np.vstack([per_run[r][None, :] for r in runs])
    seen = sorted({p for r in runs for p in bits.unpack(per_run[r])})
    if not seen:
        return (np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32))
    keys = np.fromiter(seen, dtype=np.int32, count=len(seen))
    word = (keys // bits.WORD).astype(np.int64)
    bit = (np.uint64(1) << (keys % bits.WORD).astype(np.uint64))
    # holds: pooled copies that carry the pathway. could: those whose run had it in its subsample.
    holds = ((pooled[:, word] & bit) != 0).sum(axis=0)
    rows = np.vstack([present[r][None, :] for r in runs])
    could = ((rows[:, word] & bit) != 0).sum(axis=0)
    vals = np.minimum(holds / np.maximum(could, 1), 1.0).astype(np.float32)
    return (keys, vals)


def solve_floors(real: Sequence[tuple[int, float]],
                 nulls: Sequence[Sequence[tuple[int, float]]]) -> list[dict[str, object]]:
    """Step 8's floors: prompt 43's solver, per stratum, with the rule-of-three substitution.

    Args:
        real: ``(size, support)`` per real theme.
        nulls: The same per calibration scramble.

    Returns:
        One entry per stratum.
    """
    seeds = max(len(nulls), 1)
    out: list[dict[str, object]] = []
    for index, (low, high) in enumerate(STRATA):
        mine = np.array([s for size, s in real if stratum_of(size) == index], dtype=np.float64)
        pooled = np.array([s for rows in nulls for size, s in rows
                           if stratum_of(size) == index], dtype=np.float64)
        entry: dict[str, object] = {"stratum": label(low, high), "floor": None,
                                    "effective": None, "real": int(len(mine)),
                                    "calibration_fdr": None, "bounded": False}
        if not len(mine):
            out.append(entry)
            continue
        for cut in sorted(set(pooled.tolist()) | set(mine.tolist())):
            keep = int(np.count_nonzero(mine >= cut))
            if not keep:
                continue
            total = int(np.count_nonzero(pooled >= cut))
            bounded = total == 0
            mean = RULE_OF_THREE / seeds if bounded else total / seeds
            if mean / keep <= TARGET:
                entry.update(floor=round(float(cut), 6), effective=round(float(cut), 6),
                             real=keep, calibration_fdr=round(mean / keep, 8), bounded=bounded)
                break
        out.append(entry)
    return out


def confirm_floors(real: Sequence[tuple[int, float]],
                   held: Sequence[Sequence[tuple[int, float]]],
                   solved: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Apply the solved floors once to the held-out scrambles.

    Args:
        real: ``(size, support)`` per real theme.
        held: The same per held-out scramble.
        solved: The solved floors.

    Returns:
        Per-stratum held-out rates and the overall rate.
    """
    per: list[dict[str, object]] = []
    total_f = total_r = 0.0
    for index, entry in enumerate(solved):
        floor = entry["effective"]
        if floor is None:
            per.append({**entry, "heldout_fdr": None, "heldout_real": 0})
            continue
        r = sum(1 for size, s in real if stratum_of(size) == index and s >= float(floor))
        f = sum(sum(1 for size, s in rows
                    if stratum_of(size) == index and s >= float(floor))
                for rows in held) / max(len(held), 1)
        total_f += f
        total_r += r
        per.append({**entry, "heldout_null": round(f, 2), "heldout_real": r,
                    "heldout_fdr": round(f / r, 5) if r else None})
    return {"strata": per,
            "overall_fdr": round(total_f / total_r, 5) if total_r else None,
            "overall_real": int(total_r), "overall_null": round(total_f, 2)}


def reproduce(args: argparse.Namespace) -> int:
    """The declared legacy check: flat 0.70, p = 0.5, no core step, the twin rule restored.

    With those four substitutions the pipeline is O50s's own pre-gate construction, so its candidate
    set must equal the cached real side's **bit for bit**. That is the check that the parts C1b
    replaces are the only parts that changed.

    Args:
        args: Parsed arguments.

    Returns:
        0.

    Raises:
        SystemExit: If the reproduction fails.
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
    from thema.ontology.v04 import INCLUSION_CUT, NO_CAP, settings_for

    meta = json.loads((args.x2 / "universe.json").read_text())
    n = meta["n_embedded"]
    trees = args.x2 / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    clock = time.perf_counter()
    print("REPRODUCTION CHECK: flat theta 0.70, p = 0.5, no core step, the twin rule restored")
    runs = [load_run(trees / f"row{r:05d}.npz", n, NO_CAP) for r in range(1, args.runs + 1)]
    conf = settings_for(len(runs), legacy=False, theta_match=0.70)
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, conf, 0, records=list(runs))
    del runs
    words = ready.present.shape[1] * bits.WORD
    pool = score(ready, conf)
    # No core step: members are the 0.5-inclusion set, which is what completion produces.
    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members_fast([grouping], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(candidate)
                         if inclusion.get(p, 0.0) >= INCLUSION_CUT)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
    # The twin rule restored: greedy seed absorption at THETA, not the mutual core rule.
    grouped = families(list(completed), completed, pool, None, conf)
    blocks = [completed[seed] for seed, family in grouped
              if not np.isnan(family_support(family, pool, ready.eligible_mask))]
    mine = np.vstack(blocks)
    with np.load(args.x2 / "calibration" / "real.npz") as handle:
        theirs = handle["blocks"]
    same = (mine.shape == theirs.shape
            and np.array_equal(np.sort(mine, axis=0), np.sort(theirs, axis=0)))
    print(f"  {len(blocks):,} candidates against the cached side's {len(theirs):,}")
    print(f"  membership identical: {same}  ({time.perf_counter() - clock:.0f}s)")
    if not same:
        raise SystemExit("the reproduction check FAILED; C1b is not a controlled change")
    print("  PASSED. Only the core, p, the mutual core rule and the dropped steps differ.")
    return 0


def side_jobs(args: argparse.Namespace) -> list[tuple[str, Path, list[str], int]]:
    """Every side this run needs, as ``(name, trees, labels, n)``.

    The real side is the x2 universe; the scrambles are universe L, which is where their trees and
    O50s's own floors came from.

    Args:
        args: Parsed arguments.

    Returns:
        One job per side, the real side first.
    """
    meta = json.loads((args.x2 / "universe.json").read_text())
    leaves = json.loads((args.leaves / "universe.json").read_text())
    x2 = args.x2 / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    ltrees = args.leaves / "trees" / f"leaves_centred_{leaves['universe_digest']}"
    jobs = [("real", x2, [f"row{r:05d}" for r in range(1, args.runs + 1)], meta["n_embedded"])]
    for seed in (*CALIBRATION, *HELDOUT):
        jobs.append((f"seed{seed:05d}", ltrees,
                     [f"seed{seed:05d}_row{r:05d}" for r in range(1, args.runs + 1)],
                     leaves["n_embedded"]))
    return jobs


def phase_one(args: argparse.Namespace) -> int:
    """Cache the per-grouping inclusion for the real side and the calibration scrambles.

    Only those eleven are needed: ``p`` is solved from the real extras against the calibration
    mean, and the held-out sides are not read until the floors exist.

    Args:
        args: Parsed arguments.

    Returns:
        0.
    """
    jobs = [job for job in side_jobs(args)
            if job[0] == "real" or int(job[0][4:]) in CALIBRATION]
    todo = [job for job in jobs if not side_cache(args.out, job[0]).is_file()]
    print(f"PHASE 1: {len(jobs)} sides for the p sweep; {len(todo)} still to compute", flush=True)
    clock = time.perf_counter()
    for name, trees, labels, n in todo:
        print(f"  {name} ({n:,} pathways)", flush=True)
        build_side(trees, labels, n, args.out, name)
        print(f"    cumulative {time.perf_counter() - clock:.0f}s", flush=True)
    print(f"  phase 1 complete ({time.perf_counter() - clock:.0f}s)", flush=True)
    return 0


def themes_of_side(name: str, trees: Path, labels: Sequence[str], n: int,
                   p_by_stratum: Sequence[float], report: bool = True) -> dict[str, object]:
    """Steps 2 to 8 for one side: cores, members, the merge, the pooled recompute and support.

    Phase 2 scores again rather than reading phase 1's cache, because the pooled recompute of step 7
    needs the **copies themselves** -- the matched cluster per run per grouping -- and those are far
    too large to cache for seventeen sides. The cache is still what ``p`` was solved from, so the
    two phases agree by construction on everything ``p`` depends on.

    Args:
        name: The side's name.
        trees: The tree directory.
        labels: Tree stems in run order.
        n: Universe size.
        p_by_stratum: The extras cut per stratum.
        report: Print progress.

    Returns:
        The side's themes: members, cores, supports and provenance.
    """
    from cut_trees import load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import prepare, score
    from thema.ontology.v04 import NO_CAP, settings_for

    clock = time.perf_counter()
    runs = [load_run(trees / f"{one}.npz", n, NO_CAP) for one in labels]
    base = settings_for(len(runs), legacy=False, theta_match=THETA[0])
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, base, 0, records=list(runs))
    del runs
    words = ready.present.shape[1] * bits.WORD

    sizes = None
    keys_all: list[np.ndarray | None] = []
    vals_all: list[np.ndarray | None] = []
    own_all: list[np.ndarray] = []
    found = eligible = None
    pools: dict[float, object] = {}
    for theta in sorted(set(THETA)):
        pool = score(ready, settings_for(len(labels), legacy=False, theta_match=theta))
        if sizes is None:
            sizes = np.bitwise_count(pool.groupings).sum(axis=1).astype(np.int64)
            # The grouping set is prepare's, identical at every threshold, so the own-sets are
            # taken once from whichever pass comes first.
            own_all = [np.fromiter(bits.unpack(pool.groupings[g]), dtype=np.int32)
                       for g in range(len(sizes))]
            keys_all = [None] * len(sizes)
            vals_all = [None] * len(sizes)
            found = np.zeros((len(sizes), RUN_WORDS), dtype=np.uint64)
            eligible = np.zeros((len(sizes), RUN_WORDS), dtype=np.uint64)
        for grouping in np.flatnonzero(
                np.array([theta_for(int(s)) == theta for s in sizes])).tolist():
            if np.isnan(pool.support[grouping]):
                continue
            keys_all[grouping], vals_all[grouping] = inclusion_of(pool, ready, grouping, words)
            found[grouping] = mask_of(sorted(pool.copies[grouping]))
            eligible[grouping] = mask_of(
                np.flatnonzero(ready.eligible_mask[grouping]).tolist())
        pools[theta] = pool
    rows = np.flatnonzero(np.array([k is not None for k in keys_all]))
    if report:
        print(f"    {name}: {len(rows):,} scored groupings "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    side = {"sizes": sizes[rows].astype(np.int32), "grouping": rows.astype(np.int32),
            "indptr": np.zeros(len(rows) + 1, dtype=np.int64),
            "keys": np.concatenate([keys_all[i] for i in rows]),
            "vals": np.concatenate([vals_all[i] for i in rows]),
            "found": found[rows], "eligible": eligible[rows],
            "own": [own_all[int(i)] for i in rows]}
    np.cumsum([len(keys_all[i]) for i in rows], out=side["indptr"][1:])
    side["n_copies"] = np.bitwise_count(side["found"]).sum(axis=1).astype(np.int64)
    shaped = core_and_members(side, p_by_stratum)
    cores, members = shaped["cores"], shaped["members"]
    support = np.array([
        np.bitwise_count(side["found"][i]).sum() / max(
            int(np.bitwise_count(side["eligible"][i]).sum()), 1)
        for i in range(len(rows))], dtype=np.float64)
    mem_sz = np.array([len(m) for m in members], dtype=np.int64)
    fams = merge_mutual(cores, members, support, mem_sz, n, report=report)

    out_members: list[np.ndarray] = []
    out_incl: list[np.ndarray] = []
    out_core: list[np.ndarray] = []
    out_support: list[float] = []
    out_rows: list[list[int]] = []
    out_copies: list[int] = []
    for family in fams:
        seed = family[0]
        index = stratum_of(int(side["sizes"][seed]))
        p = p_by_stratum[index if index >= 0 else 0]
        if len(family) == 1:
            keys, vals = keys_all[int(rows[seed])], vals_all[int(rows[seed])]
        else:
            by_theta: dict[float, list[int]] = {}
            for row in family:
                by_theta.setdefault(theta_for(int(side["sizes"][row])), []).append(
                    int(rows[row]))
            parts: dict[int, np.ndarray] = {}
            for theta, groupings in by_theta.items():
                k, v = pooled_inclusion(groupings, pools[theta], ready.present, words)
                for key, value in zip(k.tolist(), v.tolist(), strict=True):
                    parts[key] = max(parts.get(key, 0.0), value)
            keys = np.fromiter(sorted(parts), dtype=np.int32, count=len(parts))
            vals = np.array([parts[int(x)] for x in keys], dtype=np.float32)
        core = keys[vals >= CORE]
        extra = keys[(vals < CORE) & (vals >= p)]
        member = np.union1d(core, extra) if len(extra) else core
        vals_for = vals[np.isin(keys, member)]
        keys = member
        if len(member) < MIN_SIZE:
            continue
        mask = np.zeros(RUN_WORDS, dtype=np.uint64)
        emask = np.zeros(RUN_WORDS, dtype=np.uint64)
        for row in family:
            mask |= side["found"][row]
            emask |= side["eligible"][row]
        hits = int(np.bitwise_count(mask).sum())
        able = int(np.bitwise_count(emask).sum())
        out_members.append(member)
        out_incl.append(vals_for)
        out_core.append(core)
        out_support.append(hits / able if able else 0.0)
        out_rows.append([int(rows[g]) for g in family])
        out_copies.append(hits)
    if report:
        print(f"    {name}: {len(out_members):,} themes before the gate "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"members": out_members, "inclusion": out_incl, "cores": out_core,
            "support": np.array(out_support), "groupings": out_rows,
            "theme_copies": np.array(out_copies, dtype=np.int64),
            "n_groupings": int(len(rows)), "n_families": len(fams),
            "copies": side["n_copies"], "grouping_sizes": side["sizes"],
            "core_exact": shaped["core_exact"]}


def immediate_parents(members: Sequence[np.ndarray], n_pathways: int,
                      report: bool = True) -> list[tuple[int, ...]]:
    """Step 9's edges: strict containment on members, immediate parents only.

    Same definition as ``recurrent.hasse`` and a different algorithm, because hasse walks every
    ordered pair in Python and C1b produces tens of thousands of themes -- 73,484 themes would be
    5.4e9 pair tests, hours of work. A superset of X must contain **every** member of X, so the
    candidates are exactly the themes holding X's rarest member; taking those from an inverted
    index and checking containment with one vectorised pass leaves only the minimal ones.

    ``tests/test_core_construction_c1b.py`` asserts this agrees with ``hasse`` on random fixtures,
    so the substitution is checked rather than assumed.

    Args:
        members: Member pathway ids per theme.
        n_pathways: Universe size.
        report: Print progress.

    Returns:
        Per theme, the sorted indices of its immediate parents.
    """
    from thema.ontology import bitset as bits

    clock = time.perf_counter()
    width = bits.words_for(n_pathways) * bits.WORD
    stack = np.vstack([bits.pack(sorted(m.tolist()), width)[None, :] for m in members])
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    holders: list[list[int]] = [[] for _ in range(n_pathways)]
    for row in range(len(members)):
        for pathway in members[row].tolist():
            holders[pathway].append(row)
    index = [np.array(h, dtype=np.int64) for h in holders]
    freq = np.array([len(h) for h in index])
    out: list[tuple[int, ...]] = []
    for row in range(len(members)):
        mine = members[row]
        if not len(mine):
            out.append(())
            continue
        rare = min(mine.tolist(), key=lambda pathway: freq[pathway])
        cand = index[rare]
        cand = cand[(cand != row) & (sizes[cand] > sizes[row])]
        if len(cand):
            inside = np.bitwise_count(stack[row][None, :] & ~stack[cand]).sum(axis=1) == 0
            cand = cand[inside]
        if len(cand) <= 1:
            out.append(tuple(int(c) for c in cand))
            continue
        # Minimal supersets only: drop any that strictly contains another superset.
        keep = []
        for position, outer in enumerate(cand.tolist()):
            others = np.delete(cand, position)
            between = np.bitwise_count(
                stack[others] & ~stack[outer]).sum(axis=1) == 0
            if not bool((between & (sizes[others] < sizes[outer])).any()):
                keep.append(outer)
        out.append(tuple(sorted(keep)))
    if report:
        print(f"  edges: {sum(len(p) for p in out):,} immediate parents over "
              f"{len(members):,} themes ({time.perf_counter() - clock:.0f}s)", flush=True)
    return out


def export_build(args: argparse.Namespace, real: Mapping[str, object], keep: Sequence[int],
                 solved: Sequence[Mapping[str, object]], confirmed: Mapping[str, object],
                 table: Sequence[Mapping[str, object]], p_by_stratum: Sequence[float],
                 clock: float) -> None:
    """Step 9's edges and the build directory.

    Edges are strict containment on members, immediate parents only. **No consensus merge, no
    chain collapse, no repair** -- those are the steps C1b drops, and what they would have acted on
    is measured in the report rather than applied here.

    Args:
        args: Parsed arguments.
        real: The real side's themes.
        keep: Which themes cleared the gate.
        solved: The floors.
        confirmed: The held-out report.
        table: The p table.
        p_by_stratum: The extras cut per stratum.
        clock: Start time.
    """
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export, v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.universe import load_embedded

    meta = json.loads((args.x2 / "universe.json").read_text())
    n = meta["n_embedded"]
    keys = list(load_embedded(args.x2, args.data / "pathways.tsv").keys)
    width = bits.words_for(n) * bits.WORD
    members = [real["members"][i] for i in keep]
    blocks = [bits.pack(sorted(m.tolist()), width) for m in members]
    parents = immediate_parents(members, n)
    ids = [f"n{i:05d}" for i in range(len(blocks))]
    incl = [dict(zip(real["members"][i].tolist(), real["inclusion"][i].tolist(), strict=True))
            for i in keep]
    cores = [set(real["cores"][i].tolist()) for i in keep]
    nodes = tuple(
        Node(id=ids[i],
             parents=tuple(ids[p] for p in parents[i]),
             members=tuple((keys[p], round(float(incl[i].get(p, 1.0)), 4))
                           for p in sorted(bits.unpack(block))),
             support=round(float(real["support"][keep[i]]), 6))
        for i, block in enumerate(blocks))
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
        "method": "v0.4-leaves, core-based construction (C1b)",
        "universe": "L minus the declared exclusions", "n": n,
        "theta_match": "per stratum, prompt 47's choice",
        "theta_match_per_stratum": {label(*s): THETA[i] for i, s in enumerate(STRATA)},
        "core_threshold": CORE,
        "min_copies": None,
        "min_copies_retired": MIN_COPIES_RETIRED,
        "amendment": "20 Oct 2026: no minimum copy count; every grouping gets a core",
        "p_per_stratum": {label(*s): p_by_stratum[i] for i, s in enumerate(STRATA)},
        "p_table": list(table), "strata": [list(s) for s in STRATA],
        "floors": list(solved), "confirmed": confirmed,
        "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
        "caps": {"per_stratum": CAP_STRATUM, "overall": CAP_OVERALL},
        "calibration_target": TARGET, "rule_of_three_numerator": RULE_OF_THREE,
        "same_theme_rule": "mutual core: core(g) inside members(seed) and core(seed) inside "
                           "members(g), compared against the seed only, no chaining",
        "dropped_steps": ["consensus merge", "chain collapse", "repair"],
        "n_groupings": real["n_groupings"], "n_families": real["n_families"],
        "n_before_gate": len(real["members"]), "n_after_gate": len(keep),
        "leaves_digest": meta["leaves_digest"], "universe_digest": meta["universe_digest"],
        "peak_mb": round(peak_mb(), 1), **shape}
    written = export.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", "0.4-leaves", genes, manifest,
        dry_run=False, info=info, directory=args.build_dir.name)
    # At tens of thousands of themes the member detail is far too large for one JSON blob, so
    # it streams to TSV and the record keeps only what the report needs to index by.
    lean = [{"node": ids[i], "size": len(members[i]),
             "copies": int(real["theme_copies"][keep[i]]),
             "support": round(float(real["support"][keep[i]]), 6),
             "core_size": len(cores[i]), "n_parents": len(parents[i])}
            for i in range(len(blocks))]
    detail = Path(written) / "themes_detail.tsv"
    with detail.open("w", newline="", encoding="utf-8") as handle:
        handle.write("node\tsize\tsupport\tcopies\tcore_size\tparents\tmembers\n")
        for i in range(len(blocks)):
            inclusion = " ".join(
                f"{keys[pathway]}:{incl[i].get(pathway, 1.0):.4f}"
                f"{':core' if pathway in cores[i] else ''}"
                for pathway in sorted(members[i].tolist()))
            handle.write(
                f"{ids[i]}\t{len(members[i])}\t{float(real['support'][keep[i]]):.6f}\t"
                f"{int(real['theme_copies'][keep[i]])}\t{len(cores[i])}\t"
                f"{' '.join(sorted(ids[p] for p in parents[i]))}\t{inclusion}\n")
    (Path(written) / "c1b.json").write_text(json.dumps({
        "p_per_stratum": p_by_stratum, "p_table": list(table),
        "floors": list(solved), "confirmed": confirmed,
        "n_groupings": real["n_groupings"], "n_families": real["n_families"],
        "n_before_gate": len(real["members"]), "n_after_gate": len(keep),
        "grouping_sizes": real["grouping_sizes"].tolist(),
        "copies": real["copies"].tolist(),
        "theme_copies": real["theme_copies"].tolist(),
        "theme_copies_kept": [int(real["theme_copies"][i]) for i in keep],
        "themes": lean, "detail": detail.name,
        "seconds": round(time.perf_counter() - clock, 1),
    }) + "\n", encoding="utf-8")
    print(f"  -> {written}  ({time.perf_counter() - clock:.0f}s, peak {peak_mb():.0f} MB)",
          flush=True)


def phase_two(args: argparse.Namespace) -> int:
    """Solve p from phase 1's caches, build every side, gate, stack and export.

    Args:
        args: Parsed arguments.

    Returns:
        0.
    """
    clock = time.perf_counter()
    jobs = {name: (trees, labels, n) for name, trees, labels, n in side_jobs(args)}

    # Solving p holds eleven phase-1 sides' inclusion in memory at once and peaks at about 15 GB,
    # which is enough to be killed on a loaded machine -- and it is deterministic in those caches,
    # so it is paid once and reused. Delete p_table.json to re-solve it.
    cached_table = args.out / "p_table.json"
    if cached_table.is_file():
        table = json.loads(cached_table.read_text(encoding="utf-8"))
        print(f"  p reused from {cached_table.name} (delete it to re-solve)", flush=True)
    else:
        real_hist = extras_histogram(load_side(side_cache(args.out, "real")))
        nulls = [extras_histogram(load_side(side_cache(args.out, f"seed{s:05d}")))
                 for s in CALIBRATION]
        table = solve_p(real_hist, nulls)
    p_by_stratum = [float(entry["p"]) for entry in table]
    print("PHASE 2: p per stratum")
    print(f"  {'stratum':<9}{'p':>7}{'real extras':>13}{'null mean':>11}{'ratio':>11}")
    for entry in table:
        print(f"  {entry['stratum']:<9}{entry['p']:>7}{entry['real_at_p']:>13,}"
              f"{entry['null_at_p']:>11.2f}"
              f"{(str(entry['ratio']) if entry['ratio'] is not None else '-'):>11}")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "p_table.json").write_text(json.dumps(table, indent=2) + "\n",
                                           encoding="utf-8")

    # Each side's theme rows are cached: the floors need only (size, support), and the real side's
    # full themes are cached too. A side is the expensive part of this phase, so a failure in the
    # edges or the export must not cost the sides again -- which is exactly what happened once.
    themes_dir = args.out / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    built: dict[str, dict[str, object]] = {}
    rows: dict[str, list[tuple[int, float]]] = {}
    for name in ["real"] + [f"seed{s:05d}" for s in (*CALIBRATION, *HELDOUT)]:
        trees, labels, n = jobs[name]
        cache = themes_dir / f"{name}.npz"
        if cache.is_file() and name != "real":
            with np.load(cache) as handle:
                rows[name] = list(zip(handle["sizes"].tolist(),
                                      handle["supports"].tolist(), strict=True))
            print(f"  {name}: {len(rows[name]):,} themes (cached)", flush=True)
            continue
        full = themes_dir / "real_full.npz"
        if name == "real" and full.is_file():
            with np.load(full, allow_pickle=False) as handle:
                # Every `handle[...]` decompresses the whole array afresh, and a slice of it keeps
                # that copy alive as its base -- so these MUST be hoisted out of the comprehensions
                # below. Reading them inside peaked at 18 GB and was killed.
                indptr = handle["indptr"]
                keys, vals = handle["keys"], handle["vals"]
                core_keys, core_indptr = handle["core_keys"], handle["core_indptr"]
                built["real"] = {
                    "members": [keys[indptr[i]:indptr[i + 1]]
                                for i in range(len(indptr) - 1)],
                    "inclusion": [vals[indptr[i]:indptr[i + 1]]
                                  for i in range(len(indptr) - 1)],
                    "cores": [core_keys[core_indptr[i]:core_indptr[i + 1]]
                              for i in range(len(core_indptr) - 1)],
                    "support": handle["supports"],
                    "theme_copies": handle["theme_copies"],
                    "groupings": [[int(g)] for g in handle["seed_grouping"]],
                    "n_groupings": int(handle["n_groupings"][0]),
                    "n_families": int(handle["n_families"][0]),
                    "copies": handle["copies"],
                    "grouping_sizes": handle["grouping_sizes"],
                    "core_exact": handle["core_exact"]}
            rows["real"] = list(zip([len(m) for m in built["real"]["members"]],
                                    built["real"]["support"].tolist(), strict=True))
            print(f"  real: {len(rows['real']):,} themes (cached)", flush=True)
            continue
        if args.only and name != args.only:
            print(f"  {name}: not cached, skipped (--only {args.only})", flush=True)
            continue
        print(f"  {name}", flush=True)
        got = themes_of_side(name, trees, labels, n, p_by_stratum)
        rows[name] = list(zip([len(m) for m in got["members"]],
                              got["support"].tolist(), strict=True))
        np.savez_compressed(cache,
                            sizes=np.array([len(m) for m in got["members"]], dtype=np.int32),
                            supports=got["support"])
        if name == "real":
            built["real"] = got
            lens = [len(m) for m in got["members"]]
            indptr = np.zeros(len(lens) + 1, dtype=np.int64)
            np.cumsum(lens, out=indptr[1:])
            clens = [len(c) for c in got["cores"]]
            cptr = np.zeros(len(clens) + 1, dtype=np.int64)
            np.cumsum(clens, out=cptr[1:])
            np.savez_compressed(
                full, indptr=indptr,
                keys=np.concatenate(got["members"]) if lens else np.zeros(0, np.int32),
                vals=np.concatenate(got["inclusion"]) if lens else np.zeros(0, np.float32),
                core_indptr=cptr,
                core_keys=np.concatenate(got["cores"]) if clens else np.zeros(0, np.int32),
                supports=got["support"], theme_copies=got["theme_copies"],
                seed_grouping=np.array([f[0] for f in got["groupings"]], dtype=np.int32),
                n_groupings=np.array([got["n_groupings"]], dtype=np.int64),
                n_families=np.array([got["n_families"]], dtype=np.int64),
                copies=got["copies"], grouping_sizes=got["grouping_sizes"],
                core_exact=got["core_exact"])
        else:
            del got

    if args.only:
        print(f"  cached {args.only}; stopping before the gate (--only)", flush=True)
        return 0

    def rows_of(side: str) -> list[tuple[int, float]]:
        """``(size, support)`` per theme, from the cache or the live build."""
        return rows[side]

    solved = solve_floors(rows_of("real"),
                          [rows_of(f"seed{s:05d}") for s in CALIBRATION])
    confirmed = confirm_floors(rows_of("real"),
                              [rows_of(f"seed{s:05d}") for s in HELDOUT], solved)
    over = {e["stratum"]: e["heldout_fdr"] for e in confirmed["strata"]
            if e["heldout_fdr"] is not None and e["heldout_fdr"] > CAP_STRATUM}
    print("  floors " + ", ".join(f"{e['stratum']}:{e['effective']}" for e in solved))
    print(f"  held-out overall {confirmed['overall_fdr']} (cap {CAP_OVERALL})"
          + (f"; OVER the per-stratum cap: {over}" if over
             else f"; every stratum inside {CAP_STRATUM}"), flush=True)

    real = built["real"]
    keep = []
    for i, member in enumerate(real["members"]):
        entry = solved[max(stratum_of(len(member)), 0)]
        floor = entry["effective"]
        if floor is not None and real["support"][i] >= float(floor):
            keep.append(i)
    print(f"  gate: {len(keep):,} of {len(real['members']):,} themes", flush=True)
    export_build(args, real, keep, solved, confirmed, table, p_by_stratum, clock)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the reproduction check, phase 1, or the build."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--x2", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--leaves", type=Path, default=Path("data/ontology/v0.4-leaves"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/core_construction_C1b_2026-10-20"))
    parser.add_argument("--build-dir", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_C1b"))
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--reproduce", action="store_true",
                        help="the declared legacy check; writes nothing")
    parser.add_argument("--build", action="store_true", help="phase 2: solve p, then build")
    parser.add_argument("--sides", action="store_true",
                        help="phase 1: cache the per-grouping inclusion for the real side and the "
                             "calibration scrambles, which is what p is solved from")
    parser.add_argument("--only", type=str, default=None,
                        help="phase 2: cache exactly this one side's themes and stop. One side per "
                             "process keeps the peak to a single side and makes progress durable; "
                             "a later --build finds every side cached and only gates and exports.")
    args = parser.parse_args(argv)

    if args.reproduce:
        return reproduce(args)
    if args.sides:
        return phase_one(args)
    if args.build:
        return phase_two(args)
    parser.error("pass --reproduce, --sides or --build")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
