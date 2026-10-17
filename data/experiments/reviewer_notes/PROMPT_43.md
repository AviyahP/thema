Prompt 43: O50 with size strata above 10 (O50s). Declared 17 Oct 2026, before any result. This build adopts nothing by itself. Prompt 42 is on hold: do not run it. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h.

WHY
Prompt 41 found that the 10+ stratum pools every size from 10 to 2,809 under one floor (0.025). The noisy small end (10-39) sets that floor. Above 40 pathways, scrambled groupings never recur twice, yet 6,453 real candidates do, with a rule-of-three FDR bound under 0.0032. Large clusters are being judged by small-cluster noise.

The fix extends the existing per-size stratification. Nothing else changes.

SPEC
Start from the frozen O50 configuration exactly: x2 universe, arm L, cached trees, 0.70 match, absorption, consensus with twin 0.50, the joint fixed point with chain 0.85, and repair.

Change only the floors:

1. **Strata.** Strata 3, 4, 5, 6 and 7-9 keep their frozen cal8 floors unchanged. Replace 10+ with doubling strata: 10-19, 20-39, 40-79, 80-159, 160-319, 320-639, 640-1,279 and 1,280+.
2. **Solver for the new strata.**
   - Use the cached calibration scrambles (3001-3010).
   - The candidate cuts are every distinct support value seen in real OR scrambled candidates of the stratum.
   - FDR(cut) = (mean scrambled count ≥ cut) / (real count ≥ cut).
   - Where the scrambled count is 0, replace it with the rule-of-three bound 3/10 per seed.
   - The floor is the lowest cut with FDR ≤ 0.008. If no cut reaches it, the stratum admits nothing.
3. **Held-out check.**
   - Seeds 4001-4002 (cached) plus 4003-4006, which must be computed.
   - Report per-stratum and overall held-out FDR.
   - Caps: 0.02 per stratum, 0.01 overall.

REPORT (docs/status/2026-10-17-O50s-strata.md), O50s vs O50
1. **Floors:** per stratum, the floor, the real count passing it, the calibration FDR and the held-out FDR. Mark which strata used the rule-of-three bound.
2. **Themes by size band:** 3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+. Give the counts after the full build.
3. **Shape:**
   - giants (over 1,000) with their sizes;
   - roots, and how many are small roots of 50 members or fewer;
   - children per node, maximum and median;
   - multi-parent share.
4. **Small themes kept:** the count of themes of 3-50 against O50's. Also the share of O50 themes that have an O50s counterpart at J ≥ 0.9.
5. **Summary placement**, overall and by band, against O50's 85.3%.
6. **Agreement with Reactome's top level:** median best Jaccard.
7. **New large themes:** the themes of 101-1,000 that have no O50 counterpart at J ≥ 0.7, plus their best J to any rec2fix area.
8. **For the reviewer:** write data/experiments/O50s_review_2026-10-17/large_themes.tsv. It lists every O50s theme of 101-1,000 members, with id, size, support, status (new or kept) and the full member keys. Do not judge them.

DECISION (declared now; to be used only after the reviewer checks)
O50s becomes a candidate to replace O50 only if all of these hold:
- held-out FDR within the caps in every stratum and overall;
- the 3-50 theme count is at least 95% of O50's;
- the 101-1,000 band gains at least 2× O50's count;
- the reviewer's blind reading finds at least 90% of the new 101-1,000 themes coherent or a linked umbrella;
- the blind intruder test on them scores at least 70%;
- Aviyah decides.

FINAL
- Copy this prompt verbatim into DECISIONS.md as "declared before running", before building.
- Output: data/ontology/v0.4-leaves/thema_L_x2_O50s/.
- Write docs/status/commit-2026-10-17-O50s.sh, to run after commit-2026-10-16-resolution-limit.sh. It commits:
  - the code, tests, build, status note and the review folder;
  - data/experiments/reviewer_notes/PROMPT_42.md, marked on hold;
  - data/experiments/reviewer_notes/PROMPT_43.md.
  No branch operations; no push of main.

END OF PROMPT. Before building, give the time estimate. After the build, give:
- the floors table;
- the band table;
- the small-theme check;
- placement and Reactome agreement;
- the count of new large themes;
- the commit script path.
