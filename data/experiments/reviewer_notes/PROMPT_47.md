Prompt 47: the match threshold calibrated per size stratum (O50s-M). Declared 19 Oct 2026, before any result. Exploratory: this adopts nothing. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h; if it is, propose running only theta 0.50 and 0.70 first.

WHY
Reviewer diagnostics, 18-19 Oct, are in the project docs thema-small-roots-nesting, thema-support-history-and-stability and thema-loose-match-support, with files in data/experiments/small_roots_nesting_2026-10-18/.
- Above about 20 pathways, support at J >= 0.70 is low for nearly every theme (non-root median 0.02-0.04), because edges wobble. At J >= 0.50 the same themes recur in a large share of runs: median 0.29 for 20-50, 0.41 for 51-200, 0.95 for 201-1,000.
- The 164 small roots of O50s stay weak even at J >= 0.50: median 0.09 for 20-50. They have no recurring parent, and every one of their pathways also sits in other themes.
- On 8 Oct, matching at 0.50 for ALL sizes failed at 3-6 pathways, because noise recurs there. So the threshold must depend on size, like the floors.

SPEC
Start from the O50s configuration exactly: x2 universe, arm L, cached trees, the O50s strata (3, 4, 5, 6, 7-9, 10-19, 20-39, 40-79, 80-159, 160-319, 320-639, 640-1,279, 1,280+), consensus with twin 0.50, the joint fixed point with chain 0.85, and repair. THETA_MERGE (absorption and consensus) stays 0.70.

Change only THETA_MATCH, the threshold used for recurrence matching and support, per stratum:
1. **For each stratum and each theta in {0.50, 0.60, 0.70}:**
   - recompute real and scrambled support (calibration scrambles 3001-3010);
   - solve the floor as in prompt 43 (target 0.008; rule of three where the scrambled count is 0);
   - record the real count passing.
2. **Selection (declared):** per stratum, choose the theta that admits the most real candidates at calibration FDR <= 0.008. On a tie, choose the higher theta.
3. **Two arms:**
   - **M:** the chosen theta and its floor per stratum.
   - **Mm:** as M, plus a minimum support of 0.33 (the original declared m) in every stratum of 10 or more, measured under that stratum's chosen theta.
4. **Held-out check** on seeds 4001-4006, per stratum and overall. Caps: 0.02 per stratum, 0.01 overall.

REPORT (docs/status/2026-10-19-match-per-stratum.md), M and Mm side by side with O50s
1. Per stratum: the chosen theta, the floor, real counts passing at each theta, and calibration and held-out FDR.
2. Themes by size band: 3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+.
3. Shape:
   - roots, and roots of 50 or fewer;
   - giants with sizes;
   - children per node, maximum and median;
   - multi-parent share.
4. Small themes: the 3-50 count against O50s, and the share of O50s themes with a counterpart at J >= 0.9.
5. The 164 O50s small roots: how many have a counterpart at J >= 0.7, and how many of those are still roots.
6. These O50s roots: n01027, n04526, n04670, n04671, n03316, n04672, n04995, n05001. For each: its counterpart (J), and whether it is a root.
7. Summary placement against O50s's 92.6%; agreement with Reactome's top level (median best J).

FOR THE REVIEWER (do not judge them yourself)
Write data/experiments/match_per_stratum_2026-10-19/{M,Mm}/roots.tsv with id, size, support, the chosen theta and the full member keys.

FINAL
- Save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_47.md, and copy it into DECISIONS.md as "declared before running", before building.
- Outputs: data/ontology/v0.4-leaves/thema_L_x2_O50s_M/ and thema_L_x2_O50s_Mm/.
- Write docs/status/commit-2026-10-19-match-per-stratum.sh, to run after commit-2026-10-18-areas-on-roots.sh. It commits:
  - the code, tests, builds, status note, reviewer folder and PROMPT_47.md;
  - the reviewer's folders data/experiments/O50s_roots_reading_2026-10-18/, areas_on_roots_reading_2026-10-18/ and small_roots_nesting_2026-10-18/, if not already committed. List their files explicitly and never include any KEY_DO_NOT_SHARE* file.
  No branch operations; no push of main.

ORDER: step 1 first; report the per-stratum table before building the arms.

END OF PROMPT. Before building, give the time estimate. After the build, give:
- the per-stratum table;
- the FDR summary;
- roots, small roots and giants per arm;
- items 5 and 6;
- the commit script path.
