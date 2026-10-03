"""The freeze table: the shape figures a build is reported by.

The nine figures this reproduces from the frozen 1,850's `FROZEN.md` are pinned, because the whole
point of a committed freeze table is that two builds are reported the same way. The two it does NOT
reproduce -- straddlers and GO BP's shape -- are pinned to THIS script's values with the discrepancy
named, so a later change to either is visible rather than silent. See `docs/debt.md`.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from freeze_table import ancestors_of, depth_of, straddlers  # noqa: E402

FROZEN = REPO_ROOT / "data/ontology/v0.2/recurrent_dag_c50"


def test_depth_is_counted_in_edges() -> None:
    """A forest of roots is depth 0; a single chain of three nodes is depth 2.

    Nodes rather than edges gave 13 where FROZEN.md records 12, and the edge convention reproduces
    all three of its depth figures.
    """
    assert depth_of({}) == 0
    assert depth_of({"a": [], "b": []}) == 0
    assert depth_of({"a": [], "b": ["a"], "c": ["b"]}) == 2


def test_depth_takes_the_longest_path_through_a_diamond() -> None:
    """With two routes to a node, depth is the longer one."""
    parents = {"r": [], "x": ["r"], "y": ["x"], "z": ["r", "y"]}
    assert depth_of(parents) == 3


def test_ancestors_are_transitive_and_survive_a_cycle() -> None:
    """A cycle must not recurse forever; a malformed DAG is reported, not hung on."""
    assert ancestors_of({"a": [], "b": ["a"], "c": ["b"]})["c"] == {"a", "b"}
    got = ancestors_of({"a": ["b"], "b": ["a"]})
    assert isinstance(got, dict)


def test_a_pathway_nested_in_its_own_parent_does_not_straddle() -> None:
    """Membership of a theme and of that theme's parent is what the hierarchy is for."""
    parents = {"p": [], "c": ["p"]}
    members = {"p": ["x", "y", "z"], "c": ["x"]}
    assert straddlers(members, ancestors_of(parents)) == 0


def test_a_pathway_in_two_unrelated_themes_straddles() -> None:
    """Two themes, neither containing the other, is exactly the straddling case."""
    parents = {"a": [], "b": []}
    members = {"a": ["x", "y"], "b": ["x", "z"]}
    assert straddlers(members, ancestors_of(parents)) == 1


def test_straddling_needs_one_unrelated_pair_not_all_pairs() -> None:
    """A pathway in a chain plus one unrelated theme straddles."""
    parents = {"p": [], "c": ["p"], "other": []}
    members = {"p": ["x", "y"], "c": ["x"], "other": ["x", "z"]}
    assert straddlers(members, ancestors_of(parents)) == 1


@pytest.mark.skipif(not (FROZEN / "nodes.tsv").is_file(),
                    reason="the frozen 1,850 build is not present")
class TestAgainstTheFrozen1850:
    """Pin the freeze table against the build whose FROZEN.md it has to match."""

    @staticmethod
    def _report() -> dict:
        import json
        import subprocess
        out = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/freeze_table.py"), str(FROZEN),
             "--out", "/dev/stdout"],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT,
        )
        return json.loads(out.stdout[out.stdout.index("{"):out.stdout.rindex("}") + 1])

    def test_reproduces_the_nine_recorded_figures(self) -> None:
        """Themes, roots, multi-parent, depth, median size, largest theme and root, placement."""
        got = self._report()
        assert got["themes"] == 800
        assert got["roots"] == 61
        assert got["roots_share"] == pytest.approx(0.076, abs=0.0005)
        assert got["multi_parent"] == 176
        assert got["multi_parent_share"] == pytest.approx(0.220, abs=0.0005)
        assert got["max_depth"] == 12
        assert got["median_theme_size"] == 8
        assert got["largest_theme"] == 819
        assert got["largest_root_direct_members"] == 64
        assert (got["placed"], got["unplaced_strict"], got["root_only"],
                got["effectively_unplaced"]) == (1831, 19, 106, 125)

    def test_pins_the_two_figures_that_do_not_reproduce(self) -> None:
        """FROZEN.md records 682 straddlers and GO BP at 20%/31%. These are what we compute.

        Pinned so the discrepancy stays visible: if a later change moves either, that is a change to
        the definition and must be decided, not absorbed.
        """
        got = self._report()
        assert got["straddlers"] == 1239          # FROZEN.md records 682
        go = got["test_2"]["go_bp"]
        assert go["roots_share"] == pytest.approx(0.0, abs=0.001)      # FROZEN.md records 20%
        assert go["multi_parent_share"] == pytest.approx(0.508, abs=0.002)  # records 31%
        assert int(go["depth"]) == 16             # this one DOES reproduce
        assert got["test_2_verdict_withheld"]

    def test_reactome_reference_reproduces(self) -> None:
        """All three Reactome figures match FROZEN.md's 1%, 11, 1%."""
        reactome = self._report()["test_2"]["reactome"]
        assert reactome["roots_share"] == pytest.approx(0.010, abs=0.002)
        assert int(reactome["depth"]) == 11
        assert reactome["multi_parent_share"] == pytest.approx(0.012, abs=0.002)
