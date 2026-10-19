# Areas on the O50s roots (Aviyah's version 1). 18 Oct 2026

**Both criteria ccode owns pass, and they pass by the widest margins any top level in this project
has managed: 12 roots against a ceiling of 49, and a held-out FDR of 0.00558 against a cap of 0.01.**
Summary placement reaches **99.2%**, a new best. The sanity check is clean: **0 nodes sit wholly
inside another without descending from it.**

**And it answers prompt 45's open question: yes.** With the giants as units, **all five are contained
by areas** — the thing arm A could never do, because arm A never offered a giant to the clustering.

**The cost is at the top.** The largest root, `a_00044`, holds **4,485 pathways — 81% of the
universe** — and contains two giants. Three of the six size strata admitted **nothing at all**.
Twelve roots may be fewer than Aviyah wants rather than more. Exploratory; adopts nothing.

| criterion | result |
|---|---|
| held-out FDR within the caps | **PASS** — overall **0.00558**, worst stratum **0.00625** |
| fewer than 49 roots | **PASS** — **12** |
| blind reading of every root ≥80% coherent | the reviewer's; 12 roots listed |
| every small root judged a distinct topic | **vacuous — there are no small roots** |
| C6 intruder test ≥70% | the reviewer's; 66 areas |

## 1. Units, and what makes this a different design

**261 units: every O50s root, the five giants included, each as one unit. No giant drop, no
anchors.** Sizes 10 / 39 / 2,564 (min / median / max), mean 109.5; **164 of the 261 hold 50 pathways
or fewer**, which is the clutter the pass is asked to absorb. Bands: 6 at 1-10, 158 at 11-50, 79 at
51-200, 13 at 201-1,000, 5 over 1,000. **Double counting 5.16×** (28,582 against 5,539) against arm
A's 7.54×. The roots cover **all 5,539 pathways**, so no unit had to be invented for a remainder —
the build asserts that rather than assuming it.

Three differences from arm A, and they are the design:

| | arm A (prompt 44) | **here** |
|---|---|---|
| units | 867, giants dropped | **261 O50s roots, giants kept** |
| anchors | 19 held out of clustering | **none** |
| structure | areas + anchors + units, 1,212 nodes | **the whole unchanged O50s DAG + areas, 5,724 nodes** |
| twin and chain rules | inside the pass **and** over the combined set | **inside the pass only** |
| O50s itself | 7 themes removed at the seams | **untouched, 0 removed** |

Because the structure holds every O50s theme, containment is complete by construction — which is the
defect prompt 45 had to repair in arm A, absent here by design rather than by patch.

## 2. Held-out FDR

| stratum | floor | calib FDR | held-out FDR | real | cap |
|---|---:|---:|---:|---:|---:|
| 3-3 | **none** | — | — | **0** | 0.02 |
| 4-4 | **none** | — | — | **0** | 0.02 |
| 5-5 | 0.9 | 0.00625 | **0.0** | 8 | 0.02 |
| 6-6 | **none** | — | — | **0** | 0.02 |
| 7-9 | 0.74 | 0.00714 | **0.0** | 21 | 0.02 |
| 10+ | 0.16 | 0.00729 | **0.00625** | 240 | 0.02 |
| **overall** | | | **0.00558** | 269 | **0.01** |

**Inside both caps with room — the best margin of any top level here.** But read the `none` rows:
**three of the six strata admit nothing**, because no support cut reached the 0.008 target for
candidates of 3, 4 or 6 units. So every area is built from a candidate of **5 units or more**, and
the floors that do exist are high — 0.9 at 5-5 and 0.74 at 7-9. 1,663 candidates → **269 gated** →
95 after consensus → **66 areas**.

That is a much stricter gate than arm A's (1,647 of 4,865), and it is why there are 66 areas rather
than 352. The areas that survive are strongly supported: support median **0.877**, min 0.165, max
1.000 — against arm A's areas, which sat near the floor.

## 3. The 12 roots

| root | size | share of universe | units | support | children | contains |
|---|---:|---:|---:|---:|---:|---|
| `a_00044` | **4,485** | **81.0%** | 92 | 0.890 | 95 | `n01843`, `n02672` |
| `a_00037` | 2,306 | 41.6% | 20 | 0.960 | 18 | `n03878` |
| `a_00062` | 2,204 | 39.8% | 28 | 0.995 | 46 | `n04994` |
| `a_00035` | 1,929 | 34.8% | 54 | 0.870 | 33 | `n01419` |
| `a_00060` | 915 | 16.5% | 37 | 0.220 | 7 | |
| `a_00057` | 857 | 15.5% | 37 | 0.250 | 15 | |
| `a_00048` | 720 | 13.0% | 47 | 0.910 | 22 | |
| `a_00052` | 688 | 12.4% | 34 | 0.315 | 6 | |
| `a_00064` | 385 | 7.0% | 21 | 0.170 | 2 | |
| `a_00050` | 262 | 4.7% | 11 | 0.330 | 6 | |
| `a_00059` | 257 | 4.6% | 10 | 0.235 | 15 | |
| `a_00021` | 239 | 4.3% | 7 | 0.935 | 7 | |

**Every root is an area — no O50s theme and no giant is left at the top.** The 12 cover all 5,539
pathways, a pathway sits in a median of **2** roots and at most 11, and **0 pathways are in no root**.

**The top is dominated by one node.** `a_00044` holds 81% of the universe over 92 units and contains
two giants. Four roots hold more than a third of the universe each. Whether that is a top level or a
single bag with eleven footnotes is exactly what the blind reading is for, and it is the main thing
to weigh against the clean criteria.

**Zero small roots.** All 164 O50s roots of ≤50 pathways are absorbed, so the small-root criterion
has nothing to judge — worth saying plainly rather than scoring as a pass.

## 4. Duplication (reported, not a gate)

**No root pair reaches J ≥ 0.5.** Roots at least 80% inside another node: **14 ordered pairs**,
binned by pathways missing:

| missing | pairs |
|---|---:|
| **0** | **0** |
| **1-5** | **0** |
| 6-20 | 3 |
| 21+ | 11 |

**Both small bins are empty**, so nothing is a bookkeeping artefact — every near-containment has a
real gap. The three tightest are genuine near-misses: `a_00048` (720) is 99.2% inside `a_00035`
missing 6; `a_00064` (385) is 98.4% inside `a_00057` missing 6; `a_00050` (262) is 97.7% inside
`a_00057` missing 6. Under Aviyah's propagation rule from prompt 45 (≥98%, ≤5 missing) **none of
these would qualify** — all three miss by one pathway over the limit.

For comparison: arm A had **37 of 47** roots ≥80% inside another node, and A1 had 110 ordered pairs.
Here it is **14**, over 12 roots. This top level is far less of a cover.

## 5. Areas

**66 areas.** Bands: 13 at 51-200, 37 at 201-500, 10 at 501-1,000, **6 over 1,000**.

| area | size | units | contains a giant |
|---|---:|---:|---|
| `a_00044` | **4,485** | 92 | `n01843` (2,564), `n02672` (2,172) |
| `a_00010` | 2,739 | 73 | `n02672` (2,172) |
| `a_00038` | 2,599 | 14 | `n01843` (2,564) |
| `a_00037` | 2,306 | 20 | `n03878` (2,135) |
| `a_00062` | 2,204 | 28 | `n04994` (2,096) |
| `a_00035` | 1,929 | 54 | `n01419` (1,603) |

**Six areas contain a giant, and between them they contain all five giants** — `n01843` and `n02672`
twice each, the other three once. **That is the direct answer to prompt 45's open question.** Arm A's
areas contained no giant because `units_of` never let a giant be a unit; make the giants units and
the clustering puts every one of them inside something.

Note `a_00038`: 2,599 pathways from only **14 units**, one of which is the 2,564-pathway giant
`n01843`. So some of these areas are a giant plus a handful of neighbours, not a synthesis — the
giant supplies almost all the membership.

## 6. Children per node

**Max 382, median 2.** The 382 is O50s's own maximum, unchanged: it belongs to a giant, and the
giants are in the structure. Nothing here adds a node with more children than O50s already had.

## 7. Placement and Reactome

| | O50s | **with the areas** |
|---|---:|---:|
| summary placement | 2,194 of 2,370 = **92.6%** | **2,352 = 99.2%** (+158) |
| Reactome median best J | 0.273 | **0.273** |

**99.2% is the best placement figure this project has produced**, ahead of arm A's 97.5% and O50s's
92.6%. Only 18 of 2,370 curated summaries now lack a node holding 80% of their leaves.

**Reactome is unchanged at 0.273, to three decimals.** That is now the sixth consecutive attempt at a
top level that leaves this measure exactly where it was — the areas pass, the recursive operator, the
floor change, arm A, A1 and this. It is evidence about the measure.

## 8. Sanity check

**0 nodes are 100% inside another node without being its descendant**, over all 5,724 nodes and
73,067 containment pairs. The build computes it, prints it and **refuses to write anything if it is
non-zero**; `tests/test_areas_on_roots.py` asserts it too. This is the invariant arm A broke
silently, and here it holds by construction because every O50s theme is in the structure.

## 9. What this says

**On the declared numbers this is the strongest top level yet.** 12 roots against 49, held-out FDR
0.00558 against 0.01, placement 99.2%, no small roots, no root pair at J ≥ 0.5, only 14
near-containment pairs with none closer than 6 missing pathways, and a clean containment invariant.

**Three things to weigh against it.**

**One root holds 81% of the universe.** `a_00044` is 4,485 pathways over 92 units with two giants
inside it. Twelve roots is comfortably under the ceiling, but if one of them is nearly everything
then the effective top level is smaller than twelve — and the ceiling was never meant to be met that
way.

**Three strata admitted nothing.** Areas of 3, 4 and 6 units are excluded entirely because no cut
reached the 0.008 target for them, and the surviving floors are high (0.9 and 0.74). The 66 areas are
well supported — median support 0.877 — but they are what a strict gate let through, not a survey of
the possibilities, and a different seed set could move which ones.

**Some areas are a giant plus a few neighbours.** `a_00038` is 2,599 pathways from 14 units, of which
one giant supplies 2,564. Containing a giant and synthesising around one are different achievements,
and the blind reading is what will tell them apart.

**Adopted: nothing.** The remaining gates are the blind reading of the 12 roots, the C6 intruder test
on the 66 areas, and Aviyah.

## For the reviewer

`data/experiments/areas_on_roots_2026-10-18/` — `roots.tsv` (12 rows: id, kind, size, n_children,
full member keys), `small_roots.tsv` (**header only: there are no small roots**), `areas.tsv` (all 66
areas with support, unit ids, which giants each contains, and full member keys). Not judged here.

## Reproducing this

```sh
uv run scripts/areas_on_roots.py     # 76 s, 696 MB
uv run pytest tests/test_areas_on_roots.py
```

Floors on the 20 unit scrambles 3001-3020, checked once on 4002-4005, target 0.008, caps 0.02 per
stratum and 0.01 overall — rec2fix's configuration unchanged. The 25 sides are cached in
`areas_roots_261units_200runs.json`. No API calls.
