# S2 against O50s: PART 1 inputs and PART 2 section C, 22 Oct 2026

Prompt 55, evaluation only. No build changed, nothing adopted. **The judgement rule is declared in
the prompt and is the reviewer's to apply. It is not applied here, and no verdict is offered below.**

**Scope: PART 1 and all four PART 2 sections are complete.** The prompt estimated at about 6 h 35
against its 5 h ceiling, so C alone was run first under its fallback instruction; Aviyah then asked
for F, then E, then G, and all three are now done. Nothing in PART 2 remains.

The readings themselves -- R, T, I and S -- are prepared and have not been judged.

---

# PART 1: the reading inputs

Seed 20261022 throughout. Builds: frozen O50s (5,658 themes, 261 roots) and S2 (5,646 themes, 270
roots). Shares, missing counts, build labels, node ids and sizes-by-build are **only** in
`KEY_DO_NOT_SHARE_S2_vs_O50s.json`, written once and not read again by this session.

| input | what | items | batches | paths |
|---|---|---:|---:|---|
| **R** | roots with no root of the other build at J >= 0.9, pooled and shuffled | **207** | 5 | `read_roots/R_b01.md` ... `R_b05.md` |
| **T** | themes unique to one build (best J < 0.9 to ANY theme of the other), bands 12-24 to 100-199 | **294** | 7 | `read_themes/T_b01.md` ... `T_b07.md` |
| **I** | the C6 intruder test over the same T themes | **122** | 4 | `intruder/I_b01.md` ... `I_b04.md` |
| **S** | the small-root test over every S2 root of 50 or fewer | **174** | 10 | `small_inputs/S_b01.md` ... `S_b10.md` |

All under `data/experiments/S2_vs_O50s_2026-10-22/`.

## R: the roots that differ

**108 of S2's 270 roots have no O50s root at J >= 0.9, and 99 of O50s's 261 roots have no S2 root at
J >= 0.9.** Pooled and shuffled into 207 unlabelled items. This is root-to-root by construction, as
the prompt specifies -- a root of one build may still match a non-root theme of the other, and 108
and 99 are therefore upper bounds on "roots that have no counterpart at all".

## T: two short bands, stated

Six of the eight band-build cells supplied the full 40. Two did not and were taken whole:

* S2 100-199: **24** available, all taken
* O50s 100-199: **30** available, all taken

## I: 172 of the 294 T themes could not get an intruder item

The C6 recipe needs at least four **maximal strict subsets** of the target among themes of 5 to 150
pathways. 172 of the T themes have fewer than four, which is expected in the smaller bands -- a
12-pathway theme rarely contains four distinct sub-themes of 5 or more. **This is a property of the
recipe and falls on both builds alike**, not a finding about either. The surviving 122 items carry
five candidate units plus one intruder, shuffled and lettered, with batches taken by stride exactly
as the 17 Oct run did.

## Mechanical checks on the blind inputs

* every item id appears exactly once as a header; every other line is `- name [source]`
* **no node id and no build label appears in any batch.** The only `S2` substrings are gene names
  (`NPAS2`, `PAPSS2`, `TRPS2`, `NEP/NS2`) and the string `O50s` appears nowhere
* S: 174 items, each with exactly three container headers labelled P, Q, R
* I: 122 items with 710 unit headers, so no item exceeds six units
* no root, theme or item is split across a batch boundary

---

# PART 2, section C: duplication

Computed by `scripts/s2_duplication.py`, which is new: no existing script covers either measure for
these builds. Both measures run on each build's own final DAG, by the same code for both.

## C1. Non-nested pairs at J >= 0.5 that remain

Banded by the **larger** theme of the pair, stated because the choice changes the table. Sibling
means sharing an immediate parent or both being roots -- `build_s2.sibling_predicate`, the same
definition the S2 build used.

| band | O50s pairs | O50s non-sibling | S2 pairs | S2 non-sibling |
|---|---:|---:|---:|---:|
| 6-11 | 0 | 0 | 41 | 41 |
| 12-24 | 0 | 0 | 150 | 150 |
| 25-49 | 0 | 0 | 157 | 157 |
| 50-99 | 0 | 0 | 52 | 52 |
| 100-199 | 0 | 0 | 9 | 9 |
| 200-399 | 0 | 0 | 2 | 2 |
| 400-799 | 0 | 0 | 1 | 1 |
| 800-1599 | 0 | 0 | 1 | 1 |
| **ALL** | **0** | **0** | **413** | **413** |
| non-sibling share | - | - | | **100.0%** |

**O50s has none and S2 has 413, every one of them a non-sibling pair.** Neither number is a
surprise and both are exactly right:

* O50s's zero is guaranteed by `repair.assert_no_stale_pair`, which refuses any build where such a
  pair survives. The measure confirms the invariant rather than discovering anything.
* S2's 413 are precisely the pairs its restriction declines to merge. **They are the same 413 that
  tripped that invariant during the S2 build** before it was made restriction-aware -- an exact
  cross-check between two independently written pieces of code, and the reason to trust the count.
* The 100% non-sibling share is true by construction, not evidence: S2 merges every sibling pair
  above the cutoff, so whatever remains can only be non-sibling.

So C1 does not measure whether S2 duplicates more in any substantive sense. It measures the size of
the hole the restriction deliberately leaves: **413 pairs, 307 of them in the 12-49 bands.** Whether
those 413 are two views of one thing or two genuinely different themes is a reading question, and
those are exactly the themes PART 1's T sample draws from.

## C2. Nodes at least 80% inside another node without being its descendant

Each node counted once, in the bin of its **best** qualifying container -- the one missing fewest of
its pathways. Descendant is transitive, so a node under a container by a chain of edges is properly
placed and is not counted. The pair count is given beside it so both readings are available.

| pathways missing | O50s | S2 |
|---|---:|---:|
| 0 | 0 | 0 |
| 1-5 | 2,596 | 2,597 |
| 6-20 | 174 | 185 |
| 21+ | 9 | 8 |
| **nodes** | **2,779** | **2,790** |
| share of themes | 49.1% | 49.4% |
| pairs | 5,776 | 6,040 |

**Essentially identical: 2,779 against 2,790 nodes, 49.1% against 49.4%.** The difference is 11
nodes out of about 5,650, and it is in the 6-20 bin.

The empty `0` row is structural, not a finding: if a node's pathways are *all* inside a strictly
larger node, strict containment makes that node an ancestor by definition, so it can never be
counted here. The measure therefore only ever sees near-containment, and **the overwhelming mass is
1-5 pathways short in both builds** -- 93.4% of O50s's cases and 93.1% of S2's.

This is the same phenomenon the 22 Oct checks found in S1p, where 84.1% of its new small roots were
within 3 pathways of being contained. It is a property of strict containment as an edge rule, it is
already present in O50s at half of all themes, and **S2 neither improves it nor makes it worse.**

---

# PART 2, section F: stability across half-builds

Runs 1-100 and 101-200 built independently, each through its own build's steps, final themes matched
at J >= 0.70, worse direction reported. `scripts/s2_stability.py`; matching uses
`theme_match.best_matches`, the statistic the RUNS ladder is stated over.

| | themes 1-100 | themes 101-200 | 1-100 -> 101-200 | 101-200 -> 1-100 | **worse** |
|---|---:|---:|---:|---:|---:|
| O50s | 4,814 | 4,691 | 0.5862 | 0.5960 | **0.5862** |
| S2 | 4,958 | 4,828 | 0.5817 | 0.5903 | **0.5817** |
| **S2 - O50s** | | | | | **-0.0045** |

Median best J: O50s 0.7500 both directions; S2 0.7460 and 0.7500.

**How the gate was transferred, because it is a real choice and the first attempt was wrong.** Six
of the thirteen stored floors are solved rates (0.84 down to 0.030151) and transfer directly. The
other seven are all exactly 0.01, and that value is **not a solved rate** -- O50s's own report marks
those strata as decided by the rule-of-three bound, where no scrambled candidate was seen at or
above the cut. On 200 runs a floor of 0.01 means "found by at least 2 runs"; on 100 runs the same
0.01 means "at least 1 run".

Applying the stored floors unchanged was tried first and **rejected on measurement grounds**: it
gates **38,811 themes of which 59.5% were found by exactly one run of 100** (38,565 and 60.1% for
the other half). A stability figure over that set measures how often single-run noise repeats. The
seven bound floors are therefore transferred as a run count -- 2 runs of 100, i.e. 0.02 -- and the
six solved rates left alone, which gates 15,726 and 15,377. **The choice is held identical across
both arms**, so the S2-against-O50s difference is unaffected either way; it is the absolute rates
that move, and they are not comparable with a 200-run build.

# PART 2, section E: agreement, placement, recall and sibling specificity

## E1. Curated recall per band, J > 0.5, with CIs

`scripts/s2_recall_ci.py`, a thin wrapper over `scripts/v04_score.py`: the estimator, bands,
bootstrap (1,000 draws) and seed (0) are all v04_score's, and all 504 Reactome and 2,388 GO curated
sets are used. The wrapper exists only because v04_score prunes the bootstrap draws when it writes
its JSON, so the per-arm intervals cannot be recovered from that file.

| source | band | n | O50s | 95% CI | S2 | 95% CI | S2-O50s | CI of difference |
|---|---|---:|---:|---|---:|---|---:|---|
| reactome | 3-10 | 371 | 0.4906 | [0.4420, 0.5391] | 0.4906 | [0.4444, 0.5414] | +0.0000 | [-0.0106, +0.0108] |
| reactome | 11-50 | 111 | 0.4775 | [0.3781, 0.5692] | 0.4505 | [0.3565, 0.5455] | -0.0270 | [-0.0661, +0.0101] |
| reactome | 51-200 | 19 | 0.3158 | [0.1053, 0.5264] | 0.2632 | [0.0625, 0.4706] | -0.0526 | [-0.1818, +0.0000] |
| go | 3-10 | 1,645 | 0.1258 | [0.1097, 0.1424] | 0.1240 | [0.1081, 0.1398] | -0.0018 | [-0.0055, +0.0019] |
| go | 11-50 | 558 | 0.0520 | [0.0344, 0.0729] | 0.0466 | [0.0303, 0.0649] | -0.0054 | [-0.0127, +0.0000] |
| go | 51-200 | 142 | 0.0493 | [0.0187, 0.0876] | 0.0493 | [0.0187, 0.0876] | +0.0000 | [+0.0000, +0.0000] |

**No recall cell's difference CI excludes zero.**

## E2. Curated precision per band, J > 0.5

| source | band | n | O50s | S2 | S2-O50s | CI of difference |
|---|---|---:|---:|---:|---:|---|
| reactome | 3-10 | 2,514 | 0.1722 | 0.1737 | +0.0015 | [-0.0012, +0.0044] |
| reactome | 11-50 | 996 | 0.1817 | 0.1787 | -0.0030 | [-0.0088, +0.0042] |
| reactome | 51-200 | 53 | 0.1132 | 0.1333 | +0.0201 | [-0.0211, +0.0245] |
| go | 3-10 | 2,700 | 0.0796 | 0.0790 | -0.0006 | [-0.0016, +0.0007] |
| go | 11-50 | 2,007 | 0.0254 | 0.0253 | -0.0001 | [-0.0017, +0.0018] |
| go | 51-200 | 138 | 0.0652 | 0.0500 | **-0.0152** | **[-0.0152, -0.0004]** |

**One cell of twelve has a difference CI excluding zero: GO precision at 51-200, S2 lower by
0.0152.** It rests on 138 themes and is the smallest cell in the table.

**The per-arm precision intervals are deliberately omitted here, and the reason matters.**
v04_score's precision bootstrap resamples the *curated-set pool*, and a theme's precision depends on
which sets are in the pool, so the bootstrap distribution sits below the point estimate by
construction -- O50s's Reactome 3-10 precision is 0.1722 with a bootstrap interval of
[0.1058, 0.1337], which does not contain its own point estimate. That is documented behaviour of
that estimator, not an error introduced here, but it means those intervals cannot be read as
uncertainty around the point. The **paired difference** CIs are unaffected and are what the table
reports.

## E3. Sibling specificity AUROC, with CIs

`scripts/s2_sibling_auroc.py`. **No existing script reports an AUROC, so the measure is defined
here and the definition is part of the result.** Positives are curator-declared sibling pairs from
`thema.evaluation.sibling_pairs`, in both the unrestricted and the fan-out<=6 form because
`validate_dag` reports neither alone. Negatives are 399,920 uniform random pathway pairs, seed
20261003, **not matched on gene overlap** -- validate_dag bands its null that way for a recovery
rate, and matching here would control away part of the signal an AUROC measures. The score of a pair
is how many themes contain both, the graded form of validate_dag's boolean "shares at least one
theme". Ties count as half, via `top_two_arms.auc`. CI is a percentile bootstrap over 2,000
resamples.

| source | pairs | O50s AUROC | 95% CI | S2 AUROC | 95% CI | S2-O50s | CIs overlap |
|---|---:|---:|---|---:|---|---:|---|
| reactome-siblings | 6,414 | 0.8859 | [0.8817, 0.8901] | 0.8915 | [0.8873, 0.8956] | +0.0056 | yes |
| reactome-siblings (fan-out<=6) | 1,163 | 0.9615 | [0.9541, 0.9681] | 0.9644 | [0.9577, 0.9709] | +0.0029 | yes |
| go-siblings | 6,806 | 0.8242 | [0.8187, 0.8296] | 0.8276 | [0.8221, 0.8331] | +0.0035 | yes |
| go-siblings (fan-out<=6) | 1,170 | 0.9671 | [0.9609, 0.9728] | 0.9669 | [0.9610, 0.9722] | -0.0002 | yes |

Mean themes containing both members of a pair: siblings 7.93 (O50s) against 8.15 (S2) for Reactome,
6.17 against 6.23 for GO; random pairs 1.01 against 1.07. **Every difference is within 0.006 and
every CI overlaps.**

## E4. The prompt-54 rows, repeated for S2

Carried over unchanged from `docs/status/2026-10-22-S2-sibling-restricted.md`, computed there by the
same code for both builds.

| | O50s | S2 |
|---|---|---|
| O50s themes with a counterpart at J >= 0.9 | - | **84.7%** |
| by band: 3-5 / 6-11 / 12-24 | - | 100% / 98.7% / 83.3% |
| by band: 25-49 / 50-99 / 100-199 | - | **63.3% / 55.8% / 55.2%** |
| by band: 200-399 and above | - | 89.5% to 100% |
| summary placement at 80% (of 2,370) | 2,194 (92.6%) | **2,204 (93.0%)** |
| Reactome median best Jaccard (29 of 29 branches) | 0.273 | **0.273** |

# PART 2, section G: gene coherence against size-matched random sets

`scripts/s2_gene_coherence.py`, new. A theme's coherence is the mean pairwise gene Jaccard over its
members; its null is the same statistic on a random pathway set of the **same size**, so the match
is by construction rather than by correction. 5,539 pathways, 15,552 gene slots, median 10 genes per
pathway. **Up to 500 member pairs are sampled per theme**, seed 20261022, with one size-matched null
set per theme.

| band | O50s obs | null | lift | S2 obs | null | lift | exact (O50s) |
|---|---:|---:|---:|---:|---:|---:|---|
| 3-5 | 0.1876 | 0.0012 | 158.1 | 0.1876 | 0.0012 | 151.2 | 524/524 |
| 6-11 | 0.0858 | 0.0011 | 77.7 | 0.0856 | 0.0013 | 68.2 | 1908/1908 |
| 12-24 | 0.0512 | 0.0012 | 41.4 | 0.0516 | 0.0012 | 41.6 | 1804/1804 |
| 25-49 | 0.0317 | 0.0011 | 27.7 | 0.0314 | 0.0012 | 26.8 | 591/1059 |
| 50-99 | 0.0213 | 0.0013 | 16.8 | 0.0199 | 0.0011 | 17.5 | 0/267 |
| 100-199 | 0.0123 | 0.0013 | 9.6 | 0.0122 | 0.0013 | 9.6 | 0/67 |
| 200-399 | 0.0099 | 0.0012 | 8.3 | 0.0090 | 0.0012 | 7.3 | 0/19 |
| 400-799 | 0.0093 | 0.0019 | 4.9 | 0.0079 | 0.0020 | 3.9 | 0/2 |
| 800-1599 | 0.0042 | 0.0010 | 4.3 | 0.0043 | 0.0010 | 4.3 | 0/3 |
| 1600+ | 0.0018 | 0.0012 | 1.5 | 0.0019 | 0.0014 | 1.4 | 0/5 |
| **ALL** | **0.0697** | 0.0012 | **59.5** | **0.0700** | 0.0012 | **57.0** | 4827/5658 |

**The two builds are within 0.0015 of each other in every band**, and the largest gap in lift is at
3-5 (158.1 against 151.2) where the observed values are identical to four decimals and the
difference comes entirely from the null draw.

**Two limitations, stated rather than buried.** The pair sample binds from the 25-49 band upward --
591 of 1,059 themes exact at 25-49 and **none above it** -- so every figure for 50+ themes is a
500-pair estimate. And there is **one** null set per theme, not a distribution, so no CI is offered
on the lift; the band-level null means are stable (0.0010 to 0.0020 throughout) because they average
over many themes, but a per-theme interval would need more draws. No CIs are reported for G and none
should be inferred.

---

## What is and is not known

**Every computed measure the prompt asked for is now in hand. Not one of them separates the two
builds beyond the margins the judgement rule names.** Collected:

| measure | O50s | S2 | S2 - O50s | CI excludes zero |
|---|---|---|---|---|
| C1 non-nested pairs at J >= 0.5 | 0 | 413 | +413 | no CI (a count, entailed by the rules) |
| C2 near-contained nodes | 49.1% | 49.4% | +0.3 pts | no CI (a count) |
| F stability, worse direction | 0.5862 | 0.5817 | **-0.0045** | no CI computed |
| E1 curated recall, 6 cells | - | - | 0.0000 to -0.0526 | **none of 6** |
| E2 curated precision, 12 cells | - | - | +0.0201 to -0.0152 | **1 of 12** (GO 51-200) |
| E3 sibling AUROC, 4 sources | 0.824-0.967 | 0.827-0.967 | -0.0002 to +0.0056 | **none of 4; all CIs overlap** |
| E4 placement at 80% | 92.6% | 93.0% | +0.4 pts | no CI computed |
| E4 Reactome median best J | 0.273 | 0.273 | 0.000 | no CI computed |
| G gene coherence, all bands | 0.0697 | 0.0700 | +0.0003 | no CI (one null draw per theme) |

**The one cell that moves beyond its CI** is GO precision at 51-200, where S2 is 0.0152 lower on
138 themes -- the smallest cell in E2, and the only one of twenty-two tested cells across E1 and E2
whose difference CI excludes zero.

**What is still unknown, and it is the whole question.** Two facts sit side by side and this note
cannot reconcile them: the computed measures find no difference, while **only 55-63% of O50s's
25-199 themes have an S2 counterpart at J >= 0.9**. The builds disagree substantially about the
middle of the ontology and agree on every aggregate. That is consistent with two readings -- that
the disagreement is between equally good descriptions, or that one is better and no computed measure
here is sensitive to it -- and nothing computed can choose between them.

**The readings are the remaining evidence**: R (207 roots), T (294 middle themes drawn from exactly
the disputed bands), I (122 intruder items) and S (174 small roots), all prepared, none judged.

**Nothing is adopted, and no verdict is offered. The judgement rule is the reviewer's to apply.**

## Outputs

| what | where |
|---|---|
| PART 1 interim note | `data/experiments/S2_vs_O50s_2026-10-22/PART1_NOTE.md` |
| counts | `.../part1_counts.json` |
| section C counts | `.../section_c.json` |
| section F | `.../section_f.json`, half sides `side_1-100.npz`, `side_101-200.npz` |
| section E | `.../section_e_recall_ci.json`, `section_e_auroc.json`, `section_e_recall.json` |
| section G | `.../section_g.json` |
| R / T / I / S batches | `.../read_roots/`, `read_themes/`, `intruder/`, `small_inputs/` |
| the key, never re-read | `.../KEY_DO_NOT_SHARE_S2_vs_O50s.json` |

```sh
uv run scripts/s2_vs_o50s_inputs.py     # PART 1
uv run scripts/s2_duplication.py        # PART 2 section C
uv run scripts/s2_stability.py --sides  # F: cache the two half sides
uv run scripts/s2_stability.py          # F
uv run scripts/s2_recall_ci.py          # E1 and E2
uv run scripts/s2_sibling_auroc.py      # E3
uv run scripts/s2_gene_coherence.py     # G
```
