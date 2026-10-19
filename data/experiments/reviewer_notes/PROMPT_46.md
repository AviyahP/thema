Prompt 46: areas on the O50s roots (Aviyah's version 1). Declared 18 Oct 2026, before any result. Exploratory: this adopts nothing. Prompt 45 ran (A1/A2) and its output stays; this is a separate design, not a fix of arm A. It also answers prompt 45's open question: here the giants are units, so areas can contain them. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 2 h.

WHY
Prompt 44 arm A used rec2fix's unit selection (giant drop: 867 units) and anchors. That is not the design Aviyah asked for. Her design: the units are the O50s roots, and the areas are built on top of the whole, unchanged O50s DAG.

SPEC
1. **Units:** the 261 O50s roots, the 5 giants included, each as one unit. No giant drop, no anchors. Each unit is the centroid of its members' vectors, with equal weight. Report the unit count and sizes.
2. **Areas pass:** rec2fix's code for everything else: 200 runs on 80% subsamples, Ward, recurrence 0.70 on unit sets, union pathway sets, consensus, the joint fixed point (twin 0.50, chain 0.85) on union sets.
3. **Noise:** floors calibrated on 20 unit scrambles (3001-3020) and checked on held-out seeds 4002-4005. Target 0.008; caps 0.02 per stratum and 0.01 overall.
4. **One structure:** the O50s DAG unchanged, plus the areas. Strict containment checked over every pair of nodes (areas, giants, all O50s themes), then transitive reduction. Areas over 1,000 pathways are kept and flagged.

REPORT (docs/status/2026-10-18-areas-on-roots.md)
1. Held-out FDR per stratum with counts, and overall.
2. **Roots:** the count, and each root's id, kind (area or O50s theme), size and number of children.
3. **Small roots (≤50 pathways):** for each, the 3 larger nodes that contain the largest share of it, with that share and the number of pathways missing.
4. **Duplication, report only:** root pairs with J ≥ 0.5; roots ≥80% inside another node, binned by pathways missing (0, 1-5, 6-20, 21+).
5. Areas: count, size bands, and those over 1,000 with their sizes and number of units. Say which areas contain a giant.
6. Children per node, maximum and median.
7. Summary placement, against O50s's 92.6%; agreement with Reactome's top level (median best J).
8. A sanity check: 0 nodes that are 100% inside another node without being its descendant.

FOR THE REVIEWER (do not judge them yourself)
Write data/experiments/areas_on_roots_2026-10-18/ containing roots.tsv (id, kind, size, n_children, full member keys), small_roots.tsv (item 3, with full member keys of the root and its 3 containers), and areas.tsv (every area with full member keys and unit ids).

DECISION RULE (same as prompt 44)
It passes only if all hold: held-out FDR within the caps; fewer than 49 roots; blind reading of every root at least 80% coherent or linked umbrella; every small root judged, blind, a distinct topic rather than belonging under one of its 3 containers; C6 intruder test at least 70%. Duplication is reported, not a gate. Aviyah decides.

FINAL
- Save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_46.md, and copy it into DECISIONS.md as "declared before running", before building.
- Output: data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/.
- Write docs/status/commit-2026-10-18-areas-on-roots.sh, to run after commit-2026-10-18-armA-containment.sh. It commits the code, tests, build, status note, reviewer folder and PROMPT_46.md. No branch operations; no push of main.

END OF PROMPT. Before building, give the unit count and the time estimate. After the build, give:
- the FDR summary;
- the roots with sizes;
- the small roots and duplication bins;
- areas over 1,000, and which contain a giant;
- placement and Reactome agreement;
- the commit script path.
