from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import (
    GO_BP_ROOT,
    go_ancestors,
    go_level1_branches,
    reactome_branches_of,
    reactome_roots,
    read_reactome_relation,
)

# Two human roots, one of them three levels deep, plus a node reaching both -- the 33-pathway case
# the real file has. The bovine edge must not load: a pathway whose parent is bovine is not a human
# root, and keeping the edge would invent one.
RELATION = "\n".join(
    (
        "R-HSA-100\tR-HSA-110",
        "R-HSA-110\tR-HSA-120",
        "R-HSA-120\tR-HSA-130",
        "R-HSA-200\tR-HSA-210",
        "R-HSA-200\tR-HSA-130",
        "R-BTA-100\tR-BTA-110",
        "R-HSA-999\tR-BTA-110",
    )
)

# A four-level BP chain under the root, one level-1 branch reached only through two intermediate
# terms, a second branch, a term reaching both, an obsolete term with no is_a at all, and an MF
# term that must not become a branch.
OBO = "\n".join(
    (
        "format-version: 1.2",
        "",
        "[Term]",
        "id: GO:0008150",
        "name: biological_process",
        "namespace: biological_process",
        "",
        "[Term]",
        "id: GO:0009987",
        "name: cellular process",
        "namespace: biological_process",
        "is_a: GO:0008150 ! biological_process",
        "",
        "[Term]",
        "id: GO:0002376",
        "name: immune system process",
        "namespace: biological_process",
        "is_a: GO:0008150 ! biological_process",
        "",
        "[Term]",
        "id: GO:0050000",
        "name: mid-level term",
        "namespace: biological_process",
        "is_a: GO:0009987 ! cellular process",
        "",
        "[Term]",
        "id: GO:0060000",
        "name: deep term",
        "namespace: biological_process",
        "is_a: GO:0050000 ! mid-level term",
        "",
        "[Term]",
        "id: GO:0070000",
        "name: term under two branches",
        "namespace: biological_process",
        "is_a: GO:0050000 ! mid-level term",
        "is_a: GO:0002376 ! immune system process",
        "",
        "[Term]",
        "id: GO:0000002",
        "name: obsolete something",
        'def: "OBSOLETE. It did a thing." [GOC:x]',
        "namespace: biological_process",
        "is_obsolete: true",
        "",
        "[Term]",
        "id: GO:0005524",
        "name: ATP binding",
        "namespace: molecular_function",
        "is_a: GO:0008150 ! biological_process",
        "",
    )
)


def _terms():
    return parse_obo_terms(OBO.splitlines(), namespace="biological_process")


# --------------------------------------------------------------- reactome


def test_only_human_edges_load():
    parents = read_reactome_relation(RELATION.splitlines())
    assert not any(node.startswith("R-BTA-") for node in parents)
    assert all(not p.startswith("R-BTA-") for found in parents.values() for p in found)


def test_a_human_parent_of_a_bovine_child_does_not_become_a_root():
    parents = read_reactome_relation(RELATION.splitlines())
    assert "R-HSA-999" not in parents, "the edge is cross-species and must not load at all"


def test_roots_are_the_nodes_no_edge_claims_as_a_child():
    parents = read_reactome_relation(RELATION.splitlines())
    assert reactome_roots(parents) == frozenset({"R-HSA-100", "R-HSA-200"})


def test_a_deep_pathway_reaches_its_root_through_every_intermediate_level():
    parents = read_reactome_relation(RELATION.splitlines())
    roots = reactome_roots(parents)
    assert reactome_branches_of("R-HSA-120", parents, roots) == frozenset({"R-HSA-100"})


def test_a_pathway_under_two_roots_returns_both_rather_than_picking_one():
    parents = read_reactome_relation(RELATION.splitlines())
    roots = reactome_roots(parents)
    assert reactome_branches_of("R-HSA-130", parents, roots) == frozenset(
        {"R-HSA-100", "R-HSA-200"}
    ), "the hierarchy is a DAG; deciding between two roots is the caller's job, not this walk's"


def test_a_root_is_its_own_branch():
    parents = read_reactome_relation(RELATION.splitlines())
    roots = reactome_roots(parents)
    assert reactome_branches_of("R-HSA-100", parents, roots) == frozenset({"R-HSA-100"})


# --------------------------------------------------------------------- go


def test_level1_branches_are_the_roots_direct_children_within_the_namespace():
    assert go_level1_branches(_terms()) == frozenset({"GO:0009987", "GO:0002376"}), (
        "the molecular_function term is filtered out before it can become a branch"
    )


def test_the_root_is_not_a_branch_of_itself():
    assert GO_BP_ROOT not in go_level1_branches(_terms())


# This is the regression the whole module exists for. A walk that returned only terminal roots
# would give {GO:0008150} here, whose intersection with the level-1 set is empty -- and a
# stratifier built on it would put all 7,538 GO terms in one bucket while reporting no error.
def test_ancestors_accumulate_inclusively_at_every_level_not_just_terminal_roots():
    terms = _terms()
    ancestors = go_ancestors("GO:0060000", terms)
    assert ancestors == frozenset({"GO:0060000", "GO:0050000", "GO:0009987", "GO:0008150"}), (
        "every node on the path must be accumulated, not only the one the path ends at"
    )
    assert ancestors & go_level1_branches(terms) == frozenset({"GO:0009987"})


def test_a_term_under_two_branches_reaches_both():
    terms = _terms()
    assert go_ancestors("GO:0070000", terms) & go_level1_branches(terms) == frozenset(
        {"GO:0009987", "GO:0002376"}
    )


# GO strips is_a from obsolete terms, so they are detached from the DAG and can never reach a
# branch. That is a fact about the data, and the reason they get a stratum of their own.
def test_an_obsolete_term_reaches_no_branch_because_go_detached_it():
    terms = _terms()
    assert go_ancestors("GO:0000002", terms) == frozenset({"GO:0000002"})
    assert not go_ancestors("GO:0000002", terms) & go_level1_branches(terms)


def test_a_term_absent_from_the_ontology_returns_just_itself_rather_than_raising():
    assert go_ancestors("GO:9999999", _terms()) == frozenset({"GO:9999999"})
