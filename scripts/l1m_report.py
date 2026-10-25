"""Sections A-E of prompt 64: L1m beside prompt 63's L1. Declared 24 Oct 2026.

Reads the three L1m sides, builds the strict-containment DAG with :mod:`l1_dag`'s verified
functions, and reports the comparison. Nothing here changes a build.

The two scramble sides are **indicative only**: two seeds cannot calibrate anything, and the 10-run
bar is a **provisional** working bar.

Usage:
    uv run scripts/l1m_report.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SEED = 20261024
FOUND_BAR = 10
BARS = (10, 20)
SCRAMBLE = (3001, 3002)
TOP_ROOT_MIN = 200
READ_ROOT_MIN = 100
READ_FALLBACK_MIN = 200
MAX_BATCHES = 40
BATCH_LINES = 2600
MATCH_J = 0.90

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return BANDS[0][2]


def bands_of(sizes: np.ndarray) -> np.ndarray:
    """Band labels for an array of sizes.

    Args:
        sizes: Pathway counts.

    Returns:
        Labels.
    """
    return np.array([band_of(int(s)) for s in sizes])


def load_l1m(where: Path, n: int, bar: int = FOUND_BAR) -> dict[str, object]:
    """One L1m side: every theme, and the accepted subset as a matrix.

    Args:
        where: A directory :mod:`l1m_build` wrote.
        n: Universe size.
        bar: Runs-found bar for the accepted set.

    Returns:
        ``{build, found, size, which, rows, sizes, matrix}``.
    """
    from scipy import sparse

    got: dict[str, object] = {"build": json.loads(
        (where / "build.json").read_text(encoding="utf-8"))}
    with np.load(where / "themes.npz") as handle:
        for key in handle.files:
            got[key] = handle[key]
    got["size"] = np.diff(got["member_indptr"]).astype(np.int64)
    which = np.flatnonzero(got["found"] >= bar)
    rows = [got["member_pathway"][got["member_indptr"][t]:got["member_indptr"][t + 1]]
            for t in which]
    sizes = np.array([len(r) for r in rows], dtype=np.int64)
    got["which"], got["rows"], got["sizes"] = which, rows, sizes
    got["matrix"] = sparse.csr_matrix(
        (np.ones(int(sizes.sum()), dtype=np.int32),
         np.concatenate(rows) if rows else np.zeros(0, dtype=np.int64),
         np.concatenate([[0], np.cumsum(sizes)])), shape=(len(rows), n))
    return got


def section_a(l1m: dict[str, object], l1: dict[str, object]) -> dict[str, object]:
    """A: the merge itself.

    Args:
        l1m: The L1m real side.
        l1: Prompt 61's core-merged side, as ``l1_report.load_l1`` returns.

    Returns:
        The table as data.
    """
    build = l1m["build"]
    print("=" * 104)
    print("A. THE MERGE: 90% EACH WAY ON MEMBERS, REPEATED TO A FIXED POINT")
    print("=" * 104)
    print(f"  {'pass':<8}{'themes before':>16}{'merged':>12}{'themes after':>15}"
          f"{'largest theme':>16}")
    for step, row in enumerate(build["history"]):
        print(f"  {row['pass']:<8}{row['themes_before']:>16,}{row['merges']:>12,}"
              f"{row['themes_after']:>15,}"
              f"{build['largest_after_each_pass'][step][0]:>16,}")
    print(f"  passes {build['passes']}, cap {build['max_passes']} hit: {build['capped']}")
    print()
    print(f"  {'':<34}{'L1m (members)':>16}{'L1 (cores)':>16}")
    print(f"  {'groups with a core of 3+':<34}{build['groups_with_a_core']:>16,}"
          f"{l1['steps']['cored_groups']:>16,}")
    print(f"  {'themes after the merge':<34}{build['themes']:>16,}"
          f"{l1['steps']['themes']:>16,}")
    print(f"  {'found in >= 10 runs':<34}{build['kept_at_the_bar']:>16,}"
          f"{int((l1['t_found'] >= FOUND_BAR).sum()):>16,}")
    groups = l1m["groups"]
    print(f"  {'groups per theme, median / max':<34}"
          f"{np.median(groups):>11.1f} / {int(groups.max()):<}"
          f"{np.median(l1['t_groups']):>11.1f} / {int(l1['t_groups'].max()):<}")
    rows = [l1m["member_pathway"][l1m["member_indptr"][t]:l1m["member_indptr"][t + 1]]
            for t in range(len(l1m["size"]))]
    repeats = len(rows) - len({r.tobytes() for r in rows})
    l1_rows = [l1["t_member_pathway"][l1["t_member_indptr"][t]:l1["t_member_indptr"][t + 1]]
               for t in range(len(l1["t_size"]))]
    l1_repeats = len(l1_rows) - len({r.tobytes() for r in l1_rows})
    print(f"  {'identical member sets remaining':<34}{repeats:>16,}{l1_repeats:>16,}")
    assert repeats == 0, f"{repeats} themes still repeat another theme's members"
    print("  the 0 is asserted in this script and in the build, not just reported")
    print()
    print("  the ten largest final themes, size after each pass (pass 0 is one theme per group)")
    print(f"  {'theme':<10}" + "".join(f"{'p' + str(i):>8}"
                                       for i in range(len(build["largest_after_each_pass"]))))
    for row in build["lineage_top"]:
        print(f"  {'m' + str(row['final_theme']):<10}"
              + "".join(f"{s:>8,}" for s in row["size_per_pass"]))
    print()
    return {"history": build["history"], "passes": build["passes"],
            "themes": build["themes"], "repeats": repeats, "l1_repeats": l1_repeats,
            "lineage_top": build["lineage_top"]}


def section_b(l1m: dict[str, object], l1: dict[str, object],
              sides: dict[int, dict[str, object]], n: int) -> dict[str, object]:
    """B: the size distribution, the scramble ratios, and redundancy.

    Args:
        l1m: The L1m real side.
        l1: Prompt 61's core-merged side.
        sides: The L1m scramble sides by seed.
        n: Universe size.

    Returns:
        The table as data.
    """
    from core_merge_pairs import brute, counts_for, matrix

    print("=" * 104)
    print("B. THEMES PER BAND, THE SCRAMBLE SIDES, AND REDUNDANCY")
    print("=" * 104)
    all_bands = bands_of(l1m["size"])
    kept_bands = bands_of(l1m["sizes"])
    l1_kept = bands_of(l1["t_size"][l1["t_found"] >= FOUND_BAR])
    print(f"  {'band':<12}{'L1m all':>11}{'L1m >= 10':>12}{'L1 >= 10':>11}"
          f"{'change':>10}")
    rows = {}
    for _lo, _hi, band in BANDS:
        every = int((all_bands == band).sum())
        kept = int((kept_bands == band).sum())
        theirs = int((l1_kept == band).sum())
        if not (every or kept or theirs):
            continue
        print(f"  {band:<12}{every:>11,}{kept:>12,}{theirs:>11,}{kept - theirs:>+10,}")
        rows[band] = {"all": every, "kept": kept, "l1_kept": theirs}
    print(f"  {'TOTAL':<12}{len(l1m['size']):>11,}{len(l1m['sizes']):>12,}"
          f"{int((l1['t_found'] >= FOUND_BAR).sum()):>11,}")
    print()
    print("  the two scramble sides at each bar -- INDICATIVE ONLY, not a calibration")
    print(f"  {'bar':<10}{'real':>12}" + "".join(f"{'seed ' + str(s):>12}" for s in SCRAMBLE)
          + f"{'mean':>12}{'scram/real':>13}")
    ratios = {}
    for bar in BARS:
        each = [int((sides[s]["found"] >= bar).sum()) for s in SCRAMBLE]
        mean = sum(each) / len(each)
        base = int((l1m["found"] >= bar).sum())
        print(f"  {'>= ' + str(bar):<10}{base:>12,}" + "".join(f"{c:>12,}" for c in each)
              + f"{mean:>12,.1f}{mean / base if base else 0:>13.2%}")
        ratios[str(bar)] = {"real": base, "seeds": each, "mean": mean,
                            "ratio": mean / base if base else None}
    print()
    print("  by band, mean of the two seeds against real")
    print(f"  {'band':<12}" + "".join(
        f"{'>=' + str(b) + ' real':>15}{'scram':>9}{'ratio':>9}" for b in BARS))
    scramble_bands = {s: {bar: bands_of(sides[s]["size"][sides[s]["found"] >= bar])
                          for bar in BARS} for s in SCRAMBLE}
    real_bands = {bar: bands_of(l1m["size"][l1m["found"] >= bar]) for bar in BARS}
    by_band = {}
    for _lo, _hi, band in BANDS:
        cells, seen = "", False
        row = {}
        for bar in BARS:
            base = int((real_bands[bar] == band).sum())
            mean = sum(int((scramble_bands[s][bar] == band).sum())
                       for s in SCRAMBLE) / len(SCRAMBLE)
            seen = seen or base or mean
            cells += (f"{base:>15,}{mean:>9,.1f}"
                      f"{(mean / base if base else float('nan')):>9.1%}")
            row[str(bar)] = {"real": base, "scramble": mean}
        if seen:
            print(f"  {band:<12}" + cells)
            by_band[band] = row
    print()
    per_pathway = np.bincount(l1m["matrix"].indices, minlength=n)
    l1_per = np.bincount(np.concatenate([
        l1["t_member_pathway"][l1["t_member_indptr"][t]:l1["t_member_indptr"][t + 1]]
        for t in np.flatnonzero(l1["t_found"] >= FOUND_BAR)]), minlength=n)
    print(f"  {'mean themes per pathway, L1m / L1 / O50s':<44}"
          f"{per_pathway.mean():>10.1f}{l1_per.mean():>10.1f}{23.5:>10.1f}")
    listed = [r.tolist() for r in l1m["rows"]]
    got = counts_for(matrix(listed, n), l1m["sizes"], report=False)
    rng = np.random.default_rng(SEED)
    take = min(2000, len(listed))
    pick = np.sort(rng.choice(len(listed), size=take, replace=False))
    fast = counts_for(matrix([listed[int(i)] for i in pick], n), l1m["sizes"][pick],
                      report=False)["totals"]
    slow = brute(listed, l1m["sizes"], pick)
    same = all(fast[k] == slow[k] for k in slow)
    per = got["totals"]["j05"] / max(len(listed), 1)
    print(f"  {'non-nested J >= 0.5 pairs per theme':<44}{per:>10.1f}"
          f"{13.4:>10.1f}{15.7:>10.1f}")
    print(f"  {'':<44}{'(' + ('verified' if same else 'MISMATCH') + ')':>10}")
    print(f"  L1m has {got['totals']['j05']:,} non-nested pairs at J >= 0.5, "
          f"{got['totals']['nested85']:,} nested at 0.85+, "
          f"{got['totals']['one_stray']:,} one outside")
    print()
    return {"per_band": rows, "scramble": ratios, "scramble_by_band": by_band,
            "mean_themes_per_pathway": float(per_pathway.mean()),
            "j05_per_theme": per, "counts": got["totals"],
            "verification": {"sparse": fast, "brute": slow, "identical": bool(same)}}


def build_dag(l1m: dict[str, object], n: int, report: bool = True) -> dict[str, object]:
    """The strict-containment DAG over the accepted L1m themes, with prompt 63's code.

    Args:
        l1m: The L1m real side.
        n: Universe size.
        report: Print progress.

    Returns:
        ``{dag, got, depth, check}``.
    """
    from l1_dag import brute_check, depths, reduce_transitive, relations

    accepted = {"matrix": l1m["matrix"], "sizes": l1m["sizes"], "rows": l1m["rows"]}
    got = relations(accepted, report=report)
    dag = reduce_transitive(accepted, got, report=report)
    depth = depths(dag, len(l1m["sizes"]), l1m["sizes"])
    clock = time.perf_counter()
    check = brute_check(accepted, dag)
    if report:
        print(f"    DAG verified against explicit set loops "
              f"({time.perf_counter() - clock:.0f}s): "
              f"{'IDENTICAL' if check['identical'] else 'MISMATCH'}  {check}", flush=True)
    return {"dag": dag, "got": got, "depth": depth, "check": check, "accepted": accepted}


def section_c(l1m: dict[str, object], made: dict[str, object], large: list[np.ndarray],
              n: int) -> dict[str, object]:
    """C: the DAG, beside prompt 63's.

    Args:
        l1m: The L1m real side.
        made: As :func:`build_dag` returns.
        large: The seven `large7` member arrays, largest first.
        n: Universe size.

    Returns:
        The table as data.
    """
    from l1_dag import children_of

    dag, depth = made["dag"], made["depth"]
    sizes, rows = l1m["sizes"], l1m["rows"]
    total = len(sizes)
    counts = np.diff(dag["indptr"])
    roots = counts == 0
    kid_ptr, kids = children_of(dag, total)
    kid_counts = np.diff(kid_ptr)
    bands = bands_of(sizes)
    print("=" * 104)
    print("C. THE DAG: STRICT CONTAINMENT ON MEMBERS, IMMEDIATE PARENTS ONLY")
    print("=" * 104)
    print(f"  {'':<42}{'L1m':>14}{'L1 (prompt 63)':>17}")
    print(f"  {'themes':<42}{total:>14,}{52001:>17,}")
    print(f"  {'edges':<42}{int(counts.sum()):>14,}{388287:>17,}")
    print(f"  {'ancestor pairs before the reduction':<42}"
          f"{len(dag['anc_child']):>14,}{5541622:>17,}")
    print(f"  {'roots':<42}{int(roots.sum()):>14,}{594:>17,}")
    print(f"  {'roots without the 3-5 themes':<42}"
          f"{int((roots & (sizes >= 6)).sum()):>14,}{569:>17,}")
    print(f"  {'multi-parent share':<42}{(counts >= 2).sum() / total:>14.2%}"
          f"{0.9116:>17.2%}")
    print(f"  {'children per node, max':<42}{int(kid_counts.max()):>14,}{1349:>17,}")
    print(f"  {'children per node, median':<42}{np.median(kid_counts):>14.1f}{4.0:>17.1f}")
    deepest = np.zeros(n, dtype=np.int64) - 1
    for t in range(total):
        np.maximum.at(deepest, rows[t], depth[t])
    held = deepest >= 0
    print(f"  {'levels per pathway, median / max':<42}"
          f"{np.median(deepest[held]):>9.1f} / {int(deepest[held].max()):<4}{16.0:>12.1f} / 33")
    print(f"  {'levels per theme, median / max':<42}"
          f"{np.median(depth):>9.1f} / {int(depth.max()):<4}{9.0:>12.1f} / 33")
    print()
    print("  roots by band")
    print(f"  {'band':<12}{'themes':>10}{'roots':>10}{'share of the band':>20}")
    by_band = {}
    for _lo, _hi, band in BANDS:
        where = bands == band
        if not where.any():
            continue
        count = int((roots & where).sum())
        print(f"  {band:<12}{int(where.sum()):>10,}{count:>10,}"
              f"{count / int(where.sum()):>20.1%}")
        by_band[band] = {"themes": int(where.sum()), "roots": count}
    print()
    big = np.flatnonzero(roots & (sizes >= TOP_ROOT_MIN))
    print(f"  every root of {TOP_ROOT_MIN}+ pathways: {len(big)} of them")
    print(f"  {'root':<10}{'size':>7}{'children':>10}   largest three children, "
          f"size (share of the root)")
    listed = []
    for r in big[np.argsort(-sizes[big])].tolist():
        mine = kids[kid_ptr[r]:kid_ptr[r + 1]]
        top = mine[np.argsort(-sizes[mine])][:3]
        shown = ", ".join(f"{int(sizes[c]):,} ({sizes[c] / sizes[r]:.0%})"
                          for c in top.tolist()) or "none"
        print(f"  {'m' + str(r):<10}{int(sizes[r]):>7,}{len(mine):>10,}   {shown}")
        listed.append({"theme": int(r), "size": int(sizes[r]), "children": int(len(mine)),
                       "largest": [[int(sizes[c]), float(sizes[c] / sizes[r])]
                                   for c in top.tolist()]})
    print()
    print("  the seven large7 sets against L1m")
    print(f"  {'set':<8}{'set size':>10}{'L1m theme':>11}{'theme size':>12}{'best J':>9}"
          f"{'root?':>8}{'parents':>9}   parent sizes")
    seven = []
    for i, members in enumerate(large):
        best, best_j = -1, 0.0
        for t in range(total):
            inter = len(np.intersect1d(rows[t], members, assume_unique=True))
            union = len(rows[t]) + len(members) - inter
            value = inter / union if union else 0.0
            if value > best_j:
                best, best_j = t, value
        if best_j < MATCH_J:
            print(f"  {'set_' + str(i + 1):<8}{len(members):>10,}{'none':>11}{'--':>12}"
                  f"{best_j:>9.3f}{'--':>8}{'--':>9}")
            seven.append({"set": i + 1, "theme": None, "best_j": best_j})
            continue
        mine = dag["parents"][dag["indptr"][best]:dag["indptr"][best + 1]]
        print(f"  {'set_' + str(i + 1):<8}{len(members):>10,}{'m' + str(best):>11}"
              f"{int(sizes[best]):>12,}{best_j:>9.3f}"
              f"{('yes' if not len(mine) else 'no'):>8}{len(mine):>9}   "
              + ", ".join(f"{int(sizes[p]):,}" for p in mine.tolist()[:6]))
        seven.append({"set": i + 1, "theme": int(best), "theme_size": int(sizes[best]),
                      "best_j": best_j, "root": not len(mine),
                      "parents": [int(sizes[p]) for p in mine.tolist()]})
    print()
    return {"themes": total, "edges": int(counts.sum()), "roots": int(roots.sum()),
            "roots_without_3_5": int((roots & (sizes >= 6)).sum()),
            "multi_parent": float((counts >= 2).sum() / total),
            "children_max": int(kid_counts.max()),
            "levels_pathway": [float(np.median(deepest[held])), int(deepest[held].max())],
            "roots_by_band": by_band, "top_roots": listed, "large7": seven}


def section_d(l1m: dict[str, object], made: dict[str, object]) -> dict[str, object]:
    """D: near-misses, and what a one- or two-pathway tolerance would reparent.

    Args:
        l1m: The L1m real side.
        made: As :func:`build_dag` returns.

    Returns:
        The table as data.
    """
    sizes = l1m["sizes"]
    dag, got = made["dag"], made["got"]
    total = len(sizes)
    roots = np.diff(dag["indptr"]) == 0
    bands = bands_of(sizes)
    missing = got["tol_missing"]
    print("=" * 104)
    print("D. NEAR-MISSES -- REPORT ONLY, NOTHING IS APPLIED")
    print("=" * 104)
    print("  pairs where the smaller is inside the larger except for a few pathways")
    print(f"  {'pathways missing':<22}{'pairs':>12}{'distinct children':>20}"
          f"{'L1 pairs (prompt 63)':>22}")
    reference = {"1": 555728, "2-5": 188621, "6+": 32774}
    buckets = (("1", missing == 1), ("2-5", (missing >= 2) & (missing <= 5)),
               ("6+", missing >= 6))
    rows = {}
    for name, where in buckets:
        kids = len(np.unique(got["tol_child"][where]))
        print(f"  {name:<22}{int(where.sum()):>12,}{kids:>20,}"
              f"{reference[name]:>22,}")
        rows[name] = {"pairs": int(where.sum()), "children": kids}
    print(f"  {'ALL':<22}{len(missing):>12,}"
          f"{len(np.unique(got['tol_child'])):>20,}{777123:>22,}")
    print()
    print("  roots that would gain a parent at a tolerance of 1 and of 2 pathways")
    print(f"  {'band':<12}{'roots':>9}{'tol 1':>9}{'share':>8}{'tol 2':>9}{'share':>8}")
    one = np.zeros(total, dtype=bool)
    one[np.unique(got["tol_child"][missing <= 1])] = True
    two = np.zeros(total, dtype=bool)
    two[np.unique(got["tol_child"][missing <= 2])] = True
    gained = {}
    for _lo, _hi, band in BANDS:
        where = roots & (bands == band)
        if not where.any():
            continue
        a, b = int((where & one).sum()), int((where & two).sum())
        print(f"  {band:<12}{int(where.sum()):>9,}{a:>9,}{a / int(where.sum()):>8.1%}"
              f"{b:>9,}{b / int(where.sum()):>8.1%}")
        gained[band] = {"roots": int(where.sum()), "tol1": a, "tol2": b}
    a, b = int((roots & one).sum()), int((roots & two).sum())
    print(f"  {'ALL':<12}{int(roots.sum()):>9,}{a:>9,}{a / max(roots.sum(), 1):>8.1%}"
          f"{b:>9,}{b / max(roots.sum(), 1):>8.1%}")
    print()
    return {"near_misses": rows, "roots_gaining": gained,
            "all_tol1": a, "all_tol2": b, "roots": int(roots.sum())}


def read_roots(l1m: dict[str, object], made: dict[str, object],
               args: argparse.Namespace) -> dict[str, object]:
    """E: the reviewer's blind reading batches for the big roots, and the key beside them.

    Args:
        l1m: The L1m real side.
        made: As :func:`build_dag` returns.
        args: Parsed arguments.

    Returns:
        ``{roots, batches, minimum}``.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}
    sizes, rows = l1m["sizes"], l1m["rows"]
    found = l1m["found"][l1m["which"]]
    roots = np.diff(made["dag"]["indptr"]) == 0

    minimum = READ_ROOT_MIN
    chosen = np.flatnonzero(roots & (sizes >= minimum))
    lines_needed = int(sizes[chosen].sum()) + 3 * len(chosen)
    if lines_needed / BATCH_LINES > MAX_BATCHES:
        print(f"  roots of {READ_ROOT_MIN}+ would need about "
              f"{lines_needed / BATCH_LINES:.0f} batches, above the {MAX_BATCHES} the prompt "
              f"allows, so the floor moves to {READ_FALLBACK_MIN}")
        minimum = READ_FALLBACK_MIN
        chosen = np.flatnonzero(roots & (sizes >= minimum))

    rng = random.Random(SEED)
    shuffled = chosen.tolist()
    rng.shuffle(shuffled)
    codes: set[str] = set()
    while len(codes) < len(shuffled):
        codes.add(f"M{rng.randrange(16 ** 4):04x}")
    ids = sorted(codes)
    rng.shuffle(ids)

    out = args.out / "read_roots"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("batch_*.md"):
        stale.unlink()
    key: dict[str, object] = {}
    batches: list[Path] = []
    lines: list[str] = []
    number = 1

    def flush() -> None:
        """Write the lines gathered so far as one batch."""
        nonlocal lines, number
        if not lines:
            return
        path = out / f"batch_{number:02d}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        batches.append(path)
        number += 1
        lines = []

    for code, t in zip(ids, shuffled, strict=True):
        body = sorted(f"- {named.get(keys[p], (keys[p], '?'))[0]} "
                      f"[{named.get(keys[p], (keys[p], '?'))[1]}]"
                      for p in rows[t].tolist())
        block = [f"## {code}", ""] + body + [""]
        if lines and len(lines) + len(block) > BATCH_LINES:
            flush()
        lines += block
        key[code] = {"theme": int(l1m["which"][t]), "size": int(sizes[t]),
                     "runs_found": int(found[t])}
    flush()
    (out / "KEY_DO_NOT_SHARE_L1m_roots.json").write_text(
        json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  {len(shuffled)} roots of {minimum}+ pathways in {len(batches)} batches -> {out}")
    print(f"    key written to {out / 'KEY_DO_NOT_SHARE_L1m_roots.json'} and not read again")
    return {"roots": len(shuffled), "batches": [p.name for p in batches], "minimum": minimum}


def main(argv: list[str] | None = None) -> int:
    """Sections A-E.

    Args:
        argv: Command line.

    Returns:
        0, or 1 if a check disagrees.
    """
    from l1_merge_rule import distinct, members_of
    from l1_report import load_l1

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1m_2026-10-24"))
    parser.add_argument("--l1", type=Path,
                        default=Path("data/experiments/L1_2026-10-24"))
    args = parser.parse_args(argv)

    n = int(json.loads((args.space_root / "universe.json").read_text())["n_embedded"])
    print("PROMPT 64: L1m -- THE MERGE ON MEMBERS, REPEATED UNTIL STABLE")
    print("  exploratory; nothing adopted. The 10-run bar is a PROVISIONAL working bar.")
    l1m = load_l1m(args.out / "real", n)
    sides = {s: load_l1m(args.out / "scramble" / f"seed0{s}", n) for s in SCRAMBLE}
    core_side = load_l1(args.l1 / "real_bothways")
    print(f"  L1m: {len(l1m['size']):,} themes, {len(l1m['sizes']):,} found in >= "
          f"{FOUND_BAR} runs")
    print()
    record: dict[str, object] = {"A": section_a(l1m, core_side)}
    record["B"] = section_b(l1m, core_side, sides, n)
    made = build_dag(l1m, n)
    print()
    jaccard_side = load_l1(args.l1 / "real")
    which = np.flatnonzero((jaccard_side["t_size"] >= 800) & (jaccard_side["t_found"] >= FOUND_BAR))
    big = members_of(jaccard_side, which)
    kept = distinct(big, n)
    large = [big[i] for i in sorted(kept["kept"], key=lambda j: -len(big[j]))]
    record["C"] = section_c(l1m, made, large, n)
    record["D"] = section_d(l1m, made)
    record["E"] = read_roots(l1m, made, args)
    record["dag_verification"] = made["check"]

    np.savez_compressed(args.out / "dag.npz", theme=l1m["which"], size=l1m["sizes"],
                        parent_indptr=made["dag"]["indptr"], parent=made["dag"]["parents"],
                        depth=made["depth"], tol_child=made["got"]["tol_child"],
                        tol_parent=made["got"]["tol_parent"],
                        tol_missing=made["got"]["tol_missing"])
    (args.out / "report.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'report.json'}")
    return 0 if made["check"]["identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
