#!/usr/bin/env python3
"""Arm A with strict containment over the whole structure. Declared 18 Oct 2026. Adopts nothing.

**The bug.** Arm A's node set was rec2fix's: the areas, the anchors and the units. ``units_of``
excludes a giant from being a unit by design -- a grab-bag is never a unit -- and rec2fix never
re-adds the giants as parents. So arm A's 1,212-node structure omitted 4,798 of O50s's 5,658 themes
including all five giants, and five anchors that O50s itself places inside a giant came out as roots
with no possible parent: ``n00225``, ``n03971`` and ``n04999`` inside ``n01419``, ``n04528`` inside
``n01843``, ``n05000`` inside ``n03878``. The edges were not wrong, they were missing.

**The fix, in the arm A assembly only.** The structure is assembled over **every** O50s theme, the
five giants included, plus the surviving areas. ``areas_rec2fix`` is not touched: its defaults, its
unit rule and its tests stand, because the defect is in what arm A hands to the structure rather
than in how rec2fix builds areas.

**One detail that would otherwise undo prompt 44.** The spec keeps the twin and chain rules "as they
were", and arm A's rules removed 7 nodes -- all of them O50s themes. Re-adding every O50s theme
unqualified would resurrect them, so they are excluded by name: the rules' outcome stands.

**No reclustering.** The cached areas are reused verbatim, so the floors and the held-out FDR are
arm A's own, unchanged, and that is asserted rather than asserted-by-comment.

Two views, the second for reporting only:

* **A1** -- strict containment, 100%.
* **A2** -- Aviyah's propagation rule: a node at least 98% inside a larger node with at most 5
  pathways missing becomes a child, and the missing pathways are added to the parent and all its
  ancestors with evidence score 0. Iterated to a fixed point, because adding members can create a
  fresh near-containment, with the rounds reported rather than hidden.

Usage::

    uv run scripts/arm_a_containment.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: A1's containment bar, and A2's.
STRICT = 1.00
NEAR = 0.98

#: A2 only acts when at most this many pathways are missing.
MAX_MISSING = 5

#: Evidence score the propagated pathways carry.
PROPAGATED_INCLUSION = 0.0

#: Guard on A2's fixed point.
MAX_ROUNDS = 20

#: A node this large is a giant.
GIANT = 1000

#: Report-only: a root this far inside another node is reported, binned by what is missing.
INSIDE = 0.80
MISSING_BINS = ((0, 0), (1, 5), (6, 20), (21, 10 ** 9))

#: A node is a summary's home if it holds this share of the summary's leaves.
HOME_SHARE = 0.80


def bin_of(missing: int) -> str:
    """The label for a missing-pathway count.

    Args:
        missing: How many of the child's pathways the parent lacks.

    Returns:
        The bin label.
    """
    for low, high in MISSING_BINS:
        if low <= missing <= high:
            return f"{low}" if low == high else (
                f"{low}-{high}" if high < 10 ** 9 else f"{low}+")
    return "?"


def pack_all(groups: Mapping[str, set[str]], keys: Sequence[str]
             ) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Ids, a bitset matrix and sizes for a node set.

    Args:
        groups: Node id to pathway keys.
        keys: Every pathway key, in bit order.

    Returns:
        ``(ids, bitsets, sizes)``.
    """
    from thema.ontology import bitset as bits

    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD
    ids = sorted(groups)
    stack = np.vstack([bits.pack(sorted(index[k] for k in groups[node]), width)[None, :]
                       for node in ids])
    return ids, stack, np.bitwise_count(stack).sum(axis=1).astype(np.int64)


def containment(stack: np.ndarray, sizes: np.ndarray) -> np.ndarray:
    """Strict-containment closure: ``out[child, parent]``.

    Args:
        stack: Node bitsets.
        sizes: Node sizes.

    Returns:
        An ``(n, n)`` boolean matrix.
    """
    n = len(stack)
    out = np.zeros((n, n), dtype=bool)
    for child in range(n):
        inside = np.bitwise_count(stack[child][None, :] & ~stack).sum(axis=1) == 0
        out[child] = inside & (sizes > sizes[child])
    np.fill_diagonal(out, False)
    return out


def direct_edges(closure: np.ndarray, block: int = 512) -> np.ndarray:
    """Transitive reduction, in blocked float32 so a 6,000-node structure fits.

    Args:
        closure: The containment closure.
        block: Rows per block.

    Returns:
        The direct edges, same shape.

    Raises:
        ValueError: If the node count would make the float32 product inexact.
    """
    n = closure.shape[0]
    if n > 2 ** 24:
        raise ValueError(f"{n} nodes would make the float32 reduction inexact")
    right = closure.astype(np.float32)
    via = np.zeros_like(closure)
    for start in range(0, n, block):
        stop = min(start + block, n)
        via[start:stop] = (closure[start:stop].astype(np.float32) @ right) > 0
    return closure & ~via


def node_set(arm: Mapping[str, object], members: Mapping[str, set[str]]
             ) -> tuple[dict[str, set[str]], dict[str, str], list[str]]:
    """Arm A's structure over every O50s theme plus the surviving areas.

    The seam victims are excluded by name so the twin and chain rules keep their outcome; without
    that, re-adding "every O50s theme" would resurrect the seven nodes they removed.

    Args:
        arm: Arm A's payload.
        members: O50s node to member keys.

    Returns:
        ``(node id to keys, node id to kind, the excluded victims)``.
    """
    areas = {node: set(keys) for node, keys in arm["area_members"].items()}
    surviving = {node for node in arm["view"] if node in areas}
    dead = sorted(set(arm["collapsed"]) | set(arm["merged"]))
    held: dict[str, set[str]] = {node: set(keys) for node, keys in members.items()
                                 if node not in set(dead)}
    kind = {node: ("giant" if len(held[node]) > GIANT else "theme") for node in held}
    for node in sorted(surviving):
        held[node] = areas[node]
        kind[node] = "area"
    for node in arm["view"]:
        if node in members and node not in set(dead):
            kind[node] = "anchor" if arm["kinds"].get(node) == "anchor" else "unit"
    return held, kind, dead


def propagate(held: dict[str, set[str]], report: bool = True
              ) -> tuple[dict[str, set[str]], dict[str, object]]:
    """A2: pull a near-contained node under its parent by giving the parent what it lacks.

    A node at least :data:`NEAR` inside a larger node, missing at most :data:`MAX_MISSING`
    pathways, becomes a child; the missing pathways go to the parent **and all its ancestors**, so
    containment stays transitive. Iterated, because adding members can create a fresh
    near-containment, and the rounds are reported.

    Args:
        held: Node id to pathway keys; copied, not mutated.
        report: Print progress.

    Returns:
        ``(the grown node sets, a record of what was added)``.
    """
    grown = {node: set(keys) for node, keys in held.items()}
    added: dict[str, int] = defaultdict(int)
    events: list[dict[str, object]] = []
    rounds = 0
    while rounds < MAX_ROUNDS:
        rounds += 1
        ids, stack, sizes = pack_all(grown, sorted({k for v in grown.values() for k in v}))
        order = {node: i for i, node in enumerate(ids)}
        closure = containment(stack, sizes)
        acting: list[tuple[str, str, set[str]]] = []
        for child in ids:
            mine = grown[child]
            if closure[order[child]].any():
                continue
            best: tuple[int, str] | None = None
            for parent in ids:
                if parent == child or len(grown[parent]) <= len(mine):
                    continue
                missing = mine - grown[parent]
                if len(missing) > MAX_MISSING:
                    continue
                if len(mine & grown[parent]) < NEAR * len(mine):
                    continue
                if best is None or len(grown[parent]) < best[0]:
                    best = (len(grown[parent]), parent)
            if best is not None:
                acting.append((child, best[1], mine - grown[best[1]]))
        if not acting:
            break
        # Ancestors are taken from the closure as it stands before this round's additions, which
        # is what keeps the pass finite and the provenance readable.
        for child, parent, missing in acting:
            above = [parent] + [ids[i] for i in np.flatnonzero(closure[order[parent]])]
            for node in above:
                fresh = missing - grown[node]
                if fresh:
                    grown[node] |= fresh
                    added[node] += len(fresh)
            events.append({"child": child, "child_size": len(grown[child]), "parent": parent,
                           "missing": sorted(missing), "ancestors": len(above) - 1,
                           "round": rounds})
        if report:
            print(f"    round {rounds}: {len(acting)} node(s) pulled under a parent, "
                  f"{sum(len(m) for _, _, m in acting)} pathway slots to fill", flush=True)
    else:
        raise RuntimeError(f"A2's propagation did not settle in {MAX_ROUNDS} rounds")
    return grown, {"rounds": rounds, "events": events,
                   "pathways_added": int(sum(added.values())),
                   "nodes_grown": len(added),
                   "added_per_node": dict(sorted(added.items()))}


def describe(name: str, held: Mapping[str, set[str]], kind: Mapping[str, str],
             out: Path, review: Path | None, arm: Mapping[str, object],
             inclusions: Mapping[str, Mapping[str, float]] | None = None) -> dict[str, object]:
    """One view: the edges, the roots, the giants' parents, the near-containment bins.

    Args:
        name: ``"A1"`` or ``"A2"``.
        held: Node id to pathway keys.
        kind: Node id to kind.
        out: Where to write the build.
        review: Where to write ``roots.tsv``, or None.
        arm: Arm A's payload, for the floors it reuses.
        inclusions: Per node, per key, the evidence score, when it is not 1.0.

    Returns:
        The view's figures.
    """
    clock = time.perf_counter()
    keys = sorted({key for one in held.values() for key in one})
    ids, stack, sizes = pack_all(held, keys)
    closure = containment(stack, sizes)
    edges = direct_edges(closure)
    roots = [ids[i] for i in range(len(ids)) if not closure[i].any()]
    parents = {ids[c]: [ids[p] for p in np.flatnonzero(edges[c])] for c in range(len(ids))}
    children: dict[str, list[str]] = {node: [] for node in ids}
    for child, above in parents.items():
        for parent in above:
            children[parent].append(child)
    counts = [len(children[node]) for node in ids]
    giants = sorted((node for node in ids if len(held[node]) > GIANT),
                    key=lambda n: -len(held[n]))
    print(f"  {name}: {len(ids):,} nodes, {len(roots)} roots, {int(edges.sum()):,} direct edges, "
          f"{int(closure.sum()):,} containment pairs; children max {max(counts, default=0)}, "
          f"median {statistics.median(counts):.0f}  ({time.perf_counter() - clock:.0f}s)",
          flush=True)

    bins: Counter[str] = Counter()
    near: list[dict[str, object]] = []
    for node in roots:
        mine = held[node]
        for other in ids:
            if other == node or len(held[other]) <= len(mine):
                continue
            share = len(mine & held[other]) / len(mine)
            if share >= INSIDE:
                missing = len(mine - held[other])
                bins[bin_of(missing)] += 1
                near.append({"root": node, "root_size": len(mine), "other": other,
                             "other_size": len(held[other]), "share": round(share, 4),
                             "missing": missing})
    near.sort(key=lambda row: (-row["share"], row["root"]))

    out.mkdir(parents=True, exist_ok=True)
    with (out / "nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["node", "kind", "size", "giant", "root",
                                            "n_parents", "n_children", "parents"])
        writer.writeheader()
        for node in ids:
            writer.writerow({
                "node": node, "kind": kind[node], "size": len(held[node]),
                "giant": "true" if len(held[node]) > GIANT else "",
                "root": "true" if node in set(roots) else "",
                "n_parents": len(parents[node]), "n_children": len(children[node]),
                "parents": " ".join(sorted(parents[node]))})
    with (out / "edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for child, above in sorted(parents.items()):
            for parent in sorted(above):
                handle.write(f"{parent}\t{child}\n")
    if inclusions is not None:
        with (out / "propagated_members.tsv").open("w", newline="", encoding="utf-8") as handle:
            handle.write("node\tkey\tinclusion\n")
            for node in sorted(inclusions):
                for key, value in sorted(inclusions[node].items()):
                    handle.write(f"{node}\t{key}\t{value}\n")
    if review is not None:
        review.mkdir(parents=True, exist_ok=True)
        with (review / "roots.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                    fieldnames=["node", "kind", "size", "n_children", "members"])
            writer.writeheader()
            for node in sorted(roots, key=lambda n: -len(held[n])):
                writer.writerow({"node": node, "kind": kind[node], "size": len(held[node]),
                                 "n_children": len(children[node]),
                                 "members": " ".join(sorted(held[node]))})
    return {
        "view": name, "n_nodes": len(ids), "n_roots": len(roots),
        "roots": sorted(roots, key=lambda n: -len(held[n])),
        "root_rows": [{"node": n, "kind": kind[n], "size": len(held[n]),
                       "n_children": len(children[n])}
                      for n in sorted(roots, key=lambda n: -len(held[n]))],
        "giant_parents": {n: sorted(parents[n]) for n in giants},
        "giant_sizes": {n: len(held[n]) for n in giants},
        "n_direct_edges": int(edges.sum()), "n_closure_pairs": int(closure.sum()),
        "children_max": max(counts, default=0),
        "children_median": float(statistics.median(counts)) if counts else 0.0,
        "near_bins": dict(bins), "near": near[:200], "n_near": len(near),
        "floors": arm["floors"], "confirmed": arm["confirmed"],
        "seconds": round(time.perf_counter() - clock, 1),
    }


def main(argv: list[str] | None = None) -> int:
    """Rebuild arm A's structure strictly (A1) and under the propagation rule (A2)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--top", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_top"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--review", type=Path,
                        default=Path("data/experiments/top_two_arms_2026-10-17"))
    args = parser.parse_args(argv)

    import recursive_top_O50 as rt
    from thema.data.hierarchy import reactome_roots, read_reactome_relation
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.leaves import targets

    clock = time.perf_counter()
    arm = json.loads((args.top / "A" / "levels.json").read_text())
    nodes, members = rt.read_build(args.o50s)
    held, kind, dead = node_set(arm, members)
    print("ARM A, STRICT CONTAINMENT OVER THE WHOLE STRUCTURE. Declared 18 Oct 2026; "
          "adopts nothing.")
    print(f"  arm A as built: {len(arm['view']):,} nodes, {len(arm['roots'])} roots")
    print(f"  the fix: every O50s theme ({len(members):,}, the 5 giants included) plus the "
          f"{sum(1 for k in kind.values() if k == 'area')} surviving areas, "
          f"minus the {len(dead)} seam victims -> {len(held):,} nodes")
    print(f"  seam victims held out, so the twin and chain rules keep their outcome: {dead}",
          flush=True)

    # No reclustering: the floors and the held-out report are arm A's own bytes.
    cache = args.top / "areas_A_848items_200runs.json"
    cached = json.loads(cache.read_text())
    same = (json.dumps(cached["floors"], sort_keys=True)
            == json.dumps(arm["floors"], sort_keys=True)
            and json.dumps(cached["confirmed"], sort_keys=True)
            == json.dumps(arm["confirmed"], sort_keys=True))
    print(f"  NO RECLUSTERING: the cached areas are reused from {cache.name}; its floors and "
          f"held-out report are identical to arm A's: {same}", flush=True)
    if not same:
        raise SystemExit("the cached areas do not match arm A's floors; stop")

    a1 = describe("A1", held, kind, args.top / "A1", args.review / "A1", arm)
    print("\n  A2: Aviyah's propagation rule", flush=True)
    grown, record = propagate(held)
    inclusions = {node: {key: PROPAGATED_INCLUSION for key in grown[node] - held[node]}
                  for node in grown if grown[node] - held[node]}
    a2 = describe("A2", grown, kind, args.top / "A2", None, arm, inclusions)
    a2["propagation"] = record
    print(f"    {record['pathways_added']:,} pathway slots added over {record['nodes_grown']} "
          f"node(s) in {record['rounds']} round(s); "
          f"{len(record['events'])} child-parent pair(s) created", flush=True)

    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    names = {f"{r['source']}:{r['source_id']}": r["name"] for r in rows}
    universe = {key for one in members.values() for key in one}
    rel = read_reactome_relation(
        (args.data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {
        f"reactome:{c}": {f"reactome:{p}" for p in ps} for c, ps in rel.items()}
    for child, ups in go_edges(
            (args.data / "raw" / "go-basic.obo").read_text().splitlines(),
            PRIMARY_RELATIONS).items():
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

    def score(pool: Mapping[str, set[str]]) -> tuple[int, float]:
        """Summary placement and the Reactome median best Jaccard for one pool."""
        items = list(pool.values())
        total = 0
        for leaves in key_sets.values():
            if any(len(leaves & one) >= HOME_SHARE * len(leaves) for one in items):
                total += 1
        best = statistics.median([
            max((len(leaves & one) / len(leaves | one) for one in items if leaves or one),
                default=0.0) for leaves in branches.values()])
        return total, best

    o50s_pool = {node: set(one) for node, one in members.items()}
    for label, pool, record_into in (("O50s", o50s_pool, None),
                                     ("A1", held, a1), ("A2", grown, a2)):
        total, best = score(pool)
        print(f"  {label:<5} placement {total:,} of {len(key_sets):,} = "
              f"{total / len(key_sets):.1%}; Reactome median best J {best:.3f}", flush=True)
        if record_into is not None:
            record_into["placement"] = total
            record_into["placement_share"] = round(total / len(key_sets), 4)
            record_into["reactome_median_best_j"] = round(best, 4)

    for name, record_out in (("A1", a1), ("A2", a2)):
        (args.top / name / "view.json").write_text(json.dumps(record_out, indent=1) + "\n",
                                                   encoding="utf-8")
    print(f"\n  -> {args.top / 'A1'} and {args.top / 'A2'}  "
          f"({time.perf_counter() - clock:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
