#!/usr/bin/env python3
"""Report the recurrence-threshold arms on universe L, as the 8 Oct theta brief declares them.

Everything here is evaluation: it reads built ontologies and never changes one. The question the
brief asks is whether lowering the recurrence threshold restores the middle of the hierarchy --
clusters of roughly 60 to 800 members -- without the middle being noise. So the two measurements
that matter most are the band counts and **gene coherence**, which is the check that a new mid-sized
theme is biologically coherent and not a bag of unrelated pathways that happened to co-occur.

Gene coherence compares each theme against **size-matched random sets**, because the share of
member pairs sharing a gene rises with theme size on its own: a 200-member theme drawn at random
from a universe where 15% of pairs share a gene has far more sharing pairs than a 5-member one. The
ratio against a size-matched null is the only form of this number that can be compared across bands.

Usage::

    uv run scripts/leaves_theta_report.py --arm L=thema_L --arm M5=thema_L_M5 --arm MS=thema_L_MS
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.pathways import PathwayCollection
from thema.ontology.universe import load_embedded

#: Size bands the brief names.
BANDS: tuple[tuple[int, int], ...] = (
    (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 300), (301, 1000), (1001, 10**9))
#: Themes sampled per band for gene coherence, and the seed.
COHERENCE_SAMPLE = 150
SEED = 0
#: Random size-matched sets drawn per sampled theme.
NULL_DRAWS = 20
#: The brief's inclusion diagnostic applies above this size.
BIG_THEME = 60
#: The band the decision rule counts.
PREFERRED = (60, 800)
#: Example themes printed per band.
EXAMPLES = 5
#: Pairs sampled when a theme is too large to enumerate every pair.
MAX_PAIRS = 20000
#: The named case.
RTK = "reactome:R-HSA-9006934"


def band_of(size: int) -> str:
    """Band label for a theme size.

    Args:
        size: Member count.

    Returns:
        The label, or ``"other"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10**9 else f"{low}+"
    return "other"


def read_build(path: Path) -> tuple[dict[str, list[str]], dict[str, dict[str, float]],
                                    dict[str, set[str]]]:
    """Members, per-member inclusion and parent edges for one build.

    Args:
        path: A built ontology directory.

    Returns:
        ``(node -> member keys, node -> {key: inclusion}, child -> parents)``.
    """
    members: dict[str, list[str]] = defaultdict(list)
    inclusion: dict[str, dict[str, float]] = defaultdict(dict)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
            try:
                inclusion[row["node"]][row["key"]] = float(row.get("inclusion") or 1.0)
            except ValueError:
                inclusion[row["node"]][row["key"]] = 1.0
    parents: dict[str, set[str]] = defaultdict(set)
    if (path / "edges.tsv").is_file():
        with (path / "edges.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                parents[row["child"]].add(row["parent"])
    return members, inclusion, parents


def pair_share(keys: list[str], genes: dict[str, frozenset[str]],
               rng: np.random.Generator) -> float | None:
    """Share of member pairs sharing at least one gene.

    Every pair is enumerated for small themes; above :data:`MAX_PAIRS` pairs a random sample of
    that many is used instead, so a 3,000-member theme does not cost four million set
    intersections.

    Args:
        keys: Member pathway keys.
        genes: Pathway key to gene set.
        rng: For sampling pairs in a large theme.

    Returns:
        The share, or None if fewer than two members carry genes.
    """
    have = [k for k in keys if genes.get(k)]
    if len(have) < 2:
        return None
    total = len(have) * (len(have) - 1) // 2
    if total <= MAX_PAIRS:
        pairs = itertools.combinations(have, 2)
        count = total
    else:
        left = rng.integers(0, len(have), MAX_PAIRS)
        right = rng.integers(0, len(have), MAX_PAIRS)
        pairs = ((have[i], have[j]) for i, j in zip(left, right, strict=True) if i != j)
        count = sum(1 for i, j in zip(left, right, strict=True) if i != j)
    if not count:
        return None
    hit = sum(1 for a, b in pairs if genes[a] & genes[b])
    return hit / count


def coherence(members: dict[str, list[str]], genes: dict[str, frozenset[str]],
              pool: list[str]) -> dict[str, dict]:
    """Gene coherence per band against a size-matched random null.

    Args:
        members: Node to member keys.
        genes: Pathway key to gene set.
        pool: Every pathway key in L, to draw the null from.

    Returns:
        Per band, the observed and null shares and their ratio.
    """
    rng = np.random.default_rng(SEED)
    by_band: dict[str, list[str]] = defaultdict(list)
    for node, keys in members.items():
        by_band[band_of(len(keys))].append(node)
    out: dict[str, dict] = {}
    for low, high in BANDS:
        band = f"{low}-{high}" if high < 10**9 else f"{low}+"
        nodes = sorted(by_band.get(band, []))
        if not nodes:
            continue
        pick = ([nodes[i] for i in rng.choice(len(nodes), COHERENCE_SAMPLE, replace=False)]
                if len(nodes) > COHERENCE_SAMPLE else nodes)
        real, null = [], []
        for node in pick:
            keys = members[node]
            got = pair_share(keys, genes, rng)
            if got is None:
                continue
            real.append(got)
            draws = []
            for _ in range(NULL_DRAWS):
                sample = [pool[i] for i in rng.choice(len(pool), len(keys), replace=False)]
                value = pair_share(sample, genes, rng)
                if value is not None:
                    draws.append(value)
            if draws:
                null.append(float(np.mean(draws)))
        if not real or not null:
            continue
        r, u = float(np.mean(real)), float(np.mean(null))
        out[band] = {"n_themes_in_band": len(nodes), "n_sampled": len(real),
                     "observed": round(r, 4), "null": round(u, 4),
                     "ratio": round(r / u, 2) if u else None}
    return out


def main(argv: list[str] | None = None) -> int:
    """Report every arm.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--arm", action="append", default=[])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    names = {p.key: p.name for p in collection.pathways}
    sources = {p.key: p.source for p in collection.pathways}

    report: dict[str, object] = {"bands": [list(b) for b in BANDS], "seed": SEED,
                                 "coherence_sample": COHERENCE_SAMPLE, "arms": {}}
    rng = np.random.default_rng(SEED)

    for spec in args.arm:
        name, _, where = spec.partition("=")
        path = root / where
        if not (path / "members.tsv").is_file():
            print(f"{name}: no build at {path}")
            continue
        members, inclusion, parents = read_build(path)
        counts: dict[str, int] = defaultdict(int)
        for keyset in members.values():
            counts[band_of(len(keyset))] += 1
        roots = [n for n in members if not parents.get(n)]
        multi = sum(1 for n in members if len(parents.get(n, ())) > 1)
        preferred = sum(1 for keyset in members.values()
                        if PREFERRED[0] <= len(keyset) <= PREFERRED[1])

        big = [n for n, keyset in members.items() if len(keyset) > BIG_THEME]
        incl_median = incl_low = None
        if big:
            values = [v for n in big for v in inclusion[n].values()]
            incl_median = round(float(np.median(values)), 4)
            incl_low = round(float(np.mean([v < 0.7 for v in values])), 4)

        manifest = json.loads((path / "manifest.json").read_text())
        floors_file = manifest.get("floors_source")
        entry: dict[str, object] = {
            "path": str(path), "themes": len(members),
            "theta_match": manifest.get("theta_match"),
            "match_split": manifest.get("match_split"),
            "bands": {b: counts.get(b, 0) for b in
                      [f"{lo}-{hi}" if hi < 10**9 else f"{lo}+" for lo, hi in BANDS]},
            "themes_60_to_800": preferred,
            "n_roots": len(roots),
            "root_sizes": sorted((len(members[r]) for r in roots), reverse=True)[:20],
            "root_size_median": float(np.median([len(members[r]) for r in roots]))
            if roots else None,
            "multi_parent_share": round(multi / len(members), 4) if members else 0.0,
            "n_effectively_unplaced": manifest.get("n_effectively_unplaced"),
            "floors_source": floors_file,
            "build_seconds": manifest.get("seconds"),
            "inclusion_above_60": {"median": incl_median, "share_below_0.7": incl_low,
                                   "n_themes": len(big)},
            "coherence": coherence(members, genes, keys),
        }
        rtk_best = (0.0, None)
        if RTK in genes:
            for node, keyset in members.items():
                inter = len(genes[RTK] & frozenset().union(
                    *(genes.get(k, frozenset()) for k in keyset)))
                if inter:
                    union = len(genes[RTK] | frozenset().union(
                        *(genes.get(k, frozenset()) for k in keyset)))
                    value = inter / union if union else 0.0
                    if value > rtk_best[0]:
                        rtk_best = (value, node)
        entry["rtk_gene_jaccard"] = {"best": round(rtk_best[0], 4),
                                     "node": rtk_best[1],
                                     "theme_size": len(members[rtk_best[1]])
                                     if rtk_best[1] else None}
        examples: dict[str, list] = {}
        for low, high in BANDS:
            band = f"{low}-{high}" if high < 10**9 else f"{low}+"
            nodes = sorted(n for n, k in members.items() if band_of(len(k)) == band)
            if not nodes:
                continue
            pick = [nodes[i] for i in rng.choice(len(nodes), min(EXAMPLES, len(nodes)),
                                                 replace=False)]
            examples[band] = [
                {"node": n, "size": len(members[n]),
                 "sources": dict(sorted(
                     {s: sum(1 for k in members[n] if sources.get(k) == s)
                      for s in {sources.get(k, "?") for k in members[n]}}.items())),
                 "members": [names.get(k, k) for k in members[n][:12]]}
                for n in pick]
        entry["examples"] = examples
        report["arms"][name] = entry
        print(f"{name:<4} themes {len(members):>6,}  60-800 {preferred:>4}  "
              f"roots {len(roots):>4}  multi {entry['multi_parent_share']:.1%}", flush=True)

    print()
    header = f"  {'arm':<5}{'themes':>8}{'60-800':>8}"
    for low, high in BANDS:
        header += f"{(f'{low}-{high}' if high < 10**9 else f'{low}+'):>10}"
    print(header)
    for name, entry in report["arms"].items():
        line = f"  {name:<5}{entry['themes']:>8,}{entry['themes_60_to_800']:>8,}"
        for band in entry["bands"]:
            line += f"{entry['bands'][band]:>10,}"
        print(line)

    print()
    print("  gene coherence: observed / size-matched null = ratio (need >= 3x in every band)")
    print(f"  {'arm':<5}{'band':>10}{'n':>7}{'observed':>10}{'null':>9}{'ratio':>8}")
    for name, entry in report["arms"].items():
        for band, cell in entry["coherence"].items():
            flag = "" if (cell["ratio"] or 0) >= 3 else "   <3x"
            print(f"  {name:<5}{band:>10}{cell['n_sampled']:>7}{cell['observed']:>10.4f}"
                  f"{cell['null']:>9.4f}{cell['ratio']:>8.2f}{flag}")

    print()
    print(f"  inclusion among themes larger than {BIG_THEME} members")
    print(f"  {'arm':<5}{'themes':>8}{'median':>9}{'share < 0.7':>13}")
    for name, entry in report["arms"].items():
        cell = entry["inclusion_above_60"]
        if cell["median"] is None:
            print(f"  {name:<5}{cell['n_themes']:>8}{'-':>9}{'-':>13}")
        else:
            print(f"  {name:<5}{cell['n_themes']:>8}{cell['median']:>9.4f}"
                  f"{cell['share_below_0.7']:>13.4f}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
