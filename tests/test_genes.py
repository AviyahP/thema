from dataclasses import replace
from datetime import date

import pytest

from thema.data.genes import Adjudication, GeneResolver, Snapshot, parse_adjudications

# The fixture is one small HGNC release, written as the real TSV so the parser is exercised too.
# Genes are chosen so that one release covers every case the resolver must handle.
#
#   HGNC:1  KLF1      approved                                   -> clean approved
#   HGNC:2  CXCL8     approved, prev IL8                         -> previous
#   HGNC:3  TP53      alias P53                                  -> alias
#   HGNC:4  AMBIA     alias DUPE                                 -> ambiguous at the alias tier
#   HGNC:5  AMBIB     alias DUPE                                 -> ambiguous at the alias tier
#   HGNC:6  NEWGENE   alias ONLYALIAS                            -> a second alias-tier match
#   HGNC:7  MULTIA / HGNC:8 MULTIB                               -> multi-mapping components
#   HGNC:20 GENEA     prev SHARED                                -> SHARED at the previous tier...
#   HGNC:21 SHARED    approved                                   -> ...and at the approved tier
#   HGNC:30 LOC5555   approved symbol shaped like a LOC name     -> approved tier must beat entrez
#   HGNC:31 DECOY     entrez 5555                                -> ...and this must not win
#   HGNC:40 GENEb     approved symbol ending in a lowercase letter -> beats the isoform strip
#   HGNC:41 GENE      the stem GENEb would strip to               -> ...and must not win
#
# withdrawn.txt supplies the rest: HGNC:100 merged into HGNC:1, HGNC:101 withdrawn outright,
# HGNC:102 split into two, and HGNC:103 -> HGNC:104 -> HGNC:3 as a two-hop merge chain.

_COLUMNS = (
    "hgnc_id\tsymbol\tname\tstatus\tprev_symbol\talias_symbol\tentrez_id\t"
    "date_approved_reserved\tdate_symbol_changed"
)


def _row(
    hgnc_id: str,
    symbol: str,
    *,
    prev: str = "",
    alias: str = "",
    entrez: str = "",
    approved: str = "1990-01-01",
    changed: str = "",
) -> str:
    return (
        f"{hgnc_id}\t{symbol}\t{symbol} gene\tApproved\t{prev}\t{alias}\t{entrez}\t"
        f"{approved}\t{changed}"
    )


COMPLETE_SET = "\n".join(
    [
        _COLUMNS,
        _row("HGNC:1", "KLF1"),
        _row("HGNC:2", "CXCL8", prev="IL8", changed="2015-06-01"),
        _row("HGNC:3", "TP53", alias="P53", entrez="7157"),
        _row("HGNC:4", "AMBIA", alias="DUPE"),
        _row("HGNC:5", "AMBIB", alias="DUPE"),
        _row("HGNC:6", "NEWGENE", alias="ONLYALIAS", approved="2019-03-01"),
        _row("HGNC:7", "MULTIA"),
        _row("HGNC:8", "MULTIB"),
        _row("HGNC:20", "GENEA", prev="SHARED", changed="2019-01-01"),
        _row("HGNC:21", "SHARED", prev="OLDB", changed="2020-01-01"),
        # LOC5555 is HGNC:30's approved symbol, while HGNC:31 holds Entrez id 5555. The approved
        # tier must win: the Entrez tier is a fallback, not a shortcut.
        _row("HGNC:30", "LOC5555"),
        _row("HGNC:31", "DECOY", entrez="5555"),
        # GENEb is HGNC:40's approved symbol while GENE is HGNC:41's: stripping the trailing
        # lowercase letter must never pre-empt a real symbol match.
        _row("HGNC:40", "GENEb"),
        _row("HGNC:41", "GENE"),
        "",
    ]
)

WITHDRAWN = "\n".join(
    [
        "HGNC_ID\tSTATUS\tWITHDRAWN_SYMBOL\tMERGED_INTO_REPORT(S) (i.e HGNC_ID|SYMBOL|STATUS)",
        "HGNC:100\tMerged/Split\tOLDMERGED\tHGNC:1|KLF1|Approved",
        "HGNC:101\tEntry Withdrawn\tGONE\t",
        "HGNC:102\tMerged/Split\tSPLITSYM\tHGNC:4|AMBIA|Approved, HGNC:5|AMBIB|Approved",
        "HGNC:103\tMerged/Split\tCHAINED\tHGNC:104|MIDDLE|Entry Withdrawn",
        "HGNC:104\tMerged/Split\tMIDDLE\tHGNC:3|TP53|Approved",
        "",
    ]
)


@pytest.fixture
def resolver() -> GeneResolver:
    return GeneResolver(Snapshot.from_tsv_text(COMPLETE_SET, WITHDRAWN))


def test_approved_symbol(resolver: GeneResolver) -> None:
    ref = resolver.resolve("KLF1")
    assert ref is not None, "an approved symbol must resolve"
    assert (ref.hgnc_id, ref.approved_symbol) == ("HGNC:1", "KLF1")
    assert ref.match_type == "approved"
    assert not ref.carried_forward


def test_previous_symbol(resolver: GeneResolver) -> None:
    ref = resolver.resolve("IL8")
    assert ref is not None, "a previous symbol must resolve"
    assert ref.hgnc_id == "HGNC:2", "IL8 is CXCL8's previous symbol"
    assert ref.approved_symbol == "CXCL8", "the ref must carry the approved symbol"
    assert ref.match_type == "previous"


def test_alias_symbol(resolver: GeneResolver) -> None:
    ref = resolver.resolve("P53")
    assert ref is not None, "an alias must resolve"
    assert (ref.hgnc_id, ref.match_type) == ("HGNC:3", "alias")


def test_ambiguous_at_the_winning_tier_returns_none_and_records_candidates(
    resolver: GeneResolver,
) -> None:
    resolution = resolver.explain("DUPE")
    assert resolution.ref is None, "an ambiguous symbol must never be guessed"
    assert resolution.outcome == "ambiguous"
    assert resolution.candidates == (("HGNC:4", "AMBIA"), ("HGNC:5", "AMBIB")), (
        "both candidate genes must be recorded for hand adjudication"
    )
    assert "HGNC:4|AMBIA" in resolution.note and "HGNC:5|AMBIB" in resolution.note


# SHARED is HGNC:21's approved symbol and HGNC:20's previous symbol. The approved tier wins
# outright; the previous tier must not be consulted, and this must not read as ambiguous. This is
# the sole guardian of tier precedence.
def test_higher_tier_match_never_falls_through_to_a_lower_tier(resolver: GeneResolver) -> None:
    resolution = resolver.explain("SHARED")
    assert resolution.outcome == "approved", "a clean approved match must not be diluted"
    assert resolution.ref is not None
    assert resolution.ref.hgnc_id == "HGNC:21"


def test_unmappable_symbol(resolver: GeneResolver) -> None:
    resolution = resolver.explain("NOTAGENE")
    assert resolution.ref is None
    assert resolution.outcome == "unmapped"


def test_withdrawn_record_is_not_a_valid_target(resolver: GeneResolver) -> None:
    resolution = resolver.explain("GONE")
    assert resolution.ref is None, "a withdrawn record must not resolve to a gene"
    assert resolution.outcome == "withdrawn"
    assert "HGNC:101" in resolution.note


def test_hop_two_follows_a_merge(resolver: GeneResolver) -> None:
    resolution = resolver.explain("OLDMERGED")
    assert resolution.outcome == "merged"
    assert resolution.ref is not None, "a merged id must carry forward, not fail"
    assert resolution.ref.hgnc_id == "HGNC:1", "hop 2 must follow the merge to the current id"
    assert resolution.ref.approved_symbol == "KLF1"
    assert resolution.ref.matched_hgnc_id == "HGNC:100", "the pre-merge id must stay visible"
    assert resolution.ref.carried_forward


def test_hop_two_follows_a_merge_chain(resolver: GeneResolver) -> None:
    resolution = resolver.explain("CHAINED")
    assert resolution.ref is not None, "a two-hop merge chain must still resolve"
    assert resolution.ref.hgnc_id == "HGNC:3", "HGNC:103 -> HGNC:104 -> HGNC:3"
    assert resolution.ref.carried_forward


def test_a_split_record_is_ambiguous_not_a_guess(resolver: GeneResolver) -> None:
    resolution = resolver.explain("SPLITSYM")
    assert resolution.ref is None, "a record split across two genes must not pick one"
    assert resolution.outcome == "ambiguous"
    assert resolution.candidates == (("HGNC:4", "AMBIA"), ("HGNC:5", "AMBIB"))


def test_resolve_set_reports_counts_and_failures(resolver: GeneResolver) -> None:
    ids, report = resolver.resolve_set(["KLF1", "IL8", "DUPE", "NOTAGENE", "GONE"])
    assert ids == {"HGNC:1", "HGNC:2"}
    counts = report.counts
    assert counts["approved"] == 1
    assert counts["previous"] == 1
    assert counts["ambiguous"] == 1
    assert counts["unmapped"] == 1
    assert counts["withdrawn"] == 1
    assert report.unmapped == ("NOTAGENE",)
    assert [r.symbol for r in report.ambiguous] == ["DUPE"]


def test_resolve_set_deduplicates_repeated_symbols(resolver: GeneResolver) -> None:
    _, report = resolver.resolve_set(["KLF1", "KLF1", " KLF1 ", ""])
    assert len(report.resolutions) == 1, "a repeated symbol must be resolved once"


def test_resolve_set_splits_multi_mapping_entries(resolver: GeneResolver) -> None:
    ids, report = resolver.resolve_set(["MULTIA /// MULTIB /// NOTAGENE"])
    assert ids == {"HGNC:7", "HGNC:8"}, "components that resolve must contribute their gene"
    assert len(report.resolutions) == 3, "one row per component, including the failure"
    assert report.multi_mapping_derived == {"HGNC:7", "HGNC:8"}, (
        "ids reached only via a split entry must be flagged for a future strict mode"
    )
    for resolution in report.resolutions:
        assert resolution.origin == "MULTIA /// MULTIB /// NOTAGENE"
        assert "multi-mapping component" in resolution.note, "provenance must reach the log"


def test_multi_mapping_flag_excludes_ids_also_seen_alone(resolver: GeneResolver) -> None:
    _, report = resolver.resolve_set(["MULTIA", "MULTIA /// MULTIB"])
    assert report.multi_mapping_derived == {"HGNC:8"}, (
        "MULTIA arrived on its own too, so only MULTIB is split-derived"
    )


# Two distinct symbols landing on one id means the source's gene sets shrink on deduplication.
def test_by_hgnc_id_exposes_within_source_collisions(resolver: GeneResolver) -> None:
    _, report = resolver.resolve_set(["CXCL8", "IL8", "KLF1"])
    grouped = report.by_hgnc_id()
    assert grouped["HGNC:2"] == ("CXCL8", "IL8"), "both spellings of one gene must be visible"
    assert grouped["HGNC:1"] == ("KLF1",)


def test_clean_approved_matches_are_excluded_from_the_log(resolver: GeneResolver) -> None:
    assert resolver.explain("KLF1").is_clean_approved
    assert not resolver.explain("IL8").is_clean_approved
    assert not resolver.explain("OLDMERGED").is_clean_approved
    assert not resolver.explain("NOTAGENE").is_clean_approved


def test_parsing_handles_pipe_delimited_and_quoted_fields() -> None:
    text = "\n".join(
        [
            _COLUMNS,
            'HGNC:9\tGENEC\tGene C\tApproved\t"OLD1|OLD2"\t"ALT1|ALT2"\t\t1990-01-01\t2014-01-01',
            "",
        ]
    )
    snapshot = Snapshot.from_tsv_text(text)
    record = snapshot.records["HGNC:9"]
    assert record.prev_symbols == ("OLD1", "OLD2")
    assert record.alias_symbols == ("ALT1", "ALT2")
    assert record.date_symbol_changed == date(2014, 1, 1)


def test_entrez_tier_decodes_a_loc_symbol(resolver: GeneResolver) -> None:
    resolution = resolver.explain("LOC7157")
    assert resolution.ref is not None, "LOC<n> decodes to Entrez Gene n"
    assert resolution.outcome == "entrez"
    assert resolution.ref.match_type == "entrez", "the tier must be distinguishable in the log"
    assert (resolution.ref.hgnc_id, resolution.ref.approved_symbol) == ("HGNC:3", "TP53")
    assert not resolution.ref.carried_forward


def test_entrez_tier_leaves_an_unknown_id_unmapped(resolver: GeneResolver) -> None:
    resolution = resolver.explain("LOC999999")
    assert resolution.ref is None, "an Entrez id HGNC does not record must not resolve"
    assert resolution.outcome == "unmapped"
    assert "999999" in resolution.note


def test_entrez_tier_is_not_consulted_when_a_higher_tier_matched(resolver: GeneResolver) -> None:
    # LOC5555 is HGNC:30's approved symbol; HGNC:31 holds Entrez id 5555. Decoding must not
    # pre-empt a real symbol match, or the fallback becomes a shortcut.
    resolution = resolver.explain("LOC5555")
    assert resolution.outcome == "approved"
    assert resolution.ref is not None
    assert resolution.ref.hgnc_id == "HGNC:30", "the approved tier owns this symbol"


def test_non_loc_symbols_never_reach_the_entrez_tier(resolver: GeneResolver) -> None:
    for symbol in ("7157", "LOC", "LOCX7157", "loc7157"):
        resolution = resolver.explain(symbol)
        assert resolution.outcome == "unmapped", f"{symbol} must not decode"
        assert resolution.ref is None


# HGNC publishes entrez_id only for approved records and withdrawn.txt carries no Entrez column,
# so a decode can never land on a merged record with real data. This builds that state directly to
# prove the tier is genuinely wired through _carry_forward and would follow a merge if it arose.
def test_entrez_tier_carries_forward_through_a_merge() -> None:
    base = Snapshot.from_tsv_text(COMPLETE_SET, WITHDRAWN)
    snapshot = replace(base, entrez_index={**base.entrez_index, "4242": "HGNC:100"})
    resolution = GeneResolver(snapshot).explain("LOC4242")

    assert resolution.outcome == "merged", "hop 2 must follow the merge, not report the dead id"
    assert resolution.ref is not None
    assert resolution.ref.hgnc_id == "HGNC:1", "HGNC:100 merged into HGNC:1"
    assert resolution.ref.match_type == "entrez", "the tier that matched must survive hop 2"
    assert resolution.ref.matched_hgnc_id == "HGNC:100"
    assert resolution.ref.carried_forward


def test_isoform_strip_resolves_when_the_stem_is_an_approved_symbol(
    resolver: GeneResolver,
) -> None:
    resolution = resolver.explain("TP53b")
    assert resolution.ref is not None, "a trailing isoform letter must strip to its stem"
    assert resolution.outcome == "isoform"
    assert (resolution.ref.hgnc_id, resolution.ref.approved_symbol) == ("HGNC:3", "TP53")
    assert resolution.ref.match_type == "isoform"


def test_isoform_strip_handles_the_dotted_form(resolver: GeneResolver) -> None:
    resolution = resolver.explain("TP53.1")
    assert resolution.ref is not None, "ROBO3.1-style labels must strip too"
    assert resolution.outcome == "isoform"
    assert resolution.ref.hgnc_id == "HGNC:3"


def test_isoform_strip_refuses_when_the_stem_does_not_resolve(resolver: GeneResolver) -> None:
    for symbol in ("NOTAGENEz", "NOTAGENE.1", "ZZTOPq"):
        resolution = resolver.explain(symbol)
        assert resolution.ref is None, f"{symbol} must not be stripped speculatively"
        assert resolution.outcome == "unmapped"


def test_isoform_strip_is_not_consulted_when_a_higher_tier_matched(resolver: GeneResolver) -> None:
    resolution = resolver.explain("GENEb")
    assert resolution.outcome == "approved", "a real symbol ending in a lowercase letter wins"
    assert resolution.ref is not None
    assert resolution.ref.hgnc_id == "HGNC:40", "must not strip to HGNC:41 GENE"


def _adjudicating(**rulings: Adjudication) -> GeneResolver:
    snapshot = Snapshot.from_tsv_text(COMPLETE_SET, WITHDRAWN)
    return GeneResolver(snapshot, {(r.source, r.symbol): r for r in rulings.values()})


def test_adjudication_assign_overrides_an_ambiguous_symbol() -> None:
    resolver = _adjudicating(
        dupe=Adjudication("reactome", "DUPE", "assign", "HGNC:4", "AMBIA", "picked A", "2026-08-24")
    )
    assert resolver.explain("DUPE").outcome == "ambiguous", "no source means no ruling applies"

    resolution = resolver.explain("DUPE", "reactome")
    assert resolution.outcome == "adjudicated"
    assert resolution.ref is not None
    assert (resolution.ref.hgnc_id, resolution.ref.approved_symbol) == ("HGNC:4", "AMBIA")
    assert resolution.ref.match_type == "adjudicated"
    assert "picked A" in resolution.note, "the rationale must reach the log"


def test_adjudication_exclude_records_an_exclusion_not_an_ambiguity() -> None:
    resolver = _adjudicating(
        dupe=Adjudication("btm", "DUPE", "exclude", "", "", "genuinely ambiguous", "2026-08-24")
    )
    resolution = resolver.explain("DUPE", "btm")
    assert resolution.outcome == "excluded"
    assert resolution.ref is None, "an exclusion resolves to no gene"
    assert "genuinely ambiguous" in resolution.note


def test_adjudication_never_overrides_a_clean_tier_match() -> None:
    resolver = _adjudicating(
        klf1=Adjudication("reactome", "KLF1", "assign", "HGNC:9", "WRONG", "should not apply", "x")
    )
    resolution = resolver.explain("KLF1", "reactome")
    assert resolution.outcome == "approved", "adjudications override the refusal and nothing else"
    assert resolution.ref is not None
    assert resolution.ref.hgnc_id == "HGNC:1"


def test_adjudication_is_scoped_to_its_source() -> None:
    resolver = _adjudicating(
        dupe=Adjudication("reactome", "DUPE", "assign", "HGNC:4", "AMBIA", "reactome only", "x")
    )
    assert resolver.explain("DUPE", "go").outcome == "ambiguous", (
        "a ruling for one source must not settle another's identically-named symbol"
    )


def test_parse_adjudications_reads_the_committed_format() -> None:
    text = (
        "source\toriginal_symbol\tdecision\thgnc_id\tapproved_symbol\trationale\tdecided_on\n"
        "go\tC18orf21\tassign\tHGNC:28802\tRMP24\tpseudogene rejected\t2026-08-24\n"
        "btm\tAG2\texclude\t-\t-\tno tiebreaker\t2026-08-24\n"
    )
    rulings = parse_adjudications(text)
    assert set(rulings) == {("go", "C18orf21"), ("btm", "AG2")}
    assert rulings[("go", "C18orf21")].hgnc_id == "HGNC:28802"
    assert rulings[("btm", "AG2")].hgnc_id == "", "a '-' cell reads as empty, as in the log"
