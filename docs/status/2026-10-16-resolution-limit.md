# The first pass's resolution limit. 16 Oct 2026

**There are two answers and the gap between them is the finding.**

**T = 39** if the limit is measured the way the floor solver actually works — walking the scrambles'
own support values for a cut. Above 39 pathways the solver's ladder has **exactly one rung** and
cannot discriminate at all.

**T is unbounded** if the limit is measured by asking whether *any* cut separates the two
populations. From 40 pathways up the scrambles produce a single distinct support — **0.005, one
subsample in 200, never two** — while the real side reaches 1.000. A cut just above 0.005 separates
them cleanly in **every** bin up to 1,280+, with a rule-of-three bound on the false-discovery rate of
0.00006 to 0.0031 against a target of 0.008.

**So the first pass can tell large real clusters from scrambled ones. Its own gate is what cannot.**
Not because the floor is too high — the 10+ floor is 0.025126 — but because the 10+ stratum pools
every size from 10 to 2,809 and solves one floor for all of them, and that floor is set by the small
end, where the null genuinely does reach high support.

Both arms agree on both answers, so the 23 exclusions do not move the limit. Read-only; adopts
nothing.

## The bin table — arm x2 (O50's own candidates)

`r` = real, `n` = scrambled (mean per seed for counts, all ten pooled for percentiles).
*SOLVER fdr* is the best rate reachable on the scrambles' own support values; *FULL fdr* the best
over every support value present in the bin. *3/10 bound* is the rule-of-three upper bound on the
rate where the full ladder's best rests on an observed zero null count.

| bin | real | null/seed | r med | r p90 | r max | n med | n max | n vals | SOLVER fdr | keeps | FULL fdr | at cut | keeps | 3/10 bound |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10-19 | 25,887 | 62,500 | 0.010 | 0.105 | 1.000 | 0.005 | **0.170** | **80** | 0.00006 | 5,793 | 0.00000 | 0.030 | 5,793 | 0.000179 |
| 20-39 | 27,148 | 32,063 | 0.005 | 0.040 | 1.000 | 0.005 | **0.015** | **3** | 0.00001 | 11,818 | 0.00000 | 0.010 | 11,818 | 0.000051 |
| 40-79 | 16,896 | 16,323 | 0.005 | 0.020 | 1.000 | 0.005 | **0.005** | **1** | **0.96611** | **0** | 0.00000 | 0.010 | **4,830** | 0.000062 |
| 80-159 | 9,053 | 8,275 | 0.005 | 0.010 | 0.980 | 0.005 | 0.005 | 1 | **0.91407** | **0** | 0.00000 | 0.010 | **1,030** | 0.000291 |
| 160-319 | 4,567 | 4,151 | 0.005 | 0.005 | 0.410 | 0.005 | 0.005 | 1 | **0.90889** | **0** | 0.00000 | 0.010 | **234** | 0.001282 |
| 320-639 | 1,974 | 2,083 | 0.005 | 0.005 | 0.090 | 0.005 | 0.005 | 1 | **1.05502** | **0** | 0.00000 | 0.010 | **96** | 0.003125 |
| 640-1,279 | 709 | 1,052 | 0.005 | 0.020 | 0.805 | 0.005 | 0.005 | 1 | **1.48392** | **0** | 0.00000 | 0.010 | **160** | 0.001875 |
| 1,280+ | 161 | 451 | 0.010 | 0.080 | 0.630 | 0.005 | 0.005 | 1 | **2.80186** | **0** | 0.00000 | 0.010 | **103** | 0.002913 |

### The finer split across the break

| bin | real | null/seed | r max | n vals | SOLVER fdr | keeps | FULL keeps | 3/10 bound |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 80-119 | 5,968 | 5,512 | 0.595 | 1 | 0.92363 | 0 | 821 | 0.000365 |
| 120-159 | 3,085 | 2,763 | 0.980 | 1 | 0.89559 | 0 | 209 | 0.001435 |
| 160-239 | 3,058 | 2,773 | 0.410 | 1 | 0.90674 | 0 | 187 | 0.001604 |
| 240-319 | 1,509 | 1,378 | 0.105 | 1 | 0.91325 | 0 | **47** | **0.006383** |

**The finer split does not move T on either ladder.** On the solver's ladder every one of these bins
keeps 0, which is already true of the doubling they sit inside. On the full ladder every one passes.
But 240-319 is the weakest link anywhere in the table: its clearance rests on **47** candidates and
a bound of **0.006383**, within 20% of the target. In arm L the same bin has 38 candidates and a
bound of **0.007895** — inside the target by 1%. If T were ever to be set by a bin rather than by a
ladder, it would be set there.

## Arm L (the side the cal8 floors were solved from)

| bin | real | SOLVER fdr | keeps | FULL keeps | 3/10 bound |
|---|---:|---:|---:|---:|---:|
| 10-19 | 26,143 | 0.00006 | 5,843 | 5,843 | 0.000183 |
| 20-39 | 27,398 | 0.00001 | 12,101 | 12,101 | 0.000051 |
| 40-79 | 16,946 | 0.96326 | 0 | 4,725 | 0.000063 |
| 80-159 | 9,007 | 0.91874 | 0 | 1,038 | 0.000289 |
| 160-319 | 4,595 | 0.90335 | 0 | 245 | 0.001224 |
| 320-639 | 2,014 | 1.03406 | 0 | 88 | 0.003409 |
| 640-1,279 | 719 | 1.46328 | 0 | 165 | 0.001818 |
| 1,280+ | 174 | 2.59253 | 0 | 123 | 0.002439 |

**T = 39 on the solver's ladder and unbounded on the full ladder — identical to arm x2.** This arm
exists because O50's floors and O50's candidates do not come from the same universe: the cal8 floors
were solved from the pre-exclusion universe L (5,559 pathways, 100,564 candidates — its per-stratum
counts 804 / 1,090 / 1,455 / 2,193 / 8,026 / 86,996 are exactly what `floors_L_cal8.json` records)
and then applied to the 23-exclusion universe (5,539 pathways, 99,951 candidates). Arm L pairs the
scrambles with the real side they were solved against, so it has no mismatch at all. **The two arms
agree on every bin to within a few candidates, so nothing in this report turns on which universe is
used.**

## Why the two ladders disagree

The floor solver walks **the scrambles' own support values** and takes the first cut where the rate
reaches the target. That is correct when the null's support is spread out, and it is what the
`n vals` column measures:

| bin | distinct scrambled supports | scrambled maximum |
|---|---:|---:|
| 10-19 | **80** | 0.170 |
| 20-39 | **3** | 0.015 |
| 40-79 and every bin above | **1** | **0.005** |

**From 40 pathways up the scrambles are degenerate: all 163,234 pooled candidates in 40-79, and
every pooled candidate in every larger bin, have support exactly 0.005.** A scrambled grouping of 40 or more pathways is found in one subsample of 200 and
never in two. So the solver's ladder offers one rung — a cut at 0.005, which keeps everything
including the whole null — and reports a best rate of 0.9 to 2.8. That is a property of the ladder,
not of the bin.

Give the same bins a cut at 0.010 and the separation is total:

| bin | real candidates above the scrambles' maximum | rule-of-three bound |
|---|---:|---:|
| 40-79 | **4,830** | 0.000062 |
| 80-159 | **1,030** | 0.000291 |
| 160-319 | **234** | 0.001282 |
| 320-639 | **96** | 0.003125 |
| 640-1,279 | **160** | 0.001875 |
| 1,280+ | **103** | 0.002913 |

A zero observed null count over ten seeds is not proof of a zero rate, so the bound column applies
the rule of three: a 95% upper bound of 3/10 on the mean null count, divided by the real count kept.
**Every bin clears 0.008 on that bound, the worst by a factor of 2.6.**

## What this means for the 10+ stratum

O50's gate uses six strata — 3-3, 4-4, 5-5, 6-6, 7-9 and **10+** — and the last one pools every size
from 10 to 2,809 under a single floor of **0.025126**. That floor is solved against the pooled null,
which is dominated by the small end: of 219,096 scrambled candidates per seed, 62,500 are 10-19, and
*those* reach support 0.170 across 80 distinct values. The floor has to sit above that noise, so it
lands at 0.025 — and then applies unchanged to a 300-pathway candidate whose own null never exceeds
0.005.

That is the same loss prompt 40 measured from the other end: 25,560 candidates of 51+ pathways died
at the gate, all with support between 0.005 and 0.025. **This report says what they would have cost
at a per-bin threshold instead**: a cut at 0.010 admits 4,830 of 40-79, 1,030 of 80-159, 234 of
160-319, 96 of 320-639, 160 of 640-1,279 and 103 of 1,280+ — **6,453 candidates at a bounded FDR
under 0.0032** — against the 16, 28 and 48 that the pooled floor admits in the 201-500, 501-1,000 and
1,001+ bands.

**This is a diagnostic and it proposes nothing.** Splitting the 10+ stratum is a change to the
method, it would need its own declaration and its own held-out confirmation, and admitting 6,453
large candidates would change everything downstream — consensus, the twin rule, the repair and the
final theme count. All this report establishes is that the evidence for those clusters exists and
that the current stratification discards it.

## Answering the question as posed

The prompt asked for T as "the largest size at which the first pass can still separate real clusters
from scrambled ones", and expected a break between 100 and 200 from O50's size distribution.

**The measured answer is not where the distribution breaks.** On the solver's ladder T = **39**, far
below 100. On the full ladder there is no break at all up to 1,280+. The O50 size distribution's
break between 100 and 200 is therefore **not** a resolution limit: it is where the pooled 10+ floor
stops admitting anything, and the two have different causes.

**The honest reading of "not vouched for by the method":** O50's clusters above 39 pathways are not
vouched for **by the floor the build used**, because that floor was calibrated against a null the
large bins do not share. They *are* separable from noise at a per-bin threshold, by a wide margin.
Those are different statements and only the first one justifies where the areas pass takes over.

## Reproducing this

```sh
uv run python data/experiments/resolution_limit_2026-10-16/code/resolution.py
```

1.3 s, 1.3 GB. The ten calibration scrambles (seeds 3001-3010) and both real sides are all cached;
nothing was recomputed. Outputs: `bins.tsv` (both arms, both bin sets, both ladders),
`summary.json`, `report.txt`. No API calls.

One note on the cross-check printed at the top: 26,095 of 26,223 `fate.tsv` rows carrying a family
support match a real-side candidate exactly on (size, support). The 128 that do not are the rows
where `fate.tsv` records the **post-consensus** size, because consensus can grow an accepted set;
those rows' sizes are no longer the pre-gate size the real side holds. The real side is the source
for every number here, and prompt 40 proved it byte-identical to the instrumented material.
