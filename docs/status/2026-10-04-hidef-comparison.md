# HiDeF and CliXO against THEMA on the 10,770 — 4 Oct 2026

## LIVE STATUS
- **20:15 UTC** — COMPLETE. All arms built, decision rule applied, maxres sensitivity done, report written.
- running: nothing.
- ETA: n/a.
- last result: **THEMA STAYS** under the declared rule, and the verdict does not change at maxres 50 or 100.
- failures: CliXO unobtainable (stopped per budget); four HiDeF install/compat problems, all resolved.

---

## §0 THE DECISION RULE, as declared

Copied verbatim into `DECISIONS.md` as the first action of the run, before HiDeF was installed.

> - Primary metric: specificity AUROC (smallest shared theme size, siblings vs random pairs), as in
>   scripts/specificity_grid.py.
>   - Computed for Reactome siblings and GO siblings separately.
>   - Computed at zero gene overlap (the current headline) and with all overlap bands pooled.
>   - That gives 4 cells per arm.
> - Comparison: paired bootstrap over pairs, 2,000 resamples, seed 0. Report the 95% CI of
>   (HiDeF - THEMA) per cell.
> - Rule:
>   - If THEMA is not significantly better than HiDeF in any of the 4 cells (every CI includes or
>     exceeds 0), and HiDeF's test-4 zero-gene sibling recovery is >= THEMA's minus 2 points on both
>     Reactome and GO, then HiDeF is "at least as good" and we switch engines.
>   - Otherwise THEMA stays, and HiDeF and CliXO are reported as baselines.
> - Everything else (shape, stability, null arm, curated ceiling, fan-out subset, hop distance) is
>   reported, not decisive.
> - Nothing is re-tuned after results are seen. If a HiDeF parameter turns out to matter, report it
>   as a post-hoc sensitivity, labelled as such.

## THE FOUR CELLS — declared run, HiDeF k = 15, maxres 25

Paired bootstrap over curated pairs, 2,000 resamples, seed 0. The null is the fixed reference both
arms are scored against; resampling it would measure the reference's stability, not the comparison's.

| cell | n | THEMA | HiDeF | HiDeF − THEMA | 95% CI | |
|---|---|---|---|---|---|---|
| Reactome siblings, zero gene overlap | 5,753 | **0.8841** | 0.7898 | −0.0943 | [−0.1004, −0.0878] | **THEMA significantly better** |
| Reactome siblings, all bands pooled | 9,396 | **0.8827** | 0.8228 | −0.0599 | [−0.0642, −0.0554] | **THEMA significantly better** |
| GO siblings, zero gene overlap | 19,828 | 0.6959 | **0.7041** | +0.0081 | [+0.0047, +0.0115] | HiDeF ahead |
| GO siblings, all bands pooled | 45,832 | 0.7342 | **0.7516** | +0.0173 | [+0.0152, +0.0196] | HiDeF ahead |

**Test-4 zero-gene sibling recovery:** Reactome THEMA **89.0%** vs HiDeF 79.1% (**−9.9 points**);
GO THEMA 59.2% vs HiDeF **64.4%** (+5.2 points).

### VERDICT UNDER THE DECLARED RULE

> **THEMA STAYS. HiDeF is reported as a baseline.**

Two of the four cells have THEMA significantly better, so the rule's first condition fails on its own
terms; the recovery condition also fails on Reactome at −9.9 points against a 2-point tolerance.
**Either one alone would have been decisive.**

**Would it change at maxres 50 or 100? NO.** At both, HiDeF's recovery condition is satisfied
(−0.1 and +1.3 points, inside the 2-point tolerance), but **THEMA remains significantly better in
both Reactome cells**, so the AUROC condition still fails and the verdict is unchanged.

## POST-HOC SENSITIVITY — maxres, labelled as such and not decisive

Everything else identical: k = 15, τ 0.75, χ 5, p 75, Leiden, same vectors, same keys.

| maxres | themes | Reactome zero-gene | Reactome pooled | GO zero-gene | GO pooled |
|---|---|---|---|---|---|
| **25 (declared)** | 472 | 0.7898 [−0.1004, −0.0878] | 0.8228 [−0.0642, −0.0554] | 0.7041 [+0.0047, +0.0115] | 0.7516 [+0.0152, +0.0196] |
| 50 (post hoc) | 679 | 0.8501 [−0.0377, −0.0298] | 0.8604 [−0.0256, −0.0188] | 0.7101 [+0.0108, +0.0175] | 0.7571 [+0.0207, +0.0249] |
| 100 (post hoc) | 1,026 | 0.8409 [−0.0475, −0.0386] | 0.8566 [−0.0297, −0.0225] | 0.7078 [+0.0085, +0.0151] | 0.7543 [+0.0179, +0.0222] |
| THEMA | 6,244 | 0.8841 | 0.8827 | 0.6959 | 0.7342 |

| maxres | Reactome recovery | vs THEMA 89.0% | GO recovery | vs THEMA 59.2% |
|---|---|---|---|---|
| **25 (declared)** | 79.1% | **−9.9** | 64.4% | +5.2 |
| 50 | 88.9% | −0.1 | 65.3% | +6.1 |
| 100 | 90.3% | +1.3 | 66.4% | +7.2 |

**maxres matters, and it matters in one direction only.** Raising it closes the Reactome recovery
gap entirely (−9.9 → +1.3) and improves HiDeF's Reactome AUROC (0.790 → 0.850), but it never closes
the AUROC gap: THEMA stays ahead on Reactome by 0.022–0.043 with intervals nowhere near zero. **The
sensitivity changes which condition fails, not whether one does.** Best at maxres 50, not 100, so
more resolutions is not monotonically better.

## Test 4 by band, HiDeF k = 15 (existing validate code, unchanged)

Note HiDeF's chance rates are much higher than THEMA's (31.7% at zero gene overlap against 21.4%),
because 472 themes of median size 59 co-locate random pairs far more often than 6,244 of median 9.

| source | band | n | HiDeF recovery | chance | lift |
|---|---|---|---|---|---|
| reactome2go | exactly 0 | 40 | 77.5% | 31.7% | 2.4x |
| Reactome siblings | exactly 0 | 5,753 | 79.1% | 31.7% | 2.5x |
| Reactome siblings, fan-out<=6 | exactly 0 | 664 | 90.4% | 31.7% | 2.8x |
| GO siblings | exactly 0 | 19,828 | 64.4% | 31.7% | 2.0x |

THEMA's comparable figures: reactome2go 80.0% at 21.4% chance (3.7x), Reactome siblings 89.0%
(4.2x), fan-out<=6 84.0% (3.9x), GO siblings 59.2% (2.8x). **HiDeF is ahead on GO and behind on
Reactome, on both recovery and lift.**

## §B3 NULL ARM — and it does not go the way THEMA's claim predicted

| arm | communities >= 3 | placed |
|---|---|---|
| HiDeF on scramble seed 4001 | **0** | 0 of 10,770 |
| HiDeF on scramble seed 4002 | **0** | 0 of 10,770 |

**Both nulls were asserted against the build's own**: a Ward tree rebuilt from the regenerated
scrambled vectors matched the persisted `seed04001_row00001.npz` and `seed04002_row00001.npz`
**byte-for-byte**, so this is the build's null and not a lookalike.

**HiDeF finds nothing in noise either.** Its persistence criterion (χ = 5 across the resolution
sweep) rejects the whole scrambled graph without any FDR calibration, 10 calibration scrambles or 5
held-out sides. **This was the one thing THEMA was expected to have that HiDeF lacks, and on this
evidence it does not have it uniquely.** THEMA's gate buys a calibrated error rate — a held-out FDR
of 0.00285 with a per-stratum number — which HiDeF does not provide; but "resists noise" is not a
distinguishing claim.

## §B4 SHAPE, every arm

| arm | themes | roots | depth | multi-parent | median size | largest theme | straddlers | eff. unplaced |
|---|---|---|---|---|---|---|---|---|
| **THEMA (frozen)** | 6,244 | 203 (3.2%) | 16 | 29.5% | 9 | 3,336 | 8,859 | 141 |
| HiDeF k=15 | 472 | 23 (4.9%) | 8 | 18.6% | 59 | 4,550 | 5,915 | 7 |
| HiDeF k=30 | 353 | 17 (4.8%) | 8 | 19.8% | 74 | 4,700 | 5,787 | 12 |
| HiDeF maxres 50 | 679 | 28 (4.1%) | 8 | 16.5% | 40 | 4,494 | 5,816 | 12 |
| HiDeF maxres 100 | 1,026 | 31 (3.0%) | 10 | 15.2% | 25 | 4,586 | 5,750 | 12 |
| HiDeF null (4001) | 0 | 0 | 0 | 0% | 0 | 0 | 0 | 10,770 |

**The two methods produce different kinds of object.** THEMA gives 6,244 fine themes (median 9) and
leaves 141 pathways effectively unplaced; HiDeF gives 472 coarse ones (median 59) and places almost
everything. **Every HiDeF arm's largest theme exceeds THEMA's declared size cap** (4,494–4,700
against 3,125) — reported, never applied, since the cap is THEMA's rule and not HiDeF's.

## §B5 STABILITY — informational, and NOT directly comparable

| arm | perturbation | worse direction at Jaccard >= 0.70 |
|---|---|---|
| THEMA | two builds from disjoint blocks of 200 trees each | **87.9%** |
| HiDeF k=15 | two Leiden seeds, same graph | 86.0% |
| HiDeF k=15 | two independent 80% subsamples, shared members | **57.0%** |

**These are not the same perturbation and the numbers are not interchangeable.** THEMA's ladder
compares two builds that each AGGREGATE 200 resampled subsamples, so resampling noise is already
averaged inside each arm before they are compared. HiDeF's subsample arm compares two SINGLE 80%
draws, with no aggregation — a strictly harsher test. The seed arm is the gentler one: same graph,
different RNG.

**Read that way, the subsample figure is the interesting one**: a single-draw HiDeF reproduces 57% of
its themes, which is roughly what THEMA's own single Ward trees would do before the recurrence
machinery averages them. It says the aggregation is doing work, not that HiDeF is unstable in the
sense THEMA is measured for.

**A correction worth recording**: my first subsample figure was **1.9%**, which was an artefact of my
own measurement — the two subsamples cover different 8,616-pathway subsets, so raw member Jaccard is
depressed by the sampling, not the method. Restricting to shared members, as the brief specifies,
gives 57.0%.

## §A CURATED CEILING AND SPECIFICITY — what a perfect answer would score

From `scripts/specificity_grid_v2.py`. Smallest shared theme size; smaller is a sharper claim.

GO siblings, fan-out<=6 subset (the cell printed in full; the whole grid is in the TSV):

| arm | median size | AUROC | <=10 | <=50 | <=200 |
|---|---|---|---|---|---|
| **CURATED CEILING** | **15** | — | **36.1%** | **85.6%** | **98.2%** |
| THEMA (frozen) | 107 | 0.878 | **25.7%** | 45.2% | 52.9% |
| HiDeF k=15 | 96 | **0.911** | 0.0% | 21.4% | 62.6% |
| TF-IDF flat@100 | 227 | 0.797 | 0.0% | 4.0% | 49.4% |
| ochiai@100 | 2,458 | 0.735 | 0.0% | 5.2% | 35.5% |
| kappa@100 | 2,254 | 0.809 | 0.0% | 1.8% | 15.5% |
| **random (THEMA shape)** | inf | **0.494** | 0.1% | 0.3% | 0.5% |

**The ceiling is the number that matters here.** A perfect reproduction of the curated hierarchy
places 36% of these sibling pairs in a node of <=10 and 86% in <=50. THEMA reaches 25.7% and 45.2%;
HiDeF reaches **0.0%** and 21.4%. **At the sharpest grain HiDeF places nothing at all**, because its
themes have median size 59 — it cannot make a <=10 claim. HiDeF's higher AUROC in this cell comes
from the coarse end: 62.6% at <=200 against THEMA's 52.9%.

**The random arm works as a control**: THEMA's own shape with pathway identities permuted scores
0.494, i.e. chance. So THEMA's specificity is not an artefact of its hierarchy's shape.

## HOP DISTANCE — undirected, pathway to themes to theme-theme edges

| arm | source, band | median curated | median random | AUROC | p | connected, curated vs random |
|---|---|---|---|---|---|---|
| THEMA | Reactome, exactly 0 | **2** | 5 | 0.826 | <1e-300 | 97.2% vs 88.1% |
| HiDeF | Reactome, exactly 0 | **2** | 7 | 0.758 | <1e-300 | 100.0% vs 100.0% |
| random | Reactome, exactly 0 | 6 | 5 | 0.490 | 1.00 | 88.7% vs 87.9% |
| THEMA | GO, exactly 0 | **2** | 5 | 0.667 | <1e-300 | 89.2% vs 88.1% |
| HiDeF | GO, exactly 0 | **2** | 7 | 0.658 | <1e-300 | 100.0% vs 100.0% |

Mann–Whitney U one-sided, curated closer than random. Both real arms separate strongly; the random
arm does not (p = 1.00). **HiDeF's connectivity is 100% in both columns** — its graph is connected
enough that every pair has a path, so connectivity carries no information for it, while THEMA's
97.2% vs 88.1% does.

## §B2 CliXO — NOT BUILT, and why

Stopped inside the ~45-minute budget, as instructed.

1. **Not on PyPI**: `clixo` resolves to nothing.
2. **`ddot` installs but ships no CliXO binary** — it expects a separately compiled C++ executable.
3. **The source is unreachable**: `idekerlab/CliXO`, `fanzheng10/CliXO_1.0`, `idekerlab/clixo_0.3`
   and `ucsd-ccbb/CliXO` all return *Repository not found*.

With no source and no binary there is nothing to compile, so α and β never became live questions.
**β = 0.5 was the declared choice and α was never selected**, because selecting it without a working
implementation would be theatre.

**Cost, recorded**: installing `ddot` downgraded `typing-extensions` to 3.10.0.2 and `wcwidth` to
0.9.1 inside the venv everything else runs in. Caught immediately, verified with the full suite (604
passed), then `ddot` was removed and both packages restored. **A dependency probe for an optional arm
should not have been run against the live environment**, and that is the lesson rather than the
downgrade itself.

## WALL TIME AND PEAK RAM

| arm | wall | peak RAM |
|---|---|---|
| **THEMA, confirmatory build** (sides cached) | ~2 min | 8.2 GB per side (21.7 GB before the join) |
| THEMA, one 200-run side from scratch | ~11.5 min | 8.2 GB |
| HiDeF k=15 | **2.1 min** | **2.13 GB** |
| HiDeF k=30 | 3.4 min | 1.6 GB |
| HiDeF maxres 50 | 2.2 min | 2.81 GB |
| HiDeF maxres 100 | 2.4 min | 4.17 GB |
| HiDeF null, seed 4001 | 4.8 min | 3.14 GB |
| HiDeF null, seed 4002 | 4.9 min | 5.26 GB |
| HiDeF 80% subsample | 1.7 min | 1.74 GB |

**HiDeF is dramatically cheaper**: one 2-minute 2 GB run against THEMA's 11 sides at ~11.5 minutes
and 8.2 GB each, plus 1,900 persisted trees. If the two had tied on the primary metric, this would
have been the strongest argument for switching, and the rule correctly gave it no weight.

## GETTING HIDEF TO RUN AT ALL — four problems, all recorded

Each could have silently produced a wrong arm.

1. **`louvain` cannot be installed here.** `hidef` requires it; it vendors igraph's C core, which
   fails under the installed clang (*variable 'v' is uninitialized when passed as a const pointer*),
   and CFLAGS do not reach its CMake build — installing `cmake` and a brew `igraph` did not help.
   But `louvain` is referenced **only** inside `if alg == 'louvain':` branches and the declared run
   is Leiden, so a stand-in is installed that **raises on any attribute access**: if HiDeF ever
   reached for it, the run fails loudly.
2. **`scipy.stats` shadows `abs`** through two star-imports, so
   `abs(np.log10(x) - np.log10(y))` raised *Transformations are currently only supported for
   continuous RVs*. Builtins restored in that module; only `abs` needed it.
3. **The pool deadlocked** — `hidef_finder.run` always creates an `mp.Pool` and macOS spawns, so
   children re-import and need the stand-in first. Three processes sat at 0.0% CPU. Now installed at
   module import time.
4. **igraph's RNG hook** wants stdlib `random.Random` (it calls `.randint` and `.gauss`), not a numpy
   `Generator` or `RandomState`.

**The toy test ran before any real data** and earned its place: 30 nodes, two planted communities of
15, three weak bridges. **Both recovered at Jaccard 1.000.** Two earlier attempts at reading HiDeF's
output returned 0 communities, and the toy caught both — the member masks live at
`weaver.hier.nodes(data=True)['index']` into `wv._assignment`, as the package's own `output_nodes`
does it. **Also caught: one of my own edits had deleted the script's `if __name__ == "__main__"`
block**, so it ran, printed nothing, and exited 0 — which a careless check reads as success.

## WHAT THIS CHANGES, AND WHAT IT DOES NOT

**Nothing declared changed. Nothing was frozen or renamed.** The frozen build and the naming code
were not touched.

**The honest summary is split, not one-sided.** THEMA wins the primary metric on Reactome decisively
and loses it on GO slightly; it makes far sharper claims at the specificity grain that matters
(25.7% at <=10 against HiDeF's 0.0%); and it costs roughly 50x more compute. HiDeF matches it on
noise rejection, which was expected to be THEMA's distinguishing property.

**Open questions for Aviyah, none of them decided here:**

1. **GO siblings favour HiDeF in both cells** (+0.008, +0.017, intervals excluding zero). Small, but
   consistent across bands and across all three maxres values. Worth understanding rather than
   dismissing.
2. **HiDeF rejects the null without any FDR machinery.** THEMA's calibration still buys a *quantified*
   error rate, which HiDeF does not offer — but if noise rejection alone were the goal, the 10
   calibration plus 5 held-out scrambles would be unnecessary.
3. **Whether a hybrid is worth testing**: HiDeF's graph and persistence sweep at THEMA's resolution
   and with THEMA's gate. Not attempted, not estimated.
4. **CliXO remains unevaluated** and its source appears gone from the locations the paper and DDOT
   cite.

## COMMIT BLOCKS

I ran no git commands. These are for you.

```sh
git add \
  DECISIONS.md \
  scripts/build_hidef.py \
  scripts/hidef_decision.py \
  scripts/specificity_grid_v2.py \
  scripts/theme_match.py \
  data/experiments/specificity_grid_v2.tsv \
  docs/status/2026-10-04-hidef-comparison.md

git commit -m "HiDeF compared against THEMA under a rule declared first; THEMA stays" -m "The decision rule was copied verbatim into DECISIONS.md before hidef was
installed, and it was written so HiDeF could win: match THEMA on all four
specificity-AUROC cells and come within 2 points on zero-gene sibling recovery,
and the engine changes.

THE FOUR CELLS, paired bootstrap over pairs, 2,000 resamples, seed 0:

  Reactome, zero gene overlap  THEMA 0.8841  HiDeF 0.7898  CI [-0.1004, -0.0878]
  Reactome, all bands pooled   THEMA 0.8827  HiDeF 0.8228  CI [-0.0642, -0.0554]
  GO, zero gene overlap        THEMA 0.6959  HiDeF 0.7041  CI [+0.0047, +0.0115]
  GO, all bands pooled         THEMA 0.7342  HiDeF 0.7516  CI [+0.0152, +0.0196]

Test-4 zero-gene recovery: Reactome 89.0% vs 79.1% (-9.9 points), GO 59.2% vs
64.4% (+5.2). THEMA is significantly better in 2 of 4 cells and HiDeF misses the
recovery tolerance on Reactome, so either condition alone decides it.

VERDICT: THEMA STAYS. HiDeF is reported as a baseline.

A LABELLED POST-HOC SENSITIVITY on maxres, which cannot change the verdict and
does not: at 50 and 100 the recovery gap closes (-0.1 and +1.3 points) but THEMA
remains significantly better on both Reactome cells. maxres changes which
condition fails, not whether one does, and 50 beats 100, so more resolution is
not monotonically better.

THE RESULT IS SPLIT, NOT ONE-SIDED, and the report says so. THEMA wins Reactome
decisively and loses GO slightly. It makes far sharper claims where it matters --
25.7% of tight GO sibling pairs in a theme of 10 or fewer, against HiDeF's 0.0%,
with the curated ceiling at 36.1% -- and it costs roughly 50x the compute: 2.1
minutes and 2.13 GB for all of HiDeF against 11 sides at ~11.5 minutes and 8.2 GB
each.

AND HIDEF FINDS NOTHING IN NOISE EITHER. On both held-out scramble seeds, each
asserted byte-for-byte against the build's own persisted tree, HiDeF returns ZERO
communities of 3 or more members, with no FDR calibration at all. Noise rejection
was expected to be THEMA's distinguishing property and on this evidence it is not
uniquely so; what THEMA's gate still buys is a quantified error rate.

A random arm -- THEMA's own shape with pathway identities permuted -- scores AUROC
0.494, so the specificity is not an artefact of the hierarchy's shape.

Four install problems are recorded because each could have produced a wrong arm
silently: louvain cannot be built here and is replaced by a stand-in that raises
on any access (hidef imports it unconditionally but uses it only for
alg='louvain'); scipy.stats shadows abs through two star-imports; the
multiprocessing pool deadlocked until the stand-in moved to import time; and
igraph's RNG hook wants stdlib random.Random. A toy test with two planted
communities ran before any real data and caught two wrong ways of reading HiDeF's
output.

theme_match.py gains --restrict-shared. Without it the subsample stability figure
was 1.9%, an artefact of two 80% subsamples covering different pathway sets;
restricted to shared members it is 57.0%.

CliXO was NOT built: it is absent from PyPI, ddot ships no binary, and four
plausible source repositories return Repository not found. Stopped inside the
budget. Probing for it downgraded typing-extensions and wcwidth in the live venv;
caught immediately, the suite re-run at 604 passed, and both restored."
```
