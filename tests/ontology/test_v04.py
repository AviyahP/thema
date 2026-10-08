"""v0.4 must not drift from v0.3 except where a stage was deliberately removed.

The expensive proof is the built-directory comparison in ``scripts/v04_run.py --all-stages-on
--verify``. These are the cheap guards that run on every ``pytest``: that every parameter v0.4
shares with v0.3 still has v0.3's value, and that the pipeline's shape is what the ablation
decided. A parameter drifting silently is the failure these exist to catch -- a truncated size-cap
share gave 3,124 against v0.3's 3,125 while this file was being written.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from thema.ontology import v04

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


def test_shared_parameters_match_v03() -> None:
    """Every knob v0.4 kept from v0.3 still holds v0.3's value."""
    import build_10770
    import cut_trees

    assert v04.THETA == cut_trees.THETA
    assert v04.MIN_SIZE == cut_trees.MIN_SIZE
    assert v04.INCLUSION_CUT == build_10770.INCLUSION_CUT
    assert v04.STRATA == build_10770.STRATA
    assert v04.MAX_FDR_OVERALL == build_10770.MAX_FDR_OVERALL
    assert v04.MAX_FDR_STRATUM == build_10770.MAX_FDR_STRATUM


def test_legacy_constants_match_the_frozen_build() -> None:
    """The values ``legacy`` restores are v0.3's, including the exact cap."""
    import cut_trees
    from thema.ontology.consensus import DEFAULT_STRAY

    assert v04.LEGACY_TOL == cut_trees.TOL
    assert v04.LEGACY_STRAY == DEFAULT_STRAY
    assert v04.LEGACY_CAP_SHARE == cut_trees.CAP_SHARE
    assert v04.cap_for(10770) == cut_trees.cap_for(10770) == 3125


def test_stage_list_is_what_the_ablation_decided() -> None:
    """Three stages kept, four removed, and each kept stage states its number."""
    assert [s.name for s in v04.STAGES] == [
        "completion", "greedy seed absorption", "per-size support floors"]
    assert all(any(c.isdigit() for c in s.why) for s in v04.STAGES)
    removed = v04.parameters(10770)["removed_stages"]
    assert removed == ["size cap", "TOL extras-only rule", "STRAY", "partial containment"]
    assert v04.parameters(10770, legacy=True)["removed_stages"] == []


def test_removed_stages_are_off_in_the_parameters() -> None:
    """v0.4 records no cap, no stray and no tol; ``legacy`` records v0.3's."""
    plain = v04.parameters(10770)
    assert plain["size_cap"] is None and plain["stray"] == 0.0 and plain["tol"] == 0.0
    old = v04.parameters(10770, legacy=True)
    assert old["size_cap"] == 3125 and old["stray"] == 0.10 and old["tol"] == 0.15
    assert plain["containment"] == old["containment"] == "strict"


def test_settings_carry_tol_only_in_legacy() -> None:
    """``TOL`` is inert in v0.3 but must still be reproduced exactly in legacy mode."""
    assert v04.settings_for(200)["tol"] == 0.0
    assert v04.settings_for(200, legacy=True)["tol"] == v04.LEGACY_TOL
    assert v04.settings_for(200)["theta"] == v04.THETA


def test_stratum_of_covers_every_size_above_min() -> None:
    """Every size at or above ``MIN_SIZE`` lands in exactly one stratum."""
    assert v04.stratum_of(2) == -1
    for size in (3, 4, 5, 6, 7, 8, 9, 10, 1000, 10770):
        index = v04.stratum_of(size)
        assert 0 <= index < len(v04.STRATA)
        low, high = v04.STRATA[index]
        assert low <= size <= high


def test_gate_refuses_a_stratum_with_no_floor() -> None:
    """A missing floor admits nothing, so a calibration gap cannot open the gate."""
    solved = [{"effective": 0.5}, {"effective": None}]
    rows = [(3, 0.9), (3, 0.4), (4, 1.0)]
    assert v04.gate(rows, solved).tolist() == [True, False, False]


def test_gate_is_inclusive_at_the_floor() -> None:
    """Support exactly at the floor passes, matching v0.3's comparison."""
    assert v04.gate([(3, 0.33)], [{"effective": 0.33}]).tolist() == [True]


def test_material_rows_are_size_and_support() -> None:
    """``Material.rows`` pairs each candidate's popcount with its support."""
    blocks = np.array([[0b111, 0], [0b1, 0b1]], dtype=np.uint64)
    got = v04.Material(blocks=blocks, supports=np.array([0.9, 0.4]), pool=7)
    assert got.rows() == [(3, 0.9), (2, 0.4)]


@pytest.mark.parametrize("legacy", [False, True])
def test_parameters_name_the_method(legacy: bool) -> None:
    """The manifest says which pipeline produced the build."""
    name = v04.parameters(10770, legacy=legacy)["method"]
    assert name == ("v0.4-legacy-all-stages" if legacy else "v0.4")
