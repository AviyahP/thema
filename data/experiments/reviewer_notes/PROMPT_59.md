Prompt 59: finding cores in the Ward trees (arm K). Declared 23 Oct 2026, before any result. Exploratory: no ontology is built, nothing adopted. Design: Aviyah, 23 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
Prompt 58 showed that cores taken from J >= 0.70 copies cannot work: from 25 pathways up the median cluster is found in 1 run of 200 (its own), so its "core" is the whole cluster. Aviyah's design finds cores directly in the trees: a core K is found in a run if the smallest cluster of that run's tree holding all of K is at least 70% K. A core does not have to appear on its own; it has to keep coming back inside clusters that are mostly the core. This prompt finds such cores, measures their support, and compares what is retained with O50s's stages and with prompt 58's arms CI and CT.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; proceed unless the COMPUTE alone is expected to exceed 2 h; if it is, stop and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_59.md (if not already there), and copy it into DECISIONS.md as "declared before running".

INPUT: frozen O50s (data/ontology/frozen/working-O50s-2026-10-22/): x2 universe, the 200 cached real runs (trees and subsamples). Reuse caches wherever possible. Exact computation throughout (sparse matrix products and exact size windows, as in prompt 58, verified against brute force on a random sample; report the check).

SPEC
1. The test. For a set K and a run r: K is judged in r if at least 3 of K's pathways were drawn in r. Then take the smallest cluster of r's tree holding all of K's drawn pathways (their lowest common ancestor). r FINDS K if K's drawn pathways make up at least 70% of that cluster. Support(K) = runs that find K / runs that judge K.
2. Candidates. Any set found in two runs r1 and r2 lies inside both enclosing clusters, each at least 70% the set. So candidates are the intersections C1 ∩ C2 of clusters (3 or more pathways) from DIFFERENT runs, where the intersection has at least 3 pathways and makes up at least 70% of C1 and at least 70% of C2. Deduplicate identical sets. Report the number of qualifying cluster pairs and of distinct candidates, by size band. If the distinct candidates exceed 5 million, stop after reporting the counts and propose a cheaper order.
3. Score every candidate with the test in all 200 runs: support, runs found, runs judged.
4. Closed cores: drop a candidate if a strictly larger candidate containing it has the same or higher support (it adds nothing). Keep the rest; report how many were dropped by this rule, by band.
5. Members of each core: the core plus every pathway present in at least half of the enclosing clusters of the runs that found it (counted over runs where that pathway was drawn). Report core size as a share of members, by band.
6. How many runs make a core. If scramble trees (seeds 3001-3010, held-out 4001-4006) are cached, run steps 1-5 on them and solve a required support per size band with the gate's own procedure (target 0.008, rule of three where scrambles never pass, caps 0.01 overall and 0.02 per band, check once on held-out). If they are not cached, do NOT build them: report the support distributions only, and use "found in at least 2 runs" as a labelled placeholder. Report the retained cores both at 2 runs and, if solved, at the calibrated floors.
No consensus, no repair, no edges.

REPORT (docs/status/2026-10-23-tree-cores.md). Arm K (at 2 runs, and at the calibrated floors if solved) next to O50s's stages (s2 families before the gate, s3 the 26,120 gated themes, s5 the 5,658 final themes) and prompt 58's CI and CT:
A. Counts: qualifying pairs, candidates, closed cores, retained cores; themes per band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+).
B. Support: median support and runs found, by band; share at or above 0.05, 0.1, 0.33, by band.
C. Near-copies, exactly as prompt 58 section C: non-nested pairs at J >= 0.5 (by band of the larger); nested pairs with the smaller >= 0.85 of the larger; pairs where the smaller has exactly 1 member outside the larger. Computed on the members of the retained themes.
D. What is retained: share of s5 themes with a K counterpart at J >= 0.9 and at J >= 0.7, by band; share of s5 themes that contain a retained core making up at least 70% of the theme; for the 5 O50s giants, the largest retained cores inside each (size, support) and the best K counterpart (J, size).
E. Twenty retained K themes of 25 or more members and twenty of 6-24, drawn at random (seed 20261023), as "name [source]" member lists with the core marked, support shown, in data/experiments/tree_cores_2026-10-23/examples/. Do not judge them.

FINAL
Write docs/status/commit-2026-10-23-tree-cores.sh, to run after commit-2026-10-23-core-merge.sh. It commits the code, status note, data/experiments/tree_cores_2026-10-23/ and PROMPT_59.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give sections A-D as tables and the commit script path.
