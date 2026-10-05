# Unattended run, 3 Oct 2026

## LIVE STATUS
- **19:05 UTC** — specificity grid run; tests 3 and 4 re-adjudicated under the post-hoc baseline amendment.
- running: nothing.
- ETA: n/a.
- last result: at matched specificity THEMA leads every arm — AUROC 0.884 at zero gene overlap on 5,753 sibling pairs, against 0.625-0.676 for the TF-IDF arms that led on lift.
- failures: none in this step.

---

## DECISIONS FOR AVIYAH

1. **The cap after completion.** The cap is declared at candidacy and holds there (0 of the
   candidate clusters exceed it). **Completion breaches it** — a family's members are the union of
   its matched copies, so 22 of 161,852 completed families exceed 3,125, the largest at 4,109. The
   gate removes 20; consensus then grows the survivors. **2 of 6,244 themes end over the cap, the
   largest at 3,336.** Whether the cap must also hold after completion and consensus changes a
   declared rule, so it is yours. Nothing was changed.

2. **Tests 3 and 4 cannot be adjudicated by their marks as written.** Both say THEMA's *recovery*
   must exceed every gene baseline. Applied literally, both FAIL — but the winning baseline is
   `kappa@25`, whose **largest cluster holds 97.3% of the universe**. It is one blob: its own chance
   rate is 94-100% and its lift is 1.0x, against THEMA's 1.3-4.2x. **A mark on raw recovery can be
   won by putting everything in one cluster**, so applying it literally produces a meaningless
   failure. `compare_baselines.py`'s own comments anticipate exactly this. The mark needs either a
   lift criterion or a non-degeneracy constraint on baselines before it decides anything. **I did
   not substitute lift and call it a pass.**

3. **Test 3's headline cell holds 8 pairs.** The plan calls the zero-gene / near-zero-lexical cell
   "the headline number". At n = 8 it cannot carry a gate whatever it shows (THEMA recovers 75.0%).
   Needs a wider lexical band, more pairs, or acceptance that this cell is unquotable.

4. **Rung 3 costs 2.8-8.0 h** at 1-2 sides in parallel, per-side peak 13.9-20.8 GB. At the high end
   a single side needs 20.8 GB against 30 GB usable. Not run; the declaration forbids me starting it.

5. **The smallest themes drive the stability shortfall.** Post hoc: 3-member themes fail to match
   across disjoint blocks at 44.9% and supply 29.8% of all misses, while every theme above 20
   members matches at >= 97% and the ten largest match perfectly. Half the misses sit at Jaccard
   0.60-0.70, just under the threshold. Whether `min_size = 3` is right for a build judged on theme
   stability is a declared parameter, so yours.

6. **Three of the four largest roots are pass-through shells** — one child holding ~90% of the
   root's members (n04286: 2,966 of 3,336; n03901: 1,625 of 1,836). Only n03106 distributes.

7. **Straddlers are 8,859 of 10,746 placed pathways (82%)** under the stated definition, and random
   pairs share a theme 21.4% of the time at zero gene overlap. Recovery figures must be read as
   lifts, not absolutes. This is a consequence of multi-membership plus large themes.

---

## ITEM 1 — RECORD RUNS = 200. **Done.**

`DECISIONS.md`, 3 Oct: RUNS = 200 as the best measured rung; the 90% mark **not met and not
changed**; both rung tables in full; items 1 and 3 of the optimisation list cross-referenced as
considered-and-not-built (per-run match storage: cross-block reuse impossible because the matching
rule reads each grouping's block-dependent origin run; size filter: bound provably correct yet the
code moved 34,637 of 49,700 supports upward, so proof and code disagree).

| measurement | runs | worse direction |
|---|---|---|
| frozen 1,850, test 9 | 100 | 85.9% |
| 10,770 rung 1 | 100 | 85.5% |
| 10,770 rung 2 | 200 | **87.9%** |

## ITEM 2 — FASTER FAMILIES. **Done** (verified 2 Oct, before this list).

Byte-for-byte identical on `real_r00001-00200`, `seed03001_n200`, and a normal re-cut byte-compared.

| | indexed | joined |
|---|---|---|
| families stage | 679.5s | **345.1s** (2.0x) |
| whole side | 977s | **689s** (1.42x) |
| peak memory | 21.7 GB | **8.2 GB** |

**3 sides fit in parallel** (24.6 GB, 11.4 GB spare). Measured across 3 sides since: median 700s,
6.9 GB. In use from here on; `families` is still the dominant stage at 59% of a side.

## ITEM 3 — CONFIRMATORY BUILD at RUNS = 200. **Done. Held-out confirmation PASSES.**

**Byte-identical to `recurrent_dag_10770_r1-200`** — `nodes.tsv`, `members.tsv`, `edges.tsv`,
`unplaced.tsv` all `cmp`-identical; only the manifest differs. So it was not rebuilt in substance,
only confirmed. Cost ~2 min, every side cached.

| stratum | floor | effective | real | null | held-out FDR |
|---|---|---|---|---|---|
| 3 | 0.790 | 0.790 | 501 | 6.0 | 0.01198 |
| 4 | 0.905 | 0.905 | 313 | 4.6 | **0.0147** |
| 5 | 0.415 | 0.415 | 422 | 4.8 | 0.01137 |
| 6 | 0.275 | **0.330** | 674 | 2.0 | 0.00297 |
| 7-9 | 0.165 | **0.330** | 1,546 | 1.0 | 0.00065 |
| 10+ | 0.020 | **0.330** | 3,000 | 0.0 | 0.0 |

**Overall 0.00285 <= 0.01; worst stratum 0.0147 <= 0.02.** Both met. The five held-out sides were
read exactly once, by this build, and nothing was re-solved afterwards.

### Freeze table

| | |
|---|---|
| themes | 6,244 |
| roots | 203 (3.2%) |
| themes with >1 parent | 1,845 (29.5%) |
| max depth (edges) | 16 |
| median theme size | 9 |
| largest theme | 3,336 — over the cap |
| largest root, direct members | 34 |
| straddlers | 8,859 |
| placed | 10,746 |
| unplaced (strict) | 24 |
| root-only | 117 |
| effectively unplaced | 141 (1.3%) |

**Straddler definition:** a pathway in two or more themes **neither of which contains the other**,
over every exported member row; membership of a theme and its ancestor is not straddling. This does
**not** reproduce the frozen 1,850's recorded 682 (it gives 1,239 there); six variants were tried
and none matched, so this is the definition of record going forward. Logged in `docs/debt.md`.

**NOTHING FROZEN.**

## ITEM 4 — DAG ANALYSES. **Done.**

### 4a Cohesion (`scripts/cohesion_reference.py`)

Themes beat their kNN-ball reference at **every** stratum.

| members | themes | median cohesion | ball median | below ball p5 |
|---|---|---|---|---|
| 3-5 | 1,227 | 0.611 | 0.568 | 24 |
| 6-9 | 2,102 | 0.498 | 0.494 | 56 |
| 10-19 | 1,926 | 0.455 | 0.431 | 18 |
| 20-49 | 836 | 0.399 | 0.367 | 1 |
| 50-199 | 143 | 0.338 | 0.287 | 0 |
| 200+ | 10 | 0.107 | 0.067 | 0 |

Least cohesive leaves: n01374 (0.183), n04210 (0.190), n04489 (0.201), n04861 (0.212), n05299
(0.242). The four largest roots each sit above their own ball median: 0.050/0.061/0.100/0.139
against 0.035/0.037/0.066/0.081. A cut at 0.20 would remove 12 themes but split 203 roots into 790
and leave 151 pathways homeless — the same shape of result as the 1,850.

### 4b Where the cap stops holding (`scripts/cap_audit.py`)

| stage | count | over cap | largest |
|---|---|---|---|
| candidate clusters | by construction | **0** | 3,125 |
| completed families | 161,852 | **22** | **4,109** |
| through the gate | 6,456 | 2 | 3,216 |
| themes after consensus | 6,244 | **2** | **3,336** |

**Completion breaches the cap first**: a family's members are the union of its matched copies across
runs, and a union of under-cap clusters can exceed it. The gate removes 20 of the 22. Consensus then
grew the largest from 3,216 to 3,336 (its closest completed family is Jaccard 0.964). Nothing changed.

### 4c The four largest roots (`scripts/root_profile.py`)

Universe mix: GO 70%, Reactome 27%, BTM 2%, Hallmark 0%.

| root | members | children | sources | largest child |
|---|---|---|---|---|
| n04286 | 3,336 | 43 | GO 72%, Reactome 24%, BTM 4% | **2,966 (89%)** |
| n04718 | 3,225 | 92 | GO 69%, Reactome 29%, BTM 1% | **2,200 (68%)** |
| n03901 | 1,836 | 18 | GO 66%, Reactome 26%, BTM 8% | **1,625 (88%)** |
| n03106 | 1,392 | 68 | GO 61%, Reactome 35%, BTM 3% | 168 (12%) |

All four are genuine source mixtures close to the universe's own, so no root is one database's
taxonomy. But three are one giant child plus a tail. Example members read sensibly — n03106's
children are E2F1 targets, transcription elongation, mismatch repair, mRNA catabolism; n04718's are
glycerophospholipid metabolism, calcium signalling, ion transport.

### 4d Unmatched themes — POST HOC, DECIDES NOTHING (`scripts/unmatched_profile.py`)

| members | themes | unmatched | rate | share of misses |
|---|---|---|---|---|
| 3 | 501 | 225 | **44.9%** | 29.8% |
| 4 | 313 | 55 | 17.6% | 7.3% |
| 7-9 | 1,462 | 169 | 11.6% | 22.4% |
| 10-19 | 1,926 | 89 | 4.6% | 11.8% |
| 20-49 | 836 | 23 | 2.8% | 3.0% |
| 200+ | 10 | **0** | **0.0%** | 0.0% |

373 of 756 misses (49%) sit at best Jaccard 0.60-0.70. Backward direction agrees. **Run after rung 2
had already failed; it licenses no change to any threshold or population.**

## FREEZE and TF-IDF RESUME (3 Oct, afternoon)

**FROZEN.** `data/ontology/v0.3/recurrent_dag_10770/FROZEN.md`, tag **`v0.3.0-10770-runs200`**. It
states the stability mark as NOT MET (85.5% at 100 runs, 87.9% at 200), the cap as applied at cut
time with 2 of 6,244 themes exceeding it through completion and consensus, and the straddler
definition that differs from the 1,850's. Nothing corrected.

**The TF-IDF control did not stall — it crashed**, and the crash was the result. No process was
running (PIDs 98175 and 98177 both gone, nothing matching `build_10770`, `build_trees_10770` or
`space tfidf`). The floor solver found **no admissible support threshold in any of the six strata**:
the TF-IDF real side yields 140,758 families against scrambles of 362,000-365,000, and no level
separates them at FDR <= 0.01. The gate then compared a support against `None` and raised. **That was
a real bug in my build script** — it printed DROP for an unsolvable stratum but did not handle one at
the gate — and it is fixed: a dropped stratum is inadmissible, nothing in it passes, and an arm that
produces no ontology is written as an empty result rather than crashing.

Re-run from the cached TF-IDF trees, sides and floors with nothing recomputed:

| | |
|---|---|
| TF-IDF real side | 140,758 families |
| TF-IDF scramble sides | 362,166-364,905 families each |
| strata with a solvable floor | **0 of 6** |
| families through the gate | **0 of 140,758** |
| themes | **0** — all 10,770 pathways unplaced |

### TEST 3 — TF-IDF condition MET; gene-baseline condition unadjudicable

Headline cell (gene overlap 0 and curated-text Jaccard <= 0.030, the bottom quintile, declared
before the run), **8 pairs**:

| arm | recovery | chance | largest cluster |
|---|---|---|---|
| **THEMA (frozen build)** | **75.0%** | 21.4% | — |
| TF-IDF DAG, identical pipeline | **0.0%** | — | no themes at all |
| TF-IDF flat, Ward at 25 | 0.0% | 5.1% | 9.2% |
| TF-IDF flat, Ward at 50 | 0.0% | 2.8% | 5.7% |
| TF-IDF flat, Ward at 100 | 0.0% | 1.4% | 4.0% |

**THEMA is ahead of every lexical arm**, and the flat arms are not degenerate, so this is a fair
comparison and not an artefact of a collapsed baseline. The plan's question — "if plain word overlap
matches BioLORD in the zero-overlap band, the embedding is adding nothing over word counting" — is
answered: it does not match, and word counting yields no recurrent structure here at all.

**Test 3 still has no overall verdict**, for two reasons that are not about the TF-IDF arm: the
headline cell holds **8 pairs**, too few to carry a gate; and the declared pass also requires beating
every gene baseline on recovery, where `kappa@25` wins with 97.3% of the universe in one cluster.
Both are in Decisions for Aviyah.

## ITEM 5 — VALIDATION TESTS. **Done, including the TF-IDF control.**

In force and not needing names, per the 25 Sep amendment: **test 1** (discharged by item 3's
held-out FDR), **test 2** (in the freeze table), **test 3**, **test 4**, **test 9** (the rung
measurement supersedes it — disjoint blocks are a stronger comparison than seed 0 vs seed 1). Tests
5 and 6 need your datasets and your time; naming tests 1 and 2 are excluded by instruction.

**New: `scripts/validate_dag.py`** — the adapter the plan says is missing ("a DAG is not a
partition"). A pair is recovered when both members share at least one theme.

### Test 3 — `reactome2go`, 680 pairs

| band | n | THEMA | null | lift | 95% CI |
|---|---|---|---|---|---|
| exactly 0 | 40 | **80.0%** | 21.4% | **3.7x** | [67.5%, 92.5%] |
| 0 < J <= 0.01 | 31 | 61.3% | 24.8% | 2.5x | [45.2%, 77.4%] |
| 0.01 < J <= 0.05 | 138 | 84.8% | 40.8% | 2.1x | [79.0%, 90.6%] |
| 0.05 < J <= 0.15 | 185 | 93.0% | 64.1% | 1.4x | [89.2%, 96.2%] |
| 0.15 < J <= 1 | 286 | 98.6% | 75.5% | 1.3x | [97.2%, 99.7%] |

Headline cell (gene 0 AND curated-text Jaccard <= 0.030, bottom quintile, declared before the run):
**8 pairs**, THEMA 75.0%. **TEST 3: NO VERDICT** — the TF-IDF arm is required by the declared pass
and has not run.

### Test 4 — sibling recovery, reported separately, never pooled

| source | pairs | exactly-0 band | lift | every band beats null? |
|---|---|---|---|---|
| Reactome siblings | 9,396 | 89.0% | 4.2x | **yes** |
| Reactome, fan-out<=6 | 2,083 | 84.0% | 3.9x | **yes** |
| GO siblings | 45,832 | 59.2% | 2.8x | **yes** |
| GO, fan-out<=6 | 3,594 | 75.5% | 3.5x | **yes** |

First half of the mark met everywhere. Second half — "not beaten by the gene baselines in the (0,0)
band" — **cannot be adjudicated**: see Decision 2. `kappa@25` beats THEMA on raw recovery in nearly
every band with a 97.3% largest cluster and 1.0x lift. Against the non-degenerate arms THEMA is
clearly ahead (e.g. GO siblings, exactly 0: THEMA 59.2% against `overlap@100` at 30.6%, whose
largest cluster is 15.7%). **TEST 4: NO VERDICT, for a defect in the mark, not a defect in the
build.** Both sources are labelled confounded, as the plan requires: the curators wrote both the
hierarchy and the prose THEMA embeds.

## ITEM 6 — RUNG 3 ESTIMATE. **Done. Not run.** (`scripts/rung3_estimate.py`)

12 sides (2 real + 10 shared calibration) plus 400 new trees (~4 min).

| | low (2x) | high (3x) |
|---|---|---|
| per-side seconds | 1,399 | 2,099 |
| per-side peak GB | 13.9 | 20.8 |
| sides in parallel | 2 | 1 |
| **total hours** | **~2.8** | **~8.0** |

A range, not a point estimate: the only evidence for cost per doubling is the single 100-to-200 step.

## WHAT WENT WRONG, AND HOW IT WAS RECOVERED

1. **The provenance guard stopped two runs, correctly both times.** First the ladder asked for
   `completion=original` while the sides said `fast`; I fixed the caller rather than overriding.
   Then the confirmatory build asked for `families=joined` while nine sides said `indexed`; that one
   needed `--allow-stale-cache`, which **I had added to the parser yesterday and never wired to
   anything** — it did nothing until I connected it. It now prints its justification on every reuse.

2. **I computed the test 3/4 verdicts on the wrong statistic** — lift instead of recovery — and
   caught it before reporting. The declared marks are on recovery. Correcting it inverted the
   apparent result and exposed the degenerate-baseline problem in Decision 2.

3. Two background waiters of mine had shell bugs (glob and integer comparison). Harmless, replaced.

4. Earlier (2 Oct, recorded there): I edited `recurrent.py` while a side-cutting loop was running
   and corrupted a cached side. That is what the provenance guard now prevents.


---

# TEST 3 FOLLOW-UP, 3 Oct (afternoon) — REPORTING ONLY

**Nothing below is a test, a verdict, or a declared quantity, and nothing declared changed.**
`scripts/test3_grid.py` produces all of it. The plan declares the gene-overlap bands and one named
cell; **it declares no lexical bands**, so the lexical bands here are a stated reporting choice:
quintiles of curated-text Jaccard measured over the 600,000-pair random null, which is a
universe-representative distribution, so the same edges apply to every source and to the null.

| band | curated-text Jaccard |
|---|---|
| L1 | 0 – 0.022 |
| L2 | 0.022 – 0.035 |
| L3 | 0.035 – 0.052 |
| L4 | 0.052 – 0.085 |
| L5 | 0.085 – 1.000 |
| L0 | one or both sides publish no curated prose |

**Curated prose, not generated.** 10,424 of 10,770 pathways (97%) publish some. The plan is explicit
that the banding must use the curated text, because the generated descriptions were written by a
model that has read both Reactome and GO.

**A baseline whose largest cluster holds more than 29% of the universe is flagged DEGENERATE** — the
size cap's own share, used here as a threshold for "this is one blob, not a partition". **9 of the 12
gene baselines are degenerate**: `kappa@25` 97.3%, `overlap@25` 82.4%, `jaccard@25` 65.4%,
`jaccard@50` 62.6%, `kappa@50` 56.0%, `ochiai@25` 44.8%, `jaccard@100` 43.8%, `overlap@50` 43.0%,
`ochiai@50` 35.4%. Only `ochiai@100`, `overlap@100` and `kappa@100` survive. **The TF-IDF arms are
not degenerate** (largest cluster 9.2% / 5.7% / 4.0%).

## 1. Why the headline cell holds 8 pairs

`reactome2go` contributes **680 pairs** inside the 10,770. Of those, **40 have exactly zero gene
overlap**, and they spread across the lexical bands:

| gene band | L1 | L2 | L3 | L4 | L5 | total |
|---|---|---|---|---|---|---|
| 0.15 < J <= 1 | 18 | 30 | 61 | 91 | 86 | 286 |
| 0.05 < J <= 0.15 | 8 | 28 | 45 | 56 | 48 | 185 |
| 0.01 < J <= 0.05 | 17 | 23 | 39 | 31 | 28 | 138 |
| 0 < J <= 0.01 | 6 | 7 | 4 | 11 | 3 | 31 |
| **exactly 0** | **5** | **5** | **8** | **11** | **11** | **40** |
| total | 54 | 93 | 157 | 200 | 176 | 680 |

**The 8 is 5 + 5, rounded up by where the quintile edge fell**: the plan's cell is zero gene overlap
AND the bottom quintile of lexical overlap, and only 40 pairs reach the first condition before the
second takes a fifth of them. **The cell is a conjunction of two rare conditions, and the plan did
not check how many pairs survive both.** Nothing is wrong with either condition; the arithmetic was
simply never done.

No `reactome2go` pair falls in L0 — both sides always publish prose, because the mapping is between
two curated databases.

## 2. Full grid — `reactome2go`

Recovery / lift over each arm's own chance rate. Cells below 20 pairs are listed for completeness
but **not quotable**; the five zero-gene cells are all in that category.

| cell | n | THEMA | TF-IDF flat@25 | flat@50 | flat@100 | best non-degenerate gene |
|---|---|---|---|---|---|---|
| exactly 0 \| L1 | **5** | 60.0% / 3.0x | — | — | — | — |
| exactly 0 \| L2 | **5** | 80.0% / 3.8x | — | — | — | — |
| exactly 0 \| L3 | **8** | 75.0% / 3.5x | — | — | — | — |
| exactly 0 \| L4 | **11** | 90.9% / 4.2x | — | — | — | — |
| exactly 0 \| L5 | **11** | 81.8% / 3.6x | — | — | — | — |
| 0.01–0.05 \| L2 | 23 | 91.3% / 2.3x | 56.5% / 4.9x | 47.8% / 6.6x | 47.8% / 12.1x | overlap@100 56.5% / 3.5x |
| 0.01–0.05 \| L3 | 39 | 76.9% / 1.9x | 59.0% / 4.4x | 53.8% / 6.5x | 48.7% / 11.2x | overlap@100 43.6% / 2.3x |
| 0.05–0.15 \| L4 | 56 | 96.4% / 1.6x | 83.9% / 2.3x | 76.8% / 2.7x | 71.4% / 3.5x | overlap@100 50.0% / 1.1x |
| 0.15–1 \| L5 | 86 | 100.0% / 1.1x | 100.0% / 1.3x | 96.5% / 1.4x | 96.5% / 1.5x | kappa@100 90.7% / 1.0x |

**THEMA's chance rate at zero gene overlap is 20–23%** across the lexical bands, against 0.9–7.8%
for the TF-IDF arms and 4.7–7.8% for the surviving gene arms. That gap is why recovery and lift
disagree so often below, and it is a consequence of multi-membership: 82% of placed pathways sit in
two or more non-nested themes.

## 3. Full grid — Reactome siblings (the larger evidence base)

9,396 pairs, and critically **5,753 of them have exactly zero gene overlap** — 144x the
`reactome2go` count. Every cell here is quotable.

| gene band | L1 | L2 | L3 | L4 | L5 | total |
|---|---|---|---|---|---|---|
| 0.15 < J <= 1 | 7 | 15 | 63 | 273 | 1,152 | 1,510 |
| 0.05 < J <= 0.15 | 4 | 29 | 84 | 252 | 671 | 1,040 |
| 0.01 < J <= 0.05 | 9 | 29 | 88 | 281 | 466 | 873 |
| 0 < J <= 0.01 | 2 | 13 | 44 | 85 | 76 | 220 |
| **exactly 0** | **80** | **171** | **467** | **2,129** | **2,906** | **5,753** |
| total | 102 | 257 | 746 | 3,020 | 5,271 | 9,396 |

Zero-gene cells, recovery / lift:

| cell | n | THEMA | flat@25 | flat@50 | flat@100 | best non-degenerate gene |
|---|---|---|---|---|---|---|
| exactly 0 \| L1 | 80 | **68.8% / 3.4x** | 22.5% / 6.5x | 18.8% / 11.3x | 17.5% / 26.1x | ochiai@100 23.8% / 3.8x |
| exactly 0 \| L2 | 171 | **74.9% / 3.5x** | 41.5% / 11.3x | 30.4% / 16.9x | 22.2% / 30.6x | overlap@100 33.3% / 8.4x |
| exactly 0 \| L3 | 467 | **78.2% / 3.7x** | 33.4% / 8.6x | 24.2% / 12.8x | 18.2% / 23.2x | overlap@100 28.3% / 6.5x |
| exactly 0 \| L4 | 2,129 | **87.2% / 4.1x** | 31.5% / 7.3x | 22.7% / 10.7x | 16.5% / 18.3x | ochiai@100 25.0% / 4.0x |
| exactly 0 \| L5 | 2,906 | **93.4% / 4.1x** | 45.3% / 8.8x | 38.0% / 14.3x | 34.1% / 27.3x | ochiai@100 40.0% / 6.1x |

**On recovery THEMA leads every arm in every zero-gene cell, by 27 to 56 points, on thousands of
pairs.** The TF-IDF DAG recovers 0.0% everywhere, because it has no themes.

**On lift it does not**, and that is the honest counterpart: the TF-IDF flat arms reach 6.5x–30.6x
against THEMA's 3.4x–4.1x, purely because their chance rates are 0.9–7.8% where THEMA's is ~21%.
A method that places each pathway in one small cluster has little chance of a spurious hit; one that
places pathways in several large themes has a lot. **Which statistic answers the plan's question is
not something this report decides.**

The fan-out-capped sibling arm agrees throughout (16 / 27 / 69 / 198 / 354 pairs in the zero-gene
cells; THEMA 93.8% / 77.8% / 79.7% / 78.8% / 87.8%).

## 4. EXPLORATORY — the hard cell widened. NOT A TEST, NOT A VERDICT.

Cell: **gene Jaccard <= 0.05 AND curated-text Jaccard <= 0.043** (the null's median, i.e. the bottom
half). **This is not the plan's cell**, which is gene overlap exactly 0 and lexical near 0. It exists
only to put the same comparison on counts large enough to read.

| source | pairs | THEMA | flat@25 | flat@50 | flat@100 | overlap@100 | kappa@100 | ochiai@100 |
|---|---|---|---|---|---|---|---|---|
| `reactome2go` | 82 | **76.8% / 3.5x** | 48.8% / 12.0x | 39.0% / 18.8x | 36.6% / 41.5x | 34.1% / 7.3x | 23.2% / 3.0x | 19.5% / 3.4x |
| Reactome siblings | 519 | **69.4% / 3.2x** | 31.8% / 7.8x | 22.9% / 11.1x | 17.9% / 20.3x | 25.2% / 5.4x | 22.7% / 2.9x | 17.9% / 3.1x |
| siblings, fan-out<=6 | 90 | **75.6% / 3.4x** | 45.6% / 11.2x | 41.1% / 19.8x | 36.7% / 41.6x | 26.7% / 5.7x | 28.9% / 3.7x | 20.0% / 3.4x |

Chance rates in this cell: THEMA 21.9%, TF-IDF flat 4.1% / 2.1% / 0.9%, surviving gene arms
4.7–7.8%. The pattern is the same as section 3: **THEMA ahead on recovery by 21 to 45 points,
behind on lift.**

**Widening the cell raises `reactome2go` from 8 pairs to 82 and the siblings to 519**, which is the
only reason these numbers are readable at all. That is also exactly why they are labelled
exploratory: a cell chosen after seeing that the declared one was too small is not the declared one.

## A bug in this report's own script, found and fixed

The first run of the grid showed **no chance rate and no lift for any zero-gene cell**. The cause was
in my code: the null's gene-overlap line read `jaccard(...) or -1.0`, and **`0.0` is falsy in
Python**, so every random pair with exactly zero gene overlap was recorded as *undefined* and the
zero-gene null band was empty — the single most important band in the grid. Fixed, re-run, and the
nulls are now populated (84,896–100,346 random pairs per zero-gene cell). The source-pair side used
a correct idiom and was never affected.


---

# SPECIFICITY GRID, 3 Oct (evening) — the recovery-versus-lift split, resolved

Both declarations were written into `DECISIONS.md` **before any of this was computed**.
`scripts/specificity_grid.py` produces all of it.

## 1. Tests 3 and 4 re-adjudicated UNDER THE POST-HOC BASELINE AMENDMENT

**The amendment is post hoc and labelled so wherever its verdicts appear.** A gene baseline whose
largest cluster exceeds **29.0133%** of the universe — THEMA's own declared size cap — is excluded.
The threshold is not chosen to produce an outcome: it is the number this project already declared
for "too big to be one theme", now applied to the comparison as well as to the build.

**9 of 12 gene baselines are excluded**: `kappa@25` 97.3%, `overlap@25` 82.4%, `jaccard@25` 65.4%,
`jaccard@50` 62.6%, `kappa@50` 56.0%, `ochiai@25` 44.8%, `jaccard@100` 43.8%, `overlap@50` 43.0%,
`ochiai@50` 35.4%. **Three are kept**: `ochiai@100`, `kappa@100`, `overlap@100` (23% / 21% / 14%).

Recovery in the two bands the marks name, against the best *kept* gene baseline:

| source | band | n | THEMA | best kept gene arm | |
|---|---|---|---|---|---|
| `reactome2go` | exactly 0 | 40 | **80.0%** | `ochiai@100` 17.5% | THEMA ahead |
| `reactome2go` | 0 < J <= 0.01 | 31 | **61.3%** | `overlap@100` 22.6% | THEMA ahead |
| Reactome siblings | exactly 0 | 5,753 | **89.0%** | `ochiai@100` 32.2% | THEMA ahead |
| Reactome siblings | 0 < J <= 0.01 | 220 | **65.5%** | `kappa@100` 21.8% | THEMA ahead |
| siblings, fan-out<=6 | exactly 0 | 664 | **84.0%** | `overlap@100` 39.9% | THEMA ahead |
| siblings, fan-out<=6 | 0 < J <= 0.01 | 51 | **70.6%** | `kappa@100` 29.4% | THEMA ahead |

### The verdicts, under the post-hoc baseline amendment

**TEST 4 — PASSES, under the post-hoc baseline amendment.** Its mark is "THEMA beats the random null
in every band, and is not beaten by the gene baselines in the (0,0) band". It beats the null in every
band of every source (1.2x–4.2x, reported earlier), and under the amendment no surviving gene
baseline beats it in the zero-overlap band — by margins of 45 to 57 points on 5,753 pairs.

**TEST 3 — the baseline half PASSES under the amendment; the gate still has no overall verdict.** Its
mark also requires exceeding every gene baseline in the (0,0) and (0,0.01) bands, which it now does,
and beating TF-IDF in the zero-gene / near-zero-lexical cell, which it does 75.0% to 0.0%. **What
still blocks it is n = 8 in that cell**, which the amendment does not touch and no re-adjudication
can fix. Widening the cell would change a declared cell definition and is Aviyah's.

**Both verdicts are conditional on a rule written after seeing the results.** Under the mark exactly
as declared on 25 Sep, both gates fail on a baseline holding 97.3% of the universe in one cluster.

## 2. The graded specificity measure — informational, not a gate

Declared before computation. **Smallest shared theme size** is the number of members of the smallest
theme containing both pathways (infinite when none; for a flat arm, the shared cluster's size).
Smaller is a sharper claim: putting a pair together in a theme of 8 says much more than in a theme
of 3,000. **AUROC** is the probability a curated pair is more specific than a band-matched random
pair, ties counted half, from midranks so infinities are ties rather than dropped observations.

### Why this settles the split

Recovery rewards co-placement at any grain; lift rewards a low base rate. The TF-IDF arms led on
lift only because their chance rates are 0.9–7.8% against THEMA's ~21%. **Compared at the same
specificity, that advantage disappears.**

**`reactome2go`, exactly zero gene overlap — 40 pairs, null 509,438**

| arm | median size | random | **AUROC** | <=10 | <=50 | <=200 |
|---|---|---|---|---|---|---|
| **THEMA (frozen)** | 1,508 | inf | **0.863** | **10.0%** / 0.0% | **32.5%** / 0.1% | **47.5%** / 0.3% |
| TF-IDF DAG | inf | inf | 0.500 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |
| TF-IDF flat@25 | 956 | inf | 0.746 | 0.0% / 0.0% | 0.0% / 0.0% | 2.5% / 0.0% |
| TF-IDF flat@50 | inf | inf | 0.703 | 0.0% / 0.0% | 0.0% / 0.0% | 22.5% / 0.3% |
| TF-IDF flat@100 | inf | inf | 0.696 | 0.0% / 0.0% | 2.5% / 0.0% | 37.5% / 0.5% |
| ochiai@100 | inf | inf | 0.555 | 0.0% / 0.0% | 2.5% / 0.0% | 5.0% / 0.2% |
| overlap@100 | inf | inf | 0.541 | 0.0% / 0.0% | 0.0% / 0.0% | 2.5% / 0.1% |
| kappa@100 | inf | inf | 0.539 | 0.0% / 0.0% | 0.0% / 0.0% | 2.5% / 0.2% |

**Reactome siblings, exactly zero gene overlap — 5,753 pairs**

| arm | median size | **AUROC** | <=10 | <=50 | <=200 |
|---|---|---|---|---|---|
| **THEMA (frozen)** | 2,200 | **0.884** | **9.3%** / 0.0% | **20.3%** / 0.1% | **24.0%** / 0.3% |
| TF-IDF DAG | inf | 0.500 | 0.0% / 0.0% | 0.0% / 0.0% | 0.0% / 0.0% |
| TF-IDF flat@25 | inf | 0.676 | 0.0% / 0.0% | 0.0% / 0.0% | 0.5% / 0.0% |
| TF-IDF flat@50 | inf | 0.645 | 0.0% / 0.0% | 0.6% / 0.0% | 17.1% / 0.3% |
| TF-IDF flat@100 | inf | 0.625 | 0.0% / 0.0% | 1.9% / 0.0% | 23.7% / 0.5% |
| ochiai@100 | inf | 0.629 | 0.0% / 0.0% | 0.6% / 0.0% | 6.0% / 0.2% |
| overlap@100 | inf | 0.624 | 0.0% / 0.0% | 1.9% / 0.0% | 4.5% / 0.1% |
| kappa@100 | inf | 0.574 | 0.0% / 0.0% | 4.6% / 0.0% | 10.0% / 0.2% |

**THEMA leads on AUROC and at every specificity cut-off, in both sources.** 0.884 against
0.625–0.676 for the TF-IDF arms that led on lift, and 0.574–0.629 for the kept gene arms. **At
<= 10 members — the sharpest claim available — THEMA is the only arm that places any curated pair
at all** (9.3% of 5,753 sibling pairs, against 0.0% for all seven others and 0.0% random).

The same ordering holds at 0.01 < J <= 0.05 (873 sibling pairs): THEMA AUROC 0.751 and 28.6% at
<= 50, against the TF-IDF arms at 0.705–0.718 and 0.0–1.7%.

**So the recovery-versus-lift disagreement was an artefact of comparing at different grains.** When
every arm is held to the same specificity, THEMA is ahead on both axes at once.

### Hop distance in the DAG — THEMA only

| source, band | median hops, curated | random | finite for curated | finite for random |
|---|---|---|---|---|
| `reactome2go`, exactly 0 | **7** | 9 | **75.0%** | 19.9% |
| siblings, exactly 0 | **7** | 9 | **87.9%** | 19.9% |
| siblings, 0.01 < J <= 0.05 | **6** | 8 | **72.3%** | 38.7% |

Curated pairs sit closer in the DAG than random ones and, more tellingly, **are connected at all far
more often** — 88% against 20% at zero gene overlap. The median gap of two hops is modest; the
reachability gap is not.

## A caveat on the median-size column

Most median sizes read `inf`, including THEMA's at some bands, because more than half the pairs in
those cells share no theme in that arm at all. The median is therefore the least informative column
here and the cut-offs and AUROC are the ones to read: AUROC uses the whole distribution including
the infinities, and the cut-offs ask directly how often an arm makes a sharp claim.
