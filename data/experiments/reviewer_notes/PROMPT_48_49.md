Prompts 48 and 49, run in order: Part A (prompt 48, light) and then Part B (prompt 49, the build). Both declared 20 Oct 2026, before any result. Exploratory and evaluation only: nothing is adopted. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules for both parts: no API calls; do not commit, leave one commit script; never open any KEY_DO_NOT_SHARE* file after writing it; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time (Part A finishes before Part B starts); times in UTC+1. Give one time estimate for both parts before starting. Stop if Part A is over 1 h or Part B is over 4 h, and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_48_49.md, and copy it into DECISIONS.md as two entries, "Prompt 48, declared before running" and "Prompt 49, declared before running", before computing anything.

==================== PART A: PROMPT 48. Is arm M better than O50s below the top? Inputs for a blind comparison ====================

WHY
Prompt 47's arm M (data/ontology/v0.4-leaves/thema_L_x2_O50s_M/) admits 47% more candidates than O50s. Its top level is already known to be worse (394 roots against 261). The open question is below the top: are M's extra themes coherent and distinct, or near-copies that only just pass? The reviewer reads the themes blind; you prepare the inputs and compute two descriptive measures. Do not judge any theme yourself.

POPULATIONS
- Builds: O50s (data/ontology/v0.4-leaves/thema_L_x2_O50s/) and M.
- M-unique: M themes of 10 or more pathways whose best Jaccard to any O50s theme is below 0.9. O50s-unique: the converse.
- Report both counts per size band: 10-19, 20-49, 50-199, 200+.

A1. BLIND READING INPUTS
- Per side, draw 15 themes at random per band (seed 20261019); if a band has fewer, take all and say so.
- Pool the up to 120 themes, shuffle (same seed), and give each a random id T001...
- For each theme write its full member list, one line per pathway: name [source], sorted by name. No build label, node id, theme name or support.
- Batches of about 2,600 lines in data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_bNN.md; a theme is never split across batches.
- Write index.json (id -> size) and KEY_DO_NOT_SHARE_m_vs_o50s.json (id -> build, node, size, band, support).

A2. REDUNDANCY (both builds, unique themes and all themes)
For each theme, its best Jaccard to any other theme of the same build whose size is within a factor of 1.5. Per band: the share at or above 0.8, and the median. Write redundancy.tsv (build, node, size, band, unique yes/no, best J, partner node).

A3. SUPPORT
For each unique theme, its support as used by its own build's gate (M: the stratum's chosen theta; O50s: 0.70) and its stratum's floor. Per band and side: median support, and the share at or below 0.02. Write support.tsv.

DECISION RULE (applied by the reviewer after the blind reading; record it now)
M counts as better than O50s below the top only if both hold: M-unique themes read coherent or linked umbrella at a rate no more than 10 points below O50s-unique themes; and M-unique themes have a near-copy share (best J >= 0.8) no higher than O50s-unique themes. Otherwise O50s stays the base and prompt 47's size-dependent threshold is recorded as a finding, not adopted. Aviyah decides.

Part A status note: docs/status/2026-10-19-m-vs-o50s-inputs.md (counts, the two tables, the batch list).

==================== PART B: PROMPT 49. Core-based construction (build C1) ====================

WHY
In O50s a theme is its 50%-inclusion member set. Groupings with the same recurring core but different extras stay separate themes unless they differ by 10% or less, which multiplies themes and roots. Reviewer diagnostic of 20 Oct: cores are real and stable; the giants are a stable part plus 400-950-pathway blocks that join in only 33-73% of runs. C1 makes the core a theme's identity (Aviyah's design decisions of 20 Oct).

SPEC. Start from O50s exactly: x2 universe, arm L, the 200 cached trees, the cached real side, calibration scrambles 3001-3010, held-out 4001-4006, the O50s strata. Change only what follows.
1. Candidates and matching. Unchanged: every cluster of 3 or more, identical sets stored once (groupings); recurrence matching at J >= 0.70 on shared pathways; one copy per run.
2. Inclusion. For each grouping, from its own matched copies: inclusion of each pathway = copies holding it / copies from runs where it was in the subsample (as family_members does now). Only groupings with at least 10 copies get a core; the rest keep their own set as both core and members.
3. Core. Inclusion >= 0.9. Also report core size at inclusion 1.0.
4. p, the extras cut, per stratum. Extras = pathways with inclusion below 0.9. For p from 0.10 to 0.85 in steps of 0.05: R(p) = real extras with inclusion >= p, summed over the stratum's groupings; N(p) = the mean over the 10 calibration scrambles, processed identically. p for the stratum = the lowest p with N(p)/R(p) <= 0.008. If none qualifies, p = 0.9 (members = core). Strata by the grouping's own size. Report the table, and the held-out ratio at the chosen p on 4001-4006.
5. Members. Core plus extras with inclusion >= the stratum's p. MIN_SIZE 3 applies to members.
6. Same theme: the mutual core rule. In today's rank order, each unclaimed grouping becomes a seed and claims every unclaimed grouping g such that core(g) is inside members(seed) AND core(seed) is inside members(g). Always compare with the seed's own core and members, never with the growing family (no chaining). The merged theme pools all copies of its groupings (one per run: the union of that run's copies), and inclusion, core and members are recomputed from the pool, using the seed's stratum p.
7. Gate. Support of a merged theme = runs that found any of its groupings / runs able to judge any. Floors solved per stratum on the scrambles passed through steps 2-6 identically: target 0.008, rule of three where the scrambled count is 0, caps 0.02 per stratum and 0.01 overall. Check once on held-out 4001-4006.
8. Edges. Strict containment on members (every member of the child is a member of the parent), immediate parents only. No consensus merge, no chain collapse, no repair.

Tests, before building: on a small fixture, the mutual core rule never chains and is order-stable for identical inputs; with p = 0.5, no core step and the twin rule restored, the merge reproduces O50s's pre-gate families.

REPORT (docs/status/2026-10-20-core-construction-C1.md), side by side with O50s
1. The p table per stratum; floors; calibration and held-out FDR per stratum and overall.
2. Groupings, merged themes before the gate, themes after the gate; themes per size band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); median core share (core/members) per band.
3. Shape: roots, and roots of 50 or fewer; giants (over 1,280) with sizes and core sizes; children per node, maximum and median; multi-parent share; mean themes per pathway; levels from a pathway to its root (median and maximum).
4. What the dropped steps would act on: parent-child pairs where the child holds at least 85% of the parent (count, and nodes chain collapse would remove); theme pairs with J >= 0.5 that were not merged (count, by size band).
5. O50s themes with a C1 counterpart at J >= 0.9 (share); the 164 O50s small roots and the eight roots n01027, n04526, n04670, n04671, n03316, n04672, n04995, n05001: counterpart J and whether still a root.
6. Summary placement against O50s's 92.6%; Reactome median best J against 0.273.

FOR THE REVIEWER (do not judge them yourself): data/experiments/core_construction_C1_2026-10-20/ with roots.tsv (id, size, support, core size, n_children, every member key with its inclusion and a core flag), themes.tsv (id, size, support, core size, parents) and p_table.tsv.
Output build: data/ontology/v0.4-leaves/thema_L_x2_C1/.

==================== FINAL (both parts) ====================
Write ONE commit script, docs/status/commit-2026-10-20-prompts-48-49.sh, to run after commit-2026-10-19-match-per-stratum.sh. It commits, as separate commits, Part A (code, status note, experiment folder) and Part B (code, tests, build, status note, reviewer folder), plus PROMPT_48_49.md and the DECISIONS.md entries. List files explicitly; never include any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate for each part and confirm Part B's reproduction test passes before building. After Part A, give the unique-theme counts, the two tables and the batch paths. After Part B, give the p table, the FDR summary, the shape table against O50s, items 4 and 5, and the commit script path.
