Prompt 62: are L1's large themes unions of smaller themes? Declared 24 Oct 2026, before any result. Evaluation only: no rule is applied, nothing removed. Design: Aviyah and reviewer, 24 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

DECISION TO RECORD FIRST (Aviyah, 24 Oct): the L1 merge rule is "two groups are the same theme if at least 90% of each core is inside the other" (90% each way), replacing Jaccard >= 0.9 on cores. Working side: data/experiments/L1_2026-10-24/real_bothways/. Record it in DECISIONS.md.

WHY
A blind reading of the 7 distinct sets above 800 pathways (found in >= 10 runs) gave: three broad domains (867 immunity, 1,143 metabolism, 1,491 core cell machinery) and four giants (2,267-2,412) that read as two or three domains glued together. Before choosing any rule against such unions, measure how often a large theme is mostly made of smaller accepted themes that are unrelated to each other.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; proceed unless the COMPUTE alone is expected to exceed 2 h. Exact computation, verified against a brute-force loop on a random sample (seed 20261024); report each check.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_62.md (if not already there), and copy it into DECISIONS.md as "declared before running".

SET: the 90%-each-way themes found in at least 10 runs (provisional working bar; label it so). Call them accepted themes.

MEASURES, for every accepted theme T of 25 or more pathways:
a. Inner themes of T: accepted themes S smaller than T with at least 90% of S inside T.
b. Single cover: the largest share of T covered by one inner theme.
c. Greedy cover: repeatedly add the inner theme that covers the most still-uncovered pathways of T; record the coverage of T after 1, 2 and 3 picks, and the Jaccard between pick 1 and pick 2.
d. Two-block pattern: T is covered at least 90% by its first two picks AND those two picks have Jaccard below 0.5 with each other. Also report the three-pick version (at least 90% by three picks, every pair of the three below 0.5).

REPORT (add a section to docs/status/2026-10-24-L1-steps1-4.md, or a new note docs/status/2026-10-24-L1-unions.md):
1. By band (25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+): accepted themes; median single cover; median coverage after 1, 2, 3 picks; share with the two-block pattern; share with the three-block pattern.
2. For each of the 7 distinct sets in large7/ (by their file number, set_1 to set_7): its first three picks, each with size, the share of the set it covers, how many of the other six sets it overlaps at J >= 0.5 (none of the six may be a pick of itself), and the coverage after 1, 2, 3 picks; and whether sets 5, 6 and 7 (the three read as broad domains) appear among the picks of sets 1-4, with the share covered.
3. Twenty random accepted themes of 100 or more pathways with the two-block pattern, and twenty without it (seed 20261024), each as "name [source]" member lists with the members of pick 1 and pick 2 marked, in data/experiments/L1_2026-10-24/unions/examples/. Do not judge them.

FINAL
Add the new code, note, outputs and PROMPT_62.md to docs/status/commit-2026-10-24-L1.sh (or a new script commit-2026-10-24-L1-unions.sh to run after it), listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give tables 1 and 2 and the commit script path. Then stop.
