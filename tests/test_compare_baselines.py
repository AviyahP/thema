import numpy as np
import pytest
import scipy.sparse as sp
from scipy.spatial.distance import pdist, squareform

from compare_baselines import gene_distances, gene_matrix
from test_normalize_descriptions import _pathway


def _with_genes(source_id, genes):
    p = _pathway("reactome", source_id, f"Pathway {source_id}")
    fields = {f: getattr(p, f) for f in p.__dataclass_fields__}
    fields.update(
        genes=frozenset(genes),
        gene_symbols=tuple((g, (g.replace("HGNC:", "SYM"),)) for g in sorted(genes)),
        n_genes=len(genes),
    )
    return type(p)(**fields)


def test_the_gene_matrix_is_sparse_and_marks_the_right_cells():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:2", "HGNC:3"})
    matrix = gene_matrix([a, b])
    assert sp.issparse(matrix), "the dense form is n x 19,000 and does not scale to the full run"
    assert matrix.shape == (2, 3)
    assert matrix.toarray().sum() == 4


# The two encodings of gene overlap must be computed from one matrix and must be what they claim:
# cosine on binary sets is Ochiai, and Jaccard is intersection over union.
def test_both_distance_encodings_match_their_definitions():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:2", "HGNC:3"})
    euclid, jac = gene_distances(gene_matrix([a, b]))
    # Ochiai = 1/2, so Euclidean on unit vectors = sqrt(2 - 2*0.5) = 1.
    assert float(euclid[0]) == pytest.approx(1.0, abs=1e-5)
    # Jaccard = 1/3, so Jaccard distance = 2/3.
    assert float(jac[0]) == pytest.approx(2 / 3, abs=1e-6)


def test_disjoint_sets_are_maximally_far_under_both_encodings():
    a = _with_genes("R-HSA-1", {"HGNC:1"})
    b = _with_genes("R-HSA-2", {"HGNC:2"})
    euclid, jac = gene_distances(gene_matrix([a, b]))
    assert float(euclid[0]) == pytest.approx(np.sqrt(2.0), abs=1e-5)
    assert float(jac[0]) == pytest.approx(1.0, abs=1e-6)


def test_identical_sets_are_at_zero_under_both_encodings():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:1", "HGNC:2"})
    euclid, jac = gene_distances(gene_matrix([a, b]))
    assert float(euclid[0]) == pytest.approx(0.0, abs=1e-5)
    assert float(jac[0]) == pytest.approx(0.0, abs=1e-6)


# A pathway with no genes must not produce NaN, which would poison every distance it takes part in
# rather than only its own.
def test_a_gene_free_pathway_produces_finite_distances():
    pathways = [_with_genes("R-HSA-1", {"HGNC:1"}), _with_genes("R-HSA-2", set())]
    euclid, jac = gene_distances(gene_matrix(pathways))
    assert np.isfinite(euclid).all() and np.isfinite(jac).all()


# The Gram route replaces pdist because pdist is O(n^2 d) on ~19,000-dimensional rows. It has to
# agree with pdist exactly, or the speedup is a silent change of answer.
def test_the_gram_route_agrees_with_pdist():
    rng = np.random.default_rng(0)
    sets = [set(rng.choice(30, size=8, replace=False).tolist()) for _ in range(25)]
    pathways = [_with_genes(f"R-HSA-{i}", {f"HGNC:{g}" for g in s}) for i, s in enumerate(sets)]
    matrix = gene_matrix(pathways)
    euclid, _jac = gene_distances(matrix)
    dense = matrix.toarray()
    unit = dense / np.linalg.norm(dense, axis=1, keepdims=True)
    assert np.allclose(euclid, pdist(unit, metric="euclidean"), atol=1e-5)


# sqrt(Jaccard) is what makes arm B' legitimate: Jaccard distance is not Euclidean, so Ward on it
# minimises nothing, while sqrt(Jaccard) is isometrically embeddable in L2.
def test_sqrt_jaccard_is_a_metric_where_raw_jaccard_distance_need_not_be():
    sets = [{"a", "b"}, {"b", "c"}, {"c", "d"}]
    pathways = [_with_genes(f"R-HSA-{i}", {f"HGNC:{g}" for g in s}) for i, s in enumerate(sets)]
    _euclid, jac = gene_distances(gene_matrix(pathways))
    square = squareform(np.sqrt(jac))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                assert square[i, j] <= square[i, k] + square[k, j] + 1e-6
    assert gene_distances(gene_matrix(pathways))[1].shape == (3,)


def test_fewer_than_two_pathways_is_an_error():
    with pytest.raises(ValueError, match="at least two"):
        gene_distances(gene_matrix([_with_genes("R-HSA-1", {"HGNC:1"})]))
