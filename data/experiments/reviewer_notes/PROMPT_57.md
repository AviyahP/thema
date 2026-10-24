Prompt 57: trim the child instead of growing the parent (build T1). Declared 23 Oct 2026, before any result. Exploratory: nothing is adopted. Design approved by Aviyah, 23 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
In O50s, consensus rule 2 (inherited) makes containment strict by GROWING the larger theme to take the smaller one's stray member, and propagating the growth to every ancestor. That growth piles up at the top (the giants) and builds 55% of the edges. Strict containment is a hard requirement (downstream statistics on the DAG need a parent's genes to include its child's). T1 keeps strictness but edits in the other direction: the SMALLER theme drops its stray member. One change relative to O50s; nothing else moves.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time (start after prompt 56 Part A is finished); times in UTC+1. Give the time estimate first; if under 3 h, proceed without waiting; if over, stop and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_57.md (if not already there), and copy it into DECISIONS.md as "declared before running".

SPEC. Start from the 26,120 gated themes of frozen O50s (data/ontology/frozen/working-O50s-2026-10-22/), exactly as prompts 53-54 reconstructed them. Use O50s's consensus and repair code unchanged except for rule 2:
- Trigger unchanged: the same pairs, in the same consensus order, that fire rule 2 in O50s's code (the smaller theme has at most 1 member outside the larger).
- Edit flipped: instead of adding the stray member to the larger theme and its ancestors, REMOVE it from the smaller theme, and from every kept theme contained in the smaller theme that holds it (downward propagation, which strict containment requires; the mirror of today's upward propagation).
- A theme that falls below 3 members is dropped (the existing minimum size, unchanged).
- Rules 1, 3, 4, the repair (stale merges J >= 0.5, chain collapse 0.85, survivor "support", joint fixed point) and final edges (strict containment, immediate parents) unchanged.

Tests before building: with the flip switched off, the code reproduces frozen O50s byte for byte; on a fixture, the flipped rule never adds a member to any theme, and every final edge is strict containment.

REPORT (docs/status/2026-10-23-trim-T1.md), T1 next to O50s, same code:
A. Edits: rule-2 events; members added (O50s) vs members removed (T1); themes edited; themes losing more than 10% and more than 25% of their members (counts, by size band 3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); themes dropped for falling below 3; themes trimmed by more than one parent.
B. Shape: final themes; themes per band; roots, and roots of 50 or fewer; giants (over 1,280) with sizes, and for each O50s giant its best T1 counterpart (J, size); children per node, maximum and median; multi-parent share; levels to root, median and maximum; edges, and how many O50s edges survive.
C. Placement: share of the 5,539 pathways in at least one theme; of the members T1 removed, how many are still in another theme; mean themes per pathway.
D. Agreement: O50s themes with a T1 counterpart at J >= 0.9 (share, by band).
E. Held-out FDR at the gate (unchanged; confirm).
Readings, stability, recall and the other evaluation sections are NOT run now.

FINAL
- Output: data/ontology/v0.4-leaves/thema_L_x2_T1/.
- Write docs/status/commit-2026-10-23-trim-T1.sh, to run after commit-2026-10-22-missed-twins.sh. It commits the code, tests, build, status note and PROMPT_57.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before building, give the time estimate and confirm both tests pass. After, give sections A-E as tables, T1 next to O50s, and the commit script path.
