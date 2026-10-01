"""Name a theme: the prompt, the response contract, and the mechanical checks.

A theme's ``label`` is null until this runs. The placeholder in ``demo.py`` joins distinctive
member terms with a separator no curator would write, precisely so it reads as machine output and
is never mistaken for a name.

Three decisions shape everything here.

**A name is keyed by its MEMBER SET, not by a node id.** Node ids (``n0000``) are assigned per
build, by size then bitset key, so a rebuild renames everything and no name would survive. A theme
IS its members, so the key is the sha256 of its sorted member keys. A rebuild then reuses every
name whose theme is unchanged and pays only for themes that actually moved -- the same property
that makes the description ledger affordable.

**Naming runs BOTTOM-UP, then a separate top-down pass disambiguates.**

Generation is bottom-up because top-down does not scale. A root theme has hundreds of members, so a
top-down name would be derived from a SAMPLE of them and would describe the slice rather than the
node. Bottom-up has bounded input at every level: measured on the 1,201-theme build, leaves hold a
median of 4 members and at most 7, and internal nodes have a median of 2 children and at most 95
short names. Nothing ever needs truncating.

- A LEAF is named from its member pathways -- name and description.
- An INTERNAL node is named from its CHILDREN'S NAMES, plus about three representative member
  descriptions so that one bad child name cannot compound up the tree.
- An unnameable child leaves a hole, and the parent falls back to member descriptions for the
  share its named children do not cover.

Disambiguation is a SECOND, top-down pass. It walks down the DAG and checks each name against ALL
its parents and against the siblings under each parent -- a node may have several parents, and a
name that distinguishes it from one while duplicating another is not distinguishing. It rewrites
ONLY where a name repeats a parent or collides with a sibling. Generate first, disambiguate second.

**Disambiguation is terminal: it does not feed back into generation.** A parent was named from its
children's GENERATED names, and disambiguation may later sharpen one of those. That is accepted
rather than iterated, because feeding it back would loop. It is bounded: disambiguation fires only
on a collision and only makes a name more specific, so the parent's summary of its children's
subjects remains true.

**If a parent cannot be made broader than its dominant child, no name is forced.** It is reported
instead, because that is a signal the intermediate node may be redundant -- and papering over it
with a strained name would hide exactly the structural fact worth seeing.

**A theme that cannot be named says so.** ``nameable: false`` is a permitted answer and carries a
reason. Some themes are genuinely heterogeneous -- the build measures recurrence, not
interpretability -- and an invented name for a grab-bag is worse than an honest refusal, because a
name is what a reader sees in an enrichment result and they cannot audit it.

Pathway NAMES are used here, and that is not in tension with stripping them from descriptions.
Names were kept out of the embedded text because clustering on a naming convention is not
clustering on biology (DECISIONS.md, 23 Sep). Naming is the one task where the names are the
evidence.
"""

import hashlib
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from thema.normalize import IDENTIFIER_PATTERNS

#: Bumped whenever the prompt changes in a way that should invalidate cached names. Part of the
#: cache key, so a bump renames rather than silently mixing two prompts in one table.
#
# name-v6 (29 Sep): ONE sentence of the system prompt changes. A cluster may take one of its
# children's names when that is the tightest true name for it, and the CHILD is then renamed
# narrower. Aviyah's design, after a level-1 read found the dominant fault was a parent named
# narrower than its own child: forbidding the parent from repeating the child forced it either to
# invent a difference or to name itself after its direct pathways. Nothing else in the prompt moves.
#
# name-v5 (29 Sep): the prompt layer replaced rather than patched. ONE prompt for leaves, internal
# nodes and collision re-asks; the user message is data with a single line of instruction; every
# worked example, source tag, inclusion value and identifier removed.
#
# name-v4 (28 Sep): Task B's three "representative members" are removed -- they were
# member_keys[:3] in FILE ORDER, so "representative" described nothing -- and every DIRECT member is
# now rendered in full with source, name, inclusion and description. The full Task C pass is
# WITHDRAWN: collisions are detected by string comparison and only the colliding names go to the
# model, whose replacement must cover every child for an internal node. See
# LEAF_PROMPT_VERSION -- leaf requests are byte-identical to name-v3 and their names carry over.
#
# name-v3 (27 Sep): "overview" joins the contentless list; a worked NEGATIVE example for over-reach;
# names must be unique across the WHOLE DAG, not only against parents and siblings; member
# INCLUSIONS are shown and coverage is stated in terms of them; Task C tests sibling discrimination
# against each sibling's MEMBERS rather than its name alone. Nothing from name-v2 carries over: the
# prompt changed, so the content-addressed cache must not answer.
#
# name-v2: Task B now states a node's DIRECT members -- those in no child. Under v1 an internal
# node saw only child names and three samples, so a single-child node was indistinguishable from
# its child and could only be refused as a restatement. That was 8 of 12 refusals in the first
# smoke run. Bumped rather than edited in place: the prompt changed, so the cache must not answer.
NAME_PROMPT_VERSION = "name-v6"

#: The version LEAF requests are cached under. **Equal to NAME_PROMPT_VERSION as of 29 Sep**, so
#: it carries nothing over right now -- kept because the mechanism is correct and will earn its
#: keep the next time only Task B or Task C changes.
#:
#: Every change in name-v4 is confined to Task B's user message and to Task C. A leaf's request is
#: ``Request(theme_key(member_keys), SYSTEM_PROMPT, render_leaf(...))`` and all three parts are
#: unchanged: ``SYSTEM_PROMPT`` is untouched (the Task B wording lives in ``render_internal``, not
#: in
#: the shared system prompt), ``render_leaf`` is untouched, and ``theme_key`` has never depended on
#: the prompt version. So the request bytes are identical and the ledger key is identical -- what
#: changed is only WHICH FILE the ledger reads, since a ledger is opened per (model, version).
#: Pointing leaves at name-v3 therefore reuses all 285 leaf completions for $0.00, while every
#: internal node and every disambiguation call is a miss and is regenerated.
#:
#: A test asserts the two are equal only when the leaf path is genuinely unchanged; bump this the
#: moment SYSTEM_PROMPT or render_leaf changes, or leaves will silently answer from the wrong
#: prompt.
LEAF_PROMPT_VERSION = "name-v6"

#: A name is a phrase a biologist would accept as a heading. Bounds are enforced by instruction and
#: MEASURED here, never by truncation.
MIN_WORDS = 1
MAX_WORDS = 10

#: Above this the name is longer than a heading wants to be, but it is not wrong. The hard bound is
#: :data:`MAX_WORDS`; this is the length the prompt asks for and is not a check -- a name that is
#: seven words because seven words are what the members share is a better name than a six-word one
#: that is broader than they are.
PREFERRED_WORDS = 6

#: How many member names the prompt shows. A theme of 250 members cannot be pasted whole, and the
#: medoid-first ordering means the ones shown are the ones nearest the theme's centre.
MAX_MEMBERS_SHOWN = 40

#: Source names must not appear in a name: "Reactome signalling" names a database, not biology.
SOURCE_WORDS = frozenset({"reactome", "hallmark", "msigdb", "btm", "gobp", "go"})

#: A name may not open with an article: "The interferon response" is a sentence fragment where a
#: heading is wanted, and articles sort badly in any list.
LEADING_ARTICLES = frozenset({"the", "a", "an"})

#: Words that carry no subject, so two names sharing only these share nothing. Used by
#: :func:`_content_words` for the parent-coverage check, not by any naming rule.
_STRUCTURAL = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "to", "by", "via", "with", "from", "for", "into",
    "at", "on", "its", "their", "regulation", "response",
})

#: Words that make a name say nothing. A theme called "Regulation of cellular processes" has been
#: labelled without being named.
EMPTY_WORDS = frozenset(
    {"various", "diverse", "multiple", "several", "miscellaneous", "general", "generic",
     "assorted", "related", "associated", "other", "misc",
     # "overview" names the act of summarising rather than the biology summarised. "General ER
     # stress and UPR overview" was a real name; two of its three content words said nothing.
     "overview",
     # Plural container nouns. "Cell cycle processes" says no more than "Cell cycle" and reads
     # as padding; the theme is the biology, not the fact that it is a set of pathways.
     "processes", "pathways", "mechanisms", "functions", "activities"}
)

#: Words that name a CATEGORY rather than a subject. A name built only from these has been
#: filed, not named: "Metabolism", "Signalling", "Immune processes". Checked as a set -- a name
#: is rejected only when EVERY content word is one of these, so "Sterol transport" and "Innate
#: immune signalling" pass while "Transport" and "Signalling" do not. It cannot catch every
#: over-broad name (nothing mechanical can), but it catches the worst without a model call.
BARE_CATEGORIES = frozenset(
    {"metabolism", "metabolic", "signalling", "signaling", "signal", "transduction",
     "transport", "trafficking", "regulation", "response", "immune", "immunity", "cellular",
     "cell", "biology", "biosynthesis", "catabolism", "development", "differentiation",
     "homeostasis", "organisation", "organization", "assembly", "binding", "activation"}
)

#: Tasks A and B. ``rationale`` is REQUIRED in both branches and carries the refusal reason when
#: ``nameable`` is false: a JSON schema cannot make a field conditionally required, and two keys
#: for one job ("rationale" when naming, "reason" when refusing) means every consumer branches on
#: ``nameable`` before it can read the explanation. One field, always present, always explaining.
NAME_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "nameable": {"type": "boolean"},
            "name": {"type": "string"},
            "rationale": {"type": "string"},
        },
        "required": ["nameable", "name", "rationale"],
        "additionalProperties": False,
    },
}

#: Task C. ``name`` and ``reason`` are empty when ``revise`` is false.
#:
#: ``revise`` is a BOOLEAN rather than an action enum for a mechanical reason worth stating:
#: ``llm.extract_text`` returns the whole parsed object only when the keyed field is not a string,
#: and returns just that field's value when it is. With every field a string there is no way to
#: recover the rest of the reply. The boolean is therefore also the response key.
DISAMBIGUATION_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "revise": {"type": "boolean"},
            "name": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["revise", "name", "reason"],
        "additionalProperties": False,
    },
}

#: Which field each schema is read through. Both are booleans, so ``extract_text`` hands back the
#: entire object instead of one field -- see the note on DISAMBIGUATION_FORMAT.
NAME_RESPONSE_KEY = "nameable"
DISAMBIGUATION_RESPONSE_KEY = "revise"

#: Kept as an alias so older callers do not break.
RESPONSE_FORMAT = NAME_FORMAT


def theme_key(members: Iterable[str], child_names: Iterable[str] = ()) -> str:
    """The stable identity of a naming REQUEST: what the name was derived from.

    Args:
        members: The theme's pathway keys, in any order.
        child_names: The generated names of this theme's children, for an internal node. Empty
            for a leaf.

    Returns:
        A hex digest. Two requests with the same inputs have the same key in every build, which is
        what lets a name survive a rebuild and pay only for themes that actually moved.

    An internal node's name is derived from its children's NAMES, so the member set alone is not
    its identity: rename a child while the parent's membership is unchanged and a member-only hash
    would match, silently reusing a parent name built from a name that no longer exists. The
    children's names are therefore part of the key, which also makes the invalidation cascade
    correct -- renaming a leaf invalidates its parent, its grandparent, and so on up.
    """
    parts = ["members"] + sorted(members)
    if child_names:
        parts += ["children"] + sorted(child_names)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def disambiguation_key(name: str, parents: Iterable[str], siblings: Iterable[str]) -> str:
    """The identity of a DISAMBIGUATION request, cached separately from generation.

    Args:
        name: The generated name being checked.
        parents: Every parent's final name.
        siblings: Every sibling name under any of those parents.

    Returns:
        A hex digest over exactly the inputs the decision depends on.
    """
    parts = [name, "parents", *sorted(parents), "siblings", *sorted(siblings)]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class NameCheck:
    """What the mechanical validator measured. Nothing here rewrites the name.

    Attributes:
        words: Word count.
        in_range: Whether ``words`` is within :data:`MIN_WORDS`-:data:`MAX_WORDS`. The prompt asks
            for fewer than :data:`PREFERRED_WORDS`, which is a preference and not checked: a longer
            name that is true of the members beats a shorter one that is not.
        identifiers: Database identifiers found in the name.
        source_words: Source names found.
        empty_words: Contentless words found.
        bare_category: Whether every content word is a bare category word, so the name files the
            theme without naming it.
        leading_article: Whether the name opens with "the", "a" or "an".
        trailing_punctuation: Whether the name ends in punctuation. A heading is not a sentence.
        sentence_case: Whether capitalisation looks like sentence case -- first word capitalised,
            later words lowercase unless they are gene symbols, acronyms or proper nouns (any token
            with an internal capital, a digit, or fully upper-case, which covers NF-kB, TP53,
            SARS-CoV-1 and Golgi-adjacent forms without trying to know biology). The FIRST word may
            also be such a symbol: "mRNA splicing" and "mTOR signalling" are correctly capitalised
            names that begin lowercase, and demanding a capital there would reject real biology.
        copies_member: Whether the name is verbatim one member's pathway name.
        repeats_parent: Whether the name equals a parent's name.
        clashes_sibling: Whether the name equals a sibling's name.
        invented_word: Content words of the name occurring nowhere in the members' own wording.
            See :func:`invented_words`. It finds words the model supplied rather than read; it
            cannot tell a genuine synonym from an invention, which is why the re-ask permits a
            synonym to stay rather than the check repairing anything.
        duplicate_name: Whether the name is already in use by any other theme ANYWHERE in the
            hierarchy, not only among parents and siblings. The raw build shipped 9 duplicated
            leaf names, one of them on two unrelated themes in different subtrees, which neither
            the parent check nor the sibling check could see.
        clean: Every check passed.
    """

    words: int
    in_range: bool
    leading_article: bool
    trailing_punctuation: bool
    sentence_case: bool
    identifiers: tuple[str, ...]
    source_words: tuple[str, ...]
    empty_words: tuple[str, ...]
    bare_category: bool
    copies_member: bool
    repeats_parent: bool
    clashes_sibling: bool
    duplicate_name: bool
    invented_word: tuple[str, ...]

    @property
    def clean(self) -> bool:
        """Whether the name passed every mechanical check."""
        return (
            self.in_range
            and not self.leading_article
            and not self.trailing_punctuation
            and self.sentence_case
            and not self.identifiers
            and not self.source_words
            and not self.empty_words
            and not self.bare_category
            and not self.copies_member
            and not self.repeats_parent
            and not self.clashes_sibling
            and not self.duplicate_name
            and not self.invented_word
        )


#: Stereochemical and positional locants that legitimately capitalise the head of a word:
#: O-glycosylation, N-linked, C-terminal, S-nitrosylation. They are chemistry, not sentence case.
CHEMICAL_PREFIX = re.compile(r"^[ONCS]-(?=[a-z])")


def _has_chemical_prefix(word: str) -> bool:
    """Whether a word opens with a chemical locant and is otherwise lowercase.

    Args:
        word: One word of a name.

    Returns:
        True for "O-glycosylation" or "N-linked"; False for "O-GlcNAc", which :func:`_is_symbol`
        already covers on its internal capital.
    """
    stripped = word.strip("(),/")
    return bool(CHEMICAL_PREFIX.match(stripped)) and stripped[2:].islower()


def _is_symbol(word: str) -> bool:
    """Whether a word may legitimately carry capitals inside a sentence-case name.

    Gene symbols, acronyms and proper nouns are not lower-cased. Recognised structurally -- an
    internal capital, any digit, or wholly upper-case -- rather than by consulting a list of
    biology, which would go stale and would never be complete.
    """
    stripped = word.strip("(),/-")
    return (
        stripped.isupper()
        or any(c.isdigit() for c in stripped)
        or any(c.isupper() for c in stripped[1:])
    )


def _norm(text: str) -> str:
    """Lowercase, collapse whitespace, drop surrounding punctuation, for comparison only."""
    return re.sub(r"\s+", " ", text.strip().strip(".,;:").lower())


def collisions(name: str, others: Iterable[str]) -> tuple[str, ...]:
    """Which of ``others`` is the same name as ``name``.

    Case, surrounding punctuation and whitespace are folded -- the same comparison every other
    collision check in this module uses.

    A duplicate name is settled by string comparison, so it is settled here rather than by asking a
    model to scan every name in the hierarchy.

    Args:
        name: The proposed name.
        others: Names in use by other themes.

    Returns:
        The colliding names, deduplicated and sorted. Empty when the name is unique.
    """
    target = _norm(name)
    return tuple(sorted({o for o in others if _norm(o) == target}))


def _content_words(text: str) -> set[str]:
    """The name's content words, lowercased, with structural words dropped.

    Args:
        text: A name.

    Returns:
        Content words. Hyphenated compounds are kept whole AND split, so "Wnt-dependent" matches a
        child named "Canonical Wnt signalling".
    """
    words = set()
    for token in re.findall(r"[a-z][a-z-]*", _norm(text)):
        if token in _STRUCTURAL:
            continue
        words.add(token)
        words.update(part for part in token.split("-") if part and part not in _STRUCTURAL)
    return words


def covers_children(name: str, children: Sequence[str]) -> bool:
    """Whether a replacement parent name could still be true of every child's name.

    Mechanical and deliberately weak. It asserts one thing only: the replacement must not be a
    NARROWING that drops a child's subject entirely. A child whose name shares no content word with
    the parent's, where the original parent name did share one, is evidence the revision walked away
    from that child. The check cannot read biology, so it is used to REJECT a revision and never to
    accept one -- a revision that passes is not thereby correct.

    Under name-v3 the disambiguation pass had no such guard and narrowed parents below their own
    children in 2 of the 3 wrong parents found in the 20-node read.

    Args:
        name: The proposed replacement.
        children: The children's names.

    Returns:
        True when every child still shares a content word with the name, or when there are no
        children to cover.
    """
    if not children:
        return True
    words = _content_words(name)
    if not words:
        return False
    return all(_content_words(child) & words for child in children)


#: Words that carry no subject of their own, so their absence from the members says nothing.
#: Separate from :data:`EMPTY_WORDS`: these are allowed in a name, they are merely not evidence.
_FUNCTION_WORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "to", "by", "via", "with", "from", "for", "into",
    "at", "on", "its", "their", "as", "is", "are", "be", "not", "no", "non", "other", "both",
    # Relational modifiers. They state how two named things connect, not a third thing, so their
    # absence from the members is not an invention: "Chaperone-mediated folding" invents nothing
    # if the members say chaperone and folding. Every one of these was a false flag in the first
    # calibration run.
    "driven", "mediated", "dependent", "independent", "induced", "based", "coupled", "linked",
    "guided", "gated", "restricted", "associated", "specific", "like", "including", "downstream",
    "upstream", "control", "regulation", "response", "signalling", "signaling", "pathway",
})

#: Suffixes stripped, longest first, when matching a name's word against the members' wording. The
#: point is to ALLOW inflection -- "replication" must match "replicate", "licensing" must match
#: "license" -- so the stemmer is deliberately generous. A false miss here flags a real word as
#: invented, which is the costlier error.
_SUFFIXES = (
    "ations", "ation", "isation", "ization", "ising", "izing", "ised", "ized", "ing", "ies",
    "ers", "er", "ed", "es", "s", "ally", "ity", "ic", "al", "ly",
)


def _stem(word: str) -> str:
    """Strip one inflectional suffix, if what remains is still a word.

    Args:
        word: A lowercased token.

    Returns:
        The stem, or the word unchanged when no suffix applies.
    """
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


#: Spelling pairs folded before matching, so a name written one way is not called an invention
#: because the members wrote it the other. Applied to both sides.
_SPELLING = (("ise", "ize"), ("isa", "iza"), ("our", "or"), ("lling", "ling"), ("lled", "led"),
             ("ence", "ense"), ("aemia", "emia"), ("oe", "e"), ("ae", "e"))


def _fold(word: str) -> str:
    """Normalise British/American spelling before matching.

    Args:
        word: A lowercased token.

    Returns:
        The folded form.
    """
    for british, american in _SPELLING:
        word = word.replace(british, american)
    return word


def _words_of(text: str) -> set[str]:
    """Content tokens of a text, with hyphenated compounds SPLIT.

    A compound is split and not kept whole: "ccr7-driven" as a unit appears in no description by
    construction, so checking it would flag every hyphenated name. What can be checked is whether
    the members say "ccr7" and "driven".

    Args:
        text: Any text.

    Returns:
        Lowercased tokens.
    """
    out: set[str] = set()
    for token in re.findall(r"[a-z0-9][a-z0-9-]*", text.lower()):
        if "-" in token:
            out.update(part for part in token.split("-") if part)
        else:
            out.add(token)
    return out


def invented_words(name: str, corpus: Iterable[str]) -> tuple[str, ...]:
    """Content words of ``name`` that occur nowhere in the members' own wording.

    A name may name only what is there. This finds the commonest way that fails -- a word the model
    supplied rather than read -- by requiring every content word to appear somewhere in the
    members' titles and descriptions, case-insensitively and allowing inflection. For an internal
    node the corpus is its children's names plus its direct members' titles and descriptions.

    It cannot see a genuine synonym: a name saying "licensing" where the members say "origin firing"
    is flagged, and the re-ask says so, permitting a real synonym to stay. It also cannot see the
    opposite fault -- a member the name fails to cover -- which is not mechanical.

    Function words and the already-banned words are exempt: their absence says nothing, and they are
    caught by :data:`_FUNCTION_WORDS` and the other checks respectively.

    Args:
        name: The proposed name.
        corpus: The members' wording -- titles, descriptions, and for an internal node the
            children's names.

    Returns:
        The unsupported words, deduplicated and sorted. Empty when every content word is supported.
    """
    haystack = " ".join(corpus).lower()
    folded = _fold(haystack)
    stems = {_stem(_fold(w)) for w in _words_of(haystack)}
    banned = EMPTY_WORDS | SOURCE_WORDS | BARE_CATEGORIES
    missing = set()
    for word in _words_of(name):
        if word in _FUNCTION_WORDS or word in banned or len(word) < 3:
            continue
        if word in haystack or _fold(word) in folded or _stem(_fold(word)) in stems:
            continue
        missing.add(word)
    return tuple(sorted(missing))


def check(
    name: str,
    members: Sequence[str],
    parents: Sequence[str] = (),
    siblings: Sequence[str] = (),
    taken: Sequence[str] = (),
    corpus: Sequence[str] = (),
) -> NameCheck:
    """Run every mechanical check over one proposed name.

    Args:
        name: The proposed name.
        members: The theme's member pathway NAMES (not keys).
        parents: The parents' names, where already assigned.
        siblings: The siblings' names, where already assigned.
        taken: Every name already assigned to another theme anywhere in the hierarchy. Pass the
            whole set, not the neighbourhood: duplicates in the raw build sat in different subtrees.
        corpus: The members' own wording -- titles and descriptions, plus a child's name for an
            internal node. Empty disables :attr:`invented_word`, since with no corpus every word
            would be unsupported.

    Returns:
        What was measured. A failing check is reported, never repaired: a silent repair hides the
        rate at which the prompt fails.
    """
    parts = name.split()
    words = len(parts)
    lowered = _norm(name)
    # A hyphenated compound is one content word: "hemophilia-associated" is a single modifier
    # and splitting it flags the fragment "associated" as contentless, which it is not here.
    tokens = {t for t in re.findall(r"[a-z]+(?:-[a-z]+)*", lowered) if t}
    later = parts[1:]
    return NameCheck(
        words=words,
        in_range=MIN_WORDS <= words <= MAX_WORDS,
        leading_article=bool(parts) and parts[0].lower() in LEADING_ARTICLES,
        trailing_punctuation=bool(name.strip()) and name.strip()[-1] in ".,;:!?",
        sentence_case=(
            bool(parts)
            and (parts[0][:1].isupper() or _is_symbol(parts[0]))
            and all(w.islower() or _is_symbol(w) or _has_chemical_prefix(w) for w in later)
        ),
        identifiers=tuple(
            label for label, pattern in IDENTIFIER_PATTERNS if pattern.search(name)
        ),
        source_words=tuple(sorted(tokens & SOURCE_WORDS)),
        empty_words=tuple(sorted(tokens & EMPTY_WORDS)),
        bare_category=bool(tokens) and tokens <= BARE_CATEGORIES,
        copies_member=any(_norm(m) == lowered for m in members),
        repeats_parent=any(_norm(p) == lowered for p in parents),
        clashes_sibling=any(_norm(s) == lowered for s in siblings),
        duplicate_name=any(_norm(t) == lowered for t in taken),
        invented_word=invented_words(name, corpus) if corpus else (),
    )


SYSTEM_PROMPT = """\
You name clusters in an ontology of human biological pathways. The ontology is a DAG: a
hierarchy of clusters, each made of pathways and/or child clusters. A pathway is a set of genes
co-acting in a specific biological process, given here with its title and a description.

The name you give a cluster must state the biological theme or process shared by ALL of its
members — every pathway and every child cluster listed — as tightly as possible: the most specific
theme that is true of all of them. Do not generalise further than the members require; a broader
name belongs to the parent, one level up. What drives the name is shared biological meaning, not
shared wording.

Name only what the members contain. Do not assert a gene, mechanism, compartment or pathway that
only one or two members concern. A name that is too broad is a minor fault; a name that invents is
a serious one, because a reader cannot tell.

Every name will sit beside hundreds of others in a browsable hierarchy, so every name must read as
though written by the same person on the same day. Up to 10 words, fewer than 6 preferred; sentence
case; no leading article; a noun phrase unless a short clause is tighter. No filler words
("various", "related", "processes", "pathways", "mechanisms"), no database names, no identifiers,
no bare category words ("Metabolism", "Signalling"), and never one member's own title as the name.
A name must not be identical to any other name in the hierarchy — except that a cluster may take
one of its children's names when that is the tightest true name for it; the child will then be
renamed.

If the members share no nameable biological theme — if the only name covering all of them would
cover much else besides, or would be an invention — say so. That is a real and useful answer.

Return an object: {"nameable": true|false, "name": "<name, or empty>", "rationale": "<one
sentence: what the members share, or why they cannot be named>"}.
"""


#: The one line added to a user message when the name it produced collides. There is no second
#: prompt: the model sees the same system prompt and the same data, plus this.
COLLISION_LINE = (
    "The name '{name}' is already used by another cluster; give a different name that is still "
    "true of every member and no broader."
)

#: The lines added when a CHILD must move because its parent took its name. name-v6 resolves a
#: parent-child collision by narrowing the child, not the parent: forbidding the parent from
#: repeating its child forced it either to invent a difference or to name itself after its direct
#: pathways, which is what the level-1 read found in 28 of 215 nodes. The child is told what the
#: parent now is and what it added, so the difference it must express is on the page rather than
#: guessed at.
NARROW_CHILD_LINES = (
    "Your parent cluster is now named '{parent}'. It contains you plus these pathways:\n"
    "{added}\n"
    "Give yourself a narrower name, true of all your members, that does not also describe those "
    "added pathways."
)

#: The one line added when a name uses words the members never say. Same shape as the collision
#: re-ask -- same prompt, same data, one line -- and it explicitly permits a genuine synonym,
#: because the check compares wording and cannot tell a synonym from an invention.
INVENTED_LINE = (
    "The word(s) '{words}' appear in no member. Remove them, or replace them with what the members "
    "actually say; a genuine synonym of the members' wording may stay."
)


def narrow_child(parent: str, added: Sequence[tuple[str, str]]) -> str:
    """The instruction appended to a child whose parent has taken its name.

    Args:
        parent: The parent's name, which is now also the child's.
        added: ``(title, description)`` for the parent's direct pathways -- exactly what the parent
            holds that the child does not, and therefore what the child's new name must exclude.

    Returns:
        The lines to append to the child's own user message.
    """
    body = "\n".join(f"{title}\n{description}" for title, description in added) or "(none)"
    return NARROW_CHILD_LINES.format(parent=parent, added=body)


def render_leaf(
    members: Sequence[tuple[str, str]],
    collides_with: str = "",
    invented: Sequence[str] = (),
    narrow: str = "",
) -> str:
    """The user message for a leaf: one instruction, then data.

    Args:
        members: ``(title, description)`` per pathway. No source tag, no inclusion, no identifier --
            name-v5 sends title and description and nothing else.
        collides_with: When set, the name that collided, appended as :data:`COLLISION_LINE`.
        invented: When set, the unsupported words, appended as :data:`INVENTED_LINE`.
        narrow: When set, the output of :func:`narrow_child`, appended verbatim.

    Returns:
        The user message.
    """
    lines = ["Name this cluster. Its pathways:", ""]
    for title, description in members:
        lines.append(title)
        lines.append(description)
        lines.append("")
    if collides_with:
        lines.append(COLLISION_LINE.format(name=collides_with))
    if invented:
        lines.append(INVENTED_LINE.format(words="', '".join(invented)))
    if narrow:
        lines.append(narrow)
    return "\n".join(lines).rstrip() + "\n"


def render_internal(
    child_names: Sequence[str] | Sequence[tuple[str, str]],
    direct: Sequence[tuple[str, str]] = (),
    collides_with: str = "",
    invented: Sequence[str] = (),
    narrow: str = "",
) -> str:
    """The user message for an internal node: one instruction, then data.

    Args:
        child_names: Either plain names, or ``(name, rationale)`` -- the sentence the child returned
            when it was named. **The pair form exists because the bare form was losing.** A direct
            pathway arrived with a title AND a description; a child arrived as one line, so the
            descriptions outweighed it and the parent was named after its direct pathways. In a
            level-1 read of 215 nodes that produced 16 clear and 12 borderline cases of a parent
            named NARROWER than its own child. Giving the child its rationale puts the two kinds of
            member on comparable footing.
        direct: ``(title, description)`` for every pathway belonging to no child. All of them --
            there is no cap and no sampling.
        collides_with: When set, the name that collided, appended as :data:`COLLISION_LINE`.
        invented: When set, the unsupported words, appended as :data:`INVENTED_LINE`.
        narrow: When set, the output of :func:`narrow_child`, appended verbatim.

    Returns:
        The user message.
    """
    lines = [
        "Name this cluster. Its child clusters (already named) and its direct pathways:",
        "",
    ]
    if child_names:
        lines.append("Child clusters:")
        lines.append("")
        for child in child_names:
            if isinstance(child, str):
                lines.append(child)
            else:
                name, rationale = child
                lines.append(name)
                if rationale:
                    lines.append(rationale)
            lines.append("")
    if direct:
        lines.append("Direct pathways:")
        lines.append("")
    for title, description in direct:
        lines.append(title)
        lines.append(description)
        lines.append("")
    if collides_with:
        lines.append(COLLISION_LINE.format(name=collides_with))
    if invented:
        lines.append(INVENTED_LINE.format(words="', '".join(invented)))
    if narrow:
        lines.append(narrow)
    return "\n".join(lines).rstrip() + "\n"


def render_theme(
    members: Sequence[tuple[str, str]],
    parents: Sequence[str] = (),
    siblings: Sequence[str] = (),
    withheld: int = 0,
) -> str:
    """Render one theme as the user half of the prompt.

    Args:
        members: ``(source, pathway name)`` pairs, medoid-first so truncation keeps the members
            nearest the theme's centre.
        parents: Parent group names already assigned. Empty for a root.
        siblings: Sibling group names already assigned.
        withheld: How many members were not shown. Stated rather than hidden, so the model knows
            it is seeing a sample and does not name the sample.

    Returns:
        The message text.
    """
    lines: list[str] = []
    lines.append(f"Members shown: {len(members)}")
    if withheld:
        lines.append(f"Members withheld: {withheld} (you are seeing a sample of the group)")
    lines.append("")
    for source, name in members:
        lines.append(f"  [{source}] {name}")
    lines.append("")
    lines.append(
        "Parent groups: " + ("; ".join(parents) if parents else "(none -- this is a root)")
    )
    lines.append(
        "Sibling groups already named: " + ("; ".join(siblings) if siblings else "(none)")
    )
    return "\n".join(lines)
