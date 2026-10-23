Prompt 54: O50s's own logic with one change, the same-theme merge restricted to siblings (build S2). Declared 22 Oct 2026, before any result. Exploratory: nothing is adopted. Design: Aviyah, 22 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
Prompt 53's S1 changed two things at once: it removed consensus's inheritance (rule 2: a theme with at most 1 member outside a larger theme makes the larger one grow to contain it) AND restricted the same-theme merge to siblings. The result (991 roots) cannot separate the two. The checks after it showed inheritance added 11,932 members in O50s and that 55.2% of O50s's edges exist only because of it. S2 changes ONE thing relative to O50s: the same-theme merge (consensus rule 3, superseded at J >= 0.5, and the stale merges in repair) applies only to pairs that are siblings in the DAG. Everything else is exactly O50s.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first; if under 3 h, proceed without waiting; if over, stop and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_54.md (if not already there), and copy it into DECISIONS.md as "declared before running".

SPEC. Start from the 26,120 gated themes of frozen O50s, exactly as prompt 53 reconstructed them. Use O50s's consensus and repair code unchanged, with this single change:
- Sibling = two themes sharing at least one immediate parent, or both roots, in the DAG (strict containment, immediate parents) of the current theme set.
- Consensus rule 3 (superseded: non-nested, J >= 0.5, the lower in consensus order dropped) applies only if the pair are siblings. Non-sibling pairs that would have been superseded fall through to rule 4 (coexist). Rules 1 (nested) and 2 (inherited: at most 1 member outside, the larger grows, with propagation to ancestors exactly as the code does it) are unchanged and apply to every pair as now.
- Repair unchanged (chain collapse at 0.85 with survivor "support", joint fixed point), except that stale merges apply only between siblings.
- Rounds: build the DAG of the gated themes; run the restricted consensus; run the restricted repair; rebuild the DAG from the resulting memberships; repeat consensus and repair on the resulting themes until a round changes nothing. Report the number of rounds and, per round, inherited members, themes that grew, supersessions, chain collapses and stale merges.
- Final edges: strict containment, immediate parents.

Tests before building: with the sibling restriction switched off, the code reproduces frozen O50s byte for byte; on a fixture, the restricted rule 3 never supersedes a non-sibling pair, and rule 2 still fires on non-sibling pairs.

REPORT (docs/status/2026-10-22-S2-sibling-restricted.md), S2 against O50s and S1p, same code:
A. Construction: gated themes, inherited members and themes grown, supersessions (and how many O50s supersessions became coexist), chain collapses, stale merges, rounds, final themes; held-out FDR (unchanged at the gate; confirm).
B. Shape: themes per band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); roots and roots of 50 or fewer; giants (over 1,280) with sizes and how many members each gained by inheritance; children per node, maximum and median; multi-parent share; mean themes per pathway; levels to root, median and maximum; edges that exist only because of inherited members.
D. The 76 parents consensus superseded in O50s: how many survive in S2 (J >= 0.9), how many O50s roots they contain.
E (short). O50s themes with an S2 counterpart at J >= 0.9 (share, by band); summary placement; Reactome median best J.
Sections C, F, G and reviewer material are NOT run now.

FINAL
- Output: data/ontology/v0.4-leaves/thema_L_x2_S2/.
- Write docs/status/commit-2026-10-22-S2.sh, to run after commit-2026-10-22-restructured-S1.sh. It commits the code, tests, build, status note and PROMPT_54.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before building, give the time estimate and confirm both tests pass. After, give sections A, B, D and E as tables for S2, O50s and S1p, and the commit script path.
