"""Matching the FINAL THEMES of two builds -- the statistic the RUNS rule is stated over.

The 2 Oct ladder measured the raw grouping pool instead and its verdict did not follow, so this
statistic is tested directly rather than trusted: the unit, the threshold and the two directions
are each pinned, and the frozen build's recorded test 9 figures are reproduced from disk.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pytest  # noqa: E402

from theme_match import best_matches, read_themes, summarise  # noqa: E402


def _build(directory: Path, themes: dict[str, list[str]]) -> Path:
    """Write a minimal build directory holding just what the statistic reads.

    Args:
        directory: Where to write it.
        themes: Theme id to member keys.

    Returns:
        The directory.
    """
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "nodes.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["node", "size", "support", "parents"])
        for node, members in themes.items():
            writer.writerow([node, len(members), "1.0000", ""])
    with (directory / "members.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["node", "key", "source", "name", "n_genes", "inclusion"])
        for node, members in themes.items():
            for key in members:
                writer.writerow([node, key, "go", "", "1", "1.0000"])
    return directory


def test_identical_builds_match_completely(tmp_path: Path) -> None:
    """Two copies of one build match at 1.0, in both directions."""
    themes = {"n0": ["a", "b", "c"], "n1": ["d", "e", "f", "g"]}
    left = read_themes(_build(tmp_path / "l", themes))
    right = read_themes(_build(tmp_path / "r", themes))
    assert summarise(best_matches(left, right))["share_ge_0.70"] == 1.0
    assert summarise(best_matches(right, left))["share_ge_0.70"] == 1.0


def test_the_two_directions_can_disagree(tmp_path: Path) -> None:
    """A build whose themes all match is not the same as a build that matches all of them.

    The right-hand build here holds one extra theme with no counterpart. Forward every left theme
    finds a partner; backward the extra one does not -- which is why the rule has to say which
    direction it means, and why both are reported.
    """
    left = read_themes(_build(tmp_path / "l", {"n0": ["a", "b", "c"]}))
    right = read_themes(_build(tmp_path / "r", {"n0": ["a", "b", "c"], "n1": ["x", "y", "z"]}))
    assert summarise(best_matches(left, right))["share_ge_0.70"] == 1.0
    assert summarise(best_matches(right, left))["share_ge_0.70"] == 0.5


def test_the_threshold_decides_a_known_pair(tmp_path: Path) -> None:
    """{a,b,c,d} against {a,b,c,d,e} is Jaccard 0.8: matched at 0.70, not at 0.90."""
    left = read_themes(_build(tmp_path / "l", {"n0": ["a", "b", "c", "d"]}))
    right = read_themes(_build(tmp_path / "r", {"n0": ["a", "b", "c", "d", "e"]}))
    got = summarise(best_matches(left, right))
    assert got["share_ge_0.50"] == 1.0
    assert got["share_ge_0.70"] == 1.0
    assert got["share_ge_0.90"] == 0.0


def test_a_theme_with_no_members_is_an_error(tmp_path: Path) -> None:
    """Silently scoring it 0 would drag the share down and look like instability."""
    directory = _build(tmp_path / "l", {"n0": ["a", "b", "c"]})
    with (directory / "nodes.tsv").open("a", encoding="utf-8") as handle:
        handle.write("n9\t0\t1.0000\t\n")
    with pytest.raises(ValueError, match="no members"):
        read_themes(directory)


@pytest.mark.skipif(
    not (REPO_ROOT / "data/ontology/v0.2/recurrent_dag_c50_seed1/nodes.tsv").is_file(),
    reason="the seed-1 twin of the frozen build is gitignored and may not be present",
)
def test_reproduces_the_frozen_builds_recorded_test_9() -> None:
    """The frozen 1,850's test 9, as recorded in OPEN.md: mean 0.862, median 0.909, 53.2% at 0.9.

    Reproducing three independently recorded figures from the build directories is what licenses
    reading the fourth -- the 86.9% at >= 0.70 the RUNS rule is stated over -- off the same run.
    """
    out = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/theme_match.py"),
         str(REPO_ROOT / "data/ontology/v0.2/recurrent_dag_c50"),
         str(REPO_ROOT / "data/ontology/v0.2/recurrent_dag_c50_seed1"),
         "--out", "/dev/stdout"],
        capture_output=True, text=True, check=True, cwd=REPO_ROOT,
    )
    blob = out.stdout[out.stdout.index("{"):out.stdout.rindex("}") + 1]
    got = json.loads(blob)
    assert got["forward"]["themes"] == 800
    assert got["forward"]["mean"] == pytest.approx(0.862, abs=0.0005)
    assert got["forward"]["median"] == pytest.approx(0.909, abs=0.0005)
    assert got["forward"]["share_ge_0.90"] == pytest.approx(0.532, abs=0.0005)
    # The figure of record for the rule, and the worse direction beside it.
    assert got["forward"]["share_ge_0.70"] == pytest.approx(0.869, abs=0.0005)
    assert got["worse_direction"] == pytest.approx(0.859, abs=0.0005)
