"""L1m: the L1 merge applied to MEMBERS, repeated until stable. Prompt 64, declared 24 Oct 2026.

Aviyah's decision of 24 Oct: the 90%-each-way test compares **members** (inclusion >= 0.5), not
cores (inclusion >= 0.9), and the pass is repeated to a fixed point. The threshold does not change,
so there is no new number. Prompt 63's evidence: comparing cores left 17,433 of 52,001 themes
repeating another theme's members exactly, because cores are unstable while the memberships they
produce are not.

**Steps 1 and 2 are prompt 61's, unchanged.** They are recomputed here rather than read back,
because :mod:`l1_build` persisted the theme-level arrays but not step 1's copies, its judge matrix
or the group-level inclusions. Recomputing re-runs the same code with the same brute-force checks,
and the printed counts can be compared against prompt 61's note line for line.

Each pass:

1. every theme's members and core come from its pooled copies (prompt 61's step 4, reused
   unchanged, over whatever grouping of groups the previous pass produced);
2. in O50s's family order -- support descending, then member-set size descending, then the member
   set's key -- each unclaimed theme seeds and absorbs every unclaimed theme whose members pass
   90%-each-way against the **seed's** members, so there is no chaining inside a pass;
3. the merged themes are re-pooled, which can change their members, which is why the pass repeats.

Both rules force ``min >= 0.9 * max``, so the size window the products use is exact, and every
comparison is integer arithmetic.

Usage:
    uv run scripts/l1m_build.py --runs 6 --out DIR     # a smoke side, with every check
    uv run scripts/l1m_build.py                        # the real side
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

MERGE_J = 0.90
FOUND_BAR = 10
MAX_PASSES = 50
SEED = 20261024
SAMPLE = 300
CHUNK = 20000


def same_members(inter: np.ndarray, left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Whether two member sets are the same theme: at least 90% of each inside the other.

    Args:
        inter: Overlap of each pair.
        left: Size of one side.
        right: Size of the other.

    Returns:
        A boolean mask.
    """
    return inter * 10 >= 9 * np.maximum(left, right)


def order_of(indptr: np.ndarray, pathway: np.ndarray, support: np.ndarray) -> np.ndarray:
    """O50s's family order over themes: support, then member-set size, then the set's key.

    Args:
        indptr: Member offsets per theme.
        pathway: Concatenated members.
        support: Support per theme.

    Returns:
        Theme indices, in order.
    """
    sizes = np.diff(indptr)
    keys = [pathway[indptr[i]:indptr[i + 1]].tobytes() for i in range(len(sizes))]
    rank = np.empty(len(sizes), dtype=np.int64)
    rank[np.argsort(keys, kind="stable")] = np.arange(len(sizes))
    return np.lexsort((rank, -sizes, -support))


def merge_pass(indptr: np.ndarray, pathway: np.ndarray, support: np.ndarray, n: int,
               report: bool = True) -> tuple[np.ndarray, int]:
    """One pass of the member merge. Returns the theme each theme was absorbed into.

    Args:
        indptr: Member offsets per theme.
        pathway: Concatenated members.
        support: Support per theme.
        n: Universe size.
        report: Print progress.

    Returns:
        ``(new theme index per old theme, merges, the old theme that seeded each new one)``.
    """
    from scipy import sparse

    total = len(indptr) - 1
    sizes = np.diff(indptr).astype(np.int64)
    matrix = sparse.csr_matrix(
        (np.ones(int(sizes.sum()), dtype=np.int32), pathway,
         indptr.astype(np.int64)), shape=(total, n))
    transposed = matrix.T.tocsc()
    by_size = np.argsort(sizes, kind="stable")
    sorted_size = sizes[by_size]
    order = order_of(indptr, pathway, support)
    claimed = np.zeros(total, dtype=bool)
    into = -np.ones(total, dtype=np.int64)
    seeds: list[int] = []
    merges = 0
    clock = time.perf_counter()
    for begin in range(0, total, CHUNK):
        block = order[begin:begin + CHUNK]
        neighbours: dict[int, np.ndarray] = {}
        band = np.maximum(np.floor(np.log2(np.maximum(sizes[block], 1))).astype(np.int64), 1)
        for b in np.unique(band):
            low, high = 2 ** int(b), 2 ** (int(b) + 1) - 1
            start = np.searchsorted(sorted_size, MERGE_J * low, side="left")
            stop = np.searchsorted(sorted_size, high / MERGE_J, side="right")
            if stop <= start:
                continue
            columns = by_size[start:stop]
            mine = block[band == b]
            got = (matrix[mine] @ transposed[:, columns]).tocoo()
            if not got.nnz:
                continue
            left = mine[got.row]
            right = columns[got.col]
            inter = got.data.astype(np.int64)
            keep = (left != right) & same_members(inter, sizes[left], sizes[right])
            left, right = left[keep], right[keep]
            if not len(left):
                continue
            pick = np.lexsort((right, left))
            left, right = left[pick], right[pick]
            edges = np.ones(len(left), dtype=bool)
            edges[1:] = left[1:] != left[:-1]
            for at in np.flatnonzero(edges):
                stop_at = np.searchsorted(left, left[at], side="right")
                neighbours[int(left[at])] = right[at:stop_at]
        for t in block.tolist():
            if claimed[t]:
                continue
            claimed[t] = True
            into[t] = len(seeds)
            for other in neighbours.get(t, ()):
                if not claimed[int(other)]:
                    claimed[int(other)] = True
                    into[int(other)] = len(seeds)
                    merges += 1
            seeds.append(t)
        if report:
            print(f"      pass {min(begin + CHUNK, total):,}/{total:,}, {len(seeds):,} themes "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return into, merges, np.array(seeds, dtype=np.int64)


def pool(side: dict[str, object], one: dict[str, object], two: dict[str, object],
         theme_of: np.ndarray, report: bool = False) -> dict[str, object]:
    """Prompt 61's step 4, reused unchanged, over an arbitrary grouping of the cored groups.

    Args:
        side: As ``l1_build.load_side`` returns.
        one: As ``l1_build.step_one`` returns.
        two: As ``l1_build.step_two`` returns.
        theme_of: Theme per group, ``-1`` for a group with no core.
        report: Print progress.

    Returns:
        As ``l1_build.step_four`` returns.
    """
    from l1_build import step_four

    seeds = np.zeros(int(theme_of.max()) + 1, dtype=np.int64)
    where = np.flatnonzero(theme_of >= 0)
    seeds[theme_of[where]] = where
    return step_four(side, one, two, {"theme_of": theme_of, "seed_group": seeds}, report=report)


def iterate(side: dict[str, object], one: dict[str, object], two: dict[str, object],
            n: int, report: bool = True) -> dict[str, object]:
    """Passes 2-3 to a fixed point, starting from one theme per cored group.

    Args:
        side: As ``l1_build.load_side`` returns.
        one: As ``l1_build.step_one`` returns.
        two: As ``l1_build.step_two`` returns.
        n: Universe size.
        report: Print progress.

    Returns:
        ``{four, theme_of, history, passes, capped}``.
    """
    cored = np.flatnonzero(two["has_core"])
    theme_of = -np.ones(len(two["has_core"]), dtype=np.int64)
    theme_of[cored] = np.arange(len(cored))
    four = pool(side, one, two, theme_of)
    history: list[dict[str, object]] = []
    lineage: list[np.ndarray] = []
    all_sizes: list[np.ndarray] = [np.diff(four["member_indptr"]).astype(np.int64)]
    capped = False
    for step in range(1, MAX_PASSES + 1):
        clock = time.perf_counter()
        before = np.diff(four["member_indptr"]).astype(np.int64)
        into, merges, seeds = merge_pass(four["member_indptr"], four["member_pathway"],
                                         four["support"], n, report=False)
        history.append({"pass": step, "themes_before": int(len(four["support"])),
                        "merges": int(merges),
                        "themes_after": int(into.max()) + 1,
                        "largest_before": sorted(before.tolist(), reverse=True)[:10],
                        "seconds": round(time.perf_counter() - clock, 1)})
        lineage.append(seeds)
        if report:
            print(f"    pass {step}: {len(four['support']):,} -> {int(into.max()) + 1:,} themes, "
                  f"{merges:,} merged ({time.perf_counter() - clock:.0f}s)", flush=True)
        if not merges:
            break
        theme_of = np.where(theme_of >= 0, into[theme_of], -1)
        four = pool(side, one, two, theme_of)
        all_sizes.append(np.diff(four["member_indptr"]).astype(np.int64))
        if step == MAX_PASSES:
            capped = True
    # The ten largest FINAL themes, traced back through the seed chain: at each pass a merged
    # theme's identity is its seed, so following the seed backwards gives one well-defined
    # ancestor per pass rather than an arbitrary constituent.
    final_sizes = all_sizes[-1]
    top = np.argsort(-final_sizes)[:10]
    grew: list[dict[str, object]] = []
    for f in top.tolist():
        at, back = f, [f]
        for seeds in reversed(lineage):
            at = int(seeds[at])
            back.append(at)
        back.reverse()
        grew.append({"final_theme": int(f), "final_size": int(final_sizes[f]),
                     "size_per_pass": [int(all_sizes[k][back[k]])
                                       for k in range(len(all_sizes))]})
    sizes_after = [sorted(s.tolist(), reverse=True)[:10] for s in all_sizes]
    return {"four": four, "theme_of": theme_of, "history": history, "lineage_top": grew,
            "sizes_after": sizes_after, "passes": len(history), "capped": capped}


def brute_adjacency(indptr: np.ndarray, pathway: np.ndarray, n: int,
                    sample: int = 2000) -> dict[str, object]:
    """The 90%-each-way adjacency by an explicit double loop, on a random sample of themes.

    Args:
        indptr: Member offsets per theme.
        pathway: Concatenated members.
        n: Universe size.
        sample: How many themes to compare.

    Returns:
        The comparison.
    """
    from scipy import sparse

    total = len(indptr) - 1
    rng = np.random.default_rng(SEED)
    pick = np.sort(rng.choice(total, size=min(sample, total), replace=False))
    sets = [set(pathway[indptr[i]:indptr[i + 1]].tolist()) for i in pick]
    slow = 0
    for i, a in enumerate(sets):
        for b in sets[i + 1:]:
            inter = len(a & b)
            if inter and 10 * inter >= 9 * max(len(a), len(b)):
                slow += 1
    sizes = np.array([len(s) for s in sets], dtype=np.int64)
    block = sparse.csr_matrix(
        (np.ones(int(sizes.sum()), dtype=np.int32),
         np.concatenate([pathway[indptr[i]:indptr[i + 1]] for i in pick]),
         np.concatenate([[0], np.cumsum(sizes)])), shape=(len(pick), n))
    got = (block @ block.T).tocoo()
    upper = got.row < got.col
    left, right, inter = got.row[upper], got.col[upper], got.data[upper].astype(np.int64)
    fast = int(same_members(inter, sizes[left], sizes[right]).sum())
    return {"themes": len(pick), "sparse": fast, "brute": slow, "identical": fast == slow}


def brute_full_pass(indptr: np.ndarray, pathway: np.ndarray, support: np.ndarray,
                    into: np.ndarray, limit: int = 20000) -> dict[str, object]:
    """Replay a whole pass with Python sets and compare the assignment, where that is feasible.

    All-pairs set arithmetic is quadratic, so this runs only on a side small enough for it and
    reports that it was skipped otherwise. On the sides where it does run it checks the greedy
    itself, not just the adjacency it walks.

    Args:
        indptr: Member offsets per theme, before the pass.
        pathway: Concatenated members.
        support: Support per theme.
        into: The pass's assignment.
        limit: Above this many themes, skip.

    Returns:
        The comparison.
    """
    total = len(indptr) - 1
    if total > limit:
        return {"themes": total, "ran": False, "identical": True,
                "note": f"skipped: {total:,} themes is above the {limit:,} all-pairs limit"}
    sets = [set(pathway[indptr[i]:indptr[i + 1]].tolist()) for i in range(total)]
    order = order_of(indptr, pathway, support)
    claimed = [False] * total
    slow = [-1] * total
    seeds = 0
    for t in order.tolist():
        if claimed[t]:
            continue
        claimed[t] = True
        slow[t] = seeds
        mine = sets[t]
        for other in range(total):
            if claimed[other]:
                continue
            inter = len(mine & sets[other])
            if inter and 10 * inter >= 9 * max(len(mine), len(sets[other])):
                claimed[other] = True
                slow[other] = seeds
        seeds += 1
    return {"themes": total, "ran": True, "sparse_themes": int(into.max()) + 1,
            "brute_themes": seeds, "identical": slow == into.tolist()}


def absorbed_invariant(indptr: np.ndarray, pathway: np.ndarray, support: np.ndarray,
                       into: np.ndarray) -> dict[str, object]:
    """Over EVERY absorbed theme, not a sample: does it pass the test against its seed?

    Args:
        indptr: Member offsets per theme, before the pass.
        pathway: Concatenated members.
        support: Support per theme.
        into: The pass's assignment.

    Returns:
        One count and whether the invariant holds.
    """
    total = len(indptr) - 1
    order = order_of(indptr, pathway, support)
    position = np.empty(total, dtype=np.int64)
    position[order] = np.arange(total)
    seed_of = np.zeros(int(into.max()) + 1, dtype=np.int64)
    best = np.full(int(into.max()) + 1, len(order), dtype=np.int64)
    for t in range(total):
        if position[t] < best[into[t]]:
            best[into[t]] = position[t]
            seed_of[into[t]] = t
    sizes = np.diff(indptr).astype(np.int64)
    checked = passed = 0
    for t in range(total):
        seed = int(seed_of[into[t]])
        if seed == t:
            continue
        checked += 1
        inter = len(np.intersect1d(pathway[indptr[t]:indptr[t + 1]],
                                   pathway[indptr[seed]:indptr[seed + 1]],
                                   assume_unique=True))
        passed += bool(same_members(np.array([inter]), np.array([sizes[t]]),
                                    np.array([sizes[seed]]))[0])
    return {"absorbed": checked, "pass_the_test_against_their_seed": passed,
            "identical": passed == checked}


def write_side(out: Path, side: dict[str, object], one: dict[str, object],
               two: dict[str, object], got: dict[str, object],
               checks: dict[str, object], light: bool = False) -> None:
    """Persist one side's L1m build.

    Args:
        out: Directory to write.
        side: As ``l1_build.load_side`` returns.
        one: As ``l1_build.step_one`` returns.
        two: As ``l1_build.step_two`` returns.
        got: As :func:`iterate` returns.
        checks: The brute-force comparisons.
        light: Write only the per-theme size, support, found and judged. A scramble side used for
            calibration contributes nothing but ``(size, support)`` rows, and its full membership
            archive is 46 MB; sixteen of them would be 740 MB for four columns.
    """
    four = got["four"]
    out.mkdir(parents=True, exist_ok=True)
    if light:
        np.savez_compressed(
            out / "themes_light.npz", size=np.diff(four["member_indptr"]).astype(np.int64),
            support=four["support"], found=four["found"], judged=four["judged"],
            groups=four["groups"])
    else:
        np.savez_compressed(
            out / "themes.npz", support=four["support"], found=four["found"],
            judged=four["judged"], groups=four["groups"], theme_of=got["theme_of"],
            core_indptr=four["core_indptr"], core_pathway=four["core_pathway"],
            member_indptr=four["member_indptr"], member_pathway=four["member_pathway"],
            incl_indptr=four["incl"]["indptr"], incl_pathway=four["incl"]["pathway"],
            incl_value=four["incl"]["inclusion"])
    (out / "build.json").write_text(json.dumps({
        "merge": "90% each way on MEMBERS, repeated to a fixed point",
        "merge_j": MERGE_J, "found_bar": FOUND_BAR, "max_passes": MAX_PASSES, "seed": SEED,
        "groups_with_a_core": int(two["has_core"].sum()),
        "themes": int(len(four["support"])),
        "kept_at_the_bar": int((four["found"] >= FOUND_BAR).sum()),
        "passes": got["passes"], "capped": got["capped"], "history": got["history"],
        "largest_after_each_pass": got["sizes_after"], "lineage_top": got["lineage_top"],
        "verification": checks,
    }, indent=1, default=float) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Build one side, verifying each pass.

    Args:
        argv: Command line.

    Returns:
        0, or 1 if a check disagrees.
    """
    from l1_build import load_side, step_one, step_two

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1m_2026-10-24/real"))
    parser.add_argument("--trees", type=Path, default=None,
                        help="override the cached real-tree directory, for a scramble side")
    parser.add_argument("--scramble-seed", type=int, default=None,
                        help="read a scramble side from the permanent cache by seed, instead of "
                             "spelling its path with --trees")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--cover", type=float, default=0.70,
                        help="kept for tree_cores.load_clusters; the match is 70% on each side")
    parser.add_argument("--light", action="store_true",
                        help="write only size, support, found and judged per theme")
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args(argv)
    if args.scramble_seed is not None:
        from scramble_cache import trees_for

        if args.trees is not None:
            raise SystemExit("pass --trees or --scramble-seed, not both")
        args.trees = trees_for(args.scramble_seed)

    print(f"L1m  merge on MEMBERS at {MERGE_J} each way, repeated to a fixed point "
          f"(cap {MAX_PASSES})", flush=True)
    side = load_side(args)
    one = step_one(side)
    two = step_two(side, one)
    n = side["n"]
    print(f"  steps 1-2 are prompt 61's, recomputed: {int(two['has_core'].sum()):,} groups with "
          f"a core of 3+", flush=True)
    got = iterate(side, one, two, n)
    four = got["four"]
    print(f"  {got['passes']} passes, capped {got['capped']}; "
          f"{int(two['has_core'].sum()):,} groups -> {len(four['support']):,} themes; "
          f"{int((four['found'] >= FOUND_BAR).sum()):,} found in >= {FOUND_BAR} runs", flush=True)

    checks: dict[str, object] = {}
    if not args.no_verify:
        clock = time.perf_counter()
        into, _merges, _seeds = merge_pass(four["member_indptr"], four["member_pathway"],
                                           four["support"], n, report=False)
        checks["final_pass_merges_nothing"] = {
            "merges": int(_merges), "identical": int(_merges) == 0}
        checks["adjacency"] = brute_adjacency(four["member_indptr"], four["member_pathway"], n)
        checks["full_pass_replay"] = brute_full_pass(
            four["member_indptr"], four["member_pathway"], four["support"], into)
        rows = [four["member_pathway"][four["member_indptr"][i]:four["member_indptr"][i + 1]]
                for i in range(len(four["support"]))]
        unique = len({r.tobytes() for r in rows})
        checks["identical_member_sets"] = {
            "themes": len(rows), "distinct": unique, "repeats": len(rows) - unique,
            "identical": len(rows) == unique}
        print(f"  VERIFICATION, seed {SEED} ({time.perf_counter() - clock:.0f}s)", flush=True)
        for name, check in checks.items():
            print(f"    {name:<28}{'IDENTICAL' if check['identical'] else 'MISMATCH'}  {check}",
                  flush=True)

    write_side(args.out, side, one, two, got, checks, light=args.light)
    print(f"  -> {args.out}", flush=True)
    return 0 if all(v["identical"] for v in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
