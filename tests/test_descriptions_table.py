"""The descriptions table keeps every generation and exposes exactly one."""

import pytest

from thema.data import descriptions as D
from thema.data.tables import write_tsv

COLUMNS = (
    "key",
    "description_generated",
    "description_generated_from",
    "genes_shown",
    "model",
    "prompt_version",
    "status",
)


def table(tmp_path, *rows):
    path = tmp_path / "pathway_descriptions.tsv"
    write_tsv(path, COLUMNS, rows)
    return path


def row(key, text, version, status=D.STATUS_CURRENT, model="claude-opus-5"):
    return (key, text, "description+name+genes", "5", model, version, status)


def test_read_returns_only_the_current_generation(tmp_path):
    p = table(
        tmp_path,
        row("go:1", "v3 text", "v3", D.STATUS_SUPERSEDED),
        row("go:1", "v4 text", "v4", D.STATUS_CURRENT),
    )
    assert D.read(p) == {"go:1": "v4 text"}


def test_an_earlier_generation_is_still_reachable_by_name(tmp_path):
    p = table(
        tmp_path,
        row("go:1", "v3 text", "v3", D.STATUS_SUPERSEDED),
        row("go:1", "v4 text", "v4", D.STATUS_CURRENT),
    )
    assert D.read(p, version="v3") == {"go:1": "v3 text"}
    assert D.versions(p) == {"v3": 1, "v4": 1}


def test_asking_for_a_generation_that_is_not_there_raises(tmp_path):
    """Returning {} would let a caller carry on against nothing."""
    p = table(tmp_path, row("go:1", "v3 text", "v3"))
    with pytest.raises(ValueError, match="holds no 'v9'"):
        D.read(p, version="v9")


def test_a_table_written_before_versioning_is_still_readable(tmp_path):
    path = tmp_path / "pathway_descriptions.tsv"
    write_tsv(path, COLUMNS[:-1], [row("go:1", "old", "v3")[:-1]])
    assert D.read(path) == {"go:1": "old"}


def test_restamp_moves_current_and_keeps_everything(tmp_path):
    p = table(
        tmp_path,
        *(row(f"go:{i}", "v3", "v3") for i in range(3)),
        *(row(f"go:{i}", "v4", "v4", D.STATUS_SUPERSEDED) for i in range(3)),
    )
    marked, superseded = D.restamp(p, COLUMNS, "v4")
    assert (marked, superseded) == (3, 3)
    assert D.read(p) == {f"go:{i}": "v4" for i in range(3)}
    assert len(D.read(p, version="v3")) == 3, "the superseded generation must still be there"


def test_a_partial_generation_may_not_supersede_a_complete_one(tmp_path):
    """An interrupted run looks exactly like a successful small one."""
    p = table(
        tmp_path,
        *(row(f"go:{i}", "v3", "v3") for i in range(10)),
        row("go:0", "v4", "v4", D.STATUS_SUPERSEDED),
    )
    with pytest.raises(ValueError, match="would supersede a generation of"):
        D.restamp(p, COLUMNS, "v4")
    assert len(D.read(p)) == 10, "the complete generation must still be the readable one"


def test_shrinking_is_possible_when_it_is_deliberate(tmp_path):
    p = table(
        tmp_path,
        *(row(f"go:{i}", "v3", "v3") for i in range(10)),
        row("go:0", "v4", "v4", D.STATUS_SUPERSEDED),
    )
    D.restamp(p, COLUMNS, "v4", allow_shrink=True)
    assert D.read(p) == {"go:0": "v4"}


def test_restamp_refuses_to_leave_nothing_current(tmp_path):
    p = table(tmp_path, row("go:1", "v3 text", "v3"))
    with pytest.raises(ValueError, match="no current generation"):
        D.restamp(p, COLUMNS, "v9")
