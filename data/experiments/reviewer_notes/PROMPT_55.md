Prompt 55: full judgement of S2 against O50s. Declared 22 Oct 2026, before any result. Evaluation only: no build changes, nothing adopted. Design approved by Aviyah, 22 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
S2 (prompt 54) has O50s's shape (270 roots against 261, depth 6, the same 5 giants) but only 55-63% of its 25-199 themes match O50s at J >= 0.9. Aviyah asks whether S2 is equivalent, better or worse. The judgement combines the computed measures not yet run for S2 with blind readings by the reviewer, focused on where the two builds differ.

JUDGEMENT RULE (declared now; applied by the reviewer after all results)
- Equivalent: every reading rate within 5 points of O50s, and every computed score within 0.02 (or within its CI where one exists).
- Better or worse: a reading difference above 5 points, or a computed score beyond 0.02 with its CI excluding zero, in a consistent direction.
- Mixed: better on some and worse on others; reported as such for Aviyah to decide.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file after writing it; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first; if under 5 h, proceed without waiting; if over, do PART 1 and the cheapest of PART 2 and stop.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_55.md (if not already there), and copy it into DECISIONS.md as "declared before running".

Builds: frozen O50s (data/ontology/frozen/working-O50s-2026-10-22/) and S2 (data/ontology/v0.4-leaves/thema_L_x2_S2/).

PART 1, FIRST: inputs for the reviewer (do not judge anything yourself), in data/experiments/S2_vs_O50s_2026-10-22/
- R (roots that differ): every S2 root with no O50s ROOT at J >= 0.9, and every O50s root with no S2 ROOT at J >= 0.9, pooled and shuffled (seed 20261022), random ids, no build label. Full member lists as "name [source]" sorted by name, giants in full; batches of about 2,600 lines in read_roots/, a root never split. Report both counts.
- T (middle themes that differ): themes unique to each build (best J below 0.9 to ANY theme of the other build), in the bands 12-24, 25-49, 50-99, 100-199; 40 per band per build drawn at random (seed 20261022), all if fewer (say so); pooled and shuffled, random ids, no build label; batches in read_themes/.
- I (intruder test): for the same T themes, inputs exactly as the C6 intruder test was prepared before; batches in intruder/.
- S (small-root test): for every S2 root of 50 or fewer pathways, as in PREREG_O50s_roots.md (the root's full list and its 3 largest-share larger S2 containers as P, Q, R in random order, each with its size and up to 40 members not in the root); shares and missing counts only in the KEY; batches in small_inputs/.
- KEY_DO_NOT_SHARE_S2_vs_O50s.json mapping every id to build, node, size, band and, for S, the shares.
Write a short note listing the counts and batch paths as soon as PART 1 is done, then continue.

PART 2: computed measures, S2 and O50s side by side, same code, existing scripts where they exist (say which, and how anything new was computed):
C. Duplication: non-nested pairs at J >= 0.5 by band (and how many are non-siblings); nodes at least 80% inside another node without being its descendant, by pathways missing (0, 1-5, 6-20, 21+).
E. Curated recall per band for Reactome and GO (J > 0.5), with CIs; sibling specificity AUROC with CIs; and repeat for S2 the counterpart, placement and Reactome rows already reported in prompt 54.
F. Stability: half-builds from runs 1-100 and 101-200, each through its own build's steps (O50s's and S2's), final-theme match, worse direction, J >= 0.70.
G. Gene coherence per band against size-matched random sets (evaluation only).

REPORT: docs/status/2026-10-22-S2-vs-O50s-judgement.md with PART 1's counts and paths and PART 2's tables, S2 next to O50s, differences with CIs where available. Do not apply the judgement rule; the reviewer does.

FINAL
Write docs/status/commit-2026-10-22-S2-judgement.sh, to run after commit-2026-10-22-S2.sh. It commits the code, status note, experiment folder (without the KEY file), PROMPT_55.md and scripts/s1_checks.py (carried forward), listing files explicitly, leaving out any file over 50 MB (and saying which). No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After PART 1, give the counts and batch paths. After PART 2, give the tables and the commit script path.
