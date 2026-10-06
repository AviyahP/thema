# HiDeF at its best on the KC2 deciding table. 7 Oct 2026

**EXPLORATORY, REPORT ONLY.** A 4 × 5 grid — k ∈ {5, 10, 15, 30} × maxres ∈ {25, 50, 100, 200,
300}, other settings at the existing defaults (τ 0.75, χ 5, consensus p 75, Leiden, seed 0). Four
builds already existed and were reused; sixteen were built.

**Scored with exactly the KC2 deciding-table code**, imported from `kc2_report` rather than
reimplemented — same source only, recall banded by the curated set's size, precision by the theme's
size, match at best Jaccard > 0.5. That reuse is the point: a comparison in which HiDeF is measured
by a second implementation of the same measure is not a comparison.

New files only (`scripts/hidef_grid.py`). Nothing frozen is touched.

---

## 20:40:20Z — build times. Nothing hit the 10-minute limit, so nothing was skipped

| k | maxres 25 | 50 | 100 | 200 | 300 |
|---|---|---|---|---|---|
| 5 | 74 s | 83 s | 92 s | 132 s | 148 s |
| 10 | 102 s | 108 s | 116 s | 162 s | 175 s |
| 15 | *reused* | *reused* | *reused* | 198 s | 213 s |
| 30 | *reused* | 219 s | 231 s | 323 s | 354 s |

Reused: k15/25 (`hidef_10770_k15`), k15/50, k15/100, k30/25 (`hidef_10770_k30`). The slowest
build was **354 s**, well inside the 600 s guard, so **no setting was skipped** and the grid is
complete at 20 of 20. Cost rises with both k and maxres, as expected, and the whole grid was about
40 minutes.

## 20:40:20Z — Reactome, 674 curated sets

Cells are *recall / precision*. `*` marks the best setting by mean recall over the eight cells.

| setting | themes | 3–10 | 11–50 | 51–200 | 201–500 | mean recall |
|---|---|---|---|---|---|---|
| k5/25 | 652 | 19.8% / 37.4% | 34.5% / 31.5% | 3.9% / 11.1% | **33.3%** / 12.5% | 0.1170 |
| k5/50 | 985 | 29.1% / **39.1%** | 35.6% / 30.4% | 3.9% / 8.3% | **33.3%** / **16.7%** | 0.1330 |
| k5/100 | 1,470 | 35.1% / 37.6% | 39.1% / 33.3% | **7.7%** / 6.5% | **33.3%** / 12.5% | 0.1534 |
| k5/200 | 2,292 | 44.3% / 37.3% | 42.5% / 31.6% | 0.0% / 4.2% | **33.3%** / 14.3% | 0.1649 |
| **k5/300** ` *` | **2,915** | **48.5%** / 38.2% | 38.5% / 28.7% | 3.9% / 5.8% | **33.3%** / 14.3% | **0.1725** |
| k10/25 | 519 | 11.7% / 33.1% | 28.2% / 31.4% | 3.9% / 4.3% | **33.3%** / 10.0% | 0.0980 |
| k10/50 | 783 | 18.7% / 32.7% | 33.9% / 30.5% | 3.9% / 9.1% | **33.3%** / 12.5% | 0.1157 |
| k10/100 | 1,161 | 25.5% / 33.9% | 42.5% / 34.4% | 0.0% / 1.7% | **33.3%** / 12.5% | 0.1316 |
| k10/200 | 1,913 | 35.3% / 33.1% | **45.4%** / **34.7%** | 3.9% / 10.5% | **33.3%** / 9.1% | 0.1572 |
| k10/300 | 2,443 | 40.4% / 33.1% | 44.8% / 33.9% | 3.9% / 9.7% | **33.3%** / **16.7%** | 0.1652 |
| k15/25 | 472 | 10.8% / 35.6% | 25.3% / 27.2% | **7.7%** / 7.3% | **33.3%** / 12.5% | 0.0975 |
| k15/50 | 679 | 15.7% / 32.1% | 33.9% / 31.2% | **7.7%** / **13.2%** | **33.3%** / 12.5% | 0.1158 |
| k15/100 | 1,026 | 23.0% / 33.7% | 41.4% / 34.5% | 3.9% / 10.4% | **33.3%** / 11.1% | 0.1314 |
| k15/200 | 1,765 | 33.4% / 34.5% | 42.5% / 34.0% | 3.9% / 9.6% | **33.3%** / 8.3% | 0.1496 |
| k15/300 | 2,263 | 36.4% / 32.7% | 44.8% / 32.5% | 0.0% / 7.1% | **33.3%** / 9.1% | 0.1538 |
| k30/25 | 353 | 8.7% / 35.6% | 19.0% / 22.1% | 0.0% / 5.4% | **33.3%** / 10.0% | 0.0771 |
| k30/50 | 553 | 11.5% / 27.7% | 26.4% / 28.1% | 0.0% / 5.5% | **33.3%** / 9.1% | 0.0903 |
| k30/100 | 840 | 17.7% / 27.6% | 34.5% / 31.6% | 3.9% / 9.3% | **33.3%** / 10.0% | 0.1162 |
| k30/200 | 1,477 | 28.5% / 31.0% | 37.4% / 33.6% | 3.9% / 6.7% | **33.3%** / 9.1% | 0.1357 |
| k30/300 | 1,781 | 30.0% / 30.4% | 39.1% / 32.2% | 3.9% / 7.3% | **33.3%** / 9.1% | 0.1411 |
| **A (frozen)** | **6,244** | **60.6%** / 37.4% | **45.4%** / **44.5%** | **7.7%** / **22.7%** | 0.0% / 0.0% | 0.1667 |
| KC2 | 1,170 | 20.2% / 38.2% | 12.1% / 8.6% | **11.5%** / 6.2% | 0.0% / 0.0% | 0.0604 |

## 20:40:20Z — GO, 2,758 curated sets

| setting | themes | 3–10 | 11–50 | 51–200 | 201–500 |
|---|---|---|---|---|---|
| k5/25 | 652 | 0.6% / **15.2%** | 0.9% / 2.7% | 0.6% / 0.8% | 0.0% / 0.0% |
| k5/50 | 985 | 1.6% / 14.6% | 2.2% / 3.0% | 0.6% / **1.6%** | 0.0% / 0.0% |
| k5/100 | 1,470 | 4.2% / 14.3% | 2.7% / 4.0% | 0.6% / 0.8% | 0.0% / 0.0% |
| k5/200 | 2,292 | 7.6% / 13.2% | **3.6%** / 4.7% | 0.6% / 0.7% | 0.0% / 0.0% |
| **k5/300** ` *` | 2,915 | **9.6%** / 12.5% | **3.6%** / **4.9%** | 0.6% / 0.7% | 0.0% / 0.0% |
| k10/300 | 2,443 | 6.3% / 8.9% | 2.8% / 4.0% | 0.6% / 0.6% | 0.0% / 0.0% |
| k15/300 | 2,263 | 5.5% / 8.8% | 2.4% / 3.5% | 0.6% / 0.6% | 0.0% / 0.0% |
| k30/100 | 840 | 1.2% / 9.1% | 1.3% / 2.7% | **1.2%** / 0.8% | 0.0% / 0.0% |
| k30/300 | 1,781 | 4.3% / 9.1% | 1.7% / 3.0% | 0.6% / 0.7% | 0.0% / 0.0% |
| **A (frozen)** | 6,244 | **14.9%** / 11.0% | **4.1%** / 4.7% | 0.6% / **5.1%** | 0.0% / 0.0% |
| KC2 | 1,170 | 3.8% / **19.8%** | 0.6% / 2.8% | 0.0% / 0.0% | 0.0% / 0.0% |

The rows omitted from the GO table are monotone between the ones shown; the full 20 are in the JSON.

## 20:40:20Z — the best setting, and the oracle

**Best HiDeF by mean recall over the eight cells: k = 5, maxres = 300, at 0.1725** — against
**A (frozen) at 0.1667** and KC2 at 0.0604. So on that single aggregate, **HiDeF tuned beats A**, by
0.0058.

The grid is almost perfectly monotone and that is worth stating: **recall rises with maxres and falls
with k** at every point. k5/300 is the corner of the grid, so the search is pressed against its own
boundary — a wider grid would very likely keep going.

**Oracle line, the best HiDeF setting chosen per cell.** This is an advantage neither A nor KC2 is
given; each of those is one fixed configuration.

| cell | best recall | by | best precision | by |
|---|---|---|---|---|
| Reactome 3–10 | 48.5% | k5/300 | 39.1% | k5/50 |
| Reactome 11–50 | 45.4% | k10/200 | 34.7% | k10/200 |
| Reactome 51–200 | 7.7% | k5/100 | 13.2% | k15/50 |
| Reactome 201–500 | 33.3% | k5/25 (all settings tie) | 16.7% | k5/50 |
| GO 3–10 | 9.6% | k5/300 | 15.2% | k5/25 |
| GO 11–50 | 3.6% | k5/200 | 4.9% | k5/300 |
| GO 51–200 | 1.2% | k30/100 | 1.6% | k5/50 |
| GO 201–500 | 0.0% | — (every setting) | 0.0% | — |

**Even the oracle does not reach A at 3–10 or 11–50 on Reactome**: 48.5% against A's 60.6%, and
45.4% tying A exactly at 45.4%.

## 20:40:20Z — does A's lead at 3–10 and 11–50 survive HiDeF at its best?

**Yes at 3–10, on both sources and by a wide margin. At 11–50 it survives on recall only as a tie,
and survives clearly on precision.** Cell by cell, against the **oracle** (the strongest version of
the question):

| cell | A | HiDeF oracle | verdict |
|---|---|---|---|
| **Reactome 3–10 recall** | **60.6%** | 48.5% | **A leads** by 12.1 points |
| **Reactome 3–10 precision** | 37.4% | **39.1%** | A trails by 1.7 points |
| **Reactome 11–50 recall** | **45.4%** | 45.4% | **exact tie** |
| **Reactome 11–50 precision** | **44.5%** | 34.7% | **A leads** by 9.8 points |
| **GO 3–10 recall** | **14.9%** | 9.6% | **A leads** by 5.3 points |
| **GO 3–10 precision** | 11.0% | **15.2%** | A trails by 4.2 points |
| **GO 11–50 recall** | **4.1%** | 3.6% | **A leads** by 0.5 points |
| **GO 11–50 precision** | 4.7% | **4.9%** | A trails by 0.2 points |

**A leads on recall in three of the four fine cells and ties the fourth. It trails on precision in
three of the four**, by 0.2 to 4.2 points, which is the honest counterweight: HiDeF at a small k
produces fewer, tighter themes, so a higher share of what it emits matches a curated set, while a
much smaller share of curated biology gets recovered at all. A emits 6,244 themes against the best
HiDeF's 2,915 and recovers far more.

**Outside the fine bands the picture inverts and both are weak.** At Reactome 51–200 A leads on both
(7.7% / 22.7% against the oracle's 7.7% / 13.2%), and KC2 leads on recall alone at 11.5%. At
Reactome 201–500 **every HiDeF setting scores 33.3% recall and A scores 0.0%** — but that is one
curated set of three, so it is a coin-flip reported to one decimal place and should not be weighed.
Across GO's two coarse bands nothing reaches 1.2% recall.

**The one aggregate where HiDeF tuned wins is the eight-cell mean**, 0.1725 against 0.1667, and it
wins it by being better in the coarse bands where the denominators are 3 and 33 curated sets. On the
fine bands, where there are 470 and 174 Reactome sets and 1,906 and 634 GO sets, A is ahead on
recall everywhere. **A mean over eight cells with denominators spanning 3 to 1,906 is not a
measure I would decide anything on**, and the protocol's own rule is cell-by-cell with CIs, not a
mean — this grid is report-only and does not change it.

---

# 21:18:03Z — EXTENSION at the winning edge: k ∈ {3, 4, 5} × maxres ∈ {300, 500, 800}

The first grid's winner, k5/maxres300, sat at the corner with recall rising monotonically toward it
in both directions — a search pressed against its own boundary. This extends past it. Nine settings,
k5/300 reused, eight built. **No setting hit the 10-minute limit** (slowest 201 s), so nothing was
skipped. Combined with the first grid, **28 HiDeF settings** are now scored.

| k | maxres 300 | 500 | 800 |
|---|---|---|---|
| 3 | 142 s | 183 s | 201 s |
| 4 | 145 s | 181 s | 201 s |
| 5 | *reused* | 184 s | 201 s |

## Reactome, 674 curated sets — *recall / precision*

| setting | themes | 3–10 | 11–50 | 51–200 | 201–500 | **6-cell** | 8-cell |
|---|---|---|---|---|---|---|---|
| k3/300 | 3,342 | 50.4% / 34.0% | 40.8% / 33.5% | 0.0% / 4.3% | 33.3% / 12.5% | 0.1767 | 0.1742 |
| k3/500 | 4,262 | 54.5% / 35.1% | 41.9% / 34.2% | 3.9% / 2.2% | 0.0% / 10.0% | 0.1947 | 0.1460 |
| **k3/800** | 4,709 | **57.9%** / 34.8% | 40.8% / 31.0% | 0.0% / 2.1% | 0.0% / 0.0% | 0.1938 | 0.1454 |
| k4/300 | 3,110 | 48.3% / 35.3% | 44.8% / 35.0% | 0.0% / 11.4% | 33.3% / 12.5% | 0.1775 | 0.1748 |
| k4/500 | 3,919 | 53.6% / 35.3% | 44.8% / 34.7% | 3.9% / 8.9% | 33.3% / 10.0% | 0.1977 | 0.1899 |
| k4/800 | 4,406 | 55.5% / 34.7% | **45.4%** / 31.0% | 3.9% / 7.3% | 0.0% / 0.0% | 0.2050 | 0.1538 |
| k5/300 | 2,915 | 48.5% / **38.2%** | 38.5% / 28.7% | 3.9% / 5.8% | 33.3% / 14.3% | 0.1745 | 0.1725 |
| k5/500 | 3,712 | 52.5% / 35.7% | 42.5% / 31.7% | **7.7%** / 6.4% | 0.0% / 0.0% | 0.1971 | 0.1479 |
| **k5/800** ` *` | **4,287** | 54.9% / 33.4% | 44.8% / 33.2% | **7.7%** / 6.0% | 33.3% / 11.1% | **0.2082** | **0.1978** |
| **A (frozen)** | 6,244 | **60.6%** / 37.4% | **45.4%** / **44.5%** | **7.7%** / **22.7%** | 0.0% / 0.0% | **0.2222** | 0.1667 |
| **A top 4,287 by support** | 4,287 | 55.7% / **40.4%** | 39.7% / **49.8%** | **7.7%** / **26.7%** | 0.0% / 0.0% | 0.2003 | 0.1502 |

## GO, 2,758 curated sets

| setting | themes | 3–10 | 11–50 | 51–200 | 201–500 |
|---|---|---|---|---|---|
| k3/300 | 3,342 | 11.8% / 12.8% | 2.4% / 3.4% | 0.6% / 0.7% | 0.0% / 0.0% |
| k3/500 | 4,262 | 14.3% / 12.2% | 2.2% / 3.1% | 0.0% / 0.0% | 0.0% / 0.0% |
| **k3/800** | 4,709 | **15.6%** / 11.7% | 2.1% / 3.4% | 0.0% / 0.0% | 0.0% / 0.0% |
| k4/300 | 3,110 | 9.8% / 12.0% | 3.0% / 4.1% | 0.6% / 0.7% | 0.0% / 0.0% |
| k4/500 | 3,919 | 12.7% / 11.7% | 3.0% / 4.1% | 0.6% / 1.4% | 0.0% / 0.0% |
| k4/800 | 4,406 | 14.6% / 12.0% | 3.0% / **5.1%** | 0.6% / 0.6% | 0.0% / 0.0% |
| k5/300 | 2,915 | 9.6% / 12.5% | **3.6%** / 4.9% | 0.6% / 0.7% | 0.0% / 0.0% |
| k5/500 | 3,712 | 11.9% / 11.4% | 3.0% / 4.5% | 0.6% / 0.8% | 0.0% / 0.0% |
| **k5/800** ` *` | 4,287 | 13.8% / 11.6% | 3.1% / 4.4% | 0.6% / 0.7% | 0.0% / 0.0% |
| **A (frozen)** | 6,244 | 14.9% / 11.0% | **4.1%** / 4.7% | 0.6% / **5.1%** | 0.0% / 0.0% |
| **A top 4,287 by support** | 4,287 | 13.5% / 12.3% | 3.0% / 5.4% | 0.6% / **7.9%** | 0.0% / — |

## 21:18:03Z — the new best, and the mean that was carrying the first grid

**Best by the 6-cell mean (201–500 dropped): k5/maxres800 at 0.2082.** Best by the old 8-cell mean:
**the same setting, at 0.1978.**

**And dropping 201–500 reverses the first grid's headline.** On the six cells that have real
denominators, **A (frozen) leads every one of the 28 HiDeF settings: 0.2222 against the best 0.2082.**
The first grid reported HiDeF tuned beating A on the eight-cell mean, 0.1725 to 0.1667; that result
was being produced by the Reactome 201–500 cell, where three curated sets gave every HiDeF setting
33.3% and A 0.0%.

**That cell's instability is now visible directly.** Across the nine new settings it reads 33.3%,
0.0%, 0.0%, 33.3%, 33.3%, 0.0%, 33.3%, 0.0%, 33.3% — it flips with maxres at fixed k and with k at
fixed maxres. One of three sets, switching on and off, moved an aggregate that three reports have
quoted.

## 21:18:03Z — oracle over the full 28-setting grid

| cell | best recall | by | best precision | by |
|---|---|---|---|---|
| Reactome 3–10 | **57.9%** | k3/800 | 39.1% | k5/50 |
| Reactome 11–50 | 45.4% | k4/800 | 35.0% | k4/300 |
| Reactome 51–200 | 7.7% | k5/500 | 13.2% | k15/50 |
| Reactome 201–500 | 33.3% | k3/300 | 16.7% | k5/50 |
| GO 3–10 | **15.6%** | k3/800 | 15.2% | k5/25 |
| GO 11–50 | 3.6% | k5/300 | 5.1% | k4/800 |
| GO 51–200 | 1.2% | k30/100 | 1.6% | k5/50 |
| GO 201–500 | 0.0% | — | 0.0% | — |

**The oracle now takes GO 3–10 off A: 15.6% against A's 14.9%.** That is the first fine-level recall
cell any HiDeF configuration has won, and it took a 28-setting search to find it.

## 21:18:03Z — is recall still rising at the edge? Yes, everywhere

| k | Reactome 3–10, maxres 300 → 500 → 800 | GO 3–10 |
|---|---|---|
| 3 | 50.4% → 54.5% → **57.9%** | 11.8% → 14.3% → **15.6%** |
| 4 | 48.3% → 53.6% → 55.5% | 9.8% → 12.7% → 14.6% |
| 5 | 48.5% → 52.5% → 54.9% | 9.6% → 11.9% → 13.8% |

**Not saturated.** Every k is still climbing at maxres 800, and the gains are not shrinking much
(k3 Reactome adds 4.1 then 3.4 points). A further extension would very likely keep going, and the
best setting is *again* at a boundary — k3 wins both 3–10 recall cells, and k = 3 is the smallest k
in this extension. **The honest reading is that HiDeF's fine-level recall is bounded by how many
themes it is allowed to emit, not by a property of the method**, and the grid has been measuring
theme count by proxy.

## 21:18:03Z — matched theme count, N = 4,287

A's themes ranked by support, truncated to the best HiDeF's count. Ties broken toward the larger
theme, so truncation cannot silently prefer small ones and flatter the fine bands.

| cell | A, all 6,244 | **A, top 4,287** | HiDeF k5/800 (4,287) |
|---|---|---|---|
| Reactome 3–10 | 60.6% / 37.4% | **55.7% / 40.4%** | 54.9% / 33.4% |
| Reactome 11–50 | 45.4% / 44.5% | **39.7% / 49.8%** | 44.8% / 33.2% |
| Reactome 51–200 | 7.7% / 22.7% | **7.7% / 26.7%** | 7.7% / 6.0% |
| GO 3–10 | 14.9% / 11.0% | **13.5% / 12.3%** | 13.8% / 11.6% |
| GO 11–50 | 4.1% / 4.7% | **3.0% / 5.4%** | 3.1% / 4.4% |
| GO 51–200 | 0.6% / 5.1% | **0.6% / 7.9%** | 0.6% / 0.7% |
| **6-cell mean recall** | **0.2222** | **0.2003** | **0.2082** |

**Truncation costs A recall and buys it precision**, which is what ranking by support should do: the
themes it drops are the low-support ones, and they were contributing recall at a poor hit rate. A's
precision rises in all six cells, to 49.8% at Reactome 11–50 and 26.7% at 51–200.

## 21:18:03Z — does A's fine-level recall lead survive?

**(a) The wider grid: mostly, but it is no longer clean.** A still leads Reactome 3–10 recall,
**60.6% against the oracle's 57.9%** — a 12.1-point lead in the first grid has narrowed to 2.7. It
ties Reactome 11–50 at 45.4%. And it has **lost GO 3–10: 14.9% against k3/800's 15.6%**. On the
six-cell mean A still leads every setting, 0.2222 against 0.2082. So: leads two fine cells, ties
one, loses one — where before it led three and tied one.

**(b) The matched theme count: no, not on recall.** At N = 4,287 A scores 0.2003 against HiDeF's
0.2082, and loses three of the four fine recall cells — Reactome 11–50 (39.7% against 44.8%), GO
3–10 (13.5% against 13.8%), GO 11–50 (3.0% against 3.1%) — holding only Reactome 3–10 by 0.8 points.
**A's recall lead at full size is substantially a volume effect.**

**But precision goes the other way, and strongly.** At matched count A beats HiDeF in every one of
the six cells, several by large margins: Reactome 11–50 **49.8% against 33.2%**, Reactome 51–200
**26.7% against 6.0%**, GO 51–200 **7.9% against 0.7%**. So at equal theme count the two arms are
not close on the same axis: **HiDeF recovers slightly more curated sets, A's themes are far more
often real.** Which matters more is a question about what the ontology is for, and this grid is
report-only and does not answer it.
