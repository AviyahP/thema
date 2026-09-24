# The encoder reads 55% of every description

*24 Sep 2026. Found while repairing the corrupted descriptions. It is the larger finding of the
two, and it is unresolved.*

---

## The measurement

`BioLORD-2023` is loaded with **`max_seq_length = 128` tokens**. Every description is truncated
there before encoding.

| | |
|---|---|
| descriptions embedded | 1,850 |
| median length | **231 tokens** |
| p90 / max | 261 / 331 |
| **exceed the 128-token cap** | **1,850 — 100.0%** |
| median fraction actually embedded | **0.55** |
| words reaching the encoder | ~75 of ~135 |

**Every description is truncated, and roughly 45% of each one has never been part of the
ontology.** The prompt is tuned to a 90-150 word band, the validator enforces that band, and the
word counts have been reported throughout as though they described what was embedded. They did
not. The second half of each description -- typically where the specific mechanism and the
distinguishing detail sit -- was discarded before the vector was computed.

Nothing warns. `embed()` is silent; the tokenizer emits `194 > 128` once, to stderr, from inside a
library call.

## How it was found

A naming call returned **"Nokia 5 launch and specifications"** for a glycosylation theme. The model
was reading its prompt correctly: `go:GO:0010560`'s description was 10,752 characters, a correct
paragraph followed by a scraped phone review. Repairing that and 204 other rows, then re-embedding
the 36 affected rows in the 1,850, moved the vectors by **exactly zero** -- because all the
appended junk sat past token 128.

## What it means for what has been measured

**The corruption's effect on the calibration is zero, not small.** E2 -- the calibration re-run on
the repaired embeddings -- reproduces E in every decision-bearing number: same real counts, same
per-size floors, same `m_eff`, **986 themes, overall held-out FDR 0.0030, no stratum dropped**. All
31 sides are byte-identical on `(arm, size, support)`. The `.tsv` files differ only in the
**cohesion** column, in the sixth decimal (`0.130022` -> `0.130023`), from float32 round-off when
the matrix was renormalised. Cohesion is descriptive and never a gate.

**Every result to date therefore describes an ontology built on truncated text.** That does not
make the results wrong -- the pipeline, the thresholds and the proofs are unaffected -- but it
changes what they are a result *about*.

## Can BioLORD read the whole thing?

Yes. The cap is configuration, not architecture: the underlying model is **MPNet with 514 learned
position embeddings**, and pooling is already mean-over-tokens. `max_seq_length = 512` runs without
error and covers the longest description at 331 tokens.

It is not a free switch. Measured over the 1,850, 128 against 512:

| | |
|---|---|
| cosine distance | median **0.069**, p90 0.123, max 0.295 |
| rows moving more than 0.05 | 1,389 of 1,850 |
| **nearest-neighbour agreement** | **56.7%** |

**Reading the full text changes which pathway is nearest to which in 43% of cases.** It is a
different embedding space, not a sharper version of the same one, so every threshold and the whole
calibration would have to be redone against it.

There is also a real caveat: positions 128-331 were pretrained in MPNet but **never fine-tuned by
BioLORD**. The second half of each description would be encoded by weights that never saw the
biomedical fine-tuning.

## Options, cheapest first -- none chosen

1. **`max_seq_length = 512`.** One line, no cost. Out-of-distribution past token 128.
2. **Chunk and mean-pool.** Split into <=128-token windows, embed each in-distribution, average.
   Every token is seen at a position the fine-tuning covered, and averaging windows extends what
   the pooling already does. The recommended route if the full text is wanted from BioLORD.
3. **Shorten descriptions to <=128 tokens** (~95 words). Needs regeneration and retires the 90-150
   word band.
4. **An encoder with native long context.** The largest change.

**How to decide it, rather than argue it.** Take pathway pairs that share a Reactome parent or a GO
ancestor and measure how well cosine similarity separates them from random pairs (AUC), for 128,
512 and chunk-mean. CPU only, no spend, and `data/hierarchy.py` already supplies the reference
structures. Not run.
