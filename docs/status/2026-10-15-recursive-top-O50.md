# The recursive top level on O50: THEMA applied to its own themes. 15 Oct 2026

**EXPLORATORY. Adopts nothing.** Declared before any result (DECISIONS, 15 Oct, prompt copied
verbatim). **One of the four criteria ccode owns fails**, so by the declaration the recursive top is
not accepted for further work as it stands.

| | criterion | result |
|---|---|---|
| | held-out FDR within the caps at level 2 | **FAIL** — overall 0.00882 is inside the 0.01 cap, but **two strata breach the 0.02 per-stratum cap**: 3-3 at **0.03846**, 7-9 at **0.02604** |
| | the top has 20-60 roots | **PASS** — **30** |
| | no node has more than 60 children | **PASS** — max **21** |
| | at least 95% of the 476 giant-only themes get an area parent | **PASS** — **100%** (476 of 476) |
| | C6, blind intruder test | **the reviewer's**, not judged here |
| | the top level is intuitive | **Aviyah's**, not judged here |

## 1. Units — 661

Exactly as the declaration specifies, from the frozen O50 read-only.

| | |
|---|---|
| giants dropped (over 1,000 members) | **4** — 2,332 / 2,018 / 2,015 / 1,412 |
| non-giant roots | **184** (168 of them 50 members or fewer) |
| themes whose only parents are giants | **476** |
| pathways in no non-giant theme, added as their own unit | **1** — `btm:M205` |
| **units** | **661** |

The one loose pathway is `btm:M205`, the same mixed BTM module that was O50's accepted C2 exception.
Unit sizes in pathways: min 1, median 15, max 813; 605 of 661 are 50 or fewer. The units cover all
**5,539** pathways. Each is the normalised mean of its members' L2-normalised rows in
`vectors_leaves_centred`, the mean normalised after — the order the build's own member centroids use.

## 2. Level 2 — 470 nodes, 30 roots

The O50 configuration unchanged: 200 Ward runs on 80% subsamples of units, recurrence matching 0.70
on unit membership, one same-theme cutoff of **0.50** in consensus and the stale pass, the joint
fixed point with chain collapse at 0.85, strict containment. Floors calibrated on **unit** scrambles
(seeds 3001-3010), confirmed once on 4001-4002, solved to a 0.008 target with no 0.33 minimum.

| | |
|---|---|
| candidates | 5,685 |
| after consensus | 556 |
| **after the joint fixed point** | **470** |
| repair | 80 collapsed, 6 merged; 2 joint rounds (4 collapse, 3 merge) |
| **roots** | **30** |
| size in **units** | min 3, median 12, max 251 |
| size in **pathways** | min 20, median 153, max 3,053 |
| multi-parent | 198 of 470 = **42.1%** |
| children per node, areas only | max **14**, median 1 |
| children per node, **combined DAG** | max **21**, median 4 — **0 over 60** |

30 roots is inside 20-60, so **the recursion stopped at one level**; no second pass was run.

"Children" is counted the way a reader browsing the combined DAG would see it: an area's child areas
plus the units it holds and does not reach through a child area. Counting only area-to-area edges
gives 14; counting the units an area holds without subtracting what its children already cover gives
251, which is the number the giants were criticised for. The middle figure, **21**, is the honest one.

### Held-out FDR — the failing criterion

| stratum | floor | calibration FDR | **held-out FDR** | real | cap |
|---|---:|---:|---:|---:|---:|
| 3-3 | 0.915 | 0.00769 | **0.03846** | 13 | 0.02 **breached** |
| 4-4 | **none** | — | — | 0 | 0.02 |
| 5-5 | 0.825 | 0.00526 | 0.0 | 19 | 0.02 |
| 6-6 | 0.595 | 0.00690 | 0.01724 | 29 | 0.02 |
| 7-9 | 0.420 | 0.00729 | **0.02604** | 96 | 0.02 **breached** |
| 10+ | 0.060 | 0.00665 | 0.00707 | 1,203 | 0.02 |
| **overall** | | | **0.00882** | 1,360 | 0.01 ok |

Two things are worth stating rather than averaging away. **Stratum 4-4 has no floor at all**: no cut
reached the 0.008 target, so it admits nothing and contributes no areas. And the two breaches sit on
**13 and 96 real candidates** — at 13, a single false positive in the averaged null is 0.038, so the
measure is coarse there rather than necessarily wrong. That is a reason to re-run calibration with
more scramble seeds, not a reason to read the cap as satisfied. **It is recorded as a failure.**

## 3. The top level — 30 areas

Sizes: min 73, median 408, max 3,053 pathways. **Five of the 30 roots hold more than 1,000
pathways** (3,053 / 2,675 / 2,651 / 1,776 / 1,405), and 19 are 201-1,000, 6 are 200 or fewer. Across
all 470 areas, 16 exceed 1,000 pathways.

So the recursion **does** produce an area layer — 30 roots in place of 4 bags, every unit parented,
no node with more than 21 children — but **the largest areas are themselves bag-sized.** The four
giants were replaced by five large areas plus twenty-five smaller ones, which is a different shape,
not an elimination of the problem.

The full list of 30 roots with their unit counts, pathway counts and ten nearest pathway names each
is in `data/ontology/v0.4-leaves/thema_L_x2_O50_rec/report.txt`. The nearest names are for judging
only and are not labels. The three largest read coherently: `a2_00128` (251 units, 3,053 pathways) is
mesenchyme, collagen and vascular development; `a2_00319` (166, 2,675) is DNA damage, replication
and NF-kB; `a2_00404` (187, 2,651) is the third large bag.

## 4. Coverage

| | |
|---|---|
| **giant-only themes with an area parent** | **476 of 476 = 100%** |
| all units with an area parent | 661 of 661 |
| roots before | **188** (4 giants + 184 non-giant) |
| roots after, combined DAG | **30 areas** — the giants are not joined |

**Per pathway, the largest non-giant theme above it:**

| band | before | after | change |
|---|---:|---:|---:|
| 1-10 | 1 | 0 | −1 |
| 11-50 | 1,096 | 0 | **−1,096** |
| 51-200 | 2,362 | 0 | **−2,362** |
| 201-1,000 | 2,079 | 0 | **−2,079** |
| 1,001+ | 0 | **5,539** | **+5,539** |

The "before" column reproduces the declaration's stated figures exactly (51-200 = 2,362; 11-50 =
1,096; 201-1,000 = 2,079), which is the check that the measurement is the same one.

**The "after" column needs reading carefully, and it is the most important number here.** Every
pathway now has a non-giant ancestor over 1,000 members — but only because the areas themselves are
that large. The declaration's complaint was that for a fifth of pathways nothing above them exceeded
50 members; that is fixed. What replaced it is not a mid-sized area layer but, for most pathways, a
very large one. **A layer at 200-1,000 members is what was wanted and is not what this produces.**

## 5. Gene coherence (report only, not gated)

Level 2, over the 182 areas holding 2-120 pathways: median pairwise gene Jaccard **0.0115** against
**0.0011** for size-matched random draws, **10.2x**. Low in absolute terms, as the declaration
expects at the top, and clearly above random. Larger areas are excluded from the measure because
pairwise Jaccard over thousands of members is both slow and uninformative.

## 6. Agreement with Reactome's top-level pathways (secondary)

All **29** Reactome top-level branches, each matched to its best area by Jaccard on leaves. **Median
best Jaccard 0.100.** The best agreements: Cellular responses to stimuli **0.238** (`a2_00100`),
Signal Transduction **0.217** (`a2_00011`, 282 leaves), Programmed Cell Death **0.214**,
Developmental Biology **0.173**, Extracellular matrix organization **0.164**, Metabolism **0.164**
(234 leaves), Immune System **0.160**, Neuronal System **0.157**. The worst: DNA Replication 0.012,
Digestion and absorption 0.025, Protein localization 0.031.

Two branches map to the same area more than once — `a2_00105` is the best match for Cell Cycle, DNA
Repair and DNA Replication, and `a2_00011` for both Signal Transduction and Disease — so the areas
are coarser than Reactome's top level, not a re-derivation of it. At a median Jaccard of 0.10 this
is agreement in direction only.

## 7. Summary placement (display only, nothing attached)

For every curated summary in the 10,747 universe that is not in L, its leaf descendants in L were
taken by the leaves-experiment closure, and the smallest node holding at least **80%** of them was
found — first in O50 alone, then in the combined DAG. **2,370 summaries have 3 or more leaf
descendants in L.**

| summary size band | n | home in O50 | of those, a giant | home combined | of those, an area |
|---|---:|---:|---:|---:|---:|
| 3-10 | 1,711 | 1,525 | 459 | **1,626** | 570 |
| 11-50 | 560 | 439 | 233 | **495** | 294 |
| 51-200 | 96 | 55 | 36 | **76** | 57 |
| 201+ | 3 | 2 | 2 | 2 | 2 |
| **ALL** | **2,370** | **2,021** | **730** | **2,199** | **923** |

**Share with a home: 85.3% in O50 → 92.8% in the combined DAG**, a gain of **7.5 points**. Of those
homes, 36.1% were a giant in O50; in the combined DAG 42.0% are an area. So the areas **do** give
summaries a home that O50 did not — most visibly in the 51-200 band, where coverage goes from 55 of
96 to **76 of 96** — and the gain is largest exactly where the missing layer was.

That is the strongest result in this report. It is also display-only: **nothing is attached**, and a
summary "having a home" means a node holds 80% of its leaves, not that the node is named for it.

## 8. Cost

| | wall time | peak RAM |
|---|---:|---:|
| units and the timed estimate | 8 s | 0.7 GB |
| level 2 (13 sides, consensus, repair, mapping) | **131 s** | **0.7 GB** |
| the report | 4 s | 0.4 GB |

The estimate given before building was ~4 minutes against 2.2 minutes actual, from one real side
timed at 7.7 s.

## 9. What this says

The recursion gives O50 the area layer it lacked, and the coverage numbers are unambiguous: every
one of the 476 giant-only themes gets an area parent, 188 roots become 30, no node exceeds 21
children, and 7.5 points more curated summaries find a home — concentrated in the 51-200 band that
was missing.

Against that, three things:

1. **The held-out FDR criterion fails.** Two strata breach the 0.02 cap, on 13 and 96 real
   candidates. More scramble seeds would settle whether that is noise at small counts or a real
   excess; until then the declared criterion is not met.
2. **Five of the 30 areas are bag-sized**, up to 3,053 pathways. The shape changed; the bags did not
   go away. The 200-1,000 member layer the declaration wanted is not what came out.
3. **Agreement with Reactome's top level is weak** (median Jaccard 0.100) and several Reactome
   branches share one area, so these are coarser than curated areas rather than a rediscovery of
   them.

**Adopted: nothing.** C6 and the intuitiveness judgement are not ccode's, and by the declaration a
failing C1-style criterion already settles the question for now.

## Reproducing this

```sh
uv run scripts/recursive_top_O50.py --estimate   # units and a timed estimate, no build
uv run scripts/recursive_top_O50.py              # level 2, map back, write the combined DAG
uv run scripts/recursive_top_report.py           # every number above
```
