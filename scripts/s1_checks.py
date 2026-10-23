"""Two report-only checks before prompt 53's sections C-G. 22 Oct 2026.

Nothing is built and nothing is adopted.

**Check 1, section D of prompt 53.** Of the 76 well-supported parents O50s's consensus superseded,
how many survive in each restructured arm, how many O50s roots they contain, and which themes
superseded them.

**Check 2, inheritance.** Consensus does not only drop themes: under its INHERITED rule a kept theme
absorbs members from a newcomer. Those members were never in the kept theme's own candidate set, so
any DAG edge that depends on them is an edge consensus manufactured. (a) measures that in O50s;
(b) asks the converse of S1p, where no inheritance happens at all: are its small roots genuinely
separate, or one or two pathways short of being contained?

The parents' member sets are regenerated from the cached side material, because prompt 52's
``potential_parents.tsv`` records the themes and roots each parent contains but **not** its member
keys -- a gap against that prompt's spec, noted here rather than papered over.

Usage:
    uv run scripts/s1_checks.py
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))


def read_members(directory: Path, index: dict[str, int], width: int
                 ) -> tuple[list[str], np.ndarray, dict[str, tuple[str, ...]]]:
    """Node ids, packed memberships and immediate parents for one build.

    Args:
        directory: A build directory.
        index: Pathway key to universe position.
        width: Bitset width in bits.

    Returns:
        ``(ids, stack, parents)``.
    """
    from thema.ontology import bitset as bits

    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    ids = [row["node"] for row in rows]
    parents = {row["node"]: tuple(p for p in (row["parents"] or "").split() if p)
               for row in rows}
    held: dict[str, list[int]] = defaultdict(list)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            held[row["node"]].append(index[row["key"]])
    stack = np.vstack([bits.pack(sorted(held[node]), width)[None, :] for node in ids])
    return ids, stack, parents


def best_jaccard(one: np.ndarray, stack: np.ndarray) -> tuple[float, int]:
    """Highest Jaccard between a bitset and any row of a stack.

    Args:
        one: A bitset.
        stack: ``(m, words)`` bitsets.

    Returns:
        ``(best jaccard, row)``.
    """
    inter = np.bitwise_count(one[None, :] & stack).sum(axis=1).astype(np.int64)
    union = np.bitwise_count(one[None, :] | stack).sum(axis=1).astype(np.int64)
    jaccard = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    row = int(jaccard.argmax())
    return float(jaccard[row]), row


def main(argv: list[str] | None = None) -> int:
    """Run both checks and print the two tables.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--s1p", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S1p"))
    parser.add_argument("--s1s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S1s"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22"))
    args = parser.parse_args(argv)

    from thema.ontology import bitset as bits
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD

    with np.load(args.out / "probe.npz", allow_pickle=False) as probe:
        got = {k: probe[k] for k in probe.files}
    with np.load(args.out / "side.npz", allow_pickle=False) as side:
        completed_keys = side["completed_keys"].tolist()
        completed_blocks = side["completed_blocks"]
    with np.load(args.space_root / "calibration" / "real.npz") as handle:
        row_blocks = handle["blocks"]

    at_grouping = {g: i for i, g in enumerate(completed_keys)}
    o_ids, o_stack, o_parents = read_members(args.o50s, index, width)
    p_ids, p_stack, p_parents = read_members(args.s1p, index, width)
    s_ids, s_stack, s_parents = read_members(args.s1s, index, width)
    o_size = np.bitwise_count(o_stack).sum(axis=1).astype(np.int64)
    p_size = np.bitwise_count(p_stack).sum(axis=1).astype(np.int64)

    # post-consensus row -> final O50s node, following the repair drops
    drops = {int(v): int(k) for v, k in zip(got["collapse_victim"], got["collapse_keeper"],
                                            strict=True)}
    drops.update({int(d): int(k) for d, k in zip(got["merge_dropped"], got["merge_kept"],
                                                 strict=True)})
    survivors = [i for i in range(len(got["consensus_members"])) if i not in drops]
    final_row = {row: i for i, row in enumerate(survivors)}

    def survivor_of(position: int) -> int:
        """Follow a post-consensus row to the row that finally survives."""
        while position in drops:
            position = drops[position]
        return position

    acc_pos = {int(g): p for p, g in enumerate(got["accepted"])}

    print("TWO CHECKS BEFORE C-G. Report only; nothing built, nothing adopted.")
    print()
    print("=" * 104)
    print("CHECK 1 (prompt 53 section D): the 76 parents consensus superseded")
    print("=" * 104)
    rows = [r for r in csv.DictReader((args.out / "potential_parents.tsv").open(encoding="utf-8"),
                                      delimiter="\t")
            if r["stage"] == "consensus" and r["unit"] == "grouping"]
    print(f"  {len(rows)} parents, regenerated from the cached side material")
    print("  (prompt 52's potential_parents.tsv records the themes and roots each contains but")
    print("   NOT its member keys, which that prompt's spec asked for; noted, not papered over)")
    print()

    survive_p = survive_s = 0
    roots_p: set[str] = set()
    roots_s: set[str] = set()
    all_roots: set[str] = set()
    detail: list[dict] = []
    for row in rows:
        block = completed_blocks[at_grouping[int(row["id"])]]
        jp, rp = best_jaccard(block, p_stack)
        js, rs = best_jaccard(block, s_stack)
        mine = set(row["root_nodes"].split())
        all_roots |= mine
        if jp >= 0.9:
            survive_p += 1
            roots_p |= mine
        if js >= 0.9:
            survive_s += 1
            roots_s |= mine
        detail.append({"id": row["id"], "size": int(row["size"]), "runs": int(row["runs"]),
                       "support": float(row["support"]), "n_roots": int(row["n_roots"]),
                       "best_o50s": float(row["best_j"]), "best_s1p": jp, "best_s1s": js,
                       "reason": row["reason"]})

    print(f"  {'':<40}{'O50s':>16}{'S1p':>16}{'S1s':>16}")
    print(f"  {'parents present at J >= 0.9':<40}{'0 (by definition)':>16}"
          f"{survive_p:>16}{survive_s:>16}")
    print(f"  {'share of the 76':<40}{'-':>16}{f'{survive_p / len(rows):.1%}':>16}"
          f"{f'{survive_s / len(rows):.1%}':>16}")
    print(f"  {'O50s roots those parents contain':<40}{'-':>16}{len(roots_p):>16}"
          f"{len(roots_s):>16}")
    print(f"  {'of the 74 roots the 76 cover':<40}{len(all_roots):>16}"
          f"{f'{len(roots_p) / len(all_roots):.1%}' if all_roots else '-':>16}"
          f"{f'{len(roots_s) / len(all_roots):.1%}' if all_roots else '-':>16}")
    print()
    best_p = np.array([d["best_s1p"] for d in detail])
    best_s = np.array([d["best_s1s"] for d in detail])
    buckets = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0001)]
    print("  best Jaccard to anything in the arm, distribution over the 76")
    print("  " + f"{'arm':<8}" + "".join(f"{f'{a:.1f}-{b:.1f}':>12}" for a, b in buckets)
          + f"{'median':>10}{'max':>8}")
    for name, arr in (("O50s", np.array([d["best_o50s"] for d in detail])),
                      ("S1p", best_p), ("S1s", best_s)):
        line = f"  {name:<8}" + "".join(
            f"{int(((arr >= a) & (arr < b)).sum()):>12,}" for a, b in buckets)
        print(line + f"{np.median(arr):>10.3f}{arr.max():>8.3f}")
    print()

    print("  the themes that superseded them in O50s")
    tally = Counter(int(re.search(r"gated (\d+)", d["reason"]).group(1)) for d in detail)
    print(f"  {len(tally)} DISTINCT superseding candidates, not two: the two largest account for "
          f"{tally.most_common(2)[0][1] + tally.most_common(2)[1][1]} of {len(rows)}")
    print(f"  {'gated':>8}{'O50s node':>12}{'size':>9}{'giant':>8}{'parents taken':>15}"
          f"{'support':>10}")
    for gated, count in tally.most_common():
        position = acc_pos.get(gated)
        if position is None:
            print(f"  {gated:>8}{'(dropped)':>12}{'-':>9}{'-':>8}{count:>15}{'-':>10}")
            continue
        node_row = final_row[survivor_of(position)]
        size = int(o_size[node_row])
        print(f"  {gated:>8}{o_ids[node_row]:>12}{size:>9,}{'YES' if size > 1280 else 'no':>8}"
              f"{count:>15}{float(got['consensus_supports'][position]):>10.4f}")
    print()

    print("=" * 104)
    print("CHECK 2a: what consensus's INHERITED rule added in O50s, and which edges rest on it")
    print("=" * 104)
    keep = got["keep"]
    accepted = got["accepted"]
    consensus_members = got["consensus_members"]
    # Each final node came from one accepted candidate. Its ORIGINAL set is that candidate's gated
    # block; its FINAL set is what consensus left it with. The difference is purely inheritance,
    # because neither repair sub-pass changes a membership.
    original = np.vstack([row_blocks[int(keep[int(accepted[survivors[i]])])][None, :]
                          for i in range(len(survivors))])
    final = np.vstack([consensus_members[survivors[i]][None, :] for i in range(len(survivors))])
    added = np.bitwise_count(final & ~original).sum(axis=1).astype(np.int64)
    lost = int(np.bitwise_count(original & ~final).sum())
    grew = int((added > 0).sum())
    print(f"  members inherited into kept themes:       {int(added.sum()):,}")
    print(f"  themes that grew:                         {grew:,} of {len(survivors):,} "
          f"= {grew / len(survivors):.1%}")
    print(f"  members a kept theme LOST (must be 0):    {lost:,}")
    print(f"  inherited members per grown theme:        median "
          f"{float(np.median(added[added > 0])) if grew else 0:.0f}, "
          f"max {int(added.max()):,}")
    biggest = np.argsort(-added)[:8]
    print("  the eight that grew most: " + ", ".join(
        f"{o_ids[i]} +{int(added[i])} (to {int(o_size[i]):,})" for i in biggest))
    print()

    with (args.o50s / "edges.tsv").open(encoding="utf-8") as handle:
        edges = [(row["child"], row["parent"]) for row in csv.DictReader(handle, delimiter="\t")]
    at_node = {node: i for i, node in enumerate(o_ids)}
    only_inherited = 0
    by_band: Counter = Counter()
    for child, parent in edges:
        c, pa = at_node[child], at_node[parent]
        if int(np.bitwise_count(final[c] & ~original[pa]).sum()):
            only_inherited += 1
            size = int(o_size[pa])
            band = ("3-9" if size <= 9 else "10-19" if size <= 19 else "20-49" if size <= 49
                    else "50-199" if size <= 199 else "200+")
            by_band[band] += 1
    print(f"  O50s edges: {len(edges):,}")
    print(f"  edges that EXIST ONLY because of the parent's inherited members: "
          f"{only_inherited:,} = {only_inherited / len(edges):.1%}")
    print("  by the parent's size band: " + ", ".join(
        f"{b} {by_band[b]:,}" for b in ("3-9", "10-19", "20-49", "50-199", "200+")
        if by_band[b]))
    print()

    print("=" * 104)
    print("CHECK 2b: S1p roots of 50 or fewer -- how close are they to being contained?")
    print("=" * 104)
    small = [i for i in range(len(p_ids)) if not p_parents[p_ids[i]] and p_size[i] <= 50]
    print(f"  S1p roots of 50 or fewer: {len(small):,}")
    gaps: list[int] = []
    for i in small:
        bigger = np.flatnonzero(p_size > p_size[i])
        if not len(bigger):
            gaps.append(10 ** 9)
            continue
        miss = np.bitwise_count(p_stack[i][None, :] & ~p_stack[bigger]).sum(axis=1)
        gaps.append(int(miss.min()))
    gaps_arr = np.array(gaps)
    print(f"  {'pathways short of containment':<34}{'roots':>10}{'share':>10}")
    for label, mask in (("exactly 1", gaps_arr == 1),
                        ("2 to 3", (gaps_arr >= 2) & (gaps_arr <= 3)),
                        ("4 to 10", (gaps_arr >= 4) & (gaps_arr <= 10)),
                        ("11 or more", gaps_arr >= 11)):
        n = int(mask.sum())
        print(f"  {label:<34}{n:>10,}{n / len(small):>10.1%}")
    near = int(((gaps_arr >= 1) & (gaps_arr <= 3)).sum())
    print(f"  {'1 to 3 (near misses)':<34}{near:>10,}{near / len(small):>10.1%}")
    print(f"  median gap {float(np.median(gaps_arr)):.0f}, "
          f"min {int(gaps_arr.min())}, max {int(gaps_arr[gaps_arr < 10**9].max())}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
