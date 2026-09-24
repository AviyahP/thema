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
NAME_PROMPT_VERSION = "name-v1"

#: A name is a noun phrase a biologist would accept as a heading. Bounds are enforced by
#: instruction and MEASURED here, never by truncation.
MIN_WORDS = 1
MAX_WORDS = 6

#: How many member names the prompt shows. A theme of 250 members cannot be pasted whole, and the
#: medoid-first ordering means the ones shown are the ones nearest the theme's centre.
MAX_MEMBERS_SHOWN = 40

#: Source names must not appear in a name: "Reactome signalling" names a database, not biology.
SOURCE_WORDS = frozenset({"reactome", "hallmark", "msigdb", "btm", "gobp", "go"})

#: A name may not open with an article: "The interferon response" is a sentence fragment where a
#: heading is wanted, and articles sort badly in any list.
LEADING_ARTICLES = frozenset({"the", "a", "an"})

#: Words that make a name say nothing. A theme called "Regulation of cellular processes" has been
#: labelled without being named.
EMPTY_WORDS = frozenset(
    {"various", "diverse", "multiple", "several", "miscellaneous", "general", "generic",
     "assorted", "related", "associated", "other", "misc",
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
        in_range: Whether ``words`` is within :data:`MIN_WORDS`-:data:`MAX_WORDS`.
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
        )


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


def check(
    name: str,
    members: Sequence[str],
    parents: Sequence[str] = (),
    siblings: Sequence[str] = (),
) -> NameCheck:
    """Run every mechanical check over one proposed name.

    Args:
        name: The proposed name.
        members: The theme's member pathway NAMES (not keys).
        parents: The parents' names, where already assigned.
        siblings: The siblings' names, where already assigned.

    Returns:
        What was measured. A failing check is reported, never repaired: a silent repair hides the
        rate at which the prompt fails.
    """
    parts = name.split()
    words = len(parts)
    lowered = _norm(name)
    tokens = set(re.findall(r"[a-z]+", lowered))
    later = parts[1:]
    return NameCheck(
        words=words,
        in_range=MIN_WORDS <= words <= MAX_WORDS,
        leading_article=bool(parts) and parts[0].lower() in LEADING_ARTICLES,
        trailing_punctuation=bool(name.strip()) and name.strip()[-1] in ".,;:!?",
        sentence_case=(
            bool(parts)
            and (parts[0][:1].isupper() or _is_symbol(parts[0]))
            and all(w.islower() or _is_symbol(w) for w in later)
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
    )


SYSTEM_PROMPT = f"""\
You name themes in an ontology of human biological pathways. A theme is a group of pathways
that belong together. Every name you write will sit beside hundreds of others in a browsable
hierarchy, so consistency of register matters as much as accuracy: every name must read as
though written by the same person on the same day.

WHAT A NAME IS

{MIN_WORDS} to {MAX_WORDS} words. A noun phrase in sentence case: no verbs, no leading article,
no trailing punctuation. It may begin with a lowercase symbol where biology requires it -- mRNA,
mTOR, cAMP, p53. Use a gene or protein symbol only when the theme is defined by it.

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

WHAT A NAME MAY NOT CONTAIN

Words that carry no information: "various", "diverse", "related", "miscellaneous", "processes",
"pathways", "mechanisms". A database name -- "Reactome signalling" names a source, not biology.
An identifier of any kind. One member's own name used as the theme's name, which privileges that
member and misstates the theme's scope. A bare category word with nothing to distinguish it:
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
You are checking names in an ontology of human biological pathways for collisions.

Each theme has a name, one or more parent themes, and sibling themes under those parents. A name
earns its place by DISTINGUISHING its theme from its parents and its siblings. A name that repeats
its parent tells a reader walking the hierarchy nothing about why they descended; a name that
cannot be told apart from a sibling leaves them unable to choose.

Revise ONLY when the name repeats a parent, or cannot be told apart from a sibling. If it is
already distinct, keep it -- an unnecessary revision costs consistency for nothing.

A revision must be MORE SPECIFIC than the current name, never broader, and must still be true of
every member of the theme. You are narrowing a name that was too close to its neighbours, not
rewriting it.

All the rules of a name still hold: {MIN_WORDS} to {MAX_WORDS} words, noun phrase, sentence case,
no database names, no identifiers, no contentless words.

OUTPUT FORMAT

Return an object with "revise" (boolean), "name" (the revised name, empty when revise is false)
and "reason" (which parent or sibling it collided with and what now separates it; empty when
revise is false).
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


def render_leaf(members: Sequence[tuple[str, str, str]]) -> str:
    """Task A. Render a leaf theme: its pathways, with descriptions.

    Args:
        members: ``(source, name, description)`` per member, medoid-first.

    Returns:
        The user message.
    """
    lines = [WORKED_EXAMPLES, "", "Below are the pathways in this theme, with their descriptions.",
             "Name the theme.", ""]
    for source, name, description in members:
        lines.append(f"  [{source}] {name}")
        lines.append(f"      {description}")
        lines.append("")
    return "\n".join(lines)


def render_internal(
    child_names: Sequence[str],
    samples: Sequence[tuple[str, str, str]],
    total_members: int,
    unnamed_children: int = 0,
) -> str:
    """Task B. Render an internal node: its children's names and a few member descriptions.

    Args:
        child_names: The already-assigned names of this node's children.
        samples: ``(source, name, description)`` for about three representative members, so one
            bad child name cannot compound upward.
        total_members: How many pathways the theme holds in total.
        unnamed_children: Children that came back unnameable. Stated, because they are a hole in
            the evidence: the parent must cover them too and has only the samples to go on.

    Returns:
        The user message.
    """
    lines = [
        INTERNAL_EXAMPLES,
        "",
        f"This theme contains {total_members} pathways, organised into the child themes below,",
        "which are already named. A few representative member descriptions follow.",
        "Name the parent.",
        "",
        "The name must satisfy two constraints at once. Broad enough to cover every child, and",
        "not a repeat of any child's name. And it must be the SMALLEST umbrella that does so:",
        "tight enough to exclude what none of the children are about. Broader than the children",
        "is required; broader than necessary is a fault. If the only name covering every child is",
        "near-vacuous, or if the parent is really just its largest child with a few extras,",
        "return nameable false and say so -- that is useful information, not a failure.",
        "",
        "Child themes:",
    ]
    for name in child_names:
        lines.append(f"  - {name}")
    if unnamed_children:
        lines.append(
            f"  - ({unnamed_children} further child theme(s) could not be named; the samples "
            "below are your only evidence for what they contain)"
        )
    lines += ["", "Representative members:", ""]
    for source, name, description in samples:
        lines.append(f"  [{source}] {name}")
        lines.append(f"      {description}")
        lines.append("")
    return "\n".join(lines)


def render_disambiguation(
    name: str, parents: Sequence[str], siblings: Sequence[str]
) -> str:
    """Task C. Render one name for the collision check.

    Args:
        name: The generated name.
        parents: Every parent's name.
        siblings: Every sibling name under any of those parents.

    Returns:
        The user message.
    """
    return "\n".join(
        [
            DISAMBIGUATION_EXAMPLE,
            "",
            f'This theme is currently named "{name}".',
            "",
            "Its parent themes are named: "
            + ("; ".join(parents) if parents else "(none -- this is a root)"),
            "Its sibling themes under those parents are named: "
            + ("; ".join(siblings) if siblings else "(none)"),
            "",
            "Decide whether to keep the name.",
        ]
    )


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
