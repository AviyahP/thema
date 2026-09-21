"""Bitsets: membership as fixed-width bit arrays."""

import numpy as np
import pytest

from thema.ontology import bitset as B


def test_words_and_roundtrip():
    assert B.words_for(1) == 1
    assert B.words_for(64) == 1
    assert B.words_for(65) == 2
    assert B.words_for(1854) == 29
    indices = [0, 5, 63, 64, 130, 199]
    assert B.unpack(B.pack(indices, 200)) == indices


def test_pack_refuses_an_index_outside_the_universe():
    """Dropping it silently would make a grouping smaller than it is and change its support."""
    with pytest.raises(IndexError):
        B.pack([200], 200)
    with pytest.raises(IndexError):
        B.pack([-1], 200)


def test_count_and_count_rows():
    assert B.count(B.pack([1, 2, 3], 100)) == 3
    rows = B.pack_many([[0, 1], [5], [3, 4, 5]], 100)
    assert B.count_rows(rows).tolist() == [2, 1, 3]
    assert B.count(rows) == 6, "count over a matrix is the total, count_rows is per row"


def test_pack_many_of_nothing_keeps_its_shape():
    empty = B.pack_many([], 130)
    assert empty.shape == (0, B.words_for(130)) == (0, 3)
    assert empty.dtype == np.uint64


def test_contains_is_non_strict_and_strict_subset_is_not():
    a = B.pack([0, 5, 64], 200)
    b = B.pack([0, 5], 200)
    assert B.contains(a, b) and not B.contains(b, a)
    assert B.contains(a, a), "a set contains itself"
    assert B.is_strict_subset(b, a)
    assert not B.is_strict_subset(a, a), "strictness is what the Hasse diagram needs"


def test_disjoint_sets_contain_nothing_of_each_other():
    a, b = B.pack([0, 1], 200), B.pack([70, 71], 200)
    assert not B.contains(a, b) and not B.contains(b, a)


def test_key_is_an_identity_not_a_digest():
    order_one = B.pack([130, 64, 5, 0], 200)
    order_two = B.pack([0, 5, 64, 130], 200)
    assert B.key(order_one) == B.key(order_two)
    assert B.key(B.pack([0], 200)) != B.key(B.pack([1], 200))
