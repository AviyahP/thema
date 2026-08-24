from pathlib import Path

from resolve_gene_symbols import (
    LOG_COLUMNS,
    SPOTCHECK_COLUMNS,
    format_pathways,
    log_rows,
    read_gmt,
    spotcheck_rows,
    write_tsv,
)
from test_genes import COMPLETE_SET, WITHDRAWN
from thema.data.genes import GeneResolver, Snapshot


def _resolver() -> GeneResolver:
    return GeneResolver(Snapshot.from_tsv_text(COMPLETE_SET, WITHDRAWN))


def test_read_gmt_skips_the_name_and_description_columns(tmp_path: Path) -> None:
    path = tmp_path / "sets.gmt"
    path.write_text(
        "SET_ONE\thttps://example.org/one\tKLF1\tTP53\n"
        "SET_TWO\tR-HSA-1\tTP53\tMULTIA\n"
        "\n",
        encoding="utf-8",
    )
    entries = read_gmt(path)
    assert list(entries) == ["KLF1", "TP53", "MULTIA"], (
        "columns one and two are the set name and its description or id, never genes"
    )
    assert entries["TP53"] == ("SET_ONE", "SET_TWO"), "every containing set must be recorded"


def test_format_pathways_caps_long_lists() -> None:
    assert format_pathways(()) == "-"
    assert format_pathways(("A", "B")) == "A; B"
    assert format_pathways(tuple("ABCDEFG")) == "A; B; C; D; E (+2 more)"


def test_log_omits_clean_matches_and_keeps_everything_else() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["KLF1", "IL8", "DUPE", "NOTAGENE"])
    rows = log_rows("hallmark", report, {})
    logged = {row[1]: row for row in rows}
    assert "KLF1" not in logged, "a clean approved match needs no human attention"
    assert set(logged) == {"IL8", "DUPE", "NOTAGENE"}
    assert logged["IL8"][2] == "previous"
    assert logged["IL8"][3] == "HGNC:2"
    assert logged["IL8"][4] == "CXCL8"
    assert all(len(row) == len(LOG_COLUMNS) for row in rows), "every row must fill every column"


# Every ambiguous row is adjudicated by hand, so the candidates it could not choose between and
# the pathways giving it biological context both have to survive into the file.
def test_ambiguous_rows_carry_candidates_and_pathways() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["DUPE"])
    row = log_rows("reactome", report, {"DUPE": ("Pathway A", "Pathway B")})[0]
    assert "HGNC:4|AMBIA" in row[-1] and "HGNC:5|AMBIB" in row[-1]
    assert row[LOG_COLUMNS.index("pathways")] == "Pathway A; Pathway B"


def test_non_ambiguous_rows_leave_pathways_empty() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["IL8"])
    row = log_rows("reactome", report, {"IL8": ("Pathway A",)})[0]
    assert row[LOG_COLUMNS.index("pathways")] == "-", (
        "only ambiguous rows carry pathways; otherwise the file balloons for no gain"
    )


def test_multi_mapping_rows_record_their_origin() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["MULTIA /// MULTIB"])
    rows = log_rows("btm", report, {})
    assert len(rows) == 2, "both components are logged even though both resolved cleanly"
    for row in rows:
        assert "multi-mapping component" in row[-1]
        assert "MULTIA /// MULTIB" in row[-1]


def test_spotcheck_takes_every_alias_and_leaves_verification_columns_empty() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["P53", "ONLYALIAS", "IL8", "KLF1"])
    rows = spotcheck_rows({"go": report}, {"go": {}})
    tiers = [row[0] for row in rows]
    assert tiers.count("alias") == 2, "the alias tier is taken in full, not sampled"
    assert tiers.count("previous") == 1
    assert all(len(row) == len(SPOTCHECK_COLUMNS) for row in rows)
    for row in rows:
        assert row[-2:] == ("", ""), "verified and note are left blank to fill in by hand"


def test_spotcheck_sampling_is_deterministic() -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["P53", "ONLYALIAS", "IL8"])
    first = spotcheck_rows({"go": report}, {"go": {}})
    assert spotcheck_rows({"go": report}, {"go": {}}) == first, (
        "a fixed seed keeps the committed spot-check file from churning in git"
    )


# The log is committed, so an unchanged run must not produce a diff.
def test_written_tsv_is_stable_across_runs(tmp_path: Path) -> None:
    resolver = _resolver()
    _, report = resolver.resolve_set(["IL8", "DUPE", "NOTAGENE", "GONE"])
    path = tmp_path / "gene_resolution_log.tsv"

    write_tsv(path, LOG_COLUMNS, log_rows("btm", report, {}))
    first = path.read_text(encoding="utf-8")
    write_tsv(path, LOG_COLUMNS, log_rows("btm", report, {}))

    assert path.read_text(encoding="utf-8") == first, "log rendering is not deterministic"
    assert first.splitlines()[0] == "\t".join(LOG_COLUMNS)
    assert not list(tmp_path.glob("*.part")), "the temporary file must not survive"
