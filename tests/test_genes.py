import warnings
from datetime import date

import pytest

from thema.data.genes import (
    BTM_CUTOFF,
    CURRENT,
    ERA_2013,
    SOURCE_SNAPSHOT,
    GeneResolver,
    Snapshot,
)

# The fixture is one small HGNC release, written as the real TSV so the parser is exercised too.
# Genes are chosen so that one snapshot pair covers every case the resolver must handle. The
# cutoff throughout is BTM_CUTOFF (2013-10-08).
#
#   HGNC:1  KLF1      approved today, approved in 2013           -> clean approved
#   HGNC:2  CXCL8     approved today, prev IL8 (renamed 2015)     -> previous / era-approved
#   HGNC:3  TP53      alias P53                                   -> alias
#   HGNC:4  AMBIA     alias DUPE                                  -> ambiguous at the alias tier
#   HGNC:5  AMBIB     alias DUPE                                  -> ambiguous at the alias tier
#   HGNC:6  NEWGENE   approved 2019, alias ONLYALIAS              -> absent from the 2013 lens
#   HGNC:7  MULTIA / HGNC:8 MULTIB                                -> multi-mapping components
#   HGNC:20 GENEA     prev SHARED, renamed 2019                   -> the critical reassignment case
#   HGNC:21 SHARED    approved today, took the name in 2020       -> ...the other half of it
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
    current = Snapshot.from_tsv_text(CURRENT, COMPLETE_SET, WITHDRAWN)
    return GeneResolver({CURRENT: current, ERA_2013: current.derived(ERA_2013, BTM_CUTOFF)})


def test_current_approved_symbol(resolver: GeneResolver) -> None:
    ref = resolver.resolve("KLF1", CURRENT)
    assert ref is not None, "an approved symbol must resolve"
    assert (ref.hgnc_id, ref.approved_symbol) == ("HGNC:1", "KLF1")
    assert ref.match_type == "approved"
    assert not ref.carried_forward


def test_previous_symbol(resolver: GeneResolver) -> None:
    ref = resolver.resolve("IL8", CURRENT)
    assert ref is not None, "a previous symbol must resolve"
    assert ref.hgnc_id == "HGNC:2", "IL8 is CXCL8's previous symbol"
    assert ref.approved_symbol == "CXCL8", "the ref must carry the current approved symbol"
    assert ref.match_type == "previous"


def test_alias_symbol(resolver: GeneResolver) -> None:
    ref = resolver.resolve("P53", CURRENT)
    assert ref is not None, "an alias must resolve"
    assert (ref.hgnc_id, ref.match_type) == ("HGNC:3", "alias")


def test_ambiguous_at_the_winning_tier_returns_none_and_records_candidates(
    resolver: GeneResolver,
) -> None:
    resolution = resolver.explain("DUPE", CURRENT)
    assert resolution.ref is None, "an ambiguous symbol must never be guessed"
    assert resolution.outcome == "ambiguous"
    assert resolution.candidates == (("HGNC:4", "AMBIA"), ("HGNC:5", "AMBIB")), (
        "both candidate genes must be recorded for hand adjudication"
    )
    assert "HGNC:4|AMBIA" in resolution.note and "HGNC:5|AMBIB" in resolution.note


def test_higher_tier_match_never_falls_through_to_a_lower_tier(resolver: GeneResolver) -> None:
    # SHARED is HGNC:21's approved symbol and HGNC:20's previous symbol. The approved tier wins
    # outright; the previous tier must not be consulted, and this must not read as ambiguous.
    resolution = resolver.explain("SHARED", CURRENT)
    assert resolution.outcome == "approved", "a clean approved match must not be diluted"
    assert resolution.ref is not None
    assert resolution.ref.hgnc_id == "HGNC:21"


def test_unmappable_symbol(resolver: GeneResolver) -> None:
    resolution = resolver.explain("NOTAGENE", CURRENT)
    assert resolution.ref is None
    assert resolution.outcome == "unmapped"


def test_withdrawn_record_is_not_a_valid_target(resolver: GeneResolver) -> None:
    resolution = resolver.explain("GONE", CURRENT)
    assert resolution.ref is None, "a withdrawn record must not resolve to a gene"
    assert resolution.outcome == "withdrawn"
    assert "HGNC:101" in resolution.note


def test_hop_two_follows_a_merge(resolver: GeneResolver) -> None:
    resolution = resolver.explain("OLDMERGED", CURRENT)
    assert resolution.outcome == "merged"
    assert resolution.ref is not None, "a merged id must carry forward, not fail"
    assert resolution.ref.hgnc_id == "HGNC:1", "hop 2 must follow the merge to the current id"
    assert resolution.ref.approved_symbol == "KLF1"
    assert resolution.ref.era_hgnc_id == "HGNC:100", "the pre-merge id must stay visible"
    assert resolution.ref.carried_forward


def test_hop_two_follows_a_merge_chain(resolver: GeneResolver) -> None:
    resolution = resolver.explain("CHAINED", CURRENT)
    assert resolution.ref is not None, "a two-hop merge chain must still resolve"
    assert resolution.ref.hgnc_id == "HGNC:3", "HGNC:103 -> HGNC:104 -> HGNC:3"
    assert resolution.ref.carried_forward


def test_a_split_record_is_ambiguous_not_a_guess(resolver: GeneResolver) -> None:
    resolution = resolver.explain("SPLITSYM", CURRENT)
    assert resolution.ref is None, "a record split across two genes must not pick one"
    assert resolution.outcome == "ambiguous"
    assert resolution.candidates == (("HGNC:4", "AMBIA"), ("HGNC:5", "AMBIB"))


# The case the whole two-hop design exists for: one symbol, two genes, two eras.
def test_symbol_reassigned_between_genes_resolves_per_era(resolver: GeneResolver) -> None:
    era = resolver.explain("SHARED", ERA_2013)
    assert era.ref is not None, "SHARED was gene A's approved symbol in 2013"
    assert era.ref.hgnc_id == "HGNC:20", "the 2013 lens must return gene A, not today's owner"
    assert era.ref.approved_symbol == "GENEA", "carried forward into the current symbol space"
    assert era.ref.match_type == "approved", (
        "a symbol approved in 2013 is a clean approved match in that lens, not an alias"
    )
    assert era.ref.snapshot == ERA_2013

    today = resolver.explain("SHARED", CURRENT)
    assert today.ref is not None
    assert today.ref.hgnc_id == "HGNC:21", "the current lens must return gene B"

    assert era.ref.hgnc_id != today.ref.hgnc_id, (
        "the two lenses must disagree here, or the era lens buys nothing"
    )


def test_derived_lens_excludes_post_cutoff_symbols_from_the_approved_tier(
    resolver: GeneResolver,
) -> None:
    assert resolver.resolve("NEWGENE", CURRENT) is not None, "the gene exists today"
    assert resolver.resolve("NEWGENE", ERA_2013) is None, (
        "a symbol approved in 2019 must not be an approved match in the 2013 lens"
    )


# HGNC sometimes re-approves a record under a new symbol and clears its history, leaving the old
# name only as an alias -- SELENOF, approved 2016-09-18, no prev_symbol, alias SEP15. Dropping such
# genes from the era lens would lose the old name entirely and buy nothing, since their current
# symbol is already barred from the approved tier.
def test_derived_lens_keeps_aliases_of_genes_reapproved_after_the_cutoff(
    resolver: GeneResolver,
) -> None:
    resolution = resolver.explain("ONLYALIAS", ERA_2013)
    assert resolution.ref is not None, "an alias must survive a post-cutoff re-approval"
    assert (resolution.ref.hgnc_id, resolution.ref.match_type) == ("HGNC:6", "alias")


def test_derived_lens_keeps_a_symbol_that_never_changed(resolver: GeneResolver) -> None:
    ref = resolver.resolve("KLF1", ERA_2013)
    assert ref is not None, "an unchanged symbol must resolve in both lenses"
    assert (ref.hgnc_id, ref.match_type) == ("HGNC:1", "approved")


def test_derived_lens_promotes_a_previous_symbol_to_approved(resolver: GeneResolver) -> None:
    era = resolver.explain("IL8", ERA_2013)
    assert era.ref is not None
    assert era.ref.match_type == "approved", "IL8 was CXCL8's approved symbol in 2013"
    assert era.ref.approved_symbol == "CXCL8", "hop 2 still lands in the current symbol space"

    assert resolver.resolve("CXCL8", ERA_2013) is None, (
        "CXCL8 was adopted in 2015 and must not match in the 2013 lens"
    )


def test_resolve_set_reports_counts_and_failures(resolver: GeneResolver) -> None:
    ids, report = resolver.resolve_set(["KLF1", "IL8", "DUPE", "NOTAGENE", "GONE"], CURRENT)
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
    _, report = resolver.resolve_set(["KLF1", "KLF1", " KLF1 ", ""], CURRENT)
    assert len(report.resolutions) == 1, "a repeated symbol must be resolved once"


def test_resolve_set_splits_multi_mapping_entries(resolver: GeneResolver) -> None:
    ids, report = resolver.resolve_set(["MULTIA /// MULTIB /// NOTAGENE"], CURRENT)
    assert ids == {"HGNC:7", "HGNC:8"}, "components that resolve must contribute their gene"
    assert len(report.resolutions) == 3, "one row per component, including the failure"
    assert report.multi_mapping_derived == {"HGNC:7", "HGNC:8"}, (
        "ids reached only via a split entry must be flagged for a future strict mode"
    )
    for resolution in report.resolutions:
        assert resolution.origin == "MULTIA /// MULTIB /// NOTAGENE"
        assert "multi-mapping component" in resolution.note, "provenance must reach the log"


def test_multi_mapping_flag_excludes_ids_also_seen_alone(resolver: GeneResolver) -> None:
    _, report = resolver.resolve_set(["MULTIA", "MULTIA /// MULTIB"], CURRENT)
    assert report.multi_mapping_derived == {"HGNC:8"}, (
        "MULTIA arrived on its own too, so only MULTIB is split-derived"
    )


def test_clean_current_approved_matches_are_excluded_from_the_log(resolver: GeneResolver) -> None:
    assert resolver.explain("KLF1", CURRENT).is_clean_current_approved
    assert not resolver.explain("IL8", CURRENT).is_clean_current_approved
    assert not resolver.explain("OLDMERGED", CURRENT).is_clean_current_approved
    assert not resolver.explain("NOTAGENE", CURRENT).is_clean_current_approved


def test_source_snapshot_table_is_complete() -> None:
    assert SOURCE_SNAPSHOT["btm"] == ERA_2013, "BTM must be read through its own era"
    for source in ("reactome", "hallmark", "go"):
        assert SOURCE_SNAPSHOT[source] == CURRENT


def test_snapshot_for_falls_back_to_current_with_a_warning() -> None:
    current = Snapshot.from_tsv_text(CURRENT, COMPLETE_SET, WITHDRAWN)
    bare = GeneResolver({CURRENT: current})
    with pytest.warns(RuntimeWarning, match="unavailable"):
        assert bare.snapshot_for("btm") == CURRENT, "a missing era lens must degrade to current"


def test_snapshot_for_does_not_warn_when_the_lens_is_present(resolver: GeneResolver) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert resolver.snapshot_for("btm") == ERA_2013
        assert resolver.snapshot_for("reactome") == CURRENT


def test_resolver_requires_a_current_snapshot() -> None:
    era = Snapshot.from_tsv_text(ERA_2013, COMPLETE_SET, WITHDRAWN)
    with pytest.raises(ValueError, match="required"):
        GeneResolver({ERA_2013: era})


def test_explain_rejects_an_unknown_snapshot(resolver: GeneResolver) -> None:
    with pytest.raises(KeyError, match="unknown snapshot"):
        resolver.explain("KLF1", "1999-01")


def test_parsing_handles_pipe_delimited_and_quoted_fields() -> None:
    text = "\n".join(
        [
            _COLUMNS,
            'HGNC:9\tGENEC\tGene C\tApproved\t"OLD1|OLD2"\t"ALT1|ALT2"\t1990-01-01\t2014-01-01',
            "",
        ]
    )
    snapshot = Snapshot.from_tsv_text(CURRENT, text)
    record = snapshot.records["HGNC:9"]
    assert record.prev_symbols == ("OLD1", "OLD2")
    assert record.alias_symbols == ("ALT1", "ALT2")
    assert record.date_symbol_changed == date(2014, 1, 1)


def test_multiple_previous_symbols_are_flagged_approximate_in_the_derived_lens() -> None:
    text = "\n".join(
        [
            _COLUMNS,
            'HGNC:9\tGENEC\tGene C\tApproved\t"OLD1|OLD2"\t\t1990-01-01\t2014-01-01',
            "",
        ]
    )
    current = Snapshot.from_tsv_text(CURRENT, text)
    resolver = GeneResolver(
        {CURRENT: current, ERA_2013: current.derived(ERA_2013, BTM_CUTOFF)}
    )
    resolution = resolver.explain("OLD1", ERA_2013)
    assert resolution.ref is not None, "the best guess still resolves"
    assert resolution.approximate, (
        "only the most recent rename is dated, so this placement is a guess and must say so"
    )
    assert "approximate" in resolution.note
    assert not resolution.is_clean_current_approved, "approximate matches belong in the log"
