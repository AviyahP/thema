# Runs performed — the tightness line of work

*A record of what was actually executed, so it can be reconstructed without access to any
conversation. Written 24 Sep 2026.*

---

## 1. Tightness calibration — 31 sides

| | |
|---|---|
| script | `tight_side.py` (worker), `tight_agg.py` (aggregation), scratchpad |
| sides | **1 real + 20 calibration scrambles (seeds 0–19) + 10 held-out scrambles (seeds 20–29)** |
| parameters | ward, `tol = 0.15`, `min_size = 3`, 100 runs, subsample 0.80, membership cutoffs **0.25 and 0.50** both computed per side |
| statistic | centred cohesion — mean pairwise cosine after subtracting the **universe mean** embedding |
| recurrence | fixed at the grid floor `m = 0.20` for the 3–4 band |
| when | 23 Sep 2026, ~14:37 → 18:20 |
| duration | **3.5 h wall, 10.7 h CPU**; mean **1,238 s per side** |
| concurrency | 4, then 2, then 4 (dropped to 2 mid-run on a memory check, restored after) |
| outputs | `tight/real.tsv`, `tight/0..29.tsv` — **scratchpad only, not in the repository** |
| row format | `cutoff, size, support, cohesion` per scored family |

**IT RAN ON A SUPERSEDED UNIVERSE.** The embeddings are `data/ontology/v0.2/embeddings.npy` dated
21 Sep, covering 1,854 keys — **4 of which the universe rule now excludes** (`reactome:R-HSA-1222541`,
`R-HSA-1660510`, `R-HSA-9679509`, `R-HSA-9727281`). Every number below is therefore for a universe
of 1,854 rather than the current 1,850 within that subset. The 3–4 band failed by a margin far
larger than four pathways could account for, so the conclusion is not thought to move, but the
**exact c\* values are provisional and must be re-derived on a rebuilt universe.**

### What it showed

Solved thresholds, membership cutoff 0.25:

| stratum | c\* | real kept | calibration FDR | held-out FDR | leave-one-out (20 folds) |
|---|---|---|---|---|---|
| size 3 | 0.122544 | 193 / 193 | 0.0199 | **0.0264 FAIL** | c\* 0.1220–0.1229, retained 193 every fold (span 0.0%) |
| size 4 | 0.104334 | 141 / 141 | 0.0199 | **0.0220 FAIL** | c\* 0.1043–0.1046, retained 141 every fold (span 0.0%) |

At cutoff 0.50: size 3 c\* 0.122640, held-out 0.0260; size 4 c\* 0.104351, held-out 0.0237. Both fail.

Bands solved on recurrence alone, cutoff 0.25: **5–9** m = 0.44, 275 themes, FDR 0.0189; **10–29**
m = 0.20, 446 themes, FDR 0.0000; **30+** m = 0.20, 75 themes, FDR 0.0000.

Overall build FDR (cutoff 0.25): **with** 3–4, 1,130 themes, 0.0115 — fails the 0.01 target;
**without**, 796 themes, **0.0060 — passes**.

### FDR and survival curves (cutoff 0.25)

Real survival is **flat at 100%** across every value shown. Only the null count moves.

| size 3, c | real | calib null | FDR | held-out FDR |
|---|---|---|---|---|
| 0.1135 | 193 | 19.05 | 0.0987 | 0.1026 |
| 0.1180 | 193 | 9.55 | 0.0495 | 0.0549 |
| **0.1225** | 193 | 3.85 | **0.0199** | **0.0264** ← c\* chosen |
| 0.1254 | 193 | 1.95 | 0.0101 | 0.0161 |
| 0.1313 | 193 | 0.20 | 0.0010 | 0.0036 |
| **0.2179** (real min) | **193** | **0.00** | **0.0000** | **0.0000** |

| size 4, c | real | calib null | FDR | held-out FDR |
|---|---|---|---|---|
| 0.0949 | 141 | 28.55 | 0.2025 | 0.2057 |
| 0.0979 | 141 | 14.30 | 0.1014 | 0.1078 |
| **0.1043** | 141 | 2.90 | **0.0206** | **0.0227** ← c\* chosen |
| 0.1069 | 141 | 1.45 | 0.0103 | 0.0106 |
| **0.3045** (real min) | **141** | **0.00** | **0.0000** | **0.0000** |

### Cohesion distributions — disjoint

| | n | min | q25 | median | q75 | max |
|---|---|---|---|---|---|---|
| real, size 3 | 193 | **0.2179** | 0.5413 | 0.6344 | — | 0.8534 |
| scrambled, size 3 | 3,805 | 0.0721 | — | 0.1001 | q95 0.1180 · q99 0.1254 | **0.1370** |
| real, size 4 | 141 | **0.3045** | 0.4990 | 0.6056 | — | 0.8336 |
| scrambled, size 4 | 5,710 | 0.0615 | — | 0.0847 | q95 0.0979 · q99 0.1043 | **0.1160** |

## 2. "Smallest c" verification

Run 24 Sep from the saved `.tsv` files. At size 3, **77** distinct null values satisfy FDR ≤ 0.02
and **none lies above the null maximum** (0.1370); the smallest is 0.122544. At size 4, 55 values,
smallest 0.104334. **An unbounded grid selects the same values**, confirming the defect is the
"smallest c" rule and not the search range.

## 3. Subset analysis — real build only

From `data/ontology/v0.2/recurrent_dag_single_banded/members.tsv` (1,201 themes, 5% target,
cutoff 0.50, min_size 3):

| size | themes | subset of a larger theme | stand alone |
|---|---|---|---|
| 3 | 179 | **176 (98%)** | 3 |
| 4 | 134 | **132 (99%)** | 2 |
| 5 | 73 | 69 (95%) | 4 |
| 10+ | 435 | 372 (86%) | 63 |

**98% of size 3–4 themes sit inside a larger theme.** A small theme is therefore **not a
free-standing discovery but a claim of finer structure inside an already-accepted node**, which is
part of why they clear a whole-universe null so easily. Not acted on; see `docs/debt.md`.

**The scrambled side of this comparison was not computed** — see §5.

## 4. Code inspection — the matching tolerance

`src/thema/ontology/recurrent.py:361`, `allowed = tol * shared_count`, compared against integer
`missing` and `extras`. Effective slack is `floor(0.15 × size)`:

| size | 3 | 4 | 5 | 6 | 7 | 13 | 14 | 20 |
|---|---|---|---|---|---|---|---|---|
| members of slack | **0** | **0** | **0** | **0** | 1 | 1 | 2 | 3 |

With `min_shared = 3`, a size-3 grouping can only be judged by a run that drew all three, and must
then reappear **exactly**. Confirmed by direct evaluation, not by reading alone.

## 5. WHAT WAS NOT SAVED, AND WHAT IT COSTS

**This is a real constraint on re-analysis and should not have to be rediscovered.**

| not persisted | consequence |
|---|---|
| the `Prepared` objects (100 runs per side) | **any change to `tol` or the matching rule requires re-running every side from scratch** — ~1,240 s each — even though `prepare` is formally independent of `tol` and could have been reused |
| scrambled **member sets** | the subset analysis in §3 **cannot be repeated on the null**, so "are small real themes absorbed into larger ones more often than scrambled ones?" is unanswerable without re-running sides |
| per-theme identities in the calibration output | rows are `(cutoff, size, support, cohesion)` only, so no theme in the calibration can be traced back to its members |

Persisting `Prepared` would have made the entire matching-rule investigation a scoring exercise of
minutes rather than hours.

## 6. verify-v1 on the 13 `v4-alt` descriptions

Batch `msgbatch_014f7CYc2Y5qx3CRAU1aoMVk`, 23 Sep, $0.07–0.09, `--generation v4-alt --keys`.
**0 of 9 checked, 4 refused by the verifier** (`R-HSA-9683673`, `R-HSA-9683610`, `R-HSA-9692913`,
`R-HSA-9683686` — all SARS-CoV-1 protein maturation or cell death). No further verification; the v4
batch was not verified row by row either.
