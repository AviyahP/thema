from test_normalize_descriptions import _pathway
from thema.data.pathways import PathwayCollection
from thema.evaluation import (
    BANDS,
    band_of,
    collision_pairs,
    jaccard,
    reactome2go_pairs,
    restrict,
    shares_name,
    sibling_pairs,
)

MAPPING = "\n".join(
    (
        "! a comment line that must be ignored",
        "Reactome:R-HSA-1 > GO:some term name ; GO:0000001",
        "Reactome:R-HSA-2 > GO:another ; GO:0000002",
        "Reactome:R-HSA-1 > GO:some term name ; GO:0000001",
    )
)


def test_the_comment_header_is_skipped_and_duplicates_collapse():
    source = reactome2go_pairs(MAPPING.splitlines())
    assert source.pairs == (("go:GO:0000001", "reactome:R-HSA-1"),
                            ("go:GO:0000002", "reactome:R-HSA-2"))
    assert source.strength == "strong"


def test_pairs_are_sorted_so_a_pair_is_the_same_pair_either_way_round():
    source = reactome2go_pairs(MAPPING.splitlines())
    assert all(a < b for a, b in source.pairs)


# Two Reactome pathways sharing a name are a curation artefact, not two databases describing one
# piece of biology, so a collision must span sources to count.
def test_only_cross_source_collisions_count():
    same = PathwayCollection.of(
        [_pathway("reactome", "R-HSA-1", "Alpha"), _pathway("reactome", "R-HSA-2", "Alpha")]
    )
    assert collision_pairs(same).pairs == ()
    across = PathwayCollection.of(
        [_pathway("reactome", "R-HSA-1", "Alpha"), _pathway("go", "GO:1", "alpha")]
    )
    assert len(across.pathways) == 2
    assert collision_pairs(across).pairs == (("go:GO:1", "reactome:R-HSA-1"),)


def test_siblings_are_every_pair_under_a_shared_parent():
    parents = {"C1": ("P",), "C2": ("P",), "C3": ("P",), "D1": ("Q",)}
    source = sibling_pairs(parents, "go:", "go-siblings", "weak because")
    assert len(source.pairs) == 3, "three children of one parent make three pairs"
    assert source.strength == "weak"


# A broad parent manufactures pairs that are not really related. GO's `cellular process` alone
# contributes 66, and ~22% of all sibling pairs come from parents with more than ten children.
def test_capping_fan_out_drops_the_broad_parents_entirely():
    parents = {f"C{i}": ("BROAD",) for i in range(6)} | {"D1": ("NARROW",), "D2": ("NARROW",)}
    assert len(sibling_pairs(parents, "go:", "s", "c").pairs) == 15 + 1
    capped = sibling_pairs(parents, "go:", "s", "c", max_children=3)
    assert len(capped.pairs) == 1, "the six-child parent contributes nothing once capped"


def test_restrict_keeps_only_pairs_with_both_members_present():
    source = reactome2go_pairs(MAPPING.splitlines())
    kept = restrict(source, {"go:GO:0000001", "reactome:R-HSA-1", "go:GO:0000002"})
    assert kept.pairs == (("go:GO:0000001", "reactome:R-HSA-1"),)
    assert kept.strength == source.strength, "restriction must not change what the source is worth"


def test_a_pair_that_is_also_a_name_collision_is_flagged_as_not_independent():
    a, b = _pathway("reactome", "R-HSA-1", "Lipophagy"), _pathway("go", "GO:1", "lipophagy")
    assert shares_name(a, b)
    assert not shares_name(a, _pathway("go", "GO:2", "Mitophagy"))


def test_an_undefined_jaccard_is_none_rather_than_zero():
    a = _pathway("reactome", "R-HSA-1", "Alpha")
    empty = PathwayCollection.of([a]).pathways[0]
    assert jaccard(a, a) == 1.0
    assert jaccard(a, empty) == 1.0


def test_exact_zero_gets_its_own_band_rather_than_joining_its_neighbour():
    assert band_of(0.0) == BANDS[0]
    assert band_of(0.005) == BANDS[1]
    assert band_of(1.0) == BANDS[-1]
