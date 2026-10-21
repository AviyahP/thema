"""Part A's measures: the bands, the size-factor rule and the blind-input discipline.

The measures are simple but two of their details decide the answer, so both are asserted: redundancy
compares only themes whose sizes are within a factor of 1.5 -- without that a theme would be called
a near-copy of something three times its size -- and the reading items must carry nothing that
identifies their build, which is what makes the reading blind.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import m_vs_o50s_inputs as mv

OUT = Path("data/experiments/m_vs_o50s_2026-10-19")


def test_the_bands_are_the_declared_four() -> None:
    assert mv.BANDS == ((10, 19), (20, 49), (50, 199), (200, 10 ** 9))
    assert mv.band_of(9) is None, "the populations start at 10 pathways"
    assert mv.band_of(10) == "10-19"
    assert mv.band_of(49) == "20-49"
    assert mv.band_of(199) == "50-199"
    assert mv.band_of(10 ** 6) == "200+"


def test_the_declared_constants_are_what_the_prompt_says() -> None:
    assert mv.SAME == 0.90
    assert mv.NEAR == 0.80
    assert mv.SIZE_FACTOR == 1.5
    assert mv.WEAK == 0.02
    assert mv.PER_BAND == 15
    assert mv.SEED == 20261019


def _pack(groups: dict[str, set[str]]) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Pack a tiny fixture."""
    keys = sorted({k for v in groups.values() for k in v})
    index = {k: i for i, k in enumerate(keys)}
    return mv.pack(groups, index, max((len(keys) + 63) // 64, 1))


def test_best_against_finds_the_closest_theme_in_the_other_build() -> None:
    mine_ids, mine, mine_sz = _pack({"a": {"p1", "p2", "p3"}})
    other_ids, other, other_sz = _pack({"x": {"p1"}, "y": {"p1", "p2", "p3"},
                                        "z": {"p9"}})
    del mine_ids
    pick, score = mv.best_against(mine[0], int(mine_sz[0]), other, other_sz)
    assert other_ids[pick] == "y"
    assert score == pytest.approx(1.0)


def test_best_against_handles_an_empty_other_build() -> None:
    _ids, mine, sizes = _pack({"a": {"p1"}})
    assert mv.best_against(mine[0], int(sizes[0]), np.zeros((0, 1), dtype=np.uint64),
                           np.zeros(0, dtype=np.int64)) == (-1, 0.0)


def test_redundancy_ignores_a_partner_outside_the_size_factor() -> None:
    """A theme three times the size is not a near-copy, however much it contains."""
    groups = {"small": {f"p{i}" for i in range(10)},
              "huge": {f"p{i}" for i in range(30)}}
    ids, stack, sizes = _pack(groups)
    got = mv.redundancy(ids, stack, sizes)
    assert got["small"] == ("", 0.0), "30 is outside 10 x 1.5, so there is no partner"
    assert got["huge"] == ("", 0.0)


def test_redundancy_finds_a_partner_inside_the_size_factor() -> None:
    groups = {"a": {f"p{i}" for i in range(10)},
              "b": {f"p{i}" for i in range(1, 12)},
              "far": {f"q{i}" for i in range(10)}}
    ids, stack, sizes = _pack(groups)
    got = mv.redundancy(ids, stack, sizes)
    assert got["a"][0] == "b"
    assert got["b"][0] == "a"
    assert got["a"][1] == pytest.approx(9 / 12)
    assert got["far"][1] == pytest.approx(0.0), "no shared pathway, so J is 0"


def test_floor_for_reads_the_stratum_the_theme_was_gated_by() -> None:
    import o50s_build as o50s

    floors = [{"effective": None}] * 5 + [{"effective": 0.03}] + [{"effective": 0.01}] * 7
    label, floor = mv.floor_for(15, floors, o50s.O50S_STRATA)
    assert (label, floor) == ("10-19", 0.03)
    label, floor = mv.floor_for(5000, floors, o50s.O50S_STRATA)
    assert (label, floor) == ("1280+", 0.01)
    assert mv.floor_for(1, floors, o50s.O50S_STRATA) == ("", None)


needs_out = pytest.mark.skipif(
    not (OUT / "measures.json").exists(),
    reason="Part A has not run; run scripts/m_vs_o50s_inputs.py")


@pytest.fixture(scope="module")
def produced() -> dict:
    """What Part A wrote."""
    with (OUT / "redundancy.tsv").open(encoding="utf-8") as handle:
        red = list(csv.DictReader(handle, delimiter="\t"))
    with (OUT / "support.tsv").open(encoding="utf-8") as handle:
        sup = list(csv.DictReader(handle, delimiter="\t"))
    return {"measures": json.loads((OUT / "measures.json").read_text()),
            "index": json.loads((OUT / "index.json").read_text()),
            "redundancy": red, "support": sup}


@needs_out
def test_120_items_were_drawn_15_per_band_per_side(produced: dict) -> None:
    measures = produced["measures"]
    assert measures["n_drawn"] == 120
    assert measures["short_bands"] == [], "every band had at least 15 unique themes"
    assert len(produced["index"]) == 120
    assert sorted(produced["index"]) == [f"T{i:03d}" for i in range(1, 121)]


@needs_out
def test_the_reading_items_carry_nothing_that_identifies_a_build(produced: dict) -> None:
    """The point of the exercise: no build label, node id, theme name or support.

    Asserted structurally rather than by substring, because a substring scan for "node" matches
    real pathway names -- *atrioventricular node development* among them. Every non-blank line
    must be either the item header or a ``name [source]`` member line, which leaves nowhere for an
    identifying mark to hide.
    """
    import re

    nodes = {row["node"] for row in produced["redundancy"]}
    header = re.compile(r"^## T\d{3}  \(\d+ pathways\)$")
    member = re.compile(r"^.+ \[[a-z0-9]+\]$")
    sources = {row.split()[-1] for path in (OUT / "read_inputs").glob("T_b*.md")
               for row in path.read_text().splitlines() if member.match(row)}
    for path in sorted((OUT / "read_inputs").glob("T_b*.md")):
        text = path.read_text(encoding="utf-8")
        assert "O50s" not in text and "thema_L" not in text, path
        for line in text.splitlines():
            if not line.strip():
                continue
            assert header.match(line) or member.match(line), (path, line)
        # A node id would have to appear as a whole word; pathway names never contain one.
        leaked = sorted(n for n in nodes if re.search(rf"\b{re.escape(n)}\b", text))
        assert not leaked, (path, leaked[:5])
    # The source tags come from pathways.tsv rather than a hardcoded list, so a new source
    # would widen this test instead of breaking it.
    with Path("data/pathways.tsv").open(encoding="utf-8") as handle:
        real = {f"[{row['source']}]" for row in csv.DictReader(handle, delimiter="\t")}
    assert sources <= real, sorted(sources - real)


@needs_out
def test_every_item_appears_once_and_is_never_split(produced: dict) -> None:
    seen: list[str] = []
    for path in sorted((OUT / "read_inputs").glob("T_b*.md")):
        here = [line.split()[1] for line in path.read_text().splitlines()
                if line.startswith("## T")]
        seen.extend(here)
    assert sorted(seen) == sorted(produced["index"]), "each theme in exactly one batch"
    assert len(seen) == len(set(seen))


@needs_out
def test_each_item_lists_exactly_its_members_sorted_by_name(produced: dict) -> None:
    sizes = produced["index"]
    for path in sorted((OUT / "read_inputs").glob("T_b*.md")):
        current, count = None, 0
        for line in path.read_text().splitlines() + ["## Tzzz  (0 pathways)"]:
            if line.startswith("## T"):
                if current is not None:
                    assert count == sizes[current], (current, count, sizes[current])
                current, count = line.split()[1], 0
                if current == "Tzzz":
                    break
            elif line.strip():
                assert line.rstrip().endswith("]"), line
                count += 1


@needs_out
def test_the_key_is_separate_from_the_blind_inputs() -> None:
    key = OUT / "KEY_DO_NOT_SHARE_m_vs_o50s.json"
    assert key.is_file(), "the key must exist"
    assert not list((OUT / "read_inputs").glob("*KEY*")), "and never inside read_inputs"
    import subprocess
    got = subprocess.run(["git", "check-ignore", str(key)], capture_output=True, text=True)
    assert got.returncode == 0, "the key must be gitignored"


@needs_out
def test_redundancy_rows_cover_every_theme_of_ten_or_more(produced: dict) -> None:
    rows = produced["redundancy"]
    assert len(rows) == 9015
    for row in rows:
        assert row["build"] in ("O50s", "M")
        assert row["unique"] in ("yes", "no")
        assert int(row["size"]) >= 10
        assert mv.band_of(int(row["size"])) == row["band"]
        assert 0.0 <= float(row["best_j"]) <= 1.0


@needs_out
def test_support_rows_are_the_unique_themes_only(produced: dict) -> None:
    rows = produced["support"]
    unique = {(r["build"], r["node"]) for r in produced["redundancy"] if r["unique"] == "yes"}
    assert {(r["build"], r["node"]) for r in rows} == unique
    assert len(rows) == len(unique) == 6776
