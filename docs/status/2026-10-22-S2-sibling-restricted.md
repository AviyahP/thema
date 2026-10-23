# S2: O50s with the same-theme merge restricted to siblings, 22 Oct 2026

Prompt 54, amended the same day before building. Exploratory; nothing is adopted. The design is
Aviyah's. Sections C, F, G and the reviewer material are not run, as the prompt says.

**The answer, in one line: restricting the same-theme merge to siblings costs almost nothing. S1's
root explosion was caused by removing inheritance, not by the sibling restriction.**

| | O50s | **S2** | S1p |
|---|---:|---:|---:|
| themes | 5,658 | **5,646** | 5,815 |
| **roots** | **261** | **270** | **991** |
| roots of 50 or fewer | 164 | **174** | 754 |
| giants over 1,280 | 5 | **5** | 9 |
| levels to a root, median | 6.0 | **6.0** | 4.0 |

S1 changed two things at once and could not separate them. S2 changes one: inheritance stays
exactly as it is, and only consensus rule 3 and the stale merge are restricted to siblings. The
result sits on top of O50s -- 12 fewer themes, 9 more roots, the same five giants, the same median
depth of 6 -- where S1p, which removed inheritance, has nearly four times the roots and loses two
levels. **Inheritance is what holds the hierarchy together.**

## Both declared tests pass

1. **With the restriction switched off, the code reproduces frozen O50s byte for byte.** Consensus
   26,120 -> 6,589 (19,531 superseded), joint fixed point 6,589 -> 5,658 (765 collapsed, 166 stale
   merged), and `nodes.tsv`, `members.tsv`, `edges.tsv` and `unplaced.tsv` all identical to
   `data/ontology/frozen/working-O50s-2026-10-22/`.
2. **On fixtures, the restricted rule 3 never supersedes a non-sibling pair, and rule 2 still fires
   on non-sibling pairs** -- checked in both the vectorised and the reference implementation, and
   with a control that the same fixture *is* superseded when unrestricted.

The gated input is checked directly too: the 26,120 themes rebuilt from the cached x2 real side and
O50s's stored floors are **identical to prompt 52's logged gate**, supports included.

**One invariant had to change, and it is worth stating plainly.** `repair.assert_no_stale_pair`
refuses any build in which a stale pair survives. Under the restriction a surviving **non-sibling**
stale pair is the intended outcome -- that is the entire content of the change -- so the unrestricted
invariant rejected exactly the build the restriction is meant to produce (413 pairs, on the first
attempt). The assertion now takes the restriction and checks only the pairs the rule was allowed to
act on. The unrestricted form is untouched, which test 1 is the proof of.

## A. Construction

| | O50s | S2 | S1p |
|---|---:|---:|---:|
| gated themes (input) | 26,120 | 26,120 | 26,120 |
| members inherited, post-consensus population | 23,007 | **39,269** | 0 (no consensus) |
| themes that grew, post-consensus population | 3,691 | **5,483** | 0 |
| members inherited, final-surviving population | 11,932 | **14,447** | 0 |
| themes that grew, final-surviving population | 2,873 | **2,893** | 0 |
| supersessions (consensus rule 3) | 19,531 | **17,513** | n/a (removed) |
| of O50s's 19,531, became coexist | - | **2,018** | - |
| after consensus | 6,589 | 8,607 | n/a |
| chain collapses | 765 | 1,037 | 1,720 |
| stale merges / sibling drops | 166 | **1,924** | 18,585 |
| repair rounds | 2 | 5 | 5 (whole loop) |
| **final themes** | **5,658** | **5,646** | 5,815 |
| held-out FDR overall | 0.00233 | 0.00233 | 0.00233 |

The gate is untouched -- all three carry the same floors, checked mechanically -- so the FDR is
unchanged by construction.

**Only 2,018 of O50s's 19,531 supersessions were between non-siblings and became coexist.** That is
10.3%, and it is the number the whole restructure turns on. Prompt 52 found that 54% of consensus's
merges joined pairs that end up neither siblings nor nested **in the finished DAG** -- but judged
against the DAG of the *gated* themes, which is the DAG that exists when consensus runs, nearly nine
in ten of those pairs already share a parent. The two measurements are not in conflict: they are
taken against different DAGs, and the second is the one consensus could in principle have consulted.

**Which population an inheritance figure is counted over matters, and both are given above.**
Consensus accepts 6,589 themes in O50s and 8,607 in S2; repair then drops 931 and 2,961 of them.
The post-consensus row counts every theme consensus accepted; the final-surviving row counts only
those still standing at the end. The gap is entirely the dropped themes: 11,075 of O50s's 23,007
inherited members sat in the 931 themes repair removed, and 818 of those 931 had grown; for S2,
24,822 of 39,269 sat in the 2,961 removed, 2,590 of them grown. Section B's edge figures below are
on the **final-surviving** definition, because an edge can only rest on a member of a surviving
node. A third quantity, not used here, is the raw event count -- every member addition to any
candidate during consensus, including candidates later superseded and including propagation to
ancestors: **73,354 for O50s** (71,351 direct, 2,003 propagated) and **101,851 for S2** (97,465
direct, 4,386 propagated). It is far larger than either row above because most of those additions
went into candidates that never became nodes.

**What the restriction mostly does is convert supersession into inheritance and then into repair
work.** Inheritance rises from 23,007 members to 39,269 and from 3,691 themes to 5,483; consensus
leaves 8,607 themes instead of 6,589; and repair then does far more -- 1,037 collapses against 765,
and 1,924 stale merges against 166, over 5 rounds instead of 2. The pairs rule 3 declines do not
survive as separate themes; they are absorbed a little later by a different rule.

## B. Shape

| band | O50s | S2 | S1p | S2-O50s | S1p-O50s |
|---|---:|---:|---:|---:|---:|
| 3-5 | 524 | 524 | 518 | +0 | -6 |
| 6-11 | 1,908 | 1,939 | 1,863 | +31 | -45 |
| 12-24 | 1,804 | 1,786 | 1,882 | -18 | +78 |
| 25-49 | 1,059 | 1,022 | 1,132 | -37 | +73 |
| 50-99 | 267 | 278 | 310 | +11 | +43 |
| 100-199 | 67 | 64 | 79 | -3 | +12 |
| 200-399 | 19 | 21 | 13 | +2 | -6 |
| 400-799 | 2 | 4 | 7 | +2 | +5 |
| 800-1599 | 3 | 3 | 5 | +0 | +2 |
| 1600+ | 5 | 5 | 6 | +0 | +1 |
| **TOTAL** | **5,658** | **5,646** | **5,815** | **-12** | **+157** |

| | O50s | S2 | S1p |
|---|---:|---:|---:|
| themes | 5,658 | 5,646 | 5,815 |
| roots | 261 | **270** | 991 |
| roots of 50 or fewer | 164 | **174** | 754 |
| giants over 1,280 | 5 | 5 | 9 |
| children per node, max | 382 | 371 | 554 |
| children per node, median | 2.0 | 2.0 | 1.0 |
| multi-parent share | 0.6329 | 0.6373 | 0.6169 |
| mean themes per pathway | 23.30 | 23.50 | 26.44 |
| levels to a root, median | 6.0 | 6.0 | 4.0 |
| levels to a root, max | 11 | 11 | 9 |
| edges | 12,555 | 12,442 | 15,607 |
| **edges resting on inherited members** | **6,928 (55.2%)** | **6,961 (55.9%)** | **0 (0.0%)** |

Giants, with members gained by inheritance. O50s: `n01843` 2,564 (+367), `n02672` 2,172 (+268),
`n03878` 2,135 (+207), `n04994` 2,096 (+101), `n01419` 1,603 (+300). S2: `n01849` 2,617 (+420),
`n02711` 2,235 (+331), `n03966` 2,207 (+279), `n05067` 2,119 (+124), `n01416` 1,628 (+325).

**The same five giants, each slightly larger and each having inherited more.** S2's dependence on
inheritance is marginally higher than O50s's (55.9% against 55.2%), not lower -- restricting the
merge did not reduce the structure's reliance on manufactured edges, it increased it slightly. On
the final-surviving definition S2 also inherits **more** in absolute terms, 14,447 members against
11,932, into almost the same number of themes (2,893 against 2,873).

## D. The 76 parents consensus superseded

| | O50s | S2 | S1p |
|---|---:|---:|---:|
| present at J >= 0.9 | 0 (by definition) | **1** | **3** |
| share of the 76 | 0.0% | 1.3% | 3.9% |
| O50s roots those survivors contain | 0 | 1 | 3 |
| of the 74 roots the 76 cover | 0.0% | 1.4% | 4.1% |
| median best Jaccard | 0.633 | 0.644 | 0.708 |
| max best Jaccard | 0.817 | 1.000 | 1.000 |

**Neither restructure brings the parents back: 1 of 76 in S2, 3 of 76 in S1p.** This is the second
time this has come out negative, and it closes the hypothesis the two restructures were built on.
The parents are not held out by the same-theme rule specifically -- remove it and they are absorbed
by chain collapse or the stale merge instead. Median best Jaccard barely moves (0.633 to 0.644), so
S2 does not even get closer to representing them than O50s does.

## E. Agreement and placement

O50s themes with a counterpart at J >= 0.9:

| band | O50s themes | S2 | S1p |
|---|---:|---:|---:|
| 3-5 | 524 | 524 (100.0%) | 517 (98.7%) |
| 6-11 | 1,908 | 1,884 (98.7%) | 1,513 (79.3%) |
| 12-24 | 1,804 | 1,503 (83.3%) | 880 (48.8%) |
| 25-49 | 1,059 | 670 (63.3%) | 290 (27.4%) |
| 50-99 | 267 | 149 (55.8%) | 63 (23.6%) |
| 100-199 | 67 | 37 (55.2%) | 13 (19.4%) |
| 200-399 | 19 | 17 (89.5%) | 3 (15.8%) |
| 400-799 | 2 | 2 (100.0%) | 1 (50.0%) |
| 800-1599 | 3 | 3 (100.0%) | 1 (33.3%) |
| 1600+ | 5 | 5 (100.0%) | 2 (40.0%) |
| **ALL** | **5,658** | **4,794 (84.7%)** | **3,283 (58.0%)** |

| | O50s | S2 | S1p |
|---|---|---|---|
| summary placement at 80% (of 2,370) | 2,194 (92.6%) | **2,204 (93.0%)** | 2,187 (92.3%) |
| Reactome branches compared | 29 of 29 | 29 of 29 | 29 of 29 |
| Reactome median best Jaccard | 0.273 | **0.273** | 0.250 |

Placement and the Reactome figure reuse `scripts/o50s_report.py`'s machinery -- the same `targets`
leaf sets, the same 80% home rule, the same branches -- and reproduce O50s's own published 92.6% and
0.273 exactly, which is what makes the S2 column comparable.

**The aggregate agreement of 84.7% hides where S2 actually differs.** The small bands are
near-identical (100% at 3-5, 98.7% at 6-11) and the large bands match outright, but the **middle
falls to 55-63% in the 25-199 range**. So S2 is not a cosmetic variation on O50s: it has the same
count, the same roots and the same depth, and a materially different mid-size composition. That is
the part a reading would have to judge, and it is not judged here.

## What this settles, and what it does not

1. **The two variables are now separated, which was the point.** The sibling restriction alone:
   261 -> 270 roots. Removing inheritance as well: 991. **The root count is an inheritance effect.**
2. **The 54% figure from prompt 52 needs its DAG stated.** Against the finished DAG, 54% of
   consensus's merges are non-sibling. Against the DAG of the gated themes -- the one that exists
   when consensus runs -- only 10.3% are. Prompt 52's number is still correct about the outcome;
   it is not a measure of what consensus could have known.
3. **Restricting the merge does not reduce the reliance on inheritance** (55.2% -> 55.9% of edges,
   and 11,932 -> 14,447 inherited members among surviving themes)
   and does not recover the superseded parents (1 of 76). On its own motivation, S2 does not
   deliver; what it delivers instead is a build that is O50s-shaped with a relationship-aware merge
   rule and a different middle.
4. **Not measured:** duplication (C), stability (F), gene coherence (G), and no theme has been read.
   Whether S2's different middle is better or worse than O50s's is exactly what is not known here.

**Nothing is adopted.**

## Outputs

| what | where |
|---|---|
| S2 build | `data/ontology/v0.4-leaves/thema_L_x2_S2/` |
| construction record | `data/ontology/v0.4-leaves/thema_L_x2_S2/s2_construction.json` |
| this note | `docs/status/2026-10-22-S2-sibling-restricted.md` |

```sh
uv run scripts/build_s2.py --check     # the two declared tests
uv run scripts/build_s2.py             # the build
uv run scripts/s2_report.py            # sections A, B, D, E
```
