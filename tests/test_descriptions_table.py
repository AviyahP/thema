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
    marked, superseded = D.restamp(p, COLUMNS, "v4")[:2]
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


def test_a_partial_generation_promotes_without_blanking_what_it_omits(tmp_path):
    """CHANGED 23 Sep 2026. This previously asserted that promoting a one-key generation over ten
    left read() returning ONLY that key -- the other nine silently lost their descriptions, with
    nothing in the table recording it. A generation can miss pathways for ordinary reasons (a
    refusal, a truncation, an interrupted chunk), so a key the incoming generation does not cover
    now keeps the current row it already has.
    """
    p = table(
        tmp_path,
        *(row(f"go:{i}", "v3", "v3") for i in range(10)),
        row("go:0", "v4", "v4", D.STATUS_SUPERSEDED),
    )
    promotion = D.restamp(p, COLUMNS, "v4", allow_shrink=True)
    assert promotion.marked == 1
    assert promotion.retained == 9, "the nine keys v4 says nothing about must keep their rows"
    assert promotion.retained_versions == {"v3": 9}
    text = D.read(p)
    assert text["go:0"] == "v4", "the key the new generation covers is promoted"
    assert len(text) == 10, "and nothing it omits was blanked"


def test_restamp_refuses_to_leave_nothing_current(tmp_path):
    p = table(tmp_path, row("go:1", "v3 text", "v3"))
    with pytest.raises(ValueError, match="no current generation"):
        D.restamp(p, COLUMNS, "v9")


def test_an_incomplete_generation_never_ends_up_marked_current(tmp_path):
    """The 2026-09-18 failure: merge promoted rows, then restamp refused, leaving two currents.

    Rows are written superseded and promoted only by `restamp`. If promotion is declined the table
    must still have exactly one current generation -- not the incoming one, and not both.
    """
    p = table(
        tmp_path,
        *(row(f"go:{i}", "v3", "v3", D.STATUS_CURRENT) for i in range(10)),
        *(row(f"go:{i}", "v4", "v4", D.STATUS_SUPERSEDED) for i in range(3)),
    )
    with pytest.raises(ValueError, match="would supersede a generation of"):
        D.restamp(p, COLUMNS, "v4")
    import csv

    rows = list(csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"))
    current = {r["prompt_version"] for r in rows if r["status"] == D.STATUS_CURRENT}
    assert current == {"v3"}, "exactly one generation may be current when promotion is declined"
    assert len(D.read(p)) == 10, "the readable set must not be a mixture of two generations"
    assert len(D.read(p, version="v4")) == 3, "the incomplete generation is kept, just not current"


def test_restamp_leaves_out_of_universe_rows_alone(tmp_path) -> None:
    """A pathway that left the universe must not be resurrected by the next promotion.

    ``restamp`` rewrites every row's status, so without an exemption the out-of-universe marking
    would survive only until the next generation landed -- and a zero-gene pathway excluded by the
    universe rule would quietly become ``current`` again.
    """
    table = tmp_path / "d.tsv"
    rows = [
        ("a", "text", "description+name+genes", "5", "m", "v4", D.STATUS_CURRENT),
        ("b", "text", "description+name+genes", "5", "m", "v4", D.STATUS_CURRENT),
        ("gone", "text", "description+name", "0", "m", "v4", D.STATUS_OUT_OF_UNIVERSE),
    ]
    write_tsv(table, COLUMNS, rows)
    marked, superseded = D.restamp(table, COLUMNS, "v4")[:2]
    assert (marked, superseded) == (2, 0), "the held row must count as neither"
    assert D.read(table) == {"a": "text", "b": "text"}, "read() must not return it"


def test_promoting_v4_does_not_blank_the_thirteen_v4_alt_pathways(tmp_path):
    """The real hazard, in miniature: v4 has no row for the 13 refused pathways.

    The readable generation spans two prompt_versions -- v4 for almost everything, v4-alt for the
    13 the v4 batch refused. Promoting v4 must not demote them, or read() silently loses 13
    pathways and the universe stops being fully described. This replaces a note in DECISIONS.md
    with a guarantee: the rule holds whether or not anyone remembers to name both versions.
    """
    universe = [f"go:{i}" for i in range(10_757)]
    refused = [f"reactome:R-{i}" for i in range(13)]
    p = table(
        tmp_path,
        *(row(k, "v4 text", "v4") for k in universe),
        *(
            row(k, "alt text", "v4-alt", D.STATUS_CURRENT, model="gpt-5-6-thinking")
            for k in refused
        ),
    )
    assert len(D.read(p)) == 10_770, "precondition: the whole universe is described"

    promotion = D.restamp(p, COLUMNS, "v4")

    assert promotion.marked == 10_757
    assert promotion.retained == 13, "v4 says nothing about the 13, so it may not demote them"
    assert promotion.retained_versions == {"v4-alt": 13}
    text = D.read(p)
    assert len(text) == 10_770, "read() must still return the whole universe"
    assert all(text[k] == "alt text" for k in refused), "and the 13 keep their own descriptions"
