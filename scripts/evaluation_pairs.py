"""Measure how many curator-declared related pairs each source actually supplies, and how good.

THEMA's headline structural claim is low-overlap recovery, and it can only be as strong as the
supply of pairs curators call related that share few genes. reactome2go alone gives three such
pairs at smoke scale, which is not a test set. This counts every source already on disk so the
claim rests on measured supply rather than on one file.

Sources are never pooled. They differ in evidential strength and a combined number would hide that:
reactome2go is cross-database, while sibling pairs come from the same curators who wrote the prose
being embedded, which makes sibling recovery partly "the text encodes the tree" rather than a
discovery. The output labels every source with its strength and its caveat.
"""

import argparse
import collections
from pathlib import Path

from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.data.tables import print_table
from thema.evaluation import (
    BANDS,
    PairSource,
    band_label,
    band_of,
    collision_pairs,
    go_parents,
    jaccard,
    reactome2go_pairs,
    restrict,
    shares_name,
    sibling_pairs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"
DEFAULT_RAW = REPO_ROOT / "data" / "raw"

#: The band below which the low-overlap claim has no support worth quoting.
LOW_BANDS = (BANDS[0], BANDS[1])


def read_descriptions(table: Path) -> dict[str, str]:
    """Read the generated descriptions out of the committed table.

    Args:
        table: Path to ``pathway_descriptions.tsv``.

    Returns:
        Pathway key to its generated description.
    """
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    key, text = header.index("key"), header.index("description_generated")
    return {row[key]: row[text] for row in (line.split("\t") for line in lines[1:] if line)}


def profile(source: PairSource, by_key: dict) -> tuple[dict, int, int]:
    """Band a source's pairs and count how many are also name collisions.

    Args:
        source: The pair source, already restricted to what is present.
        by_key: Pathways by key.

    Returns:
        Band counts, how many pairs have an undefined Jaccard, and how many share a name.
    """
    bands: dict[tuple[float, float], int] = collections.Counter()
    undefined = 0
    named = 0
    for a, b in source.pairs:
        pa, pb = by_key[a], by_key[b]
        named += shares_name(pa, pb)
        value = jaccard(pa, pb)
        if value is None:
            undefined += 1
            continue
        bands[band_of(value)] += 1
    return bands, undefined, named


def main(argv: list[str] | None = None) -> int:
    """Report evaluation-pair supply."""
    parser = argparse.ArgumentParser(
        prog="evaluation_pairs.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw data directory")
    parser.add_argument("--examples", type=int, default=10, help="pairs to print per source")
    args = parser.parse_args(argv)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    described = sorted(set(read_descriptions(args.data / "pathway_descriptions.tsv")) & set(by_key))

    relation = read_reactome_relation(
        (args.raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    with (args.raw / "go-basic.obo").open("r", encoding="utf-8") as handle:
        terms = parse_obo_terms(handle, namespace="biological_process")

    sources = [
        collision_pairs(collection),
        reactome2go_pairs((args.raw / "reactome2go").read_text(encoding="utf-8").splitlines()),
        sibling_pairs(
            relation,
            "reactome:",
            "reactome-siblings",
            "same curators wrote the hierarchy AND the summations THEMA embeds, so recovery is "
            "partly 'the text encodes the tree'",
        ),
        sibling_pairs(
            go_parents(terms),
            "go:",
            "go-siblings",
            "same caveat as Reactome siblings, and a parent with many heterogeneous children "
            "manufactures pairs that are not really related",
        ),
    ]

    scopes = {
        "smoke 1,854": described,
        "full 10,817": sorted(by_key),
    }
    for scope, keys in scopes.items():
        print(f"\n{'=' * 92}\nPAIR SUPPLY -- {scope}\n{'=' * 92}\n")
        rows = []
        for source in sources:
            here = restrict(source, keys)
            bands, undefined, named = profile(here, by_key)
            low = sum(bands[b] for b in LOW_BANDS)
            rows.append(
                (
                    here.name,
                    here.strength,
                    f"{len(here.pairs):,}",
                    *(f"{bands[b]:,}" for b in reversed(BANDS)),
                    f"{undefined:,}",
                    f"{low:,}",
                    f"{named:,}",
                )
            )
        print_table(
            (
                "source",
                "strength",
                "pairs",
                *(band_label(*b) for b in reversed(BANDS)),
                "undef",
                "J<=0.01",
                "same name",
            ),
            rows,
            align="<<" + ">" * 9,
        )

    print("\n" + "=" * 92)
    print(f"LOWEST NON-EMPTY BAND, {args.examples} PAIRS PER SOURCE (smoke set)")
    print("=" * 92)
    for source in sources:
        here = restrict(source, described)
        by_band: dict[tuple[float, float], list] = collections.defaultdict(list)
        for a, b in here.pairs:
            value = jaccard(by_key[a], by_key[b])
            if value is not None:
                by_band[band_of(value)].append((a, b, value))
        lowest = next((b for b in BANDS if by_band[b]), None)
        print(f"\n-- {here.name}  [{here.strength}]")
        print(f"   caveat: {here.caveat}")
        if lowest is None:
            print("   no pairs with a defined Jaccard")
            continue
        picked = sorted(by_band[lowest], key=lambda x: x[2])[: args.examples]
        print(f"   lowest non-empty band: {band_label(*lowest)}  (n={len(by_band[lowest])})\n")
        for a, b, value in picked:
            mark = "  [also a name collision]" if shares_name(by_key[a], by_key[b]) else ""
            print(f"     J={value:.4f}  {by_key[a].name}")
            print(f"               <-> {by_key[b].name}{mark}")

    print(
        "\nSTRENGTH, STATED RATHER THAN IMPLIED\n"
        "  reactome2go is cross-database and is the only strong structural source here.\n"
        "  Sibling pairs are WEAKER: Reactome's curators wrote both the hierarchy and the\n"
        "  summations THEMA embeds, so sibling recovery is partly 'the text encodes the tree'\n"
        "  rather than a discovery, and the same holds for GO. Siblings are supplementary and\n"
        "  must never carry the headline. Collision pairs test redundancy, not structure, and\n"
        "  are circular for any arm that sees the pathway name."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
