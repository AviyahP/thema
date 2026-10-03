# The 2 Oct RUNS measurement was a MIS-IMPLEMENTATION of the rule

*2 Oct 2026. The 10,770 track. CPU only, no API spend. The frozen 1,850 build was not modified.*

> **READ THIS FIRST -- corrected later the same day.** The RUNS rule as defined 25 Sep is
> **">= 90% of FINAL THEMES matched at Jaccard >= 0.70 between builds from disjoint tree blocks"**.
> Everything below matched the **raw grouping pool** instead -- every deduplicated Ward cluster at or
> above three members, before completion, before the support gate, before consensus. That is a
> different population, and the 90% mark was never stated over it.
>
> **So the verdicts below -- "FAIL", "RUNS = 200 is not confirmed" -- do not follow.** The figures
> are correct for what they measure and are kept, because grouping-pool agreement is a real property
> of the method and the diagnostic that explains it is worth keeping. They are simply **not evidence
> about RUNS**, in either direction.
>
> The rule's own statistic, on the frozen 1,850 (`scripts/theme_match.py`, test 9, two full builds):
> **86.9% forward, 85.9% backward** at Jaccard >= 0.70 -- which misses the 90% mark by 3 to 4 points.
> See `DECISIONS.md`, 2 Oct, "The RUNS rule was always about FINAL THEMES", for the correction of
> record and what a correct re-measurement requires.

## The declared measurement, and its result

Declared before it ran (`scripts/cut_trees.py`, and the sampling in `DECISIONS.md` 2 Oct): match the
grouping pool of one block of runs against the pool of a disjoint block, report the share with a
partner at **Jaccard >= 0.70**, and **pass at >= 90% in the worse direction**. Current setup:
centred-and-renormalised space, inclusion cutoff 0.50, size cap 29.0133% = 3,125, tol 0.15,
min_size 3. Estimated from 5,000 sampled groupings per direction, seed 20261002.

| pair | pool sizes | forward | backward | worse | verdict |
|---|---|---|---|---|---|
| 1-100 vs 101-200 | 276,725 vs 275,986 | 61.0% +/- 0.69% | 61.6% +/- 0.69% | **61.0%** | **FAIL** vs 90% |
| 1-200 vs 201-400 | 500,429 vs 501,120 | 64.0% +/- 0.68% | 63.5% +/- 0.68% | **63.5%** | **FAIL** vs 90% |

**RUNS = 200 is not confirmed. No build was run. No new trees were built.**

## The control: the frozen 1,850 fails the same mark, harder

`docs/status/OPEN.md` records "100 trees per run: 89.1% of groupings match at >= 0.70. 200 gives
91.4%" from the 1,850 work. No committed script produced it and it records no space and no cutoff
(`docs/debt.md`). A 61% against a claimed 89% has two possible readings, and they call for opposite
decisions: either the 10,770 recurs less than the 1,850 did, or **the 89.1% measured a different
quantity and the 90% mark never applied to this one**.

`scripts/ladder_control_1850.py` separates them -- the identical estimator, sample size, seed,
theta, tol, min_size, centred space and cap share, on the 1,850 universe. It reads the universe
through the verifying loader and builds its own trees in a scratch directory; **nothing in the
frozen build is read or written.**

| universe | pair 1 worse | pair 2 worse | verdict |
|---|---|---|---|
| 10,770 | **61.0%** | **63.5%** | FAIL |
| **1,850 (the frozen build's own universe)** | **54.8%** | **58.2%** | **FAIL** |

**The frozen 1,850 build fails the pass mark by this measurement, more badly than the 10,770 does.**
The 10,770 is *more* stable here, not less. So the second reading holds: the recorded 89.1% is not
the share of the raw grouping pool, and the 90% mark was never a gate on this quantity.

## Where the failure sits -- post hoc, and labelled as such

`scripts/ladder_diagnostic.py` breaks the FAILED share out by the grouping's own support and by its
size, from the same sample, seed and threshold. **It was written after the failure and cannot turn
it into a pass.** Pair 1 on both universes, and the two agree band for band:

| the grouping's own support | 1,850: share of pool | matched | 10,770: share of pool | matched |
|---|---|---|---|---|
| 0.00-0.10 | **53.2%** | **26.3%** | **47.8%** | **28.3%** |
| 0.10-0.20 | 15.3% | 78.1% | 15.0% | 80.1% |
| 0.20-0.33 | 12.0% | 90.3% | 12.5% | 90.4% |
| 0.33-0.50 | 8.6% | 93.7% | 9.9% | 95.9% |
| 0.50-0.75 | 6.3% | 96.8% | 7.9% | 98.2% |
| 0.75-1.01 | 4.6% | 98.7% | 7.0% | 99.4% |
| **at or above the declared m = 0.33** | **19.5%** | **95.9%** | **24.7%** | **97.7%** |
| overall | | 55.5% | | 61.0% |

| members | 1,850: share of pool | matched | median support | 10,770: share of pool | matched | median support |
|---|---|---|---|---|---|---|
| 3 | 5.4% | 80.7% | 0.230 | 5.0% | 79.2% | 0.240 |
| 4 | 10.4% | 77.8% | 0.208 | 10.0% | 81.4% | 0.221 |
| 5 | 8.5% | 77.3% | 0.189 | 9.3% | 81.3% | 0.255 |
| 6 | 8.4% | 77.4% | 0.202 | 7.7% | 81.3% | 0.214 |
| 7-9 | 17.5% | 73.7% | 0.130 | 18.0% | 80.9% | 0.190 |
| 10+ | **49.8%** | **34.3%** | 0.030 | **50.0%** | **41.0%** | 0.030 |

The two universes agree closely enough that the shape is a property of the METHOD, not of either
dataset: in both, half the pool is a 10+-member cluster with median support 0.030, and in both the
matched share rises monotonically with support to essentially 100% at the top.

**Over half the pool is a grouping one subsample produced and no other run reproduced.** Every
internal Ward node at or above three members enters the pool, so a single 80% draw contributes
thousands of clusters -- most of them large, with median support 0.030 at 10+ members. Those are
precisely what the support gate removes, and they are counted in the declared share.

## What this does and does not establish -- rewritten after the correction

**Established:** the raw grouping pool agrees across disjoint run blocks at 55-64%, at both scales,
and the shape of that disagreement is a property of the method -- half the pool is a 10+-member
cluster with median support 0.030 that one subsample produced and no other reproduced. The 1,850 and
the 10,770 agree band for band, so this is not a scale effect.

**NOT established -- and this is the correction:** anything about RUNS. The rule is about final
themes and these numbers are about the grouping pool, so they neither confirm nor refuse RUNS = 200.
My original reading of them as a failure of the rule was wrong.

**Also not established:** that the build is fine. The rule's own statistic on the frozen 1,850 is
86.9% forward and 85.9% backward, **below the declared 90%**. That is a real shortfall on the right
unit, and it is the live question -- not the 61% above.

**Still not established, and still not to be read off the support table:** that gating at m = 0.33
rescues the measurement. "95.9% above m = 0.33" is a post-hoc cut, and a threshold chosen after
seeing which threshold works is not evidence. It is kept here as diagnosis only.

**Aviyah's decision, not mine.** Nothing proceeds to the build.
