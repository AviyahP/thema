#!/usr/bin/env python3
"""Test R stage 3: calibrate the gap gate, then every report item. EXPLORATORY.

Spec: `docs/spec/test-R-2026-10-07.md`. Nothing here is part of the declared protocol.

**The unit this works in, stated because it is the one substitution Test R makes.** The scores are
per-GROUPING: `h_full` is defined over "runs where g is found", which is a property of a pool
grouping and of nothing downstream. The floors, by contrast, are applied by the build to completed
FAMILIES. So every number below -- for the fixed cut, for the floors and for the gap gate alike --
is computed on pool groupings, which makes the comparison internally valid while making it NOT
interchangeable with Test F's family-level FDR. The size of that gap is itself reported, because it
turned out to be large and to have a mechanism.

Usage::

    uv run scripts/test_r.py --report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Size strata the per-size threshold is set on, and the bands item 5 reports.
STRATA: tuple[tuple[int, int], ...] = ((3, 3), (4, 4), (5, 5), (6, 6), (7, 9))
BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))

#: Calibration and held-out scramble seeds, and the declared FDR caps.
CALIBRATION = (3001, 3002, 3003)
HELDOUT = (4001, 4002, 4003, 4004, 4005)
MAX_OVERALL = 0.01
MAX_STRATUM = 0.02

#: The ratio the gap threshold is solved to, from the spec.
TARGET_RATIO = 0.01


#: Arm A's 3-seed floors, from Test F (`docs/status/2026-10-07-test-F.md`). Support thresholds, the
#: effective value the build would apply, so `max(0.33, floor)`.
FLOORS_3SEED: dict[str, float] = {"3-3": 0.790, "4-4": 0.910, "5-5": 0.410,
                                  "6-6": 0.330, "7-9": 0.330}


def curated_sets(data: Path, keys: list[str]) -> list[set[int]]:
    """Every curated Reactome or GO BP set: a node plus all its descendants, as E1 defines it.

    Args:
        data: The data directory.
        keys: Universe keys in row order.

    Returns:
        One index set per curated node with at least three members in the universe.
    """
    from thema.data.formats import parse_obo_terms
    from thema.data.hierarchy import read_reactome_relation
    from thema.evaluation import go_parents

    position = {k: i for i, k in enumerate(keys)}
    out: list[set[int]] = []
    for relation, prefix in (
        (read_reactome_relation(
            (data / "raw" / "ReactomePathwaysRelation.txt").read_text(
                encoding="utf-8").splitlines()), "reactome:"),
        (go_parents(parse_obo_terms(
            (data / "raw" / "go-basic.obo").read_text(encoding="utf-8").splitlines())), "go:"),
    ):
        children: dict[str, list[str]] = {}
        for child, parents in relation.items():
            for parent in parents:
                children.setdefault(parent, []).append(child)
        for node in set(relation) | set(children):
            stack, seen = [node], set()
            while stack:
                at = stack.pop()
                if at in seen:
                    continue
                seen.add(at)
                stack.extend(children.get(at, ()))
            members = {position[f"{prefix}{t}"] for t in seen if f"{prefix}{t}" in position}
            if len(members) >= 3:
                out.append(members)
    return out


def best_jaccard(groups: list[np.ndarray], curated: list[set[int]], n: int) -> np.ndarray:
    """Best-match Jaccard of each grouping against any curated set.

    An inverted index keeps this cheap: a grouping of at most nine members can only overlap the
    curated sets one of those members belongs to, so the comparison is against a handful rather than
    against all of them.

    Args:
        groups: Per grouping, its member indices.
        curated: The curated sets.
        n: Universe size.

    Returns:
        One best Jaccard per grouping.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(curated):
        for member in members:
            holders[member].append(index)
    out = np.zeros(len(groups))
    for position, members in enumerate(groups):
        want = set(members.tolist())
        candidates = {c for m in members.tolist() for c in holders[m]}
        best = 0.0
        for c in candidates:
            other = curated[c]
            inter = len(want & other)
            best = max(best, inter / (len(want) + len(other) - inter))
        out[position] = best
    return out


def load(path: Path) -> dict[str, np.ndarray]:
    """Read one side's scores.

    Args:
        path: The ``.npz`` written by ``test_r_pool.py``.

    Returns:
        The arrays.
    """
    with np.load(path) as handle:
        return {k: handle[k] for k in handle.files}


def stratum_of(size: int) -> int:
    """Which size stratum a grouping falls in.

    Args:
        size: Member count.

    Returns:
        Index into :data:`STRATA`, or -1 outside 3-9.
    """
    for index, (low, high) in enumerate(STRATA):
        if low <= size <= high:
            return index
    return -1


def solve_threshold(
    real: np.ndarray, nulls: list[np.ndarray], target: float = TARGET_RATIO
) -> float | None:
    """Lowest gap cutoff whose scrambled/real ratio is at or below ``target``.

    Mirrors the floors solver's shape: walk the observed values upward and take the first that
    holds, so the threshold is one of the data's own values rather than an interpolated one.

    Args:
        real: Real-side scores.
        nulls: One array of scrambled scores per calibration seed.
        target: The ratio to reach.

    Returns:
        The cutoff, or None if no value reaches the target.
    """
    real = real[np.isfinite(real)]
    clean = [v[np.isfinite(v)] for v in nulls]
    if not len(real):
        return None
    candidates = np.unique(np.concatenate([real] + [c for c in clean if len(c)]))
    for cut in candidates:
        kept = int((real >= cut).sum())
        if not kept:
            break
        mean_null = float(np.mean([float((c >= cut).sum()) for c in clean])) if clean else 0.0
        if mean_null / kept <= target:
            return float(cut)
    return None


def auroc(positive: np.ndarray, negative: np.ndarray) -> float:
    """AUROC of a score separating real from scrambled, ties counted half.

    Args:
        positive: Real-side scores.
        negative: Scrambled scores.

    Returns:
        The AUROC, or NaN when either side is empty.
    """
    a = positive[np.isfinite(positive)]
    b = negative[np.isfinite(negative)]
    if not len(a) or not len(b):
        return float("nan")
    order = np.sort(b)
    less = np.searchsorted(order, a, side="left")
    equal = np.searchsorted(order, a, side="right") - less
    return float(np.mean((less + 0.5 * equal) / len(order)))


def main(argv: list[str] | None = None) -> int:
    """Calibrate and report.

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
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe = meta["universe_digest"]
    scores = root / "trees" / f"{args.space}_{universe}" / "heights"

    def side(name: str, suffix: str = "") -> dict[str, np.ndarray] | None:
        """Load a side's scores if present.

        Args:
            name: ``real`` or a seed.
            suffix: ``_all`` for the all-sizes pass.

        Returns:
            The arrays, or None.
        """
        path = scores / f"scores_{name}_n{args.runs:03d}{suffix}.npz"
        return load(path) if path.is_file() else None

    real = side("real")
    if real is None:
        print("the real side has not been scored yet")
        return 1
    cal = {s: side(str(s)) for s in CALIBRATION}
    held = {s: side(str(s)) for s in HELDOUT}
    missing = [s for s, v in {**cal, **held}.items() if v is None]
    if missing:
        print(f"  not yet scored: {missing}")
    cal = {s: v for s, v in cal.items() if v is not None}
    held = {s: v for s, v in held.items() if v is not None}

    report: dict = {"unit": "pool groupings, not completed families",
                    "target_ratio": TARGET_RATIO, "max_overall": MAX_OVERALL,
                    "max_stratum": MAX_STRATUM,
                    "calibration": sorted(cal), "heldout": sorted(held)}
    print(f"TEST R stage 3  real {len(real['sizes']):,} groupings 3-9 at support >= 0.33")
    print(f"  calibration {sorted(cal)}, held-out {sorted(held)}")
    print("  UNIT: pool groupings. The floors are applied to completed FAMILIES, so these")
    print("  numbers are internally comparable but NOT interchangeable with Test F.", flush=True)

    # ---- per-size and single thresholds, on the calibration seeds only
    per_size: dict[str, float | None] = {}
    for index, (low, high) in enumerate(STRATA):
        pick = np.array([stratum_of(int(s)) == index for s in real["sizes"]])
        nulls = [v["g_loo"][np.array([stratum_of(int(s)) == index for s in v["sizes"]])]
                 for v in cal.values()]
        per_size[f"{low}-{high}"] = solve_threshold(real["g_loo"][pick], nulls)
    single = solve_threshold(real["g_loo"], [v["g_loo"] for v in cal.values()])
    report["t_per_size"] = per_size
    report["t_single"] = single
    print(f"\n  GAP THRESHOLDS from {sorted(cal)}, ratio <= {TARGET_RATIO}")
    for band, value in per_size.items():
        print(f"    t[{band}] = {'none reaches the target' if value is None else f'{value:.4f}'}")
    print(f"    single t  = {'none reaches the target' if single is None else f'{single:.4f}'}")

    # ---- AUROC per size, three scores
    print("\n  AUROC separating real from scrambled, per size (calibration seeds pooled)")
    print(f"    {'size':<8}{'n real':>9}{'n null':>9}{'G_loo':>9}{'G_life':>9}{'support':>9}")
    auc: dict[str, dict[str, float]] = {}
    for index, (low, high) in enumerate(STRATA):
        pick = np.array([stratum_of(int(s)) == index for s in real["sizes"]])
        nmask = {s: np.array([stratum_of(int(x)) == index for x in v["sizes"]])
                 for s, v in cal.items()}
        row = {}
        for field in ("g_loo", "g_life", "support"):
            neg = (np.concatenate([v[field][nmask[s]] for s, v in cal.items()])
                   if cal else np.zeros(0))
            row[field] = auroc(real[field][pick], neg)
        auc[f"{low}-{high}"] = row
        n_null = int(sum(int(m.sum()) for m in nmask.values()))
        print(f"    {low}-{high:<6}{int(pick.sum()):>9,}{n_null:>9,}"
              f"{row['g_loo']:>9.4f}{row['g_life']:>9.4f}{row['support']:>9.4f}")
    report["auroc"] = auc

    # ---- items 1 and 2: held-out FDR and real kept, floors vs gap
    def keep_mask(data: dict[str, np.ndarray], gate: str,
                  t: dict[str, float | None] | float | None) -> np.ndarray:
        """Which groupings a gate keeps.

        Args:
            data: One side's scores.
            gate: ``fixed``, ``floors``, ``gap`` or ``gap_single``.
            t: Per-size thresholds, or one value, or None.

        Returns:
            Boolean mask over the side's groupings.
        """
        support_ok = data["support"] >= 0.33
        if gate == "fixed":
            return support_ok
        bands = np.array([stratum_of(int(x)) for x in data["sizes"]])
        if gate == "floors":
            need = np.array([FLOORS_3SEED[f"{STRATA[b][0]}-{STRATA[b][1]}"] if b >= 0 else 2.0
                             for b in bands])
            return data["support"] >= need
        score = data["g_loo"]
        if gate == "gap_single":
            return support_ok & np.isfinite(score) & (score >= (t if t is not None else np.inf))
        cuts = np.array([
            (t.get(f"{STRATA[b][0]}-{STRATA[b][1]}") if b >= 0 else None) or np.inf
            for b in bands
        ])
        return support_ok & np.isfinite(score) & (score >= cuts)

    gates = {"fixed 0.33": ("fixed", None), "floors (3-seed)": ("floors", None),
             "gap per-size t": ("gap", per_size), "gap single t": ("gap_single", single)}
    print(f"\n  ITEM 1 -- held-out FDR on {sorted(held)}, pool groupings, sizes 3-9")
    print(f"    {'gate':<17}{'real kept':>11}{'mean null':>11}{'FDR':>9}"
          f"{'worst stratum':>15}   verdict")
    item1: dict[str, dict] = {}
    for name, (gate, t) in gates.items():
        rk = keep_mask(real, gate, t)
        nulls = [keep_mask(v, gate, t) for v in held.values()] if held else []
        per: dict[str, float | None] = {}
        for index, (low, high) in enumerate(STRATA):
            rm = rk & np.array([stratum_of(int(x)) == index for x in real["sizes"]])
            r = int(rm.sum())
            f = float(np.mean([
                int((m & np.array([stratum_of(int(x)) == index for x in v["sizes"]])).sum())
                for m, v in zip(nulls, held.values(), strict=True)
            ])) if nulls else 0.0
            per[f"{low}-{high}"] = round(f / r, 5) if r else None
        total_r = int(rk.sum())
        total_f = float(np.mean([int(m.sum()) for m in nulls])) if nulls else 0.0
        overall = total_f / total_r if total_r else None
        worst = max((v for v in per.values() if v is not None), default=None)
        ok = (overall is not None and overall <= MAX_OVERALL
              and worst is not None and worst <= MAX_STRATUM)
        item1[name] = {"real_kept": total_r, "mean_null": round(total_f, 2),
                       "overall_fdr": None if overall is None else round(overall, 5),
                       "per_stratum": per, "worst": worst, "passes": bool(ok)}
        print(f"    {name:<17}{total_r:>11,}{total_f:>11.1f}"
              f"{(overall if overall is not None else float('nan')):>9.5f}"
              f"{(worst if worst is not None else float('nan')):>15.5f}   "
              f"{'PASSES' if ok else 'FAILS'}")
    report["item1"] = item1

    print("\n  ITEM 2 -- real groupings kept, and the overlap")
    floors_mask = keep_mask(real, "floors", None)
    gap_mask = keep_mask(real, "gap", per_size)
    single_mask = keep_mask(real, "gap_single", single)
    print(f"    {'size':<8}{'floors':>9}{'gap(t_s)':>10}{'both':>9}"
          f"{'floors only':>13}{'gap only':>10}{'gap(single)':>12}")
    item2: dict[str, dict] = {}
    for index, (low, high) in enumerate(STRATA):
        band = np.array([stratum_of(int(x)) == index for x in real["sizes"]])
        f, g, sg = floors_mask & band, gap_mask & band, single_mask & band
        row = {"floors": int(f.sum()), "gap": int(g.sum()), "both": int((f & g).sum()),
               "floors_only": int((f & ~g).sum()), "gap_only": int((g & ~f).sum()),
               "gap_single": int(sg.sum())}
        item2[f"{low}-{high}"] = row
        print(f"    {low}-{high:<6}{row['floors']:>9,}{row['gap']:>10,}{row['both']:>9,}"
              f"{row['floors_only']:>13,}{row['gap_only']:>10,}{row['gap_single']:>12,}")
    totals = {k: sum(r[k] for r in item2.values()) for k in next(iter(item2.values()))}
    print(f"    {'TOTAL':<8}{totals['floors']:>9,}{totals['gap']:>10,}{totals['both']:>9,}"
          f"{totals['floors_only']:>13,}{totals['gap_only']:>10,}{totals['gap_single']:>12,}")
    report["item2"] = {"per_size": item2, "totals": totals}

    # ---- item 3: quality proxy
    from thema.ontology.universe import load_embedded
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    curated = curated_sets(args.data, keys)
    print(f"\n  ITEM 3 -- quality proxy: {len(curated):,} curated Reactome and GO BP sets")
    groups = [np.asarray(np.flatnonzero(np.unpackbits(
        real["groupings"][i].view(np.uint8), bitorder="little")[:n]), dtype=np.int64)
        for i in range(len(real["sizes"]))]
    jac = best_jaccard(groups, curated, n)
    print(f"    {'set':<17}{'n':>9}{'share best-match J > 0.5':>27}")
    item3 = {}
    for name, mask in (("floors", floors_mask), ("gap per-size t", gap_mask),
                       ("gap single t", single_mask),
                       ("floors only", floors_mask & ~gap_mask),
                       ("gap only", gap_mask & ~floors_mask)):
        share = float((jac[mask] > 0.5).mean()) if mask.any() else float("nan")
        item3[name] = {"n": int(mask.sum()), "share_above_half": round(share, 4)}
        print(f"    {name:<17}{int(mask.sum()):>9,}{share:>26.1%}")
    report["item3"] = item3

    rng = np.random.default_rng(0)
    info = {p.key: p.name for p in __import__("thema.data.pathways", fromlist=["x"])
            .PathwayCollection.from_tsv_text(
                (args.data / "pathways.tsv").read_text(encoding="utf-8")).pathways}
    examples: dict[str, list] = {}
    for name, mask in (("gap only", gap_mask & ~floors_mask),
                       ("floors only", floors_mask & ~gap_mask)):
        where = np.flatnonzero(mask)
        pick = rng.choice(where, size=min(10, len(where)), replace=False) if len(where) else []
        shown = []
        print(f"\n    10 random examples, {name.upper()}:")
        for i in np.atleast_1d(pick).tolist():
            titles = [info.get(keys[m], keys[m]) for m in groups[i].tolist()]
            shown.append({"size": int(real["sizes"][i]), "support": float(real["support"][i]),
                          "g_loo": float(real["g_loo"][i]), "best_jaccard": float(jac[i]),
                          "titles": titles})
            head = "; ".join(t[:46] for t in titles[:3])
            print(f"      size {int(real['sizes'][i])} support {real['support'][i]:.2f} "
                  f"G_loo {real['g_loo'][i]:.2f} J {jac[i]:.2f} | {head}")
        examples[name] = shown
    report["item3_examples"] = examples

    # ---- item 5: one rule for every size
    every = side("real", "_all")
    if every is not None and single is not None:
        print(f"\n  ITEM 5 (report only) -- the single t = {single:.4f} applied to EVERY size")
        groups_all = [np.asarray(np.flatnonzero(np.unpackbits(
            every["groupings"][i].view(np.uint8), bitorder="little")[:n]), dtype=np.int64)
            for i in range(len(every["sizes"]))]
        jac_all = best_jaccard(groups_all, curated, n)
        removed = np.isfinite(every["g_loo"]) & (every["g_loo"] < single)
        print(f"    {'band':<10}{'groupings':>11}{'removed':>10}{'share':>8}"
              f"{'J>0.5 of removed':>19}")
        item5 = {}
        for low, high in BANDS:
            band = (every["sizes"] >= low) & (every["sizes"] <= high)
            r = removed & band
            share = float(r.sum() / band.sum()) if band.any() else float("nan")
            q = float((jac_all[r] > 0.5).mean()) if r.any() else float("nan")
            item5[f"{low}-{high}"] = {"groupings": int(band.sum()), "removed": int(r.sum()),
                                      "share": round(share, 4),
                                      "quality_of_removed": round(q, 4)}
            print(f"    {low}-{high:<6}{int(band.sum()):>11,}{int(r.sum()):>10,}"
                  f"{share:>8.1%}{q:>18.1%}")
        report["item5"] = item5
    else:
        print("\n  ITEM 5: the all-sizes pass is not scored yet")

    # ---- transfer: the 10,770 thresholds applied unchanged to a new universe
    transfer_root = root / "transfer"
    if transfer_root.is_dir():
        print("\n  TRANSFER -- the 10,770 thresholds and floors applied UNCHANGED")
        report["transfer"] = {}
        for setting in sorted(d.name for d in transfer_root.iterdir() if d.is_dir()):
            t_real = load(transfer_root / setting / f"scores_real_n{args.runs:03d}.npz") \
                if (transfer_root / setting / f"scores_real_n{args.runs:03d}.npz").is_file() \
                else None
            t_null = {}
            for seed in (4001, 4002):
                path = transfer_root / setting / f"scores_{seed}_n{args.runs:03d}.npz"
                if path.is_file():
                    t_null[seed] = load(path)
            if t_real is None or not t_null:
                print(f"    {setting}: not scored yet")
                continue
            print(f"    {setting} -- real {len(t_real['sizes']):,} groupings, "
                  f"held-out {sorted(t_null)}")
            print(f"      {'gate':<17}{'real kept':>11}{'mean null':>11}{'FDR':>9}"
                  f"{'worst stratum':>15}   verdict")
            per_setting = {}
            for name, (gate, t) in gates.items():
                rk = keep_mask(t_real, gate, t)
                nulls = [keep_mask(v, gate, t) for v in t_null.values()]
                per: dict[str, float | None] = {}
                for index, (low, high) in enumerate(STRATA):
                    rm = rk & np.array([stratum_of(int(x)) == index for x in t_real["sizes"]])
                    r = int(rm.sum())
                    f = float(np.mean([
                        int((m & np.array([stratum_of(int(x)) == index
                                           for x in v["sizes"]])).sum())
                        for m, v in zip(nulls, t_null.values(), strict=True)
                    ]))
                    per[f"{low}-{high}"] = round(f / r, 5) if r else None
                total_r, total_f = int(rk.sum()), float(np.mean([int(m.sum()) for m in nulls]))
                overall = total_f / total_r if total_r else None
                worst = max((v for v in per.values() if v is not None), default=None)
                ok = overall is not None and overall <= MAX_OVERALL
                per_setting[name] = {
                    "real_kept": total_r, "mean_null": round(total_f, 2),
                    "overall_fdr": None if overall is None else round(overall, 5),
                    "per_stratum": per, "worst": worst, "overall_passes": bool(ok),
                }
                print(f"      {name:<17}{total_r:>11,}{total_f:>11.1f}"
                      f"{(overall if overall is not None else float('nan')):>9.5f}"
                      f"{(worst if worst is not None else float('nan')):>15.5f}   "
                      f"{'PASSES' if ok else 'FAILS'}")
            report["transfer"][setting] = per_setting

    # ---- the declared exploratory verdict
    print("\n  THE DECLARED EXPLORATORY VERDICT")
    floors_kept = report["item2"]["totals"]["floors"]
    floors_quality = report["item3"]["floors"]["share_above_half"]
    verdict = {}
    for name, key in (("gap per-size t", "gap per-size t"), ("gap single t", "gap single t")):
        a = report["item1"][key]["passes"]
        kept = report["item2"]["totals"]["gap" if "per-size" in name else "gap_single"]
        b = kept >= floors_kept
        c = report["item3"][key]["share_above_half"] >= floors_quality - 0.02
        settings = report.get("transfer", {})
        d_each = {s: v[key]["overall_passes"] for s, v in settings.items()}
        d = bool(d_each) and all(d_each.values()) and len(d_each) >= 2
        verdict[name] = {"a_fdr": bool(a), "b_kept": bool(b), "c_quality": bool(c),
                         "d_transfer": bool(d), "d_per_setting": d_each,
                         "kept": kept, "floors_kept": floors_kept,
                         "promising": bool(a and b and c and d)}
        print(f"    {name}: (a) FDR {'PASS' if a else 'FAIL'}   "
              f"(b) kept {kept:,} vs floors {floors_kept:,} {'PASS' if b else 'FAIL'}   "
              f"(c) quality {'PASS' if c else 'FAIL'}   "
              f"(d) transfer {'PASS' if d else 'FAIL'} {d_each}")
        print(f"      => {'PROMISING' if verdict[name]['promising'] else 'NOT PROMISING'}")
    floors_d = {s: v["floors (3-seed)"]["overall_passes"]
                for s, v in report.get("transfer", {}).items()}
    print(f"    the FLOORS on criterion (d), separately: {floors_d}")
    report["verdict"] = verdict
    report["floors_transfer"] = floors_d

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
