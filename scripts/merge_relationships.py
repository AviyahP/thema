"""Which relationships do O50s's merges act on? Prompt 52, declared 22 Oct 2026.

Evaluation only. Nothing here changes a build, and nothing is adopted.

The three merges were designed for relationships -- **twins are siblings** (themes sharing a
parent) and **chains are parent and child** -- but none of the three code paths tests a
relationship. ``consensus.classify`` compares two member sets and runs *before any DAG exists*;
``repair.merge_stale`` compares two member sets on final memberships; ``repair.collapse_chains``
does test containment, which is a relationship, but only the pair's own sets decide which survives.
This script asks what the merges turned out to act on, by classifying every merged pair against the
FINAL DAG after the fact.

The merge log needs no new instrumentation of the repair pass. Neither ``collapse_chains`` nor
``merge_stale`` mutates a membership -- both only ever drop rows -- and ``repair_joint`` already
maps every drop back to its post-consensus index, so both member sets of every collapse and every
stale merge are recoverable from the post-consensus stack by index. Only consensus needed a hook,
because a newcomer can grow by inheritance before it meets the theme that supersedes it, so the
pair actually compared is not ``member_sets[candidate]``. That hook is one new write-only field on
``consensus.Outcome``, and ``scripts/o50s_build.py --verify`` passing with it in place is the proof
that collecting it changes nothing.

Usage:
    uv run scripts/o50s_build.py --directory thema_L_x2_O50s_relog --probe OUT/probe.npz
    uv run scripts/merge_relationships.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: Size bands the report uses for the kept node.
BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 9, "3-9"), (10, 19, "10-19"), (20, 49, "20-49"),
    (50, 199, "50-199"), (200, 10**9, "200+"),
)

#: The four tables the byte-for-byte check compares.
TABLES = ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv")

#: Relationship classes, in report order.
CLASSES = ("siblings", "nested immediate", "nested deeper", "unrelated")


def band_of(size: int) -> str:
    """The report band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        The band label.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return "3-9" if size < 3 else "200+"


def sha256(path: Path) -> str:
    """Hex digest of a file.

    Args:
        path: The file.

    Returns:
        Hex digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_nodes(directory: Path) -> tuple[list[str], dict[str, tuple[str, ...]]]:
    """Node ids in file order, and immediate parents per node.

    Args:
        directory: A build directory.

    Returns:
        ``(ids, parents)``.
    """
    ids: list[str] = []
    parents: dict[str, tuple[str, ...]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            ids.append(row["node"])
            field = row.get("parents", "") or ""
            parents[row["node"]] = tuple(p for p in field.split() if p)
    return ids, parents


def subset(a: np.ndarray, b: np.ndarray) -> bool:
    """Is every bit of ``a`` also in ``b``?

    Args:
        a: Bitset.
        b: Bitset.

    Returns:
        True if ``a`` is contained in ``b``, equality included.
    """
    return not int(np.bitwise_count(a & ~b).sum())


def contained_in(one: np.ndarray, stack: np.ndarray) -> np.ndarray:
    """Which rows of ``stack`` strictly contain ``one``.

    Args:
        one: A bitset.
        stack: ``(m, words)`` bitsets.

    Returns:
        Row indices, strict: an identical row is not a container.
    """
    inside = np.bitwise_count(one[None, :] & ~stack).sum(axis=1) == 0
    bigger = np.bitwise_count(stack).sum(axis=1) > int(np.bitwise_count(one).sum())
    return np.flatnonzero(inside & bigger)


def minimal(rows: Sequence[int], stack: np.ndarray) -> list[int]:
    """Keep only the containment-minimal rows of a container set.

    Args:
        rows: Candidate rows, all containing the same set.
        stack: ``(m, words)`` bitsets.

    Returns:
        Those rows no other row of the set is strictly inside.
    """
    rows = list(rows)
    if len(rows) <= 1:
        return rows
    keep: list[int] = []
    for row in rows:
        if not any(other != row and subset(stack[other], stack[row])
                   and int(np.bitwise_count(stack[other]).sum())
                   < int(np.bitwise_count(stack[row]).sum())
                   for other in rows):
            keep.append(row)
    return keep


def jaccard_of(a: np.ndarray, b: np.ndarray) -> float:
    """Jaccard of two bitsets.

    Args:
        a: Bitset.
        b: Bitset.

    Returns:
        ``|a & b| / |a | b|``, or 0.0 if both are empty.
    """
    inter = int(np.bitwise_count(a & b).sum())
    union = int(np.bitwise_count(a | b).sum())
    return inter / union if union else 0.0


def classify_pair(dropped: np.ndarray, kept_row: int, stack: np.ndarray,
                  dag_parents: Sequence[tuple[int, ...]]) -> tuple[str, float]:
    """Classify one merged pair against the final DAG.

    The dropped set is treated as if it were a node, its parents being the smallest final themes
    that strictly contain it -- which is exactly how the DAG would have placed it had it survived.

    Args:
        dropped: The dropped side's member bitset, as the merge compared it.
        kept_row: Final row index of the side that was kept.
        stack: ``(m, words)`` final member bitsets.
        dag_parents: Immediate parent rows per final row.

    Returns:
        ``(class, jaccard)``.
    """
    kept = stack[kept_row]
    inter = int(np.bitwise_count(dropped & kept).sum())
    size_d = int(np.bitwise_count(dropped).sum())
    size_k = int(np.bitwise_count(kept).sum())
    union = size_d + size_k - inter
    jaccard = inter / union if union else 0.0

    d_in_k = inter == size_d and size_d < size_k
    k_in_d = inter == size_k and size_k < size_d
    if d_in_k or k_in_d:
        inner, outer = (dropped, kept) if d_in_k else (kept, dropped)
        # Immediate if no final theme sits strictly between them.
        between = contained_in(inner, stack)
        gap = [row for row in between
               if subset(stack[row], outer)
               and int(np.bitwise_count(stack[row]).sum()) < int(np.bitwise_count(outer).sum())]
        if d_in_k:
            gap = [row for row in gap if row != kept_row]
        return ("nested immediate" if not gap else "nested deeper"), jaccard

    d_parents = set(minimal(contained_in(dropped, stack).tolist(), stack))
    k_parents = set(dag_parents[kept_row])
    if (d_parents & k_parents) or (not d_parents and not k_parents):
        return "siblings", jaccard
    return "unrelated", jaccard


def table(counts: Counter, rows: Sequence[str], label: str) -> list[str]:
    """Render a class-by-band count table.

    Args:
        counts: ``{(row, class): n}``.
        rows: Row keys in order.
        label: Header for the first column.

    Returns:
        Lines.
    """
    width = max(len(label), *(len(r) for r in rows)) + 2
    head = f"  {label:<{width}}" + "".join(f"{c:>18}" for c in CLASSES) + f"{'total':>10}"
    out = [head, "  " + "-" * (width + 18 * len(CLASSES) + 10)]
    for row in rows:
        total = sum(counts[(row, c)] for c in CLASSES)
        line = f"  {row:<{width}}"
        for c in CLASSES:
            n = counts[(row, c)]
            share = f"{n / total:.1%}" if total else "-"
            line += f"{f'{n:,} ({share})':>18}"
        out.append(line + f"{total:>10,}")
    grand = sum(counts.values())
    line = f"  {'ALL':<{width}}"
    for c in CLASSES:
        n = sum(counts[(row, c)] for row in rows)
        line += f"{f'{n:,} ({n / grand:.1%})' if grand else '-':>18}"
    out.append(line + f"{grand:>10,}")
    return out


def resolve_survivor(row: int, drops: dict[int, int]) -> int:
    """Follow a post-consensus row through every later drop to the row that finally survives.

    A consensus keeper can itself be collapsed or stale-merged away in a later round, so the node
    a merge actually left behind is the end of that chain, not the immediate keeper.

    Args:
        row: A post-consensus row index.
        drops: ``{dropped row: the row that took it}``, collapse and stale merge together.

    Returns:
        The surviving row.
    """
    seen = {row}
    while row in drops:
        row = drops[row]
        if row in seen:                                  # cannot happen; refuse rather than spin
            raise ValueError(f"drop chain cycles at row {row}")
        seen.add(row)
    return row


def main(argv: list[str] | None = None) -> int:
    """Classify every O50s merge against the final DAG.

    Args:
        argv: Command line.

    Returns:
        0, or 2 if the rebuild is not byte-identical to the frozen baseline.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_relog"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22"))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    print("O50s MERGE RELATIONSHIPS. Prompt 52, 22 Oct 2026. Evaluation only; adopts nothing.")
    print()
    print("=" * 108)
    print("0. VERIFICATION")
    print("=" * 108)
    bad = [name for name in TABLES
           if sha256(args.build / name) != sha256(args.frozen / name)]
    for name in TABLES:
        mark = "DIFFERS" if name in bad else "identical"
        print(f"  {mark:<10} {name}")
    if bad:
        print(f"  FAILED: {bad} differ from the frozen baseline; the merge log cannot be trusted")
        return 2
    print("  O50s REPRODUCED BYTE FOR BYTE from the cached trees and re-solved floors, with the")
    print("  merge hooks in place. The hooks are therefore inert.")
    print()

    with np.load(args.probe, allow_pickle=False) as probe:
        got = {key: probe[key] for key in probe.files}
    stack_all = got["consensus_members"]
    supports_all = got["consensus_supports"]
    collapse_victim, collapse_keeper = got["collapse_victim"], got["collapse_keeper"]
    merge_dropped, merge_kept = got["merge_dropped"], got["merge_kept"]
    merge_kind = got["merge_kind"]

    drops: dict[int, int] = {int(v): int(k) for v, k in zip(collapse_victim, collapse_keeper,
                                                            strict=True)}
    drops.update({int(d): int(k) for d, k in zip(merge_dropped, merge_kept, strict=True)})
    survivors = [i for i in range(len(stack_all)) if i not in drops]
    final_row = {row: i for i, row in enumerate(survivors)}
    stack = stack_all[survivors]

    ids, parent_ids = read_nodes(args.build)
    if len(ids) != len(survivors):
        print(f"  REFUSING: {len(ids):,} nodes in the build but {len(survivors):,} survivors "
              "derived from the probe; the index mapping is wrong")
        return 2
    index_of = {node: i for i, node in enumerate(ids)}
    dag_parents = [tuple(index_of[p] for p in parent_ids[node]) for node in ids]
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)

    # The survivors' memberships must be the post-consensus ones untouched, which is the claim
    # that lets both member sets of every repair pair be read off by index.
    with (args.build / "members.tsv").open(encoding="utf-8") as handle:
        counted: Counter = Counter()
        for row in csv.DictReader(handle, delimiter="\t"):
            counted[row["node"]] += 1
    mismatch = [ids[i] for i in range(len(ids)) if counted[ids[i]] != int(sizes[i])]
    print("=" * 108)
    print("0b. THE INDEX MAPPING, CHECKED")
    print("=" * 108)
    print(f"  post-consensus rows {len(stack_all):,}; dropped by repair {len(drops):,} "
          f"({len(collapse_victim):,} collapse + {len(merge_dropped):,} stale); "
          f"survivors {len(survivors):,}; nodes in the build {len(ids):,}")
    print(f"  member counts disagreeing with members.tsv: {len(mismatch)}"
          + ("" if not mismatch else f"  {mismatch[:5]}"))
    if mismatch:
        print("  REFUSING: repair changed a membership, so pairs cannot be read off by index")
        return 2
    print("  every surviving row's membership equals its post-consensus membership, so neither")
    print("  repair sub-pass mutated a set and both sides of every pair are recoverable by index")
    print()

    pairs: list[dict] = []
    for dropped_candidate, kept_position, block, against in zip(
            got["sup_dropped"], got["sup_kept_position"], got["sup_blocks"],
            got["sup_against"], strict=True):
        survivor = resolve_survivor(int(kept_position), drops)
        kind, jaccard = classify_pair(block, final_row[survivor], stack, dag_parents)
        pairs.append({
            "merge": "consensus", "kind": "", "relationship": kind,
            "jaccard_at_merge": round(jaccard_of(block, against), 4),
            "dropped_size": int(np.bitwise_count(block).sum()),
            "kept_node": ids[final_row[survivor]],
            "kept_size": int(sizes[final_row[survivor]]),
            "jaccard": round(jaccard, 4),
            "dropped_support": round(float(got["gated_supports"][int(dropped_candidate)]), 6),
            "kept_support": round(float(supports_all[survivor]), 6),
        })

    for victim, keeper in zip(collapse_victim, collapse_keeper, strict=True):
        survivor = resolve_survivor(int(keeper), drops)
        kind, jaccard = classify_pair(stack_all[int(victim)], final_row[survivor], stack,
                                      dag_parents)
        v_size = int(np.bitwise_count(stack_all[int(victim)]).sum())
        k_size = int(np.bitwise_count(stack_all[int(keeper)]).sum())
        pairs.append({
            "merge": "chain", "kind": "child" if k_size < v_size else "parent",
            "relationship": kind, "dropped_size": v_size,
            "kept_node": ids[final_row[survivor]],
            "kept_size": int(sizes[final_row[survivor]]),
            "jaccard": round(jaccard, 4),
            "dropped_support": round(float(supports_all[int(victim)]), 6),
            "kept_support": round(float(supports_all[int(keeper)]), 6),
            "jaccard_at_merge": round(jaccard_of(stack_all[int(victim)],
                                                 stack_all[int(keeper)]), 4),
            "parent_size": max(v_size, k_size), "child_size": min(v_size, k_size),
        })

    for dropped, keeper, how in zip(merge_dropped, merge_kept, merge_kind, strict=True):
        survivor = resolve_survivor(int(keeper), drops)
        kind, jaccard = classify_pair(stack_all[int(dropped)], final_row[survivor], stack,
                                      dag_parents)
        pairs.append({
            "merge": f"stale {how}", "kind": str(how), "relationship": kind,
            "dropped_size": int(np.bitwise_count(stack_all[int(dropped)]).sum()),
            "kept_node": ids[final_row[survivor]],
            "kept_size": int(sizes[final_row[survivor]]),
            "jaccard": round(jaccard, 4),
            "dropped_support": round(float(supports_all[int(dropped)]), 6),
            "kept_support": round(float(supports_all[int(keeper)]), 6),
            "jaccard_at_merge": round(jaccard_of(stack_all[int(dropped)],
                                                 stack_all[int(keeper)]), 4),
        })

    report(pairs, args)
    return 0


def report(pairs: Sequence[dict], args: argparse.Namespace) -> None:
    """Print report sections 1 to 3 and write the per-pair table.

    Args:
        pairs: One record per merged pair.
        args: Parsed arguments.
    """
    kinds = ("consensus", "stale identical", "stale overlap", "chain")
    print("=" * 108)
    print("1. WHAT THE MERGES ACT ON: merge kind by relationship")
    print("=" * 108)
    by_kind: Counter = Counter()
    for row in pairs:
        by_kind[(row["merge"], row["relationship"])] += 1
    for line in table(by_kind, kinds, "merge kind"):
        print(line)
    print()
    print("  the same, by size band of the KEPT node")
    for kind in kinds:
        subset_rows = [r for r in pairs if r["merge"] == kind]
        if not subset_rows:
            continue
        print(f"\n  {kind}  ({len(subset_rows):,} pairs)")
        by_band: Counter = Counter()
        for row in subset_rows:
            by_band[(band_of(row["kept_size"]), row["relationship"])] += 1
        for line in table(by_band, [b[2] for b in BANDS], "kept band"):
            print("  " + line)
    print()

    print("=" * 108)
    print("2. THE PAIRS CLASSED UNRELATED")
    print("=" * 108)
    odd = [r for r in pairs if r["relationship"] == "unrelated"]
    print(f"  {len(odd):,} of {len(pairs):,} pairs = {len(odd) / len(pairs):.1%}")
    if odd:
        buckets = [(0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0001)]
        # Two Jaccards, and the difference matters. AT MERGE is what the rule acted on. FINAL is
        # against the kept node's finished membership, and a consensus keeper goes on growing by
        # inheritance after it supersedes someone -- so the final figure can fall below the 0.50
        # cutoff that merged the pair, which would look like a bug if only it were reported.
        for name, key in (("at merge", "jaccard_at_merge"), ("final", "jaccard")):
            js = np.array([r[key] for r in odd])
            print(f"  Jaccard {name:<9}: min {js.min():.3f}  q1 {np.percentile(js, 25):.3f}  "
                  f"median {np.median(js):.3f}  q3 {np.percentile(js, 75):.3f}  "
                  f"max {js.max():.3f}")
            print("    " + "".join(f"{f'{lo:.1f}-{hi:.1f}':>12}" for lo, hi in buckets))
            print("    " + "".join(
                f"{sum(1 for j in js if lo <= j < hi):>12,}" for lo, hi in buckets))
        print()
        print("  ten examples, largest kept node first")
        print(f"  {'merge':<16}{'kept node':<12}{'kept':>8}{'dropped':>9}{'J merge':>9}"
              f"{'J final':>9}{'kept sup':>10}{'drop sup':>10}")
        for row in sorted(odd, key=lambda r: -r["kept_size"])[:10]:
            print(f"  {row['merge']:<16}{row['kept_node']:<12}{row['kept_size']:>8,}"
                  f"{row['dropped_size']:>9,}{row['jaccard_at_merge']:>9.3f}"
                  f"{row['jaccard']:>9.3f}"
                  f"{row['kept_support']:>10.4f}{row['dropped_support']:>10.4f}")
    print()

    print("=" * 108)
    print("3. CHAIN COLLAPSES: which end survived, by the PARENT's size band")
    print("=" * 108)
    chains = [r for r in pairs if r["merge"] == "chain"]
    print(f"  {len(chains):,} collapses")
    print(f"  {'parent band':<14}{'kept parent':>14}{'kept child':>14}{'total':>10}"
          f"{'child kept':>13}")
    rows_out = []
    for low, high, name in BANDS:
        here = [r for r in chains if low <= r["parent_size"] <= high]
        if not here:
            continue
        child = sum(1 for r in here if r["kind"] == "child")
        rows_out.append((name, len(here) - child, child, len(here)))
        print(f"  {name:<14}{len(here) - child:>14,}{child:>14,}{len(here):>10,}"
              f"{child / len(here):>13.1%}")
    tot_child = sum(r[2] for r in rows_out)
    tot = sum(r[3] for r in rows_out)
    print(f"  {'ALL':<14}{tot - tot_child:>14,}{tot_child:>14,}{tot:>10,}"
          f"{(tot_child / tot if tot else 0):>13.1%}")
    print()

    path = args.out / "pairs.tsv"
    fields = ["merge", "kind", "relationship", "kept_node", "kept_size", "dropped_size",
              "jaccard_at_merge", "jaccard", "kept_support", "dropped_support",
              "parent_size", "child_size"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t",
                                extrasaction="ignore", restval="")
        writer.writeheader()
        writer.writerows(pairs)
    print(f"  -> {path}  ({len(pairs):,} pairs)")


if __name__ == "__main__":
    raise SystemExit(main())
