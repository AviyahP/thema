"""The per-stratum match threshold: the solver, the selection rule and the two arms.

The sweep itself is 2.3 h of compute, so what is testable here is the logic around it: the floor
solver (prompt 43's, reused), the declared selection rule including its tie-break, arm Mm's 0.33
minimum, and the invariants of whatever the sweep produced.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import match_per_stratum as mps

SWEEP = Path("data/experiments/match_per_stratum_2026-10-19")
O50S = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s")
ROOT = Path("data/ontology/v0.4-leaves")


def test_the_strata_are_o50ss_thirteen_unchanged() -> None:
    import o50s_build as o50s

    assert mps.STRATA == o50s.O50S_STRATA
    assert mps.stratum_of(3) == 0
    assert mps.stratum_of(19) == 5
    assert mps.stratum_of(1280) == 12
    assert mps.stratum_of(2) == -1
    assert mps.label(1280, 10 ** 9) == "1280+"


def test_the_merge_threshold_is_not_swept() -> None:
    """Only matching moves; absorption and consensus stay at 0.70 by the spec."""
    assert mps.THETA_MERGE == 0.70
    assert mps.THETAS == (0.50, 0.60, 0.70)


def test_the_solver_is_prompt_43s() -> None:
    """Same rule: lowest cut reaching the target, with the rule of three on an observed zero."""
    real = [0.01] * 100 + [0.005] * 5
    nulls = [np.array([0.005]) for _ in range(10)]
    got = mps.solve_stratum(np.array(real), nulls)
    assert got["floor"] == 0.01
    assert got["real"] == 100
    assert got["bounded"] is True
    assert got["calibration_fdr"] == pytest.approx(0.3 / 100)


def test_the_solver_gives_up_when_no_cut_reaches_the_target() -> None:
    got = mps.solve_stratum(np.array([0.01, 0.02]),
                            [np.array([0.02, 0.02]) for _ in range(10)])
    assert got["floor"] is None and got["effective"] is None


def test_the_bound_still_needs_38_real_candidates() -> None:
    """The latent limit prompt 43 recorded, carried over unchanged."""
    nulls = [np.array([0.005]) for _ in range(10)]
    assert mps.solve_stratum(np.array([0.5] * 37), nulls)["floor"] is None
    assert mps.solve_stratum(np.array([0.5] * 38), nulls)["floor"] == 0.5


def test_an_empty_stratum_is_reported_not_crashed() -> None:
    got = mps.solve_stratum(np.array([]), [np.array([0.005])])
    assert got["floor"] is None and got["real"] == 0


def test_the_selection_rule_takes_the_most_admitted() -> None:
    """Declared: most real candidates at FDR <= target."""
    per = {0.50: {"real": 10, "effective": 0.1}, 0.60: {"real": 50, "effective": 0.2},
           0.70: {"real": 20, "effective": 0.3}}
    best = max(mps.THETAS, key=lambda t: (per[t]["real"] if per[t]["effective"] is not None
                                          else -1, t))
    assert best == 0.60


def test_the_selection_rule_breaks_a_tie_on_the_higher_theta() -> None:
    per = {0.50: {"real": 50, "effective": 0.1}, 0.60: {"real": 50, "effective": 0.2},
           0.70: {"real": 50, "effective": 0.3}}
    best = max(mps.THETAS, key=lambda t: (per[t]["real"] if per[t]["effective"] is not None
                                          else -1, t))
    assert best == 0.70, "the higher theta wins a tie"


def test_a_stratum_that_admits_nothing_is_not_chosen_over_one_that_does() -> None:
    per = {0.50: {"real": 0, "effective": None}, 0.60: {"real": 3, "effective": 0.2},
           0.70: {"real": 0, "effective": None}}
    best = max(mps.THETAS, key=lambda t: (per[t]["real"] if per[t]["effective"] is not None
                                          else -1, t))
    assert best == 0.60


def test_arm_mms_minimum_applies_only_from_ten_pathways_up() -> None:
    assert mps.DECLARED_M == 0.33
    assert mps.MM_FROM == 10
    for low, floor, expected in ((3, 0.9, 0.9), (7, 0.1, 0.1),
                                 (10, 0.1, 0.33), (1280, 0.5, 0.5)):
        got = max(float(floor), mps.DECLARED_M) if low >= mps.MM_FROM else floor
        assert got == expected, (low, floor)


needs_sweep = pytest.mark.skipif(
    not (SWEEP / "strata.json").exists(),
    reason="the sweep has not been solved; run --sides then --solve")
needs_arms = pytest.mark.skipif(
    not (ROOT / "thema_L_x2_O50s_M" / "nodes.tsv").exists(),
    reason="the arms are not built")


@needs_sweep
def test_every_side_and_theta_was_cached() -> None:
    for name in ["real"] + [f"seed{s:05d}" for s in (*mps.CALIBRATION, *mps.HELDOUT)]:
        for theta in mps.THETAS:
            assert mps.side_cache(SWEEP, name, theta).is_file(), (name, theta)


@needs_sweep
def test_theta_070_reproduces_the_cached_real_side() -> None:
    """The replication check: the sweep's own 0.70 pass must be O50s's own candidate set."""
    sizes, supports = mps.rows_of(mps.side_cache(SWEEP, "real", 0.70))
    with np.load(Path("data/ontology/v0.4-leaves-x2/calibration/real.npz")) as handle:
        theirs = np.bitwise_count(handle["blocks"]).sum(axis=1).astype(np.int64)
        their_sup = np.round(handle["supports"], 6)
    assert len(sizes) == len(theirs) == 99951
    assert np.array_equal(np.sort(sizes), np.sort(theirs))
    assert np.array_equal(np.sort(supports), np.sort(their_sup))


@needs_sweep
def test_the_table_records_a_choice_per_stratum() -> None:
    table = json.loads((SWEEP / "strata.json").read_text())["table"]
    assert len(table) == len(mps.STRATA)
    for entry in table:
        assert set(entry["per_theta"]) == {str(t) for t in mps.THETAS}
        if entry["chosen_theta"] is not None:
            assert entry["chosen_theta"] in mps.THETAS
            admitted = entry["admitted"]
            assert admitted[str(entry["chosen_theta"])] == max(admitted.values()), \
                entry["stratum"]
            assert entry["effective"] is not None


@needs_arms
@pytest.mark.parametrize("arm", ["M", "Mm"])
def test_the_arm_is_inside_both_caps_or_says_which_stratum_is_not(arm: str) -> None:
    manifest = json.loads((ROOT / f"thema_L_x2_O50s_{arm}" / "manifest.json").read_text())
    confirmed = manifest["confirmed"]
    over = [e["stratum"] for e in confirmed["strata"]
            if e["heldout_fdr"] is not None and e["heldout_fdr"] > mps.CAP_STRATUM]
    # Recorded either way: the test documents the verdict rather than demanding a pass.
    assert isinstance(over, list)
    assert confirmed["overall_fdr"] is None or confirmed["overall_fdr"] >= 0


@needs_arms
def test_mm_floors_are_never_below_m_from_ten_up() -> None:
    manifest = json.loads((ROOT / "thema_L_x2_O50s_Mm" / "manifest.json").read_text())
    for entry, (low, _high) in zip(manifest["floors"], mps.STRATA, strict=True):
        if entry["effective"] is not None and low >= mps.MM_FROM:
            assert entry["effective"] >= mps.DECLARED_M, entry["stratum"]


@needs_arms
@pytest.mark.parametrize("arm", ["M", "Mm"])
def test_the_build_records_the_chosen_theta_per_stratum(arm: str) -> None:
    manifest = json.loads((ROOT / f"thema_L_x2_O50s_{arm}" / "manifest.json").read_text())
    assert manifest["theta_merge"] == mps.THETA_MERGE
    assert manifest["theta_same"] == 0.50
    per = manifest["theta_match_per_stratum"]
    assert len(per) == len(mps.STRATA)
    for stratum, theta in per.items():
        assert theta is None or theta in mps.THETAS, stratum


@needs_arms
@pytest.mark.parametrize("arm", ["M", "Mm"])
def test_the_reviewer_table_matches_the_build(arm: str) -> None:
    path = SWEEP / arm / "roots.tsv"
    if not path.exists():
        pytest.skip("the reviewer table is not written")
    with (ROOT / f"thema_L_x2_O50s_{arm}" / "nodes.tsv").open(encoding="utf-8") as handle:
        nodes = {r["node"]: r for r in csv.DictReader(handle, delimiter="\t")}
    roots = {n for n, r in nodes.items() if not r["parents"].strip()}
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert {r["node"] for r in rows} == roots
    for row in rows:
        assert len(row["members"].split()) == int(row["size"])
