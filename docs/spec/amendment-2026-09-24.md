# Amendment — the threshold structure is replaced by an empirical null test

*24 Sep 2026. **This amends `addendum-2026-09-21.md` step 9. That document is NOT rewritten:**
it records the rule that was pre-registered and what it produced, and that history is the point.
Read it first, then this.*

**Pre-registered: written before the test described at the end of this document was run.**

---

## 1. What the old rule was, and what it produced

Step 9 of the addendum selected themes by **size band** (3–4, 5–9, 10–29, 30+), each band with its
own recurrence threshold `m`, plus a **cohesion gate on the two small bands**. The cohesion
threshold began as *the null's 95th percentile at the same size* — a constant that admits 5% of the
null by construction — and was then replaced, on 23 Sep, by **c\*(s) = the smallest cohesion value
with FDR ≤ 0.02**, calibrated on 20 scrambles and evaluated once on 10 held-out scrambles.

It produced, at membership cutoff 0.25:

| stratum | c\* | real kept | calibration FDR | held-out FDR | verdict |
|---|---|---|---|---|---|
| size 3 | 0.122544 | 193 / 193 | 0.0199 | **0.0264** | fail |
| size 4 | 0.104334 | 141 / 141 | 0.0199 | **0.0220** | fail |

Leave-one-out over all 20 folds was **perfectly stable** — c\* varied in the fourth decimal and the
retained count never moved. The band was dropped under the failure branch declared in advance.

## 2. Why it is being replaced

**The rule was mechanically incapable of reaching the correct answer. That is a defect, not a
result we disliked.**

The real and scrambled cohesion distributions are **disjoint**:

| | n | min | median | max |
|---|---|---|---|---|
| real, size 3 | 193 | **0.2179** | 0.6344 | 0.8534 |
| scrambled, size 3 (20 scrambles pooled) | 3,805 | 0.0721 | 0.1001 | **0.1370** |
| real, size 4 | 141 | **0.3045** | 0.6056 | 0.8336 |
| scrambled, size 4 | 5,710 | 0.0615 | 0.0847 | **0.1160** |

The scrambled maximum lies **below** the real minimum at both sizes. Every real theme is tighter
than every scrambled theme produced across twenty scrambles. At any threshold between the null
maximum and the real minimum, **all real themes are retained and the false rate is 0.0000 on both
calibration and held-out.**

**The operative defect is the "smallest c" rule**, not the search grid. Verified from the saved
data: 77 null values at size 3 satisfy FDR ≤ 0.02 and **none lies above the null's maximum**, so an
unbounded grid would select the same 0.122544 — any larger value is, by definition, not smaller.
Real survival is flat at 100% from 0.1225 up to 0.2179, so the low end **buys no themes and spends
the entire margin**. Held-out then lands just over the line, exactly as the earlier 5% build did
(0.0500 in-sample → 0.0533 held out).

*(An earlier diagnosis in conversation attributed this to the grid ceiling. That was wrong and is
recorded here as wrong.)*

## 3. What makes this amendment legitimate

The test an amendment must pass is that it **cannot be tuned toward an outcome**:

- **It removes parameters rather than adding them.** Gone: four band boundaries, four per-band
  recurrence thresholds, the cohesion statistic as a gate, and the percentile-or-solved threshold
  behind it. The only remaining input is **q = 0.02**, declared weeks before any of this.
- **Selection is no longer a threshold anyone picks.** It is a p-value against an empirical null
  and one multiple-testing correction.
- **It is pre-registered before the test below runs.**

It is *not* legitimate because the old rule gave an answer we disliked. It is legitimate because
the old rule could not reach the right answer with any grid.

## 4. The replacement

**One statistic for every theme: support (recurrence).** No size bands in the criteria.

**Cohesion is demoted from gate to descriptor.** Ward's objective function *is* within-cluster
tightness, so recurrence and cohesion are not independent evidence — gating on both double-counts
the same signal. Cohesion is still computed and reported per theme; it decides nothing.

**The null** is the scramble through the identical pipeline, **conditioned on size**: a real theme
of size *s* is compared only to scrambled themes of size *s*.

**Empirical null p-value**, per theme:

```
p = (1 + scrambled themes of size s with support >= observed)
    / (1 + scrambled themes of size s)
```

**It is called an EMPIRICAL NULL p-value, not a permutation p-value, and the difference is
material.** A permutation test recomputes the statistic for the *same object* under relabelling.
Here a real theme's support is compared against the supports of *different objects* — themes
discovered in scrambled data. That is the correct null for a **discovery** procedure, because it
accounts for selection: the scrambled themes were found by the same search that found the real
ones. But it is not the stronger guarantee a permutation test gives, and must not be described as
one.

**The p-value floor is reported explicitly.** With *N* scrambled themes in a stratum, no p below
`1/(N+1)` can be claimed, whatever the data.

**One correction across the whole build at q = 0.02.** Both **BH** and **BY** are reported with
their **actual** cost. BY holds under arbitrary dependence, which matters here because themes
overlap and nest. BY is **not free**: its factor is `Σ(1/i)` over m themes, ≈ 7.7 at m ≈ 1,200, so
BY at q = 0.02 is roughly BH at q = 0.0026.

**Size bins, if the null needs them to have enough themes per stratum, are BINNING TO ESTIMATE THE
NULL and nothing else.** They are not criteria. The two uses of the word "band" are kept strictly
apart: the old bands applied *different rules* to different sizes; a null bin applies *the same
rule* and only pools the reference distribution. A reader must never have to work out which is
meant.

## 5. The matching rule

`allowed = tol * shared_count` is a float compared against integer counts, so the effective slack
is `floor(0.15 × size)` — **zero for every size from 3 to 6**, and 3 members at size 20. "Recurs"
therefore means *exact repetition* at small sizes and *15% drift* at large ones.

**Consequence for the record:** the earlier finding "285 real / 286 scrambled at 3–4 members" shows
only that **recurrence-under-exact-repetition** is uninformative at this size. It is *not* evidence
that recurrence carries no information there. That sentence in `addendum-2026-09-21.md` stands as
what was believed at the time and is corrected here.

**Replacement: Jaccard matching.** Two groupings match when `|A ∩ B| / |A ∪ B| >= theta`, applied
identically at every size.

### theta is a DECLARED parameter, not a derived one

The Jaccard equivalent to `tol = 0.15` two-sided is **a range, not a value**, because `floor()` is
discontinuous — over sizes 15–30 it runs **0.7391 to 0.8095**, mean 0.7707, jumping wherever
`floor(0.15s)` increments.

**A range cannot determine a parameter.** And the choice within it decides the size-3 question:

| case at size 3 | Jaccard | counts as recurring when |
|---|---|---|
| exact repeat | 1.00 | always |
| gains one member | **0.75** | **theta ≤ 0.75** |
| one member swapped | 0.50 | theta ≤ 0.50 |

Selecting theta = 0.74 — the permissive end — because it admits the size-3 case is **choosing the
value that produces the desired outcome and calling it a derivation**. It is refused on those
grounds, having been proposed in conversation and withdrawn.

**Primary analysis: theta = 0.70.** Justified in advance as a round, interpretable value — 70% of
the union shared — that sits **clear of every size-3 boundary case**, so no conclusion turns on a
tie. **It is explicitly NOT justified by equivalence to the old rule.**

**Known dependency, stated rather than discovered: the size-3 result is conditional on
theta ≤ 0.75.** Above that, a triple that gains a member does not count as recurring and size 3
returns to exact repetition.

## 6. The test this pre-registers

Real plus **5 scrambles**, all arms scored off **one** `prepare` per side, since `prepare` is the
expensive stage and is independent of the matching rule. Five scrambles is sufficient because this
is a question about the **bulk** of a distribution, not a tail estimate — the reasoning that
required 20 for the cohesion calibration does not apply.

**Arms — theta = 0.70 is primary and fixed now; the rest are sensitivity and are reported whatever
they show:**

| arm | role |
|---|---|
| **Jaccard theta = 0.70** | **PRIMARY** |
| Jaccard theta = 0.74 | sensitivity |
| Jaccard theta = 0.77 | sensitivity |
| Jaccard theta = 0.80 | sensitivity |
| current `floor(0.15 s)` rule | reference |

**Reported for sizes 3 and 4 under each arm:** whether the real and scrambled support distributions
separate, and the per-theme empirical null p-values under the scheme in §4.

**If a theta other than 0.70 is adopted after this table is seen, that is a post-hoc choice and
must be recorded as one** — not presented as the plan. This paragraph exists so that cannot be done
quietly.
