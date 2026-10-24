"""Sections A, B, D and E of prompt 58: CI and CT against O50s's stages.

Declared 23 Oct 2026. Evaluation only; nothing is adopted. Section C is
``scripts/core_merge_pairs.py`` and is reported from its own JSON.

O50s's stages, for the columns:

``s1``  groupings
``s2``  families before the gate
``s3``  the gated themes
``s4``  after consensus
``s5``  final

Jaccards against s5 use chunked sparse products, the same device section C uses, rather than an
all-pairs loop.

Usage:
    uv run scripts/core_merge_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SEED = 20261023
EXAMPLES = 20
EXAMPLE_MIN = 25

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)
SUPPORT_AT = (0.05, 0.10, 0.33)


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


def best_j(left_rows: list[list[int]], right_rows: list[list[int]], n_pathways: int,
           chunk: int = 128) -> tuple[np.ndarray, np.ndarray]:
    """Best Jaccard of each left theme against any right theme, and which one, by sparse products.

    The argmax comes out of the same product rather than a second pass: finding it with a Python
    comprehension over every right theme would be O(left x right) set operations and is the one
    thing this function exists to avoid.

    Args:
        left_rows: Member indices per left theme.
        right_rows: Member indices per right theme.
        n_pathways: Universe size.
        chunk: Rows per product.

    Returns:
        ``(best jaccard, best right index)``, both ``(len(left),)``.
    """
    from core_merge_pairs import matrix

    left = matrix(left_rows, n_pathways)
    right = matrix(right_rows, n_pathways).T.tocsc()
    l_size = np.array([len(r) for r in left_rows], dtype=np.int64)
    r_size = np.array([len(r) for r in right_rows], dtype=np.int64)
    out = np.zeros(len(left_rows), dtype=np.float64)
    which = np.full(len(left_rows), -1, dtype=np.int64)
    for start in range(0, len(left_rows), chunk):
        stop = min(start + chunk, len(left_rows))
        block = (left[start:stop] @ right).tocoo()
        if not len(block.data):
            continue
        inter = block.data.astype(np.int64)
        rows = block.row + start
        union = l_size[rows] + r_size[block.col] - inter
        jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
        order = np.lexsort((jac, rows))          # ascending jac within each row
        rows, jac, cols = rows[order], jac[order], block.col[order]
        last = np.ones(len(rows), dtype=bool)
        last[:-1] = rows[:-1] != rows[1:]        # the final entry of each row is its maximum
        better = jac[last] > out[rows[last]]
        target = rows[last][better]
        out[target] = jac[last][better]
        which[target] = cols[last][better]
    return out, which


def main(argv: list[str] | None = None) -> int:
    """Print sections A, B, D and write section E's examples.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/core_merge_2026-10-23"))
    args = parser.parse_args(argv)

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    index = {k: i for i, k in enumerate(keys)}
    arms = json.loads((args.out / "arms.json").read_text())
    loaded: dict[str, dict] = {}
    for arm in ("CI", "CT"):
        with np.load(args.out / f"themes_{arm}.npz") as handle:
            loaded[arm] = {k: handle[k] for k in handle.files}
    with np.load(args.space_root / "calibration" / "real.npz") as handle:
        s2_blocks, s2_support = handle["blocks"], handle["supports"]

    print("PROMPT 58, SECTIONS A, B, D, E. CI and CT against O50s's stages.")
    print("  s1 groupings, s2 families before the gate, s3 gated, s4 after consensus, s5 final.")
    print()
    print("=" * 104)
    print("A. COUNTS")
    print("=" * 104)
    print(f"  groupings at J >= 0.70                    {arms['n_groupings']:>10,}   (s1)")
    print(f"  eligible to score                         {arms['n_eligible']:>10,}")
    print(f"  without a core of {arms['min_core']}+ pathways            "
          f"{arms['n_no_core']:>10,}")
    print("  those without a core, by the band of their COMPLETED set:")
    for _lo, _hi, band in BANDS:
        if arms["no_core_by_band"].get(band):
            print(f"    {band:<10}{arms['no_core_by_band'][band]:>8,}")
    print()
    print(f"  {'':<34}{'CI':>12}{'CT':>12}{'O50s s2':>12}{'s3':>10}{'s4':>9}{'s5':>9}")
    print(f"  {'themes':<34}{len(loaded['CI']['size']):>12,}{len(loaded['CT']['size']):>12,}"
          f"{len(s2_support):>12,}{26120:>10,}{6589:>9,}{5658:>9,}")
    for arm in ("CI", "CT"):
        g = loaded[arm]["groupings"]
        print(f"  {'groupings per theme, ' + arm + ' median/max':<34}"
              f"{f'{statistics.median(g):.1f} / {int(g.max()):,}':>12}")
    print()
    print(f"  {'band':<12}{'CI':>12}{'CT':>12}{'O50s s2':>12}{'s5':>10}")
    s2_sizes = np.bitwise_count(s2_blocks).sum(axis=1).astype(np.int64)
    with (args.frozen / "members.tsv").open(encoding="utf-8") as handle:
        s5_hold: dict[str, list[int]] = defaultdict(list)
        for row in csv.DictReader(handle, delimiter="\t"):
            s5_hold[row["node"]].append(index[row["key"]])
    s5_rows = [sorted(v) for v in s5_hold.values()]
    s5_sizes = np.array([len(r) for r in s5_rows], dtype=np.int64)
    for _lo, _hi, band in BANDS:
        a = int(sum(1 for s in loaded["CI"]["size"] if band_of(int(s)) == band))
        b = int(sum(1 for s in loaded["CT"]["size"] if band_of(int(s)) == band))
        c = int(sum(1 for s in s2_sizes if band_of(int(s)) == band))
        d = int(sum(1 for s in s5_sizes if band_of(int(s)) == band))
        if not (a or b or c or d):
            continue
        print(f"  {band:<12}{a:>12,}{b:>12,}{c:>12,}{d:>10,}")
    print(f"  {'TOTAL':<12}{len(loaded['CI']['size']):>12,}{len(loaded['CT']['size']):>12,}"
          f"{len(s2_sizes):>12,}{len(s5_sizes):>10,}")
    print()
    print("  core size as a share of members, median by band")
    print(f"  {'band':<12}{'CI':>10}{'CT':>10}")
    for _lo, _hi, band in BANDS:
        cells = []
        for arm in ("CI", "CT"):
            share = [int(c) / int(s) for c, s in zip(loaded[arm]["core_size"],
                                                     loaded[arm]["size"], strict=True)
                     if band_of(int(s)) == band and int(s)]
            cells.append(f"{statistics.median(share):.3f}" if share else "-")
        if cells != ["-", "-"]:
            print(f"  {band:<12}{cells[0]:>10}{cells[1]:>10}")
    print()

    print("=" * 104)
    print("B. SUPPORT")
    print("=" * 104)
    print(f"  {'band':<12}" + "".join(f"{n + ' med':>10}" for n in ("CI", "CT", "s2"))
          + "".join(f"{n + f' >={t}':>13}" for t in SUPPORT_AT for n in ("CI", "CT", "s2")))
    series = {"CI": (loaded["CI"]["size"], loaded["CI"]["support"]),
              "CT": (loaded["CT"]["size"], loaded["CT"]["support"]),
              "s2": (s2_sizes, s2_support)}
    for _lo, _hi, band in BANDS:
        cells_med, cells_share = [], []
        any_here = False
        for name in ("CI", "CT", "s2"):
            sizes, support = series[name]
            vals = [float(v) for s, v in zip(sizes, support, strict=True)
                    if band_of(int(s)) == band]
            any_here = any_here or bool(vals)
            cells_med.append(f"{statistics.median(vals):.4f}" if vals else "-")
        for threshold in SUPPORT_AT:
            for name in ("CI", "CT", "s2"):
                sizes, support = series[name]
                vals = [float(v) for s, v in zip(sizes, support, strict=True)
                        if band_of(int(s)) == band]
                cells_share.append(
                    f"{sum(1 for v in vals if v >= threshold) / len(vals):.1%}" if vals else "-")
        if any_here:
            print(f"  {band:<12}" + "".join(f"{c:>10}" for c in cells_med)
                  + "".join(f"{c:>13}" for c in cells_share))
    print()

    print("=" * 104)
    print("D. CORRESPONDENCE WITH s5 (final O50s)")
    print("=" * 104)
    arm_rows = {arm: [sorted(bits.unpack(loaded[arm]["members"][i]))
                      for i in range(len(loaded[arm]["size"]))] for arm in ("CI", "CT")}
    scored = {arm: best_j(s5_rows, arm_rows[arm], len(keys)) for arm in ("CI", "CT")}
    best = {arm: scored[arm][0] for arm in ("CI", "CT")}
    argbest = {arm: scored[arm][1] for arm in ("CI", "CT")}
    print(f"  {'band':<12}{'s5 themes':>10}  {'CI >=0.9':>13}{'CI >=0.7':>13}"
          f"{'CT >=0.9':>13}{'CT >=0.7':>13}")
    for _lo, _hi, band in BANDS:
        rows = [i for i in range(len(s5_rows)) if band_of(int(s5_sizes[i])) == band]
        if not rows:
            continue
        cells = []
        for arm in ("CI", "CT"):
            for cut in (0.9, 0.7):
                hit = sum(1 for i in rows if best[arm][i] >= cut)
                cells.append(f"{hit:,} ({hit / len(rows):.0%})")
        print(f"  {band:<12}{len(rows):>10,}  " + "".join(f"{c:>13}" for c in cells))
    cells = []
    for arm in ("CI", "CT"):
        for cut in (0.9, 0.7):
            hit = int((best[arm] >= cut).sum())
            cells.append(f"{hit:,} ({hit / len(s5_rows):.0%})")
    print(f"  {'ALL':<12}{len(s5_rows):>10,}  " + "".join(f"{c:>13}" for c in cells))
    print()
    ids = list(s5_hold)
    giants = sorted(((int(s5_sizes[i]), ids[i], i) for i in range(len(ids))
                     if s5_sizes[i] > 1280), reverse=True)
    print("  the 5 O50s giants and their best counterpart in each arm")
    print(f"  {'giant':<10}{'size':>8}   {'arm':<4}{'J':>7}{'size':>8}{'core':>7}")
    for size, node, row in giants:
        for arm in ("CI", "CT"):
            which = int(argbest[arm][row])
            if which < 0:
                print(f"  {node:<10}{size:>8,}   {arm:<4}{'-':>7}{'-':>8}{'-':>7}")
                continue
            print(f"  {node:<10}{size:>8,}   {arm:<4}{float(best[arm][row]):>7.3f}"
                  f"{int(loaded[arm]['size'][which]):>8,}"
                  f"{int(loaded[arm]['core_size'][which]):>7,}")
    print()

    # --- E. examples ---------------------------------------------------------------------------
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}
    out = args.out / "examples"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.md"):
        stale.unlink()
    rng = random.Random(SEED)
    written = []
    for arm in ("CI", "CT"):
        pool = [i for i in range(len(loaded[arm]["size"]))
                if int(loaded[arm]["size"][i]) >= EXAMPLE_MIN]
        pick = sorted(rng.sample(pool, min(EXAMPLES, len(pool))))
        lines = []
        for position, row in enumerate(pick, 1):
            members = arm_rows[arm][row]
            core = set(bits.unpack(loaded[arm]["cores"][row]))
            lines.append(f"## {arm}-{position:02d}  ({len(members)} pathways, "
                         f"{len(core)} in the core)")
            lines.append("")
            lines += sorted(
                f"- {named.get(keys[p], (keys[p], '?'))[0]} "
                f"[{named.get(keys[p], (keys[p], '?'))[1]}]"
                + ("  **core**" if p in core else "")
                for p in members)
            lines.append("")
        path = out / f"{arm}_examples.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
        print(f"  E: {len(pick)} {arm} themes of {EXAMPLE_MIN}+ members -> {path}")
    print("  not judged here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
