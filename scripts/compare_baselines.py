"""Compare THEMA against the baselines a reader will ask about, on identical inputs.

Five arms over the same pathways, the same cuts, and -- for four of the five -- the same linkage,
so what differs between arms is one thing at a time:

  A   thema        embeddings of ``description_generated``, L2-normalised, Ward
  A'  name-strip   the same descriptions with the pathway's own name removed, Ward
  B   gene binary  binary gene-presence vectors, L2-normalised, Ward
  B'  gene sqrt-J  sqrt(Jaccard distance), Ward
  D   gene avg-J   Jaccard distance, average linkage -- the classic method as practised

A vs B isolates the REPRESENTATION: same algorithm, same cuts, different account of what a pathway
is. A vs A' measures how much of A's score is the pathway's own name, which the v3 prompt requires
every description to repeat and which the collision test defines its positives by.

B and B' are two encodings of one idea and are both run because they can disagree. Jaccard distance
is NOT Euclidean, so Ward on it minimises nothing -- and scipy will run it anyway without
complaining, which is the dangerous part. The square root of Jaccard distance IS isometrically
embeddable in L2, so Ward on sqrt(J) is legitimate. If B and B' diverge, the gene baseline is
sensitive to representation and no single number should be quoted for it. Average linkage (D) has no
Euclidean requirement, so raw Jaccard is proper there.

Arm C (name-only embeddings) is deliberately ABSENT from the recovery metric and present only in the
partition-agreement table. The reason is in the output, not only here.

Every observed rate is printed beside a BAND-MATCHED chance rate: random pairs drawn from the same
gene-overlap band, so the null controls for the thing being stratified on. A rate without its null
is unreadable -- on this data the classic gene baseline once showed 98.9% co-clustering against a
94.86% chance rate, a lift of 1x, because everything was in one cluster.

Pair sources are never pooled. They differ in evidential strength and a combined number would hide
that; each is reported separately with its caveat.
"""

import argparse
import collections
import random
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import adjusted_rand_score

from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import Pathway, PathwayCollection
from thema.data.tables import print_table
from thema.embed import embed, l2_normalize
from thema.evaluation import (
    BANDS,
    QUOTABLE,
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
from thema.normalize import display_name, strip_name

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"
DEFAULT_RAW = REPO_ROOT / "data" / "raw"

CUTS = (25, 50, 100)

#: Random pairs drawn to estimate the band-matched chance rate. Large because the rarest band holds
#: a small share of all pairs and its null needs enough draws to be stable.
NULL_DRAWS = 400_000

#: Fan-out cap for the precision-filtered sibling arms.
SIBLING_FANOUT = 6


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


def gene_matrix(pathways: list[Pathway]) -> sp.csr_matrix:
    """Build the sparse binary gene-presence matrix.

    Sparse because the dense form is ``n x 19,000`` and most rows hold a few dozen genes; at the
    full collection the dense float32 form alone would be most of a gigabyte before any distance is
    computed.

    Args:
        pathways: The pathways, in the order the comparison uses.

    Returns:
        A CSR matrix, one row per pathway, one column per gene in the union.
    """
    genes = sorted({g for p in pathways for g in p.genes})
    index = {g: i for i, g in enumerate(genes)}
    rows, cols = [], []
    for row, pathway in enumerate(pathways):
        for gene in pathway.genes:
            rows.append(row)
            cols.append(index[gene])
    data = np.ones(len(rows), dtype=np.float32)
    return sp.csr_matrix((data, (rows, cols)), shape=(len(pathways), len(genes)), dtype=np.float32)


def gene_distances(matrix: sp.csr_matrix) -> tuple[np.ndarray, np.ndarray]:
    """Compute Euclidean-on-L2-normalised and Jaccard distances from one sparse matrix.

    Args:
        matrix: The binary gene matrix.

    Returns:
        The condensed cosine-derived Euclidean distances, and the condensed Jaccard distances.

    Raises:
        ValueError: If fewer than two rows are given.
    """
    if matrix.shape[0] < 2:
        raise ValueError("need at least two pathways to compare")
    intersection = np.asarray((matrix @ matrix.T).todense(), dtype=np.float32)
    sizes = np.asarray(matrix.sum(axis=1), dtype=np.float32).ravel()
    union = sizes[:, None] + sizes[None, :] - intersection
    with np.errstate(divide="ignore", invalid="ignore"):
        similarity = np.where(union > 0, intersection / np.maximum(union, 1e-9), 0.0)
        norms = np.sqrt(np.outer(sizes, sizes))
        cosine = np.where(norms > 0, intersection / np.maximum(norms, 1e-9), 0.0)
    euclid = np.sqrt(np.maximum(2.0 - 2.0 * np.clip(cosine, -1.0, 1.0), 0.0))
    jac = 1.0 - similarity
    for square in (euclid, jac):
        np.fill_diagonal(square, 0.0)
    return squareform(euclid, checks=False), squareform(jac, checks=False)


def cluster(condensed: np.ndarray, method: str) -> dict[int, np.ndarray]:
    """Cluster one arm and cut it at every depth.

    Args:
        condensed: The condensed distance matrix.
        method: The linkage.

    Returns:
        Cut size to a label per observation.
    """
    tree = linkage(condensed, method=method)
    return {k: fcluster(tree, t=k, criterion="maxclust") for k in CUTS}


def null_by_band(
    pathways: list[Pathway], labels: dict[int, np.ndarray], cut: int, seed: int = 0
) -> dict[tuple[float, float], float]:
    """Estimate the chance co-clustering rate separately within each gene-overlap band.

    A single overall chance rate is the wrong null for a stratified table: low-overlap pairs are
    rarer and differently distributed, and comparing an observed low-overlap rate against an
    all-pairs null flatters or punishes an arm for reasons unrelated to the arm.

    Args:
        pathways: The pathways, in label order.
        labels: The arm's labels per cut.
        cut: Which cut to estimate for.
        seed: RNG seed.

    Returns:
        Band to its chance co-clustering rate; a band with no draws maps to 0.0.
    """
    rng = random.Random(seed)
    label = labels[cut]
    hits: collections.Counter = collections.Counter()
    draws: collections.Counter = collections.Counter()
    count = len(pathways)
    for _ in range(NULL_DRAWS):
        i, j = rng.randrange(count), rng.randrange(count)
        if i == j:
            continue
        value = jaccard(pathways[i], pathways[j])
        if value is None:
            continue
        band = band_of(value)
        draws[band] += 1
        hits[band] += label[i] == label[j]
    return {b: (hits[b] / draws[b] if draws[b] else 0.0) for b in BANDS}


def recovery_table(
    source: PairSource,
    arms: dict[str, dict[int, np.ndarray]],
    position: dict[str, int],
    pathways: list[Pathway],
    cut: int,
) -> None:
    """Print one source's band-stratified recovery, with a band-matched null beside every rate.

    Args:
        source: The pair source, restricted to present pairs.
        arms: Arm name to labels per cut.
        position: Pathway key to row index.
        pathways: The pathways, in row order.
        cut: Which cut to report.
    """
    banded: dict[tuple[float, float], list[tuple[str, str]]] = {b: [] for b in BANDS}
    undefined = 0
    for a, b in source.pairs:
        value = jaccard(pathways[position[a]], pathways[position[b]])
        if value is None:
            undefined += 1
            continue
        banded[band_of(value)].append((a, b))

    nulls = {name: null_by_band(pathways, labels, cut) for name, labels in arms.items()}
    rows: list[tuple[str, ...]] = []
    for band in reversed(BANDS):
        pairs = banded[band]
        if not pairs:
            continue
        cells: list[str] = []
        for name, labels in arms.items():
            label = labels[cut]
            hit = sum(1 for a, b in pairs if label[position[a]] == label[position[b]])
            observed = f"{hit}/{len(pairs)}" if len(pairs) < QUOTABLE else f"{hit / len(pairs):.0%}"
            cells += [observed, f"{nulls[name][band]:.1%}"]
        note = "n too small to quote" if len(pairs) < QUOTABLE else ""
        rows.append((band_label(*band), str(len(pairs)), *cells, note))
    if undefined:
        rows.append(("undefined J", str(undefined), *["-"] * (2 * len(arms)), "no genes"))
    headers = ["band", "n"]
    for name in arms:
        headers += [name, "chance"]
    headers.append("")
    print_table(headers, rows, align="<>" + ">" * (2 * len(arms)) + "<")


def main(argv: list[str] | None = None) -> int:
    """Run the baseline comparison."""
    parser = argparse.ArgumentParser(
        prog="compare_baselines.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw data directory")
    parser.add_argument("--cut", type=int, default=50, help="cut for the stratified tables")
    args = parser.parse_args(argv)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    texts = {
        k: v
        for k, v in read_descriptions(args.data / "pathway_descriptions.tsv").items()
        if k in by_key and v.strip()
    }
    keys = sorted(texts)
    pathways = [by_key[k] for k in keys]
    position = {k: i for i, k in enumerate(keys)}
    print(f"\nBASELINE COMPARISON  ({len(keys):,} pathways, stratified tables at k={args.cut})")

    print("embedding descriptions (A)", file=sys.stderr)
    a_vec = embed([texts[k] for k in keys])
    print("embedding name-stripped descriptions (A')", file=sys.stderr)
    a_strip = embed([strip_name(texts[k], display_name(by_key[k])) for k in keys])
    print("embedding names only (C, ARI table only)", file=sys.stderr)
    c_vec = embed([display_name(p) for p in pathways])
    print("building gene distances (B, B', D)", file=sys.stderr)
    euclid, jac = gene_distances(gene_matrix(pathways))

    from thema.cluster import distances as unit_distances

    arms = {
        "A thema": cluster(unit_distances(a_vec), "ward"),
        "A' strip": cluster(unit_distances(a_strip), "ward"),
        "B binary": cluster(euclid, "ward"),
        "B' sqrtJ": cluster(np.sqrt(jac), "ward"),
        "D avg-J": cluster(jac, "average"),
    }
    c_arm = cluster(unit_distances(l2_normalize(c_vec)), "ward")

    relation = read_reactome_relation(
        (args.raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    with (args.raw / "go-basic.obo").open("r", encoding="utf-8") as handle:
        terms = parse_obo_terms(handle, namespace="biological_process")

    mapped = reactome2go_pairs((args.raw / "reactome2go").read_text(encoding="utf-8").splitlines())
    independent = PairSource(
        "reactome2go (independent)",
        tuple(
            p
            for p in mapped.pairs
            if p[0] in by_key and p[1] in by_key and not shares_name(by_key[p[0]], by_key[p[1]])
        ),
        "strong",
        "the subset that is NOT also a name collision -- the only structural evidence here that is "
        "independent of the collision test",
    )
    sources = [
        collision_pairs(collection),
        mapped,
        independent,
        sibling_pairs(relation, "reactome:", "reactome-siblings", "same-curator hierarchy"),
        sibling_pairs(
            relation,
            "reactome:",
            f"reactome-siblings (fan-out<={SIBLING_FANOUT})",
            "same-curator hierarchy, broad parents dropped",
            max_children=SIBLING_FANOUT,
        ),
        sibling_pairs(go_parents(terms), "go:", "go-siblings", "same-curator hierarchy"),
        sibling_pairs(
            go_parents(terms),
            "go:",
            f"go-siblings (fan-out<={SIBLING_FANOUT})",
            "same-curator hierarchy, broad parents dropped",
            max_children=SIBLING_FANOUT,
        ),
    ]

    for source in sources:
        here = restrict(source, keys)
        print(f"\n{'=' * 100}")
        print(f"{here.name.upper()}  [{here.strength}]  n={len(here.pairs):,} pairs, k={args.cut}")
        print(f"caveat: {here.caveat}")
        print("=" * 100 + "\n")
        if not here.pairs:
            print("  no pairs present in this run\n")
            continue
        recovery_table(here, arms, position, pathways, args.cut)

    print(f"\n{'=' * 100}\nPARTITION AGREEMENT (adjusted Rand, k={args.cut})\n{'=' * 100}\n")
    everything = {**arms, "C name-only": c_arm}
    names = list(everything)
    def ari(a: str, b: str) -> str:
        """Adjusted Rand between two arms at the reported cut."""
        if a == b:
            return "-"
        return f"{adjusted_rand_score(everything[a][args.cut], everything[b][args.cut]):.3f}"

    print_table(
        ("arm", *names),
        [(a, *[ari(a, b) for b in names]) for a in names],
        align="<" + ">" * len(names),
    )

    bb = adjusted_rand_score(arms["B binary"][args.cut], arms["B' sqrtJ"][args.cut])
    ac = adjusted_rand_score(arms["A thema"][args.cut], c_arm[args.cut])
    print("\nWHAT THESE NUMBERS DO AND DO NOT ESTABLISH\n")
    for line in (
        f"  ARI(B, B') = {bb:.3f}. Jaccard distance is not Euclidean, so Ward on it minimises",
        "    nothing and scipy runs it silently; sqrt(Jaccard) IS L2-embeddable, so B' is the",
        "    legitimate encoding. If these two disagree the gene baseline is sensitive to",
        "    representation and no single number should be quoted for it.",
        "",
        f"  ARI(A, C) = {ac:.3f}. This establishes that the descriptions CHANGE the structure",
        "    relative to names alone. It does NOT establish that they IMPROVE it: the ground",
        "    truth used here is name-defined, so it cannot referee between a tree built from",
        "    names and a tree built from prose written to repeat those names.",
        "",
        "  Arm C is excluded from every recovery table above. The collision pairs are DEFINED by",
        "    a shared name and arm C embeds only the name, so it would score at ceiling by",
        "    construction -- measuring the metric rather than the method. It is kept in the ARI",
        "    table, where it is informative.",
        "",
        "  Sibling sources are WEAK evidence: the curators who declared the relationship also",
        "    wrote the prose being embedded, so recovery is partly 'the text encodes the tree'.",
        "    They are supplementary and must never carry the headline.",
    ):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
