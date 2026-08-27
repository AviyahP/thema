import json
from pathlib import Path

from build_pathways import (
    Check,
    btm_ids_agreeing_with_url,
    build_summary,
    collapsed_members,
    duplicate_human_names,
    duplicate_summation_ids,
    inputs_under,
    log_non_resolving,
    main,
    name_collisions,
    percentile,
    sanity_checks,
    spread,
)
from test_formats import MSIGDB_XML, OBO
from test_genes import COMPLETE_SET, WITHDRAWN
from test_pathways import (
    BTM_GMT,
    DISCARDS,
    GO_GMT,
    GO_TERM_IDS,
    HALLMARK_GMT,
    MEMBERSHIP,
    PATHWAY_NAMES,
    SUMMATIONS,
    _collection,
)
from thema.data.tables import sha256_file

# NOSUCHGENE is the only symbol the fixture's GO set drops, so a log recording exactly that is a
# log this build agrees with.
RESOLUTION_LOG = "\n".join(
    (
        "source\toriginal_symbol\toutcome\thgnc_id\tapproved_symbol\tmatch_type"
        "\tcarried_forward\tpathways\tnote",
        "go\tNOSUCHGENE\tunmapped\t-\t-\t-\t-\t-\t",
        "go\tCXCL8\tprevious\tHGNC:2\tCXCL8\tprevious\tfalse\t-\t",
        "btm\tNOSUCHGENE\tunmapped\t-\t-\t-\t-\t-\t",
        "reactome\tGAG\tunmapped\t-\t-\t-\t-\t-\t",
    )
)

MEMBERSHIP_SUMMARY = "\n".join(
    (
        "section\tkey\tvalue\tnote",
        "digest\treactome_membership.tsv\tdeadbeef\tsha256 of the regenerable kept table",
    )
)


def _raw_and_out(tmp_path: Path) -> tuple[Path, Path]:
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    out.mkdir()
    files = {
        raw / "ReactomePathways.txt": PATHWAY_NAMES,
        raw / "pathway2summation.txt": SUMMATIONS,
        raw / "c5.go.bp.v2026.1.Hs.symbols.gmt": GO_GMT,
        raw / "c5.go.bp.v2026.1.Hs.json": json.dumps(
            {name: {"exactSource": go_id} for name, go_id in GO_TERM_IDS.items()}
        ),
        raw / "go-basic.obo": OBO,
        raw / "h.all.v2026.1.Hs.symbols.gmt": HALLMARK_GMT,
        raw / "msigdb_v2026.1.Hs.xml": MSIGDB_XML,
        raw / "BTM_for_GSEA_20131008.gmt": BTM_GMT,
        raw / "hgnc_complete_set_2026-07-07.txt": COMPLETE_SET,
        raw / "withdrawn_2026-07-07.txt": WITHDRAWN,
        out / "reactome_membership.tsv": MEMBERSHIP,
        out / "reactome_membership_discards.tsv": DISCARDS,
        out / "reactome_membership_summary.tsv": MEMBERSHIP_SUMMARY,
        out / "gene_resolution_log.tsv": RESOLUTION_LOG,
    }
    for path, text in files.items():
        path.write_text(text + "\n", encoding="utf-8")
    return raw, out


def _summary(tmp_path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    raw, out = _raw_and_out(tmp_path)
    assert main(["--raw", str(raw), "--out", str(out)]) == 0
    rows = (out / "pathways_summary.tsv").read_text(encoding="utf-8").splitlines()
    assert rows[0].split("\t") == ["section", "key", "value", "note"]
    parsed = {}
    for row in rows[1:]:
        section, key, value, note = row.split("\t")
        parsed[(section, key)] = (value, note)
    return parsed


def test_percentile_uses_nearest_rank_and_survives_an_empty_sequence():
    assert percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert percentile([], 0.5) == 0


def test_spread_renders_the_five_numbers_in_order():
    assert spread([1, 2, 3, 4, 5]) == "1/1/3/5/5"
    assert spread([]) == "-"


def test_a_check_that_matches_its_expectation_passes():
    assert Check("k", "5", "5").status == "pass"


def test_a_check_that_diverges_fails_and_keeps_the_measured_value():
    check = Check("k", "7", "5")
    assert check.status == "FAIL"
    assert check.row() == ("sanity", "k", "7", "expected 5 [FAIL]")


def test_a_check_carries_its_note_beside_the_verdict():
    assert Check("k", "5", "5", "because").row()[3] == "expected 5 [pass] - because"


def test_duplicate_summation_ids_finds_the_pathway_with_two_rows():
    assert duplicate_summation_ids(SUMMATIONS.splitlines()) == ("R-HSA-2",)


def test_duplicate_human_names_ignores_other_species():
    names = PATHWAY_NAMES + (
        "\nR-HSA-6\tAlpha pathway\tHomo sapiens\nR-BTA-8\tAlpha pathway\tBos taurus"
    )
    assert duplicate_human_names(names.splitlines()) == 1


def test_btm_module_ids_are_confirmed_against_the_url_in_their_own_second_column():
    agreed, total = btm_ids_agreeing_with_url(BTM_GMT.splitlines())
    assert (agreed, total) == (5, 6), "the one unlabelled module has no id to confirm"


def test_collapsed_members_counts_what_deduplication_removed():
    # Reactome's R-HSA-1 lists TP53 and P53, which are one gene.
    assert collapsed_members(_collection(), "reactome") == 1


def test_name_collisions_are_counted_verbatim_and_normalized():
    collection = _collection()
    assert name_collisions(collection, normalize=False) >= 0
    assert name_collisions(collection, normalize=True) >= name_collisions(
        collection, normalize=False
    ), "normalizing can only ever reveal more collisions, never fewer"


def test_log_non_resolving_keeps_only_the_outcomes_that_produced_no_gene():
    log = log_non_resolving(RESOLUTION_LOG.splitlines())
    assert log["go"] == {"NOSUCHGENE"}, "a symbol that resolved via the previous tier is not a drop"


# The two files record the same fact from different directions: this build re-resolves the same
# GMTs the resolution log was written from. If they disagree, that is the finding.
def test_drops_agreeing_with_the_resolution_log_pass(tmp_path: Path):
    summary = _summary(tmp_path)
    value, note = summary[("sanity", "go drops agree with the resolution log")]
    assert value == "1 built, 1 logged, 0 differing"
    assert "[pass]" in note


def test_drops_diverging_from_the_resolution_log_fail_with_both_numbers(tmp_path: Path):
    raw, out = _raw_and_out(tmp_path)
    inputs = inputs_under(raw, out)
    checks = sanity_checks(_collection(), inputs, "abc", "abc", {"go": {"SOMETHINGELSE"}})
    go = next(c for c in checks if c.key == "go drops agree with the resolution log")
    assert go.status == "FAIL"
    assert go.measured == "1 built, 1 logged, 2 differing", (
        "a divergence must show both counts, not merely that they disagree"
    )


def test_a_stale_cascade_output_is_reported_rather_than_built_on_silently(tmp_path: Path):
    summary = _summary(tmp_path)
    _, note = summary[("sanity", "cascade output is the one the cascade committed")]
    assert "[FAIL]" in note, "the fixture's committed digest is deliberately wrong"


def test_summary_records_the_digest_of_the_regenerable_table(tmp_path: Path):
    raw, out = _raw_and_out(tmp_path)
    main(["--raw", str(raw), "--out", str(out)])
    rows = dict(
        (line.split("\t")[1], line.split("\t")[2])
        for line in (out / "pathways_summary.tsv").read_text(encoding="utf-8").splitlines()[1:]
    )
    assert rows["pathways.tsv"] == sha256_file(out / "pathways.tsv")


def test_summary_reports_a_stated_expectation_as_measured_when_it_fails(tmp_path: Path):
    summary = _summary(tmp_path)
    value, note = summary[("sanity", "reactome human pathways")]
    assert (value, "[FAIL]" in note) == ("5", True), (
        "a divergence is recorded with its measured value, never absorbed into a new expectation"
    )


# A pass here means the build reproduces the planning measurement, not that the number is right.
# That distinction has to survive in the file, or a later reader takes the block for validation.
def test_summary_labels_where_its_expectations_came_from(tmp_path: Path):
    _, note = _summary(tmp_path)[("sanity", "expectation provenance")]
    assert "not from an independent source" in note


def test_summary_counts_every_source_and_every_enum_value_including_the_zeroes(tmp_path: Path):
    summary = _summary(tmp_path)
    for source in ("reactome", "go", "hallmark", "btm"):
        assert ("source", source) in summary
        for value in ("ok", "depleted", "empty_after_resolution", "no_source_members"):
            assert ("degradation", f"{source}/{value}") in summary
        for value in ("described", "name_only", "no_usable_text"):
            assert ("text_availability", f"{source}/{value}") in summary


def test_summary_records_that_reactome_drops_are_deliberately_not_cross_checked(tmp_path: Path):
    value, _ = _summary(tmp_path)[("sanity", "reactome drops are not checked against the log")]
    assert value == "by design"


def test_the_build_writes_one_row_per_pathway(tmp_path: Path):
    raw, out = _raw_and_out(tmp_path)
    main(["--raw", str(raw), "--out", str(out)])
    lines = (out / "pathways.tsv").read_text(encoding="utf-8").splitlines()
    assert len(lines) - 1 == len(_collection())


def test_building_twice_produces_an_identical_table(tmp_path: Path):
    raw, out = _raw_and_out(tmp_path)
    main(["--raw", str(raw), "--out", str(out)])
    first = (out / "pathways.tsv").read_bytes()
    main(["--raw", str(raw), "--out", str(out)])
    assert (out / "pathways.tsv").read_bytes() == first
    assert not list(out.glob("*.part")), "the temporary file must be renamed, never left behind"


# data/reactome_membership.tsv is gitignored, so this is the first thing a fresh clone hits.
def test_main_reports_a_missing_cascade_output_instead_of_crashing(tmp_path: Path, capsys):
    raw, out = _raw_and_out(tmp_path)
    (out / "reactome_membership.tsv").unlink()
    assert main(["--raw", str(raw), "--out", str(out)]) == 1
    assert "reactome_membership.tsv" in capsys.readouterr().err


def test_build_summary_covers_every_section_a_reader_expects():
    collection = _collection()
    sections = {row[0] for row in build_summary(collection, "d1", "d2", [], 0, 0)}
    assert sections == {
        "digest",
        "input",
        "source",
        "description",
        "description_chars",
        "size",
        "degradation",
        "text_availability",
        "genes",
        "dropped",
        "collapsed",
        "quality",
        "sanity",
    }
