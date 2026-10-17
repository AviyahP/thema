Prompt 40: where do the large first-pass candidates go? A diagnostic, declared 16 Oct 2026. It is read-only and adopts nothing. (Prompt 39, the weighting test, is withdrawn: do not run it.) This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; times in UTC+1. Stop if the estimate is over 2 h.

WHY
The 8 Oct re-gate report (L_cal8, after collapse) has only 22 themes of 101-300 pathways and 6 of 301-1,000, and O50 has 5 of 201-500 and 2 of 501-1,000. Yet the 10+ floor is only 0.025, so large candidates should pass the gate. M5_cal8 (match 0.5 at all sizes) kept about 3x more of them.

Question 1: at which step are large candidates lost?
Question 2: are the lost candidates the same groups that the areas pass (rec2fix, equal weight) later rebuilds?

STEPS
1. **Rebuild the O50 pipeline instrumented, not changed.** Use the cached trees if they exist; otherwise rerun exactly. Confirm that the final output is byte-identical to the frozen O50.
2. **Track every candidate of 51 pathways or more** through each step:
   - gate (support ≥ floor);
   - families / absorption (twin rule);
   - consensus;
   - stale pass;
   - chain collapse (0.85);
   - final.
   For each candidate removed, record the step and the node that removed or absorbed it: its id, its size, and the Jaccard between the two.
3. **Report the counts surviving each step, by size band:** 51-100, 101-200, 201-500, 501-1,000, 1,001+.
   - For bands 201-500 and 501-1,000, list the 20 most-supported removed candidates. For each: size, support, the step that removed it, and what removed it.
4. **Compare with the areas pass.** Take the removed candidates of 201-1,000 that passed the gate, collapsed to distinct groups (J ≥ 0.9 counts as one).
   - For each, give its best-match J to any rec2fix area (data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/area_members.tsv) and to any O50 node. Report the distribution: ≥0.7, 0.5-0.7, <0.5.
   - In reverse, for each rec2fix area of 201-1,000, give its best J to any gated first-pass candidate, and to any removed one.

OUTPUT
- data/experiments/consensus_fate_2026-10-16/: the code, the tables, and fate.tsv with one row per tracked candidate.
- docs/status/2026-10-16-consensus-fate.md.
- docs/status/commit-2026-10-16-consensus-fate.sh, to run after commit-2026-10-16-areas-rec3.sh. It commits:
  - the folder and the note;
  - data/experiments/reviewer_notes/PROMPT_40.md;
  - data/experiments/reviewer_notes/REVIEWER_LOG_2026-10-12_to_16.md, if no earlier script commits it.
  No branch operations; no push of main.

END OF PROMPT. Before running, confirm in one line whether the cached trees exist, and give the time estimate. After the run, give:
- the survival table by step and band;
- the overlap distributions from step 4;
- the commit script path.
