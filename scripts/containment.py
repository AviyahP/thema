"""Measure what gene-overlap similarity does to Reactome's own parent-child edges.

Not siblings -- the hierarchy edges themselves, the relationships Reactome asserts most directly.
A parent contains its children, so the archetypal curated relation in this data is CONTAINMENT: a
small specific pathway wholly inside a large general one.

The point is a property of the formula rather than of this dataset, and the output says so.
Jaccard divides the shared genes by the UNION, so a 10-gene pathway wholly contained in a
500-gene parent scores 10/500 = 0.02 -- statistically indistinguishable from two unrelated
pathways that happen to share ten genes. The overlap coefficient divides by the SMALLER set, so
the same pair scores 1.0. Jaccard is therefore blind by arithmetic to the exact relationship the
dendrograms of the classic tools claim to display, and the measured distribution below says how
often that blindness bites here.

This costs nothing to run: no model, no clustering, no API.
"""

import argparse
import statistics
import sys
from pathlib import Path

from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import Pathway, PathwayCollection
from thema.data.tables import SUMMARY_COLUMNS, print_table, write_tsv

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"
DEFAULT_RAW = REPO_ROOT / "data" / "raw"

#: Below this, a pair is in the band where gene-overlap clustering has effectively no signal.
BLIND_THRESHOLD = 0.05


def measures(a: Pathway, b: Pathway) -> tuple[float, float] | None:
    """Jaccard and overlap coefficient for one edge.

    Args:
        a: One pathway.
        b: The other.

    Returns:
        ``(jaccard, overlap)``, or None when either set is empty and both are undefined.
    """
    if not a.genes or not b.genes:
        return None
    shared = len(a.genes & b.genes)
    return shared / len(a.genes | b.genes), shared / min(len(a.genes), len(b.genes))


def spread(values: list[float]) -> tuple[float, float, float, float, float]:
    """Min, q1, median, q3 and max of a sample."""
    ordered = sorted(values)
    q1, _median, q3 = statistics.quantiles(ordered, n=4)
    return ordered[0], q1, statistics.median(ordered), q3, ordered[-1]


def main(argv: list[str] | None = None) -> int:
    """Report the containment figure."""
    parser = argparse.ArgumentParser(prog="containment.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw data directory")
    args = parser.parse_args(argv)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    relation = read_reactome_relation(
        (args.raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )

    edges = [
        (f"reactome:{parent}", f"reactome:{child}")
        for child, parents in relation.items()
        for parent in parents
    ]
    usable, undefined = [], 0
    for parent, child in edges:
        if parent not in by_key or child not in by_key:
            continue
        found = measures(by_key[parent], by_key[child])
        if found is None:
            undefined += 1
            continue
        usable.append((parent, child, *found))
    if not usable:
        print("no usable parent-child edges", file=sys.stderr)
        return 1

    jac = [j for _p, _c, j, _o in usable]
    ovl = [o for _p, _c, _j, o in usable]
    print("\nCONTAINMENT ON REACTOME PARENT-CHILD EDGES\n")
    print(f"  edges with both members in the collection : {len(usable):,}")
    print(f"  edges dropped (a member has no genes)     : {undefined:,}\n")
    print_table(
        ("measure", "min", "q1", "median", "q3", "max", f"< {BLIND_THRESHOLD:g}"),
        [
            (
                "Jaccard  shared/union",
                *(f"{v:.3f}" for v in spread(jac)),
                f"{sum(1 for v in jac if v < BLIND_THRESHOLD)}/{len(jac)} "
                f"({sum(1 for v in jac if v < BLIND_THRESHOLD) / len(jac):.0%})",
            ),
            (
                "overlap  shared/min",
                *(f"{v:.3f}" for v in spread(ovl)),
                f"{sum(1 for v in ovl if v < BLIND_THRESHOLD)}/{len(ovl)} "
                f"({sum(1 for v in ovl if v < BLIND_THRESHOLD) / len(ovl):.0%})",
            ),
        ],
        align="<>>>>>>",
    )

    print(
        "\nWHAT THIS IS A PROPERTY OF\n"
        "  Jaccard divides shared genes by the UNION. A small pathway wholly contained in a large\n"
        "  one therefore scores near zero -- the SAME score as two unrelated pathways sharing a\n"
        "  few genes. But containment IS the parent-child relation: it is the most direct\n"
        "  relationship a curator asserts in this data. The overlap coefficient divides by the\n"
        "  SMALLER set and scores that same pair at or near 1.\n"
        "\n"
        "  So a Jaccard-based method is blind BY ARITHMETIC to the relationship the\n"
        "  dendrograms of the classic tools claim to display. This is not a tuning failure\n"
        "  and no threshold fixes it. The distribution above says how often it bites here.\n"
    )

    rows = [
        ("input", "edges", str(len(usable)), "Reactome parent-child, both members present"),
        ("input", "dropped", str(undefined), "a member resolved to no genes"),
    ]
    for name, values in (("jaccard", jac), ("overlap_coefficient", ovl)):
        low, q1, median, q3, high = spread(values)
        rows.append(
            (
                name,
                "min_q1_median_q3_max",
                "/".join(f"{v:.4f}" for v in (low, q1, median, q3, high)),
                "",
            )
        )
        below = sum(1 for v in values if v < BLIND_THRESHOLD)
        rows.append(
            (
                name,
                f"below_{BLIND_THRESHOLD:g}",
                f"{below}/{len(values)}",
                f"{below / len(values):.1%}",
            )
        )
    out = args.data / "ontology" / "containment.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_tsv(out, SUMMARY_COLUMNS, rows)
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
