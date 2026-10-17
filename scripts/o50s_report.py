#!/usr/bin/env python3
"""Everything prompt 43 asks for: O50s against O50, and the reviewer's table of large themes.

Read-only over both builds. ``--o50`` is the frozen build and is never written.

Usage::

    uv run scripts/o50s_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

#: The declared theme size bands.
BANDS = ((3, 5), (6, 11), (12, 24), (25, 49), (50, 99), (100, 199), (200, 399), (400, 799),
         (800, 1599), (1600, 10 ** 9))

#: A theme this large is a giant.
GIANT = 1000

#: A root holding this many members or fewer is a small root.
SMALL_ROOT = 50

#: The small-theme band the decision rule protects.
SMALL = (3, 50)

#: The large band the decision rule wants to grow, and the reviewer's table covers.
LARGE = (101, 1000)

#: A counterpart at or above this Jaccard is the same theme.
SAME = 0.90

#: A counterpart at or above this Jaccard means a large theme is not new.
KEPT = 0.70

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80


def band_of(size: int) -> str:
    """The band label a size falls in.

    Args:
        size: Theme size.

    Returns:
        The band label, or ``"under 3"``.
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
    """For each set on the left, its best Jaccard partner on the right.

    Bitsets and one vectorised pass per left node, because the real comparisons here are 4,602
    against 5,658 and a Python double loop over member sets would take minutes.

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


def main(argv: list[str] | None = None) -> int:
    """Print the report and write the reviewer's table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--o50", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--rec2fix", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix"))
    parser.add_argument("--review", type=Path,
                        default=Path("data/experiments/O50s_review_2026-10-17"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    new = read_build(args.o50s)
    old = read_build(args.o50)
    floors = json.loads((args.o50s / "floors_o50s.json").read_text())
    nm, om = new["members"], old["members"]
    allk = sorted({k for one in om.values() for k in one})
    print("O50s: THE FROZEN O50 WITH SIZE STRATA ABOVE 10. Declared 17 Oct 2026.")
    print("Adopts nothing by itself. The harness reproduces the frozen O50 byte for byte with the")
    print("frozen strata and floors (scripts/o50s_build.py --verify).\n")

    print("=" * 104)
    print("1. FLOORS")
    print("=" * 104)
    print(f"  {'stratum':<10}{'floor':>11}{'real passing':>14}{'calib FDR':>12}"
          f"{'held-out FDR':>14}{'held-out real':>15}  source")
    for entry in floors["confirmed"]["strata"]:
        mark = " *" if entry.get("bounded") else ""
        print(f"  {entry['stratum']:<10}{str(entry['effective']):>11}{entry['real']:>14,}"
              f"{str(entry['calibration_fdr']):>12}{str(entry['heldout_fdr']):>14}"
              f"{entry['heldout_real']:>15,}  {entry.get('source', '')}{mark}")
    print(f"  {'OVERALL':<10}{'':>11}{floors['confirmed']['overall_real']:>14,}{'':>12}"
          f"{str(floors['confirmed']['overall_fdr']):>14}")
    print(f"  caps: {floors['caps']['per_stratum']} per stratum, "
          f"{floors['caps']['overall']} overall; over the cap: {floors['over_cap'] or 'none'}")
    print("  * = the rule-of-three bound decided the cut: no scrambled candidate was observed at "
          "or above it,")
    print("      so the mean count was replaced by 3/10 rather than read as zero.")
    print("  O50 for comparison: one 10+ stratum at 0.025126 over 86,395 real candidates")

    print("\n" + "=" * 104)
    print("2. THEMES BY SIZE BAND, after the full build")
    print("=" * 104)
    nb = Counter(band_of(len(v)) for v in nm.values())
    ob = Counter(band_of(len(v)) for v in om.values())
    labels = [f"{a}-{b}" if b < 10 ** 9 else f"{a}+" for a, b in BANDS]
    print(f"  {'band':<12}{'O50':>10}{'O50s':>10}{'change':>12}{'ratio':>9}")
    for one in labels:
        a, b = ob.get(one, 0), nb.get(one, 0)
        ratio = f"{b / a:.2f}x" if a else "-"
        print(f"  {one:<12}{a:>10,}{b:>10,}{b - a:>+12,}{ratio:>9}")
    print(f"  {'TOTAL':<12}{len(om):>10,}{len(nm):>10,}{len(nm) - len(om):>+12,}"
          f"{len(nm) / len(om):>8.2f}x")

    print("\n" + "=" * 104)
    print("3. SHAPE")
    print("=" * 104)
    for name, build, mem in (("O50", old, om), ("O50s", new, nm)):
        nodes = build["nodes"]
        giants = sorted(((len(mem[k]), k) for k in mem if len(mem[k]) > GIANT), reverse=True)
        roots = [k for k, row in nodes.items() if not row["parents"].strip()]
        small_roots = [k for k in roots if len(mem[k]) <= SMALL_ROOT]
        kids = [len(row["children"].split()) for row in nodes.values()]
        multi = sum(1 for row in nodes.values() if len(row["parents"].split()) > 1)
        print(f"  {name}: {len(nodes):,} themes")
        print(f"    giants over {GIANT:,}: {len(giants)}  "
              + ", ".join(f"{k} ({s:,})" for s, k in giants))
        print(f"    roots {len(roots):,}; of {SMALL_ROOT} members or fewer: {len(small_roots):,} "
              f"= {len(small_roots) / max(len(roots), 1):.1%}")
        print(f"    children per node: max {max(kids):,}, median {statistics.median(kids):.0f}")
        print(f"    multi-parent {multi:,} = {multi / len(nodes):.1%}")

    print("\n" + "=" * 104)
    print("4. SMALL THEMES KEPT")
    print("=" * 104)
    low, high = SMALL
    n_small_new = sum(1 for v in nm.values() if low <= len(v) <= high)
    n_small_old = sum(1 for v in om.values() if low <= len(v) <= high)
    print(f"  themes of {low}-{high} members: O50 {n_small_old:,}, O50s {n_small_new:,} "
          f"= {n_small_new / n_small_old:.1%} of O50's")
    print(f"  the declared bar is 95%: "
          f"{'PASS' if n_small_new >= 0.95 * n_small_old else 'FAIL'}")
    matched = best_matches(om, nm, allk)
    at_same = sum(1 for _, score in matched.values() if score >= SAME)
    print(f"  O50 themes with an O50s counterpart at J >= {SAME}: {at_same:,} of {len(om):,} "
          f"= {at_same / len(om):.1%}")
    dist = Counter("1.00" if s >= 0.999 else f"{int(s * 10) / 10:.1f}"
                   for _, s in matched.values())
    print("  the whole distribution of O50 -> best O50s Jaccard: " + ", ".join(
        f"{k}: {dist[k]:,}" for k in sorted(dist, reverse=True)))
    return more(args, new, old, nm, om, allk, matched, floors)


def more(args: argparse.Namespace, new: dict, old: dict, nm: dict[str, set[str]],
         om: dict[str, set[str]], allk: Sequence[str],
         matched: dict[str, tuple[str, float]], floors: dict) -> int:
    """Summary placement, Reactome agreement, the new large themes and the reviewer's table.

    Args:
        args: Parsed arguments.
        new: The O50s build.
        old: The frozen O50 build.
        nm: O50s node to member keys.
        om: O50 node to member keys.
        allk: Every pathway key.
        matched: O50 node to its best O50s counterpart.
        floors: The O50s floors record.

    Returns:
        0.
    """
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    universe = set(allk)
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    names = {f"{r['source']}:{r['source_id']}": r["name"] for r in rows}
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {
        f"reactome:{c}": {f"reactome:{p}" for p in ps} for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(),
            PRIMARY_RELATIONS).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}
    key_sets = targets(edges, sorted(set(names) - universe), universe, min_size=3)

    def home(leaf_set: frozenset[str], pool: Mapping[str, set[str]]) -> str:
        """The smallest node holding HOME_SHARE of a summary's leaves, if any."""
        best, size = "", 0
        for node, held in pool.items():
            if len(leaf_set & held) >= HOME_SHARE * len(leaf_set):
                if not best or len(held) < size:
                    best, size = node, len(held)
        return best

    print("\n" + "=" * 104)
    print("5. SUMMARY PLACEMENT (display only, nothing attached)")
    print("=" * 104)
    got_old = sum(1 for s in key_sets.values() if home(s, om))
    got_new = sum(1 for s in key_sets.values() if home(s, nm))
    print(f"  curated summaries with 3+ leaf descendants in L: {len(key_sets):,}")
    print(f"    with a node holding {HOME_SHARE:.0%} of their leaves:")
    print(f"      O50   {got_old:>6} = {got_old / len(key_sets):.1%}")
    print(f"      O50s  {got_new:>6} = {got_new / len(key_sets):.1%}  "
          f"({got_new - got_old:+} summaries)")
    print(f"    {'summary band':<16}{'n':>6}{'O50':>8}{'O50s':>8}{'change':>9}")
    for low, high in ((3, 10), (11, 50), (51, 200), (201, 10 ** 9)):
        band = {k: s for k, s in key_sets.items() if low <= len(s) <= high}
        if not band:
            continue
        a = sum(1 for s in band.values() if home(s, om))
        b = sum(1 for s in band.values() if home(s, nm))
        name = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
        print(f"    {name:<16}{len(band):>6}{a:>8}{b:>8}{b - a:>+9}")

    print("\n" + "=" * 104)
    print("6. AGREEMENT WITH REACTOME'S TOP LEVEL (best Jaccard)")
    print("=" * 104)
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
    scores: dict[str, list[float]] = {"O50": [], "O50s": []}
    print(f"  {len(branches)} of {len(reactome_roots(rel))} top-level branches have 3+ leaves in L")
    print(f"  {'reactome top':<44}{'leaves':>7}  {'O50':<13}{'J':>7}  {'O50s':<13}{'J':>7}")
    for root, leaves in sorted(branches.items(), key=lambda kv: -len(kv[1])):
        cells = []
        for name, pool in (("O50", om), ("O50s", nm)):
            best, score = "", 0.0
            for node, held in pool.items():
                union = len(leaves | held)
                value = len(leaves & held) / union if union else 0.0
                if value > score:
                    best, score = node, value
            scores[name].append(score)
            cells.append(f"  {best:<13}{score:>7.3f}")
        print(f"  {names.get(f'reactome:{root}', root)[:42]:<44}{len(leaves):>7}" + "".join(cells))
    print(f"  {'MEDIAN best Jaccard':<44}{'':>7}"
          + "".join(f"  {'':<13}{statistics.median(scores[k]):>7.3f}" for k in ("O50", "O50s")))

    low, high = LARGE
    back = best_matches({k: v for k, v in nm.items() if low <= len(v) <= high}, om, allk)
    fix: dict[str, set[str]] = defaultdict(set)
    path = args.rec2fix / "area_members.tsv"
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                fix[row["node"]].add(row["key"])
    to_fix = best_matches({k: nm[k] for k in back}, dict(fix), allk) if fix else {}
    band = sorted(back, key=lambda k: -len(nm[k]))
    fresh = [k for k in band if back[k][1] < KEPT]
    print("\n" + "=" * 104)
    print(f"7. NEW LARGE THEMES: {low}-{high} members with no O50 counterpart at J >= {KEPT}")
    print("=" * 104)
    print(f"  O50s themes of {low}-{high}: {len(band):,}  (O50 has "
          f"{sum(1 for v in om.values() if low <= len(v) <= high):,})")
    print(f"  of those, NEW (best J to any O50 theme below {KEPT}): {len(fresh):,} "
          f"= {len(fresh) / max(len(band), 1):.1%}")
    print(f"  the declared bar is 2x O50's count in the band: "
          f"{len(band)} against {sum(1 for v in om.values() if low <= len(v) <= high)} = "
          f"{len(band) / max(sum(1 for v in om.values() if low <= len(v) <= high), 1):.2f}x")
    print(f"\n  {'theme':<10}{'size':>6}{'support':>9}  {'best O50':<10}{'J':>7}  "
          f"{'best rec2fix area':<18}{'J':>7}")
    for node in fresh[:40]:
        area, av = to_fix.get(node, ("", 0.0))
        print(f"  {node:<10}{len(nm[node]):>6}{new['nodes'][node]['support']:>9}  "
              f"{back[node][0]:<10}{back[node][1]:>7.3f}  {area:<18}{av:>7.3f}")
    if len(fresh) > 40:
        print(f"  ... and {len(fresh) - 40} more, all in the reviewer table")
    if fresh:
        fresh_fix = [to_fix.get(k, ('', 0.0))[1] for k in fresh]
        print(f"\n  best J to any rec2fix area, over the {len(fresh)} new themes: "
              f">=0.7 {sum(1 for v in fresh_fix if v >= 0.7)}, "
              f"0.5-0.7 {sum(1 for v in fresh_fix if 0.5 <= v < 0.7)}, "
              f"<0.5 {sum(1 for v in fresh_fix if v < 0.5)}; "
              f"median {statistics.median(fresh_fix):.3f}, max {max(fresh_fix):.3f}")

    args.review.mkdir(parents=True, exist_ok=True)
    out = args.review / "large_themes.tsv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "size", "support", "status", "best_o50", "j_o50",
                        "best_rec2fix_area", "j_area", "members"])
        writer.writeheader()
        for node in band:
            area, av = to_fix.get(node, ("", 0.0))
            writer.writerow({
                "node": node, "size": len(nm[node]),
                "support": new["nodes"][node]["support"],
                "status": "new" if back[node][1] < KEPT else "kept",
                "best_o50": back[node][0], "j_o50": round(back[node][1], 4),
                "best_rec2fix_area": area, "j_area": round(av, 4),
                "members": " ".join(sorted(nm[node]))})
    print("\n" + "=" * 104)
    print("8. FOR THE REVIEWER")
    print("=" * 104)
    print(f"  -> {out}  ({len(band):,} themes of {low}-{high} members, "
          f"{len(fresh):,} marked new, {len(band) - len(fresh):,} kept)")
    print("  Not judged here. Every row carries its full member key list.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
