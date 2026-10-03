# FROZEN — `v0.3.0-10770-runs200`, RUNS = 200, inclusion 0.50, CENTRED clustering space

**The full universe.** 10,770 pathways — every one with at least one gene and a description. This
supersedes the 1,850-pathway subset build (`v0.2.2-subset-1850-c50`) as the official THEMA ontology.
That build stays as history and as the method-development record; its names do not transfer, because
membership differs at every level.

| | |
|---|---|
| frozen | 2026-10-03 |
| built from commit | `80743f04a0c5a4ea686e361370ab1873f5f1ea6a` |
| build script | `scripts/build_10770.py --runs 200 --scramble-rows 200 --completion fast --families joined --confirm-heldout` |
| clustering space | centred-and-renormalised MedCPT vectors |
| inclusion cutoff | **0.50** |
| size cap | **29.0133% of the universe = 3,125 pathways**, applied at cut time |
| floors | 0.790 / 0.905 / 0.415 at sizes 3/4/5; the declared m = 0.33 governs 6 and above |
| floors calibrated | **10 calibration + 5 held-out scrambles**, 200 trees each, seeds 3001-3010 and 4001-4005 |
| held-out FDR | **0.00285 overall; worst stratum 0.0147** |
| runs / theta / declared m | **200** / 0.70 / 0.33 |
| descriptions digest | `7fa24853293f536f` |
| universe digest | `c54319cdfbbe9eb7` |

**The trees are persisted, so this build is a re-cut rather than a rebuild.** 400 real Ward trees and
15 scramble sides of 200 live under `data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/`, written
once without a size cap. Changing the cap, the cutoff or the floors re-cuts them; it does not rebuild
them.

## THE DECLARED STABILITY MARK IS NOT MET

**This is the first thing a reader of this build should know.**

> The declared mark is **>= 90% of final themes matched at Jaccard >= 0.70, in the worse direction,
> between two builds from disjoint blocks of trees.** This build reaches **87.9%**.

| rung | runs | worse direction | |
|---|---|---|---|
| trees 1-100 vs 101-200 | 100 | **85.5%** | FAIL |
| trees 1-200 vs 201-400 | 200 | **87.9%** | FAIL |

**The mark was not lowered to accommodate the result, and the result was not re-measured until it
passed.** No declared rung passes, so the ladder stopped: no third rung, no new trees, no change to
the mark. RUNS = 200 is adopted as the **best measured** setting, not as a passing one.

**What the ladder did establish.** The run count genuinely drives theme stability — doubling it
gained 2.4 points. Three independent measurements now sit below the mark and close together:

| measurement | runs | worse direction |
|---|---|---|
| frozen 1,850, test 9 (seed 0 vs seed 1) | 100 | 85.9% |
| 10,770, rung 1 | 100 | 85.5% |
| 10,770, rung 2 — **this build** | 200 | **87.9%** |

The two 100-run figures agree to 0.4 points across universes six times apart in size, so the
shortfall reads as a property of the method at this run count rather than of either dataset.
Extrapolating 2.4 points per doubling puts 400 runs near 89-90% — **a line through two points, and
rung 3 was not run.**

**Any public description of this ontology must carry the figure**: its theme set reproduces at 87.9%
against an independent rebuild from disjoint trees, below the 90% mark this project declares for a
build it would call stable.

## THE SIZE CAP IS EXCEEDED BY TWO THEMES — STATED, NOT CORRECTED

The cap is declared **at cut time**, on the clusters a Ward tree offers as candidates, and it holds
exactly there: **0 candidate clusters exceed 3,125**, the largest being exactly 3,125. Downstream it
is breached, and the audit says precisely where:

| stage | count | over cap | largest |
|---|---|---|---|
| candidate clusters, cut under the cap | by construction | **0** | 3,125 |
| completed families, before the gate | 161,852 | **22** | **4,109** |
| families through the support gate | 6,456 | 2 | 3,216 |
| **themes, after consensus and Hasse** | **6,244** | **2** | **3,336** |

**Completion breaches it first.** A family's members are the union of its matched copies across runs,
not any single cluster, so a union of under-cap clusters can exceed the cap. The support gate then
removes 20 of the 22. Consensus grew the largest survivor from 3,216 to 3,336 by inheritance — its
closest completed family sits at Jaccard 0.964.

**Nothing was corrected.** The cap constrains candidacy, which is where it is declared to apply.
Whether it must also hold after completion and consensus would change a declared rule, and that
decision is open. `scripts/cap_audit.py` reproduces this table.

## Shape

| | 1,850 (`v0.2.2`) | **this build (10,770)** |
|---|---|---|
| themes | 800 | **6,244** |
| roots | 61 (7.6%) | **203 (3.2%)** |
| themes with >1 parent | 176 (22.0%) | **1,845 (29.5%)** |
| max depth (edges) | 12 | **16** |
| median theme size | 8 | **9** |
| largest theme | 819 | **3,336** |
| largest root, direct members | 64 | **34** |
| edges | 939 | **8,208** |
| straddlers | see note | **8,859** |

**Straddler definition, which differs from the 1,850's recorded figure:** a pathway in **two or more
themes neither of which contains the other**, over every exported member row; membership of a theme
and of its ancestor is not straddling. This definition gives **1,239** on the frozen 1,850, where
`FROZEN.md` there records 682. Six variants were tried and none reproduces 682, and the original
computation was ad hoc with no committed script. **This is the definition of record going forward**
(`scripts/freeze_table.py`); the discrepancy is logged in `docs/debt.md`.

Straddlers are **82% of placed pathways**, and random pairs share a theme 21.4% of the time at zero
gene overlap. Any co-membership statistic on this build must be read as a lift over that chance rate,
never as an absolute.

## Placement — reported three ways, because one number hides the cost

| | 1,850 (`v0.2.2`) | **this build** |
|---|---|---|
| pathways placed | 1,831 | **10,746** |
| **unplaced (strict)** | 19 | **24** |
| **root-only** — in no theme that has a parent | 106 | **117** |
| **effectively unplaced** — the sum | 125 (6.8%) | **141 (1.3%)** |

A root-only pathway has been placed by the letter of the algorithm and told a reader almost nothing:
a top-level bucket and no theme within it. **The full universe places far better than the subset did**
— 1.3% effectively unplaced against 6.8% — which is the clearest benefit of building at full scale.

## Held-out FDR per stratum — confirmed ONCE

| stratum | floor | effective | real | null | held-out FDR |
|---|---|---|---|---|---|
| 3 | 0.790 | 0.790 | 501 | 6.0 | 0.01198 |
| 4 | 0.905 | 0.905 | 313 | 4.6 | **0.0147** |
| 5 | 0.415 | 0.415 | 422 | 4.8 | 0.01137 |
| 6 | 0.275 | **0.330** | 674 | 2.0 | 0.00297 |
| 7-9 | 0.165 | **0.330** | 1,546 | 1.0 | 0.00065 |
| 10+ | 0.020 | **0.330** | 3,000 | 0.0 | 0.0 |

**Overall 0.00285 against the declared <= 0.01; worst stratum 0.0147 against <= 0.02.** Both met. The
five held-out scramble sides were read **exactly once**, by this build, and **nothing was re-solved
afterwards** — a floor adjusted against the held-out set is not a held-out set. The declared m = 0.33
governs every stratum at 6 members and above, where the solved floor falls below it.

## Cohesion

Themes are tighter than kNN balls of the same size **at every stratum**, including all four largest
roots. Cohesion falls with size, from a median 0.611 at 3-5 members to 0.107 at 200+; each of the
four largest roots sits above its own ball median (0.050/0.061/0.100/0.139 against
0.035/0.037/0.066/0.081). **No cohesion threshold is applied**: a cut at 0.20 would remove 12 themes
but split 203 roots into 790 and leave 151 pathways with no home at all.
`scripts/cohesion_reference.py` reproduces this.

## Test 2 — shape against curated ontologies

Informational, never a gate.

| | ours | Reactome | GO BP |
|---|---|---|---|
| roots | 3.2% | 1.0% | 0.0% |
| max depth (edges) | 16 | 11 | 16 |
| multi-parent | 29.5% | 1.2% | 50.8% |

**No inside-the-range verdict is claimed.** The 1,850's `FROZEN.md` records GO BP at 20% roots and
31% multi-parent; neither is reproducible from `go-basic.obo` (computed: 0.0% and 50.8%), and whether
our 3.2% roots sits inside the curated range turns entirely on which GO figure is used. The figures
are reported and the verdict withheld. Logged in `docs/debt.md`.

## Validation — continues on this frozen build

| test | kind | state |
|---|---|---|
| **1** scramble error rate | gate | **discharged** by the held-out FDR above |
| **2** shape vs GO / Reactome | informational | reported above, verdict withheld |
| **3** `reactome2go` recovery | gate, headline | **TF-IDF condition MET; gene-baseline condition unadjudicable** |
| **4** sibling recovery | gate | **numbers in, NO VERDICT** — see below |
| **9** seed stability | informational | superseded by the rung measurement above |
| **5** enrichment task | gate | needs Aviyah's dataset approval |
| **6** blind human rating | gate | Aviyah's time |
| naming **1** and **2** | gates | this build is UNNAMED |

Tests 3 and 4 beat the band-matched null in **every** band of every source — `reactome2go` recovers
80.0% at zero gene overlap against a 21.4% null, a 3.7x lift.

**Test 3's TF-IDF condition is MET, decisively.** The lexical control was built through the identical
pipeline on TF-IDF vectors over the same descriptions, and it **produces no ontology at all**: its
floors cannot be solved in any size stratum, so no family passes the recurrence gate and all 10,770
pathways are unplaced. A flat TF-IDF clustering at the declared cuts (largest cluster 4-9%, so not
degenerate) recovers **0.0%** of the headline cell where this build recovers **75.0%**. Plain word
overlap on these descriptions is not merely worse than the embedding; it yields nothing the
resampling gate will keep.

**But neither gate has an overall verdict, and not because the build failed.** Test 4's mark requires that no gene baseline beat THEMA's *recovery*
in the zero-overlap band; applied literally it fails, and the winning baseline is `kappa@25`, whose
largest cluster holds **97.3% of the universe** and whose lift is 1.0x. A mark on raw recovery is
winnable by putting everything in one cluster. Against the non-degenerate arms THEMA is clearly
ahead. The marks need a lift criterion or a non-degeneracy constraint before they adjudicate
anything; **lift was not substituted for recovery to manufacture a pass.**

**THE BUILD IS UNNAMED.** Naming has not run on the 10,770. The 1,850's 287 leaf and 215 level-1
names refer to themes that do not exist here.

## What was NOT re-solved

Nothing. Theta stays 0.70, the declared m stays 0.33, the strata are the amendment's, the inclusion
cutoff stays 0.50, the consensus parameters are unchanged (STRAY 0.10, JACCARD 0.70), the size cap
rule is unchanged, and the encoder and its revision are unchanged. The floors were solved on the
calibration scrambles at this build's own run count and confirmed once on the held-out set.

**Two implementation changes were made and each was proved byte-identical before use**: the
vectorised completion and the exact set-similarity join for seed absorption. Every cached side
carries a fingerprint of the code that wrote it, and a mismatch refuses to be reused.
