# Where do the large first-pass candidates go? 16 Oct 2026

**Answer to question 1: the gate, and not because the gate is strict.** Of 31,027 candidates holding
51 or more pathways, **25,560 (82%) fail the support floor** — and every one of them has support
between **0.005 and 0.025**, with a **median of 0.005**. Support 0.005 is *one subsample in 200*. The
floor is 0.025126, about five runs in 200. **Not one gated-out candidate of any size is within reach
of it.** Large groupings are not being filtered out by a strict threshold; they barely recur at all.

**Answer to question 2: no.** The large candidates the pipeline removes *after* the gate are
near-duplicates of themes O50 already keeps — **81% match an O50 node at J ≥ 0.7, and 0% match a
rec2fix area at J ≥ 0.7**. And in reverse, of the 105 rec2fix areas holding 201-1,000 pathways,
**none matches any first-pass candidate at J ≥ 0.7** — gated, removed or surviving. The best any area
manages is **0.625** against the 13,537 gated candidates, **0.585** against the 37 removed ones and
**0.696** against a final O50 theme, with 95% of areas below 0.5 on the first of those. **The areas
pass does not recover a layer the first pass discarded. It builds objects the first pass never
proposed.**

Read-only. Nothing is adopted, no build is changed.

## The premise this corrects

The prompt's reasoning was: *the 10+ floor is only 0.025, so large candidates should pass the gate.*
The floor is indeed 0.025126 — and it is the **same** floor for every band here, because a candidate
of 51 or more pathways is always in the 10+ stratum. The candidates still fail it, because their
support is an order of magnitude lower still:

| band | gated out | floor | support min | median | max | at or over the floor |
|---|---:|---:|---:|---:|---:|---:|
| 51-100 | 12,931 | 0.025126 | 0.0050 | 0.0050 | 0.0250 | **0** |
| 101-200 | 7,227 | 0.025126 | 0.0050 | 0.0050 | 0.0250 | **0** |
| 201-500 | 4,148 | 0.025126 | 0.0050 | 0.0050 | 0.0250 | **0** |
| 501-1,000 | 973 | 0.025126 | 0.0050 | 0.0050 | 0.0250 | **0** |
| 1,001+ | 281 | 0.025126 | 0.0050 | 0.0050 | 0.0250 | **0** |

The maximum is 0.025 — five runs in 200 — which is *just* under 0.025126. So the distribution does
not even brush the floor: there is no near-miss population, and lowering the floor a little would
admit nothing. Lowering it to 0.005 would admit the whole one-run tail, which is 25,560 candidates in
these bands alone and is exactly what the FDR calibration (target 0.008) exists to exclude.

**That is the finding: a 300-pathway grouping that recurs in one subsample of 200 is not evidence of
a theme, and the first pass is right to drop it. The mid-size layer is missing because it was never
recurrently proposed, not because it was thrown away.**

## 1. The pipeline, instrumented and proved identical

Two proofs run before any number is reported, and both pass:

| proof | result |
|---|---|
| the instrumented candidate material against the cached real side (`calibration/real.npz`) | **blocks identical, supports identical** |
| the final themes against the frozen O50's `members.tsv` | **4,602 against 4,602, identical as sets** |

Nothing in the recurrence machinery is reimplemented: `prepare`, `score`, `family_members_fast`,
`families`, `family_support`, `gate`, `consensus`, `collapse_chains` and `merge_stale` are the
build's own functions, composed with recording between them. The one piece of library *structure*
re-expressed is `material`'s loop over groupings, because the instrumentation has to sit inside it —
and proof 1 is what makes that re-expression checkable rather than trusted.

**The step order is not quite the one the prompt lists**, and it matters for reading the table:
absorption (the twin rule) runs **before** the gate, not after; and chain collapse and the stale pass
**alternate** to a joint fixed point rather than running once each. Reported in the real order.

| stage | in | out |
|---|---:|---:|
| matched groupings (the pool) | | 270,570 |
| completion | 270,570 | 264,897 (5,673 unscored, **0** under `MIN_SIZE`) |
| absorption, the twin rule at θ = 0.70 | 264,897 | **99,951 seeds** (164,946 absorbed) |
| family support | 99,951 | 99,951 (**0** dropped for NaN) |
| **the gate** | 99,951 | **13,537** |
| consensus at 0.50 | 13,537 | 5,261 (8,276 superseded) |
| joint fixed point at 0.85 / 0.50 | 5,261 | **4,602** (587 collapsed, 72 merged) |

## 2. Survival by step and band, candidates of 51+ pathways

| step | 51-100 | 101-200 | 201-500 | 501-1,000 | 1,001+ | total |
|---|---:|---:|---:|---:|---:|---:|
| completed | 16,816 | 7,749 | 4,232 | 1,403 | 827 | 31,027 |
| after absorption | 13,452 | 7,277 | 4,164 | 1,001 | 329 | 26,223 |
| after family support | 13,452 | 7,277 | 4,164 | 1,001 | 329 | 26,223 |
| **after the gate** | **521** | **50** | **16** | **28** | **48** | **663** |
| after consensus | 100 | 14 | 5 | 2 | 8 | 129 |
| **final** | **68** | **10** | **5** | **2** | **4** | **89** |

**Lost at each step:**

| step | 51-100 | 101-200 | 201-500 | 501-1,000 | 1,001+ | total |
|---|---:|---:|---:|---:|---:|---:|
| absorption | 3,364 | 472 | 68 | 402 | 498 | 4,804 |
| family support | 0 | 0 | 0 | 0 | 0 | 0 |
| **the gate** | **12,931** | **7,227** | **4,148** | **973** | **281** | **25,560** |
| consensus | 421 | 36 | 11 | 26 | 40 | 534 |
| collapse and stale | 32 | 4 | 0 | 0 | 4 | 40 |

**By fate:** absorbed 4,804, gated out 25,560, superseded 534, collapsed 35, merged 5, final 89.

Three things to read out of this.

**The gate is where the large candidates go, by two orders of magnitude.** In 201-500, 4,164 reach
the gate and **16** pass. In 501-1,000, 1,001 reach it and **28** pass. Everything downstream is
small by comparison: consensus removes 11 and 26 in those bands, collapse and the stale pass remove
**zero**.

**Absorption is the second-largest loss, and it is concentrated at the top.** It removes 498 of 827
candidates over 1,000 pathways and 402 of 1,403 in 501-1,000 — 60% and 29% — against 1.6% in 201-500.
Large groupings come in near-identical variants (the worst examples below sit at J = 0.97-0.99), and
the twin rule folds them into one seed. That is the rule working, not a leak: the seed survives and
carries the family's pooled support.

**The final counts reproduce the figures the prompt quotes for O50 exactly**: **5** themes of 201-500
and **2** of 501-1,000. The instrumented rebuild agrees with the frozen build on the very numbers
that prompted the question, which is a third check on it.

## 3. The 20 most-supported removed candidates

### 201-500 pathways — 4,227 removed of 4,232

| grouping | size | support | removed at | removed by | by size | J |
|---|---:|---:|---|---|---:|---:|
| `g184958` | 208 | 0.115 | consensus | `c3493` | 206 | 0.824 |
| `g173912` | 355 | 0.090 | consensus | `c6406` | 349 | 0.801 |
| `g135822` | 204 | 0.055 | consensus | `c3493` | 206 | 0.814 |
| `g60058` | 358 | 0.035 | absorption | `g173912` | 355 | 0.896 |
| `g74783` | 230 | 0.035 | consensus | `c2767` | 176 | 0.631 |
| `g156347` | 209 | 0.035 | consensus | `c10023` | 280 | 0.619 |
| `g178851` | 370 | 0.035 | absorption | `g173912` | 355 | 0.883 |
| `g264761` | 253 | 0.035 | absorption | `g270530` | 255 | 0.889 |
| `g49351` | 334 | 0.030 | absorption | `g87573` | 319 | 0.882 |
| `g71866` | 277 | 0.030 | consensus | `c10023` | 280 | 0.803 |

The top of the list tops out at **support 0.115** — 23 runs in 200 — and falls to 0.025 by row 19.
Every removal is to something of nearly the same size at J = 0.6-0.9: these are variants of each
other, not a distinct layer. The full twenty is in the build's `report.txt`.

### 501-1,000 pathways — 1,401 removed of 1,403

| grouping | size | support | removed at | removed by | by size | J |
|---|---:|---:|---|---|---:|---:|
| `g61576` | 801 | **0.595** | consensus | `c1360` | 813 | 0.845 |
| `g44639` | 728 | 0.405 | absorption | `g246103` | 727 | **0.990** |
| `g137152` | 724 | 0.405 | absorption | `g246103` | 727 | 0.977 |
| `g79089` | 721 | 0.395 | absorption | `g246103` | 727 | 0.981 |
| `g161465` | 775 | 0.385 | consensus | `c1664` | 781 | 0.859 |
| `g214059` | 722 | 0.385 | absorption | `g246103` | 727 | 0.969 |
| `g242572` | 725 | 0.385 | absorption | `g246103` | 727 | 0.970 |

This band's losses *are* well supported — up to 0.595 — and that is exactly the point: five of the
seven are absorbed into **one** seed, `g246103` (727 pathways), at J = 0.97-0.99. The band's
apparent mass is one theme described seven slightly different ways. The two consensus removals go to
813- and 781-pathway candidates at J = 0.85-0.86, which are the themes O50 keeps as `n01027` and
`n01279`.

## 4. Do the losses match what the areas pass rebuilds? No, in both directions

**Forward: the removed 201-1,000 candidates that passed the gate.** 37 of them, **36 distinct groups**
at J ≥ 0.9. Every single one was removed at **consensus** — none at collapse or the stale pass.

| best J to | ≥0.7 | 0.5-0.7 | <0.5 |
|---|---:|---:|---:|
| any **rec2fix area** | **0 (0%)** | 7 (19%) | 29 (81%) |
| any **O50 node** | **29 (81%)** | 7 (19%) | 0 (0%) |

**The removed candidates are variants of the themes O50 kept, not of the areas rec2fix built.** The
O50 partners are the same handful every time: `n01027` (813), `n01279` (781), `n01420` (1,412),
`n03315` (349), `n02017` (206) — at J up to 0.859. Consensus removed them *because* an accepted theme
already covered them, which is what a same-theme cutoff of 0.50 is for.

**Reverse: the 105 rec2fix areas of 201-1,000 pathways.**

| best J to | ≥0.7 | 0.5-0.7 | <0.5 |
|---|---:|---:|---:|
| any **gated first-pass candidate** (13,537 of them) | **0 (0%)** | 5 (5%) | 100 (95%) |
| any **removed candidate** (the 37) | **0 (0%)** | 1 (1%) | 104 (99%) |
| any **final O50 theme** | **0 (0%)** | 7 (7%) | 98 (93%) |

**Not one rec2fix area reaches 0.7 against anything the first pass produced**, and the three maxima
are close enough to be worth naming: **0.625** (`b2_00158` against a gated candidate), **0.585**
(`b2_00198` against a removed one) and **0.696** (`b2_00158` against a final O50 theme — missing the
0.7 bar by four thousandths). The clearest point of contact is `b2_00198` (851 pathways) against
`g180090`, which *was* gated (as `c9085`, hence the identical 0.585 in both columns) and was then
superseded at consensus by the 1,412-pathway candidate that became `n01420`. Everything else is below
0.5, and 95% of areas have no gated first-pass candidate above 0.5 at all.

The largest areas are the clearest: `b2_00242` (977 pathways) matches its best gated candidate at
**0.337**, its best removed one at 0.108, and its best O50 theme at 0.292. `b2_00156` (919): 0.446 /
0.043 / 0.350. These are not themes that were proposed and rejected. They are unions of units that
the resampling never grouped together as a pathway set.

## 5. What this says

**The mid-size layer is absent from the first pass for a reason that no threshold change will fix.**
Large groupings do not recur: the gate removes 25,560 candidates of 51+ pathways and their support
has a median of 0.005 — one subsample in 200 — against a floor of 0.025126. There is no near-miss
band to recover. This is the same thing the 8 Oct diagnostic saw from the other side when it found
that mid-size clusters recur at J 0.5 but not at 0.70; here the effect is visible in support rather
than in the match threshold, and it is much larger than a threshold adjustment could reach.

**M5_cal8 keeping about 3× more of them is consistent with this, and does not contradict it.** M5
lowers the *recurrence* threshold to 0.50, which changes how support is computed — a grouping that
matches nothing at J ≥ 0.70 can match plenty at J ≥ 0.50 — so the support distribution itself moves.
What this diagnostic shows is that at θ = 0.70, no floor would have helped. Whether θ = 0.50 support
is evidence of a theme is a separate question and this run says nothing about it.

**The areas pass is not a recovery operation.** 0 of 105 areas in 201-1,000 matches a first-pass
candidate at 0.7; 95% have nothing above 0.5. The areas are constructed objects — unions of the
maximal non-grab-bag nodes — and their relationship to the recurrence evidence is that they have
almost none. That is worth knowing before the layer is defended on the grounds that it recovers
structure the first pass lost: it does not, because the structure was never there to lose.

**The downstream stages are nearly irrelevant for large candidates.** Consensus removes 11 of the
201-500 band and 26 of 501-1,000; collapse and the stale pass remove **zero** in both. Whatever is
wrong with the size distribution, it is not the twin rule and it is not the repair.

**Adopted: nothing. This is a diagnostic and it changes no build.**

## Reproducing this

```sh
uv run python data/experiments/consensus_fate_2026-10-16/code/fate.py
```

167 s and 3.3 GB on the cached trees, which are all present. Outputs: `fate.tsv` (31,027 rows, one
per tracked candidate), `step4_groups.tsv`, `step4_areas.tsv`, `summary.json` and `report.txt`.
No API calls.
