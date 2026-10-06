#!/usr/bin/env python3
"""PREVIEW 2, REPORT ONLY: overall 4-cell specificity AUROC and reactome2go recovery/lift.

Three arms -- THEMA-Ward (A), THEMA-L (B) and HiDeF k15 maxres 25 as the declared reference.
Nothing here is a verdict: four of the engine arms do not exist yet, and the engine search's own
rule is the 16 BAND-RESTRICTED scores, not these.

Two measures, both already declared elsewhere and reused unchanged:

- **(a) the overall 4-cell specificity AUROC** -- Reactome and GO siblings x zero-gene and pooled,
  over ALL theme sizes, which is the 4 Oct HiDeF comparison's primary metric. Cluster bootstrap over
  curated parents, so pairs inside one sibling group are resampled together.
- **(b) reactome2go recovery and lift by gene-overlap band** -- test 3's measure. Recovery is the
  share of cross-source pairs sharing a theme; lift is recovery divided by the matched null's, so a
  lift of 1.0 means the arm does no better than chance at that overlap.

Usage::

    uv run scripts/preview_overall.py --arm A=v0.3/recurrent_dag_10770
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from granularity_bands import read_arm  # noqa: E402
from hidef_decision import (  # noqa: E402
    BOOTSTRAP,
    BOOTSTRAP_SEED,
    NULL_DRAWS,
    NULL_SEED,
    _parent_of,
    auroc_from_ranks,
)
from thema.data.formats import parse_obo_terms  # noqa: E402
from thema.data.hierarchy import read_reactome_relation  # noqa: E402
from thema.data.pathways import PathwayCollection  # noqa: E402
from thema.evaluation import (  # noqa: E402
    go_parents,
    jaccard,
    reactome2go_pairs,
    restrict,
    sibling_pairs,
)
from thema.ontology.universe import load_embedded  # noqa: E402

#: Gene-overlap bands for (b). The zero band is kept separate because a pair with no shared gene is
#: the only one where a shared theme cannot be explained by shared genes.
GENE_BANDS = ((0.0, 0.0), (0.0, 0.1), (0.1, 0.3), (0.3, 1.01))


def smallest_shared(
    homes: dict[str, frozenset[str]], sizes: dict[str, int], left: list[str], right: list[str]
) -> np.ndarray:
    """Smallest shared theme size per pair, over ALL theme sizes, inf when none.

    Args:
        homes: Pathway key to its themes.
        sizes: Theme to member count.
        left: First members.
        right: Second members.

    Returns:
        One value per pair.
    """
    out = np.full(len(left), float("inf"))
    empty: frozenset[str] = frozenset()
    for i, (a, b) in enumerate(zip(left, right, strict=True)):
        shared = homes.get(a, empty) & homes.get(b, empty)
        if shared:
            out[i] = float(min(sizes[t] for t in shared))
    return out


def main(argv: list[str] | None = None) -> int:
    """Run both previews.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--arm", action="append", default=[], help="NAME=path under data/ontology/")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    base = args.data / "ontology"
    root = base / f"v{args.version}"
    arms = {}
    for spec in args.arm:
        name, path = spec.split("=", 1)
        if (base / path / "members.tsv").is_file():
            arms[name] = read_arm(base / path)
        else:
            print(f"  {name}: not built ({base / path})", flush=True)
    if not arms:
        return 1
    print(f"PREVIEW 2  arms: {', '.join(arms)}  (REPORT ONLY, not the verdict)", flush=True)

    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    present = set(keys)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = {p.key: p for p in collection.pathways if p.key in present}

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
    null_spec = {n: smallest_shared(h, s, null_left, null_right)
                 for n, (h, s, _r) in arms.items()}

    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    terms = parse_obo_terms((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines())
    report: dict = {"preview": "overall 4-cell AUROC and reactome2go", "not_a_verdict": True,
                    "resamples": BOOTSTRAP, "seed": BOOTSTRAP_SEED, "cells": {}, "r2g": {}}

    # ---- (a) the overall four cells
    print("\n(a) OVERALL 4-CELL SPECIFICITY AUROC, all theme sizes, cluster bootstrap")
    for source_name, source, rel, prefix in (
        ("Reactome", sibling_pairs(relation, "reactome:", "r", ""), relation, "reactome:"),
        ("GO", sibling_pairs(go_parents(terms), "go:", "g", ""), go_parents(terms), "go:"),
    ):
        kept = restrict(source, present)
        left = [a for a, _ in kept.pairs]
        right = [b for _, b in kept.pairs]
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[a], by_key[b])) for a, b in zip(left, right, strict=True)])
        groups = _parent_of(rel, prefix, left, right)
        spec = {n: smallest_shared(h, s, left, right) for n, (h, s, _r) in arms.items()}
        for gene_band, mask, nmask in (
            ("zero-gene", gvals == 0.0, gene_null == 0.0),
            ("pooled", np.ones(len(left), dtype=bool), np.ones(len(ia), dtype=bool)),
        ):
            idx = np.flatnonzero(mask)
            ref = {n: np.sort(null_spec[n][nmask]) for n in arms}
            point = {n: auroc_from_ranks(spec[n][mask], ref[n]) for n in arms}
            buckets: dict[str, list[int]] = defaultdict(list)
            for i in idx.tolist():
                buckets[groups[i]].append(i)
            members = [np.array(v, dtype=np.int64) for v in buckets.values()]
            boot = {n: np.empty(BOOTSTRAP) for n in arms}
            bs = np.random.default_rng(BOOTSTRAP_SEED)
            for r in range(BOOTSTRAP):
                drawn = bs.integers(0, len(members), size=len(members))
                picked = np.concatenate([members[d] for d in drawn])
                for n in arms:
                    boot[n][r] = auroc_from_ranks(spec[n][picked], ref[n])
            cell = f"{source_name}|{gene_band}"
            print(f"\n  {source_name}, {gene_band} -- {len(idx):,} pairs, "
                  f"{len(members):,} curated parents")
            print(f"    {'arm':<8}{'AUROC':>8}   95% CI of (arm - A)")
            report["cells"][cell] = {"n": int(mask.sum()), "parents": len(members),
                                     "auroc": {}, "ci_vs_A": {}}
            for n in arms:
                line = f"    {n:<8}{point[n]:>8.4f}"
                report["cells"][cell]["auroc"][n] = round(point[n], 4)
                if "A" in arms and n != "A":
                    diff = boot[n] - boot["A"]
                    lo = float(np.percentile(diff, 2.5))
                    hi = float(np.percentile(diff, 97.5))
                    line += f"   {point[n] - point['A']:+.4f}  [{lo:+.4f}, {hi:+.4f}]"
                    report["cells"][cell]["ci_vs_A"][n] = [round(lo, 4), round(hi, 4)]
                print(line, flush=True)

    # ---- (b) reactome2go recovery and lift
    print("\n(b) REACTOME2GO: recovery and lift by gene-overlap band")
    r2g = restrict(
        reactome2go_pairs((raw / "reactome2go").read_text(encoding="utf-8").splitlines()),
        present,
    )
    left = [a for a, _ in r2g.pairs]
    right = [b for _, b in r2g.pairs]
    gvals = np.array([(lambda v: -1.0 if v is None else v)(
        jaccard(by_key[a], by_key[b])) for a, b in zip(left, right, strict=True)])
    shared = {n: np.isfinite(smallest_shared(h, s, left, right))
              for n, (h, s, _r) in arms.items()}
    null_shared = {n: np.isfinite(null_spec[n]) for n in arms}
    print(f"  {len(left):,} cross-source pairs")
    print(f"  {'band':<12}{'pairs':>8}" + "".join(f"{n + ' rec':>10}{n + ' lift':>10}"
                                                  for n in arms))
    for lo, hi in GENE_BANDS:
        mask = (gvals == 0.0) if hi == 0.0 else ((gvals > lo) & (gvals <= hi))
        nmask = (gene_null == 0.0) if hi == 0.0 else ((gene_null > lo) & (gene_null <= hi))
        if not mask.any():
            continue
        label = "zero" if hi == 0.0 else f"{lo:g}-{hi:g}"
        cells = ""
        report["r2g"][label] = {"pairs": int(mask.sum()), "arms": {}}
        for n in arms:
            rec = float(shared[n][mask].mean())
            nul = float(null_shared[n][nmask].mean()) if nmask.any() else 0.0
            lift = rec / nul if nul > 0 else float("inf")
            cells += f"{rec:>9.1%} {lift:>9.2f} "
            report["r2g"][label]["arms"][n] = {"recovery": round(rec, 4),
                                               "null": round(nul, 5),
                                               "lift": None if nul == 0 else round(lift, 2)}
        print(f"  {label:<12}{int(mask.sum()):>8,} {cells}", flush=True)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
