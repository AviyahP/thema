# The match threshold calibrated per size stratum (O50s-M). 19 Oct 2026

**The reviewer's diagnosis is confirmed exactly, and the threshold flips at exactly 10 pathways.**
Below 10, θ = 0.70 wins every stratum and θ = 0.50 admits **literally nothing** at 3-3, 4-4 and 5-5 —
the 8 Oct failure reproduced. From 10 up, 0.50 wins everywhere except 20-39, where 0.60 edges it. The
sweep admits **38,434 candidates against O50s's 26,120, +47%**, and **both arms are inside both
caps**.

**And neither arm fixes what it was built to fix.** The 164 small roots were the target. **Arm M makes
the root count worse — 394 against O50s's 261 — and still leaves 155 small roots.** Arm Mm reaches 94
roots but only by discarding half the build: 2,973 themes against 5,658, the 3-50 count down to
**54.9%** of O50s's, placement down **11 points to 81.5%**, and 115 pathways effectively unplaced.
Exploratory; adopts nothing.

| | O50s | **M** | **Mm** |
|---|---:|---:|---:|
| held-out FDR overall | 0.00233 | **0.00324** | **0.00379** |
| worst stratum | 0.01088 | **0.01088** | **0.01088** |
| inside both caps | yes | **yes** | **yes** |
| themes | 5,658 | **6,884** | **2,973** |
| roots | 261 | **394** | **94** |
| roots of ≤50 | 164 | **155** | **83** |
| summary placement | 92.6% | **93.1%** | **81.5%** |
| Reactome median best J | 0.273 | **0.273** | **0.237** |

## 1. Per stratum: the sweep, the chosen θ and the floor

| stratum | adm@0.50 | adm@0.60 | adm@0.70 | **chosen** | floor | real | calib FDR | held M | held Mm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3-3 | **0** | 20 | **213** | **0.70** | 0.832461 | 213 | 0.00751 | 0.00391 | 0.00391 |
| 4-4 | **0** | 71 | **126** | **0.70** | 0.915 | 126 | 0.00635 | 0.00265 | 0.00265 |
| 5-5 | **0** | 176 | **192** | **0.70** | 0.515 | 192 | 0.00729 | 0.01042 | 0.01042 |
| 6-6 | 18 | 193 | **353** | **0.70** | 0.326633 | 353 | 0.00652 | 0.00378 | 0.00378 |
| 7-9 | 909 | 1,052 | **1,179** | **0.70** | 0.195 | 1,179 | 0.00772 | **0.01088** | **0.01088** |
| 10-19 | **7,019** | 6,713 | 5,793 | **0.50** | 0.050251 | 7,019 | 0.00739 | 0.00741 | 0.0 |
| 20-39 | 13,030 | **14,294** | 11,818 | **0.60** | 0.01 | 14,294 | 0.00388 | 0.00386 | 0.0 |
| 40-79 | **9,335** | 6,928 | 4,830 | **0.50** | 0.01 | 9,335 | 1.07e-05 | 0.0 | 0.0 |
| 80-159 | **3,428** | 2,042 | 1,030 | **0.50** | 0.01 | 3,428 | 8.75e-05 **\*** | 0.0 | 0.0 |
| 160-319 | **1,274** | 612 | 234 | **0.50** | 0.01 | 1,274 | 2.35e-04 **\*** | 0.0 | 0.0 |
| 320-639 | **609** | 316 | 96 | **0.50** | 0.01 | 609 | 4.93e-04 **\*** | 0.0 | 0.0 |
| 640-1,279 | **260** | 183 | 160 | **0.50** | 0.01 | 260 | 1.15e-03 **\*** | 0.0 | 0.0 |
| 1,280+ | **152** | 122 | 103 | **0.50** | 0.01 | 152 | 1.97e-03 **\*** | 0.0 | 0.0 |

**\*** = the rule-of-three bound decided the cut. **Chosen θ: 0.70 in five strata, 0.60 in one, 0.50
in seven. No stratum admits nothing.**

**The flip is sharp and it is exactly at 10.** Three strata admit **zero** candidates at θ = 0.50 —
3-3, 4-4 and 5-5 — because at that threshold the scrambles recur as readily as the data, which is
the 8 Oct result that killed a global 0.50. One stratum above 10 keeps a mid θ (20-39 at 0.60, where
0.60 admits 14,294 against 0.50's 13,030 and 0.70's 11,818). Everywhere else above 10, loosening to
0.50 roughly doubles what gets in: 40-79 goes 4,830 → **9,335**, 80-159 1,030 → **3,428**, 160-319
234 → **1,274**, 320-639 96 → **609**.

**Both arms are inside both caps.** M overall **0.00324**, Mm **0.00379**, against a 0.01 cap; worst
stratum **0.01088** in both, which is 7-9 — a **frozen** stratum whose floor neither arm changed, so
the worst held-out rate in this build is inherited from O50s rather than caused by the sweep. Every
stratum the sweep actually moved (10 up) has a held-out rate of **0.00741 or better**, and six of them
are exactly **0.0**.

**Arm Mm's 0.33 minimum lifted the floor in all eight strata of 10 or more**, and the effect is
drastic: the gate falls from **38,434 to 4,578**. Per stratum: 10-19 7,019 → 1,726, 20-39 14,294 →
499, 40-79 9,335 → 231, 80-159 3,428 → **19**, 160-319 1,274 → **5**, 320-639 609 → **2**, 640-1,279
260 → 16, 1,280+ 152 → 17. The large strata are all but emptied.

## 2. Themes by size band

| band | O50s | **M** | **Mm** |
|---|---:|---:|---:|
| 3-5 | 524 | 529 | 529 |
| 6-11 | 1,908 | 1,971 | 1,549 |
| 12-24 | 1,804 | **2,048** | 680 |
| 25-49 | 1,059 | **1,425** | 150 |
| 50-99 | 267 | **610** | 48 |
| 100-199 | 67 | **221** | 7 |
| 200-399 | 19 | **55** | 3 |
| 400-799 | 2 | **15** | 2 |
| 800-1,599 | 3 | 6 | 2 |
| 1,600+ | 5 | 4 | 3 |
| **total** | **5,658** | **6,884** | **2,973** |

**M grows the mid-size layer again**, on top of what O50s already did: 50-99 more than doubles (267 →
610), 100-199 more than triples (67 → 221), 200-399 nearly triples (19 → 55). Measured against the
original O50 these bands are now 6× and 20× their starting size.

**Mm destroys it.** 12-24 falls to 38% of O50s, 25-49 to 14%, 100-199 to **7 themes**. Only the
smallest band survives intact, because 3-5 is governed by a frozen stratum the minimum never touches.

## 3. Shape

| | O50s | **M** | **Mm** |
|---|---|---|---|
| themes | 5,658 | 6,884 | 2,973 |
| **roots** | **261** | **394** | **94** |
| roots of ≤50 pathways | 164 | **155** | 83 |
| children max / median | 382 / 2 | **535** / 2 | 192 / 1 |
| multi-parent share | 63.3% | **67.1%** | **29.1%** |
| effectively unplaced | 0 | **0** | **115** |

**Giants.** Ids are positional and not comparable between builds.

| build | giants |
|---|---|
| O50s | `n01843` 2,564, `n02672` 2,172, `n03878` 2,135, `n04994` 2,096, `n01419` 1,603 |
| **M** | **7**: `n00000` 2,832, `n02091` 2,409, `n01264` 2,218, `n00001` 1,854, `n04480` 1,182, `n00490` 1,113, `n00002` 1,091 |
| **Mm** | **4**: `n00000` 2,165, `n02073` 1,925, `n01256` 1,712, `n00001` 1,374 |

M gains two giants and a larger maximum (2,832 against 2,564); Mm loses one and shrinks them.

## 4. Small themes and O50s counterparts

| | **M** | **Mm** |
|---|---|---|
| themes of 3-50 | 5,999 = **113.1%** of O50s's 5,305 | 2,911 = **54.9%** |
| O50s themes with a counterpart at J ≥ 0.9 | 2,869 of 5,658 = **50.7%** | 2,389 = **42.2%** |

**M keeps the small end and adds to it — but it is not the same small end.** Only **half** of O50s's
themes survive recognisably at J ≥ 0.9, against the 94.9% that survived O50s's own floor change in
prompt 43. Loosening the match threshold does not refine O50s's themes; it **replaces** them. That is
the single most important number in this report for anyone thinking of adopting M: it is a different
ontology, not a better-resolved one.

## 5. The 164 O50s small roots — the thing this was meant to fix

| | counterpart at J ≥ 0.7 | of those, still roots |
|---|---|---|
| **M** | **86 of 164 = 52.4%** | **20 = 23.3%** |
| **Mm** | **8 of 164 = 4.9%** | 2 = 25.0% |

**Arm M does dissolve most of them**: 78 of the 164 have no recognisable counterpart at all, and of
the 86 that survive, 66 acquire a parent. **But the root count still rises from 261 to 394**, because
the 38,434 admitted candidates create new roots faster than the old ones are absorbed. The small-root
count barely moves, 164 → 155.

**Arm Mm's 4.9% is not a fix either** — it is the small roots vanishing along with half the build.

## 6. The named O50s roots

| O50s root | size | **M** counterpart | J | root? | **Mm** counterpart | J | root? |
|---|---:|---|---:|---|---|---:|---|
| `n01027` | 923 | `n03803` | 0.841 | **no** | `n00002` | 0.839 | yes |
| `n04526` | 820 | `n02653` | 0.474 | **no** | `n00001` | 0.499 | no |
| `n04670` | 618 | `n04001` | 0.788 | **no** | `n00000` | 0.277 | yes |
| `n04671` | 434 | `n04951` | 0.551 | **yes** | `n02688` | 0.479 | no |
| `n03316` | 386 | `n02706` | 0.822 | **no** | `n02687` | 0.772 | no |
| `n04672` | 348 | `n04481` | 0.638 | **no** | `n00001` | 0.216 | no |
| `n04995` | 262 | `n04955` | 0.705 | **no** | `n00002` | 0.302 | yes |
| `n05001` | 209 | `n02092` | 0.486 | **no** | `n02074` | 0.368 | yes |

**In M, seven of the eight stop being roots** — only `n04671` remains, and at J = 0.551 it is barely
the same theme. Three of the eight (`n04526`, `n04671`, `n05001`) have no counterpart above 0.7 at
all, so "no longer a root" partly means "no longer there".

**In Mm, four of the eight are still roots**, and their counterparts are much poorer — `n04670` at
0.277, `n04672` at 0.216. Mm replaces them with a handful of large nodes (`n00000`, `n00001`,
`n00002` appear repeatedly) rather than parenting them.

## 7. Placement and Reactome

| | O50s | **M** | **Mm** |
|---|---:|---:|---:|
| summary placement | 2,194 = 92.6% | **2,206 = 93.1%** | **1,932 = 81.5%** |
| Reactome median best J | 0.273 | **0.273** | **0.237** |

**M gains half a point of placement for 1,226 extra themes** — a poor exchange rate next to prompt
43's +7.3 points, and next to prompt 46's 99.2%. **Mm loses 11 points.**

**Reactome: 0.273 unchanged for M, and 0.237 for Mm — the first build in this project to make that
measure actively worse.** Seven consecutive attempts have now failed to improve it.

## 8. What this says

**The calibration is correct and the finding is real.** Matching at 0.70 above 10 pathways was
throwing away recurrence evidence, exactly as the reviewer's diagnostics said; per-stratum selection
recovers 47% more candidates with the held-out rate *inside* both caps and six strata at 0.0. **The
threshold genuinely does have to depend on size, and the switch point is 10 pathways.**

**But recovering candidates is not the same as fixing the top.** The 164 small roots are the problem
this was aimed at, and:

- **M leaves 155 of them and raises the root count to 394.** More admitted candidates means more
  nodes that nothing contains. The gate was the wrong lever for this problem.
- **M replaces O50s rather than refining it.** Only 50.7% of O50s's themes survive at J ≥ 0.9. Any
  reviewer reading already done on O50s does not transfer.
- **Mm hits 94 roots but is not a build worth having**: half the themes gone, the 100-199 band down
  to 7, placement −11 points, Reactome worse, and 115 pathways effectively unplaced. The 0.33
  minimum is doing the same thing to the gate that it was retired for doing in the first place.

**The honest comparison with what already exists.** Prompt 46's areas-on-roots reached **12 roots and
99.2% placement** by building a layer *above* O50s and leaving it untouched. This prompt reaches 394
or 94 roots by rebuilding O50s from a looser gate. On every criterion the two share, the layer wins —
and it does not invalidate the reviewer's reading of O50s.

**Adopted: nothing.** If anything here is worth keeping it is the per-stratum table itself: the
measured fact that the match threshold should be 0.70 below 10 pathways and 0.50 above it is a
property of the data, and it will be true of any future build whatever is done with the top.

## For the reviewer

`data/experiments/match_per_stratum_2026-10-19/{M,Mm}/roots.tsv` — id, size, support, the stratum's
chosen θ, children and full member keys. **394 rows for M, 94 for Mm.** Not judged here.

## Reproducing this

```sh
uv run scripts/match_per_stratum.py --sides    # 8,740 s, resumable, 305 MB of cached rows
uv run scripts/match_per_stratum.py --solve    # 1 s
uv run scripts/match_per_stratum.py --arm M    # 458 s, peak 3.1 GB
uv run scripts/match_per_stratum.py --arm Mm   # 23 s
uv run scripts/match_per_stratum_report.py     # 6 s
uv run pytest tests/test_match_per_stratum.py
```

The sweep is 17 sides × 3 thetas. `prepare` is θ-free and costs 4 s, so it is paid once a side; each
θ then costs 120 s on the real side and 161 s on a scramble. **θ = 0.70 reproduces the cached sides
exactly — 99,951 real candidates and 218,729 on seed 3001** — which is the replication check, and a
test asserts it. Total 2.4 h for the sweep and about 10 min for everything after it. No API calls.
