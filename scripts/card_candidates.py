#!/usr/bin/env python3
"""Search the O50 build for example-card candidates. Reports; chooses nothing.

The landing page's two example cards no longer hold on O50 (the NF-kB four are in the build but
share no theme; the insulin three are curated summaries and were removed with the rest of them).
This searches for replacements against the criteria Aviyah set, writes the top fifteen of each, and
**changes no card** -- the choice is hers.

Card 1, "names that look unrelated"
    3 to 5 pathways from at least 2 databases whose gene lists do not connect them -- every pair
    below kappa 0.05, or sharing no gene at all -- that nevertheless all sit in one theme of 50
    members or fewer.

Card 2, "the same observation counted twice"
    Nested or heavily overlapping pathways inside one theme, reported with the gene figures the
    current card states: each member's gene count, what a pair shares, and what the larger one adds.

Both are ranked by the smallest theme first, then by the theme's support. Usage::

    uv run scripts/card_candidates.py
"""

from __future__ import annotations

import argparse
import csv
import itertools
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

#: Card 1's ceiling on theme size: a card has to point at a theme a reader can take in.
MAX_THEME = 50

#: Card 1's kappa ceiling. The current card states "below 0.04"; the search uses the looser 0.05
#: Aviyah set, and every candidate's worst pair is reported so she can apply either.
MAX_KAPPA = 0.05

#: Card 1's set size.
MIN_SET, MAX_SET = 3, 5

#: How many candidates to write per card.
TOP = 15

#: Card 2 calls a pair heavily overlapping at or above this containment of the smaller side.
HEAVY = 0.60

#: The criteria Aviyah set do not bound gene-set size, and the ranking she set -- smallest theme,
#: then support -- puts the smallest themes on top. Those are full of one-gene Reactome variant
#: pathways, where "every pair below kappa 0.05" is true because there is almost nothing to share
#: and "nested" is true because both sets are the same single gene. The primary lists are reported
#: exactly as specified; these floors drive a SECOND list per card where the gene figures mean
#: something, which is the comparison the current card actually makes (104/6/46/200 genes, and
#: 21 shared against 57 new).
CARD1_MIN_GENES = 5
CARD2_MIN_GENES = 10

#: Words too common in pathway names to count as a shared one.
STOP = frozenset({
    "of", "the", "and", "in", "to", "by", "for", "via", "with", "on", "from", "at", "a", "an",
    "regulation", "positive", "negative", "signaling", "signalling", "pathway", "process",
    "activity", "response", "cell", "protein", "hallmark",
})


def shared_words(names_of: Sequence[str]) -> int:
    """The largest number of content words any two of these names share.

    Card 1's point is that the NAMES look unrelated, which the structural criteria do not test at
    all. This is a crude proxy, reported so the sets whose names obviously do connect can be seen
    rather than discovered after one is chosen.

    Args:
        names_of: The member names.

    Returns:
        The maximum shared content-word count over all pairs, 0 if there is none.
    """
    bags = [
        {w for w in "".join(c.lower() if c.isalnum() else " " for c in name).split()
         if w not in STOP and len(w) > 2}
        for name in names_of
    ]
    return max(
        (len(a & b) for a, b in itertools.combinations(bags, 2)), default=0
    )


def kappa(a: frozenset[str], b: frozenset[str], universe: int) -> float:
    """Cohen's kappa for two gene sets over a universe of that many genes.

    Args:
        a: One gene set.
        b: The other.
        universe: Distinct genes across the collection.

    Returns:
        The agreement above chance, 0.0 when it is undefined.
    """
    both = len(a & b)
    neither = universe - len(a | b)
    observed = (both + neither) / universe
    expected = (
        (len(a) * len(b) + (universe - len(a)) * (universe - len(b))) / (universe * universe)
    )
    return 0.0 if expected >= 1.0 else (observed - expected) / (1 - expected)


def compatible_clique(
    members: Sequence[str],
    genes: Mapping[str, frozenset[str]],
    sources: Mapping[str, str],
    universe: int,
) -> list[str]:
    """The best card-1 set inside one theme, or an empty list.

    "Best" is the largest set up to :data:`MAX_SET` whose every pair is unconnected by genes, with
    source diversity broken in favour of more databases. The search is deterministic: members are
    considered in name order and extensions are tried in that order, so the same theme always yields
    the same set.

    Args:
        members: The theme's pathway keys.
        genes: Pathway key to its genes.
        sources: Pathway key to its database.
        universe: Distinct genes across the collection.

    Returns:
        The chosen keys, or ``[]`` if the theme has no qualifying set.
    """
    ok: dict[str, set[str]] = {key: set() for key in members}
    for left, right in itertools.combinations(members, 2):
        shared = genes[left] & genes[right]
        if not shared or kappa(genes[left], genes[right], universe) < MAX_KAPPA:
            ok[left].add(right)
            ok[right].add(left)
    best: list[str] = []
    for start in members:
        clique = [start]
        for candidate in members:
            if candidate == start or len(clique) >= MAX_SET:
                continue
            if all(candidate in ok[member] for member in clique):
                clique.append(candidate)
        if len(clique) < MIN_SET:
            continue
        key = (len({sources[k] for k in clique}), len(clique))
        if not best or key > (len({sources[k] for k in best}), len(best)):
            best = clique
    return best if len({sources[k] for k in best}) >= 2 else []


def overlapping_group(
    members: Sequence[str], genes: Mapping[str, frozenset[str]]
) -> list[str]:
    """The best card-2 group inside one theme: a nested pair, extended to a triple when one exists.

    Nesting is the strongest form of "the same observation counted twice", so a nested pair is
    preferred over a merely overlapping one, and a third member is added when it overlaps the pair
    heavily.

    Args:
        members: The theme's pathway keys.
        genes: Pathway key to its genes.

    Returns:
        2 or 3 keys, largest gene set first, or ``[]``.
    """
    with_genes = [key for key in members if genes[key]]
    nested: list[tuple[int, str, str]] = []
    heavy: list[tuple[float, str, str]] = []
    for left, right in itertools.combinations(with_genes, 2):
        a, b = genes[left], genes[right]
        inner, outer = (left, right) if len(a) <= len(b) else (right, left)
        small, big = genes[inner], genes[outer]
        if small <= big:
            nested.append((len(small), outer, inner))
        else:
            share = len(small & big) / len(small)
            if share >= HEAVY:
                heavy.append((share, outer, inner))
    if nested:
        _size, outer, inner = max(nested)
    elif heavy:
        _share, outer, inner = max(heavy)
    else:
        return []
    group = [outer, inner]
    third, best = "", 0.0
    for key in with_genes:
        if key in group:
            continue
        small = min((genes[key], genes[inner]), key=len)
        share = len(genes[key] & genes[inner]) / max(len(small), 1)
        if share > best and share >= HEAVY:
            third, best = key, share
    if third:
        group.append(third)
    return sorted(group, key=lambda k: -len(genes[k]))


def main(argv: list[str] | None = None) -> int:
    """Write the candidate list."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path,
                        default=Path("data/ontology/frozen/working-O50-2026-10-14"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path,
                        default=Path("docs/status/2026-10-15-card-candidates.md"))
    parser.add_argument("--names", type=Path, default=Path(
        "data/experiments/naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.tsv"))
    args = parser.parse_args(argv)

    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    key_of = {f"{r['source']}:{r['source_id']}": r for r in rows}
    genes = {
        key: frozenset(r["genes"].split(";")) if r["genes"] not in ("", "-") else frozenset()
        for key, r in key_of.items()
    }
    names = {key: r["name"] for key, r in key_of.items()}
    sources = {key: r["source"] for key, r in key_of.items()}
    universe = len(set().union(*genes.values()))

    members: dict[str, list[str]] = defaultdict(list)
    with (args.build / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    support: dict[str, float] = {}
    with (args.build / "nodes.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row["node"]] = float(row["support"])
    theme_name: dict[str, str] = {}
    if args.names.is_file():
        with args.names.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                theme_name[row["theme_id"]] = row["name"]

    print(f"O50: {len(members):,} themes, {len(key_of):,} pathways, {universe:,} genes")
    small = {node: sorted(keys, key=lambda k: names[k].lower())
             for node, keys in members.items() if len(keys) <= MAX_THEME}
    print(f"  themes of {MAX_THEME} members or fewer: {len(small):,}")

    card1 = []
    for node, keys in small.items():
        chosen = compatible_clique(keys, genes, sources, universe)
        if chosen:
            worst = max(kappa(genes[a], genes[b], universe)
                        for a, b in itertools.combinations(chosen, 2))
            nogene = sum(1 for a, b in itertools.combinations(chosen, 2)
                         if not (genes[a] & genes[b]))
            card1.append((len(keys), -support[node], node, chosen, worst, nogene))
    card1.sort()
    card1_rich = [row for row in card1
                  if min(len(genes[k]) for k in row[3]) >= CARD1_MIN_GENES]
    print(f"  CARD 1 candidates: {len(card1):,} themes qualify; "
          f"{len(card1_rich):,} with every member at {CARD1_MIN_GENES}+ genes")

    card2 = []
    for node, keys in members.items():
        group = overlapping_group(sorted(keys, key=lambda k: names[k].lower()), genes)
        if group:
            card2.append((len(keys), -support[node], node, group))
    card2.sort()
    card2_rich = [row for row in card2
                  if min(len(genes[k]) for k in row[3]) >= CARD2_MIN_GENES]
    print(f"  CARD 2 candidates: {len(card2):,} themes qualify; "
          f"{len(card2_rich):,} with every member at {CARD2_MIN_GENES}+ genes")

    lines: list[str] = []
    lines.append("# Example-card candidates on O50. 15 Oct 2026\n")
    lines.append(
        "**A search, not a choice. No card was changed.** The page's two examples no longer hold "
        "on O50: the four NF-kB pathways are all in the build but no single theme contains all "
        "four, and the three insulin-secretion pathways are curated summaries, which universe L "
        "removes, so they are absent entirely. These are the candidates for replacements, ranked "
        "as Aviyah specified -- smallest theme first, then by the theme's support. **Aviyah "
        "picks.**\n")
    lines.append(f"Searched: `{args.build}`, {len(members):,} themes over {len(key_of):,} "
                 f"pathways, {universe:,} distinct genes. Theme names are naming-c1-lite and are "
                 "shown only to make the rows readable.\n")

    lines.append("## Card 1 — names that look unrelated\n")
    lines.append(
        f"Criteria: 3 to 5 pathways, at least 2 databases, **every pair below kappa "
        f"{MAX_KAPPA}** or sharing no gene at all, and **all members in one theme of "
        f"{MAX_THEME} members or fewer**. {len(card1):,} themes qualify; the top {TOP} follow. "
        "The current card states \"below kappa 0.04\" and \"two of them share no gene at all\", so "
        "the worst pair and the no-shared-gene count are given for each.\n")
    def write_card1(rows: list, label: str) -> None:
        lines.append(f"### {label}\n")
        for rank, (size, negsup, node, chosen, worst, nogene) in enumerate(rows[:TOP], 1):
            lines.append(f"#### {rank}. `{node}` — theme of **{size}** members, support "
                         f"**{-negsup:.3f}**")
            if theme_name.get(node):
                lines.append(f"*{theme_name[node]}*\n")
            lines.append(
                f"{len(chosen)} pathways from {len({sources[k] for k in chosen})} databases; "
                f"worst pairwise kappa **{worst:.4f}**; pairs sharing no gene: **{nogene}** of "
                f"{len(chosen) * (len(chosen) - 1) // 2}; smallest gene set "
                f"**{min(len(genes[k]) for k in chosen)}**; most content words shared by any pair "
                f"**{shared_words([names[k] for k in chosen])}**\n")
            lines.append("| pathway | source | genes |")
            lines.append("|---|---|---:|")
            for key in chosen:
                lines.append(f"| {names[key]} | {sources[key]} | {len(genes[key])} |")
            lines.append("")
            lines.append("| pair | kappa | shared genes |")
            lines.append("|---|---:|---:|")
            for a, b in itertools.combinations(chosen, 2):
                pair_kappa = kappa(genes[a], genes[b], universe)
                lines.append(f"| {names[a][:38]} / {names[b][:38]} | {pair_kappa:.4f} | "
                             f"{len(genes[a] & genes[b])} |")
            lines.append("")

    def write_card2(rows: list, label: str) -> None:
        lines.append(f"### {label}\n")
        for rank, (size, negsup, node, group) in enumerate(rows[:TOP], 1):
            lines.append(f"#### {rank}. `{node}` — theme of **{size}** members, support "
                         f"**{-negsup:.3f}**")
            if theme_name.get(node):
                lines.append(f"*{theme_name[node]}*\n")
            lines.append("| pathway | source | genes |")
            lines.append("|---|---|---:|")
            for key in group:
                lines.append(f"| {names[key]} | {sources[key]} | {len(genes[key])} |")
            lines.append("")
            lines.append("| pair | relation | shared | larger adds |")
            lines.append("|---|---|---:|---:|")
            for a, b in itertools.combinations(group, 2):
                big, small = (a, b) if len(genes[a]) >= len(genes[b]) else (b, a)
                relation = ("nested: every gene of the smaller is in the larger"
                            if genes[small] <= genes[big]
                            else f"{len(genes[small] & genes[big]) / len(genes[small]):.0%} of the "
                                 "smaller is inside the larger")
                lines.append(f"| {names[big][:34]} / {names[small][:34]} | {relation} | "
                             f"{len(genes[big] & genes[small])} | "
                             f"{len(genes[big] - genes[small])} |")
            lines.append("")

    write_card1(card1, f"A. As ranked: smallest theme, then support (top {TOP} of "
                       f"{len(card1):,})")
    lines.append(
        f"**The ranking as specified puts degenerate sets on top.** The smallest themes are full "
        f"of one-gene Reactome variant pathways, where \"every pair below kappa {MAX_KAPPA}\" "
        f"holds because there is almost nothing to share, and where the names often do connect "
        f"(`n00290`'s three members are all Wnt). The structural criteria do not test whether the "
        f"names look unrelated, which is the card's whole point. The same ranking with every "
        f"member at **{CARD1_MIN_GENES}+ genes** follows, so the kappa figure means something; "
        f"the \"content words shared\" column is a crude proxy for how unrelated the names "
        f"look, and lower is better.\n")
    write_card1(card1_rich, f"B. The same, every member at {CARD1_MIN_GENES}+ genes (top {TOP} of "
                            f"{len(card1_rich):,})")
    for rank, (size, negsup, node, chosen, worst, nogene) in enumerate([], 1):
        lines.append(f"### {rank}. `{node}` — theme of **{size}** members, support "
                     f"**{-negsup:.3f}**")
        if theme_name.get(node):
            lines.append(f"*{theme_name[node]}*\n")
        lines.append(f"{len(chosen)} pathways from "
                     f"{len({sources[k] for k in chosen})} databases; worst pairwise kappa "
                     f"**{worst:.4f}**; pairs sharing no gene at all: **{nogene}** of "
                     f"{len(chosen) * (len(chosen) - 1) // 2}\n")
        lines.append("| pathway | source | genes |")
        lines.append("|---|---|---:|")
        for key in chosen:
            lines.append(f"| {names[key]} | {sources[key]} | {len(genes[key])} |")
        lines.append("")
        lines.append("| pair | kappa | shared genes |")
        lines.append("|---|---:|---:|")
        for a, b in itertools.combinations(chosen, 2):
            pair_kappa = kappa(genes[a], genes[b], universe)
            lines.append(f"| {names[a][:38]} / {names[b][:38]} | {pair_kappa:.4f} | "
                         f"{len(genes[a] & genes[b])} |")
        lines.append("")

    lines.append("## Card 2 — the same observation counted twice\n")
    lines.append(
        f"Criteria: nested or heavily overlapping pathways (the smaller at least {HEAVY:.0%} "
        f"inside the larger) within one theme, reported with the gene figures the current card "
        f"states -- each member's gene count, what a pair shares, and what the larger one adds. "
        f"{len(card2):,} themes qualify; the top {TOP} follow. \"Nested\" means every gene of the "
        "smaller is in the larger, which is the relation the current card asserts.\n")
    write_card2(card2, f"A. As ranked: smallest theme, then support (top {TOP} of "
                       f"{len(card2):,})")
    lines.append(
        f"**Same caveat.** The top of that list is triples of one-gene pathways that are nested "
        f"because both sets are the same single gene, which cannot carry the current card's "
        f"figures (21 shared against 57 new). The same ranking with every member at "
        f"**{CARD2_MIN_GENES}+ genes** follows.\n")
    write_card2(card2_rich, f"B. The same, every member at {CARD2_MIN_GENES}+ genes (top {TOP} of "
                            f"{len(card2_rich):,})")
    for rank, (size, negsup, node, group) in enumerate([], 1):
        lines.append(f"### {rank}. `{node}` — theme of **{size}** members, support "
                     f"**{-negsup:.3f}**")
        if theme_name.get(node):
            lines.append(f"*{theme_name[node]}*\n")
        lines.append("| pathway | source | genes |")
        lines.append("|---|---|---:|")
        for key in group:
            lines.append(f"| {names[key]} | {sources[key]} | {len(genes[key])} |")
        lines.append("")
        lines.append("| pair | relation | shared | larger adds |")
        lines.append("|---|---|---:|---:|")
        for a, b in itertools.combinations(group, 2):
            big, small = (a, b) if len(genes[a]) >= len(genes[b]) else (b, a)
            relation = ("nested: every gene of the smaller is in the larger"
                        if genes[small] <= genes[big]
                        else f"{len(genes[small] & genes[big]) / len(genes[small]):.0%} of the "
                             "smaller is inside the larger")
            lines.append(f"| {names[big][:34]} / {names[small][:34]} | {relation} | "
                         f"{len(genes[big] & genes[small])} | {len(genes[big] - genes[small])} |")
        lines.append("")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> {args.out}  (top {TOP} of each)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
