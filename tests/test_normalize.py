import re

from thema.data.pathways import Pathway
from thema.normalize import (
    MAX_WORDS,
    MIN_WORDS,
    PROMPT_VERSION,
    PROVENANCE,
    SYSTEM_PROMPT,
    display_name,
    genes_for_prompt,
    provenance_of,
    render_user_message,
    strip_markup,
    strip_name,
    summarize,
    validate,
    word_count,
)


def _pathway(
    source="reactome",
    source_id="R-HSA-1",
    name="Alpha pathway",
    description="Alpha does a thing.",
    symbols=(("HGNC:1", ("AAA",)), ("HGNC:2", ("BBB", "CCC"))),
    text_availability="described",
):
    genes = frozenset(identifier for identifier, _ in symbols)
    return Pathway(
        source=source,
        source_id=source_id,
        name=name,
        description_source=description,
        description_source_from="reactome_summation" if description else "none",
        description_generated=None,
        description_generated_from=None,
        genes=genes,
        gene_symbols=tuple(symbols),
        n_genes=len(genes),
        n_dropped=0,
        dropped_symbols=(),
        degradation="ok",
        drop_fraction=0.0,
        text_availability=text_availability,
    )


# ------------------------------------------------------------------ prompt


# The whole point of normalization is to erase source-specific register. Leaking the source name
# into the prompt would hand the model exactly the signal we are trying to remove.
def test_the_source_database_appears_nowhere_in_the_rendered_prompt():
    for source in ("reactome", "go", "hallmark", "btm"):
        message = render_user_message(_pathway(source=source))
        assert source not in message.lower(), f"{source} leaked into the prompt"


def test_the_source_id_is_not_shown_either_because_it_names_the_database_as_surely():
    message = render_user_message(_pathway(source_id="R-HSA-109581"))
    assert "R-HSA-109581" not in message


# 2,612 genes is the largest set. Any truncation rule would bias exactly the pathways where the
# sample matters most, so there is no truncation rule.
def test_the_gene_list_is_never_truncated_however_long_it_is():
    symbols = tuple((f"HGNC:{i}", (f"GENE{i}",)) for i in range(2612))
    message = render_user_message(_pathway(symbols=symbols))
    for i in (0, 1305, 2611):
        assert f"GENE{i}" in message, f"GENE{i} was dropped from the prompt"


def test_several_symbols_meeting_on_one_gene_are_all_shown():
    assert genes_for_prompt(_pathway()) == ("AAA", "BBB", "CCC")


def test_symbols_are_sorted_so_two_runs_render_the_same_prompt():
    forward = _pathway(symbols=(("HGNC:1", ("ZZZ",)), ("HGNC:2", ("AAA",))))
    backward = _pathway(symbols=(("HGNC:2", ("AAA",)), ("HGNC:1", ("ZZZ",))))
    assert render_user_message(forward) == render_user_message(backward)


def test_a_pathway_with_no_description_says_none_rather_than_showing_an_empty_line():
    message = render_user_message(_pathway(description=None, text_availability="name_only"))
    assert "Input description: (none)" in message


# The 47 Reactome pathways that resolved to no genes at all still get a prompt.
def test_a_pathway_with_no_genes_renders_a_prompt_rather_than_failing():
    message = render_user_message(_pathway(symbols=()))
    assert "Input genes: (none)" in message


# ------------------------------------------------------------- provenance


def test_provenance_has_exactly_the_three_values_the_decision_names():
    assert set(PROVENANCE.values()) == {"description+name+genes", "name+genes", "genes"}


def test_provenance_follows_text_availability_and_nothing_else():
    assert provenance_of(_pathway(text_availability="described")) == "description+name+genes"
    assert provenance_of(_pathway(text_availability="name_only")) == "name+genes"
    assert provenance_of(_pathway(text_availability="no_usable_text")) == "genes"


# A zero-gene pathway is still `described`, so it is still description+name+genes. genes_shown
# carries the fact that no genes were shown, rather than a fourth enum value.
def test_a_zero_gene_described_pathway_keeps_its_provenance_and_shows_no_genes():
    pathway = _pathway(symbols=())
    assert provenance_of(pathway) == "description+name+genes"
    assert genes_for_prompt(pathway) == ()


# ------------------------------------------------------------- validator


def _body(text=""):
    """A description of legal length, with `text` spliced in."""
    filler = " ".join(["cells"] * (MIN_WORDS + 5 - word_count(text)))
    return f"Alpha pathway {text} {filler}".strip()


def test_a_clean_description_trips_nothing():
    assert validate(_body(), "Alpha pathway").clean


def test_go_identifiers_are_caught():
    found = validate(_body("relates to GO:0006915 broadly"), "Alpha pathway").identifiers
    assert [f.kind for f in found] == ["go_id"]


def test_reactome_identifiers_are_caught():
    found = validate(_body("see R-HSA-109581 for detail"), "Alpha pathway").identifiers
    assert [f.kind for f in found] == ["reactome_id"]


def test_hallmark_identifiers_are_caught():
    found = validate(_body("overlaps HALLMARK_APOPTOSIS strongly"), "Alpha pathway").identifiers
    assert [f.kind for f in found] == ["hallmark_id"]


def test_kegg_and_wikipathways_identifiers_are_caught_though_neither_is_a_v1_source():
    kegg = validate(_body("mirrors hsa04210 closely"), "Alpha pathway").identifiers
    wiki = validate(_body("mirrors WP254 closely"), "Alpha pathway").identifiers
    assert [f.kind for f in kegg] == ["kegg_id"]
    assert [f.kind for f in wiki] == ["wikipathways_id"]


def test_naming_a_database_is_caught():
    for text, kind in (
        ("the Reactome pathway covers", "reactome"),
        ("this Gene Ontology entry states", "gene_ontology"),
        ("drawn from MSigDB directly", "msigdb"),
        ("a hallmark gene set covering", "hallmark_set"),
    ):
        found = validate(_body(text), "Alpha pathway").references
        assert kind in [f.kind for f in found], f"{text!r} was not caught"


# "A hallmark of cancer" is ordinary English. Matching bare "hallmark" would fire on a large share
# of legitimate cancer biology and make the whole check useless, so it is deliberately not matched.
def test_a_hallmark_of_cancer_is_ordinary_english_and_is_not_flagged():
    assert validate(_body("sustained proliferation is a hallmark of cancer"), "Alpha").clean


# Describing a relationship in ordinary language is the thematic content we want, not a recited
# database edge. The validator must leave it alone.
def test_functional_relationships_in_plain_language_are_not_flagged():
    for phrase in (
        "a subtype of apoptosis",
        "part of cell cycle control",
        "downstream of interferon signalling",
    ):
        assert validate(_body(phrase), "Alpha pathway").clean, f"{phrase!r} was flagged"


def test_a_short_description_is_out_of_range_and_says_so():
    result = validate("Alpha pathway is short.", "Alpha pathway")
    assert not result.in_range
    assert "length" in [f.kind for f in result.findings]


def test_a_long_description_is_out_of_range():
    long = " ".join(["Alpha pathway"] + ["word"] * MAX_WORDS)
    assert not validate(long, "Alpha pathway").in_range


def test_a_description_that_never_names_its_pathway_fails_the_echo_check():
    result = validate(" ".join(["cells"] * (MIN_WORDS + 5)), "Alpha pathway")
    assert not result.name_echoed
    assert "name_echo" in [f.kind for f in result.findings]


# BTM's 87 TBA modules have no real name to echo, and the prompt tells the model to open with the
# biology instead. Demanding an echo of "TBA" would fail all 87 for obeying the instruction.
def test_a_placeholder_name_is_not_held_to_the_echo_check():
    assert validate(_body(), "TBA").name_echoed


# The v2 prompt asks the model to open with the name in DOUBLE QUOTES. The echo check strips
# punctuation from both sides before matching, so this passes -- but it is the one thing that
# prompt change could plausibly have broken, so it is pinned rather than reasoned about.
def test_a_quoted_name_still_echoes():
    quoted = '"Alpha pathway" is what this describes. ' + " ".join(["cells"] * MIN_WORDS)
    assert validate(quoted, "Alpha pathway").name_echoed


# Curly quotes too: a model that types the name in typographic quotes has still echoed it.
def test_a_curly_quoted_name_still_echoes():
    quoted = "\u201cAlpha pathway\u201d is what this describes. " + " ".join(["cells"] * MIN_WORDS)
    assert validate(quoted, "Alpha pathway").name_echoed


def test_summarize_counts_every_check_including_the_ones_that_never_fired():
    results = [
        validate(_body("relates to GO:0006915 broadly"), "Alpha pathway"),
        validate(_body(), "Alpha pathway"),
    ]
    tally = summarize(results)
    assert tally["total"] == 2
    assert tally["clean"] == 1
    assert tally["go_id"] == 1
    assert tally["reactome_id"] == 0, "a check that never fired must still report a zero"


# ------------------------------------------------------------ hallmark names


# All 50 Hallmark "names" are the database's own identifiers. Repeating one, as the prompt asks the
# model to do, would write a database identifier into all 50 descriptions and hand a reader the
# source -- so the name is humanized for the prompt while Pathway.name keeps what MSigDB published.
def test_a_hallmark_identifier_is_never_shown_to_the_model():
    pathway = _pathway(source="hallmark", name="HALLMARK_INTERFERON_ALPHA_RESPONSE")
    assert display_name(pathway) == "Interferon alpha response"
    assert "HALLMARK" not in render_user_message(pathway)


def test_gene_symbols_inside_a_hallmark_name_keep_their_case():
    for raw, shown in (
        ("HALLMARK_TNFA_SIGNALING_VIA_NFKB", "TNFA signaling via NFKB"),
        ("HALLMARK_IL6_JAK_STAT3_SIGNALING", "IL6 JAK STAT3 signaling"),
        ("HALLMARK_PI3K_AKT_MTOR_SIGNALING", "PI3K AKT MTOR signaling"),
        ("HALLMARK_MYC_TARGETS_V1", "MYC targets V1"),
        ("HALLMARK_G2M_CHECKPOINT", "G2M checkpoint"),
    ):
        assert display_name(_pathway(source="hallmark", name=raw)) == shown


def test_the_stored_name_is_untouched_because_the_loader_owns_it():
    pathway = _pathway(source="hallmark", name="HALLMARK_APOPTOSIS")
    display_name(pathway)
    assert pathway.name == "HALLMARK_APOPTOSIS"


def test_no_other_source_has_its_name_rewritten():
    for source, name in (
        ("reactome", "Interleukin-6 signaling"),
        ("go", "citrulline metabolic process"),
        ("btm", "enriched in B cells (I)"),
    ):
        assert display_name(_pathway(source=source, name=name)) == name


# GO is the only v1 source with deprecated terms, so "obsolete" in a name hands the model the
# database. The 124 that carry it are stripped for the prompt only; the record keeps what GO
# published, and the description the model sees still opens "OBSOLETE.".
def test_an_obsolete_go_term_loses_the_marker_from_its_prompt_name():
    pathway = _pathway(source="go", name="obsolete citrulline metabolic process")
    assert display_name(pathway) == "citrulline metabolic process"
    assert pathway.name == "obsolete citrulline metabolic process"


def test_obsolete_is_stripped_only_as_a_prefix_and_only_for_go():
    assert display_name(_pathway(source="go", name="response to obsolete signal")) == (
        "response to obsolete signal"
    )
    assert display_name(_pathway(source="reactome", name="obsolete thing")) == "obsolete thing"


# The humanized name is what the model was asked to echo, so it is what the echo check must look
# for. Checking against the raw identifier would fail all 50 for obeying the instruction.
def test_the_echo_check_uses_the_name_the_model_was_actually_shown():
    pathway = _pathway(source="hallmark", name="HALLMARK_INTERFERON_ALPHA_RESPONSE")
    body = _body("Interferon alpha response covers the antiviral program")
    assert validate(body, display_name(pathway)).name_echoed


# ------------------------------------------------------------- output residue


# Structured output guarantees the response's shape, not its content. Two of the first thirty-six
# sampled descriptions were valid JSON whose string carried stray braces, one of them a visible
# self-correction. Both would have gone into committed, embedded prose unnoticed.
def test_stray_braces_from_the_response_format_are_caught():
    result = validate(_body("and remodeling}}"), "Alpha pathway")
    assert "json_residue" in [f.kind for f in result.findings]
    assert not result.clean


def test_a_visible_self_correction_is_caught():
    result = validate(_body("into reactive species. wait fix formatting"), "Alpha pathway")
    assert "self_correction" in [f.kind for f in result.findings]


def test_a_dangling_quote_at_the_end_is_caught():
    assert not validate(_body() + '"', "Alpha pathway").clean


# Ordinary prose must not trip it, or the check is worthless at 10,817 rows.
def test_ordinary_prose_carries_no_residue():
    assert validate(_body("the beta-catenin destruction complex"), "Alpha pathway").clean


# --------------------------------------------------------- name stripping


# The v3 prompt makes every description open with its own name, and the collision test defines its
# positives BY name. Both members of a pair therefore carry the same string in the embedded text,
# so the score is inflated by an unknown amount until the name is removed and it is re-measured.
def test_the_quoted_name_is_removed():
    text = '"Chylomicron assembly" is how the small intestine packages dietary fat.'
    assert strip_name(text, "Chylomicron assembly") == (
        "is how the small intestine packages dietary fat."
    )


def test_an_unquoted_repeat_later_in_the_text_goes_too():
    text = '"Alpha pathway" is a thing. Alpha pathway also needs APOB.'
    out = strip_name(text, "Alpha pathway")
    assert "Alpha pathway" not in out
    assert "needs APOB" in out


# GO publishes lowercase names and the model often capitalises the first letter when quoting them.
def test_a_case_changed_echo_is_still_removed():
    text = '"Angiogenesis involved in wound healing" is the sprouting of new capillaries.'
    out = strip_name(text, "angiogenesis involved in wound healing")
    assert "ngiogenesis involved in wound healing" not in out


def test_curly_quotes_are_handled_like_straight_ones():
    text = "“Alpha pathway” is a thing."
    assert strip_name(text, "Alpha pathway") == "is a thing."


# Nothing is paraphrased: the name is deleted and the surrounding words fall where they fall.
# Rewriting the sentence would substitute one intervention for another and measure that instead.
def test_the_rest_of_the_sentence_is_left_exactly_as_it_was():
    text = '"Alpha pathway" is the canonical route, requiring ATP and Mg2+.'
    assert strip_name(text, "Alpha pathway") == "is the canonical route, requiring ATP and Mg2+."


def test_a_description_that_never_names_itself_is_returned_unchanged():
    text = "This module has no title and is described from its genes alone."
    assert strip_name(text, "TBA") == text


def test_an_empty_name_changes_nothing():
    assert strip_name("Alpha does a thing.", "") == "Alpha does a thing."


# ------------------------------------------------------------ v4 prompt


def _flat(text=None):
    """The prompt with line wrapping collapsed, so assertions match sentences not line breaks."""
    return re.sub(r"\s+", " ", SYSTEM_PROMPT if text is None else text)


# 982 Reactome summations carry HTML, kept verbatim on the row for the as-is A/B arm. The model
# copied it into 3 of 1,854 v3 completions, so v4 stops showing it any: removal beats prohibition,
# because a rule against writing markup competes with an example of markup.
def test_markup_is_stripped_from_the_prompt_but_not_from_the_row():
    pathway = _pathway(description="Alpha does a thing.<br><br>Then <i>another</i>.")
    message = render_user_message(pathway)
    assert "<br>" not in message and "<i>" not in message
    assert "Alpha does a thing. Then another." in message
    assert pathway.description_source == "Alpha does a thing.<br><br>Then <i>another</i>.", (
        "the row keeps its markup; the 2026-08-21 A/B arm compares sources as published"
    )


def test_stripping_markup_leaves_no_gap_before_punctuation():
    assert strip_markup("Gamma (see <b>note</b>), then delta.") == "Gamma (see note), then delta."
    assert strip_markup("<i>Emphasis</i> and <a href='x'>a link</a>.") == "Emphasis and a link."


def test_a_description_with_no_markup_is_untouched():
    assert strip_markup("plain prose, unchanged") == "plain prose, unchanged"
    assert strip_markup(None) == ""
    assert strip_markup("") == ""


# The v3 rule "Begin by repeating the pathway's name in double quotes" put the same string inside
# both members of every collision pair and gave 33/47 of one family a shared opening.
def test_the_prompt_no_longer_mandates_a_quoted_name_first():
    assert "Begin by repeating the pathway's name in double quotes" not in _flat()
    assert "Do not open with the name in quotation marks." in _flat()
    assert "it need not come first" in _flat()


# "If the genes support a claim, state it" is the diagnosed cause of the 27 wrong claims. Two
# opposing rules would leave the model weighing them, so the anti-hedging rule is gone outright.
def test_the_anti_hedging_rule_is_gone_rather_than_softened():
    assert "if the genes support a claim, state it" not in _flat()
    assert "Do not hedge" not in _flat()
    assert "Accuracy comes before confidence." in _flat()


def test_the_precision_section_names_the_four_things_to_be_sure_of():
    assert "PRECISION ON GENE-LEVEL CLAIMS" in _flat()
    for rule in ("molecular identity", "direction of effect", "substrate or partner"):
        assert rule in _flat(), f"{rule!r} missing from the precision section"
    assert "that the gene is actually in the list you were given" in _flat()
    assert "A single gene from another tissue refutes the claim." in _flat()


# Models copy examples more reliably than they follow prose, so a worked example that opens with
# the shape the prompt now forbids would undo the instruction.
def test_neither_worked_example_opens_with_a_forbidden_template():
    pattern = r"^Output: (.+?)(?=\n\nInput name|\n\nOUTPUT FORMAT)"
    outputs = re.findall(pattern, SYSTEM_PROMPT, re.S | re.M)
    assert len(outputs) == 2
    for text in outputs:
        assert not text.lstrip().startswith('"'), "no example may open with the quoted name"
        assert not text.lstrip().startswith("This pathway is"), "nor with the v3 second template"
        assert MIN_WORDS <= len(text.split()) <= MAX_WORDS, "an example must obey its own band"
    first, second = (t.split()[0].lower() for t in outputs)
    assert first != second, "the two openings must not share a first word"


def test_bumping_the_prompt_version_is_what_separates_the_caches():
    assert PROMPT_VERSION == "v4"
