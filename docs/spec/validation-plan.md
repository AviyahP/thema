# THEMA validation plan

*Written 2026-09-23, **before any of these tests were run**. Pass conditions are declared here in
advance. A test graded after the fact is not a test, and any condition edited after seeing a result
must be recorded as an amendment with its date and reason, not silently revised.*

**Gate** = must pass before the ontology is called frozen. **Informational** = reported, argued
about, never used to justify a freeze on its own.

| # | test | kind | build | runtime |
|---|---|---|---|---|
| 1 | scramble error rate | **gate** | either | ~20 min/scramble |
| 2 | hierarchy shape vs curated ontologies | informational | either | seconds |
| 3 | `reactome2go` recovery, banded | **gate — headline** | **10,817** | ~2–4 h |
| 4 | sibling recovery, GO and Reactome | **gate** | either | ~1–2 h |
| 5 | the enrichment task | **gate, protocol not yet approved** | 10,817 | unknown |
| 6 | blind human rating | **gate** | 1,854 | ~1 h of Aviyah's time |
| 7 | wrong-description control | **gate** | 1,854 | ~2 h |
| 8 | contested-member validation | informational | either | ~15 min |
| 9 | seed stability | informational | 1,854 | ~40 min |

---

## 1. Scramble error rate — GATE

**Measures:** whether themes are distinguishable from themes built on data with the same marginals
and no structure. **A floor, not a quality measure.** Passing means "not noise" and nothing more.

**Statistic:** permute each embedding dimension independently across pathways, re-normalise rows,
run the identical pipeline. FDR = scrambled themes passing / real themes passing, per size band and
overall, averaged over calibration scrambles and evaluated on held-out scrambles.

**Baselines:** the scramble is the baseline.

**Pass:** overall held-out FDR **≤ 0.01**, no band above **0.02**.

**Build:** either. **Runtime:** ~20 min per scramble side; 20 calibration + 10 held-out ≈ 10 h
serial, ~2.5 h at four concurrent.

**Known limitation, stated because it motivates test 7:** this scrambles the EMBEDDINGS. It tests
the clustering step only and cannot detect a failure in description generation — descriptions that
are fluent, plausible and wrong would pass it cleanly.

## 2. Hierarchy shape vs human-curated ontologies — INFORMATIONAL

**Measures:** whether the structure resembles what curators build over comparable material.
Plausibility, never correctness: a hierarchy can have textbook proportions and group the wrong
things, and the MITF/mismatch-repair glue passes this test.

**Statistic:** node count, roots as a fraction of nodes, max and median depth, median branching
factor, multi-parent fraction, node-size distribution. Against **full** GO BP and full Reactome —
**not** induced over our subset, which gave 79% roots and median depth 0 and measured only how
sparsely the collection samples GO.

**Baselines:** GO BP (51,986 nodes, 20% roots, max depth 16, median 5, 31% multi-parent);
Reactome human (2,883 nodes, 1% roots, max depth 11, median 3, 1% multi-parent).

**Pass:** none declared — informational. A build whose roots exceed ~40% of nodes or whose median
depth is ≤ 1 is an outlier against both and that will be said plainly.

**Build:** either. **Runtime:** seconds.

**Caveat carried in every report of it:** GO and Reactome nodes ARE pathways, nesting by
subsumption; THEMA's nodes are SETS of pathways, nesting by member containment. Both are
containment orders; they are not the same object.

## 3. `reactome2go` recovery, banded — GATE, AND THE HEADLINE

**Measures:** THEMA's actual claim — that it co-clusters pathways curators call related,
**especially those sharing few or no genes**.

**Statistic:** for each curated pair, recovered = both pathways share at least one node (DAG) or
fall in the same cluster at the stated cut (flat). Reported as recovery rate **within gene-overlap
bands** `(0,0)`, `(0,0.01)`, `(0.01,0.05)`, `(0.05,0.15)`, `(0.15,1.01)`, each against a
**band-matched random-pair null** — "better than chance among pairs this similar?". Also the
cut-free form already implemented in `compare_baselines.py`: **AUROC and Cliff's delta**, curated
pairs against random pairs of the same band, which needs no threshold and so cannot be tuned by
choosing a flattering cut.

**Baselines — all three required:**

1. **gene-overlap clustering** — Jaccard, Ochiai, overlap coefficient, and Cohen's kappa
   (`GENE_MEASURES`), each with the linkage its geometry permits.
2. **RANDOM** — the band-matched null above.
3. **TF-IDF / lexical clustering on the SAME descriptions.** **Not optional.** If plain word
   overlap matches BioLORD in the zero-overlap band, the embedding is adding nothing over word
   counting, and that must be known before the freeze rather than after.

**The lexical control, and why it exists.** Band additionally by **lexical overlap between the two
CURATED texts** (not the generated ones), and report the cell where **gene overlap is 0 AND lexical
overlap is near 0**. The descriptions were written by a model that has read both Reactome and GO,
so without this control a recovery result may be measuring memorised phrasing rather than inferred
biology. **This cell is the headline number.**

**Pass:** in the `(0,0)` and `(0,0.01)` gene-overlap bands, THEMA's recovery exceeds **every** gene
baseline and the random null, with non-overlapping bootstrap intervals; **and** THEMA exceeds the
TF-IDF baseline in the zero-gene / near-zero-lexical cell. Failing the TF-IDF comparison is a
failure of this gate even if the gene baselines are beaten.

**Build: 10,817 — required.** Only ~10 name-controlled pairs exist in the 1,854 subset against ~90
at full scale; ten pairs cannot distinguish two methods.

**Runtime:** ~2–4 h including the baseline arms.

**Extension needed before it can run:** `compare_baselines.py` compares partitions and a DAG is not
one. The pair-recovery framing transfers directly — a pair is recovered if both pathways share at
least one node — but that adapter does not exist yet.

## 4. Sibling recovery on GO and Reactome — GATE

**Measures:** whether pathways a curator filed under one parent end up together. A **necessary
floor**: failing it would be damning.

**Statistic:** as test 3, over `sibling_pairs` computed separately for Reactome (from
`ReactomePathwaysRelation.txt`) and GO (from `go_parents`), banded by gene overlap, with the
band-matched null.

**Baselines:** the same three as test 3.

**Pass:** THEMA beats the random null in every band, and is not beaten by the gene baselines in the
`(0,0)` band. Reported separately for GO and Reactome, never pooled.

**Confounded, and labelled so wherever reported — but not circular.** Reactome's curators wrote
both the hierarchy AND the summation prose THEMA embeds, so recovering a sibling is partly "the
text encodes the tree". The same applies to GO. **This is a different thing from the name-collision
circularity:** a sibling test *can* fail, which is what makes it evidence; a name-collision test
cannot fail for any method that reads names, which is what makes that one circular. Necessary, not
distinctive.

**Build:** either. **Runtime:** ~1–2 h.

## 5. The enrichment task — GATE, PROTOCOL PROPOSED ONLY

**This has never been measured and it is what the tool is for.** A build could win every test above
and fail here. **The datasets below are a proposal; Aviyah approves them before anything is run.**

**Measures:** whether running enrichment against the hierarchy beats running it against a flat
pathway list, on datasets whose correct answer is agreed in advance.

**Proposed datasets** (each with a biology no reasonable analyst would dispute):

| dataset | agreed answer |
|---|---|
| an interferon-stimulation time course | type I interferon response |
| an LPS / TLR4 stimulation set | innate immune / NF-κB signalling |
| a hypoxia / HIF-1α set | hypoxia response, glycolytic shift |
| a cell-cycle arrest set | cell cycle, DNA replication |
| a whole-blood autoimmune RNA-seq set | interferon and/or neutrophil signature |

**Statistics, all three:**

1. **Rank of the correct biology** — position of the first theme a domain reader would accept as
   the agreed answer. Lower is better.
2. **Terms read to reach it** — how many entries a reader passes before the correct one. This is
   the redundancy cost a flat list imposes and the hierarchy is supposed to remove.
3. **Redundancy reduction** — among the top 20 results, the number of distinct biologies, and the
   maximum pairwise gene Jaccard among them. A flat list returns the same biology many times.

**Baselines:** the flat pathway list over the same universe with the same statistical test;
`ward_tree` at a matched cut; the same gene sets through a standard tool (DAVID-style kappa
merging) if available.

**Pass:** the correct biology ranks **no worse** against the hierarchy than against the flat list on
every dataset, and **terms-read-to-reach-it is lower on a majority**, with redundancy among the top
20 strictly lower.

**Who judges:** whether a theme "is" the agreed answer is read by Aviyah, blind to which method
produced the list. Claude Code does not grade this.

**Build:** 10,817. **Runtime:** unknown — the harness does not exist. Estimate after the protocol
is approved.

## 6. Blind human rating — GATE

**Measures:** whether a theme reads as biology. No automated metric substitutes for it.

**Design:** 30 THEMA themes drawn at random. For each, the **size-matched** Ward node closest in
size and not identical to it; pairs where no Ward node is within ±20% of the size are dropped and
the drop count reported. All 60 shuffled into one list.

**Blinding:** each theme is shown as **member pathway names and sources only** — no node ids, no
membership values, no parents, no supports, no method label. Order randomised with a recorded seed.
The key is written to `blind_key.tsv` and **not opened until every rating is entered**. Ratings go
in a separate file that does not contain the key.

**Rated on two axes, independently:**

1. **Coherence** — coherent / broad-but-fine / grab-bag.
2. **Nameable identity** — could you give this theme a biological name a colleague would accept?
   yes / partly / no.

**Pass:** THEMA's **grab-bag share is no more than 10 percentage points above Ward's**, and its
**"no nameable identity" share is no higher than Ward's**.

**Build:** 1,854. **Runtime:** ~1 h of Aviyah's time.

## 7. Wrong-description control — GATE

**Measures:** whether the pipeline can detect that the descriptions are wrong. **Test 1 cannot:**
it scrambles the embeddings, so it tests the clustering step only. Fluent, plausible,
wrongly-assigned descriptions would pass test 1 cleanly.

**Design:** shuffle the description-to-pathway assignment — every pathway keeps a real, well-formed
description, but the wrong one. Everything else identical: same embedder, same parameters, same
scramble calibration, same thresholds. Rebuild.

**Pass:** **nothing survives** — the build produces no themes meeting the frozen criteria, or a
false rate indistinguishable from the scramble null. If a shuffled build produces a comparable
number of themes at a comparable FDR, **the criteria are measuring embedding geometry rather than
biological content**, and the freeze does not proceed.

**Build:** 1,854. **Runtime:** ~2 h.

## 8. Contested-member validation — INFORMATIONAL FOR NOW

*Specified in `thema-master-spec.md` §14 item 2 and never implemented.*

**Measures:** whether fractional inclusion means anything. A pathway at inclusion 0.6 should be
genetically intermediate between the theme's settled members and random outsiders.

**Statistic:** for members with `inclusion < 1`, Jaccard(pathway genes, union of the genes of that
node's `inclusion == 1` members). Three groups compared: contested, settled, random non-members.
Medians and Mann–Whitney.

**Pass (when promoted to a gate):** contested sits strictly between settled and random with a clear
gap from random. **Fail:** contested ≈ random, meaning soft membership is noise.

**It is the test that would justify membership cutoff 0.25 over 0.50** — nothing else currently
adjudicates that choice. **Informational for now, and that is a statement about its implementation
status, not about its importance.**

**Build:** either. **Runtime:** ~15 min once written.

## 9. Seed stability — INFORMATIONAL

**Measures:** how much of the build is a property of the data rather than of the subsample seed.

**Statistic:** rebuild with a different master seed, identical everything else. Report theme-set
Jaccard (best-match over themes), the fraction of themes with a ≥0.9 match, and node-level
membership agreement for matched themes.

**Pass:** none declared — informational. **But:** if the theme-set Jaccard is low, the word
**"frozen"** is not used, because what would be frozen is a seed and not a finding. That
consequence is declared here in advance.

**Build:** 1,854. **Runtime:** ~40 min.

---

## Rejected: mean gene overlap within themes

**Considered and rejected as a quality metric.** It runs **inverse** to THEMA's purpose.

Measured on the 1,201-theme build: median within-theme gene Jaccard by source count — 1 source
**0.0718**, 2 sources 0.0542, 3 sources 0.0364, 4 sources **0.0286**; Spearman(n_sources, Jaccard)
= **−0.272, p = 7e-22**. Single-source themes are GO siblings, which share genes by construction
and are thematically trivial, and they score highest.

The NF-κB showcase card — four pathways THEMA is presented as correctly grouping — has mean
pairwise gene Jaccard **0.0076**, about **6.5× below the build median**. Using this metric would
rank the flagship example in the bottom decile.

**Genes are the right evidence used differently:** as the *independent axis* in tests 3 and 4
(banding, so recovery is measured where gene methods are blind), and as the *within-theme* three-way
comparison in test 8. Neither scores a theme on how much gene overlap it has.
