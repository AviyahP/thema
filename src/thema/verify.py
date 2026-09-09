"""Fact-checking for generated descriptions: the prompt, the schema, and the flags it returns.

Descriptions are written with world knowledge on purpose (DECISIONS, 2026-08-29), which is what
makes them useful and also what makes them capable of being confidently wrong. The failure is
specific and it is not stylistic: a description reads fluently, matches the pathway name, passes
every mechanical check, and states something about a gene that is false. The method here caught
``SLC31A2`` described as an iron transporter and ``SPINT1``/``SPINT2`` described as proteases --
they are a copper transporter and protease *inhibitors*. Neither is visible to a validator that
matches patterns, and neither would look wrong in a cluster.

Two design constraints, both to keep the check honest:

The verifier is not told which model wrote the description, or that a model wrote it at all. It is
also not told the source database, for the same reason the generator is not: a check that knows it
is reading Reactome can rationalise Reactome's register instead of reading the claim.

Nothing here rewrites anything. The verifier returns flags; deciding what to do about one is the
caller's job, and the repair loop that follows never accepts a rewrite without re-checking it.

Recorded caveat: this is Opus checking Opus, so the rate carries a self-preference bias and should
be read as a lower bound rather than a measurement. A different model would be independent and
cheaper, but weaker on exactly the single-gene detail this exists to catch. Reported, not fixed.
"""

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from thema.data.pathways import Pathway
from thema.normalize import (
    MAX_WORDS,
    MIN_WORDS,
    display_name,
    genes_for_prompt,
    render_user_message,
)

#: Cache-key component for the first verification pass. Bumping it invalidates cleanly rather than
#: mixing two verifier versions in one file, exactly as PROMPT_VERSION does for generation.
VERIFY_PROMPT_VERSION = "verify-v1"

#: The re-check of a repaired description. A separate version, so the second opinion on a repair is
#: never served from the first pass's cache entry for the same pathway.
RECHECK_PROMPT_VERSION = "verify-v1-recheck"

#: Regeneration carrying the verifier's objection. Separate again, so a repair never overwrites the
#: original completion and both remain on disk.
REPAIR_PROMPT_VERSION = "repair-v1"

#: What a flag says about a claim. ``wrong`` contradicts established biology; ``unsupported`` may
#: be true but cannot be reached from the evidence shown. They are kept apart because they call for
#: different responses -- one is an error, the other is overreach.
FLAG_KINDS = ("wrong", "unsupported")

#: What happened to a row, in the order a row can move through them.
VERIFICATION_STATUSES = ("unverified", "clean", "flagged", "repaired", "repair_failed")

RESPONSE_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "quote": {"type": "string"},
                        "kind": {"type": "string", "enum": list(FLAG_KINDS)},
                        "reason": {"type": "string"},
                    },
                    "required": ["quote", "kind", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["claims"],
        "additionalProperties": False,
    },
}

#: The key of the schema above that carries the payload.
RESPONSE_KEY = "claims"

SYSTEM_PROMPT = f"""You are checking a description of a biological gene set for factual errors.

You will be shown a gene set's name, the curated description its database publishes (where there is
one), its full gene list, and a CANDIDATE DESCRIPTION written to summarise it. Your only job is to
find claims in the candidate description that are WRONG or UNSUPPORTED.

WHAT TO FLAG

wrong -- the claim contradicts established biology. Pay particular attention to statements about
what a specific named gene or protein does: its molecular function, its substrate, the ion or
molecule it transports, its direction of effect, and whether it activates or inhibits. Calling a
copper transporter an iron transporter is wrong. Calling a protease inhibitor a protease is wrong.
Assigning a gene to the wrong compartment, pathway direction, or cell type is wrong.

unsupported -- the claim may well be true, but it cannot be reached from the name, the curated
description, or the gene list, and it is not something established biology settles. A specific
number, a named disease association, a claimed tissue restriction, or a mechanism nothing shown
implies belongs here.

WHAT NOT TO FLAG

Do not flag style, tone, length, or word choice. Do not flag omissions -- a description that leaves
something out is not wrong. Do not flag ordinary summarising or generalisation, and do not flag a
correct statement merely because the curated description does not happen to repeat it: established
biology is a legitimate source and the description was written with it deliberately in view. Do not
flag the absence of database identifiers; they are forbidden on purpose. Do not flag a description
for being between {MIN_WORDS} and {MAX_WORDS} words, which is what it was asked to be.

If a claim is arguable rather than clearly wrong, say so in the reason and prefer `unsupported` to
`wrong`. Do not manufacture findings: a description with nothing wrong in it must return an empty
list, and that is the expected result for most of what you will read.

OUTPUT FORMAT

Return a JSON object with one key, "claims", holding a list. Each entry has:
  "quote"  -- the sentence from the candidate description, copied exactly, unedited
  "kind"   -- "wrong" or "unsupported"
  "reason" -- one line saying what is actually the case, and how you know

Return {{"claims": []}} when the description is sound. Never rewrite the description; never return
a corrected version. You report, and nothing else."""


@dataclass(frozen=True, slots=True)
class Flag:
    """One claim the verifier objected to.

    Attributes:
        quote: The sentence it objected to, as the verifier copied it.
        kind: One of :data:`FLAG_KINDS`.
        reason: One line on what is actually the case.
    """

    quote: str
    kind: str
    reason: str


def render_verify_message(pathway: Pathway, description: str) -> str:
    """Build the verification prompt for one description.

    The source database is not named and neither is the model that wrote the description. What the
    verifier gets is exactly the evidence the claim has to stand on.

    Args:
        pathway: The pathway the description is of.
        description: The generated description under check.

    Returns:
        The user message.
    """
    genes = genes_for_prompt(pathway)
    return "\n".join(
        (
            f"Name: {display_name(pathway)}",
            f"Curated description: {pathway.description_source or '(none)'}",
            f"Genes: {', '.join(genes) or '(none)'}",
            "",
            "CANDIDATE DESCRIPTION:",
            description,
        )
    )


def render_repair_message(pathway: Pathway, description: str, flags: Sequence[Flag]) -> str:
    """Build the regeneration prompt for a flagged description.

    The objection is appended to the ordinary generation prompt as a correction instruction rather
    than replacing it, so the rewrite is still bound by every rule the original was written under.

    Args:
        pathway: The pathway.
        description: The description that was flagged.
        flags: What the verifier objected to.

    Returns:
        The user message, for use with the generation system prompt.
    """
    objections = "\n".join(f'- {flag.kind}: "{flag.quote}" -- {flag.reason}' for flag in flags)
    return "\n".join(
        (
            render_user_message(pathway),
            "",
            "A previous attempt at this description was reviewed and the following claims were",
            "found to be wrong or unsupported:",
            "",
            objections,
            "",
            "Write the description again. Correct exactly these claims. Do not restate a claim you",
            "cannot support: leave it out rather than hedging it. Keep everything else that was",
            "sound, and obey every rule above as before.",
        )
    )


def parse_flags(text: str) -> tuple[Flag, ...]:
    """Read the verifier's reply into flags.

    Args:
        text: The stored completion text, a JSON object carrying a ``claims`` list.

    Returns:
        The flags, empty when the description was found sound.

    Raises:
        ValueError: If the reply is not the shape the schema requires. A reply that cannot be read
            is never treated as "nothing wrong" -- that would silently pass an unchecked row.
    """
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"verifier reply was not valid JSON: {error}") from error
    if not isinstance(parsed, dict) or not isinstance(parsed.get(RESPONSE_KEY), list):
        raise ValueError(f"verifier reply carried no {RESPONSE_KEY!r} list")
    flags: list[Flag] = []
    for entry in parsed[RESPONSE_KEY]:
        if not isinstance(entry, dict):
            raise ValueError(f"verifier claim was not an object: {type(entry).__name__}")
        kind = str(entry.get("kind", ""))
        if kind not in FLAG_KINDS:
            raise ValueError(f"verifier claim had unknown kind {kind!r}")
        flags.append(
            Flag(
                quote=_collapse(str(entry.get("quote", ""))),
                kind=kind,
                reason=_collapse(str(entry.get("reason", ""))),
            )
        )
    return tuple(flags)


def tally(results: Iterable[Sequence[Flag]]) -> dict[str, int]:
    """Count flags by kind across a set of verified descriptions.

    Args:
        results: One flag sequence per description.

    Returns:
        A count per kind, plus ``descriptions``, ``flagged`` and ``flags``. Every kind is pre-seeded
        to zero, so a kind that never fired still reports a number rather than going missing.
    """
    counts = dict.fromkeys(FLAG_KINDS, 0)
    counts["descriptions"] = 0
    counts["flagged"] = 0
    counts["flags"] = 0
    for flags in results:
        counts["descriptions"] += 1
        counts["flagged"] += bool(flags)
        counts["flags"] += len(flags)
        for flag in flags:
            counts[flag.kind] += 1
    return counts


_WHITESPACE = re.compile(r"\s+")


def _collapse(text: str) -> str:
    """Flatten whitespace so a flag can live in a TSV cell."""
    return _WHITESPACE.sub(" ", text).strip()
