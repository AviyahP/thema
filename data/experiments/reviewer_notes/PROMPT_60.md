Prompt 60: tree cores at 70%, what each recurrence bar keeps (5, 10, 20 runs). Declared 23 Oct 2026, before any result. Exploratory: nothing is built beyond the cores, nothing adopted. Design: Aviyah, 23 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
The new pipeline rebuilds themes from scratch with the tree-core definition (prompt 59, cover 0.70): a run finds a core K if K's drawn pathways make up at least 70% of the smallest cluster holding them. Steps 1-2 of the pipeline are: find the cores (done in prompt 59, steps 2-3), and keep the cores that recur. Aviyah wants to see what bars of 5, 10 and 20 runs (of 200) keep before choosing one. Nothing after step 2 is run.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; proceed unless the COMPUTE alone is expected to exceed 2 h.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_60.md (if not already there), and copy it into DECISIONS.md as "declared before running".

INPUT: prompt 59's cover-0.70 candidates and scores (data/experiments/tree_cores_2026-10-23/candidates.npz, scored.npz), unchanged. Do not recompute them.

1. Retained cores at each bar: found in at least 5, at least 10, at least 20 runs. For each bar:
   a. retained cores, by size band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599);
   b. the largest retained core sizes (top 10);
   c. pathways covered: how many of the 5,539 are in at least one retained core;
   d. redundancy among the retained cores, with prompt 58's verified exact counter (sparse products, exact size windows, brute-force check on a 2,000 sample, seed 20261023): non-nested pairs at J >= 0.5 (by band of the larger), nested pairs with the smaller >= 0.85 of the larger, pairs where the smaller has exactly 1 member outside the larger.

2. Noise check (indicative, NOT a calibration): build Ward trees for scramble seeds 3001 and 3002 only (200 trees each, x2 universe, the same subsamples and scramble procedure O50s uses: each embedding dimension shuffled independently across pathways, rows rescaled to length 1), in a new directory; never overwrite anything cached. Run prompt 59 steps 2-3 at cover 0.70 on each. Report, by band and for each bar (5, 10, 20): scrambled candidates retained (per seed and the mean), and the ratio scrambled / real retained. Label it clearly as two seeds, indicative only.

3. For reading later (do not judge): from the real retained cores, 20 drawn at random (seed 20261023) from each of these groups: found in 5-9 runs (kept by 5, dropped by 10); 10-19 runs (kept by 10, dropped by 20); 20 or more runs. Only cores of 6 or more pathways. Each as a "name [source]" member list with its runs-found count, in data/experiments/tree_cores_2026-10-23/bars/examples/.

REPORT: add a section "Recurrence bars" to docs/status/2026-10-23-tree-cores.md, with tables for 1a-1d at each bar side by side, and 2.

FINAL
Write docs/status/commit-2026-10-23-tree-cores.sh, to run after commit-2026-10-23-core-merge.sh. It commits the code, the status note, data/experiments/tree_cores_2026-10-23/ (including bars/), PROMPT_59.md and PROMPT_60.md, listing files explicitly. Leave out any file over 50 MB and say which (cover50/candidates.npz, 122 MB, regenerable, must be left out; also the scramble trees). Never include any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give the tables for 1a-1d and 2 and the commit script path. Then stop.
