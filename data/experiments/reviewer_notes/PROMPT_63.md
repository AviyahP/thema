Prompt 63: the DAG of L1's recurring themes (strict containment). Declared 24 Oct 2026, before any result. Exploratory: nothing adopted. Design: Aviyah, 24 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
L1 (90%-each-way merge) gives recurring themes but no hierarchy yet. Prompt 62 showed the four giant sets contain the three broad domains (set_3 holds all of set_6; set_4 holds set_5 and set_7). Build the DAG and look at the top before deciding anything.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file after writing it; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; proceed unless the COMPUTE alone is expected to exceed 2 h. Exact computation, verified against brute force on a random sample (seed 20261024); report each check.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_63.md (if not already there), and copy it into DECISIONS.md as "declared before running".

SET: the 90%-each-way L1 themes (data/experiments/L1_2026-10-24/real_bothways/) found in at least 10 runs (provisional bar; label it so). Members = inclusion >= 0.5.

DAG: A is a parent of B if every member of B is in A and A is larger; keep immediate parents only (transitive reduction). No inheritance, no chain collapse, no merging: memberships are not changed.

REPORT (docs/status/2026-10-24-L1-dag.md)
A. Shape: themes; edges; roots, and roots by band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); the same root counts if themes of 3-5 are left out; multi-parent share; children per node (max, median); levels to a root (median, max); themes with no parent and no child.
B. The top: every root of 200 or more pathways, with size, number of children, and its largest three children (size, share of the root); for the seven large7 sets (matched at J >= 0.9 to an L1 theme, say which, or none), whether each is a root, and its parents.
C. What a tolerance would change (report only, apply nothing): pairs where B is at least 90% inside a larger A but not 100% (by pathways missing: 1, 2-5, 6+); how many roots would gain a parent if such pairs counted as edges, by band; how many edges are near-chains (child holding at least 85% of its parent).
D. Placement: pathways in at least one theme; pathways in no theme; mean themes per pathway; for each pathway, the size of the largest theme holding it (median).

FOR THE REVIEWER (do not judge): every root of 50 or more pathways, shuffled (seed 20261024), with random ids, as "name [source]" member lists sorted by name, in batches of about 2,600 lines, in data/experiments/L1_2026-10-24/dag/read_roots/; the id-to-theme mapping (with size and runs found) only in KEY_DO_NOT_SHARE_L1_roots.json in the same folder.

FINAL
Write docs/status/commit-2026-10-24-L1-dag.sh, to run after commit-2026-10-24-L1-unions.sh. It commits the code, note, data/experiments/L1_2026-10-24/dag/ (without the KEY file) and PROMPT_63.md, listing files explicitly, leaving out any file over 50 MB (and saying which). No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give sections A-D as tables, the reading batch paths, and the commit script path. Then stop.
