#!/usr/bin/env python3
"""KC2: sweep the absolute closeness bar on scrambles, then build at the chosen value. EXPLORATORY.

The fine level does not depend on ``c``, so it is computed once per side and the sweep reuses it.

Usage::

    uv run scripts/kc2_sweep.py --out SWEEP.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))
FINE_T = 1.5
SCRAMBLES = (3001, 3002, 3003)


def band_of(size: int) -> str:
    """Band label for a size.

    Args:
        size: Member count.

    Returns:
        The label, or ``"500+"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "500+"


def counts(themes: list[np.ndarray]) -> dict[str, int]:
    """Themes per band.

    Args:
        themes: Theme member arrays.

    Returns:
        Band label to count, plus the total.
    """
    out = {f"{lo}-{hi}": 0 for lo, hi in BANDS}
    out["500+"] = 0
    for theme in themes:
        out[band_of(len(theme))] += 1
    out["total"] = len(themes)
    return out


def units_for(matrix: np.ndarray, n: int, t: float) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """The fine level's kept themes and the units they induce.

    Args:
        matrix: The centred unit-vector matrix.
        n: Node count.
        t: Lifetime threshold.

    Returns:
        ``(kept, units)``.
    """
    from thema.ontology import kc
    from thema.ontology import mutualrank as mr

    near = mr.neighbours(matrix, mr.K_MAX)
    edges, rank = mr.mutual_rank_edges(near)
    fine = kc.fine_level(kc.filtration(edges, rank, n), n)
    alive = np.isfinite(fine.lifetime)
    kept = [fine.members[i] for i in np.flatnonzero(alive & (fine.lifetime >= t)).tolist()]
    leaves = kc.minimal(kept, n)
    units = [kept[i] for i in leaves]
    covered = {int(p) for i in leaves for p in kept[i].tolist()}
    units += [np.array([p], dtype=np.int64) for p in range(n) if p not in covered]
    return kept, units


def main(argv: list[str] | None = None) -> int:
    """Sweep c and report the table.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from thema.embed import centre_and_renormalise
    from thema.ontology import kc, kc2
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--share", type=float, default=kc.JOIN_SHARE)
    parser.add_argument("--max-levels", type=int, default=kc.MAX_LEVELS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    n = len(embedded.keys)
    base, _mean = centre_and_renormalise(embedded.vectors)
    base = np.ascontiguousarray(base.astype(np.float32))

    marks: dict[str, float] = {}
    clock = time.perf_counter()
    sides: dict[str, tuple[list[np.ndarray], list[np.ndarray]]] = {}
    sides["real"] = units_for(base, n, FINE_T)
    for seed in SCRAMBLES:
        matrix = np.ascontiguousarray(null_embeddings(base, seed).astype(np.float32))
        sides[str(seed)] = units_for(matrix, n, FINE_T)
    marks["fine levels, all four sides"] = time.perf_counter() - clock
    print(f"KC2 SWEEP  n={n:,}, fine t={FINE_T}, join share {args.share}, "
          f"max levels {args.max_levels}")
    for side, (kept, units) in sides.items():
        print(f"  {side:<6} fine kept {len(kept):>5,}  units {len(units):>7,}")
    print(f"  fine levels: {marks['fine levels, all four sides']:.0f}s, "
          f"peak {peak_mb():.0f} MB", flush=True)

    matrices = {"real": base}
    for seed in SCRAMBLES:
        matrices[str(seed)] = np.ascontiguousarray(
            null_embeddings(base, seed).astype(np.float32))

    clock = time.perf_counter()
    rows: list[dict] = []
    print(f"\n  {'c':<8}{'real':>8}{'3-10':>8}{'11-50':>8}{'51-200':>8}{'201-500':>9}"
          f"{'500+':>7}{'unplaced':>10}{'scr mean':>10}{'ratio':>9}   verdict")
    for c in kc2.C_GRID:
        per_side: dict[str, dict[str, int]] = {}
        unplaced: dict[str, int] = {}
        for side, (kept, units) in sides.items():
            levels = kc2.levels_at(units, matrices[side], c, args.share, args.max_levels)
            every = list(kept) + [m for level in levels for m in level]
            seen: set[bytes] = set()
            themes = []
            for m in every:
                key = m.astype(np.int32).tobytes()
                if key not in seen:
                    seen.add(key)
                    themes.append(m)
            per_side[side] = counts(themes)
            placed = {int(p) for m in themes for p in m.tolist()}
            unplaced[side] = n - len(placed)
        real = per_side["real"]
        scr = [per_side[str(s)]["total"] for s in SCRAMBLES]
        mean = float(np.mean(scr))
        ratio = mean / real["total"] if real["total"] else float("inf")
        ok = ratio <= kc2.TARGET_RATIO
        rows.append({"c": c, "real": real, "unplaced_real": unplaced["real"],
                     "scramble": {str(s): per_side[str(s)] for s in SCRAMBLES},
                     "unplaced_scramble": {str(s): unplaced[str(s)] for s in SCRAMBLES},
                     "scramble_mean": round(mean, 1), "ratio": round(ratio, 5),
                     "meets_target": bool(ok)})
        print(f"  {c:<8.3f}{real['total']:>8,}{real['3-10']:>8,}{real['11-50']:>8,}"
              f"{real['51-200']:>8,}{real['201-500']:>9,}{real['500+']:>7,}"
              f"{unplaced['real']:>10,}{mean:>10.1f}{ratio:>9.2%}   "
              f"{'MEETS 1%' if ok else ''}", flush=True)
    marks["c sweep"] = time.perf_counter() - clock

    chosen = next((r["c"] for r in rows if r["meets_target"]), None)
    print(f"\n  sweep {marks['c sweep']:.0f}s, peak {peak_mb():.0f} MB")
    if chosen is None:
        print(f"  EARLY STOP: no c in {kc2.C_GRID[0]}..{kc2.C_GRID[-1]} reaches a ratio of "
              f"{kc2.TARGET_RATIO}")
    else:
        print(f"  CHOSEN c = {chosen} (lowest meeting the 1% target)")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "fine_t": FINE_T, "share": args.share, "max_levels": args.max_levels,
        "grid": list(kc2.C_GRID), "target_ratio": kc2.TARGET_RATIO,
        "fine": {s: {"kept": len(k), "units": len(u)} for s, (k, u) in sides.items()},
        "rows": rows, "chosen_c": chosen,
        "timing_seconds": {k: round(v, 1) for k, v in marks.items()},
        "peak_mb": round(peak_mb(), 1),
    }, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
