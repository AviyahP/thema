"""PART 2 section E of prompt 55: curated recall and precision per band, with CIs.

Declared 22 Oct 2026. Evaluation only; nothing is adopted and no verdict is offered.

This is a thin wrapper over ``scripts/v04_score.py``, which already computes per-band recall and
precision against Reactome's and GO's curated descendant sets at J > 0.5, with a curated-set
cluster bootstrap. ``v04_score`` prunes the bootstrap draws when it writes its JSON, so the per-arm
intervals
cannot be recovered from it; this script calls the same ``cells_with_ci`` estimator and keeps
them, and uses ``v04_score.ci_of_difference`` for the interval on S2 minus O50s. **Nothing is
re-implemented** -- the estimator, the bands, the bootstrap count and the seed are all v04_score's.

Usage:
    uv run scripts/s2_recall_ci.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main(argv: list[str] | None = None) -> int:
    """Print recall and precision with CIs for S2 and O50s.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.data.hierarchy import read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, descendant_sets, go_edges
    from thema.ontology.universe import load_embedded
    from v04_score import (
        BANDS,
        BOOT_SEED,
        BOOTSTRAP,
        MARGIN,
        band_of,
        cells_with_ci,
        ci_of_difference,
        read_members,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--s2", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/S2_vs_O50s_2026-10-22"))
    args = parser.parse_args(argv)

    embedded = load_embedded(args.space_root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    position = {key: i for i, key in enumerate(keys)}
    raw = args.data / "raw"
    reactome = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines())
    sources = {
        "reactome": descendant_sets({c: set(p) for c, p in reactome.items()},
                                    position, "reactome:"),
        "go": descendant_sets(
            go_edges((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines(),
                     PRIMARY_RELATIONS), position, "go:"),
    }
    bands = [f"{lo}-{hi}" for lo, hi in BANDS]
    print("PROMPT 55 PART 2, SECTION E: CURATED RECALL AND PRECISION, J > 0.5, WITH CIs.")
    print(f"  v04_score's own estimator, bands, bootstrap ({BOOTSTRAP:,}) and seed ({BOOT_SEED});")
    print(f"  every curated set is used (the 'all' half); margin {MARGIN} is v04_score's")
    for source, sets in sources.items():
        print(f"  {source}: {len(sets):,} curated sets")
    print()

    scored: dict[str, dict] = {}
    for name, path in (("O50s", args.o50s), ("S2", args.s2)):
        build = read_members(path)
        row = {}
        for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
            own, t_bands = [], []
            for theme in build:
                members = {position[k] for k in theme if k.startswith(prefix)}
                if len(members) >= 3:
                    own.append(members)
                    t_bands.append(band_of(len(members)))
            sets = sources[source]
            row[source] = cells_with_ci(own, sets, [band_of(len(s)) for s in sets],
                                        t_bands, len(keys))
        scored[name] = row
        print(f"  scored {name}: {len(build):,} themes", flush=True)
    print()

    report: dict = {"bootstrap": BOOTSTRAP, "seed": BOOT_SEED, "margin": MARGIN, "cells": []}
    for field, boot_field in (("recall", "recall_boot"), ("precision", "precision_boot")):
        print("=" * 104)
        print(f"E. CURATED {field.upper()} PER BAND, J > 0.5")
        print("=" * 104)
        print(f"  {'source':<10}{'band':<10}{'n':>6}"
              f"{'O50s':>9}{'95% CI':>18}{'S2':>9}{'95% CI':>18}"
              f"{'S2-O50s':>10}{'CI of diff':>20}")
        for source in ("reactome", "go"):
            for band in bands:
                a = scored["O50s"][source][band]
                b = scored["S2"][source][band]
                if a[field] is None or b[field] is None:
                    continue
                a_lo, a_hi = np.nanpercentile(a[boot_field], [2.5, 97.5])
                b_lo, b_hi = np.nanpercentile(b[boot_field], [2.5, 97.5])
                delta = b[field] - a[field]
                d_lo, d_hi = ci_of_difference(b[boot_field], a[boot_field])
                excludes = np.isfinite(d_lo) and np.isfinite(d_hi) and (d_lo > 0 or d_hi < 0)
                n = a["n_curated"] if field == "recall" else a["n_themes"]
                print(f"  {source:<10}{band:<10}{n:>6,}"
                      f"{a[field]:>9.4f}{f'[{a_lo:.4f}, {a_hi:.4f}]':>18}"
                      f"{b[field]:>9.4f}{f'[{b_lo:.4f}, {b_hi:.4f}]':>18}"
                      f"{delta:>+10.4f}{f'[{d_lo:+.4f}, {d_hi:+.4f}]':>20}"
                      + ("  *" if excludes else ""))
                report["cells"].append({
                    "field": field, "source": source, "band": band, "n": int(n),
                    "O50s": a[field], "O50s_ci": [float(a_lo), float(a_hi)],
                    "S2": b[field], "S2_ci": [float(b_lo), float(b_hi)],
                    "delta": round(delta, 4), "delta_ci": [float(d_lo), float(d_hi)],
                    "ci_excludes_zero": bool(excludes)})
        print("  * = the CI of the difference excludes zero")
        print()
    (args.out / "section_e_recall_ci.json").write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'section_e_recall_ci.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
