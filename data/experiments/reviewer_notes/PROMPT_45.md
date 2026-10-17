Prompt 45: fix strict containment in arm A of prompt 44. Declared 18 Oct 2026, before any result. A bug fix plus a report; it adopts nothing. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build (write a new build); working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 1 h.

WHY
In arm A (data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A/), 5 roots are 100% inside another node with 0 pathways missing, for example anchor n05000 inside O50s giant n03878, and n00225, n04999, n03971 inside n01419. Under strict containment they must be children. In O50s itself these edges exist, so the likely cause is the giant drop in rec2fix's unit selection: giants were removed as parents and never put back.

SPEC
1. **Find the cause** and fix it in the arm A assembly only, with rec2fix defaults unchanged (its tests must still pass).
2. **Rebuild arm A** with no reclustering: reuse the cached areas (areas_A_848items_200runs.json). Apply strict containment over the whole structure: every area, anchor, O50s giant and O50s theme, then transitive reduction. The twin and chain rules stay as they were.
3. **Report two views**, the second for reporting only:
   - **A1, strict:** containment at 100%.
   - **A2, Aviyah's propagation rule:** if a node is at least 98% inside a larger node and at most 5 pathways are missing, it becomes a child, and the missing pathways are added to the parent and all its ancestors with evidence score 0. Count the pathways added.

REPORT (docs/status/2026-10-18-armA-containment.md), for A1 and A2
- the cause, in 2-3 lines;
- the root count, and the list of roots with id, kind (area or anchor), size and number of children;
- where each O50s giant sits now (its parents);
- roots ≥80% inside another node, binned by pathways missing: 0, 1-5, 6-20, 21+;
- summary placement and agreement with Reactome's top level (median best J);
- held-out FDR is unchanged (no reclustering); confirm this.

FOR THE REVIEWER
Write data/experiments/top_two_arms_2026-10-17/A1/roots.tsv in the same format as A/roots.tsv (id, kind, size, n_children, full member keys).

FINAL
- Save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_45.md, and copy it into DECISIONS.md as "declared before running", before building.
- Output: data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A1/ (and A2/).
- Write docs/status/commit-2026-10-18-armA-containment.sh, to run after commit-2026-10-17-top-two-arms.sh. It commits the code, tests, builds, status note, reviewer file and PROMPT_45.md. No branch operations; no push of main.

END OF PROMPT. Before building, give the cause and the time estimate. After the build, give:
- the root counts for A1 and A2;
- the giants' parents;
- the near-containment bins;
- the commit script path.
