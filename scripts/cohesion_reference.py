#!/usr/bin/env python3
"""Reproduce every table in the 29 Sep cohesion decision, from its declared inputs and seeds.

The decision entry in ``DECISIONS.md`` was measured ad hoc. This is the committed reproduction it
requires before it is relied on: same inputs, same seeds, same strata, same draw counts, printed in
the same shape so a reader can diff the numbers by eye.

**Cohesion** of a theme is the mean pairwise cosine among its members in the CENTRED space -- the
build's own geometry, not gene overlap and not names.

Two nulls, and the entry's claim is that only one of them is informative:

- **random sets** -- subsets of the universe of the same size, seed 0. After centring the mean
  cosine over all pairs is zero, so this null sits at 0.000 by construction and every theme beats
  it. A yes that carries no information.
- **kNN balls** -- a random pathway plus its s-1 nearest neighbours, seed 1: the tightest group of
  size s the space can offer at a random location. This one can fail, which is what makes it
  evidence.

Usage::

    uv run scripts/cohesion_reference.py
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.embed import centre_and_renormalise
from thema.ontology.universe import load_embedded

csv.field_size_limit(1 << 30)

#: Size strata, as the decision declares them.
STRATA: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 9, "6-9"), (10, 19, "10-19"),
    (20, 49, "20-49"), (50, 199, "50-199"), (200, 10**9, "200+"),
)

#: Seeds and draw counts, declared in the entry's Reproduction section.
SEED_RANDOM = 0
SEED_BALLS = 1
DRAWS_PER_LEAF = 20
DRAWS_PER_STRATUM = 200
BALLS_PER_STRATUM = 300

#: The threshold the entry evaluates and then declines to adopt.
PROPOSED_CUT = 0.20


def load_space(directory: Path, pathways: Path) -> tuple[list[str], np.ndarray]:
    """Load the universe through the verifying loader and put it in the clustering space.

    Goes through :func:`thema.ontology.universe.load_embedded` rather than reading the ``.npy``
    directly, so a superseded or inconsistent artifact raises here as it would in a build. A test
    asserts that nothing in the repo bypasses it.

    Args:
        directory: A versioned ontology directory.
        pathways: Path to ``pathways.tsv``, which the loader verifies the keys against.

    Returns:
        Keys, and the centred-and-renormalised vectors the build clustered.
    """
    embedded = load_embedded(directory, pathways)
    centred, _mean = centre_and_renormalise(embedded.vectors)
    return list(embedded.keys), np.ascontiguousarray(centred.astype(np.float64))


def load_build(directory: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Read a build's parents and members.

    Args:
        directory: A build directory.

    Returns:
        Node id to parent ids, and node id to member keys.
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, list[str]] = defaultdict(list)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    return parents, dict(members)


def cohesion(rows: np.ndarray) -> float:
    """Mean pairwise cosine of a set of unit vectors.

    Args:
        rows: ``(n, dim)`` unit vectors.

    Returns:
        The mean over the ``n(n-1)/2`` distinct pairs, or 0.0 for fewer than two rows.
    """
    n = len(rows)
    if n < 2:
        return 0.0
    gram = rows @ rows.T
    return float((gram.sum() - np.trace(gram)) / (n * (n - 1)))


def stratum_of(size: int) -> str:
    """Label of the stratum a theme of this size falls in.

    Args:
        size: Member count.

    Returns:
        A label from :data:`STRATA`.

    Raises:
        ValueError: If no stratum covers the size.
    """
    for low, high, label in STRATA:
        if low <= size <= high:
            return label
    raise ValueError(f"no stratum covers size {size}")


def percentile(values: Sequence[float], q: float) -> float:
    """A percentile, or 0.0 for an empty sample.

    Args:
        values: The sample.
        q: Percentile in 0-100.

    Returns:
        The percentile.
    """
    return float(np.percentile(values, q)) if len(values) else 0.0


def main(argv: list[str] | None = None) -> int:
    """Reproduce the decision's tables.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.2")
    parser.add_argument("--build", default="recurrent_dag_c50")
    parser.add_argument("--compare", default="recurrent_dag_consensus_centred")
    parser.add_argument("--roots", type=int, default=4,
                        help="how many of the largest roots to report cohesion for, each against "
                             "kNN balls of its own size")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys, space = load_space(root, args.data / "pathways.tsv")
    index = {key: i for i, key in enumerate(keys)}
    parents, members = load_build(root / args.build)
    kids: dict[str, list[str]] = defaultdict(list)
    for node, ps in parents.items():
        for parent in ps:
            kids[parent].append(node)

    def rows_of(node: str) -> np.ndarray:
        return space[[index[k] for k in members[node] if k in index]]

    coh = {node: cohesion(rows_of(node)) for node in parents}
    sizes = {node: len(members[node]) for node in parents}
    roots = [n for n, ps in parents.items() if not ps]
    leaves = [n for n in parents if not kids.get(n)]
    internal = [n for n in parents if kids.get(n)]

    print(f"REPRODUCING the 29 Sep cohesion entry -- {args.build}\n")
    print("  THE BUILD, IN SHAPE")
    print(f"    themes {len(parents)}: {len(roots)} roots, {len(internal)} internal, "
          f"{len(leaves)} leaves")
    leaf_sizes = sorted(sizes[n] for n in leaves)
    print(f"    leaves have {leaf_sizes[0]}-{leaf_sizes[-1]} members "
          f"(median {int(statistics.median(leaf_sizes))})")
    big = sorted(roots, key=lambda n: -sizes[n])[:3]
    print("    three largest roots: " + ", ".join(f"{n} ({sizes[n]})" for n in big))
    island = sorted(sizes[n] for n in roots if n not in big)
    print(f"    remaining {len(roots) - 3} roots span {island[0]}-{island[-1]} members")
    one_child = [n for n in internal if len(kids[n]) == 1]
    extra = sorted(len(set(members[n]) - set(members[kids[n][0]])) for n in one_child)
    print(f"    single-child internal nodes: {len(one_child)} of {len(internal)} "
          f"(median {int(statistics.median(extra))} direct members)")
    multi = sum(1 for ps in parents.values() if len(ps) > 1)
    print(f"    multi-parent {multi / len(parents):.0%}, "
          f"{sum(1 for n in internal if len(kids[n]) == 2)} nodes with two children, "
          f"{sum(1 for n in internal if len(kids[n]) >= 3)} with three or more")

    print("\n  COHESION BY SIZE")
    print(f"    {'members':<9} {'themes':>7} {'median':>8} {'p10':>8}")
    for _low, _high, label in STRATA:
        vals = [coh[n] for n in parents if stratum_of(sizes[n]) == label]
        if vals:
            print(f"    {label:<9} {len(vals):>7} {statistics.median(vals):>8.3f} "
                  f"{percentile(vals, 10):>8.3f}")
    lv = [coh[n] for n in leaves]
    print(f"\n    leaves p10/median/p90 = {percentile(lv, 10):.3f} / "
          f"{statistics.median(lv):.3f} / {percentile(lv, 90):.3f}")
    print(f"    all-theme median {statistics.median(list(coh.values())):.3f}")
    least = sorted(leaves, key=lambda n: coh[n])[:5]
    most = sorted(leaves, key=lambda n: -coh[n])[:3]
    print("    least cohesive leaves: " + ", ".join(f"{n} ({coh[n]:.3f})" for n in least))
    print("    most cohesive leaves:  " + ", ".join(f"{n} ({coh[n]:.3f})" for n in most))

    print("\n  NULL 1 -- random sets from the actual space (seed 0)")
    rng = np.random.default_rng(SEED_RANDOM)
    for _low, _high, label in STRATA:
        got = [sizes[n] for n in parents if stratum_of(sizes[n]) == label]
        if not got:
            continue
        draws = [
            cohesion(space[rng.choice(len(space), size=min(s, len(space)), replace=False)])
            for s in rng.choice(got, size=DRAWS_PER_STRATUM)
        ]
        print(f"    {label:<9} median {statistics.median(draws):>7.3f}  "
              f"sd {statistics.pstdev(draws):>6.3f}")
    leaf_draws = [
        cohesion(space[rng.choice(len(space), size=sizes[n], replace=False)])
        for n in leaves
        for _ in range(DRAWS_PER_LEAF)
    ]
    print(f"    per-leaf ({DRAWS_PER_LEAF} draws each): median "
          f"{statistics.median(leaf_draws):.3f}, sd {statistics.pstdev(leaf_draws):.3f}")

    print("\n  NULL 2 -- kNN balls (seed 1)")
    rng = np.random.default_rng(SEED_BALLS)
    print(f"    {'members':<9} {'ball p5':>8} {'ball med':>9} {'themes p10':>11} "
          f"{'themes med':>11} {'below p5':>14}")
    for _low, _high, label in STRATA:
        got = [n for n in parents if stratum_of(sizes[n]) == label]
        if not got:
            continue
        pool = [sizes[n] for n in got]
        balls = []
        for size in rng.choice(pool, size=BALLS_PER_STRATUM):
            centre = int(rng.integers(len(space)))
            order = np.argsort(-(space @ space[centre]))[:size]
            balls.append(cohesion(space[order]))
        vals = [coh[n] for n in got]
        p5 = percentile(balls, 5)
        below = sum(1 for v in vals if v < p5)
        print(f"    {label:<9} {p5:>8.3f} {statistics.median(balls):>9.3f} "
              f"{percentile(vals, 10):>11.3f} {statistics.median(vals):>11.3f} "
              f"{f'{below} of {len(vals)}':>14}")

    print(f"\n  THE {args.roots} LARGEST ROOTS")
    print(f"    {'root':<10} {'members':>9} {'children':>9} {'cohesion':>9} "
          f"{'ball p5':>9} {'ball med':>9}")
    rng = np.random.default_rng(SEED_BALLS)
    for node in sorted(roots, key=lambda n: -sizes[n])[: args.roots]:
        size = sizes[node]
        balls = []
        for _ in range(BALLS_PER_STRATUM):
            centre = int(rng.integers(len(space)))
            order = np.argsort(-(space @ space[centre]))[:size]
            balls.append(cohesion(space[order]))
        print(f"    {node:<10} {size:>9,} {len(kids.get(node, [])):>9} {coh[node]:>9.3f} "
              f"{percentile(balls, 5):>9.3f} {statistics.median(balls):>9.3f}")

    print(f"\n  WHAT A CUT AT COHESION < {PROPOSED_CUT} WOULD DO")
    for label, directory in ((args.compare, args.compare), (args.build, args.build)):
        ps, ms = load_build(root / directory)
        ks: dict[str, list[str]] = defaultdict(list)
        for node, pl in ps.items():
            for parent in pl:
                ks[parent].append(node)
        cc = {n: cohesion(space[[index[k] for k in ms[n] if k in index]]) for n in ps}
        cut = [n for n in ps if cc[n] < PROPOSED_CUT]
        kept = {n for n in ps if n not in cut}
        homeless = {k for n in cut for k in ms[n]} - {k for n in kept for k in ms[n]}
        roots_after = sum(1 for n in kept if not [p for p in ps[n] if p in kept])
        print(f"    {label}")
        print(f"      removed {len(cut)}; roots among them "
              f"{sum(1 for n in cut if not ps[n])}; "
              f"every theme >= 200 members "
              f"{sum(1 for n in cut if len(ms[n]) >= 200)} of "
              f"{sum(1 for n in ps if len(ms[n]) >= 200)}")
        print(f"      leaves among them {sum(1 for n in cut if not ks.get(n))}; "
              f"roots after removal {sum(1 for n in ps if not ps[n])} -> {roots_after}; "
              f"pathways losing their only home {len(homeless)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
