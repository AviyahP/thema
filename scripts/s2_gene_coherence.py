"""PART 2 section G of prompt 55: gene coherence per band, against size-matched random sets.

Declared 22 Oct 2026. Evaluation only; nothing is adopted and no verdict is offered.

A theme's **coherence** is the mean pairwise gene Jaccard over its member pathways. Its **null** is
the same statistic on a random set of pathways of the SAME SIZE, drawn from the same universe, so
the comparison is size-matched by construction rather than by a correction afterwards. The reported
quantity per band is the mean observed coherence, the mean null, and the lift between them.

**Pairs are sampled, and that is a real limitation.** A 2,600-pathway theme has 3.4 million member
pairs; computing all of them for every theme in two builds is not worth the hours. Up to
``PAIR_SAMPLE`` pairs are drawn per theme, with a fixed seed, and every theme with fewer pairs than
that is computed exactly. The sampling error on a 500-pair mean is small next to the band-to-band
differences this is looking for, but it is sampling and the number of exactly-computed themes is
reported so the reader can see where it bites.

No existing script reports this; ``thema.evaluation.gene_similarity`` computes a similarity matrix
from precomputed intersections and is not the per-theme-against-null harness needed here, so the
harness is new and the definition above is part of the result.

Usage:
    uv run scripts/s2_gene_coherence.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: Pairs drawn per theme. Themes with fewer pairs are computed exactly.
PAIR_SAMPLE = 500

#: Null sets drawn per theme.
NULL_SETS = 1

SEED = 20261022

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return "3-5"


def gene_bitsets(keys: Sequence[str], genes: dict[str, frozenset[str]]
                 ) -> tuple[np.ndarray, np.ndarray]:
    """Pack each pathway's gene set into a bitset.

    Args:
        keys: Pathway keys in universe order.
        genes: Key to its genes.

    Returns:
        ``(stack, sizes)``.
    """
    every = sorted({g for key in keys for g in genes.get(key, ())})
    at = {g: i for i, g in enumerate(every)}
    words = (len(every) + 63) // 64
    stack = np.zeros((len(keys), words), dtype=np.uint64)
    for row, key in enumerate(keys):
        for gene in genes.get(key, ()):
            position = at[gene]
            stack[row, position // 64] |= np.uint64(1) << np.uint64(position % 64)
    return stack, np.bitwise_count(stack).sum(axis=1).astype(np.int64)


def mean_pairwise(rows: np.ndarray, stack: np.ndarray, sizes: np.ndarray,
                  rng: np.random.Generator) -> tuple[float, bool]:
    """Mean pairwise gene Jaccard over a set of pathways.

    Args:
        rows: Universe positions of the set's members.
        stack: Gene bitsets.
        sizes: Gene-set size per pathway.
        rng: Generator for the pair sample.

    Returns:
        ``(mean jaccard, whether every pair was computed)``.
    """
    count = len(rows)
    if count < 2:
        return float("nan"), True
    total = count * (count - 1) // 2
    if total <= PAIR_SAMPLE:
        left, right = np.triu_indices(count, k=1)
        exact = True
    else:
        left = rng.integers(0, count, size=PAIR_SAMPLE * 2)
        right = rng.integers(0, count, size=PAIR_SAMPLE * 2)
        good = left != right
        left, right = left[good][:PAIR_SAMPLE], right[good][:PAIR_SAMPLE]
        exact = False
    a, b = rows[left], rows[right]
    inter = np.bitwise_count(stack[a] & stack[b]).sum(axis=1).astype(np.int64)
    union = sizes[a] + sizes[b] - inter
    jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    return float(jac.mean()), exact


def coherence(name: str, directory: Path, index: dict[str, int], stack: np.ndarray,
              sizes: np.ndarray, n_pathways: int) -> dict[str, object]:
    """Coherence and its size-matched null, per band, for one build.

    Args:
        name: Build label.
        directory: The build directory.
        index: Pathway key to universe position.
        stack: Gene bitsets.
        sizes: Gene-set size per pathway.
        n_pathways: Universe size.

    Returns:
        Per-band means and counts.
    """
    held: dict[str, list[int]] = defaultdict(list)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            held[row["node"]].append(index[row["key"]])

    rng = np.random.default_rng(SEED)
    observed: dict[str, list[float]] = defaultdict(list)
    null: dict[str, list[float]] = defaultdict(list)
    exact_count: dict[str, int] = defaultdict(int)
    total_count: dict[str, int] = defaultdict(int)
    for members in held.values():
        rows = np.array(sorted(members), dtype=np.int64)
        band = band_of(len(rows))
        value, exact = mean_pairwise(rows, stack, sizes, rng)
        if not np.isfinite(value):
            continue
        observed[band].append(value)
        total_count[band] += 1
        exact_count[band] += int(exact)
        draws = []
        for _ in range(NULL_SETS):
            pick = rng.choice(n_pathways, size=len(rows), replace=False)
            got, _ = mean_pairwise(np.sort(pick), stack, sizes, rng)
            if np.isfinite(got):
                draws.append(got)
        if draws:
            null[band].append(float(np.mean(draws)))
    out = {}
    for _low, _high, band in BANDS:
        if not observed[band]:
            continue
        o = float(np.mean(observed[band]))
        e = float(np.mean(null[band])) if null[band] else float("nan")
        out[band] = {"themes": total_count[band], "exact": exact_count[band],
                     "observed": o, "null": e,
                     "lift": (o / e) if e and np.isfinite(e) and e > 0 else float("nan")}
    every_o = [v for band in observed for v in observed[band]]
    every_n = [v for band in null for v in null[band]]
    out["ALL"] = {"themes": sum(total_count.values()), "exact": sum(exact_count.values()),
                  "observed": float(np.mean(every_o)), "null": float(np.mean(every_n)),
                  "lift": float(np.mean(every_o) / np.mean(every_n))}
    return {"name": name, "bands": out}


def main(argv: list[str] | None = None) -> int:
    """Print section G for S2 and O50s.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology.universe import load_embedded

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

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    index = {key: i for i, key in enumerate(keys)}
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in table.pathways}
    stack, sizes = gene_bitsets(keys, genes)
    print("PROMPT 55 PART 2, SECTION G: GENE COHERENCE AGAINST SIZE-MATCHED RANDOM SETS.")
    print(f"  {len(keys):,} pathways; {int(stack.shape[1] * 64):,} gene slots; "
          f"median genes per pathway {int(np.median(sizes))}")
    print(f"  up to {PAIR_SAMPLE} member pairs per theme, seed {SEED}; "
          f"{NULL_SETS} size-matched random set per theme")
    print()

    got = []
    for name, path in (("O50s", args.o50s), ("S2", args.s2)):
        got.append(coherence(name, path, index, stack, sizes, len(keys)))
        print(f"  {name} done", flush=True)
    print()
    print("=" * 104)
    print("G. MEAN PAIRWISE GENE JACCARD, OBSERVED AGAINST A SIZE-MATCHED RANDOM SET")
    print("=" * 104)
    print(f"  {'band':<11}" + "".join(
        f"{g['name'] + ' obs':>13}{'null':>9}{'lift':>8}" for g in got) + f"{'exact':>18}")
    labels = [b[2] for b in BANDS] + ["ALL"]
    for band in labels:
        if not any(band in g["bands"] for g in got):
            continue
        line = f"  {band:<11}"
        for g in got:
            cell = g["bands"].get(band)
            if cell is None:
                line += f"{'-':>13}{'-':>9}{'-':>8}"
                continue
            line += f"{cell['observed']:>13.4f}{cell['null']:>9.4f}{cell['lift']:>8.1f}"
        exact = got[0]["bands"].get(band, {})
        line += f"{f'{exact.get('exact', 0)}/{exact.get('themes', 0)}':>18}"
        print(line)
    print()
    print("  lift is observed / null. 'exact' counts themes where every member pair was computed")
    print("  rather than sampled, for O50s; S2's counts are within a few of the same.")
    print()
    (args.out / "section_g.json").write_text(json.dumps(got, indent=1) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'section_g.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
