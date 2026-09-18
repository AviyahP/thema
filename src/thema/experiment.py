"""The three arms of the v4 prompt experiment, defined once so the runner only orchestrates.

Each arm is the same v4 prompt reaching the model by a different route, so that what differs
between arms is one mechanism at a time:

  A  plain          the v4 prompt, nothing else
  B  repair         the v4 prompt, then a separate verify-and-repair pass over what it wrote
  C  pre-check      the v4 prompt plus a two-field schema whose first field is written first

**Arm C is PRE-WRITING VERIFICATION, not self-critique.** It states what it has confirmed before it
writes, so nothing is being critiqued -- there is no draft yet. The accurate name is used here, in
the runner's output, and in the queue, because "self-critique" would later be read as evidence about
a revision step that was never tested.

``checks`` is scoring scaffolding. It never enters a descriptions table, is never embedded, and
never reaches a downstream consumer; it is kept in the ledger so a human can see whether the arm
checked anything. Only ``description`` is graded, so arm C earns no credit for what it claims to
have verified -- only for what it finally wrote.

**Arm B is graded against what it was optimised for, and that cannot be designed away.** It repairs
using ``verify-v1`` findings and is then scored by ``verify-v1``, so it will fix what that verifier
can see and leave what it cannot. Its advantage may therefore not generalise to errors a different
checker would catch. This is inherent to the arm, is stated wherever its score is reported, and is
the reason its result carries a caveat that arms A and C do not.
"""

from dataclasses import dataclass

from thema.normalize import PROMPT_VERSION, RESPONSE_FORMAT, SYSTEM_PROMPT

#: Appended to the v4 system prompt for arm C only.
PRE_CHECK_ADDENDUM = """

BEFORE WRITING THE DESCRIPTION

Return two fields, "checks" and "description". Fill "checks" first.

In "checks", list what you have confirmed about every gene you intend to name, against the four
requirements above: molecular identity, direction of effect, substrate or partner, and presence in
the gene list you were given. One entry per gene. If a check fails, do not make that claim -- write
the pathway-level biology instead, and record in "checks" that you dropped it.

"checks" is working notes and is discarded. Only "description" is kept, so the description must
stand alone and must never refer to the checks."""

#: Arm C's schema. ``checks`` is a LIST rather than a string on purpose: the client stores the whole
#: envelope whenever the keyed field is not a plain string, so a list is what keeps both fields on
#: the ledger record where the critique can be inspected.
PRE_CHECK_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "checks": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string"},
        },
        "required": ["checks", "description"],
        "additionalProperties": False,
    },
}


@dataclass(frozen=True, slots=True)
class Arm:
    """One experimental arm.

    Attributes:
        name: The label used in tables, reports and flag rows. Readable, not terse: two arms that
            differ only in which flags trigger a repair must say so where a reader will see it.
        slug: The filename stem. Kept separate from ``name`` so a name can be made clearer without
            renaming ``v4_b.tsv`` and orphaning every file already written under it.
        prompt_version: Cache namespace for this arm's generation ledger.
        system: The system prompt this arm sends.
        response_format: The structured-output schema.
        response_key: Which field the client keys the payload on. A non-string field stores the
            whole envelope, which is how arm C keeps its checks.
        assumed_output: Output tokens per completion assumed BEFORE any completion exists to
            measure. Arm C emits its checks as well as its description, so assuming the same
            figure as the other arms would understate it by the size of the thing that makes it
            different. Once one completion exists the ledger's own mean replaces this.
        repairs: Whether the arm runs a verify-and-repair pass after generating.
        repair_kinds: Which flag kinds trigger a rewrite. This was an implicit choice until
            2026-09-17 and the implicit answer was "all of them", which is why arm B rewrote 59
            descriptions to fix 9: ``unsupported`` is the verifier saying the gene list does not
            support a claim, not that the claim is false. Every one of the 11 descriptions the
            repair BROKE across both samples came from rewriting text flagged only that way, and
            none came from text carrying a real error. Made explicit so the choice is visible.
        caveat: Printed wherever this arm's score is reported; empty when there is none.
    """

    name: str
    slug: str
    prompt_version: str
    system: str
    response_format: dict[str, object]
    response_key: str
    assumed_output: int
    repairs: bool
    repair_kinds: tuple[str, ...]
    caveat: str


#: Arms A and B share generation entirely -- B is A plus a repair pass -- so B costs nothing extra
#: to generate and the two are guaranteed to start from identical text.
ARMS: dict[str, Arm] = {
    "A plain": Arm(
        name="A plain",
        slug="a",
        prompt_version=PROMPT_VERSION,
        system=SYSTEM_PROMPT,
        response_format=RESPONSE_FORMAT,
        response_key="description",
        assumed_output=420,
        repairs=False,
        repair_kinds=(),
        caveat="",
    ),
    "B repair (all flags)": Arm(
        name="B repair (all flags)",
        slug="b",
        prompt_version=PROMPT_VERSION,
        system=SYSTEM_PROMPT,
        response_format=RESPONSE_FORMAT,
        response_key="description",
        assumed_output=420,
        repairs=True,
        # As tested, and deliberately left so: the numbers reported for this arm on 2026-09-16/17
        # were produced by rewriting on every flag, and changing it here would make them
        # irreproducible. "D repair (errors only)" is the corrected arm.
        repair_kinds=("wrong", "unsupported"),
        caveat=(
            "REWRITES ON EVERY FLAG, INCLUDING 'unsupported': 59 of 100 descriptions rewritten to "
            "fix 9. All 11 collateral errors across both samples came from rewriting text that "
            "carried no error. See arm D for the same mechanism scoped to factual errors. ALSO "
            "GRADED AGAINST WHAT IT WAS OPTIMISED FOR: this arm repairs using verify-v1 findings "
            "and is then scored by verify-v1, so it fixes what that verifier can see and leaves "
            "what it cannot. Its advantage may not generalise to errors a different checker would "
            "catch. Inherent to the design; it cannot be removed."
        ),
    ),
    "C pre-check": Arm(
        name="C pre-check",
        slug="c",
        prompt_version=f"{PROMPT_VERSION}c",
        system=SYSTEM_PROMPT + PRE_CHECK_ADDENDUM,
        response_format=PRE_CHECK_FORMAT,
        response_key="checks",
        assumed_output=760,
        repairs=False,
        repair_kinds=(),
        caveat=(
            "PRE-WRITING VERIFICATION, not self-critique: the checks are written before the "
            "description, so nothing is critiqued. Only the description is graded."
        ),
    ),
    "D repair (errors only)": Arm(
        name="D repair (errors only)",
        slug="d",
        prompt_version=PROMPT_VERSION,
        system=SYSTEM_PROMPT,
        response_format=RESPONSE_FORMAT,
        response_key="description",
        assumed_output=420,
        repairs=True,
        # The rule this project recorded and then applied in only one of the two repair paths:
        # ``unsupported`` is a judgement about what the evidence supports, not about what is true,
        # and rewriting on its account trades a possible overreach for a possible new error.
        repair_kinds=("wrong",),
        caveat=(
            "GRADED AGAINST WHAT IT WAS OPTIMISED FOR: repairs using verify-v1 findings and is "
            "then scored by verify-v1, so it fixes what that verifier can see and leaves what it "
            "cannot. Inherent to the design. Unlike arm B it rewrites ONLY descriptions carrying "
            "a factual error, which is where all of arm B's collateral damage came from."
        ),
    ),
}
