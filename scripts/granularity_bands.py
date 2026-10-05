#!/usr/bin/env python3
"""C3 and C4: compare arms at matched theme granularity, and test why GO favours HiDeF.

**Informational. Neither section can change the 4 Oct verdict**, which is defined only for the
declared configuration. Every CI here uses the **cluster bootstrap over curated parents**: pairs
inside one sibling group share pathways and are not independent, so a pair bootstrap understates the
uncertainty -- measured at roughly 7x too narrow on the four headline cells.

**C3, granularity-matched.** THEMA has 6,244 themes at median size 9; HiDeF k=15 has 472 at median
59. A comparison that lets each arm answer at its own grain is partly measuring grain. Restricting
the smallest-shared-theme search to themes INSIDE a size band asks both arms the same question: at
this grain, do you put curated siblings together?

**C4, three hypotheses for the GO gap, declared in the brief before any of this was looked at.**

- **H1 loose siblings** -- the advantage concentrates in pairs with large curated parents, high
  fan-out, or low pair cosine.
- **H2 thin middle** -- it comes from pairs HiDeF places in a 51-500 theme while THEMA's smallest
  shared theme is >500 or none.
- **H3 unplaced** -- it comes from pairs where at least one pathway is unplaced or root-only in
  THEMA.

Usage::

    uv run scripts/granularity_bands.py --mode c3
    uv run scripts/granularity_bands.py --mode c4
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from hidef_decision import (
    BOOTSTRAP,
    BOOTSTRAP_SEED,
    EQUIVALENCE_MARGIN,
    NULL_DRAWS,
    NULL_SEED,
    _parent_of,
    auroc_from_ranks,
)
from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.embed import centre_and_renormalise
from thema.evaluation import go_parents, jaccard, restrict, sibling_pairs
from thema.ontology.universe import load_embedded

csv.field_size_limit(1 << 30)

#: C3's theme size bands, declared in the brief.
SIZE_BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))

#: C4 H2's "middle" band, and the threshold above which THEMA's answer counts as too coarse.
MIDDLE = (51, 500)
TOO_COARSE = 500

#: C4 fan-out strata.
FANOUT_BANDS: tuple[tuple[str, int, int], ...] = (
    ("<=6", 0, 6), ("7-20", 7, 20), (">20", 21, 10**9),
)

ARMS = {
    "THEMA": "recurrent_dag_10770",
    "HiDeF m25": "hidef_10770_k15",
    "HiDeF m50": "hidef_10770_k15_maxres50",
}


def read_arm(directory: Path) -> tuple[dict[str, frozenset[str]], dict[str, int], set[str]]:
    """Homes, theme sizes, and the themes that have no parent (roots).

    Args:
        directory: A build directory in THEMA's schema.

    Returns:
        Pathway key to its themes, theme to size, and the set of root themes.
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    homes: dict[str, set[str]] = defaultdict(set)
    for node, keys in members.items():
        for key in keys:
            homes[key].add(node)
    roots = {n for n, ps in parents.items() if not ps}
    return ({k: frozenset(v) for k, v in homes.items()},
            {n: len(v) for n, v in members.items()}, roots)


def smallest_in_band(
    homes: dict[str, frozenset[str]], sizes: dict[str, int],
    left: list[str], right: list[str], low: int, high: int,
) -> np.ndarray:
    """Smallest shared theme whose size is within ``[low, high]``, else inf.

    Args:
        homes: Pathway key to its themes.
        sizes: Theme to member count.
        left: First members.
        right: Second members.
        low: Band floor.
        high: Band ceiling.

    Returns:
        One value per pair.
    """
    out = np.full(len(left), float("inf"))
    empty: frozenset[str] = frozenset()
    for i, (a, b) in enumerate(zip(left, right, strict=True)):
        best = float("inf")
        for theme in homes.get(a, empty) & homes.get(b, empty):
            size = sizes[theme]
            if low <= size <= high and size < best:
                best = float(size)
        out[i] = best
    return out


def cluster_ci(
    hidef: np.ndarray, thema: np.ndarray,
    ref_hidef: np.ndarray, ref_thema: np.ndarray,
    groups: list[str], index: np.ndarray,
) -> tuple[float, float, str]:
    """Cluster-bootstrap CI of (HiDeF - THEMA) AUROC, resampling curated parents.

    Args:
        hidef: HiDeF specificity per pair.
        thema: THEMA specificity per pair.
        ref_hidef: HiDeF's sorted null values.
        ref_thema: THEMA's sorted null values.
        groups: Curated parent label per pair.
        index: Which pairs are in this cell.

    Returns:
        Lower bound, upper bound, and the reading against the equivalence margin.
    """
    buckets: dict[str, list[int]] = defaultdict(list)
    for i in index:
        buckets[groups[i]].append(i)
    members = [np.array(v, dtype=np.int64) for v in buckets.values()]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    diffs = np.empty(BOOTSTRAP)
    for r in range(BOOTSTRAP):
        drawn = rng.integers(0, len(members), size=len(members))
        picked = np.concatenate([members[d] for d in drawn])
        diffs[r] = (auroc_from_ranks(hidef[picked], ref_hidef)
                    - auroc_from_ranks(thema[picked], ref_thema))
    low, high = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    if low >= -EQUIVALENCE_MARGIN and high <= EQUIVALENCE_MARGIN:
        reading = "equivalent"
    elif high < 0.0:
        reading = "THEMA better"
    elif low > 0.0:
        reading = "HiDeF better"
    else:
        reading = "inconclusive"
    return low, high, reading


def main(argv: list[str] | None = None) -> int:
    """Run C3 or C4.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("c3", "c4"), required=True)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--tsv", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    present = set(keys)
    position = {k: i for i, k in enumerate(keys)}
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = {p.key: p for p in collection.pathways if p.key in present}
    arms = {name: read_arm(root / d) for name, d in ARMS.items()
            if (root / d / "members.tsv").is_file()}
    print(f"{args.mode.upper()}  arms: {', '.join(arms)}")

    rng = np.random.default_rng(NULL_SEED)
    ia = rng.integers(0, len(keys), size=NULL_DRAWS)
    ib = rng.integers(0, len(keys), size=NULL_DRAWS)
    keep = ia != ib
    ia, ib = ia[keep], ib[keep]
    null_left = [keys[i] for i in ia]
    null_right = [keys[j] for j in ib]
    gene_null = np.array([
        (lambda v: -1.0 if v is None else v)(jaccard(by_key[a], by_key[b]))
        for a, b in zip(null_left, null_right, strict=True)
    ])
    zero_null = gene_null == 0.0

    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    terms = parse_obo_terms((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines())
    go_rel = go_parents(terms)
    sources = {
        "Reactome": (sibling_pairs(relation, "reactome:", "r", ""), relation, "reactome:"),
        "GO": (sibling_pairs(go_rel, "go:", "g", ""), go_rel, "go:"),
    }

    rows: list[tuple[str, ...]] = []
    report: dict = {"mode": args.mode, "bootstrap": "cluster over curated parents",
                    "resamples": BOOTSTRAP, "seed": BOOTSTRAP_SEED,
                    "equivalence_margin": EQUIVALENCE_MARGIN, "cells": []}

    for source_name, (source, relation_map, prefix) in sources.items():
        kept = restrict(source, present)
        left = [a for a, _ in kept.pairs]
        right = [b for _, b in kept.pairs]
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[a], by_key[b])) for a, b in zip(left, right, strict=True)])
        zero = gvals == 0.0
        groups = _parent_of(relation_map, prefix, left, right)
        print(f"\n{'=' * 100}\n{source_name} siblings: {len(left):,} pairs, "
              f"{int(zero.sum()):,} at zero gene overlap\n{'=' * 100}")

        if args.mode == "c3":
            for low, high in SIZE_BANDS:
                spec = {n: smallest_in_band(h, s, left, right, low, high)
                        for n, (h, s, _r) in arms.items()}
                nspec = {n: smallest_in_band(h, s, null_left, null_right, low, high)
                         for n, (h, s, _r) in arms.items()}
                for band_name, mask, nmask in (
                    ("zero-gene", zero, zero_null),
                    ("pooled", np.ones(len(left), dtype=bool), np.ones(len(ia), dtype=bool)),
                ):
                    idx = np.flatnonzero(mask)
                    ref = {n: np.sort(nspec[n][nmask]) for n in arms}
                    point = {n: auroc_from_ranks(spec[n][mask], ref[n]) for n in arms}
                    rec = {n: float(np.isfinite(spec[n][mask]).mean()) for n in arms}
                    print(f"\n  themes {low}-{high}, {band_name} -- {len(idx):,} pairs")
                    print(f"    {'arm':<12} {'AUROC':>7} {'recovery':>9}")
                    for n in arms:
                        print(f"    {n:<12} {point[n]:>7.4f} {rec[n]:>8.1%}")
                    cell = {"source": source_name, "size_band": f"{low}-{high}",
                            "gene_band": band_name, "n": int(mask.sum()),
                            "auroc": {n: round(point[n], 4) for n in arms},
                            "recovery": {n: round(rec[n], 4) for n in arms}, "ci": {}}
                    for n in arms:
                        if n == "THEMA":
                            continue
                        lo, hi, reading = cluster_ci(spec[n], spec["THEMA"], ref[n],
                                                     ref["THEMA"], groups, idx)
                        print(f"      {n} - THEMA  {point[n] - point['THEMA']:+.4f}  "
                              f"CI [{lo:+.4f}, {hi:+.4f}]  {reading.upper()}")
                        cell["ci"][n] = {"diff": round(point[n] - point["THEMA"], 4),
                                         "low": round(lo, 4), "high": round(hi, 4),
                                         "reading": reading}
                        rows.append((source_name, f"{low}-{high}", band_name, n,
                                     str(int(mask.sum())), f"{point[n]:.4f}",
                                     f"{point['THEMA']:.4f}", f"{lo:.4f}", f"{hi:.4f}", reading))
                    report["cells"].append(cell)
        else:
            report["cells"].append(_c4(source_name, arms, left, right, zero, groups,
                                       null_left, null_right, zero_null,
                                       relation_map, prefix, embedded, position))

    if args.tsv:
        args.tsv.parent.mkdir(parents=True, exist_ok=True)
        with args.tsv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["source", "size_band", "gene_band", "arm", "n", "auroc_arm",
                             "auroc_thema", "ci_low", "ci_high", "reading"])
            writer.writerows(rows)
        print(f"\n  -> {args.tsv}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


def _c4(
    source_name: str,
    arms: dict,
    left: list[str],
    right: list[str],
    zero: np.ndarray,
    groups: list[str],
    null_left: list[str],
    null_right: list[str],
    zero_null: np.ndarray,
    relation_map: dict,
    prefix: str,
    embedded: object,
    position: dict[str, int],
) -> dict:
    """C4: strata, hypothesis counts, and the decomposition. See the module docstring.

    Args:
        source_name: Which sibling source.
        arms: Arm name to ``(homes, sizes, roots)``.
        left: First members.
        right: Second members.
        zero: Mask of zero-gene-overlap pairs.
        groups: Curated parent label per pair.
        null_left: Null first members.
        null_right: Null second members.
        zero_null: Mask of zero-gene-overlap null pairs.
        relation_map: Child to parents in the curated hierarchy.
        prefix: Key prefix.
        embedded: The loaded universe, for the pair cosine.
        position: Pathway key to row.

    Returns:
        The stratum table, hypothesis counts and decomposition.
    """
    from hidef_decision import specificity

    spec = {n: specificity(h, s, left, right) for n, (h, s, _r) in arms.items()}
    nspec = {n: specificity(h, s, null_left, null_right) for n, (h, s, _r) in arms.items()}
    ref_zero = {n: np.sort(nspec[n][zero_null]) for n in arms}
    hidef = "HiDeF m25"
    base = (auroc_from_ranks(spec[hidef][zero], ref_zero[hidef])
            - auroc_from_ranks(spec["THEMA"][zero], ref_zero["THEMA"]))
    print(f"\n  BASELINE GAP at zero gene overlap: {hidef} - THEMA = {base:+.4f}")

    children: dict[str, set[str]] = defaultdict(set)
    for child, parents in relation_map.items():
        for parent in parents:
            children[parent].add(prefix + child)
    parent_size = np.array([len(children.get(g, ())) for g in groups], dtype=float)

    vectors, _mean = centre_and_renormalise(embedded.vectors)
    vectors = np.ascontiguousarray(vectors.astype(np.float32))
    cosine = np.array([float(vectors[position[a]] @ vectors[position[b]])
                       for a, b in zip(left, right, strict=True)])

    out: dict = {"source": source_name, "baseline_gap_zero_gene": round(base, 4), "strata": [],
                 "hypotheses": {}}

    def gap(mask: np.ndarray) -> tuple[float, int]:
        if not mask.any():
            return float("nan"), 0
        return (auroc_from_ranks(spec[hidef][mask], ref_zero[hidef])
                - auroc_from_ranks(spec["THEMA"][mask], ref_zero["THEMA"])), int(mask.sum())

    print("\n  (a) AUROC GAP PER STRATUM, zero gene overlap")
    quart = np.nanquantile(parent_size[zero], [0.25, 0.5, 0.75])
    for i, (lo, hi) in enumerate(zip([-1, *quart], [*quart, 1e18], strict=True)):
        mask = zero & (parent_size > lo) & (parent_size <= hi)
        g, n = gap(mask)
        print(f"    curated parent size Q{i + 1} ({lo:.0f}-{hi:.0f} children)  "
              f"n={n:>6,}  gap {g:+.4f}")
        out["strata"].append({"kind": "parent_size_quartile", "q": i + 1, "n": n,
                              "gap": None if np.isnan(g) else round(g, 4)})
    for label, lo, hi in FANOUT_BANDS:
        mask = zero & (parent_size >= lo) & (parent_size <= hi)
        g, n = gap(mask)
        print(f"    fan-out {label:<6}  n={n:>6,}  gap {g:+.4f}")
        out["strata"].append({"kind": "fanout", "band": label, "n": n,
                              "gap": None if np.isnan(g) else round(g, 4)})
    cq = np.nanquantile(cosine[zero], [0.25, 0.5, 0.75])
    for i, (lo, hi) in enumerate(zip([-2.0, *cq], [*cq, 2.0], strict=True)):
        mask = zero & (cosine > lo) & (cosine <= hi)
        g, n = gap(mask)
        print(f"    pair cosine Q{i + 1} ({lo:+.3f} to {hi:+.3f})  n={n:>6,}  gap {g:+.4f}")
        out["strata"].append({"kind": "cosine_quartile", "q": i + 1, "n": n,
                              "gap": None if np.isnan(g) else round(g, 4)})

    thema_homes, thema_sizes, thema_roots = arms["THEMA"]
    hidef_homes, hidef_sizes, _hr = arms[hidef]
    h2 = np.zeros(len(left), dtype=bool)
    h3 = np.zeros(len(left), dtype=bool)
    for i, (a, b) in enumerate(zip(left, right, strict=True)):
        shared_hidef = hidef_homes.get(a, frozenset()) & hidef_homes.get(b, frozenset())
        hs = [hidef_sizes[t] for t in shared_hidef]
        mid = any(MIDDLE[0] <= v <= MIDDLE[1] for v in hs)
        h2[i] = mid and (np.isinf(spec["THEMA"][i]) or spec["THEMA"][i] > TOO_COARSE)
        for key in (a, b):
            homes = thema_homes.get(key, frozenset())
            if not homes or homes <= thema_roots:
                h3[i] = True
    print(f"\n  (b) HYPOTHESIS COUNTS at zero gene overlap ({int(zero.sum()):,} pairs)")
    for name, mask in (("H2 thin middle", h2), ("H3 unplaced/root-only", h3)):
        both = zero & mask
        g_rest, n_rest = gap(zero & ~mask)
        print(f"    {name:<24} {int(both.sum()):>6,} pairs  "
              f"gap with them REMOVED {g_rest:+.4f} (n={n_rest:,})")
        out["hypotheses"][name] = {
            "pairs": int(both.sum()),
            "gap_without": None if np.isnan(g_rest) else round(g_rest, 4),
            "share_of_gap_explained": None if np.isnan(g_rest) or base == 0
            else round(1.0 - g_rest / base, 4),
        }
    overlap = int((zero & h2 & h3).sum())
    print(f"    H2 and H3 OVERLAP: {overlap:,} pairs -- the shares below are not additive")
    out["hypotheses"]["h2_h3_overlap"] = overlap
    return out


if __name__ == "__main__":
    raise SystemExit(main())
