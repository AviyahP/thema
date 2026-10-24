"""Sections A-E of prompt 61: what level 1's steps 1-4 produced. Declared 24 Oct 2026.

Reads the three sides :mod:`l1_build` wrote and reports them. Near-copy counting is prompt 58's
verified exact counter, reused unchanged, so section C's numbers sit beside O50s's gated themes and
prompt 60's tree cores on the same definitions.

The two scramble sides are **indicative only** -- two seeds cannot calibrate anything, and no floor
is derived here. Nothing in this script changes a build.

Usage:
    uv run scripts/l1_report.py
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
BARS = (5, 10, 20)
SCRAMBLE = (3001, 3002)
EXAMPLES = 20
O50S_PER_THEME = 409858 / 26120
CORES_PER_CORE = 696.5

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
        Labels, same shape.
    """
    return np.array([band_of(int(s)) for s in sizes])


def load_l1(where: Path) -> dict[str, object]:
    """One side's groups and themes.

    Args:
        where: A directory :func:`l1_build.write_side` wrote.

    Returns:
        Everything both archives hold, plus derived sizes and ragged member lists.
    """
    got: dict[str, object] = {}
    with np.load(where / "groups.npz") as handle:
        for key in handle.files:
            got[f"g_{key}"] = handle[key]
    with np.load(where / "themes.npz") as handle:
        for key in handle.files:
            got[f"t_{key}"] = handle[key]
    got["steps"] = json.loads((where / "steps.json").read_text(encoding="utf-8"))
    got["t_size"] = np.diff(got["t_member_indptr"]).astype(np.int64)
    got["t_core_size"] = np.diff(got["t_core_indptr"]).astype(np.int64)
    got["g_core_size"] = np.diff(got["g_core_indptr"]).astype(np.int64)
    return got


def rows_of(indptr: np.ndarray, pathway: np.ndarray,
            which: np.ndarray | None = None) -> list[np.ndarray]:
    """Member arrays for some rows of a ragged table.

    Args:
        indptr: Offsets.
        pathway: Concatenated members.
        which: Which rows, or every row.

    Returns:
        One array per row.
    """
    rows = range(len(indptr) - 1) if which is None else (int(i) for i in which)
    return [pathway[indptr[i]:indptr[i + 1]] for i in rows]


def section_a(real: dict[str, object]) -> dict[str, object]:
    """A: counts, by band.

    Args:
        real: The real side.

    Returns:
        The table as data.
    """
    print("=" * 104)
    print("A. COUNTS")
    print("=" * 104)
    steps = real["steps"]
    print(f"  {'group seeds (distinct clusters of 3+)':<52}{steps['seeds']:>12,}")
    print(f"  {'groups with a core of 3+':<52}{steps['cored_groups']:>12,}")
    print(f"  {'groups with no core':<52}{steps['seeds'] - steps['cored_groups']:>12,}")
    print(f"  {'themes after the merge':<52}{steps['themes']:>12,}")
    print(f"  {'ordered core pairs at J >= 0.9':<52}{steps['core_pairs']:>12,}")
    groups = real["t_groups"]
    print(f"  {'groups per theme, median / max':<52}"
          f"{np.median(groups):>7.1f} / {int(groups.max()):<}")
    print()
    print("  groups with and without a core, by band of the SEED cluster")
    print(f"  {'band':<12}{'seeds':>12}{'with core':>12}{'no core':>12}{'no core %':>12}"
          f"{'median core / seed':>21}")
    seed_bands = bands_of(real["g_seed_sizes"])
    cored = real["g_has_core"]
    rows = {}
    for _lo, _hi, band in BANDS:
        where = seed_bands == band
        if not where.any():
            continue
        with_core = int((where & cored).sum())
        share = (int(where.sum()) - with_core) / int(where.sum())
        ratio = (real["g_core_size"][where & cored] / real["g_seed_sizes"][where & cored])
        print(f"  {band:<12}{int(where.sum()):>12,}{with_core:>12,}"
              f"{int(where.sum()) - with_core:>12,}{share:>12.1%}"
              f"{np.median(ratio) if len(ratio) else float('nan'):>21.3f}")
        rows[band] = {"seeds": int(where.sum()), "with_core": with_core,
                      "no_core": int(where.sum()) - with_core}
    print()
    print("  themes by band of MEMBERS, with the core as a share of members")
    print(f"  {'band':<12}{'themes':>12}{'share':>10}{'median core/members':>22}"
          f"{'median members':>16}")
    tb = bands_of(real["t_size"])
    per_band = {}
    for _lo, _hi, band in BANDS:
        where = tb == band
        if not where.any():
            continue
        ratio = real["t_core_size"][where] / np.maximum(real["t_size"][where], 1)
        print(f"  {band:<12}{int(where.sum()):>12,}{int(where.sum()) / len(tb):>10.1%}"
              f"{np.median(ratio):>22.3f}{np.median(real['t_size'][where]):>16.0f}")
        per_band[band] = int(where.sum())
    print(f"  {'TOTAL':<12}{len(tb):>12,}")
    print()
    return {"per_band": per_band, "groups_by_band": rows,
            "groups_per_theme": {"median": float(np.median(groups)), "max": int(groups.max())}}


def section_b(real: dict[str, object], sides: dict[int, dict[str, object]]) -> dict[str, object]:
    """B: support by band, with the two scramble sides beside it.

    Args:
        real: The real side.
        sides: The scramble sides by seed.

    Returns:
        The table as data.
    """
    print("=" * 104)
    print("B. SUPPORT, AND THE TWO SCRAMBLE SIDES (INDICATIVE ONLY, NOT A CALIBRATION)")
    print("=" * 104)
    tb = bands_of(real["t_size"])
    found = real["t_found"]
    print(f"  {'band':<12}{'themes':>10}{'med runs':>10}{'med judged':>12}"
          + "".join(f"{'>=' + str(b):>11}" for b in BARS))
    got: dict[str, object] = {"real": {}, "scramble": {}}
    for _lo, _hi, band in BANDS:
        where = tb == band
        if not where.any():
            continue
        cells = [int((found[where] >= b).sum()) for b in BARS]
        print(f"  {band:<12}{int(where.sum()):>10,}{np.median(found[where]):>10.0f}"
              f"{np.median(real['t_judged'][where]):>12.0f}"
              + "".join(f"{c:>11,}" for c in cells))
        got["real"][band] = {"themes": int(where.sum()),
                             "median_found": float(np.median(found[where])),
                             "bars": dict(zip([str(b) for b in BARS], cells, strict=True))}
    print(f"  {'ALL':<12}{len(tb):>10,}{np.median(found):>10.0f}"
          f"{np.median(real['t_judged']):>12.0f}"
          + "".join(f"{int((found >= b).sum()):>11,}" for b in BARS))
    print()
    print("  scramble sides: themes at each bar, per seed, and the ratio to real")
    print(f"  {'bar':<10}{'real':>12}" + "".join(f"{'seed ' + str(s):>12}" for s in SCRAMBLE)
          + f"{'mean':>12}{'scram/real':>13}")
    for bar in BARS:
        each = [int((sides[s]["t_found"] >= bar).sum()) for s in SCRAMBLE]
        mean = sum(each) / len(each)
        base = int((found >= bar).sum())
        print(f"  {'>= ' + str(bar):<10}{base:>12,}" + "".join(f"{c:>12,}" for c in each)
              + f"{mean:>12,.1f}{mean / base if base else 0:>13.2%}")
        got["scramble"][str(bar)] = {"real": base, "seeds": each, "mean": mean,
                                     "ratio": mean / base if base else None}
    print()
    print("  by band, mean of the two seeds against real")
    print(f"  {'band':<12}" + "".join(
        f"{'>=' + str(b) + ' real':>15}{'scram':>9}{'ratio':>9}" for b in BARS))
    scramble_bands = {s: bands_of(sides[s]["t_size"]) for s in SCRAMBLE}
    for _lo, _hi, band in BANDS:
        cells, seen = "", False
        for bar in BARS:
            base = int(((found >= bar) & (tb == band)).sum())
            mean = sum(int(((sides[s]["t_found"] >= bar) & (scramble_bands[s] == band)).sum())
                       for s in SCRAMBLE) / len(SCRAMBLE)
            seen = seen or base or mean
            ratio = mean / base if base else float("nan")
            cells += f"{base:>15,}{mean:>9,.1f}{ratio:>9.1%}"
        if seen:
            print(f"  {band:<12}" + cells)
    print()
    return got


def section_c(real: dict[str, object], n: int) -> dict[str, object]:
    """C: near-copies among the themes, with prompt 58's verified counter.

    Args:
        real: The real side.
        n: Universe size.

    Returns:
        The counts for both sets.
    """
    from core_merge_pairs import brute, counts_for, matrix

    print("=" * 104)
    print("C. NEAR-COPIES AMONG THE THEMES (prompt 58's exact counter, brute-force verified)")
    print("=" * 104)
    print(f"  {'set':<22}{'themes':>10}{'J>=0.5 non-nested':>20}{'nested >=0.85':>15}"
          f"{'1 outside':>13}{'J0.5/theme':>12}{'all/theme':>11}{'verified':>11}")
    out: dict[str, object] = {}
    for name, which in (("all themes", None),
                        ("found in >= 10 runs", np.flatnonzero(real["t_found"] >= 10))):
        rows = rows_of(real["t_member_indptr"], real["t_member_pathway"], which)
        listed = [r.tolist() for r in rows]
        sizes = np.array([len(r) for r in listed], dtype=np.int64)
        clock = time.perf_counter()
        got = counts_for(matrix(listed, n), sizes, report=False)
        rng = np.random.default_rng(SEED)
        take = min(2000, len(listed))
        pick = np.sort(rng.choice(len(listed), size=take, replace=False))
        fast = counts_for(matrix([listed[int(i)] for i in pick], n), sizes[pick],
                          report=False)["totals"]
        slow = brute(listed, sizes, pick)
        same = all(fast[k] == slow[k] for k in slow)
        total = got["totals"]
        per = total["j05"] / max(len(listed), 1)
        every = sum(total.values()) / max(len(listed), 1)
        print(f"  {name:<22}{len(listed):>10,}{total['j05']:>20,}{total['nested85']:>15,}"
              f"{total['one_stray']:>13,}{per:>12.1f}{every:>11.1f}"
              f"{'IDENTICAL' if same else 'MISMATCH':>11}")
        got["verification"] = {"sample": int(take), "seed": SEED, "sparse": fast, "brute": slow,
                               "identical": bool(same)}
        got["j05_per_theme"] = per
        got["all_relations_per_theme"] = every
        got["seconds"] = round(time.perf_counter() - clock, 1)
        out[name] = got
    print()
    print("  the J0.5/theme column is the one comparable to O50s and prompt 60: non-nested pairs")
    print(f"  at J >= 0.5 per object -- O50s gated themes {O50S_PER_THEME:.1f}, "
          f"prompt 60 tree cores {CORES_PER_CORE:.1f}")
    print()
    print("  non-nested pairs at J >= 0.5 by band of the larger theme")
    print(f"  {'band':<12}{'all themes':>16}{'>= 10 runs':>16}")
    for _lo, _hi, band in BANDS:
        cells = [out[name]["j05"].get(band, 0) for name in out]
        if any(cells):
            print(f"  {band:<12}" + "".join(f"{c:>16,}" for c in cells))
    print()
    return out


def o50s_members(path: Path, keys: list[str]) -> tuple[list[np.ndarray], np.ndarray]:
    """The frozen O50s build's final themes, as universe indices.

    Args:
        path: ``members.tsv`` of the frozen build.
        keys: Universe keys in row order.

    Returns:
        Member arrays per node and their sizes.
    """
    index = {key: i for i, key in enumerate(keys)}
    per: dict[str, list[int]] = {}
    for line in path.read_text(encoding="utf-8").split("\n")[1:]:
        if not line:
            continue
        node, key = line.split("\t")[0], line.split("\t")[1]
        per.setdefault(node, []).append(index[key])
    rows = [np.array(sorted(v), dtype=np.int64) for _k, v in sorted(per.items())]
    return rows, np.array([len(r) for r in rows], dtype=np.int64)


def section_d(real: dict[str, object], n: int, args: argparse.Namespace) -> dict[str, object]:
    """D: how much of O50s the recurrent L1 themes recover.

    Args:
        real: The real side.
        n: Universe size.
        args: Parsed arguments.

    Returns:
        The table as data.
    """
    from scipy import sparse

    from core_merge_pairs import matrix
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    o50s, o_sizes = o50s_members(args.frozen / "members.tsv", keys)
    which = np.flatnonzero(real["t_found"] >= 10)
    rows = rows_of(real["t_member_indptr"], real["t_member_pathway"], which)
    l1 = matrix([r.tolist() for r in rows], n)
    l_sizes = np.array([len(r) for r in rows], dtype=np.int64)
    print("=" * 104)
    print("D. CORRESPONDENCE WITH THE FROZEN O50s")
    print("=" * 104)
    print(f"  {len(o50s):,} O50s themes against {len(rows):,} L1 themes found in >= 10 runs")
    best = np.zeros(len(o50s), dtype=np.float64)
    o = matrix([r.tolist() for r in o50s], n)
    transposed = sparse.csr_matrix(l1).T.tocsc()
    for begin in range(0, len(o50s), 256):
        stop = min(begin + 256, len(o50s))
        got = (o[begin:stop] @ transposed).tocoo()
        if not got.nnz:
            continue
        inter = got.data.astype(np.int64)
        union = o_sizes[got.row + begin] + l_sizes[got.col] - inter
        jac = inter / union
        np.maximum.at(best, got.row + begin, jac)
    bands = bands_of(o_sizes)
    print(f"  {'band':<12}{'O50s themes':>13}{'J >= 0.9':>18}{'J >= 0.7':>18}{'median best J':>15}")
    out = {}
    for _lo, _hi, band in BANDS:
        where = bands == band
        if not where.any():
            continue
        nine = int((best[where] >= 0.9).sum())
        seven = int((best[where] >= 0.7).sum())
        total = int(where.sum())
        print(f"  {band:<12}{total:>13,}{nine:>12,} ({nine / total:>5.1%}){seven:>12,} "
              f"({seven / total:>5.1%}){np.median(best[where]):>15.3f}")
        out[band] = {"themes": total, "j09": nine, "j07": seven,
                     "median_best": float(np.median(best[where]))}
    nine, seven = int((best >= 0.9).sum()), int((best >= 0.7).sum())
    print(f"  {'ALL':<12}{len(o50s):>13,}{nine:>12,} ({nine / len(o50s):>5.1%})"
          f"{seven:>12,} ({seven / len(o50s):>5.1%}){np.median(best):>15.3f}")
    print()
    top = which[np.argsort(-l_sizes)][:10]
    print("  the ten largest L1 themes found in >= 10 runs, size (runs found)")
    print("    " + ", ".join(f"{int(real['t_size'][t])} ({int(real['t_found'][t])}r)"
                             for t in top))
    print()
    return {"by_band": out, "all": {"themes": len(o50s), "j09": nine, "j07": seven,
                                    "median_best": float(np.median(best))},
            "largest": [[int(real["t_size"][t]), int(real["t_found"][t])] for t in top]}


def section_e(real: dict[str, object], args: argparse.Namespace) -> list[Path]:
    """E: forty themes written out for reading, with the core marked.

    Args:
        real: The real side.
        args: Parsed arguments.

    Returns:
        The files written.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}
    out = args.out / "examples"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.md"):
        stale.unlink()
    rng = random.Random(SEED)
    written = []
    for label, low, high in (("6-24", 6, 24), ("25plus", 25, 10 ** 9)):
        pool = np.flatnonzero((real["t_found"] >= 10) & (real["t_size"] >= low)
                              & (real["t_size"] <= high))
        pick = sorted(rng.sample(pool.tolist(), min(EXAMPLES, len(pool))))
        lines = []
        for position, t in enumerate(pick, 1):
            core = set(real["t_core_pathway"][
                real["t_core_indptr"][t]:real["t_core_indptr"][t + 1]].tolist())
            members = real["t_member_pathway"][
                real["t_member_indptr"][t]:real["t_member_indptr"][t + 1]]
            lines.append(f"## {label}-{position:02d}  ({len(members)} members, "
                         f"{len(core)} in the core, found in {int(real['t_found'][t])} of "
                         f"{int(real['t_judged'][t])} runs able to judge)")
            lines.append("")
            body = []
            for p in members.tolist():
                name, source = named.get(keys[p], (keys[p], "?"))
                body.append(f"- {'**CORE** ' if p in core else '      '}{name} [{source}]")
            lines += sorted(body, key=lambda s: (not s.startswith("- **CORE**"), s))
            lines.append("")
        path = out / f"themes_{label}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
        print(f"  examples {label}: {len(pick)} of {len(pool):,} available -> {path}")
    return written


def main(argv: list[str] | None = None) -> int:
    """Sections A-E.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1_2026-10-24"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--sections", default="ABCDE")
    args = parser.parse_args(argv)

    real = load_l1(args.out / "real")
    sides = {s: load_l1(args.out / "scramble" / f"seed0{s}") for s in SCRAMBLE}
    n = int(json.loads((args.space_root / "universe.json").read_text())["n_embedded"])
    print(f"PROMPT 61: LEVEL 1, STEPS 1-4. theta {real['steps']['theta']} on each side, "
          f"core {real['steps']['core_cut']}, merge J {real['steps']['merge_j']}, "
          f"members {real['steps']['member_cut']}")
    print(f"  {n:,} pathways; every step brute-force verified in the build: "
          + ", ".join(f"{k} {'OK' if v['identical'] else 'MISMATCH'}"
                      for k, v in real["steps"]["verification"].items()))
    print()
    record: dict[str, object] = {}
    if "A" in args.sections:
        record["A"] = section_a(real)
    if "B" in args.sections:
        record["B"] = section_b(real, sides)
    if "C" in args.sections:
        record["C"] = section_c(real, n)
    if "D" in args.sections:
        record["D"] = section_d(real, n, args)
    if "E" in args.sections:
        section_e(real, args)
    (args.out / "report.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
