# Leaves, part 2: does a centre-based proposer give THEMA a middle level from leaves alone?

*Declared 8 Oct 2026, before any result. Branch `leaves-2026-10`. Exploratory arm. Anything changed later is labelled as post hoc.*

## Why

The leaves experiment (`docs/status/2026-10-08-leaves.md`) failed all three declared conditions. Only 8.5% of curated summaries have a theme recreating their leaves. But Test T showed that text places a summary correctly when such a theme exists (rank 1 in 64% of cases, top 5 in 86%).

The reviewer's signal check (`claude/thema-leaves-signal-check-2026-10-08.md`, scripts `/tmp/qs/star*.py`) shows that the grouping signal is in the leaves. It is a GROUP-level signal, not a PAIR-level one:

- Leaf–leaf cosine within a curated group falls with size: Reactome 0.40 → 0.17, GO 0.32 → 0.14.
- Leaf → centroid of its siblings stays high: Reactome 0.53 / 0.51 / 0.40; GO 0.43 / 0.40 / 0.35, for bands 3–10 / 11–50 / 51–200.
- A random group of the same size scores about 0.

**Hypothesis.** Ward with recurrence is excellent at the fine level and is kept unchanged. It misses diffuse, star-shaped mid-level groups because it merges pairwise and the matching is strict. A centre-based proposer (spherical k-means) sees exactly the signal those groups carry.

## Principle (unchanged)

A theme is a group that recurs across 80% subsamples more often than calibrated noise allows; themes are stacked by containment. The only change is that each run proposes candidates from TWO sources, Ward and spherical k-means. All candidates pass the same matching, support, floors and containment.

## Step 1: engine-ceiling diagnostic (TUNING half only, no build)

For each curated summary in the TUNING half (leaf set ≥ 3), per band and source:

- (a) the best Jaccard between its leaf set and ANY candidate cluster in L's 200 Ward trees, before the gate;
- (b) the same over spherical k-means clusters, at the step 2 ladder, on the same 200 subsamples;
- (c) the share with best Jaccard > 0.5 under (a), under (b), and under (a) ∪ (b);
- (d) the same share for the final thema_L themes, i.e. after the gate.

**Reading.** If (a) is high and (d) is low, the gate kills mid-size groups. If (a) is low and (b) is high, Ward never forms them and k-means does. Report only; this step changes nothing.

## Step 2: build arms on L (5,559 leaves, vectors centred on L)

- **L-W:** today's leaves Ward build (v0.4 kept stages), re-calibrated under the rule below. This is the reference.
- **L-WK (primary):** per run, Ward candidates plus spherical k-means clusters at k ∈ {50, 100, 200, 400}.
  - Seed per run and k, k-means++ initialisation, n_init = 1, max_iter = 100, cosine on unit vectors.
  - All candidates go through the identical v0.4 pipeline: matching θ = 0.70, completion, greedy absorption, per-size floors, strict containment.
- **L-K (report-only):** k-means candidates only, using L-WK's floors, labelled as such.

**Calibration (existing protocol rule from Test F: "3 seeds if they pass held-out, else 10").**
- Three seeds already failed on L (stratum 5-5). So BOTH L-W and L-WK are calibrated on 10 scramble seeds, 3001–3010, and checked on held-out 4001 and 4002 together.
- Caps: overall ≤ 0.01, every stratum ≤ 0.02.
- If a cap still fails, report it. Do NOT choose floors from the held-out side.

## Step 3: tests (TEST half; cluster bootstrap over targets, 1,000 resamples, seed 0)

- Targets: curated summaries as leaf sets (≥ 3 leaves). Primary GO closure; `is_a`-only secondary.
- Arms: L-W, L-WK, L-K, (a) = v0.4 restricted to leaves, and HiDeF k4/800 on L.
- Metrics:
  - recall and precision per band and source (Jaccard > 0.5);
  - near-pair agreement (clarification 10);
  - themes per band, held-out FDR, stability between run halves, scatter;
  - the RTK case (R-HSA-9006934; 101 leaves);
  - Test T (text placement: T1 and T2) for L-WK.

## Decision rules (declared now)

1. **Does the centre proposer help?** L-WK is preferred over L-W if, on the TEST half, ALL of the following hold:
   - it is not worse by > 2 points (CI excluding 0) in any 3–10 recall cell;
   - it is better by > 2 points (CI excluding 0) in at least one 11–50 or 51–200 recall cell;
   - its held-out FDR is within the caps.
2. **Does leaves-only reach the bar?** Leaves-only "works" if the preferred leaves arm is not worse than (a) by > 2 points (CI excluding 0) in any recall cell, with FDR within the caps. If it fails, report exactly which cells fail.

Nothing is frozen; Aviyah decides.

## Preservation and budget

- New files only, under `data/ontology/v0.4-leaves/` and `data/experiments/leaves/`. v0.3, v0.4 and thema_L stay untouched; new builds get new directories.
- The byte-identity test must still pass.
- Reuse the existing Ward sides (real, 3001–3003, 4001).
- Estimate the time first; if it is over 4 h, stop and report the estimate.
- Status: `docs/status/2026-10-08-leaves-centroid.md`. Leave a commit script.
