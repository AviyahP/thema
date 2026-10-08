#!/usr/bin/env python3
"""v0.4 scoring: the deciding table with clarification 9, CIs, and clarification 10's pairs.

The bootstrap resamples CURATED SETS, as §0 declares, and both measures are recomputed on the
resample rather than only recall. That matters and is cheap once set up: a theme's precision depends
on which curated sets are in the pool, so resampling sets moves precision too. Precomputing the
theme-by-set match matrix once makes each resample a sparse mat-vec.

- **recall** under a resample = the share of drawn curated sets that some theme matches at J > 0.5.
- **precision** under a resample = the share of themes matching at least one DRAWN set at J > 0.5.

Usage::

    uv run scripts/v04_score.py --half tuning --arm baseline=ablate/baseline ...
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse

sys.path.insert(0, str(Path(__file__).parent))

BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200))
MATCH = 0.5
BOOTSTRAP = 1000
BOOT_SEED = 0
MARGIN = 0.02


def band_of(size: int) -> str:
    """Band label, or None-like for out of range.

    Args:
        size: Member count.

    Returns:
        The label, or ``"other"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "other"


def match_matrix(themes: list[set[int]], sets: list[set[int]], n: int) -> sparse.csr_matrix:
    """Themes by curated sets, 1 where the Jaccard exceeds the match threshold.

    Built from an inverted index so only pairs sharing a member are ever compared.

    Args:
        themes: Theme member index sets.
        sets: Curated sets.
        n: Universe size.

    Returns:
        A ``(themes, sets)`` sparse 0/1 matrix.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(sets):
        for member in members:
            holders[member].append(index)
    rows, cols = [], []
    for position, members in enumerate(themes):
        for candidate in {c for m in members for c in holders[m]}:
            other = sets[candidate]
            inter = len(members & other)
            if inter and inter / (len(members) + len(other) - inter) > MATCH:
                rows.append(position)
                cols.append(candidate)
    return sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, cols)),
        shape=(max(len(themes), 1), max(len(sets), 1)))


def cells_with_ci(
    themes: list[set[int]], sets: list[set[int]], set_bands: list[str],
    theme_bands: list[str], n: int,
) -> dict:
    """Per-band recall and precision with a curated-set cluster bootstrap.

    Args:
        themes: Theme member index sets, source-restricted.
        sets: Curated sets for that source, already restricted to a half.
        set_bands: Band per curated set.
        theme_bands: Band per theme.
        n: Universe size.

    Returns:
        Per band, point estimates, bootstrap draws and the denominators.
    """
    matrix = match_matrix(themes, sets, n)
    set_hit = np.asarray(matrix.sum(axis=0)).ravel() > 0
    rng = np.random.default_rng(BOOT_SEED)
    out: dict[str, dict] = {}
    bands = [f"{lo}-{hi}" for lo, hi in BANDS]
    draws = [rng.integers(0, max(len(sets), 1), size=max(len(sets), 1))
             for _ in range(BOOTSTRAP)]
    for band in bands:
        s_idx = np.array([i for i, b in enumerate(set_bands) if b == band], dtype=np.int64)
        t_idx = np.array([i for i, b in enumerate(theme_bands) if b == band], dtype=np.int64)
        recall = float(set_hit[s_idx].mean()) if len(s_idx) else None
        precision = (float((np.asarray(matrix[t_idx].sum(axis=1)).ravel() > 0).mean())
                     if len(t_idx) else None)
        r_boot, p_boot = [], []
        for drawn in draws:
            if len(s_idx):
                keep = drawn[np.isin(drawn, s_idx)]
                r_boot.append(float(set_hit[keep].mean()) if len(keep) else np.nan)
            if len(t_idx):
                mult = np.bincount(drawn, minlength=matrix.shape[1])
                hit = np.asarray(matrix[t_idx] @ mult).ravel() > 0
                p_boot.append(float(hit.mean()))
        out[band] = {
            "recall": None if recall is None else round(recall, 4),
            "precision": None if precision is None else round(precision, 4),
            "n_curated": int(len(s_idx)), "n_themes": int(len(t_idx)),
            "recall_boot": r_boot, "precision_boot": p_boot,
        }
    return out


def read_members(path: Path) -> list[list[str]]:
    """Theme member key lists from an exported build.

    Args:
        path: A build directory.

    Returns:
        One key list per theme.
    """
    grouped: dict[str, list[str]] = defaultdict(list)
    with (path / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            grouped[row["node"]].append(row["key"])
    return list(grouped.values())


def ci_of_difference(a: list[float], b: list[float]) -> tuple[float, float]:
    """95% interval of (a - b) over paired bootstrap draws.

    Args:
        a: One arm's draws.
        b: The other's.

    Returns:
        Lower and upper bounds.
    """
    if not a or not b or len(a) != len(b):
        return (float("nan"), float("nan"))
    diff = np.array(a) - np.array(b)
    diff = diff[np.isfinite(diff)]
    if not len(diff):
        return (float("nan"), float("nan"))
    return (float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5)))


def main(argv: list[str] | None = None) -> int:
    """Score the given arms on one half of the curated sets.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from thema.data.hierarchy import read_reactome_relation
    from thema.ontology.evalsets import (
        PRIMARY_RELATIONS,
        SECONDARY_RELATIONS,
        descendant_sets,
        go_edges,
        split_half,
    )
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--half", choices=("tuning", "test", "all"), default="tuning")
    parser.add_argument("--relations", choices=("primary", "secondary"), default="primary")
    parser.add_argument("--arm", action="append", default=[],
                        help="NAME=path under data/ontology/")
    parser.add_argument("--reference", default="baseline")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    base = args.data / "ontology"
    root = base / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    position = {key: i for i, key in enumerate(keys)}
    relations = PRIMARY_RELATIONS if args.relations == "primary" else SECONDARY_RELATIONS

    sources: dict[str, list[set[int]]] = {}
    reactome = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text(
            encoding="utf-8").splitlines())
    sources["reactome"] = descendant_sets(
        {c: set(p) for c, p in reactome.items()}, position, "reactome:")
    sources["go"] = descendant_sets(
        go_edges((args.data / "raw" / "go-basic.obo").read_text(encoding="utf-8").splitlines(),
                 relations), position, "go:")

    print(f"v0.4 SCORING  half={args.half}, GO relations={args.relations}")
    chosen: dict[str, tuple[list[set[int]], list[str]]] = {}
    for source, sets in sources.items():
        bands = [band_of(len(s)) for s in sets]
        tuning, test = split_half(sets, bands, seed=0)
        pick = {"tuning": tuning, "test": test,
                "all": list(range(len(sets)))}[args.half]
        chosen[source] = ([sets[i] for i in pick], [bands[i] for i in pick])
        counts = {b: sum(1 for i in pick if bands[i] == b)
                  for b in [f"{lo}-{hi}" for lo, hi in BANDS]}
        print(f"  {source}: {len(sets):,} sets, {len(pick):,} in the {args.half} half  {counts}")

    report: dict = {"half": args.half, "relations": args.relations,
                    "bootstrap": BOOTSTRAP, "seed": BOOT_SEED, "margin": MARGIN, "arms": {}}
    for spec in args.arm:
        name, path = spec.split("=", 1)
        full = base / path
        if not (full / "members.tsv").is_file():
            print(f"  {name}: not built ({full})")
            continue
        build = read_members(full)
        row: dict = {"themes": len(build), "path": path}
        for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
            own, t_bands = [], []
            for theme in build:
                members = {position[k] for k in theme if k.startswith(prefix)}
                if len(members) >= 3:
                    own.append(members)
                    t_bands.append(band_of(len(members)))
            sets, s_bands = chosen[source]
            row[source] = cells_with_ci(own, sets, s_bands, t_bands, n)
        report["arms"][name] = row
        print(f"  scored {name:<22} themes {len(build):>6,}", flush=True)

    ref = report["arms"].get(args.reference)
    bands = [f"{lo}-{hi}" for lo, hi in BANDS]
    if ref is not None:
        print(f"\n  effect of each arm against {args.reference}, margin {MARGIN}")
        header = f"    {'arm':<22}{'themes':>7}"
        for source in ("reactome", "go"):
            for band in bands:
                header += f"{source[:2]}|{band:>8}"
        print(header)
        for name, row in report["arms"].items():
            if name == args.reference:
                continue
            cells = ""
            worsened = []
            for source in ("reactome", "go"):
                for band in bands:
                    g, h = row[source][band], ref[source][band]
                    marks = []
                    for field, boot in (("recall", "recall_boot"),
                                        ("precision", "precision_boot")):
                        if g[field] is None or h[field] is None:
                            continue
                        delta = g[field] - h[field]
                        lo, hi = ci_of_difference(g[boot], h[boot])
                        if delta < -MARGIN and np.isfinite(hi) and hi < 0:
                            marks.append(f"{field[0].upper()}{delta:+.3f}")
                            worsened.append(f"{source} {band} {field} {delta:+.4f}")
                    cells += f"{(','.join(marks) or '.'):>11}"
            row["worsened_beyond_margin"] = worsened
            print(f"    {name:<22}{row['themes']:>7,}{cells}")
        print("\n    a cell shows R or P with the delta only where the arm is WORSE than")
        print("    the reference beyond the margin AND the paired CI excludes zero")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        def strip(value: object, key: str) -> object:
            """Drop the bootstrap draws so the JSON stays small.

            Args:
                value: The field value.
                key: Its key.

            Returns:
                The value, with draws removed for a source block.
            """
            if key not in ("reactome", "go"):
                return value
            return {b: {x: y for x, y in value[b].items() if not x.endswith("_boot")}
                    for b in bands}

        slim = {**report, "arms": {
            name: {k: strip(v, k) for k, v in row.items()}
            for name, row in report["arms"].items()}}
        args.out.write_text(json.dumps(slim, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
