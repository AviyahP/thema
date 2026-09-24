"""A name must distinguish a theme from its neighbours, and must be refusable."""

from thema.naming import (
    DISAMBIGUATION_FORMAT,
    MAX_WORDS,
    NAME_FORMAT,
    NAME_PROMPT_VERSION,
    RESPONSE_FORMAT,
    check,
    disambiguation_key,
    render_disambiguation,
    render_internal,
    render_leaf,
    theme_key,
)


def test_theme_key_is_the_member_set_not_the_order() -> None:
    """Names are keyed by members so they survive a rebuild that renumbers every node."""
    assert theme_key(["go:2", "go:1"]) == theme_key(["go:1", "go:2"])
    assert theme_key(["go:1", "go:2"]) != theme_key(["go:1", "go:3"])


def test_theme_key_changes_when_one_member_changes() -> None:
    """A theme that gained or lost a pathway is a different theme and must be renamed."""
    base = theme_key(["a", "b", "c"])
    assert base != theme_key(["a", "b", "c", "d"])
    assert base != theme_key(["a", "b"])


def test_a_name_repeating_its_parent_is_rejected() -> None:
    """The name's job is to distinguish; repeating the parent does not."""
    c = check("Immune signalling", ["interferon production"], parents=["Immune signalling"])
    assert c.repeats_parent and not c.clean


def test_a_name_clashing_with_a_sibling_is_rejected() -> None:
    c = check("Interferon response", ["x"], siblings=["interferon response"])
    assert c.clashes_sibling and not c.clean


def test_a_name_copying_one_member_verbatim_is_rejected() -> None:
    """Returning one member's name privileges it and misstates the group's scope."""
    c = check("Interferon alpha/beta signaling", ["Interferon alpha/beta signaling", "other"])
    assert c.copies_member and not c.clean


def test_database_names_and_identifiers_are_rejected() -> None:
    assert check("Reactome signalling", ["x"]).source_words == ("reactome",)
    assert check("Signalling by GO:0006954", ["x"]).identifiers == ("go_id",)
    assert not check("Signalling by GO:0006954", ["x"]).clean


def test_contentless_names_are_rejected() -> None:
    """'Various signalling pathways' labels a group without naming it."""
    assert check("Various signalling pathways", ["x"]).empty_words == ("pathways", "various")
    assert not check("Various signalling pathways", ["x"]).clean


def test_a_good_name_passes_every_check() -> None:
    c = check(
        "Interferon response",
        ["interferon-gamma production", "Interferon alpha/beta signaling"],
        parents=["Immune signalling"],
        siblings=["Interleukin signalling"],
    )
    assert c.clean and c.words == 2


def test_length_is_measured_not_truncated() -> None:
    long = " ".join(["word"] * (MAX_WORDS + 3))
    c = check(long, ["x"])
    assert c.words == MAX_WORDS + 3 and not c.in_range and not c.clean


def test_a_root_says_it_has_no_parent_rather_than_omitting_the_line() -> None:
    assert "(none -- this is a root)" in render_disambiguation("X", [], [])


def test_the_response_contract_allows_refusal() -> None:
    """`nameable: false` is a permitted answer; an invented name for a grab-bag is worse."""
    props = RESPONSE_FORMAT["schema"]["properties"]  # type: ignore[index]
    assert set(props) == {"nameable", "name", "rationale"}
    assert props["nameable"]["type"] == "boolean"
    assert RESPONSE_FORMAT["schema"]["additionalProperties"] is False  # type: ignore[index]


def test_rationale_is_required_in_both_branches() -> None:
    """One field that always explains, rather than `rationale` or `reason` depending on outcome.

    A JSON schema cannot make a field conditionally required, and two keys for one job forces
    every consumer to branch on `nameable` before it can read the explanation.
    """
    assert set(NAME_FORMAT["schema"]["required"]) == {"nameable", "name", "rationale"}  # type: ignore[index]


def test_disambiguation_has_its_own_contract_and_only_two_actions() -> None:
    props = DISAMBIGUATION_FORMAT["schema"]["properties"]  # type: ignore[index]
    assert props["revise"]["type"] == "boolean", (
        "must be a boolean: extract_text returns the whole object only for a non-string key"
    )
    assert set(DISAMBIGUATION_FORMAT["schema"]["required"]) == {"revise", "name", "reason"}  # type: ignore[index]


def test_an_internal_node_is_told_how_many_children_could_not_be_named() -> None:
    """An unnameable child is a hole in the evidence and the parent must be told."""
    text = render_internal(["A", "B"], [("go", "x", "d")], 40, unnamed_children=3)
    assert "3 further child theme(s) could not be named" in text
    assert "could not be named" not in render_internal(["A"], [("go", "x", "d")], 40)


def test_an_internal_node_is_told_its_true_member_count() -> None:
    """It sees 3 descriptions but must name a theme of 61, and must know that."""
    assert "contains 61 pathways" in render_internal(["A"], [("go", "x", "d")], 61)


def test_a_leaf_shows_descriptions_not_only_names() -> None:
    text = render_leaf([("go", "interferon-gamma production", "Cells release IFN-gamma.")])
    assert "interferon-gamma production" in text and "Cells release IFN-gamma." in text


def test_bare_category_words_are_rejected_but_qualified_ones_pass() -> None:
    """Checked as a set, so a distinguishing term rescues a category word."""
    assert check("Metabolism", ["x"]).bare_category
    assert check("Signalling", ["x"]).bare_category
    assert check("Cellular response", ["x"]).bare_category
    assert not check("Sterol transport", ["x"]).bare_category
    assert not check("Innate immune signalling", ["x"]).bare_category


def test_container_nouns_are_contentless() -> None:
    assert check("Cell cycle processes", ["x"]).empty_words == ("processes",)
    assert check("Immune pathways", ["x"]).empty_words == ("pathways",)


def test_prompt_version_is_part_of_the_contract() -> None:
    assert NAME_PROMPT_VERSION == "name-v2"


def test_an_internal_nodes_key_includes_its_childrens_names() -> None:
    """Rename a child and the parent must be regenerated, even with identical membership.

    Keying an internal node on members alone would match after a child was renamed, silently
    reusing a parent name derived from a name that no longer exists.
    """
    members = ["go:1", "go:2"]
    before = theme_key(members, child_names=["Interferon response"])
    after = theme_key(members, child_names=["Type I interferon response"])
    assert before != after
    assert theme_key(members) != before, "a leaf and an internal node are different requests"


def test_the_key_cascade_reaches_every_ancestor() -> None:
    """Renaming a leaf must invalidate its parent AND its grandparent."""
    parent_before = theme_key(["a", "b"], ["leaf name"])
    parent_after = theme_key(["a", "b"], ["leaf RENAMED"])
    assert parent_before != parent_after
    assert theme_key(["a", "b", "c"], [parent_before]) != theme_key(["a", "b", "c"], [parent_after])


def test_child_name_order_does_not_change_the_key() -> None:
    assert theme_key(["a"], ["x", "y"]) == theme_key(["a"], ["y", "x"])


def test_disambiguation_is_cached_on_its_own_inputs() -> None:
    """It depends on parents and siblings, not on the theme's members."""
    name, par, sib = "Interferon response", ["Immune signalling"], ["Interleukin signalling"]
    base = disambiguation_key(name, par, sib)
    assert base == disambiguation_key(name, par, sib)
    assert base != disambiguation_key(name, ["Cytokine signalling"], sib)
    assert base != disambiguation_key(name, par, ["Chemokine signalling"])


def test_structure_rules() -> None:
    assert check("The interferon response", ["x"]).leading_article
    assert check("Interferon response.", ["x"]).trailing_punctuation
    assert not check("Interferon Response", ["x"]).sentence_case
    assert check("Interferon response", ["x"]).clean


def test_gene_symbols_and_acronyms_survive_the_sentence_case_check() -> None:
    """Capitals are recognised structurally, not from a list of biology that would go stale."""
    for name in (
        "Signalling by NF-kB",
        "TP53 regulation",
        "SARS-CoV-1 replication",
        "mRNA splicing",
        "mTOR signalling",
    ):
        assert check(name, ["other"]).sentence_case, name


def test_a_chemical_locant_is_not_a_capitalisation_error() -> None:
    """O-, N-, C- and S- prefixes are chemistry; only the locant may be upper-case."""
    assert check("Protein O-glycosylation", ["x"]).sentence_case
    assert check("N-linked glycan trimming", ["x"]).sentence_case
    assert not check("Protein Glycosylation", ["x"]).sentence_case


def test_a_hyphenated_compound_is_one_content_word() -> None:
    """Splitting it flagged the fragment "associated" as contentless, which it is not."""
    assert check("Hemophilia-associated factor VIII defects", ["x"]).empty_words == ()
    # standalone, it is still contentless -- only the hyphenated compound is spared
    assert check("Regulation of associated processes", ["x"]).empty_words == (
        "associated", "processes",
    )


def test_an_internal_node_states_its_direct_members() -> None:
    """A single-child node is broader than its child exactly by the members no child holds."""
    rendered = render_internal(["Notch receptor processing"], [], 8, 0,
                               [("gobp", "regulation of Notch signaling pathway")])
    assert "Direct members (1)" in rendered
    assert "regulation of Notch signaling pathway" in rendered
    assert "(none" in render_internal(["A child"], [], 3, 0, [])
