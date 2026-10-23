"""Sections A, B, D and E of prompt 54: S2 against O50s and S1p, by the same code.

Declared 22 Oct 2026. Evaluation only; nothing is adopted. Sections C, F, G and the reviewer
material are not run, as the prompt says.

Two measures have no existing script and are computed here, with the method stated:

* **edges that exist only because of inherited members.** A final node's ORIGINAL set is the gated
  block of the candidate consensus accepted for it; its FINAL set is what consensus left it with,
  and neither repair sub-pass changes a membership. An edge ``child -> parent`` rests on inheritance
  if the child is not contained in the parent's original set. For S1p this is 0 by construction --
  it has no consensus and so no inheritance.
* **section A's construction counts**, which come from each build's own manifest and construction
  record.

Placement and the Reactome comparison reuse ``scripts/o50s_report.py``'s machinery (``targets``,
``go_edges``, ``read_reactome_relation``, and its 80% home rule) so the figures are comparable with
the ones in O50s's own report.

Usage:
    uv run scripts/s2_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The share of a summary's leaves one node must hold to be its home. O50s's own value.
HOME_SHARE = 0.80

BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return "3-5"


def read_build(directory: Path) -> dict[str, object]:
    """Nodes, memberships and manifest for one build.

    Args:
        directory: A build directory.

    Returns:
        ``{nodes, parents, members, manifest}``.
    """
    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    parents = {r["node"]: tuple(p for p in (r["parents"] or "").split() if p) for r in rows}
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    with (directory / "edges.tsv").open(encoding="utf-8") as handle:
        edges = [(r["child"], r["parent"]) for r in csv.DictReader(handle, delimiter="\t")]
    return {"ids": [r["node"] for r in rows], "parents": parents, "members": dict(members),
            "edges": edges,
            "manifest": json.loads((directory / "manifest.json").read_text())}


def levels(ids: Sequence[str], parents: Mapping[str, tuple[str, ...]],
           members: Mapping[str, set[str]]) -> tuple[float, int]:
    """Levels from a pathway to its root: median and maximum over pathways.

    Args:
        ids: Node ids.
        parents: Immediate parents per node.
        members: Node to member keys.

    Returns:
        ``(median, maximum)``.
    """
    depth: dict[str, int] = {}

    def climb(node: str) -> int:
        """Longest upward path to a root."""
        if node in depth:
            return depth[node]
        depth[node] = 0
        if parents[node]:
            depth[node] = 1 + max(climb(p) for p in parents[node])
        return depth[node]

    for node in ids:
        climb(node)
    deepest: dict[str, int] = {}
    for node, keys in members.items():
        for key in keys:
            if depth[node] > deepest.get(key, -1):
                deepest[key] = depth[node]
    values = sorted(deepest.values())
    return (statistics.median(values), max(values)) if values else (0.0, 0)


def originals_for(build: dict, accepted: Sequence[int], drops: Mapping[int, int],
                  gated: np.ndarray) -> np.ndarray | None:
    """Per final node, the ORIGINAL gated block of the candidate consensus accepted for it.

    Args:
        build: A read build.
        accepted: Gated index per post-consensus position.
        drops: ``{dropped post-consensus row: the row that took it}``.
        gated: ``(g, words)`` gated member bitsets.

    Returns:
        ``(nodes, words)`` original bitsets, or None if the mapping does not line up.
    """
    survivors = [i for i in range(len(accepted)) if i not in drops]
    if len(survivors) != len(build["ids"]):
        return None
    return np.vstack([gated[int(accepted[i])][None, :] for i in survivors])


def inheritance_edges(build: dict, originals: np.ndarray | None, index: Mapping[str, int],
                      width: int) -> tuple[int, int, np.ndarray | None]:
    """Edges that exist only because the parent gained inherited members.

    Args:
        build: A read build.
        originals: Original bitsets per node, or None when the build has no inheritance.
        index: Pathway key to universe position.
        width: Bitset width in bits.

    Returns:
        ``(edges, edges resting on inheritance, per-node inherited counts)``.
    """
    from thema.ontology import bitset as bits

    edges = build["edges"]
    if originals is None:
        return len(edges), 0, None
    at = {node: i for i, node in enumerate(build["ids"])}
    final = np.vstack([
        bits.pack(sorted(index[k] for k in build["members"].get(node, ())), width)[None, :]
        for node in build["ids"]])
    gained = np.bitwise_count(final & ~originals).sum(axis=1).astype(np.int64)
    rests = 0
    for child, parent in edges:
        if int(np.bitwise_count(final[at[child]] & ~originals[at[parent]]).sum()):
            rests += 1
    return len(edges), rests, gained


def section_d(args: argparse.Namespace, builds: Sequence[tuple[str, dict]],
              index: Mapping[str, int], width: int) -> None:
    """Section D: do the 76 parents O50s's consensus superseded come back?

    Args:
        args: Parsed arguments.
        builds: ``(name, build)`` pairs.
        index: Pathway key to universe position.
        width: Bitset width in bits.
    """
    from thema.ontology import bitset as bits

    side = args.parents.parent / "side.npz"
    with np.load(side, allow_pickle=False) as handle:
        completed_keys = handle["completed_keys"].tolist()
        completed_blocks = handle["completed_blocks"]
    at = {g: i for i, g in enumerate(completed_keys)}
    rows = [r for r in csv.DictReader(args.parents.open(encoding="utf-8"), delimiter="\t")
            if r["stage"] == "consensus" and r["unit"] == "grouping"]

    stacks = {}
    for name, build in builds:
        stacks[name] = np.vstack([
            bits.pack(sorted(index[k] for k in build["members"].get(node, ())), width)[None, :]
            for node in build["ids"]])

    print("=" * 104)
    print("D. THE 76 PARENTS O50s's CONSENSUS SUPERSEDED")
    print("=" * 104)
    survived: dict[str, int] = {}
    roots_back: dict[str, set[str]] = {}
    bests: dict[str, list[float]] = {}
    all_roots: set[str] = set()
    for name, _build in builds:
        survived[name] = 0
        roots_back[name] = set()
        bests[name] = []
    for row in rows:
        block = completed_blocks[at[int(row["id"])]]
        mine = set(row["root_nodes"].split())
        all_roots |= mine
        for name, _build in builds:
            stack = stacks[name]
            inter = np.bitwise_count(block[None, :] & stack).sum(axis=1).astype(np.int64)
            union = np.bitwise_count(block[None, :] | stack).sum(axis=1).astype(np.int64)
            jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
            best = float(jac.max())
            bests[name].append(best)
            if best >= 0.9:
                survived[name] += 1
                roots_back[name] |= mine
    print(f"  {len(rows)} parents, member sets regenerated from the cached side material")
    print(f"  {'':<42}" + "".join(f"{n:>14}" for n, _b in builds))
    print(f"  {'present at J >= 0.9':<42}"
          + "".join(f"{survived[n]:>14}" for n, _b in builds))
    print(f"  {'share of the 76':<42}"
          + "".join(f"{survived[n] / len(rows):>14.1%}" for n, _b in builds))
    print(f"  {'O50s roots those survivors contain':<42}"
          + "".join(f"{len(roots_back[n]):>14}" for n, _b in builds))
    print(f"  {'of the ' + str(len(all_roots)) + ' roots the 76 cover':<42}"
          + "".join(f"{len(roots_back[n]) / len(all_roots):>14.1%}" for n, _b in builds))
    print(f"  {'median best Jaccard':<42}"
          + "".join(f"{float(np.median(bests[n])):>14.3f}" for n, _b in builds))
    print(f"  {'max best Jaccard':<42}"
          + "".join(f"{max(bests[n]):>14.3f}" for n, _b in builds))
    print()


def section_e(args: argparse.Namespace, o50s: dict, others: Sequence[tuple[str, dict]],
              allk: Sequence[str]) -> None:
    """Section E (short): counterparts by band, summary placement, Reactome median best J.

    Placement and the Reactome figure follow ``scripts/o50s_report.py`` exactly -- the same
    ``targets`` leaf sets, the same 80% home rule, the same top-level branches -- so they are
    comparable with the numbers in O50s's own report.

    Args:
        args: Parsed arguments.
        o50s: The O50s build.
        others: ``(name, build)`` for the arms being compared.
        allk: Every pathway key.
    """
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    print("=" * 104)
    print("E. AGREEMENT AND PLACEMENT")
    print("=" * 104)
    om = o50s["members"]
    sizes = {node: len(keys) for node, keys in om.items()}
    print("  O50s themes with a counterpart at J >= 0.9, by band")
    print(f"  {'band':<12}{'O50s themes':>13}" + "".join(f"{n:>14}" for n, _b in others))
    tallies: dict[str, dict[str, int]] = {n: defaultdict(int) for n, _b in others}
    counts: dict[str, int] = defaultdict(int)
    for node, keys in om.items():
        band = band_of(sizes[node])
        counts[band] += 1
        for name, build in others:
            best = 0.0
            for other in build["members"].values():
                inter = len(keys & other)
                if not inter:
                    continue
                jac = inter / (len(keys) + len(other) - inter)
                if jac > best:
                    best = jac
                    if best >= 0.9:
                        break
            if best >= 0.9:
                tallies[name][band] += 1
    for _low, _high, band in BANDS:
        if not counts[band]:
            continue
        print(f"  {band:<12}{counts[band]:>13,}" + "".join(
            f"{f'{tallies[n][band]:,} ({tallies[n][band] / counts[band]:.1%})':>14}"
            for n, _b in others))
    total = sum(counts.values())
    print(f"  {'ALL':<12}{total:>13,}" + "".join(
        f"{f'{sum(tallies[n].values()):,} ({sum(tallies[n].values()) / total:.1%})':>14}"
        for n, _b in others))
    print()

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

    def placed(leaf_set: frozenset[str], pool: Mapping[str, set[str]]) -> bool:
        """Does some node hold HOME_SHARE of this summary's leaves?"""
        need = HOME_SHARE * len(leaf_set)
        return any(len(leaf_set & held) >= need for held in pool.values())

    print(f"  curated summaries with 3+ leaf descendants in L: {len(key_sets):,}")
    print(f"  {'summary placement at 80%':<42}", end="")
    pool = [("O50s", o50s), *others]
    got = {}
    for name, build in pool:
        got[name] = sum(1 for s in key_sets.values() if placed(s, build["members"]))
    print("".join(f"{f'{got[n]:,} ({got[n] / len(key_sets):.1%})':>18}" for n, _b in pool))

    kids: dict[str, set[str]] = defaultdict(set)
    for child, ups in rel.items():
        for parent in ups:
            kids[parent].add(child)

    def descend(root: str) -> set[str]:
        """Every Reactome pathway under a top-level branch."""
        seen, stack = set(), [root]
        while stack:
            here = stack.pop()
            for kid in kids.get(here, ()):
                if kid not in seen:
                    seen.add(kid)
                    stack.append(kid)
        return seen

    # read_reactome_relation registers every parent as a key with an empty parent list, so the
    # top-level branches are the keys nothing claims -- 29 in the pinned release. Deriving them as
    # "appears as a parent, never as a child" gives the EMPTY set, which is how this silently
    # compared nothing the first time. The root belongs in its own leaf set, as o50s_report has it.
    tops = sorted(reactome_roots(rel))
    best_by: dict[str, list[float]] = {n: [] for n, _b in pool}
    for top in tops:
        leaves = {f"reactome:{k}" for k in descend(top) | {top}} & universe
        if len(leaves) < 3:
            continue
        for name, build in pool:
            best = 0.0
            for held in build["members"].values():
                inter = len(leaves & held)
                if inter:
                    best = max(best, inter / (len(leaves) + len(held) - inter))
            best_by[name].append(best)
    n_tops = len(best_by[pool[0][0]])
    print(f"  {'Reactome top-level branches compared':<42}"
          f"{f'{n_tops} of {len(tops)}':>18}")
    if not n_tops:
        print("  REFUSING to report a median over nothing; the branch derivation is wrong")
        return
    print(f"  {'Reactome median best Jaccard':<42}" + "".join(
        f"{float(np.median(best_by[n])):>18.3f}" for n, _b in pool))
    print()


def main(argv: list[str] | None = None) -> int:
    """Print sections A, B, D and E.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from restructure_s1 import gated_themes
    from thema.ontology import bitset as bits

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--s2", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S2"))
    parser.add_argument("--s1p", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S1p"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--parents", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22"
                                     "/potential_parents.tsv"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--out-version", default="0.4-leaves")
    args = parser.parse_args(argv)

    got = gated_themes(args)
    index = {key: i for i, key in enumerate(got.keys)}
    width = bits.words_for(got.n) * bits.WORD
    gated = np.vstack([bits.pack(m.tolist(), width)[None, :] for m in got.members])

    o50s, s2, s1p = (read_build(args.frozen), read_build(args.s2), read_build(args.s1p))
    builds = (("O50s", o50s), ("S2", s2), ("S1p", s1p))

    with np.load(args.probe, allow_pickle=False) as probe:
        o_accepted = probe["accepted"]
        o_drops = {int(v): int(k) for v, k in zip(probe["collapse_victim"],
                                                  probe["collapse_keeper"], strict=True)}
        o_drops.update({int(d): int(k) for d, k in zip(probe["merge_dropped"],
                                                       probe["merge_kept"], strict=True)})
    log = json.loads((args.s2 / "s2_construction.json").read_text())
    s_accepted = log["accepted"]
    s_drops = {int(k): int(v) for k, v in log["collapsed_map"].items()}
    s_drops.update({int(k): int(v) for k, v in log["merged_map"].items()})

    o_orig = originals_for(o50s, o_accepted, o_drops, gated)
    s_orig = originals_for(s2, s_accepted, s_drops, gated)
    o_edges, o_rests, o_gain = inheritance_edges(o50s, o_orig, index, width)
    s_edges, s_rests, s_gain = inheritance_edges(s2, s_orig, index, width)
    p_edges, p_rests, _ = inheritance_edges(s1p, None, index, width)

    print("PROMPT 54, SECTIONS A, B, D, E. S2 against O50s and S1p, by the same code.")
    print("Sections C, F, G and reviewer material are not run, as the prompt says.")
    print()
    print("=" * 104)
    print("A. CONSTRUCTION")
    print("=" * 104)
    sc = log
    om = o50s["manifest"]
    pm = s1p["manifest"]
    rows = [
        ("gated themes (input)", "26,120", f"{sc['gated']:,}", "26,120"),
        ("members inherited (into post-consensus themes)", "23,007", f"{sc['inherited']:,}",
         "0 (no consensus)"),
        ("themes that grew", "3,691", f"{sc['grew']:,}", "0"),
        ("supersessions (consensus rule 3)", "19,531", f"{sc['superseded']:,}",
         "n/a (removed)"),
        ("  of O50s's 19,531, became coexist", "-", f"{19531 - sc['superseded']:,}", "-"),
        ("after consensus", "6,589", f"{sc['after_consensus']:,}", "n/a"),
        ("chain collapses", f"{om['repair']['n_collapsed']:,}", f"{sc['collapsed']:,}",
         f"{pm['n_chain_collapses']:,}"),
        ("stale merges / sibling drops", f"{om['repair']['n_merged']:,}",
         f"{sc['stale_merged']:,}", f"{pm['n_sibling_drops']:,}"),
        ("repair rounds", str(om['repair']['rounds'].get('joint', '-')),
         str(sc['repair_rounds'].get('joint', '-')), f"{pm['n_rounds']} (whole loop)"),
        ("FINAL THEMES", f"{om['n_nodes']:,}", f"{s2['manifest']['n_nodes']:,}",
         f"{pm['n_nodes']:,}"),
        ("held-out FDR overall", str(om['confirmed']['overall_fdr']),
         str(s2['manifest']['confirmed']['overall_fdr']),
         str(pm['confirmed']['overall_fdr'])),
    ]
    print(f"  {'':<48}{'O50s':>18}{'S2':>18}{'S1p':>18}")
    for label, a, b, c in rows:
        print(f"  {label:<48}{a:>18}{b:>18}{c:>18}")
    floors = {json.dumps(b["manifest"]["floors"], sort_keys=True) for _n, b in builds}
    print(f"\n  the gate is untouched: all three carry the same floors -> {len(floors) == 1}")
    print()

    print("=" * 104)
    print("B. SHAPE")
    print("=" * 104)
    sizes = {name: {node: len(b["members"].get(node, ())) for node in b["ids"]}
             for name, b in builds}
    print(f"  {'band':<12}{'O50s':>12}{'S2':>12}{'S1p':>12}{'S2-O50s':>11}{'S1p-O50s':>11}")
    for _low, _high, band in BANDS:
        counts = [sum(1 for s in sizes[name].values() if band_of(s) == band)
                  for name, _b in builds]
        print(f"  {band:<12}{counts[0]:>12,}{counts[1]:>12,}{counts[2]:>12,}"
              f"{counts[1] - counts[0]:>+11,}{counts[2] - counts[0]:>+11,}")
    totals = [len(b["ids"]) for _n, b in builds]
    print(f"  {'TOTAL':<12}{totals[0]:>12,}{totals[1]:>12,}{totals[2]:>12,}"
          f"{totals[1] - totals[0]:>+11,}{totals[2] - totals[0]:>+11,}")
    print()

    print(f"  {'':<42}{'O50s':>14}{'S2':>14}{'S1p':>14}")
    stats: dict[str, list] = {}
    for name, b in builds:
        kids: dict[str, int] = defaultdict(int)
        for ps in b["parents"].values():
            for parent in ps:
                kids[parent] += 1
        counts = [kids.get(node, 0) for node in b["ids"]]
        roots = [node for node in b["ids"] if not b["parents"][node]]
        per: dict[str, int] = defaultdict(int)
        for keys in b["members"].values():
            for key in keys:
                per[key] += 1
        med, mx = levels(b["ids"], b["parents"], b["members"])
        multi = sum(1 for node in b["ids"] if len(b["parents"][node]) > 1)
        stats[name] = [len(b["ids"]), len(roots),
                       sum(1 for r in roots if sizes[name][r] <= 50),
                       sum(1 for node in b["ids"] if sizes[name][node] > 1280),
                       max(counts), statistics.median(counts),
                       multi / len(b["ids"]), sum(per.values()) / len(per), med, mx]
    labels = ("themes", "roots", "roots of 50 or fewer", "giants over 1,280",
              "children per node, max", "children per node, median", "multi-parent share",
              "mean themes per pathway", "levels to a root, median", "levels to a root, max")
    formats = ("{:,}", "{:,}", "{:,}", "{:,}", "{:,}", "{:.1f}", "{:.4f}", "{:.2f}",
               "{:.1f}", "{:,}")
    for i, (label, fmt) in enumerate(zip(labels, formats, strict=True)):
        print(f"  {label:<42}" + "".join(
            f"{fmt.format(stats[name][i]):>14}" for name, _b in builds))
    print(f"  {'edges':<42}{o_edges:>14,}{s_edges:>14,}{p_edges:>14,}")
    print(f"  {'edges resting on inherited members':<42}{o_rests:>14,}{s_rests:>14,}"
          f"{p_rests:>14,}")
    print(f"  {'  as a share of edges':<42}{o_rests / o_edges:>14.1%}"
          f"{s_rests / s_edges:>14.1%}{p_rests / p_edges:>14.1%}")
    print()
    for name, b, gain in (("O50s", o50s, o_gain), ("S2", s2, s_gain)):
        giants = sorted(((sizes[name][node], node) for node in b["ids"]
                         if sizes[name][node] > 1280), reverse=True)
        at = {node: i for i, node in enumerate(b["ids"])}
        print(f"  {name} giants over 1,280, with members gained by inheritance:")
        for size, node in giants:
            got_n = int(gain[at[node]]) if gain is not None else 0
            print(f"    {node}  {size:,}  +{got_n}")
    print()
    section_d(args, builds, index, width)
    section_e(args, o50s, (("S2", s2), ("S1p", s1p)), got.keys)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
