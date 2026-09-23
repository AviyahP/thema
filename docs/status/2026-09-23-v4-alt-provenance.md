# `v4-alt`: 13 descriptions not written by Claude — 23 Sep 2026

*A status note so the `v4-alt` class is auditable without reference to any conversation.*

## What it is

13 of the 10,817 Reactome pathways were refused by the v4 Anthropic batch (`stop_reason=refusal`,
no text block). All 13 are toxin or viral-pathogen pathways. All 13 **have genes** and remain in
the universe under the universe rule, so they cannot simply be dropped.

They were obtained elsewhere and are stored as a **separate generation**: `prompt_version =
v4-alt`, `status = superseded`, `model = gpt-5-6-thinking` on every row.

**These 13 descriptions were not written by the model that wrote the rest of the table.**

## How they were produced

- **2026-09-23**, through the **ChatGPT web app** at chatgpt.com on a Plus account, driven by
  browser automation. **Not an API call.**
- Model **`gpt-5-6-thinking`**, slug read from the page's own message metadata rather than inferred
  from a UI label.
- **Reasoning effort High** — the app default. The Anthropic v4 batch ran at
  `output_config.effort = low`.
- **One fresh temporary chat per pathway**, set to Unpersonalized, with memory, plugins and custom
  instructions off and nothing saved to history. No pathway ever shared a context with another.
- **One user message, one reply.** No follow-ups and no regeneration; the first reply was taken in
  every case.
- Input: the system prompt and the user block from `data/keys/refused_13_prompts.md`, pasted as a
  single message with a line containing only `---` between them.
- Output: every reply came back as `{"description": "..."}` **because the prompt asks for it, not
  because a schema was enforced** — no JSON schema, no `max_tokens`. The wrapper was stripped when
  the TSV was written. Nothing else was edited.
- All 13 paragraphs are **108–123 words** against the 90–150 target, and all pass the mechanical
  validator.

## The two things that are not identical to the v4 batch

1. **The system prompt was re-flowed.** The user blocks are byte-identical to
   `render_user_message()`. The system prompt is that file's text with hard line-wrapping re-flowed
   to one line per paragraph — no wording changed, both worked examples kept, OUTPUT FORMAT line
   kept — but it is a different byte sequence from what the Anthropic batch received.
2. **No structured output.** The v4 batch enforced a JSON schema and set `max_tokens = 8000`.
   Neither applied here.

## Two rows were re-run

`botA` (`reactome:R-HSA-5250968`) and `botB` (`reactome:R-HSA-5250958`) were first produced under a
different, flattened rendering of the prompt. **Those answers were discarded** and both were re-run
under the procedure above, so all 13 rows come from one identical procedure.

## Status

**Promoted to `status = current`.** `read()` now returns **10,770** — the whole universe, every
pathway described: 10,757 rows by `claude-opus-5` and 13 by `gpt-5-6-thinking`. The readable
generation therefore spans two models, and `prompt_version` plus the per-row `model` column are
what record it.

Verification: verify-v1 was run against this generation using `verify_descriptions.py
--generation v4-alt` (added because a non-current generation is invisible to the default reader) —
**0 of 9 checked, 4 refused by the verifier**. No further verification was done; the v4 batch was
not verified row by row either.

**Hazard:** the readable generation spans two `prompt_version` values, and `restamp()` promotes
exactly one. The next promotion must name both, or it will silently demote these 13.
