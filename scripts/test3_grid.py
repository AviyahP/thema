#!/usr/bin/env python3
"""Test 3 and test 4 recovery on a gene-overlap x lexical-overlap grid. REPORTING ONLY.

**Nothing here is a test, a verdict, or a declared quantity.** The validation plan declares the
gene-overlap bands and one named cell ("gene overlap is 0 AND lexical overlap is near 0"); it
declares no lexical bands. The lexical bands below are therefore a **reporting choice**, stated as
one, and the sections marked EXPLORATORY widen the plan's cell to counts large enough to read --
which makes them not the plan's cell and not evidence for its gate.

What this exists for: the plan's headline cell holds 8 pairs on the frozen 10,770, and 8 pairs
cannot carry a gate. This shows where the pairs actually are, so the shortage is visible rather than
asserted, and puts the same comparison on the much larger sibling pair set.

A baseline whose largest cluster holds more than **29%** of the universe is flagged DEGENERATE: a
coarse partition buys recovery with an equally high chance rate, and comparing raw recovery against
it is how a collapsed blob "wins" a gate.

Usage::

    uv run scripts/test3_grid.py data/ontology/v0.3/recurrent_dag_10770
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
from scipy import sparse

from compare_baselines import (
    CUTS,
    SIBLING_FANOUT,
    cluster,
    condensed,
    gene_matrix,
    largest_share,
    similarities,
)
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.embed import centre_and_renormalise
from thema.evaluation import (
    BANDS,
    GENE_MEASURES,
    band_label,
    band_of,
    jaccard,
    reactome2go_pairs,
    restrict,
    sibling_pairs,
)
from thema.ontology.universe import load_embedded

csv.field_size_limit(1 << 30)

#: Random pairs for the doubly-matched null, and the seed. The null must be matched on BOTH axes,
#: so it needs enough draws that the sparse corners of the grid still fill.
NULL_DRAWS = 600_000
NULL_SEED = 20261003

#: Lexical band edges, as QUANTILES of curated-text Jaccard over the null draws -- a
#: universe-representative distribution, so the same edges apply to every source and to the null and
#: the bands are comparable across them. A REPORTING CHOICE; the plan declares no lexical bands.
LEXICAL_QUANTILES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

#: A baseline this collapsed is not a baseline. Set at the size cap's own share of the universe.
DEGENERATE_SHARE = 0.29

#: Below this many pairs a cell's percentage is not quoted.
QUOTABLE = 20

WORD = re.compile(r"[a-z][a-z0-9-]{2,}")


def tokens_of(collection: PathwayCollection, keys: list[str]) -> dict[str, frozenset[str]]:
    """Word sets of each pathway's CURATED prose, not the generated prose.

    The plan is explicit: band by "lexical overlap between the two CURATED texts (not the generated
    ones)", because the generated descriptions were written by a model that has read both Reactome
    and GO, so their wording cannot separate memorised phrasing from inferred biology.

    Args:
        collection: The pathway collection.
        keys: The universe's keys.

    Returns:
        Key to its curated-text word set; absent where the source publishes no prose.
    """
    present = set(keys)
    out = {}
    for pathway in collection.pathways:
        if pathway.key not in present:
            continue
        text = pathway.description_source or ""
        words = frozenset(WORD.findall(text.lower()))
        if words:
            out[pathway.key] = words
    return out


def lexical_of(a: str, b: str, tokens: dict[str, frozenset[str]]) -> float | None:
    """Curated-text Jaccard, or None when either side publishes no prose.

    Args:
        a: One key.
        b: The other.
        tokens: Key to word set.

    Returns:
        The Jaccard, or None.
    """
    left, right = tokens.get(a), tokens.get(b)
    if not left or not right:
        return None
    return len(left & right) / len(left | right)


def membership(directory: Path, index: dict[str, int]) -> sparse.csr_matrix:
    """A (pathways x themes) binary matrix, so co-membership is one sparse product.

    Args:
        directory: A build directory.
        index: Pathway key to row.

    Returns:
        The membership matrix.
    """
    themes: dict[str, int] = {}
    rows, cols = [], []
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["key"] not in index:
                continue
            theme = themes.setdefault(row["node"], len(themes))
            rows.append(index[row["key"]])
            cols.append(theme)
    return sparse.csr_matrix(
        (np.ones(len(rows), dtype=bool), (rows, cols)),
        shape=(len(index), max(len(themes), 1)),
    )


def dag_recovered(matrix: sparse.csr_matrix, left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Whether each pair shares at least one theme, in chunks.

    Args:
        matrix: Membership matrix.
        left: Row indices.
        right: Row indices.

    Returns:
        Boolean per pair.
    """
    out = np.zeros(len(left), dtype=bool)
    step = 200_000
    for begin in range(0, len(left), step):
        a = matrix[left[begin:begin + step]]
        b = matrix[right[begin:begin + step]]
        out[begin:begin + step] = np.asarray(
            a.multiply(b).sum(axis=1), dtype=np.int64
        ).ravel() > 0
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the grids.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--tfidf-build", type=Path,
                        default=Path("data/ontology/v0.3/recurrent_dag_10770_tfidf"))
    parser.add_argument("--tfidf-vectors", type=Path,
                        default=Path("data/ontology/v0.3/tfidf_vectors.npy"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--tsv", type=Path, default=None,
                        help="every cell x arm number, which the printed tables summarise")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    index = {k: i for i, k in enumerate(keys)}
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = {p.key: p for p in collection.pathways if p.key in index}
    tokens = tokens_of(collection, keys)
    print("TEST 3 / TEST 4 GRID -- REPORTING ONLY, no verdicts")
    print(f"  universe {len(keys):,}; {len(tokens):,} have curated prose "
          f"({len(tokens) / len(keys):.0%}), the rest publish none")

    # ---- arms ----
    arms: dict[str, object] = {"THEMA (frozen)": membership(args.build, index)}
    degenerate: dict[str, float] = {}
    if args.tfidf_build.is_file() or (args.tfidf_build / "members.tsv").is_file():
        arms["TF-IDF DAG"] = membership(args.tfidf_build, index)
    if args.tfidf_vectors.is_file():
        vectors, _mean = centre_and_renormalise(np.load(args.tfidf_vectors))
        vectors = np.ascontiguousarray(vectors.astype(np.float32))
        labels = cluster(condensed(1.0 - (vectors @ vectors.T)), "ward", cuts=CUTS)
        for k in CUTS:
            arms[f"TF-IDF flat@{k}"] = labels[k]
            degenerate[f"TF-IDF flat@{k}"] = largest_share(labels[k])
        del vectors, labels
    matrix, span = gene_matrix([by_key[k] for k in keys])
    sims = similarities(matrix, span)
    for measure in GENE_MEASURES:
        linkage = "ward" if measure in ("jaccard", "ochiai") else "average"
        square = (np.sqrt(np.maximum(1.0 - sims[measure], 0.0)) if measure == "jaccard"
                  else 1.0 - sims[measure])
        labels = cluster(condensed(square), linkage, cuts=CUTS)
        for k in CUTS:
            arms[f"{measure}@{k}"] = labels[k]
            degenerate[f"{measure}@{k}"] = largest_share(labels[k])
        del square, labels
    del sims, matrix
    print(f"  arms: {len(arms)} "
          f"({sum(1 for v in degenerate.values() if v > DEGENERATE_SHARE)} flagged degenerate "
          f"at >{DEGENERATE_SHARE:.0%} of the universe in one cluster)")
    for name, share in sorted(degenerate.items(), key=lambda kv: -kv[1]):
        if share > DEGENERATE_SHARE:
            print(f"    DEGENERATE  {name:<16} largest cluster {share:.1%}")

    # ---- the doubly-matched null ----
    rng = np.random.default_rng(NULL_SEED)
    a = rng.integers(0, len(keys), size=NULL_DRAWS)
    b = rng.integers(0, len(keys), size=NULL_DRAWS)
    keep = a != b
    a, b = a[keep], b[keep]
    # NOT `jaccard(...) or -1.0`: a gene Jaccard of exactly 0.0 is FALSY, so that idiom recorded
    # every zero-overlap pair as undefined and emptied the `exactly 0` null band -- the single most
    # important cell in this grid. Only None means undefined.
    gene_null = np.array([
        (lambda v: -1.0 if v is None else v)(jaccard(by_key[keys[i]], by_key[keys[j]]))
        for i, j in zip(a, b, strict=True)
    ])
    lex_null = np.array([(lambda v: -1.0 if v is None else v)(
        lexical_of(keys[i], keys[j], tokens)) for i, j in zip(a, b, strict=True)])
    have_lex = lex_null >= 0
    edges = [float(np.quantile(lex_null[have_lex], q)) for q in LEXICAL_QUANTILES]
    edges[0], edges[-1] = -1e-9, 1.0 + 1e-9
    lex_labels = [f"L{i + 1} {edges[i]:.3f}-{edges[i + 1]:.3f}" for i in range(len(edges) - 1)]
    print(f"  null: {len(a):,} random pairs, seed {NULL_SEED}; "
          f"{int(have_lex.sum()):,} have two curated texts")
    print(f"  lexical bands, quantiles {LEXICAL_QUANTILES} of the null's curated-text Jaccard "
          f"(A REPORTING CHOICE):")
    for label in lex_labels:
        print(f"    {label}")
    print("    L0 = one or both sides publish no curated prose")

    def lex_band(values: np.ndarray) -> np.ndarray:
        out = np.zeros(len(values), dtype=np.int64)
        for i in range(len(edges) - 1):
            out[(values > edges[i]) & (values <= edges[i + 1])] = i + 1
        out[values < 0] = 0
        return out

    def gene_band(values: np.ndarray) -> list[tuple[float, float]]:
        return [band_of(v) if v >= 0 else None for v in values]

    null_lex = lex_band(lex_null)
    null_gene = gene_band(gene_null)
    arm_null: dict[str, np.ndarray] = {}
    for name, arm in arms.items():
        arm_null[name] = (dag_recovered(arm, a, b) if sparse.issparse(arm)
                          else (np.asarray(arm)[a] == np.asarray(arm)[b]))

    # ---- sources ----
    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    sources = [
        reactome2go_pairs((raw / "reactome2go").read_text(encoding="utf-8").splitlines()),
        sibling_pairs(relation, "reactome:", "reactome-siblings", "same-curator hierarchy"),
        sibling_pairs(relation, "reactome:", f"reactome-siblings (fan-out<={SIBLING_FANOUT})",
                      "broad parents dropped", max_children=SIBLING_FANOUT),
    ]

    rows_out: list[tuple[str, ...]] = []
    report: dict = {"lexical_band_edges": edges, "lexical_bands_are_a_reporting_choice": True,
                    "degenerate_share_flag": DEGENERATE_SHARE,
                    "largest_cluster_share": {k: round(v, 4) for k, v in degenerate.items()},
                    "null_draws": int(len(a)), "null_seed": NULL_SEED, "sources": {}}

    for source in sources:
        kept = restrict(source, set(index))
        pa = np.array([index[x] for x, _ in kept.pairs], dtype=np.int64)
        pb = np.array([index[y] for _, y in kept.pairs], dtype=np.int64)
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[keys[i]], by_key[keys[j]])) for i, j in zip(pa, pb, strict=True)])
        lvals = np.array([(lambda v: -1.0 if v is None else v)(
            lexical_of(keys[i], keys[j], tokens)) for i, j in zip(pa, pb, strict=True)])
        gb = gene_band(gvals)
        lb = lex_band(lvals)
        rec = {name: (dag_recovered(arm, pa, pb) if sparse.issparse(arm)
                      else (np.asarray(arm)[pa] == np.asarray(arm)[pb]))
               for name, arm in arms.items()}

        print(f"\n{'=' * 100}\n{kept.name}  ({kept.strength}) -- {len(kept.pairs):,} pairs in the "
              f"universe\n{'=' * 100}")
        undefined = int((gvals < 0).sum())
        if undefined:
            print(f"  {undefined} pair(s) dropped from the grid: a member resolved to no genes")
        print("  THE COUNT, by gene-overlap band and lexical band")
        names = ["L0", *lex_labels]
        header = (f"    {'gene band':<16} "
                  + " ".join(f"{name.split()[0]:>7}" for name in names)
                  + f" {'total':>8}")
        print(header)
        for band in reversed(BANDS):
            mask = np.array([x == band for x in gb])
            if not mask.any():
                continue
            cells = [int((mask & (lb == i)).sum()) for i in range(len(lex_labels) + 1)]
            print(f"    {band_label(*band):<16} " + " ".join(f"{c:>7,}" for c in cells)
                  + f" {int(mask.sum()):>8,}")
        print(f"    {'TOTAL':<16} "
              + " ".join(f"{int((lb == i).sum()):>7,}" for i in range(len(lex_labels) + 1))
              + f" {len(kept.pairs):>8,}")

        entry: dict = {"pairs": len(kept.pairs), "undefined_gene": undefined, "cells": []}
        for band in reversed(BANDS):
            gmask = np.array([x == band for x in gb])
            if not gmask.any():
                continue
            for i in range(len(lex_labels) + 1):
                cell = gmask & (lb == i)
                n = int(cell.sum())
                if not n:
                    continue
                nulls = np.array([x == band for x in null_gene]) & (null_lex == i)
                label = (["L0 no curated prose", *lex_labels])[i]
                row = {"gene_band": band_label(*band), "lexical_band": label, "n": n,
                       "n_null": int(nulls.sum()), "arms": {}}
                for name in arms:
                    r = float(rec[name][cell].mean())
                    c = float(arm_null[name][nulls].mean()) if nulls.any() else float("nan")
                    row["arms"][name] = {
                        "recovery": round(r, 4),
                        "chance": None if np.isnan(c) else round(c, 4),
                        "lift": None if (np.isnan(c) or c == 0) else round(r / c, 3),
                        "degenerate": degenerate.get(name, 0.0) > DEGENERATE_SHARE,
                    }
                    rows_out.append((
                        kept.name, band_label(*band), label, str(n), str(int(nulls.sum())), name,
                        f"{r:.4f}", "" if np.isnan(c) else f"{c:.4f}",
                        "" if (np.isnan(c) or c == 0) else f"{r / c:.3f}",
                        "yes" if degenerate.get(name, 0.0) > DEGENERATE_SHARE else "no",
                    ))
                entry["cells"].append(row)
        report["sources"][kept.name] = entry

        print(f"\n  RECOVERY AND LIFT, per cell. Baselines flagged * are DEGENERATE "
              f"(>{DEGENERATE_SHARE:.0%} in one cluster).")
        keyarms = ["THEMA (frozen)"] + [k for k in arms if k.startswith("TF-IDF")]
        print(f"    {'cell':<34} {'n':>6} " + " ".join(f"{k[:14]:>15}" for k in keyarms)
              + f" {'best non-degen gene':>22}")
        for row in entry["cells"]:
            if row["n"] < QUOTABLE:
                continue
            good = {k: v for k, v in row["arms"].items()
                    if not v["degenerate"] and not k.startswith(("THEMA", "TF-IDF"))}
            best = max(good, key=lambda k: good[k]["recovery"]) if good else None
            cells = " ".join(
                f"{row['arms'][k]['recovery']:>7.1%}/"
                f"{(str(row['arms'][k]['lift']) + 'x') if row['arms'][k]['lift'] else '-':>6}"
                for k in keyarms
            )
            tail = (f"{best[:12]} {good[best]['recovery']:.1%}/"
                    f"{good[best]['lift']}x" if best else "none")
            print(f"    {row['gene_band'] + ' | ' + row['lexical_band'][:14]:<34} "
                  f"{row['n']:>6,} {cells} {tail:>22}")

    # ---- EXPLORATORY ----
    print(f"\n{'=' * 100}")
    print("EXPLORATORY -- the plan's hard cell WIDENED. Not a test, not a verdict.")
    print("=" * 100)
    median_lex = float(np.quantile(lex_null[have_lex], 0.5))
    print(f"  cell: gene Jaccard <= 0.05 AND curated-text Jaccard <= {median_lex:.3f} "
          f"(the null's median, i.e. the bottom 50%)")
    print("  This is NOT the plan's cell, which is gene overlap exactly 0 and lexical near 0.")
    explore: dict = {"gene_max": 0.05, "lexical_max": round(median_lex, 4), "sources": {}}
    for source in sources:
        kept = restrict(source, set(index))
        pa = np.array([index[x] for x, _ in kept.pairs], dtype=np.int64)
        pb = np.array([index[y] for _, y in kept.pairs], dtype=np.int64)
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[keys[i]], by_key[keys[j]])) for i, j in zip(pa, pb, strict=True)])
        lvals = np.array([(lambda v: -1.0 if v is None else v)(
            lexical_of(keys[i], keys[j], tokens)) for i, j in zip(pa, pb, strict=True)])
        cell = (gvals >= 0) & (gvals <= 0.05) & (lvals >= 0) & (lvals <= median_lex)
        nulls = (gene_null >= 0) & (gene_null <= 0.05) & (lex_null >= 0) & (lex_null <= median_lex)
        print(f"\n  {kept.name}: {int(cell.sum()):,} pairs in the widened cell "
              f"(null {int(nulls.sum()):,})")
        if not cell.any():
            continue
        print(f"    {'arm':<18} {'recovery':>9} {'chance':>8} {'lift':>7}  flag")
        got = {}
        for name, arm in arms.items():
            r = float((dag_recovered(arm, pa[cell], pb[cell]) if sparse.issparse(arm)
                       else (np.asarray(arm)[pa[cell]] == np.asarray(arm)[pb[cell]])).mean())
            c = float(arm_null[name][nulls].mean()) if nulls.any() else float("nan")
            flag = "DEGENERATE" if degenerate.get(name, 0.0) > DEGENERATE_SHARE else ""
            print(f"    {name:<18} {r:>8.1%} {c:>7.1%} "
                  f"{(r / c if c else float('inf')):>6.1f}x  {flag}")
            got[name] = {
                "recovery": round(r, 4),
                "chance": None if np.isnan(c) else round(c, 4),
                "lift": round(r / c, 3) if c else None,
                "degenerate": degenerate.get(name, 0.0) > DEGENERATE_SHARE,
            }
        explore["sources"][kept.name] = {"n": int(cell.sum()), "n_null": int(nulls.sum()),
                                         "arms": got}
    report["exploratory_widened_cell"] = explore

    if args.tsv:
        args.tsv.parent.mkdir(parents=True, exist_ok=True)
        with args.tsv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["source", "gene_band", "lexical_band", "n_pairs", "n_null", "arm",
                             "recovery", "chance", "lift", "degenerate"])
            writer.writerows(rows_out)
        print(f"\n  every cell x arm -> {args.tsv}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
