# Naming: the first smoke run, and what it found

*24 Sep 2026. 50 themes of the 1,201 in `v0.2/recurrent_dag_single_banded`, bottom-up closed,
seed 20260924. Sonnet 5 only. **Actual spend $0.34** against a $0.78 quote.*

---

## Result

38 named, **12 declared unnameable**, 4 revised by the top-down pass, 3 failed a mechanical check.

Two bugs of mine preceded it, both of which cost money for no output:

- the per-model client in the two-model loop was built without `response_key`, so every call parsed
  against the default `"description"` key. 200 calls, ~$2, nothing usable.
- `generate()` built a request-key -> node map and never filled it, so each level crashed *after*
  its calls returned. `disambiguate()` was already correct.

## The refusals were the prompt's fault, not the DAG's

Eight of twelve said a version of *"the parent has only a single child, so any parent name would
just restate it"* -- on nodes that are plainly nameable as biology: Notch, hemostasis, NF-kappaB,
monocyte cytokine signalling.

Task B was showing an internal node its children's names and three sampled members, and **never
distinguished the members belonging to no child**. Those direct members are exactly what makes a
parent broader than its child. Without them a single-child node is indistinguishable from its
child, and refusing is the correct answer to the question that was actually asked.

`render_internal` now states them, labelled, with the count -- including "(none)" when there are
none, which is the only case where a single-child node really is a restatement. Prompt version
bumped **`name-v1` -> `name-v2`**: the prompt changed, so the cache must not answer.

**Re-running the 12 refused nodes under `name-v2`: 10 of 12 now name.**

| | |
|---|---|
| now name | **10 / 12** |
| still refuse | 2 -- genuinely heterogeneous, and the rationales say why |
| **genuine pass-throughs** (single child, adding only partial-inclusion members) | **0** |

Names recovered include "Notch signalling regulation and transcriptional output", "Hemostasis and
coagulation", "NF-kappaB and NOD-like receptor signalling", "Adrenal corticosteroid biosynthesis
and disorders". The two remaining refusals are a mix of chromatin, metabolic and mitotic
regulators, and two broad unrelated housekeeping modules.

**No node in the sample was a genuine pass-through.** Every single-child node added direct members
at full inclusion.

## The checker flagged three names, all of them correct

- `Protein O-glycosylation` -- `sentence_case`, because `O-` is capitalised. It is a chemical
  locant. `O-`, `N-`, `C-` and `S-` before a lowercase word are now accepted.
- `Hemophilia-associated factor VIII/IX defects` -- `associated`, because the tokenizer split the
  hyphenated compound and flagged the fragment. A hyphenated compound is now one content word.
  Standalone `associated` still flags.
- `Ubiquitin ligase activation and chromatin protein turnover` -- `in_range`, 7 words against a
  limit of 6. **This one stands.** The limit is not relaxed.

## A description-table defect the naming run exposed

One node came back named **"Nokia 5 launch and specifications"**. The model was not hallucinating:
the prompt genuinely contained a smartphone review. The description of `go:GO:0010560` is 10,752
characters -- a correct paragraph about glycoprotein biosynthesis followed by a scraped web page,
closing `</p></div>`.

**66 of 10,770 descriptions (0.61%) carry appended junk**: 64 with HTML tags, one with a URL and a
blog timestamp, one with the phone review. All are **v4, opus-5, `stop_reason: end_turn`** -- the
model continued past the description and the API called it a normal completion. Output ran to
**4,651 tokens** against a typical ~330; the median description is 969 characters and the 99th
percentile 1,122, so seven of these are gross outliers.

Every one begins with a correct description. The corruption is always appended.

This matters beyond naming: **these descriptions fed the embeddings**, so they are in the ontology,
and they would reach the public demo. The validator does not test for trailing markup, a length
ceiling, or off-topic continuation, and `--report` did not flag them. The fact-check pass
(`verify-v1`, 13 wrong per 100) measures a different failure and would not catch this either.

Not yet fixed. The repair is a targeted regeneration of the 66 keys, which
`normalize_descriptions.py --keys FILE` already supports, plus validator rules for the three
signatures above.

## Production price, corrected

Two things were wrong in the earlier quote.

**Prompt caching was in the docstring, not the arithmetic.** `_cost()` computes
`calls * user_tokens + system_tokens`, and `count_tokens()` already *includes* the system prompt in
`user_tokens` -- so the 956-token system prompt was billed at full rate on every call and then
added once more. The run proves caching works: **59,500 cache-read tokens across 50 calls**, which
is why actual was $0.34 against $0.78.

**"Batch is impractical" was an assumption, and it was too strong.** From 28 real batches of <=200
requests -- the shape a naming level has:

| | |
|---|---|
| median | 13.6 min |
| mean | 99.5 min |
| p75 | 257.0 min |
| p90 | 301.8 min |
| max | 565.5 min (9.4 h) |
| **under one hour** | **19/28 = 68%** |

68% return inside an hour, but a third take 4-9 hours. Over 20 sequential levels: **4.5 h if every
level hits the median, 33 h at the mean, and a single p90 level is 5 h on its own.** Honestly
stated, Sonnet-batch is a coin flip between one night and two days -- not impractical, and not
dependable either.

**Sonnet, 7,000 themes (12,180 calls at 1.74 calls per theme):**

| | script said | correctly cached |
|---|---|---|
| live | $108.87 | **$77.71** |
| batch | $54.44 | **$38.86** |
