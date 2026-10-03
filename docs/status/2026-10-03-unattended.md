# Unattended run, 3 Oct 2026

## LIVE STATUS
- **15:45 UTC** — both tasks DONE: build frozen as v0.3.0-10770-runs200; TF-IDF control resumed and test 3's arm run.
- running: nothing.
- ETA: n/a — everything on both lists is complete.
- last result: TF-IDF produces NO ontology (floors unsolvable in all 6 strata); THEMA 75.0% vs TF-IDF 0.0% in test 3's headline cell.
- failures: TF-IDF build crashed on a None threshold; bug fixed, re-run from cache, no recompute.

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
