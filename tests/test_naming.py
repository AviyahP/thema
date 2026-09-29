"""A name must distinguish a theme from its neighbours, and must be refusable."""

import hashlib

from thema.naming import (
    DISAMBIGUATION_FORMAT,
    LEAF_PROMPT_VERSION,
    MAX_WORDS,
    NAME_FORMAT,
    NAME_PROMPT_VERSION,
    PREFERRED_WORDS,
    RESPONSE_FORMAT,
    SYSTEM_PROMPT,
    check,
    covers_children,
    disambiguation_key,
    render_disambiguation,
    render_internal,
    render_leaf,
    theme_key,
)

#: The leaf path's bytes as of name-v4. If either changes without LEAF_PROMPT_VERSION moving with
#: it, leaves would answer from a prompt that no longer exists, so these are pinned rather than
#: recomputed. They changed on 29 Sep when the shared system prompt's line break was fixed.
LEAF_SYSTEM_SHA = "d1c9243d73ddb3ad"
LEAF_RENDER_SHA = "ada95d6410d54265"


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


def test_task_c_is_only_ever_asked_about_a_real_collision() -> None:
    """v4. The pass is withdrawn: the model is told WHAT it collides with, not asked whether."""
    rendered = render_disambiguation(
        "Nucleotide excision repair",
        collides_with=["Nucleotide excision repair"],
        repeats_parent=True,
        children=["Global genome NER", "Transcription-coupled NER"],
        taken=["Nucleotide excision repair", "DNA repair"],
    )
    assert "IDENTICAL to the name of 1 other theme" in rendered
    assert "REPEATS the name of its own parent" in rendered
    assert "true of EVERY one of them" in rendered
    assert "Global genome NER" in rendered
    assert "Give the replacement." in rendered


def test_task_c_shows_a_leaf_its_members_and_an_internal_node_its_children() -> None:
    """v4. The two have opposite rules, so they are shown different evidence."""
    leaf = render_disambiguation(
        "X", collides_with=["X"], members=[("response to caffeine", 0.8)]
    )
    assert "This theme is a leaf" in leaf and "response to caffeine" in leaf
    internal = render_disambiguation("X", collides_with=["X"], children=["A child"])
    assert "This theme is a leaf" not in internal and "A child" in internal


def test_a_revision_that_drops_a_child_is_rejected() -> None:
    """v4. name-v3 narrowed parents below their own children; this is the guard."""
    assert covers_children(
        "Wnt and Hedgehog signalling",
        ["Canonical Wnt signalling", "Hedgehog ligand reception"],
    )
    assert not covers_children(
        "Canonical Wnt destruction complex",
        ["Canonical Wnt signalling", "Hedgehog ligand reception"],
    )
    assert covers_children("anything at all", [])


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
    text = render_internal(["A", "B"], 40, unnamed_children=3)
    assert "3 further child theme(s) could not be named" in text
    assert "could not be named" not in render_internal(["A"], 40)


def test_an_internal_node_is_told_its_true_member_count() -> None:
    """It sees its children and its direct members, but must name a theme of 61."""
    assert "contains 61 pathways" in render_internal(["A"], 61)


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
    assert NAME_PROMPT_VERSION == "name-v4"


def test_the_leaf_pin_moves_with_the_leaf_prompt() -> None:
    """The leaf ledger may only lag NAME_PROMPT_VERSION while the leaf path is byte-identical.

    A leaf request is ``Request(theme_key(members), SYSTEM_PROMPT, render_leaf(...))``. Pointing it
    at an older ledger reuses completions, which is right only if those three are unchanged. On
    29 Sep the shared system prompt was edited (a line break), so LEAF_PROMPT_VERSION moved to
    name-v4 with it and currently carries nothing over. This pins the two artefacts so the next
    edit fails loudly here rather than the cache quietly answering from a prompt that is gone.
    """
    assert LEAF_PROMPT_VERSION == "name-v4"
    # The exact bytes a leaf request carries, as of name-v3.
    assert hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:16] == LEAF_SYSTEM_SHA
    rendered = render_leaf([("go", "response to caffeine", "The response to caffeine.")], [0.5])
    assert hashlib.sha256(rendered.encode()).hexdigest()[:16] == LEAF_RENDER_SHA


def test_ten_words_is_in_range_and_eleven_is_not() -> None:
    """v3. The bound is 1-10; fewer than PREFERRED_WORDS is asked for but never checked."""
    assert check(" ".join(["word"] * MAX_WORDS), ["x"]).in_range
    assert not check(" ".join(["word"] * (MAX_WORDS + 1)), ["x"]).in_range
    assert MAX_WORDS == 10 and PREFERRED_WORDS == 6
    # Seven words is over the preference and still clean: the preference is not a check.
    long_but_true = "Ubiquitin-dependent degradation of misfolded proteins by the proteasome"
    assert check(long_but_true, ["x"]).clean


def test_a_clause_with_a_verb_passes_but_a_full_sentence_does_not() -> None:
    """v3. "no verbs" is withdrawn; a clause is allowed when it is the tightest true statement."""
    assert check("Calcineurin dephosphorylates NFAT", ["x"]).clean
    assert check("Cohesin holds sister chromatids until anaphase", ["x"]).clean
    sentence = check("The cell divides.", ["x"])
    assert sentence.leading_article and sentence.trailing_punctuation and not sentence.clean


def test_general_and_overview_are_contentless() -> None:
    """v3. Both shipped in raw-build leaf names and neither says anything about the members."""
    assert check("General ER stress and UPR overview", ["x"]).empty_words == (
        "general",
        "overview",
    )
    # "Regulation of ..." stays allowed: regulation is a real biological relation, not a hedge.
    assert check("Regulation of calcium ion import", ["x"]).clean


def test_a_name_used_elsewhere_in_the_dag_is_a_duplicate() -> None:
    """v3. The raw build shipped 9 duplicate leaf names, none of them parent/sibling pairs."""
    name = "Mitotic chromosome segregation fidelity"
    assert check(name, ["x"], taken=[name]).duplicate_name
    assert not check(name, ["x"], taken=["Kinetochore attachment checking"]).duplicate_name
    assert not check(name, ["x"]).duplicate_name


def test_a_leaf_renders_each_members_inclusion() -> None:
    """v3. The model is told how strongly each member belongs, so it can exclude the weak ones."""
    rendered = render_leaf(
        [("go", "response to caffeine", "desc.")],
        inclusions=[0.31],
    )
    assert "(inclusion 0.31)" in rendered


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
    rendered = render_internal(
        ["Notch receptor processing"],
        8,
        0,
        [("gobp", "regulation of Notch signaling pathway", 0.62, "How Notch output is tuned.")],
    )
    assert "Direct members (1)" in rendered
    assert "regulation of Notch signaling pathway" in rendered
    # v4: the direct member carries its inclusion AND its full description, not a bare name.
    assert "(inclusion 0.62)" in rendered
    assert "How Notch output is tuned." in rendered
    assert "(none" in render_internal(["A child"], 3, 0, [])


def test_task_b_no_longer_shows_file_order_representative_members() -> None:
    """v4. They were member_keys[:3] in file order; "representative" was not true of them."""
    rendered = render_internal(["A child"], 900, 0, [])
    assert "Representative members" not in rendered
