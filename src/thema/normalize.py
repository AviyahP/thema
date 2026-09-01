"""Prompt, provenance and validator for the generated pathway descriptions.

This module is deliberately free of any provider SDK: it builds the strings that go to a model and
checks the strings that come back, and both halves are ordinary text processing that must stay
testable without a network, an API key, or ``anthropic`` installed. :mod:`thema.llm` is the only
module in the repo that imports the SDK, and ``tests/test_llm.py`` pins that.

The rules encoded here are the 2026-08-29 ``DECISIONS.md`` entry, and the reasons live there rather
than being repeated in full: one description per pathway at one length and register; the source
database is never shown; the gene list is always shown, whole; world knowledge is wanted; a specific
database entry may never be named.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from thema.data.pathways import Pathway, TextAvailability

#: Bumped whenever the prompt changes in a way that should invalidate cached completions. The cache
#: key includes it, so a bump regenerates rather than silently mixing two prompts in one table.
PROMPT_VERSION = "v1"

#: The stated length band, in words. Enforced by instruction and measured by :func:`validate`, never
#: by truncation -- a length-dependent cutoff would reintroduce the bias normalization removes.
MIN_WORDS = 90
MAX_WORDS = 130
TARGET_WORDS = 110

#: What produced a description, one value per ``text_availability``. These are the three strings
#: written to ``description_generated_from``.
PROVENANCE: dict[TextAvailability, str] = {
    "described": "description+name+genes",
    "name_only": "name+genes",
    "no_usable_text": "genes",
}

#: The response is a single field, so no model can prepend "Here is the description:".
RESPONSE_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {"description": {"type": "string"}},
        "required": ["description"],
        "additionalProperties": False,
    },
}

#: Ontology identifiers the description must not contain. KEGG and WikiPathways are matched too:
#: neither is a v1 source, but a model reciting one is failing in exactly the same way.
IDENTIFIER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("go_id", re.compile(r"\bGO:\d{7}\b")),
    ("reactome_id", re.compile(r"\bR-[A-Z]{3}-\d+\b")),
    ("hallmark_id", re.compile(r"\bHALLMARK_[A-Z0-9_]+")),
    ("btm_id", re.compile(r"\b[MS]\d+(?:\.\d+)*\b(?=\s*(?:module|\)|$))")),
    ("kegg_id", re.compile(r"\bhsa\d{5}\b")),
    ("wikipathways_id", re.compile(r"\bWP\d{3,}\b")),
)

#: References to a database object rather than to biology. Bare "hallmark" is deliberately absent:
#: "a hallmark of cancer" is ordinary English, and matching it would make this check useless.
REFERENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("reactome", re.compile(r"\bReactome\b", re.IGNORECASE)),
    ("gene_ontology", re.compile(r"\bGene Ontology\b|\bGO (?:term|category|annotation)", re.I)),
    ("msigdb", re.compile(r"\bMSigDB\b|\bMolecular Signatures Database\b", re.IGNORECASE)),
    ("hallmark_set", re.compile(r"\bhallmark (?:gene )?set\b|\bhallmark collection\b", re.I)),
    ("btm", re.compile(r"\bblood transcriptio(?:n|nal) module\b|\bBTM\b", re.IGNORECASE)),
    ("database_object", re.compile(r"\bthe (?:pathway|term|gene set) (?:named|called)\b", re.I)),
    ("curation", re.compile(r"\bthis (?:gene set|pathway) (?:is annotated|was curated)\b", re.I)),
)

#: Hallmark's ``name`` IS its database identifier -- all 50 are ``HALLMARK_<WORDS>``. Sending one
#: and asking the model to repeat it would write a database identifier into all 50 descriptions,
#: trip the validator 50 times, and hand the reader the source. The name is therefore humanized for
#: the prompt only; ``Pathway.name`` keeps the source's string, as the loader entry requires.
HALLMARK_PREFIX = "HALLMARK_"

#: Tokens of a Hallmark name that must not be lowercased. Tokens carrying a digit (``E2F``, ``P53``,
#: ``MTORC1``, ``V1``) are handled by rule; these are the all-alphabetic remainder, enumerated
#: because the collection is fifty frozen sets and a list can be checked against all of them.
HALLMARK_ACRONYMS = frozenset(
    {"AKT", "DN", "DNA", "JAK", "KRAS", "MTOR", "MYC", "NFKB", "TGF", "TNFA", "UV", "WNT"}
)

#: Structured output guarantees the response's SHAPE, not its content: two of the first thirty-six
#: sampled descriptions came back as valid JSON whose string held stray braces and, in one case, a
#: visible self-correction ("...reactive species.}wait fix formatting}{"). Both would have gone
#: straight into committed, embedded prose, so the residue is checked for rather than hoped against.
RESIDUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("json_residue", re.compile(r"[{}]|\"description\"\s*:")),
    ("self_correction", re.compile(r"\b(?:wait|oops|let me|actually,? (?:fix|redo))\b[^.]{0,30}"
                                   r"(?:fix|format|again|rewrite)", re.IGNORECASE)),
    ("dangling_quote", re.compile(r"[\"\u201c\u201d]\s*$")),
)

SYSTEM_PROMPT = f"""\
You write short functional descriptions of biological gene sets. Each description you write will be
embedded and clustered with thousands of others, so consistency of length and register matters as
much as accuracy: every description must read as though written by the same person on the same day.

You will be given a gene set's name, its curated description when one exists, and its full list of
member genes. You will NOT be told which database the set came from, and you must not speculate
about it.

WHAT TO WRITE

Write one paragraph of {MIN_WORDS}-{MAX_WORDS} words, targeting about {TARGET_WORDS}. Do not write
a list, headings, or more than one paragraph.

Begin by repeating the set's name, so the description stays anchored to its subject. If the name is
a placeholder such as "TBA" and carries no meaning, open instead by naming the biology you infer
from the genes, and do not mention that the name was missing.

State which general cellular or physiological processes the set relates to, and be specific about
purpose. "Signal transduction" is not an answer; signal transduction toward what end is. A reader
should finish the paragraph knowing what this set is FOR, not merely what category it falls in.

Use your own knowledge of biology freely. Curated descriptions are often too terse to carry thematic
meaning, and adding that context is the point of this task. Where a curated description exists it
anchors the content and you must stay faithful to it, but you may and should extend it. Where the
genes tell you something the text does not -- a shared complex, a compartment, a cell type, a
regulatory relationship -- say so. Where there is no text at all, derive the biology from the genes
and commit to it. Do not hedge with phrases like "this set may be involved in"; if the genes support
a claim, state it.

WHAT NOT TO WRITE

Never cite a specific database entry. Do not write ontology identifiers of any kind, and do not name
another pathway, term or gene set AS A DATABASE OBJECT -- not "the Reactome pathway X", not "the GO
term Y", not "this MSigDB set". Do not name the databases themselves.

This prohibition is narrow and is about citation, not about relationships. Describing how this
biology relates to other biology, in ordinary language, is exactly what is wanted: "a subtype of
apoptosis", "part of cell cycle control", "downstream of interferon signalling", "one arm of the
unfolded protein response". Write those freely.

Do not list gene symbols exhaustively. Naming a few genes that carry the set's identity is useful;
transcribing the input is not.

Do not describe the input. No "this gene set contains", no "the description provided states", no
meta-commentary about what you were given.

EXAMPLES

Input name: Mitochondrial iron-sulfur cluster assembly
Input description: Assembly of [2Fe-2S] and [4Fe-4S] clusters on a scaffold protein and their
transfer to recipient apoproteins.
Input genes: NFS1, ISCU, FXN, LYRM4, FDX2, FDXR, HSPA9, HSCB, GLRX5, ISCA1, ISCA2, IBA57, NFU1

Output: Mitochondrial iron-sulfur cluster assembly builds [2Fe-2S] and [4Fe-4S] cofactors on a
dedicated scaffold and hands them to the apoproteins that cannot function without them. A cysteine
desulfurase supplies sulfur, a ferredoxin pair supplies electrons, and a chaperone-cochaperone step
releases the finished cluster. The recipients are the workhorses of oxidative metabolism and genome
maintenance: respiratory chain complexes, aconitase, lipoate synthase, and several DNA repair
helicases. The process therefore sits upstream of cellular energy production and of iron homeostasis
generally, and cells sense its failure as apparent iron starvation. Loss of individual components
causes progressive mitochondrial disease, which locates this biology firmly in the maintenance of
respiratory capacity rather than in any single metabolic route.

Input name: TBA
Input description: (none)
Input genes: CD19, MS4A1, CD79A, CD79B, BLNK, BTK, PAX5, EBF1, VPREB1, IGLL1, CR2, FCRL1, TNFRSF13C

Output: This set describes the B lymphocyte lineage and the receptor that defines it. Its members
are the surface and adaptor components of B cell antigen receptor signalling together with the
transcription factors that specify and maintain B cell identity, and the surrogate light chain
proteins that test receptor assembly before a cell is allowed to mature. Function here is
developmental checkpointing as much as signalling: the pathway commits a progenitor to the lineage,
verifies that a functional receptor has been built, and then transmits antigen engagement into
proliferation and survival. It underpins humoral immunity, and its components are the standard
markers by which B cells are identified and therapeutically targeted.

OUTPUT FORMAT

Return an object with a single key, "description", whose value is the paragraph.
"""


@dataclass(frozen=True, slots=True)
class Finding:
    """One thing the validator objected to in one description.

    Attributes:
        kind: Which check fired -- an :data:`IDENTIFIER_PATTERNS` or :data:`REFERENCE_PATTERNS`
            name, ``length`` or ``name_echo``.
        detail: The offending text, or a short statement of what was measured.
    """

    kind: str
    detail: str


@dataclass(frozen=True, slots=True)
class Validation:
    """What the mechanical validator measured for one description.

    Nothing here rewrites the description. The 2026-08-29 entry requires the counts to be reported
    rather than the text repaired, because a silent repair hides the rate at which the prompt fails.

    Attributes:
        words: Word count.
        in_range: Whether ``words`` falls within :data:`MIN_WORDS`-:data:`MAX_WORDS`.
        name_echoed: Whether the pathway's name appears in the description.
        identifiers: Ontology identifiers found.
        references: Database-object references found.
        residue: Fragments of the response format that leaked into the prose.
    """

    words: int
    in_range: bool
    name_echoed: bool
    identifiers: tuple[Finding, ...]
    references: tuple[Finding, ...]
    residue: tuple[Finding, ...] = ()

    @property
    def clean(self) -> bool:
        """Whether the description tripped no check at all."""
        return (
            self.in_range
            and self.name_echoed
            and not self.identifiers
            and not self.references
            and not self.residue
        )

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Every finding, identifiers first."""
        extra: list[Finding] = []
        if not self.in_range:
            extra.append(Finding("length", f"{self.words} words, want {MIN_WORDS}-{MAX_WORDS}"))
        if not self.name_echoed:
            extra.append(Finding("name_echo", "the pathway name does not appear"))
        return (*self.identifiers, *self.references, *self.residue, *extra)


def word_count(text: str) -> int:
    """Count words the way the length instruction means them.

    Args:
        text: The description.

    Returns:
        The number of whitespace-separated tokens.
    """
    return len(text.split())


def genes_for_prompt(pathway: Pathway) -> tuple[str, ...]:
    """The gene symbols shown to the model, sorted and deduplicated.

    The source's own symbols are used rather than HGNC identifiers: a model recognises ``CD19``, and
    ``HGNC:1633`` tells it nothing. Where several source symbols met on one gene, all of them are
    kept -- discarding one would silently drop a name the source actually published.

    Args:
        pathway: The pathway.

    Returns:
        The symbols, sorted. Empty for the 47 pathways that resolved to no genes at all.
    """
    symbols: set[str] = set()
    for _identifier, names in pathway.gene_symbols:
        symbols.update(names)
    return tuple(sorted(symbols))


def display_name(pathway: Pathway) -> str:
    """The pathway's name as the model should see it.

    Identical to ``pathway.name`` for every source but Hallmark, whose names are the database's own
    identifiers rather than titles. Those are humanized here rather than in the loader, because the
    stored record must keep what the source published; this is a rendering concern.

    Args:
        pathway: The pathway.

    Returns:
        The name to show.
    """
    if pathway.source != "hallmark" or not pathway.name.startswith(HALLMARK_PREFIX):
        return pathway.name
    tokens = pathway.name[len(HALLMARK_PREFIX) :].split("_")
    words = [
        token if any(c.isdigit() for c in token) or token in HALLMARK_ACRONYMS else token.lower()
        for token in tokens
    ]
    rendered = " ".join(words)
    return rendered[:1].upper() + rendered[1:]


def provenance_of(pathway: Pathway) -> str:
    """What inputs this pathway's description will be written from.

    Args:
        pathway: The pathway.

    Returns:
        One of the three :data:`PROVENANCE` values.
    """
    return PROVENANCE[pathway.text_availability]


def render_user_message(pathway: Pathway) -> str:
    """Render the per-pathway half of the prompt.

    The source database appears nowhere, by decision: telling the model which database it is looking
    at invites source-specific register, which is what normalization exists to remove. The gene list
    is whole -- no truncation and no subsetting, because any truncation rule would hand the model a
    biased sample of exactly the pathways where the sample matters most.

    Args:
        pathway: The pathway to describe.

    Returns:
        The user message.
    """
    genes = genes_for_prompt(pathway)
    lines = [
        f"Input name: {display_name(pathway)}",
        f"Input description: {pathway.description_source or '(none)'}",
        f"Input genes: {', '.join(genes) if genes else '(none)'}",
    ]
    return "\n".join(lines)


def _name_echoed(description: str, name: str) -> bool:
    """Whether a pathway's name is recognisably present in its description."""
    stripped = re.sub(r"[^a-z0-9 ]+", " ", name.lower())
    tokens = [token for token in stripped.split() if len(token) > 3]
    if not tokens:
        # A name too short or too generic to check for -- BTM's "TBA" and similar. Not a failure.
        return True
    haystack = re.sub(r"[^a-z0-9 ]+", " ", description.lower())
    hits = sum(1 for token in tokens if token in haystack)
    return hits >= max(1, (len(tokens) + 1) // 2)


def validate(description: str, name: str) -> Validation:
    """Run every mechanical check over one description.

    Args:
        description: The generated description.
        name: The pathway's name, for the echo check.

    Returns:
        What was measured. Nothing is rewritten.
    """
    identifiers = tuple(
        Finding(kind, match)
        for kind, pattern in IDENTIFIER_PATTERNS
        for match in pattern.findall(description)
    )
    references = tuple(
        Finding(kind, pattern.search(description).group(0))  # type: ignore[union-attr]
        for kind, pattern in REFERENCE_PATTERNS
        if pattern.search(description)
    )
    residue = tuple(
        Finding(kind, pattern.search(description).group(0))  # type: ignore[union-attr]
        for kind, pattern in RESIDUE_PATTERNS
        if pattern.search(description)
    )
    words = word_count(description)
    return Validation(
        words=words,
        in_range=MIN_WORDS <= words <= MAX_WORDS,
        name_echoed=_name_echoed(description, name),
        identifiers=identifiers,
        references=references,
        residue=residue,
    )


def validate_all(pairs: Iterable[tuple[str, str]]) -> tuple[Validation, ...]:
    """Validate many ``(description, name)`` pairs.

    Args:
        pairs: ``(description, name)`` pairs.

    Returns:
        One :class:`Validation` per pair, in order.
    """
    return tuple(validate(description, name) for description, name in pairs)


def summarize(validations: Sequence[Validation]) -> dict[str, int]:
    """Tally validator findings across many descriptions.

    Args:
        validations: The results.

    Returns:
        Counts by check name, plus ``total`` and ``clean``.
    """
    tally: dict[str, int] = {"total": len(validations), "clean": 0}
    for name, _pattern in (*IDENTIFIER_PATTERNS, *REFERENCE_PATTERNS, *RESIDUE_PATTERNS):
        tally[name] = 0
    tally["length"] = 0
    tally["name_echo"] = 0
    for validation in validations:
        if validation.clean:
            tally["clean"] += 1
        for finding in validation.findings:
            tally[finding.kind] = tally.get(finding.kind, 0) + 1
    return tally
