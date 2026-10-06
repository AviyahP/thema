# THEMA evaluation protocol — A vs B vs HiDeF (declared 6 Oct 2026)

**Status of knowledge at declaration.** These results already exist and were seen: Preview 1 and 2 of the engine run (sibling AUROC for A, B, HiDeF), shape, stability and gates for A, B, B2, and the floors in each build's manifest. NOTHING below (test F, E1–E4) has been computed for any arm. Arms C, G, H stay paused and untouched. They resume afterwards under the engine rule exactly as declared. This protocol does not amend that rule.

**Arms.**
- **A** = THEMA-Ward (v0.3).
- **B** = THEMA-L (10-rung ladder).
- **HiDeF-tuned**: HiDeF at its best parameters, chosen as in §H.

**Shared definitions.**
- **Bands** are set by curated (or planted) term size: 3–10, 11–50 ("fine") and 51–200, 201–500 ("middle").
- **Margin:** 0.02 (2 points).
- **CIs:** paired cluster bootstrap, 2,000 resamples, seed 0.
  - Clusters for Reactome and the planted data: the top-level Reactome pathway each term descends from.
  - Clusters for GO: the child of biological_process each term descends from.
  - A term under several top-levels is assigned to the lexicographically first.
- **Anything changed after results** is a labelled post-hoc sensitivity.

---

## Test F — do the scramble floors earn their cost? (runs FIRST)

**Known before this test.** The manifests show the floors bind only on small themes:
- A raises the declared minimum support (0.33) only for sizes 3–5.
- B drops sizes 3–4 entirely and raises sizes 5–9.
- For everything above, the fixed 0.33 already decides.

**Steps, per arm A and B, on the 10,770:**
1. **Fixed-cut build.** Support ≥ 0.33 for every size, with no calibration. Everything else is unchanged.
2. **FDR at the fixed cut.** Use the build's own FDR computation, on all 15 existing scramble sides (3001–3010 and 4001–4005).
   - No threshold is fitted, so every seed is valid test data.
   - This is a second read of 4001–4005; it is labelled as such and is allowed because the cut is declared here.
3. **Report:**
   - themes per band, floors build vs fixed-cut build;
   - final-theme match between the two builds (Jaccard ≥ 0.70, worse direction);
   - wall time with and without calibration.
4. **Three seeds instead of ten.** Floors solved from 3001–3003 only. Report them beside the 10-seed floors, and their FDR on 4001–4005.
5. **Transfer.** Apply the 10,770 floors to each new universe used below: Reactome-only, GO-only, synthetic, SPECTER2. Check each with ONE held-out side (4001's scramble of that universe).
6. **HiDeF on scrambled data.** From the existing null builds (4001, 4002), count HiDeF communities per band and its implied FDR per band. This is the "what HiDeF lets through" line.

**Decision, per arm:**
- **DROP floors** if the fixed cut gives FDR ≤ 0.01 overall and ≤ 0.02 in every stratum. Default builds then have no scramble step. The FDR table becomes a one-off certificate in the paper.
- **Otherwise KEEP floors, in the cheapest passing form:**
  - 3 seeds if their floors pass the held-out FDR (≤ 0.01 overall, ≤ 0.02 per stratum), else 10;
  - on a new universe, reuse the 10,770 floors if the one-side check passes, else recalibrate that universe.
- Every later build in this protocol uses the form decided here.

---

## E1 — curated recovery (DECISIVE)

**Curated sets.**
- Reactome: each node of ReactomePathwaysRelation becomes the set {itself + all descendants} among the Reactome pathways in the universe.
- GO BP: each is_a term becomes {itself + all descendants} among the GO BP terms in the universe.
- Only sets of ≥ 3 members are kept.

**Builds:**
- (i) **Source-only.** A Reactome-only build and a GO-only build per arm. Centring is recomputed on the subset, as the method would do.
- (ii) **Full-build restricted.** Each 10,770 theme is cut down to its Reactome members (resp. GO members). Keep sets of ≥ 3 and deduplicate.

**Matching** (HiDeF's criterion plus CliXO's null):
- A curated set's score is its best-match Jaccard against any theme.
- **Null:** 100 label permutations (seed 0) of each built ontology, keeping its shape. Take the 95th percentile of the best-match Jaccard per band.
- A curated set is **recovered** if its score > max(0.5, that 95th percentile).
- **Recall** = share of curated sets recovered.
- **Precision** = share of themes whose best curated match passes the same rule.
- F1 is reported. Raw recall at 0.5 (no null) is reported too.

**Split** (protects against tuning HiDeF on the test):
- Curated sets are split in half at random (seed 0), stratified by band.
- The tuning half is used ONLY for selecting HiDeF's parameters (§H).
- All arms are scored on the test half.

**Bravi et al.** (arXiv 2608.28178): read their Reactome evaluation. If their metric can be computed from our outputs, report A, B and HiDeF-tuned in it (report-only).

## E2 — planted truth (DECISIVE at σ*, rest reported)

**Planted data:**
- Use the Reactome tree shape from E1, with the same Reactome pathways and the same dimension (768).
- Each curated node a gets a random unit direction u_a.
- Pathway p's vector = normalise( Σ over ancestors a of p, including p, of u_a / √(number of those ancestors) ), plus σ·g with g ~ N(0, I/768), then renormalised.

**Noise and replicates:**
- σ ∈ {0.5, 1.0, 1.5, 2.0, 3.0}; replicates use seeds 0, 1, 2.
- **σ\*** = the σ whose mean top-15 cosine is closest to that of the real Reactome-only centred vectors. It is fixed before any engine runs on synthetic data.

**Scoring and null:**
- Score the E1 matching against the planted sets.
- HiDeF is tuned on replicate 0 at σ\*. All arms are scored on replicates 1–2.
- **Pure-noise dataset:** g only, no signal, seed 0. Report themes per band for every arm (expected: none).

**Stated limitation:** Gaussian geometry may favour Ward. This is why E2 is one of two decisive tests and never the only one.

## E3 — robustness the method did not average over (REPORTED)

- **Source drop.** Declared prediction: Reactome-only themes reappear in the full build restricted to Reactome at Jaccard ≥ 0.70. Report the fraction recovered per band, per arm, from E1's builds.
- **Embedding swap.**
  - Re-embed the same descriptions with SPECTER2 (allenai/specter2_base + proximity adapter, the model Bravi et al. used), with the same centring and renormalising.
  - Build A, B and HiDeF-tuned on these vectors.
  - Report, per band, the fraction of MedCPT-build themes matched in the SPECTER2 build (Jaccard ≥ 0.70, worse direction), and E1 recall on the SPECTER2 builds.
- Resampling stability (two run halves) is still reported. It is labelled circular for THEMA.

## E4 — independent biological evidence (REPORTED)

- **STRING v12** coherence (the existing G4 code) for HiDeF-tuned, beside A and B.
- **Co-expression.** If a free public human gene co-expression resource of ≤ 5 GB exists (e.g. ARCHS4 correlations):
  - Per theme, the mean co-expression between genes of different member pathways, excluding shared genes, vs 100 size-matched random themes (seed 0).
  - Report the fraction of themes with p < 0.01 per band.
  - Otherwise write "co-expression not run" and why.
- **Blind rating sheet** (built, not rated):
  - 40 random themes per arm (seed 0), mixed together, arm hidden, member pathway titles shown.
  - Key in data/keys/eval_rating_key.tsv.

## Also reported

- Sibling AUROC (the 16 scores) for HiDeF-tuned.
- Gene-overlap grouping: pairs with gene Jaccard ≥ 0.5 or overlap coefficient ≥ 0.8 vs size-matched random pairs, AUROC per band, with kappa@100 as reference.
- Core build time (no calibration) and full time, against HiDeF, on the same Mac.

---

## §H — HiDeF at its best

**Grid:**
- kNN k ∈ {10, 15, 30} (cosine, symmetric union, weight = cosine);
- maxres ∈ {25, 50, 100};
- persistence χ ∈ {3, 5, 10};
- τ = 0.75 and the other defaults kept;
- 27 settings per universe.

**Selection:** the highest mean recall over the 4 bands × 2 sources on the E1 tuning half, run separately for E1 and for E2 (replicate 0, σ\*). This is HiDeF-tuned.

**Oracle line (reported):** HiDeF's best setting per cell, chosen on the test half. This is an advantage A and B never get. If a THEMA arm still wins against the oracle, say so. If it wins only against HiDeF-tuned, say that too.

## Final decision rule (A, B, HiDeF)

**Decisive recall cells:**
- E1 source-only (2 sources × 4 bands);
- E1 full-restricted (2 × 4);
- E2 at σ\* (4 bands).

**Rule:**
1. A THEMA arm X **beats HiDeF** if all of these hold:
   - X is better than HiDeF-tuned by > 0.02, with the CI excluding 0, in at least one fine-band cell AND at least one middle-band cell;
   - X is not worse by > 0.02 (CI excluding 0) in any decisive recall cell;
   - X is not worse by > 0.02 (CI excluding 0) in E1 source-only precision.
2. If both A and B beat HiDeF, the max-min shortfall over the decisive cells chooses. Ties within 0.01 go to fewer knobs, then to the faster core build.
3. **If neither beats HiDeF**, HiDeF becomes THEMA's engine. THEMA's contribution is then the descriptions, embeddings, naming and statistics layer, plus the Test-F certificate where it applies.
4. Nothing is frozen. Aviyah decides. Then arms C, G and H resume under the engine rule, and any winner among them is re-checked against this protocol.
## Clarifications 1–8 (declared 6 Oct 2026, before any result of this protocol)
1. Floors on a new universe go through a declared override, `--floors-transfer <file>`. It records the source and the target universe digests in the manifest, and is valid only together with Test F step 5's one-side held-out check. The existing guard is otherwise unchanged.
2. Recall bands are always set by the curated (or planted) set's size. Precision bands are set by the theme's size after restriction. Restricted themes under 3 members are dropped.
3. Planted sets under 3 members are excluded, as in E1.
4. σ* is computed from the Reactome-only centred vectors (the subset of the embedding matrix, recentred and renormalised; no build is needed). It is fixed before any engine runs on synthetic data.
5. E2's HiDeF-tuned is selected on mean recall over the 4 planted bands, replicate 0, σ*.
6. Knobs = the parameters a user sets in that arm's manifest. The ladder counts as one knob. The count per arm is listed in the report.
7. Bands are by curated-set size, not theme size, so every arm can win any band: a 5-member theme matches a 3-member curated set at Jaccard 0.6. A win in either 3–10 or 11–50 satisfies "fine", and a win in either 51–200 or 201–500 satisfies "middle". There is no special case for any arm.
8. Test F decides per arm. Each arm is evaluated as a complete method in the form Test F decided for it, and the report states each arm's form. No further adjustment.

Also recorded: co-expression is not run. The only resource found, ARCHS4, is 7.49 GB and in R format, over the declared 5 GB limit.
