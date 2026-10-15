# Areas, second and last try (rec2). 15 Oct 2026

**It fails.** Four of the six criteria ccode owns pass; **two fail** — no area over 1,000 pathways
(largest **2,618**), and no node over 60 children (max **181**). By the declaration there is no third
try: **the working view becomes O50 with the giants dropped and about 660 flat roots.**

The two changes it tested both **worked on the thing they targeted**, which is why the failure is
worth reading rather than filing. Everything here is EXPLORATORY and **adopts nothing**. The three
changes to rec are **post hoc**, from the reviewer's reading of rec's failure.

| criterion | rec2 | rec |
|---|---|---|
| held-out FDR within the caps, every stratum and overall | **PASS** — overall **0.00429**, worst stratum 0.00459 | FAIL (0.038, 0.026) |
| 20-60 roots, anchors included | **PASS** — **42** | pass (30) |
| no node over 60 children | **FAIL** — max **181** | pass (21) |
| ≥95% of the 476 giant-only themes get a parent area or anchor | **PASS** — **100%** | pass (100%) |
| no two roots at pathway Jaccard ≥ 0.50 | **PASS** — highest **0.492** | FAIL (0.71) |
| no area over 1,000 pathways | **FAIL** — largest **2,618**, 8 areas over | FAIL (3,053, 16 over) |
| C6, blind intruder test | the reviewer's | — |
| the top is intuitive | Aviyah's | — |

## 1. Anchors — 6, as declared

| anchor | pathways | support | O50 children | |
|---|---:|---:|---:|---|
| `n01027` | **813** | 0.805 | 105 | |
| `n01279` | **781** | 0.695 | 59 | |
| `n03315` | 349 | 0.105 | 14 | |
| `n03959` | 290 | 0.045 | 33 | giant-only in O50 |
| `n03376` | 280 | 0.095 | 12 | giant-only in O50 |
| `n02017` | 206 | 0.410 | 7 | giant-only in O50 |

6 anchors holding **2,079** pathways between them; **655** units went to level 2.

## 2. Level 2, beside rec

| | rec2 | rec |
|---|---:|---:|
| units clustered | 655 | 661 |
| anchors | **6** | 0 |
| candidates | 5,691 | 5,685 |
| through the gate | 1,398 | — |
| after consensus | **418** | 556 |
| **areas** | **343** | 470 |
| area roots | 36 | 30 |
| **roots in all** | **42** | 30 |
| collapsed / merged | 75 / 0 | 80 / 6 |
| size in units (min/med/max) | 4 / 18 / 405 | 3 / 12 / 251 |
| size in pathways | 27 / 131 / **2,618** | 20 / 153 / 3,053 |
| multi-parent | 156 = 45.5% | 198 = 42.1% |
| children per node (max / median) | **181** / 7 | 21 / 4 |
| areas over 1,000 pathways | **8** | 16 |
| wall time | 251.3 s | 135.8 s |

### Held-out FDR — fixed, and by a wide margin

| stratum | floor | calib FDR | **held-out** | real | cap | rec |
|---|---:|---:|---:|---:|---:|---:|
| 3-3 | none | — | — | 0 | 0.02 | 0.03846 |
| 4-4 | 0.940 | 0.00588 | **0.0** | 17 | 0.02 | — |
| 5-5 | 0.815 | 0.00588 | **0.0** | 17 | 0.02 | 0.0 |
| 6-6 | 0.770 | 0.00556 | **0.0** | 18 | 0.02 | 0.01724 |
| 7-9 | 0.485 | 0.00652 | **0.00272** | 92 | 0.02 | 0.02604 |
| 10+ | 0.055276 | 0.00682 | **0.00459** | 1,254 | 0.02 | 0.00707 |
| **overall** | | | **0.00429** | | 0.01 | 0.00882 |

Every stratum is inside the cap with room, and the overall rate halves. **Change 3 worked**: rec's
two breaches sat on 13 and 96 real candidates, and 20 calibration seeds against 10, with 4 held-out
seeds against 2, made the estimate precise enough to stop tripping. Stratum 3-3 now gets **no floor
at all** — no cut reached the 0.008 target — so it admits nothing, which is why its real count is 0.

## 3. Root overlap — change (a) worked

| | rec2 | rec |
|---|---|---|
| roots | **42** (6 anchors + 36 areas) | 30 |
| **highest root pair, pathway Jaccard** | **0.492** | **0.71** |
| root pairs at or above 0.50 | **0** | 4 |
| roots per pathway, median / mean / max | **4** / 3.80 / 15 | 3 / — / 14 |
| pathways in no root | 0 | — |

**How many roots each pathway sits in**, in full:

| roots | pathways | | roots | pathways | | roots | pathways |
|---:|---:|---|---:|---:|---|---:|---:|
| 1 | 975 | | 6 | 435 | | 11 | 27 |
| 2 | 973 | | 7 | 365 | | 12 | 10 |
| 3 | 769 | | 8 | 215 | | 13 | 3 |
| 4 | 963 | | 9 | 96 | | 14 | 2 |
| 5 | 672 | | 10 | 32 | | 15 | 2 |

The mass sits at 1-5 roots (4,352 of 5,539 pathways), with a thin tail to 15.

**The criterion passes, narrowly, and the underlying problem is not actually better.** No two roots
reach 0.50 — against rec's 0.71, 0.52, 0.51, 0.51 — so measuring the cutoff on pathway sets did stop
areas being built that hold mostly the same pathways. But a pathway still sits in a **median of 4**
roots, up from 3, and in up to 15. Removing the near-duplicate root *pairs* did not make the top
level a partition; it spread the same multiplicity over more roots.

**Every root pair at pathway Jaccard 0.30 or more** — 19 of the 861 pairs:

| J | root A | root B | shared |
|---:|---|---|---:|
| **0.492** | `b2_00161` (2,009) | `b2_00251` (1,288) | 1,087 |
| 0.486 | `b2_00261` (354) | `b2_00296` (346) | 229 |
| 0.437 | `b2_00252` (958) | `b2_00338` (1,903) | 870 |
| 0.431 | `b2_00252` (958) | `b2_00307` (1,177) | 643 |
| 0.430 | `n01279` (781) **anchor** | `n03315` (349) **anchor** | 340 |
| 0.415 | `b2_00147` (2,618) | `b2_00307` (1,177) | 1,113 |
| 0.409 | `b2_00307` (1,177) | `b2_00318` (680) | 539 |
| 0.403 | `b2_00090` (84) | `b2_00303` (191) | 79 |
| 0.399 | `b2_00241` (228) | `b2_00263` (445) | 192 |
| 0.385 | `b2_00283` (745) | `b2_00338` (1,903) | 736 |
| 0.378 | `b2_00301` (145) | `b2_00323` (125) | 74 |
| 0.376 | `b2_00090` (84) | `b2_00314` (176) | 71 |
| 0.367 | `b2_00308` (210) | `b2_00329` (505) | 192 |
| 0.366 | `b2_00251` (1,288) | `b2_00283` (745) | 545 |
| 0.362 | `b2_00272` (175) | `b2_00305` (220) | 105 |
| 0.357 | `n01279` (781) **anchor** | `n03376` (280) **anchor** | 279 |
| 0.342 | `b2_00251` (1,288) | `b2_00338` (1,903) | 814 |
| 0.332 | `b2_00241` (228) | `b2_00315` (141) | 92 |
| 0.313 | `b2_00270` (409) | `b2_00284` (379) | 188 |

Two of the 19 are **anchor pairs** — `n01279` / `n03315` at 0.430 and `n01279` / `n03376` at 0.357.
That overlap is inherited from O50 and is not something level 2 could have fixed: anchors are
finished areas by construction and were never candidates for merging.

## 4. The largest areas — why the size criterion fails

| area | pathways | units | support | |
|---|---:|---:|---:|---|
| `b2_00147` | **2,618** | 281 | 0.690 | **root** |
| `b2_00076` | **2,197** | 405 | 0.930 |  |
| `b2_00161` | **2,009** | 342 | 0.665 | **root** |
| `b2_00338` | **1,903** | 224 | 0.060 | **root** |
| `b2_00112` | **1,340** | 351 | 0.830 |  |
| `b2_00251` | **1,288** | 233 | 0.195 | **root** |
| `b2_00307` | **1,177** | 105 | 0.080 | **root** |
| `b2_00211` | **1,083** | 131 | 0.410 |  |
| `b2_00242` | 977 | 102 | 0.250 |  |
| `b2_00252` | 958 | 198 | 0.610 | **root** |
| `b2_00156` | 919 | 138 | 0.675 |  |
| `b2_00198` | 851 | 128 | 0.475 |  |
| `b2_00281` | 818 | 120 | 0.130 |  |
| `b2_00283` | 745 | 73 | 0.120 | **root** |
| `b2_00153` | 689 | 194 | 0.680 |  |
| `b2_00118` | 687 | 101 | 0.810 |  |
| `b2_00318` | 680 | 69 | 0.070 | **root** |
| `b2_00326` | 659 | 80 | 0.065 |  |
| `b2_00327` | 643 | 51 | 0.065 |  |
| `b2_00260` | 637 | 69 | 0.180 |  |
| `b2_00213` | 620 | 87 | 0.405 |  |
| `b2_00319` | 609 | 52 | 0.070 |  |
| `b2_00226` | 517 | 35 | 0.320 |  |
| `b2_00238` | 511 | 57 | 0.270 |  |
| `b2_00328` | 506 | 35 | 0.065 | **root** |
| `b2_00329` | 505 | 48 | 0.065 | **root** |
| `b2_00214` | 478 | 137 | 0.395 |  |
| `b2_00245` | 466 | 45 | 0.225 |  |
| `b2_00127` | 462 | 127 | 0.785 |  |
| `b2_00243` | 451 | 69 | 0.235 |  |

**Eight areas exceed O50's own giant definition** of 1,000 pathways, five of them roots. The tail is
not reassuring either: the 30th largest still holds 451 pathways, and support is low across a third
of them — **ten of the 30 sit under 0.15**, so they recur in fewer than one subsample in six and
clear the 10+ stratum floor of 0.0553 only just. Ten of the 30 are roots.

Anchoring the six area-sized units removed one cause of bags — n01027 is no longer in three roots at once — but the bags came back
from the other direction: 655 small units still agglomerate into very large areas, because nothing in
the method bounds an area's size. rec had 16 such areas and a 3,053-pathway maximum; rec2 has 8 and
2,618. **Better, and still failing.**

## 5. Coverage

| | rec2 | rec |
|---|---|---|
| giant-only themes with a parent area or anchor | **476 / 476 = 100%** | 100% |
| of which, promoted to an anchor in their own right | 3 | — |
| all units with a parent area or anchor | **661 / 661** | 661 / 661 |
| roots before → after | 188 → **42** | 188 → 30 |

**Per pathway, the largest non-giant theme or area above it:**

| band | before | rec2 | rec |
|---|---:|---:|---:|
| 1-10 | 1 | 0 | 0 |
| 11-50 | 1,096 | 0 | 0 |
| 51-200 | 2,362 | 0 | 0 |
| 201-1,000 | 2,079 | **999** | 0 |
| 1,001+ | 0 | **4,540** | 5,539 |

rec put every pathway under something over 1,000 members. rec2 gets **999 pathways** into the
201-1,000 band — a real improvement, the first sign of a mid-sized layer — but 4,540 are still under
a 1,000-plus area.

## 6. Secondary measures

**Gene coherence** (report only): median pairwise gene Jaccard **0.0118** against **0.0011**
size-matched random over the 159 areas of 2-120 pathways — **10.7×**, against rec's 10.2× over 182.
Essentially unchanged; low in absolute terms, as expected at the top.

**Summary placement** (display only, nothing attached). 2,370 curated summaries with 3+ leaf
descendants in L, counting a node that holds 80% of their leaves:

| summary band | n | O50 | rec | **rec2** |
|---|---:|---:|---:|---:|
| 3-10 | 1,711 | 1,525 | 1,626 | 1,578 |
| 11-50 | 560 | 439 | 495 | 441 |
| 51-200 | 96 | 55 | 76 | **52** |
| 201+ | 3 | 2 | 2 | **0** |
| **all** | **2,370** | 2,021 — **85.3%** | 2,199 — **92.8%** | 2,071 — **87.4%** |

**rec2 is worse than rec here, and worse than O50 in the 51-200 band** (52 against O50's own 55).
rec's strongest result does not survive anchoring: with 343 areas instead of 470 and six large units
held out of the clustering, there are fewer mid-sized nodes to be a summary's home. A gain of 2.1
points over O50 against rec's 7.5.

## 7. One methodological point, because it changes a number

Change (a) compares pathway sets while a candidate is still a set of units, so a surviving area's
unit list has to be recovered. **Recovering it by index is wrong**, and a test caught it:
`consensus` does not only drop candidates — `STRAY_FLOOR` is 1, so a candidate whose extras beyond an
accepted one number at most one is *inherited* and the accepted set grows, whatever `stray` is set
to. All 343 areas failed the units-union check under index recovery.

Units are therefore recovered from **provenance**: an area's own units, plus those of every candidate
superseded into it (followed transitively) and of every candidate whose members it inherited. Under
that recovery the compared pathway set is a **subset** of the units' union for all 343 areas, equal
for **155**, and smaller by a median of 19 pathways for the other 188 — because a candidate can be
folded in on the strength of one member while provenance credits its whole unit.

This is the one place rec2's numbers depend on a choice ccode made rather than one the declaration
fixed. **The children figure is the number affected**: 181 under provenance (4 areas over 60), 48
under index recovery (0 over 60). Provenance is the faithful reading and is what the verdict above
uses. **The area-size criterion fails under either**, so the overall result does not turn on it.
Prompt 34 never met this because it compared unit sets, where the union was true by construction.

## 8. What this says

Both targeted changes did what they were meant to:

- **Change 3 fixed the FDR outright** — every stratum inside the cap, overall halved to 0.00429.
- **Change (a) fixed the near-duplicate roots** — highest pair 0.492 against 0.71, none at 0.50.
- **Change (b) stopped the generic units joining everything** — n01027 is an anchor, not a member of
  three bag roots.
- And a mid-sized layer appeared for the first time: **999 pathways** now sit under something in the
  201-1,000 band.

And it still fails, for a reason neither change addressed: **nothing bounds an area's size.** Eight
areas exceed 1,000 pathways and the largest holds 2,618 — 47% of the universe. 655 small units
agglomerate into bags whether or not the big units are held out. Summary placement went backwards
too, from 92.8% to 87.4%, because anchoring left fewer mid-sized nodes to act as homes.

**Adopted: nothing. There is no third try, as declared.** The working view becomes **O50 with the
giants dropped and about 660 flat roots** — which is what the 661 units of this experiment are, and
what `data/experiments/naming_O50_2026-10-14/roots_without_giants_O50.tsv` already lists with
reviewer labels. C6 and the intuitiveness judgement are moot for adoption but the build is on disk if
either is still wanted.

## Reproducing this

```sh
uv run scripts/recursive_top_O50_rec2.py --estimate
uv run scripts/recursive_top_O50_rec2.py
uv run scripts/recursive_top_report2.py
uv run pytest tests/test_recursive_top2.py
```
