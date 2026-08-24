from pathlib import Path

from resolve_gene_symbols import (
    LOG_COLUMNS,
    SOURCE_FILES,
    log_rows,
    read_gmt_symbols,
    write_log,
)
from test_genes import COMPLETE_SET, WITHDRAWN
from thema.data.genes import CURRENT, SOURCE_SNAPSHOT, GeneResolver, Snapshot


def _resolver() -> GeneResolver:
    return GeneResolver({CURRENT: Snapshot.from_tsv_text(CURRENT, COMPLETE_SET, WITHDRAWN)})


def test_every_source_file_has_a_snapshot_assignment() -> None:
    for source in SOURCE_FILES:
        assert source.key in SOURCE_SNAPSHOT, f"{source.key} has no assigned snapshot"


def test_read_gmt_symbols_skips_the_name_and_description_columns(tmp_path: Path) -> None:
    path = tmp_path / "sets.gmt"
    path.write_text(
        "SET_ONE\thttps://example.org/one\tKLF1\tTP53\n"
        "SET_TWO\tR-HSA-1\tTP53\tMULTIA\n"
        "\n",
        encoding="utf-8",
    )
    assert read_gmt_symbols(path) == ("KLF1", "TP53", "MULTIA"), (
        "columns one and two are the set name and its description or id, never genes"
    )


def test_log_omits_clean_matches_and_keeps_everything_else() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["KLF1", "IL8", "DUPE", "NOTAGENE"], CURRENT)
    rows = log_rows("hallmark", report)
    logged = {row[1]: row for row in rows}
    assert "KLF1" not in logged, "a clean current-approved match needs no human attention"
    assert set(logged) == {"IL8", "DUPE", "NOTAGENE"}
    assert logged["IL8"][2] == "previous"
    assert logged["IL8"][3] == "HGNC:2"
    assert logged["IL8"][4] == "CXCL8"
    assert all(len(row) == len(LOG_COLUMNS) for row in rows), "every row must fill every column"


# Every ambiguous row is adjudicated by hand, so the candidates it could not choose between have
# to survive into the file rather than staying in memory.
def test_ambiguous_rows_carry_their_candidates() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["DUPE"], CURRENT)
    note = log_rows("reactome", report)[0][-1]
    assert "HGNC:4|AMBIA" in note and "HGNC:5|AMBIB" in note


def test_multi_mapping_rows_record_their_origin() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["MULTIA /// MULTIB"], CURRENT)
    rows = log_rows("btm", report)
    assert len(rows) == 2, "both components are logged even though both resolved cleanly"
    for row in rows:
        assert "multi-mapping component" in row[-1]
        assert "MULTIA /// MULTIB" in row[-1]


# The log is committed, so an unchanged run must not produce a diff.
def test_written_log_is_stable_across_runs(tmp_path: Path) -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["IL8", "DUPE", "NOTAGENE", "GONE"], CURRENT)
    path = tmp_path / "gene_resolution_log.tsv"

    write_log(path, log_rows("btm", report))
    first = path.read_text(encoding="utf-8")
    write_log(path, log_rows("btm", report))

    assert path.read_text(encoding="utf-8") == first, "log rendering is not deterministic"
    assert first.splitlines()[0] == "\t".join(LOG_COLUMNS)
    assert not list(tmp_path.glob("*.part")), "the temporary file must not survive"
