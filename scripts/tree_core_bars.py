"""Prompt 60: what each recurrence bar keeps, and an indicative noise check.

Declared 23 Oct 2026. Exploratory; nothing is built beyond the cores and nothing is adopted.

Steps 1-2 of the new pipeline are: find the tree cores (prompt 59, cover 0.70) and keep the ones
that recur. This reports what bars of 5, 10 and 20 runs of 200 keep, before a bar is chosen.

**The scramble side is two seeds and is indicative only.** It is not a calibration: step 6's floor
procedure needs the ten calibration seeds to estimate a mean, with a rule-of-three substitution
where scrambles never pass. Two seeds say whether scrambled trees yield comparable numbers of
recurrent cores at all, and nothing more.

The scramble trees reuse the **identical subsamples** of the cached real runs -- their ``present``
bitsets are read back and handed to ``tree_from_subset`` -- so the only difference between a real
side and a scramble side is the permutation, which is what ``recurrent.null_embeddings`` does:
each embedding dimension shuffled independently across pathways, then rows rescaled to unit length.
They are written to a new directory and nothing cached is touched.

Usage:
    uv run scripts/tree_core_bars.py --scramble-trees      # build 2 x 200 trees
    uv run scripts/tree_core_bars.py                       # tasks 1 and 3, and report 2
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

BARS = (5, 10, 20)
SEEDS = (3001, 3002)
SEED = 20261023
EXAMPLES = 20
EXAMPLE_MIN = 6
COVER = 0.70

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"),
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
    return BANDS[-1][2] if size >= 1600 else BANDS[0][2]


def build_scramble_trees(args: argparse.Namespace) -> int:
    """Task 2's trees: two scramble seeds, the real subsamples, a new directory.

    Args:
        args: Parsed arguments.

    Returns:
        0.
    """
    from build_trees_10770 import MIN_SIZE as MIN_SIZE_TREE
    from build_trees_10770 import save_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import null_embeddings, tree_from_subset
    from thema.ontology.universe import load_embedded

    meta = json.loads((args.space_root / "universe.json").read_text())
    n = meta["n_embedded"]
    real = args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    # The universe is verified through the one loader, exactly as build_trees_10770 does, and then
    # the vectors are swapped for the CENTRED sidecar -- the matrix the real x2 trees were built
    # from. ``embeddings.npy`` is stored RAW on this universe; clustering it instead silently
    # compares a scrambled raw space against a real centred one. Asserted below against row 1.
    embedded = load_embedded(args.space_root, args.data / "pathways.tsv")
    if len(embedded.keys) != n:
        raise ValueError(f"{args.space_root}: {len(embedded.keys)} keys but universe.json says {n}")
    x = np.ascontiguousarray(np.load(args.space_root / args.vectors).astype(np.float32))
    if x.shape[0] != n:
        raise ValueError(f"{args.vectors} has {x.shape[0]} rows, universe has {n}")

    subsets = []
    for r in range(1, args.runs + 1):
        with np.load(real / f"row{r:05d}.npz") as handle:
            subsets.append(np.fromiter(bits.unpack(handle["present"]), dtype=np.int64))
    print(f"  reusing the {len(subsets)} real subsamples "
          f"({len(subsets[0]):,} pathways each)", flush=True)

    # Proof that ``x`` is the matrix the cached real trees were clustered from: rebuilding run 1
    # from it must return that run's clusters exactly. A wrong matrix is otherwise invisible --
    # the scramble side still builds, and its counts are simply not comparable to the real ones.
    from cut_trees import load_run
    from thema.ontology.v04 import NO_CAP

    reference = load_run(real / "row00001.npz", n, NO_CAP)
    rebuilt = tree_from_subset(x, n, subsets[0], MIN_SIZE_TREE)
    if not np.array_equal(np.asarray(rebuilt.clusters), np.asarray(reference.clusters)):
        raise ValueError(
            f"{args.vectors} does not reproduce the cached real run 1: "
            f"{np.asarray(rebuilt.clusters).shape} against "
            f"{np.asarray(reference.clusters).shape}. The scramble would not be comparable."
        )
    print(f"  {args.vectors} reproduces cached real run 1 exactly "
          f"({np.asarray(reference.clusters).shape[0]:,} clusters)", flush=True)

    from scramble_cache import CACHE

    seeds = (tuple(int(s) for s in args.seeds.split(",")) if getattr(args, "seeds", None)
             else SEEDS)
    # The cache is where the sides live; it is read-only on disk, so an already-built seed is
    # skipped before anything tries to write, and a new seed needs the folder made writable first.
    root = args.trees_out if getattr(args, "trees_out", None) else CACHE
    for seed in seeds:
        out = root / f"seed{seed:05d}"
        if out.exists() and len(list(out.glob("row*.npz"))) >= args.runs:
            print(f"  seed {seed}: already built, skipping", flush=True)
            continue
        out.mkdir(parents=True, exist_ok=True)
        null = null_embeddings(x, seed)
        clock = time.perf_counter()
        for r, subset in enumerate(subsets, 1):
            run = tree_from_subset(null, n, subset, MIN_SIZE_TREE)
            save_run(out / f"row{r:05d}.npz", run)
            if r % 50 == 0:
                print(f"    seed {seed}: {r}/{args.runs} "
                      f"({time.perf_counter() - clock:.0f}s)", flush=True)
        print(f"  seed {seed}: {args.runs} trees -> {out} "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return 0




def load_scored(out: Path) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Candidates, their sizes and their runs-found count from a prompt-59 output directory.

    Args:
        out: Directory holding ``candidates.npz`` and ``scored.npz``.

    Returns:
        ``(member arrays, sizes, found)``.
    """
    with np.load(out / "candidates.npz") as handle:
        flat, indptr = handle["flat"], handle["indptr"]
    with np.load(out / "scored.npz") as handle:
        found = handle["found"]
    cands = [flat[indptr[i]:indptr[i + 1]] for i in range(len(indptr) - 1)]
    return cands, np.diff(indptr).astype(np.int64), found


def redundancy(rows: list[np.ndarray], n: int) -> dict[str, object]:
    """Prompt 58's verified exact counter, reused unchanged.

    Args:
        rows: Member index arrays per retained core.
        n: Universe size.

    Returns:
        The three near-copy counts, with the brute-force check.
    """
    from core_merge_pairs import brute, counts_for, matrix

    sizes = np.array([len(r) for r in rows], dtype=np.int64)
    listed = [r.tolist() for r in rows]
    got = counts_for(matrix(listed, n), sizes, report=True)
    rng = np.random.default_rng(SEED)
    take = min(2000, len(listed))
    pick = np.sort(rng.choice(len(listed), size=take, replace=False))
    fast = counts_for(matrix([listed[int(i)] for i in pick], n), sizes[pick],
                      report=False)["totals"]
    slow = brute(listed, sizes, pick)
    got["verification"] = {"sample": int(take), "seed": SEED, "sparse": fast, "brute": slow,
                           "identical": all(fast[k] == slow[k] for k in slow)}
    return got


def examples(cands: list[np.ndarray], found: np.ndarray, sizes: np.ndarray,
             keys: list[str], args: argparse.Namespace) -> list[Path]:
    """Task 3: twenty cores from each recurrence group, for reading later.

    Args:
        cands: Member index arrays.
        found: Runs found per candidate.
        sizes: Members per candidate.
        keys: Pathway keys in universe order.
        args: Parsed arguments.

    Returns:
        The files written.
    """
    from thema.data.pathways import PathwayCollection

    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}
    out = args.out / "bars" / "examples"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.md"):
        stale.unlink()
    groups = (("5-9", 5, 9), ("10-19", 10, 19), ("20plus", 20, 10 ** 9))
    rng = random.Random(SEED)
    written = []
    for label, low, high in groups:
        pool = np.flatnonzero((found >= low) & (found <= high) & (sizes >= EXAMPLE_MIN))
        pick = sorted(rng.sample(pool.tolist(), min(EXAMPLES, len(pool))))
        lines = []
        for position, row in enumerate(pick, 1):
            lines.append(f"## {label}-{position:02d}  ({int(sizes[row])} pathways, "
                         f"found in {int(found[row])} runs of 200)")
            lines.append("")
            lines += sorted(
                f"- {named.get(keys[p], (keys[p], '?'))[0]} "
                f"[{named.get(keys[p], (keys[p], '?'))[1]}]"
                for p in cands[row].tolist())
            lines.append("")
        path = out / f"runs_{label}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
        print(f"  examples {label}: {len(pick)} of {len(pool):,} available -> {path}")
    return written


def noise(real_found: np.ndarray, real_sizes: np.ndarray,
          args: argparse.Namespace) -> dict[str, object]:
    """Task 2: how many cores the two scramble sides retain at each bar.

    Indicative only. Two seeds is not a calibration, and the ratio below is a ratio of counts
    on one draw each, with no interval.

    Args:
        real_found: Runs found per real candidate.
        real_sizes: Members per real candidate.
        args: Parsed arguments.

    Returns:
        Per-seed and mean retained counts, by band and bar.
    """
    root = args.out / "bars" / "scramble"
    got: dict[str, object] = {}
    for seed in SEEDS:
        where = root / f"seed{seed:05d}"
        if not (where / "scored.npz").is_file():
            return {}
        _c, sizes, found = load_scored(where)
        bands = np.array([band_of(int(s)) for s in sizes])
        got[str(seed)] = {
            "candidates": int(len(sizes)),
            "bars": {str(bar): {"total": int((found >= bar).sum()),
                                "bands": {band: int(((found >= bar) & (bands == band)).sum())
                                          for _lo, _hi, band in BANDS}}
                     for bar in BARS},
        }
    real_bands = np.array([band_of(int(s)) for s in real_sizes])
    print("=" * 104)
    print("2. NOISE CHECK -- TWO SCRAMBLE SEEDS, INDICATIVE ONLY, NOT A CALIBRATION")
    print("=" * 104)
    print(f"  candidates: real {len(real_sizes):,}; " + "; ".join(
        f"seed {s} {got[str(s)]['candidates']:,}" for s in SEEDS))
    print()
    print(f"  {'bar':<10}{'real':>12}{'seed 3001':>12}{'seed 3002':>12}{'mean':>12}"
          f"{'scrambled/real':>18}")
    summary = {}
    for bar in BARS:
        real = int((real_found >= bar).sum())
        each = [got[str(s)]["bars"][str(bar)]["total"] for s in SEEDS]
        mean = sum(each) / len(each)
        print(f"  {'>= ' + str(bar) + ' runs':<10}{real:>12,}{each[0]:>12,}{each[1]:>12,}"
              f"{mean:>12,.1f}{mean / real if real else 0:>17.2%}")
        summary[str(bar)] = {"real": real, "seeds": each, "mean": mean,
                             "ratio": mean / real if real else None}
    print()
    print("  by band, mean of the two seeds against real")
    print(f"  {'band':<10}" + "".join(
        f"{'>=' + str(b) + ' real':>14}{'scram':>10}{'ratio':>9}" for b in BARS))
    for _lo, _hi, band in BANDS:
        cells, any_seen = "", False
        for bar in BARS:
            real = int(((real_found >= bar) & (real_bands == band)).sum())
            mean = sum(got[str(s)]["bars"][str(bar)]["bands"][band] for s in SEEDS) / len(SEEDS)
            any_seen = any_seen or real or mean
            cells += (f"{real:>14,}{mean:>10,.1f}"
                      f"{(mean / real if real else float('nan')):>9.1%}")
        if any_seen:
            print(f"  {band:<10}" + cells)
    print()
    return {"seeds": got, "by_bar": summary}


def main(argv: list[str] | None = None) -> int:
    """Tasks 1 and 3, and report task 2 if the scramble sides are present.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/tree_cores_2026-10-23"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--vectors", type=Path,
                        default=Path("vectors_leaves_centred.npy"),
                        help="the matrix the real trees were built from, relative "
                             "to --space-root; the x2 universe stores embeddings.npy "
                             "RAW and this centred sidecar beside it")
    parser.add_argument("--scramble-trees", action="store_true",
                        help="build the scramble sides' trees and stop")
    parser.add_argument("--seeds", default=None,
                        help="comma-separated scramble seeds; defaults to prompt 60's 3001,3002")
    parser.add_argument("--trees-out", type=Path, default=None,
                        help="where to write them; defaults to the permanent cache, "
                             "scramble_cache.CACHE")
    args = parser.parse_args(argv)

    if args.scramble_trees:
        return build_scramble_trees(args)

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    cands, sizes, found = load_scored(args.out)
    print("PROMPT 60: WHAT EACH RECURRENCE BAR KEEPS. Tree cores at cover 0.70.")
    print(f"  {len(cands):,} candidates from prompt 59, unchanged; "
          f"{len(keys):,} pathways in the universe")
    print()

    record: dict[str, object] = {"bars": {}, "cover": COVER, "universe": len(keys)}
    print("=" * 104)
    print("1a. RETAINED CORES BY BAND, AT EACH BAR")
    print("=" * 104)
    print(f"  {'band':<12}" + "".join(f"{'>=' + str(b) + ' runs':>16}" for b in BARS))
    bands_of = np.array([band_of(int(s)) for s in sizes])
    for _lo, _hi, band in BANDS:
        cells = []
        for bar in BARS:
            cells.append(int(((found >= bar) & (bands_of == band)).sum()))
        if any(cells):
            print(f"  {band:<12}" + "".join(f"{c:>16,}" for c in cells))
    print(f"  {'TOTAL':<12}" + "".join(f"{int((found >= b).sum()):>16,}" for b in BARS))
    print()

    print("=" * 104)
    print("1b. THE TEN LARGEST RETAINED CORES, AT EACH BAR")
    print("=" * 104)
    for bar in BARS:
        rows = np.flatnonzero(found >= bar)
        top = rows[np.argsort(-sizes[rows])][:10]
        print(f"  >= {bar} runs: " + ", ".join(
            f"{int(sizes[i])} ({int(found[i])}r)" for i in top))
    print()

    print("=" * 104)
    print("1c. PATHWAYS COVERED BY AT LEAST ONE RETAINED CORE")
    print("=" * 104)
    print(f"  {'bar':<12}{'pathways':>12}{'share of ' + str(len(keys)):>20}")
    for bar in BARS:
        rows = np.flatnonzero(found >= bar)
        covered = np.unique(np.concatenate([cands[i] for i in rows])) if len(rows) else []
        print(f"  {'>= ' + str(bar) + ' runs':<12}{len(covered):>12,}"
              f"{len(covered) / len(keys):>20.2%}")
        record["bars"][str(bar)] = {"retained": int(len(rows)), "covered": int(len(covered))}
    print()

    print("=" * 104)
    print("1d. REDUNDANCY AMONG THE RETAINED CORES (prompt 58's exact counter)")
    print("=" * 104)
    print(f"  {'bar':<12}{'cores':>11}{'J>=0.5 non-nested':>20}{'nested >=0.85':>16}"
          f"{'1 outside':>14}{'verified':>11}")
    for bar in BARS:
        rows = np.flatnonzero(found >= bar)
        clock = time.perf_counter()
        got = redundancy([cands[i] for i in rows], len(keys))
        tot = got["totals"]
        ok = got["verification"]["identical"]
        print(f"  {'>= ' + str(bar) + ' runs':<12}{len(rows):>11,}{tot['j05']:>20,}"
              f"{tot['nested85']:>16,}{tot['one_stray']:>14,}"
              f"{'IDENTICAL' if ok else 'MISMATCH':>11}")
        record["bars"][str(bar)]["redundancy"] = got
        record["bars"][str(bar)]["seconds"] = round(time.perf_counter() - clock, 1)
    print()
    print("  by band of the larger theme, non-nested pairs at J >= 0.5")
    print(f"  {'band':<12}" + "".join(f"{'>=' + str(b):>14}" for b in BARS))
    for _lo, _hi, band in BANDS:
        cells = [record["bars"][str(b)]["redundancy"]["j05"].get(band, 0) for b in BARS]
        if any(cells):
            print(f"  {band:<12}" + "".join(f"{c:>14,}" for c in cells))
    print()

    (args.out / "bars").mkdir(parents=True, exist_ok=True)
    (args.out / "bars" / "bars.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    record["noise"] = noise(found, sizes, args)
    (args.out / "bars" / "bars.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    examples(cands, found, sizes, keys, args)
    print(f"  -> {args.out / 'bars' / 'bars.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
