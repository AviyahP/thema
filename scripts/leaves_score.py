#!/usr/bin/env python3
"""Score the leaves experiment: do themes built from atomic pathways recreate the summaries?

The answer key is the summaries themselves. Every pathway removed from the universe has a target --
its leaf descendants in L -- and a build scores by whether some theme matches that target. The
curated hierarchy is the judge, never an input: no arm sees the relation files.

Everything the spec declares, in its order:

- **primary**: recall and precision of targets per band and source at Jaccard > 0.5, with a cluster
  bootstrap over targets (1,000 resamples, seed 0);
- **near-pair agreement** among leaves (clarification 10) with a labels-shuffled null;
- **matched theme count**, L cut by support to the chosen HiDeF's count;
- **shape** per arm;
- **named case**, Reactome "Signaling by Receptor Tyrosine Kinases";
- **scatter**, how many distinct root themes an internal pathway's leaves fall under;
- **placement layer** (display only), each summary attached to its best-Jaccard theme.

Decisions use the TUNING half; the report uses the TEST half. Usage::

    uv run scripts/leaves_score.py --half tuning --arm L=thema_L ...
    uv run scripts/leaves_score.py --half test --out OUT.json --arm L=thema_L ...
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection, partition_universe
from thema.ontology.evalsets import PRIMARY_RELATIONS, SECONDARY_RELATIONS, go_edges
from thema.ontology.leaves import internal, targets
from thema.ontology.universe import load_embedded

#: Target-size bands, including the 201-500 band the spec adds for leaf sets.
BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))
MATCH = 0.5
BOOTSTRAP = 1000
BOOT_SEED = 0
MARGIN = 0.02
#: The named case the spec calls out.
NAMED_CASE = "reactome:R-HSA-9006934"
NAMED_CHILD = "reactome:R-HSA-1433557"
#: Near-pair thresholds, clarification 10.
NEAR_T = (10, 50)


def band_of(size: int) -> str:
    """Band label for a target size.

    Args:
        size: Leaf count.

    Returns:
        The label, or ``"other"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "other"


def read_build(path: Path, index_of: dict[str, int]) -> tuple[list[set[int]], list[float]]:
    """Theme member index sets and supports for one build.

    Args:
        path: A built ontology directory.
        index_of: Pathway key to L row index.

    Returns:
        ``(member sets, supports)``.
    """
    members: dict[str, set[int]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["key"] in index_of:
                members[row["node"]].add(index_of[row["key"]])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            node = row.get("node") or row.get("id")
            support[node] = float(row.get("support") or 1.0)
    order = sorted(members)
    return [members[k] for k in order], [support.get(k, 1.0) for k in order]


def roots_of(path: Path) -> dict[str, set[str]]:
    """Each node's root ancestors.

    Args:
        path: A built ontology directory.

    Returns:
        Node id to the set of root ids above it.
    """
    parents: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            nodes.add(row["node"])
    if (path / "edges.tsv").is_file():
        with (path / "edges.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                parents[row["child"]].add(row["parent"])
    memo: dict[str, set[str]] = {}

    def climb(node: str, seen: frozenset[str]) -> set[str]:
        """Root ancestors of one node."""
        if node in memo:
            return memo[node]
        ups = [p for p in parents.get(node, ()) if p not in seen]
        memo[node] = {node} if not ups else set().union(
            *(climb(p, seen | {node}) for p in ups))
        return memo[node]

    sys.setrecursionlimit(100000)
    return {node: climb(node, frozenset()) for node in nodes}


def match_matrix(themes: list[set[int]], sets: list[set[int]], n: int) -> sparse.csr_matrix:
    """Themes by targets, 1 where the Jaccard exceeds :data:`MATCH`.

    Args:
        themes: Theme member index sets.
        sets: Target leaf sets.
        n: Size of L.

    Returns:
        A ``(themes, targets)`` sparse 0/1 matrix.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(sets):
        for member in members:
            holders[member].append(index)
    rows, cols = [], []
    for position, members in enumerate(themes):
        for candidate in {c for m in members for c in holders[m]}:
            other = sets[candidate]
            inter = len(members & other)
            if inter and inter / (len(members) + len(other) - inter) > MATCH:
                rows.append(position)
                cols.append(candidate)
    return sparse.csr_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, cols)),
        shape=(max(len(themes), 1), max(len(sets), 1)))


def best_jaccard(themes: list[set[int]], sets: list[set[int]], n: int) -> np.ndarray:
    """The highest Jaccard any theme reaches with each target.

    Args:
        themes: Theme member index sets.
        sets: Target leaf sets.
        n: Size of L.

    Returns:
        One best Jaccard per target.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(themes):
        for member in members:
            holders[member].append(index)
    out = np.zeros(len(sets), dtype=np.float64)
    for position, members in enumerate(sets):
        best = 0.0
        for candidate in {c for m in members for c in holders[m]}:
            other = themes[candidate]
            inter = len(members & other)
            best = max(best, inter / (len(members) + len(other) - inter))
        out[position] = best
    return out


def cells(themes: list[set[int]], sets: list[set[int]], set_bands: list[str],
          theme_bands: list[str], n: int) -> dict:
    """Per-band recall and precision with a target cluster bootstrap.

    Args:
        themes: Theme member index sets.
        sets: Target leaf sets for one source and half.
        set_bands: Band per target.
        theme_bands: Band per theme.
        n: Size of L.

    Returns:
        Per band, the point estimates and the bootstrap percentile interval.
    """
    matrix = match_matrix(themes, sets, n)
    hit = np.asarray(matrix.sum(axis=0)).ravel() > 0
    rng = np.random.default_rng(BOOT_SEED)
    draws = [rng.integers(0, max(len(sets), 1), size=max(len(sets), 1))
             for _ in range(BOOTSTRAP)]
    out: dict[str, dict] = {}
    for low, high in BANDS:
        band = f"{low}-{high}"
        s_idx = np.array([i for i, b in enumerate(set_bands) if b == band], dtype=np.int64)
        t_idx = np.array([i for i, b in enumerate(theme_bands) if b == band], dtype=np.int64)
        recall = float(hit[s_idx].mean()) if len(s_idx) else None
        precision = (float((np.asarray(matrix[t_idx].sum(axis=1)).ravel() > 0).mean())
                     if len(t_idx) else None)
        r_boot, p_boot = [], []
        for drawn in draws:
            if len(s_idx):
                keep = drawn[np.isin(drawn, s_idx)]
                r_boot.append(float(hit[keep].mean()) if len(keep) else np.nan)
            if len(t_idx):
                mult = np.bincount(drawn, minlength=matrix.shape[1])
                p_boot.append(float((np.asarray(matrix[t_idx] @ mult).ravel() > 0).mean()))
        out[band] = {
            "recall": None if recall is None else round(recall, 4),
            "precision": None if precision is None else round(precision, 4),
            "recall_ci": ([round(float(np.nanpercentile(r_boot, 2.5)), 4),
                           round(float(np.nanpercentile(r_boot, 97.5)), 4)] if r_boot else None),
            "precision_ci": ([round(float(np.nanpercentile(p_boot, 2.5)), 4),
                              round(float(np.nanpercentile(p_boot, 97.5)), 4)]
                             if p_boot else None),
            "n_targets": int(len(s_idx)), "n_themes": int(len(t_idx)),
            "recall_draws": [round(v, 6) for v in r_boot] if r_boot else None,
        }
    return out


def near_pairs(themes: list[set[int]], sets: list[set[int]], n: int, seed: int) -> dict:
    """Clarification 10's near-pair agreement among leaves, with a shuffled null.

    Args:
        themes: Theme member index sets.
        sets: Target leaf sets.
        n: Size of L.
        seed: RNG seed for the null.

    Returns:
        Recall and precision at each threshold, and the null.
    """
    def smallest(sets_in: list[set[int]]) -> dict[tuple[int, int], int]:
        """Smallest containing set size per co-occurring pair."""
        out: dict[tuple[int, int], int] = {}
        for members in sorted(sets_in, key=len):
            ordered = sorted(members)
            size = len(ordered)
            for i, a in enumerate(ordered):
                for b in ordered[i + 1:]:
                    out.setdefault((a, b), size)
        return out

    curated = smallest([s for s in sets if len(s) <= 200])
    built = smallest([t for t in themes if len(t) <= 200])
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    shuffled = {(min(int(perm[a]), int(perm[b])), max(int(perm[a]), int(perm[b]))): v
                for (a, b), v in built.items()}
    out: dict[str, dict] = {}
    for threshold in NEAR_T:
        near = {p for p, size in curated.items() if size <= threshold}
        got = {p for p, size in built.items() if size <= threshold}
        null = {p for p, size in shuffled.items() if size <= threshold}
        out[f"T{threshold}"] = {
            "n_near": len(near),
            "recall": round(len(near & got) / len(near), 4) if near else None,
            "precision": round(len(near & got) / len(got), 4) if got else None,
            "null_recall": round(len(near & null) / len(near), 4) if near else None,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Score every arm on one half.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from thema.ontology.evalsets import split_half

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--half", choices=("tuning", "test", "all"), default="test")
    parser.add_argument("--relations", choices=("primary", "secondary"), default="primary")
    parser.add_argument("--arm", action="append", default=[],
                        help="NAME=DIRECTORY, relative to the versioned ontology directory")
    parser.add_argument("--reference", default="L")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    index_of = {key: i for i, key in enumerate(keys)}
    n = len(keys)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    kept, _excluded = partition_universe(collection)
    full = {p.key for p in kept}
    sources = {p.key: p.source for p in collection.pathways}
    names = {p.key: p.name for p in collection.pathways}

    relations = PRIMARY_RELATIONS if args.relations == "primary" else SECONDARY_RELATIONS
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {f"reactome:{c}": {f"reactome:{p}" for p in ps}
                                  for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(), relations).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}

    marked = internal(edges, full)
    key_sets = targets(edges, marked, keys, min_size=3)
    target_keys = sorted(key_sets)
    sets = [{index_of[k] for k in key_sets[tk]} for tk in target_keys]
    set_bands = [band_of(len(s)) for s in sets]
    in_band = [i for i, b in enumerate(set_bands) if b != "other"]
    tuning, test = split_half([sets[i] for i in in_band], [set_bands[i] for i in in_band], seed=0)
    chosen = {"tuning": tuning, "test": test,
              "all": list(range(len(in_band)))}[args.half]
    picked = [in_band[i] for i in chosen]

    print(f"LEAVES SCORING  half={args.half}, GO relations={args.relations}, n(L)={n:,}")
    print(f"  summaries removed: {len(marked):,}; with >= 3 leaves in L: {len(target_keys):,}; "
          f"in a band: {len(in_band):,}; this half: {len(picked):,}")
    by_source: dict[str, list[int]] = defaultdict(list)
    for i in picked:
        by_source[sources.get(target_keys[i], "?")].append(i)
    for source, idx in sorted(by_source.items()):
        counts: dict[str, int] = defaultdict(int)
        for i in idx:
            counts[set_bands[i]] += 1
        print(f"    {source:<10} {len(idx):>5,} targets  "
              + "  ".join(f"{b}:{counts[b]}" for b in (f"{lo}-{hi}" for lo, hi in BANDS)))

    report: dict[str, object] = {
        "half": args.half, "relations": args.relations, "n_leaves": n,
        "bootstrap": BOOTSTRAP, "seed": BOOT_SEED, "match": MATCH, "margin": MARGIN,
        "n_summaries": len(marked), "n_targets_scored": len(picked), "arms": {},
    }

    for spec in args.arm:
        name, _, where = spec.partition("=")
        path = root / where
        if not (path / "members.tsv").is_file():
            print(f"  {name}: no build at {path}")
            continue
        themes, supports = read_build(path, index_of)
        theme_bands = [band_of(len(t)) for t in themes]
        entry: dict[str, object] = {"themes": len(themes), "path": str(path)}
        for source, idx in sorted(by_source.items()):
            if source not in ("go", "reactome"):
                continue
            source_sets = [sets[i] for i in idx]
            entry[source] = cells(themes, source_sets, [set_bands[i] for i in idx],
                                  theme_bands, n)
        entry["near_pairs"] = near_pairs(themes, [sets[i] for i in picked], n, BOOT_SEED)
        best = best_jaccard(themes, [sets[i] for i in picked], n)
        entry["placement"] = {}
        for low, high in BANDS:
            band = f"{low}-{high}"
            sel = [j for j, i in enumerate(picked) if set_bands[i] == band]
            if sel:
                entry["placement"][band] = {
                    "median_best_jaccard": round(float(np.median(best[sel])), 4),
                    "share_above_0.5": round(float((best[sel] > MATCH).mean()), 4),
                    "n": len(sel)}
        rootmap = roots_of(path)
        node_members: dict[str, set[int]] = defaultdict(set)
        with (path / "members.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["key"] in index_of:
                    node_members[row["node"]].add(index_of[row["key"]])
        holder: dict[int, set[str]] = defaultdict(set)
        for node, rows in node_members.items():
            for r in rows:
                holder[r] |= rootmap.get(node, {node})
        scatter = [len({root_id for leaf in sets[i] for root_id in holder.get(leaf, ())})
                   for i in picked]
        entry["scatter"] = {"median_root_themes": float(np.median(scatter)) if scatter else None,
                            "mean_root_themes": round(float(np.mean(scatter)), 2) if scatter
                            else None,
                            "share_in_one_root": round(float(np.mean(
                                [s <= 1 for s in scatter])), 4) if scatter else None}
        if NAMED_CASE in key_sets:
            rtk = {index_of[k] for k in key_sets[NAMED_CASE]}
            kit = ({index_of[k] for k in key_sets[NAMED_CHILD]}
                   if NAMED_CHILD in key_sets else set())
            jac, which = 0.0, None
            for position, members in enumerate(themes):
                inter = len(members & rtk)
                if inter:
                    value = inter / (len(members) + len(rtk) - inter)
                    if value > jac:
                        jac, which = value, position
            entry["named_case"] = {
                "key": NAMED_CASE, "name": names.get(NAMED_CASE),
                "leaf_set_size": len(rtk), "best_theme_jaccard": round(jac, 4),
                "best_theme_size": len(themes[which]) if which is not None else None,
                "child_key": NAMED_CHILD, "child_leaf_set_size": len(kit),
                "child_leaves_inside": (len(kit & themes[which]) if which is not None and kit
                                        else 0),
                "child_leaves_total": len(kit)}
        report["arms"][name] = entry
        print(f"  scored {name:<16} themes {len(themes):>6,}", flush=True)

    print()
    print(f"  recall/precision at Jaccard > {MATCH}, TARGET bands")
    header = f"    {'arm':<16}{'themes':>8}"
    for source in ("reactome", "go"):
        for low, high in BANDS:
            header += f"{source[:2] + ' ' + str(low) + '-' + str(high):>14}"
    print(header)
    for name, entry in report["arms"].items():
        line = f"    {name:<16}{entry['themes']:>8,}"
        for source in ("reactome", "go"):
            for low, high in BANDS:
                cell = entry.get(source, {}).get(f"{low}-{high}")
                if not cell or cell["recall"] is None:
                    line += f"{'-':>14}"
                else:
                    line += f"{cell['recall']:.3f}/{cell['precision'] or 0:.3f}".rjust(14)
        print(line)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"    -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
