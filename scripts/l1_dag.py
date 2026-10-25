"""The strict-containment DAG over L1's recurring themes. Prompt 63, declared 24 Oct 2026.

Exploratory; **nothing is adopted and no membership is changed** -- no inheritance, no chain
collapse, no merging. ``A`` is a parent of ``B`` when every member of ``B`` is in ``A`` and ``A`` is
larger, reduced to immediate parents only.

The set is the **90%-each-way** themes found in at least 10 runs -- a **provisional** working bar,
not a calibrated one -- with members at inclusion >= 0.5.

**The transitive reduction is exact and does not need the full ancestor-of-ancestor product.**
Walking each theme's ancestors in ascending size, a candidate ``A`` is an immediate parent unless
some already-confirmed immediate parent ``P`` satisfies ``P`` subset of ``A``: any ancestor strictly
inside ``A`` has a minimal ancestor below it, and that minimal one is already confirmed. So the test
is against the confirmed parents alone, which is a handful rather than hundreds, and each test is a
lookup in the containment relation that has already been computed.

Levels follow the convention `s2_report.levels` set for every earlier build: a node's depth is the
**longest** upward path to a root, and the reported median and maximum are over **pathways**, each
taking the deepest node that holds it. The per-node figures are printed beside them because this
prompt does not say which.

Usage:
    uv run scripts/l1_dag.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SEED = 20261024
FOUND_BAR = 10
TOL_CONTAIN = 0.90
NEAR_CHAIN = 0.85
TOP_ROOT_MIN = 200
READ_ROOT_MIN = 50
BATCH_LINES = 2600
MATCH_J = 0.90
CHUNK = 256
SAMPLE = 300

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
    return BANDS[0][2]


def relations(accepted: dict[str, object], report: bool = True) -> dict[str, object]:
    """Strict containment, and the 90%-tolerance pairs, in one chunked pass.

    For a pair ``(B, A)`` with ``|A| > |B|``: containment is ``|A inter B| == |B|``, and a
    tolerance pair is ``|A inter B| >= 0.9 |B|`` without being containment. Integer arithmetic.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        report: Print progress.

    Returns:
        ``{child, parent, tol_child, tol_parent, tol_missing, seconds}``.
    """
    matrix, sizes = accepted["matrix"], accepted["sizes"]
    total = matrix.shape[0]
    transposed = matrix.T.tocsc()
    child: list[np.ndarray] = []
    parent: list[np.ndarray] = []
    tol_child: list[np.ndarray] = []
    tol_parent: list[np.ndarray] = []
    tol_missing: list[np.ndarray] = []
    clock = time.perf_counter()
    for begin in range(0, total, CHUNK):
        stop = min(begin + CHUNK, total)
        got = (matrix @ transposed[:, begin:stop]).tocoo()
        left, right = got.row, got.col + begin          # left is the candidate child
        inter = got.data.astype(np.int64)
        bigger = sizes[right] > sizes[left]
        exact = bigger & (inter == sizes[left])
        child.append(left[exact].astype(np.int32))
        parent.append(right[exact].astype(np.int32))
        near = bigger & (inter * 10 >= 9 * sizes[left]) & (inter < sizes[left])
        tol_child.append(left[near].astype(np.int32))
        tol_parent.append(right[near].astype(np.int32))
        tol_missing.append((sizes[left[near]] - inter[near]).astype(np.int32))
        if report and (begin // CHUNK) % 50 == 0:
            print(f"      containment {stop:,}/{total:,} "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
    out = {"child": np.concatenate(child), "parent": np.concatenate(parent),
           "tol_child": np.concatenate(tol_child), "tol_parent": np.concatenate(tol_parent),
           "tol_missing": np.concatenate(tol_missing)}
    out["seconds"] = round(time.perf_counter() - clock, 1)
    if report:
        print(f"    containment: {len(out['child']):,} ancestor pairs, "
              f"{len(out['tol_child']):,} tolerance pairs ({out['seconds']:.0f}s)", flush=True)
    return out


def reduce_transitive(accepted: dict[str, object], got: dict[str, object],
                      report: bool = True) -> dict[str, object]:
    """Immediate parents only, exactly, from the ancestor relation.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        got: As :func:`relations` returns.
        report: Print progress.

    Returns:
        ``{parents, indptr, ancestors, anc_indptr}`` as ragged arrays per theme.
    """
    sizes = accepted["sizes"]
    total = len(sizes)
    order = np.lexsort((sizes[got["parent"]], got["child"]))
    children = got["child"][order]
    parents = got["parent"][order]
    bounds = np.searchsorted(children, np.arange(total + 1))
    pairs = set((children.astype(np.int64) * total + parents.astype(np.int64)).tolist())
    keep_ptr = np.zeros(total + 1, dtype=np.int64)
    keep: list[np.ndarray] = []
    clock = time.perf_counter()
    for b in range(total):
        candidates = parents[bounds[b]:bounds[b + 1]]
        if not len(candidates):
            continue
        confirmed: list[int] = []
        for a in candidates.tolist():
            if any(p * total + a in pairs for p in confirmed):
                continue
            confirmed.append(a)
        keep.append(np.array(confirmed, dtype=np.int32))
        keep_ptr[b + 1] = len(confirmed)
        if report and b and b % 10000 == 0:
            print(f"      reduction {b:,}/{total:,} ({time.perf_counter() - clock:.0f}s)",
                  flush=True)
    keep_ptr = np.cumsum(keep_ptr)
    flat = np.concatenate(keep) if keep else np.zeros(0, dtype=np.int32)
    if report:
        print(f"    reduction: {len(flat):,} edges from {len(children):,} ancestor pairs "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"parents": flat, "indptr": keep_ptr, "anc_child": children, "anc_parent": parents,
            "anc_indptr": bounds}


def brute_check(accepted: dict[str, object], dag: dict[str, object],
                sample: int = SAMPLE) -> dict[str, object]:
    """Ancestors and immediate parents by explicit set loops, on a random sample of themes.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        dag: As :func:`reduce_transitive` returns.
        sample: How many themes to check.

    Returns:
        The comparison.
    """
    rng = random.Random(SEED)
    rows, sizes = accepted["rows"], accepted["sizes"]
    total = len(rows)
    sets = [set(r.tolist()) for r in rows]
    pick = rng.sample(range(total), min(sample, total))
    anc_same = parents_same = 0
    for b in pick:
        mine = sets[b]
        slow_anc = sorted(a for a in range(total)
                          if sizes[a] > sizes[b] and mine <= sets[a])
        fast_anc = sorted(dag["anc_parent"][
            dag["anc_indptr"][b]:dag["anc_indptr"][b + 1]].tolist())
        anc_same += slow_anc == fast_anc
        slow_parents = sorted(a for a in slow_anc
                              if not any(sets[c] < sets[a] for c in slow_anc if c != a))
        fast_parents = sorted(dag["parents"][
            dag["indptr"][b]:dag["indptr"][b + 1]].tolist())
        parents_same += slow_parents == fast_parents
    return {"themes": len(pick), "ancestors_agree": anc_same, "parents_agree": parents_same,
            "identical": anc_same == len(pick) and parents_same == len(pick)}


def depths(dag: dict[str, object], total: int, sizes: np.ndarray) -> np.ndarray:
    """Longest upward path to a root, per theme.

    Args:
        dag: As :func:`reduce_transitive` returns.
        total: Theme count.
        sizes: Members per theme.

    Returns:
        Depth per theme.
    """
    # Largest first: a parent is strictly larger, so its depth is always settled before its
    # children are reached. Ascending order would read -1 for every parent.
    depth = -np.ones(total, dtype=np.int64)
    for b in np.argsort(-sizes, kind="stable").tolist():
        mine = dag["parents"][dag["indptr"][b]:dag["indptr"][b + 1]]
        depth[b] = 0 if not len(mine) else 1 + int(depth[mine].max())
    return depth


def children_of(dag: dict[str, object], total: int) -> tuple[np.ndarray, np.ndarray]:
    """Children per theme, as a ragged array.

    Args:
        dag: As :func:`reduce_transitive` returns.
        total: Theme count.

    Returns:
        ``(indptr, children)``.
    """
    child = np.repeat(np.arange(total), np.diff(dag["indptr"]))
    parent = dag["parents"].astype(np.int64)
    order = np.argsort(parent, kind="stable")
    parent, child = parent[order], child[order]
    return np.searchsorted(parent, np.arange(total + 1)), child


def section_a(accepted: dict[str, object], dag: dict[str, object],
              depth: np.ndarray) -> dict[str, object]:
    """A: the shape of the DAG.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        dag: As :func:`reduce_transitive` returns.
        depth: Per-theme depth.

    Returns:
        The table as data.
    """
    sizes = accepted["sizes"]
    total = len(sizes)
    counts = np.diff(dag["indptr"])
    roots = counts == 0
    kid_ptr, kids = children_of(dag, total)
    kid_counts = np.diff(kid_ptr)
    bands = np.array([band_of(int(s)) for s in sizes])
    print("=" * 104)
    print("A. SHAPE")
    print("=" * 104)
    print(f"  {'themes':<44}{total:>12,}")
    print(f"  {'edges (immediate parents only)':<44}{int(counts.sum()):>12,}")
    print(f"  {'ancestor pairs before the reduction':<44}{len(dag['anc_child']):>12,}")
    print(f"  {'roots':<44}{int(roots.sum()):>12,}")
    print(f"  {'roots if themes of 3-5 are left out':<44}"
          f"{int((roots & (sizes >= 6)).sum()):>12,}")
    print(f"  {'multi-parent themes':<44}{int((counts >= 2).sum()):>12,}"
          f"{(counts >= 2).sum() / total:>10.2%}")
    print(f"  {'children per node, max / median':<44}"
          f"{int(kid_counts.max()):>12,} / {np.median(kid_counts):.1f}")
    print(f"  {'children per node, median over parents':<44}"
          f"{np.median(kid_counts[kid_counts > 0]):>12.1f}")
    print(f"  {'themes with no parent and no child':<44}"
          f"{int((roots & (kid_counts == 0)).sum()):>12,}")
    print(f"  {'identical member sets (duplicate themes)':<44}"
          f"{total - len({tuple(r.tolist()) for r in accepted['rows']}):>12,}")
    print()
    print("  levels to a root. Per PATHWAY, each taking the deepest theme that holds it, which is")
    print("  the convention every earlier build reported; the per-theme figures are beside it.")
    deepest = np.zeros(accepted["matrix"].shape[1], dtype=np.int64) - 1
    for t in range(total):
        np.maximum.at(deepest, accepted["rows"][t], depth[t])
    held = deepest >= 0
    print(f"  {'levels per pathway, median / max':<44}"
          f"{np.median(deepest[held]):>12.1f} / {int(deepest[held].max())}")
    print(f"  {'levels per theme, median / max':<44}"
          f"{np.median(depth):>12.1f} / {int(depth.max())}")
    print()
    print("  roots by band")
    print(f"  {'band':<12}{'themes':>10}{'roots':>10}{'share of the band':>20}"
          f"{'share of all roots':>20}")
    rows = {}
    for _lo, _hi, band in BANDS:
        where = bands == band
        if not where.any():
            continue
        count = int((roots & where).sum())
        print(f"  {band:<12}{int(where.sum()):>10,}{count:>10,}"
              f"{count / int(where.sum()):>20.1%}"
              f"{count / max(int(roots.sum()), 1):>20.1%}")
        rows[band] = {"themes": int(where.sum()), "roots": count}
    print()
    return {"themes": total, "edges": int(counts.sum()), "roots": int(roots.sum()),
            "roots_without_3_5": int((roots & (sizes >= 6)).sum()),
            "multi_parent": int((counts >= 2).sum()),
            "children_max": int(kid_counts.max()),
            "children_median": float(np.median(kid_counts)),
            "isolated": int((roots & (kid_counts == 0)).sum()),
            "levels_pathway_median": float(np.median(deepest[held])),
            "levels_pathway_max": int(deepest[held].max()),
            "roots_by_band": rows}


def section_b(accepted: dict[str, object], dag: dict[str, object], large: list[np.ndarray],
              args: argparse.Namespace) -> dict[str, object]:
    """B: the top of the DAG, and where the seven large sets sit in it.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        dag: As :func:`reduce_transitive` returns.
        large: The seven `large7` member arrays, largest first.
        args: Parsed arguments.

    Returns:
        The table as data.
    """
    sizes, rows = accepted["sizes"], accepted["rows"]
    total = len(sizes)
    counts = np.diff(dag["indptr"])
    roots = np.flatnonzero((counts == 0) & (sizes >= TOP_ROOT_MIN))
    kid_ptr, kids = children_of(dag, total)
    print("=" * 104)
    print(f"B. THE TOP: every root of {TOP_ROOT_MIN}+ pathways")
    print("=" * 104)
    print(f"  {'root':<8}{'size':>7}{'children':>10}   largest three children, "
          f"size (share of the root)")
    out: dict[str, object] = {"roots": []}
    for r in roots[np.argsort(-sizes[roots])].tolist():
        mine = kids[kid_ptr[r]:kid_ptr[r + 1]]
        top = mine[np.argsort(-sizes[mine])][:3]
        shown = ", ".join(f"{int(sizes[c]):,} ({sizes[c] / sizes[r]:.0%})" for c in top.tolist())
        print(f"  {'t' + str(r):<8}{int(sizes[r]):>7,}{len(mine):>10,}   {shown}")
        out["roots"].append({"theme": int(r), "size": int(sizes[r]), "children": int(len(mine)),
                             "largest": [[int(sizes[c]), float(sizes[c] / sizes[r])]
                                         for c in top.tolist()]})
    print()
    print("  the seven large7 sets: the L1 theme each matches at J >= 0.90, and its place")
    print(f"  {'set':<8}{'set size':>10}{'L1 theme':>10}{'theme size':>12}{'best J':>9}"
          f"{'root?':>8}{'parents':>9}   parent sizes")
    out["large7"] = []
    for i, members in enumerate(large):
        best, best_j = -1, 0.0
        for t in range(total):
            if abs(len(rows[t]) - len(members)) > len(members):
                continue
            inter = len(np.intersect1d(rows[t], members, assume_unique=True))
            union = len(rows[t]) + len(members) - inter
            value = inter / union if union else 0.0
            if value > best_j:
                best, best_j = t, value
        if best_j < MATCH_J:
            print(f"  {'set_' + str(i + 1):<8}{len(members):>10,}{'none':>10}{'--':>12}"
                  f"{best_j:>9.3f}{'--':>8}{'--':>9}")
            out["large7"].append({"set": i + 1, "size": int(len(members)), "theme": None,
                                  "best_j": best_j})
            continue
        mine = dag["parents"][dag["indptr"][best]:dag["indptr"][best + 1]]
        print(f"  {'set_' + str(i + 1):<8}{len(members):>10,}{'t' + str(best):>10}"
              f"{int(sizes[best]):>12,}{best_j:>9.3f}"
              f"{('yes' if not len(mine) else 'no'):>8}{len(mine):>9}   "
              + ", ".join(f"{int(sizes[p]):,}" for p in mine.tolist()[:6]))
        out["large7"].append({"set": i + 1, "size": int(len(members)), "theme": int(best),
                              "theme_size": int(sizes[best]), "best_j": best_j,
                              "root": not len(mine), "parents": int(len(mine)),
                              "parent_sizes": [int(sizes[p]) for p in mine.tolist()]})
    print()
    return out


def section_c(accepted: dict[str, object], dag: dict[str, object],
              got: dict[str, object]) -> dict[str, object]:
    """C: what a 90% tolerance would change. Report only; nothing is applied.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        dag: As :func:`reduce_transitive` returns.
        got: As :func:`relations` returns.

    Returns:
        The table as data.
    """
    sizes = accepted["sizes"]
    total = len(sizes)
    counts = np.diff(dag["indptr"])
    roots = counts == 0
    bands = np.array([band_of(int(s)) for s in sizes])
    missing = got["tol_missing"]
    print("=" * 104)
    print("C. WHAT A 90% TOLERANCE WOULD CHANGE -- REPORT ONLY, NOTHING IS APPLIED")
    print("=" * 104)
    print(f"  pairs where the child is at least {TOL_CONTAIN:.0%} inside a larger theme but not "
          f"wholly inside it")
    print(f"  {'pathways missing':<22}{'pairs':>12}{'distinct children':>20}")
    buckets = (("1", missing == 1), ("2-5", (missing >= 2) & (missing <= 5)),
               ("6+", missing >= 6))
    rows = {}
    for name, where in buckets:
        kids = len(np.unique(got["tol_child"][where]))
        print(f"  {name:<22}{int(where.sum()):>12,}{kids:>20,}")
        rows[name] = {"pairs": int(where.sum()), "children": kids}
    print(f"  {'ALL':<22}{len(missing):>12,}{len(np.unique(got['tol_child'])):>20,}")
    print()
    gain = np.zeros(total, dtype=bool)
    gain[np.unique(got["tol_child"])] = True
    print("  roots that would gain a parent, by band")
    print(f"  {'band':<12}{'roots':>10}{'would gain':>12}{'share':>9}")
    gained = {}
    for _lo, _hi, band in BANDS:
        where = roots & (bands == band)
        if not where.any():
            continue
        count = int((where & gain).sum())
        print(f"  {band:<12}{int(where.sum()):>10,}{count:>12,}"
              f"{count / int(where.sum()):>9.1%}")
        gained[band] = {"roots": int(where.sum()), "would_gain": count}
    print(f"  {'ALL':<12}{int(roots.sum()):>10,}{int((roots & gain).sum()):>12,}"
          f"{(roots & gain).sum() / max(roots.sum(), 1):>9.1%}")
    print()
    child = np.repeat(np.arange(total), np.diff(dag["indptr"]))
    parent = dag["parents"].astype(np.int64)
    near = sizes[child] * 100 >= NEAR_CHAIN * 100 * sizes[parent]
    print(f"  edges whose child holds at least {NEAR_CHAIN:.0%} of its parent: "
          f"{int(near.sum()):,} of {len(child):,} ({near.sum() / max(len(child), 1):.1%})")
    print(f"  distinct parents involved: {len(np.unique(parent[near])):,}; "
          f"distinct children: {len(np.unique(child[near])):,}")
    print()
    return {"tolerance_pairs": rows, "roots_gaining": gained,
            "near_chain_edges": int(near.sum()), "edges": int(len(child))}


def section_d(accepted: dict[str, object]) -> dict[str, object]:
    """D: placement of the pathways.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.

    Returns:
        The table as data.
    """
    matrix, sizes = accepted["matrix"], accepted["sizes"]
    n = matrix.shape[1]
    per_pathway = np.bincount(matrix.indices, minlength=n)
    largest = np.zeros(n, dtype=np.int64)
    for t in range(matrix.shape[0]):
        np.maximum.at(largest, accepted["rows"][t], sizes[t])
    print("=" * 104)
    print("D. PLACEMENT")
    print("=" * 104)
    print(f"  {'pathways in at least one theme':<44}{int((per_pathway > 0).sum()):>12,}"
          f"{(per_pathway > 0).sum() / n:>10.2%}")
    print(f"  {'pathways in no theme':<44}{int((per_pathway == 0).sum()):>12,}"
          f"{(per_pathway == 0).sum() / n:>10.2%}")
    print(f"  {'mean themes per pathway':<44}{per_pathway.mean():>12.1f}")
    print(f"  {'median themes per pathway':<44}{np.median(per_pathway):>12.1f}")
    print(f"  {'largest theme holding a pathway, median':<44}"
          f"{np.median(largest[per_pathway > 0]):>12.0f}")
    print(f"  {'largest theme holding a pathway, min':<44}"
          f"{int(largest[per_pathway > 0].min()):>12,}")
    print()
    return {"placed": int((per_pathway > 0).sum()), "unplaced": int((per_pathway == 0).sum()),
            "mean_themes_per_pathway": float(per_pathway.mean()),
            "median_largest": float(np.median(largest[per_pathway > 0]))}


def read_roots(accepted: dict[str, object], dag: dict[str, object],
               args: argparse.Namespace) -> dict[str, object]:
    """Write the reviewer's blind reading batches, and the key beside them.

    Every root of 50 or more pathways, shuffled, under a random id, as a member list sorted by
    name. Size and runs found appear **only** in the key file, which this function writes and
    nothing reads afterwards.

    Args:
        accepted: As ``l1_unions.accepted_side`` returns.
        dag: As :func:`reduce_transitive` returns.
        args: Parsed arguments.

    Returns:
        ``{batches, roots, key}``.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}
    sizes, rows = accepted["sizes"], accepted["rows"]
    found = accepted["side"]["t_found"][accepted["which"]]
    roots = np.flatnonzero((np.diff(dag["indptr"]) == 0) & (sizes >= READ_ROOT_MIN))
    rng = random.Random(SEED)
    shuffled = roots.tolist()
    rng.shuffle(shuffled)
    codes: set[str] = set()
    while len(codes) < len(shuffled):
        codes.add(f"R{rng.randrange(16 ** 4):04x}")
    ids = sorted(codes)
    rng.shuffle(ids)

    out = args.out / "dag" / "read_roots"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("batch_*.md"):
        stale.unlink()
    key: dict[str, object] = {}
    batches: list[Path] = []
    lines: list[str] = []
    number = 1

    def flush() -> None:
        """Write the lines gathered so far as one batch."""
        nonlocal lines, number
        if not lines:
            return
        path = out / f"batch_{number:02d}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        batches.append(path)
        number += 1
        lines = []

    for code, t in zip(ids, shuffled, strict=True):
        body = sorted(f"- {named.get(keys[p], (keys[p], '?'))[0]} "
                      f"[{named.get(keys[p], (keys[p], '?'))[1]}]"
                      for p in rows[t].tolist())
        block = [f"## {code}", ""] + body + [""]
        if lines and len(lines) + len(block) > BATCH_LINES:
            flush()
        lines += block
        key[code] = {"theme": int(t), "size": int(sizes[t]), "runs_found": int(found[t])}
    flush()
    (out / "KEY_DO_NOT_SHARE_L1_roots.json").write_text(
        json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  {len(shuffled)} roots of {READ_ROOT_MIN}+ pathways in {len(batches)} batches "
          f"-> {out}")
    print(f"    {', '.join(p.name for p in batches)}")
    print(f"    key written to {out / 'KEY_DO_NOT_SHARE_L1_roots.json'} and not read again")
    return {"roots": len(shuffled), "batches": [p.name for p in batches]}


def main(argv: list[str] | None = None) -> int:
    """The DAG, sections A-D, and the reviewer's reading batches.

    Args:
        argv: Command line.

    Returns:
        0, or 1 if the brute-force check disagrees.
    """
    from l1_merge_rule import distinct, members_of
    from l1_report import load_l1
    from l1_unions import accepted_side

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1_2026-10-24"))
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args(argv)

    print("PROMPT 63: THE DAG OF L1'S RECURRING THEMES, STRICT CONTAINMENT")
    print("  exploratory; nothing adopted, and no membership is changed")
    accepted = accepted_side(args.out / "real_bothways")
    n = accepted["matrix"].shape[1]
    print(f"  {len(accepted['rows']):,} themes (90% each way, found in >= {FOUND_BAR} runs -- a "
          f"PROVISIONAL bar), members at inclusion >= 0.5")
    print()
    got = relations(accepted)
    dag = reduce_transitive(accepted, got)
    depth = depths(dag, len(accepted["sizes"]), accepted["sizes"])
    print()

    checks: dict[str, object] = {}
    if not args.no_verify:
        clock = time.perf_counter()
        checks["dag"] = brute_check(accepted, dag)
        print(f"  VERIFICATION against explicit set loops, seed {SEED} "
              f"({time.perf_counter() - clock:.0f}s)")
        print(f"    {'IDENTICAL' if checks['dag']['identical'] else 'MISMATCH'}  {checks['dag']}")
        print()

    jaccard_side = load_l1(args.out / "real")
    which = np.flatnonzero((jaccard_side["t_size"] >= 800) & (jaccard_side["t_found"] >= FOUND_BAR))
    big = members_of(jaccard_side, which)
    kept = distinct(big, n)
    large = [big[i] for i in sorted(kept["kept"], key=lambda j: -len(big[j]))]

    record: dict[str, object] = {"themes": len(accepted["rows"]), "found_bar": FOUND_BAR,
                                 "verification": checks}
    record["A"] = section_a(accepted, dag, depth)
    record["B"] = section_b(accepted, dag, large, args)
    record["C"] = section_c(accepted, dag, got)
    record["D"] = section_d(accepted)
    record["read_roots"] = read_roots(accepted, dag, args)

    where = args.out / "dag"
    where.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(where / "dag.npz", theme=accepted["which"], size=accepted["sizes"],
                        parent_indptr=dag["indptr"], parent=dag["parents"], depth=depth,
                        tol_child=got["tol_child"], tol_parent=got["tol_parent"],
                        tol_missing=got["tol_missing"])
    (where / "dag.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"  -> {where}")
    return 0 if all(v["identical"] for v in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
