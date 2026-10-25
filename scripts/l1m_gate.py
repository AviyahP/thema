"""The gate for L1m, calibrated on scrambles exactly as O50s's gate. Prompt 65, 24 Oct 2026.

Exploratory; **nothing adopted.** L1m's 10-run bar is provisional, and two scramble seeds showed it
admits noise below 12 pathways. This replaces it with **O50s's own procedure, reused rather than
reimplemented**:

* ``o50s_build.O50S_STRATA`` -- the 13 size bands, 3 / 4 / 5 / 6 / 7-9 / 10-19 / 20-39 / 40-79 /
  80-159 / 160-319 / 320-639 / 640-1279 / 1280+;
* ``o50s_build.TARGET = 0.008`` and ``RULE_OF_THREE = 3.0``;
* ``o50s_build.solve_stratum`` -- one floor per band, the cut ladder being every distinct support
  value real **or** scrambled, with the rule-of-three bound where no scrambled theme is observed;
* ``o50s_build.confirm_with`` -- the held-out check, applied once;
* ``o50s_build.CAP_OVERALL = 0.01`` and ``CAP_STRATUM = 0.02``;
* ``thema.ontology.v04.gate`` and ``stratum_of`` -- a band with no floor admits **nothing**, so a
  gap in the calibration cannot silently open the gate.

Two things differ from O50s, both because L1m is a different population and neither a change to the
procedure. O50s keeps its first five strata frozen at their cal8 floors (``FROZEN_SMALL = 5``);
there is no earlier L1m calibration to freeze, so all 13 bands are solved here. And support is
rounded to **six decimals** on every side before any comparison, which is what ``Material.rows``
does in O50s -- comparing raw floats across two arrays loses themes that should be kept.

Floors are solved on calibration seeds 3001-3010 only and the held-out seeds 4001-4006 are read
exactly once, by the checker.

Usage:
    uv run scripts/l1m_gate.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

FOUND_BAR = 10
RUNS = 200
TOP_ROOT_MIN = 200
SEED = 20261024

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The reporting band a size falls in. Distinct from the 13 calibration strata.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return BANDS[0][2]


def rows_of(size: np.ndarray, support: np.ndarray) -> list[tuple[int, float]]:
    """``(size, support)`` rows, with support rounded as ``Material.rows`` rounds it.

    Args:
        size: Member count per theme.
        support: Support per theme.

    Returns:
        One row per theme.
    """
    return [(int(a), round(float(b), 6)) for a, b in zip(size, support, strict=True)]


def load_side(where: Path) -> tuple[np.ndarray, np.ndarray]:
    """One L1m side's sizes and supports, from either the full or the light archive.

    Args:
        where: A directory ``l1m_build`` wrote.

    Returns:
        ``(size, support)``.
    """
    light = where / "themes_light.npz"
    if light.is_file():
        with np.load(light) as handle:
            return handle["size"], handle["support"]
    with np.load(where / "themes.npz") as handle:
        return (np.diff(handle["member_indptr"]).astype(np.int64), handle["support"])


def calibrate(real: list[tuple[int, float]],
              nulls: list[list[tuple[int, float]]],
              held: list[list[tuple[int, float]]],
              report: bool = True) -> dict[str, object]:
    """Solve one floor per band on the calibration seeds, then confirm once on held-out.

    Args:
        real: The real side's rows.
        nulls: One list of rows per calibration seed.
        held: One list of rows per held-out seed.
        report: Print progress.

    Returns:
        ``{solved, confirmed}``.
    """
    from o50s_build import O50S_STRATA, TARGET, confirm_with, solve_stratum
    from thema.ontology.v04 import stratum_of

    solved: list[dict] = []
    clock = time.perf_counter()
    for index, (low, high) in enumerate(O50S_STRATA):
        mine = [s for size, s in real if stratum_of(size, O50S_STRATA) == index]
        per = [[s for size, s in rows if stratum_of(size, O50S_STRATA) == index]
               for rows in nulls]
        entry = solve_stratum(mine, per, TARGET)
        entry["stratum"] = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
        solved.append(entry)
        if report:
            print(f"    {entry['stratum']:>9}  real {entry['real']:>7,}  "
                  f"floor {entry['floor']}  fdr {entry['calibration_fdr']}  "
                  f"bounded {entry['bounded']}", flush=True)
    confirmed = confirm_with(real, held, solved, O50S_STRATA)
    if report:
        print(f"    solved 13 bands on {len(nulls)} calibration seeds, confirmed once on "
              f"{len(held)} held-out ({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"solved": solved, "confirmed": confirmed}


def brute_solve(real: list[tuple[int, float]], nulls: list[list[tuple[int, float]]],
                index: int) -> dict[str, object]:
    """One band's floor recomputed by an explicit loop, as a check on the reused solver.

    Args:
        real: The real side's rows.
        nulls: One list of rows per calibration seed.
        index: Which stratum.

    Returns:
        The floor and the rate behind it.
    """
    from o50s_build import O50S_STRATA, RULE_OF_THREE, TARGET
    from thema.ontology.v04 import stratum_of

    mine = [s for size, s in real if stratum_of(size, O50S_STRATA) == index]
    per = [[s for size, s in rows if stratum_of(size, O50S_STRATA) == index] for rows in nulls]
    pooled = [s for one in per for s in one]
    seeds = max(len(per), 1)
    for cut in sorted(set(pooled) | set(mine)):
        keep = len([s for s in mine if s >= cut])
        if not keep:
            continue
        total = len([s for s in pooled if s >= cut])
        mean = RULE_OF_THREE / seeds if total == 0 else total / seeds
        if mean / keep <= TARGET:
            return {"floor": round(float(cut), 6), "real": keep,
                    "fdr": round(mean / keep, 8), "bounded": total == 0}
    return {"floor": None, "real": len(mine), "fdr": None, "bounded": False}


def section_a(got: dict[str, object], args: argparse.Namespace) -> dict[str, object]:
    """A: the floors, beside O50s's and beside the provisional bar.

    Args:
        got: As :func:`calibrate` returns.
        args: Parsed arguments.

    Returns:
        The table as data.
    """
    o50s = {}
    floors = json.loads((args.o50s_floors).read_text(encoding="utf-8"))
    for entry in (floors if isinstance(floors, list) else floors.get("solved", [])):
        o50s[entry.get("stratum")] = entry.get("effective")
    print("=" * 104)
    print("A. FLOORS PER BAND, SOLVED ON THE 10 CALIBRATION SEEDS")
    print("=" * 104)
    print(f"  {'band':>9}{'real themes':>13}{'floor':>10}{'runs of 200':>13}"
          f"{'cal FDR':>11}{'bounded':>9}{'O50s floor':>12}{'10-run bar':>12}")
    rows = {}
    for entry in got["solved"]:
        floor = entry["effective"]
        theirs = o50s.get(entry["stratum"])
        fdr = entry["calibration_fdr"]
        shown_floor = "--" if floor is None else f"{floor:.4f}"
        shown_runs = "--" if floor is None else f"{floor * RUNS:.1f}"
        shown_fdr = "--" if fdr is None else f"{fdr:.5f}"
        shown_theirs = "--" if theirs is None else f"{theirs:.4f}"
        print(f"  {entry['stratum']:>9}{entry['real']:>13,}{shown_floor:>10}"
              f"{shown_runs:>13}{shown_fdr:>11}{str(entry['bounded']):>9}"
              f"{shown_theirs:>12}{FOUND_BAR / RUNS:>12.4f}")
        rows[entry["stratum"]] = {"real": entry["real"], "floor": floor,
                                 "calibration_fdr": entry["calibration_fdr"],
                                 "bounded": entry["bounded"], "o50s": theirs}
    print()
    print(f"  the provisional bar was {FOUND_BAR} runs of {RUNS}, support "
          f"{FOUND_BAR / RUNS:.4f}, the same number in every band")
    print()
    return rows


def section_b(got: dict[str, object]) -> dict[str, object]:
    """B: the held-out check.

    Args:
        got: As :func:`calibrate` returns.

    Returns:
        The table as data.
    """
    from o50s_build import CAP_OVERALL, CAP_STRATUM

    confirmed = got["confirmed"]
    print("=" * 104)
    print("B. HELD-OUT FDR, READ ONCE ON SEEDS 4001-4006")
    print("=" * 104)
    print(f"  {'band':>9}{'floor':>10}{'real kept':>12}{'scrambled (mean)':>19}"
          f"{'held-out FDR':>14}{'cap ' + str(CAP_STRATUM):>12}")
    bad = []
    for entry in confirmed["strata"]:
        fdr = entry.get("heldout_fdr")
        over = fdr is not None and fdr > CAP_STRATUM
        bad += [entry["stratum"]] if over else []
        floor = entry["effective"]
        shown_floor = "--" if floor is None else f"{floor:.4f}"
        shown_fdr = "--" if fdr is None else f"{fdr:.5f}"
        print(f"  {entry['stratum']:>9}{shown_floor:>10}"
              f"{entry.get('heldout_real', 0):>12,}"
              f"{entry.get('heldout_null', 0):>19,.2f}"
              f"{shown_fdr:>14}{('OVER' if over else 'ok'):>12}")
    print(f"  {'OVERALL':>9}{'':>10}{confirmed['overall_real']:>12,}"
          f"{confirmed['overall_null']:>19,.2f}"
          f"{(confirmed['overall_fdr'] if confirmed['overall_fdr'] is not None else 0):>14.5f}"
          f"{('OVER' if (confirmed['overall_fdr'] or 0) > CAP_OVERALL else 'ok'):>12}")
    print()
    if bad:
        print(f"  CAP FAILURE: bands over {CAP_STRATUM}: {bad}")
    if (confirmed["overall_fdr"] or 0) > CAP_OVERALL:
        print(f"  CAP FAILURE: overall {confirmed['overall_fdr']} over {CAP_OVERALL}")
    if not bad and (confirmed["overall_fdr"] or 0) <= CAP_OVERALL:
        print(f"  both caps hold: overall {confirmed['overall_fdr']} <= {CAP_OVERALL}, "
              f"every band <= {CAP_STRATUM}")
    print("  the floors were not touched after this check, by declaration")
    print()
    return {"confirmed": confirmed, "bands_over_cap": bad,
            "overall_over_cap": (confirmed["overall_fdr"] or 0) > CAP_OVERALL}


def section_c(size: np.ndarray, support: np.ndarray, found: np.ndarray,
              kept: np.ndarray, member_indptr: np.ndarray, member_pathway: np.ndarray,
              n: int) -> dict[str, object]:
    """C: what the calibrated gate keeps, against the provisional bar.

    Args:
        size: Member count per theme.
        support: Support per theme.
        found: Runs found per theme.
        kept: Boolean mask from the calibrated gate.
        member_indptr: Member offsets per theme.
        member_pathway: Concatenated members.
        n: Universe size.

    Returns:
        The table as data.
    """
    from core_merge_pairs import brute, counts_for, matrix

    bar = found >= FOUND_BAR
    bands = np.array([band_of(int(s)) for s in size])
    print("=" * 104)
    print("C. WHAT THE CALIBRATED GATE KEEPS, AGAINST THE PROVISIONAL 10-RUN BAR")
    print("=" * 104)
    print(f"  {'band':<12}{'all themes':>12}{'gated':>10}{'10-run bar':>12}{'change':>10}"
          f"{'gated share of the band':>26}")
    rows = {}
    for _lo, _hi, band in BANDS:
        where = bands == band
        if not where.any():
            continue
        a, b = int((where & kept).sum()), int((where & bar).sum())
        print(f"  {band:<12}{int(where.sum()):>12,}{a:>10,}{b:>12,}{a - b:>+10,}"
              f"{a / int(where.sum()):>26.1%}")
        rows[band] = {"all": int(where.sum()), "gated": a, "bar": b}
    print(f"  {'TOTAL':<12}{len(size):>12,}{int(kept.sum()):>10,}{int(bar.sum()):>12,}"
          f"{int(kept.sum()) - int(bar.sum()):>+10,}")
    print()
    out: dict[str, object] = {"per_band": rows, "gated": int(kept.sum()),
                              "bar": int(bar.sum())}
    for name, mask in (("calibrated gate", kept), ("10-run bar", bar)):
        which = np.flatnonzero(mask)
        listed = [member_pathway[member_indptr[t]:member_indptr[t + 1]].tolist() for t in which]
        sizes = np.array([len(r) for r in listed], dtype=np.int64)
        per_pathway = np.bincount(np.concatenate(listed) if listed else np.zeros(0, dtype=int),
                                  minlength=n)
        got = counts_for(matrix(listed, n), sizes, report=False)
        rng = np.random.default_rng(SEED)
        take = min(2000, len(listed))
        pick = np.sort(rng.choice(len(listed), size=take, replace=False))
        fast = counts_for(matrix([listed[int(i)] for i in pick], n), sizes[pick],
                          report=False)["totals"]
        slow = brute(listed, sizes, pick)
        same = all(fast[k] == slow[k] for k in slow)
        print(f"  {name:<18}{len(listed):>9,} themes   "
              f"{per_pathway.mean():>7.1f} themes per pathway   "
              f"{got['totals']['j05'] / max(len(listed), 1):>6.1f} non-nested J>=0.5 per theme   "
              f"({'verified' if same else 'MISMATCH'})")
        out[name] = {"themes": len(listed),
                     "themes_per_pathway": float(per_pathway.mean()),
                     "j05_per_theme": got["totals"]["j05"] / max(len(listed), 1),
                     "counts": got["totals"],
                     "verification": {"sparse": fast, "brute": slow, "identical": bool(same)}}
    print("  for comparison: L1 13.4 and O50s 15.7 non-nested pairs per theme; O50s 23.5 "
          "themes per pathway")
    print()
    return out


def section_d(kept: np.ndarray, member_indptr: np.ndarray, member_pathway: np.ndarray,
              n: int) -> dict[str, object]:
    """D: the DAG over the gated themes, with prompt 63's verified code.

    Args:
        kept: Boolean mask from the calibrated gate.
        member_indptr: Member offsets per theme.
        member_pathway: Concatenated members.
        n: Universe size.

    Returns:
        The table as data.
    """
    from scipy import sparse

    from l1_dag import brute_check, children_of, depths, reduce_transitive, relations

    which = np.flatnonzero(kept)
    rows = [member_pathway[member_indptr[t]:member_indptr[t + 1]] for t in which]
    sizes = np.array([len(r) for r in rows], dtype=np.int64)
    accepted = {"rows": rows, "sizes": sizes, "matrix": sparse.csr_matrix(
        (np.ones(int(sizes.sum()), dtype=np.int32),
         np.concatenate(rows) if rows else np.zeros(0, dtype=np.int64),
         np.concatenate([[0], np.cumsum(sizes)])), shape=(len(rows), n))}
    got = relations(accepted, report=False)
    dag = reduce_transitive(accepted, got, report=False)
    depth = depths(dag, len(sizes), sizes)
    check = brute_check(accepted, dag)
    counts = np.diff(dag["indptr"])
    roots = counts == 0
    kid_ptr, _kids = children_of(dag, len(sizes))
    kid_counts = np.diff(kid_ptr)
    bands = np.array([band_of(int(s)) for s in sizes])
    deepest = np.zeros(n, dtype=np.int64) - 1
    for t in range(len(sizes)):
        np.maximum.at(deepest, rows[t], depth[t])
    held = deepest >= 0
    print("=" * 104)
    print("D. THE DAG OVER THE GATED THEMES")
    print("=" * 104)
    print(f"  {'':<42}{'gated':>14}{'10-run bar (prompt 64)':>25}")
    print(f"  {'themes':<42}{len(sizes):>14,}{41605:>25,}")
    print(f"  {'edges':<42}{int(counts.sum()):>14,}{161869:>25,}")
    print(f"  {'roots':<42}{int(roots.sum()):>14,}{617:>25,}")
    print(f"  {'roots without the 3-5 themes':<42}"
          f"{int((roots & (sizes >= 6)).sum()):>14,}{578:>25,}")
    print(f"  {'multi-parent share':<42}"
          f"{(counts >= 2).sum() / max(len(sizes), 1):>14.2%}{0.8194:>25.2%}")
    print(f"  {'children per node, max':<42}{int(kid_counts.max()):>14,}{1295:>25,}")
    print(f"  {'children per node, median':<42}{np.median(kid_counts):>14.1f}{2.0:>25.1f}")
    print(f"  {'levels per pathway, median / max':<42}"
          f"{np.median(deepest[held]):>10.1f} / {int(deepest[held].max()):<3}"
          f"{12.0:>20.1f} / 22")
    print(f"  {'roots of 200+ pathways':<42}"
          f"{int((roots & (sizes >= TOP_ROOT_MIN)).sum()):>14,}{75:>25,}")
    print(f"  DAG verified against explicit set loops: "
          f"{'IDENTICAL' if check['identical'] else 'MISMATCH'}  {check}")
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
    return {"themes": len(sizes), "edges": int(counts.sum()), "roots": int(roots.sum()),
            "roots_without_3_5": int((roots & (sizes >= 6)).sum()),
            "multi_parent": float((counts >= 2).sum() / max(len(sizes), 1)),
            "children_max": int(kid_counts.max()),
            "children_median": float(np.median(kid_counts)),
            "levels_pathway": [float(np.median(deepest[held])), int(deepest[held].max())],
            "roots_200_plus": int((roots & (sizes >= TOP_ROOT_MIN)).sum()),
            "roots_by_band": by_band, "verification": check}


def main(argv: list[str] | None = None) -> int:
    """Calibrate the gate, confirm it once, and report sections A-D.

    Args:
        argv: Command line.

    Returns:
        0, or 1 if a cap fails or a check disagrees.
    """
    from o50s_build import CALIBRATION, HELDOUT, O50S_STRATA
    from thema.ontology.v04 import gate

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--l1m", type=Path,
                        default=Path("data/experiments/L1m_2026-10-24"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1m_gate_2026-10-24"))
    parser.add_argument("--o50s-floors", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22/"
                                     "floors_o50s.json"))
    args = parser.parse_args(argv)

    n = int(json.loads((args.space_root / "universe.json").read_text())["n_embedded"])
    print("PROMPT 65: THE GATE FOR L1m, O50s'S PROCEDURE UNCHANGED")
    print("  exploratory; nothing adopted. Floors solved on 3001-3010, confirmed once on "
          "4001-4006.")
    with np.load(args.l1m / "real" / "themes.npz") as handle:
        member_indptr = handle["member_indptr"]
        member_pathway = handle["member_pathway"]
        support = handle["support"]
        found = handle["found"]
    size = np.diff(member_indptr).astype(np.int64)
    real = rows_of(size, support)
    print(f"  real side: {len(size):,} L1m themes")

    def side_for(seed: int) -> Path:
        """Where a scramble side's L1m output lives.

        Args:
            seed: Scramble seed.

        Returns:
            The directory.
        """
        mine = args.out / "scramble" / f"seed{seed:05d}"
        return mine if mine.is_dir() else args.l1m / "scramble" / f"seed{seed:05d}"

    nulls, held = [], []
    for seed in CALIBRATION:
        nulls.append(rows_of(*load_side(side_for(seed))))
    for seed in HELDOUT:
        held.append(rows_of(*load_side(side_for(seed))))
    print(f"  {len(nulls)} calibration sides, {len(held)} held-out sides; "
          f"{sum(len(r) for r in nulls) / len(nulls):,.0f} themes per calibration side")
    print()
    got = calibrate(real, nulls, held)
    print()

    checks: dict[str, object] = {}
    for index in (0, 5, 9, 12):
        mine = brute_solve(real, nulls, index)
        entry = got["solved"][index]
        checks[f"solve band {entry['stratum']}"] = {
            "reused": entry["floor"], "brute": mine["floor"],
            "identical": entry["floor"] == mine["floor"]}
    print("  VERIFICATION: the reused solver against an explicit loop, four bands")
    for name, check in checks.items():
        print(f"    {name:<22}{'IDENTICAL' if check['identical'] else 'MISMATCH'}  {check}")
    print()

    kept = gate(real, got["solved"], O50S_STRATA)
    record: dict[str, object] = {"themes": len(size), "gated": int(kept.sum()),
                                 "verification": checks}
    record["A"] = section_a(got, args)
    record["B"] = section_b(got)
    record["C"] = section_c(size, support, found, kept, member_indptr, member_pathway, n)
    record["D"] = section_d(kept, member_indptr, member_pathway, n)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "floors_l1m.json").write_text(json.dumps({
        "strata": [list(s) for s in O50S_STRATA],
        "calibration": list(CALIBRATION), "heldout": list(HELDOUT),
        "solved": got["solved"], "confirmed": got["confirmed"],
        "note": "all 13 bands solved; O50s's FROZEN_SMALL does not apply, there being no earlier "
                "L1m calibration to freeze",
    }, indent=1, default=float) + "\n", encoding="utf-8")
    np.savez_compressed(args.out / "gated.npz", size=size, support=support, found=found,
                        kept=kept)
    (args.out / "report.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out}")
    bad = record["B"]["bands_over_cap"] or record["B"]["overall_over_cap"]
    return 1 if bad or not all(v["identical"] for v in checks.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
