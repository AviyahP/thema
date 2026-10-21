#!/usr/bin/env python3
"""Prompt 50's report and reviewer material for C1b, side by side with O50s.

Read-only over both builds. Usage::

    uv run scripts/core_construction_c1b_report.py
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

#: The reading bands for the non-root sample.
READ_BANDS = ((3, 9), (10, 19), (20, 49), (50, 199), (200, 10 ** 9))

#: A node over this is a giant, by the prompt's definition.
GIANT = 1280

#: A root this small is a small root.
SMALL_ROOT = 50

#: Counterpart and overlap thresholds.
SAME = 0.90
CHAIN = 0.85
TWIN = 0.50

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80

#: Reviewer sampling.
MAX_ROOTS_READ = 300
PER_BAND = 24
SEED = 20261020
BATCH_LINES = 2600

#: The named O50s roots item 5 asks about.
NAMED = ("n01027", "n04526", "n04670", "n04671", "n03316", "n04672", "n04995", "n05001")


def band_of(size: int, bands: Sequence[tuple[int, int]] = BANDS) -> str | None:
    """The band label a size falls in.

    Args:
        size: Theme size.
        bands: The band edges.

    Returns:
        The label, or None.
    """
    for low, high in bands:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
    return None


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


def pack(group: Mapping[str, set[str]], index: Mapping[str, int], words: int
         ) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Ids, bitsets and sizes.

    Args:
        group: Node id to member keys.
        index: Pathway key to bit position.
        words: Bitset width in words.

    Returns:
        ``(ids, bitsets, sizes)``.
    """
    ids = sorted(group)
    out = np.zeros((len(ids), words), dtype=np.uint64)
    for row, node in enumerate(ids):
        for key in group[node]:
            position = index[key]
            out[row, position // 64] |= np.uint64(1) << np.uint64(position % 64)
    return ids, out, np.bitwise_count(out).sum(axis=1).astype(np.int64)


def best_matches(left: Mapping[str, set[str]], right: Mapping[str, set[str]],
                 keys: Sequence[str]) -> dict[str, tuple[str, float]]:
    """Each left set's best Jaccard partner on the right.

    Args:
        left: Node id to member keys.
        right: Node id to member keys.
        keys: Every pathway key.

    Returns:
        Left node id to ``(best right id, Jaccard)``.
    """
    index = {key: i for i, key in enumerate(keys)}
    words = (len(keys) + 63) // 64
    left_ids, left_bits, left_sz = pack(left, index, words)
    right_ids, right_bits, right_sz = pack(right, index, words)
    out: dict[str, tuple[str, float]] = {}
    for row, node in enumerate(left_ids):
        if not len(right_ids):
            out[node] = ("", 0.0)
            continue
        shared = np.bitwise_count(left_bits[row][None, :] & right_bits).sum(axis=1)
        union = left_sz[row] + right_sz - shared
        with np.errstate(divide="ignore", invalid="ignore"):
            scores = np.where(union > 0, shared / union, 0.0)
        pick = int(np.argmax(scores))
        out[node] = (right_ids[pick], float(scores[pick]))
    return out


def depths(nodes: Mapping[str, Mapping[str, str]], members: Mapping[str, set[str]]
           ) -> dict[str, object]:
    """Levels from a pathway to its root: the shortest and longest upward path.

    Args:
        nodes: Node rows.
        members: Node to member keys.

    Returns:
        Median and maximum levels over the pathways, and the per-node depth.
    """
    parents = {node: [p for p in row["parents"].split() if p] for node, row in nodes.items()}
    depth: dict[str, int] = {}

    def climb(node: str) -> int:
        """Longest upward path from a node to a root."""
        if node in depth:
            return depth[node]
        depth[node] = 0
        depth[node] = 0 if not parents[node] else 1 + max(climb(p) for p in parents[node])
        return depth[node]

    for node in nodes:
        climb(node)
    per: dict[str, int] = {}
    for node, one in members.items():
        for key in one:
            per[key] = max(per.get(key, 0), depth[node])
    values = sorted(per.values())
    return {"median": float(statistics.median(values)) if values else 0.0,
            "max": max(values) if values else 0, "depth": depth}


def main(argv: list[str] | None = None) -> int:
    """Print the report and write the reviewer material."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--c1b", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_C1b"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/core_construction_C1b_2026-10-20"))
    args = parser.parse_args(argv)

    import core_construction_c1b as c1b
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    new = read_build(args.c1b)
    old = read_build(args.o50s)
    record = json.loads((args.c1b / "c1b.json").read_text())
    nm, om = new["members"], old["members"]
    allk = sorted({k for v in om.values() for k in v})
    byid = {row["node"]: row for row in record["themes"]}
    print("C1b: THE CORE-BASED CONSTRUCTION, copies matched per stratum. "
          "Declared 20 Oct 2026; adopts nothing.\n")

    print("=" * 112)
    print("1. COPIES, p AND THE FLOORS")
    print("=" * 112)
    kept = record.get("theme_copies_kept") or []
    if kept:
        buckets = (("1", 1, 1), ("2", 2, 2), ("3-9", 3, 9), ("10+", 10, 10 ** 9))
        rows_by_band: dict[str, list[int]] = defaultdict(list)
        for row, count in zip(record["themes"], kept, strict=True):
            one = band_of(int(row["size"]), READ_BANDS)
            if one:
                rows_by_band[one].append(int(count))
        print("  copies per FINAL theme, by size band "
              "(the amendment of 20 Oct asks for this distribution)")
        print(f"  {'band':<10}{'themes':>8}" + "".join(f"{b[0]:>9}" for b in buckets)
              + f"{'median':>9}")
        for low, high in READ_BANDS:
            one = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
            here = rows_by_band.get(one, [])
            if not here:
                continue
            cells = "".join(
                f"{sum(1 for c in here if lo <= c <= hi):>9,}" for _n, lo, hi in buckets)
            print(f"  {one:<10}{len(here):>8,}{cells}{statistics.median(here):>9.0f}")
        every = [c for v in rows_by_band.values() for c in v]
        print(f"  {'ALL':<10}{len(every):>8,}" + "".join(
            f"{sum(1 for c in every if lo <= c <= hi):>9,}" for _n, lo, hi in buckets)
            + f"{statistics.median(every):>9.0f}")
    else:
        print("    (theme copies not recorded)")
    print(f"\n  {'stratum':<9}{'p':>7}{'real extras':>13}{'null mean':>11}{'ratio':>11}"
          f"{'floor':>11}{'real':>8}{'calib':>11}{'held-out':>11}")
    held = {e["stratum"]: e for e in record["confirmed"]["strata"]}
    for entry, floor in zip(record["p_table"], record["floors"], strict=True):
        h = held.get(entry["stratum"], {})
        print(f"  {entry['stratum']:<9}{entry['p']:>7}{entry['real_at_p']:>13,}"
              f"{entry['null_at_p']:>11.2f}"
              f"{(str(entry['ratio']) if entry['ratio'] is not None else '-'):>11}"
              f"{str(floor['effective']):>11}{floor['real']:>8,}"
              f"{str(floor['calibration_fdr']):>11}{str(h.get('heldout_fdr')):>11}")
    conf = record["confirmed"]
    worst = max((e["heldout_fdr"] or 0.0) for e in conf["strata"])
    inside = (conf["overall_fdr"] or 0) <= c1b.CAP_OVERALL and worst <= c1b.CAP_STRATUM
    print(f"  OVERALL held-out {conf['overall_fdr']} (cap {c1b.CAP_OVERALL}), worst stratum "
          f"{round(worst, 5)} (cap {c1b.CAP_STRATUM}) -- "
          f"{'INSIDE both caps' if inside else 'OVER A CAP'}")
    print(f"  groupings {record['n_groupings']:,} -> families {record['n_families']:,} -> "
          f"before the gate {record['n_before_gate']:,} -> after {record['n_after_gate']:,}")

    print("\n" + "=" * 112)
    print("2. THEMES BY SIZE BAND, AND THE CORE SHARE")
    print("=" * 112)
    labels = [f"{a}-{b}" if b < 10 ** 9 else f"{a}+" for a, b in BANDS]
    cn = Counter(band_of(len(v)) for v in nm.values())
    co = Counter(band_of(len(v)) for v in om.values())
    share: dict[str, list[float]] = defaultdict(list)
    for node, one in nm.items():
        row = byid.get(node)
        if row and len(one):
            share[band_of(len(one))].append(int(row["core_size"]) / len(one))
    print(f"  {'band':<12}{'O50s':>10}{'C1b':>10}{'change':>10}{'core share':>13}")
    for one in labels:
        median = statistics.median(share[one]) if share.get(one) else None
        print(f"  {one:<12}{co.get(one, 0):>10,}{cn.get(one, 0):>10,}"
              f"{cn.get(one, 0) - co.get(one, 0):>+10,}"
              f"{(f'{median:.3f}' if median is not None else '-'):>13}")
    print(f"  {'TOTAL':<12}{len(om):>10,}{len(nm):>10,}{len(nm) - len(om):>+10,}")
    return more(args, new, old, nm, om, allk, record, byid, c1b,
                reactome_roots, read_reactome_relation, targets, go_edges, PRIMARY_RELATIONS)


def more(args: argparse.Namespace, new: Mapping[str, object], old: Mapping[str, object],
         nm: Mapping[str, set[str]], om: Mapping[str, set[str]], allk: Sequence[str],
         record: Mapping[str, object], byid: Mapping[str, Mapping[str, str]], c1b: object,
         reactome_roots: Callable[..., object], read_reactome_relation: Callable[..., object],
         targets: Callable[..., object], go_edges: Callable[..., object],
         relations: Sequence[str]) -> int:
    """Items 3 to 6, and the reviewer material.

    Args:
        args: Parsed arguments.
        new: The C1b build.
        old: The O50s build.
        nm: C1b node to member keys.
        om: O50s node to member keys.
        allk: Every pathway key.
        record: C1b's own record.
        byid: C1b node id to its core row.
        c1b: The build module, for its constants.
        reactome_roots: The branch finder.
        read_reactome_relation: The relation reader.
        targets: The summary target builder.
        go_edges: The GO edge reader.
        relations: The primary GO relations.

    Returns:
        0.
    """
    print("\n" + "=" * 112)
    print("3. SHAPE")
    print("=" * 112)
    shapes: dict[str, dict[str, object]] = {}
    for name, build, members in (("O50s", old, om), ("C1b", new, nm)):
        nodes = build["nodes"]
        roots = [n for n, row in nodes.items() if not row["parents"].strip()]
        kids = [len(row["children"].split()) for row in nodes.values()]
        multi = sum(1 for row in nodes.values() if len(row["parents"].split()) > 1)
        per_pathway: Counter[str] = Counter()
        for one in members.values():
            for key in one:
                per_pathway[key] += 1
        got = depths(nodes, members)
        shapes[name] = {
            "themes": len(nodes), "roots": len(roots),
            "small_roots": sum(1 for n in roots if len(members[n]) <= SMALL_ROOT),
            "giants": sorted(((len(members[n]), n) for n in members
                              if len(members[n]) > GIANT), reverse=True),
            "children_max": max(kids, default=0),
            "children_median": float(statistics.median(kids)) if kids else 0.0,
            "multi_share": round(multi / len(nodes), 4) if nodes else 0.0,
            "themes_per_pathway": round(
                sum(per_pathway.values()) / max(len(per_pathway), 1), 3),
            "levels_median": got["median"], "levels_max": got["max"],
            "root_ids": roots}
    for key, title in (("themes", "themes"), ("roots", "roots"),
                       ("small_roots", f"roots of {SMALL_ROOT} or fewer"),
                       ("children_max", "children max"),
                       ("children_median", "children median"),
                       ("multi_share", "multi-parent share"),
                       ("themes_per_pathway", "mean themes per pathway"),
                       ("levels_median", "levels to a root, median"),
                       ("levels_max", "levels to a root, max")):
        print(f"  {title:<30}{str(shapes['O50s'][key]):>14}{str(shapes['C1b'][key]):>14}")
    for name in shapes:
        giants = shapes[name]["giants"]
        print(f"  {name} giants over {GIANT:,}: {len(giants)}")
        for size, node in giants[:12]:
            core = byid.get(node, {}).get("core_size", "") if name == "C1b" else ""
            print(f"    {node:<10}{size:>7,}" + (f"   core {core}" if core != "" else ""))

    print("\n" + "=" * 112)
    print("4. WHAT THE DROPPED STEPS WOULD ACT ON (reported, not a gate)")
    print("=" * 112)
    index = {key: i for i, key in enumerate(allk)}
    words = (len(allk) + 63) // 64
    ids, stack, sizes = pack(nm, index, words)
    nodes = new["nodes"]
    chainable = 0
    for node, row in nodes.items():
        child = len(nm[node])
        for parent in row["parents"].split():
            if parent and child >= CHAIN * len(nm[parent]):
                chainable += 1
    victims = {node for node, row in nodes.items()
               for parent in row["parents"].split()
               if parent and len(nm[node]) >= CHAIN * len(nm[parent])}
    print(f"  parent-child pairs with the child holding at least {CHAIN:.0%} of the parent: "
          f"{chainable:,}")
    print(f"    distinct children in such a pair, which is what chain collapse would remove: "
          f"{len(victims):,}")
    # Non-nested pairs at or above the twin cutoff: one vectorised row against all later rows,
    # which is cheap enough at a few thousand themes and needs no inverted index.
    by_band: Counter[str] = Counter()
    total_pairs = 0
    for row in range(len(ids)):
        if row + 1 >= len(ids):
            break
        shared = np.bitwise_count(stack[row][None, :] & stack[row + 1:]).sum(axis=1)
        union = sizes[row] + sizes[row + 1:] - shared
        with np.errstate(divide="ignore", invalid="ignore"):
            scores = np.where(union > 0, shared / union, 0.0)
        for offset in np.flatnonzero(scores >= TWIN).tolist():
            other = row + 1 + offset
            if shared[offset] == sizes[row] or shared[offset] == sizes[other]:
                continue       # nested, which the rule spares by design
            total_pairs += 1
            one = band_of(int(max(sizes[row], sizes[other])))
            if one:
                by_band[one] += 1
    print(f"  non-nested theme pairs at J >= {TWIN} that were not merged: {total_pairs:,}")
    for one in [f"{a}-{b}" if b < 10 ** 9 else f"{a}+" for a, b in BANDS]:
        if by_band.get(one):
            print(f"    {one:<10}{by_band[one]:>8,}")
    return final(args, new, old, nm, om, allk, record, shapes, c1b,
                 reactome_roots, read_reactome_relation, targets, go_edges, relations)


def final(args: argparse.Namespace, new: Mapping[str, object], old: Mapping[str, object],
          nm: Mapping[str, set[str]], om: Mapping[str, set[str]], allk: Sequence[str],
          record: Mapping[str, object], shapes: Mapping[str, Mapping[str, object]],
          c1b: object, reactome_roots: Callable[..., object],
          read_reactome_relation: Callable[..., object], targets: Callable[..., object],
          go_edges: Callable[..., object], relations: Sequence[str]) -> int:
    """Items 5 and 6, and the reviewer material.

    Args:
        args: Parsed arguments.
        new: The C1b build.
        old: The O50s build.
        nm: C1b node to member keys.
        om: O50s node to member keys.
        allk: Every pathway key.
        record: C1b's own record.
        shapes: Both builds' shape figures.
        c1b: The build module.
        reactome_roots: The branch finder.
        read_reactome_relation: The relation reader.
        targets: The summary target builder.
        go_edges: The GO edge reader.
        relations: The primary GO relations.

    Returns:
        0.
    """
    print("\n" + "=" * 112)
    print("5. O50s COUNTERPARTS")
    print("=" * 112)
    matched = best_matches(om, nm, allk)
    at_same = sum(1 for _, s in matched.values() if s >= SAME)
    print(f"  O50s themes with a C1b counterpart at J >= {SAME}: {at_same:,} of {len(om):,} "
          f"= {at_same / len(om):.1%}")
    small = [n for n in shapes["O50s"]["root_ids"] if len(om[n]) <= SMALL_ROOT]
    c1b_roots = set(shapes["C1b"]["root_ids"])
    have = [n for n in small if matched[n][1] >= 0.70]
    still = [n for n in have if matched[n][0] in c1b_roots]
    print(f"  the {len(small)} O50s small roots: {len(have)} have a counterpart at J >= 0.70 "
          f"= {len(have) / len(small):.1%}; of those, {len(still)} are still roots "
          f"= {len(still) / max(len(have), 1):.1%}")
    print(f"\n  {'O50s root':<10}{'size':>7}  {'C1b counterpart':<16}{'J':>7}{'root?':>7}")
    for node in NAMED:
        if node not in om:
            print(f"  {node:<10}{'absent':>7}")
            continue
        partner, score = matched[node]
        print(f"  {node:<10}{len(om[node]):>7,}  {partner:<16}{score:>7.3f}"
              f"{('yes' if partner in c1b_roots else 'no'):>7}")

    print("\n" + "=" * 112)
    print("6. PLACEMENT AND REACTOME")
    print("=" * 112)
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    names = {f"{r['source']}:{r['source_id']}": r["name"] for r in rows}
    info = {f"{r['source']}:{r['source_id']}": (r["name"], r["source"]) for r in rows}
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
        """Every Reactome pathway under a branch."""
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
        """Placement and the Reactome median best Jaccard."""
        items = list(pool.values())
        total = sum(1 for leaves in key_sets.values()
                    if any(len(leaves & one) >= HOME_SHARE * len(leaves) for one in items))
        best = statistics.median([
            max((len(leaves & one) / len(leaves | one) for one in items), default=0.0)
            for leaves in branches.values()])
        return total, best

    for name, pool in (("O50s", om), ("C1b", nm)):
        total, best = score_pool(pool)
        print(f"  {name:<6} placement {total:,} of {len(key_sets):,} = "
              f"{total / len(key_sets):.1%}; Reactome median best J {best:.3f}", flush=True)

    reviewer(args, new, old, nm, om, record, shapes, info)
    return 0


def write_batches(folder: Path, blocks: Sequence[tuple[str, list[str]]]) -> list[tuple[Path, int]]:
    """Write reading blocks into batches of about :data:`BATCH_LINES`, never splitting one.

    Args:
        folder: Where the batches go.
        blocks: ``(id, lines)`` per item.

    Returns:
        ``(path, lines)`` per batch.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.md"):
        old.unlink()
    batch: list[str] = []
    count = 0
    written: list[tuple[Path, int]] = []
    for _tid, lines in blocks:
        if batch and count + len(lines) > BATCH_LINES:
            path = folder / f"b{len(written) + 1:02d}.md"
            path.write_text("\n".join(batch) + "\n", encoding="utf-8")
            written.append((path, count))
            batch, count = [], 0
        batch.extend(lines)
        count += len(lines)
    if batch:
        path = folder / f"b{len(written) + 1:02d}.md"
        path.write_text("\n".join(batch) + "\n", encoding="utf-8")
        written.append((path, count))
    return written


def reviewer(args: argparse.Namespace, new: Mapping[str, object], old: Mapping[str, object],
             nm: Mapping[str, set[str]], om: Mapping[str, set[str]],
             record: Mapping[str, object], shapes: Mapping[str, Mapping[str, object]],
             info: Mapping[str, tuple[str, str]]) -> None:
    """The reviewer's two reading sets, the key, and the three tables.

    The roots are read **with** their identity, since they are C1b's own and there is nothing to
    blind them against. The non-root sample is pooled from C1b and O50s and carries **no build
    label**, because that comparison is the point of item 4 of the decision rule.

    Args:
        args: Parsed arguments.
        new: The C1b build.
        old: The O50s build.
        nm: C1b node to member keys.
        om: O50s node to member keys.
        record: C1b's own record.
        shapes: Both builds' shape figures.
        info: Pathway key to ``(name, source)``.
    """
    print("\n" + "=" * 112)
    print("FOR THE REVIEWER")
    print("=" * 112)
    args.out.mkdir(parents=True, exist_ok=True)
    byid = {row["node"]: row for row in record["themes"]}
    detail: dict[str, str] = {}
    path = args.c1b / record.get("detail", "themes_detail.tsv")
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                detail[row["node"]] = row["members"]
    rng = np.random.default_rng(SEED)

    def lines_for(members: set[str], tid: str) -> list[str]:
        """One reading block."""
        out = [f"## {tid}  ({len(members)} pathways)", ""]
        for key in sorted(members, key=lambda k: (info.get(k, (k, ""))[0].lower(), k)):
            name, source = info.get(key, (key, "?"))
            out.append(f"{name} [{source}]")
        out.append("")
        return out

    roots = sorted(shapes["C1b"]["root_ids"], key=lambda n: -len(nm[n]))
    sampled = roots
    note = "every root"
    if len(roots) > MAX_ROOTS_READ:
        picked = rng.choice(len(roots), MAX_ROOTS_READ, replace=False)
        sampled = [roots[i] for i in sorted(picked.tolist())]
        note = f"a random {MAX_ROOTS_READ} of {len(roots)}"
    order = rng.permutation(len(sampled))
    root_key: dict[str, object] = {}
    blocks = []
    for position, pick in enumerate(order.tolist(), 1):
        node = sampled[pick]
        tid = f"R{position:03d}"
        root_key[tid] = {"build": "C1b", "node": node, "size": len(nm[node]),
                         "band": band_of(len(nm[node]), READ_BANDS)}
        blocks.append((tid, lines_for(nm[node], tid)))
    root_batches = write_batches(args.out / "read_roots", blocks)
    print(f"  R: {len(sampled)} roots ({note}) in {len(root_batches)} batch(es)")

    pool: list[tuple[str, str, int]] = []
    short: list[str] = []
    for name, members, build_roots in (("C1b", nm, set(shapes["C1b"]["root_ids"])),
                                       ("O50s", om, set(shapes["O50s"]["root_ids"]))):
        for low, high in READ_BANDS:
            one = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
            here = sorted(n for n, v in members.items()
                          if n not in build_roots and low <= len(v) <= high)
            if len(here) <= PER_BAND:
                take = here
                short.append(f"{name} {one}: {len(here)} available, all taken")
            else:
                picked = rng.choice(len(here), PER_BAND, replace=False)
                take = [here[i] for i in sorted(picked.tolist())]
            pool.extend((name, node, len(members[node])) for node in take)
    order = rng.permutation(len(pool))
    theme_key: dict[str, object] = {}
    blocks = []
    for position, pick in enumerate(order.tolist(), 1):
        name, node, size = pool[pick]
        tid = f"T{position:03d}"
        theme_key[tid] = {"build": name, "node": node, "size": size,
                          "band": band_of(size, READ_BANDS)}
        blocks.append((tid, lines_for(nm[node] if name == "C1b" else om[node], tid)))
    theme_batches = write_batches(args.out / "read_themes", blocks)
    print(f"  T: {len(pool)} non-root themes ({PER_BAND} per band per build where available) "
          f"in {len(theme_batches)} batch(es)")
    for line in short:
        print(f"    short band -- {line}")

    (args.out / "KEY_DO_NOT_SHARE_C1b.json").write_text(
        json.dumps({"roots": root_key, "themes": theme_key}, indent=1) + "\n",
        encoding="utf-8")
    with (args.out / "roots.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "support", "core_size", "n_children", "members"])
        writer.writeheader()
        for node in roots:
            row = byid.get(node, {})
            writer.writerow({
                "node": node, "size": len(nm[node]),
                "support": new["nodes"][node]["support"],
                "core_size": row.get("core_size", ""),
                "n_children": len(new["nodes"][node]["children"].split()),
                "members": detail.get(node, "")})
    with (args.out / "themes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "support", "core_size", "parents", "members"])
        writer.writeheader()
        for node in sorted(nm, key=lambda n: -len(nm[n])):
            row = byid.get(node, {})
            writer.writerow({
                "node": node, "size": len(nm[node]),
                "support": new["nodes"][node]["support"],
                "core_size": row.get("core_size", ""),
                "parents": new["nodes"][node]["parents"],
                "members": detail.get(node, "")})
    with (args.out / "p_table.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["stratum", "theta", "p", "real_extras", "null_mean", "ratio",
                        "floor", "real", "calibration_fdr", "heldout_fdr"])
        writer.writeheader()
        held = {e["stratum"]: e for e in record["confirmed"]["strata"]}
        import core_construction_c1b as mod
        for entry, floor in zip(record["p_table"], record["floors"], strict=True):
            h = held.get(entry["stratum"], {})
            writer.writerow({
                "stratum": entry["stratum"],
                "theta": mod.THETA[entry["index"]], "p": entry["p"],
                "real_extras": entry["real_at_p"], "null_mean": entry["null_at_p"],
                "ratio": entry["ratio"] if entry["ratio"] is not None else "",
                "floor": floor["effective"] if floor["effective"] is not None else "",
                "real": floor["real"],
                "calibration_fdr": floor["calibration_fdr"]
                if floor["calibration_fdr"] is not None else "",
                "heldout_fdr": h.get("heldout_fdr") if h.get("heldout_fdr") is not None else ""})
    print(f"  -> {args.out}: roots.tsv, themes.tsv, p_table.tsv, the key, "
          f"read_roots/ and read_themes/")
    print("  The key is written and is never read again by this session. Nothing is judged here.")


if __name__ == "__main__":
    raise SystemExit(main())
