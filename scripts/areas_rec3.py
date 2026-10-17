#!/usr/bin/env python3
"""The areas pass as one operator T, applied recursively. Constrained, size-weighted Ward.

Declared 16 Oct 2026 before any result, copied verbatim into DECISIONS.

rec2, rec2fix and the prompt-34 build each bolted something on: anchors held out of the
clustering, a giant drop, seam rules applied after the fact. None of that was argued and none of it
generalises. This states the pass as **one operator** that can be applied to its own output, so a
paper can describe it in a sentence: *take the maximal nodes that are not grab-bags, treat each as a
single item weighted by how many pathways it holds, and run the same resampled Ward recurrence over
them.* The precedents are Louvain-style aggregation, constrained Ward, HiDeF and NeXO.

**The operator is unchanged from O50's own configuration** -- 200 runs on 80% subsamples, Ward,
recurrence 0.70 on item sets, floors solved on 20 item scrambles and held out on 4, target 0.008,
caps 0.02 per stratum and 0.01 overall, consensus, the joint fixed point at twin 0.50 and chain 0.85
on pathway union sets, strict containment. **One thing is new**: an item is a *set* of pathways, not
a pathway, so Ward is continued from fixed clusters rather than started from points.

That is the constrained, size-weighted part, and it is exact rather than approximate. An item of
``w`` pathways enters as a cluster of weight ``w`` at its members' centroid, and Lance-Williams is
initialised with those weights:

* the stored distance is ``d(i,j) = sqrt(2 w_i w_j / (w_i + w_j)) * ||c_i - c_j||``, which reduces
  to the plain Euclidean distance when both weights are 1;
* the update is scipy's own ward recurrence with the cardinalities replaced by the weights.

Two checks pin it down, both in ``tests/test_areas_rec3.py``. With every weight 1 the merge
sequence, the merge counts and the heights are **scipy's ward** to 2e-15. With integer weights the
heights are **scipy's ward on the replicated point set** -- ``w`` coincident copies of each
centroid -- which is the definition of Ward continued from fixed clusters, and is what makes the
must-link reading exact instead of a metaphor.

Arm **W** is size-weighted and is the primary arm. Arm **E** gives every item weight 1 and is an
ablation only; it runs through the same code so the arms differ in exactly one number.

Usage::

    uv run scripts/areas_rec3.py --estimate
    uv run scripts/areas_rec3.py --arm W
    uv run scripts/areas_rec3.py --arm E
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist, squareform

import recursive_top_O50 as rt
import recursive_top_O50_rec2 as r2

#: A node this large is a grab-bag: never an item. O50's own bar, and Aviyah's for an area.
GIANT = rt.GIANT

#: Stop when the structure is this small at the top, or when a level admits nothing.
MAX_ROOTS = rt.MAX_ROOTS

#: Guard on the recursion, far above any plausible number of levels.
MAX_LEVELS = rt.MAX_LEVELS

#: Memory cap for the transitive reduction, in nodes per block.
BLOCK = 1024


def ward_condensed(centroids: np.ndarray, weights: Sequence[float]) -> np.ndarray:
    """The Ward distance between weighted clusters, condensed.

    ``d(i,j)^2 = 2 w_i w_j / (w_i + w_j) * ||c_i - c_j||^2`` is the parametrisation scipy's ward
    uses: for two singletons it is the plain Euclidean distance, and in general ``d^2 / 2`` is the
    increase in total within-cluster scatter that merging the pair would cause.

    Args:
        centroids: One unit vector per item.
        weights: One weight per item, in the same order.

    Returns:
        The condensed Ward distances, ``n * (n - 1) / 2`` entries.

    Raises:
        ValueError: If fewer than two items are given, or a weight is not positive.
    """
    w = np.asarray(weights, dtype=np.float64)
    if len(w) < 2:
        raise ValueError(f"need at least two items to cluster, got {len(w)}")
    if not np.all(w > 0):
        raise ValueError("every item weight must be positive")
    upper, lower = np.triu_indices(len(w), 1)
    return pdist(centroids, metric="euclidean") * np.sqrt(
        2.0 * w[upper] * w[lower] / (w[upper] + w[lower]))


def ward_weighted(condensed: np.ndarray, weights: Sequence[float]) -> np.ndarray:
    """Agglomerate by Ward's Lance-Williams update with arbitrary initial cluster weights.

    Squared distances are held in a full matrix with ``inf`` in the dead rows and columns, so the
    global minimum is one ``argmin`` and the update is one vectorised row write. ``O(n^2)`` memory
    and ``O(n^2)`` work per merge, which at the scale here -- a few hundred items -- is about 80 ms
    for a 529-item run against scipy's 1.2 ms. Paying that is the point: scipy's ward cannot take
    weights, and the weights are what makes this Ward continued from fixed clusters.

    Args:
        condensed: Condensed Ward distances from :func:`ward_condensed`.
        weights: One weight per item.

    Returns:
        A scipy-convention linkage matrix: ``(n - 1, 4)``, rows in merge order, ids below ``n`` the
        items themselves and step ``t`` creating id ``n + t``.
    """
    w = np.asarray(weights, dtype=np.float64)
    n = len(w)
    squared = squareform(np.asarray(condensed, dtype=np.float64)) ** 2
    np.fill_diagonal(squared, np.inf)
    size = w.astype(np.float64).copy()
    label = np.arange(n, dtype=np.int64)
    out = np.empty((n - 1, 4), dtype=np.float64)
    counts = np.ones(2 * n - 1, dtype=np.float64)
    row = np.empty(n, dtype=np.float64)
    for step in range(n - 1):
        first, second = divmod(int(np.argmin(squared)), n)
        if first > second:
            first, second = second, first
        pair = squared[first, second]
        left, right = sorted((int(label[first]), int(label[second])))
        counts[n + step] = counts[left] + counts[right]
        out[step] = (left, right, np.sqrt(max(pair, 0.0)), counts[n + step])
        # scipy's ward recurrence with the cardinalities replaced by the weights.
        head, tail = size[first], size[second]
        np.multiply(squared[first], head + size, out=row)
        row += (tail + size) * squared[second]
        row -= size * pair
        row /= head + tail + size
        np.maximum(row, 0.0, out=row)
        dead = ~np.isfinite(squared[first]) & ~np.isfinite(squared[second])
        row[dead] = np.inf
        row[first] = np.inf
        row[second] = np.inf
        squared[first, :] = row
        squared[:, first] = row
        squared[second, :] = np.inf
        squared[:, second] = np.inf
        size[first] = head + tail
        label[first] = n + step
    return out


def side_weighted(
    centroids: np.ndarray, weights: Sequence[float], n: int,
    rows: Sequence[np.ndarray], theta_match: float
) -> object:
    """One side's material, with the trees built by weighted Ward.

    The bookkeeping is ``linkage.run_from_merges``, which exists for exactly this: it does what
    ``recurrent.tree_from_subset`` does over a supplied merge sequence instead of calling scipy
    itself, and ``tests/ontology/test_linkage.py`` already proves the two agree field for field on
    Ward's own merges. So nothing in the recurrence machinery is reimplemented or modified here.

    Args:
        centroids: One unit vector per item.
        weights: One weight per item.
        n: Item count.
        rows: The shared subsample sequence.
        theta_match: Recurrence threshold, on item sets.

    Returns:
        A ``v04.Material``.
    """
    from thema.ontology.linkage import run_from_merges
    from thema.ontology.v04 import MIN_SIZE, material

    full = squareform(ward_condensed(centroids, weights))
    weight = np.asarray(weights, dtype=np.float64)
    runs = []
    for row in rows:
        block = squareform(full[np.ix_(row, row)], checks=False)
        merges = ward_weighted(block, weight[row])[:, :2]
        runs.append(run_from_merges(merges, n, row, MIN_SIZE))
    return material(runs, n, theta_match=theta_match)


def item_pathways(members: Sequence[set[str]]) -> tuple[list[str], dict[str, int]]:
    """A stable index over every pathway any item holds.

    Args:
        members: Pathway keys per item.

    Returns:
        ``(keys_in_index_order, key_to_index)``.
    """
    keys = sorted({key for held in members for key in held})
    return keys, {key: i for i, key in enumerate(keys)}


def operator_T(
    centroids: np.ndarray,
    weights: Sequence[float],
    members: Sequence[set[str]],
    runs: int,
    *,
    theta_match: float = rt.THETA_MATCH,
    theta_same: float = rt.THETA_SAME,
    collapse_share: float = rt.COLLAPSE_SHARE,
    report: bool = True,
) -> dict[str, object]:
    """T: the operator, applied once to a set of items.

    Identical to O50's configuration in every parameter. The only difference from a pathway-level
    build is that an item carries a weight and a pathway set, so the trees come from
    :func:`side_weighted` and every set comparison after the gate is on the **union** of an area's
    items' pathways. The item bookkeeping is ``areas_rec2fix.fold_units``, which is where the
    union is kept exact.

    Args:
        centroids: One unit vector per item.
        weights: Ward weight per item -- its pathway count for arm W, 1 for arm E.
        members: Pathway keys per item.
        runs: Trees per side.
        theta_match: Recurrence threshold, on item sets.
        theta_same: Twin cutoff, on pathway union sets.
        collapse_share: Chain share, on pathway union sets.
        report: Print progress.

    Returns:
        The areas, their items, the floors and the timings.

    Raises:
        ValueError: If an area's pathway set is not the union of its items' pathways.
    """
    from areas_rec2fix import fold_units
    from build_10770 import confirm
    from regate_floors import solve_to, without_minimum
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.recurrent import null_embeddings
    from thema.ontology.repair import repair_joint
    from thema.ontology.v04 import gate

    n = len(members)
    clock = time.perf_counter()
    rows_seq = rt.subsample_rows(n, runs)
    real = side_weighted(centroids, weights, n, rows_seq, theta_match)
    real_rows = real.rows()
    if report:
        print(f"    real side: {len(real_rows):,} candidates "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    calib: list[list[tuple[int, float]]] = []
    held_sides: list[list[tuple[int, float]]] = []
    for label, seeds, sink in (("calibration", r2.CALIBRATION_SEEDS, calib),
                               ("held out", r2.HELDOUT_SEEDS, held_sides)):
        for seed in seeds:
            got = side_weighted(np.ascontiguousarray(null_embeddings(centroids, seed)),
                                weights, n, rows_seq, theta_match)
            sink.append(got.rows())
            del got
        if report:
            print(f"    {label}: {len(seeds)} side(s) "
                  f"({time.perf_counter() - clock:.0f}s cumulative)", flush=True)

    solved = without_minimum(solve_to(real_rows, calib, r2.FLOOR_TARGET))
    confirmed = confirm(real_rows, held_sides, solved)
    if report:
        print("    floors " + ", ".join(
            f"{e['stratum']}:{e['effective']}" for e in solved), flush=True)

    keep = np.flatnonzero(gate(real_rows, solved)).tolist()
    if not keep:
        if report:
            print("    NOTHING through the gate; the recursion stops here", flush=True)
        return {"pathway_members": [], "item_indices": [], "supports": [], "floors": solved,
                "confirmed": confirmed, "n_candidates": len(real_rows), "n_gated": 0,
                "n_after_consensus": 0, "seconds": round(time.perf_counter() - clock, 1),
                "repair": {"n_collapsed": 0, "n_merged": 0, "rounds": {}}}

    item_blocks = [real.blocks[i] for i in keep]
    supports = [float(real.supports[i]) for i in keep]
    inclusions = [real.selections[i] for i in keep]
    keys, index = item_pathways(members)
    width = bits.words_for(len(keys)) * bits.WORD
    path_blocks = r2.as_pathway_blocks(item_blocks, members, index, len(keys))
    if report:
        print(f"    {len(keep):,} through the gate; comparing on {len(keys):,} pathways "
              f"instead of {n} items", flush=True)

    verdict = consensus(path_blocks, supports, inclusions, width, stray=0.0, jaccard=theta_same)
    accepted = list(verdict.accepted)
    folded = fold_units(len(keep), verdict.inherited, item_blocks, n)
    repaired = repair_joint(
        [verdict.members[i] for i in range(len(accepted))],
        [supports[c] for c in accepted], [inclusions[c] for c in accepted],
        collapse_share, theta_same, rt.SURVIVOR)
    dropped = set(repaired.collapsed) | set(repaired.merged)
    survivors = [i for i in range(len(accepted)) if i not in dropped]
    if len(survivors) != len(repaired.members):
        raise ValueError("collapse or merge did not only drop rows")
    if report:
        print(f"    consensus {len(keep):,} -> {len(accepted):,}; joint fixed point at "
              f"{collapse_share}/{theta_same} -> {len(repaired.members):,} areas", flush=True)

    item_rows = [sorted(bits.unpack(folded[accepted[i]])) for i in survivors]
    paths = [sorted(keys[b] for b in bits.unpack(block)) for block in repaired.members]
    for position, (held, rows) in enumerate(zip(paths, item_rows, strict=True)):
        union = sorted({key for row in rows for key in members[row]})
        if held != union:
            raise ValueError(
                f"area {position}: {len(held)} pathways against a union of {len(union)} over "
                f"{len(rows)} items")
    return {
        "pathway_members": paths,
        "item_indices": item_rows,
        "supports": [float(s) for s in repaired.supports],
        "floors": solved,
        "confirmed": confirmed,
        "n_candidates": len(real_rows),
        "n_gated": len(keep),
        "n_after_consensus": len(accepted),
        "seconds": round(time.perf_counter() - clock, 1),
        "repair": {"n_collapsed": len(repaired.collapsed), "n_merged": len(repaired.merged),
                   "rounds": repaired.rounds},
    }


def containment(blocks: Sequence[np.ndarray]) -> np.ndarray:
    """Strict-containment closure: ``out[child, parent]`` iff child is strictly inside parent.

    Args:
        blocks: Member bitsets, all the same width.

    Returns:
        An ``(n, n)`` boolean matrix.
    """
    stack = np.vstack([block[None, :] for block in blocks])
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    n = len(blocks)
    out = np.zeros((n, n), dtype=bool)
    for child in range(n):
        inside = np.bitwise_count(stack[child][None, :] & ~stack).sum(axis=1) == 0
        out[child] = inside & (sizes > sizes[child])
    np.fill_diagonal(out, False)
    return out


def direct_edges(closure: np.ndarray, block: int = BLOCK) -> np.ndarray:
    """Transitive reduction of a strict-containment closure.

    An edge is direct iff no third node sits between the two, which for a strict partial order is
    ``closure & ~(closure @ closure)``. The product is taken in float32 blocks so the whole
    structure -- every O50 node plus every area -- fits in memory: counts stay well inside float32's
    exact integer range at these sizes.

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


def structure(
    ids: Sequence[str],
    held: Sequence[set[str]],
    support: Sequence[float],
    keys: Sequence[str],
    *,
    theta_same: float = rt.THETA_SAME,
    collapse_share: float = rt.COLLAPSE_SHARE,
    report: bool = True,
) -> dict[str, object]:
    """One structure over every node: the rules over the whole set, then the reduced edges.

    No seam cases. Every pair in the set -- O50 node against O50 node, area against area, area
    against O50 node, giant against anything -- is held to the same two rules with O50's own
    survivor rule, and the edges are strict containment transitively reduced. O50 already satisfies
    both rules on its own, so in practice only pairs involving an area can act; that is checked
    rather than assumed, by reporting every event.

    Args:
        ids: Node ids.
        held: Pathway keys per node.
        support: Support per node.
        keys: The pathway index, in order.
        theta_same: Twin cutoff.
        collapse_share: Chain share.
        report: Print progress.

    Returns:
        The surviving nodes, the edges, the closure, the roots and what the rules did.

    Raises:
        ValueError: If the repair did something other than drop rows.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.repair import repair_joint

    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD
    blocks = [bits.pack(sorted(index[key] for key in one), width) for one in held]
    inclusions = [{b: 1.0 for b in bits.unpack(block)} for block in blocks]
    clock = time.perf_counter()
    repaired = repair_joint(blocks, list(support), inclusions, collapse_share, theta_same,
                            rt.SURVIVOR)
    dead = set(repaired.collapsed) | set(repaired.merged)
    alive = [i for i in range(len(ids)) if i not in dead]
    if len(alive) != len(repaired.members):
        raise ValueError("the structure repair did something other than drop rows")
    events = [
        {"victim": ids[v], "victim_size": len(held[v]), "keeper": ids[k],
         "keeper_size": len(held[k]), "rule": rule,
         "detail": repaired.merged_kind.get(v, "")}
        for rule, book in (("collapse", repaired.collapsed), ("merge", repaired.merged))
        for v, k in sorted(book.items())
    ]
    if report:
        print(f"    rules over {len(ids):,} nodes: {len(repaired.collapsed)} collapsed, "
              f"{len(repaired.merged)} merged -> {len(alive):,} "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    closure = containment([repaired.members[i] for i in range(len(alive))])
    edges = direct_edges(closure)
    roots = [ids[node] for position, node in enumerate(alive) if not closure[position].any()]
    parents = {ids[alive[c]]: [ids[alive[p]] for p in np.flatnonzero(edges[c])]
               for c in range(len(alive))}
    children: dict[str, list[str]] = {ids[node]: [] for node in alive}
    for child, above in parents.items():
        for parent in above:
            children[parent].append(child)
    if report:
        counts = [len(children[ids[node]]) for node in alive]
        print(f"    {int(edges.sum()):,} direct edges, {int(closure.sum()):,} containment pairs, "
              f"{len(roots)} roots, children max {max(counts, default=0)}", flush=True)
    return {
        "alive": [ids[i] for i in alive],
        "alive_at": alive,
        "closure": closure,
        "edges": edges,
        "roots": roots,
        "parents": parents,
        "children": children,
        "events": events,
        "collapsed": {ids[v]: ids[k] for v, k in repaired.collapsed.items()},
        "merged": {ids[v]: ids[k] for v, k in repaired.merged.items()},
        "rounds": repaired.rounds,
    }


def items_of(
    alive: Sequence[str], held: Mapping[str, set[str]], closure: np.ndarray,
    every_key: Sequence[str]
) -> tuple[list[str], list[str]]:
    """The next level's items: the maximal non-grab-bag nodes, plus any orphaned pathway.

    A node is an item iff it holds at most :data:`GIANT` pathways and no node that also holds at
    most :data:`GIANT` strictly contains it. A giant ancestor does not disqualify a node -- that is
    the whole point, and it is the same rule that made O50's 476 giant-only themes level-1 items.

    Args:
        alive: Node ids, in the closure's row order.
        held: Node id to pathway keys.
        closure: The strict-containment closure over ``alive``.
        every_key: Every pathway in the universe.

    Returns:
        ``(item_node_ids, loose_pathway_keys)``.
    """
    small = np.array([len(held[node]) <= GIANT for node in alive])
    picked = [alive[i] for i in range(len(alive))
              if small[i] and not (closure[i] & small).any()]
    covered = {key for node in picked for key in held[node]}
    return picked, sorted(set(every_key) - covered)


def write_arm(out: Path, payload: Mapping[str, object]) -> None:
    """Write one arm's build.

    Args:
        out: The arm's directory.
        payload: Everything the arm produced.
    """
    out.mkdir(parents=True, exist_ok=True)
    held = payload["held"]
    kind = payload["kind"]
    level_of = payload["level_of"]
    support = payload["support"]
    items_count = payload["items_count"]
    final = payload["final"]
    parents, children = final["parents"], final["children"]
    giants = {node for node in final["alive"] if len(held[node]) > GIANT}
    roots = set(final["roots"])

    with (out / "nodes.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "kind", "level", "size", "n_items", "support", "giant", "root",
                        "n_parents", "n_children", "parents", "children"])
        writer.writeheader()
        for node in final["alive"]:
            writer.writerow({
                "node": node, "kind": kind[node], "level": level_of[node],
                "size": len(held[node]), "n_items": items_count.get(node, 1),
                "support": round(float(support[node]), 6),
                "giant": "true" if node in giants else "",
                "root": "true" if node in roots else "",
                "n_parents": len(parents[node]), "n_children": len(children[node]),
                "parents": " ".join(sorted(parents[node])),
                "children": " ".join(sorted(children[node]))})

    with (out / "areas.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "level", "size", "n_items", "support", "giant", "root", "items"])
        writer.writeheader()
        for node in final["alive"]:
            if kind[node] != "area":
                continue
            writer.writerow({
                "node": node, "level": level_of[node], "size": len(held[node]),
                "n_items": items_count[node], "support": round(float(support[node]), 6),
                "giant": "true" if node in giants else "",
                "root": "true" if node in roots else "",
                "items": " ".join(payload["area_items"][node])})
    with (out / "area_members.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("node\tkey\n")
        for node in final["alive"]:
            if kind[node] != "area":
                continue
            for key in sorted(held[node]):
                handle.write(f"{node}\t{key}\n")
    with (out / "edges.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        for child, above in sorted(parents.items()):
            for parent in sorted(above):
                handle.write(f"{parent}\t{child}\n")
    with (out / "closure.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("parent\tchild\n")
        alive = final["alive"]
        closure = final["closure"]
        for child in range(len(alive)):
            for parent in np.flatnonzero(closure[child]):
                handle.write(f"{alive[parent]}\t{alive[child]}\n")
    with (out / "items.tsv").open("w", newline="", encoding="utf-8") as handle:
        handle.write("level\titem\tsize\tweight\n")
        for entry in payload["levels"]:
            for node, size, weight in zip(entry["item_ids"], entry["item_sizes"],
                                          entry["item_weights"], strict=True):
                handle.write(f"{entry['level']}\t{node}\t{size}\t{weight}\n")
    with (out / "giants.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "kind", "level", "size", "n_items", "support",
                        "share_of_universe"])
        writer.writeheader()
        universe = len(payload["every_key"])
        for node in sorted(giants, key=lambda n: -len(held[n])):
            writer.writerow({
                "node": node, "kind": kind[node], "level": level_of[node],
                "size": len(held[node]), "n_items": items_count.get(node, 1),
                "support": round(float(support[node]), 6),
                "share_of_universe": round(len(held[node]) / universe, 4)})

    levels = [{k: v for k, v in entry.items() if k != "closure"} for entry in payload["levels"]]
    (out / "levels.json").write_text(json.dumps({
        "arm": payload["arm"], "frozen": payload["frozen"],
        "every_key": payload["every_key"],
        "o50_giants": payload["o50_giants"],
        "kind": kind, "level_of": level_of, "support": support,
        "items_count": items_count, "area_items": payload["area_items"],
        "area_members": {n: sorted(held[n]) for n in final["alive"] if kind[n] == "area"},
        "levels": levels,
        "final": {
            "alive": final["alive"], "roots": final["roots"],
            "parents": parents, "children": children,
            "events": final["events"], "collapsed": final["collapsed"],
            "merged": final["merged"], "rounds": final["rounds"],
            "n_direct_edges": int(final["edges"].sum()),
            "n_closure_pairs": int(final["closure"].sum()),
        },
        "stopped_because": payload["stopped_because"],
        "seconds": payload["seconds"],
    }) + "\n", encoding="utf-8")
    write_manifest(out)


def write_manifest(out: Path) -> None:
    """Write one arm's manifest from the build it already wrote.

    Kept separate from :func:`write_arm` so a manifest can be regenerated from a finished build
    without rebuilding it, and so the two can never disagree: both read the same ``levels.json``.

    Args:
        out: The arm's directory, holding ``levels.json``.
    """
    payload = json.loads((out / "levels.json").read_text())
    levels = payload["levels"]
    final = payload["final"]
    held = payload["area_members"]
    alive = set(final["alive"])
    manifest = {
        "method": "v0.4 areas as one operator, applied recursively (rec3)",
        "arm": payload["arm"],
        "arm_meaning": ("size-weighted: an item enters Ward as a cluster of weight equal to its "
                        "pathway count" if payload["arm"] == "W"
                        else "equal weight: every item enters Ward with weight 1 (ablation only)"),
        "built_from": payload["frozen"],
        "declared": "DECISIONS, 2026-10-16, before any result",
        "operator": {
            "runs": rt.RUNS, "subsample": rt.SUBSAMPLE, "master_seed": rt.MASTER_SEED,
            "linkage": "ward, continued from fixed clusters by Lance-Williams with the item "
                       "weights as the initial cluster sizes",
            "theta_match": rt.THETA_MATCH, "theta_match_space": "item sets",
            "theta_same": rt.THETA_SAME, "theta_same_space": "pathway union sets",
            "collapse_share": rt.COLLAPSE_SHARE, "collapse_space": "pathway union sets",
            "survivor": rt.SURVIVOR, "joint_fixed_point": True,
            "containment": "strict subset over all members, which is O50's own definition",
            "floor_target": r2.FLOOR_TARGET, "floor_minimum": "none",
            "calibration_seeds": list(r2.CALIBRATION_SEEDS),
            "heldout_seeds": list(r2.HELDOUT_SEEDS),
            "caps": {"per_stratum": r2.CAP_STRATUM, "overall": r2.CAP_OVERALL},
        },
        "recursion": {
            "level_0": "the frozen O50, as is",
            "item_rule": f"the maximal nodes holding at most {GIANT} pathways, giants excluded as "
                         "items, plus any pathway in none of them",
            "giant": GIANT,
            "stop": f"a level admits no candidate under the floors, or the structure reaches "
                    f"{MAX_ROOTS} roots or fewer",
            "max_levels": MAX_LEVELS,
            "stopped_because": payload["stopped_because"],
            "levels_run": len(levels),
        },
        "no_special_cases": ["no anchors", "no giant drop", "no seam rules",
                             "one structure over every node, O50 giants included"],
        "o50_giants": payload["o50_giants"],
        "levels": [{
            "level": entry["level"], "n_items": entry["n_items"],
            "double_counting": entry["double_counting"],
            "n_candidates": entry["n_candidates"], "n_gated": entry["n_gated"],
            "n_after_consensus": entry["n_after_consensus"], "n_areas": entry["n_areas"],
            "floors": entry["floors"], "confirmed": entry["confirmed"],
            "seconds": entry["seconds"], "repair": entry["repair"],
            "n_nodes": entry.get("n_nodes"), "n_roots": entry.get("n_roots"),
            "n_direct_edges": entry.get("n_direct_edges"),
            "children_max": entry.get("children_max"),
        } for entry in levels],
        "final": {
            "n_nodes": len(final["alive"]), "n_roots": len(final["roots"]),
            "n_areas": sum(1 for n in held if n in alive),
            "n_direct_edges": final["n_direct_edges"],
            "n_closure_pairs": final["n_closure_pairs"],
            "n_collapsed": len(final["collapsed"]), "n_merged": len(final["merged"]),
            "children_max": max((len(v) for v in final["children"].values()), default=0),
            "areas_over_giant": sorted(n for n, keys in held.items()
                                       if n in alive and len(keys) > GIANT),
        },
        "seconds": payload["seconds"],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def run_arm(
    arm: str, nodes: Mapping[str, Mapping[str, str]], members: Mapping[str, set[str]],
    keys: Sequence[str], vectors: np.ndarray, runs: int, report: bool = True
) -> dict[str, object]:
    """The recursion for one arm.

    Args:
        arm: ``"W"`` for size-weighted, ``"E"`` for equal weight.
        nodes: O50 node rows.
        members: O50 node to member keys.
        keys: Embedding row keys, in row order.
        vectors: The centred matrix those keys index.
        runs: Trees per side.
        report: Print progress.

    Returns:
        Everything :func:`write_arm` needs.

    Raises:
        ValueError: If the arm is neither, or the level-0 items disagree with the unit rule.
    """
    if arm not in ("W", "E"):
        raise ValueError(f"arm must be W or E, not {arm!r}")
    clock = time.perf_counter()
    every_key = sorted({key for one in members.values() for key in one})
    held: dict[str, set[str]] = {node: set(one) for node, one in members.items()}
    support: dict[str, float] = {node: float(row["support"]) for node, row in nodes.items()}
    kind: dict[str, str] = dict.fromkeys(nodes, "o50")
    level_of: dict[str, int] = dict.fromkeys(nodes, 0)
    items_count: dict[str, int] = dict.fromkeys(nodes, 1)
    area_items: dict[str, list[str]] = {}
    o50_giants = sorted(n for n in members if len(members[n]) > GIANT)

    alive = sorted(nodes)
    print(f"  LEVEL 0 is the frozen O50 as is: {len(alive):,} nodes, "
          f"{len(o50_giants)} giants, {len(every_key):,} pathways", flush=True)
    base = structure(alive, [held[n] for n in alive], [support[n] for n in alive], every_key,
                     report=report)
    picked, loose = items_of(base["alive"], held, base["closure"], every_key)
    declared, _, _, rt_loose = rt.units_of(dict(nodes), dict(members))
    if sorted(picked) != sorted(declared) or loose != rt_loose:
        raise ValueError(
            f"the level-0 items ({len(picked)} + {len(loose)} loose) disagree with the unit rule "
            f"({len(declared)} + {len(rt_loose)} loose)")
    print(f"    level-0 items agree with the unit rule: {len(picked)} nodes + {len(loose)} loose",
          flush=True)

    final = base
    levels: list[dict[str, object]] = []
    stopped = "max levels reached"
    for level in range(1, MAX_LEVELS + 1):
        item_ids = list(picked) + [f"loose:{key}" for key in loose]
        item_members = [held[node] for node in picked] + [{key} for key in loose]
        sizes = [len(one) for one in item_members]
        weights = sizes if arm == "W" else [1] * len(sizes)
        print(f"\n  LEVEL {level}: T on {len(item_ids)} items "
              f"(arm {arm}, weights {'= pathway count' if arm == 'W' else 'all 1'})", flush=True)
        print(f"    item sizes min {min(sizes)} median {int(np.median(sizes))} "
              f"max {max(sizes)}; sum {sum(sizes):,} against {len(every_key):,} pathways "
              f"-> {sum(sizes) / len(every_key):.2f}x double counting", flush=True)
        centroids = rt.unit_centroids(item_members, keys, vectors)
        got = operator_T(centroids, weights, item_members, runs, report=report)
        entry = {
            "level": level, "n_items": len(item_ids), "item_ids": item_ids,
            "item_sizes": sizes, "item_weights": list(weights),
            "double_counting": round(sum(sizes) / len(every_key), 4),
            "floors": got["floors"], "confirmed": got["confirmed"],
            "n_candidates": got["n_candidates"], "n_gated": got["n_gated"],
            "n_after_consensus": got["n_after_consensus"], "seconds": got["seconds"],
            "repair": got["repair"],
            "n_areas": len(got["pathway_members"]),
            "area_ids": [], "area_sizes": [],
        }
        if not got["pathway_members"]:
            stopped = f"level {level} admitted no candidate under the floors"
            levels.append(entry)
            print(f"    STOP: {stopped}", flush=True)
            break

        new_ids = [f"a{level}_{i:05d}" for i in range(len(got["pathway_members"]))]
        for position, node in enumerate(new_ids):
            held[node] = set(got["pathway_members"][position])
            support[node] = got["supports"][position]
            kind[node] = "area"
            level_of[node] = level
            items_count[node] = len(got["item_indices"][position])
            area_items[node] = [item_ids[i] for i in got["item_indices"][position]]
        entry["area_ids"] = new_ids
        entry["area_sizes"] = [len(held[n]) for n in new_ids]
        print(f"    {len(new_ids)} areas, sizes {min(entry['area_sizes'])}/"
              f"{int(np.median(entry['area_sizes']))}/{max(entry['area_sizes'])} pathways",
              flush=True)

        pool = sorted(set(final["alive"]) | set(new_ids))
        final = structure(pool, [held[n] for n in pool], [support[n] for n in pool], every_key,
                          report=report)
        entry["n_nodes"] = len(final["alive"])
        entry["n_roots"] = len(final["roots"])
        entry["n_direct_edges"] = int(final["edges"].sum())
        entry["children_max"] = max(
            (len(final["children"][n]) for n in final["alive"]), default=0)
        levels.append(entry)
        if len(final["roots"]) <= MAX_ROOTS:
            stopped = f"level {level} brought the structure to {len(final['roots'])} roots"
            print(f"    STOP: {stopped}", flush=True)
            break
        nxt, nxt_loose = items_of(final["alive"], held, final["closure"], every_key)
        if sorted(nxt) == sorted(picked) and nxt_loose == loose:
            stopped = f"level {level} did not change the item set"
            print(f"    STOP: {stopped}", flush=True)
            break
        picked, loose = nxt, nxt_loose
    return {
        "arm": arm, "held": held, "support": support, "kind": kind, "level_of": level_of,
        "items_count": items_count, "area_items": area_items, "every_key": every_key,
        "o50_giants": o50_giants, "levels": levels, "final": final,
        "stopped_because": stopped, "seconds": round(time.perf_counter() - clock, 1),
        "frozen": "",
    }


def null_diagnostic(
    nodes: Mapping[str, Mapping[str, str]], members: Mapping[str, set[str]],
    keys: Sequence[str], vectors: np.ndarray, runs: int, scrambles: int,
    which: Sequence[str]
) -> int:
    """Why a floor can or cannot be solved: the real side against the scrambles, per stratum.

    The floor solver walks the **null's** own support values upward and takes the first cut where
    the averaged null count over the real count falls to the target. If the scrambled sides recur as
    strongly as the real one, no such cut exists and the stratum gets no floor at all -- which is
    not a failure of the solver but its verdict. This prints the evidence behind that verdict.

    Args:
        nodes: O50 node rows.
        members: O50 node to member keys.
        keys: Embedding row keys, in row order.
        vectors: The centred matrix.
        runs: Trees per side.
        scrambles: How many calibration seeds to use, from the declared list.
        which: Which arms to diagnose.

    Returns:
        0.
    """
    from build_10770 import STRATA, stratum_of
    from thema.ontology.recurrent import null_embeddings

    declared, _, _, loose = rt.units_of(dict(nodes), dict(members))
    item_members = [members[node] for node in declared] + [{key} for key in loose]
    sizes = [len(one) for one in item_members]
    n = len(item_members)
    centroids = rt.unit_centroids(item_members, keys, vectors)
    rows_seq = rt.subsample_rows(n, runs)
    seeds = list(r2.CALIBRATION_SEEDS[:scrambles])
    print(f"\nNULL DIAGNOSTIC: the real side against {len(seeds)} scrambles, {n} items, "
          f"{runs} runs")
    for arm in which:
        weights = sizes if arm == "W" else [1] * n
        real = side_weighted(centroids, weights, n, rows_seq, rt.THETA_MATCH).rows()
        nulls = []
        for seed in seeds:
            nulls.append(side_weighted(
                np.ascontiguousarray(null_embeddings(centroids, seed)), weights, n,
                rows_seq, rt.THETA_MATCH).rows())
        print(f"\n  ARM {arm}: {len(real):,} real candidates, "
              f"{', '.join(f'{len(one):,}' for one in nulls)} in the scrambles")
        print(f"    highest support: real {max(s for _, s in real):.3f}, "
              f"scrambles {max(max(s for _, s in one) for one in nulls):.3f}")
        print(f"    {'stratum':<9}{'cut':>7}{'real>=cut':>11}{'null>=cut':>11}{'FDR':>9}  "
              f"target {r2.FLOOR_TARGET}")
        for index, (low, high) in enumerate(STRATA):
            label = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
            mine = [s for size, s in real if stratum_of(size) == index]
            per = [[s for size, s in one if stratum_of(size) == index] for one in nulls]
            best = None
            for cut in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 1.00):
                null = sum(sum(1 for s in one if s >= cut) for one in per) / max(len(per), 1)
                keep = sum(1 for s in mine if s >= cut)
                fdr = null / keep if keep else None
                mark = ""
                if fdr is not None and fdr <= r2.FLOOR_TARGET and best is None:
                    best = cut
                    mark = "   <- a floor would work here"
                print(f"    {label:<9}{cut:>7.2f}{keep:>11,}{null:>11.2f}"
                      f"{(f'{fdr:.5f}' if fdr is not None else '-'):>9}{mark}")
            # The solver's OWN walk: it tries the null's support values in ascending order and
            # takes the first cut where the FDR reaches the target. Reporting the best FDR that
            # walk can reach says whether a floor exists at all, rather than whether one exists on
            # the fixed grid above.
            walk = sorted({s for one in per for s in one})
            reached: tuple[float, float] | None = None
            for cut in walk:
                null = sum(sum(1 for s in one if s >= cut) for one in per) / max(len(per), 1)
                keep = sum(1 for s in mine if s >= cut)
                if not keep:
                    continue
                value = null / keep
                if reached is None or value < reached[0]:
                    reached = (value, cut)
            if reached is None:
                print(f"    {label:<9}{'':>7}{'':>11}{'':>11}{'NO CUT':>9}   the solver has no "
                      f"candidate cut here")
            else:
                verdict = ("a floor exists" if reached[0] <= r2.FLOOR_TARGET
                           else "NO FLOOR EXISTS")
                print(f"    {label:<9}{'solver':>7}{'':>11}{'':>11}{reached[0]:>9.5f}"
                      f"   best over its own {len(walk)} cuts, at {reached[1]:.3f}: {verdict}")
        del nulls
    return 0

def main(argv: list[str] | None = None) -> int:
    """Run one arm, both arms, or just the estimate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--space", type=Path, default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50_rec3"))
    parser.add_argument("--arm", choices=("W", "E", "both"), default="both")
    parser.add_argument("--runs", type=int, default=rt.RUNS)
    parser.add_argument("--estimate", action="store_true")
    parser.add_argument("--manifest", action="store_true",
                        help="rewrite each built arm's manifest.json from its levels.json")
    parser.add_argument("--null-diagnostic", type=int, default=0, metavar="SCRAMBLES",
                        help="compare the real side with this many scrambles, per stratum")
    args = parser.parse_args(argv)

    from thema.ontology.universe import load_centred

    if args.manifest:
        for arm in ("W", "E"):
            if (args.out / arm / "levels.json").exists():
                write_manifest(args.out / arm)
                print(f"  -> {args.out / arm / 'manifest.json'}")
        return 0

    nodes, members = rt.read_build(args.frozen)
    keys, vectors = load_centred(args.space, args.data / "pathways.tsv")
    print(f"AREAS AS ONE OPERATOR (rec3) from {args.frozen}")

    if args.null_diagnostic:
        return null_diagnostic(nodes, members, keys, vectors, args.runs,
                               args.null_diagnostic,
                               ("W", "E") if args.arm == "both" else (args.arm,))

    if args.estimate:
        unit_themes, giants, _, loose = rt.units_of(nodes, members)
        item_members = [members[n] for n in unit_themes] + [{k} for k in loose]
        sizes = np.array([len(one) for one in item_members])
        n = len(item_members)
        centroids = rt.unit_centroids(item_members, keys, vectors)
        rows = rt.subsample_rows(n, args.runs)
        full = squareform(ward_condensed(centroids, sizes))
        clock = time.perf_counter()
        for row in rows[:5]:
            ward_weighted(squareform(full[np.ix_(row, row)], checks=False), sizes[row])
        one = (time.perf_counter() - clock) / 5
        sides = 1 + len(r2.CALIBRATION_SEEDS) + len(r2.HELDOUT_SEEDS)
        level1 = sides * args.runs * one * 1.3 + 120
        total = 2 * (level1 + 240)
        print("\nTIMED ESTIMATE (five real weighted-Ward runs actually run)")
        print(f"  level 1 items: {n} ({len(unit_themes)} themes + {len(loose)} loose), "
              f"{len(giants)} O50 giants excluded")
        print(f"  one weighted Ward run on {len(rows[0])} items: {one * 1000:.0f} ms")
        print(f"  {sides} sides x {args.runs} runs: {sides * args.runs * one / 60:.1f} min per arm "
              f"at level 1")
        print(f"  plus the structure over {len(nodes):,} nodes, later levels and the report: "
              f"about {total / 60:.0f} min for BOTH arms")
        print("  WELL UNDER the 3 h ceiling." if total < 10800 else "  OVER 3 h: STOP.")
        return 0

    for arm in (("W", "E") if args.arm == "both" else (args.arm,)):
        print(f"\n{'=' * 78}\nARM {arm}: "
              f"{'size-weighted, the primary arm' if arm == 'W' else 'equal weight, ablation only'}"
              f"\n{'=' * 78}", flush=True)
        payload = run_arm(arm, nodes, members, keys, vectors, args.runs)
        payload["frozen"] = str(args.frozen)
        write_arm(args.out / arm, payload)
        print(f"\n  -> {args.out / arm}  ({payload['seconds']:.0f}s), "
              f"stopped because {payload['stopped_because']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
