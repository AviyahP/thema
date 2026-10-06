#!/usr/bin/env python3
"""Naive arm K: build the DAG at each lifetime cutoff and report. EXPLORATORY.

Cutoffs 1.5, 2 and 3 are scored on IDENTICAL candidates, because `naive_k.py` saves every candidate
rather than only the gated ones. The 2 is the declared one; 1.5 and 3 are report-only, added so the
sensitivity to that choice is visible rather than assumed.

The DAG follows the spec: THEMA's consensus merge at Jaccard 0.70, majority-inclusion membership,
**no completion step**, containment edges with multi-parent allowed.

Usage::

    uv run scripts/naive_k_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Bands the report uses, and the lifetime cutoffs.
BANDS: tuple[tuple[int, int], ...] = ((3, 10), (11, 50), (51, 200), (201, 500))
CUTOFFS: tuple[float, ...] = (1.5, 2.0, 3.0)
DECLARED = 2.0
SUPPORT_CUT = 0.33


def band_of(size: int) -> str:
    """Which band a theme size falls in.

    Args:
        size: Member count.

    Returns:
        The band label, or ``"500+"``.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}"
    return "500+"


def build_dag(blocks: np.ndarray, support: np.ndarray, words: int, keys: list[str]) -> dict:
    """Consensus, majority-inclusion membership and containment edges.

    Args:
        blocks: ``(g, words)`` candidate bitsets that passed the gate.
        support: Support per candidate.
        words: Bitset width in bits.
        keys: Universe keys in row order.

    Returns:
        Nodes, edges and the shape counts.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import DEFAULT_JACCARD, DEFAULT_STRAY, consensus
    from thema.ontology.recurrent import hasse

    if not len(blocks):
        return {"nodes": [], "parents": [], "superseded": 0}
    # No completion step, so every member is certain and the inclusion vote is 1.0 throughout.
    # That is what makes membership "majority-inclusion" trivially here: a candidate IS its members.
    inclusions = [{p: 1.0 for p in bits.unpack(b)} for b in blocks]
    verdict = consensus(list(blocks), list(support.tolist()), inclusions, words,
                        stray=DEFAULT_STRAY, jaccard=DEFAULT_JACCARD)
    kept = [(verdict.members[i], float(support[c])) for i, c in enumerate(verdict.accepted)]
    parents_of = hasse([b for b, _s in kept])
    nodes = [
        {"id": f"n{i:05d}", "parents": [f"n{p:05d}" for p in parents_of[i]],
         "members": [keys[p] for p in sorted(bits.unpack(block))], "support": round(sup, 6)}
        for i, (block, sup) in enumerate(kept)
    ]
    return {"nodes": nodes, "superseded": len(verdict.superseded)}


def shape(nodes: list[dict], keys: list[str]) -> dict:
    """Bands, multi-parent share, roots, depth and unplaced.

    Args:
        nodes: The DAG's nodes.
        keys: Universe keys.

    Returns:
        The shape counts.
    """
    bands: dict[str, int] = defaultdict(int)
    for node in nodes:
        bands[band_of(len(node["members"]))] += 1
    roots = [n for n in nodes if not n["parents"]]
    multi = [n for n in nodes if len(n["parents"]) > 1]
    by_id = {n["id"]: n for n in nodes}
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
        parents = by_id[node_id]["parents"]
        depth[node_id] = 0 if not parents else 1 + max(depth_of(p) for p in parents)
        return depth[node_id]

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10 * len(nodes) + 1000))
    depths = [depth_of(n["id"]) for n in nodes] if nodes else []
    placed = {k for n in nodes for k in n["members"]}
    root_ids = {n["id"] for n in roots}
    in_nonroot = {k for n in nodes if n["id"] not in root_ids for k in n["members"]}
    return {
        "themes": len(nodes), "bands": dict(bands), "roots": len(roots),
        "multi_parent": len(multi),
        "multi_parent_share": round(len(multi) / len(nodes), 4) if nodes else 0.0,
        "max_depth": max(depths) if depths else 0,
        "median_depth": float(np.median(depths)) if depths else 0.0,
        "unplaced": len(keys) - len(placed),
        "root_only": len(placed - in_nonroot),
        "effectively_unplaced": (len(keys) - len(placed)) + len(placed - in_nonroot),
    }


def quality(nodes: list[dict], data: Path, keys: list[str]) -> dict:
    """Per-source quality proxy: Reactome members against Reactome sets, GO against GO.

    Restricted per source, as asked. A theme's Reactome members are compared only with curated
    Reactome sets and its GO members only with GO sets, so a mixed theme is judged on each side
    separately rather than penalised for being mixed.

    Args:
        nodes: The DAG's nodes.
        data: The data directory.
        keys: Universe keys.

    Returns:
        Per source, the share of themes whose best match exceeds Jaccard 0.5, overall and per band.
    """
    from thema.data.formats import parse_obo_terms
    from thema.data.hierarchy import read_reactome_relation
    from thema.evaluation import go_parents

    position = {k: i for i, k in enumerate(keys)}
    out: dict[str, dict] = {}
    for prefix, relation in (
        ("reactome:", read_reactome_relation(
            (data / "raw" / "ReactomePathwaysRelation.txt").read_text(
                encoding="utf-8").splitlines())),
        ("go:", go_parents(parse_obo_terms(
            (data / "raw" / "go-basic.obo").read_text(encoding="utf-8").splitlines()))),
    ):
        children: dict[str, list[str]] = {}
        for child, parents in relation.items():
            for parent in parents:
                children.setdefault(parent, []).append(child)
        curated: list[set[int]] = []
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
                curated.append(members)
        holders: list[list[int]] = [[] for _ in range(len(keys))]
        for index, members in enumerate(curated):
            for member in members:
                holders[member].append(index)
        hits, per_band = [], defaultdict(list)
        for node in nodes:
            own = {position[k] for k in node["members"] if k.startswith(prefix)}
            if len(own) < 3:
                continue
            candidates = {c for m in own for c in holders[m]}
            best = 0.0
            for c in candidates:
                other = curated[c]
                inter = len(own & other)
                best = max(best, inter / (len(own) + len(other) - inter))
            hits.append(best > 0.5)
            per_band[band_of(len(node["members"]))].append(best > 0.5)
        out[prefix.rstrip(":")] = {
            "themes_scored": len(hits), "curated_sets": len(curated),
            "share_above_half": round(float(np.mean(hits)), 4) if hits else None,
            "per_band": {b: round(float(np.mean(v)), 4) for b, v in sorted(per_band.items())},
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Report naive K at each cutoff.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--dir", type=Path, default=Path("data/ontology/v0.3/naive_k_v2"))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    words = bits.words_for(n) * bits.WORD
    titles = {p.key: p.name for p in PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")).pathways}

    sides = {}
    for side in ("real", "3001"):
        path = args.dir / f"{side}.npz"
        if path.is_file():
            with np.load(path) as handle:
                sides[side] = {k: handle[k] for k in handle.files}
    if "real" not in sides:
        print("the real side is not built")
        return 1

    report: dict = {"support_cut": SUPPORT_CUT, "cutoffs": list(CUTOFFS),
                    "declared_cutoff": DECLARED, "sides": {}}
    print(f"NAIVE K REPORT  support >= {SUPPORT_CUT}, lifetime in {CUTOFFS} "
          f"(declared {DECLARED})")

    dags: dict[float, dict] = {}
    for cut in CUTOFFS:
        row: dict = {}
        for side, data in sides.items():
            keep = np.flatnonzero((data["support"] >= SUPPORT_CUT)
                                  & np.isfinite(data["lifetime"])
                                  & (data["lifetime"] >= cut))
            built = build_dag(data["members"][keep], data["support"][keep], words, keys)
            info = shape(built["nodes"], keys)
            info["gated_candidates"] = int(len(keep))
            info["superseded"] = built["superseded"]
            row[side] = info
            if side == "real":
                dags[cut] = built
        report["sides"][str(cut)] = row
    print(f"\n  {'cutoff':<8}{'real themes':>13}{'scramble':>10}{'scr/real':>10}"
          f"{'3-10':>8}{'11-50':>8}{'51-200':>8}{'201-500':>9}{'500+':>7}")
    for cut in CUTOFFS:
        r = report["sides"][str(cut)]["real"]
        s = report["sides"][str(cut)].get("3001", {})
        ratio = (s.get("themes", 0) / r["themes"]) if r["themes"] else float("nan")
        mark = "  <= DECLARED" if cut == DECLARED else ""
        print(f"  {cut:<8}{r['themes']:>13,}{s.get('themes', 0):>10,}{ratio:>10.2%}"
              f"{r['bands'].get('3-10', 0):>8,}{r['bands'].get('11-50', 0):>8,}"
              f"{r['bands'].get('51-200', 0):>8,}{r['bands'].get('201-500', 0):>9,}"
              f"{r['bands'].get('500+', 0):>7,}{mark}")

    print(f"\n  {'cutoff':<8}{'roots':>8}{'multi-parent':>14}{'max depth':>11}"
          f"{'median depth':>14}{'unplaced':>10}{'eff. unplaced':>15}")
    for cut in CUTOFFS:
        r = report["sides"][str(cut)]["real"]
        print(f"  {cut:<8}{r['roots']:>8,}{r['multi_parent_share']:>13.1%}"
              f"{r['max_depth']:>11}{r['median_depth']:>14.1f}"
              f"{r['unplaced']:>10,}{r['effectively_unplaced']:>15,}")

    # Quality proxy, per source, for K at each cutoff and for the comparison builds.
    print("\n  QUALITY PROXY -- share of themes whose best match to a curated set of the SAME "
          "source exceeds Jaccard 0.5")
    print(f"    {'build':<28}{'reactome':>10}{'n':>8}{'GO':>10}{'n':>8}")
    report["quality"] = {}
    for cut in CUTOFFS:
        q = quality(dags[cut]["nodes"], args.data, keys)
        report["quality"][f"K lifetime>={cut}"] = q
        print(f"    {'K, lifetime >= ' + str(cut):<28}"
              f"{(q['reactome']['share_above_half'] or 0):>9.1%}"
              f"{q['reactome']['themes_scored']:>8,}"
              f"{(q['go']['share_above_half'] or 0):>9.1%}{q['go']['themes_scored']:>8,}")
    for label, path in (("A (frozen v0.3)", root / "recurrent_dag_10770"),
                        ("HiDeF k15 maxres 25", root / "hidef_10770_k15"),
                        ("HiDeF k15 maxres 50", root / "hidef_10770_k15_maxres50"),
                        ("HiDeF k15 maxres 100", root / "hidef_10770_k15_maxres100")):
        if not (path / "members.tsv").is_file():
            print(f"    {label:<28}{'not built':>10}")
            continue
        grouped: dict[str, list[str]] = defaultdict(list)
        with (path / "members.tsv").open(encoding="utf-8", newline="") as handle:
            for row_ in csv.DictReader(handle, delimiter="\t"):
                grouped[row_["node"]].append(row_["key"])
        nodes = [{"id": k, "parents": [], "members": v} for k, v in grouped.items()]
        q = quality(nodes, args.data, keys)
        report["quality"][label] = q
        print(f"    {label:<28}{(q['reactome']['share_above_half'] or 0):>9.1%}"
              f"{q['reactome']['themes_scored']:>8,}"
              f"{(q['go']['share_above_half'] or 0):>9.1%}{q['go']['themes_scored']:>8,}")

    # Ten random themes from two bands, at the declared cutoff.
    rng = np.random.default_rng(0)
    report["examples"] = {}
    for band in ("3-10", "51-200"):
        pool = [node for node in dags[DECLARED]["nodes"]
                if band_of(len(node["members"])) == band]
        pick = rng.choice(len(pool), size=min(10, len(pool)), replace=False) if pool else []
        print(f"\n  10 RANDOM THEMES, band {band}, at the declared lifetime >= {DECLARED} "
              f"({len(pool):,} available)")
        shown = []
        for i in np.atleast_1d(pick).tolist():
            node = pool[i]
            names = [titles.get(k, k) for k in node["members"]]
            shown.append({"size": len(names), "support": node["support"], "titles": names})
            print(f"    [{len(names)} members, support {node['support']:.2f}] "
                  + "; ".join(t[:44] for t in names[:4]))
        report["examples"][band] = shown

    # Export the declared cutoff's DAG in the v0.3 schema, at the path the spec names.
    from thema.ontology import export
    from thema.ontology.base import Node, Ontology

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    chosen = dags[DECLARED]["nodes"]
    placed = {k for node in chosen for k in node["members"]}
    manifest = {
        "method": "naive_k", "engine": "mutual-rank ladder", "exploratory": True,
        "n": n, "runs": int(sides["real"]["support_only"][0] * 0) + 100,
        "ladder": "3,4,5,6,8,10,13,16,20,25,32,40,50,64,80,100; next after last 128",
        "support_cut": SUPPORT_CUT, "lifetime_cut": DECLARED,
        "calibrated": False,
        "cutoffs_chosen_in_advance": True,
        "note": "NAIVE probe: fixed cutoffs, no calibration, no completion step. Not a candidate.",
        "n_nodes": len(chosen),
        "n_unplaced": n - len(placed),
    }
    ontology = Ontology(
        method="naive_k",
        params={"support_cut": SUPPORT_CUT, "lifetime_cut": DECLARED, "runs": 100},
        nodes=tuple(
            Node(id=node["id"], parents=tuple(node["parents"]),
                 members=tuple((k, 1.0) for k in node["members"]),
                 support=node["support"])
            for node in chosen
        ),
        unplaced=tuple(k for k in keys if k not in placed),
        manifest=manifest,
    )
    written = export.write(ontology, args.data / "ontology", "0.3x_engines", genes, manifest,
                           dry_run=False, info=info, directory="K_naive")
    print(f"\n  DAG exported -> {written}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
