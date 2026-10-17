# Arm A, strict containment fixed (A1 and A2). 18 Oct 2026

**The bug is real, the fix is one line of assembly, and the root count does not change.** A1 has
**47 roots** — exactly as arm A did — because the five anchors that were wrongly roots are now
children, and the five O50s giants that were missing from the structure become roots in their place.
A bug fix, a report, and it adopts nothing.

| | arm A as built | **A1, strict** | **A2, propagation** |
|---|---:|---:|---:|
| nodes | 1,212 | **6,003** | 6,003 |
| **roots** | 47 | **47** | **41** |
| root composition | 31 areas + 16 anchors | **31 areas + 11 anchors + 5 giants** | 29 + 7 + 5 |
| direct edges | 2,076 | 14,920 | 14,868 |
| children per node, max / median | 51 / 0 | **319** / 2 | 312 / 2 |
| roots 100% inside another node | **5** | **0** | **0** |
| roots ≥80% inside, 1-5 missing | — | 10 | **0** |
| summary placement | 97.5% | **97.5%** | **97.5%** |
| Reactome median best J | 0.273 | **0.273** | **0.273** |
| pathways added | — | 0 | **22** over 6 nodes |

## 1. The cause

Arm A's node set was rec2fix's: the areas, the anchors and the units. **`units_of` excludes a giant
from being a unit by design** — a grab-bag is never a unit — **and rec2fix never re-adds the giants
as parents.** So arm A's 1,212-node structure omitted 4,798 of O50s's 5,658 themes, the five giants
among them, and five anchors that O50s itself places inside a giant came out as roots with no node
in the structure that could possibly be their parent.

The hypothesis in the prompt was right, and the five cases are all the same shape:

| anchor | size | belongs under | giant size |
|---|---:|---|---:|
| `n00225` | 212 | `n01419` | 1,603 |
| `n03971` | 311 | `n01419` | 1,603 |
| `n04999` | 213 | `n01419` | 1,603 |
| `n04528` | 208 | `n01843` | 2,564 |
| `n05000` | 206 | `n03878` | 2,135 |

**The edges were not wrong, they were missing.** All 4,798 omissions were invisible except these
five, because the non-maximal themes sit *below* the units while the giants sit *above* them.

## 2. The fix

**In the arm A assembly only.** The structure is assembled over **every** O50s theme, the five giants
included, plus the 352 surviving areas: **6,003 nodes**. `areas_rec2fix` is not touched — its
defaults, its unit rule and its 14 tests all stand, because the defect is in what arm A hands to the
structure, not in how rec2fix builds areas. `git diff` on `areas_rec2fix.py` is empty for this
prompt.

**One detail that would otherwise have undone prompt 44.** The spec says the node set is "every area,
anchor, O50s giant and O50s theme" **and** that the twin and chain rules stay as they were. Arm A's
rules removed 7 nodes and **all 7 are O50s themes** — `n02019`, `n04530`, `n04674`, `n04676`,
`n04997`, `n05010`, `n05037`. Re-adding "every O50s theme" unqualified would have resurrected them.
They are excluded by name, so the rules keep their outcome, and `tests/test_arm_a_containment.py`
asserts both the arithmetic (6,003 = 5,658 + 352 − 7) and that each victim stays out.

**No reclustering**, as required: the cached areas (`areas_A_848items_200runs.json`) are reused
verbatim.

## 3. Held-out FDR — confirmed unchanged

The floors and the held-out report in A1 and A2 are **byte-identical to arm A's**, and identical to
the cached areas file they came from. The build asserts this before reporting anything and stops if
it fails; the test asserts it too.

| stratum | floor | calib FDR | held-out FDR | real | cap |
|---|---:|---:|---:|---:|---:|
| 3-3 | 0.96 | 0.00714 | 0.0 | 7 | 0.02 |
| 4-4 | 0.945 | 0.00588 | 0.0 | 17 | 0.02 |
| 5-5 | 0.79 | 0.00667 | 0.00833 | 30 | 0.02 |
| 6-6 | 0.52 | 0.00612 | 0.01020 | 49 | 0.02 |
| 7-9 | 0.475 | 0.00745 | 0.00266 | 94 | 0.02 |
| 10+ | 0.055 | 0.00634 | 0.01052 | 1,450 | 0.02 |
| **overall** | | | **0.00987** | | **0.01** |

Unchanged means unchanged, including the 1.3% margin on the overall cap that prompt 44 flagged.

## 4. A1, strict containment at 100%

**47 roots** — the same count as arm A, by a coincidence worth spelling out:

| | |
|---|---|
| roots arm A had that A1 does not | **exactly the five bug cases**: `n00225`, `n03971`, `n04528`, `n04999`, `n05000` |
| roots A1 has that arm A did not | **exactly the five O50s giants**: `n01419`, `n01843`, `n02672`, `n03878`, `n04994` |
| net | **0** |

**So the fix does not reduce the top level; it corrects what the top level is made of.** Five
200-to-311-pathway anchors stop being top-level topics, and five 1,603-to-2,564-pathway grab-bags
start being them. Whether that is an improvement is a judgement, not a number: the structure is now
truthful about containment, and the price is that O50s's giants are back at the top where O50s itself
puts them.

### Where each O50s giant sits now

| giant | size | parents | direct children |
|---|---:|---|---:|
| `n01843` | 2,564 | **root** | 266 |
| `n02672` | 2,172 | **root** | 279 |
| `n03878` | 2,135 | **root** | 284 |
| `n04994` | 2,096 | **root** | 319 |
| `n01419` | 1,603 | **root** | 147 |

**All five are roots**, and none is inside any area. That is the honest answer to the prompt's
question and it is a little deflating: the areas pass never built anything that contains a giant, so
re-admitting the giants adds five top-level nodes rather than slotting them under something.

**19 nodes exceed 1,000 pathways in all — the 5 giants and 14 giant areas — and 12 of the 19 are
roots.** The 7 that are contained are all areas: `b2_00157` (2,133) under `b2_00311`, `b2_00136`
(1,486) under `b2_00116`, `b2_00283` (1,436) under `b2_00157`, `b2_00254` (1,419) under `b2_00330`,
`b2_00326` (1,233) under `b2_00245`, `b2_00232` (1,130) under `b2_00157`, and `b2_00027` (1,072)
under both `b2_00116` and `b2_00345`. So areas do nest inside each other; what none of them does is
contain a giant.

### Children per node

**Max 319, median 2** — against arm A's 51 and 0. The jump is not a new defect: it is O50s's own
shape arriving with its own nodes. `n04994` has 319 direct children because that is roughly what it
has in O50s, whose own maximum is 382. Arm A's 51 was an artefact of the 4,798 missing themes.

### Roots ≥80% inside another node, binned by pathways missing

| missing | A1 | **A2** |
|---|---:|---:|
| **0** | **0** | **0** |
| 1-5 | 10 | **0** |
| 6-20 | 39 | 31 |
| 21+ | 61 | 54 |
| **ordered pairs** | **110** | **85** |

**The 0 bin is empty in A1, which is the regression test.** Before the fix it held 5. The remaining
110 pairs are genuine near-containments with real gaps, not bookkeeping failures — and 100 of the
110 are missing 6 or more pathways, so no rule short of a loose share threshold would absorb them.

## 5. A2, Aviyah's propagation rule (reporting only)

A node at least 98% inside a larger node, missing at most 5 pathways, becomes a child; the missing
pathways go to the parent **and all its ancestors** with evidence score 0.

| | |
|---|---|
| child-parent pairs created | **6** |
| **pathways added** | **22** slots over **6** nodes |
| rounds to a fixed point | 2 — the second found nothing more |
| roots | **41**, down from 47 |
| the 1-5 missing bin | **emptied**, 10 → 0 |

**It does exactly what it was designed to do and nothing more.** Six nodes move, 22 member slots are
invented, and the 1-5 bin clears. The 6-20 and 21+ bins fall only because six roots stopped being
roots (39 → 31, 61 → 54), not because anything else was absorbed.

The six events, with what each was missing:

| child | size | now under | missing | ancestors also given it |
|---|---:|---|---:|---:|
| `n04670` | 618 | `n01843` **giant** | 4 | 0 |
| `n04671` | 434 | `n02672` **giant** | 3 | 0 |
| `b2_00294` | 304 | `b2_00245` | 4 | 0 |
| `n04995` | 262 | `n03878` **giant** | 3 | 0 |
| `b2_00320` | 249 | `b2_00311` | 4 | 0 |
| `n05001` | 209 | `n04994` **giant** | 4 | 0 |

**Four of the six put an anchor under an O50s giant**, and every parent was itself a root, so the
"all its ancestors" clause never fired: all 22 slots went to the six parents directly. The rule as
written would propagate up a chain; here there were no chains to climb.

I iterated to a fixed point rather than running one pass, because adding members can create a fresh
near-containment; the second round found none, so a single pass would have given the same answer
here. The rounds are reported rather than assumed.

**The 22 invented members are in `A2/propagated_members.tsv`**, every one at inclusion 0.0, and the
test asserts that. They are the whole reason A2 is reporting-only: six roots are removed by **writing
22 pathway memberships that no run ever voted for**. At this scale it is cheap — 22 slots against a
5,539-pathway universe — and it is still a different kind of object from a recurrence-backed
membership.

## 6. Placement and Reactome

| | O50s | **A1** | **A2** |
|---|---:|---:|---:|
| summary placement | 2,194 = 92.6% | **2,310 = 97.5%** | **2,310 = 97.5%** |
| Reactome median best J | 0.273 | **0.273** | **0.273** |

**Both unchanged from arm A, and one of them needs reconciling with prompt 44.** That note reported
arm A's Reactome agreement as "view 0.162, full pool 0.273" — the 0.162 was the *view alone*, 1,212
nodes, which was the only pool arm A's structure offered. A1's structure **is** the full pool, so
0.273 is the figure that applies, and the 0.162 was an artefact of the same omission this prompt
fixes. **The areas still do not improve on O50s's 0.273, but they no longer appear to make it worse.**

Placement is identical in all three columns because it was already measured against "every O50s theme
plus arm A's areas", which is now what the structure contains.

## 7. What this says

**The bug was real and is fixed.** No root in A1 is wholly inside another node; the five named
anchors sit under the giants O50s puts them under; and the containment relation is now complete over
a 6,003-node structure rather than a 1,212-node slice of it.

**It does not make arm A's top level smaller.** 47 before, 47 after. What changed is the membership
of the top: five mid-sized anchors out, five grab-bags in. If the goal is "fewer than 49
thematically coherent roots", A1 still meets the count and the coherence question just got harder,
because **five of its 47 roots are now O50s's giants** — the nodes this project has repeatedly
described as grab-bags, one of which (`n04994`) was flagged in prompt 43 as a brand-new 2,096-pathway
theme no declared check had read.

**A2 buys six roots for 22 invented memberships.** 41 roots is comfortably inside the target, and
the cost is small and fully recorded. It remains reporting-only by declaration, and the question it
raises is whether a hierarchy may assert memberships no resampling supports — which is a design
decision, not a measurement.

**Nothing in the reviewer's pending work changes.** The 47 roots in `A1/roots.tsv` are not the same
47 as `A/roots.tsv`: ten differ. If the blind reading has already started on `A/roots.tsv`, five of
its items are no longer roots and five new ones have appeared.

## For the reviewer

`data/experiments/top_two_arms_2026-10-17/A1/roots.tsv` — 47 rows, same format as `A/roots.tsv`
(id, kind, size, n_children, full member keys). **Five rows differ from `A/roots.tsv` in each
direction**, as above. Not judged here.

## Reproducing this

```sh
uv run scripts/arm_a_containment.py      # 13 s, 540 MB
uv run pytest tests/test_arm_a_containment.py
```

No reclustering, no API calls. The cached areas are reused and the floors are asserted identical to
arm A's before anything is reported.
