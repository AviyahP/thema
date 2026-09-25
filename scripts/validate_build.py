"""Run the validation-plan tests that need no API spend, against their declared conditions.

Pass conditions live in ``docs/spec/validation-plan.md`` and are printed beside every result, so a
condition can never be quietly adjusted to fit an outcome. Tests 7 and 8 are **withdrawn** -- see
the 25 Sep amendment in that file; test 7's pass condition ("nothing survives") is unreachable
because the pipeline reads only text, and test 8 grades soft membership by gene overlap, which the
plan itself rejects as a quality measure.
"""

import argparse
import csv
from collections.abc import Sequence
from pathlib import Path

from thema.validation import seed_stability, shape

#: Full-ontology baselines for test 2, as the plan declares them. NOT induced over our subset,
#: which measured only how sparsely the collection samples GO.
BASELINES = {
    "GO BP (full)": {"nodes": 51986, "root_fraction": 0.20, "max_depth": 16,
                     "median_depth": 5, "multi_parent_fraction": 0.31},
    "Reactome (human)": {"nodes": 2883, "root_fraction": 0.01, "max_depth": 11,
                         "median_depth": 3, "multi_parent_fraction": 0.01},
}


def read_build(directory: Path) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Read a build's parents and sizes.

    Args:
        directory: A build directory holding ``nodes.tsv``.

    Returns:
        Node id to parent ids, and node id to member count.
    """
    rows = list(csv.DictReader((directory / "nodes.tsv").open(encoding="utf-8"), delimiter="\t"))
    parents = {r["node"]: [p for p in r["parents"].replace(",", " ").split() if p] for r in rows}
    sizes = {r["node"]: int(r["size"]) for r in rows}
    return parents, sizes


def theme_sets(directory: Path) -> list[frozenset[str]]:
    """Every theme's member keys.

    Args:
        directory: A build directory holding ``members.tsv``.

    Returns:
        One frozen set of pathway keys per node.
    """
    grouped: dict[str, set[str]] = {}
    for row in csv.DictReader((directory / "members.tsv").open(encoding="utf-8"), delimiter="\t"):
        grouped.setdefault(row["node"], set()).add(row["key"])
    return [frozenset(v) for v in grouped.values()]


def test_2(builds: dict[str, Path]) -> None:
    """Hierarchy shape against full GO BP and full Reactome. INFORMATIONAL."""
    print("\n=== TEST 2: hierarchy shape vs curated ontologies (INFORMATIONAL) ===")
    print(f"  {'':<30}{'nodes':>7}{'roots':>7}{'root%':>8}{'maxD':>6}{'medD':>6}"
          f"{'medBr':>7}{'multiP%':>9}{'sizeMed':>8}{'sizeMax':>8}")
    for label, directory in builds.items():
        parents, sizes = read_build(directory)
        got = shape(parents, sizes)
        print(f"  {label:<30}{got['nodes']:>7}{got['roots']:>7}{got['root_fraction']:>8.1%}"
              f"{got['max_depth']:>6}{got['median_depth']:>6.0f}{got['median_branching']:>7.0f}"
              f"{got['multi_parent_fraction']:>9.1%}{got['size_median']:>8.0f}"
              f"{got['size_max']:>8}")
    for label, base in BASELINES.items():
        print(f"  {label:<30}{base['nodes']:>7}{'':>7}{base['root_fraction']:>8.1%}"
              f"{base['max_depth']:>6}{base['median_depth']:>6}{'':>7}"
              f"{base['multi_parent_fraction']:>9.1%}")
    print("  DECLARED: no pass condition. A build whose roots exceed ~40% of nodes, or whose")
    print("  median depth is <= 1, is an outlier against both and that is said plainly.")
    print("  CAVEAT: GO and Reactome nodes ARE pathways, nesting by subsumption; THEMA's nodes")
    print("  are SETS of pathways, nesting by member containment. Not the same object.")


def test_9(pairs: dict[str, tuple[Path, Path]]) -> None:
    """Seed stability. INFORMATIONAL, but it governs the word "frozen"."""
    print("\n=== TEST 9: seed stability (INFORMATIONAL — governs the word \"frozen\") ===")
    for label, (first, second) in pairs.items():
        got = seed_stability(theme_sets(first), theme_sets(second))
        print(f"  {label}: {got['themes_first']} themes vs {got['themes_second']}")
        print(f"    mean best-match Jaccard   {got['mean_jaccard']:.3f}"
              f"   (reverse {got['mean_jaccard_reverse']:.3f})")
        print(f"    median                    {got['median_jaccard']:.3f}")
        print(f"    matching at >= 0.9        {got['matched_at_0.9']:.1%}")
        print(f"    matching at >= 0.7        {got['matched_at_0.7']:.1%}")
        print(f"    matching at >= 0.5        {got['matched_at_0.5']:.1%}")
        print(f"    member agreement          {got['member_agreement']:.3f}")
    print("  DECLARED: no pass condition, but a low theme-set Jaccard forbids the word")
    print("  \"frozen\". Settled 25 Sep: it applies to the theme set and its nesting, NOT to")
    print("  exact member lists. See DECISIONS.md.")


def main(argv: Sequence[str] | None = None) -> int:
    """Run tests 2 and 9 over the named builds."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.2")
    parser.add_argument("--builds", nargs="+",
                        default=["recurrent_dag_confirmatory", "recurrent_dag_consensus"])
    parser.add_argument("--seed-pair", nargs=2, metavar=("FIRST", "SECOND"),
                        help="two build directories differing only in master seed, for test 9")
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    test_2({name: root / name for name in args.builds})
    if args.seed_pair:
        first, second = (Path(p) for p in args.seed_pair)
        test_9({f"{first.name} vs {second.name}": (first, second)})
    else:
        print("\n  test 9 needs --seed-pair; see scripts/price_side.py for building one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
