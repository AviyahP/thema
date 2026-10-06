#!/usr/bin/env python3
"""HiDeF at its best on the KC2 deciding table. EXPLORATORY, REPORT ONLY.

A 4 x 5 grid, k in {5, 10, 15, 30} by maxres in {25, 50, 100, 200, 300}, other settings at the
existing defaults (tau 0.75, chi 5, consensus p 75, Leiden, seed 0). Four of the twenty already
exist and are reused rather than rebuilt.

**Scored with exactly the KC2 deciding-table code**, imported from `kc2_report` rather than
reimplemented: same source only, recall banded by the curated set's size and precision by the
theme's size, match at best Jaccard > 0.5. Reusing that code is the point -- a comparison where
HiDeF is measured by a second implementation of the same measure is not a comparison.

The 10-minute rule: if one setting exceeds it, the larger maxres values for that k are skipped and
the skip is reported rather than left as a gap.

Usage::

    uv run scripts/hidef_grid.py --out GRID.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: The declared grid.
K_VALUES: tuple[int, ...] = (5, 10, 15, 30)
MAXRES_VALUES: tuple[float, ...] = (25.0, 50.0, 100.0, 200.0, 300.0)

#: Builds that already exist, as (k, maxres) -> directory name.
EXISTING: dict[tuple[int, float], str] = {
    (15, 25.0): "hidef_10770_k15",
    (15, 50.0): "hidef_10770_k15_maxres50",
    (15, 100.0): "hidef_10770_k15_maxres100",
    (30, 25.0): "hidef_10770_k30",
}

#: Wall-clock guard, in seconds.
TIME_LIMIT = 600.0


def directory_for(k: int, maxres: float) -> str:
    """Where a grid setting's build lives.

    Args:
        k: Neighbours.
        maxres: Maximum Leiden resolution.

    Returns:
        The directory name under the version directory.
    """
    if (k, maxres) in EXISTING:
        return EXISTING[(k, maxres)]
    return f"hidef_grid_k{k}_maxres{int(maxres)}"


def main(argv: list[str] | None = None) -> int:
    """Build what is missing, then score the whole grid.

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
    parser.add_argument("--build", action="store_true", help="build the missing settings")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    report: dict = {"grid": {"k": list(K_VALUES), "maxres": list(MAXRES_VALUES)},
                    "time_limit_seconds": TIME_LIMIT, "builds": {}, "skipped": [],
                    "reused": [directory_for(k, m) for (k, m) in EXISTING]}

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
                done = subprocess.run(
                    [sys.executable, str(Path(__file__).parent / "build_hidef.py"),
                     "--k", str(k), "--maxres", str(maxres), "--directory", name],
                    capture_output=True, text=True, check=False,
                )
                seconds = time.perf_counter() - clock
                ok = (root / name / "members.tsv").is_file()
                print(f"  {label}: {'built' if ok else 'FAILED'} in {seconds:.0f}s", flush=True)
                if not ok:
                    tail = (done.stderr or done.stdout).strip().splitlines()[-2:]
                    for line in tail:
                        print(f"      {line[:120]}", flush=True)
                report["builds"][label] = {"directory": name, "reused": False,
                                           "seconds": round(seconds, 1), "built": ok}
                if seconds > TIME_LIMIT:
                    over = True
                    print(f"      over the {TIME_LIMIT:.0f}s limit; larger maxres at k={k} "
                          f"will be skipped", flush=True)

    # ---- score everything available with the KC2 code
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    position = {key: i for i, key in enumerate(keys)}
    sets = {source: curated(args.data, keys, prefix)
            for source, prefix in (("reactome", "reactome:"), ("go", "go:"))}

    available: dict[str, Path] = {}
    for k in K_VALUES:
        for maxres in MAXRES_VALUES:
            path = root / directory_for(k, maxres)
            if (path / "members.tsv").is_file():
                available[f"k{k}_maxres{int(maxres)}"] = path
    # Arm A beside it, from the same code.
    if (root / "recurrent_dag_10770" / "members.tsv").is_file():
        available["A (frozen)"] = root / "recurrent_dag_10770"
    if (root.parent / "v0.3x_engines" / "KC2" / "members.tsv").is_file():
        available["KC2"] = root.parent / "v0.3x_engines" / "KC2"

    bands = [f"{lo}-{hi}" for lo, hi in BANDS]
    scored: dict[str, dict] = {}
    for label, path in available.items():
        build = read_build(path)
        row: dict = {"themes": len(build)}
        for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
            own = [{position[key] for key in theme if key.startswith(prefix)}
                   for theme in build]
            own = [s for s in own if len(s) >= 3]
            row[source] = recall_precision(own, sets[source], n)
        mean_recall = float(np.mean([
            row[source][b]["recall"] for source in ("reactome", "go") for b in bands
            if row[source][b]["recall"] is not None
        ])) if build else 0.0
        row["mean_recall_8_cells"] = round(mean_recall, 4)
        scored[label] = row
        print(f"  scored {label:<20} themes {len(build):>5,}  "
              f"mean recall {mean_recall:.4f}", flush=True)
    report["scored"] = scored

    hidef_only = {k: v for k, v in scored.items() if k.startswith("k")}
    best = max(hidef_only, key=lambda k: hidef_only[k]["mean_recall_8_cells"]) \
        if hidef_only else None
    report["best_by_mean_recall"] = best
    oracle: dict[str, dict] = {}
    for source in ("reactome", "go"):
        for b in bands:
            cells = {k: v[source][b] for k, v in hidef_only.items()}
            best_r = max((k for k in cells if cells[k]["recall"] is not None),
                         key=lambda k: cells[k]["recall"], default=None)
            best_p = max((k for k in cells if cells[k]["precision"] is not None),
                         key=lambda k: cells[k]["precision"], default=None)
            oracle[f"{source}|{b}"] = {
                "best_recall_setting": best_r,
                "best_recall": None if best_r is None else cells[best_r]["recall"],
                "best_precision_setting": best_p,
                "best_precision": None if best_p is None else cells[best_p]["precision"],
            }
    report["oracle"] = oracle

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"\n  best HiDeF by mean recall over the 8 cells: {best}")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
