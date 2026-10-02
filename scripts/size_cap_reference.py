#!/usr/bin/env python3
"""How big is the largest category a curated ontology is willing to call one thing?

A size cap on our clusters needs a reference, and the only defensible one is what curators already
do: Reactome's top-level pathways and GO BP's level-1 branches are categories a human was prepared
to name, so their sizes bound what "too big to be one theme" can mean. This measures them over OUR
universe -- a Reactome root's size here is how many of our 10,770 fall under it, not how many
pathways Reactome has -- because a cap is applied to our clusters.

**Measurement only. No cap is applied and none is recommended here.**

A GO or Hallmark or BTM pathway counts toward a Reactome root only where a mapping exists
(`data/raw/reactome2go`); unmapped pathways are reported separately rather than silently dropped,
since a reference that quietly ignores 80% of the universe is not a reference.

Usage::

    uv run scripts/size_cap_reference.py
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import (
    go_ancestors,
    go_level1_branches,
    reactome_branches_of,
    reactome_roots,
    read_reactome_relation,
)
from thema.data.pathways import PathwayCollection
from thema.ontology.universe import load_embedded

csv.field_size_limit(1 << 30)

#: The GO generic slim, as published. Hard-coded rather than downloaded: it is a fixed list of 78
#: terms and adding a network dependency for 78 identifiers would be worse than writing them down.
#: Only the BP terms are used, since our GO members are BP.
GO_GENERIC_SLIM_BP = (
    "GO:0000003", "GO:0000278", "GO:0002376", "GO:0003013", "GO:0006091", "GO:0006259",
    "GO:0006397", "GO:0006399", "GO:0006412", "GO:0006457", "GO:0006461", "GO:0006464",
    "GO:0006605", "GO:0006629", "GO:0006790", "GO:0006913", "GO:0006914", "GO:0006950",
    "GO:0007005", "GO:0007009", "GO:0007010", "GO:0007049", "GO:0007059", "GO:0007155",
    "GO:0007165", "GO:0007267", "GO:0007275", "GO:0007399", "GO:0008219", "GO:0008283",
    "GO:0009056", "GO:0009058", "GO:0009790", "GO:0012501", "GO:0015979", "GO:0016071",
    "GO:0016192", "GO:0019748", "GO:0021700", "GO:0022607", "GO:0022618", "GO:0030154",
    "GO:0030198", "GO:0032196", "GO:0034330", "GO:0034641", "GO:0040007", "GO:0040011",
    "GO:0042254", "GO:0043473", "GO:0044281", "GO:0044403", "GO:0048646", "GO:0048856",
    "GO:0048870", "GO:0050877", "GO:0051186", "GO:0051276", "GO:0051301", "GO:0055085",
    "GO:0061024", "GO:0065003", "GO:0071554", "GO:0071941", "GO:0098754", "GO:0140014",
)


def reactome_sizes(
    collection: PathwayCollection, raw: Path, mapping: dict[str, set[str]]
) -> tuple[Counter, int, int]:
    """How many of our pathways fall under each Reactome top-level pathway.

    Args:
        collection: Our universe.
        raw: ``data/raw``.
        mapping: GO term to Reactome stable ids, from ``reactome2go``.

    Returns:
        Root stable id to count, the number of pathways attributed to no root, and how many of
        those are unmapped by construction (not Reactome and with no reactome2go entry).
    """
    lines = (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    parents = read_reactome_relation(lines)
    roots = reactome_roots(parents)
    counts: Counter = Counter()
    homeless = unmapped = 0
    for pathway in collection.pathways:
        ids: set[str] = set()
        if pathway.source == "reactome":
            ids.add(pathway.source_id)
        else:
            ids.update(mapping.get(pathway.source_id, ()))
        reached: set[str] = set()
        for stable in ids:
            reached |= set(reactome_branches_of(stable, parents, roots))
        if reached:
            for root in reached:
                counts[root] += 1
        else:
            homeless += 1
            if not ids:
                unmapped += 1
    return counts, homeless, unmapped


def go_sizes(
    collection: PathwayCollection, raw: Path, which: str
) -> tuple[Counter, dict[str, str], int]:
    """How many of our GO pathways fall under each level-1 branch, or each generic-slim term.

    Args:
        collection: Our universe.
        raw: ``data/raw``.
        which: ``level1`` or ``slim``.

    Returns:
        Term id to count, term id to name, and the number of GO pathways under no such term.
    """
    # splitlines(): parse_obo_terms takes LINES, and a bare string iterates characters,
    # which parsed 0 terms and reported every GO branch as empty.
    terms = parse_obo_terms((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines())
    targets = (
        set(go_level1_branches(terms)) if which == "level1"
        else {t for t in GO_GENERIC_SLIM_BP if t in terms}
    )
    names = {t: terms[t].name for t in targets if t in terms}
    counts: Counter = Counter()
    homeless = 0
    for pathway in collection.pathways:
        if pathway.source != "go":
            continue
        up = set(go_ancestors(pathway.source_id, terms)) | {pathway.source_id}
        hit = up & targets
        if hit:
            for term in hit:
                counts[term] += 1
        else:
            homeless += 1
    return counts, names, homeless


def frozen_sizes(directory: Path) -> list[int]:
    """Cluster sizes of the frozen 1,850 build, for the proportional comparison.

    Args:
        directory: The frozen build directory.

    Returns:
        Member counts, descending.
    """
    members: dict[str, int] = defaultdict(int)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]] += 1
    return sorted(members.values(), reverse=True)


def main(argv: list[str] | None = None) -> int:
    """Report the reference sizes.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--frozen", default="v0.2/recurrent_dag_c50")
    args = parser.parse_args(argv)
    raw = args.data / "raw"
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    # THE UNIVERSE IS THE 10,770 THAT WERE EMBEDDED, not the 10,817 rows of pathways.tsv. A cap is
    # applied to clusters of embedded pathways, so a reference counted over the wider table would
    # be measuring a universe the build never sees.
    # Through the verifying loader rather than the key file: a superseded or inconsistent artifact
    # must raise here as it would in a build. A test greps for direct reads, and it greps source
    # text, so naming the file even in a comment trips it -- deliberately blunt.
    keys = set(
        load_embedded(args.data / "ontology" / "v0.3", args.data / "pathways.tsv").keys
    )
    collection = PathwayCollection(
        tuple(p for p in collection.pathways if p.key in keys)
    )
    n = len(collection.pathways)
    by_source = Counter(p.source for p in collection.pathways)
    print(f"SIZE-CAP REFERENCE  over our {n:,} pathways: {dict(by_source)}\n")

    # reactome2go is one FILE, not a directory, and its lines read
    #   Reactome:R-HSA-1008248 > GO:<term name> ; GO:0046899
    # so the Reactome id is the first token and the GO id is the last.
    mapping: dict[str, set[str]] = defaultdict(set)
    r2g = raw / "reactome2go"
    if r2g.is_file():
        for line in r2g.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("!") or ">" not in line:
                continue
            left, _, right = line.partition(">")
            react = [t for t in left.replace("Reactome:", " ").split() if t.startswith("R-HSA-")]
            gos = [t.strip() for t in right.split(";") if t.strip().startswith("GO:")]
            gos = [g for g in gos if g[3:].isdigit()]
            for go in gos:
                mapping[go].update(react)
    print(f"  reactome2go: {len(mapping):,} GO terms mapped to a Reactome id")

    counts, homeless, unmapped = reactome_sizes(collection, raw, mapping)
    names = {}
    for line in (raw / "ReactomePathways.txt").read_text(encoding="utf-8").splitlines():
        cells = line.split("\t")
        if len(cells) >= 3 and cells[2].strip() == "Homo sapiens":
            names[cells[0]] = cells[1]
    print(f"\n  REACTOME TOP-LEVEL PATHWAYS: {len(counts)} with at least one of ours")
    print(f"  {'size':>6}  {'share':>6}  root")
    for root, size in counts.most_common(12):
        print(f"  {size:>6}  {size / n:>5.1%}  {names.get(root, root)}")
    largest_r = counts.most_common(1)[0] if counts else ("none", 0)
    print(f"  ... attributed to no root: {homeless:,} "
          f"(of which unmappable by construction: {unmapped:,})")
    print(f"  LARGEST: {names.get(largest_r[0], largest_r[0])} = {largest_r[1]:,} "
          f"({largest_r[1] / n:.1%} of the universe)")

    for which, label in (("level1", "GO BP LEVEL-1 BRANCHES"), ("slim", "GO GENERIC SLIM (BP)")):
        gc, gnames, gh = go_sizes(collection, raw, which)
        total_go = by_source.get("go", 0)
        print(f"\n  {label}: {len(gc)} with at least one of ours "
              f"(of {total_go:,} GO pathways; {gh:,} under none)")
        print(f"  {'size':>6}  {'share of GO':>11}  term")
        for term, size in gc.most_common(10):
            print(f"  {size:>6}  {size / max(total_go, 1):>10.1%}  "
                  f"{gnames.get(term, term)} ({term})")
        if gc:
            top = gc.most_common(1)[0]
            print(f"  LARGEST: {gnames.get(top[0], top[0])} = {top[1]:,}")

    cap = 2 * largest_r[1]
    print(f"\n  A CAP OF 2x THE REACTOME LARGEST = {cap:,} pathways "
          f"({cap / n:.1%} of the 10,770)")
    frozen = frozen_sizes(args.data / "ontology" / args.frozen)
    scaled = round(cap * 1850 / n)
    over = [s for s in frozen if s > scaled]
    print(f"  proportionally on the frozen 1,850 build that is {scaled:,} members")
    print(f"  clusters there exceeding it: {len(over)} of {len(frozen)} "
          f"-- sizes {over[:8]}{'...' if len(over) > 8 else ''}")
    print("  (information only; the frozen build is not changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
