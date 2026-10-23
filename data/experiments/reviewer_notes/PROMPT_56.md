Prompt 56: how many of O50s's after-gate merges are missed twins? Declared 22 Oct 2026, before any result. Evaluation only: no build changes, nothing adopted. Design approved by Aviyah, 22 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
O50s removes duplicates twice: the 10% twin rule in families (before the gate) and consensus rule 3 (superseded, J >= 0.5) plus the stale merges and chain collapses in repair (after the gate). Consensus rule 2 (inherited) creates containment. Aviyah asks whether the after-gate rules are mostly catching twins that families should already have pooled. If so, the fix belongs in families; if not, the after-gate rules are doing a different job and stay.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first; if under 3 h, proceed without waiting; if over, stop and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_56.md (if not already there), and copy it into DECISIONS.md as "declared before running".

Build: frozen O50s (data/ontology/frozen/working-O50s-2026-10-22/). Reuse the event logs of prompt 52 (data/experiments/merge_relationships_2026-10-22/) if they hold both sets as they were at the moment of each event; otherwise replay O50s's consensus and repair with logging only, and confirm the replay reproduces frozen O50s byte for byte.

TWIN TEST: the step-5 variant test exactly as the code implements it (each side's private part at most max(2, 10% of the shared part), with the code's rounding). Quote the code lines you use. Applied to the two sets as they were at the moment of the event.

0. From the code: does step 5 compare groupings on their raw sets or their completed sets? Quote the lines.

1. Event counts in O50s, by rule: consensus rule 1 (nested), rule 2 (inherited), rule 3 (superseded), rule 4 (coexist), repair stale merges, chain collapses. Reconcile with 26,120 gated -> final 5,658.

2. For each of: rule 3 supersessions, stale merges, chain collapses, rule 2 inheritances, report
   a. how many pass the twin test (share, with counts);
   b. by J band: 0.5-0.6, 0.6-0.7, 0.7-0.83, 0.83+ (for chains and inheritances, also by size ratio smaller/larger: under 0.5, 0.5-0.8, 0.8-0.91, 0.91+);
   c. by size band of the larger theme (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+).

3. For the twin-test passes among rule 3 and stale merges: why families missed them. For each pair, take the two families' seed groupings (raw sets) and apply the twin test to them: raw twins too (greedy seeding split them) / raw not twins (completion moved the borders). Counts only.

4. For the rule 3 supersessions that FAIL the twin test: how many dropped themes are not strictly inside any final O50s theme (would be a root if kept); by size band.

5. Twenty examples, drawn at random (seed 20261022) from the rule 3 supersessions that fail the twin test, and twenty from those that pass: both member lists as "name [source]" sorted by name, J and sizes, no support values, no node ids, in data/experiments/missed_twins_2026-10-22/examples/. Do not judge them.

REPORT: docs/status/2026-10-22-missed-twins.md, tables for 0-4, and the example path.

FINAL
Write docs/status/commit-2026-10-22-missed-twins.sh, to run after commit-2026-10-22-S2-judgement.sh. It commits the code, status note, data/experiments/missed_twins_2026-10-22/ and PROMPT_56.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give the tables for 0-4 and the commit script path.
