"""The 10,770 build's completion cache and its floor solving.

The cache is what makes a cap or cutoff change a re-cut rather than a rebuild, so what it must
guarantee is that a round trip is EXACT -- an inclusion read back as a slightly different float
would export a different membership than the run that computed it.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_10770 import (  # noqa: E402
    DECLARED_M,
    STRATA,
    Material,
    cut_key,
    load_material,
    save_material,
    solve,
    stratum_of,
)


def _material() -> Material:
    """A two-family side whose inclusions are ratios a float32 could not hold exactly.

    Returns:
        The material.
    """
    blocks = np.array([[0b1011, 0], [0b110000, 1]], dtype=np.uint64)
    return Material(
        blocks,
        np.array([0.9, 1 / 3]),
        ({0: 1.0, 1: 0.6, 3: 1 / 3}, {4: 1.0, 5: 1 / 7, 64: 0.75}),
    )


def test_material_round_trip_is_exact(tmp_path: Path) -> None:
    """Blocks, support and every inclusion come back bit-identical."""
    original = _material()
    save_material(tmp_path / "side.npz", original)
    back = load_material(tmp_path / "side.npz")
    assert np.array_equal(back.blocks, original.blocks)
    assert np.array_equal(back.supports, original.supports)
    # Equality, not approximate equality: these floats are rounded and exported.
    assert back.selections == original.selections


def test_material_round_trip_survives_an_empty_side(tmp_path: Path) -> None:
    """A side with no families round-trips rather than raising."""
    empty = Material(np.zeros((0, 2), dtype=np.uint64), np.zeros(0), ())
    save_material(tmp_path / "empty.npz", empty)
    back = load_material(tmp_path / "empty.npz")
    assert back.blocks.shape == (0, 2)
    assert back.selections == ()
    assert back.rows() == []


def test_rows_reports_size_and_support() -> None:
    """``rows`` counts set bits, not words, and pairs each with its own support."""
    rows = _material().rows()
    assert rows == [(3, 0.9), (3, round(1 / 3, 6))]


def test_cut_key_changes_with_either_parameter() -> None:
    """A different cap or cutoff is a different cache key, so neither overwrites the other."""
    assert cut_key(3125, 0.50) == "cap3125_inc050"
    assert cut_key(3125, 0.50) != cut_key(3125, 0.33)
    assert cut_key(3125, 0.50) != cut_key(2000, 0.50)


def test_strata_cover_every_size_once() -> None:
    """Every size from the minimum up has exactly one stratum."""
    for size in (3, 4, 5, 6, 7, 9, 10, 3125):
        assert 0 <= stratum_of(size) < len(STRATA)
    with pytest.raises(ValueError):
        stratum_of(2)


def test_floor_never_falls_below_the_declared_m() -> None:
    """A stratum where the null is empty still takes the declared m as its threshold.

    The floor is the FDR-solved number; the threshold applied is ``max(declared_m, floor)``, so a
    quiet null cannot license keeping a family the declared rule would have dropped.
    """
    real = [(3, 0.9), (3, 0.1), (4, 0.8)]
    solved = solve(real, [[], []])
    assert solved[0]["floor"] == 0.0
    assert solved[0]["effective"] == DECLARED_M


def test_floor_rises_above_the_declared_m_when_the_null_demands_it() -> None:
    """A null reaching above m pushes the threshold up, not down."""
    real = [(3, 0.95)] * 100
    nulls = [[(3, 0.5)]] * 10
    solved = solve(real, nulls)
    assert solved[0]["floor"] == 0.5
    assert solved[0]["effective"] == 0.5
    assert solved[0]["calibration_fdr"] <= 0.01


def test_a_stratum_the_null_dominates_is_dropped_not_clamped() -> None:
    """When no candidate meets the FDR target the stratum is refused, never clamped.

    The candidate floors are the null's own support values, so a floor can never be set above
    anything the null achieved. If even the null's highest value leaves too many false families per
    real one, the stratum cannot be admitted -- and the build says so rather than quietly clamping
    to the declared m, which would admit it on no evidence.
    """
    real = [(3, 0.95)] * 50
    nulls = [[(3, 0.5), (3, 0.6), (3, 0.7)]] * 10
    solved = solve(real, nulls)
    assert solved[0]["floor"] is None
    assert solved[0]["effective"] is None
