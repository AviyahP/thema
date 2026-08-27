from dataclasses import replace

import pytest

from test_formats import OBO
from test_genes import COMPLETE_SET, WITHDRAWN
from thema.data.formats import parse_obo_terms
from thema.data.genes import GeneResolver, Snapshot
from thema.data.pathways import (
    PATHWAY_COLUMNS,
    Pathway,
    PathwayCollection,
    btm_identity,
    load_btm_pathways,
    load_go_pathways,
    load_hallmark_pathways,
    load_reactome_pathways,
)

# R-HSA-2's name carries a trailing space, as 28 human names in the real file do. R-HSA-3 appears
# only in the discards, R-HSA-4 in neither table, and the bovine row must not load at all.
PATHWAY_NAMES = "\n".join(
    (
        "R-HSA-1\tAlpha pathway\tHomo sapiens",
        "R-HSA-2\tBeta pathway \tHomo sapiens",
        "R-HSA-3\tGamma pathway\tHomo sapiens",
        "R-HSA-4\tDelta pathway\tHomo sapiens",
        "R-HSA-5\tDepleted pathway\tHomo sapiens",
        "R-BTA-9\tBovine pathway\tBos taurus",
    )
)

# pathway_name here deliberately disagrees with ReactomePathways.txt, the way the real GMT's
# `_<id>` disambiguation does. DUPE would be refused as ambiguous by the resolver; the cascade
# already settled it, so it must survive.
MEMBERSHIP = "\n".join(
    (
        "pathway_id\tpathway_name\tsymbol\thgnc_id\tapproved_symbol\tmatch_type\tprovenance",
        "R-HSA-1\tAlpha pathway_1\tTP53\tHGNC:3\tTP53\tapproved\tconfirmed",
        "R-HSA-1\tAlpha pathway_1\tP53\tHGNC:3\tTP53\talias\tconfirmed",
        "R-HSA-1\tAlpha pathway_1\tKLF1\tHGNC:1\tKLF1\tapproved\tconfirmed",
        "R-HSA-2\tBeta pathway\tCXCL8\tHGNC:2\tCXCL8\tprevious\tconfirmed",
        "R-HSA-2\tBeta pathway\tDUPE\tHGNC:4\tAMBIA\tadjudicated\tconfirmed",
        "R-HSA-5\tDepleted pathway\tMULTIA\tHGNC:7\tMULTIA\tapproved\tconfirmed",
    )
)

DISCARDS = "\n".join(
    (
        "pathway_id\tpathway_name\tsymbol\thgnc_id\tmatch_type\ttest\treason",
        "R-HSA-3\tGamma pathway\tVIRAL1\t-\t-\t0\tsymbol resolves to no HGNC record",
        "R-HSA-3\tGamma pathway\tVIRAL2\t-\t-\t0\tsymbol resolves to no HGNC record",
        "R-HSA-5\tDepleted pathway\tGAG\t-\t-\t0\tsymbol resolves to no HGNC record",
        "R-HSA-5\tDepleted pathway\tPOL\t-\t-\t0\tsymbol resolves to no HGNC record",
    )
)

# R-HSA-2 has two rows, as R-HSA-166016 does. R-HSA-3's summation contains a literal tab, as
# R-HSA-212436's does. R-HSA-4 has none at all. R-HSA-1's carries markup, as 981 real ones do.
SUMMATIONS = "\n".join(
    (
        "Identifier\tName\tSummation",
        "R-HSA-1\tAlpha pathway\tThe alpha <b>pathway</b>.",
        "R-HSA-2\tBeta pathway\tFirst half.",
        "R-HSA-2\tBeta pathway\tSecond half.",
        "R-HSA-3\tGamma pathway\tSplit\tacross a tab.",
        "R-HSA-5\tDepleted pathway\tDepleted prose.",
    )
)

GO_GMT = "\n".join(
    (
        "GOBP_ONE\thttps://www.gsea-msigdb.org/gsea/msigdb/human/geneset/GOBP_ONE"
        "\tTP53\tKLF1\tNOSUCHGENE",
        "GOBP_OBSOLETE\thttps://www.gsea-msigdb.org/gsea/msigdb/human/geneset/GOBP_OBSOLETE\tKLF1",
        "GOBP_BY_ALT_ID\thttps://www.gsea-msigdb.org/gsea/msigdb/human/geneset/GOBP_BY_ALT_ID"
        "\tCXCL8",
        "GOBP_UNJOINED\thttps://www.gsea-msigdb.org/gsea/msigdb/human/geneset/GOBP_UNJOINED\tKLF1",
    )
)

GO_TERM_IDS = {
    "GOBP_ONE": "GO:0000012",
    "GOBP_OBSOLETE": "GO:0000002",
    "GOBP_BY_ALT_ID": "GO:0019008",
    "GOBP_UNJOINED": "GO:0404040",
}

HALLMARK_GMT = "\n".join(
    (
        "HALLMARK_ONE\thttps://www.gsea-msigdb.org/gsea/msigdb/human/geneset/HALLMARK_ONE"
        "\tTP53\tKLF1",
        "HALLMARK_UNDESCRIBED\thttps://www.gsea-msigdb.org/gsea/msigdb/human/geneset/"
        "HALLMARK_UNDESCRIBED\tKLF1",
    )
)

BTM_GMT = "\n".join(
    (
        "targets of FOSL1/2 (M0)\thttp://mummichog.org/BTM/M0.htm\tTP53\tKLF1",
        "TBA (M26.0)\thttp://mummichog.org/BTM/M26.0.htm\tKLF1",
        "TBA (source: B cells) (M152.0)\thttp://mummichog.org/BTM/M152.0.htm\tKLF1",
        "T cell surface signature (S0)\thttp://mummichog.org/BTM/S0.htm\tCXCL8",
        "probe module (M9)\thttp://mummichog.org/BTM/M9.htm"
        "\tMULTIA /// MULTIB\tMULTIA /// NOSUCHGENE",
        "unlabelled module\thttp://mummichog.org/BTM/none.htm\tKLF1",
    )
)


def _resolver():
    return GeneResolver(Snapshot.from_tsv_text(COMPLETE_SET, WITHDRAWN))


def _reactome():
    return {
        p.source_id: p
        for p in load_reactome_pathways(
            PATHWAY_NAMES.splitlines(),
            MEMBERSHIP.splitlines(),
            DISCARDS.splitlines(),
            SUMMATIONS.splitlines(),
        )
    }


def _go():
    terms = parse_obo_terms(OBO.splitlines(), "biological_process")
    return {
        p.source_id: p
        for p in load_go_pathways(GO_GMT.splitlines(), GO_TERM_IDS, terms, _resolver())
    }


def _hallmark(descriptions=None):
    if descriptions is None:
        descriptions = {"HALLMARK_ONE": "Genes up-regulated in one."}
    return {
        p.source_id: p
        for p in load_hallmark_pathways(HALLMARK_GMT.splitlines(), descriptions, _resolver())
    }


def _btm():
    return {p.source_id: p for p in load_btm_pathways(BTM_GMT.splitlines(), _resolver())}


def _collection():
    return PathwayCollection.of(
        _reactome().values(), _go().values(), _hallmark().values(), _btm().values()
    )


# ---------------------------------------------------------------- reactome


# The cascade uses Reactome's own identifier exports to settle display names no symbol resolver
# could -- PB1 is human PBRM1 in two pathways and influenza polymerase in twenty-five. DUPE stands
# in for that here: the resolver refuses it as ambiguous, and it must still arrive.
def test_reactome_takes_its_genes_from_the_cascade_and_never_calls_the_resolver():
    assert _reactome()["R-HSA-2"].genes == frozenset({"HGNC:2", "HGNC:4"})


def test_reactome_name_comes_from_the_pathway_list_not_from_the_membership_table():
    name = _reactome()["R-HSA-1"].name
    assert name == "Alpha pathway", "the membership table's copy is the GMT's"


def test_reactome_names_are_stripped_of_trailing_whitespace():
    assert _reactome()["R-HSA-2"].name == "Beta pathway"


def test_non_human_reactome_pathways_are_excluded():
    assert "R-BTA-9" not in _reactome()


def test_reactome_pathway_with_two_summations_joins_them_in_file_order():
    assert _reactome()["R-HSA-2"].description_source == "First half. Second half."


def test_reactome_summation_containing_a_tab_is_read_whole():
    assert _reactome()["R-HSA-3"].description_source == "Split across a tab."


def test_reactome_markup_is_kept_because_removing_it_would_be_normalization():
    assert _reactome()["R-HSA-1"].description_source == "The alpha <b>pathway</b>."


def test_two_reactome_display_names_meeting_on_one_gene_keep_both_symbols():
    alpha = _reactome()["R-HSA-1"]
    assert alpha.symbols_by_gene["HGNC:3"] == ("TP53", "P53")
    assert alpha.n_genes == 2, "n_genes counts genes, not the symbols that reached them"


def test_a_pathway_absent_from_the_gmt_is_no_source_members_not_empty_after_resolution():
    delta = _reactome()["R-HSA-4"]
    assert delta.degradation == "no_source_members", "never having members is not losing them"
    assert (delta.n_genes, delta.n_dropped) == (0, 0)


def test_empty_after_resolution_takes_precedence_over_depleted():
    gamma = _reactome()["R-HSA-3"]
    assert gamma.drop_fraction == 1.0
    assert gamma.degradation == "empty_after_resolution", "the more specific value must win"


def test_drop_fraction_is_zero_when_a_pathway_never_had_members():
    assert _reactome()["R-HSA-4"].drop_fraction == 0.0


def test_a_pathway_losing_most_but_not_all_of_its_members_is_depleted():
    depleted = _reactome()["R-HSA-5"]
    assert (depleted.n_genes, depleted.n_dropped) == (1, 2)
    assert depleted.degradation == "depleted"


def test_a_pathway_with_no_summation_records_none_rather_than_an_empty_string():
    delta = _reactome()["R-HSA-4"]
    assert delta.description_source is None
    assert delta.description_source_from == "none"


# ---------------------------------------------------------------- go


def test_go_source_id_comes_from_exact_source_not_from_the_gmt_url_column():
    assert "GO:0000012" in _go(), "the GMT carries a URL and a name slug, never a GO id"


def test_go_name_and_description_come_from_the_obo_term():
    one = _go()["GO:0000012"]
    assert one.name == "single strand break repair"
    assert one.description_source == "The repair of single strand breaks in DNA."
    assert one.description_source_from == "go_def"


def test_go_obsolete_term_keeps_its_marker_in_name_and_description():
    obsolete = _go()["GO:0000002"]
    assert obsolete.name.startswith("obsolete ")
    assert obsolete.description_source.startswith("OBSOLETE."), (
        "GO writes obsolescence into the text; that token is what normalization has to erase"
    )


def test_go_set_joining_through_an_alternate_id_still_finds_its_term():
    assert _go()["GO:0019008"].name == "mitochondrion inheritance"


def test_go_set_whose_term_is_missing_falls_back_to_the_set_name_with_no_description():
    unjoined = _go()["GO:0404040"]
    assert unjoined.name == "GOBP_UNJOINED"
    assert (unjoined.description_source, unjoined.description_source_from) == (None, "none")


def test_go_symbol_matching_nothing_is_dropped_and_recorded():
    one = _go()["GO:0000012"]
    assert one.dropped_symbols == ("NOSUCHGENE",)
    assert one.n_genes == 2


# ---------------------------------------------------------------- hallmark


def test_hallmark_description_comes_from_the_xml_because_the_json_carries_none():
    one = _hallmark()["HALLMARK_ONE"]
    assert one.description_source == "Genes up-regulated in one."
    assert one.description_source_from == "msigdb_xml"


def test_hallmark_name_is_the_standard_name_because_msigdb_publishes_no_title():
    assert _hallmark()["HALLMARK_ONE"].name == "HALLMARK_ONE"


def test_hallmark_set_absent_from_the_xml_loads_with_no_description():
    undescribed = _hallmark()["HALLMARK_UNDESCRIBED"]
    assert (undescribed.description_source, undescribed.description_source_from) == (None, "none")


# Hallmark's real descriptions run to a 58-character median. Brevity is a number the build already
# reports; it must not become a value in this vocabulary.
def test_hallmark_terseness_does_not_change_text_availability():
    terse = _hallmark({"HALLMARK_ONE": "Short."})["HALLMARK_ONE"]
    assert terse.text_availability == "described"


# ---------------------------------------------------------------- btm


def test_btm_source_id_is_the_module_id_parsed_out_of_the_set_name():
    assert "M0" in _btm()


def test_btm_name_drops_the_module_id_it_was_parsed_from():
    assert _btm()["M0"].name == "targets of FOSL1/2"


def test_btm_surface_signature_sets_are_recognised_as_well_as_modules():
    assert "S0" in _btm(), "twelve real modules are S-prefixed; a pattern of M\\d+ would drop them"


def test_btm_set_with_no_parsable_module_id_falls_back_to_the_whole_name():
    assert _btm()["unlabelled module"].name == "unlabelled module"


def test_btm_has_no_description_and_records_that_as_none_rather_than_missing():
    assert all(p.description_source_from == "none" for p in _btm().values())


def test_btm_placeholder_name_reads_as_no_usable_text_and_a_real_name_as_name_only():
    modules = _btm()
    assert modules["M26.0"].text_availability == "no_usable_text"
    assert modules["M152.0"].text_availability == "no_usable_text", "TBA with a hint is still TBA"
    assert modules["M0"].text_availability == "name_only"


def test_btm_identity_leaves_a_name_without_an_id_alone():
    assert btm_identity("unlabelled module") == ("unlabelled module", "unlabelled module", False)


def test_btm_multi_mapping_entry_contributes_every_component_that_resolves():
    assert _btm()["M9"].genes == frozenset({"HGNC:7", "HGNC:8"})


def test_a_multi_mapping_entry_drops_only_the_component_that_failed():
    probe = _btm()["M9"]
    assert probe.dropped_symbols == ("NOSUCHGENE",), (
        "a drop is a component, so a half-resolving entry both gives a gene and records a loss"
    )


# ---------------------------------------------------------------- collection


def test_collection_is_sorted_by_source_then_source_id():
    collection = _collection()
    assert [p.source for p in collection][:5] == ["reactome"] * 5
    assert [p.source_id for p in collection.of_source("go")] == sorted(
        p.source_id for p in collection.of_source("go")
    )


def test_collection_counts_every_source_including_one_that_contributed_nothing():
    assert PathwayCollection.of(_btm().values()).counts_by_source == {
        "reactome": 0,
        "go": 0,
        "hallmark": 0,
        "btm": 6,
    }


def test_collection_gene_union_deduplicates_across_sources():
    assert _collection().gene_union == frozenset(
        {"HGNC:1", "HGNC:2", "HGNC:3", "HGNC:4", "HGNC:7", "HGNC:8"}
    )


def test_gene_symbols_cover_exactly_the_gene_set():
    for pathway in _collection():
        assert {hgnc_id for hgnc_id, _ in pathway.gene_symbols} == set(pathway.genes)


def test_gene_symbols_are_sorted_so_two_builds_agree():
    for pathway in _collection():
        assert [hgnc_id for hgnc_id, _ in pathway.gene_symbols] == sorted(pathway.genes)


def test_generated_description_fields_stay_empty_until_the_normalizer_runs():
    for pathway in _collection():
        assert (pathway.description_generated, pathway.description_generated_from) == (None, None)


def test_pathway_key_is_unique_across_every_source():
    collection = _collection()
    assert len(collection.by_key) == len(collection)


def test_collection_rejects_two_pathways_sharing_a_key():
    one = _btm()["M0"]
    with pytest.raises(ValueError, match="share the key"):
        PathwayCollection.of([one, one])


def test_collection_rejects_a_stored_count_that_contradicts_its_collection():
    with pytest.raises(ValueError, match="n_genes"):
        PathwayCollection.of([replace(_btm()["M0"], n_genes=99)])


def test_collection_rejects_a_drop_fraction_that_contradicts_its_counts():
    with pytest.raises(ValueError, match="drop_fraction"):
        PathwayCollection.of([replace(_btm()["M0"], drop_fraction=0.5)])


def test_collection_rejects_a_description_origin_that_contradicts_the_description():
    with pytest.raises(ValueError, match="stated origin"):
        PathwayCollection.of([replace(_btm()["M0"], description_source="invented")])


def test_collection_round_trips_through_its_tsv_form():
    collection = _collection()
    text = "\n".join(
        ["\t".join(PATHWAY_COLUMNS), *("\t".join(row) for row in collection.to_rows())]
    )
    assert PathwayCollection.from_tsv_text(text) == collection


def test_from_tsv_text_rejects_a_table_whose_header_is_not_the_expected_columns():
    with pytest.raises(ValueError, match="header"):
        PathwayCollection.from_tsv_text("source\tsource_id\nbtm\tM0\n")


def test_from_row_rejects_a_row_with_the_wrong_number_of_cells():
    with pytest.raises(ValueError, match="cells"):
        Pathway.from_row(("btm", "M0"))


# frozenset iteration order depends on PYTHONHASHSEED, which is randomised per process. A cell
# written from unsorted genes is stable within one run and different between runs, so a
# build-twice-and-compare test cannot catch it -- but the committed digest would drift.
def test_gene_column_is_sorted_so_the_digest_does_not_depend_on_hash_randomisation():
    row = _go()["GO:0000012"].to_row()
    genes = _go()["GO:0000012"].genes
    assert row[PATHWAY_COLUMNS.index("genes")] == ";".join(sorted(genes))


def test_building_the_same_inputs_twice_produces_identical_rows():
    assert _collection().to_rows() == _collection().to_rows()
