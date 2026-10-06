#!/usr/bin/env python3
"""Gate G4: do an arm's themes hold genes that interact more than chance? STRING v12.

Declared by amendment 2 of the engine brief, before any arm was built. For each final theme, the PPI
edge density inside its gene union is compared against 100 size-matched random gene sets drawn from
STRING-covered genes, and the arm's statistic is the fraction of themes with empirical p < 0.01.
An arm passes if that fraction is no more than 5 points below THEMA-Ward's.

Why this gate earns its place: every other gate and score is computed from the same embeddings the
engines cluster, so an engine that exploits a quirk of the embedding could pass all of them. STRING
is **independent evidence** -- curated and experimental protein interactions, nothing to do with
pathway descriptions or their vectors.

Two choices worth stating, both made before any arm was scored:

- **Edges at combined score >= 700** ("high confidence"), the threshold the declaration names.
- **The null draws from STRING-COVERED genes only.** Drawing from all pathway genes would compare a
  theme against sets containing genes STRING has never seen, which have no edges by construction,
  and every theme would look enriched.

Usage::

    uv run scripts/string_coherence.py --arm A=recurrent_dag_10770 --arm B=v0.3x_engines/leiden
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse

sys.path.insert(0, str(Path(__file__).parent))

#: Edge confidence floor, and the null's shape. Declared, not tuned.
MIN_SCORE = 700
NULL_SETS = 100
NULL_SEED = 0
ALPHA = 0.01

#: Bands the statistic is reported per, matching the scores.
BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))

#: Gate: an arm may fall at most this far below THEMA-Ward's fraction.
GATE_POINTS = 0.05


def load_string(raw: Path) -> tuple[dict[str, set[str]], list[str]]:
    """STRING's high-confidence human network, keyed by gene symbol.

    Args:
        raw: The ``data/raw`` directory.

    Returns:
        Symbol to its neighbour symbols, and the sorted list of covered symbols.
    """
    alias_path = raw / "9606.protein.aliases.v12.0.txt.gz"
    symbol_of: dict[str, str] = {}
    with gzip.open(alias_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            protein, alias, source = parts[0], parts[1], parts[2]
            # One protein carries many aliases. Prefer the HGNC symbol, which is the namespace the
            # pathway gene sets are already resolved into; fall back to Ensembl's display name.
            if source == "Ensembl_HGNC_symbol" or (
                protein not in symbol_of and source == "Ensembl_gene_display_name"
            ):
                symbol_of[protein] = alias
    neighbours: dict[str, set[str]] = defaultdict(set)
    with gzip.open(raw / "9606.protein.links.v12.0.txt.gz", "rt", encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            left, right, score = line.split()
            if int(score) < MIN_SCORE:
                continue
            a, b = symbol_of.get(left), symbol_of.get(right)
            if a is None or b is None or a == b:
                continue
            neighbours[a].add(b)
            neighbours[b].add(a)
    return dict(neighbours), sorted(neighbours)


def theme_genes(directory: Path, genes: dict[str, frozenset[str]]) -> dict[str, set[str]]:
    """Each theme's gene union.

    Args:
        directory: A build directory.
        genes: Pathway key to its gene symbols.

    Returns:
        Theme id to the union of its members' genes.
    """
    out: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out[row["node"]].update(genes.get(row["key"], frozenset()))
    return dict(out)


def theme_sizes(directory: Path) -> dict[str, int]:
    """Member count per theme.

    Args:
        directory: A build directory.

    Returns:
        Theme id to pathway count.
    """
    out: dict[str, int] = defaultdict(int)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out[row["node"]] += 1
    return dict(out)


def density(members: np.ndarray, adjacency: sparse.csr_matrix) -> float:
    """Internal edge density of a gene set, as a share of the pairs it could have.

    Computed as a sparse submatrix rather than a loop over neighbour lists. The loop was the first
    version and it was far too slow to be run: a theme of 5,000 genes needs ~700,000 membership
    tests, and the null needs a hundred of those per theme across thousands of themes.

    Args:
        members: Gene indices into the covered-symbol list.
        adjacency: Symmetric CSR adjacency over covered genes, no self-loops.

    Returns:
        Internal edges divided by ``k * (k - 1) / 2``, or 0.0 below two members.
    """
    k = int(members.shape[0])
    if k < 2:
        return 0.0
    inside = adjacency[members][:, members]
    # Symmetric with no self-loops, so nnz is twice the edge count and the two factors of 2 cancel.
    return float(inside.nnz) / (k * (k - 1))


def null_for(
    k: int,
    adjacency: sparse.csr_matrix,
    covered: int,
    cache: dict[int, np.ndarray],
) -> np.ndarray:
    """The size-matched null for gene sets of size ``k``, drawn once and reused.

    Memoised by ``k`` because the null depends on nothing else: two themes whose gene unions happen
    to be the same size are being compared against the same distribution, so drawing it twice would
    cost twice as much and answer the same question. The draw order is fixed by the single seeded
    generator, so the result is reproducible.

    Args:
        k: Gene-set size.
        adjacency: Symmetric CSR adjacency over covered genes.
        covered: How many genes STRING covers.
        cache: Size to its null densities.

    Returns:
        A ``(NULL_SETS,)`` array of densities.
    """
    if k not in cache:
        rng = np.random.default_rng([NULL_SEED, k])
        out = np.empty(NULL_SETS)
        for i in range(NULL_SETS):
            out[i] = density(np.sort(rng.choice(covered, size=k, replace=False)), adjacency)
        cache[k] = out
    return cache[k]


def main(argv: list[str] | None = None) -> int:
    """Score every arm's PPI coherence and apply the gate.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from thema.data.pathways import PathwayCollection

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--arm", action="append", default=[], help="NAME=path under data/ontology/")
    parser.add_argument("--reference", default="A", help="the arm the gate is stated against")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    raw = args.data / "raw"
    if not (raw / "9606.protein.links.v12.0.txt.gz").is_file():
        print("G4 NOT RUN: STRING v12 is not present in data/raw", flush=True)
        return 2

    clock = time.perf_counter()
    neighbours, covered = load_string(raw)
    position = {symbol: i for i, symbol in enumerate(covered)}
    left, right = [], []
    for symbol, partners in neighbours.items():
        a = position[symbol]
        for partner in partners:
            b = position.get(partner)
            if b is not None:
                left.append(a)
                right.append(b)
    adjacency = sparse.csr_matrix(
        (np.ones(len(left), dtype=np.int8), (np.asarray(left), np.asarray(right))),
        shape=(len(covered), len(covered)),
    )
    adjacency.setdiag(0)
    adjacency.eliminate_zeros()
    total_edges = adjacency.nnz // 2
    print(f"STRING v12, combined score >= {MIN_SCORE}: {len(covered):,} genes, "
          f"{total_edges:,} edges ({time.perf_counter() - clock:.0f}s)", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}

    base = args.data / "ontology"
    null_cache: dict[int, np.ndarray] = {}
    report: dict = {"min_score": MIN_SCORE, "null_sets": NULL_SETS, "null_seed": NULL_SEED,
                    "alpha": ALPHA, "gate_points": GATE_POINTS,
                    "string_genes": len(covered), "string_edges": total_edges, "arms": {}}

    for spec in args.arm:
        name, path = spec.split("=", 1)
        directory = base / path
        if not (directory / "members.tsv").is_file():
            print(f"  {name}: no build at {directory}", flush=True)
            continue
        start = time.perf_counter()
        sizes = theme_sizes(directory)
        unions = theme_genes(directory, genes)
        rows = []
        for theme, symbols in unions.items():
            members = np.sort(np.fromiter(
                (position[s] for s in symbols if s in position), dtype=np.int64
            ))
            if members.shape[0] < 2:
                continue
            k = int(members.shape[0])
            observed = density(members, adjacency)
            null = null_for(k, adjacency, len(covered), null_cache)
            # Empirical p with the observed value included, so p is never 0.
            p = (1.0 + float((null >= observed).sum())) / (NULL_SETS + 1.0)
            rows.append((theme, sizes.get(theme, 0), k, observed, float(null.mean()), p))

        significant = [r for r in rows if r[5] < ALPHA]
        fraction = len(significant) / len(rows) if rows else 0.0
        per_band = {}
        for low, high in BANDS:
            band = [r for r in rows if low <= r[1] <= high]
            hit = [r for r in band if r[5] < ALPHA]
            per_band[f"{low}-{high}"] = {
                "themes": len(band),
                "fraction": round(len(hit) / len(band), 4) if band else None,
            }
        report["arms"][name] = {
            "themes_tested": len(rows), "themes_total": len(sizes),
            "fraction_p_lt_alpha": round(fraction, 4),
            "median_observed_density": round(float(np.median([r[3] for r in rows])), 6) if rows
            else None,
            "median_null_density": round(float(np.median([r[4] for r in rows])), 6) if rows
            else None,
            "per_band": per_band, "seconds": round(time.perf_counter() - start, 1),
        }
        print(f"\n  {name}: {len(rows):,} of {len(sizes):,} themes testable "
              f"({time.perf_counter() - start:.0f}s)")
        print(f"    fraction with p < {ALPHA}: {fraction:.1%}")
        for band, got in per_band.items():
            shown = "n/a" if got["fraction"] is None else f"{got['fraction']:.1%}"
            print(f"      {band:<9} {got['themes']:>6,} themes   {shown}")

    ref = report["arms"].get(args.reference)
    if ref is not None:
        print(f"\n  GATE G4, against {args.reference} "
              f"({ref['fraction_p_lt_alpha']:.1%}), tolerance {GATE_POINTS:.0%}")
        for name, got in report["arms"].items():
            gap = got["fraction_p_lt_alpha"] - ref["fraction_p_lt_alpha"]
            verdict = "PASS" if gap >= -GATE_POINTS else "FAIL"
            got["g4_gap"] = round(gap, 4)
            got["g4"] = verdict
            print(f"    {name:<6} {got['fraction_p_lt_alpha']:>7.1%}  {gap:>+7.1%}  {verdict}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
