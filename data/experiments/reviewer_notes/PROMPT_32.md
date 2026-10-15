Prompt 32: adopt and freeze O50, merge it, and prepare offline naming-c1 for the reviewer. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave commit scripts; do not touch the existing frozen folders; never open any KEY_DO_NOT_SHARE* file; one heavy job at a time; times in UTC+1. Do not touch the stale main branch; the working branch is leaves-2026-10.

PRECONDITION
0. Check that commit-2026-10-12-handoff.sh and commit-2026-10-12-overlap-arm.sh have run (their commit messages are in git log and branch overlap-2026-10 exists). If not, stop and say which.

PART A: finalise O50
1. Read data/experiments/o50_eval_2026-10-13/REPORT.md (the reviewer's C4 and C5). Add DECISIONS entries:
   - C4 PASS (112 not-ok vs 195; 97.57% vs 97.64% ok); C5 O50 WINS (87 vs 33, p = 9e-7).
   - C2: Aviyah accepted btm:M205 as a known exception on 13 Oct.
   - DECISION (Aviyah, 14 Oct): thema_L_x2_O50 is the WORKING VERSION. c85 and the 2026-10-09 baseline stay frozen as fallbacks.
2. Freeze O50 at data/ontology/frozen/working-O50-2026-10-14/, exactly as the c85 freeze was done:
   - build files, manifest and inputs;
   - all_verdicts_O50.json: the carried c85 verdicts for the 3,744 identical themes, plus the reviewer's 858 judgements (data/experiments/o50_eval_2026-10-13/judged/C4_*.out.json);
   - the reviewer's REPORT.md;
   - FROZEN.md, CHECKSUMS.sha256, and checksum-test coverage.
   Update CLAUDE.md.
3. Write docs/status/commit-2026-10-14-adopt-O50.sh. It must:
   - on overlap-2026-10, commit the freeze, DECISIONS, CLAUDE.md, and the reviewer folders data/experiments/o50_eval_2026-10-13/ and data/experiments/hidef_eval_2026-10-13/, plus reviewer_eval_x2_2026-10-09/o50_facets.py and o50_facets_output.txt;
   - switch to leaves-2026-10 and merge overlap-2026-10 with --no-ff;
   - tag thema-O50-2026-10-14;
   - push the branch and the tag.
   Check with git check-ignore that no key file can be staged.

PART B: naming-c1 offline mode, the reviewer answers and the code decides
4. Add an offline mode to scripts/name_themes_c1.py, using the existing functions in src/thema/naming_c1.py unchanged. In offline mode no client is built and no API key is read. Defaults stay unchanged. The stages write to a folder you name (default data/experiments/naming_O50_2026-10-14/code_run/), never into the reviewer's folders:
   - `--offline n1`: for every O50 theme with 3-200 members, write the N1 namer items for 3 candidate slots. Use the pilot's format and seeds, theme order random.Random(7) over the sorted theme ids, 25 themes per file per slot.
   - `--offline s1`: read the reviewer's raw namer outputs. Validate that every item is answered exactly once with a valid schema, and list failures. Write the S1 back-match items, with keys in KEY_DO_NOT_SHARE_* files.
   - `--offline select`: read the S1 judgements, apply select(), find duplicates, and write the uniqueness (dedup) items.
   - `--offline final`: read the dedup judgements, apply apply_uniqueness(), and write final_names.tsv (node, name, n_correct, n_nameable, low_confidence, unnameable) plus a summary.
5. Equivalence proof on the 11 Oct pilot's raw outputs: the four stages must reproduce the pilot's files and final_names.json exactly. Add a test. If it fails, stop.
6. Equivalence on O50. The reviewer has already built the O50 namer inputs with the pilot scripts (data/experiments/naming_O50_2026-10-14/inputs/, made by code/nm_build.py) and is running the namers and judges.
   - Run `--offline n1` and diff your files against the reviewer's inputs: they must be byte-identical.
   - Run `--offline s1` on the reviewer's 552 raw outputs (all present and validated). Report the item and file counts. The reviewer ran S1 only on a 200-theme sample (sample/, built from rendered titles); it is not a reproduction target, so do not diff against it.
   - Do not run select or final: Aviyah chose, for now, names without a full back-match (select_lite/, "naming-c1-lite").
   - Stop there.
7. Write docs/status/commit-2026-10-14-naming-offline.sh, to run on leaves-2026-10 AFTER the adopt script. It commits:
   - the code and the test;
   - the reviewer's naming_O50_2026-10-14 folder (except KEY files);
   - a status note.
   The reviewer's files are in the folder (N1_SUMMARY.md, RUN_LOG.md, candidates_all.tsv, raw/, raw_rejected/, sample/ except KEY files, select_lite/). Check with git check-ignore that none of them is ignored and no KEY file can be staged.

Note for the record: the reviewer ran all namers as in-session subagents (no API spend; 552 files, all validated; see N1_SUMMARY.md). S1 was run only on a 200-theme sample (sample/REPORT_S1_sample.md: E1 96.5%, E2 0.924). The names in select_lite/ are the lite selection; a full back-match can be run later from the same raw outputs. Never write into the reviewer's files: inputs/, raw/, raw_rejected/, sample/, select_lite/.

END OF PROMPT. Confirm 0, A1-A3 and B4-B7. Give:
- the frozen folder size and the tag;
- the equivalence-proof result;
- the O50 n1 diff result, and the n1 and s1 item and file counts;
- both commit script paths.
