from pathlib import Path

from filter_reactome_membership import (
    DISCARD_COLUMNS,
    classify,
    descendants,
    load_exports,
    load_hgnc,
    read_gmt_rows,
    write_tsv,
)
from thema.data.genes import GeneRef

# Two identifiers per gene, as HGNC gives: Entrez and Ensembl. A hit on either passes.
GENE = frozenset({"7157", "ENSG00000141510"})


def _ref(match_type: str = "approved", hgnc_id: str = "HGNC:11998") -> GeneRef:
    return GeneRef(
        hgnc_id=hgnc_id,
        approved_symbol="TP53",
        match_type=match_type,
        carried_forward=False,
        matched_hgnc_id=hgnc_id,
    )


def test_0_symbol_resolving_to_nothing_is_discarded() -> None:
    d = classify(None, "R-HSA-1", GENE, set(), set())
    assert (d.test, d.keep) == (0, False)
    assert d.provenance == ""


def test_1_identifier_paired_with_this_pathway_is_confirmed() -> None:
    d = classify(_ref(), "R-HSA-1", GENE, {("7157", "R-HSA-1")}, {"7157"})
    assert (d.test, d.keep, d.provenance) == (1, True, "confirmed")


def test_1_a_hit_in_the_ensembl_identifier_alone_passes() -> None:
    d = classify(_ref(), "R-HSA-1", GENE, {("ENSG00000141510", "R-HSA-1")}, {"ENSG00000141510"})
    assert (d.test, d.keep) == (1, True), "the two exports are unioned; either identifier suffices"


def test_2_covered_elsewhere_but_not_here_is_discarded() -> None:
    d = classify(_ref(), "R-HSA-1", GENE, {("7157", "R-HSA-999")}, {"7157"})
    assert (d.test, d.keep) == (2, False)
    assert "covered" in d.reason


# Order is the whole design: a gene paired here AND covered elsewhere must confirm, not discard.
def test_1_beats_2_when_both_conditions_hold() -> None:
    pairs = {("7157", "R-HSA-1"), ("7157", "R-HSA-999")}
    d = classify(_ref(), "R-HSA-1", GENE, pairs, {"7157"})
    assert d.test == 1, "the first test that fires decides the row"


def test_3_uncovered_approved_symbol_is_kept_as_fill() -> None:
    d = classify(_ref(), "R-HSA-1", GENE, set(), set())
    assert (d.test, d.keep, d.provenance) == (3, True, "gmt_fill")


def test_4_uncovered_non_approved_match_is_discarded() -> None:
    for match_type in ("previous", "alias", "entrez", "isoform"):
        d = classify(_ref(match_type), "R-HSA-1", GENE, set(), set())
        assert (d.test, d.keep) == (4, False), f"{match_type} must not be trusted uncorroborated"


# mtDNA protein, rRNA and tRNA genes come off one polycistronic transcript, so the exports cover
# the tRNAs but not the proteins in transcript-processing pathways. Test 2's premise fails there.
def test_mitochondrial_genes_are_exempt_from_test_2() -> None:
    covered, pairs = {"7157"}, {("7157", "R-HSA-999")}
    assert classify(_ref(), "R-HSA-1", GENE, pairs, covered).test == 2

    d = classify(_ref(), "R-HSA-1", GENE, pairs, covered, mitochondrial=True)
    assert (d.test, d.keep, d.provenance) == (3, True, "mtdna_exempt"), (
        "an exempted keep must stay distinguishable from an ordinary gmt_fill"
    )


def test_mitochondrial_exemption_does_not_rescue_a_non_approved_match() -> None:
    d = classify(
        _ref("alias"), "R-HSA-1", GENE, {("7157", "R-HSA-999")}, {"7157"}, mitochondrial=True
    )
    assert (d.test, d.keep) == (4, False), "HN-style alias collisions must still be discarded"


def test_load_exports_filters_species_and_evidence(tmp_path: Path) -> None:
    path = tmp_path / "X2Reactome_All_Levels.txt"
    path.write_text(
        "7157\tR-HSA-1\turl\tName\tTAS\tHomo sapiens\n"
        "7157\tR-HSA-2\turl\tName\tIEA\tHomo sapiens\n"
        "9999\tR-CEL-3\turl\tName\tTAS\tCaenorhabditis elegans\n",
        encoding="utf-8",
    )
    pairs, covered = load_exports([path], frozenset({"TAS", "IEA"}))
    assert pairs == {("7157", "R-HSA-1"), ("7157", "R-HSA-2")}, "non-human pathways are excluded"
    assert covered == {"7157"}

    pairs_tas, _ = load_exports([path], frozenset({"TAS"}))
    assert pairs_tas == {("7157", "R-HSA-1")}, "the TAS slice must drop IEA rows"


def test_load_hgnc_indexes_identifiers_and_the_mitochondrial_genome(tmp_path: Path) -> None:
    path = tmp_path / "hgnc.txt"
    path.write_text(
        "hgnc_id\tsymbol\tlocus_type\tlocation\tentrez_id\tensembl_gene_id\n"
        "HGNC:1\tTP53\tgene with protein product\t17p13.1\t7157\tENSG00000141510\n"
        "HGNC:2\tMT-CO1\tgene with protein product\tmitochondria\t4512\tENSG00000198804\n",
        encoding="utf-8",
    )
    identifiers, locus, mito = load_hgnc(path)
    assert identifiers["HGNC:1"] == {"7157", "ENSG00000141510"}
    assert locus["HGNC:2"] == "gene with protein product"
    assert mito == {"HGNC:2"}, "the exemption keys on location, not on the MT- symbol prefix"


def test_descendants_walks_the_pathway_hierarchy(tmp_path: Path) -> None:
    path = tmp_path / "rel.txt"
    path.write_text(
        "R-HSA-root\tR-HSA-a\nR-HSA-a\tR-HSA-b\nR-HSA-other\tR-HSA-c\nR-BTA-x\tR-BTA-y\n",
        encoding="utf-8",
    )
    assert descendants(path, "R-HSA-root") == {"R-HSA-root", "R-HSA-a", "R-HSA-b"}


def test_read_gmt_rows_yields_one_row_per_member(tmp_path: Path) -> None:
    path = tmp_path / "sets.gmt"
    path.write_text("Name One\tR-HSA-1\tTP53\tKLF1\nName Two\tR-HSA-2\tTP53\n", encoding="utf-8")
    assert read_gmt_rows(path) == [
        ("R-HSA-1", "Name One", "TP53"),
        ("R-HSA-1", "Name One", "KLF1"),
        ("R-HSA-2", "Name Two", "TP53"),
    ]


def test_written_tsv_is_stable_across_runs(tmp_path: Path) -> None:
    path = tmp_path / "out.tsv"
    rows = [("R-HSA-1", "Name", "TP53", "HGNC:1", "approved", "2", "reason")]
    write_tsv(path, DISCARD_COLUMNS, rows)
    first = path.read_text(encoding="utf-8")
    write_tsv(path, DISCARD_COLUMNS, rows)
    assert path.read_text(encoding="utf-8") == first
    assert not list(tmp_path.glob("*.part")), "the temporary file must not survive"
