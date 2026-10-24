"""Section C of prompt 58: the near-copy counts, computed exactly without an all-pairs loop.

Declared 23 Oct 2026. Evaluation only.

Three relations are counted over every unordered pair of themes in a set:

1. **non-nested pairs at J >= 0.5** -- neither contains the other, ``inter / union >= 0.5``;
2. **nested pairs with the smaller holding >= 0.85 of the larger** -- ``inter == smaller``
   and ``smaller >= 0.85 * larger``;
3. **pairs where the smaller has exactly one member outside the larger** --
   ``smaller - inter == 1``, which is consensus rule 2's inheritance trigger.

**Method, and one stated deviation.** All three relations are functions of ``(inter, smaller,
larger)`` alone, so the overlap counts come from chunked sparse products of the theme-by-pathway
matrix with its own transpose -- never an all-pairs loop. Relations 1 and 2 admit exact size
windows (relation 1 needs ``smaller >= 0.5 * larger``, relation 2 needs ``smaller >= 0.85 *
larger``), but **relation 3 admits none**: a 3-member theme can sit one stray away from a
2,000-member theme. The unwindowed product is therefore required anyway, so it is computed once per
chunk and the windows are applied as masks on the resulting triples rather than as three separate
restricted products. That is exact and strictly less work than three passes; it is a deviation from
the letter of "a size-window filter" and is recorded here rather than left implicit.

**Verified against brute force** on a random sample of 2,000 themes, seed 20261023: the sampled
sub-matrix is counted both ways and every figure must agree exactly.

Usage:
    uv run scripts/core_merge_pairs.py --set CI
    uv run scripts/core_merge_pairs.py --set s2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SEED = 20261023
SAMPLE = 2000
CHUNK = 128

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
    return BANDS[0][2]


def matrix(rows: list[list[int]], n_pathways: int) -> object:
    """Theme-by-pathway CSR matrix.

    Args:
        rows: Member pathway indices per theme.
        n_pathways: Universe size.

    Returns:
        A ``scipy.sparse.csr_matrix`` of ones. Typed loosely because scipy is imported inside the
        function, as every heavy third-party import in this repo is.
    """
    from scipy import sparse

    indptr = np.zeros(len(rows) + 1, dtype=np.int64)
    np.cumsum([len(r) for r in rows], out=indptr[1:])
    indices = np.concatenate([np.asarray(r, dtype=np.int32) for r in rows]) if rows \
        else np.zeros(0, np.int32)
    data = np.ones(len(indices), dtype=np.int32)
    return sparse.csr_matrix((data, indices, indptr),
                             shape=(len(rows), n_pathways), dtype=np.int32)


def counts_for(csr: object, sizes: np.ndarray,
               report: bool = True) -> dict[str, object]:
    """The three relations, counted exactly by chunked sparse products.

    Args:
        csr: Theme-by-pathway matrix.
        sizes: Members per theme.
        report: Print progress.

    Returns:
        Totals and per-band breakdowns, banded by the LARGER theme.
    """
    n = csr.shape[0]
    transposed = csr.T.tocsc()
    j05: dict[str, int] = defaultdict(int)
    n85: dict[str, int] = defaultdict(int)
    one: dict[str, int] = defaultdict(int)
    clock = time.perf_counter()
    for start in range(0, n, CHUNK):
        stop = min(start + CHUNK, n)
        block = (csr[start:stop] @ transposed).tocoo()
        left = block.row + start
        right = block.col
        inter = block.data.astype(np.int64)
        keep = left < right                       # each unordered pair once
        left, right, inter = left[keep], right[keep], inter[keep]
        if not len(left):
            continue
        a, b = sizes[left], sizes[right]
        smaller = np.minimum(a, b)
        larger = np.maximum(a, b)
        union = a + b - inter
        nested = inter == smaller
        # 1. non-nested at J >= 0.5, with the exact window smaller >= 0.5 * larger
        hit = (~nested) & (union > 0) & (inter * 2 >= union) & (smaller * 2 >= larger)
        for size in larger[hit]:
            j05[band_of(int(size))] += 1
        # 2. nested, the smaller holding >= 0.85 of the larger
        hit = nested & (smaller * 100 >= 85 * larger)
        for size in larger[hit]:
            n85[band_of(int(size))] += 1
        # 3. the smaller exactly one member outside the larger -- no window is exact here
        hit = (smaller - inter) == 1
        for size in larger[hit]:
            one[band_of(int(size))] += 1
        if report and (start // CHUNK) % 200 == 0:
            print(f"      {stop:,}/{n:,} ({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"j05": dict(j05), "nested85": dict(n85), "one_stray": dict(one),
            "totals": {"j05": sum(j05.values()), "nested85": sum(n85.values()),
                       "one_stray": sum(one.values())},
            "seconds": round(time.perf_counter() - clock, 1)}


def brute(rows: list[list[int]], sizes: np.ndarray, pick: np.ndarray) -> dict[str, int]:
    """The same three counts by an explicit double loop over a sample.

    Args:
        rows: Member indices per theme.
        sizes: Members per theme.
        pick: Theme indices in the sample.

    Returns:
        Totals for the sample.
    """
    sets = {int(i): set(rows[int(i)]) for i in pick}
    order = sorted(int(i) for i in pick)
    got = {"j05": 0, "nested85": 0, "one_stray": 0}
    for position, i in enumerate(order):
        a = sets[i]
        for j in order[position + 1:]:
            b = sets[j]
            inter = len(a & b)
            if not inter:
                continue
            sa, sb = len(a), len(b)
            small, large = min(sa, sb), max(sa, sb)
            union = sa + sb - inter
            nested = inter == small
            if (not nested) and union and inter * 2 >= union and small * 2 >= large:
                got["j05"] += 1
            if nested and small * 100 >= 85 * large:
                got["nested85"] += 1
            if small - inter == 1:
                got["one_stray"] += 1
    return got


def load_set(name: str, args: argparse.Namespace) -> tuple[list[list[int]], np.ndarray,
                                                            np.ndarray]:
    """Member index lists, sizes and supports for one theme set.

    ``CI`` and ``CT`` come from the arms; ``s2`` is O50s's families before the gate and ``s3`` the
    26,120 that cleared it, both from the cached x2 real side.

    Args:
        name: ``"CI"``, ``"CT"``, ``"s2"`` or ``"s3"``.
        args: Parsed arguments.

    Returns:
        ``(rows, sizes, supports)``.
    """
    from thema.ontology import bitset as bits

    if name in ("CI", "CT"):
        with np.load(args.arms / f"themes_{name}.npz") as handle:
            stack, support = handle["members"], handle["support"]
        rows = [sorted(bits.unpack(stack[i])) for i in range(len(stack))]
        return rows, np.array([len(r) for r in rows], dtype=np.int64), support

    with np.load(args.space_root / "calibration" / "real.npz") as handle:
        blocks, supports = handle["blocks"], handle["supports"]
    if name == "s3":
        frozen = json.loads((args.frozen / "manifest.json").read_text())
        from thema.ontology.v04 import Material, gate
        indptr = None
        with np.load(args.space_root / "calibration" / "real.npz") as handle:
            indptr = handle["indptr"]
            vote_keys, vote_vals = handle["vote_keys"], handle["vote_vals"]
        votes = tuple(
            dict(zip(vote_keys[indptr[i]:indptr[i + 1]].tolist(),
                     vote_vals[indptr[i]:indptr[i + 1]].tolist(), strict=True))
            for i in range(len(indptr) - 1))
        keep = np.flatnonzero(gate(Material(blocks=blocks, supports=supports,
                                            selections=votes).rows(),
                                   frozen["floors"], [tuple(s) for s in frozen["strata"]]))
        blocks, supports = blocks[keep], supports[keep]
    rows = [sorted(bits.unpack(blocks[i])) for i in range(len(blocks))]
    return rows, np.array([len(r) for r in rows], dtype=np.int64), supports


def main(argv: list[str] | None = None) -> int:
    """Count the three relations for one theme set, and verify against brute force.

    Args:
        argv: Command line.

    Returns:
        0, or 2 if the verification disagrees.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--arms", type=Path,
                        default=Path("data/experiments/core_merge_2026-10-23"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/core_merge_2026-10-23"))
    parser.add_argument("--set", dest="which", required=True,
                        choices=("CI", "CT", "s2", "s3"))
    parser.add_argument("--floors-only", action="store_true",
                        help="restrict to themes passing O50s's stored floors (INDICATIVE)")
    args = parser.parse_args(argv)

    rows, sizes, supports = load_set(args.which, args)
    label = args.which + ("-floors" if args.floors_only else "")
    if args.floors_only:
        frozen = json.loads((args.frozen / "manifest.json").read_text())
        floors = frozen["floors"]
        strata = [tuple(s) for s in frozen["strata"]]

        def passes(size: int, support: float) -> bool:
            """Does this theme clear its stratum's stored floor?

            The support is rounded to six decimals first, because ``Material.rows`` -- the form
            ``v04.gate`` consumes -- does exactly that. Comparing the raw float instead rejects
            themes whose support sits a hair under a floor and would have passed the real gate: it
            cost 28 of s2's 26,120 before this was found.
            """
            value = round(float(support), 6)
            for (low, high), entry in zip(strata, floors, strict=True):
                if low <= size <= high:
                    return value >= float(entry["effective"])
            return False

        keep = [i for i in range(len(rows)) if passes(int(sizes[i]), float(supports[i]))]
        rows = [rows[i] for i in keep]
        sizes = sizes[np.array(keep, dtype=np.int64)] if keep else np.zeros(0, np.int64)
        print(f"  INDICATIVE ONLY: the stored floors were calibrated for O50s's families, not "
              f"for this set; {len(keep):,} of {len(supports):,} themes pass")

    n_pathways = max((max(r) for r in rows if r), default=0) + 1
    print(f"  {label}: {len(rows):,} themes, {n_pathways:,} pathway slots", flush=True)
    csr = matrix(rows, n_pathways)
    got = counts_for(csr, sizes)
    print(f"  totals  J>=0.5 non-nested {got['totals']['j05']:,};  "
          f"nested >=0.85 {got['totals']['nested85']:,};  "
          f"one stray {got['totals']['one_stray']:,}  ({got['seconds']:.0f}s)")

    rng = np.random.default_rng(SEED)
    take = min(SAMPLE, len(rows))
    pick = np.sort(rng.choice(len(rows), size=take, replace=False))
    sub_rows = [rows[int(i)] for i in pick]
    sub_sizes = sizes[pick]
    fast = counts_for(matrix(sub_rows, n_pathways), sub_sizes, report=False)["totals"]
    slow = brute(rows, sizes, pick)
    agree = all(fast[k] == slow[k] for k in slow)
    print(f"  VERIFICATION on {take:,} themes (seed {SEED}): sparse {fast} vs brute {slow} "
          f"-> {'IDENTICAL' if agree else 'MISMATCH'}")
    got["verification"] = {"sample": int(take), "seed": SEED, "sparse": fast, "brute": slow,
                           "identical": bool(agree)}
    (args.out / f"section_c_{label}.json").write_text(json.dumps(got, indent=1) + "\n",
                                                      encoding="utf-8")
    print(f"  -> {args.out / f'section_c_{label}.json'}")
    return 0 if agree else 2


if __name__ == "__main__":
    raise SystemExit(main())
