Prompt 50: does the core-based algorithm (build C1b) beat O50s? Declared 20 Oct 2026, before any result. Exploratory: nothing is adopted without Aviyah. It replaces the withdrawn Part B of PROMPT_48_49.md, with one change: copies are matched at prompt 47's per-stratum thresholds, so that mid-sized groups have enough copies to form a core. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file after writing it; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first; stop if it is over 4 h and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_50.md, and copy it into DECISIONS.md as "declared before running", before computing anything.

SPEC. Start from O50s exactly: x2 universe, arm L, the 200 cached trees, the cached sides (real, calibration 3001-3010, held-out 4001-4006), the O50s strata. Change only what follows. Every step is applied identically to the real and to the scramble sides.
1. Candidates. Unchanged: every cluster of 3 or more; identical sets stored once (groupings).
2. Matching. A run finds a grouping if one of its clusters matches it at the threshold prompt 47 chose for the grouping's stratum: 0.70 below 10 pathways, 0.50 for 10-19, 0.60 for 20-39, 0.50 from 40 up. Pathways counted on those present in both subsamples. One copy per run.
3. Inclusion. For each grouping, from its matched copies: inclusion of a pathway = copies holding it / copies from runs where it was in the subsample. Groupings with fewer than 10 copies keep their own set as both core and members.
4. Core. Inclusion >= 0.9. Also report core size at inclusion 1.0.
5. p, the extras cut, per stratum. Extras = pathways with inclusion below 0.9. For p from 0.10 to 0.85 in steps of 0.05: R(p) = real extras with inclusion >= p, summed over the stratum's groupings; N(p) = the mean over the 10 calibration scrambles. p = the lowest value with N(p)/R(p) <= 0.008; if none qualifies, p = 0.9. Report the table and the held-out ratio at the chosen p.
6. Members. Core plus extras with inclusion >= the stratum's p. MIN_SIZE 3 applies to members.
7. Same theme: the mutual core rule. In today's rank order, each unclaimed grouping becomes a seed and claims every unclaimed grouping g with core(g) inside members(seed) AND core(seed) inside members(g). Always compare with the seed's own core and members (no chaining). The merged theme pools its groupings' copies (one per run: the union of that run's copies); inclusion, core and members are recomputed from the pool, using the seed's stratum p.
8. Gate. Support of a merged theme = runs that found any of its groupings / runs able to judge any. Floors solved per stratum on the scrambles after steps 2-7: target 0.008, rule of three where the scrambled count is 0, caps 0.02 per stratum and 0.01 overall. Checked once on 4001-4006.
9. Edges. Strict containment on members (every member of the child is a member of the parent), immediate parents only. No consensus merge, no chain collapse, no repair.

Tests before building: on a fixture, the mutual core rule never chains and is order-stable; with prompt 47's thresholds replaced by 0.70 everywhere, p = 0.5, no core step and the twin rule restored, the merge reproduces O50s's pre-gate families.

REPORT (docs/status/2026-10-20-core-construction-C1b.md), side by side with O50s
1. Copies per grouping by band (median); the p table; floors; calibration and held-out FDR per stratum and overall.
2. Themes per size band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); median core share per band.
3. Shape: roots and roots of 50 or fewer; giants (over 1,280) with sizes and core sizes; children per node, maximum and median; multi-parent share; mean themes per pathway; levels from a pathway to its root, median and maximum.
4. What the dropped steps would act on: parent-child pairs with the child holding at least 85% of the parent; non-merged theme pairs with J >= 0.5, by band.
5. O50s themes with a C1b counterpart at J >= 0.9 (share); the 164 O50s small roots and the roots n01027, n04526, n04670, n04671, n03316, n04672, n04995, n05001: counterpart J, and whether still a root.
6. Summary placement against 92.6%; Reactome median best J against 0.273.

FOR THE REVIEWER (do not judge anything yourself), in data/experiments/core_construction_C1b_2026-10-20/:
- R: every C1b root (if more than 300, a random 300, seed 20261020), full member lists as "name [source]" sorted by name, random ids, batches of about 2,600 lines in read_roots/.
- T: 24 random non-root themes per band (3-9, 10-19, 20-49, 50-199, 200+) from C1b AND the same from O50s, pooled, shuffled (seed 20261020), random ids, no build label, batches in read_themes/.
- KEY_DO_NOT_SHARE_C1b.json (id -> build, node, size, band); roots.tsv and themes.tsv with every member's inclusion and core flag; p_table.tsv.

DECISION RULE (applied by the reviewer and Aviyah after the readings; record it now)
C1b counts as better than O50s only if all hold:
1. held-out FDR within the caps;
2. fewer roots than O50s (261) and fewer roots of 50 or fewer (164);
3. its roots read coherent or linked umbrella at no less than 78.9% (O50s's 83.9% minus 5 points), with the R1 classes;
4. its sampled non-root themes read coherent or linked umbrella no more than 5 points below the O50s themes read in the same blind pool;
5. placement of at least 90% and Reactome median best J of at least 0.25.
Reported, not gates: giants, children per node, multi-parent share, and item 4 of the report.

FINAL
- Output build: data/ontology/v0.4-leaves/thema_L_x2_C1b/.
- Write docs/status/commit-2026-10-20-core-construction-C1b.sh, to run after the Prompt 48 commit script. It commits the code, tests, build, status note, reviewer folder and PROMPT_50.md, listing files explicitly and never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before building, give the time estimate and confirm the reproduction test passes. After the build, give: the copies table, the p table, the FDR summary, the shape table against O50s, items 4 and 5, and the commit script path.
