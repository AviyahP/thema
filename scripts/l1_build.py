"""Level 1 of the core-recurrence design, steps 1-4. Prompt 61, declared 24 Oct 2026.

Aviyah's design. Every Ward cluster of 3+ pathways is a GROUP SEED. For a seed ``C`` and a run
``r``, ``r`` can judge ``C`` if at least 3 of ``C``'s members were drawn. ``D`` is the smallest
cluster of ``r``'s tree holding at least 70% of ``C``'s drawn members, and ``r`` FINDS ``C`` if in
addition ``C`` makes up at least 70% of ``D``. ``D`` is then ``C``'s copy in ``r``.

**The match is 70% on each side, not Jaccard on the union.** Prompt 58 showed why: two clusters that
are each 70% the same core score only about 0.54 on the union, so a Jaccard rule at any useful
threshold cannot see them as copies of one another.

**The size window is exact, not a heuristic.** ``D`` holds at least ``0.7k`` of the ``k`` drawn
members, so ``|D| >= 0.7k``; and if ``C`` is to make up 70% of ``D`` then ``|D| <= k / 0.7``. So the
smallest qualifying cluster, whenever the pair is found at all, has ``|D|`` in ``[0.7k, 1.43k]``.
Searching only that window is therefore exact: if nothing in it qualifies, the true smallest
qualifying cluster is larger than ``k / 0.7`` and fails the second test anyway. Without the window
the search is 200 runs x ~450,000 seeds of ancestor walking; with it, it is a handful of chunked
sparse products per run.

**C's own runs are counted exactly as O50s counts them**: a run in which the seed appears as a
cluster is eligible (all its members were drawn) and FOUND by definition, with the copy being the
seed itself -- ``recurrent.score``'s origin convention, ``src/thema/ontology/recurrent.py:739``.
Written out, because the smallest cluster holding 70% of C in C's own run can be a child of C, so
the general rule and the origin convention do not always agree.

Exploratory: no gate, no consensus, no repair, no edges, nothing adopted.

Usage:
    uv run scripts/l1_build.py --steps 12 --runs 6     # a smoke side, with brute-force checks
    uv run scripts/l1_build.py                         # the real side, all four steps
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

MIN_SIZE = 3
MIN_SHARED = 3
THETA = 0.70
CORE_CUT = 0.90
MEMBER_CUT = 0.50
MERGE_J = 0.90
SEED = 20261024
SAMPLE_PAIRS = 400
SAMPLE_GROUPS = 500
SAMPLE_CORES = 2000
SAMPLE_THEMES = 300
CHUNK = 20000

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


def load_side(args: argparse.Namespace) -> dict[str, object]:
    """The runs of one side, their clusters deduplicated into group seeds.

    Args:
        args: Parsed arguments.

    Returns:
        ``{records, present, n, seeds, sizes, origins, pool_of}`` where ``seeds`` is the CSR of
        distinct cluster sets, ``origins`` the runs each occurs in, and ``pool_of[r]`` the seed row
        each of run ``r``'s clusters is.
    """
    from thema.ontology.recurrent import _dedup
    from tree_cores import load_clusters, to_csr

    loaded = load_clusters(args)
    records, n = loaded["records"], loaded["n"]
    clock = time.perf_counter()
    stacked, origins, pool_of = _dedup(records, n)
    sizes = np.bitwise_count(stacked).sum(axis=1).astype(np.int64)
    print(f"  {len(stacked):,} distinct seeds of {MIN_SIZE}+ from "
          f"{len(loaded['stack']):,} clusters ({time.perf_counter() - clock:.0f}s)", flush=True)
    present = np.zeros((len(records), n), dtype=bool)
    for r, run in enumerate(records):
        present[r, _unpack(run.present)] = True
    return {"records": records, "present": present, "n": n, "seeds": to_csr(stacked, n),
            "bits": stacked, "sizes": sizes, "origins": origins, "pool_of": pool_of}


def _unpack(packed: np.ndarray) -> np.ndarray:
    """Set bit positions of a bitset.

    Args:
        packed: ``uint64`` words.

    Returns:
        The indices, ascending.
    """
    from thema.ontology import bitset as bits

    return np.fromiter(bits.unpack(packed), dtype=np.int64)


def step_one(side: dict[str, object], report: bool = True) -> dict[str, object]:
    """Step 1: which runs can judge each seed, which find it, and the copy in each.

    Args:
        side: As :func:`load_side` returns.
        report: Print progress.

    Returns:
        ``{eligible, found, copy_indptr, copy_run, copy_pool, support}``.
    """
    from tree_cores import to_csr

    seeds, present = side["seeds"], side["present"]
    records, pool_of, n = side["records"], side["pool_of"], side["n"]
    total, runs = seeds.shape[0], len(records)
    eligible = np.zeros(total, dtype=np.int32)
    found = np.zeros(total, dtype=np.int32)
    judge = np.zeros((total, runs), dtype=bool)
    own = np.zeros((total, runs), dtype=bool)
    for g, where in enumerate(side["origins"]):
        for r in where:
            own[g, r] = True
    pairs_seed: list[np.ndarray] = []
    pairs_run: list[np.ndarray] = []
    pairs_pool: list[np.ndarray] = []
    clock = time.perf_counter()
    for r in range(runs):
        drawn = seeds @ present[r].astype(np.int32)
        can = drawn >= MIN_SHARED
        eligible += can
        judge[:, r] = can
        mine = own[:, r]
        found += mine
        rows = np.flatnonzero(mine)
        pairs_seed.append(rows.astype(np.int32))
        pairs_run.append(np.full(len(rows), r, dtype=np.int16))
        pairs_pool.append(rows.astype(np.int32))        # the copy is the seed itself

        cluster_rows = to_csr(np.asarray(records[r].clusters), n)
        cluster_size = np.asarray(records[r].sizes).astype(np.int64)
        by_size = np.argsort(cluster_size, kind="stable")
        sorted_size = cluster_size[by_size]
        todo = np.flatnonzero(can & ~mine)
        if not len(todo):
            continue
        band = np.maximum(np.floor(np.log2(drawn[todo])).astype(np.int64), 1)
        for b in np.unique(band):
            low, high = 2 ** int(b), 2 ** (int(b) + 1) - 1
            start = np.searchsorted(sorted_size, THETA * low, side="left")
            stop = np.searchsorted(sorted_size, high / THETA, side="right")
            if stop <= start:
                continue
            columns = by_size[start:stop]
            block = cluster_rows[columns]
            which = todo[band == b]
            for begin in range(0, len(which), CHUNK):
                take = which[begin:begin + CHUNK]
                got = (seeds[take] @ block.T).tocoo()
                if not got.nnz:
                    continue
                left = take[got.row]
                right = columns[got.col]
                inter = got.data.astype(np.int64)
                keep = 10 * inter >= 7 * drawn[left]
                if not keep.any():
                    continue
                left, right, inter = left[keep], right[keep], inter[keep]
                # the smallest qualifying cluster per seed, which the laminar family makes unique
                order = np.lexsort((cluster_size[right], left))
                left, right, inter = left[order], right[order], inter[order]
                first = np.ones(len(left), dtype=bool)
                first[1:] = left[1:] != left[:-1]
                left, right, inter = left[first], right[first], inter[first]
                hit = 10 * inter >= 7 * cluster_size[right]
                if not hit.any():
                    continue
                found[left[hit]] += 1
                pairs_seed.append(left[hit].astype(np.int32))
                pairs_run.append(np.full(int(hit.sum()), r, dtype=np.int16))
                pairs_pool.append(pool_of[r][right[hit]].astype(np.int32))
        if report and (r + 1) % 25 == 0:
            print(f"      run {r + 1}/{runs} ({time.perf_counter() - clock:.0f}s)", flush=True)
    seed_of = np.concatenate(pairs_seed)
    run_of = np.concatenate(pairs_run)
    pool = np.concatenate(pairs_pool)
    order = np.lexsort((run_of, seed_of))
    seed_of, run_of, pool = seed_of[order], run_of[order], pool[order]
    indptr = np.zeros(total + 1, dtype=np.int64)
    np.add.at(indptr, seed_of.astype(np.int64) + 1, 1)
    indptr = np.cumsum(indptr)
    support = np.where(eligible > 0, found / np.maximum(eligible, 1), 0.0)
    if report:
        print(f"    step 1: {len(seed_of):,} (seed, run) copies, "
              f"median {np.median(found):.0f} runs found of "
              f"{np.median(eligible):.0f} able to judge "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"eligible": eligible, "found": found, "copy_indptr": indptr, "copy_run": run_of,
            "copy_pool": pool, "support": support, "judge": judge,
            "seconds": time.perf_counter() - clock}


def brute_step_one(side: dict[str, object], one: dict[str, object],
                   sample: int = SAMPLE_PAIRS) -> dict[str, object]:
    """Step 1 by an explicit loop over every cluster of the run, on a random sample of pairs.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        sample: How many ``(seed, run)`` pairs to check.

    Returns:
        The comparison.
    """
    seeds, present, records = side["bits"], side["present"], side["records"]
    rng = random.Random(SEED)
    total, runs = len(seeds), len(records)
    checked = agreed = found_fast = found_slow = copy_same = 0
    for _ in range(sample):
        g = rng.randrange(total)
        r = rng.randrange(runs)
        members = set(_unpack(seeds[g]).tolist())
        drawn = {p for p in members if present[r, p]}
        if len(drawn) < MIN_SHARED:
            continue
        checked += 1
        best, best_size = None, None
        for c in range(len(records[r].clusters)):
            cluster = set(_unpack(np.asarray(records[r].clusters)[c]).tolist())
            if 10 * len(drawn & cluster) >= 7 * len(drawn) and (
                    best_size is None or len(cluster) < best_size):
                best, best_size = c, len(cluster)
        slow = False
        slow_copy: set[int] = set()
        if best is not None:
            cluster = set(_unpack(np.asarray(records[r].clusters)[best]).tolist())
            if 10 * len(drawn & cluster) >= 7 * len(cluster):
                slow, slow_copy = True, cluster
        begin, end = one["copy_indptr"][g], one["copy_indptr"][g + 1]
        at = np.flatnonzero(one["copy_run"][begin:end] == r)
        fast = bool(len(at))
        fast_copy: set[int] = set()
        if fast:
            fast_copy = set(_unpack(seeds[int(one["copy_pool"][begin + at[0]])]).tolist())
        if r in side["origins"][g]:
            # the origin convention overrides the general rule, exactly as O50s does
            slow, slow_copy = True, members
        found_fast += fast
        found_slow += slow
        agreed += fast == slow
        copy_same += fast_copy == slow_copy
    return {"pairs_judged": checked, "verdicts_agree": agreed, "copies_agree": copy_same,
            "found_fast": found_fast, "found_slow": found_slow,
            "identical": agreed == checked and copy_same == checked}


def inclusions(side: dict[str, object], indptr: np.ndarray, run_of: np.ndarray,
               pool: np.ndarray, report: bool = True) -> dict[str, object]:
    """Inclusion of every pathway in every group or theme, from its pooled copies.

    ``inclusion(p) = copies holding p / copies from runs where p was drawn``, which is §10.7's
    rule. Computed in chunks: the numerator is a sparse product of the copy sets, the denominator a
    dense slice of the drawn matrix over just the pathways the numerator reaches.

    Args:
        side: As :func:`load_side` returns.
        indptr: Offsets into ``run_of`` and ``pool``, per group.
        run_of: The run of each copy.
        pool: The seed row each copy is.
        report: Print progress.

    Returns:
        ``{indptr, pathway, inclusion}`` as a ragged CSR over groups.
    """
    from scipy import sparse

    seeds, present = side["seeds"], side["present"]
    total = len(indptr) - 1
    out_ptr = np.zeros(total + 1, dtype=np.int64)
    columns: list[np.ndarray] = []
    values: list[np.ndarray] = []
    clock = time.perf_counter()
    for begin in range(0, total, CHUNK):
        stop = min(begin + CHUNK, total)
        lo, hi = int(indptr[begin]), int(indptr[stop])
        if hi == lo:
            continue
        rows = np.repeat(np.arange(stop - begin), np.diff(indptr[begin:stop + 1]))
        spread = sparse.csr_matrix(
            (np.ones(hi - lo, dtype=np.int32), (rows, np.arange(hi - lo))),
            shape=(stop - begin, hi - lo))
        numerator = (spread @ seeds[pool[lo:hi]]).tocsr()
        numerator.sort_indices()
        for local in range(stop - begin):
            head, tail = numerator.indptr[local], numerator.indptr[local + 1]
            cols = numerator.indices[head:tail]
            if not len(cols):
                continue
            mine = run_of[int(indptr[begin + local]):int(indptr[begin + local + 1])]
            denominator = present[np.ix_(mine, cols)].sum(axis=0)
            columns.append(cols.astype(np.int32))
            values.append((numerator.data[head:tail] / denominator).astype(np.float32))
            out_ptr[begin + local + 1] = len(cols)
        if report and (begin // CHUNK) % 5 == 0:
            print(f"      inclusions {stop:,}/{total:,} "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
    out_ptr = np.cumsum(out_ptr)
    return {"indptr": out_ptr,
            "pathway": np.concatenate(columns) if columns else np.zeros(0, dtype=np.int32),
            "inclusion": np.concatenate(values) if values else np.zeros(0, dtype=np.float32),
            "seconds": round(time.perf_counter() - clock, 1)}


def cut(incl: dict[str, object], threshold: float) -> tuple[np.ndarray, np.ndarray]:
    """The members at or above an inclusion threshold, as a ragged array.

    Args:
        incl: As :func:`inclusions` returns.
        threshold: Inclusion cut.

    Returns:
        ``(indptr, pathway)``.
    """
    total = len(incl["indptr"]) - 1
    keep = incl["inclusion"] >= threshold
    group = np.repeat(np.arange(total), np.diff(incl["indptr"]))
    sizes = np.bincount(group[keep], minlength=total) if len(keep) else np.zeros(total, dtype=int)
    indptr = np.concatenate([[0], np.cumsum(sizes)]).astype(np.int64)
    return indptr, incl["pathway"][keep]


def step_two(side: dict[str, object], one: dict[str, object],
             report: bool = True) -> dict[str, object]:
    """Step 2: the core of every group, and the groups that have none.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        report: Print progress.

    Returns:
        ``{incl, core_indptr, core_pathway, has_core}``.
    """
    incl = inclusions(side, one["copy_indptr"], one["copy_run"], one["copy_pool"], report)
    core_ptr, core_path = cut(incl, CORE_CUT)
    has_core = np.diff(core_ptr) >= MIN_SIZE
    if report:
        print(f"    step 2: {int(has_core.sum()):,} of {len(has_core):,} groups have a core of "
              f"{MIN_SIZE}+ ({incl['seconds']:.0f}s)", flush=True)
    return {"incl": incl, "core_indptr": core_ptr, "core_pathway": core_path,
            "has_core": has_core}


def brute_step_two(side: dict[str, object], one: dict[str, object], two: dict[str, object],
                   sample: int = SAMPLE_GROUPS) -> dict[str, object]:
    """Step 2 by explicit set arithmetic over each group's copies, on a random sample.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        two: As :func:`step_two` returns.
        sample: How many groups to check.

    Returns:
        The comparison.
    """
    rng = random.Random(SEED)
    present, seeds = side["present"], side["bits"]
    total = len(one["copy_indptr"]) - 1
    pick = rng.sample(range(total), min(sample, total))
    agreed = cores_same = 0
    for g in pick:
        begin, end = int(one["copy_indptr"][g]), int(one["copy_indptr"][g + 1])
        runs = one["copy_run"][begin:end]
        sets = [set(_unpack(seeds[int(p)]).tolist()) for p in one["copy_pool"][begin:end]]
        slow: dict[int, float] = {}
        for members in sets:
            for p in members:
                slow.setdefault(p, 0.0)
        for p in list(slow):
            holding = sum(1 for members in sets if p in members)
            drawn = sum(1 for r in runs if present[int(r), p])
            slow[p] = holding / drawn
        head, tail = int(two["incl"]["indptr"][g]), int(two["incl"]["indptr"][g + 1])
        fast = {int(a): float(b) for a, b in zip(two["incl"]["pathway"][head:tail],
                                                 two["incl"]["inclusion"][head:tail],
                                                 strict=True)}
        agreed += (set(fast) == set(slow)
                   and all(abs(fast[p] - slow[p]) < 1e-5 for p in slow))
        slow_core = {p for p, v in slow.items() if v >= CORE_CUT}
        a, b = int(two["core_indptr"][g]), int(two["core_indptr"][g + 1])
        cores_same += set(two["core_pathway"][a:b].tolist()) == slow_core
    return {"groups": len(pick), "inclusions_agree": agreed, "cores_agree": cores_same,
            "identical": agreed == len(pick) and cores_same == len(pick)}


def family_order(side: dict[str, object], one: dict[str, object],
                 mask: np.ndarray) -> np.ndarray:
    """O50s's family order over the cored groups: support, then seed size, then bitset key.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        mask: Which groups to order.

    Returns:
        Group indices, in order.
    """
    from thema.ontology import bitset as bits

    rows = np.flatnonzero(mask)
    keys = [bits.key(side["bits"][int(g)]) for g in rows]
    rank = np.empty(len(rows), dtype=np.int64)
    rank[np.argsort(keys, kind="stable")] = np.arange(len(rows))
    order = np.lexsort((rank, -side["sizes"][rows], -one["support"][rows]))
    return rows[order]


def step_three(side: dict[str, object], one: dict[str, object], two: dict[str, object],
               report: bool = True) -> dict[str, object]:
    """Step 3: merge groups whose cores agree at Jaccard 0.9 with the seed's core.

    In family order, each unclaimed group becomes a theme seed and absorbs every unclaimed group
    whose core reaches ``J >= 0.9`` with the SEED's core. The comparison is against the seed only,
    so there is no chaining. ``J >= 0.9`` forces ``smaller >= 0.9 * larger``, which is the exact
    window the products use.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        two: As :func:`step_two` returns.
        report: Print progress.

    Returns:
        ``{theme_of, seed_group, pairs}``.
    """
    from scipy import sparse

    cored = two["has_core"]
    order = family_order(side, one, cored)
    core_ptr, core_path = two["core_indptr"], two["core_pathway"]
    core_size = np.diff(core_ptr)
    rows = np.flatnonzero(cored)
    local = -np.ones(len(cored), dtype=np.int64)
    local[rows] = np.arange(len(rows))
    cores = sparse.csr_matrix(
        (np.ones(int(core_size[rows].sum()), dtype=np.int32),
         np.concatenate([core_path[core_ptr[g]:core_ptr[g + 1]] for g in rows]),
         np.concatenate([[0], np.cumsum(core_size[rows])])),
        shape=(len(rows), side["n"]))
    sizes = core_size[rows].astype(np.int64)
    by_size = np.argsort(sizes, kind="stable")
    sorted_size = sizes[by_size]
    transposed = cores.T.tocsc()

    claimed = np.zeros(len(rows), dtype=bool)
    theme_of = -np.ones(len(cored), dtype=np.int64)
    seed_group: list[int] = []
    pairs = 0
    clock = time.perf_counter()
    for begin in range(0, len(order), CHUNK):
        block = order[begin:begin + CHUNK]
        mine = local[block]
        neighbours: dict[int, np.ndarray] = {}
        band = np.maximum(np.floor(np.log2(np.maximum(sizes[mine], 1))).astype(np.int64), 1)
        for b in np.unique(band):
            low, high = 2 ** int(b), 2 ** (int(b) + 1) - 1
            start = np.searchsorted(sorted_size, MERGE_J * low, side="left")
            stop = np.searchsorted(sorted_size, high / MERGE_J, side="right")
            if stop <= start:
                continue
            columns = by_size[start:stop]
            got = (cores[mine[band == b]] @ transposed[:, columns]).tocoo()
            if not got.nnz:
                continue
            left = mine[band == b][got.row]
            right = columns[got.col]
            inter = got.data.astype(np.int64)
            union = sizes[left] + sizes[right] - inter
            keep = (left != right) & (inter * 100 >= MERGE_J * 100 * union)
            left, right = left[keep], right[keep]
            pairs += int(len(left))
            order_by = np.lexsort((right, left))
            left, right = left[order_by], right[order_by]
            edges = np.ones(len(left), dtype=bool)
            edges[1:] = left[1:] != left[:-1]
            for at in np.flatnonzero(edges):
                stop_at = np.searchsorted(left, left[at], side="right")
                neighbours[int(left[at])] = right[at:stop_at]
        for g in block:
            me = int(local[g])
            if claimed[me]:
                continue
            claimed[me] = True
            theme_of[g] = len(seed_group)
            for other in neighbours.get(me, ()):
                if not claimed[int(other)]:
                    claimed[int(other)] = True
                    theme_of[rows[int(other)]] = len(seed_group)
            seed_group.append(int(g))
        if report:
            print(f"      merge {min(begin + CHUNK, len(order)):,}/{len(order):,}, "
                  f"{len(seed_group):,} themes ({time.perf_counter() - clock:.0f}s)", flush=True)
    if report:
        print(f"    step 3: {len(seed_group):,} themes from {len(rows):,} cored groups, "
              f"{pairs:,} ordered core pairs at J >= {MERGE_J} "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"theme_of": theme_of, "seed_group": np.array(seed_group, dtype=np.int64),
            "pairs": pairs, "seconds": round(time.perf_counter() - clock, 1)}


def brute_step_three(side: dict[str, object], two: dict[str, object],
                     sample: int = SAMPLE_CORES) -> dict[str, object]:
    """The ``J >= 0.9`` core adjacency by an explicit double loop, on a random sample of cores.

    Args:
        side: As :func:`load_side` returns.
        two: As :func:`step_two` returns.
        sample: How many cored groups to compare.

    Returns:
        The comparison.
    """
    from scipy import sparse

    rows = np.flatnonzero(two["has_core"])
    rng = np.random.default_rng(SEED)
    pick = np.sort(rng.choice(len(rows), size=min(sample, len(rows)), replace=False))
    core_ptr, core_path = two["core_indptr"], two["core_pathway"]
    sets = [set(core_path[core_ptr[g]:core_ptr[g + 1]].tolist()) for g in rows[pick]]
    slow = 0
    for i, a in enumerate(sets):
        for b in sets[i + 1:]:
            inter = len(a & b)
            if inter and inter * 100 >= MERGE_J * 100 * (len(a) + len(b) - inter):
                slow += 1
    block = sparse.csr_matrix(
        (np.ones(sum(len(s) for s in sets), dtype=np.int32),
         np.concatenate([core_path[core_ptr[g]:core_ptr[g + 1]] for g in rows[pick]]),
         np.concatenate([[0], np.cumsum([len(s) for s in sets])])),
        shape=(len(pick), side["n"]))
    got = (block @ block.T).tocoo()
    sizes = np.array([len(s) for s in sets], dtype=np.int64)
    upper = got.row < got.col
    left, right, inter = got.row[upper], got.col[upper], got.data[upper].astype(np.int64)
    union = sizes[left] + sizes[right] - inter
    fast = int(((inter * 100) >= MERGE_J * 100 * union).sum())
    return {"cores": len(pick), "sparse": fast, "brute": slow, "identical": fast == slow}


def step_four(side: dict[str, object], one: dict[str, object], two: dict[str, object],
              three: dict[str, object], report: bool = True) -> dict[str, object]:
    """Step 4: pool each theme's copies one per run, then its support, core and members.

    The copy kept for a run is the one belonging to the theme's highest-support group found in that
    run, ties broken by the family order. Support is runs that found any of the theme's groups over
    runs able to judge any of them.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        two: As :func:`step_two` returns.
        three: As :func:`step_three` returns.
        report: Print progress.

    Returns:
        ``{incl, core_indptr, core_pathway, member_indptr, member_pathway, support, found,
        judged, groups, copy_indptr, copy_run, copy_pool}``.
    """
    theme_of = three["theme_of"]
    themes = len(three["seed_group"])
    order = family_order(side, one, two["has_core"])
    rank = np.empty(len(theme_of), dtype=np.int64)
    rank[order] = np.arange(len(order))

    counts = np.diff(one["copy_indptr"])
    group_of_copy = np.repeat(np.arange(len(counts)), counts)
    mine = theme_of[group_of_copy] >= 0
    theme_of_copy = theme_of[group_of_copy][mine]
    run_of_copy = one["copy_run"][mine]
    pool_of_copy = one["copy_pool"][mine]
    rank_of_copy = rank[group_of_copy[mine]]
    pick = np.lexsort((rank_of_copy, run_of_copy, theme_of_copy))
    theme_of_copy = theme_of_copy[pick]
    run_of_copy = run_of_copy[pick]
    pool_of_copy = pool_of_copy[pick]
    first = np.ones(len(pick), dtype=bool)
    first[1:] = ((theme_of_copy[1:] != theme_of_copy[:-1])
                 | (run_of_copy[1:] != run_of_copy[:-1]))
    theme_of_copy = theme_of_copy[first]
    run_of_copy = run_of_copy[first]
    pool_of_copy = pool_of_copy[first]
    indptr = np.zeros(themes + 1, dtype=np.int64)
    np.add.at(indptr, theme_of_copy + 1, 1)
    indptr = np.cumsum(indptr)
    found = np.diff(indptr).astype(np.int64)

    cored = np.flatnonzero(theme_of >= 0)
    by_theme = cored[np.argsort(theme_of[cored], kind="stable")]
    starts = np.searchsorted(theme_of[by_theme], np.arange(themes), side="left")
    judged = np.zeros(themes, dtype=np.int64)
    union = np.bitwise_or.reduceat(one["judge"][by_theme], starts, axis=0)
    judged = union.sum(axis=1).astype(np.int64)
    groups = np.bincount(theme_of[cored], minlength=themes)

    incl = inclusions(side, indptr, run_of_copy, pool_of_copy, report)
    core_ptr, core_path = cut(incl, CORE_CUT)
    member_ptr, member_path = cut(incl, MEMBER_CUT)
    support = np.where(judged > 0, found / np.maximum(judged, 1), 0.0)
    if report:
        print(f"    step 4: {themes:,} themes, median {np.median(np.diff(member_ptr)):.0f} "
              f"members, median {np.median(found):.0f} runs found of "
              f"{np.median(judged):.0f} judged", flush=True)
    return {"incl": incl, "core_indptr": core_ptr, "core_pathway": core_path,
            "member_indptr": member_ptr, "member_pathway": member_path, "support": support,
            "found": found, "judged": judged, "groups": groups, "copy_indptr": indptr,
            "copy_run": run_of_copy, "copy_pool": pool_of_copy}


def brute_step_four(side: dict[str, object], one: dict[str, object], two: dict[str, object],
                    three: dict[str, object], four: dict[str, object],
                    sample: int = SAMPLE_THEMES) -> dict[str, object]:
    """Step 4 by explicit loops over each theme's groups, on a random sample of themes.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        two: As :func:`step_two` returns.
        three: As :func:`step_three` returns.
        four: As :func:`step_four` returns.
        sample: How many themes to check.

    Returns:
        The comparison.
    """
    rng = random.Random(SEED)
    themes = len(three["seed_group"])
    pick = rng.sample(range(themes), min(sample, themes))
    order = family_order(side, one, two["has_core"])
    rank = np.empty(len(three["theme_of"]), dtype=np.int64)
    rank[order] = np.arange(len(order))
    members_of = {t: [] for t in pick}
    for g in np.flatnonzero(three["theme_of"] >= 0):
        t = int(three["theme_of"][g])
        if t in members_of:
            members_of[t].append(int(g))
    present, seeds = side["present"], side["bits"]
    copies_same = support_same = members_same = 0
    for t in pick:
        groups = sorted(members_of[t], key=lambda g: rank[g])
        best: dict[int, int] = {}
        judged: set[int] = set()
        for g in groups:
            judged |= set(np.flatnonzero(one["judge"][g]).tolist())
            begin, end = int(one["copy_indptr"][g]), int(one["copy_indptr"][g + 1])
            for r, p in zip(one["copy_run"][begin:end], one["copy_pool"][begin:end],
                            strict=True):
                best.setdefault(int(r), int(p))
        head, tail = int(four["copy_indptr"][t]), int(four["copy_indptr"][t + 1])
        fast = dict(zip(four["copy_run"][head:tail].tolist(),
                        four["copy_pool"][head:tail].tolist(), strict=True))
        copies_same += fast == best
        slow_support = len(best) / len(judged) if judged else 0.0
        support_same += abs(slow_support - float(four["support"][t])) < 1e-9
        counts: dict[int, list[int]] = {}
        for p in best.values():
            for q in _unpack(seeds[p]).tolist():
                counts.setdefault(q, [0, 0])
                counts[q][0] += 1
        for q in counts:
            counts[q][1] = sum(1 for r in best if present[r, q])
        slow_members = {q for q, (a, b) in counts.items() if a / b >= MEMBER_CUT}
        a, b = int(four["member_indptr"][t]), int(four["member_indptr"][t + 1])
        members_same += set(four["member_pathway"][a:b].tolist()) == slow_members
    return {"themes": len(pick), "copies_agree": copies_same, "support_agree": support_same,
            "members_agree": members_same,
            "identical": copies_same == len(pick) and support_same == len(pick)
            and members_same == len(pick)}


def invariants(side: dict[str, object], one: dict[str, object], two: dict[str, object],
               three: dict[str, object], four: dict[str, object]) -> dict[str, object]:
    """Checks over EVERY theme, not a sample, of things the four steps must satisfy.

    A singleton theme must inherit its one group's support exactly; every absorbed group's core
    must really reach ``J >= 0.9`` with its theme seed's core, which is what "compared with the
    seed only, no chaining" means; and the core must be a subset of the members, since 0.9 > 0.5.

    Args:
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        two: As :func:`step_two` returns.
        three: As :func:`step_three` returns.
        four: As :func:`step_four` returns.

    Returns:
        One count per invariant and whether all of them hold.
    """
    theme_of, seed_group = three["theme_of"], three["seed_group"]
    themes = len(seed_group)
    singles = np.flatnonzero(four["groups"] == 1)
    group_of_single = seed_group[singles]
    found_ok = int((four["found"][singles] == one["found"][group_of_single]).sum())
    judged_ok = int((four["judged"][singles] == one["eligible"][group_of_single]).sum())

    core_ptr, core_path = two["core_indptr"], two["core_pathway"]
    absorbed = np.flatnonzero(theme_of >= 0)
    absorbed = absorbed[absorbed != seed_group[theme_of[absorbed]]]
    merge_ok = 0
    for g in absorbed.tolist():
        seed = int(seed_group[theme_of[g]])
        a = set(core_path[core_ptr[g]:core_ptr[g + 1]].tolist())
        b = set(core_path[core_ptr[seed]:core_ptr[seed + 1]].tolist())
        inter = len(a & b)
        merge_ok += inter * 100 >= MERGE_J * 100 * (len(a) + len(b) - inter)

    subset_ok = 0
    for t in range(themes):
        core = set(four["core_pathway"][
            four["core_indptr"][t]:four["core_indptr"][t + 1]].tolist())
        members = set(four["member_pathway"][
            four["member_indptr"][t]:four["member_indptr"][t + 1]].tolist())
        subset_ok += core <= members
    claimed = int((theme_of >= 0).sum())
    return {
        "singleton_themes": int(len(singles)),
        "singleton_found_matches_group": found_ok,
        "singleton_judged_matches_group": judged_ok,
        "absorbed_groups": int(len(absorbed)),
        "absorbed_reach_J0.9_with_the_seed": merge_ok,
        "themes": themes,
        "core_subset_of_members": subset_ok,
        "cored_groups_placed": claimed,
        "cored_groups": int(two["has_core"].sum()),
        "identical": (found_ok == len(singles) and judged_ok == len(singles)
                      and merge_ok == len(absorbed) and subset_ok == themes
                      and claimed == int(two["has_core"].sum())),
    }


def write_side(out: Path, side: dict[str, object], one: dict[str, object],
               two: dict[str, object], three: dict[str, object],
               four: dict[str, object], checks: dict[str, object]) -> None:
    """Persist one side's four steps.

    Args:
        out: Directory to write.
        side: As :func:`load_side` returns.
        one: As :func:`step_one` returns.
        two: As :func:`step_two` returns.
        three: As :func:`step_three` returns.
        four: As :func:`step_four` returns.
        checks: The brute-force comparisons.
    """
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out / "groups.npz", seed_sizes=side["sizes"], eligible=one["eligible"],
        found=one["found"], support=one["support"], core_indptr=two["core_indptr"],
        core_pathway=two["core_pathway"], has_core=two["has_core"],
        theme_of=three["theme_of"], seed_group=three["seed_group"])
    np.savez_compressed(
        out / "themes.npz", support=four["support"], found=four["found"],
        judged=four["judged"], groups=four["groups"],
        core_indptr=four["core_indptr"], core_pathway=four["core_pathway"],
        member_indptr=four["member_indptr"], member_pathway=four["member_pathway"],
        incl_indptr=four["incl"]["indptr"], incl_pathway=four["incl"]["pathway"],
        incl_value=four["incl"]["inclusion"])
    (out / "steps.json").write_text(json.dumps({
        "theta": THETA, "core_cut": CORE_CUT, "member_cut": MEMBER_CUT, "merge_j": MERGE_J,
        "min_size": MIN_SIZE, "min_shared": MIN_SHARED, "seed": SEED,
        "seeds": int(len(side["sizes"])), "cored_groups": int(two["has_core"].sum()),
        "themes": int(len(three["seed_group"])), "core_pairs": int(three["pairs"]),
        "verification": checks,
    }, indent=1, default=float) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Build one side through steps 1-4, verifying each step against a brute-force loop.

    Args:
        argv: Command line.

    Returns:
        0, or 1 if any verification failed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1_2026-10-24/real"))
    parser.add_argument("--trees", type=Path, default=None,
                        help="override the cached real-tree directory, for a scramble side")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--cover", type=float, default=THETA,
                        help="kept for tree_cores.load_clusters; the match uses THETA on each side")
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args(argv)

    print(f"L1 STEPS 1-4  theta {THETA} on each side, core {CORE_CUT}, merge J {MERGE_J}, "
          f"members {MEMBER_CUT}", flush=True)
    side = load_side(args)
    one = step_one(side)
    two = step_two(side, one)
    three = step_three(side, one, two)
    four = step_four(side, one, two, three)

    checks: dict[str, object] = {}
    if not args.no_verify:
        clock = time.perf_counter()
        checks["step1"] = brute_step_one(side, one)
        checks["step2"] = brute_step_two(side, one, two)
        checks["step3"] = brute_step_three(side, two)
        checks["step4"] = brute_step_four(side, one, two, three, four)
        checks["invariants"] = invariants(side, one, two, three, four)
        print(f"  VERIFICATION against brute force, seed {SEED} "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
        for name in ("step1", "step2", "step3", "step4", "invariants"):
            got = checks[name]
            print(f"    {name}: {'IDENTICAL' if got['identical'] else 'MISMATCH'}  {got}",
                  flush=True)
    write_side(args.out, side, one, two, three, four, checks)
    print(f"  -> {args.out}", flush=True)
    bad = [k for k, v in checks.items() if not v["identical"]]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
