Prompt 38: areas as one operator, applied recursively (constrained, size-weighted Ward), declared 16 Oct 2026 before any result. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not touch frozen folders or the rec, rec2 and rec2fix builds; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h.

WHY
Reviewer findings from 15-16 Oct (project docs; data/experiments/giants_reading_2026-10-15/ and top_compare_2026-10-16/):
- O50's giants are mostly wide themes, not grab bags. Keep them.
- The pathway-level pass cannot make stable 200-1,000 groups: c85 had only 10, O50 has 7. The 8 Oct diagnostic agrees: mid-size clusters recur at J 0.5 but not at 0.70.
- The areas pass fills that layer and browses better. But it carries ad hoc parts (anchors, giant drop, seam rules), and its equal weighting was never argued.

This prompt restates the areas pass as one formal operator, so a paper can describe it. The precedents are Louvain-style aggregation, constrained Ward, HiDeF and NeXO.

THE OPERATOR T (reuse the existing code)
200 runs on 80% subsamples; Ward; recurrence 0.70 on item sets; floors solved on 20 item scrambles (seeds 3001-3020), held out on 4002-4005, target 0.008, caps 0.02 per stratum and 0.01 overall; consensus; joint fixed point with twin 0.50 and chain 0.85 on pathway union sets; strict containment.

RECURSION
- **Level 0** is the frozen O50, as is.
- **Level k+1** is T applied to the items of level k: the maximal level-k nodes with at most 1,000 pathways (giants are not items), plus any pathway in none of them.
- **Each item** is its pathway set. Its position is the size-weighted centroid of its members (vectors_leaves_centred). Its Ward weight is its pathway count: initialise Lance-Williams with these sizes, so this is Ward continued from fixed clusters (must-link). Items overlap; report how much double counting that causes.
- **No anchors, no giant drop, no seam special cases.** After each level, build one structure over all nodes (O50 nodes including giants, plus all area levels):
  - edges by strict containment, transitively reduced;
  - twin and chain rules applied over the whole set;
  - an area's pathways are always the union of its items.
- **Stop** when a level admits no candidate under the floors, or when the structure has 60 roots or fewer.

ARMS
- **W:** size-weighted, as above. This is the primary arm.
- **E:** equal weight per item, otherwise identical. This is an ablation only.
Output: data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/{W,E}/

REPORT (docs/status/2026-10-16-areas-rec3.md), each arm against O50 and rec2fix with giants in
- Per level: items, held-out FDR per stratum with counts, and areas by size band.
- Roots: count and the list with sizes. Maximum and median direct children.
- Areas over 1,000 pathways, and how many areas each item over 200 pathways joins.
- Summary placement, overall and by band.
- Agreement with Reactome's top-level pathways (best Jaccard).
- Root pairs with J of 0.30 or more.

DECISION (declared now)
Arm W is accepted for further work if all of these hold:
- held-out FDR within the caps at every level;
- 20-60 roots, giants included;
- no node with more than 60 direct children;
- summary placement at least O50's 85.3%;
- reviewer checks pass: C6 intruder test at least 70%, and any new node over 1,000 pathways gets the 15 Oct giant reading and intruder test;
- Aviyah judges the top intuitive.
Arm E only shows what the weighting does. If W fails, nothing is adopted and O50 stays as it is.

FINAL
- Copy this prompt verbatim into DECISIONS.md as "declared before running", before building.
- Write docs/status/commit-2026-10-16-areas-rec3.sh. It commits:
  - the code, tests, build folders and status note;
  - data/experiments/reviewer_notes/PROMPT_38.md;
  - the reviewer folders data/experiments/giants_reading_2026-10-15/, top_compare_2026-10-16/, and the files added to areas_rec2_giantdrop_2026-10-15/ since prompt 37, never any KEY_DO_NOT_SHARE* file.
  No branch operations; no push of main.

END OF PROMPT. Before building, give in a few lines:
- how many items level 1 has;
- how you implement size-weighted Ward;
- the time estimate.
After the build, give:
- per-criterion pass or fail for W;
- roots and sizes;
- the W vs E table;
- the commit script path.
