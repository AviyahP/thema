"""Compare THEMA's ontology against the baselines a reader will ask about, on identical inputs.

Four arms over the same pathways, the same cuts, and -- for three of the four -- the same linkage,
so that what differs between arms is one thing at a time:

  A  thema         embeddings of ``description_generated``, L2-normalised, Ward
  B  gene overlap  binary gene-presence vectors, L2-normalised, Ward
  C  name only     embeddings of the pathway name alone, no description, Ward
  D  gene overlap  the same vectors as B, average linkage

A vs B isolates the REPRESENTATION: same algorithm, same normalization, same cuts, different
description of what a pathway is. A vs C asks what the generated prose buys over the name it was
written from -- if the answer is "little", the prose is not worth what it costs. D is separate
because average linkage over gene overlap is what the field actually does (``docs/eval-plan.md``
section 2), and a reader will ask for it even though this project's own measurements reject that
linkage.

B is binary presence L2-normalised rather than a Jaccard distance matrix, deliberately. Cosine
between L2-normalised binary set vectors is the Ochiai coefficient, a close kin of Jaccard, and it
is genuinely Euclidean -- which is what Ward's variance criterion requires and what a Jaccard matrix
cannot promise. Feeding Ward a non-Euclidean matrix fails silently rather than loudly.

The headline is the cross-source name-collision test: pathways that different databases give the
same name are the redundancy THEMA exists to collapse, and whether an arm puts them together is a
question with an answer. The stratification by gene-set Jaccard is the part that separates the
methods rather than the part that flatters them, and it carries two caveats the output states
rather than buries.
"""

import argparse
import random
import statistics
import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import adjusted_rand_score

from thema.data.pathways import Pathway, PathwayCollection, collision_groups
from thema.data.tables import SUMMARY_COLUMNS, print_table, write_tsv
from thema.embed import embed, l2_normalize
from thema.normalize import display_name

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"
BASELINE_SUMMARY = "ontology/baseline_comparison.tsv"

#: The cuts every arm is compared at.
CUTS = (25, 50, 100)

#: Gene-set Jaccard bands for the stratified report. The first is exact zero -- pairs sharing no
#: gene at all -- because that is the band where gene-overlap clustering cannot succeed by
#: construction, and it deserves to be visible rather than averaged into a neighbouring bin.
BANDS = ((0.0, 0.0), (0.0, 0.01), (0.01, 0.05), (0.05, 0.15), (0.15, 1.01))

#: How many random pairs estimate the chance co-clustering rate.
BASELINE_DRAWS = 200_000


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


def gene_vectors(pathways: list[Pathway]) -> np.ndarray:
    """Build L2-normalised binary gene-presence vectors.

    Args:
        pathways: The pathways, in the order the rest of the comparison uses.

    Returns:
        A ``(n, genes)`` float32 array of unit vectors. A pathway with no genes stays all-zero;
        :func:`~thema.embed.l2_normalize` leaves it alone rather than producing NaN, and it simply
        sits at distance sqrt(2) from everything.
    """
    genes = sorted({g for p in pathways for g in p.genes})
    index = {g: i for i, g in enumerate(genes)}
    matrix = np.zeros((len(pathways), len(genes)), dtype=np.float32)
    for row, pathway in enumerate(pathways):
        for gene in pathway.genes:
            matrix[row, index[gene]] = 1.0
    return l2_normalize(matrix)


def condensed_from_unit(vectors: np.ndarray) -> np.ndarray:
    """Condensed Euclidean distances for unit vectors, via the Gram matrix.

    ``pdist`` is O(n^2 * d) and the gene-presence vectors are ~14,000-dimensional, which makes the
    direct route slow enough to matter. For unit vectors ||a-b||^2 = 2 - 2*(a.b), so one BLAS matrix
    multiply gives every distance at once.

    Args:
        vectors: A ``(n, dim)`` array of unit vectors.

    Returns:
        The condensed distance matrix.
    """
    gram = np.clip(vectors @ vectors.T, -1.0, 1.0)
    square = np.sqrt(np.maximum(2.0 - 2.0 * gram, 0.0))
    np.fill_diagonal(square, 0.0)
    return squareform(square, checks=False)


def labels_for(vectors: np.ndarray, method: str, cuts: tuple[int, ...]) -> dict[int, np.ndarray]:
    """Cluster one arm and cut it at each depth.

    Args:
        vectors: Unit vectors for this arm.
        method: The linkage.
        cuts: The depths.

    Returns:
        Cut size to a label per observation.
    """
    tree = linkage(condensed_from_unit(vectors), method=method)
    return {k: fcluster(tree, t=k, criterion="maxclust") for k in cuts}


def jaccard(a: Pathway, b: Pathway) -> float | None:
    """Gene-set Jaccard, or None when either set is empty and the ratio is undefined."""
    if not a.genes or not b.genes:
        return None
    return len(a.genes & b.genes) / len(a.genes | b.genes)


def main(argv: list[str] | None = None) -> int:
    """Run the baseline comparison."""
    parser = argparse.ArgumentParser(
        prog="compare_baselines.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    args = parser.parse_args(argv)

    pathways_table = args.data / PATHWAY_TABLE
    descriptions = args.data / DESCRIPTIONS_TABLE
    for path in (pathways_table, descriptions):
        if not path.is_file():
            print(f"missing input: {path}", file=sys.stderr)
            return 1

    collection = PathwayCollection.from_tsv_text(pathways_table.read_text(encoding="utf-8"))
    by_key = collection.by_key
    texts = {k: v for k, v in read_descriptions(descriptions).items() if k in by_key and v.strip()}
    keys = sorted(texts)
    pathways = [by_key[k] for k in keys]
    position = {k: i for i, k in enumerate(keys)}
    print(f"\nBASELINE COMPARISON  ({len(keys):,} pathways, cuts {'/'.join(map(str, CUTS))})\n")

    print("embedding descriptions (arm A)", file=sys.stderr)
    thema = embed([texts[k] for k in keys])
    print("embedding names only (arm C)", file=sys.stderr)
    names = embed([display_name(p) for p in pathways])
    print("building gene-presence vectors (arms B and D)", file=sys.stderr)
    genes = gene_vectors(pathways)

    arms = {
        "A thema": labels_for(thema, "ward", CUTS),
        "B gene-overlap": labels_for(genes, "ward", CUTS),
        "C name-only": labels_for(names, "ward", CUTS),
        "D gene-overlap avg": labels_for(genes, "average", CUTS),
    }

    groups = {
        n: m for n, m in collision_groups(collection).items() if all(p.key in position for p in m)
    }
    print(f"cross-source name-collision groups usable here: {len(groups)}\n")

    rng = random.Random(0)
    rows: list[tuple[str, ...]] = []
    for name, cuts in arms.items():
        for k in CUTS:
            labels = cuts[k]
            together = sum(
                1
                for members in groups.values()
                if len({labels[position[p.key]] for p in members}) == 1
            )
            chance = (
                sum(
                    1
                    for _ in range(BASELINE_DRAWS)
                    if labels[rng.randrange(len(keys))] == labels[rng.randrange(len(keys))]
                )
                / BASELINE_DRAWS
            )
            rows.append(
                (
                    name,
                    str(k),
                    f"{together}/{len(groups)}",
                    f"{together / len(groups):.1%}",
                    f"{chance:.2%}",
                    f"{(together / len(groups)) / chance:.0f}x",
                )
            )
    print("COLLISION-PAIR CO-CLUSTERING\n")
    print_table(("arm", "k", "together", "rate", "chance", "lift"), rows, align="<>>>>>")

    # ---- stratification by gene-set Jaccard
    banded: dict[tuple[float, float], list[tuple[str, ...]]] = {b: [] for b in BANDS}
    undefined = 0
    for name, members in groups.items():
        pairs = [
            jaccard(a, b)
            for i, a in enumerate(members)
            for b in members[i + 1 :]
            if a.source != b.source
        ]
        usable = [j for j in pairs if j is not None]
        if not usable:
            undefined += 1
            continue
        value = statistics.mean(usable)
        for low, high in BANDS:
            if (low == high == 0.0 and value == 0.0) or (low < value <= high and high > 0):
                banded[(low, high)].append((name, members))
                break

    print("\nGENE-SET JACCARD ACROSS THE COLLISION GROUPS\n")
    dist = [
        (
            "exactly 0" if low == high == 0.0 else f"{low:g} < J <= {min(high, 1.0):g}",
            str(len(banded[(low, high)])),
            f"{len(banded[(low, high)]) / max(len(groups), 1):.0%}",
        )
        for low, high in BANDS
    ]
    dist.append(("undefined (a member has no genes)", str(undefined), ""))
    print_table(("band", "groups", "share"), dist, align="<>>")

    print("\nCO-CLUSTERING BY OVERLAP BAND (k=50)\n")
    strat_rows: list[tuple[str, ...]] = []
    for low, high in BANDS:
        members_in_band = banded[(low, high)]
        label = "exactly 0" if low == high == 0.0 else f"{low:g} < J <= {min(high, 1.0):g}"
        if not members_in_band:
            strat_rows.append((label, "0", *["-"] * len(arms)))
            continue
        cells = []
        for arm in arms:
            labels = arms[arm][50]
            hit = sum(
                1 for _name, m in members_in_band if len({labels[position[p.key]] for p in m}) == 1
            )
            cells.append(
                f"{hit}/{len(members_in_band)}"
                if len(members_in_band) < 10
                else f"{hit / len(members_in_band):.0%}"
            )
        strat_rows.append((label, str(len(members_in_band)), *cells))
    print_table(("band", "n", *arms), strat_rows, align="<>" + ">" * len(arms))

    # The collision test selects its positives BY NAME IDENTITY, and arm C embeds only the name.
    # C is therefore guaranteed to score near-perfectly on it by construction, and its result there
    # measures the metric rather than the method. Partition agreement is the fair A-vs-C comparison:
    # it asks whether the two arms build the same tree, using no name-defined ground truth at all.
    print("\nPARTITION AGREEMENT BETWEEN ARMS (adjusted Rand, k=50)\n")
    names_list = list(arms)
    agree_rows = [
        (
            a,
            *[
                "-" if a == b else f"{adjusted_rand_score(arms[a][50], arms[b][50]):.3f}"
                for b in names_list
            ],
        )
        for a in names_list
    ]
    print_table(("arm", *names_list), agree_rows, align="<" + ">" * len(names_list))
    print(
        "\n  A vs C is the number that answers 'what did the descriptions buy?'. The collision\n"
        "  test cannot answer it: its pairs are DEFINED by having the same name, and arm C embeds\n"
        "  the name, so C scores near-perfectly there by construction rather than by merit."
    )

    print("\nTWO CAVEATS, STATED RATHER THAN BURIED\n")
    for line in (
        "1. Gene-overlap clustering CANNOT group a pair sharing no genes. In the zero",
        "   band its failure is structural, not a tuning fault, so a THEMA win there is",
        "   expected rather than surprising. What is informative is the SIZE of the gap",
        "   and how fast it opens as overlap falls -- not the win itself.",
        "2. THEMA's descriptions were written with the gene lists in view (DECISIONS,",
        "   2026-08-29), so its embeddings partly re-encode gene overlap. That confound",
        "   is strongest in the HIGH band and weakest in the LOW band -- which is the",
        "   band the product claim rests on.",
    ):
        print(line)

    summary = [("input", "pathways", str(len(keys)), "same set in every arm")]
    summary += [
        ("input", "collision_groups", str(len(groups)), "cross-source, both members present")
    ]
    summary += [
        (f"arm_{r[0].split()[0]}", f"k{r[1]}", r[3], f"chance {r[4]}, lift {r[5]}") for r in rows
    ]
    write_tsv(args.data / BASELINE_SUMMARY, SUMMARY_COLUMNS, summary)
    print(f"\n-> {args.data / BASELINE_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
