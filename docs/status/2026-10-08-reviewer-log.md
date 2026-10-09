# Reviewer log, 8 Oct 2026 — work done with Aviyah outside ccode

**Everything in this file is EXPLORATORY.** It records analysis the reviewer ran with Aviyah outside
ccode, on reviewer scripts that were not declared in advance, were not written or run by ccode, and
have **not been reproduced here**. The scripts themselves lived in `/tmp` on a VM and are gone; only
`data/experiments/llm_grouping_pilot/` survives. Treat every number below as a pointer to a question,
not as a measurement the repo can stand behind. **Where a number would change a decision, it needs
re-running under the declared protocol before it counts.**

Recorded so none of it is lost. Relayed by Aviyah; written down by ccode without re-running anything.

## Working rules, from now on (DECISION)

1. **The reviewer only analyses and writes prompts. ccode writes and runs all code.** No parallel
   reviewer scripts.
2. **Everything Aviyah and the reviewer try outside ccode is relayed to ccode to record**, as this
   file was.

The reason is visible in this log: a dozen results exist that nobody can reproduce, and at least one
of them (item 12) overturned an explanation that had already shaped a declared experiment.

## 1. Engine ceiling — can any clustering recreate the curated middle from leaves?

All of L; a random half of targets, seed 42; **best Jaccard > 0.5 before any gate**, so this is the
ceiling an engine could reach if the gate were free. Columns: Reactome 3–10 / 11–50 / 51–200, then
GO 3–10 / 11–50 / 51–200.

| engine | re 3–10 | re 11–50 | re 51–200 | go 3–10 | go 11–50 | go 51–200 |
|---|---:|---:|---:|---:|---:|---:|
| Ward tree, all nodes | 29.6 | 17.0 | 0 | 7.2 | 0.9 | 4.3 |
| spherical k-means (k 50–800) | 13.0 | 17.0 | 0 | 2.0 | 0.9 | 4.3 |
| bisecting spherical k-means | 13.6 | 6.4 | 0 | 0.6 | 0.5 | 4.3 |
| Ward + k-means | 32.0 | 19.1 | 0 | 8.3 | 1.4 | 4.3 |
| gated `thema_L` | 26.6 | 19.1 | 0 | 5.7 | 1.9 | 4.3 |

**No clustering recreates the curated middle from leaves.** The 51–200 column is 0 for every engine
on Reactome.

**This does not show the gate is harmless.** The gated build sits close to the ungated ceiling, which
would normally say the gate costs little — but the measure undercounts good groups, because a group
can be coherent and useful without matching a curated set at Jaccard > 0.5 (item 6). So the
comparison bounds what the curated benchmark can see, not what the gate removes.

Consequence: the leaves-centroid spec (`docs/spec/2026-10-08-leaves-centroid.md`) **is moot and was
not run** — a centre-based proposer cannot beat a ceiling that is already 0 in the band it targets.

## 2. Group-level signal, not pair-level

| | cosine |
|---|---|
| leaf to leaf within a curated group | 0.14–0.40 |
| leaf to its siblings' centroid | 0.35–0.53 |
| random groups | about 0 |

The signal that a curated group exists is in its **centre**, not in its pairs. This is the
observation the leaves-centroid spec was built on, and it survives even though that spec is moot.

## 3. LLM grouping pilot

Material: `data/experiments/llm_grouping_pilot/`. **No API spend** — the work was done by subagents.

Setup: 16 batches (10 Reactome, 6 GO), 481 leaves. Each batch holds the leaves of 4–7 sibling
summaries under one grandparent, so the right answer is "which sibling does each leaf belong to".
Blinded descriptions, plus a names-only arm. Subagents grouped them into 2–10 groups; outputs in
`out/`.

ARI, and groups recovered at Jaccard > 0.5. **Ward and k-means were given the true k**; the LLM was
not.

| | Reactome ARI / recovered | GO ARI / recovered |
|---|---|---|
| **LLM on descriptions** | **0.82 / 0.90** | **0.46 / 0.57** |
| Ward | 0.65 / 0.70 | 0.40 / 0.38 |
| spherical k-means | 0.64 / 0.67 | 0.33 / 0.28 |
| names-only arm | 0.84 | 0.59 |

The LLM beats both clustering engines on both sources, despite not being told k.

**Leakage, and it is substantial:** 13 of 98 labels equal the hidden parent name exactly, and 45 of
98 share at least half its words. So part of the margin is the model reciting curated vocabulary
rather than reasoning from the description — the same failure the direction pilot hit (63% of GO
"broader" phrases were verbatim curated ancestors). The names-only arm scoring *higher* than
descriptions on both sources points the same way.

**This needs re-running under the protocol before it counts**, with the leakage controlled rather
than measured after the fact.

## 4. Text rewrites — NEGATIVE

Material: `rewrites/`, `embed_rewrites.py`, `compare_rewrites.html`. Arms: neutral, process-only,
context-only. Two jobs were stopped by a safety filter (process 00–03, context 08–11), so the
batch sets differ between comparisons and the two rows below are not directly comparable.

| batches | orig | neutral | process | context |
|---|---|---|---|---|
| 04–15 | 0.52 | 0.55 | 0.48 | — |
| 00–07, 12–15 | 0.57 | 0.60 | — | 0.46 |

Ward ARI. Neutral rewriting gains about 3 points; stripping to process or context loses 4–11.
**Negative.**

## 5. One-sentence reductions — NEGATIVE

Aviyah's idea: reduce each description to one sentence about process, disease or tissue. Material:
`reductions/`, `embed_reductions.py`, `compare_reductions.html`. Ward ARI over all 16 batches:

| | ARI |
|---|---|
| orig | 0.56 |
| process | 0.40 |
| disease | 0.25 |
| tissue | 0.30 |
| joined text | 0.45 |
| orig + process vector | 0.54 |

Leakage: the exact parent name appears in 5% of process sentences, half its words in 25%.

**Negative: compression loses signal.** Nothing beats the original text, including concatenating the
reductions or appending the process vector.

## 6. Curated axes — different, both valid (DECISION)

- **Reactome** groups by **protagonist molecule** (a receptor or transcription factor) or by
  **mechanism stage**.
- **GO** groups by **logical class**: regulation direction × target class, or an abstract form.
- Text + Ward regroups the ERBB family **by step type instead of by receptor**. Both axes are valid
  descriptions of the same biology.

Mean within-group gene Jaccard:

| | curated | text Ward | LLM | random |
|---|---|---|---|---|
| Reactome | 0.140 | **0.149** | **0.155** | 0.051 |
| GO | 0.028 | **0.032** | **0.041** | 0.009 |

**Text and LLM groups are at least as gene-coherent as the curated ones they disagree with.** So
disagreement with curation is not evidence of error.

**DECISION: independent coherence — genes, and an intruder test — is the PRIMARY evaluation. Curated
agreement is secondary.** This reverses the weighting every evaluation in this repo has used so far,
and it is the most consequential item in this log.

## 7. Levels and the shape of `thema_L`

Mean within-group gene Jaccard, THEMA / Reactome / GO / random:

| band | THEMA | Reactome | GO | random |
|---|---|---|---|---|
| 3–5 | 0.169 | 0.203 | 0.066 | 0.000 |
| 21–50 | 0.059 | 0.049 | 0.014 | 0.001 |
| 51–300 | 0.02–0.04 | 0.02 | 0.007 | 0.001 |
| over 300 | 0.002–0.004 | 0.002 | — | 0.001 |

**The conceptual top cannot be validated by genes, even for Reactome** — above 300 members the
curated hierarchy is itself at 0.002 against a random 0.001. ccode's own measurements found the same
thing twice independently (the theta arms and the one-linkage step 1 both give 1.4–1.9× at 1001+), so
this one is corroborated.

Leaves by the largest theme of 1,000 or fewer they reach: **3% none, 10% at 3–10, 40% at 11–50, 19%
at 51–300, 27% at 301–1000.**

DAG shape:

| | roots / parentless | children | multi-parent |
|---|---|---|---|
| Reactome | **29 top areas** | 8–18 each | 1% |
| GO (MSigDB subset) | 611 parentless terms | — | 61% |
| `thema_L` | 40 roots | giant roots have **50–227**; median 2 per node | — |

Reactome's 29 areas with 8–18 children each is the target shape. `thema_L`'s roots with 50–227
children is the defect.

## 8. Areas from theme centroids — one run, k=30 by hand

Units: 526 maximal themes of 300 or fewer members, plus 200 leaves. Method: normalised centroids,
Ward cut at 30. Result: **about 30 intuitive areas** —

TGF-β/Wnt; amino-acid metabolism; development; synaptic transmission; cell cycle; translation; ECM;
apoptosis/p53; innate / adaptive / antiviral / inflammasome immunity; chromatin; membrane traffic;
lipid regulation; cardiac; smooth muscle; ion transport; endocrine; RHO/actin.

This is the result that motivated the one-linkage experiment. Note what it actually did: it clustered
**already-built themes** by their centroids, not raw leaves. ccode's engine C clustered raw leaves and
got 8 coherent areas at a 30-cut, not 30 — so the two are not the same experiment, and the 30-area
result has not been reproduced from leaves.

## 9. Other checks

- **Gene coverage:** leaves cover 82% of genes (Reactome 89%, GO 69%).
- **GO source:** MSigDB C5 GO:BP, roughly 5–2,000 genes per set. GO "immune response", "immune system
  process" and "innate immune response" are **absent from the universe**; why is still to be checked.
- **Placement:** the smallest theme holding at least 80% of a summary's leaves is a **giant root in
  30–73% of cases**. Placement needs a real middle; failing that, show summaries as **tags across
  themes** rather than as nodes.

## 10. Prior work read

| | |
|---|---|
| Bravi 2026 | uses Reactome's ancestor map; weak metrics; about 38% of edges by back-calculation |
| NeXO 2013 | about 25% of GO BP; restructuring into multi-way joins plus extra parents |
| LLMs4OL | GO F1 **0.049** |
| OLLM, HiT, OnT | trained on the target hierarchy |
| Hu et al., *Nature Methods* 2024 | GPT-4 GO naming about 60% close |
| also | LENS (ICLR 2026 workshop); EMNLP 2025 multi-aspect taxonomy clustering; PAVER |
| LlmBdc (arXiv 2608.00099) | **not yet read** |

## 11. Ideas contemplated, not run

- **LLM as the similarity function**: it judges embedding neighbours, and the calibrated clustering
  builds the levels.
- **Facets**: tissue and disease tags on one main hierarchy, versus separate per-facet hierarchies.
- **Data-driven aspect discovery**: multi-view or alternative clustering, or recurring LLM-proposed
  axes.
- **Near-copy collapse**, NeXO-style.
- **Reactome reactions as finer atoms.**
- **A memorisation probe and a post-cutoff pathway test before any LLM-built level.** Given the
  leakage in items 3 and 5, this is a prerequisite rather than an extra.
- **Paper framing**: calibrated recurrence + levels + contamination-aware evaluation. Venues:
  ICLR/NeurIPS bio workshops; ISMB/*Bioinformatics*.

## 12. One-linkage step 1 — the reviewer's reading (DECISION)

- **C's 6.4× more 51–1000 nodes is mostly chaining**, not extra levels: nested near-copies, a node
  with 72 children after collapse, 19 singletons in the cut at 30. **The declared criterion counted
  raw tree nodes, which rewards chaining — record that as a flaw of the criterion.** ccode's own step
  1 report flagged the same three symptoms; the reviewer's reading is that they are the whole effect.
- **The raw Ward tree is balanced** — at most 4 children after collapse, sensible cuts at every
  level. **The reviewer's earlier explanation, that Ward's size weighting lets blobs swallow groups,
  is WITHDRAWN.** The 100–227-child roots come from the **built DAG**: intermediate nodes fail the
  gate, and their children attach to the root instead.
- **Step 2 for C is NOT approved.**
- **DECISION: UPGMA (engine A) is recorded as a candidate alternative engine, to revisit later.** On
  step 1 it had well-formed cuts, the best curated recall (Reactome 3–10 .364 against Ward's .334),
  took 0.2 s a tree, and needs no new code. **For now Ward stays**, and the next test is the re-gate
  grid.

That withdrawal is why the gate, not the merge rule, is the next thing tested: if intermediate nodes
exist in the tree and are removed by the gate, the fix is in the gate.

## 13. Process notes

- The reviewer once ran `git status` on the Mac by mistake. It was read-only, left no lock files, and
  the index was unchanged.
- Reviewer scripts lived in `/tmp` on the VM and are gone. Only the files under
  `data/experiments/llm_grouping_pilot/` remain. Its `KEY_DO_NOT_SHARE.tsv` is gitignored, as is any
  file of that name anywhere.
