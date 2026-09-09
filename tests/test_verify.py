import pytest

from test_normalize_descriptions import _pathway
from thema.verify import (
    FLAG_KINDS,
    RECHECK_PROMPT_VERSION,
    REPAIR_PROMPT_VERSION,
    VERIFY_PROMPT_VERSION,
    Flag,
    parse_flags,
    render_repair_message,
    render_verify_message,
    tally,
)


def _reply(*claims):
    import json

    return json.dumps({"claims": list(claims)})


# ------------------------------------------------------------------ prompt


# Same rule as the generator, and for a stronger reason: a checker that knows it is reading
# Reactome can rationalise Reactome's register instead of reading the claim.
def test_the_source_database_appears_nowhere_in_the_verification_prompt():
    for source in ("reactome", "go", "hallmark", "btm"):
        message = render_verify_message(_pathway(source, "R-HSA-1", "Alpha"), "Alpha does things.")
        assert source not in message.lower(), f"{source} leaked into the verification prompt"


def test_the_verifier_is_never_told_which_model_wrote_the_description():
    message = render_verify_message(_pathway("go", "GO:1", "Alpha"), "Alpha does things.")
    for token in ("opus", "sonnet", "haiku", "claude", "model", "llm", "generated"):
        assert token not in message.lower(), f"{token!r} would tell the verifier what wrote this"


def test_the_verifier_sees_the_name_the_curated_prose_the_genes_and_the_candidate():
    pathway = _pathway("reactome", "R-HSA-1", "Alpha pathway", "Alpha is curated prose.")
    message = render_verify_message(pathway, "Alpha does a thing.")
    assert "Alpha pathway" in message
    assert "Alpha is curated prose." in message
    assert "AAA" in message
    assert "CANDIDATE DESCRIPTION:" in message
    assert "Alpha does a thing." in message


def test_a_pathway_with_no_curated_prose_says_none_rather_than_showing_an_empty_line():
    pathway = _pathway("btm", "M1", "TBA", None, "no_usable_text")
    assert "Curated description: (none)" in render_verify_message(pathway, "It does things.")


# ------------------------------------------------------------------ repair


# The objection is appended to the ordinary generation prompt rather than replacing it, so the
# rewrite is still bound by every rule the original was written under.
def test_the_repair_prompt_carries_the_objection_verbatim_and_the_original_prompt():
    flags = (Flag("SLC31A2 is an iron transporter.", "wrong", "It transports copper."),)
    message = render_repair_message(_pathway("go", "GO:1", "Copper transport"), "x", flags)
    assert "SLC31A2 is an iron transporter." in message
    assert "It transports copper." in message
    assert "wrong:" in message
    assert "Input name:" in message, "the ordinary generation prompt must still be present"
    assert "AAA" in message, "the gene list must still be present"


def test_every_flag_reaches_the_repair_prompt_not_just_the_first():
    flags = (
        Flag("First claim.", "wrong", "Because one."),
        Flag("Second claim.", "unsupported", "Because two."),
    )
    message = render_repair_message(_pathway("go", "GO:1", "Alpha"), "x", flags)
    assert "First claim." in message and "Second claim." in message


# ------------------------------------------------------------- cache keys


# Three passes write to three ledger files. If any two shared a prompt version, a repair would
# overwrite the original completion, or a re-check would be served the first pass's answer.
def test_the_three_passes_use_three_distinct_prompt_versions():
    versions = (VERIFY_PROMPT_VERSION, RECHECK_PROMPT_VERSION, REPAIR_PROMPT_VERSION)
    assert len(set(versions)) == 3, "a shared version would silently serve the wrong cached answer"


# --------------------------------------------------------------- parsing


def test_a_sound_description_returns_no_flags():
    assert parse_flags(_reply()) == ()


def test_a_flag_carries_the_quote_the_kind_and_the_reason():
    flags = parse_flags(
        _reply({"quote": "SPINT1 is a protease.", "kind": "wrong", "reason": "It inhibits one."})
    )
    assert flags == (Flag("SPINT1 is a protease.", "wrong", "It inhibits one."),)


def test_a_quote_spanning_lines_is_flattened_so_it_fits_a_tsv_cell():
    flags = parse_flags(_reply({"quote": "One\n  two", "kind": "wrong", "reason": "a\tb"}))
    assert flags[0].quote == "One two"
    assert "\t" not in flags[0].reason


# An unreadable reply is never treated as "nothing wrong" -- that would silently pass a row that
# was never actually checked, which is worse than failing loudly.
def test_an_unreadable_reply_raises_rather_than_reporting_a_clean_description():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_flags("nonsense")
    with pytest.raises(ValueError, match="no 'claims' list"):
        parse_flags('{"other": []}')
    with pytest.raises(ValueError, match="unknown kind"):
        parse_flags(_reply({"quote": "x", "kind": "stylistic", "reason": "y"}))


def test_only_the_two_kinds_are_accepted():
    assert FLAG_KINDS == ("wrong", "unsupported")
    for kind in FLAG_KINDS:
        assert parse_flags(_reply({"quote": "x", "kind": kind, "reason": "y"}))[0].kind == kind


# ---------------------------------------------------------------- tally


def test_every_kind_reports_a_number_even_when_it_never_fired():
    counts = tally([()])
    for kind in FLAG_KINDS:
        assert counts[kind] == 0, f"{kind} must report zero rather than going missing"
    assert counts == {"wrong": 0, "unsupported": 0, "descriptions": 1, "flagged": 0, "flags": 0}


def test_a_description_with_two_flags_counts_once_as_flagged_and_twice_as_flags():
    counts = tally([(Flag("a", "wrong", "r"), Flag("b", "unsupported", "r")), ()])
    assert counts["descriptions"] == 2
    assert counts["flagged"] == 1
    assert counts["flags"] == 2
    assert counts["wrong"] == 1 and counts["unsupported"] == 1
