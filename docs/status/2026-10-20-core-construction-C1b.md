# C1b, the core-based construction: ANSWERED NO, 20 Oct 2026

Prompt 50 asked whether a core-based algorithm beats O50s. It does not, and the declared decision
rule settles it without the readings: **criterion 2 fails on the machine-checkable half.** C1b has
**1,066 roots against O50s's 261**, where the rule requires fewer than 261.

Build: `data/ontology/v0.4-leaves/thema_L_x2_C1b/`. Nothing is adopted. O50s stands.

**The build is dominated by one degenerate parameter, and that is the finding worth keeping.** The
20 Oct amendment removed the minimum copy count for a core, so a grouping seen once has every
member at inclusion 1.0 and therefore **no extras by construction**. Scrambled groupings of 40+
pathways almost never recur, so they are nearly all one-copy, so the null extras count is literally
**0.00 from 40 pathways up**. `N(p)/R(p)` is then 0 at every cut and step 5 selects the lowest `p`
on offer, 0.10, for every stratum from 20 upward. Members become core plus nearly every extra. The
rule-of-three substitution is declared for the floors (step 8) but **not** for `p` (step 5), so an
observed zero is taken at face value.

So C1b as specified is a fair test of *this specification* and weak evidence about the core *idea*.
Reported here as measured; the rule change is Aviyah's call.

## The declared decision rule

| # | criterion | required | C1b | verdict |
|---|---|---|---|---|
| 1 | held-out FDR within caps | overall <= 0.01, stratum <= 0.02 | 0.00504, worst 0.00894 | **PASS** |
| 2 | fewer roots, and fewer small roots | < 261 roots AND < 164 of <= 50 | **1,066** roots; 50 small | **FAIL** |
| 3 | roots read coherent or umbrella | >= 78.9% | reviewer | pending |
| 4 | non-root themes vs O50s in pool | within 5 points | reviewer | pending |
| 5 | placement and Reactome | >= 90% and J >= 0.25 | 99.9%, 0.286 | **PASS** |

Criterion 2 is decisive: the readings cannot rescue it. Criterion 5 passes but means little here --
with a mean of 448.5 themes per pathway, being placed *somewhere* is close to guaranteed.

## 1. Copies, p and the floors

Copies per final theme by band. The amendment asked for this distribution, and it is the clearest
statement of how thin the large themes are: the median large theme rests on **three copies**.

| band | themes | 1 | 2 | 3-9 | 10+ | median |
|---|---:|---:|---:|---:|---:|---:|
| 3-9 | 28,975 | 0 | 0 | 1,863 | 27,112 | 36 |
| 10-19 | 27,053 | 0 | 153 | 8,143 | 18,757 | 20 |
| 20-49 | 8,391 | 0 | 3,450 | 2,529 | 2,412 | **3** |
| 50-199 | 7,126 | 0 | 3,340 | 3,088 | 698 | **3** |
| 200+ | 1,939 | 0 | 885 | 958 | 96 | **3** |
| ALL | 73,484 | 0 | 7,828 | 16,581 | 49,075 | 20 |

This is the same wall that withdrew prompt 49's Part B. Prompt 50's fix -- matching copies at
prompt 47's per-stratum thresholds -- raised the copy counts below 20 pathways but not above:
mid and large groupings still recur about three times in 200 runs.

The p table, floors and FDR per stratum:

| stratum | p | real extras | null mean | ratio | floor | real kept | calib FDR | held-out |
|---|---|---:|---:|---|---|---:|---|---|
| 3-3 | 0.9 | 541 | 75.10 | - | 0.540404 | 578 | 0.00778547 | 0.00894 |
| 4-4 | 0.9 | 2,801 | 1033.70 | - | 0.496689 | 1,290 | 0.00775194 | 0.00879 |
| 5-5 | 0.9 | 4,312 | 524.70 | - | 0.140244 | 4,558 | 0.00774462 | 0.00826 |
| 6-6 | 0.9 | 4,837 | 1224.00 | - | 0.085106 | 5,641 | 0.00762276 | 0.00801 |
| 7-9 | 0.9 | 13,276 | 1141.00 | - | 0.035088 | 16,910 | 0.00621526 | 0.00655 |
| 10-19 | 0.9 | 54,690 | 1634.50 | - | 0.01005 | 27,053 | 0.00534876 | 0.00558 |
| 20-39 | **0.1** | 608,270 | 36.90 | 6.1e-05 | 0.01 | 6,471 | 0.00114356 | 0.00137 |
| 40-79 | **0.1** | 588,725 | **0.00** | 0.0 | 0.01 | 5,263 | 5.7e-05 | 0.0 |
| 80-159 | **0.1** | 281,416 | **0.00** | 0.0 | 0.01 | 3,144 | 9.542e-05 | 0.0 |
| 160-319 | **0.1** | 248,695 | **0.00** | 0.0 | 0.01 | 1,458 | 0.00020576 | 0.0 |
| 320-639 | **0.1** | 653,453 | **0.00** | 0.0 | 0.01 | 689 | 0.00043541 | 0.0 |
| 640-1279 | **0.1** | 1,261,432 | **0.00** | 0.0 | 0.01 | 311 | 0.00096463 | 0.0 |
| 1280+ | **0.1** | 903,993 | **0.00** | 0.0 | 0.01 | 120 | 0.0025 | 0.0 |

A `p` of 0.9 means no cut qualified and members are the core alone; a `p` of 0.1 means the null
showed zero extras and nearly every extra is admitted. No stratum chose anything in between.

**OVERALL held-out 0.00504 (cap 0.01), worst stratum 0.00894 (cap 0.02) -- inside both.**
Pipeline: 264,897 groupings -> 155,939 families -> 154,475 themes before the gate -> **73,484 after**.

## 2. Themes by size band, and the core share

| band | O50s | C1b | change | core share |
|---|---:|---:|---:|---:|
| 3-5 | 524 | 6,425 | +5,901 | 1.000 |
| 6-11 | 1,908 | 32,015 | +30,107 | 1.000 |
| 12-24 | 1,804 | 21,054 | +19,250 | 1.000 |
| 25-49 | 1,059 | 4,925 | +3,866 | 0.750 |
| 50-99 | 267 | 4,454 | +4,187 | 0.636 |
| 100-199 | 67 | 2,672 | +2,605 | 0.613 |
| 200-399 | 19 | 1,045 | +1,026 | 0.622 |
| 400-799 | 2 | 628 | +626 | 0.598 |
| 800-1599 | 3 | 196 | +193 | 0.464 |
| 1600+ | 5 | 70 | +65 | 0.426 |
| TOTAL | 5,658 | 73,484 | +67,826 | |

The core share is where `p = 0.1` shows itself: in the largest band **57% of members are extras**
admitted because the null happened to show none. Below 25 pathways the share is 1.000, which is the
other degeneracy -- there `p = 0.9` and members are exactly the core.

## 3. Shape

| | O50s | C1b |
|---|---:|---:|
| themes | 5,658 | 73,484 |
| roots | 261 | 1,066 |
| roots of 50 or fewer | 164 | 50 |
| children, max | 382 | 4,565 |
| children, median | 2.0 | 3.0 |
| multi-parent share | 0.6329 | 0.958 |
| mean themes per pathway | 23.3 | 448.53 |
| levels to a root, median | 6.0 | 13.0 |
| levels to a root, max | 11 | 28 |
| giants over 1,280 | 5 | **119** |
| edges | - | 1,362,498 |

**Giants are much worse: 119 against 5.** The largest is `n01846` at 4,451 pathways on a core of
1,061. One, `n12995`, holds 3,816 pathways on a core of **4** -- the clearest single illustration of
what `p = 0.1` does.

C1b's twelve largest: n01846 4,451 (core 1,061), n26177 4,102 (546), n12995 3,816 (**4**),
n50459 3,719 (770), n42575 3,334 (497), n53337 3,227 (932), n54794 3,103 (1,008), n00828 2,858 (844),
n05748 2,664 (549), n50460 2,581 (659), n56843 2,580 (844), n54795 2,547 (1,090).

The one axis where C1b wins is small roots: **50 against 164**. It does so by having four times as
many roots overall, so this is not the fix prompt 47 was looking for either.

## 4. What the dropped steps would act on (reported, not a gate)

Step 9 took strict containment only -- no consensus merge, no chain collapse, no repair. What those
would have found:

- parent-child pairs where the child holds at least 85% of the parent: **42,554**
  (distinct children, which chain collapse would remove: **25,509**, a third of the build)
- non-nested theme pairs at J >= 0.5 left unmerged: **1,430,335**

| band | unmerged pairs at J >= 0.5 |
|---|---:|
| 3-5 | 8,742 |
| 6-11 | 435,131 |
| 12-24 | 725,198 |
| 25-49 | 48,659 |
| 50-99 | 61,748 |
| 100-199 | 54,799 |
| 200-399 | 43,154 |
| 400-799 | 41,108 |
| 800-1599 | 10,387 |
| 1600+ | 1,409 |

1.43 million near-duplicate pairs is not a redundancy that a post-pass tidies; it says the mutual
core rule did not do the merging job that O50s's same-theme cutoff does.

## 5. O50s counterparts

- O50s themes with a C1b counterpart at **J >= 0.9: 2,310 of 5,658 = 40.8%**. C1b does not contain
  O50s; it is a different decomposition, not a refinement of one.
- Of the 164 O50s small roots, **83 have a counterpart at J >= 0.70 (50.6%)**, and of those only
  **4 are still roots (4.8%)**.

The eight named roots:

| O50s root | size | C1b counterpart | J | still a root |
|---|---:|---|---:|---|
| n01027 | 923 | n54828 | 0.814 | yes |
| n04526 | 820 | n65874 | 0.805 | yes |
| n04670 | 618 | n56935 | 0.834 | no |
| n04671 | 434 | n66196 | 0.849 | yes |
| n03316 | 386 | n56996 | 0.811 | no |
| n04672 | 348 | n66192 | 0.683 | no |
| n04995 | 262 | n66602 | 0.836 | no |
| n05001 | 209 | n66692 | 0.774 | no |

## 6. Placement and Reactome

| | O50s | C1b |
|---|---|---|
| summary placement | 2,194 of 2,370 = 92.6% | 2,367 of 2,370 = **99.9%** |
| Reactome median best J | 0.273 | **0.286** |

Both improve, and both are nearly uninformative at this density: with 448.5 themes per pathway a
summary is almost certain to find some theme that contains it. Criterion 5 passes on the letter.

## Reviewer material

`data/experiments/core_construction_C1b_2026-10-20/`:

- **R**: 300 roots (a random 300 of 1,066, seed 20261020) in **75 batches** in `read_roots/`
- **T**: 227 non-root themes, 24 per band per build where available, pooled and shuffled, in
  **8 batches** in `read_themes/`. Short band: O50s 200+ had only 11 available, all taken.
- `roots.tsv`, `themes.tsv`, `p_table.tsv`, and `KEY_DO_NOT_SHARE_C1b.json`, written once and
  never read again by this session. Nothing is judged here.

Criterion 2 already fails, so the readings are no longer decisive for the prompt-50 question. They
are still worth having as a calibration of what a `p = 0.1` theme reads like.

## Cost, and what a re-run costs

| stage | time | peak |
|---|---|---|
| phase 1, eleven inclusion sides | cached from earlier | - |
| solving p | ~150 s | **15.3 GB** |
| one theme side | ~330 s | 4.0-4.6 GB |
| seventeen theme sides | ~95 min | - |
| gate, edges and export | 303 s | 3.7 GB |
| report | 190 s | 0.9 GB |

**A change to the `p` rule costs about 100 minutes, not minutes.** `themes_of_side` recomputes
matching from the trees and applies `p` inside that pass, so every one of the seventeen theme sides
must be rebuilt. The phase-1 `sides/` caches are `p`-independent but are only used to solve `p`.

Two caches were added because this build was killed three times:

- `--only SIDE` builds exactly one theme side and stops, so a kill costs one side rather than
  seventeen.
- `p_table.json` is reused if present. Solving `p` holds eleven sides' inclusion at once and peaks
  at 15.3 GB, and it is deterministic in those caches, so it is paid once. Delete the file to
  re-solve.

**The three kills were one bug, in the caching patch, not in the method.** `handle["keys"][a:b]`
inside a comprehension decompresses the whole array on every iteration, and each slice pins its own
copy alive as its base -- 0.6 GB of members became an 18 GB peak. Hoisting the arrays out took the
peak to 4.5 GB. The arrays were correct throughout, so nothing in the output pointed at it; the
cause was found by measuring peak RSS rather than reasoning about it.
`test_no_npz_handle_is_subscripted_inside_a_comprehension` is an AST walk over the script, and
`test_the_guard_fails_on_the_code_that_caused_the_kill` proves the guard fires on the verbatim
pre-fix expression -- a first attempt with a regex did **not**, because the offending expression
nests brackets. A sweep of `src/` and `scripts/` found no other instance.

## Verdict

**C1b is not better than O50s.** Criterion 2 fails by a factor of four on roots, criterion 1 and 5
pass, and criteria 3 and 4 are no longer decisive. O50s stays the working version.

What the build does establish, and what is worth carrying forward:

1. **Mid and large groupings recur about three times in 200 runs**, even with prompt 47's loosened
   per-stratum thresholds. Any method that needs several copies of a large group to estimate
   anything is building on three observations.
2. **Step 5's `p` rule has no guard against an observed zero in the null.** The floors have the
   rule-of-three for exactly this case. Adding it to `p` is a one-line change to a declared rule and
   is Aviyah's call; it would cost ~100 min to rebuild.
3. **The mutual core rule does not merge.** 1.43 million unmerged pairs at J >= 0.5 against O50s's
   same-theme cutoff doing that work inside the build.
