# Choosing the inclusion cutoff: 0.25 / 0.33 / 0.50

*28 Sep 2026. CPU only, $0.00. Measurement for a decision that is Aviyah's; no cutoff is adopted
here and no naming has been run.*

## 1. The straddler histogram, on the frozen 0.25 centred build

A pathway's **homes** are the MINIMAL themes containing it. Nested themes are one home at two
granularities, not two homes, so this counts only genuine straddling.

```
pathways placed                   1,842
with >= 2 non-nested homes          852  (46.3%)
(pathway, home) pairs             2,000
homes per straddler: max 5, median 2
```

Inclusion of each straddler in each of its non-nested homes:

| bin | pairs | share |
|---|---|---|
| below 0.25 * | 0 | 0.0% |
| 0.25–0.33 | 477 | 23.8% |
| 0.33–0.50 | 328 | 16.4% |
| 0.50–0.75 | 251 | 12.6% |
| 0.75–1.00 | **944** | **47.2%** |

**The distribution is bimodal.** Nearly half of all multi-home memberships sit at inclusion 0.75 or
above — a pathway that most of the resampling runs put in both places — while a quarter sit in the
bottom bin, just above the cutoff. Overlap in this ontology is mostly not a threshold artefact.

\* The `below 0.25` bin is empty **by construction**, not by luck. 430 of the build's 13,599 member
rows are below the cutoff because the consensus pass INHERITED them from an ancestor, and an
inherited member's node is an ancestor of the node it came from, so it is never a minimal home.

> **A correction.** A first pass at this reported 1,044 straddlers. It filtered members at 0.25 and
> so dropped those 430 inherited rows; smaller member sets break containment relations, which turns
> nested pairs into non-nested ones and inflates the count. 852 is the build as it ships.

### How many keep >= 2 homes at a higher cutoff

A pathway keeps two homes at cutoff *t* exactly when its **second-highest** home inclusion >= *t*:

| bin | straddlers | share |
|---|---|---|
| 0.25–0.33 | 258 | 30.3% |
| 0.33–0.50 | 207 | 24.3% |
| 0.50–0.75 | 135 | 15.8% |
| 0.75–1.00 | 252 | 29.6% |

median second home **0.44**

Two ways of asking, and they disagree, so both are given:

| cutoff | filter this build | REBUILT at that cutoff |
|---|---|---|
| 0.25 | 1,044 | 852 |
| 0.33 | 931 | 711 |
| 0.50 | 819 | 529 |

The right-hand column is the answer. Raising the cutoff changes which families form, so the ontology
is different rather than merely filtered.

## 2. The three builds side by side

**Each build uses floors solved at its own cutoff.** The floors in `build_consensus.py` were solved
on scrambles at inclusion 0.25, and the cutoff is applied at completion — before families form and
before the support gate — so a build at another cutoff running those floors has an unknown FDR
rather than an inherited one. `scripts/calibrate_inclusion.py` re-solves them per cutoff under the
declared procedure of `addendum-2026-09-21.md`: 20 calibration scrambles solve, 10 held-out confirm,
candidates are every distinct support value in the null, no grid and no rounding.

|  | 0.25 | 0.33 | 0.50 |
|---|---|---|---|
| themes | 880 | 864 | 794 |
| roots | 53 | 57 | 61 |
| **pass-through parents** (one child, no member outside it) | **0** | **0** | **0** |
| — one child, any direct members | 283 | 274 | 243 |
| **held-out FDR** (target <= 0.01) | **0.00538** | **0.00460** | **0.00248** |
| — real themes behind it | 910 | 892 | 805 |
| — scrambled, mean of 10 | 4.9 | 4.1 | 2.0 |
| **test 9 mean Jaccard** | **0.851** | **0.853** | **0.864** |
| — median Jaccard | 0.889 | 0.889 | 0.909 |
| — matched at >= 0.9 | 46.0% | 47.0% | 53.7% |
| edges | 1,062 | 1,031 | 930 |
| themes with >1 parent | 203 | 186 | 174 |
| pathways placed | 1,842 | 1,841 | 1,831 |
| unplaced | 8 | 9 | 19 |
| straddlers (>= 2 homes) | 876 | 796 | 688 |
| — share of placed | 47.6% | 43.2% | 37.6% |
| median theme size | 10 | 9 | 8 |
| largest theme | 933 | 867 | 819 |
| depth | 12 | 14 | 12 |

### The floors each cutoff solved

| stratum | 0.25 | 0.33 | 0.50 |
|---|---|---|---|
| 3 | 0.8500 | 0.8600 | 0.8900 |
| 4 | 0.9000 | 0.9100 | 0.9300 |
| 5 | 0.6400 | 0.6400 | 0.6100 |
| 6 | 0.4600 | 0.4400 | 0.4000 |
| 7–9 | 0.3636 | 0.3300 | 0.3300 |

Effective threshold is `max(0.33, floor)`. Strata above 10 members all solve below 0.33 at every
cutoff, so they are pinned at the declared `m` regardless, and the coarser `10+` stratum the
calibration used cannot change a build.

### Two things to read carefully

**The 0.25 column is a re-derivation, not a reproduction.** It returns held-out FDR **0.00538**
against the **0.0051** recorded for the frozen build, and floors of 0.850/0.900/0.640/0.460/0.364
against the recorded 0.838/0.890/0.670/0.530/0.370. The scramble seeds differ (1000–1019 and
2000–2009 here). The agreement is a check that the procedure reproduces; the small differences are
seed noise and are the scale of it. This build has 880 themes where the frozen one has 873, for the
same reason.

**Pass-through parents are 0 in all three builds** under the strict reading — a node with exactly
one child and no member outside that child. The looser reading, one child regardless of direct
members, is 283/274/243, and those are NOT pass-throughs: their direct members are what makes them
broader than their child. The earlier "6 pass-throughs" used a different definition.

## 3. What the numbers say, without choosing

Every cutoff meets the FDR target, and it gets **monotonically safer** as the cutoff rises
(0.00538 -> 0.00460 -> 0.00248), because the scrambled count falls faster than the real one. Test 9
also improves monotonically (0.851 -> 0.853 -> 0.864). So on both declared criteria, 0.50 is the
best of the three, and nothing here rules any of them out.

What 0.50 costs is overlap and coverage: straddlers fall 876 -> 688 (47.6% -> 37.6% of placed),
themes 880 -> 794, and unplaced pathways rise 8 -> 19. The bimodal histogram is what makes that a
real cost rather than a clean-up: **47.2% of multi-home memberships sit at inclusion >= 0.75**, so
the overlap being discarded is largely not marginal.

The decision is therefore not "which cutoff is statistically safe" — all three are — but how much
genuine multi-membership the ontology should represent. That is Aviyah's call.

## Reproducing

```sh
uv run scripts/calibrate_inclusion.py --cutoffs 0.25 0.33 0.50 --workers 8
uv run scripts/build_consensus.py --space centred --inclusion 0.33 \
    --floors data/experiments/inclusion_floors.json --directory recurrent_dag_cal033
```

31 sides on 8 workers, about 6 minutes; a single build is 22 s. `prepare` and `score` are
independent of the cutoff, so one pass over the sides serves all three.
