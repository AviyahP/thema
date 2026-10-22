Prompt 52: which relationships do O50s's merges act on? Declared 22 Oct 2026, before any result. Evaluation only: no build changes, nothing adopted. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_52.md, and copy it into DECISIONS.md as "declared before running".

WHY
The O50s merges were designed for relationships: twins are siblings (themes sharing a parent), chains are parent and child. In the code, the consensus merge (J >= 0.5) and the stale-merge repair test only the two sets, not whether they share a parent, and consensus runs before the DAG exists. This checks what the merges actually act on.

TASK
1. Re-run the O50s build from the cached trees and stored floors with logging only, and verify it reproduces O50s byte for byte (scripts/o50s_build.py --verify or equivalent). Log every merge with both member sets:
   - consensus: every pair resolved as "same theme" (the dropped one and the one kept);
   - repair, stale merges (identical and overlap);
   - repair, chain collapses (child holding at least 0.85 of the parent).
2. Classify each merged pair against the final O50s DAG, adding the dropped set as if it were a node (its parents = the smallest final themes that strictly contain it):
   - siblings: they share at least one immediate parent, or both have none (both roots);
   - nested: one strictly inside the other (say whether immediate parent-child or deeper ancestor);
   - unrelated: neither.
3. For chain collapses: whether the kept node was the parent or the child, by size band of the parent.
4. DROPPED PARENTS, ALL OF THEM (Aviyah's question: which parents that would build the top exist anywhere in the data, and where and why were they lost?). Do not filter on support or redundancy; record them as attributes instead.
   - Units: every grouping (its completed set, as the build sees it; also record its raw size) and every family (after step 5).
   - A unit is a POTENTIAL PARENT if it strictly contains at least 2 final O50s themes that are not nested in each other, at least one of which is a final root, and it is not in the final build (no final theme at J >= 0.9).
   - For each potential parent record: size; runs that found it (including 1 = only its own run); support; its stratum's floor; J to its nearest final theme; whether the build's rules would call it redundant (J >= 0.5 with a final theme it is not nested with; or a final theme inside it holding 0.85 or more of it); the final themes and roots it contains.
   - And the STAGE where it was lost, with the reason: completion (completed set under 3), absorbed as a variant into another grouping's family (which seed), the gate (support, floor, gap), consensus (superseded by which theme, J, both supports), stale merge, chain collapse (replaced by which child, that child's support), or other (say what).

REPORT (docs/status/2026-10-22-merge-relationships.md)
- Counts per merge kind (consensus, stale identical, stale overlap, chain) by relationship (siblings, nested immediate, nested deeper, unrelated), with size bands (3-9, 10-19, 20-49, 50-199, 200+) of the kept node.
- For pairs classed unrelated: J distribution and 10 examples with sizes and node ids.
- Chain collapses: kept parent vs kept child, by the parent's size band.
- Potential parents, every drop: counts by stage x runs found (1, 2-4, 5-19, 20+) x size band (20-49, 50-199, 200-399, 400-799, 800+), separately for groupings and families, and how many are redundant by the build's rules; for each stage, how many current roots its potential parents would contain (each root counted once) and how many current roots of 50 or fewer; per stage, the 30 that contain the most current roots, with size, runs, support, floor, reason and the roots they contain.
- Verification line: O50s reproduced byte for byte.
Write the per-pair table to data/experiments/merge_relationships_2026-10-22/pairs.tsv, and every potential parent to potential_parents.tsv (id, unit, size, raw size, runs, support, floor, redundant flags, stage, reason, the final themes and roots it contains, and its full member keys) in the same folder.

FOR THE REVIEWER (coherence is judged blind by the reviewer; do not judge anything yourself): in the same folder, read_parents/: per stage, the 15 potential parents that contain the most current roots plus 15 drawn at random (seed 20261022), families preferred over groupings when both exist for the same set; full member lists as "name [source]" sorted by name, random ids, no stage, support or node id shown; batches of about 2,600 lines, a parent never split. KEY_DO_NOT_SHARE_parents.json maps ids to everything else.

FINAL
Write docs/status/commit-2026-10-22-merge-relationships.sh, to run now (the earlier scripts have all been run; HEAD is b1090a2). It commits the code, status note, experiment folder, PROMPT_52.md, DECISIONS.md and data/experiments/reviewer_notes/PROMPT_51.md (carried forward), listing files explicitly, leaving out any file over 50 MB (and saying which), and never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give the counts table, the chain table, the potential-parents tables, the reviewer batch paths, and the commit script path.
