# Speed and evaluation — 5 Oct 2026

## LIVE STATUS
- **21:40 UTC** — COMPLETE. Parts A, B and C done; C6 estimated and skipped per its budget.
- running: nothing.
- ETA: n/a.
- last result: the thin middle is explained — the support gate removes **99.7%** of 51–500 candidates, and they fail **80.6% on missing members**.
- failures: two self-inflicted, both fixed — the floors writer overwrote the record it loaded, and `--floors-from` first cut the sides anyway.

---

# PART A — read-only answers

## A1. Does recurrence forgive MISSING shared members, or only extras?

**It forgives both.** The frozen build runs the `theta` branch, and `theta` is a Jaccard in which
missing members lower the numerator rather than disqualifying the pair. `src/thema/ontology/recurrent.py:478-489`:

```python
# TWO-SIDED. Missing: members this run drew but placed outside the cluster. Extras: cluster
# members the origin run drew that the grouping lacks. The one-sided rule tested only the
# second, and only after demanding the first be zero -- so a grouping whose members scatter was
# rejected before its extras were ever counted.
missing = shared_count - bits.count(cluster & g_s)
extras = bits.count(cluster & origin_present & ~grouping)
if theta is not None:
    # |A n C| = shared - missing;  |A u C| = shared + extras, both restricted to what the
    # origin run had, exactly as the tolerance rule restricts them.
    union = shared_count + extras
    return (union > 0 and (shared_count - missing) / union >= theta), cluster
return (missing <= allowed and extras <= allowed), cluster
```

The code's own comment records that an **earlier** one-sided rule demanded `missing == 0` before
counting extras, and that this was changed precisely because "a grouping whose members scatter was
rejected before its extras were ever counted".

### A finding: TOL = 0.15 does not affect the frozen build

`allowed = tol * shared_count` (line 477) is used **only** in the `theta is None` branch. The frozen
build's manifest records **both** `theta 0.7` and `tol 0.15`, and because `theta` is not None the
tolerance branch never executes. `tol` survives in one other place, the matching size-filter floor
(line 817), and that filter is **off by default** after it failed verification on 2 Oct.

**So `tol = 0.15` is inert in `recurrent_dag_10770`.** It is recorded in the manifest and in
`FROZEN.md` as though it were a live parameter. Nothing is wrong with the build; the record
overstates what governs it.

## A2. Where does DEFAULT_STRAY = 0.10 apply?

**Only in consensus merging** — specifically the `Rule.INHERITED` decision in
`consensus.classify()`, `src/thema/ontology/consensus.py:148-152`:

```python
strays_b = out_of_a / size_b
strays_a = out_of_b / size_a
if (strays_b <= stray or out_of_a <= STRAY_FLOOR) and strays_a > stray:
    return Rule.INHERITED, left_is_a
```

**Not** support counting, **not** seed absorption, **not** completion. It is passed in from exactly
one place, `scripts/build_10770.py:654`.

**A distinction worth stating:** seed absorption also uses 0.10, but it is a *different constant* --
`TWIN_FRACTION = 0.10` with `TWIN_FLOOR = 2` (`recurrent.py:100-101`), governing whether two
groupings are variants. Same number, different parameter, different stage. Changing one would not
change the other.

## A3. Where does DEFAULT_JACCARD = 0.70 apply?

**Only in consensus merging** — the `Rule.SUPERSEDED` decision, `consensus.py:154-156`:

```python
union = size_a + size_b - bits.count(a & b)
if union and bits.count(a & b) / union >= jaccard:
    return Rule.SUPERSEDED, left_is_a
```

Its declaration notes it is "the same value as the matching rule's theta, and declared for the same
reason: one notion of 'these are the same set' across the method" — but they are **separate
constants at separate stages**: `THETA` decides whether a grouping is *found in a run*;
`DEFAULT_JACCARD` decides whether two surviving themes are *the same theme*.

## A4. What does completion do? Does it extend groups to all 10,770?

**No. It does not assign the ~20% a run did not sample.** `family_members`,
`recurrent.py:1378-1402`:

```python
# One copy per run: where several family members were found in the same run, their copies are
# variants of each other, and the union is what that run actually saw of the family.
per_run: dict[int, np.ndarray] = {}
for g in family:
    for run, copy in pool.copies[g].items():
        per_run[run] = copy if run not in per_run else (per_run[run] | copy)
    for run in pool.origins[g]:
        if run not in per_run:
            per_run[run] = pool.groupings[g]
...
candidates = stack[0].copy()
for block in stack[1:]:
    candidates = candidates | block

inclusions: dict[int, float] = {}
for p in bits.unpack(candidates):
    holds = int(np.count_nonzero(stack[:, word] & bit))
    could = int(np.count_nonzero(records_present[runs][:, word] & bit))
    inclusions[p] = min(holds / could, 1.0) if could else 0.0
```

Three things follow:

1. **The candidate set is the UNION of the matched copies**, nothing wider. A pathway that appears
   in no copy of the family never becomes a candidate, however often it was drawn.
2. **Sampling loss is handled in the DENOMINATOR, not by assignment.** `could` counts only the runs
   that *actually drew* `p`. A run that never sampled a pathway "cannot be evidence either way", so
   it neither helps nor hurts that pathway's inclusion.
3. **Membership is then a majority vote**: `build_10770.py` keeps `inclusion >= INCLUSION_CUT`
   (0.50).

So completion **repairs sampling loss for pathways some run did place**, and extends nothing to
pathways absent from every copy. The name "completion" means completing a *grouping's* membership
from pooled evidence, not completing the *universe*.

## A5. What target FDR were the v0.3 floors calibrated to?

**FDR <= 0.01 overall, <= 0.02 per stratum.** Declared in
`docs/spec/amendment-2026-09-24c.md:12`:

> **Per-size floor `m_null`** solved from the scramble, calibrated at **FDR <= 0.01**

and line 65: "single-size strata at 3-6, FDR <= 0.01 calibrated against 0.02 per stratum and 0.01
overall". Implemented at `scripts/build_10770.py:72-73`:

```python
#: Error caps, declared: overall held-out FDR and the per-stratum ceiling.
MAX_FDR_OVERALL = 0.01
MAX_FDR_STRATUM = 0.02
```

**Achieved by the frozen build: 0.00285 overall, worst stratum 0.0147** — inside both caps, on 5
held-out scrambles read exactly once.


---

# PART B — calibrate once, and exact speed-ups

## B1. Calibrate once

**The floors were already persisted**, with full provenance, at
`data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/floors_r1-200_n200.json`
— carrying the solved floor and effective threshold per stratum, the 10 calibration seeds, the 5
held-out seeds, the per-stratum held-out FDR and the overall 0.00285.

**`--floors-from <file>`** loads them and **does not cut the ten calibration sides at all**. It
refuses outright if the stored configuration differs on any of `n`, `runs`, `scramble_rows`,
`size_cap`, `inclusion_cut`, `universe_digest` or `space` — the floors are a property of one null at
one configuration, and a mismatch means the stored null describes a different population.

**`--check-heldout <seed>`** cuts ONE held-out side and reports its FDR against the loaded floors.
**Nothing is re-solved from it**, so it cannot launder a stored floor into a fitted one. Measured on
seed 4001: **overall FDR 0.0017 against the 0.01 cap — CHECK PASSES.**

### Byte-identity

| rebuild | nodes | members | edges | unplaced |
|---|---|---|---|---|
| stored floors | **identical** | **identical** | **identical** | **identical** |
| stored floors + B2 | **identical** | **identical** | **identical** | **identical** |
| stored floors + B2 + held-out check | **identical** | **identical** | **identical** | **identical** |

All against the frozen `recurrent_dag_10770`, by `cmp`.

### A self-inflicted fault, found and fixed

The first `--floors-from` run **still cut all ten calibration sides** before overriding the floors,
so it saved nothing. The provenance guard caught it by refusing sides written by older code.

Worse, the floors writer then **overwrote the very file it had loaded**, replacing
`overall_fdr 0.00285` and every per-stratum held-out number with `null` — destroying the record of
the one-and-only held-out confirmation. A faithful copy survived inside
`freeze_confirmatory.json` (the freeze table embeds the whole floors dict), so the file was restored
from data rather than retyped from the report.

**The writer now refuses to overwrite**: a run that LOADED its floors never rewrites them, and a run
that solved its own writes only where no file exists.

## B2. Exact speed-ups (2-hour time box)

**Profiled first, because I had guessed wrong twice before.** `cProfile` on `families` at the 1,850
scale named the hot spot unambiguously:

```
19324    0.531    1.932  {built-in method numpy.fromiter}
14783823 1.402    1.402  recurrent.py:1268(<genexpr>)
```

**14,783,823 calls to a generator inside `np.fromiter` — 48% of `families`.** It was this line:

```python
rows = np.fromiter((row_of[int(g)] for g in near), dtype=np.int64, count=len(near))
```

The posting arrays held grouping **IDS**, mapped to **ROW** indices one Python `int` at a time, once
per candidate per seed.

**The fix is exact and structural**: the index is rewritten from ids to rows **once**, in NumPy, with
a single fancy-index per pathway (~800,000 elements total). The seed loop then has nothing to map.
This also removes the last place where ids and rows were both in play — the confusion that cost a
variant on 2 Oct now cannot recur, because the conversion happens in exactly one line.

**What I did NOT do**: the brief suggested an LCA query instead of ancestor walks. The ancestor walk
lives in `_score_tree`, the reference path; the build runs `_score_matrix`, which already replaces
walks with sparse products. An LCA would optimise code the build does not execute. Precomputed
per-run counts are also already there (`ready.overlap`). Matching is 198–200 s and essentially
unchanged; **no exact win was found in it inside the time box, and nothing approximate was tried.**

### Measured, and byte-identical on two independent sides

| side | stage | before | after | |
|---|---|---|---|---|
| real, trees 1–200 | families | 254 s | **45 s** | 5.6x |
| | matching | 157 s | 160 s | — |
| | completion | 43 s | 30 s | — |
| | **total** | **486 s** | **277 s** | **1.75x** |
| | peak | 13.6 GB | **7.8 GB** | |
| held-out, seed 4001 | families | 430 s | **142 s** | 3.0x |
| | matching | 205 s | 198 s | — |
| | **total** | **702 s** | **406 s** | **1.73x** |
| | peak | 6.5 GB | 6.7 GB | |

**Both sides reproduce their cached `.npz` byte-for-byte.** The real side's `families` gains more
because it has fewer, larger families; the ratio is not constant across sides and both are reported
rather than the better one.

## B3. Timing table

"Cold" means no cached completions — the honest cost of producing the build from persisted trees.
"Warm" means the sides already cut, which is what a re-cut at a different cutoff or cap would pay.

| configuration | sides cut | cold wall | cold peak | warm wall | warm peak |
|---|---|---|---|---|---|
| **frozen build, as originally run** | 1 real + 10 calibration | **~10,157 s (2.82 h)** | 21.0 GB | 81 s | 6.4 GB |
| stored floors | 1 real | ~567 s (9.5 min) | 13.6 GB | 81 s | 6.4 GB |
| **stored floors + B2** | 1 real | **~358 s (6.0 min)** | **7.8 GB** | **67 s** | **2.6 GB** |
| stored floors + B2 + one held-out check | 1 real + 1 held-out | ~764 s (12.7 min) | 7.8 GB | 69 s | 5.2 GB |

**Cold totals are measured per-side times summed, not a stopwatch on one run**: the real side
(486 s before, 277 s after), the ten calibration sides at a median 959 s each as originally cut, the
held-out side (406 s), plus the measured 81 s / 67 s tail for gate, consensus, Hasse and export.

**28x cheaper to reproduce the frozen build**, 2.82 h to 6.0 min, byte-identically. Almost all of it
is calibrate-once: not cutting ten scramble sides saves ~9,590 s, and B2 saves a further ~209 s on
the one remaining side.

### Stage profile, per side

| stage | real side, as originally cut | real side, B2 | held-out side, B2 | share after B2 |
|---|---|---|---|---|
| load trees + cap | 11.3 s | 11.3 s | 9.7 s | 4% |
| prepare (dedup + eligibility) | 10.7 s | 10.7 s | 12.7 s | 4% |
| **matching (support)** | 157 s | **160 s** | **198 s** | **54%** |
| completion | 43 s | 30 s | 30 s | 11% |
| **families (seed absorption)** | **254 s** | **45 s** | **142 s** | **22%** |
| family support + selection | 7.8 s | 7.8 s | 13.6 s | 3% |

**Matching is now the dominant stage**, having been second to families all along. That is where any
further exact work should go, and I found none inside the box.


---

# PART C — completing the THEMA vs HiDeF evaluation

Arms: THEMA frozen, HiDeF k15 maxres 25 (declared), HiDeF k15 maxres 50 (best post hoc).
**Every CI below uses the cluster bootstrap over curated parents**, 2,000 resamples, seed 0.
Practical-equivalence margin **±0.02 AUROC**.

## C1. The verdict, recorded

Added to `DECISIONS.md`, 5 Oct, quoting the four cells and both recovery numbers from the 4 Oct
report. **THEMA stays; HiDeF and CliXO are baselines** — and the entry states plainly that it is not
a clean win, that CliXO is a baseline in name only because it was never obtainable, and what THEMA
still has that HiDeF does not.

## C2. POST-HOC SENSITIVITY: the cluster bootstrap. Cannot change the verdict.

**The pair bootstrap understated the uncertainty by roughly 7x**, exactly as the brief anticipated.
Reactome zero-gene: pair CI width 0.013, cluster CI width 0.140.

**Declared arm, HiDeF k15 maxres 25:**

| cell | n pairs | parents | diff | cluster CI | reading vs ±0.02 |
|---|---|---|---|---|---|
| Reactome, zero-gene | 5,753 | 285 | −0.0943 | [−0.1433, −0.0030] | **THEMA better** |
| Reactome, pooled | 9,396 | 632 | −0.0599 | [−0.1106, **−0.0001**] | **THEMA better** |
| GO, zero-gene | 19,828 | 1,370 | +0.0081 | [−0.0139, +0.0331] | inconclusive |
| GO, pooled | 45,832 | 2,370 | +0.0173 | [+0.0001, +0.0361] | HiDeF better |

**The declared verdict survives the better bootstrap**: still 2 of 4 cells with THEMA significantly
better. But Reactome pooled now excludes zero by **0.0001** — it is on the boundary, and a different
seed could plausibly move it.

**Post-hoc arm, maxres 50:** 0 of 4 cells have THEMA significantly better (Reactome zero-gene
[−0.0591, +0.0140], Reactome pooled [−0.0470, +0.0093], GO zero-gene [−0.0054, +0.0355], GO pooled
[+0.0085, +0.0390]), and recovery is within tolerance on both hierarchies (−0.1 and +6.1 points).

> **Mechanically, the rule's conditions WOULD be met by maxres 50 under the cluster bootstrap.**

**That is not a verdict and must not be read as one.** It requires *two* departures from the
declaration at once — a non-declared parameter and a non-declared bootstrap — and §0 fixes the
verdict on the declared run. The script now **refuses to print a verdict** for any arm or bootstrap
that is not the declared pair, so this cannot be misread from a log. What it does say honestly is
that **the declared verdict is less robust than the 4 Oct report made it look.**

**No cell anywhere reads "equivalent"**: the cluster CIs are too wide to establish practical
equivalence at ±0.02, in either direction.

## C3. Granularity-matched comparison

Restricting the smallest-shared-theme search to themes inside each size band asks both arms the same
question at the same grain.

**Reactome siblings, zero-gene** (AUROC / recovery):

| theme band | THEMA | HiDeF m25 | HiDeF m50 | reading (m25 − THEMA) |
|---|---|---|---|---|
| 3–10 | **0.5466** / 9.3% | 0.5000 / 0.0% | 0.5002 / 0.0% | THEMA better [−0.0873, −0.0278] |
| 11–50 | **0.5970** / 19.5% | 0.5555 / 11.2% | 0.5802 / 16.2% | THEMA better [−0.0989, −0.0191] |
| 51–200 | 0.5760 / 15.5% | **0.6403** / 28.8% | 0.6428 / 29.3% | **HiDeF better** [+0.0461, +0.1100] |
| 201–500 | 0.5400 / 8.1% | **0.6249** / 26.7% | 0.5878 / 19.0% | **HiDeF better** |

**GO siblings, zero-gene:**

| theme band | THEMA | HiDeF m25 | reading |
|---|---|---|---|
| 3–10 | **0.5064** / 1.3% | 0.5000 / 0.0% | equivalent [−0.0085, −0.0050] |
| 11–50 | **0.5158** / 3.3% | 0.5093 / 1.9% | equivalent [−0.0093, −0.0044] |
| 51–200 | 0.5162 / 3.5% | **0.5455** / 9.9% | **HiDeF better** [+0.0234, +0.0353] |

**One line:** the comparison is not a contest between methods but between grains — **THEMA wins at
≤50 members on both hierarchies, HiDeF wins at ≥51 on both**, and the sign flips in the same place
every time.

## C4. Why GO favours HiDeF — H1 refuted, H2 explains it entirely

Baseline gap at zero gene overlap: **GO +0.0081**, Reactome **−0.0943**.

### (a) AUROC gap per stratum, GO, zero-gene

| stratum | n | gap |
|---|---|---|
| curated parent size Q1 (smallest) | 5,068 | **+0.0459** |
| Q2 | 4,911 | +0.0343 |
| Q3 | 5,028 | −0.0158 |
| Q4 (largest) | 4,821 | **−0.0333** |
| fan-out ≤6 | 916 | **+0.0386** |
| fan-out 7–20 | 3,509 | **+0.0417** |
| fan-out >20 | 15,403 | −0.0014 |
| pair cosine Q1 (lowest) | 4,957 | +0.0065 |
| pair cosine Q4 (highest) | 4,957 | **+0.0325** |

**H1 is refuted by its own predicted strata.** H1 said the advantage would concentrate in pairs with
*large* parents, *high* fan-out and *low* cosine. It concentrates in the opposite of all three:
small parents, low fan-out, high cosine. HiDeF's GO advantage is on **tight, coherent** sibling
groups, not loose ones.

### (b) and (c) Hypothesis counts and decomposition

| hypothesis | GO pairs | gap with them removed | share of gap explained |
|---|---|---|---|
| **H2 thin middle** | 2,253 | **−0.0115** | **242%** (over-explains: the sign flips) |
| H3 unplaced / root-only | 549 | +0.0038 | 53% |
| H2 ∩ H3 | 39 | — | **shares are not additive** |

On Reactome the same removal *widens* THEMA's lead (−0.0943 → −0.1243), i.e. the thin-middle pairs
are where HiDeF does relatively best there too.

### (d) One plain line

**H2 explains the whole GO gap and more**: removing the 2,253 pairs HiDeF places in a 51–500 theme
while THEMA has nothing tighter than 500 turns +0.0081 into −0.0115. H3 explains about half but is
only 549 pairs. **H1 is refuted.**

## C5. Middle-level diagnosis

### (a) Themes per size band

| arm | 3–10 | 11–50 | 51–200 | 201–500 | 501–3,125 | >3,125 | total |
|---|---|---|---|---|---|---|---|
| **THEMA** | 3,675 | 2,421 | **138** | **3** | 5 | 2 | 6,244 |
| HiDeF m25 | 5 | 200 | 211 | 38 | 16 | 2 | 472 |
| HiDeF m50 | 20 | 396 | 206 | 38 | 17 | 2 | 679 |
| HiDeF m100 | 121 | 650 | 198 | 38 | 17 | 2 | 1,026 |

**Themes of 51–500 members: THEMA 141 (2.3% of its themes), HiDeF m25 249 (52.8%).** The two arms
are nearly disjoint in grain: THEMA puts 98% of its themes below 51 members, HiDeF puts 43% above.

### (b) Recurrence failure analysis, real Ward runs

1,000 failing groupings sampled per band (seed 20261005), every failed (grouping, run) check
classified.

| band | checks | missing members | extras over tol | not eligible |
|---|---|---|---|---|
| **51–500** | 197,173 | **158,936 (80.6%)** | 38,237 (19.4%) | 0 (0.0%) |
| 3–50 | 179,422 | 54,449 (30.3%) | **115,540 (64.4%)** | 9,433 (5.3%) |

**The failure mode inverts with size.** Mid-size groupings fail because their members **scatter**:
the smallest cluster of the other run containing all the shared members is far too big, so the
Jaccard dies on the missing term. Small groupings fail the other way, on extras. Eligibility is
never the binding constraint for mid-size candidates — **0.0%**.

### (c) Where mid-size candidates are lost

| stage | 51–500 candidates surviving |
|---|---|
| in the pool | 48,836 |
| completed | 45,461 |
| **through the support gate** | **140** |
| after consensus, in the build | 141 |

**The support gate removes 99.7% of them.** The size cap removes essentially nothing (22 completed
families over 3,125, at any size), and consensus *adds* one. **One plain line: THEMA's middle is thin
because mid-size groupings do not recur under 80% resampling — their members scatter across the other
run's clusters — and the support floor is doing exactly what it was calibrated to do.**

## C6. Fair stability comparison — ESTIMATED AND SKIPPED

Every figure below is measured elsewhere in this run.

| component | measured | per subsample arm |
|---|---|---|
| 200 Ward trees | 0.58 s/tree | 116 s |
| one real side | 277 s (B2) | 277 s |
| 10 calibration sides | 406 s each (B2) | 4,060 s |
| gate + consensus + export | 67 s | 67 s |
| **one arm** | | **4,520 s (1.26 h)** |
| **two arms** | | **9,040 s (2.51 h)** |

**The stored floors do not transfer**: they record `n = 10,770` and the subsample universe is 8,616,
so `--floors-from` refuses by design. Calibration must be redone at the subsample size, and that is
essentially the whole cost.

**2.51 h exceeds the 2-hour budget the brief sets, so C6 was skipped and the estimate reported**, as
instructed.

### The like-for-like pair, which exists already

| comparison | perturbation | worse direction |
|---|---|---|
| THEMA | two 200-tree halves, same data | **87.9%** |
| HiDeF k15 | two Leiden seeds, same graph | **86.0%** |
| HiDeF k15 | two independent 80% subsamples | 57.0% |

**The first two are the fair same-data pair and they are close.** THEMA's 87.9% against HiDeF's
57.0% is not a like-for-like comparison and should not be quoted as one: THEMA's figure averages 200
subsamples inside each arm before comparing, HiDeF's compares two single draws.

## C7. Hashing feasibility — measurement only

500 groupings at support ≥ 0.5 (seed 20261005), every distinct copy pair.

| reading | pairs | median J | share ≥ 0.70 |
|---|---|---|---|
| **(a) raw sampled members** | 4,598,091 | **0.633** | **36.6%** |
| (b) copy vs completed family set | 66,305 | 0.778 | 70.6% |

The sampling-only expectation for a perfectly stable group is **0.667**, and the observed median is
**0.633** — i.e. copies are barely less similar than pure 80%-sampling noise predicts.

**(b) as literally specified does not exist.** A4 established that completion does not produce
full-universe members; the nearest measurable quantity is reported in its place and labelled.

**One plain line: no. A single global fingerprint at Jaccard ≥ 0.70 would recover 36.6% of true copy
pairs and miss 63.4%.** The build's rule is not a plain Jaccard on raw members — it restricts both
sides to what the origin run drew, which is precisely the correction a global fingerprint cannot
make.

## The compute-line amendment

Applied to the 5 Oct verdict entry as a labelled `AMENDED` block beneath the original sentence,
**not as a rewrite** — the 50x stands as the historical figure, because it was true of the build as
originally run and of every cost statement made before today. The measured replacement is in the
table in that entry and summarised in point 5 below. **No number above the compute line moves.**

## C8. Related work

**No related-work or defence document existed**; `docs/spec/related-work.md` was created. It adds one
cited line each for HiDeF (Zheng et al. 2021), CliXO (Kramer et al. 2014), DDOT (Yu et al. 2019),
MuSIC (Qin et al. 2021), multimodal cell maps (Schaffer et al. 2025 — the precedent for running
HiDeF on *embeddings* rather than a measured network), and **Bravi et al., arXiv:2608.28178** —
concurrent, Reactome-only, tree-shaped, and the closest published result to THEMA's central claim.
Plus a one-line HiDeF verdict.

---

# What the evaluation now says

## The declared verdict

**THEMA stays.** Under the rule written before the build: significantly better on both Reactome
specificity cells, and HiDeF misses the zero-gene recovery tolerance on Reactome by 9.9 points.
**This survives the statistically correct cluster bootstrap** — still 2 of 4 cells.

## Post-hoc sensitivities, none of which change it

1. **The pair bootstrap understated uncertainty ~7x.** The verdict holds under the cluster
   bootstrap, but **Reactome pooled now excludes zero by 0.0001** — the declared verdict is on a
   boundary, not comfortable.
2. **maxres 50 + cluster bootstrap would mechanically meet the rule's conditions.** Two departures
   from the declaration at once; not a verdict, and the tooling now refuses to print one.
3. **The contest is about grain, not quality.** THEMA wins ≤50 members, HiDeF wins ≥51, on both
   hierarchies, every time.
4. **The GO gap is entirely the thin middle.** H1 refuted by its own strata; H2 over-explains.
5. **THEMA is now ~4x the cost of HiDeF, not 50x** (Part B), plus one-time calibration. The
   verdict entry's compute line is amended accordingly, measured: 116 s trees + 277 s side + 67 s
   tail = **~460 s against HiDeF's 126 s**, with calibration at **~1.1 h per configuration**. The
   original 50x is kept as the historical figure, since it was true of every cost statement made
   before today.

## Open questions

1. **The middle is a calibration consequence, not a bug.** 99.7% of 51–500 candidates die at the
   support gate because mid-size groupings do not recur under 80% resampling (80.6% missing-member
   failures). Whether the subsample fraction, `TOL`, or the per-size floors should differ for
   mid-size candidates is a declared-parameter question and untouched.
2. **`TOL = 0.15` is inert** and recorded as though live, in both the manifest and `FROZEN.md`.
3. **Reactome pooled at CI upper bound −0.0001.** The verdict should not rest on one cell this close;
   more curated parents, or a stated tolerance, would settle it.
4. **C6 unbuilt** at an estimated 2.51 h — the one comparison that would make the stability numbers
   like-for-like.
5. **CliXO still unobtainable**, and Bravi et al. (concurrent) is unevaluated against THEMA on
   Reactome, where it is the strongest baseline.

---

# Working tree, before the commit block

Three things a reader of `git status` should not have to work out.

**1. One record WAS overwritten, against the convention. Flagging it rather than hiding it.**
Re-cutting the real side under B2 wrote its timings to the same key, so
`real_r00001-00200.stages.json` and `seed04001_n200.stages.json` now hold the B2 numbers and the
pre-B2 ones survive only in git history and in the B3 table above. Nothing output-affecting moved —
the build is byte-identical, and the provenance digest is what guards that — but the stage side-car
is a record and I replaced it in place. The B3 table quotes both numbers precisely so the comparison
is not lost.

**2. The three verification build directories should NOT be committed.**
`recurrent_dag_10770_b2/`, `_b2check/` and `_storedfloors/` are byte-identical copies of the frozen
build; committing them would add three redundant copies of a build already in the repository. Their
value is the comparison, which is in the B3 table. **Recommend `rm -rf` on all three, or leave them
untracked.** They are *not* gitignored — `.gitignore:46` re-includes `data/ontology/v*/*/*.tsv` — so
a bare `git add data/ontology` would sweep them in. The block below names every path explicitly for
that reason.

**3. Uncommitted work from the earlier briefs is still in the tree and is not mine to commit here.**
The naming-track files (`scripts/name_themes.py`, `src/thema/naming.py`, `src/thema/data/names.py`,
`tests/test_naming.py`, `data/theme_names.tsv`), the 3 Oct report, and the whole 4 Oct HiDeF
comparison (`scripts/build_hidef.py`, the `hidef_*` build directories,
`docs/status/2026-10-04-hidef-comparison.md`) are all untracked or modified. The 4 Oct report
carries its own commit block. **None of them is in the block below.**

The one file that straddles the two is `scripts/hidef_decision.py`: created on 4 Oct, and changed
today for C2 (the cluster bootstrap, the equivalence margin, the verdict guard). **It is in the
block below**, so whichever block runs second will find it already staged — harmless, but worth
knowing before you paste.

# COMMIT BLOCKS

I ran no git commands.

```sh
git add \
  DECISIONS.md \
  docs/spec/related-work.md \
  docs/status/2026-10-05-speed-and-evaluation.md \
  src/thema/ontology/recurrent.py \
  scripts/build_10770.py \
  scripts/hidef_decision.py \
  scripts/granularity_bands.py \
  scripts/middle_diagnosis.py \
  scripts/hashing_feasibility.py \
  data/experiments/granularity_bands_c3.tsv

git commit -m "Calibrate once, an exact 1.75x on every side, and the HiDeF verdict" -m "PART A, read-only, answered from quoted code. Recurrence forgives BOTH missing
and extra members: the frozen build runs the theta branch, where missing lowers
the numerator rather than disqualifying. A finding falls out of that -- TOL = 0.15
is INERT in the frozen build, used only in the theta-is-None branch, yet recorded
in the manifest and FROZEN.md as though it governed something. DEFAULT_STRAY and
DEFAULT_JACCARD apply only in consensus merging, and seed absorption uses a
different 0.10 (TWIN_FRACTION). Completion does NOT extend groups to the full
universe: candidates are the union of matched copies, and unsampled pathways are
handled in the inclusion denominator, not by assignment. Floors were calibrated at
FDR <= 0.01 overall and 0.02 per stratum.

PART B. --floors-from loads stored floors and does not cut the ten calibration
sides at all; it refuses outright if the stored configuration differs on any of
n, runs, scramble_rows, size_cap, inclusion_cut, universe_digest or space.
--check-heldout cuts ONE held-out side and reports its FDR against them, with
nothing re-solved: seed 4001 gives 0.0017 against the 0.01 cap.

An exact speed-up, found by profiling rather than guessing: 14,783,823 generator
calls inside np.fromiter, 48% of the families stage, mapping grouping ids to row
indices one Python int at a time. The index is now converted once in NumPy, which
also removes the last place ids and rows were both in play. families 254s to 45s
on the real side and 430s to 142s on a scramble side; each side 1.75x and 1.73x
faster at 7.8 GB instead of 13.6 GB.

A full rebuild is 2.82 h to 6.0 min cold, 28x, and BYTE-IDENTICAL to the frozen
build on nodes, members, edges and unplaced in all three configurations.

Matching is now the dominant stage at 54%. No exact win was found in it inside the
time box, and nothing approximate was tried. The brief's LCA suggestion targets
_score_tree, the reference path; the build runs _score_matrix, which already uses
sparse products.

PART C. The verdict is recorded: THEMA stays, HiDeF and CliXO are baselines.

It survives the cluster bootstrap -- the statistically correct one, since pairs in
a sibling group are not independent -- but the pair bootstrap had understated
uncertainty about 7x, and Reactome pooled now excludes zero by 0.0001. The
declared verdict sits on a boundary. maxres 50 under the cluster bootstrap would
mechanically meet the rule conditions, which is TWO departures from the
declaration at once and not a verdict; hidef_decision.py now refuses to print a
verdict for any arm or bootstrap that is not the declared pair.

The contest turns out to be about GRAIN. THEMA wins themes of 3-50 members on both
hierarchies, HiDeF wins 51-500 on both, and the sign flips in the same place every
time. THEMA has 141 themes of 51-500 (2.3%) against HiDeF's 249 (52.8%).

Of three hypotheses declared before looking, H1 is REFUTED BY ITS OWN PREDICTED
STRATA: the GO advantage concentrates in small parents, low fan-out and high
cosine, the opposite of loose siblings. H2, the thin middle, over-explains the gap
-- removing the 2,253 pairs HiDeF places in a 51-500 theme flips GO from +0.0081
to -0.0115.

And the middle is explained mechanistically. The support gate removes 99.7% of
51-500 candidates, and 80.6% of their failed checks are MISSING MEMBERS against
30.3% for small groupings: mid-size groups scatter across the other run's
clusters, so the smallest cluster containing their shared members is too big. The
floor is doing what it was calibrated to do.

Hashing is not feasible: one global fingerprint at Jaccard >= 0.70 recovers 36.6%
of true copy pairs and misses 63.4%, with copies at median 0.633 against the 0.667
that 80% sampling alone predicts. The build's rule restricts both sides to what the
origin run drew, which is the correction a fingerprint cannot make.

C6 was estimated at 2.51 h from measured per-side times, exceeding its 2-hour
budget, and skipped as the brief directs.

docs/spec/related-work.md is NEW -- no related-work or defence document existed --
and cites HiDeF, CliXO, DDOT, MuSIC, Schaffer et al. 2025 for HiDeF on embeddings,
and Bravi et al. arXiv:2608.28178 as concurrent Reactome-only tree-shaped work.

TWO SELF-INFLICTED FAULTS, both fixed. --floors-from first loaded the floors but
still cut all ten calibration sides, saving nothing; the provenance guard caught
it. Then the floors writer OVERWROTE the file it had loaded, replacing
overall_fdr 0.00285 and every per-stratum held-out number with null. A faithful
copy survived inside freeze_confirmatory.json, so it was restored from data rather
than retyped. The writer now refuses: a run that loaded its floors never rewrites
them."
```
