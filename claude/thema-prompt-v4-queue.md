# Prompt v4 queue

Recorded, not implemented. Nothing here changes `PROMPT_VERSION` or the prompt text: a bump
invalidates every cached completion and re-charges the full run, so v4 changes are batched and
applied once, together, with a 100-sample check before any full run.

Each item states the change, the measurements that motivate it, the done-condition to check on the
v4 sample, and what it will NOT fix.

---

## 1. NAME HANDLING — replaces "repeat the name in quotes, first"

**Current rule** (`src/thema/normalize.py`, SYSTEM_PROMPT): *"Begin by repeating the pathway's name
in double quotes, exactly as given."*

**Replacement.** The pathway name should be incorporated into the description in a way that aids the
description: meaning preserved, exact phrasing not required, position anywhere in the text. The
anchor is the point, not the verbatim string in first position.

**Why — two measured problems from one rule.**

*It inflates the collision metric.* The cross-source collision test defines its positives as
pathways sharing a name, and the prompt puts that shared name inside the text being embedded. Both
members of every pair therefore carry the same string. Removing the name and re-running the
identical pipeline: co-clustering falls from **98.9% to 87.2%** at k=50 (lift 40x to 34x), and the
same fall appears at every cut (k=200: 98.9% to 79.8%). The claim survives — 87.2% at 34x is real —
but roughly 12 points of the headline was the literal name, and the write-up must quote the stripped
number.

*It creates a fixed opening template that lets grammatical shape drive clustering.* Reactome names
one family to a template, so **33 of 47** descriptions in that cluster open near-identically, and 22
continue `" describes what` — a phrasing absent from the top four openings table-wide. Re-embedding
with first sentences removed **shatters the cluster into 17 groups, largest holding 11 (23%)**,
while a size-matched control holds at 68% and overall partition agreement stays at **96.2%**. The
cluster's within-group gene Jaccard is **0.0047, the lowest of all 50 clusters**, against a 0.0034
random background — tight in embedding space, unrelated in genes.

**Done-condition on the v4 100-sample.** Report both, and both should fall substantially versus v3:

- fraction of descriptions whose first 8 words match another description's first 8 words
- fraction containing the pathway name verbatim

**Known limit, recorded so it is not mistaken for a failure.** This will not eliminate the Defective
family. Forty-seven pathways named `Defective X causes Y` share genuine vocabulary — gene symbols,
disease words, "inherited", "loss of function" — and that lexical overlap survives any prompt
change. The rule removes the *structural* component (a shared grammatical opening); the *lexical*
component is a property of the source's naming and stays.

---

## 2. NAME-FREE ABLATION — a new experiment, not a prompt change

**What.** Generate ~100 descriptions with the name withheld from the prompt entirely, so the prose
is coherent and never contained a name at any point. Compare collision recovery against v3 and
against the post-hoc name-stripped arm.

**Why.** Post-hoc stripping conflates two different things: signal genuinely carried by the name,
and grammatical damage from deleting a sentence's subject. The stripped text reads
`is the cell-autonomous 24-hour timekeeper that schedules gene expression...` — no subject, and the
most topical noun phrase gone. Two measurements say the damage is not small and not confined to
templated text: **48.1% of pathways change cluster** under the strip, and the correlation between a
cluster's mover rate and how much its members share an opening is **+0.096** — essentially none. The
instability is broad, which is what removing the topic phrase from every description would do, and
not what removing a template would do.

**Therefore 87.2% is a LOWER BOUND, not an estimate.** An unknown share of the 12-point drop and of
ARI(kept, stripped) = 0.348 is grammatical damage rather than lost signal. Only text written without
a name can separate the two.

**Cost.** ~100 descriptions, a few dollars, same batch gate as every other run.

**Why it is worth it.** This is the number worth defending: "our structural claim does not depend on
the model repeating the pathway name, and here is the arm that proves it" is a different statement
from "we deleted the name afterwards and the score mostly held up".

---

## Evidence index

| Claim | Where |
|---|---|
| 98.9% -> 87.2% on name strip, per cut and per overlap band | `scripts/name_strip_test.py` |
| Defective family: 33/47 shared opening, shatters to 17 clusters, J=0.0047 | DECISIONS 2026-09-10 |
| 48.1% movers, template correlation +0.096 | step C diagnostic, this queue |
| Band-matched nulls, five arms, all pair sources | `scripts/compare_baselines.py` |
| Pair supply per source and scale | `scripts/evaluation_pairs.py` |
