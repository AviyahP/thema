#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git add .gitignore
git diff --cached --quiet || git commit -m "Ignore every answer key by name, not only the tsv one"

git add src/thema/naming_c1.py tests/test_naming_c1.py src/thema/llm.py
git diff --cached --quiet || git commit -m "naming-c1 as code, proved against the reviewer pilot item for item"

git add scripts/name_themes_c1.py
git diff --cached --quiet || git commit -m "Runner for naming-c1: gated on submit, logs every call, records the prompts"

git add \
  data/experiments/naming_pilot_2026-10-11/code/np_build.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c1b_build.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c1b_eval.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c1b_score.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c1b_sel.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c2_build.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c2_eval.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c2_score.py \
  data/experiments/naming_pilot_2026-10-11/code/np_c2_sel.py \
  data/experiments/naming_pilot_2026-10-11/code/np_dedupsel.py \
  data/experiments/naming_pilot_2026-10-11/code/np_dup.py \
  data/experiments/naming_pilot_2026-10-11/code/np_eval_build.py \
  data/experiments/naming_pilot_2026-10-11/code/np_score.py \
  data/experiments/naming_pilot_2026-10-11/code/np_sel.py \
  data/experiments/naming_pilot_2026-10-11/code/np_select.py \
  data/experiments/naming_pilot_2026-10-11/spec/ALGORITHM.md \
  data/experiments/naming_pilot_2026-10-11/spec/E2_fit.md \
  data/experiments/naming_pilot_2026-10-11/spec/E3_equivalence.md \
  data/experiments/naming_pilot_2026-10-11/spec/N1_namer.md \
  data/experiments/naming_pilot_2026-10-11/spec/N2_namer.md \
  data/experiments/naming_pilot_2026-10-11/spec/S1_backmatch.md \
  data/experiments/reviewer_eval_x2_2026-10-09/tf_common.py
git diff --cached --quiet || git commit -m "The naming pilot specification, prompt templates and the reviewer code"

git add \
  data/experiments/naming_pilot_2026-10-11/PREREG_c1b.md \
  data/experiments/naming_pilot_2026-10-11/PREREG_c2.md \
  data/experiments/naming_pilot_2026-10-11/PREREG.md \
  data/experiments/naming_pilot_2026-10-11/PROMPT_ccode_naming_c1.md \
  data/experiments/naming_pilot_2026-10-11/REPORT_naming_pilot.md \
  data/experiments/naming_pilot_2026-10-11/SIDE_BY_SIDE.md
git diff --cached --quiet || git commit -m "Naming pilot pre-registrations and results: 91.5 percent back-matching, P4 failed"

git add \
  data/experiments/naming_pilot_2026-10-11/inputs/confusables_after_dedup.json \
  data/experiments/naming_pilot_2026-10-11/inputs/dedup_slot0.json \
  data/experiments/naming_pilot_2026-10-11/inputs/dedup_slot1.json \
  data/experiments/naming_pilot_2026-10-11/inputs/dedup_slot2.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b01.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b02.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b03.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b04.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b05.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b06.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b07.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot0_b08.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b01.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b02.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b03.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b04.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b05.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b06.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b07.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot1_b08.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b01.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b02.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b03.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b04.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b05.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b06.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b07.json \
  data/experiments/naming_pilot_2026-10-11/inputs/namer_slot2_b08.json \
  data/experiments/naming_pilot_2026-10-11/inputs/repro_subset.json \
  data/experiments/naming_pilot_2026-10-11/inputs/rerun_slot0_b01.json \
  data/experiments/naming_pilot_2026-10-11/inputs/rerun_slot0_b02.json \
  data/experiments/naming_pilot_2026-10-11/inputs/rerun_slot1_b01.json \
  data/experiments/naming_pilot_2026-10-11/inputs/rerun_slot1_b02.json \
  data/experiments/naming_pilot_2026-10-11/inputs/rerun_slot2_b01.json \
  data/experiments/naming_pilot_2026-10-11/inputs/rerun_slot2_b02.json \
  data/experiments/naming_pilot_2026-10-11/inputs/sample_and_confusables.json \
  data/experiments/naming_pilot_2026-10-11/raw/dedup_slot0.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/dedup_slot1.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/dedup_slot2.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b01.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b02.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b03.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b04.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b05.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b06.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b07.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot0_b08.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b01.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b02.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b03.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b04.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b05.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b06.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b07.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot1_b08.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b01.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b02.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b03.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b04.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b05.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b06.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b07.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/namer_slot2_b08.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/rerun_slot0_b01.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/rerun_slot0_b02.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/rerun_slot1_b01.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/rerun_slot1_b02.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/rerun_slot2_b01.out.json \
  data/experiments/naming_pilot_2026-10-11/raw/rerun_slot2_b02.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/dedup_sel_01.json \
  data/experiments/naming_pilot_2026-10-11/selection/dedup_sel_01.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/final_names.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_01.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_01.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_02.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_02.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_03.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_03.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_04.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_04.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_05.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_05.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_06.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_06.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_07.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_07.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_08.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_08.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_09.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_09.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_10.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_10.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_11.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_11.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_12.json \
  data/experiments/naming_pilot_2026-10-11/selection/main_sel_12.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_01.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_01.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_02.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_02.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_03.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_03.out.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_04.json \
  data/experiments/naming_pilot_2026-10-11/selection/rerun_sel_04.out.json
git diff --cached --quiet || git commit -m "Pilot inputs, raw model replies and selections: the material the port is proved against"

git add \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_01.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_02.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_03.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_03.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_04.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_04.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_05.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_05.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_06.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E1_06.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_01.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_02.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_03.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_03.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_04.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E2_04.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E3_01.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E3_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E3_02.json \
  data/experiments/naming_pilot_2026-10-11/c1b/eval/E3_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/final_names_c1b.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bM_seed3_b1.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bM_seed3_b2.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bM_seed4_b1.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bM_seed4_b2.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bR_seed13_b1.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bR_seed13_b2.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bR_seed14_b1.json \
  data/experiments/naming_pilot_2026-10-11/c1b/inputs/c1bR_seed14_b2.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bM_seed3_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bM_seed3_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bM_seed4_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bM_seed4_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bR_seed13_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bR_seed13_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bR_seed14_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/raw/c1bR_seed14_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_01.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_02.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_03.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_03.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_04.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_04.out.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_05.json \
  data/experiments/naming_pilot_2026-10-11/c1b/selection/sel_05.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E1_01.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E1_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E1_02.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E1_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E1_03.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E1_03.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E2_01.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E2_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E2_02.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E2_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E3_01.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E3_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E3_02.json \
  data/experiments/naming_pilot_2026-10-11/c2/eval/E3_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/final_names_c2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot0_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot0_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot1_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot1_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot2_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot2_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot3_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot3_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot4_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2A_slot4_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot0_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot0_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot1_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot1_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot2_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot2_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot3_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot3_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot4_b1.json \
  data/experiments/naming_pilot_2026-10-11/c2/inputs/c2B_slot4_b2.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot0_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot0_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot1_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot1_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot2_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot2_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot3_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot3_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot4_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2A_slot4_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot0_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot0_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot1_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot1_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot2_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot2_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot3_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot3_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot4_b1.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/raw/c2B_slot4_b2.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_01.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_02.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_03.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_03.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_04.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_04.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_05.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_05.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_06.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/A_sel_06.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_01.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_01.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_02.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_02.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_03.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_03.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_04.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_04.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_05.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_05.out.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_06.json \
  data/experiments/naming_pilot_2026-10-11/c2/selection/B_sel_06.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_01.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_01.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_02.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_02.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_03.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_03.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_04.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_04.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_05.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_05.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_06.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_06.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_07.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_07.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_08.json \
  data/experiments/naming_pilot_2026-10-11/eval/E1_08.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_01.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_01.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_02.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_02.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_03.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_03.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_04.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_04.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_05.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_05.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_06.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_06.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_07.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_07.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_08.json \
  data/experiments/naming_pilot_2026-10-11/eval/E2_08.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E3_01.json \
  data/experiments/naming_pilot_2026-10-11/eval/E3_01.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/E3_02.json \
  data/experiments/naming_pilot_2026-10-11/eval/E3_02.out.json \
  data/experiments/naming_pilot_2026-10-11/eval/scored_rows.json
git diff --cached --quiet || git commit -m "Pilot evaluation, and the rejected c1b and c2 variants"

git add data/experiments/naming_pilot_2026-10-11/api_run/example_request.json
git diff --cached --quiet || git commit -m "The exact text a naming-c1 run would send, for review before any spend"

git add CLAUDE.md DECISIONS.md docs/status/commit-2026-10-11-naming-c1.sh
git diff --cached --quiet || git commit -m "naming-c1 reproduces the pilot; the 100-theme run is priced at 9.83 and not approved"

git push
