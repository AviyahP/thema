Prompt 61: level 1 of the core-recurrence design, steps 1-4 (build L1). Declared 24 Oct 2026, before any result. Exploratory: no gate, no DAG, nothing adopted. Design: Aviyah, 23-24 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
Aviyah's design: every Ward cluster gathers its matching clusters in the other runs; the part they reliably share is its core; groups with the same core merge; members by majority. The match is 70% on EACH side (not Jaccard on the union, which failed in prompt 58 because two clusters each 70% the same core score only ~0.54). Prompts 59-60 showed this kind of match finds real, noise-free cores up to ~50 pathways. Large structure is expected to come later from level 2 (themes as units), not from this step.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; proceed unless the COMPUTE alone is expected to exceed 2 h. Exact computation throughout (sparse products, exact windows), each step verified against a brute-force loop on a random sample (seed 20261024); report every check.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_61.md (if not already there), and copy it into DECISIONS.md as "declared before running".

INPUT: the x2 universe and the 200 cached real trees with their subsamples (frozen O50s), and prompt 60's two scramble sides (seeds 3001, 3002; centred matrix, verified). Nothing cached is overwritten.

SPEC (run on the real side, and identically on each scramble seed)
1. Groups. Seeds = every distinct cluster of 3 or more pathways over the 200 runs (identical sets stored once, with all the runs they occur in). For a seed C and a run r: r can judge C if at least 3 of C's members were drawn in r. Let D be the smallest cluster of r's tree holding at least 70% of C's drawn members (unique, since tree clusters are nested or disjoint). r FINDS C if, in addition, C's members make up at least 70% of D. D is C's copy in r. Support(C) = runs that find C / runs that can judge C, counting C's own runs as O50s counts them (say how).
2. Core of each group: inclusion of a pathway = copies holding it / copies from runs where it was drawn. Core = inclusion >= 0.9. A group whose core has fewer than 3 pathways has no core: count these by band and leave them out.
3. Merge. In O50s's family order (support descending, then the seed's size descending, then key), each unclaimed group becomes a seed and absorbs every unclaimed group whose core has Jaccard >= 0.9 with the SEED's core (compared with the seed only; no chaining).
4. Each theme: copies pooled, one per run (the copy of the theme's highest-support group found in that run); support pooled (runs that found any of its groups / runs able to judge any); inclusions recomputed; core = inclusion >= 0.9; members = inclusion >= 0.5.
No gate, no consensus, no repair, no edges.

REPORT (docs/status/2026-10-24-L1-steps1-4.md), real side, with the scramble sides where asked:
A. Counts: seeds; groups with and without a core (by band); themes after merge; groups per theme (median, max); themes per size band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); median core size as a share of members, by band.
B. Support: by band, median runs found, and themes found in at least 5, 10 and 20 runs. The same for each scramble seed, and the ratio scrambled / real, by band and bar (two seeds: indicative only, label it).
C. Near-copies among the themes, with prompt 58's verified counter, for all themes and for themes found in at least 10 runs: non-nested pairs at J >= 0.5 (by band of the larger), nested pairs with the smaller >= 0.85 of the larger, pairs where the smaller has exactly 1 member outside the larger. Also per theme, next to O50s's gated themes (409,858 pairs / 26,120 = 15.7 per theme) and prompt 60's cores (about 700 per core).
D. Correspondence: share of O50s's final 5,658 themes with an L1 counterpart (found in at least 10 runs) at J >= 0.9 and J >= 0.7, by band; the 10 largest L1 themes found in at least 10 runs (size, runs found).
E. For reading later (do not judge): 20 themes found in at least 10 runs of 6-24 pathways, and 20 of 25 or more, drawn at random (seed 20261024), as "name [source]" member lists with the core marked and runs found, in data/experiments/L1_2026-10-24/examples/.

FINAL
Write docs/status/commit-2026-10-24-L1.sh, to run after commit-2026-10-23-tree-cores.sh. It commits the code, status note, data/experiments/L1_2026-10-24/ and PROMPT_61.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give tables A-D and the commit script path. Then stop.
