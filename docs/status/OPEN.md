# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-29

---

## RUNNING

Nothing. No process, no API call, nothing scheduled.

## WAITING ON AVIYAH

**On the frozen 10,770** (all recorded in `docs/status/2026-10-03-unattended.md`, Decisions for
Aviyah):

1. **Whether the size cap must hold after completion and consensus**, not only at candidacy. 2 of
   6,244 themes exceed it; largest 3,336 against 3,125. Changing this changes a declared rule.
2. **Tests 3 and 4 cannot be adjudicated as written** — the marks are on raw recovery, which a
   collapsed baseline wins (`kappa@25`, 97.3% of the universe in one cluster, lift 1.0x). They need
   a lift criterion or a non-degeneracy constraint.
3. **Test 3's headline cell holds 8 pairs.** The plan calls it the headline number; it cannot be one.
4. **Rung 3**, 2.8-8.0 h at 1-2 sides in parallel. Would settle whether 90% is reachable rather
   than extrapolated. The declaration forbids starting it without a decision.
5. **Whether `min_size = 3` is right** for a build judged on theme stability: 3-member themes fail
   to reproduce at 44.9% and supply 29.8% of all misses.
6. **Three of the four largest roots are pass-through shells** — one child holding ~90%.
7. **Whether the 1,850 demo should be rebuilt on the frozen 10,770.** It currently shows the subset
   build at 85.9% stability, with that stated on its landing page.

**On naming** (unchanged, nothing has run):

8. **The `name-v5` prompts**, rendered to `docs/spec/naming-prompt-v5-rendered.md`. **Nothing runs
   until these are approved** — `CLAUDE.md` requires the text before the spend.
9. **The level-0 price, $2.29**, on the 1,850. Approving prompts and approving price are separate
   gates. **Note:** naming the frozen 10,770 is a different and larger job, never priced.

## CURRENT BUILD — `v0.3.0-10770-runs200`, the official ontology

`data/ontology/v0.3/recurrent_dag_10770`, frozen 3 Oct 2026, `FROZEN.md` in the directory.
**Supersedes `v0.2.2-subset-1850-c50`**, which covered 1,850 of the 10,770 and remains as the
method-development record.

**6,244 themes, 203 roots (3.2%), 8,208 edges, 29.5% multi-parent, depth 16 edges, largest theme
3,336, 8,859 straddlers.** Centred-and-renormalised MedCPT vectors, **RUNS = 200**, theta 0.70,
membership at inclusion >= 0.50, declared m 0.33 with per-size floors solved at 0.50 — 0.790 / 0.905
/ 0.415 at sizes 3/4/5, m governing 6 and above — from **10 calibration and 5 held-out scrambles of
200 trees**, **held-out FDR 0.00285 overall, worst stratum 0.0147**.

**Placement, three ways:** 24 unplaced strictly, **117 root-only**, **141 effectively unplaced** —
1.3% of the universe, against the subset build's 6.8%. The clearest benefit of full scale.

**THE DECLARED STABILITY MARK IS NOT MET: 87.9% against 90%** (85.5% at 100 runs). The mark was not
lowered. Any public description must carry the figure.

**THE SIZE CAP IS EXCEEDED BY TWO THEMES**, through completion and then consensus. Declared at cut
time, where it holds exactly. Stated, not corrected.

**The build is UNNAMED.** Naming has not run on the 10,770; the 1,850's 502 names refer to themes
that do not exist here.

## NAMING — plan, level by level

`name-v5` is **one prompt**: the same system prompt for leaves, internal nodes and collision
re-asks. The user message is data with a single line of instruction — title and description only,
no source tags, no inclusion values, no identifiers, no worked examples. A collision is the same
message with one line appended.

`--max-level N` names up to level N and **skips** everything above it. A skip is not a refusal: an
internal node whose children are unnamed is left alone rather than recorded as unnameable, and
because a request is keyed by its members and its children's names, a later run at a higher level
reuses every completion already in the ledger.

| step | scope | price | state |
|---|---|---|---|
| level 0 | 287 leaves | **$2.29** | priced, awaiting approval |
| levels 1+ | 513 internal | ~$2.34 more | after level 0 is read |

## THE LADDER — the rule, and what has and has not been measured against it

**The rule, as defined 25 Sep:** **≥ 90% of FINAL THEMES matched at Jaccard ≥ 0.70 between builds
from disjoint tree blocks.** The unit is a finished theme — completed, support-gated,
consensus-reconciled, with its exported member list.

**Measured against the rule.** Test 9 on the frozen 1,850, two full builds at 100 runs each (seed 0
vs seed 1), reproduced by `scripts/theme_match.py`:

| direction | mean | median | ≥ 0.50 | **≥ 0.70** | ≥ 0.90 |
|---|---|---|---|---|---|
| seed 0 → seed 1 | 0.862 | 0.909 | 95.8% | **86.9%** | 53.2% |
| seed 1 → seed 0 | 0.863 | 0.909 | 96.6% | **85.9%** | 53.3% |

**The frozen build misses the 90% mark by 3.1 points forward and 4.1 in the worse direction.** The
rule does not say which direction the mark applies to — **open**. This is the live question.

**NOT measured against the rule, and previously misread as if it were.** The 2 Oct re-measurement
matched the **raw grouping pool**, not themes: 61.0% and 63.5% at 10,770, 54.8% and 58.2% on the
1,850. That was a **mis-implementation of the rule** (`DECISIONS.md`, 2 Oct), so those figures
neither confirm nor refuse RUNS = 200. They stand as a correct description of grouping-pool
agreement, whose shape the diagnostic explains: half the pool is a 10+-member cluster with median
support 0.030 that no second run reproduced.

Also superseded, kept visible: this section once read "100 trees per run: 89.1% of groupings match at
≥ 0.70. 200 gives 91.4%." No committed script produced those figures and they record no space and no
inclusion cutoff (`docs/debt.md`).

**A correct re-measurement** needs two full builds from trees 1–100 and 101–200, compared with
`scripts/theme_match.py`. The trees are on disk; `scripts/build_10770.py` needs a row-range option.
**Not run. Aviyah decides**, including whether a mark the frozen build misses survives as the mark.
`docs/status/2026-10-02-runs-ladder.md` is the write-up.

## COHESION — measured, no threshold added

`DECISIONS.md`, 29 Sep, reproduced by `scripts/cohesion_reference.py`. Themes are tighter than
random kNN balls of the same size at **every** stratum, so the geometry finds nothing to remove; a
cut at 0.20 would delete the top of the tree and leave the incoherent leaves untouched. What judges
"too unrelated" instead is the namer's `nameable: false`, shown as an unnamed umbrella and never
hidden. **Aviyah's reservation is recorded**: she does not like an LLM verdict acting as the
structural filter, and it is accepted only because no measured geometric rule does the job.

**Follow-up, declared before the leaf names exist:** after level-0 naming, compare the cohesion of
refused leaves against named ones. If refusals concentrate in the low-cohesion tail, a size-aware
floor calibrated from those verdicts may be declared and applied to the 10,770. If they do not, the
idea is closed.

## SCALE — built and frozen, 3 Oct

Everything expensive is on disk: **400 real Ward trees and 15 scramble sides of 200** under
`data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/`, written once without a size cap, so any change
to the cap, the cutoff or the floors is a **re-cut rather than a rebuild**. Per-side completions are
cached too, each carrying a fingerprint of the code that wrote it; a mismatch refuses reuse.

**Two implementation changes were made and each proved byte-identical before use**: a vectorised
completion (1.8-2.2x on its stage) and an exact set-similarity join for seed absorption (2.0x on its
stage, and peak memory per side from 21.7 GB to 8.2 GB, which is what makes three sides fit at once).
A side is ~700 s. `families` remains the dominant stage at ~59%.

**Rung 3 is priced and not run**: 2.8-8.0 h, 1-2 sides in parallel, 13.9-20.8 GB per side.

## VALIDATION — tests 1-4 run on the frozen build; two gates cannot be adjudicated

| test | kind | state |
|---|---|---|
| **1** scramble error rate | gate | **DISCHARGED** — held-out FDR 0.00285, worst stratum 0.0147 |
| **2** shape vs GO / Reactome | informational | reported; **verdict withheld**, the GO figures the old verdict rested on are not reproducible |
| **3** `reactome2go` recovery | gate, headline | **TF-IDF condition MET** (75.0% vs 0.0%); **no overall verdict** |
| **4** sibling recovery | gate | beats the null in every band of every source; **no verdict** |
| **9** seed stability | informational | **superseded** by the rung measurement, which is stronger |
| **5** enrichment task | gate | needs Aviyah's dataset approval |
| **6** blind human rating | gate | Aviyah's time |
| naming **1** and **2** | gates | the build is unnamed |

**The TF-IDF control produces no ontology at all.** Built through the identical pipeline on TF-IDF
vectors over the same descriptions, its floors are unsolvable in all six strata — 140,758 real
families against scrambles of 362,000-365,000 — so nothing passes the recurrence gate and all 10,770
pathways are unplaced. Flat TF-IDF clusterings recover 0.0% of test 3's headline cell where the
frozen build recovers 75.0%, and those arms are not degenerate. Word counting yields no recurrent
structure here.

**Why tests 3 and 4 have no verdict is a defect in the marks, not in the build** — see WAITING ON
AVIYAH items 2 and 3, and `docs/debt.md`.

## SPEND

$232.52 to date. $0.00 since the `name-v3` run on 27 Sep.
