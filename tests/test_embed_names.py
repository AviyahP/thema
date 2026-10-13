"""The theme-name embedding script's guards, checked without loading a model.

The guard that matters is :func:`assert_nothing_barred`. The names-test directory holds a blind
test's answer key and its blind and judged chunks, and this script is only allowed to read the one
names file. A rule nothing checks is a rule that erodes, so it is checked here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_script() -> object:
    """Import ``scripts/embed_theme_names.py`` as a module.

    Returns:
        The imported module.
    """
    path = REPO_ROOT / "scripts" / "embed_theme_names.py"
    spec = importlib.util.spec_from_file_location("embed_theme_names", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["embed_theme_names"] = module
    spec.loader.exec_module(module)
    return module


SCRIPT = load_script()


@pytest.mark.parametrize("name", [
    "KEY_DO_NOT_SHARE.json",
    "blind_07.json",
    "judged_12.json",
    "rubric_nameblind.md",
])
def test_a_barred_file_is_refused(name: str) -> None:
    with pytest.raises(ValueError, match="must not open"):
        SCRIPT.assert_nothing_barred([Path("somewhere") / name])


def test_the_names_file_is_allowed() -> None:
    SCRIPT.assert_nothing_barred([Path("x/theme_names_c85.tsv")])


def test_the_script_declares_one_input_and_checks_it() -> None:
    # The run opens exactly one declared file and passes it through the guard before reading.
    text = (REPO_ROOT / "scripts" / "embed_theme_names.py").read_text()
    assert "opened = [source]" in text, "the opened list must stay a single declared input"
    assert "assert_nothing_barred(opened)" in text, "the guard must actually be called"
    assert text.index("assert_nothing_barred(opened)") < text.index("read_names(source)"), (
        "the guard must run before the file is read"
    )


def test_every_barred_fragment_is_covered() -> None:
    # The four file shapes the brief bars, each matched by a fragment in BARRED.
    for name in ("KEY_DO_NOT_SHARE.json", "blind_01.json", "judged_15.json",
                 "rubric_nameblind.md"):
        assert any(fragment in name for fragment in SCRIPT.BARRED), f"{name} is not barred"


def test_names_are_read_in_file_order(tmp_path: Path) -> None:
    path = tmp_path / "names.tsv"
    path.write_text("node\tname\nn2\tbeta\nn1\talpha\nn3\tgamma\n", encoding="utf-8")
    nodes, names = SCRIPT.read_names(path)
    assert nodes == ["n2", "n1", "n3"], "rows must not be sorted"
    assert names == ["beta", "alpha", "gamma"]


def test_wrong_columns_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "names.tsv"
    path.write_text("node\tlabel\nn1\talpha\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected columns"):
        SCRIPT.read_names(path)


def test_an_empty_name_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "names.tsv"
    path.write_text("node\tname\nn1\talpha\nn2\t   \n", encoding="utf-8")
    with pytest.raises(ValueError, match="names are empty"):
        SCRIPT.read_names(path)


def test_the_census_reports_truncation() -> None:
    got = SCRIPT.census("probe", [3, 8, 70], window=64)
    assert got == {"min": 3, "median": 8, "max": 70, "window": 64, "over_window": 1}


def test_the_census_reports_no_truncation_when_everything_fits() -> None:
    got = SCRIPT.census("probe", [3, 8, 20], window=512)
    assert got["over_window"] == 0
