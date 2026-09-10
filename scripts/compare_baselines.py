"""Compare THEMA against the strongest gene-overlap baselines available, on identical inputs.

Six measures of what a pathway is, clustered identically wherever the mathematics allows it:

  descriptions      BioLORD embeddings of ``description_generated``            Ward
  name-stripped     the same descriptions with the pathway's own name removed  Ward
  jaccard           shared/union                                               Ward on sqrt(1-J)
  ochiai            shared/sqrt(n1*n2)                                         Ward
  overlap           shared/min(n1,n2)                                          average
  kappa             chance-corrected agreement on membership                   average

A Jaccard-only gene baseline is not the classic method: DAVID and Metascape use Cohen's kappa, and
Metascape merges terms above kappa 0.3. Quoting a single gene number would be picking a convenient
opponent, so every band names its BEST GENE ARM and says which measure that was. Where a gene
measure beats THEMA, the output says so in the same words as everywhere else.

Linkage is not a free choice. Ward's criterion is defined on squared Euclidean distance and scipy
runs it on any matrix without complaining, so each measure carries its reasoning in
``thema.evaluation.GENE_MEASURES``: Ochiai is cosine between binary vectors and is Euclidean
directly; 1-Jaccard is a metric but not L2-embeddable while sqrt(1-Jaccard) is, so Ward sees the
square root and never the raw value; the overlap coefficient is 1 for any containment, so distinct
sets sit at distance 0 and it is not a metric at all; kappa can go negative. The last two get
average linkage, which requires no geometry.

Two nulls are printed for every rate. The band-matched null removes exactly the variable the gene
arms cluster on, which makes it the right question -- "better than chance among pairs of this
overlap?" -- and also makes it look stacked against them if shown alone. The global null is shown
beside it throughout.

Arm C (name-only embeddings) is absent from every recovery table and present only in the
partition-agreement table; the reason is printed in the output.
"""

import argparse
import collections
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import adjusted_rand_score

from thema.cluster import distances as unit_distances
from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import Pathway, PathwayCollection
from thema.data.tables import print_table, write_tsv
from thema.embed import embed, l2_normalize
from thema.evaluation import (
    BANDS,
    GENE_MEASURES,
    QUOTABLE,
    PairSource,
    band_label,
    band_of,
    collision_pairs,
    gene_similarity,
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
NULL_DRAWS = 400_000

#: Fan-out cap for the precision-filtered sibling arms. A judgement, not a derived threshold: it
#: drops the broad parents that manufacture unrelated pairs. The sensitivity of the RESULTS to this
#: value has not been tested, and the sibling sources are reported both capped and uncapped.
SIBLING_FANOUT = 6

#: Arms built from gene membership rather than text. Named so a "best gene arm" row can be computed
#: without hard-coding which columns those are.
GENE_ARMS = ("jaccard", "ochiai", "overlap", "kappa", "D classic", "D matched")


@dataclass(frozen=True, slots=True)
class Run:
    """Everything one comparison computed, so the reporting signature stays readable.

    Attributes:
        collection: All pathways.
        by_key: Pathways by key.
        keys: Keys in row order.
        pathways: Pathways in row order.
        position: Key to row index.
        labels: Arm name to labels at the reported cut.
        nulls: Band-matched chance per arm.
        globals_: Global chance per arm.
        sim: Gene similarity matrices by measure.
        a_vec: Description embeddings.
        a_strip: Name-stripped embeddings.
        c_vec: Name-only embeddings, for the agreement table only.
    """

    collection: PathwayCollection
    by_key: dict[str, Pathway]
    keys: list[str]
    pathways: list[Pathway]
    position: dict[str, int]
    labels: dict[str, np.ndarray]
    nulls: dict[str, dict[tuple[float, float], float]]
    globals_: dict[str, float]
    sim: dict[str, np.ndarray]
    a_vec: np.ndarray
    a_strip: np.ndarray
    c_vec: np.ndarray


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


def gene_matrix(pathways: list[Pathway]) -> tuple[sp.csr_matrix, int]:
    """Build the sparse binary gene-presence matrix and the size of its universe.

    Args:
        pathways: The pathways, in the order the comparison uses.

    Returns:
        The CSR matrix and how many distinct genes it spans. That count is the universe kappa's
        chance term is computed over, and it is stated in the output because kappa depends on it.
    """
    genes = sorted({g for p in pathways for g in p.genes})
    index = {g: i for i, g in enumerate(genes)}
    rows, cols = [], []
    for row, pathway in enumerate(pathways):
        for gene in pathway.genes:
            rows.append(row)
            cols.append(index[gene])
    matrix = sp.csr_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, cols)),
        shape=(len(pathways), len(genes)),
        dtype=np.float32,
    )
    return matrix, len(genes)


def similarities(matrix: sp.csr_matrix, universe: int) -> dict[str, np.ndarray]:
    """Compute every gene-set similarity matrix from one sparse pass.

    Args:
        matrix: The binary gene matrix.
        universe: Genes spanned, for kappa's chance term.

    Returns:
        Measure name to an ``(n, n)`` similarity array.
    """
    intersection = np.asarray((matrix @ matrix.T).todense(), dtype=np.float64)
    sizes = np.asarray(matrix.sum(axis=1), dtype=np.float64).ravel()
    return {name: gene_similarity(intersection, sizes, universe, name) for name in GENE_MEASURES}


def condensed(square: np.ndarray) -> np.ndarray:
    """Condense a square distance matrix, forcing an exact zero diagonal."""
    out = np.array(square, dtype=np.float64, copy=True)
    np.fill_diagonal(out, 0.0)
    return squareform(np.maximum(out, 0.0), checks=False)


def cluster(dist: np.ndarray, method: str, cuts: tuple[int, ...] = CUTS) -> dict[int, np.ndarray]:
    """Cluster one arm and cut it at every depth.

    Args:
        dist: The condensed distance matrix.
        method: The linkage.
        cuts: The depths.

    Returns:
        Cut size to a label per observation.
    """
    tree = linkage(dist, method=method)
    return {k: fcluster(tree, t=k, criterion="maxclust") for k in cuts}


def largest_share(labels: np.ndarray) -> float:
    """What share of observations the biggest cluster holds."""
    _values, counts = np.unique(labels, return_counts=True)
    return float(counts.max() / counts.sum())


def match_cut(tree: np.ndarray, target: float, count: int) -> tuple[int, float]:
    """Find the cut at which a tree's largest-cluster share is closest to a target.

    Average linkage on Jaccard collapses into one blob at the cuts the other arms use, and cutting
    it there is not how the classic method is used -- so it is also reported at whatever depth makes
    its largest cluster comparable to THEMA's, which is the fair version of the same baseline.

    Args:
        tree: The linkage matrix.
        target: The largest-cluster share to match.
        count: How many observations.

    Returns:
        The matched k and the share it achieved.
    """
    best, best_share, best_gap = CUTS[0], 1.0, 2.0
    for k in range(2, min(count, 4000)):
        share = largest_share(fcluster(tree, t=k, criterion="maxclust"))
        gap = abs(share - target)
        if gap < best_gap:
            best, best_share, best_gap = k, share, gap
        if share <= target:
            break
    return best, best_share


def null_grids(
    pathways: list[Pathway], arms: dict[str, np.ndarray], seed: int = 0
) -> tuple[dict[str, dict[tuple[float, float], float]], dict[str, float]]:
    """Estimate band-matched and global chance rates once per arm.

    The nulls do not depend on the pair source, so they are computed once and reused; doing it per
    source multiplied the work by the number of sources for identical numbers.

    Args:
        pathways: The pathways, in label order.
        arms: Arm name to its labels at the reported cut.
        seed: RNG seed.

    Returns:
        Band-matched rates per arm, and the global rate per arm.
    """
    rng = random.Random(seed)
    count = len(pathways)
    hits = {name: collections.Counter() for name in arms}
    draws: collections.Counter = collections.Counter()
    globals_ = dict.fromkeys(arms, 0)
    total = 0
    for _ in range(NULL_DRAWS):
        i, j = rng.randrange(count), rng.randrange(count)
        if i == j:
            continue
        total += 1
        for name, labels in arms.items():
            globals_[name] += labels[i] == labels[j]
        value = jaccard(pathways[i], pathways[j])
        if value is None:
            continue
        band = band_of(value)
        draws[band] += 1
        for name, labels in arms.items():
            hits[name][band] += labels[i] == labels[j]
    banded = {
        name: {b: (hits[name][b] / draws[b] if draws[b] else 0.0) for b in BANDS} for name in arms
    }
    return banded, {name: globals_[name] / max(total, 1) for name in arms}


def auroc(positive: np.ndarray, negative: np.ndarray) -> float:
    """Probability a random positive scores above a random negative, ties counted as half.

    Args:
        positive: Similarities of curated pairs.
        negative: Similarities of random pairs.

    Returns:
        The AUROC, or 0.5 when either side is empty.
    """
    if not len(positive) or not len(negative):
        return 0.5
    order = np.argsort(np.concatenate([positive, negative]), kind="mergesort")
    ranks = np.empty(len(order), dtype=np.float64)
    ranks[order] = np.arange(1, len(order) + 1)
    values = np.concatenate([positive, negative])
    # Average ranks within ties so a tie contributes exactly 0.5.
    _uniq, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    sums = np.zeros(len(_uniq))
    np.add.at(sums, inverse, ranks)
    ranks = (sums / counts)[inverse]
    n_pos = len(positive)
    return float((ranks[:n_pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * len(negative)))


def band_pairs(
    source: PairSource, position: dict[str, int], pathways: list[Pathway]
) -> tuple[dict[tuple[float, float], list[tuple[int, int]]], int]:
    """Group a source's pairs by gene-overlap band, as row-index pairs.

    Args:
        source: The pair source, restricted to present pairs.
        position: Pathway key to row index.
        pathways: The pathways, in row order.

    Returns:
        Band to index pairs, and how many pairs had an undefined Jaccard.
    """
    banded: dict[tuple[float, float], list[tuple[int, int]]] = {b: [] for b in BANDS}
    undefined = 0
    for a, b in source.pairs:
        i, j = position[a], position[b]
        value = jaccard(pathways[i], pathways[j])
        if value is None:
            undefined += 1
            continue
        banded[band_of(value)].append((i, j))
    return banded, undefined


def cell(hit: int, total: int) -> str:
    """Render a recovery cell: a percentage, or a raw fraction when n is too small to quote."""
    return f"{hit}/{total}" if total < QUOTABLE else f"{hit / total:.0%}"


def recovery_grid(
    source: PairSource,
    arms: dict[str, np.ndarray],
    banded: dict[tuple[float, float], list[tuple[int, int]]],
    undefined: int,
    nulls: dict[str, dict[tuple[float, float], float]],
    globals_: dict[str, float],
    rows_out: list[tuple[str, ...]],
) -> None:
    """Print one source's grid: rows are measures, columns are gene-overlap bands.

    Args:
        source: The pair source.
        arms: Arm name to labels at the reported cut.
        banded: Band to index pairs.
        undefined: Pairs with no defined Jaccard.
        nulls: Band-matched chance per arm.
        globals_: Global chance per arm.
        rows_out: Accumulator for the committed TSV.
    """
    used = [b for b in reversed(BANDS) if banded[b]]
    header = ["measure", *(band_label(*b) for b in used)]
    rows: list[tuple[str, ...]] = [("n pairs", *(str(len(banded[b])) for b in used))]

    scores: dict[str, dict[tuple[float, float], float]] = {}
    for name, labels in arms.items():
        cells = []
        scores[name] = {}
        for band in used:
            pairs = banded[band]
            hit = sum(1 for i, j in pairs if labels[i] == labels[j])
            scores[name][band] = hit / len(pairs)
            cells.append(cell(hit, len(pairs)))
            rows_out.append(
                (
                    source.name,
                    source.strength,
                    band_label(*band),
                    str(len(pairs)),
                    name,
                    f"{hit / len(pairs):.4f}",
                    f"{nulls[name][band]:.4f}",
                    f"{globals_[name]:.4f}",
                    f"{scores[name][band] / nulls[name][band]:.2f}" if nulls[name][band] else "inf",
                )
            )
        rows.append((name, *cells))

    best = []
    beaten = []
    for band in used:
        winner = max(GENE_ARMS, key=lambda g: scores[g][band])
        # The chance rate travels with the winner. Without it "D classic 100%" reads as a strong
        # baseline when it is a collapsed blob whose own null is also near 100%.
        hits = round(scores[winner][band] * len(banded[band]))
        best.append(f"{cell(hits, len(banded[band]))} {winner} ch{nulls[winner][band]:.0%}")
        if scores[winner][band] > scores["descriptions"][band]:
            beaten.append(
                (
                    band_label(*band),
                    winner,
                    scores[winner][band],
                    scores["descriptions"][band],
                    nulls[winner][band],
                    nulls["descriptions"][band],
                )
            )
    rows.append(("BEST GENE ARM", *best))

    print_table(header, rows, align="<" + ">" * len(used))
    small = [band_label(*b) for b in used if len(banded[b]) < QUOTABLE]
    if small:
        print(f"  n too small to quote: {', '.join(small)} (shown as raw fractions)")
    if undefined:
        print(f"  {undefined} pair(s) dropped: a member resolved to no genes")
    for band, winner, gene_rate, thema_rate, gene_chance, thema_chance in beaten:
        print(
            f"  A GENE MEASURE BEATS THEMA HERE: in band {band}, {winner} scores "
            f"{gene_rate:.0%} against descriptions at {thema_rate:.0%}. Their chance rates are "
            f"{gene_chance:.0%} and {thema_chance:.0%}, so the lifts are "
            f"{gene_rate / gene_chance:.1f}x and {thema_rate / thema_chance:.1f}x."
        )


def main(argv: list[str] | None = None) -> int:
    """Run the baseline comparison."""
    parser = argparse.ArgumentParser(
        prog="compare_baselines.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw data directory")
    parser.add_argument("--cut", type=int, default=50, help="cut for the stratified grids")
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

    print("embedding descriptions", file=sys.stderr)
    a_vec = embed([texts[k] for k in keys])
    print("embedding name-stripped descriptions", file=sys.stderr)
    a_strip = embed([strip_name(texts[k], display_name(by_key[k])) for k in keys])
    print("embedding names only (ARI table only)", file=sys.stderr)
    c_vec = l2_normalize(embed([display_name(p) for p in pathways]))
    print("computing gene similarities", file=sys.stderr)
    matrix, universe = gene_matrix(pathways)
    sim = similarities(matrix, universe)

    print(f"\nBASELINE COMPARISON  ({len(keys):,} pathways, grids at k={args.cut})")
    print(f"kappa universe: {universe:,} genes -- the union across this run, NOT the genome.")
    print("Over the genome, shared ABSENCE dominates kappa's chance term and the coefficient")
    print("collapses toward the raw overlap it exists to correct. DAVID uses the submitted list")
    print(
        "for the same reason; THEMA's background is the measured universe (DECISIONS 2026-08-21).\n"
    )
    print_table(
        ("measure", "linkage", "why"),
        [
            ("descriptions", "ward", "L2-normalised embeddings are Euclidean points"),
            ("name-stripped", "ward", "same"),
            *(
                (name, "ward" if name in ("jaccard", "ochiai") else "average", reason)
                for name, reason in GENE_MEASURES.items()
            ),
        ],
        align="<<<",
    )

    trees = {
        "descriptions": linkage(unit_distances(a_vec), "ward"),
        "name-stripped": linkage(unit_distances(a_strip), "ward"),
        "jaccard": linkage(condensed(np.sqrt(np.maximum(1.0 - sim["jaccard"], 0.0))), "ward"),
        "ochiai": linkage(
            condensed(np.sqrt(np.maximum(2.0 - 2.0 * np.clip(sim["ochiai"], -1, 1), 0.0))), "ward"
        ),
        "overlap": linkage(condensed(1.0 - sim["overlap"]), "average"),
        "kappa": linkage(condensed(1.0 - sim["kappa"]), "average"),
        "D classic": linkage(condensed(1.0 - sim["jaccard"]), "average"),
    }
    labels = {name: fcluster(t, t=args.cut, criterion="maxclust") for name, t in trees.items()}

    target = largest_share(labels["descriptions"])
    matched_k, matched_share = match_cut(trees["D classic"], target, len(keys))
    labels["D matched"] = fcluster(trees["D classic"], t=matched_k, criterion="maxclust")
    print(
        f"\nD classic at k={args.cut} holds "
        f"{largest_share(labels['D classic']):.1%} of pathways in one cluster "
        f"against THEMA's {target:.1%}."
    )
    print(
        f"D matched re-cuts the SAME tree at k={matched_k}, largest cluster "
        f"{matched_share:.1%} -- the fair version of the classic baseline, since "
        "nobody uses it at a cut where it has collapsed."
    )

    print("\ncomputing nulls once per arm", file=sys.stderr)
    nulls, globals_ = null_grids(pathways, labels)
    print("\n" + "=" * 100)
    print("CHANCE RATES (identical for every pair source, so shown once)")
    print("=" * 100 + "\n")
    print_table(
        ("measure", *(band_label(*b) for b in reversed(BANDS)), "global"),
        [
            (name, *(f"{nulls[name][b]:.1%}" for b in reversed(BANDS)), f"{globals_[name]:.1%}")
            for name in labels
        ],
        align="<" + ">" * (len(BANDS) + 1),
    )
    return _report(
        args,
        Run(
            collection,
            by_key,
            keys,
            pathways,
            position,
            labels,
            nulls,
            globals_,
            sim,
            a_vec,
            a_strip,
            c_vec,
        ),
    )


def cosine_pairs(vectors: np.ndarray, pairs: list[tuple[int, int]]) -> np.ndarray:
    """Cosine similarity for a list of index pairs of unit vectors."""
    if not pairs:
        return np.empty(0)
    i = np.fromiter((p[0] for p in pairs), dtype=int, count=len(pairs))
    j = np.fromiter((p[1] for p in pairs), dtype=int, count=len(pairs))
    return np.einsum("ij,ij->i", vectors[i], vectors[j])


def matrix_pairs(square: np.ndarray, pairs: list[tuple[int, int]]) -> np.ndarray:
    """Look up a similarity matrix at a list of index pairs."""
    if not pairs:
        return np.empty(0)
    i = np.fromiter((p[0] for p in pairs), dtype=int, count=len(pairs))
    j = np.fromiter((p[1] for p in pairs), dtype=int, count=len(pairs))
    return square[i, j]


def _report(args: argparse.Namespace, run: "Run") -> int:
    """Print every source's grid, the cut-free metrics, and the agreement table.

    Args:
        args: Parsed arguments.
        run: Everything the comparison computed, bundled so this signature stays readable.

    Returns:
        0.
    """
    collection, by_key, keys = run.collection, run.by_key, run.keys
    pathways, position, labels = run.pathways, run.position, run.labels
    nulls, globals_, sim = run.nulls, run.globals_, run.sim
    a_vec, a_strip, c_vec = run.a_vec, run.a_strip, run.c_vec

    relation = read_reactome_relation(
        (args.raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    with (args.raw / "go-basic.obo").open("r", encoding="utf-8") as handle:
        terms = parse_obo_terms(handle, namespace="biological_process")
    mapped = reactome2go_pairs((args.raw / "reactome2go").read_text(encoding="utf-8").splitlines())
    sources = [
        collision_pairs(collection),
        mapped,
        PairSource(
            "reactome2go (independent)",
            tuple(
                p
                for p in mapped.pairs
                if p[0] in by_key and p[1] in by_key and not shares_name(by_key[p[0]], by_key[p[1]])
            ),
            "strong",
            "the subset that is NOT also a name collision -- the only structural evidence here "
            "independent of the collision test",
        ),
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

    rows_out: list[tuple[str, ...]] = []
    auc_out: list[tuple[str, ...]] = []
    rng = np.random.default_rng(0)
    for source in sources:
        here = restrict(source, keys)
        print(f"\n{'=' * 100}")
        print(f"{here.name.upper()}  [{here.strength}]  n={len(here.pairs):,}, k={args.cut}")
        print(f"caveat: {here.caveat}")
        print("=" * 100 + "\n")
        if not here.pairs:
            print("  no pairs present in this run\n")
            continue
        banded, undefined = band_pairs(here, position, pathways)
        recovery_grid(here, labels, banded, undefined, nulls, globals_, rows_out)

        # ---- cut-free: separate curated pairs from random pairs of the SAME overlap band
        measures = {
            "descriptions": lambda p: cosine_pairs(a_vec, p),
            "name-stripped": lambda p: cosine_pairs(a_strip, p),
            **{m: (lambda p, m=m: matrix_pairs(sim[m], p)) for m in GENE_MEASURES},
        }
        grid_rows = []
        used = [b for b in reversed(BANDS) if len(banded[b]) >= QUOTABLE]
        if used:
            controls = {}
            for band in used:
                pool = []
                while len(pool) < 2000:
                    i, j = int(rng.integers(len(pathways))), int(rng.integers(len(pathways)))
                    if i == j:
                        continue
                    value = jaccard(pathways[i], pathways[j])
                    if value is not None and band_of(value) == band:
                        pool.append((i, j))
                    if len(pool) == 0 and len(controls) > 200000:
                        break
                controls[band] = pool
            for name, fn in measures.items():
                cells = []
                for band in used:
                    a = auroc(fn(banded[band]), fn(controls[band]))
                    cells.append(f"{a:.2f}/{2 * a - 1:+.2f}")
                    auc_out.append(
                        (
                            here.name,
                            here.strength,
                            band_label(*band),
                            str(len(banded[band])),
                            name,
                            f"{a:.4f}",
                            f"{2 * a - 1:.4f}",
                        )
                    )
                grid_rows.append((name, *cells))
            print("\n  CUT-FREE: AUROC / Cliff's delta, curated vs random pairs of the same band\n")
            print_table(
                ("measure", *(band_label(*b) for b in used)), grid_rows, align="<" + ">" * len(used)
            )
            print("  (bands with n<10 omitted here; a rank statistic on nine pairs is noise)")

    out = args.data / "ontology" / "baseline_comparison.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_tsv(
        out,
        ("source", "strength", "band", "n", "arm", "rate", "band_chance", "global_chance", "lift"),
        rows_out,
    )
    auc_path = args.data / "ontology" / "baseline_cutfree.tsv"
    write_tsv(
        auc_path, ("source", "strength", "band", "n", "measure", "auroc", "cliffs_delta"), auc_out
    )
    print(f"\n{len(rows_out):,} recovery rows -> {out}")
    print(f"{len(auc_out):,} cut-free rows -> {auc_path}")

    c_labels = fcluster(linkage(unit_distances(c_vec), "ward"), t=args.cut, criterion="maxclust")
    everything = {**labels, "name-only": c_labels}
    names = list(everything)

    def ari(a: str, b: str) -> str:
        """Adjusted Rand between two arms at the reported cut."""
        return "-" if a == b else f"{adjusted_rand_score(everything[a], everything[b]):.3f}"

    print(f"\n{'=' * 100}\nPARTITION AGREEMENT (adjusted Rand, k={args.cut})\n{'=' * 100}\n")
    print_table(
        ("arm", *names),
        [(a, *[ari(a, b) for b in names]) for a in names],
        align="<" + ">" * len(names),
    )

    ac = adjusted_rand_score(everything["descriptions"], c_labels)
    print("\nWHAT THESE NUMBERS DO AND DO NOT ESTABLISH\n")
    for line in (
        f"  ARI(A, C) = {ac:.3f}. This establishes that the descriptions CHANGE the structure",
        "    relative to names alone. It does NOT establish that they IMPROVE it: the ground",
        "    truth used here is name-defined, so it cannot referee between a tree built from",
        "    names and a tree built from prose written to repeat those names.",
        "",
        "  Arm C is excluded from every recovery grid above. The collision pairs are DEFINED by",
        "    a shared name and arm C embeds only the name, so it would score at ceiling by",
        "    construction -- measuring the metric rather than the method. It is kept here,",
        "    where it is informative.",
        "",
        "  THEMA'S OWN LIMIT, stated by us. Recovery falls as gene overlap falls even for the",
        "    description arms. That is what our own eval plan predicts: descriptions are written",
        "    with the gene list in view (DECISIONS 2026-08-29), so v1 is a HYBRID text-and-",
        "    membership method, not a pure text method, and its advantage is largest exactly",
        "    where it shares the baseline's information. Lift holds because chance falls too,",
        "    but the absolute decline is real and is ours to report.",
        "",
        "  Sibling sources are WEAK: the curators who declared the relationship also wrote the",
        "    prose being embedded, so recovery is partly 'the text encodes the tree'.",
    ):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
