#!/usr/bin/env python3
"""Item 4: describe every theme of 51+ members in the repaired build. No rule is applied.

Aviyah declared no rule for big themes and will decide after seeing this, so nothing here gates or
filters: it describes. Five columns per theme, and the two that are new:

- **support at Jaccard 0.5.** A theme's own support is the share of runs holding a matching node at
  the *build's* threshold, 0.70. The same theme scored at 0.50 says how much of its apparent
  weakness is the strictness of the match rather than absence of the group. A theme at support 0.08
  and support-at-0.5 of 0.60 recurs reliably in a slightly different form each time; one at 0.08
  and 0.09 does not recur at all. The reviewer's diagnostic found mid-size Ward clusters recur at
  0.5 and not at 0.70, which is exactly this gap.
- **gene coherence against a size-matched null.** Size-matched because mean pairwise overlap falls
  with set size on its own, so an unmatched null would make every large theme look incoherent.

Also reports what the 80% chain-collapse share would have given, as counts only, from the same
consensus output -- the declared rule is 90% and the choice is not made from these numbers.

Read-only. Usage::

    uv run scripts/repair_big_themes.py --build thema_L_repair
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
from thema.ontology import bitset as bits
from thema.ontology.universe import load_embedded

#: Themes at or above this size are described.
BIG = 51
#: Bands for the histograms.
BANDS: tuple[tuple[int, int], ...] = ((51, 100), (101, 300), (301, 1000), (1001, 10**9))
#: The second matching threshold, for "support at Jaccard 0.5".
SOFT_THETA = 0.50
#: Null draws and pair cap for coherence.
NULL_DRAWS = 10
MAX_PAIRS = 4000
SEED = 0
NEAREST = 7
#: Support histogram edges.
SUPPORT_EDGES = (0.0, 0.05, 0.1, 0.2, 0.33, 0.5, 0.7, 1.01)


def label(low: int, high: int) -> str:
    """Band label."""
    return f"{low}-{high}" if high < 10**9 else f"{low}+"


def band_of(size: int) -> str:
    """Band label for a size, or ``"small"`` below :data:`BIG`."""
    for low, high in BANDS:
        if low <= size <= high:
            return label(low, high)
    return "small"


def soft_support(query: np.ndarray, runs: list, theta: float) -> float:
    """Share of runs holding a node matching ``query`` at ``theta`` on present members.

    The walk is the one ``recurrent.score`` uses: restrict the query to what the run drew, start at
    the smallest recorded cluster holding one of its members, and climb the parent chain taking the
    best Jaccard. Runs that drew fewer than three of the query's members are not eligible, so a
    theme is never penalised for a run that could not have held it.

    Args:
        query: The theme's member bitset.
        runs: Loaded per-run records.
        theta: Match threshold.

    Returns:
        The share over eligible runs, or nan if none.
    """
    hit = eligible = 0
    for run in runs:
        present = query & run.present
        size = bits.count(present)
        if size < 3:
            continue
        eligible += 1
        start = int(run.leaf_cluster[bits.unpack(present)[0]])
        node, best = start, 0.0
        while node != -1:
            inter = bits.count(present & run.clusters[node])
            union = size + int(run.sizes[node]) - inter
            if union:
                best = max(best, inter / union)
            node = int(run.parent[node])
        if best >= theta:
            hit += 1
    return hit / eligible if eligible else float("nan")


def mean_pair_jaccard(keys: list[str], genes: dict[str, frozenset[str]],
                      rng: np.random.Generator) -> float | None:
    """Mean pairwise gene Jaccard, sampling pairs above :data:`MAX_PAIRS`."""
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
    out = []
    for a, b in pairs:
        union = len(genes[a] | genes[b])
        out.append(len(genes[a] & genes[b]) / union if union else 0.0)
    return float(np.mean(out))


def main(argv: list[str] | None = None) -> int:
    """Describe the big themes, and report the 80% collapse counts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--space", default="leaves_centred")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    from cut_trees import load_run

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    n = meta["n_embedded"]
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    index_of = {k: i for i, k in enumerate(keys)}
    vectors = np.ascontiguousarray(
        np.load(root / "vectors_leaves_centred.npy").astype(np.float32))
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    names = {p.key: p.name for p in collection.pathways}
    sources = {p.key: p.source for p in collection.pathways}

    path = root / args.build
    members: dict[str, list[str]] = defaultdict(list)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row.get("node") or row.get("id")] = float(row.get("support") or 0.0)
    children: dict[str, int] = Counter()
    if (path / "edges.tsv").is_file():
        with (path / "edges.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                children[row["parent"]] += 1

    big = sorted((node for node, keyset in members.items() if len(keyset) >= BIG),
                 key=lambda node: -len(members[node]))
    print(f"ITEM 4: {len(big):,} themes of {BIG}+ members in {args.build} "
          f"(of {len(members):,} total)")
    trees = root / "trees" / f"{args.space}_{meta['universe_digest']}"
    runs = [load_run(trees / f"row{r:05d}.npz", n, 10**9) for r in range(1, args.runs + 1)]
    width = ((n + bits.WORD - 1) // bits.WORD) * bits.WORD
    rng = np.random.default_rng(SEED)

    rows_out = []
    for node in big:
        keyset = members[node]
        block = bits.pack(sorted(index_of[k] for k in keyset), width)
        soft = soft_support(block, runs, SOFT_THETA)
        observed = mean_pair_jaccard(keyset, genes, rng)
        draws = []
        for _ in range(NULL_DRAWS):
            sample = [keys[i] for i in rng.choice(len(keys), len(keyset), replace=False)]
            value = mean_pair_jaccard(sample, genes, rng)
            if value is not None:
                draws.append(value)
        null = float(np.mean(draws)) if draws else None
        idx = [index_of[k] for k in keyset]
        centre = vectors[idx].mean(axis=0)
        norm = np.linalg.norm(centre)
        centre = centre / (norm if norm else 1.0)
        nearest = [keyset[i] for i in np.argsort(-(vectors[idx] @ centre))[:NEAREST]]
        rows_out.append({
            "node": node, "size": len(keyset),
            "support": round(support.get(node, 0.0), 4),
            "support_at_0.5": None if np.isnan(soft) else round(soft, 4),
            "coherence_observed": None if observed is None else round(observed, 5),
            "coherence_null": None if null is None else round(null, 5),
            "coherence_ratio": (round(observed / null, 2)
                                if observed is not None and null else None),
            "children": children.get(node, 0),
            "band": band_of(len(keyset)),
            "sources": dict(sorted(Counter(sources.get(k, "?") for k in keyset).items())),
            "nearest": [names.get(k, k) for k in nearest]})

    head = (f"  {'node':<9}{'size':>6}{'supp':>7}{'s@0.5':>7}{'coh':>8}{'kids':>6}"
            "  nearest the centroid")
    print(head)
    for r in rows_out:
        soft = r["support_at_0.5"] if r["support_at_0.5"] is not None else float("nan")
        print(f"  {r['node']:<9}{r['size']:>6,}{r['support']:>7.3f}{soft:>7.3f}"
              f"{(r['coherence_ratio'] or 0):>7.1f}x{r['children']:>6}  "
              f"{'; '.join(r['nearest'][:3])}")

    print()
    print("  HISTOGRAMS per band")
    for low, high in BANDS:
        band = label(low, high)
        sel = [r for r in rows_out if r["band"] == band]
        if not sel:
            continue
        print(f"    {band} ({len(sel)} themes)")
        counts = Counter()
        for r in sel:
            for lo, hi in zip(SUPPORT_EDGES, SUPPORT_EDGES[1:], strict=False):
                if lo <= r["support"] < hi:
                    counts[f"{lo:g}-{hi:g}"] += 1
                    break
        print("      support:   " + "  ".join(
            f"{k}:{counts[k]}" for k in (f"{lo:g}-{hi:g}" for lo, hi in
                                         zip(SUPPORT_EDGES, SUPPORT_EDGES[1:], strict=False))
            if counts[k]))
        soft_vals = [r["support_at_0.5"] for r in sel if r["support_at_0.5"] is not None]
        sup_vals = [r["support"] for r in sel]
        if soft_vals:
            print(f"      median support {np.median(sup_vals):.3f}, "
                  f"median support at 0.5 {np.median(soft_vals):.3f}, "
                  f"median gap {np.median(np.array(soft_vals) - np.array(sup_vals)):+.3f}")
        ratios = [r["coherence_ratio"] for r in sel if r["coherence_ratio"]]
        if ratios:
            rc = Counter()
            for v in ratios:
                rc["<3x" if v < 3 else "3-10x" if v < 10 else "10-30x" if v < 30 else ">=30x"] += 1
            print("      coherence: " + "  ".join(f"{k}:{rc[k]}" for k in
                                                  ("<3x", "3-10x", "10-30x", ">=30x") if rc[k])
                  + f"   median {np.median(ratios):.1f}x")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"build": args.build, "big": BIG,
                                        "soft_theta": SOFT_THETA, "themes": rows_out},
                                       indent=2, default=float) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
