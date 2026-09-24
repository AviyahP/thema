# Third amendment, 24 Sep 2026 — the confirmatory calibration, pre-registered

*Locked before the run. Supersedes the selection design in `amendment-2026-09-24.md`, which
`amendment-2026-09-24b.md` withdrew. Neither earlier document is rewritten.*

---

## The rule, verbatim

- **Declared `m` = 0.33 at every size**, the same value as the earlier builds. Reported with
  sensitivity at **0.20, 0.25, 0.40 — reported, not used.**
- **Per-size floor `m_null`** solved from the scramble, calibrated at **FDR ≤ 0.01**, evaluated
  **once** on held-out against **0.02 per stratum** and **0.01 overall**.
- **Effective threshold = max(declared m, floor).**
- **Jaccard theta = 0.70 declared**; 0.74 and 0.77 reported as **sensitivity only**.
- **Strata** as in the six-side table, **single sizes at 3–6**: 3, 4, 5, 6, 7–9, 10–14, 15–29,
  30–49, 50–99, 100–199, 200+. **No stratum is merged.** If size 5 fails on 30 scrambles the
  declared branch drops it and that is the result.
- **20 calibration scrambles, 10 held-out.**
- **Cohesion is descriptive only. Never a gate.**

## Failure branches, declared now

| condition | consequence |
|---|---|
| a stratum's held-out rate exceeds **0.02** | that stratum is **dropped** |
| the overall build exceeds **0.01** held-out | **no freeze** |

**Nothing is re-solved after held-out.** No threshold, no stratum boundary, no theta.

## What this is

The design that gated every band before this week, with its **two mechanical defects fixed**: a
match rule that rounded to zero below size 7 (now Jaccard, uniform at every size), and a threshold
rule that sat on the boundary with no margin (now calibrated at half the ceiling). Neither defect
was a reason to change the statistic, and the statistic has not changed.

`max(declared, floor)` is what keeps the declared value honest: 0.33 is carried over from the
earlier builds rather than chosen now, and the floor only ever raises it where the null demands
more. A stratum whose null requires less than 0.33 still gets 0.33.

## Run

One arm (theta 0.70) on the **1,850-row universe artifact**, 31 sides: 1 real, 20 calibration,
10 held-out. Sensitivity arms are scored from the same sides.

Reported per stratum and overall. **That result goes in the spec and is the procedure the 10,770
rebuild uses unchanged.**

## Scramble counts at 10,770 — declared before the run

**The 1,850-pathway calibration uses 20 + 10.** The 10,770 rebuild uses **10 calibration and 5
held-out**, declared here rather than chosen after seeing a runtime.

**Reason.** The floor is solved from **counts**, not from a tail quantile, and each stratum at
10,770 holds roughly **six times more null families** than at 1,850 — so a single scramble
contributes proportionally more evidence to the same count-based estimate. The argument that
required 20 at this scale (a thin tail) weakens as the pool grows.

**The cost that forces the question.** Matching cost scales with pool × runs, so 5.8× the pathways
is ~6–8× per side: 30 scrambles is ~150 CPU hours and ~38 h wall at four concurrent. 15 scrambles
is ~19 h.

Every other clause of this amendment — declared m = 0.33, `max(declared, floor)`, theta 0.70,
single-size strata at 3–6, FDR ≤ 0.01 calibrated against 0.02 per stratum and 0.01 overall, and
the failure branches — applies unchanged at 10,770.
