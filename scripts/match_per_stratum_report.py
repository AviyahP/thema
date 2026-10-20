#!/usr/bin/env python3
"""Prompt 47's report: arms M and Mm side by side with O50s.

Read-only over all three builds. Usage::

    uv run scripts/match_per_stratum_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np

#: The declared theme size bands.
BANDS = ((3, 5), (6, 11), (12, 24), (25, 49), (50, 99), (100, 199), (200, 399), (400, 799),
         (800, 1599), (1600, 10 ** 9))

#: A theme this large is a giant.
GIANT = 1000

#: A root this small is a small root.
SMALL_ROOT = 50

#: Counterpart thresholds.
SAME = 0.90
KEPT = 0.70

#: The small band the report tracks.
SMALL = (3, 50)

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80

#: Report item 6's named O50s roots.
NAMED = ("n01027", "n04526", "n04670", "n04671", "n03316", "n04672", "n04995", "n05001")


def band_of(size: int) -> str:
    """The band label a size falls in.

    Args:
        size: Theme size.

    Returns:
        The band label.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
    return "under 3"


def read_build(path: Path) -> dict[str, object]:
    """One build's nodes, members and manifest.

    Args:
        path: The build directory.

    Returns:
        ``nodes``, ``members``, ``manifest``.
    """
    with (path / "nodes.tsv").open(encoding="utf-8") as handle:
        nodes = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return {"nodes": nodes, "members": dict(members),
            "manifest": json.loads((path / "manifest.json").read_text())}


def best_matches(left: Mapping[str, set[str]], right: Mapping[str, set[str]],
                 keys: Sequence[str]) -> dict[str, tuple[str, float]]:
    """For each set on the left, its best Jaccard partner on the right, by bitset.

    Args:
        left: Node id to member keys.
        right: Node id to member keys.
        keys: Every pathway key, in bit order.

    Returns:
        Left node id to ``(best right id, Jaccard)``.
    """
    index = {key: i for i, key in enumerate(keys)}
    words = (len(keys) + 63) // 64

    def pack(group: Mapping[str, set[str]]) -> tuple[list[str], np.ndarray]:
        """Ids and a bitset matrix."""
        ids = sorted(group)
        out = np.zeros((len(ids), words), dtype=np.uint64)
        for row, node in enumerate(ids):
            for key in group[node]:
                position = index[key]
                out[row, position // 64] |= np.uint64(1) << np.uint64(position % 64)
        return ids, out

    left_ids, left_bits = pack(left)
    right_ids, right_bits = pack(right)
    right_sizes = np.bitwise_count(right_bits).sum(axis=1).astype(np.int64)
    out: dict[str, tuple[str, float]] = {}
    for row, node in enumerate(left_ids):
        mine = left_bits[row]
        size = int(np.bitwise_count(mine).sum())
        shared = np.bitwise_count(mine[None, :] & right_bits).sum(axis=1).astype(np.int64)
        union = size + right_sizes - shared
        with np.errstate(divide="ignore", invalid="ignore"):
            scores = np.where(union > 0, shared / union, 0.0)
        if not len(scores):
            out[node] = ("", 0.0)
            continue
        pick = int(np.argmax(scores))
        out[node] = (right_ids[pick], float(scores[pick]))
    return out


def shape_of(build: Mapping[str, object]) -> dict[str, object]:
    """Roots, small roots, giants, children and the multi-parent share.

    Args:
        build: One build, as :func:`read_build` returns it.

    Returns:
        The shape figures.
    """
    nodes, members = build["nodes"], build["members"]
    roots = [n for n, row in nodes.items() if not row["parents"].strip()]
    kids = [len(row["children"].split()) for row in nodes.values()]
    multi = sum(1 for row in nodes.values() if len(row["parents"].split()) > 1)
    giants = sorted(((len(members[n]), n) for n in members if len(members[n]) > GIANT),
                    reverse=True)
    return {"n_nodes": len(nodes), "n_roots": len(roots),
            "n_small_roots": sum(1 for n in roots if len(members[n]) <= SMALL_ROOT),
            "giants": [(n, s) for s, n in giants],
            "children_max": max(kids, default=0),
            "children_median": float(statistics.median(kids)) if kids else 0.0,
            "multi_parent": multi,
            "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
            "roots": roots}


def main(argv: list[str] | None = None) -> int:
    """Print the report and write the reviewer's root tables."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--root", type=Path, default=Path("data/ontology/v0.4-leaves"))
    parser.add_argument("--sweep", type=Path,
                        default=Path("data/experiments/match_per_stratum_2026-10-19"))
    args = parser.parse_args(argv)

    import match_per_stratum as mps
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    base = read_build(args.o50s)
    arms = {name: read_build(args.root / f"thema_L_x2_O50s_{name}")
            for name in ("M", "Mm")
            if (args.root / f"thema_L_x2_O50s_{name}" / "nodes.tsv").exists()}
    table = json.loads((args.sweep / "strata.json").read_text())["table"]
    om = base["members"]
    allk = sorted({k for v in om.values() for k in v})
    print("THE MATCH THRESHOLD PER SIZE STRATUM (O50s-M). Declared 19 Oct 2026; adopts nothing.\n")

    print("=" * 112)
    print("1. PER STRATUM: THE SWEEP, THE CHOSEN THETA AND THE FLOOR")
    print("=" * 112)
    print(f"  {'stratum':<9}" + "".join(f"{'adm@' + str(t):>11}" for t in mps.THETAS)
          + f"{'CHOSEN':>8}{'floor':>11}{'real':>8}{'calib':>11}" + "".join(
              f"{'held ' + n:>12}" for n in arms))
    held = {name: {e["stratum"]: e for e in arms[name]["manifest"]["confirmed"]["strata"]}
            for name in arms}
    for entry in table:
        cells = "".join(f"{entry['admitted'][str(t)]:>11,}" for t in mps.THETAS)
        chosen = entry["chosen_theta"]
        tail = "".join(
            f"{str(held[n].get(entry['stratum'], {}).get('heldout_fdr')):>12}" for n in arms)
        print(f"  {entry['stratum']:<9}{cells}{(str(chosen) if chosen else 'none'):>8}"
              f"{str(entry['effective']):>11}{entry['real']:>8,}"
              f"{str(entry['calibration_fdr']):>11}{tail}")
    picked = Counter(e["chosen_theta"] for e in table if e["chosen_theta"])
    print(f"\n  chosen thetas: {dict(picked)}; "
          f"{sum(1 for e in table if e['chosen_theta'] is None)} stratum/strata admit nothing")
    for name in arms:
        confirmed = arms[name]["manifest"]["confirmed"]
        worst = max((e["heldout_fdr"] or 0.0) for e in confirmed["strata"])
        inside = (confirmed["overall_fdr"] or 0) <= mps.CAP_OVERALL and worst <= mps.CAP_STRATUM
        print(f"  arm {name}: held-out overall {confirmed['overall_fdr']} "
              f"(cap {mps.CAP_OVERALL}), worst stratum {round(worst, 5)} "
              f"(cap {mps.CAP_STRATUM}) -- {'INSIDE both caps' if inside else 'OVER A CAP'}")
        if name == "Mm":
            lifted = [e["stratum"] for e in arms[name]["manifest"]["floors"]
                      if e.get("m_applied")]
            print(f"    the 0.33 minimum lifted the floor in: {lifted or 'no stratum'}")

    print("\n" + "=" * 112)
    print("2. THEMES BY SIZE BAND")
    print("=" * 112)
    labels = [f"{a}-{b}" if b < 10 ** 9 else f"{a}+" for a, b in BANDS]
    counts = {"O50s": Counter(band_of(len(v)) for v in om.values())}
    for name in arms:
        counts[name] = Counter(band_of(len(v)) for v in arms[name]["members"].values())
    print(f"  {'band':<12}" + "".join(f"{k:>10}" for k in counts))
    for one in labels:
        print(f"  {one:<12}" + "".join(f"{counts[k].get(one, 0):>10,}" for k in counts))
    print(f"  {'TOTAL':<12}" + "".join(f"{sum(counts[k].values()):>10,}" for k in counts))

    print("\n" + "=" * 112)
    print("3. SHAPE")
    print("=" * 112)
    shapes = {"O50s": shape_of(base)}
    for name in arms:
        shapes[name] = shape_of(arms[name])
    for key, title in (("n_nodes", "themes"), ("n_roots", "roots"),
                       ("n_small_roots", f"roots of {SMALL_ROOT} or fewer"),
                       ("children_max", "children max"),
                       ("children_median", "children median"),
                       ("multi_parent_share", "multi-parent share")):
        print(f"  {title:<28}" + "".join(f"{str(shapes[k][key]):>14}" for k in shapes))
    for k in shapes:
        print(f"  {k} giants: " + (", ".join(f"{n} ({s:,})" for n, s in shapes[k]["giants"])
                                   or "none"))

    print("\n" + "=" * 112)
    print("4. SMALL THEMES, AND O50s COUNTERPARTS")
    print("=" * 112)
    low, high = SMALL
    n_small_base = sum(1 for v in om.values() if low <= len(v) <= high)
    matched: dict[str, dict[str, tuple[str, float]]] = {}
    for name in arms:
        nm = arms[name]["members"]
        n_small = sum(1 for v in nm.values() if low <= len(v) <= high)
        matched[name] = best_matches(om, nm, allk)
        at_same = sum(1 for _, s in matched[name].values() if s >= SAME)
        print(f"  arm {name}: themes of {low}-{high}: {n_small:,} against O50s's "
              f"{n_small_base:,} = {n_small / n_small_base:.1%}")
        print(f"    O50s themes with a counterpart at J >= {SAME}: {at_same:,} of "
              f"{len(om):,} = {at_same / len(om):.1%}")
    return more(args, base, arms, shapes, matched, om, allk, table,
                reactome_roots, read_reactome_relation, targets, go_edges, PRIMARY_RELATIONS)


def more(args: argparse.Namespace, base: Mapping[str, object],
         arms: Mapping[str, Mapping[str, object]], shapes: Mapping[str, Mapping[str, object]],
         matched: Mapping[str, Mapping[str, tuple[str, float]]],
         om: Mapping[str, set[str]], allk: Sequence[str], table: Sequence[Mapping[str, object]],
         reactome_roots: Callable[..., object], read_reactome_relation: Callable[..., object],
         targets: Callable[..., object], go_edges: Callable[..., object],
         relations: Sequence[str]) -> int:
    """Items 5 to 7, and the reviewer's root tables.

    Args:
        args: Parsed arguments.
        base: The O50s build.
        arms: The M and Mm builds.
        shapes: Each build's shape figures.
        matched: Per arm, each O50s theme's best counterpart.
        om: O50s node to member keys.
        allk: Every pathway key.
        table: The per-stratum table.
        reactome_roots: The branch finder.
        read_reactome_relation: The relation reader.
        targets: The summary target builder.
        go_edges: The GO edge reader.
        relations: The primary GO relations.

    Returns:
        0.
    """
    import match_per_stratum as mps

    small_roots = [n for n in shapes["O50s"]["roots"] if len(om[n]) <= SMALL_ROOT]
    print("\n" + "=" * 112)
    print(f"5. THE {len(small_roots)} O50s SMALL ROOTS")
    print("=" * 112)
    for name in arms:
        nm = arms[name]["members"]
        nodes = arms[name]["nodes"]
        still = 0
        have = 0
        for node in small_roots:
            partner, score = matched[name][node]
            if score >= KEPT:
                have += 1
                if partner and not nodes[partner]["parents"].strip():
                    still += 1
        print(f"  arm {name}: {have} of {len(small_roots)} have a counterpart at J >= {KEPT} "
              f"= {have / len(small_roots):.1%}; of those, {still} are STILL ROOTS "
              f"= {still / max(have, 1):.1%}")
        del nm

    print("\n" + "=" * 112)
    print("6. THE NAMED O50s ROOTS")
    print("=" * 112)
    print(f"  {'O50s root':<10}{'size':>7}" + "".join(
        f"  {('arm ' + n):<12}{'J':>7}{'root?':>7}" for n in arms))
    for node in NAMED:
        if node not in om:
            print(f"  {node:<10}{'absent':>7}")
            continue
        cells = []
        for name in arms:
            partner, score = matched[name][node]
            is_root = (partner and not arms[name]["nodes"][partner]["parents"].strip())
            cells.append(f"  {partner:<12}{score:>7.3f}{('yes' if is_root else 'no'):>7}")
        print(f"  {node:<10}{len(om[node]):>7,}" + "".join(cells))

    print("\n" + "=" * 112)
    print("7. SUMMARY PLACEMENT AND REACTOME")
    print("=" * 112)
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    names = {f"{r['source']}:{r['source_id']}": r["name"] for r in rows}
    universe = set(allk)
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {
        f"reactome:{c}": {f"reactome:{p}" for p in ps} for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(), relations).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}
    key_sets = targets(edges, sorted(set(names) - universe), universe, min_size=3)
    kids: dict[str, set[str]] = defaultdict(set)
    for child, ups in rel.items():
        for parent in ups:
            kids[parent].add(child)

    def descend(root: str) -> set[str]:
        """Every Reactome pathway under a top-level branch."""
        seen, stack = set(), [root]
        while stack:
            node = stack.pop()
            for kid in kids.get(node, ()):
                if kid not in seen:
                    seen.add(kid)
                    stack.append(kid)
        return seen

    branches = {}
    for root in sorted(reactome_roots(rel)):
        leaves = {f"reactome:{k}" for k in descend(root) | {root}} & universe
        if len(leaves) >= 3:
            branches[root] = leaves

    def score_pool(pool: Mapping[str, set[str]]) -> tuple[int, float]:
        """Summary placement and the Reactome median best Jaccard."""
        items = list(pool.values())
        total = sum(1 for leaves in key_sets.values()
                    if any(len(leaves & one) >= HOME_SHARE * len(leaves) for one in items))
        best = statistics.median([
            max((len(leaves & one) / len(leaves | one) for one in items), default=0.0)
            for leaves in branches.values()])
        return total, best

    pools = {"O50s": om}
    pools.update({name: arms[name]["members"] for name in arms})
    for name, pool in pools.items():
        total, best = score_pool(pool)
        print(f"  {name:<6} placement {total:,} of {len(key_sets):,} = "
              f"{total / len(key_sets):.1%}; Reactome median best J {best:.3f}", flush=True)

    chosen = {e["stratum"]: e["chosen_theta"] for e in table}
    for name in arms:
        folder = args.sweep / name
        folder.mkdir(parents=True, exist_ok=True)
        nm, nodes = arms[name]["members"], arms[name]["nodes"]
        roots = shapes[name]["roots"]
        with (folder / "roots.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, delimiter="\t", lineterminator="\n",
                fieldnames=["node", "size", "support", "theta", "n_children", "members"])
            writer.writeheader()
            for node in sorted(roots, key=lambda n: -len(nm[n])):
                index = mps.stratum_of(len(nm[node]))
                stratum = mps.label(*mps.STRATA[index]) if index >= 0 else ""
                writer.writerow({
                    "node": node, "size": len(nm[node]),
                    "support": nodes[node]["support"],
                    "theta": chosen.get(stratum, ""),
                    "n_children": len(nodes[node]["children"].split()),
                    "members": " ".join(sorted(nm[node]))})
        print(f"  -> {folder / 'roots.tsv'}  ({len(roots)} roots)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
