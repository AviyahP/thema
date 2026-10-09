# Exclusion-2 rubric (ccode, 9 Oct 2026)

You are judging **input gene sets** for a biological ontology. For each set you see **only its
source name and its full generated description**. You do not see its genes, and you do not see how
it clustered. That is deliberate: the judgement must not be contaminated by either.

## The question, which is the declared rule

> **Does EITHER the name OR the description identify one specific biological theme?**

A **theme** counts if it is any one of:

- a **process** (e.g. glycolysis, apoptosis, mRNA splicing)
- a **system** (e.g. complement, the proteasome, the respiratory chain)
- a **pathway** (e.g. Notch signalling, TCA cycle)
- a **mechanism** (e.g. clathrin-mediated endocytosis, ubiquitin-dependent degradation)
- a **cell type or tissue** (e.g. plasma cells, cardiac muscle, retina)
- a **shared regulator** — a transcription factor, a sequence motif, or a TF target set. **A set
  defined as "the targets of X" or "genes with the X motif" DOES identify a theme.**

Answer **yes** (keep) if either the name or the description identifies one such theme.
Answer **no** (exclude) if **neither** does.

## What does NOT count as a theme

- a shared position in an experiment or screen — e.g. "co-occurs in interaction screens",
  "co-expressed in this dataset", "clusters together"
- a list of several unrelated themes with no single one dominating
- "housekeeping", "various", "miscellaneous", or an explicit statement that no single process unites
  the genes

## Important cautions

1. **A hedge is not automatically a no.** Many descriptions open by acknowledging breadth and then
   go on to name a real theme ("Although the members span several compartments, they converge on
   lysosomal catabolism"). If a theme is named, answer **yes**.
2. **A name alone is enough.** If the source name identifies a theme, answer **yes** even if the
   description wanders.
3. **"TBA" is not a name.** Where the name is `TBA`, the description must carry it alone.
4. **Breadth is not incoherence.** "Immune signalling" is broad but is one theme. "Immune signalling,
   lipid storage and cilium assembly" is three.
5. Judge only what is written. Do not use outside knowledge of what the module id usually means.

## Output

Return **one JSON object per line**, nothing else — no prose before or after, no code fence:

{"key": "<the key exactly as given>", "verdict": "yes", "sentence": "<the ONE sentence from the name or description that decides it, quoted or closely paraphrased>"}

- `verdict` must be exactly `yes` or `no`.
- `sentence` must be the single sentence that decided it — for a **yes**, the sentence naming the
  theme; for a **no**, the sentence showing that no theme is named. Keep it under 40 words.
