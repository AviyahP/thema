#!/usr/bin/env python3
"""The top of O50s, two arms. Declared 17 Oct 2026, before any result. Exploratory: adopts nothing.

O50s fixed the 100-1,000 layer and left 261 roots, 164 of them 50 pathways or fewer. Two ways to
build a top of fewer than 49 coherent roots are tested on the same base.

**Arm A** is rec2fix's areas pass, rules unchanged, with O50s as level 0 instead of O50.

**Arm B** measures first. Hennig's clusterwise Jaccard (2007) asks, for each theme, how well the
theme reappears when the data is resampled: restrict it to a run's 80% subsample, take the best
Jaccard against any cluster of that run's Ward tree, and average over the 200 runs. The first size
band whose median falls below 0.6 sets a cut T; the themes below T become the items for an areas
pass, and the themes at or above T are dropped and kept only for comparison.

**One measurement choice that changes the large bands.** A cached run records only its dendrogram
nodes of 3 or more members **and at most half the draw** -- the recurrence machinery excludes the
top of a tree on purpose, because a node holding most of a draw recurs by arithmetic rather than by
meaning. Scoring a 2,000-pathway theme against that set would cap its achievable Jaccard and
understate exactly the bands the cut depends on. So :func:`run_clusters` **rebuilds each run's full
dendrogram** and scores against every internal node of 3 or more members, with no upper cap. The
trees are rebuilt, not re-chosen: the same persisted subsample rows, the same Ward linkage, the same
vectors.

Usage::

    uv run scripts/top_two_arms.py --stability
    uv run scripts/top_two_arms.py --arm A
    uv run scripts/top_two_arms.py --arm B
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The declared stability bands.
BANDS = ((50, 99), (100, 199), (200, 399), (400, 799), (800, 1599), (1600, 10 ** 9))

#: The declared cut, and the alternative the prompt also asks for.
CUT = 0.60
CUT_ALT = 0.75

#: Smallest theme the stability pass scores.
FROM_SIZE = 50

#: Smallest dendrogram node worth scoring against.
MIN_CLUSTER = 3

#: Scrambled candidates sampled per band per seed. The full set is 264,346 and would need hours of
#: matrix work; the sample sizes are reported beside every figure.
SAMPLE_PER_BAND = 500

#: Seed for that sample, so the table is reproducible.
SAMPLE_SEED = 20261017

#: The calibration scrambles the noise check uses.
NOISE_SEEDS = tuple(range(3001, 3011))

#: A root this small is a small root.
SMALL_ROOT = 50

#: Report-only duplication thresholds.
PAIR_J = 0.50
INSIDE = 0.80


def label(low: int, high: int) -> str:
    """A band's label.

    Args:
        low: Lower edge, inclusive.
        high: Upper edge, inclusive.

    Returns:
        ``"low-high"``, or ``"low+"`` for the open top band.
    """
    return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"


def band_of(size: int) -> str | None:
    """The band a size falls in, or None below the smallest.

    Args:
        size: Theme size in pathways.

    Returns:
        The band label, or None.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return label(low, high)
    return None


def run_clusters(full: np.ndarray, n: int, sub: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Every internal node of one run's full Ward dendrogram, as a dense indicator.

    Args:
        full: Condensed distances over all ``n`` pathways.
        n: Universe size.
        sub: The run's sorted subsample indices.

    Returns:
        ``(indicator (clusters, take) float32, sizes (clusters,) float32)``.
    """
    from scipy.cluster.hierarchy import linkage

    from thema.ontology.recurrent import condensed_subset

    take = len(sub)
    merged = linkage(condensed_subset(full, n, sub), method="ward")
    block = np.zeros((2 * take - 1, take), dtype=np.float32)
    block[np.arange(take), np.arange(take)] = 1.0
    for step in range(take - 1):
        left, right = int(merged[step, 0]), int(merged[step, 1])
        np.add(block[left], block[right], out=block[take + step])
    sizes = block.sum(axis=1)
    keep = np.flatnonzero((np.arange(2 * take - 1) >= take) & (sizes >= MIN_CLUSTER))
    return block[keep], sizes[keep]


def stability(groups: Sequence[set[int]], full: np.ndarray, n: int,
              rows: Sequence[np.ndarray], report: bool = True) -> np.ndarray:
    """Hennig's clusterwise Jaccard for every group, over every run.

    One ``float32`` matrix product per run does the whole population at once, which is what makes
    scoring thousands of groups against 200 rebuilt dendrograms affordable.

    Args:
        groups: Member index sets, in the universe's own indexing.
        full: Condensed distances over all ``n`` pathways.
        n: Universe size.
        rows: The persisted subsample rows, one per run.
        report: Print progress.

    Returns:
        ``(groups, runs)`` best Jaccard per group per run.
    """
    out = np.zeros((len(groups), len(rows)), dtype=np.float32)
    clock = time.perf_counter()
    listed = [np.fromiter(one, dtype=np.int64, count=len(one)) for one in groups]
    for index, sub in enumerate(rows):
        take = len(sub)
        where = np.full(n, -1, dtype=np.int64)
        where[sub] = np.arange(take)
        block, sizes = run_clusters(full, n, sub)
        here = np.zeros((len(groups), take), dtype=np.float32)
        for position, members in enumerate(listed):
            local = where[members]
            here[position, local[local >= 0]] = 1.0
        mine = here.sum(axis=1)
        shared = here @ block.T
        union = mine[:, None] + sizes[None, :] - shared
        with np.errstate(divide="ignore", invalid="ignore"):
            scores = np.where(union > 0, shared / union, 0.0)
        out[:, index] = scores.max(axis=1)
        del block, here, shared, union, scores
        if report and (index + 1) % 50 == 0:
            print(f"      {index + 1}/{len(rows)} runs "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return out


def quartiles(values: Sequence[float]) -> tuple[float, float, float]:
    """``(p25, median, p75)``.

    Args:
        values: The numbers.

    Returns:
        The three quantiles, or zeros if empty.
    """
    if not values:
        return (0.0, 0.0, 0.0)
    array = np.asarray(values, dtype=np.float64)
    return (float(np.percentile(array, 25)), float(np.median(array)),
            float(np.percentile(array, 75)))


def auc(positive: Sequence[float], negative: Sequence[float]) -> float | None:
    """Area under the ROC curve, by the rank identity, ties counted as half.

    Args:
        positive: Scores for the real population.
        negative: Scores for the scrambled population.

    Returns:
        The AUC, or None if either side is empty.
    """
    if not len(positive) or not len(negative):
        return None
    pos = np.asarray(positive, dtype=np.float64)
    neg = np.asarray(negative, dtype=np.float64)
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order), dtype=np.float64)
    ranks[order] = np.arange(1, len(order) + 1)
    combined = np.concatenate([pos, neg])
    # Average the ranks within each tie group, which is what makes ties count as half.
    values, inverse, counts = np.unique(combined, return_inverse=True, return_counts=True)
    totals = np.zeros(len(values))
    np.add.at(totals, inverse, ranks)
    ranks = (totals / counts)[inverse]
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2)
                 / (len(pos) * len(neg)))


def load_space(root: Path, data: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Keys, the centred matrix and the persisted subsample rows for one universe.

    Args:
        root: The version root.
        data: The data directory.

    Returns:
        ``(keys, vectors, indices)``.
    """
    from thema.ontology.universe import load_centred

    keys, vectors = load_centred(root, data / "pathways.tsv")
    return list(keys), np.ascontiguousarray(vectors), np.load(root / "subsamples" / "indices.npy")


def sample_scrambles(path: Path, rng: np.random.Generator) -> tuple[list[set[int]], list[int],
                                                                    list[float]]:
    """Up to :data:`SAMPLE_PER_BAND` scrambled candidates per band from one cached side.

    Args:
        path: The cached scramble side.
        rng: The sampler.

    Returns:
        ``(member sets, sizes, supports)``.
    """
    from thema.ontology import bitset as bits

    with np.load(path) as handle:
        blocks = handle["blocks"]
        supports = np.round(handle["supports"].astype(np.float64), 6)
    sizes = np.bitwise_count(blocks).sum(axis=1).astype(np.int64)
    picked: list[int] = []
    for low, high in BANDS:
        here = np.flatnonzero((sizes >= low) & (sizes <= high))
        if len(here) > SAMPLE_PER_BAND:
            here = rng.choice(here, SAMPLE_PER_BAND, replace=False)
        picked.extend(int(i) for i in here)
    picked.sort()
    return ([set(bits.unpack(blocks[i])) for i in picked],
            [int(sizes[i]) for i in picked],
            [float(supports[i]) for i in picked])


def run_stability(args: argparse.Namespace) -> dict[str, object]:
    """Arm B steps 1 to 3: the stability table, the noise check and T.

    Args:
        args: Parsed arguments.

    Returns:
        The table, the noise figures and the cut.
    """
    import recursive_top_O50 as rt
    from thema.cluster import distances
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.v04 import stratum_of

    clock = time.perf_counter()
    keys, vectors, indices = load_space(args.x2, args.data)
    n = len(keys)
    position = {key: i for i, key in enumerate(keys)}
    rows = [np.sort(indices[r]) for r in range(args.runs)]
    nodes, members = rt.read_build(args.o50s)
    themes = {node: one for node, one in members.items() if len(one) >= FROM_SIZE}
    print(f"ARM B STEP 1: stability over {args.runs} rebuilt dendrograms, universe x2 "
          f"({n:,} pathways, draw {len(rows[0]):,})")
    print(f"  O50s final themes of {FROM_SIZE}+: {len(themes)}", flush=True)

    import o50s_build as o50s
    floors = json.loads((args.o50s / "floors_o50s.json").read_text())["solved"]
    with np.load(args.x2 / "calibration" / "real.npz") as handle:
        blocks = handle["blocks"]
        supports = np.round(handle["supports"].astype(np.float64), 6)
    cand_sizes = np.bitwise_count(blocks).sum(axis=1).astype(np.int64)
    need = np.array([floors[stratum_of(int(s), o50s.O50S_STRATA)]["effective"] or np.inf
                     for s in cand_sizes])
    gated = np.flatnonzero((supports >= need) & (cand_sizes >= FROM_SIZE))
    print(f"  real GATED candidates of {FROM_SIZE}+: {len(gated):,}", flush=True)

    order = sorted(themes)
    groups = [{position[k] for k in themes[node]} for node in order]
    groups += [set(bits.unpack(blocks[i])) for i in gated]
    full = distances(vectors)
    scores = stability(groups, full, n, rows)
    del full
    theme_mean = scores[:len(order)].mean(axis=1)
    cand_mean = scores[len(order):].mean(axis=1)
    cand_size = [int(cand_sizes[i]) for i in gated]
    cand_support = [float(supports[i]) for i in gated]
    print(f"  real side done ({time.perf_counter() - clock:.0f}s)", flush=True)

    rng = np.random.default_rng(SAMPLE_SEED)
    lkeys, lvectors, lindices = load_space(args.leaves, args.data)
    ln = len(lkeys)
    lrows = [np.sort(lindices[r]) for r in range(args.runs)]
    noise: dict[str, list[float]] = {label(a, b): [] for a, b in BANDS}
    noise_support: dict[str, list[float]] = {label(a, b): [] for a, b in BANDS}
    print(f"\n  NOISE CHECK: {len(NOISE_SEEDS)} scrambles, each against its own {args.runs} runs, "
          f"universe L ({ln:,} pathways, draw {len(lrows[0]):,})", flush=True)
    for seed in NOISE_SEEDS:
        side = args.leaves / "calibration" / f"seed{seed:05d}.npz"
        picked, sizes, sups = sample_scrambles(side, rng)
        scrambled = np.ascontiguousarray(null_embeddings(lvectors, seed))
        got = stability(picked, distances(scrambled), ln, lrows, report=False)
        means = got.mean(axis=1)
        for value, size, support in zip(means.tolist(), sizes, sups, strict=True):
            name = band_of(size)
            if name:
                noise[name].append(float(value))
                noise_support[name].append(support)
        print(f"    seed {seed}: {len(picked):,} sampled "
              f"({time.perf_counter() - clock:.0f}s cumulative)", flush=True)
        del scrambled, got

    table = []
    for low, high in BANDS:
        name = label(low, high)
        here = [float(v) for node, v in zip(order, theme_mean.tolist(), strict=True)
                if band_of(len(themes[node])) == name]
        p25, mid, p75 = quartiles(here)
        cand_here = [v for v, s in zip(cand_mean.tolist(), cand_size, strict=True)
                     if band_of(s) == name]
        cand_sup_here = [v for v, s in zip(cand_support, cand_size, strict=True)
                         if band_of(s) == name]
        null_here = noise[name]
        null_sup = noise_support[name]
        table.append({
            "band": name, "low": low,
            "n_themes": len(here), "p25": round(p25, 4), "median": round(mid, 4),
            "p75": round(p75, 4),
            "n_gated": len(cand_here),
            "gated_median": round(float(np.median(cand_here)), 4) if cand_here else None,
            "n_null": len(null_here),
            "null_median": round(float(np.median(null_here)), 4) if null_here else None,
            "null_p95": round(float(np.percentile(null_here, 95)), 4) if null_here else None,
            "cut_above_null_p95": (bool(CUT > float(np.percentile(null_here, 95)))
                                   if null_here else None),
            "auc_stability": auc(cand_here, null_here),
            "auc_support": auc(cand_sup_here, null_sup),
        })
    below = [entry for entry in table if entry["n_themes"] and entry["median"] < CUT]
    below_alt = [entry for entry in table if entry["n_themes"] and entry["median"] < CUT_ALT]
    return {
        "table": table,
        "T": below[0]["low"] if below else None,
        "T_band": below[0]["band"] if below else None,
        "T_alt": below_alt[0]["low"] if below_alt else None,
        "T_alt_band": below_alt[0]["band"] if below_alt else None,
        "cut": CUT, "cut_alt": CUT_ALT,
        "sample_per_band": SAMPLE_PER_BAND, "sample_seed": SAMPLE_SEED,
        "noise_seeds": list(NOISE_SEEDS),
        "theme_stability": {node: round(float(v), 4)
                            for node, v in zip(order, theme_mean.tolist(), strict=True)},
        "seconds": round(time.perf_counter() - clock, 1),
    }


def show_stability(got: Mapping[str, object]) -> None:
    """Print the stability table, the noise check and T.

    Args:
        got: What :func:`run_stability` returned.
    """
    print("\n" + "=" * 118)
    print("ARM B STEPS 1-3: STABILITY (Hennig clusterwise Jaccard), THE NOISE CHECK AND T")
    print("=" * 118)
    print(f"  {'band':<10}{'themes':>8}{'p25':>8}{'MEDIAN':>9}{'p75':>8}"
          f"{'gated n':>9}{'gated med':>11}"
          f"{'null n':>8}{'null med':>10}{'null p95':>10}"
          f"{'0.6 > p95':>11}{'AUC stab':>10}{'AUC supp':>10}")
    for entry in got["table"]:
        def cell(key: str, places: int = 4, width: int = 10,
                 row: Mapping[str, object] = entry) -> str:
            """One numeric cell, or a dash."""
            value = row[key]
            return f"{'-':>{width}}" if value is None else f"{value:>{width}.{places}f}"
        print(f"  {entry['band']:<10}{entry['n_themes']:>8,}"
              + cell("p25", 3, 8) + cell("median", 3, 9) + cell("p75", 3, 8)
              + f"{entry['n_gated']:>9,}" + cell("gated_median", 3, 11)
              + f"{entry['n_null']:>8,}" + cell("null_median", 3, 10)
              + cell("null_p95", 3, 10)
              + f"{('yes' if entry['cut_above_null_p95'] else 'NO'):>11}"
              + cell("auc_stability", 3, 10) + cell("auc_support", 3, 10))
    print(f"\n  sampling: at most {got['sample_per_band']} scrambled candidates per band per seed, "
          f"seed {got['sample_seed']}, over scrambles {got['noise_seeds']}")
    if got["T"] is None:
        print(f"  NO BAND has a median stability below {got['cut']}: there is no cut, and arm B's "
              "steps 4-5 are skipped by the declaration.")
    else:
        print(f"  T = {got['T']}: the lower edge of {got['T_band']}, the first band with a median "
              f"below {got['cut']}")
    if got["T_alt"] is None:
        print(f"  at {got['cut_alt']} there would be no cut either")
    else:
        print(f"  at {got['cut_alt']} the cut would be {got['T_alt']} ({got['T_alt_band']})")


def items_for(arm: str, nodes: Mapping[str, Mapping[str, str]],
              members: Mapping[str, set[str]], cut: int | None,
              every: Sequence[str]) -> tuple[list[str], list[set[str]], list[float], list[int]]:
    """The arm's items.

    Arm A is rec2fix's own rule: the maximal nodes that are not grab-bags, which ``units_of``
    computes. Arm B takes the themes **below the measured cut** that are not strictly inside
    another such theme, plus any pathway none of them holds.

    Args:
        arm: ``"A"`` or ``"B"``.
        nodes: O50s node rows.
        members: O50s node to member keys.
        cut: Arm B's cut T; ignored for arm A.
        every: Every pathway key.

    Returns:
        ``(ids, member sets, supports, anchor positions)``.
    """
    import recursive_top_O50 as rt
    import recursive_top_O50_rec2 as r2

    if arm == "A":
        units, _giants, _giant_only, loose = rt.units_of(dict(nodes), dict(members))
        ids = list(units) + [f"loose:{key}" for key in loose]
        held = [set(members[node]) for node in units] + [{key} for key in loose]
        support = ([float(nodes[node]["support"]) for node in units] + [0.0] * len(loose))
        anchors = [i for i, one in enumerate(held) if len(one) > r2.ANCHOR_PATHWAYS]
        return ids, held, support, anchors
    small = {node: set(one) for node, one in members.items() if len(one) < cut}
    # Maximality by bitset rather than by 28 million Python set comparisons: one vectorised pass
    # per candidate asks whether any other sub-cut theme strictly contains it.
    from thema.ontology import bitset as bits

    order = sorted(small)
    index = {key: i for i, key in enumerate(every)}
    width = bits.words_for(len(every)) * bits.WORD
    stack = np.vstack([bits.pack(sorted(index[k] for k in small[node]), width)[None, :]
                       for node in order])
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    inside = np.zeros(len(order), dtype=bool)
    for position in range(len(order)):
        covered = np.bitwise_count(stack[position][None, :] & ~stack).sum(axis=1) == 0
        inside[position] = bool((covered & (sizes > sizes[position])).any())
    maximal = [order[i] for i in range(len(order)) if not inside[i]]
    covered = {key for node in maximal for key in small[node]}
    loose = sorted(set(every) - covered)
    ids = list(maximal) + [f"loose:{key}" for key in loose]
    held = [small[node] for node in maximal] + [{key} for key in loose]
    support = [float(nodes[node]["support"]) for node in maximal] + [0.0] * len(loose)
    return ids, held, support, []


def build_arm(args: argparse.Namespace, arm: str) -> int:
    """One arm: the items, the areas pass, the combined structure and the reviewer tables.

    Args:
        args: Parsed arguments.
        arm: ``"A"`` or ``"B"``.

    Returns:
        0.
    """
    import areas_rec2fix as fix
    import recursive_top_O50 as rt
    from thema.ontology.universe import load_centred

    clock = time.perf_counter()
    nodes, members = rt.read_build(args.o50s)
    every = sorted({key for one in members.values() for key in one})
    cut = None
    if arm == "B":
        record = json.loads((args.out / "stability.json").read_text())
        cut = record["T"]
        if cut is None:
            print("  arm B has no cut: steps 4-5 are skipped by the declaration")
            return 0
        print(f"  arm B: the cut is T = {cut}, from {args.out / 'stability.json'}")
    ids, held, support, anchors = items_for(arm, nodes, members, cut, every)
    level = [i for i in range(len(ids)) if i not in set(anchors)]
    sizes = [len(one) for one in held]
    print(f"ARM {arm}: {len(ids)} items, {len(anchors)} anchors, {len(level)} clustered")
    print(f"  item sizes {min(sizes)}/{int(np.median(sizes))}/{max(sizes)}; "
          f"sum {sum(sizes):,} against {len(every):,} pathways "
          f"-> {sum(sizes) / len(every):.2f}x double counting", flush=True)
    if arm == "B":
        dropped = sorted(node for node, one in members.items() if len(one) >= cut)
        print(f"  dropped (T or more): {len(dropped)} themes, kept for comparison only",
              flush=True)

    # The 25 sides are the expensive part, about six minutes, and they are a pure function of the
    # items and the run count. Cached so a failure downstream does not pay for them twice; the
    # cache key carries both, so a different item set never reads the wrong one.
    cache = args.out / f"areas_{arm}_{len(level)}items_{args.runs}runs.json"
    if cache.is_file():
        got = json.loads(cache.read_text())
        got["confirmed"]["strata"] = list(got["confirmed"]["strata"])
        print(f"  areas from {cache} ({len(got['pathway_members'])} areas, cached)", flush=True)
    else:
        keys, vectors = load_centred(args.x2, args.data / "pathways.tsv")
        centroids = rt.unit_centroids([held[i] for i in level], keys, vectors)
        got = fix.build_areas(centroids, [held[i] for i in level], args.runs)
        args.out.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(got) + "\n", encoding="utf-8")
    if not got["pathway_members"]:
        print("  nothing through the gate; this arm builds no areas")
        return 0
    area_units = [[level[i] for i in rows] for rows in got["unit_indices"]]
    print(f"  {len(got['pathway_members'])} areas", flush=True)
    comb = fix.combine(got["pathway_members"], area_units, got["supports"], ids, held,
                       support, anchors, level, drop_giants=False)
    return write_arm(args, arm, nodes, members, every, ids, held, cut, got, comb, clock)


def main(argv: list[str] | None = None) -> int:
    """Run the stability pass, arm A, or arm B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--x2", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--leaves", type=Path, default=Path("data/ontology/v0.4-leaves"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_top"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--stability", action="store_true",
                        help="arm B steps 1-3 only: the stability table, the noise check and T")
    parser.add_argument("--arm", choices=("A", "B"), default=None)
    parser.add_argument("--review", type=Path,
                        default=Path("data/experiments/top_two_arms_2026-10-17"))
    args = parser.parse_args(argv)

    if args.stability:
        got = run_stability(args)
        show_stability(got)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "stability.json").write_text(json.dumps(got, indent=2) + "\n",
                                                 encoding="utf-8")
        with (args.out / "stability.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, delimiter="\t", lineterminator="\n",
                fieldnames=["band", "low", "n_themes", "p25", "median", "p75", "n_gated",
                            "gated_median", "n_null", "null_median", "null_p95",
                            "cut_above_null_p95", "auc_stability", "auc_support"])
            writer.writeheader()
            for entry in got["table"]:
                writer.writerow({k: ("" if entry[k] is None else entry[k])
                                 for k in writer.fieldnames})
        print(f"\n  -> {args.out / 'stability.json'} and stability.tsv "
              f"({got['seconds']:.0f}s)")
        return 0
    if args.arm:
        return build_arm(args, args.arm)
    parser.error("pass --stability or --arm")
    return 2


def write_arm(args: argparse.Namespace, arm: str, nodes: Mapping[str, Mapping[str, str]],
              members: Mapping[str, set[str]], every: Sequence[str], ids: Sequence[str],
              held: Sequence[set[str]], cut: int | None, got: Mapping[str, object],
              comb: Mapping[str, object], clock: float) -> int:
    """Write one arm's build, its report section and the reviewer's three tables.

    Args:
        args: Parsed arguments.
        arm: ``"A"`` or ``"B"``.
        nodes: O50s node rows.
        members: O50s node to member keys.
        every: Every pathway key.
        ids: Item ids.
        held: Item member sets.
        cut: Arm B's cut, or None.
        got: What ``build_areas`` returned.
        comb: What ``combine`` returned.
        clock: Start time.

    Returns:
        0.
    """
    import areas_rec2fix as fix

    out = args.out / arm
    out.mkdir(parents=True, exist_ok=True)
    review = args.review / arm
    review.mkdir(parents=True, exist_ok=True)

    kinds = dict(zip(comb["ids"], comb["kinds"], strict=True))
    units_of_node = dict(zip(comb["ids"], comb["units"], strict=True))
    support_of = dict(zip(comb["ids"], comb["support"], strict=True))
    area_keys = {node: set(keys) for node, keys
                 in zip([comb["ids"][i] for i in range(len(got["pathway_members"]))],
                        got["pathway_members"], strict=True)}
    item_keys = {ids[i]: held[i] for i in range(len(ids))}

    def keys_of(node: str) -> set[str]:
        """Any combined node's pathway set."""
        return area_keys[node] if kinds[node] == "area" else item_keys[node]

    view = list(comb["view"])
    roots = [comb["ids"][view[i]] for i in range(len(view)) if not comb["edges"][i].any()]
    parents = {comb["ids"][view[c]]: [comb["ids"][view[p]]
                                      for p in np.flatnonzero(comb["edges"][c])]
               for c in range(len(view))}
    children: dict[str, list[str]] = {comb["ids"][n]: [] for n in view}
    for child, above in parents.items():
        for parent in above:
            children[parent].append(child)
    counts = [len(children[comb["ids"][n]]) for n in view]
    view_keys = {comb["ids"][n]: keys_of(comb["ids"][n]) for n in view}
    giants = sorted((n for n in view_keys if len(view_keys[n]) > fix.GIANT_AREA),
                    key=lambda n: -len(view_keys[n]))

    print(f"\n  ARM {arm} STRUCTURE: {len(view):,} nodes, {len(roots)} roots, "
          f"{int(comb['edges'].sum()):,} direct edges; children max {max(counts, default=0)}, "
          f"median {statistics.median(counts):.0f}; "
          f"{len(giants)} nodes over {fix.GIANT_AREA:,} pathways (kept, flagged)", flush=True)

    small = [n for n in roots if len(view_keys[n]) <= SMALL_ROOT]
    bigger = {n: view_keys[n] for n in view_keys}
    containing: dict[str, list[dict[str, object]]] = {}
    for node in small:
        mine = view_keys[node]
        scored = []
        for other, keys in bigger.items():
            if other == node or len(keys) <= len(mine):
                continue
            scored.append((len(mine & keys) / len(mine), other, len(keys), len(mine - keys)))
        scored.sort(reverse=True)
        containing[node] = [
            {"node": o, "size": s, "share": round(share, 4), "missing": miss}
            for share, o, s, miss in scored[:3]]

    pairs = list(itertools.combinations(sorted(roots), 2))
    dup = []
    for a, b in pairs:
        ka, kb = view_keys[a], view_keys[b]
        value = len(ka & kb) / len(ka | kb) if (ka or kb) else 0.0
        if value >= PAIR_J:
            dup.append((round(value, 4), a, len(ka), b, len(kb)))
    dup.sort(reverse=True)
    mostly = []
    for node in roots:
        mine = view_keys[node]
        for other, keys in view_keys.items():
            if other == node or len(keys) <= len(mine):
                continue
            share = len(mine & keys) / len(mine)
            if share >= INSIDE:
                mostly.append((round(share, 4), node, len(mine), other, len(keys)))
    mostly.sort(reverse=True)

    payload = {
        "arm": arm, "o50s": str(args.o50s), "cut": cut,
        "n_items": len(ids), "item_ids": list(ids),
        "n_areas": len(area_keys), "area_members": {k: sorted(v) for k, v in area_keys.items()},
        "area_units": {comb["ids"][i]: [ids[u] for u in units_of_node[comb["ids"][i]]]
                       for i in range(len(area_keys))},
        "kinds": kinds, "support": support_of,
        "view": [comb["ids"][n] for n in view], "roots": roots,
        "parents": parents, "children": children,
        "giants": giants,
        "small_roots": containing,
        "duplication": {"root_pairs_ge_0.5": dup, "roots_80_inside": mostly},
        "floors": got["floors"], "confirmed": got["confirmed"],
        "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
        "n_after_consensus": got["n_after_consensus"], "repair": got["repair"],
        "seams": comb["seams"], "collapsed": comb["collapsed"], "merged": comb["merged"],
        "n_direct_edges": int(comb["edges"].sum()),
        "n_closure_pairs": int(comb["closure"].sum()),
        "children_max": max(counts, default=0),
        "children_median": float(statistics.median(counts)) if counts else 0.0,
        "seconds": round(time.perf_counter() - clock, 1),
    }
    (out / "levels.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with (out / "nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "kind", "size", "n_units", "support",
                                            "giant", "root", "n_parents", "n_children"])
        writer.writeheader()
        for node in payload["view"]:
            writer.writerow({
                "node": node, "kind": kinds[node], "size": len(view_keys[node]),
                "n_units": len(units_of_node[node]),
                "support": round(float(support_of[node]), 6),
                "giant": "true" if node in set(giants) else "",
                "root": "true" if node in set(roots) else "",
                "n_parents": len(parents[node]), "n_children": len(children[node])})
    with (out / "edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for child, above in sorted(parents.items()):
            for parent in sorted(above):
                handle.write(f"{parent}\t{child}\n")

    with (review / "roots.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "kind", "size", "n_children", "members"])
        writer.writeheader()
        for node in sorted(roots, key=lambda n: -len(view_keys[n])):
            writer.writerow({"node": node, "kind": kinds[node], "size": len(view_keys[node]),
                             "n_children": len(children[node]),
                             "members": " ".join(sorted(view_keys[node]))})
    with (review / "small_roots.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["root", "root_size", "root_members", "rank", "container",
                        "container_size", "share", "missing", "container_members"])
        writer.writeheader()
        for node in sorted(small, key=lambda n: -len(view_keys[n])):
            for rank, entry in enumerate(containing[node], 1):
                writer.writerow({
                    "root": node, "root_size": len(view_keys[node]),
                    "root_members": " ".join(sorted(view_keys[node])),
                    "rank": rank, "container": entry["node"],
                    "container_size": entry["size"], "share": entry["share"],
                    "missing": entry["missing"],
                    "container_members": " ".join(sorted(view_keys[entry["node"]]))})
    with (review / "areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "n_units", "support", "giant", "root", "units",
                        "members"])
        writer.writeheader()
        for node in sorted(area_keys, key=lambda n: -len(area_keys[n])):
            if node not in view_keys:
                continue
            writer.writerow({
                "node": node, "size": len(area_keys[node]),
                "n_units": len(units_of_node[node]),
                "support": round(float(support_of[node]), 6),
                "giant": "true" if node in set(giants) else "",
                "root": "true" if node in set(roots) else "",
                "units": " ".join(payload["area_units"][node]),
                "members": " ".join(sorted(area_keys[node]))})
    print(f"  -> {out} and {review}  ({payload['seconds']:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
