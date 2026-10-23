"""PART 2 section C of prompt 55: duplication in S2 and O50s, by the same code.

Declared 22 Oct 2026. Evaluation only; nothing is adopted. The judgement rule is the reviewer's to
apply, not this script's.

Two measures, both on each build's own final DAG:

1. **Non-nested pairs at J >= 0.5 that remain**, by band, and how many of them are NOT siblings.
   Sibling means sharing at least one immediate parent, or both being roots -- the same definition
   the S2 build used, taken from ``build_s2.sibling_predicate`` rather than reimplemented. A pair is
   banded by the LARGER of the two themes, stated here because the choice changes the table.
2. **Nodes at least 80% inside another node without being its descendant**, binned by how many of
   the node's pathways the container is missing (0, 1-5, 6-20, 21+). A node is counted once, in the
   bin of its BEST qualifying container -- the one missing fewest of its pathways -- because the
   question is whether a node is near-contained somewhere, not how many places it is near-contained
   in. The pair count is reported beside it so both readings are available.

   "Descendant" is transitive, not just an immediate edge: a node sitting under a container by a
   chain of edges is properly placed and must not be counted as duplication.

No existing script covers either measure for these builds; both are computed here.

Usage:
    uv run scripts/s2_duplication.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)

#: Bins for how many of a node's pathways its best container is missing.
MISSING_BINS: tuple[tuple[int, int, str], ...] = (
    (0, 0, "0"), (1, 5, "1-5"), (6, 20, "6-20"), (21, 10**9, "21+"),
)

NEAR_SHARE = 0.80
PAIR_JACCARD = 0.50


def band_of(size: int, bands: tuple[tuple[int, int, str], ...]) -> str:
    """The band a value falls in.

    Args:
        size: The value.
        bands: Band edges.

    Returns:
        Band label.
    """
    for low, high, name in bands:
        if low <= size <= high:
            return name
    return bands[0][2]


def read_build(directory: Path) -> dict[str, object]:
    """Node ids, memberships and immediate parents.

    Args:
        directory: A build directory.

    Returns:
        ``{ids, members, parents}``.
    """
    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    parents = {r["node"]: tuple(p for p in (r["parents"] or "").split() if p) for r in rows}
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return {"ids": [r["node"] for r in rows], "members": dict(members), "parents": parents}


def ancestors_of(ids: Sequence[str], parents: Mapping[str, tuple[str, ...]]
                 ) -> dict[str, frozenset[str]]:
    """Every node above each node, transitively.

    Args:
        ids: Node ids.
        parents: Immediate parents per node.

    Returns:
        Node to the set of all its ancestors.
    """
    done: dict[str, frozenset[str]] = {}

    def climb(node: str) -> frozenset[str]:
        """All ancestors of one node."""
        if node in done:
            return done[node]
        done[node] = frozenset()                      # guard against a cycle
        got: set[str] = set()
        for parent in parents[node]:
            got.add(parent)
            got |= climb(parent)
        done[node] = frozenset(got)
        return done[node]

    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, len(ids) + 1000))
    try:
        for node in ids:
            climb(node)
    finally:
        sys.setrecursionlimit(old)
    return done


def duplication(name: str, build: dict[str, object], index: Mapping[str, int],
                width: int, n: int) -> dict[str, object]:
    """Both measures for one build.

    Args:
        name: Build label.
        build: A read build.
        index: Pathway key to universe position.
        width: Bitset width in bits.
        n: Universe size.

    Returns:
        The counts.
    """
    from build_s2 import sibling_predicate
    from thema.ontology import bitset as bits

    ids = build["ids"]
    members = build["members"]
    parents = build["parents"]
    stack = np.vstack([
        bits.pack(sorted(index[k] for k in members.get(node, ())), width)[None, :]
        for node in ids])
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    same = sibling_predicate([stack[i] for i in range(len(ids))], n)
    above = ancestors_of(ids, parents)

    pair_bands: dict[str, int] = defaultdict(int)
    pair_nonsib: dict[str, int] = defaultdict(int)
    near_pairs = 0
    near_best: dict[int, int] = {}

    for row in range(len(ids)):
        mine = stack[row]
        inter = np.bitwise_count(mine[None, :] & stack).sum(axis=1).astype(np.int64)
        union = sizes[row] + sizes - inter
        jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)

        # 1. non-nested pairs at or above the cutoff, counted once per pair (row < other)
        nested = (inter == sizes[row]) | (inter == sizes)
        hits = np.flatnonzero((jac >= PAIR_JACCARD) & ~nested)
        for other in hits.tolist():
            if other <= row:
                continue
            band = band_of(int(max(sizes[row], sizes[other])), BANDS)
            pair_bands[band] += 1
            if not same(row, other):
                pair_nonsib[band] += 1

        # 2. near-containment in a node that is not an ancestor
        missing = sizes[row] - inter
        bigger = sizes > sizes[row]
        qualifies = bigger & (inter >= NEAR_SHARE * sizes[row])
        cand = np.flatnonzero(qualifies)
        if not len(cand):
            continue
        mine_above = above[ids[row]]
        keep = [c for c in cand.tolist() if ids[c] not in mine_above]
        if not keep:
            continue
        near_pairs += len(keep)
        near_best[row] = int(min(missing[c] for c in keep))

    bins: dict[str, int] = defaultdict(int)
    for gap in near_best.values():
        bins[band_of(gap, MISSING_BINS)] += 1
    return {
        "name": name, "themes": len(ids),
        "pair_bands": dict(pair_bands), "pair_nonsib": dict(pair_nonsib),
        "pairs": sum(pair_bands.values()), "pairs_nonsib": sum(pair_nonsib.values()),
        "near_nodes": len(near_best), "near_pairs": near_pairs,
        "near_bins": dict(bins),
    }


def main(argv: list[str] | None = None) -> int:
    """Print section C for S2 and O50s.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.ontology import bitset as bits
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
    width = bits.words_for(len(keys)) * bits.WORD

    print("PROMPT 55 PART 2, SECTION C: DUPLICATION. S2 and O50s, same code.")
    print("Sections E, F and G are not run: the full PART 2 estimate was about 4 h 30 against a")
    print("5 h ceiling for the whole prompt, and the prompt's instruction in that case is PART 1")
    print("plus the cheapest of PART 2. C is the cheapest.")
    print()
    got = []
    for name, path in (("O50s", args.o50s), ("S2", args.s2)):
        got.append(duplication(name, read_build(path), index, width, len(keys)))
        print(f"  {name} done", flush=True)
    print()

    print("=" * 100)
    print("C1. NON-NESTED PAIRS AT J >= 0.5 THAT REMAIN, by the band of the LARGER theme")
    print("=" * 100)
    print(f"  {'band':<12}" + "".join(f"{g['name'] + ' pairs':>16}{'non-sib':>11}" for g in got))
    for _low, _high, band in BANDS:
        if not any(g["pair_bands"].get(band) for g in got):
            continue
        line = f"  {band:<12}"
        for g in got:
            total = g["pair_bands"].get(band, 0)
            nons = g["pair_nonsib"].get(band, 0)
            line += f"{total:>16,}{nons:>11,}"
        print(line)
    line = f"  {'ALL':<12}"
    for g in got:
        line += f"{g['pairs']:>16,}{g['pairs_nonsib']:>11,}"
    print(line)
    print(f"  {'non-sibling share':<12}" + "".join(
        f"{f'{g['pairs_nonsib'] / g['pairs']:.1%}' if g['pairs'] else '-':>27}" for g in got))
    print()

    print("=" * 100)
    print("C2. NODES AT LEAST 80% INSIDE ANOTHER NODE WITHOUT BEING ITS DESCENDANT")
    print("=" * 100)
    print("  binned by how many of the node's pathways its BEST such container is missing")
    print(f"  {'pathways missing':<20}" + "".join(f"{g['name']:>14}" for g in got))
    for _low, _high, name in MISSING_BINS:
        print(f"  {name:<20}" + "".join(f"{g['near_bins'].get(name, 0):>14,}" for g in got))
    print(f"  {'NODES':<20}" + "".join(f"{g['near_nodes']:>14,}" for g in got))
    print(f"  {'  share of themes':<20}" + "".join(
        f"{g['near_nodes'] / g['themes']:>14.1%}" for g in got))
    print(f"  {'PAIRS':<20}" + "".join(f"{g['near_pairs']:>14,}" for g in got))
    print()
    (args.out / "section_c.json").write_text(json.dumps(got, indent=1) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'section_c.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
