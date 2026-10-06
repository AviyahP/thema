#!/usr/bin/env python3
"""KC2: build the DAG at the chosen c, then the deciding recall/precision table. EXPLORATORY.

**Band assignment follows the evaluation protocol's clarification 2**, so the two measures are not
banded the same way and should not be: **recall bands are set by the CURATED set's size**, because
recall asks what share of curated biology at a given grain is recovered; **precision bands are set
by the THEME's size**, because precision asks what share of what an arm produces at a given grain is
real. Banding both by theme size would make recall unanswerable for any band an arm declines to
populate.

Usage::

    uv run scripts/kc2_report.py --c 0.15
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))
MATCH = 0.5


def band_of(size: int) -> str:
    """Band label for a size.

    Args:
        size: Member count.

    Returns:
        The label, or ``"500+"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "500+"


def curated(data: Path, keys: list[str], prefix: str) -> list[set[int]]:
    """Curated sets for one source: each node plus all its descendants, as E1 defines them.

    Args:
        data: The data directory.
        keys: Universe keys in row order.
        prefix: ``reactome:`` or ``go:``.

    Returns:
        One index set per curated node with at least three members in the universe.
    """
    from thema.data.formats import parse_obo_terms
    from thema.data.hierarchy import read_reactome_relation
    from thema.evaluation import go_parents

    position = {k: i for i, k in enumerate(keys)}
    if prefix == "reactome:":
        relation = read_reactome_relation(
            (data / "raw" / "ReactomePathwaysRelation.txt").read_text(
                encoding="utf-8").splitlines())
    else:
        relation = go_parents(parse_obo_terms(
            (data / "raw" / "go-basic.obo").read_text(encoding="utf-8").splitlines()))
    children: dict[str, list[str]] = {}
    for child, parents in relation.items():
        for parent in parents:
            children.setdefault(parent, []).append(child)
    out: list[set[int]] = []
    for node in set(relation) | set(children):
        stack, seen = [node], set()
        while stack:
            at = stack.pop()
            if at in seen:
                continue
            seen.add(at)
            stack.extend(children.get(at, ()))
        members = {position[f"{prefix}{t}"] for t in seen if f"{prefix}{t}" in position}
        if len(members) >= 3:
            out.append(members)
    return out


def recall_precision(themes: list[set[int]], sets: list[set[int]], n: int) -> dict:
    """Per-band recall and precision at best-match Jaccard > 0.5.

    Args:
        themes: Theme member index sets, already restricted to the source.
        sets: Curated sets for that source.
        n: Universe size.

    Returns:
        Per band, recall and precision with their denominators.
    """
    holders_theme: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(themes):
        for member in members:
            holders_theme[member].append(index)
    holders_set: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(sets):
        for member in members:
            holders_set[member].append(index)

    def best(query: set[int], holders: list[list[int]], pool: list[set[int]]) -> float:
        """Best Jaccard of a query against anything sharing a member.

        Args:
            query: The member set.
            holders: Inverted index.
            pool: The candidate sets.

        Returns:
            The best Jaccard.
        """
        out = 0.0
        for other in {c for m in query for c in holders[m]}:
            o = pool[other]
            inter = len(query & o)
            out = max(out, inter / (len(query) + len(o) - inter))
        return out

    # Recall: banded by the CURATED set's size.
    rec: dict[str, list[bool]] = defaultdict(list)
    for members in sets:
        rec[band_of(len(members))].append(best(members, holders_theme, themes) > MATCH)
    # Precision: banded by the THEME's size.
    pre: dict[str, list[bool]] = defaultdict(list)
    for members in themes:
        pre[band_of(len(members))].append(best(members, holders_set, sets) > MATCH)

    bands = [f"{lo}-{hi}" for lo, hi in BANDS]
    return {
        b: {
            "recall": round(float(np.mean(rec[b])), 4) if rec[b] else None,
            "n_curated": len(rec[b]),
            "precision": round(float(np.mean(pre[b])), 4) if pre[b] else None,
            "n_themes": len(pre[b]),
        }
        for b in bands
    }


def read_build(path: Path) -> list[list[str]]:
    """Theme member key lists from an exported build.

    Args:
        path: A build directory.

    Returns:
        One key list per theme.
    """
    grouped: dict[str, list[str]] = defaultdict(list)
    with (path / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            grouped[row["node"]].append(row["key"])
    return list(grouped.values())


def main(argv: list[str] | None = None) -> int:
    """Build and report.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from kc2_sweep import FINE_T, counts, units_for
    from thema.data.pathways import PathwayCollection
    from thema.embed import centre_and_renormalise
    from thema.ontology import bitset as bits
    from thema.ontology import export, kc, kc2
    from thema.ontology.base import Node, Ontology
    from thema.ontology.recurrent import hasse
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--c", type=float, required=True)
    parser.add_argument("--share", type=float, default=kc.JOIN_SHARE)
    parser.add_argument("--max-levels", type=int, default=kc.MAX_LEVELS)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    position = {k: i for i, k in enumerate(keys)}
    base, _mean = centre_and_renormalise(embedded.vectors)
    base = np.ascontiguousarray(base.astype(np.float32))
    marks: dict[str, float] = {}

    clock = time.perf_counter()
    kept, units = units_for(base, n, FINE_T)
    marks["fine level and units"] = time.perf_counter() - clock
    clock = time.perf_counter()
    levels = kc2.levels_at(units, base, args.c, args.share, args.max_levels)
    marks["levels"] = time.perf_counter() - clock

    every = list(kept) + [m for level in levels for m in level]
    seen: set[bytes] = set()
    themes: list[np.ndarray] = []
    for m in every:
        key = m.astype(np.int32).tobytes()
        if key not in seen:
            seen.add(key)
            themes.append(m)
    print(f"KC2  c={args.c}, fine t={FINE_T}, share {args.share}")
    print(f"  fine kept {len(kept):,}; units {len(units):,}; "
          f"levels {[len(x) for x in levels]}; themes {len(themes):,}")

    clock = time.perf_counter()
    blocks = [bits.pack(m.tolist(), n) for m in themes]
    parents_of = hasse(blocks)
    ids = [f"n{i:05d}" for i in range(len(themes))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents_of[i]),
             members=tuple((keys[p], 1.0) for p in themes[i].tolist()), support=1.0)
        for i in range(len(themes))
    )
    marks["containment DAG"] = time.perf_counter() - clock

    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = [node for node in nodes if len(node.parents) > 1]
    by_id = {node.id: node for node in nodes}
    depth: dict[str, int] = {}

    def depth_of(node_id: str) -> int:
        """Longest path from a root.

        Args:
            node_id: The node.

        Returns:
            Its depth.
        """
        if node_id in depth:
            return depth[node_id]
        parents = by_id[node_id].parents
        depth[node_id] = 0 if not parents else 1 + max(depth_of(p) for p in parents)
        return depth[node_id]

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10 * len(nodes) + 1000))
    depths = [depth_of(node.id) for node in nodes]
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {
        "themes": len(nodes), "bands": counts(themes), "roots": len(roots),
        "multi_parent": len(multi),
        "multi_parent_share": round(len(multi) / len(nodes), 4) if nodes else 0.0,
        "max_depth": max(depths) if depths else 0,
        "median_depth": float(np.median(depths)) if depths else 0.0,
        "unplaced": len(unplaced),
        "root_only": len(placed - in_nonroot),
        "effectively_unplaced": len(unplaced) + len(placed - in_nonroot),
    }
    print(f"  roots {shape['roots']:,}  multi-parent {shape['multi_parent_share']:.1%}  "
          f"max depth {shape['max_depth']}  median depth {shape['median_depth']:.1f}  "
          f"unplaced {shape['unplaced']:,}  effectively unplaced "
          f"{shape['effectively_unplaced']:,}")

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    titles = {p.key: p.name for p in collection.pathways}
    manifest = {"method": "kc2", "engine": "mutual-rank fine level + absolute near-cliques",
                "exploratory": True, "n": n, "fine_lifetime": FINE_T,
                "close_absolute": args.c, "join_share": args.share,
                "max_levels": args.max_levels, "calibrated_on": "scrambles 3001-3003",
                "note": "EXPLORATORY probe. Not a declared arm.", **shape}
    written = export.write(
        Ontology(method="kc2", params={"c": args.c, "fine_t": FINE_T, "share": args.share},
                 nodes=nodes, unplaced=unplaced, manifest=manifest),
        args.data / "ontology", "0.3x_engines", genes, manifest,
        dry_run=False, info=info, directory="KC2")
    print(f"  DAG -> {written}")

    # ---- the deciding table
    builds: dict[str, list[list[str]]] = {
        "KC2": [[keys[p] for p in m.tolist()] for m in themes],
    }
    for label, path in (("naive K", root / "../v0.3x_engines/K_naive"),
                        ("A (frozen)", root / "recurrent_dag_10770"),
                        ("HiDeF m25", root / "hidef_10770_k15"),
                        ("HiDeF m50", root / "hidef_10770_k15_maxres50"),
                        ("HiDeF m100", root / "hidef_10770_k15_maxres100")):
        resolved = path.resolve()
        if (resolved / "members.tsv").is_file():
            builds[label] = read_build(resolved)

    table: dict[str, dict] = {}
    for source, prefix in (("reactome", "reactome:"), ("go", "go:")):
        sets = curated(args.data, keys, prefix)
        print(f"\n  {source.upper()}: {len(sets):,} curated sets")
        header = (f"    {'build':<13}" + "".join(
            f"{b:>21}" for b in [f'{lo}-{hi}' for lo, hi in BANDS]))
        print(header)
        print(f"    {'':<13}" + "".join(f"{'recall / prec':>21}" for _ in BANDS))
        for label, build in builds.items():
            own = [{position[k] for k in theme if k.startswith(prefix)} for theme in build]
            own = [s for s in own if len(s) >= 3]
            got = recall_precision(own, sets, n)
            table.setdefault(source, {})[label] = got
            cells = ""
            for lo, hi in BANDS:
                g = got[f"{lo}-{hi}"]
                r = "  --" if g["recall"] is None else f"{g['recall']:.1%}"
                p = "  --" if g["precision"] is None else f"{g['precision']:.1%}"
                ns = f"({g['n_curated']},{g['n_themes']})"
                cells += f"{r + ' / ' + p:>14}{ns:>7}"
            print(f"    {label:<13}{cells}")

    rng = np.random.default_rng(0)
    examples: dict[str, list] = {}
    for band in ("51-200", "201-500"):
        pool = [m for m in themes if band_of(len(m)) == band]
        pick = rng.choice(len(pool), size=min(10, len(pool)), replace=False) if pool else []
        print(f"\n  10 RANDOM THEMES, band {band} ({len(pool):,} available)")
        shown = []
        for i in np.atleast_1d(pick).tolist():
            names = [titles.get(keys[p], keys[p]) for p in pool[i].tolist()]
            shown.append({"size": len(names), "titles": names})
            print(f"    [{len(names)}] " + "; ".join(t[:40] for t in names[:5]))
        examples[band] = shown

    print("\n  timing: " + ", ".join(f"{k} {v:.1f}s" for k, v in marks.items())
          + f"; peak {peak_mb():.0f} MB")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "c": args.c, "fine_t": FINE_T, "share": args.share, "shape": shape,
            "table": table, "examples": examples,
            "timing_seconds": {k: round(v, 1) for k, v in marks.items()},
            "peak_mb": round(peak_mb(), 1),
        }, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
