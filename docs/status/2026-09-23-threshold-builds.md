# `recurrent_dag` builds compared — 23 Sep 2026

*Four builds on the same 1,854 v4 embeddings, ward linkage, tol 0.15. They differ only in how
themes are kept. None is frozen.*

---

## The four builds

| | **A** single m | **B** banded, two-merge | **C** banded, single-merge | **D** C + tightness |
|---|---|---|---|---|
| order | families on raw sets, threshold, membership, **second merge** | same | **completion first**, no second merge | same as C |
| `min_size` | 5 | 3 | 3 | 3 |
| threshold | one, m = 0.33 | per band | per band | per band, **joint budget** |
| tightness test | no | no | no | **3–4 and 5–9** |
| **nodes** | **391** | **293** | **792** | **1201** |
| **placed** | 1706 (92%) | 1776 (96%) | 1846 (100%) | **1854 (100%)** |
| **multi-parent** | 19 | 46 | 317 | 534 |
| **roots** | 158 | 57 | 92 | 116 |
| variant pairs | 0 | 0 | **0** | **0** |
| **glued themes** | 12 / 391 (3.1%) | 6 / 293 (2.0%) | — | **21 / 1201 (1.7%)** |
| false rate | 0.015 (families) | — | — | **0.0500 in-sample, 0.0533 held out** |

**B's apparent improvement on glued themes is not one.** It dropped the 3–4 and 5–9 bands
entirely, so six of the twelve glued nodes were deleted along with their whole size class rather
than resolved. Their halves could not appear either — every node in B has ≥ 10 members.

## Band thresholds per build

**B — banded, two-merge.** 3–4 **dropped** (ratio ~1.8 at m=0.48, real and scrambled falling in
lockstep). 5–9 **dropped** — a near miss, 0.0571 at m=0.48, reaching 0.05 only at m ≈ 0.497, against
a 0.5 ceiling. 10–29 and 30+ at m = 0.20, both with **zero** scrambled themes.

**C — banded, single-merge.** 3–4 **dropped** (285 real / 286 scrambled at m=0.48). 5–9 **passes at
m = 0.30**, 357 real against 14 scrambled (0.039) — the band the two-merge order could not keep.
10–29 and 30+ at m = 0.20, zero scrambled.

**D — with tightness and a joint 5% budget.**

| band | m | tightness | real | scrambled | rate |
|---|---|---|---|---|---|
| 3–4 | 0.34 | **yes** | 313 | 44 | 0.141 |
| 5–9 | 0.20 | **yes** | 453 | 16 | 0.035 |
| 10–29 | 0.20 | no | 371 | **0** | 0.000 |
| 30+ | 0.20 | no | 64 | **0** | 0.000 |
| **total** | | | **1201** | **60** | **0.0500** |

Held out on a second scramble: **64 / 1201 = 0.0533**, above target. Per band, 3–4 was stable
(44 → 43); the drift was 5–9 (16 → 21). The optimiser had saturated the budget exactly, leaving no
margin.

## Where D's themes come from

| band | nodes | match a build-A theme (J ≥ 0.7) | new |
|---|---|---|---|
| 3–4 | 313 | 8 | **305** |
| 5–9 | 453 | 246 | 207 |
| 10–29 | 371 | 273 | 98 |
| 30+ | 64 | 29 | 35 |
| **total** | **1201** | **556** | **645** |

**378 of build A's 391 themes (97%) have a match in D** — D is close to a superset, not a different
partition. The growth is a size class A could not express (A's `min_size` was 5) plus relaxed
thresholds recovering 98 mid-size and 35 large themes.

Two-parent themes in D: 534, median size 6. Child size as a fraction of each parent: p25 0.103,
**median 0.417**, p90 0.700. (The other direction is vacuous — Hasse edges are strict containment,
so a child is always wholly inside its parent.) 127 of the 534 have parents differing in size by
more than 2×, up to 117× — themes sitting inside both a tight and a broad parent, which is the
multi-granularity case the DAG exists for.

## Glued themes in D

Four nodes flagged in build A, checked against D:

| A node | whole node in D | half A | half B |
|---|---|---|---|
| n0352 epigenetics ‖ cell fate | **exact** | **exact** | **exact** |
| n0342 MITF ‖ mismatch repair | **exact** | **exact** | partial 0.50 |
| n0364 | close 0.80 | **exact** | — |
| n0212 PLK1 ‖ PI3K/AKT/PTEN | **exact** | PLK1 half **exact** | PI3K half absorbed, 0.50 |

**D resolves the glue by representing both the whole and its halves as overlapping themes**, which
is what a DAG is for and what a tree cannot do. Unlike B, the small themes still exist, so the
halves have somewhere to be.

## Open

The **0.05 target itself** is the open question, not the mechanism. A frozen ontology is reused by
every downstream analysis, so a false theme misleads indefinitely; `DECISIONS.md` (23 Sep) records
the move to **overall ≤ 0.01 with no band above 0.02**, calibrated on the mean of five scrambles.
The rebuild at that target, and the membership-cutoff comparison (0.25 against 0.50), were running
when this note was written and are not in it.
