#!/usr/bin/env python3
"""Measure the three redundancy shapes in a build before any rule is chosen. Read-only.

Declared 9 Oct 2026 before any result. The reviewer's plausibility review left four open issues
(`DECISIONS.md`); three of them are structure that looks redundant by eye and sits **below every
threshold the build applies**. This measures how much there actually is, and what each candidate
rule would remove. **It applies nothing.**

1. **Chain ratios** -- ``|child| / |parent|`` over every edge. The declared collapse is 0.90, so the
   question is whether 0.85-0.90 holds a lot of edges and whether there is a natural valley to cut
   at rather than a round number.
2. **Sibling near-twins** -- the Jaccard of every pair of themes sharing a parent and not nested.
   The merge is 0.70, so anything at 0.5-0.7 is invisible to it.
3. **Fans** -- a node with three or more parents where **every** parent is the child plus at most a
   handful of other members. That is one theme described several nearly-identical ways, which is the
   ``n00150`` case.

Counts for the candidate rules are reported as **counts only**: how many edges, pairs or nodes each
would touch. Nothing is merged, collapsed or written to any build.

Usage::

    uv run scripts/redundancy_measure.py --stats STATS.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

#: Parent-size bands for the chain-ratio histogram.
PARENT_BANDS: tuple[tuple[int, int], ...] = (
    (3, 10), (11, 50), (51, 300), (301, 1000), (1001, 10**9))
#: Chain-ratio histogram range and step.
RATIO_LO, RATIO_HI, RATIO_STEP = 0.5, 1.0, 0.025
#: Sibling-Jaccard histogram range and step.
SIB_LO, SIB_HI, SIB_STEP = 0.4, 0.7, 0.025
#: A fan parent may add at most this many members beyond the child.
FAN_SLACK = 5
#: Minimum parents for a fan.
FAN_PARENTS = 3
#: Candidate rules, declared here and not applied.
CHAIN_RULE = 0.85
SIBLING_RULE = 0.60
#: The worked case the brief names.
FOCUS = "n00150"
FOCUS_LEVELS = 3
EXAMPLES = 5


def label(low: int, high: int) -> str:
    """Band label."""
    return f"{low}-{high}" if high < 10**9 else f"{low}+"


def band_of(size: int) -> str:
    """Parent-size band."""
    for low, high in PARENT_BANDS:
        if low <= size <= high:
            return label(low, high)
    return "other"


def histogram(values: list[float], lo: float, hi: float, step: float) -> dict[str, int]:
    """Counts per bin, bins labelled by their lower edge.

    Args:
        values: The values.
        lo: Lower edge.
        hi: Upper edge.
        step: Bin width.

    Returns:
        Bin label to count.
    """
    edges = np.arange(lo, hi + step / 2, step)
    out: dict[str, int] = {}
    for left, right in zip(edges, edges[1:], strict=False):
        last = abs(right - hi) < step / 2
        n = sum(1 for v in values
                if left <= v < right or (last and abs(v - hi) < 1e-12))
        out[f"{left:.3f}-{right:.3f}"] = n
    return out


def gist(node: str, stats: dict, n: int = 3) -> str:
    """The member names nearest a theme's centroid.

    Args:
        node: Theme id.
        stats: Per-node stats.
        n: How many names.

    Returns:
        A short description.
    """
    return "; ".join((stats.get(node, {}).get("nearest") or [])[:n])


def main(argv: list[str] | None = None) -> int:
    """Measure and report; change nothing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    path = root / args.build
    stats = json.loads(args.stats.read_text())["nodes"]

    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row.get("node") or row.get("id")] = float(row.get("support") or 0.0)
    parents: dict[str, set[str]] = defaultdict(set)
    children: dict[str, set[str]] = defaultdict(set)
    with (path / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
            children[row["parent"]].add(row["child"])
    sizes = {node: len(keys) for node, keys in members.items()}
    report: dict[str, object] = {"build": args.build, "n_themes": len(members)}

    # ---------------------------------------------------------------- 1. chain ratios
    edges = [(c, p, sizes[c] / sizes[p]) for c, ups in parents.items() for p in ups]
    ratios = [r for _c, _p, r in edges]
    print(f"1. CHAIN RATIOS over {len(edges):,} edges  (|child| / |parent|)")
    overall = histogram(ratios, RATIO_LO, RATIO_HI, RATIO_STEP)
    heads = "".join(f"{label(low, high):>10}" for low, high in PARENT_BANDS)
    print(f"   {'bin':<16}{'all':>8}" + heads)
    per_band = {
        label(low, high): histogram(
            [r for _c, p, r in edges if band_of(sizes[p]) == label(low, high)],
            RATIO_LO, RATIO_HI, RATIO_STEP)
        for low, high in PARENT_BANDS}
    for key, count in overall.items():
        print(f"   {key:<16}{count:>8,}"
              + "".join(f"{per_band[label(low, high)][key]:>10,}" for low, high in PARENT_BANDS))
    below = sum(1 for r in ratios if r < RATIO_LO)
    print(f"   (a further {below:,} edges are below {RATIO_LO})")
    in_8590 = [(c, p, r) for c, p, r in edges if 0.85 <= r < 0.90]
    in_8085 = [(c, p, r) for c, p, r in edges if 0.80 <= r < 0.85]
    print(f"   edges in 0.85-0.90: {len(in_8590):,}    edges in 0.80-0.85: {len(in_8085):,}")
    # Is there a valley? Compare each bin with its neighbours over 0.75-1.0.
    keys = [k for k in overall if float(k.split("-")[0]) >= 0.75]
    series = [(k, overall[k]) for k in keys]
    print("   shape over 0.75-1.0: " + " ".join(f"{v}" for _k, v in series))
    valleys = [series[i][0] for i in range(1, len(series) - 1)
               if series[i][1] < series[i - 1][1] and series[i][1] < series[i + 1][1]]
    print(f"   local minima in that range: {valleys if valleys else 'none -- monotone or flat'}")
    for name, rows in (("0.85-0.90", in_8590), ("0.80-0.85", in_8085)):
        print(f"   examples, {name}:")
        for c, p, r in sorted(rows, key=lambda t: -sizes[t[1]])[:EXAMPLES]:
            print(f"     {c} ({sizes[c]}) in {p} ({sizes[p]})  ratio {r:.3f}  "
                  f"support {support.get(c, 0):.3f} / {support.get(p, 0):.3f}")
            print(f"        child:  {gist(c, stats)}")
            print(f"        parent: {gist(p, stats)}")
    report["chain"] = {
        "n_edges": len(edges), "histogram": overall, "per_parent_band": per_band,
        "below_range": below, "n_0.85_0.90": len(in_8590), "n_0.80_0.85": len(in_8085),
        "local_minima_0.75_1.0": valleys,
        "examples_0.85_0.90": [{"child": c, "parent": p, "ratio": round(r, 4),
                                "child_size": sizes[c], "parent_size": sizes[p]}
                               for c, p, r in
                               sorted(in_8590, key=lambda t: -sizes[t[1]])[:EXAMPLES]],
        "examples_0.80_0.85": [{"child": c, "parent": p, "ratio": round(r, 4),
                                "child_size": sizes[c], "parent_size": sizes[p]}
                               for c, p, r in
                               sorted(in_8085, key=lambda t: -sizes[t[1]])[:EXAMPLES]],
    }

    # ---------------------------------------------------- 2. sibling near-twins
    print()
    pairs: dict[tuple[str, str], float] = {}
    for kids in children.values():
        ordered = sorted(kids)
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:]:
                if (a, b) in pairs:
                    continue
                sa, sb = members[a], members[b]
                if sa <= sb or sb <= sa:
                    continue
                inter = len(sa & sb)
                if not inter:
                    continue
                pairs[(a, b)] = inter / (len(sa) + len(sb) - inter)
    values = list(pairs.values())
    print(f"2. SIBLING NEAR-TWINS: {len(pairs):,} pairs share a parent and are not nested")
    sib = histogram(values, SIB_LO, SIB_HI, SIB_STEP)
    for key, count in sib.items():
        print(f"   {key:<16}{count:>8,}")
    for mark in (0.50, 0.60, 0.65):
        print(f"   at or above {mark:.2f}: {sum(1 for v in values if v >= mark):,}")
    print(f"   at or above 0.70 (the merge; should be 0 after the repair): "
          f"{sum(1 for v in values if v >= 0.70):,}")
    hot = sorted(((v, a, b) for (a, b), v in pairs.items() if 0.60 <= v < 0.70), reverse=True)
    print("   examples, 0.60-0.70:")
    for v, a, b in hot[:EXAMPLES]:
        print(f"     {a} ({sizes[a]}, support {support.get(a, 0):.3f}) vs "
              f"{b} ({sizes[b]}, support {support.get(b, 0):.3f})  J={v:.3f}")
        print(f"        {gist(a, stats)}")
        print(f"        {gist(b, stats)}")
    for a, b in (("n02333", "n03211"), ("n03211", "n02333")):
        if (a, b) in pairs:
            v = pairs[(a, b)]
            print(f"   the named pair {a} ({sizes[a]}) / {b} ({sizes[b]}): J={v:.3f}, "
                  f"supports {support.get(a, 0):.3f} / {support.get(b, 0):.3f}")
            print(f"        {gist(a, stats, 4)}")
            print(f"        {gist(b, stats, 4)}")
            break
    else:
        inter = len(members.get("n02333", set()) & members.get("n03211", set()))
        if inter:
            u = len(members["n02333"]) + len(members["n03211"]) - inter
            print(f"   the named pair n02333 / n03211 do NOT share a parent; "
                  f"their Jaccard is {inter / u:.3f}")
    report["siblings"] = {
        "n_pairs": len(pairs), "histogram": sib,
        "at_least": {f"{m:.2f}": sum(1 for v in values if v >= m)
                     for m in (0.50, 0.60, 0.65, 0.70)},
        "examples_0.60_0.70": [{"a": a, "b": b, "jaccard": round(v, 4),
                                "a_size": sizes[a], "b_size": sizes[b]}
                               for v, a, b in hot[:EXAMPLES]],
    }

    # ----------------------------------------------------------------- 3. fans
    print()
    fans: dict[str, list[str]] = {}
    for node, ups in parents.items():
        if len(ups) < FAN_PARENTS:
            continue
        if all(sizes[p] - sizes[node] <= FAN_SLACK for p in ups):
            fans[node] = sorted(ups, key=lambda p: -support.get(p, 0.0))
    print(f"3. FANS: {len(fans):,} nodes have {FAN_PARENTS}+ parents where EVERY parent is the "
          f"child plus at most {FAN_SLACK} members")
    spread = Counter(len(v) for v in fans.values())
    print("   parents per fan node: " + ", ".join(
        f"{k}:{spread[k]}" for k in sorted(spread)))
    sup_all = [support.get(p, 0.0) for v in fans.values() for p in v]
    if sup_all:
        print(f"   fan parents' support: median {np.median(sup_all):.3f}, "
              f"mean {np.mean(sup_all):.3f}, "
              f"share at or below 0.2: {np.mean([s <= 0.2 for s in sup_all]):.1%}")
    order = sorted(fans, key=lambda node: (-len(fans[node]), -sizes[node]))
    shown = [FOCUS] if FOCUS in fans else []
    shown += [node for node in order if node != FOCUS][:EXAMPLES - len(shown)]
    for node in shown:
        ups = fans[node]
        print(f"   {node} ({sizes[node]} members, support {support.get(node, 0):.3f}) "
              f"has {len(ups)} parents: {gist(node, stats)}")
        for p in ups:
            print(f"      parent {p} ({sizes[p]}, support {support.get(p, 0):.3f}, "
                  f"+{sizes[p] - sizes[node]}): {gist(p, stats)}")
    report["fans"] = {
        "n_fan_nodes": len(fans), "parents_per_node": dict(sorted(spread.items())),
        "parent_support_median": float(np.median(sup_all)) if sup_all else None,
        "parent_support_share_le_0.2": (float(np.mean([s <= 0.2 for s in sup_all]))
                                        if sup_all else None),
        "nodes": {node: {"size": sizes[node], "support": support.get(node),
                         "parents": [{"node": p, "size": sizes[p],
                                      "support": support.get(p),
                                      "extra": sizes[p] - sizes[node]} for p in ups]}
                  for node, ups in fans.items()},
    }

    # --------------------------------------------- 4. what each candidate rule would remove
    print()
    print("4. WHAT EACH CANDIDATE RULE WOULD REMOVE -- counts only, nothing applied")
    chain_hits = {c for c, p, r in edges if r >= CHAIN_RULE}
    n_chain = sum(1 for _c, _p, r in edges if r >= CHAIN_RULE)
    print(f"   chain collapse at {CHAIN_RULE}: {n_chain:,} edges qualify, touching "
          f"{len(chain_hits):,} distinct children "
          f"({100 * len(chain_hits) / len(members):.1f}% of themes)")
    sib_hits = {b for (a, b), v in pairs.items() if v >= SIBLING_RULE}
    print(f"   sibling merge at Jaccard >= {SIBLING_RULE}: "
          f"{sum(1 for v in values if v >= SIBLING_RULE):,} pairs qualify, "
          f"at most {len(sib_hits):,} themes dropped if one of each pair goes")
    fan_parents = {p for ups in fans.values() for p in ups}
    # NO fan-merge candidate. Aviyah decided on 9 Oct 2026 that a fan of facet parents around a
    # stable core is intended multi-parent DAG behaviour, not redundancy, so fans are measured and
    # described and no removal rule is proposed for them. The count below is the scale of the shape,
    # not the cost of a rule.
    print(f"   fans: NO removal rule proposed. {len(fans):,} fans over {len(fan_parents):,} parent "
          f"themes -- intended DAG behaviour per the 9 Oct decision, measured not gated")
    report["candidate_rules"] = {
        "chain_collapse_0.85": {"edges": sum(1 for _c, _p, r in edges if r >= CHAIN_RULE),
                                "distinct_children": len(chain_hits)},
        "sibling_merge_0.60": {"pairs": sum(1 for v in values if v >= SIBLING_RULE),
                               "themes_at_most": len(sib_hits)},
        "fan_merge": None,
        "fans_measured_not_gated": {
            "fans": len(fans), "parent_themes": len(fan_parents),
            "note": ("no removal rule proposed; a fan of facet parents around a stable core is "
                     "intended multi-parent DAG behaviour per Aviyah's 9 Oct 2026 decision")},
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
