# Merge by core, arms CI and CT. 23 Oct 2026

Prompt 58. Exploratory; **no ontology is built** -- this runs as far as the merge and stops -- and
nothing is adopted.

**The answer to the prompt's own question is no: comparing versions on their cores does not remove
the near-copies.** CT, the arm closest to O50s, lands on 98,817 themes against O50s's 99,951
families -- almost the same count from an entirely different comparison -- and has **more**
near-copies, not fewer: 1,063,235 non-nested pairs at J >= 0.5 against O50s's 823,931, and
essentially the same number of inheritance triggers (5,296,155 against 5,308,972). CI, the strict
arm, is much worse on every count.

So the wobbly borders were not what made the near-copies. Cores wobble too.

## Method notes, and two things worth knowing before the tables

**The ordering is O50s's, and deliberately not the core's.** Seeds are taken in support descending,
then the grouping's own **completed-set** size descending, then that set's bitset key -- exactly as
`recurrent.families` ranks. Only the merge *test* moved to the core. This is why the arms are not
simply `families(candidates, cores, ...)`: that call derives rank and comparison from the same set,
so passing cores would have changed which grouping seeds each theme as well. The shortlist keeping
CT off all-pairs is still the repo's own `_variant_shortlist`, built on cores, because it is
documented as a superset of the rule rather than a filter on it. `is_variant` is imported unchanged.

**Step 4's pooling is not O50s's.** `family_members` unions every copy a run holds of any family
member; this prompt specifies *the copy of the highest-support grouping found in that run*, and that
is what was implemented. The origin convention is kept from O50s: a grouping's own run contributes
the grouping's own bitset when that run has no matched copy.

## A. Counts

| | |
|---|---:|
| groupings at J >= 0.70 (s1) | 270,570 |
| eligible to score | 264,897 |
| **without a core of 3+ pathways** | **331** |

The 331 without a core are all small: 180 in the 3-5 band and 151 in 6-11, by their completed-set
size. **Effectively every grouping has a core**, so the no-core rule removes nothing of substance.

| | CI | CT | O50s s2 | s3 | s4 | s5 |
|---|---:|---:|---:|---:|---:|---:|
| themes | **183,091** | **98,817** | 99,951 | 26,120 | 6,589 | 5,658 |

Groupings per theme: **median 1.0 in both arms**, maximum 197 (CI) and 291 (CT). The median tells
the story -- most themes absorb nothing at all.

| band | CI | CT | O50s s2 | s5 |
|---|---:|---:|---:|---:|
| 3-5 | 15,870 | 2,660 | 3,362 | 524 |
| 6-11 | 50,269 | 13,328 | 15,873 | 1,908 |
| 12-24 | 53,442 | 29,533 | 29,709 | 1,804 |
| 25-49 | 32,412 | 25,602 | 24,223 | 1,059 |
| 50-99 | 16,740 | 14,512 | 13,867 | 267 |
| 100-199 | 7,879 | 7,500 | 7,395 | 67 |
| 200-399 | 3,620 | 3,582 | 3,553 | 19 |
| 400-799 | 1,695 | 1,426 | 1,395 | 2 |
| 800-1599 | 795 | 558 | 488 | 3 |
| 1600+ | 369 | 116 | 86 | 5 |
| **TOTAL** | **183,091** | **98,817** | **99,951** | **5,658** |

**CT tracks O50s's s2 band for band**, within a few per cent above 12 members; it differs mainly by
holding fewer very small themes (2,660 against 3,362 at 3-5) and more very large ones (116 against
86 at 1,600+). CI inflates every band, most of all the small ones.

Core size as a share of members, median by band:

| band | CI | CT |
|---|---:|---:|
| 3-5 | 1.000 | 0.800 |
| 6-11 | 0.833 | 0.882 |
| 12-24 | 0.846 | 1.000 |
| 25-49 | 0.919 | 1.000 |
| 50-99 to 400-799 | 1.000 | 1.000 |
| 800-1599 | 0.795 | 1.000 |
| 1600+ | **0.697** | **0.736** |

**For most themes the core IS the membership** -- a median share of 1.000 from 12 members (CT) or 50
(CI) up to 799. The core only becomes a genuinely smaller object in the giants, where it is about
70% of the members. That is the measurement behind the headline: if the core and the full set are
the same object for most themes, comparing on cores cannot behave very differently from comparing on
full sets.

## B. Support

Median support, and the share at or above each threshold:

| band | CI med | CT med | s2 med | CI >=0.05 | CT >=0.05 | s2 >=0.05 | CI >=0.33 | CT >=0.33 | s2 >=0.33 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3-5 | 0.0654 | 0.2450 | 0.1156 | 55.3% | 65.0% | 59.0% | 16.9% | 47.3% | 38.7% |
| 6-11 | 0.0603 | 0.0150 | 0.0200 | 55.3% | 29.2% | 31.8% | 11.8% | 9.8% | 9.3% |
| 12-24 | 0.0202 | 0.0100 | 0.0100 | 34.6% | 15.0% | 13.6% | 4.9% | 3.0% | 2.4% |
| 25-49 | 0.0100 | 0.0050 | 0.0050 | 18.2% | 8.3% | 6.3% | 1.8% | 0.9% | 0.8% |
| 50-99 | 0.0050 | 0.0050 | 0.0050 | 9.3% | 3.4% | 2.2% | 1.0% | 0.3% | 0.3% |
| 100-199 | 0.0050 | 0.0050 | 0.0050 | 3.0% | 0.5% | 0.4% | 0.1% | 0.1% | 0.0% |
| 1600+ | 0.1300 | 0.0200 | 0.0150 | 68.0% | 28.4% | 24.4% | 0.3% | 2.6% | 4.7% |

**CT's support distribution is close to s2's throughout** -- the two are within a few points in
almost every cell, which is what one expects of two different merge rules landing on nearly the same
number of themes. **CI's is higher in the middle bands** but that is an artefact of splitting: it
makes many more, smaller-evidence themes and each keeps whatever support its own grouping had rather
than pooling.

The 400-799 and 800-1599 rows are omitted above for width; CI reaches 16.0% and 31.8% at >= 0.05
there against CT's 1.5% and 9.9%.

## C. Near-copies -- the thing consensus and repair exist to fix

Counted **exactly**, by chunked sparse products of the theme-by-pathway matrix with its transpose.
**Every figure is verified against an explicit double loop** on a random sample of 2,000 themes
(seed 20261023) and **every count matched exactly, in all seven runs.**

| set | themes | non-nested J >= 0.5 | nested, smaller >= 0.85 | smaller 1 member outside |
|---|---:|---:|---:|---:|
| **CI** | 183,091 | **4,115,817** | **364,412** | **28,895,622** |
| **CT** | 98,817 | **1,063,235** | 18,408 | **5,296,155** |
| O50s s2 | 99,951 | 823,931 | 3,704 | 5,308,972 |
| O50s s3 (gated) | 26,120 | 409,858 | 1,968 | 570,291 |

**CT has 29% more non-nested near-copies than s2 at nearly the same theme count, five times as many
0.85-nested pairs, and the same number of inheritance triggers.** CI has five times s2's non-nested
pairs, a hundred times its nested pairs, and five times its triggers. Neither arm reduces the work
consensus and repair are there to do; both increase it.

Restricted to themes passing O50s's stored floors -- **INDICATIVE ONLY**, because those floors were
calibrated for O50s's families and neither arm pools the same way, so this measures neither arm's
real false-discovery rate:

| set | themes passing | non-nested J >= 0.5 | nested >= 0.85 | 1 outside |
|---|---:|---:|---:|---:|
| CI | 69,639 of 183,091 | 2,670,050 | 316,425 | 4,823,927 |
| CT | 27,799 of 98,817 | 583,027 | 15,055 | 790,835 |
| s2 | **26,120** of 99,951 | 409,858 | 1,968 | 570,291 |

The s2 row is a consistency check rather than a finding: applying the stored floors to s2 reproduces
**exactly** the 26,120 gated themes and exactly s3's three counts, as it must. Getting there
required matching `Material.rows`, which rounds support to six decimals before the comparison --
comparing the raw float instead rejected 28 themes that the real gate keeps.

## D. Correspondence with s5, the final O50s

| band | s5 themes | CI >= 0.9 | CI >= 0.7 | CT >= 0.9 | CT >= 0.7 |
|---|---:|---:|---:|---:|---:|
| 3-5 | 524 | 516 (98%) | 524 (100%) | 407 (78%) | 496 (95%) |
| 6-11 | 1,908 | 1,688 (88%) | 1,906 (100%) | 907 (48%) | 1,745 (91%) |
| 12-24 | 1,804 | 1,514 (84%) | 1,802 (100%) | 1,032 (57%) | 1,767 (98%) |
| 25-49 | 1,059 | 653 (62%) | 1,055 (100%) | 564 (53%) | 1,053 (99%) |
| 50-99 | 267 | 134 (50%) | 263 (99%) | 120 (45%) | 262 (98%) |
| 100-199 | 67 | 21 (31%) | 67 (100%) | 19 (28%) | 67 (100%) |
| 200-399 | 19 | 3 (16%) | 19 (100%) | 3 (16%) | 19 (100%) |
| 400-799 | 2 | 1 (50%) | 2 (100%) | 1 (50%) | 2 (100%) |
| 800-1599 | 3 | 1 (33%) | 3 (100%) | 1 (33%) | 3 (100%) |
| 1600+ | 5 | 2 (40%) | 5 (100%) | 1 (20%) | 5 (100%) |
| **ALL** | **5,658** | **4,533 (80%)** | **5,646 (100%)** | **3,055 (54%)** | **5,419 (96%)** |

**Almost every final O50s theme has a counterpart at J >= 0.7 in both arms** -- 100% for CI, 96% for
CT -- so the material O50s ends up with is present in these pools before any gate, consensus or
repair. At J >= 0.9 the agreement falls with size, to 16% at 200-399. The arms contain O50s's
answers approximately but not exactly, and the approximation gets looser the larger the theme.

The five O50s giants and their best counterpart:

| giant | size | arm | J | counterpart size | its core |
|---|---:|---|---:|---:|---:|
| n01843 | 2,564 | CI | 0.857 | 2,197 | 1,456 |
| n01843 | 2,564 | CT | 0.865 | 2,260 | 1,574 |
| n02672 | 2,172 | CI | 0.877 | 1,924 | 1,345 |
| n02672 | 2,172 | CT | 0.870 | 1,892 | 1,290 |
| n03878 | 2,135 | CI | 0.903 | 1,928 | 1,344 |
| n03878 | 2,135 | CT | 0.871 | 1,887 | 1,296 |
| n04994 | 2,096 | CI | 0.952 | 1,995 | 1,603 |
| n04994 | 2,096 | CT | 0.952 | 1,995 | 1,603 |
| n01419 | 1,603 | CI | 0.821 | 1,347 | 982 |
| n01419 | 1,603 | CT | 0.822 | 1,413 | 994 |

**The giants exist in both arms before any merging machinery runs**, at J 0.82 to 0.95, with cores
of 980 to 1,600 pathways. They are not made by consensus or repair; they are in the groupings.

## E. Examples

Twenty CI and twenty CT themes of 25 or more members, drawn at random with seed 20261023, as
`name [source]` lists with each core member marked:

* `data/experiments/core_merge_2026-10-23/examples/CI_examples.md`
* `data/experiments/core_merge_2026-10-23/examples/CT_examples.md`

Not judged here.

## What this says

1. **The hypothesis does not hold.** Comparing versions on cores rather than full sets produces the
   same number of themes (CT: 98,817 against 99,951) with **more** near-copies, not fewer. The
   borders were not the problem.
2. **The reason is visible in section A.** For most themes the core *is* the membership -- median
   core share 1.000 from 12 members up to 799. A rule comparing cores is therefore comparing nearly
   the same objects as a rule comparing full sets, and behaves accordingly. Only in the giants is
   the core a distinct, smaller object.
3. **CI is not a serious candidate.** Requiring identical cores merges almost nothing: 183,091
   themes, median 1.0 groupings each, and 4.1 million non-nested near-copies.
4. **O50s's answers are already in the pool.** 96-100% of its final themes have a J >= 0.7
   counterpart in both arms, and all five giants do. Whatever consensus and repair contribute, it is
   not the discovery of these themes.

**Nothing is adopted and no ontology was built.**

## Outputs

| what | where |
|---|---|
| both arms, with members and cores | `data/experiments/core_merge_2026-10-23/themes_CI.npz`, `themes_CT.npz` |
| the no-core census and parameters | `.../arms.json` |
| section C, one file per set | `.../section_c_{CI,CT,s2,s3}.json` and `*-floors.json` |
| section E | `.../examples/CI_examples.md`, `CT_examples.md` |

```sh
uv run scripts/core_merge.py                        # both arms
uv run scripts/core_merge_pairs.py --set CT         # section C, per set
uv run scripts/core_merge_pairs.py --set CT --floors-only
uv run scripts/core_merge_report.py                 # sections A, B, D, E
```
