import numpy as np
import pytest
from scipy.spatial.distance import pdist

from compare_baselines import condensed_from_unit, gene_vectors, jaccard
from test_normalize_descriptions import _pathway


def _with_genes(key_id, genes):
    p = _pathway("reactome", key_id, f"Pathway {key_id}")
    symbols = tuple((g, (g.replace("HGNC:", "SYM"),)) for g in sorted(genes))
    return type(p)(
        **{
            **{f.name: getattr(p, f.name) for f in p.__dataclass_fields__.values()},
            "genes": frozenset(genes),
            "gene_symbols": symbols,
            "n_genes": len(genes),
        }
    )


# Ward needs Euclidean input. Binary presence vectors, L2-normalised, give the Ochiai coefficient
# under cosine -- a close kin of Jaccard that IS Euclidean, which a Jaccard matrix is not.
def test_gene_vectors_are_unit_length_and_mark_the_right_genes():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:2", "HGNC:3"})
    vectors = gene_vectors([a, b])
    assert vectors.shape == (2, 3), "one column per gene in the union"
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)
    # Cosine between them is the Ochiai coefficient: |A n B| / sqrt(|A| |B|) = 1/2.
    assert float(vectors[0] @ vectors[1]) == pytest.approx(0.5)


# A zero row cannot be normalised. It must not become NaN, which would poison every distance it
# takes part in rather than only its own.
def test_a_pathway_with_no_genes_produces_a_zero_row_not_nan():
    empty = _with_genes("R-HSA-3", set())
    vectors = gene_vectors([_with_genes("R-HSA-1", {"HGNC:1"}), empty])
    assert not np.isnan(vectors).any()
    assert float(np.linalg.norm(vectors[1])) == 0.0


# The Gram-matrix route exists because pdist is O(n^2 d) and the gene vectors are ~14,000-dim.
# It has to agree with pdist exactly, or the speedup is a silent change of answer.
def test_the_gram_route_agrees_with_pdist_on_unit_vectors():
    rng = np.random.default_rng(0)
    raw = rng.normal(size=(40, 12)).astype(np.float32)
    unit = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    assert np.allclose(condensed_from_unit(unit), pdist(unit, metric="euclidean"), atol=1e-5)


def test_the_gram_route_gives_zero_distance_between_identical_vectors():
    unit = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)
    assert float(condensed_from_unit(unit)[0]) == pytest.approx(0.0, abs=1e-6)


def test_jaccard_is_undefined_rather_than_zero_when_a_set_is_empty():
    a = _with_genes("R-HSA-1", {"HGNC:1", "HGNC:2"})
    b = _with_genes("R-HSA-2", {"HGNC:2"})
    empty = _with_genes("R-HSA-3", set())
    assert jaccard(a, b) == pytest.approx(0.5)
    assert jaccard(a, empty) is None, "0/0 is undefined, and reporting it as 0 would be a claim"
