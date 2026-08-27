import xml.etree.ElementTree as ElementTree

import pytest

from thema.data.formats import (
    parse_geneset_attributes,
    parse_obo_terms,
    read_gmt_sets,
    read_msigdb_descriptions,
    read_msigdb_exact_sources,
)

# Column two means something different in every source: a stable id in Reactome's GMT, a URL
# elsewhere. The last line has no members and must not become a set.
GMT = "\n".join(
    (
        "2-LTR circle formation\tR-HSA-164843\tBANF1\tHMGA1\t",
        "integrin cell surface interactions (I) (M1.0)\thttp://mummichog.org/BTM/M1.0.htm\tCAV2",
        "probe module (M9)\thttp://mummichog.org/BTM/M9.htm\tMULTIA /// MULTIB\tPLAIN",
        "empty set\thttp://example.invalid/none",
    )
)

# A header before the first stanza; a [Typedef] wedged between two terms, whose keys must not leak
# into either; an obsolete term carrying its marker in name and def, as GO writes them; a term in
# another namespace; and a term with two alt_ids.
OBO = "\n".join(
    (
        "format-version: 1.2",
        "data-version: releases/2026-07-26",
        "name: should be ignored, this is the header",
        "",
        "[Term]",
        "id: GO:0000012",
        "name: single strand break repair",
        'def: "The repair of single strand breaks in DNA." [GOC:ai, PMID:123]',
        "namespace: biological_process",
        "is_a: GO:0006281 ! DNA repair",
        "is_a: GO:0006974",
        "",
        "[Typedef]",
        "id: part_of",
        "name: part of",
        "namespace: external",
        "",
        "[Term]",
        "id: GO:0000002",
        "name: obsolete citrulline metabolic process",
        'def: "OBSOLETE. The chemical reactions involving citrulline." [GOC:go_curators]',
        "namespace: biological_process",
        "is_obsolete: true",
        "",
        "[Term]",
        "id: GO:0005524",
        "name: ATP binding",
        'def: "Binding to ATP." [GOC:ai]',
        "namespace: molecular_function",
        "",
        "[Term]",
        "id: GO:0000001",
        "name: mitochondrion inheritance",
        'def: "The distribution of mitochondria." [GOC:mcc]',
        "namespace: biological_process",
        "alt_id: GO:0019008",
        "alt_id: GO:0019009",
        "is_a: GO:0048311 ! mitochondrion distribution",
        "",
    )
)

# The second element reproduces the defect that rules out an XML parser: a raw, unescaped `<`
# inside an attribute value. In the real msigdb_v2026.1.Hs.xml this appears on line 330 as
# EXACT_SOURCE="Table 3S: fold change (log2) < 0".
MSIGDB_XML = "\n".join(
    (
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<MSIGDB NAME=\"msigdb\" VERSION=\"2026.1.Hs\">",
        '  <GENESET STANDARD_NAME="HALLMARK_ONE" CATEGORY_CODE="H" EXACT_SOURCE=""'
        ' DESCRIPTION_BRIEF="Genes up-regulated &gt; 2-fold." DESCRIPTION_FULL=""'
        ' MEMBERS="TP53,KLF1"/>',
        '  <GENESET STANDARD_NAME="HALLMARK_RAW" CATEGORY_CODE="H"'
        ' EXACT_SOURCE="Table 3S: fold change (log2) < 0"'
        ' DESCRIPTION_BRIEF="Read despite the raw bracket." MEMBERS="TP53"/>',
        '  <GENESET STANDARD_NAME="HALLMARK_BARE" CATEGORY_CODE="H" MEMBERS="EGFR"/>',
        '  <GENESET STANDARD_NAME="GOBP_SOMETHING" CATEGORY_CODE="C5"'
        ' DESCRIPTION_BRIEF="Not asked for." MEMBERS="ACTB"/>',
        "</MSIGDB>",
    )
)

C5_JSON = """
{
  "GOBP_ONE": {"collection": "C5:GO:BP", "exactSource": "GO:0000012", "geneSymbols": ["APLF"]},
  "GOBP_TWO": {"collection": "C5:GO:BP", "exactSource": "GO:0000001", "geneSymbols": ["TP53"]},
  "HALLMARK_ONE": {"collection": "H", "exactSource": "", "geneSymbols": ["EGFR"]}
}
"""


def _terms(namespace=""):
    return parse_obo_terms(OBO.splitlines(), namespace)


def test_read_gmt_sets_keeps_the_second_column_whatever_it_means():
    sets = read_gmt_sets(GMT.splitlines())
    assert sets[0].secondary == "R-HSA-164843"
    assert sets[1].secondary == "http://mummichog.org/BTM/M1.0.htm"


def test_read_gmt_sets_preserves_member_order_and_drops_blank_entries():
    assert read_gmt_sets(GMT.splitlines())[0].entries == ("BANF1", "HMGA1")


def test_read_gmt_sets_keeps_a_multi_mapping_entry_whole_for_the_resolver_to_split():
    assert read_gmt_sets(GMT.splitlines())[2].entries == ("MULTIA /// MULTIB", "PLAIN")


def test_read_gmt_sets_skips_a_line_with_no_members():
    assert [s.name for s in read_gmt_sets(GMT.splitlines())] == [
        "2-LTR circle formation",
        "integrin cell surface interactions (I) (M1.0)",
        "probe module (M9)",
    ]


def test_parse_obo_flushes_a_stanza_on_any_bracket_line_not_only_term():
    terms = _terms()
    assert "part_of" not in terms, "a [Typedef] stanza must not become a term"
    assert terms["GO:0000012"].name == "single strand break repair"
    assert terms["GO:0000002"].name.startswith("obsolete "), "the typedef must not leak either way"


def test_parse_obo_ignores_the_header_before_the_first_stanza():
    assert all(term.name != "should be ignored, this is the header" for term in _terms().values())


def test_parse_obo_extracts_the_quoted_definition_and_drops_the_reference_list():
    assert _terms()["GO:0000012"].definition == "The repair of single strand breaks in DNA."


def test_parse_obo_filters_to_one_namespace_when_asked():
    assert "GO:0005524" not in _terms("biological_process"), "GO's other branches are not BP"
    assert "GO:0005524" in _terms(), "an unfiltered read keeps every namespace"


def test_parse_obo_keeps_obsolete_terms_and_flags_them():
    obsolete = _terms()["GO:0000002"]
    assert obsolete.is_obsolete
    assert obsolete.definition.startswith("OBSOLETE."), "GO's marker is in the text and stays there"


def test_parse_obo_reads_is_a_targets_without_the_trailing_name():
    assert _terms()["GO:0000012"].parents == ("GO:0006281", "GO:0006974")


def test_parse_obo_gives_an_obsolete_term_no_parents_as_go_strips_them():
    assert _terms()["GO:0000002"].parents == ()


def test_parse_obo_indexes_alternate_ids_onto_the_primary_term():
    terms = _terms()
    assert terms["GO:0019008"] is terms["GO:0000001"]
    assert terms["GO:0019008"].term_id == "GO:0000001", "the record keeps its own primary id"


# The regression that fixes the reader's shape. Proven, not assumed: the fixture is first shown to
# still defeat an XML parser, so this test fails loudly if MSigDB ever ships a well-formed file and
# the workaround stops being necessary.
def test_msigdb_descriptions_survive_a_raw_left_angle_bracket_in_an_attribute():
    with pytest.raises(ElementTree.ParseError):
        ElementTree.fromstring(MSIGDB_XML)
    found = read_msigdb_descriptions(MSIGDB_XML.splitlines(), {"HALLMARK_RAW"})
    assert found == {"HALLMARK_RAW": "Read despite the raw bracket."}


def test_msigdb_descriptions_unescape_html_entities():
    found = read_msigdb_descriptions(MSIGDB_XML.splitlines(), {"HALLMARK_ONE"})
    assert found["HALLMARK_ONE"] == "Genes up-regulated > 2-fold."


def test_msigdb_descriptions_ignore_sets_that_were_not_asked_for():
    found = read_msigdb_descriptions(MSIGDB_XML.splitlines(), {"HALLMARK_ONE"})
    assert set(found) == {"HALLMARK_ONE"}, "reading every line would materialise every MEMBERS list"


def test_msigdb_set_with_no_brief_description_reads_as_empty_not_missing():
    found = read_msigdb_descriptions(MSIGDB_XML.splitlines(), {"HALLMARK_BARE", "HALLMARK_GONE"})
    assert found == {"HALLMARK_BARE": ""}, "present-but-blank and absent must stay distinguishable"


def test_parse_geneset_attributes_reads_a_line_no_xml_parser_would_accept():
    attributes = parse_geneset_attributes(MSIGDB_XML.splitlines()[3])
    assert attributes["EXACT_SOURCE"] == "Table 3S: fold change (log2) < 0"


def test_read_msigdb_exact_sources_maps_set_names_to_term_ids():
    assert read_msigdb_exact_sources(C5_JSON) == {
        "GOBP_ONE": "GO:0000012",
        "GOBP_TWO": "GO:0000001",
    }, "a set carrying no exactSource, as every Hallmark set does, is omitted"
