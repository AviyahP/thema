Prompt 31: catch up on the reviewer's work, freeze c85, then test one in-build overlap rule on a branch. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave commit scripts; do not touch data/ontology/frozen/baseline-2026-10-09/; never open any KEY_DO_NOT_SHARE* file; one heavy job at a time; times in UTC+1.

PRECONDITION
0. Check that commit-2026-10-09-chain-c85.sh, commit-2026-10-10-names-embed.sh and commit-2026-10-11-naming-c1.sh have been run (their last commit messages are in git log). If not, stop and say which.

PART A, on main: record and freeze
1. Read data/experiments/reviewer_notes/HANDOFF_2026-10-12.md in full; it is what happened 10-12 Oct while you were idle. Add one DECISIONS entry summarising its sections 0-8, keeping the tables in sections 2 and 5. In CLAUDE.md:
   - c85 is the working version;
   - the sibling merge rule is superseded and must not be run;
   - the paid naming run is held until the overlap arm is decided;
   - add a pointer to the handoff.
2. Carry out Parts A and B of data/experiments/reviewer_notes/PROMPT_28_original.md:
   - record the corrected c85 assessment;
   - freeze data/ontology/frozen/working-c85-2026-10-10/ with its checksum test;
   - tag thema-c85-2026-10-10.
   Skip Part C; it is obsolete.
3. Write docs/status/commit-2026-10-12-handoff.sh, to run on main. It commits:
   - the reviewer files listed in handoff section 9;
   - the freeze and the tag;
   - CLAUDE.md and DECISIONS.md.
   Check with git check-ignore that no key file can be staged.

PART B, on a new branch overlap-2026-10: the overlap arm
4. Before building, copy data/experiments/reviewer_notes/SPEC_overlap_arm_2026-10-12.md verbatim into a DECISIONS entry titled "declared before running".
5. Implement the spec:
   - split the recurrence threshold (theta_match) from the same-theme cutoff;
   - pass one same-theme cutoff to both consensus and the stale-merge pass;
   - add a joint fixed-point loop of chain collapse and stale merge;
   - add CLI flags, recorded in the manifest, with every default unchanged;
   - add tests.
6. Harness proof: same-theme 0.70 without the joint loop must reproduce thema_L_x2_c85 byte-identically, and the frozen baseline test must pass. If either fails, stop.
7. Build these, one at a time:
   - O70, O50 and O60 on the x2 universe: thema_L_x2_O70, thema_L_x2_O50, thema_L_x2_O60;
   - O50 on the repair universe: thema_L_repair_O50.
8. Report criteria C1-C3 and every report-only item in the spec, against c85, in docs/status/2026-10-12-overlap-arm.md. Do not judge C4 or C5; the reviewer does. For C4, write O50_new_themes.json: every O50 theme not identical to a c85 theme, with its full members. Add a DECISIONS result entry. Adopt nothing.
9. Write docs/status/commit-2026-10-12-overlap-arm.sh. It must:
   - check that the handoff script has run;
   - git switch -c overlap-2026-10;
   - commit only Part B files;
   - push the branch;
   - switch back to main.
   It must never merge.

END OF PROMPT. Confirm 0, A1-A3 and B4-B9. Give:
- the frozen folder size and the tag;
- the harness-proof result;
- theme counts for c85, O70, O50 and O60;
- C1-C3;
- the multi-parent shares;
- both commit script paths.
