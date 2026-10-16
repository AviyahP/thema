Prompt 37: areas layer, corrected re-run (rec2fix), declared 15 Oct 2026 before any result. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not touch frozen folders, thema_L_x2_O50_rec or thema_L_x2_O50_rec2; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h.

WHY: rec2 did not implement what was declared
This is a corrected re-run of prompt 36, not a new method. The reviewer audited rec2 (scripts in data/experiments/areas_rec2_giantdrop_2026-10-15/code/) and found two implementation gaps:

1. **Area pathway sets were trimmed.** Prompt 34 step 3 declared that an area's pathways are the union of its units' pathways. rec2 instead stored the consensus pathway set, which is smaller than the union for 188 areas (your report, section 7). Same-theme, collapse and containment all ran on the trimmed sets.
   - Example: R43 = b2_00313. All 16 of its units are also under R04 = b2_00198, so by units R43 lies entirely inside R04. It was left a root because 4 of its pathways are missing from R04's trimmed set, although they are in R04's own units.
   - With union sets, 9 roots are strictly inside another root.
2. **The tree's rules were not applied at the seams.**
   - Anchors were never checked against each other or against areas. n03376 (280) is 100% inside n01279 (781) and is unlinked.
   - Chain collapse was not applied between an area and its own units: 3 areas are 85-95% one unit.
   - 27 units are strictly inside an area but not linked to it.
   - area_edges.tsv lists transitive area->unit edges, which inflated your children count (181).

Aviyah's giant rule, written down now: areas over 1,000 pathways are giants and are kept out of the working view, exactly as O50's giants are. She intended this before the rec2 result but did not write it down; record that wording.

BEFORE BUILDING, answer in a few lines
- Why is n03376 not a child of n01279 in the frozen O50, when its members.tsv rows are 100% inside? If O50's containment uses a different membership definition (for example core members only), use that same definition everywhere below, and say which.
- Can consensus, collapse and the stale pass run on union sets as specified below? If not, say what you propose instead and stop.

SPEC: everything as in prompt 36 except the following; reuse its code, floors and seeds
1. **Union everywhere.** An area is a set of units. Its pathway set is always the union of its units' pathways, recomputed after every inheritance, merge or collapse. Same-theme 0.50, chain collapse 0.85, containment and sizes all use these union sets. Recurrence matching 0.70 stays on unit sets.
2. **One structure for the whole top.** After level 2, build the final structure over a single combined node set: areas, the 6 anchors and all units.
   - **Edges** are strict containment on pathway sets.
   - **Transitive reduction:** area_edges.tsv holds direct edges only; write the closure separately.
   - **Rules on every pair in this set,** with the same survivor rule as O50:
     - two nodes with J of 0.50 or more that are not nested are merged;
     - a parent whose child covers 85% or more of it collapses.
   - Report every merge and collapse that involves an anchor or a unit.
3. **Giants.** Areas over 1,000 pathways are flagged giant and kept out of the view. Their children are re-parented to their remaining parents or become roots.
4. **Output:** data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/, with the same files as rec2 plus giants.tsv and closure.tsv.

TESTS (all must pass before reporting)
- Every area's pathway set equals the union of its units.
- Every edge is strict containment.
- Every strict containment within the combined set is reachable through edges.
- No two non-nested nodes have J of 0.50 or more.
- No parent-child pair has a share of 0.85 or more.
- Children counts come from direct edges only.

REPORT (docs/status/2026-10-15-areas-rec2fix.md), side by side with rec2
- Levels, held-out FDR per stratum with counts.
- Anchors, giants (with sizes and the share of pathways they hold), merges and collapses at the seams.
- Roots of the view with sizes, and children per node (maximum and median).
- Root pairs with pathway J of 0.30 or more.
- How many roots each pathway sits in.
- How many roots are 80% or more inside another root (report only).
- Coverage of the 476 giant-only themes, and the pathway bands.
- Summary placement against O50 and rec2.

DECISION (declared now; this is the last build of the areas layer)
Accepted for further work if all of these hold, measured on the view (giants out):
- held-out FDR within the caps in every stratum and overall;
- 20-60 roots, anchors included;
- no node with more than 60 direct children;
- at least 95% of the 476 giant-only themes and of all units have a non-giant parent area or anchor, or are roots of the view;
- no two roots with pathway J of 0.50 or more;
- C6 blind intruder test, rerun by the reviewer under the 15 Oct pre-registration, passes;
- Aviyah judges the top intuitive.
If it fails: the working view is O50 without giants (about 660 flat roots).

FINAL
- Copy this prompt verbatim into DECISIONS.md as "declared before running", before building.
- Write docs/status/commit-2026-10-15-areas-rec2fix.sh. It commits:
  - the code, tests, build folder and status note;
  - data/experiments/reviewer_notes/PROMPT_37.md;
  - data/experiments/areas_rec2_giantdrop_2026-10-15/ (PREREG_C6.md, code/, roots.tsv, root_labels.json, ROOTS_for_Aviyah.md, C6_judgements.json, C6_misses.tsv, inputs/, batches/, c6_batches/), never any KEY_DO_NOT_SHARE* file.
  No branch operations; no push of main.

END OF PROMPT. Before building, give:
- the two answers above;
- the number of units and anchors;
- the time estimate.

After the build, give:
- per-criterion pass or fail;
- roots and sizes;
- giants;
- held-out FDR per stratum with counts;
- seam merges and collapses;
- summary placement;
- the commit script path.
