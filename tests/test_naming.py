"""A name must distinguish a theme from its neighbours, and must be refusable."""

import hashlib

from thema.naming import (
    LEAF_PROMPT_VERSION,
    MAX_WORDS,
    NAME_FORMAT,
    NAME_PROMPT_VERSION,
    PREFERRED_WORDS,
    RESPONSE_FORMAT,
    SYSTEM_PROMPT,
    check,
    covers_children,
    invented_words,
    narrow_child,
    render_internal,
    render_leaf,
    theme_key,
)

#: The leaf path's bytes as of name-v6. If either changes without LEAF_PROMPT_VERSION moving with
#: it, leaves would answer from a prompt that no longer exists, so these are pinned rather than
#: recomputed.
LEAF_SYSTEM_SHA = "19074b71ad0d429e"
LEAF_RENDER_SHA = "2b68f43ec74afbab"


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
    assert NAME_PROMPT_VERSION == "name-v6"


def test_the_leaf_pin_moves_with_the_leaf_prompt() -> None:
    """The leaf ledger may only lag NAME_PROMPT_VERSION while the leaf path is byte-identical.

    A leaf request is ``Request(theme_key(members), SYSTEM_PROMPT, render_leaf(...))``. Pointing it
    at an older ledger reuses completions, which is right only if those three are unchanged. On
    29 Sep the shared system prompt was edited (a line break), so LEAF_PROMPT_VERSION moved to
    name-v5 with it, so it currently carries nothing over. This pins the two artefacts so the next
    edit fails loudly here rather than the cache quietly answering from a prompt that is gone.
    """
    assert LEAF_PROMPT_VERSION == "name-v6"
    # The exact bytes a leaf request carries, as of name-v3.
    assert hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:16] == LEAF_SYSTEM_SHA
    rendered = render_leaf([("response to caffeine", "The response to caffeine.")])
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




def test_the_v5_user_message_is_data_and_one_instruction() -> None:
    """v5. Every few-shot example and every second instruction is gone from the user messages."""
    leaf = render_leaf([("response to caffeine", "The cellular response to caffeine.")])
    assert leaf.startswith("Name this cluster. Its pathways:")
    assert "response to caffeine" in leaf and "The cellular response to caffeine." in leaf
    assert "[go]" not in leaf and "inclusion" not in leaf and "go:" not in leaf
    internal = render_internal(["Wnt ligand secretion"], [("a title", "a description")])
    assert internal.startswith(
        "Name this cluster. Its child clusters (already named) and its direct pathways:"
    )
    assert "Wnt ligand secretion" in internal and "a description" in internal


def test_a_collision_resends_the_same_message_plus_one_line() -> None:
    """v5. There is no separate collision prompt -- the same data with one line appended."""
    plain = render_leaf([("response to caffeine", "The cellular response to caffeine.")])
    again = render_leaf(
        [("response to caffeine", "The cellular response to caffeine.")],
        collides_with="Caffeine response",
    )
    assert again.startswith(plain.rstrip())
    assert again[len(plain.rstrip()):].strip() == (
        "The name 'Caffeine response' is already used by another cluster; give a different name "
        "that is still true of every member and no broader."
    )


def test_there_is_only_one_naming_prompt() -> None:
    """v5. The separate disambiguation system prompt and every worked example are gone."""
    import thema.naming as naming

    assert not hasattr(naming, "DISAMBIGUATION_SYSTEM_PROMPT")
    assert not hasattr(naming, "WORKED_EXAMPLES")
    assert not hasattr(naming, "INTERNAL_EXAMPLES")
    assert "DAG" in SYSTEM_PROMPT and "nameable" in SYSTEM_PROMPT


def test_invented_word_finds_what_the_members_never_say() -> None:
    """v5. A content word absent from the members' own wording is flagged."""
    corpus = ["DNA replication", "Origins are licensed by the origin recognition complex."]
    # "licensing" is an inflection of a word the members use, so it is NOT an invention.
    assert invented_words("DNA replication and licensing", corpus) == ()
    # "kinase" appears nowhere in that corpus.
    assert invented_words("DNA replication kinase", corpus) == ("kinase",)


def test_invented_word_does_not_flag_spelling_or_connectives() -> None:
    """Both were false flags in the first calibration and both are wording, not invention."""
    # British/American spelling folded on both sides.
    assert invented_words("Humoral defence", ["humoral defense response"]) == ()
    assert invented_words("Immune signalling", ["immune signaling cascade"]) == ()
    # A relational modifier states how two named things connect, not a third thing.
    assert invented_words("Chaperone-mediated folding", ["chaperone", "protein folding"]) == ()
    # A hyphenated compound is checked by its parts: the compound itself appears in no description.
    assert invented_words("CCR7-driven trafficking", ["the receptor CCR7", "trafficking"]) == ()


def test_the_invented_word_reask_permits_a_synonym() -> None:
    """The check compares wording and cannot see a synonym, so the re-ask permits one to stay."""
    rendered = render_leaf([("a title", "a description")], invented=["ossification"])
    assert rendered.rstrip().endswith(
        "The word(s) 'ossification' appear in no member. Remove them, or replace them with what "
        "the members actually say; a genuine synonym of the members' wording may stay."
    )


def test_invented_word_is_a_mechanical_check_and_needs_a_corpus() -> None:
    """With no corpus every word would look unsupported, so the check disables itself."""
    assert check("Sterol efflux", ["x"]).invented_word == ()
    flagged = check("Sterol efflux", ["x"], corpus=["sterol binding"])
    # "transport" would NOT be flagged here: it is a bare category word, which another check owns.
    assert flagged.invented_word == ("efflux",)
    assert not flagged.clean


def test_a_child_is_rendered_with_its_rationale() -> None:
    """A bare child line lost to the direct pathways' descriptions; now it carries its sentence."""
    rendered = render_internal(
        [("Copper ion homeostasis", "All members concern intracellular copper levels.")],
        [("manganese ion transport", "Manganese is needed as a cofactor.")],
    )
    assert "Child clusters:" in rendered and "Direct pathways:" in rendered
    assert "Copper ion homeostasis" in rendered
    assert "All members concern intracellular copper levels." in rendered
    # the child's sentence must come before the direct pathways, under its own heading
    assert rendered.index("All members concern") < rendered.index("Direct pathways:")


def test_plain_child_names_still_render() -> None:
    """The bare form stays valid, so a caller with no rationale need not invent one."""
    rendered = render_internal(["A child name"], [])
    assert "A child name" in rendered and "Direct pathways:" not in rendered


def test_v6_permits_a_parent_to_take_its_childs_name() -> None:
    """The one sentence that changed, and the only thing in the prompt that did."""
    assert "except that a cluster may take" in SYSTEM_PROMPT
    assert "the child will then be" in SYSTEM_PROMPT


def test_a_displaced_child_is_told_what_its_parent_added() -> None:
    """The child must exclude the parent's direct pathways, so it is shown them in full."""
    line = narrow_child(
        "Vitamin D metabolism", [("bile acid synthesis", "Bile acids come from cholesterol.")]
    )
    assert "now named 'Vitamin D metabolism'" in line
    assert "bile acid synthesis" in line and "Bile acids come from cholesterol." in line
    assert "narrower name" in line
    rendered = render_leaf([("a title", "a description")], narrow=line)
    assert rendered.rstrip().endswith("does not also describe those added pathways.")


def test_a_parent_with_no_direct_pathways_says_none() -> None:
    """It should never render an empty list as though the parent added nothing visible."""
    assert "(none)" in narrow_child("A parent", [])
