import hashlib
from pathlib import Path

import filter_reactome_membership as cascade
from thema.data.tables import (
    EMPTY,
    cell,
    flatten,
    join_bindings,
    join_items,
    optional,
    sha256_file,
    split_bindings,
    split_items,
    write_tsv,
)

COLUMNS = ("source", "source_id", "genes")
ROWS = (
    ("go", "GO:0000012", "HGNC:1541;HGNC:6018"),
    ("hallmark", "HALLMARK_APOPTOSIS", EMPTY),
)


def test_flatten_collapses_the_whitespace_a_cell_cannot_hold():
    assert flatten("a\tb\nc  d ") == "a b c d"


def test_flatten_is_idempotent_so_a_reload_changes_nothing():
    once = flatten("Curated\tprose\nwith breaks")
    assert flatten(once) == once, "flattening on load must survive a round trip unchanged"


def test_an_absent_value_reads_back_as_none_not_as_a_hyphen():
    assert cell(None) == EMPTY
    assert optional(cell(None)) is None


def test_an_empty_list_is_distinguishable_from_a_list_holding_one_blank():
    assert join_items(()) == EMPTY
    assert split_items(EMPTY) == ()
    assert split_items(join_items(("a", "b"))) == ("a", "b")


def test_bindings_round_trip_including_a_gene_reached_by_two_symbols():
    bindings = (("HGNC:1541", ("CBL",)), ("HGNC:6018", ("IL6", "IFNB2")))
    assert join_bindings(bindings) == "HGNC:1541=CBL;HGNC:6018=IL6,IFNB2"
    assert split_bindings(join_bindings(bindings)) == bindings


def test_no_bindings_round_trip_through_the_empty_cell():
    assert join_bindings(()) == EMPTY
    assert split_bindings(EMPTY) == ()


def test_write_tsv_puts_the_header_first_and_ends_with_a_newline(tmp_path: Path):
    path = tmp_path / "t.tsv"
    write_tsv(path, COLUMNS, ROWS)
    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "source\tsource_id\tgenes"
    assert text.endswith("\n")


def test_written_tsv_is_stable_across_runs(tmp_path: Path):
    first, second = tmp_path / "a.tsv", tmp_path / "b.tsv"
    write_tsv(first, COLUMNS, ROWS)
    write_tsv(second, COLUMNS, ROWS)
    assert first.read_bytes() == second.read_bytes()
    leftovers = list(tmp_path.glob("*.part"))
    assert not leftovers, "the temporary file must be renamed, never left behind"


def test_sha256_file_matches_a_digest_of_the_whole_file(tmp_path: Path):
    path = tmp_path / "t.tsv"
    write_tsv(path, COLUMNS, ROWS)
    assert sha256_file(path) == hashlib.sha256(path.read_bytes()).hexdigest()


# The cascade keeps its own copy of write_tsv and must not be modified, so the two are pinned
# against each other instead. A digest is committed on this writer's output; a silent divergence
# in trailing-newline or empty-row handling would change that digest with nothing to explain it.
def test_write_tsv_agrees_byte_for_byte_with_the_copy_in_filter_reactome_membership(tmp_path: Path):
    ours, theirs = tmp_path / "ours.tsv", tmp_path / "theirs.tsv"
    write_tsv(ours, COLUMNS, ROWS)
    cascade.write_tsv(theirs, COLUMNS, ROWS)
    assert ours.read_bytes() == theirs.read_bytes()


def test_sha256_file_agrees_with_the_copy_in_filter_reactome_membership(tmp_path: Path):
    path = tmp_path / "t.tsv"
    write_tsv(path, COLUMNS, ROWS)
    assert sha256_file(path) == cascade.sha256_file(path)
