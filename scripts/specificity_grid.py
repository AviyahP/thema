#!/usr/bin/env python3
"""Grade tests 3 and 4 at matched SPECIFICITY, and re-adjudicate them under the baseline amendment.

Two declared things, both recorded in `DECISIONS.md` on 3 Oct **before this was computed**:

1. **The post-hoc baseline amendment.** A gene baseline whose largest cluster exceeds 29.0133%
   of the universe -- THEMA's own declared size cap -- is DEGENERATE and excluded. It is post
   hoc, written after seeing that 9 of 12 baselines win on raw recovery while holding most of
   the universe in one cluster, and every verdict it produces is labelled so.

2. **The graded specificity measure.** INFORMATIONAL, NOT A GATE. Recovery rewards placing a pair
   together at any grain; lift rewards a low base rate; neither compares arms at the same grain.
   Smallest-shared-theme size does: being put together in a theme of 8 is a sharper claim than in a
   theme of 3,000.

Usage::

    uv run scripts/specificity_grid.py data/ontology/v0.3/recurrent_dag_10770
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

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

NULL_DRAWS = 600_000
NULL_SEED = 20261003

#: THEMA's own size cap, as a share. A baseline above it is excluded -- the post-hoc amendment.
DEGENERATE_SHARE = 2 * 469 / 3233

#: The declared specificity cut-offs.
SPECIFICITY_CUTS = (10, 50, 200)

#: Below this many pairs a figure is reported but not treated as quotable.
QUOTABLE = 20

WORD = re.compile(r"[a-z][a-z0-9-]{2,}")


def read_build(directory: Path) -> tuple[dict[str, list[str]], dict[str, set[str]]]:
    """A build's parent edges and its member sets.

    Args:
        directory: A build directory.

    Returns:
        Node to parents, and node to member keys.
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return parents, dict(members)


def upward(parents: dict[str, list[str]]) -> dict[str, dict[str, int]]:
    """For every node, its ancestors-or-self and the fewest parent-edges to each.

    Args:
        parents: Node to its direct parents.

    Returns:
        Node to ``{ancestor: hops}``, including itself at 0.
    """
    out: dict[str, dict[str, int]] = {}
    for node in parents:
        seen = {node: 0}
        queue = deque([node])
        while queue:
            at = queue.popleft()
            for parent in parents.get(at, ()):
                if parent not in seen:
                    seen[parent] = seen[at] + 1
                    queue.append(parent)
        out[node] = seen
    return out


def smallest_shared(
    homes: dict[str, set[str]], sizes: dict[str, int], a: str, b: str
) -> float:
    """Members of the smallest theme containing both, or inf.

    Args:
        homes: Pathway key to the themes holding it.
        sizes: Theme to its member count.
        a: One key.
        b: The other.

    Returns:
        The size, or ``inf``.
    """
    shared = homes.get(a, frozenset()) & homes.get(b, frozenset())
    return float(min((sizes[t] for t in shared), default=float("inf")))


def auroc(curated: np.ndarray, random: np.ndarray) -> float:
    """Probability a curated pair is more specific than a random one, ties counted half.

    Midranks over the combined sample, so an infinite size on either side is a tie among all such
    pairs rather than a dropped observation. Smaller size is more specific, so the rank statistic is
    taken on the sizes directly and low ranks are wins.

    Args:
        curated: Smallest-shared-theme sizes for curated pairs.
        random: The same for band-matched random pairs.

    Returns:
        The AUROC, or nan when either side is empty.
    """
    n, m = len(curated), len(random)
    if not n or not m:
        return float("nan")
    ranks = rankdata(np.concatenate([curated, random]))
    wins = float(ranks[:n].sum()) - n * (n + 1) / 2.0
    # `wins` counts (curated, random) pairs where curated ranks lower, ties at 0.5 via midranks.
    return 1.0 - wins / (n * m)


def main(argv: list[str] | None = None) -> int:
    """Run the specificity grid and the re-adjudication.

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
    parser.add_argument("--tsv", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    present = set(keys)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = {p.key: p for p in collection.pathways if p.key in present}

    print("SPECIFICITY GRID -- informational, not a gate")
    print(f"  universe {len(keys):,}")

    # ---- arms: DAG arms carry (homes, sizes); flat arms carry labels ----
    dag_arms: dict[str, tuple[dict[str, frozenset[str]], dict[str, int]]] = {}
    flat_arms: dict[str, np.ndarray] = {}
    collapse: dict[str, float] = {}

    def homes_of(directory: Path) -> tuple[dict[str, frozenset[str]], dict[str, int]]:
        _parents, members = read_build(directory)
        sizes = {node: len(ms) for node, ms in members.items()}
        homes: dict[str, set[str]] = defaultdict(set)
        for node, ms in members.items():
            for key in ms:
                homes[key].add(node)
        return {k: frozenset(v) for k, v in homes.items()}, sizes

    dag_arms["THEMA (frozen)"] = homes_of(args.build)
    if (args.tfidf_build / "members.tsv").is_file():
        dag_arms["TF-IDF DAG"] = homes_of(args.tfidf_build)
    if args.tfidf_vectors.is_file():
        vectors, _mean = centre_and_renormalise(np.load(args.tfidf_vectors))
        vectors = np.ascontiguousarray(vectors.astype(np.float32))
        labels = cluster(condensed(1.0 - (vectors @ vectors.T)), "ward", cuts=CUTS)
        for k in CUTS:
            flat_arms[f"TF-IDF flat@{k}"] = labels[k]
            collapse[f"TF-IDF flat@{k}"] = largest_share(labels[k])
        del vectors, labels
    matrix, span = gene_matrix([by_key[k] for k in keys])
    sims = similarities(matrix, span)
    excluded: list[tuple[str, float]] = []
    for measure in GENE_MEASURES:
        linkage = "ward" if measure in ("jaccard", "ochiai") else "average"
        square = (np.sqrt(np.maximum(1.0 - sims[measure], 0.0)) if measure == "jaccard"
                  else 1.0 - sims[measure])
        labels = cluster(condensed(square), linkage, cuts=CUTS)
        for k in CUTS:
            name = f"{measure}@{k}"
            share = largest_share(labels[k])
            collapse[name] = share
            if share > DEGENERATE_SHARE:
                excluded.append((name, share))
            else:
                flat_arms[name] = labels[k]
        del square, labels
    del sims, matrix

    print("\n  THE POST-HOC BASELINE AMENDMENT, applied: a baseline whose largest cluster exceeds")
    print(f"  {DEGENERATE_SHARE:.4%} of the universe -- THEMA's own size cap -- is excluded.")
    for name, share in sorted(excluded, key=lambda kv: -kv[1]):
        print(f"    EXCLUDED  {name:<14} largest cluster {share:>6.1%}")
    kept_gene = [n for n in flat_arms if not n.startswith("TF-IDF")]
    print(f"    KEPT      {', '.join(f'{n} ({collapse[n]:.1%})' for n in kept_gene)}")
    print(f"    {len(excluded)} of 12 gene baselines excluded, {len(kept_gene)} kept")

    # ---- hop distances, THEMA only ----
    parents, members = read_build(args.build)
    sizes_thema = {node: len(ms) for node, ms in members.items()}
    tightest: dict[str, str] = {}
    for key in keys:
        holding = [n for n in dag_arms["THEMA (frozen)"][0].get(key, ())]
        if holding:
            tightest[key] = min(holding, key=lambda n: (sizes_thema[n], n))
    ups = upward(parents)
    print(f"\n  hop distance: {len(tightest):,} pathways have a tightest theme; "
          f"ancestor maps for {len(ups):,} themes")

    def hops(a: str, b: str) -> float:
        ta, tb = tightest.get(a), tightest.get(b)
        if ta is None or tb is None:
            return float("inf")
        da, db = ups[ta], ups[tb]
        common = da.keys() & db.keys()
        return float(min((da[t] + db[t] for t in common), default=float("inf")))

    # ---- the corrected null ----
    rng = np.random.default_rng(NULL_SEED)
    ia = rng.integers(0, len(keys), size=NULL_DRAWS)
    ib = rng.integers(0, len(keys), size=NULL_DRAWS)
    keep = ia != ib
    ia, ib = ia[keep], ib[keep]
    # NOT `jaccard(...) or -1.0`: 0.0 is falsy and that emptied the zero-gene band once already.
    gene_null = np.array([
        (lambda v: -1.0 if v is None else v)(jaccard(by_key[keys[i]], by_key[keys[j]]))
        for i, j in zip(ia, ib, strict=True)
    ])
    null_band = [band_of(v) if v >= 0 else None for v in gene_null]
    print(f"  null: {len(ia):,} random pairs, seed {NULL_SEED}; "
          f"{int((gene_null == 0).sum()):,} at exactly zero gene overlap")

    def spec_for(name: str, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        if name in dag_arms:
            homes, sizes = dag_arms[name]
            return np.array([smallest_shared(homes, sizes, keys[i], keys[j])
                             for i, j in zip(left, right, strict=True)])
        labels = flat_arms[name]
        counts = np.bincount(labels)
        same = labels[left] == labels[right]
        out = np.full(len(left), float("inf"))
        out[same] = counts[labels[left][same]].astype(float)
        return out

    arm_names = ["THEMA (frozen)", *[n for n in dag_arms if n != "THEMA (frozen)"],
                 *[n for n in flat_arms if n.startswith("TF-IDF")], *kept_gene]
    null_spec = {name: spec_for(name, ia, ib) for name in arm_names}
    null_hops = np.array([hops(keys[i], keys[j]) for i, j in zip(ia, ib, strict=True)])

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

    rows: list[tuple[str, ...]] = []
    report: dict = {
        "post_hoc_baseline_amendment": {
            "share": DEGENERATE_SHARE, "excluded": dict(excluded),
            "kept": {n: round(collapse[n], 4) for n in kept_gene},
            "label": "under the post-hoc baseline amendment",
        },
        "graded_measure": "informational, not a gate; declared before computation",
        "specificity_cuts": list(SPECIFICITY_CUTS),
        "null_draws": int(len(ia)), "null_seed": NULL_SEED,
        "sources": {},
    }

    for source in sources:
        kept = restrict(source, present)
        pa = np.array([x for x, _ in kept.pairs])
        pb = np.array([y for _, y in kept.pairs])
        index = {k: i for i, k in enumerate(keys)}
        la = np.array([index[x] for x in pa], dtype=np.int64)
        lb = np.array([index[y] for y in pb], dtype=np.int64)
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[x], by_key[y])) for x, y in zip(pa, pb, strict=True)])
        bands = [band_of(v) if v >= 0 else None for v in gvals]
        spec = {name: spec_for(name, la, lb) for name in arm_names}
        pair_hops = np.array([hops(x, y) for x, y in zip(pa, pb, strict=True)])

        print(f"\n{'=' * 104}\n{kept.name}  ({kept.strength}) -- {len(kept.pairs):,} pairs"
              f"\n{'=' * 104}")
        entry: dict = {"pairs": len(kept.pairs), "bands": []}
        for band in reversed(BANDS):
            mask = np.array([x == band for x in bands])
            if not mask.any():
                continue
            nmask = np.array([x == band for x in null_band])
            print(f"\n  gene band {band_label(*band)} -- {int(mask.sum()):,} pairs "
                  f"(null {int(nmask.sum()):,})"
                  + ("  [n < 20, not quotable]" if int(mask.sum()) < QUOTABLE else ""))
            print(f"    {'arm':<17} {'med size':>9} {'rand':>8} {'AUROC':>7} "
                  + " ".join(f"{'<=' + str(c):>15}" for c in SPECIFICITY_CUTS))
            band_entry: dict = {"band": band_label(*band), "n": int(mask.sum()),
                                "n_null": int(nmask.sum()), "arms": {}}
            for name in arm_names:
                cur, ran = spec[name][mask], null_spec[name][nmask]
                med = float(np.median(cur))
                medr = float(np.median(ran))
                area = auroc(cur, ran)
                cuts = []
                got: dict = {"median_size": None if np.isinf(med) else med,
                             "median_size_random": None if np.isinf(medr) else medr,
                             "auroc": None if np.isnan(area) else round(area, 4),
                             "at_cut": {}}
                for c in SPECIFICITY_CUTS:
                    r = float((cur <= c).mean())
                    rr = float((ran <= c).mean()) if len(ran) else float("nan")
                    cuts.append(f"{r:>6.1%}/{rr:>7.1%}")
                    got["at_cut"][c] = {"curated": round(r, 4),
                                        "random": None if np.isnan(rr) else round(rr, 4)}
                    rows.append((kept.name, band_label(*band), name, str(int(mask.sum())),
                                 str(c), f"{r:.4f}", "" if np.isnan(rr) else f"{rr:.4f}",
                                 "" if np.isnan(area) else f"{area:.4f}",
                                 "inf" if np.isinf(med) else f"{med:.0f}"))
                print(f"    {name:<17} {'inf' if np.isinf(med) else f'{med:.0f}':>9} "
                      f"{'inf' if np.isinf(medr) else f'{medr:.0f}':>8} "
                      f"{'n/a' if np.isnan(area) else f'{area:.3f}':>7} " + " ".join(cuts))
                band_entry["arms"][name] = got
            finite = pair_hops[mask][np.isfinite(pair_hops[mask])]
            nfinite = null_hops[nmask][np.isfinite(null_hops[nmask])]
            band_entry["hops"] = {
                "median_curated": None if not len(finite) else float(np.median(finite)),
                "median_random": None if not len(nfinite) else float(np.median(nfinite)),
                "share_finite_curated": round(float(np.isfinite(pair_hops[mask]).mean()), 4),
                "share_finite_random": round(float(np.isfinite(null_hops[nmask]).mean()), 4),
            }
            print(f"    {'THEMA hop dist':<17} median "
                  f"{'n/a' if not len(finite) else f'{np.median(finite):.0f}'} vs random "
                  f"{'n/a' if not len(nfinite) else f'{np.median(nfinite):.0f}'}; "
                  f"finite for {np.isfinite(pair_hops[mask]).mean():.1%} of pairs vs "
                  f"{np.isfinite(null_hops[nmask]).mean():.1%} random")
            entry["bands"].append(band_entry)
        report["sources"][kept.name] = entry

    if args.tsv:
        args.tsv.parent.mkdir(parents=True, exist_ok=True)
        with args.tsv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["source", "gene_band", "arm", "n_pairs", "specificity_cut",
                             "curated_rate", "random_rate", "auroc", "median_size"])
            writer.writerows(rows)
        print(f"\n  every band x arm x cut -> {args.tsv}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
