Prompt 36: areas, second and last try, declared 15 Oct 2026 before any result. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not touch frozen folders or thema_L_x2_O50_rec; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h.

WHY (the reviewer's reading of prompt 34; the three changes below are post hoc and must be labelled so)
Prompt 34 failed its declared criteria:
- **Held-out FDR:** strata 3-3 (0.038) and 7-9 (0.026) were over the 0.02 cap.
- **Bags at the top:** 3 roots hold 2,651-3,053 pathways.
- **Overlapping top:** the reviewer measured this on area_members.tsv. A pathway sits in a median of 3 of the 30 roots, and 5 root pairs share at least half their pathways (pathway Jaccard 0.71, 0.52, 0.51, 0.51, 0.47).

Two causes:
- **(a) Overlap was measured on the wrong sets.** The 0.50 same-theme cutoff was measured on unit sets, while units themselves share pathways. Two areas with different units can therefore hold mostly the same pathways.
- **(b) Area-sized units were clustered as ordinary units.** These are the themes over 200 pathways (immune 813, gene expression 781, cell cycle 349, and others). Their centroids are generic, so they join several areas at once; for example, n01027 sits in all three bag roots.

CHANGES (everything else exactly as in prompt 34; reuse its code)
1. **Anchors.** Every unit with more than 200 pathways is an anchor: a finished area, not clustered at level 2.
   - Anchors are roots of the combined DAG.
   - The level-2 build runs on the remaining units only.
   - Report the anchors with their sizes.
2. **Overlap measured on pathways.** Inside level 2, the same-theme cutoff (0.50, consensus and stale pass) and chain collapse (0.85) use pathway sets: the union of each candidate area's units' members. Unit sets are no longer used for these. Recurrence matching (0.70) stays on unit membership.
3. **Floors.**
   - Calibrate on 20 unit scrambles (seeds 3001-3020), held out 4002-4005 (4 seeds), target 0.008.
   - Caps unchanged: 0.02 per stratum, 0.01 overall.
   - Report each stratum's count of real candidates beside its FDR.
4. **Output:** data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/, with the same files as rec plus anchors.tsv.

REPORT (docs/status/2026-10-15-recursive-top-2.md)
- Everything prompt 34 reported, side by side with rec.
- The distribution of how many roots each pathway sits in.
- Every root pair with pathway Jaccard of 0.30 or more.
- The 30 largest areas by pathways.

DECISION (declared now)
Accepted for further work only if all of these hold:
- held-out FDR is within the caps in every stratum and overall;
- 20-60 roots, anchors included;
- no node has more than 60 children;
- at least 95% of the 476 giant-only themes get a parent area or anchor;
- no two roots have pathway Jaccard of 0.50 or more (O50's own rule, applied at the top);
- no area holds more than 1,000 pathways (O50's own giant definition);
- C6 (reviewer, after the build) passes: the blind intruder test as declared in prompt 34;
- Aviyah judges the top intuitive.
If it fails, there is no third try. The working view becomes O50 with the giants dropped and about 660 flat roots.

FINAL
- Copy this prompt verbatim into DECISIONS.md as "declared before running", before building.
- Write docs/status/commit-2026-10-15-recursive-top-2.sh (code, tests, build folder and status note on leaves-2026-10; no branch operations; no push of main). It also commits reviewer files still uncommitted: data/experiments/reviewer_notes/PROMPT_36.md, and in data/experiments/naming_O50_2026-10-14/style/: PREREG_style.md, REPORT_style.md, H1_pairs_for_Aviyah.md, new_names.json, scores_style.json, inputs/, raw/, evalout/. Never any KEY_DO_NOT_SHARE* file.

END OF PROMPT. Before building, confirm in one line:
- the anchors with their sizes;
- the number of level-2 units;
- the time estimate.
After the build, give:
- per-criterion pass or fail;
- roots and sizes;
- held-out FDR per stratum with counts;
- root overlap;
- summary placement against rec;
- the commit script path.
