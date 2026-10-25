Prompt 64: L1 merge on members, repeated until stable (L1m), then the DAG. Declared 24 Oct 2026, before any result. Exploratory: nothing adopted. Design: Aviyah, 24 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
Prompt 63 showed L1 keeps many copies of each theme: 17,433 of 52,001 recurring themes repeat another's members exactly, each pathway sits in 210 themes (O50s: 23.5), and the top is 205 roots of 200+ that are variants of the same 7 sets. Cause: step 3 compared CORES (inclusion >= 0.9), which are unstable, so versions of one theme with slightly different cores never merged although their MEMBERS (inclusion >= 0.5) are the same or nearly so. Fix (Aviyah, 24 Oct): the same 90%-each-way rule, applied to members, repeated until nothing changes. It replaces the core-based merge; no new number.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file after writing it; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; proceed unless the COMPUTE alone is expected to exceed 2 h. Exact computation; verify each step against brute force on a random sample (seed 20261024) and report each check.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_64.md (if not already there), and copy it into DECISIONS.md as "declared before running". Record in DECISIONS: the L1 merge compares members, not cores (Aviyah, 24 Oct).

INPUT: prompt 61's steps 1-2 output (the 261,984 groups with a core: their copies, support, inclusions), real side and both scramble sides. Steps 1-2 are unchanged.

SPEC (real side and each scramble side)
1. Start: every group with a core is a theme; members = inclusion >= 0.5 over its copies; core = inclusion >= 0.9.
2. One pass: in O50s's family order (support descending, then member-set size descending, then key), each unclaimed theme becomes a seed and absorbs every unclaimed theme whose MEMBERS pass the test against the seed's members: at least 90% of each member set is inside the other. Compare with the seed only within a pass (no chaining inside a pass).
3. After the pass, each merged theme: copies pooled, one per run (the copy of its highest-support constituent found in that run); support pooled (runs that found any constituent / runs able to judge any); inclusions recomputed; members = inclusion >= 0.5; core = inclusion >= 0.9.
4. Repeat passes 2-3 on the resulting themes until a pass merges nothing. Report passes and merges per pass; cap at 50 passes and report if the cap is hit.
5. Keep themes found in at least 10 runs (provisional bar; label it so).
6. DAG: strict containment on members, immediate parents only; no inheritance, no collapse, memberships unchanged.

REPORT (docs/status/2026-10-24-L1m.md), L1m next to prompt 63's L1 (and O50s where given):
A. Merge: passes, merges per pass; themes before and after; groups per theme (median, max); largest themes and how much each grew across passes; identical member sets remaining (must be 0; assert it).
B. Themes per band (3-5 ... 1,600+) before and after the 10-run bar; scrambled / real ratio by band at 10 and 20 runs (two seeds, indicative); mean themes per pathway; non-nested J >= 0.5 pairs per theme.
C. DAG: roots (by band, and without 3-5); multi-parent share; children per node (max, median); levels to a root (median, max); every root of 200 or more pathways with size, children and its three largest children (share); for the seven large7 sets (best L1m match at J >= 0.9, or none), whether each is a root and its parents.
D. Near-misses (report only): pairs where the smaller is inside the larger except for 1, 2-5, 6+ pathways; how many roots would gain a parent with a tolerance of 1 and of 2 pathways, by band.
E. FOR THE REVIEWER (do not judge): every root of 100 or more pathways, shuffled (seed 20261024), random ids, "name [source]" sorted by name, batches of about 2,600 lines, in data/experiments/L1m_2026-10-24/read_roots/; mapping only in KEY_DO_NOT_SHARE_L1m_roots.json there. If this exceeds 40 batches, take roots of 200 or more instead and say so.

FINAL
Write docs/status/commit-2026-10-24-L1m.sh, to run after commit-2026-10-24-L1-dag.sh. It commits the code, note, data/experiments/L1m_2026-10-24/ (without the KEY file) and PROMPT_64.md, listing files explicitly, leaving out any file over 50 MB (and saying which). No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give sections A-D as tables, the reading batch paths, and the commit script path. Then stop.
