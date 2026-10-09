#!/usr/bin/env python3
"""Report the re-gate grid: six arms side by side, on the DAG each one actually built.

The grid crosses three match thresholds with two floor rules, so every pair of arms differs in
exactly one thing. What it is looking for is the middle of the hierarchy: themes of 51-1000 members,
and whether they are coherent or merely numerous.

Two measurements here are about SHAPE rather than score, and they are the ones that decide whether a
new middle is real:

- **children after collapsing** a child that holds more than 70% of its parent. A child that large
  is the same group with something added, so counting it as a branch makes a long absorption chain
  look like a wide, well-structured node. Collapsing lifts its children into the parent, and the
  maximum is then the length of the worst chain. This is computed on the **built DAG**, where a node
  may have several parents -- not on a binary tree.
- **leaves by the largest theme of 1,000 or fewer they reach**. If every leaf's largest sub-1000
  theme is already in the 301-1000 band, there is no middle to place anything in.

Gene coherence is against a **size-matched** null, because mean pairwise overlap rises with set size
on its own. Curated recall is reported as SECONDARY, per the 8 Oct decision that independent
coherence is primary.

Usage::

    uv run scripts/regate_report.py --arm L=thema_L --arm L_cal=thema_L_cal ...
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.pathways import PathwayCollection
from thema.ontology.universe import load_embedded

#: Size bands the grid reports, plus 6-9 which the clarification asks for separately.
BANDS: tuple[tuple[int, int], ...] = (
    (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 300), (301, 1000), (1001, 10**9))
#: The clarification's extra band: the 0.33 minimum overrode the 6-6 and 7-9 floors too.
EXTRA_BANDS: tuple[tuple[int, int], ...] = ((3, 10), (6, 9), (51, 1000))
CHAIN_SHARE = 0.70
COHERENCE_SAMPLE = 150
NULL_DRAWS = 10
MAX_PAIRS = 4000
PLACEMENT_CAP = 1000
EXAMPLES = 5
EXAMPLE_FROM = 51
SEED = 0


def label(low: int, high: int) -> str:
    """Band label.

    Args:
        low: Lower bound.
        high: Upper bound.

    Returns:
        The label.
    """
    return f"{low}-{high}" if high < 10**9 else f"{low}+"


def band_of(size: int) -> str:
    """Band label for a theme size.

    Args:
        size: Member count.

    Returns:
        The label, or ``"other"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return label(low, high)
    return "other"


def read_build(path: Path) -> tuple[dict[str, list[str]], dict[str, set[str]]]:
    """Members and parent edges of a built ontology.

    Args:
        path: A built ontology directory.

    Returns:
        ``(node -> member keys, child -> parents)``.
    """
    members: dict[str, list[str]] = defaultdict(list)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    parents: dict[str, set[str]] = defaultdict(set)
    if (path / "edges.tsv").is_file():
        with (path / "edges.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                parents[row["child"]].add(row["parent"])
    return members, parents


def collapsed_children(members: dict[str, list[str]],
                       parents: dict[str, set[str]]) -> dict[str, list[str]]:
    """Children per node on the DAG, with chain links collapsed.

    Args:
        members: Node to member keys.
        parents: Child to parents.

    Returns:
        Node to its children after collapsing.
    """
    children: dict[str, list[str]] = defaultdict(list)
    for child, ups in parents.items():
        for parent in ups:
            children[parent].append(child)
    sizes = {node: len(keys) for node, keys in members.items()}
    out: dict[str, list[str]] = {}
    for node, kids in children.items():
        collected: list[str] = []
        frontier = list(kids)
        seen: set[str] = set()
        while frontier:
            kid = frontier.pop()
            if kid in seen:
                continue
            seen.add(kid)
            if children.get(kid) and sizes.get(kid, 0) > CHAIN_SHARE * sizes.get(node, 1):
                frontier.extend(children[kid])
            else:
                collected.append(kid)
        out[node] = collected
    return out


def collapse_near_copies(members: dict[str, list[str]],
                         parents: dict[str, set[str]]) -> set[str]:
    """Which themes survive after near-copies are merged into their parents.

    Declared 8 Oct 2026 **before any structure result was read**. A child holding more than
    ``CHAIN_SHARE`` of its parent's members is the same theme with a little added, not a distinct
    one, so a build that splits one theme into a chain of near-copies gets a large raw theme count
    for no extra structure. **Arms are ranked on the collapsed count, not the raw count** -- the
    same flaw the one-linkage step 1 criterion had when it counted raw tree nodes.

    Removal is iterated to a fixed point, because collapsing a near-copy can leave its own child
    a near-copy of the surviving parent. Edges are strict containment, so a child is always a
    subset of its parent and the share is just the size ratio.

    Args:
        members: Node to member keys.
        parents: Child to parents.

    Returns:
        The surviving node ids.
    """
    sizes = {node: len(keys) for node, keys in members.items()}
    alive = set(members)
    children: dict[str, set[str]] = defaultdict(set)
    for child, ups in parents.items():
        for parent in ups:
            children[parent].add(child)
    up: dict[str, set[str]] = {node: set(parents.get(node, ())) for node in members}

    changed = True
    while changed:
        changed = False
        for node in sorted(alive, key=lambda x: sizes[x], reverse=True):
            if node not in alive:
                continue
            doomed = [p for p in up.get(node, ()) if p in alive
                      and sizes[node] > CHAIN_SHARE * sizes[p]]
            if not doomed:
                continue
            keeper = max(doomed, key=lambda x: sizes[x])
            alive.discard(node)
            # The collapsed node's children become the keeper's, so a chain keeps collapsing.
            for kid in children.get(node, ()):
                if kid in alive:
                    up.setdefault(kid, set()).add(keeper)
                    children[keeper].add(kid)
            changed = True
    return alive


def near_duplicate_share(members: dict[str, list[str]], threshold: float = 0.7) -> float:
    """Share of themes whose most similar other theme exceeds a Jaccard threshold.

    Declared 8 Oct 2026 before any structure result was read. Computed from an inverted index, so
    only themes sharing at least one member are ever compared -- a full pairwise sweep over eleven
    thousand themes would be the expensive way to get the same answer.

    Args:
        members: Node to member keys.
        threshold: The Jaccard above which two themes count as near-duplicates.

    Returns:
        The share, or 0.0 when there are fewer than two themes.
    """
    order = sorted(members)
    sets = [set(members[n]) for n in order]
    if len(sets) < 2:
        return 0.0
    holders: dict[str, list[int]] = defaultdict(list)
    for index, keys in enumerate(sets):
        for key in keys:
            holders[key].append(index)
    hit = 0
    for index, keys in enumerate(sets):
        best = 0.0
        for other in {o for k in keys for o in holders[k]}:
            if other == index:
                continue
            inter = len(keys & sets[other])
            union = len(keys) + len(sets[other]) - inter
            if union:
                best = max(best, inter / union)
                if best > threshold:
                    break
        if best > threshold:
            hit += 1
    return round(hit / len(sets), 4)


def mean_pair_jaccard(keys: list[str], genes: dict[str, frozenset[str]],
                      rng: np.random.Generator) -> float | None:
    """Mean pairwise gene Jaccard over a theme's members.

    Args:
        keys: Member pathway keys.
        genes: Pathway key to gene set.
        rng: For sampling pairs in a large theme.

    Returns:
        The mean, or None if fewer than two members carry genes.
    """
    have = [k for k in keys if genes.get(k)]
    if len(have) < 2:
        return None
    total = len(have) * (len(have) - 1) // 2
    if total <= MAX_PAIRS:
        pairs = list(itertools.combinations(have, 2))
    else:
        left = rng.integers(0, len(have), MAX_PAIRS)
        right = rng.integers(0, len(have), MAX_PAIRS)
        pairs = [(have[i], have[j]) for i, j in zip(left, right, strict=True) if i != j]
    if not pairs:
        return None
    values = []
    for a, b in pairs:
        ga, gb = genes[a], genes[b]
        union = len(ga | gb)
        values.append(len(ga & gb) / union if union else 0.0)
    return float(np.mean(values))


def coherence(members: dict[str, list[str]], genes: dict[str, frozenset[str]],
              pool: list[str]) -> dict[str, dict]:
    """Mean pairwise gene Jaccard per band against a size-matched null.

    Args:
        members: Node to member keys.
        genes: Pathway key to gene set.
        pool: Every pathway key in the universe, to draw the null from.

    Returns:
        Per band, observed, null and ratio.
    """
    rng = np.random.default_rng(SEED)
    by_band: dict[str, list[str]] = defaultdict(list)
    for node, keys in members.items():
        by_band[band_of(len(keys))].append(node)
    out: dict[str, dict] = {}
    for low, high in BANDS:
        band = label(low, high)
        nodes = sorted(by_band.get(band, []))
        if not nodes:
            continue
        pick = ([nodes[i] for i in rng.choice(len(nodes), COHERENCE_SAMPLE, replace=False)]
                if len(nodes) > COHERENCE_SAMPLE else nodes)
        real, null = [], []
        for node in pick:
            got = mean_pair_jaccard(members[node], genes, rng)
            if got is None:
                continue
            real.append(got)
            draws = []
            for _ in range(NULL_DRAWS):
                sample = [pool[i] for i in
                          rng.choice(len(pool), len(members[node]), replace=False)]
                value = mean_pair_jaccard(sample, genes, rng)
                if value is not None:
                    draws.append(value)
            if draws:
                null.append(float(np.mean(draws)))
        if not real or not null:
            continue
        r, u = float(np.mean(real)), float(np.mean(null))
        out[band] = {"n_nodes": len(nodes), "n_sampled": len(real),
                     "observed": round(r, 5), "null": round(u, 5),
                     "ratio": round(r / u, 2) if u else None}
    return out


def main(argv: list[str] | None = None) -> int:
    """Report every arm of the grid.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--arm", action="append", default=[])
    parser.add_argument("--reference", default="L")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    names = {p.key: p.name for p in collection.pathways}
    sources = {p.key: p.source for p in collection.pathways}

    report: dict[str, object] = {"bands": [list(b) for b in BANDS],
                                 "chain_share": CHAIN_SHARE, "seed": SEED, "arms": {}}
    rng = np.random.default_rng(SEED)

    for spec in args.arm:
        name, _, where = spec.partition("=")
        path = root / where
        if not (path / "members.tsv").is_file():
            print(f"{name}: no build at {path}")
            continue
        members, parents = read_build(path)
        sizes = {node: len(k) for node, k in members.items()}
        counts = Counter(band_of(s) for s in sizes.values())
        extra = {label(lo, hi): sum(1 for s in sizes.values() if lo <= s <= hi)
                 for lo, hi in EXTRA_BANDS}

        survivors = collapse_near_copies(members, parents)
        collapsed_counts = Counter(band_of(sizes[n]) for n in survivors)
        collapsed_extra = {label(lo, hi): sum(1 for n in survivors if lo <= sizes[n] <= hi)
                           for lo, hi in EXTRA_BANDS}
        collapsed = collapsed_children(members, parents)
        kid_counts = [len(v) for v in collapsed.values() if v]
        raw = defaultdict(int)
        for ups in parents.values():
            for parent in ups:
                raw[parent] += 1
        roots = sorted((n for n in members if not parents.get(n)),
                       key=lambda n: -sizes[n])
        root_children = [len(collapsed.get(r, [])) for r in roots]

        best = {}
        for node, size in sorted(sizes.items(), key=lambda kv: -kv[1]):
            if size > PLACEMENT_CAP:
                continue
            for key in members[node]:
                if key not in best:
                    best[key] = size
        placement = Counter(band_of(best[k]) if k in best else "none" for k in keys)

        manifest = json.loads((path / "manifest.json").read_text())
        floors = manifest.get("floors") or []
        entry: dict[str, object] = {
            "path": str(path), "themes": len(members),
            "theta_match": manifest.get("theta_match"),
            "match_split": manifest.get("match_split"),
            "floors_source": manifest.get("floors_source"),
            "effective_floors": {e.get("stratum"): e.get("effective") for e in floors},
            "bands": {label(lo, hi): counts.get(label(lo, hi), 0) for lo, hi in BANDS},
            "extra_bands": extra,
            "themes_after_collapse": len(survivors),
            "bands_collapsed": {label(lo, hi): collapsed_counts.get(label(lo, hi), 0)
                                for lo, hi in BANDS},
            "extra_bands_collapsed": collapsed_extra,
            "near_duplicate_share": near_duplicate_share(members),
            "n_roots": len(roots),
            "root_sizes": [sizes[r] for r in roots[:12]],
            "root_children": sorted(root_children, reverse=True)[:12],
            "root_children_max": max(root_children) if root_children else 0,
            "children_median_raw": float(np.median(list(raw.values()))) if raw else None,
            "children_median_collapsed": float(np.median(kid_counts)) if kid_counts else None,
            "children_max_collapsed": int(max(kid_counts)) if kid_counts else 0,
            "n_over_30_children": sum(1 for c in kid_counts if c > 30),
            "multi_parent_share": round(
                sum(1 for n in members if len(parents.get(n, ())) > 1) / len(members), 4),
            "n_effectively_unplaced": manifest.get("n_effectively_unplaced"),
            "build_seconds": manifest.get("seconds"),
            "leaf_placement": dict(sorted(placement.items())),
            "coherence": coherence(members, genes, keys),
        }
        examples: dict[str, list] = {}
        for low, high in BANDS:
            if high < EXAMPLE_FROM:
                continue
            band = label(low, high)
            nodes = sorted(n for n, s in sizes.items() if band_of(s) == band)
            if not nodes:
                continue
            pick = [nodes[i] for i in rng.choice(len(nodes), min(EXAMPLES, len(nodes)),
                                                 replace=False)]
            examples[band] = [
                {"node": n, "size": sizes[n],
                 "sources": dict(sorted(Counter(sources.get(k, "?")
                                                for k in members[n]).items())),
                 "members": [names.get(k, k) for k in members[n][:10]]}
                for n in pick]
        entry["examples"] = examples
        report["arms"][name] = entry
        print(f"  {name:<10} raw {len(members):>6,} -> collapsed {len(survivors):>6,}  "
              f"51-1000 {extra['51-1000']:>5,} -> {collapsed_extra['51-1000']:>5,}  "
              f"near-dup {entry['near_duplicate_share']:>6.1%}  "
              f"roots {len(roots):>4}  max children {entry['children_max_collapsed']:>4}",
              flush=True)

    ref = report["arms"].get(args.reference)
    for which, bands_key, extra_key in (
            ("RAW", "bands", "extra_bands"),
            ("AFTER COLLAPSING NEAR-COPIES -- arms are ranked on THIS", "bands_collapsed",
             "extra_bands_collapsed")):
        print()
        print(f"  {which}")
        header = f"  {'arm':<10}{'themes':>8}{'51-1000':>9}{'3-10':>7}{'vs L':>7}{'6-9':>6}"
        for low, high in BANDS:
            header += f"{label(low, high):>9}"
        print(header)
        for name, entry in report["arms"].items():
            total = (entry["themes"] if bands_key == "bands"
                     else entry["themes_after_collapse"])
            share = (f"{100 * entry[extra_key]['3-10'] / ref[extra_key]['3-10']:.0f}%"
                     if ref and ref[extra_key]["3-10"] else "-")
            line = (f"  {name:<10}{total:>8,}{entry[extra_key]['51-1000']:>9,}"
                    f"{entry[extra_key]['3-10']:>7,}{share:>7}{entry[extra_key]['6-9']:>6,}")
            for low, high in BANDS:
                line += f"{entry[bands_key][label(low, high)]:>9,}"
            print(line)
    print()
    print(f"  {'arm':<10}{'near-duplicate share (max Jaccard to another theme > 0.7)':>58}")
    for name, entry in report["arms"].items():
        print(f"  {name:<10}{entry['near_duplicate_share']:>58.1%}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
