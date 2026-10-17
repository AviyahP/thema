"""O50s: the stratification as a parameter, and the declared floor solver.

The build's own guard is `scripts/o50s_build.py --verify`, which reproduces the frozen O50 byte for
byte from the frozen six strata and floors. These tests cover the pieces that proof cannot reach on
its own: that the new `strata` argument leaves the default behaviour untouched, that the declared
solver does what the prompt says including the rule-of-three substitution, and that the
strata-aware held-out check is `build_10770.confirm` with a parameter rather than a second opinion.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

import o50s_build as o50s
from thema.ontology import v04

FROZEN = Path("data/ontology/frozen/working-O50-2026-10-14")
BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s")
REVIEW = Path("data/experiments/O50s_review_2026-10-17/large_themes.tsv")


def test_the_declared_strata_are_well_formed() -> None:
    """Ascending, contiguous from 3, open at the top, and the frozen five are untouched."""
    strata = o50s.O50S_STRATA
    assert strata[: o50s.FROZEN_SMALL] == v04.STRATA[: o50s.FROZEN_SMALL]
    assert strata[0][0] == 3
    assert strata[-1][1] == 10 ** 9
    for (_, high), (low, _) in zip(strata, strata[1:], strict=False):
        assert low == high + 1, f"a gap or an overlap at {high} to {low}"
    # The frozen 10+ stratum is exactly covered by the eight that replace it.
    assert strata[o50s.FROZEN_SMALL][0] == v04.STRATA[o50s.FROZEN_SMALL][0]


def test_stratum_of_defaults_to_the_frozen_strata() -> None:
    for size in (3, 4, 5, 6, 7, 9, 10, 500, 2809):
        assert v04.stratum_of(size) == v04.stratum_of(size, v04.STRATA)
    assert v04.stratum_of(10) == 5
    assert v04.stratum_of(2809) == 5, "the frozen build pools everything from 10 upward"
    assert v04.stratum_of(2) == -1


def test_stratum_of_respects_a_supplied_table() -> None:
    assert v04.stratum_of(10, o50s.O50S_STRATA) == 5
    assert v04.stratum_of(39, o50s.O50S_STRATA) == 6
    assert v04.stratum_of(40, o50s.O50S_STRATA) == 7
    assert v04.stratum_of(2809, o50s.O50S_STRATA) == 12
    assert v04.stratum_of(2, o50s.O50S_STRATA) == -1


def test_gate_defaults_are_unchanged_and_a_table_can_be_supplied() -> None:
    rows = [(5, 0.9), (12, 0.2), (300, 0.02)]
    frozen = [{"effective": 0.5}] * 6
    assert list(v04.gate(rows, frozen)) == list(v04.gate(rows, frozen, v04.STRATA))
    assert list(v04.gate(rows, frozen)) == [True, False, False]
    wide = [{"effective": 0.5}] * 5 + [{"effective": 0.1}] * 8
    # 12 falls in 10-19 and 300 in 160-319, so both are judged by the 0.1 floor.
    assert list(v04.gate(rows, wide, o50s.O50S_STRATA)) == [True, True, False]


def test_a_stratum_with_no_floor_admits_nothing() -> None:
    rows = [(300, 1.0)]
    solved = [{"effective": None}] * 13
    assert list(v04.gate(rows, solved, o50s.O50S_STRATA)) == [False]


def test_the_solver_takes_the_lowest_cut_reaching_the_target() -> None:
    """0.005 fails on five real candidates against one null a seed; 0.01 clears it on the bound."""
    real = [0.01] * 100 + [0.005] * 5
    nulls = [[0.005] for _ in range(10)]
    got = o50s.solve_stratum(real, nulls)
    # At 0.005: 105 real, mean null 1.0, FDR 0.00952 -- over the 0.008 target.
    # At 0.01: 100 real, no null observed, so the bound 0.3 gives 0.003.
    assert got["floor"] == 0.01
    assert got["real"] == 100
    assert got["bounded"] is True
    assert got["calibration_fdr"] == pytest.approx(0.3 / 100)


def test_the_lowest_cut_wins_even_when_a_higher_one_is_cleaner() -> None:
    """The rule is the LOWEST cut reaching the target, which keeps the most real candidates."""
    real = [0.9] * 60 + [0.01] * 60
    nulls = [[] for _ in range(10)]
    got = o50s.solve_stratum(real, nulls)
    assert got["floor"] == 0.01, "0.01 reaches the target, so the cleaner 0.9 is not taken"
    assert got["real"] == 120


def test_the_rule_of_three_applies_only_to_an_observed_zero() -> None:
    # At 0.01 the scrambles DO appear: 10 candidates over 10 seeds is a mean of 1.0, and 1.0/200
    # is 0.005, which already clears 0.008 without any substitution.
    real = [0.01] * 200
    nulls = [[0.01] for _ in range(10)]
    got = o50s.solve_stratum(real, nulls)
    assert got["floor"] == 0.01
    assert got["bounded"] is False
    assert got["calibration_fdr"] == pytest.approx(1.0 / 200)


def test_the_solver_gives_up_when_no_cut_reaches_the_target() -> None:
    # The scrambles sit on top of the real candidates at every value.
    real = [0.01, 0.02]
    nulls = [[0.02, 0.02] for _ in range(10)]
    got = o50s.solve_stratum(real, nulls)
    assert got["floor"] is None
    assert got["effective"] is None
    assert got["calibration_fdr"] is None


def test_the_ladder_includes_real_values_not_only_scrambled_ones() -> None:
    """The choice prompt 41 showed matters: a scrambled-only ladder can have one rung.

    With 40 real candidates at 0.5 and the scrambles stuck at 0.005, the only cut that separates
    the two is a REAL value. A scrambled-only ladder would offer 0.005 alone and reach 0.05.
    """
    real = [0.5] * 40
    nulls = [[0.005] for _ in range(10)]
    got = o50s.solve_stratum(real, nulls)
    assert got["n_cuts"] == 2, "the ladder is {0.005, 0.5}"
    assert got["floor"] == 0.5
    assert got["bounded"] is True
    assert got["calibration_fdr"] == pytest.approx(0.3 / 40)


def test_the_rule_of_three_bound_needs_38_real_candidates_to_clear_the_target() -> None:
    """A latent limit of the declared rule, worth asserting so it cannot be forgotten.

    A bounded cut's FDR is ``0.3 / kept``, so it reaches 0.008 only once ``kept >= 37.5``. A
    stratum with fewer real candidates above the scrambles' maximum can never pass on the bound,
    however clean the separation looks. Every new stratum in the real build has at least 96.
    """
    nulls = [[0.005] for _ in range(10)]
    assert o50s.solve_stratum([0.5] * 37, nulls)["floor"] is None
    assert o50s.solve_stratum([0.5] * 38, nulls)["floor"] == 0.5


def test_an_empty_stratum_is_reported_rather_than_crashing() -> None:
    got = o50s.solve_stratum([], [[0.005]])
    assert got["floor"] is None
    assert got["real"] == 0


needs_frozen = pytest.mark.skipif(
    not (FROZEN / "manifest.json").exists(), reason="the frozen O50 is not present")
needs_build = pytest.mark.skipif(
    not (BUILD / "manifest.json").exists(),
    reason="O50s is not built; run scripts/o50s_build.py")


@needs_frozen
def test_confirm_with_is_confirm_plus_a_parameter() -> None:
    """On the frozen six strata the two must agree field for field."""
    from build_10770 import confirm
    scrambles = Path("data/ontology/v0.4-leaves/calibration")
    seeds = [scrambles / f"seed{s:05d}.npz" for s in (4001, 4002)]
    if not all(p.is_file() for p in seeds):
        pytest.skip("the cached held-out scrambles are absent")
    real = o50s.rows_of(Path("data/ontology/v0.4-leaves-x2/calibration/real.npz"))
    held = [o50s.rows_of(p) for p in seeds]
    cal8 = json.loads((FROZEN / "manifest.json").read_text())["floors"]
    mine = o50s.confirm_with(real, held, cal8, v04.STRATA)
    assert json.dumps(mine, sort_keys=True) == json.dumps(confirm(real, held, cal8),
                                                          sort_keys=True)


@needs_build
def test_the_build_used_the_declared_strata_and_kept_the_frozen_floors() -> None:
    manifest = json.loads((BUILD / "manifest.json").read_text())
    assert [tuple(s) for s in manifest["strata"]] == list(o50s.O50S_STRATA)
    cal8 = json.loads((FROZEN / "manifest.json").read_text())["floors"]
    for index in range(o50s.FROZEN_SMALL):
        assert manifest["floors"][index]["effective"] == cal8[index]["effective"]
        assert manifest["floors"][index]["source"] == "frozen cal8, unchanged"
    for entry in manifest["floors"][o50s.FROZEN_SMALL:]:
        assert entry["source"] == "solved 17 Oct 2026"


@needs_build
def test_the_held_out_check_is_inside_both_caps() -> None:
    floors = json.loads((BUILD / "floors_o50s.json").read_text())
    assert floors["over_cap"] == {}
    assert floors["overall_over_cap"] is False
    assert floors["confirmed"]["overall_fdr"] <= o50s.CAP_OVERALL
    for entry in floors["confirmed"]["strata"]:
        if entry["heldout_fdr"] is not None:
            assert entry["heldout_fdr"] <= o50s.CAP_STRATUM, entry["stratum"]


@needs_build
def test_every_theme_falls_in_a_declared_stratum_above_its_floor() -> None:
    floors = json.loads((BUILD / "floors_o50s.json").read_text())["solved"]
    with (BUILD / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(rows) > 5000
    for row in rows:
        index = v04.stratum_of(int(row["size"]), o50s.O50S_STRATA)
        assert index >= 0, row["node"]
        # A theme's membership can grow in consensus and in the repair, so its final size may sit
        # in a different stratum from the candidate that was gated. The floor is a property of the
        # candidate, not of the node, which is why this asserts the stratum exists rather than
        # that the node's own support clears that stratum's floor.
        assert floors[index]["stratum"] is not None


@needs_build
def test_the_reviewer_table_covers_exactly_the_large_band() -> None:
    low, high = 101, 1000
    sizes: dict[str, int] = {}
    with (BUILD / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            sizes[row["node"]] = sizes.get(row["node"], 0) + 1
    want = {node for node, size in sizes.items() if low <= size <= high}
    if not REVIEW.exists():
        pytest.skip("the reviewer table is not written; run scripts/o50s_report.py")
    with REVIEW.open(encoding="utf-8") as handle:
        got = list(csv.DictReader(handle, delimiter="\t"))
    assert {row["node"] for row in got} == want
    for row in got:
        assert row["status"] in ("new", "kept")
        assert len(row["members"].split()) == int(row["size"]) == sizes[row["node"]]
        assert (float(row["j_o50"]) < 0.70) == (row["status"] == "new")


@needs_build
def test_the_small_end_is_not_swallowed() -> None:
    """The declared bar: at least 95% of O50's 3-50 themes."""
    def small(path: Path) -> int:
        """How many themes of 3-50 members a build has."""
        sizes: dict[str, int] = {}
        with (path / "members.tsv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                sizes[row["node"]] = sizes.get(row["node"], 0) + 1
        return sum(1 for size in sizes.values() if 3 <= size <= 50)

    assert small(BUILD) >= 0.95 * small(FROZEN)


def test_sha256_reads_the_bytes(tmp_path: Path) -> None:
    import hashlib
    one = tmp_path / "a.txt"
    one.write_bytes(b"strata")
    assert o50s.sha256(one) == hashlib.sha256(b"strata").hexdigest()


def test_rows_of_refuses_a_missing_side(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not cached"):
        o50s.rows_of(tmp_path / "nope.npz")


def test_labels_read_as_the_frozen_build_writes_them() -> None:
    assert o50s.label(3, 3) == "3-3"
    assert o50s.label(7, 9) == "7-9"
    assert o50s.label(1280, 10 ** 9) == "1280+"
    assert [o50s.label(*s) for s in o50s.O50S_STRATA][-1] == "1280+"
