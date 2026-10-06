#!/usr/bin/env python3
"""Extend the HiDeF grid at its winning edge, and match A to its theme count. REPORT ONLY.

The first grid's winner was k = 5, maxres = 300 -- the corner of the grid, with recall rising
monotonically toward it in both directions. A search pressed against its own boundary has not
finished, so this extends past that corner: k in {3, 4, 5} by maxres in {300, 500, 800}.

Two reporting changes the brief asks for, both of which make the comparison fairer to HiDeF and
harder for A:

- **A six-cell mean that drops 201-500.** Reactome has only 3 curated sets there and GO 33, and
  every HiDeF setting scored exactly 33.3% on the Reactome cell against A's 0.0%. That single cell
  of three sets was carrying the eight-cell mean, so the brief asks for the mean without it. Both
  are reported.
- **A matched theme count.** A emits 6,244 themes against the best HiDeF's ~2,900, and recall
  rises with theme count for every arm. So A is also scored on its top N themes by support, N being
  the best HiDeF's count, which asks whether A's lead is a property of its ranking or of its volume.

Scored with exactly the KC2 deciding-table code, imported from `kc2_report`.

Usage::

    uv run scripts/hidef_grid2.py --build --out GRID2.json
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

K_VALUES: tuple[int, ...] = (3, 4, 5)
MAXRES_VALUES: tuple[float, ...] = (300.0, 500.0, 800.0)
TIME_LIMIT = 600.0

#: Already built by the first grid.
REUSE: dict[tuple[int, float], str] = {(5, 300.0): "hidef_grid_k5_maxres300"}


def directory_for(k: int, maxres: float) -> str:
    """Where a setting's build lives.

    Args:
        k: Neighbours.
        maxres: Maximum Leiden resolution.

    Returns:
        The directory name.
    """
    return REUSE.get((k, maxres), f"hidef_grid_k{k}_maxres{int(maxres)}")


def top_by_support(path: Path, n_keep: int) -> list[list[str]]:
    """A build's themes, ranked by support, truncated to ``n_keep``.

    Args:
        path: The build directory.
        n_keep: How many themes to keep.

    Returns:
        Member key lists for the highest-support themes, most supported first.
    """
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row["node"]] = float(row.get("support") or 0.0)
    members: dict[str, list[str]] = {}
    with (path / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members.setdefault(row["node"], []).append(row["key"])
    # Ties broken toward the LARGER theme, so truncation does not silently prefer the small ones
    # and flatter the fine bands.
    order = sorted(members, key=lambda node: (-support.get(node, 0.0), -len(members[node]), node))
    return [members[node] for node in order[:n_keep]]


def main(argv: list[str] | None = None) -> int:
    """Build, score, and report.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from kc2_report import BANDS, curated, read_build, recall_precision
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    report: dict = {"grid": {"k": list(K_VALUES), "maxres": list(MAXRES_VALUES)},
                    "time_limit_seconds": TIME_LIMIT, "builds": {}, "skipped": []}

    if args.build:
        for k in K_VALUES:
            over = False
            for maxres in MAXRES_VALUES:
                name = directory_for(k, maxres)
                label = f"k{k}_maxres{int(maxres)}"
                if (root / name / "members.tsv").is_file():
                    print(f"  {label}: reusing {name}", flush=True)
                    report["builds"][label] = {"directory": name, "reused": True}
                    continue
                if over:
                    print(f"  {label}: SKIPPED, a smaller maxres at k={k} exceeded "
                          f"{TIME_LIMIT:.0f}s", flush=True)
                    report["skipped"].append(label)
                    continue
                clock = time.perf_counter()
                subprocess.run(
                    [sys.executable, str(Path(__file__).parent / "build_hidef.py"),
                     "--k", str(k), "--maxres", str(maxres), "--directory", name],
                    capture_output=True, text=True, check=False,
                )
                seconds = time.perf_counter() - clock
                ok = (root / name / "members.tsv").is_file()
                print(f"  {label}: {'built' if ok else 'FAILED'} in {seconds:.0f}s", flush=True)
                report["builds"][label] = {"directory": name, "reused": False,
                                           "seconds": round(seconds, 1), "built": ok}
                if seconds > TIME_LIMIT:
                    over = True
                    print(f"      over the {TIME_LIMIT:.0f}s limit; larger maxres at k={k} "
                          f"will be skipped", flush=True)

    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    position = {key: i for i, key in enumerate(keys)}
    sets = {source: curated(args.data, keys, prefix)
            for source, prefix in (("reactome", "reactome:"), ("go", "go:"))}
    bands = [f"{lo}-{hi}" for lo, hi in BANDS]
    six = [b for b in bands if b != "201-500"]

    def score(build: list[list[str]]) -> dict:
        """Score one build with the KC2 code.

        Args:
            build: Member key lists.

        Returns:
            Per source the banded cells, plus the two means.
        """
        row: dict = {"themes": len(build)}
        for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
            own = [{position[key] for key in theme if key.startswith(prefix)}
                   for theme in build]
            own = [s for s in own if len(s) >= 3]
            row[source] = recall_precision(own, sets[source], n)
        for name, which in (("mean_recall_8_cells", bands), ("mean_recall_6_cells", six)):
            vals = [row[s][b]["recall"] for s in ("reactome", "go") for b in which
                    if row[s][b]["recall"] is not None]
            row[name] = round(float(np.mean(vals)), 4) if vals else 0.0
        return row

    # Everything in the extended grid, plus the first grid's full set for the combined oracle.
    scored: dict[str, dict] = {}
    for k in K_VALUES:
        for maxres in MAXRES_VALUES:
            path = root / directory_for(k, maxres)
            if (path / "members.tsv").is_file():
                scored[f"k{k}_maxres{int(maxres)}"] = score(read_build(path))
    first_grid = [(kk, mm) for kk in (5, 10, 15, 30) for mm in (25, 50, 100, 200, 300)]
    for kk, mm in first_grid:
        label = f"k{kk}_maxres{int(mm)}"
        if label in scored:
            continue
        for candidate in (f"hidef_grid_k{kk}_maxres{int(mm)}",
                          {25: "hidef_10770_k15", 50: "hidef_10770_k15_maxres50",
                           100: "hidef_10770_k15_maxres100"}.get(mm, "") if kk == 15 else "",
                          "hidef_10770_k30" if (kk, mm) == (30, 25) else ""):
            if candidate and (root / candidate / "members.tsv").is_file():
                scored[label] = score(read_build(root / candidate))
                break

    arm_a = root / "recurrent_dag_10770"
    scored["A (frozen)"] = score(read_build(arm_a))

    hidef_only = {k: v for k, v in scored.items() if k.startswith("k")}
    best6 = max(hidef_only, key=lambda k: hidef_only[k]["mean_recall_6_cells"])
    best8 = max(hidef_only, key=lambda k: hidef_only[k]["mean_recall_8_cells"])
    report["best_by_mean_recall_6_cells"] = best6
    report["best_by_mean_recall_8_cells"] = best8

    n_match = hidef_only[best6]["themes"]
    scored[f"A top {n_match} by support"] = score(top_by_support(arm_a, n_match))
    report["matched_n"] = n_match

    oracle: dict[str, dict] = {}
    for source in ("reactome", "go"):
        for b in bands:
            cells = {k: v[source][b] for k, v in hidef_only.items()}
            br = max((k for k in cells if cells[k]["recall"] is not None),
                     key=lambda k: cells[k]["recall"], default=None)
            bp = max((k for k in cells if cells[k]["precision"] is not None),
                     key=lambda k: cells[k]["precision"], default=None)
            oracle[f"{source}|{b}"] = {
                "best_recall_setting": br,
                "best_recall": None if br is None else cells[br]["recall"],
                "best_precision_setting": bp,
                "best_precision": None if bp is None else cells[bp]["precision"]}
    report["oracle_full_grid"] = oracle
    report["scored"] = scored

    order = [f"k{k}_maxres{int(m)}" for k in K_VALUES for m in MAXRES_VALUES]
    for source in ("reactome", "go"):
        print(f"\n  {source.upper()}")
        print(f"    {'setting':<20}{'themes':>7}"
              + "".join(f"{b:>19}" for b in bands) + f"{'6-cell':>9}{'8-cell':>9}")
        for label in order + ["A (frozen)", f"A top {n_match} by support"]:
            if label not in scored:
                continue
            row = scored[label]
            cells = ""
            for b in bands:
                g = row[source][b]
                rc = "  -- " if g["recall"] is None else f"{g['recall']:.1%}"
                pc = "  -- " if g["precision"] is None else f"{g['precision']:.1%}"
                cells += f"{rc + '/' + pc:>19}"
            star = " *" if label == best6 else ""
            print(f"    {label:<20}{row['themes']:>7,}{cells}"
                  f"{row['mean_recall_6_cells']:>9.4f}{row['mean_recall_8_cells']:>9.4f}{star}")

    print(f"\n  best over 6 cells (201-500 dropped): {best6}")
    print(f"  best over 8 cells:                   {best8}")
    print(f"  matched theme count N = {n_match:,}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
