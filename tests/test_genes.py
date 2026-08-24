from datetime import date

import pytest

from thema.data.genes import GeneResolver, Snapshot

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
#
# withdrawn.txt supplies the rest: HGNC:100 merged into HGNC:1, HGNC:101 withdrawn outright,
# HGNC:102 split into two, and HGNC:103 -> HGNC:104 -> HGNC:3 as a two-hop merge chain.

_COLUMNS = (
    "hgnc_id\tsymbol\tname\tstatus\tprev_symbol\talias_symbol\t"
    "date_approved_reserved\tdate_symbol_changed"
)


def _row(
    hgnc_id: str,
    symbol: str,
    *,
    prev: str = "",
    alias: str = "",
    approved: str = "1990-01-01",
    changed: str = "",
) -> str:
    return f"{hgnc_id}\t{symbol}\t{symbol} gene\tApproved\t{prev}\t{alias}\t{approved}\t{changed}"


COMPLETE_SET = "\n".join(
    [
        _COLUMNS,
        _row("HGNC:1", "KLF1"),
        _row("HGNC:2", "CXCL8", prev="IL8", changed="2015-06-01"),
        _row("HGNC:3", "TP53", alias="P53"),
        _row("HGNC:4", "AMBIA", alias="DUPE"),
        _row("HGNC:5", "AMBIB", alias="DUPE"),
        _row("HGNC:6", "NEWGENE", alias="ONLYALIAS", approved="2019-03-01"),
        _row("HGNC:7", "MULTIA"),
        _row("HGNC:8", "MULTIB"),
        _row("HGNC:20", "GENEA", prev="SHARED", changed="2019-01-01"),
        _row("HGNC:21", "SHARED", prev="OLDB", changed="2020-01-01"),
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
            'HGNC:9\tGENEC\tGene C\tApproved\t"OLD1|OLD2"\t"ALT1|ALT2"\t1990-01-01\t2014-01-01',
            "",
        ]
    )
    snapshot = Snapshot.from_tsv_text(text)
    record = snapshot.records["HGNC:9"]
    assert record.prev_symbols == ("OLD1", "OLD2")
    assert record.alias_symbols == ("ALT1", "ALT2")
    assert record.date_symbol_changed == date(2014, 1, 1)
