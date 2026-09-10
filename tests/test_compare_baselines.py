import numpy as np
import pytest
import scipy.sparse as sp
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

from compare_baselines import auroc, condensed, gene_matrix, largest_share, match_cut, similarities
from test_normalize_descriptions import _pathway
from thema.evaluation import GENE_MEASURES, gene_similarity


def _with_genes(source_id, genes):
    p = _pathway("reactome", source_id, f"Pathway {source_id}")
    fields = {f: getattr(p, f) for f in p.__dataclass_fields__}
    fields.update(
        genes=frozenset(genes),
        gene_symbols=tuple((g, (g.replace("HGNC:", "SYM"),)) for g in sorted(genes)),
        n_genes=len(genes),
    )
    return type(p)(**fields)


def test_the_gene_matrix_is_sparse_and_reports_its_universe():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:2", "HGNC:3"})
    matrix, universe = gene_matrix([a, b])
    assert sp.issparse(matrix), "the dense form does not scale to the full collection"
    assert (matrix.shape, universe) == ((2, 3), 3)


# Each measure must be what it claims. These are the four the classic tools actually use, and a
# Jaccard-only baseline is a stand-in for them rather than the thing itself.
def test_every_measure_matches_its_definition():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:2", "HGNC:3"})
    sim = similarities(*gene_matrix([a, b]))
    assert set(sim) == set(GENE_MEASURES)
    assert sim["jaccard"][0, 1] == pytest.approx(1 / 3)
    assert sim["ochiai"][0, 1] == pytest.approx(0.5)
    assert sim["overlap"][0, 1] == pytest.approx(0.5)


# The overlap coefficient is 1 for ANY containment, which is why it has no containment blind spot
# and also why it is not a metric: two distinct sets sit at distance 0.
def test_the_overlap_coefficient_is_one_for_containment_where_jaccard_is_small():
    small = _with_genes("R-HSA-1", {"HGNC:1"})
    big = _with_genes("R-HSA-2", {f"HGNC:{i}" for i in range(1, 21)})
    sim = similarities(*gene_matrix([small, big]))
    assert sim["overlap"][0, 1] == pytest.approx(1.0)
    assert sim["jaccard"][0, 1] == pytest.approx(1 / 20)


# Kappa's chance term is dominated by shared ABSENCE, so the universe is not a detail: over a large
# universe the coefficient collapses toward the raw overlap it exists to correct.
def test_kappa_depends_on_the_universe_it_is_computed_over():
    inter = np.array([[2.0, 1.0], [1.0, 2.0]])
    sizes = np.array([2.0, 2.0])
    small = gene_similarity(inter, sizes, 10, "kappa")[0, 1]
    large = gene_similarity(inter, sizes, 20000, "kappa")[0, 1]
    assert small == pytest.approx(0.375, abs=1e-3)
    assert large == pytest.approx(0.500, abs=1e-3)
    # The direction is not the point and is not fixed across set sizes; the DEPENDENCE is the
    # point, which is why the universe is an argument and is stated in the output.
    assert abs(large - small) > 0.1, "the universe must move the coefficient substantially"


def test_an_unknown_measure_is_an_error_rather_than_a_silent_zero():
    with pytest.raises(ValueError, match="unknown measure"):
        gene_similarity(np.zeros((2, 2)), np.ones(2), 10, "cosine-ish")


# sqrt(Jaccard distance) is what makes Ward legitimate on Jaccard: 1-J is a metric but is not
# L2-embeddable, while its square root is.
def test_sqrt_jaccard_distance_satisfies_the_triangle_inequality():
    sets = [{"a", "b"}, {"b", "c"}, {"c", "d"}]
    pathways = [_with_genes(f"R-HSA-{i}", {f"HGNC:{g}" for g in s}) for i, s in enumerate(sets)]
    sim = similarities(*gene_matrix(pathways))
    square = squareform(condensed(np.sqrt(np.maximum(1.0 - sim["jaccard"], 0.0))))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                assert square[i, j] <= square[i, k] + square[k, j] + 1e-6


def test_condensing_forces_an_exact_zero_diagonal():
    square = np.array([[1e-9, 0.5], [0.5, 1e-9]])
    assert condensed(square).shape == (1,)
    assert condensed(square)[0] == pytest.approx(0.5)


# Average linkage on Jaccard collapses into one blob at the cuts the other arms use. Cutting it
# there is not how the classic method is used, so it is also reported at a comparable share.
def test_match_cut_finds_the_depth_with_a_comparable_largest_cluster():
    rng = np.random.default_rng(0)
    raw = rng.normal(size=(60, 6))
    unit = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    tree = linkage(squareform(np.linalg.norm(unit[:, None] - unit[None, :], axis=-1)), "average")
    k, share = match_cut(tree, 0.10, 60)
    assert k >= 2
    assert share <= 0.25, "the matched cut must actually reduce the largest cluster"


def test_largest_share_is_the_biggest_clusters_fraction():
    assert largest_share(np.array([1, 1, 1, 2])) == pytest.approx(0.75)


# The cut-free metric is the one that survives when the partition does not, so its statistic has to
# be right: ties count as half, and a perfect separation is 1.
def test_auroc_handles_perfect_separation_ties_and_empty_input():
    assert auroc(np.array([3.0, 4.0]), np.array([1.0, 2.0])) == pytest.approx(1.0)
    assert auroc(np.array([1.0, 2.0]), np.array([3.0, 4.0])) == pytest.approx(0.0)
    assert auroc(np.array([1.0, 1.0]), np.array([1.0, 1.0])) == pytest.approx(0.5)
    assert auroc(np.array([]), np.array([1.0])) == pytest.approx(0.5)
