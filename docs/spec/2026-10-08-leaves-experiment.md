# The leaves experiment: declared 8 Oct 2026, before any result

*Spec for ccode. Exploratory arm. Everything is declared here before any number exists. Any later change is labelled as post hoc.*

## Why

Curated parents are summaries by construction. A Reactome parent's genes contain every child's (100% of edges), and GO propagates annotations upward. 58% of the GO pathways in the universe (4,370 of 7,538) and 29% of Reactome (848 of 2,883) are such internal nodes. They are large (median 43–51 genes; leaves have a median of 9–10).

Today they are clustered alongside their own children as if they were independent items. The consequences (`docs/spec/2026-10-08-reviewer-monotonicity-notes.md`):
- general pathways cluster with their general synonyms instead of sitting above their specifics;
- the same genes appear all over the DAG;
- there is no middle-level theme for groups like "RTK signalling".

Text-only direction signals have been tried and are weak (about 60%) or contaminated (the LLM pilot: 62.5%, with 63% verbatim GO ancestors).

## What we are trying to achieve

Build THEMA from the **atomic** pathways only (the leaves), then test whether its themes **recreate the curated summaries** by merging leaves. If they do, THEMA's claim becomes: *"From the atomic pathways of four databases, text alone merges cross-database duplicates and recovers the curated summary structure."* Curated parents are then placed on the theme that recreates them, which gives users general-above-specific without using text direction.

**Leakage statement.** The curated hierarchy is used ONLY to mark which pathways are summaries (internal nodes). It is never used to decide how leaves group. The placement layer (step 6) is display only and is never scored.

## Design

1. **Universe L.**
   - Remove every Reactome pathway with ≥ 1 descendant in the universe (ReactomePathwaysRelation).
   - Remove every GO term with ≥ 1 descendant in the universe (closure over `is_a`, `part_of`, `regulates`, `positively_regulates`, `negatively_regulates`, as in clarification 9).
   - Keep all Hallmark and BTM pathways.
   - Expected size: about 5,599. Report the counts per source.
   - Sensitivity, counts only: GO internal defined by `is_a` + `part_of` only.
2. **Vectors.** The existing MedCPT vectors for L, **re-centred on L** and renormalised, as the protocol does for subsets.
3. **Build.**
   - v0.4 as finalised: kept stages only, 200 runs, 80% subsamples.
   - Floors: reuse the stored 3-seed floors and check them on ONE held-out scramble of L (seed 4001). If held-out FDR > 0.01 overall or > 0.02 in any stratum, recalibrate on L (seeds 3001–3003) and say so.
   - Stability between run halves.
   - Output: `data/ontology/v0.4-leaves/thema_L/`.
4. **Baselines on the same L.**
   - (a) **Full-universe v0.4 restricted to its L members**: keep themes of ≥ 3 after restriction, deduplicated. This answers "does building on leaves beat simply hiding the parents?"
   - (b) **HiDeF on L**, re-tuned on the TUNING half over k ∈ {3, 4, 5} × maxres ∈ {300, 500, 800}.
5. **Answer key.**
   - For every internal node P (Reactome; GO with full links as primary, `is_a`-only as secondary), the target set is P's leaf descendants in L, kept if ≥ 3.
   - Split targets in half, seed 0, stratified by band (3–10, 11–50, 51–200, 201–500 leaves).
   - Any choice uses the TUNING half; the report uses the TEST half.
6. **Placement layer (display only, report-only).** Attach each internal pathway to the theme with the highest Jaccard to its leaf set. Report the distribution of that best Jaccard per band.

## Tests (all on the TEST half; CIs from a cluster bootstrap over targets, 1,000 resamples, seed 0)

- **Primary:** recall and precision of targets per band, per source, at Jaccard > 0.5 (the existing deciding-table code), for L, (a), and (b).
- Near-pair agreement among leaves (clarification 10).
- Matched theme count: L cut by support to HiDeF's count.
- Shape: themes per band, unplaced, multi-parent %, held-out FDR, stability, build time.
- **Named case:** Reactome "Signaling by Receptor Tyrosine Kinases" (R-HSA-9006934). Report its leaf-set size, the best theme Jaccard in each build, and whether "Signaling by SCF-KIT"'s leaves sit inside that theme.
- **Scatter:** for each internal pathway, the number of distinct root themes its leaves fall under, for L vs (a).

## Additional declared tests (added 8 Oct, before any result): can THEMA's TEXT place and name the held-out summaries?

These test the thematic approach directly. The curated hierarchy is used only as the judge. Both tests are REPORTED, not decisive. They run on internal pathways in the TEST half only.

### Test T: text placement (no API cost)

- Each internal pathway P was never in the build. Represent it by its own MedCPT description vector, centred with L's mean and renormalised.
- Represent each theme of the leaves build by the centroid of its members' vectors, centred on L and renormalised.
- **T1 (primary).** Place P on the theme with the highest cosine to P, among all themes of ≥ 3 members, with no size information. Score: Jaccard(P's leaf set, the placed theme's members). Report the median and the share > 0.5, per band and source.
  - Ceiling: gene placement (the theme whose gene union has the highest Jaccard with P's genes).
  - Floor: a random theme of the same size as the text-placed one (100 draws, seed 0).
  - Baseline: the same text procedure on HiDeF-on-L and on baseline (a).
- **T2.** For P whose leaves ARE recovered (some theme has Jaccard > 0.5 with P's leaf set): top-1 and top-5 accuracy of the text ranking in hitting that theme.

### Test N: naming from leaves (API cost; PRICED FIRST, Aviyah approves before any call)

- For recovered P, run the current namer on the matching theme. The namer sees leaf members only; P was never in the build.
- Score: semantic similarity of the generated name to P's held-out name, as a percentile against all GO BP and Reactome pathway names, using the encoders in the existing naming evaluation. Report the share at ≥ 90th and ≥ 98th percentile.
- **Leakage control (required).** Child names often contain the parent's name (for example "regulation of X" under X). Report separately the themes where NO member name contains P's name as a substring.
- **Abstention control.** Size-matched random leaf sets; report the abstention rate.
- Before any call, write the price (dry run) to the status file and STOP for approval.

## Decision rule (declared now)

The leaves version is preferred if, on the TEST half, it:
- is **not worse than (a) by more than 2 points** (CI excluding 0) in any 3–10 or 11–50 recall cell; and
- is **better than (a) by more than 2 points** (CI excluding 0) in at least one 11–50 or 51–200 recall cell; and
- keeps held-out FDR within the caps.

Otherwise the full-universe v0.4 stays. Nothing is frozen; Aviyah decides.

## Preservation

- Branch `leaves-2026-10`, created from main after v0.4 is merged and tagged `v0.4`.
- New files only. The universe filter is a new function or option whose default leaves v0.4's output byte-identical; re-run the byte-identity test.
- Outputs go to `data/ontology/v0.4-leaves/` and `data/experiments/leaves/`.
- `v0.3/` and `v0.4/` are untouched.
- Status: `docs/status/2026-10-08-leaves.md`.
- Estimate the time first; stop if it is over 3 h.
