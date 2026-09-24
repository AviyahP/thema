# Second amendment, 24 Sep 2026 — the per-theme design is withdrawn

*This withdraws the selection design pre-registered in `amendment-2026-09-24.md`. **That document
is NOT rewritten.** It records what was pre-registered and is the reason this one can be checked
against it.*

---

## What is withdrawn

From `amendment-2026-09-24.md` §4: one statistic (support), a size-conditioned empirical null, a
**per-theme p-value**, and **one correction across the build at q = 0.02** reporting BH and BY.
Also §5's demotion of cohesion from gate to descriptor, on the argument that Ward optimises
tightness so cohesion is not independent evidence.

**What survives:** Jaccard matching (§5), theta declared rather than derived, size stratification,
and the principle that thresholds are solved from a declared error rate rather than chosen.

## Why — measured, not argued

**1. Support does not separate by disjointness at any size, and that was never the right test.**
Real and scrambled support both run from 0.01 to the top of the range in every stratum. Judged as
the cohesion distributions were judged, support "fails" everywhere — but real data legitimately
produces many non-recurring families, and the threshold exists to remove them. Support must be
judged by a **count-based rate at a threshold**, not by overlap.

**2. The per-theme design is arithmetically impossible at this scale.** With no threshold, every
candidate family is a hypothesis: **m ≈ 16,000** rather than ~1,200. The top-ranked theme then
needs `p ≤ q/(m·c)`, about **1e-7** under BY. An empirical p-value cannot fall below
**1/(N+1) ≈ 1e-3**, set by the number of null draws. Reaching 1e-7 would need roughly **3,000
scrambles**. Measured: **BY passes zero themes; BH passes 4,716**, most of them tied at the floor
and accepted because the BH threshold rises with rank, not because they are individually
significant.

**The reviewer's error, recorded as such:** the per-theme design multiplied the hypothesis count
by ~14 while leaving p-value resolution fixed. Build-level count FDR has no such floor, which is
why the original design did not have this problem.

**3. Demoting cohesion conflated two things.** "The algorithm selects for tightness" is true;
"tightness therefore carries no information" does not follow. The **level achieved** still
discriminates, and the data show it: at every size from 3 to 200+ (with 30+ split into 30–49,
50–99, 100–199, 200+), **no scrambled candidate reaches the tightness of any real one**.

That is also why cohesion cannot be the gate. A gate that passes **15,783 of 15,783** candidates
at held-out FDR 0.0106 is not selecting; it distinguishes clusters-from-real-data from
clusters-from-scrambled-data, which is true of every real family.

**4. theta 0.77 and 0.80 are indistinguishable** on this data — Jaccard is discrete at small sizes
and both fall in the same gap. The sweep had four effective arms, not five.

## Also rejected: two gates

Cohesion for error control plus recurrence as a declared "granularity" parameter. Rejected twice
over. A declared `m` with no anchor is a hand-chosen parameter, which this project does not accept.
And **a cohesion gate applied to the null — as it must be, symmetrically — removes every null
candidate**, so the null count drops to zero and recurrence has nothing left to be solved from.
Cohesion as a gate does not merely fail to select: it destroys the other gate's anchor.

## What replaces it

**Recurrence is the only gate.** Stated in full in `DECISIONS.md` (24 Sep) and pre-registered for
the confirmatory run separately. In outline: support with Jaccard matching at **theta = 0.70**
applied identically to real and scrambled data; the scramble null **intact**, size-stratified, with
no cohesion filter on either side; **m(size) solved on calibration scrambles at count-based
FDR ≤ 0.01**, half the ceiling so there is margin, evaluated **once** on held-out scrambles against
0.02 per stratum and 0.01 overall; 20 calibration and 10 held-out scrambles; a stratum failing
held-out is dropped and nothing is re-solved afterwards.

**Cohesion is reported per theme as a descriptive number and decides nothing.** The spec carries
one sentence: *at every size, no scrambled candidate reaches the tightness of any real one.*

## What this amendment actually changed

**The design is the one from two days ago with its two mechanical defects fixed:** a match rule
that rounded to zero below size 7, and a threshold rule that sat on the boundary with no margin.
**Neither was a reason to change the statistic.** Everything between is recorded as the route by
which that was established, not as progress.
