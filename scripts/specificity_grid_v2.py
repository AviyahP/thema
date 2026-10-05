#!/usr/bin/env python3
"""The graded specificity measure, extended (§A of the 4 Oct brief), over every comparison arm.

Supersedes `scripts/specificity_grid.py`; that script and its outputs are kept, as the no-overwrite
convention requires. What this adds:

- **Every arm**: THEMA (frozen), HiDeF, CliXO if built, TF-IDF flat, `ochiai@100`, `kappa@100`, and
  a **random arm**.
- **Pooled bands** beside the per-band figures.
- **A curated ceiling row**: the size of the smallest CURATED node containing both members of a
  sibling pair. This is what a perfect reproduction of the curated hierarchy would score, so it is
  the number the arms should be read against rather than against each other alone.
- **A fan-out subset**: sibling pairs whose curated parent has at most 6 children, i.e. tight
  sibling groups rather than pairs manufactured by a broad parent.
- **Hop distance**: the undirected shortest path between two pathways through the arm's own graph,
  pathway to its themes to theme-theme edges, with Mann-Whitney U and connectivity.

**THE RANDOM ARM is THEMA's own structure with pathway identities permuted** (seed 0). It keeps the
theme count, every theme size and the multi-membership pattern exactly, and destroys only the
correspondence to biology. So it answers the question a uniform random partition cannot: how much of
THEMA's specificity advantage is the shape of its hierarchy rather than what is in it.

**Informational. Not a gate.** The 4 Oct decision rule names specificity AUROC as its primary
metric; everything else here is reported.

Usage::

    uv run scripts/specificity_grid_v2.py
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu, rankdata

from compare_baselines import CUTS, cluster, condensed, gene_matrix, similarities
from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.embed import centre_and_renormalise
from thema.evaluation import (
    BANDS,
    band_label,
    band_of,
    go_parents,
    jaccard,
    restrict,
    sibling_pairs,
)
from thema.ontology.universe import load_embedded

csv.field_size_limit(1 << 30)

NULL_DRAWS = 600_000
NULL_SEED = 20261003

#: Hop distance needs a breadth-first search per pair, so its null is a subsample of the main one.
#: Stated rather than silently applied.
HOP_NULL_DRAWS = 50_000

#: The declared specificity cut-offs.
SPECIFICITY_CUTS = (10, 50, 200)

#: Fan-out cap for the tight-sibling subset, as `compare_baselines.SIBLING_FANOUT`.
FANOUT = 6

#: Seed for the random arm's permutation.
RANDOM_ARM_SEED = 0

#: Unreachable, in the uint8 theme-distance matrix.
FAR = 255


def read_arm(directory: Path) -> tuple[dict[str, frozenset[str]], dict[str, int], dict[str, list]]:
    """An arm's homes, theme sizes and parent edges.

    Args:
        directory: A build directory in THEMA's schema.

    Returns:
        Pathway key to its themes, theme to size, theme to parents.
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    homes: dict[str, set[str]] = defaultdict(set)
    for node, keys in members.items():
        for key in keys:
            homes[key].add(node)
    return (
        {k: frozenset(v) for k, v in homes.items()},
        {n: len(members.get(n, ())) for n in parents},
        parents,
    )


def theme_distances(parents: dict[str, list[str]]) -> tuple[np.ndarray, dict[str, int]]:
    """Undirected shortest paths between themes, in edges.

    A full breadth-first search from every theme. At 6,244 themes and 8,208 edges this is about
    50 million steps and fits in a 39 MB uint8 matrix, which is what makes per-pair hop distance
    affordable at all: a pathway-to-pathway path is ``1 + d(theme, theme) + 1``.

    Args:
        parents: Theme to its parents.

    Returns:
        The distance matrix with :data:`FAR` for unreachable, and theme to row index.
    """
    nodes = sorted(parents)
    index = {n: i for i, n in enumerate(nodes)}
    neighbours: list[list[int]] = [[] for _ in nodes]
    for child, ps in parents.items():
        for parent in ps:
            if parent in index:
                neighbours[index[child]].append(index[parent])
                neighbours[index[parent]].append(index[child])
    out = np.full((len(nodes), len(nodes)), FAR, dtype=np.uint8)
    for start in range(len(nodes)):
        out[start, start] = 0
        queue = deque([start])
        while queue:
            at = queue.popleft()
            step = out[start, at] + 1
            if step >= FAR:
                continue
            for nxt in neighbours[at]:
                if out[start, nxt] == FAR:
                    out[start, nxt] = step
                    queue.append(nxt)
    return out, index


def smallest_shared(
    homes: dict[str, frozenset[str]], sizes: dict[str, int], a: str, b: str
) -> float:
    """Members of the smallest theme holding both, or inf."""
    shared = homes.get(a, frozenset()) & homes.get(b, frozenset())
    return float(min((sizes[t] for t in shared), default=float("inf")))


def hop(
    homes: dict[str, frozenset[str]],
    matrix: np.ndarray,
    index: dict[str, int],
    a: str,
    b: str,
) -> float:
    """Undirected pathway-to-pathway hops through the arm's graph, or inf."""
    left = [index[t] for t in homes.get(a, ()) if t in index]
    right = [index[t] for t in homes.get(b, ()) if t in index]
    if not left or not right:
        return float("inf")
    best = int(matrix[np.ix_(left, right)].min())
    return float("inf") if best >= FAR else float(best + 2)


def auroc(curated: np.ndarray, random_values: np.ndarray) -> float:
    """P(curated more specific than random), ties half, via midranks."""
    n, m = len(curated), len(random_values)
    if not n or not m:
        return float("nan")
    ranks = rankdata(np.concatenate([curated, random_values]))
    wins = float(ranks[:n].sum()) - n * (n + 1) / 2.0
    return 1.0 - wins / (n * m)


def curated_parents(
    relation: dict[str, list[str]], prefix: str
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Curated node to its member pathway keys, and its child count.

    Args:
        relation: Child to parents, in the curated hierarchy.
        prefix: Key prefix, e.g. ``reactome:``.

    Returns:
        Curated node key to the pathway keys beneath it, and node to its direct child count.
    """
    children: dict[str, list[str]] = defaultdict(list)
    for child, ps in relation.items():
        for parent in ps:
            children[parent].append(child)
    below: dict[str, set[str]] = {}

    def gather(node: str) -> set[str]:
        if node in below:
            return below[node]
        got = {prefix + node}
        below[node] = got
        for child in children.get(node, ()):
            got |= gather(child)
        below[node] = got
        return got

    for node in set(relation) | set(children):
        gather(node)
    return below, {n: len(v) for n, v in children.items()}


def main(argv: list[str] | None = None) -> int:
    """Run the extended grid.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--tsv", type=Path,
                        default=Path("data/experiments/specificity_grid_v2.tsv"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--markdown", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    present = set(keys)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = {p.key: p for p in collection.pathways if p.key in present}
    print(f"SPECIFICITY GRID v2 -- informational, not a gate. Universe {len(keys):,}")

    # ---- hierarchical arms ----
    hier: dict[str, tuple] = {}
    for name, where in (
        ("THEMA (frozen)", root / "recurrent_dag_10770"),
        ("HiDeF k=15", root / "hidef_10770_k15"),
        ("CliXO", root / "clixo_10770"),
    ):
        if (where / "members.tsv").is_file():
            homes, sizes, parents = read_arm(where)
            matrix, index = theme_distances(parents)
            hier[name] = (homes, sizes, matrix, index)
            print(f"  {name}: {len(sizes):,} themes, hop matrix {matrix.shape}")

    # The random arm: THEMA's structure, pathway identities permuted. Sizes and multi-membership
    # are preserved exactly; only what is in each theme changes.
    if "THEMA (frozen)" in hier:
        homes, sizes, matrix, index = hier["THEMA (frozen)"]
        rng = np.random.default_rng(RANDOM_ARM_SEED)
        shuffled = list(keys)
        rng.shuffle(shuffled)
        mapping = dict(zip(keys, shuffled, strict=True))
        permuted: dict[str, set[str]] = defaultdict(set)
        for key, themes in homes.items():
            permuted[mapping[key]] |= set(themes)
        hier["random (THEMA shape)"] = (
            {k: frozenset(v) for k, v in permuted.items()}, sizes, matrix, index,
        )
        print(f"  random arm: THEMA's shape with identities permuted, seed {RANDOM_ARM_SEED}")

    # ---- flat arms ----
    flat: dict[str, np.ndarray] = {}
    tfidf = root / "tfidf_vectors.npy"
    if tfidf.is_file():
        vectors, _mean = centre_and_renormalise(np.load(tfidf))
        vectors = np.ascontiguousarray(vectors.astype(np.float32))
        labels = cluster(condensed(1.0 - (vectors @ vectors.T)), "ward", cuts=CUTS)
        flat["TF-IDF flat@100"] = labels[100]
        del vectors, labels
    gene, span = gene_matrix([by_key[k] for k in keys])
    sims = similarities(gene, span)
    for measure in ("ochiai", "kappa"):
        # Ochiai IS the cosine between binary indicator vectors, so 1 - ochiai is Euclidean and
        # Ward is legitimate on it directly; kappa is not a metric, so average linkage only. Both
        # match `compare_baselines.GENE_MEASURES`.
        labels = cluster(condensed(1.0 - sims[measure]),
                         "ward" if measure == "ochiai" else "average", cuts=CUTS)
        flat[f"{measure}@100"] = labels[100]
        del labels
    del sims, gene
    print(f"  flat arms: {', '.join(flat)}")

    arm_names = [*hier, *flat]
    position = {k: i for i, k in enumerate(keys)}

    # ---- curated references ----
    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    terms = parse_obo_terms((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines())
    go_rel = go_parents(terms)
    curated = {
        "reactome-siblings": (sibling_pairs(relation, "reactome:", "reactome-siblings", ""),
                              *curated_parents(relation, "reactome:")),
        "go-siblings": (sibling_pairs(go_rel, "go:", "go-siblings", ""),
                        *curated_parents(go_rel, "go:")),
    }

    # ---- null ----
    rng = np.random.default_rng(NULL_SEED)
    ia = rng.integers(0, len(keys), size=NULL_DRAWS)
    ib = rng.integers(0, len(keys), size=NULL_DRAWS)
    keep = ia != ib
    ia, ib = ia[keep], ib[keep]
    gene_null = np.array([
        (lambda v: -1.0 if v is None else v)(jaccard(by_key[keys[i]], by_key[keys[j]]))
        for i, j in zip(ia, ib, strict=True)
    ])
    null_bands = [band_of(v) if v >= 0 else None for v in gene_null]
    print(f"  null {len(ia):,} pairs; {int((gene_null == 0).sum()):,} at zero gene overlap")

    def spec(name: str, left: list[str], right: list[str]) -> np.ndarray:
        if name in hier:
            homes, sizes, _m, _i = hier[name]
            return np.array([smallest_shared(homes, sizes, a, b)
                             for a, b in zip(left, right, strict=True)])
        labels = flat[name]
        counts = np.bincount(labels)
        out = np.full(len(left), float("inf"))
        for n, (a, b) in enumerate(zip(left, right, strict=True)):
            if labels[position[a]] == labels[position[b]]:
                out[n] = float(counts[labels[position[a]]])
        return out

    null_left = [keys[i] for i in ia]
    null_right = [keys[j] for j in ib]
    null_spec = {name: spec(name, null_left, null_right) for name in arm_names}
    print("  null specificity computed for every arm", flush=True)

    hop_rng = np.random.default_rng(NULL_SEED + 1)
    hop_pick = hop_rng.choice(len(ia), size=min(HOP_NULL_DRAWS, len(ia)), replace=False)
    null_hops = {
        name: np.array([hop(hier[name][0], hier[name][2], hier[name][3],
                            null_left[i], null_right[i]) for i in hop_pick])
        for name in hier
    }
    print(f"  null hop distance on a {len(hop_pick):,}-pair subsample", flush=True)

    rows: list[tuple[str, ...]] = []
    report: dict = {"arms": arm_names, "null_draws": int(len(ia)),
                    "hop_null_draws": int(len(hop_pick)), "sources": {}}

    for source, (pairs, below, child_count) in curated.items():
        kept = restrict(pairs, present)
        left = [a for a, _ in kept.pairs]
        right = [b for _, b in kept.pairs]
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[a], by_key[b])) for a, b in zip(left, right, strict=True)])
        bands = [band_of(v) if v >= 0 else None for v in gvals]

        # Curated ceiling: the smallest curated node containing both, and its fan-out.
        ceiling = np.full(len(left), float("inf"))
        tight = np.zeros(len(left), dtype=bool)
        for n, (a, b) in enumerate(zip(left, right, strict=True)):
            best, best_node = float("inf"), None
            for node, keyset in below.items():
                if a in keyset and b in keyset and len(keyset) < best:
                    best, best_node = float(len(keyset)), node
            ceiling[n] = best
            if best_node is not None:
                tight[n] = child_count.get(best_node, 0) <= FANOUT

        arm_spec = {name: spec(name, left, right) for name in arm_names}
        arm_hops = {
            name: np.array([hop(hier[name][0], hier[name][2], hier[name][3], a, b)
                            for a, b in zip(left, right, strict=True)])
            for name in hier
        }
        print(f"\n{'=' * 104}\n{source} -- {len(left):,} pairs, "
              f"{int(tight.sum()):,} with a curated parent of <= {FANOUT} children\n{'=' * 104}")

        entry: dict = {"pairs": len(left), "tight_pairs": int(tight.sum()), "bands": []}
        band_list = [*reversed(BANDS), None]  # None = pooled
        for band in band_list:
            mask = (np.ones(len(left), dtype=bool) if band is None
                    else np.array([x == band for x in bands]))
            nmask = (np.ones(len(ia), dtype=bool) if band is None
                     else np.array([x == band for x in null_bands]))
            if not mask.any():
                continue
            label = "ALL BANDS POOLED" if band is None else band_label(*band)
            for subset, subset_name in ((mask, "all"), (mask & tight, f"fanout<={FANOUT}")):
                if not subset.any():
                    continue
                print(f"\n  {label}  [{subset_name}] -- {int(subset.sum()):,} pairs "
                      f"(null {int(nmask.sum()):,})")
                print(f"    {'arm':<22} {'med':>7} {'AUROC':>7} "
                      + " ".join(f"{'<=' + str(c):>14}" for c in SPECIFICITY_CUTS))
                ceil_cuts = " ".join(
                    f"{float((ceiling[subset] <= c).mean()):>6.1%}/{'':>7}"
                    for c in SPECIFICITY_CUTS
                )
                print(f"    {'CURATED CEILING':<22} "
                      f"{np.median(ceiling[subset]):>7.0f} {'':>7} {ceil_cuts}")
                band_entry: dict = {
                    "band": label, "subset": subset_name, "n": int(subset.sum()),
                    "n_null": int(nmask.sum()),
                    "curated_ceiling": {
                        "median": float(np.median(ceiling[subset])),
                        **{f"at_{c}": round(float((ceiling[subset] <= c).mean()), 4)
                           for c in SPECIFICITY_CUTS},
                    },
                    "arms": {},
                }
                for name in arm_names:
                    cur, ran = arm_spec[name][subset], null_spec[name][nmask]
                    area = auroc(cur, ran)
                    cuts, got = [], {"auroc": None if np.isnan(area) else round(area, 4),
                                     "median": None if np.isinf(np.median(cur))
                                     else float(np.median(cur)), "at_cut": {}}
                    for c in SPECIFICITY_CUTS:
                        r = float((cur <= c).mean())
                        rr = float((ran <= c).mean())
                        cuts.append(f"{r:>6.1%}/{rr:>7.1%}")
                        got["at_cut"][c] = {"curated": round(r, 4), "random": round(rr, 4)}
                        rows.append((source, label, subset_name, name,
                                     str(int(subset.sum())), str(c), f"{r:.4f}", f"{rr:.4f}",
                                     "" if np.isnan(area) else f"{area:.4f}"))
                    med = np.median(cur)
                    print(f"    {name:<22} {'inf' if np.isinf(med) else f'{med:.0f}':>7} "
                          f"{'n/a' if np.isnan(area) else f'{area:.3f}':>7} " + " ".join(cuts))
                    band_entry["arms"][name] = got
                if subset_name == "all":
                    for name in hier:
                        ch = arm_hops[name][subset]
                        nh = null_hops[name]
                        fc, fn = np.isfinite(ch), np.isfinite(nh)
                        if fc.any() and fn.any():
                            u, pvalue = mannwhitneyu(ch[fc], nh[fn], alternative="less")
                        else:
                            u, pvalue = float("nan"), float("nan")
                        hop_area = auroc(ch, nh)
                        band_entry.setdefault("hops", {})[name] = {
                            "median_curated": None if not fc.any() else float(np.median(ch[fc])),
                            "median_random": None if not fn.any() else float(np.median(nh[fn])),
                            "auroc": None if np.isnan(hop_area) else round(hop_area, 4),
                            "mannwhitney_u": None if np.isnan(u) else float(u),
                            "p_value": None if np.isnan(pvalue) else float(pvalue),
                            "connectivity_curated": round(float(fc.mean()), 4),
                            "connectivity_random": round(float(fn.mean()), 4),
                        }
                        print(f"      hops {name:<22} median "
                              f"{'n/a' if not fc.any() else f'{np.median(ch[fc]):.0f}'} vs "
                              f"{'n/a' if not fn.any() else f'{np.median(nh[fn]):.0f}'}  "
                              f"AUROC {'n/a' if np.isnan(hop_area) else f'{hop_area:.3f}'}  "
                              f"p {'n/a' if np.isnan(pvalue) else f'{pvalue:.2e}'}  "
                              f"connected {fc.mean():.1%} vs {fn.mean():.1%}")
                entry["bands"].append(band_entry)
        report["sources"][source] = entry

    args.tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.tsv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["source", "band", "subset", "arm", "n_pairs", "specificity_cut",
                         "curated_rate", "random_rate", "auroc"])
        writer.writerows(rows)
    print(f"\n  -> {args.tsv}")
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
