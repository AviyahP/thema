"""The provisional labelling and the not-computed discipline behind the demo export."""

import numpy as np
import pytest

from thema.demo import (
    LABEL_SEPARATOR,
    NOT_COMPUTED,
    distinctive_terms,
    document_frequency,
    medoid,
    provisional_label,
    source_spread,
    tokenize,
    uncomputed_tests,
)


def test_tokenize_drops_structure_and_short_tokens() -> None:
    assert tokenize("Regulation of the TP53 pathway by AA") == {"regulation", "tp53", "pathway"}


def test_tokenize_ignores_the_tba_placeholder() -> None:
    """``TBA`` is a source placeholder, not biology, and must never reach a label."""
    assert "tba" not in tokenize("TBA regulation of DNA repair")


def test_distinctive_terms_prefers_the_cluster_specific_word() -> None:
    background = document_frequency(
        ["interferon signaling", "neutrophil signaling", "apoptotic signaling", "cell signaling"]
    )
    terms = distinctive_terms(
        ["interferon signaling", "interferon response"], background, 4, limit=1
    )
    # "signaling" is in three of four background names; "interferon" in one.
    assert terms == ("interferon",)


def test_distinctive_terms_ignores_a_term_one_member_happens_to_carry() -> None:
    members = ["cell cycle"] * 9 + ["cell cycle and RB1"]
    terms = distinctive_terms(members, document_frequency(members), 10, limit=3)
    assert "rb1" not in terms


def test_distinctive_terms_floor_can_be_relaxed() -> None:
    members = ["cell cycle"] * 9 + ["cell cycle and RB1"]
    terms = distinctive_terms(members, document_frequency(members), 10, limit=3, floor=0.05)
    assert "rb1" in terms


def test_provisional_label_joins_with_a_separator_no_curator_writes() -> None:
    names = ["interferon alpha response", "interferon beta response"]
    label = provisional_label(names, document_frequency(names), 2)
    assert LABEL_SEPARATOR in label


def test_provisional_label_says_so_when_there_is_no_shared_vocabulary() -> None:
    assert provisional_label([], {}, 0) == "unlabelled"


def test_medoid_picks_the_member_nearest_the_centre() -> None:
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    assert medoid([0, 1, 2], vectors) == 2


def test_medoid_refuses_an_empty_cluster() -> None:
    with pytest.raises(ValueError):
        medoid([], np.zeros((1, 2)))


def test_source_spread_orders_by_count_then_name() -> None:
    counted = source_spread(["go", "reactome", "go", "btm"])
    assert counted == [("go", 2), ("btm", 1), ("reactome", 1)]


def test_every_attribution_test_reports_not_computed() -> None:
    """None of the three tests is implemented; none may render as having a result."""
    rows = uncomputed_tests()
    assert len(rows) == 3
    assert all(row[2] == NOT_COMPUTED and row[3] is False for row in rows)
