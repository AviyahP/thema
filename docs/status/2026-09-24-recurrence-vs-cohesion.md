# Recurrence vs cohesion — what the sweep settled, 24 Sep 2026

*Companion to `DECISIONS.md` (24 Sep) and `docs/spec/amendment-2026-09-24b.md`. This note holds
the numbers; the decision and the chronology are there.*

**Outcome: recurrence is the only gate. Cohesion is descriptive. The 3–4 band is decided by
recurrence like every other stratum.**

---

## The run

Theta sweep, 6 sides (real + scrambles 0–4), five matching arms scored off one `prepare` per
side. **Real side 1,802 s; each null side 4,602–4,790 s. ~2h 40m wall at 4 concurrent, ~7.4 h
CPU.** Estimated at 75–85 min: wrong by ~2×, because a measurement carried over from an earlier
run had timed `prepare+score` together, and `score` is per-arm and not shareable.

Ran on the **21 Sep embeddings**, which still contain 4 pathways the universe rule excludes — see
`docs/status/OPEN.md`. Exploratory only.

## Cohesion separates at every size; it just does not select

Arm j070, real + 3 scrambles, real min against null max:

| stratum | real n | real min | null max | disjoint |
|---|---|---|---|---|
| 3 | 240 | 0.218 | 0.131 | **yes** |
| 4 | 221 | 0.163 | 0.110 | **yes** |
| 5 | 235 | 0.152 | 0.095 | **yes** |
| 6 | 369 | 0.174 | 0.087 | **yes** |
| 7–9 | 1,256 | 0.144 | 0.079 | **yes** |
| 10–14 | 2,114 | 0.140 | 0.062 | **yes** |
| 15–29 | 4,485 | 0.099 | 0.046 | **yes** |
| 30–49 | 2,763 | 0.101 | 0.027 | **yes** |
| 50–99 | 2,344 | 0.058 | 0.017 | **yes** |
| 100–199 | 1,169 | 0.048 | 0.009 | **yes** |
| 200+ | 587 | 0.017 | 0.005 | **yes** |

The single apparent failure — a coarse 30+ bin where real min 0.017 fell below null max 0.027 —
was a **binning artifact**: one bin compared 300-member themes against a null dominated by
40-member ones. Split, every stratum is disjoint. The 13 themes that looked exposed were candidate
families of **443–1,045 members**.

**And that is exactly why it cannot be the gate.** Calibrated at FDR ≤ 0.01 on seeds 0–2, held out
on seed 3, a cohesion-only gate keeps **15,783 of 15,783** candidate families (100%) in every
stratum, held-out FDR 0.0106. It distinguishes clusters-from-real-data from
clusters-from-scrambled-data, which is true of every real family.

## Support overlaps everywhere — and that was the wrong test

Real and scrambled support both run from 0.01 to the top in every stratum. Judged by disjointness
support "fails" universally. But **real data legitimately produces many non-recurring families,
and the threshold exists to remove them.** Support must be judged by a count-based rate at a
threshold.

Judged that way it reproduces the earlier results exactly — arm `floor`, cutoff 0.25:

| band | m | real | null per scramble | mean | FDR |
|---|---|---|---|---|---|
| 5–9 | 0.44 | **275** | 7, 4, 4, 3 | 4.50 | 0.0164 |
| 10–29 | 0.20 | **446** | 0, 0, 0, 0 | 0.00 | 0.0000 |
| 30+ | 0.20 | **75** | 0, 0, 0, 0 | 0.00 | 0.0000 |
| **total** | | **796** | | 4.50 | 0.0057 |

Against strict2's 275 / 446 / 75 on 20 scrambles. **Reproduced.**

## Why the per-theme design failed arithmetically

With no threshold every candidate family is a hypothesis, **m ≈ 16,000**. BY's factor is ≈ 10.3, so
the top theme needs `p ≤ 0.02/(16,000 × 10.3) ≈ 1e-7`. An empirical p-value cannot fall below
**1/(N+1) ≈ 1e-3**. Measured: **BY passes 0, BH passes 4,716** — mostly ties at the floor.
Closing that gap needs ~3,000 scrambles. **Build-level count FDR has no floor of this kind.**

## Candidate families entering the gate

Not an estimate — counted, per arm:

| arm | real families | null per scramble |
|---|---|---|
| floor | 17,020 | ~38,276 |
| j070 | 15,783 | ~38,591 |
| j074 | 16,120 | ~38,667 |
| j077 | 16,377 | ~38,339 |
| j080 | 16,684 | ~38,360 |

`j077` and `j080` produce **identical** results — Jaccard is discrete at small sizes and both fall
in the same gap, so the sweep had four effective arms, not five.
