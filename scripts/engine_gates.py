#!/usr/bin/env python3
"""The gates table: G1 held-out FDR, G2 stability, G3 unplaced, G4 STRING coherence.

An arm must pass all four to be eligible for the scores. The gates come first and the scores cannot
promote a failed arm -- `engine_scores.py --eligible` is how that is enforced, and this script is
what produces the list it is given.

Where each number comes from:

- **G1** is read from the arm's own FLOORS file, written by the build that confirmed it -- not the
  manifest, which records only `heldout_confirmed: true` and the FDR in prose. It is never
  recomputed here: the held-out scrambles are read ONCE, by the build, and a second reading would
  make "held out" false.
- **G2** is `theme_match.py` between the arm's two half-builds, worse direction, run by the same
  script for every arm.
- **G3** is `n_effectively_unplaced / n` from the manifest.
- **G4** is read from `string_coherence.py`'s report, if it was run.

Usage::

    uv run scripts/engine_gates.py --arm A=recurrent_dag_10770 --arm B=v0.3x_engines/leiden
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#: Declared thresholds.
MAX_FDR_OVERALL = 0.01
MAX_FDR_STRATUM = 0.02
STABILITY_SLACK = 0.02
MAX_UNPLACED_SHARE = 0.05


def halves_of(base: Path, path: str) -> tuple[Path, Path]:
    """The two stability half-builds of an arm.

    Args:
        base: ``data/ontology``.
        path: The arm's build path under ``base``.

    Returns:
        The rows 1-100 and rows 101-200 directories.
    """
    if path.endswith("recurrent_dag_10770"):
        return (base / "v0.3" / "recurrent_dag_10770_r1-100",
                base / "v0.3" / "recurrent_dag_10770_r101-200")
    return base / f"{path}_r1-100", base / f"{path}_r101-200"


def _floors_beside(data: Path, manifest: dict) -> Path | None:
    """Find the floors file a build solved, from the manifest's own parameters.

    Args:
        data: The data directory.
        manifest: The build's manifest.

    Returns:
        The floors path, or None if the manifest does not say enough to locate it.
    """
    universe = manifest.get("universe_digest")
    cap = manifest.get("size_cap")
    cut = manifest.get("inclusion_cut") or manifest.get("inclusion_threshold")
    engine = manifest.get("engine") or "ward"
    rows = manifest.get("rows")
    scramble = manifest.get("scramble_rows")
    if None in (universe, cap, cut, rows, scramble):
        return None
    key = f"cap{cap}_inc{int(round(float(cut) * 100)):03d}"
    if engine != "ward":
        key = f"{key}_{engine}"
    # GLOBBED, not reconstructed: the manifest's `space` is a DESCRIPTION
    # ("centred-renormalised") and the tree directory is named for the flag ("centred"), so
    # building the path from the manifest silently misses. The universe digest in the directory
    # name is what makes the glob unambiguous.
    found = sorted((data / "ontology" / "v0.3" / "trees").glob(
        f"*_{universe}/completions/{key}/floors_r{rows}_n{scramble}.json"
    ))
    return found[0] if found else None


def stability(left: Path, right: Path) -> float | None:
    """Worse-direction final-theme match between two builds.

    Args:
        left: One half-build.
        right: The other.

    Returns:
        The worse-direction share, or None if either half is missing.
    """
    if not (left / "nodes.tsv").is_file() or not (right / "nodes.tsv").is_file():
        return None
    # Read the JSON, not stdout. Scraping the printed line was the first version and it picked up
    # the 90% PASS MARK from the same sentence as the result, reporting arm A's stability as 0.900
    # when it is 0.855 -- a wrong number that looked plausible, which is the worst kind.
    with tempfile.TemporaryDirectory() as scratch:
        report = Path(scratch) / "match.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "theme_match.py"),
             str(left), str(right), "--out", str(report)],
            capture_output=True, text=True, check=False,
        )
        if not report.is_file():
            return None
        got = json.loads(report.read_text())
    key = f"share_ge_{got.get('theta', 0.7):.2f}"
    both = [got[d][key] for d in ("forward", "backward") if key in got.get(d, {})]
    return min(both) if both else None


def num(value: float | None) -> float:
    """A figure that is not available prints as nan rather than crashing the row.

    Args:
        value: The figure, or None.

    Returns:
        The figure, or nan.
    """
    return float("nan") if value is None else float(value)


def main(argv: list[str] | None = None) -> int:
    """Assemble the gates table and print the eligible list.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--arm", action="append", default=[], help="NAME=path under data/ontology/")
    parser.add_argument("--reference", default="A")
    parser.add_argument("--string", type=Path, default=None,
                        help="string_coherence.py's report, for G4")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    base = args.data / "ontology"
    g4 = {}
    if args.string and args.string.is_file():
        g4 = json.loads(args.string.read_text()).get("arms", {})

    rows: dict[str, dict] = {}
    for spec in args.arm:
        name, path = spec.split("=", 1)
        directory = base / path
        if not (directory / "manifest.json").is_file():
            print(f"  {name}: NOT BUILT ({directory})", flush=True)
            rows[name] = {"built": False}
            continue
        manifest = json.loads((directory / "manifest.json").read_text())
        floors_path = manifest.get("floors_file")
        overall, worst = None, None
        found = Path(floors_path) if floors_path else _floors_beside(args.data, manifest)
        if found is not None and found.is_file():
            solved = json.loads(found.read_text())
            overall = solved.get("overall_fdr")
            held_out = [
                float(row["heldout_fdr"]) for row in solved.get("strata", [])
                if isinstance(row, dict) and row.get("heldout_fdr") is not None
            ]
            worst = max(held_out) if held_out else None
        n = int(manifest.get("n", 0)) or 1
        unplaced = int(manifest.get("n_effectively_unplaced", 0)) / n
        left, right = halves_of(base, path)
        rows[name] = {
            "built": True, "path": path,
            "nodes": manifest.get("n_nodes"), "roots": manifest.get("n_roots"),
            "engine": manifest.get("engine", "ward"),
            "g1_overall_fdr": overall, "g1_worst_stratum": worst,
            "g3_unplaced_share": round(unplaced, 5),
            "g2_stability": stability(left, right),
            "g4_fraction": g4.get(name, {}).get("fraction_p_lt_alpha"),
        }

    ref = rows.get(args.reference, {})
    ref_stability = ref.get("g2_stability")
    ref_g4 = ref.get("g4_fraction")

    print(f"\n{'arm':<5}{'nodes':>8}{'G1 FDR':>9}{'worst':>8}{'G2 stab':>9}"
          f"{'G3 unpl':>9}{'G4 coh':>8}   gates")
    eligible = []
    for name, got in rows.items():
        if not got.get("built"):
            print(f"{name:<5}{'--':>8}{'not built':>9}")
            continue
        checks = {}
        checks["G1"] = (got["g1_overall_fdr"] is not None
                        and got["g1_overall_fdr"] <= MAX_FDR_OVERALL
                        and (got["g1_worst_stratum"] is None
                             or got["g1_worst_stratum"] <= MAX_FDR_STRATUM))
        checks["G2"] = (got["g2_stability"] is not None and ref_stability is not None
                        and got["g2_stability"] >= ref_stability - STABILITY_SLACK)
        checks["G3"] = got["g3_unplaced_share"] <= MAX_UNPLACED_SHARE
        checks["G4"] = (True if ref_g4 is None or got["g4_fraction"] is None
                        else got["g4_fraction"] >= ref_g4 - 0.05)
        got["gates"] = {k: bool(v) for k, v in checks.items()}
        got["eligible"] = all(checks.values())
        if got["eligible"]:
            eligible.append(name)
        shown = " ".join(f"{k}{'+' if v else '-'}" for k, v in checks.items())
        print(f"{name:<5}{got['nodes'] or 0:>8,}"
              f"{num(got['g1_overall_fdr']):>9.5f}"
              f"{num(got['g1_worst_stratum']):>8.4f}"
              f"{num(got['g2_stability']):>9.3f}"
              f"{got['g3_unplaced_share']:>9.4f}"
              f"{num(got['g4_fraction']):>8.3f}"
              f"   {shown}  {'ELIGIBLE' if got['eligible'] else 'FAILS'}")
    if ref_g4 is None:
        print("\n  G4 NOT RUN (no STRING report given): the gate is treated as passed and the "
              "decision rests on G1-G3, as the declaration directs.")
    print(f"\n  eligible: {','.join(eligible) if eligible else 'NONE'}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(
            {"thresholds": {"fdr_overall": MAX_FDR_OVERALL, "fdr_stratum": MAX_FDR_STRATUM,
                            "stability_slack": STABILITY_SLACK,
                            "unplaced_share": MAX_UNPLACED_SHARE},
             "reference": args.reference, "arms": rows, "eligible": eligible},
            indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
