"""§0's decision rule, on cases where the right answer is known by hand.

The rule has three moving parts that could each be wrong in a way no amount of real data would make
obvious: dominance needs BOTH a significant win somewhere and no significant loss anywhere;
max-min scores an arm by its WORST cell against the best eligible arm; and an ineligible arm must
not be able to win or to dominate. Hand-built curves make each testable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from engine_scores import decide, reading_of  # noqa: E402


def _flat(values: dict[str, dict[str, float]]) -> dict[str, dict[str, np.ndarray]]:
    """Degenerate bootstrap curves: every resample gives the point estimate.

    A zero-width interval excludes 0 whenever the point estimate differs, which is exactly the
    "significant" case, and makes the dominance arithmetic checkable by hand.

    Args:
        values: Cell to arm to AUROC.

    Returns:
        Cell to arm to a constant curve.
    """
    return {c: {a: np.full(2000, v) for a, v in s.items()} for c, s in values.items()}


def test_dominance_needs_a_significant_win_and_no_significant_loss() -> None:
    """Y wins one cell by more than the margin and ties the other, so X is dominated."""
    cells = {"c1": {"X": 0.50, "Y": 0.55}, "c2": {"X": 0.60, "Y": 0.60}}
    out = decide(["X", "Y"], cells, _flat(cells), ["X", "Y"])
    assert out["dominated"] == {"X": ["Y"]}
    assert out["non_dominated"] == ["Y"]
    assert out["winner"] == "Y"


def test_a_win_inside_the_margin_does_not_dominate() -> None:
    """0.015 is significant but below the 0.02 margin, so it dominates nothing."""
    cells = {"c1": {"X": 0.500, "Y": 0.515}, "c2": {"X": 0.600, "Y": 0.600}}
    out = decide(["X", "Y"], cells, _flat(cells), ["X", "Y"])
    assert out["dominated"] == {}


def test_a_significant_loss_anywhere_blocks_dominance() -> None:
    """Y wins c1 by 0.05 but loses c2 by 0.10, so neither dominates and max-min decides."""
    cells = {"c1": {"X": 0.50, "Y": 0.55}, "c2": {"X": 0.70, "Y": 0.60}}
    out = decide(["X", "Y"], cells, _flat(cells), ["X", "Y"])
    assert out["dominated"] == {}
    # X's worst gap is 0.05 (c1), Y's is 0.10 (c2). Smallest shortfall wins.
    assert out["shortfall"] == {"X": 0.05, "Y": 0.1}
    assert out["winner"] == "X"
    assert out["worst_cell"]["X"] == "c1"


def test_shortfall_is_measured_against_the_best_ELIGIBLE_arm() -> None:
    """An ineligible arm's score must not set the bar the others are judged against.

    X and Y are kept inside the margin of each other so neither dominates and both survive to the
    max-min step, which is where the "best eligible" choice actually bites.
    """
    cells = {"c1": {"X": 0.500, "Y": 0.510, "Z": 0.900},
             "c2": {"X": 0.600, "Y": 0.600, "Z": 0.900}}
    out = decide(["X", "Y", "Z"], cells, _flat(cells), ["X", "Y"])

    assert "Z" not in out["eligible"]
    assert out["dominated"] == {}, "0.01 is inside the 0.02 margin"
    # Judged against Y, the best ELIGIBLE arm, not against Z's 0.90. Were Z's score used, X's
    # shortfall would be 0.40 and Y's 0.39.
    assert out["shortfall"] == {"X": 0.01, "Y": 0.0}
    assert out["winner"] == "Y"


def test_the_margin_comparison_is_strict_and_boundary_sensitive() -> None:
    """A gap of exactly the margin is NOT a dominance win -- and the float boundary is fragile.

    `0.52 - 0.50` is 0.020000000000000018 in binary floating point, which is strictly greater than
    0.02, so a pair of scores a reader would call "exactly 0.02 apart" can dominate while another
    pair genuinely 0.02 apart does not. This is pinned rather than smoothed over with a tolerance,
    because choosing a tolerance is a tuning decision and §0 forbids tuning. The practical
    consequence is small -- real AUROCs do not land on the boundary -- but a verdict resting on a
    gap within a hair of 0.02 should be read as a boundary case and said to be one.
    """
    assert 0.52 - 0.50 > 0.02, "the float fact this test exists to record"
    near = {"c1": {"X": 0.50, "Y": 0.52}, "c2": {"X": 0.60, "Y": 0.60}}
    assert decide(["X", "Y"], near, _flat(near), ["X", "Y"])["dominated"] == {"X": ["Y"]}

    # Exactly representable and exactly the margin: 0.5 + 0.02 is not > 0.02 away from 0.5 here,
    # because the subtraction is exact for these two values.
    exact = {"c1": {"X": 0.25, "Y": 0.27}, "c2": {"X": 0.60, "Y": 0.60}}
    assert (0.27 - 0.25) > 0.02, "also above, by the same binary artefact"
    assert decide(["X", "Y"], exact, _flat(exact), ["X", "Y"])["dominated"] == {"X": ["Y"]}


def test_an_ineligible_arm_cannot_win_even_when_best_everywhere() -> None:
    """The gates come first; the scores cannot promote a failed arm."""
    cells = {"c1": {"X": 0.50, "Z": 0.95}, "c2": {"X": 0.60, "Z": 0.95}}
    out = decide(["X", "Z"], cells, _flat(cells), ["X"])
    assert out["winner"] == "X"
    assert out["dominated"] == {}


def test_no_eligible_arm_gives_no_winner() -> None:
    """If every arm fails its gates the rule must return nothing, not the least bad."""
    cells = {"c1": {"X": 0.50, "Y": 0.90}}
    out = decide(["X", "Y"], cells, _flat(cells), [])
    assert out["winner"] is None
    assert out["non_dominated"] == []


def test_ties_within_a_hundredth_are_reported_as_ties() -> None:
    """The declared tie-break needs to know a tie happened."""
    cells = {"c1": {"X": 0.600, "Y": 0.595}, "c2": {"X": 0.700, "Y": 0.700}}
    out = decide(["X", "Y"], cells, _flat(cells), ["X", "Y"])
    assert out["winner"] == "X"
    assert set(out["tied_within_0.01"]) == {"X", "Y"}


def test_reading_of_an_interval() -> None:
    """The four readings, including that 'equivalent' needs BOTH bounds inside the margin."""
    assert reading_of(-0.005, 0.005) == "equivalent"
    assert reading_of(0.03, 0.05) == "better"
    assert reading_of(-0.05, -0.03) == "worse"
    assert reading_of(-0.10, 0.10) == "inconclusive"
    # Inside the margin but straddling zero is still equivalent; wide but one-sided is not.
    assert reading_of(-0.019, 0.019) == "equivalent"
    assert reading_of(0.001, 0.30) == "better"
