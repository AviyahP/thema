# The top of O50s, two arms. 17 Oct 2026

**Arm A passes both criteria ccode owns. Arm B fails both.** Exploratory; adopts nothing.

| | **arm A** | **arm B** |
|---|---|---|
| held-out FDR within the caps | **PASS** — overall 0.00987, worst stratum 0.01052 | **FAIL** — stratum 3-3 at **0.02564**, over the 0.02 cap |
| fewer than 49 roots | **PASS** — **47** | **FAIL** — **49**, which is not fewer than 49 |
| blind reading of every root ≥80% coherent | the reviewer's; 47 roots listed | — |
| every small root judged a distinct topic | **vacuous — neither arm has a single root of ≤50 pathways** | vacuous |
| C6 intruder test on the areas ≥70% | the reviewer's; 352 areas | — |

**And the measurement that was supposed to justify arm B contradicts its premise.** Arm B exists to
cut the unstable large themes off and rebuild above them. Stability does **not** fall as themes grow:
the 800-1,599 band is the **most** stable in the build at 0.663, and the two least stable are the two
smallest. Every band is below 0.6, so the declared rule puts the cut at **T = 50**, the lower edge of
the very first band — which means arm B drops **all 363** themes of 50 or more pathways. That is the
rule applied faithfully, and it is not the surgery the arm was designed to do.

## 1. Arm B steps 1-3: stability, the noise check and T

Hennig's clusterwise Jaccard (2007): restrict a theme to each run's 80% subsample, take its best
Jaccard against any cluster of that run's Ward tree, average over 200 runs.

| band | themes | p25 | **median** | p75 | gated n | gated med | null n | null med | null p95 | 0.6 > p95 | AUC stab | AUC supp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50-99 | 267 | 0.403 | **0.463** | 0.537 | 3,192 | 0.540 | 5,000 | 0.083 | 0.102 | yes | **1.000** | **1.000** |
| 100-199 | 67 | 0.414 | **0.457** | 0.539 | 549 | 0.541 | 5,000 | 0.059 | 0.067 | yes | **1.000** | **1.000** |
| 200-399 | 19 | 0.454 | **0.545** | 0.655 | 181 | 0.624 | 5,000 | 0.061 | 0.076 | yes | **1.000** | **1.000** |
| 400-799 | 2 | 0.526 | **0.535** | 0.543 | 95 | 0.600 | 5,000 | 0.102 | 0.142 | yes | **1.000** | **1.000** |
| 800-1,599 | 3 | 0.603 | **0.663** | 0.684 | 138 | 0.607 | 5,000 | 0.195 | 0.277 | yes | **1.000** | **1.000** |
| 1,600+ | 5 | 0.515 | **0.556** | 0.653 | 70 | 0.598 | 2,429 | 0.338 | 0.396 | yes | **1.000** | **1.000** |

**T = 50** — the lower edge of 50-99, the first band with a median below 0.6. **At 0.75 the cut would
also be 50**, so the alternative threshold changes nothing.

**Three readings, and they pull in different directions.**

**The measure works perfectly as a detector.** Scrambled candidates sit at a median stability of
0.059-0.338 against the real candidates' 0.54-0.62. **0.6 clears the scrambled 95th percentile in
every band**, and the AUC separating real gated candidates from scrambled ones is **1.000 in every
band, for stability and for support alike**. There is no overlap at all. Whatever else is true, these
themes are not noise.

**But 0.6 is not a noise threshold, and the declaration treats it as a coherence bar.** The scrambled
p95 tops out at 0.396; 0.6 sits far above it. So a theme can be utterly distinguishable from noise
and still score 0.46. The bar asks a different question — *does this theme reappear as a single Ward
cluster when the data is resampled* — and the honest answer for O50s is that most themes do not,
recovering about half of themselves on a typical run.

**The premise behind arm B is not supported.** The band medians, smallest first, are
**0.463, 0.457, 0.545, 0.535, 0.663, 0.556**. They rise rather than fall. If stability were the
criterion for what to cut, it would argue for cutting the *small* themes, not the large ones.

### One measurement choice that had to be made, because it changes the large bands

A cached run records only its dendrogram nodes of 3 or more members **and at most half the draw** —
the recurrence machinery excludes the top of each tree on purpose, since a node holding most of a
draw recurs by arithmetic rather than by meaning. Scoring a 2,000-pathway theme against that set
would cap its achievable Jaccard and understate exactly the bands the cut depends on. So the pass
**rebuilds each run's full dendrogram** and scores against every internal node of 3 or more members
with no upper cap. The trees are rebuilt, not re-chosen: same persisted subsample rows, same Ward
linkage, same vectors. `tests/test_top_two_arms.py` asserts the root of a tree is scored against.

### Sampling, stated

The 363 O50s themes and all 4,225 real gated candidates of 50+ are scored in full. The scrambled
population is 264,346 candidates across the ten calibration seeds and would need hours on its own,
so it is **sampled at most 500 per band per seed** (seed 20261017), giving 27,429 scored — 5,000 per
band except 1,600+, which has 2,429 because the seeds do not hold 500 each. Sample sizes are in the
`null n` column.

## 2. Arm A: areas on O50s, rec2fix's rules

**867 items** — 867 O50s themes and **0 loose pathways**, since O50s leaves nothing unplaced — of
which **19 are anchors** over 200 pathways and 848 are clustered. Item sizes 7 / 31 / 923. **Double
counting 7.54×**: the item sizes sum to 41,751 against 5,539 pathways, against 3.14× when the same
rule ran on O50. O50s's extra mid-size themes overlap heavily, and areas are unions of items.

4,865 candidates → 1,647 gated → 459 after consensus → **352 areas**. The combined set of 1,219
nodes lost 4 to collapse and 3 to merge, all 7 at a seam, leaving **1,212 nodes in the view** with
**14 nodes over 1,000 pathways kept and flagged**.

| stratum | floor | calib FDR | held-out FDR | real | cap |
|---|---:|---:|---:|---:|---:|
| 3-3 | 0.96 | 0.00714 | 0.0 | 7 | 0.02 |
| 4-4 | 0.945 | 0.00588 | 0.0 | 17 | 0.02 |
| 5-5 | 0.79 | 0.00667 | 0.00833 | 30 | 0.02 |
| 6-6 | 0.52 | 0.00612 | 0.01020 | 49 | 0.02 |
| 7-9 | 0.475 | 0.00745 | 0.00266 | 94 | 0.02 |
| 10+ | 0.055 | 0.00634 | 0.01052 | 1,450 | 0.02 |
| **overall** | | | **0.00987** | | **0.01** |

**Inside both caps — but the overall rate is 0.00987 against a cap of 0.01, a margin of 1.3%.** That
is a pass and it is also the thinnest margin any build in this project has reported; a different
held-out seed could plausibly tip it.

**47 roots**, of which **31 areas and 16 anchors** — no root is a bare unit. The largest: `b2_00311` 2,912 pathways (51 children),
`b2_00245` 2,550 (40), `b2_00116` 2,367 (23), `b2_00345` 2,353 (26), `b2_00330` 1,801 (21). The
smallest is `b2_00263` at 160. **Children per node: max 51, median 0, none over 60.**

**Zero small roots.** O50s's 164 roots of ≤50 pathways are all absorbed. The declared criterion that
every small root be judged a distinct topic is therefore satisfied with nothing to judge — worth
saying plainly rather than scoring it as a pass.

| | |
|---|---|
| summary placement, O50s alone | 2,194 of 2,370 = **92.6%** |
| the view alone (1,212 nodes) | 2,251 = **95.0%** |
| every O50s theme plus arm A's areas | 2,310 = **97.5%** (+116) |
| Reactome median best J — full pool / view / O50s | **0.273** / **0.162** / 0.273 |

**97.5% is the highest placement figure this project has produced.** And the Reactome column is the
counterweight: the areas as a top level score **0.162**, materially *worse* than O50s's own 0.273.
The areas place curated summaries better and resemble curated top-level branches less.

**Duplication (reported, not a gate).** No root pair reaches J ≥ 0.5 — but **37 of the 47 roots are
at least 80% inside another node**, 85 ordered pairs, the worst at 0.995 (`n04528`, 208 pathways,
inside `b2_00345`, 2,353). So the top is not a partition; it is a heavily overlapping cover in which
most roots are nearly contained in a bigger one. The reviewer reading 47 roots blind should know
that three quarters of them are near-subsets of a sibling.

## 3. Arm B: the measured cut, then areas above it

With T = 50, the items are the O50s themes below 50 pathways that are not strictly inside another
such theme: **1,330 items**, 0 anchors by declaration, sizes 6 / 27 / 49, double counting 6.72×.
**363 themes of 50+ are dropped.** 7,441 candidates → 2,760 gated → 732 after consensus → **609
areas**; 1,939 combined nodes lose 3, leaving **1,936 in the view** with 14 over 1,000 kept.

| stratum | floor | calib FDR | held-out FDR | real | cap |
|---|---:|---:|---:|---:|---:|
| **3-3** | 0.895 | 0.00513 | **0.02564** | 39 | 0.02 **OVER** |
| 4-4 | 0.935 | 0.00455 | 0.0 | 22 | 0.02 |
| 5-5 | 0.73 | 0.00745 | 0.0 | 47 | 0.02 |
| 6-6 | 0.565 | 0.00738 | 0.01230 | 61 | 0.02 |
| 7-9 | 0.38 | 0.00788 | 0.00679 | 184 | 0.02 |
| 10+ | 0.040201 | 0.00671 | 0.00654 | 2,407 | 0.02 |
| **overall** | | | **0.00679** | | 0.01 |

**The overall rate is better than arm A's, and the build still fails**: stratum 3-3 sits at 0.02564
against a 0.02 cap, on 39 real candidates — one false positive in the averaged held-out null is worth
0.0256 there, which is the same coarseness that sank earlier builds in thin strata.

**49 roots, all of them areas — a failure by one.** The criterion is "fewer than 49". Children max 42, median 0, none
over 60. **Zero small roots**, as in arm A. Duplication: no root pair at J ≥ 0.5, and **38 of 49
roots at least 80% inside another node**, 106 ordered pairs.

| | |
|---|---|
| the view alone (1,936 nodes) | 2,193 = **92.5%** |
| the O50s themes below 50 plus arm B's areas | 2,193 = **92.5%** (−1 against O50s) |
| Reactome median best J — full pool / view / O50s | 0.273 / **0.167** / 0.273 |

**Arm B buys nothing in placement.** Dropping the 363 large themes and rebuilding costs one summary
net. Arm A, which keeps them and adds areas on top, gains 116.

### The 363 dropped themes, and what replaced them

Best Jaccard from each dropped theme to any arm B area: **median 0.490**; **44 at ≥0.7**, 127 at
0.5-0.7, **192 below 0.5**. The best cases are near-identical rebuilds — `n02517` (79 pathways) at
0.889, `n01167` (114) at 0.882, `n01278` (886) at 0.816, `n01419` (1,603) at 0.775, `n02672` (2,172)
at 0.764. The worst is `n05063` at 0.180.

**So arm B dismantles 363 themes and reconstitutes about an eighth of them recognisably.** More than
half come back at under 0.5 — different objects, not the same themes rebuilt. Given that the
stability measure said the dropped themes were the *more* stable half of the build, that is a poor
trade on its own terms.

## 4. What this says

**Arm A is the surviving candidate and it is a strong one on the numbers ccode can check.** 47 roots
from O50s's 261, no small roots at all, no node over 60 children, held-out FDR inside both caps, and
**97.5% summary placement — the best figure this project has recorded**.

**Three things the reviewer and Aviyah should weigh against it.**

**The FDR margin is 1.3%.** 0.00987 against 0.01. It passes; it would not take much to fail.

**Three quarters of the roots are near-subsets of another node.** 37 of 47 at 80% or more. The
declaration makes this report-only, and that was the right call for a gate, but it is the single
biggest fact about the shape of this top level: it is a cover, not a partition, and a blind reader
asked whether each root is a distinct topic will be reading a lot of near-duplicates.

**The areas are further from curated top-level biology than O50s's own themes**, 0.162 against 0.273.
Every attempt at a top level in this project has now failed to move the Reactome measure, and arm A
actively moves it the wrong way.

**Arm B fails, and the measurement it rests on argues against its own design.** Stability rises with
size rather than falling; the cut therefore lands at the first band and takes everything with it; and
the themes it discards are the ones the measure rated most stable. The one genuinely useful thing it
produced is the noise check: **AUC 1.000 in every band, for stability and support alike**, which says
the first pass's large candidates are perfectly separable from scrambled ones — the same conclusion
prompt 41 reached from the other direction.

## 5. The base's own verdict arrived while this ran, and it qualifies everything above

While prompt 44 was building, `9b74a7c` landed the reviewer's blind reading of **O50s**, the base both
arms sit on. Scoring its own committed code against prompt 43's declared criteria:

| O50s criterion (prompt 43) | bar | result |
|---|---|---|
| blind reading of the 59 new 101-1,000 themes: coherent or linked umbrella | **≥90%** | **48 of 59 = 81.4% — FAIL** |
| blind intruder test on them | ≥70% | **58 of 59 = 98.3% — PASS** |
| the 28 "kept" themes, reported not gated | — | R1 **25 of 28 = 89.3%**, R2 26 of 26 = 100% |

**A note on the commit subject, which reads the other way.** `9b74a7c` is titled "blind reading R1
48/59 fail"; the scorer in that commit reports **48 of 59 passing**, 81.4%. Eleven fail: eight "core
with misfits" and three "unlinked mixture", none outright incoherent. The worst is `n04526`
(820 pathways), read as a "pan-metabolism catch-all".

**Two things follow, and they cut in opposite directions.**

**O50s does not currently clear its own reading gate**, so a top built on it inherits an unadopted
base. Nothing in arm A's numbers changes, but what arm A would be adopted *into* is unsettled.

**The 90% bar is not met by O50's own retained themes either.** The 28 "kept" themes — the ones O50
already had, which this project has been treating as the good case — score **89.3%**. So the gap
between the new themes and the incumbent ones is **8 points of pass rate** (81.4% against 89.3%),
and *both* sit under 90%. That is evidence about the bar as much as about O50s, and it is worth
settling before arm A's 47 roots are read against a similar standard.

**Adopted: nothing.** Arm A's remaining gates are the blind reading of its 47 roots, the C6 intruder
test on its 352 areas, and then Aviyah. Arm B is out on two counts. And the base itself has one
criterion outstanding.

## For the reviewer

`data/experiments/top_two_arms_2026-10-17/{A,B}/` — `roots.tsv` (id, kind, size, children, full
member keys), `small_roots.tsv` (**header only in both arms: neither has a root of ≤50 pathways**),
`areas.tsv` (every area with its unit ids and full member keys). Not judged here.

## Reproducing this

```sh
uv run scripts/top_two_arms.py --stability    # 399 s
uv run scripts/top_two_arms.py --arm A        # 359 s
uv run scripts/top_two_arms.py --arm B        # 666 s
uv run scripts/top_two_arms_report.py         # 10 s
uv run pytest tests/test_top_two_arms.py
```

Both arms calibrate on the 20 item scrambles 3001-3020 and are checked once on 4002-4005, to target
0.008 with caps 0.02 per stratum and 0.01 overall — rec2fix's own configuration, unchanged. Each
arm's 25 sides are cached in `areas_{arm}_{items}items_{runs}runs.json` so a downstream change does
not pay for them again. Cost: 399 s + 359 s + 666 s + 10 s, peak about 2.5 GB. No API calls.
