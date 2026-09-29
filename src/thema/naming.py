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
NAME_PROMPT_VERSION = "name-v4"

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
LEAF_PROMPT_VERSION = "name-v4"

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


def check(
    name: str,
    members: Sequence[str],
    parents: Sequence[str] = (),
    siblings: Sequence[str] = (),
    taken: Sequence[str] = (),
) -> NameCheck:
    """Run every mechanical check over one proposed name.

    Args:
        name: The proposed name.
        members: The theme's member pathway NAMES (not keys).
        parents: The parents' names, where already assigned.
        siblings: The siblings' names, where already assigned.
        taken: Every name already assigned to another theme anywhere in the hierarchy. Pass the
            whole set, not the neighbourhood: duplicates in the raw build sat in different subtrees.

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
    )


SYSTEM_PROMPT = f"""\
You name themes in an ontology of human biological pathways. A theme is a group of pathways
that belong together. Every name you write will sit beside hundreds of others in a browsable
hierarchy, so consistency of register matters as much as accuracy: every name must read as
though written by the same person on the same day.

WHAT A NAME IS

{MIN_WORDS} to {MAX_WORDS} words, and fewer than {PREFERRED_WORDS} is preferred. Sentence case,
no leading article, no trailing punctuation.

A noun phrase by default. A clause with a verb is acceptable only when it is the tightest true
statement of what the members share; never a full sentence. Do not reach for a clause to sound
precise -- reach for it only when the noun phrase you would otherwise write is broader than the
members are.

It may begin with a lowercase symbol where biology requires it -- mRNA, mTOR, cAMP, p53. Use a gene
or protein symbol only when the theme is defined by it.

COVER EVERY MEMBER, GENERALISE NO FURTHER

A name is the tightest description that is true of EVERY member.

Those are two demands and both bind. It must cover all of them: a name true of most members and
false of the rest is wrong, however well it fits the majority. And it must generalise no further
than they require: if every member is about sterol transport, the name is about sterol transport,
not lipid metabolism. "Lipid metabolism" is TRUE of a theme of sterol transporters and still
wrong, because it admits half the lipid world and tells a reader nothing about which part they
are looking at. Specific enough to exclude the neighbouring themes; no broader than the members
themselves.

Where a name cannot both cover every member and stay tight to them, that is a fact about the
theme, not a wording problem. Say so rather than stretching.

EVERY MEMBER CARRIES AN INCLUSION. USE IT

Each member is listed with its inclusion -- the share of the evidence that placed it in this theme.
A member at 1.00 is settled. A member at 0.3 was placed by a minority of the evidence and is a
boundary case.

When you are naming a theme from its own members, the name must be true of every member at
inclusion 0.5 or above. It MAY leave out members below 0.5, and when it does you must say which
ones in the rationale, by name. Weakly included members are never on their own a reason to answer
nameable false -- if the members at 0.5 and above share a nameable biology, name it and note what
you excluded.

**That allowance does not apply to a parent's DIRECT members.** When the task below gives you child
themes plus direct members, every direct member must be covered whatever its inclusion, because the
direct members are the whole of what the parent adds. The task says so again where it matters.

DO NOT ASSERT A MECHANISM THE MEMBERS DO NOT CONTAIN

A name may name only what is there. This is the most common way a name goes wrong, and it is worse
than a name that is too broad, because a reader cannot tell it is invented.

Example of the failure: nine calcium-signalling terms -- regulation of calcium-mediated signalling,
regulation of calcium ion import, regulation of calcium ion transmembrane transport, calcineurin-
mediated signalling and its negative regulation, plus response to caffeine -- named "Calcineurin-
NFAT feedback regulation". Calcineurin is fair: seven of the nine concern it. But NFAT appears in
only two of the nine, and no member concerns feedback at all. The name promises a specific
downstream axis that most of the theme does not contain. "Calcium signalling and calcineurin
regulation" would have been true. The fault is not vagueness; it is invention.

Before answering, check each content word of your name against the members. If a word names a
gene, a protein, a compartment or a mechanism that only one or two members concern, take it out.

WHAT A NAME MAY NOT CONTAIN

Words that carry no information: "various", "diverse", "related", "miscellaneous", "processes",
"pathways", "mechanisms". A database name -- "Reactome signalling" names a source, not biology.
An identifier of any kind. One member's own name used as the theme's name, which privileges that
member and misstates the theme's scope. A name already used by another theme anywhere in the
hierarchy -- two themes with one name make the hierarchy unreadable, and the reader cannot tell
which of them they are looking at. A bare category word with nothing to distinguish it:
"Metabolism", "Signalling", "Transport", "Immune processes" file a theme without naming it.

WHEN A THEME CANNOT BE NAMED

If the members do not share a nameable biology -- if the only name covering all of them is so
broad it would cover much else besides, or if any name would be an invention -- say so. Return
nameable false, with one sentence in the rationale explaining what the members actually have in
common, or that they have nothing in common.

This is a real and expected answer. These themes were formed by measuring which pathways recur
together across resampling, which is not the same as being interpretable, so some are genuinely
heterogeneous. An honest blank is worth more than a plausible label nobody can check: the name
is often all a reader sees, and they cannot audit it.

OUTPUT FORMAT

Return an object with "nameable" (boolean), "name" (string, empty when nameable is false) and
"rationale" (string: what the members share, or why they cannot be named).
"""

#: Task C runs against its own system prompt: keeping or revising a name under collision is a
#: different instruction from writing one, and folding both into one prompt made the naming rules
#: compete with the revision rules for the model's attention.
DISAMBIGUATION_SYSTEM_PROMPT = f"""\
You are fixing ONE name that collides with another name in an ontology of human biological pathways.

The collision has already been established by string comparison, so you are not being asked whether
it collides. You are being asked for a replacement. Two themes with one name make the hierarchy
unreadable, and a child that repeats its parent tells a reader who descended nothing about why.

You are given the name, what it collides with, and the theme's own contents.

FOR A THEME WITH CHILDREN, the replacement MUST still be true of every child's name. A replacement
that covers only some of the children is worse than the collision it fixes -- it makes the parent
narrower than its own contents, which is a false statement about the hierarchy rather than an
awkward one. Stay as broad as the children require and find the difference elsewhere.

FOR A LEAF, the replacement must be MORE SPECIFIC than the name it replaces, never broader, and
still true of every member at inclusion 0.5 or above.

In both cases the replacement must not assert a mechanism the contents do not contain, and must not
collide with any of the names you are shown.

Distinguishing is not the same as sharing no words. "Canonical Wnt signalling" and "Non-canonical
Wnt signalling" share almost everything and are perfectly distinct. What matters is that a reader
could not apply your name to the other theme.

All the rules of a name still hold: {MIN_WORDS} to {MAX_WORDS} words with fewer than
{PREFERRED_WORDS} preferred; a noun phrase unless a clause is tighter; sentence case;
no database names, no identifiers, no contentless words.

OUTPUT FORMAT

Return an object with "revise" (boolean), "name" (the replacement, empty when revise is false) and
"reason" (what it collided with and what now separates them; empty when revise is false). Return
revise false only if you genuinely cannot find a replacement that satisfies the constraints above,
which is a finding worth reporting rather than a failure.
"""


WORKED_EXAMPLES = """\
Example input: four pathways -- Interferon alpha/beta signalling; Interferon gamma signalling;
ISG15 antiviral mechanism; Antiviral mechanism by IFN-stimulated genes.
Example output: {"nameable": true, "name": "Interferon response", "rationale": "All four are
interferon signalling or its direct antiviral effectors."}

Example input: three pathways -- MITF-M-dependent DNA repair; Mismatch repair; Melanocyte
differentiation.
Example output: {"nameable": false, "name": "", "rationale": "One member bridges melanocyte
biology and DNA repair through MITF; the other two share nothing with each other beyond that
bridge."}
"""

INTERNAL_EXAMPLES = """\
Example input: children -- Interferon response; Toll-like receptor signalling; Complement
activation; NOD-like receptor signalling. 61 members.
Example output: {"nameable": true, "name": "Innate immune signalling", "rationale": "Every child
is a pathogen-sensing or first-line effector arm of innate immunity; nothing adaptive is present,
so 'immune signalling' would be too broad."}
"""

DISAMBIGUATION_EXAMPLE = """\
Example: name "Immune signalling"; parent "Immune signalling"; siblings "Innate immune
signalling", "Cytokine signalling".
Example output: {"revise": true, "name": "Adaptive immune signalling", "reason": "Repeated the
parent; the members are T and B cell receptor pathways, which separates it from both siblings."}
"""


def render_leaf(
    members: Sequence[tuple[str, str, str]], inclusions: Sequence[float] | None = None
) -> str:
    """Task A. Render a leaf theme: its pathways, with inclusions and descriptions.

    Args:
        members: ``(source, name, description)`` per member, medoid-first.
        inclusions: Each member's inclusion, in the same order. Shown because the coverage rule is
            stated in terms of it: the name must be true of every member at 0.5 or above, may leave
            out those below, and must then say which. Omitted only by callers that have no
            inclusions to show.

    Returns:
        The user message.
    """
    lines = [
        WORKED_EXAMPLES, "",
        "Below are the pathways in this theme, with their inclusion and their descriptions.",
        "Name the theme.", "",
    ]
    for index, (source, name, description) in enumerate(members):
        share = "" if inclusions is None else f"  (inclusion {inclusions[index]:.2f})"
        lines.append(f"  [{source}] {name}{share}")
        lines.append(f"      {description}")
        lines.append("")
    return "\n".join(lines)


def render_internal(
    child_names: Sequence[str],
    total_members: int,
    unnamed_children: int = 0,
    direct: Sequence[tuple[str, str, float, str]] = (),
) -> str:
    """Task B. Render an internal node: its children by name, its DIRECT members in full.

    **name-v4 removed the three "representative members".** They were ``member_keys[:3]`` in file
    order -- not medoids, not highest-inclusion, not sampled -- so "representative" described
    nothing, and three arbitrary descriptions out of a 933-member theme were noise that competed
    with the children for the model's attention. What the parent actually adds is its direct
    members, and those are now given in full: source, name, inclusion and the whole description.

    Args:
        child_names: The already-assigned names of this node's children.
        total_members: How many pathways the theme holds in total.
        unnamed_children: Children that came back unnameable. Stated, because they are a hole in
            the evidence the parent must still cover.
        direct: ``(source, name, inclusion, description)`` for every member belonging to NO child,
            highest inclusion first. These are what make a parent broader than its children.
            Without them a single-child node looks identical to its child and can only be refused
            as a restatement, which is what the first smoke run did on eight of twelve refusals.

    Returns:
        The user message.
    """
    lines = [
        INTERNAL_EXAMPLES,
        "",
        f"This theme contains {total_members} pathways: the child themes below, which are already",
        "named, PLUS the direct members listed after them. Name the parent.",
        "",
        "The name must satisfy two constraints at once. Broad enough to cover every child AND",
        "every direct member, and not a repeat of any child's name. And it must be the SMALLEST",
        "umbrella that does so: tight enough to exclude what none of them are about. Broader than",
        "the children is required; broader than necessary is a fault.",
        "",
        "COVERAGE, precisely. The name must be true of EVERY child theme's name AND of EVERY",
        "direct member below, whatever its inclusion. No threshold here, and nothing left out:",
        "the direct members are the whole of what this node adds to its children, so a name",
        "that excludes one is not a name for this node. Each member's inclusion is shown because",
        "it says how central that member is, not because it licenses ignoring it.",
        "",
        "THE DIRECT MEMBERS ARE WHY THIS NODE EXISTS. They belong to no child, so they are exactly",
        "what the parent adds, and they are given below in full. Name the union of children and",
        "direct members. Do not refuse merely because there is one child: a node with one child",
        "and direct members is broader than that child, and the direct members tell you how.",
        "",
        "Return nameable false only when the union is genuinely incoherent -- unrelated biology",
        "with no honest umbrella short of a near-vacuous word -- or when there are NO direct",
        "members and a single child, so the parent really would just restate it. Saying so is",
        "useful information, not a failure.",
        "",
        f"Child themes ({len(child_names)}), already named:",
    ]
    for name in child_names:
        lines.append(f"  - {name}")
    if unnamed_children:
        lines.append(
            f"  - ({unnamed_children} further child theme(s) could not be named. You have no "
            "evidence for what they contain; cover them as best the rest allows and say so.)"
        )
    lines += ["", f"Direct members ({len(direct)}) -- in this theme but in NO child:", ""]
    if direct:
        for source, name, inclusion, description in direct:
            lines.append(f"  [{source}] {name}  (inclusion {inclusion:.2f})")
            lines.append(f"      {description}")
            lines.append("")
    else:
        lines.append("  (none -- every member of this theme sits in one of the children above)")
        lines.append("")
    return "\n".join(lines)


def render_disambiguation(
    name: str,
    collides_with: Sequence[str],
    repeats_parent: bool = False,
    children: Sequence[str] = (),
    members: Sequence[tuple[str, float]] = (),
    taken: Sequence[str] = (),
) -> str:
    """Task C. Render ONE name that mechanically collides, and ask for a replacement.

    **name-v4 withdrew the full pass.** Under name-v3 every theme with a parent or a sibling was
    sent to the model -- 806 of the run's 1,676 calls -- to be asked a question string comparison
    answers. It cost more than half the run and made the result worse three ways: it created 20
    duplicate names, every one of them by revising two themes onto the same replacement; it narrowed
    parents below their own children (2 of the 3 wrong parents in the 20-node read); and it produced
    one false refusal, n0475, whose two children it had given the same name. Detection is now
    mechanical and the model is asked only about names that actually collide.

    Args:
        name: The colliding name.
        collides_with: The other names it is identical to, elsewhere in the hierarchy.
        repeats_parent: Whether it repeats one of its own parents' names.
        children: This theme's children's names. Non-empty means the replacement must cover them
            ALL, which is the opposite of the leaf rule and is stated as such in the prompt.
        members: ``(pathway name, inclusion)`` for a leaf's members, highest inclusion first.
        taken: Names in use that the replacement must avoid -- the collisions plus the parents.

    Returns:
        The user message.
    """
    lines = [DISAMBIGUATION_EXAMPLE, "", f'This theme is named "{name}".', ""]
    if collides_with:
        lines.append(
            f"It is IDENTICAL to the name of {len(collides_with)} other theme(s) elsewhere in the "
            "hierarchy."
        )
    if repeats_parent:
        lines.append("It REPEATS the name of its own parent.")
    lines.append("")
    if children:
        lines.append(
            f"This theme has {len(children)} children, already named. Your replacement must be "
            "true of EVERY one of them:"
        )
        lines.extend(f"  - {child}" for child in children)
    elif members:
        lines.append("This theme is a leaf. Its members, highest inclusion first:")
        lines.extend(f"  - {member}  (inclusion {share:.2f})" for member, share in members)
    lines.append("")
    if taken:
        lines.append("Names your replacement must NOT be:")
        lines.extend(f"  - {other}" for other in sorted(set(taken)))
        lines.append("")
    lines.append("Give the replacement.")
    return "\n".join(lines)


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
