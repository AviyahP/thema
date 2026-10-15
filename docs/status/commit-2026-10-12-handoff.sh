#!/bin/zsh
set -euo pipefail
cd ~/code/thema

TAG=thema-c85-2026-10-10
BRANCH=$(git rev-parse --abbrev-ref HEAD)

git cat-file -e HEAD:data/ontology/v0.4-leaves/thema_L_x2_c85/nodes.tsv

git add \
  data/experiments/reviewer_eval_x2_2026-10-09/c85_unjudged.json \
  data/experiments/reviewer_eval_x2_2026-10-09/dirfeat.py \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/blind_chunk1.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/blind_chunk2.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/blind_chunk3.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/blind_chunk4.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/blind_chunk5.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/blind_chunk6.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/judged_chunk1.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/judged_chunk2.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/judged_chunk3.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/judged_chunk4.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/judged_chunk5.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facet_strength/judged_chunk6.json \
  data/experiments/reviewer_eval_x2_2026-10-09/facets_real_output.txt \
  data/experiments/reviewer_eval_x2_2026-10-09/facets_real.py \
  data/experiments/reviewer_eval_x2_2026-10-09/fam2.py \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_01.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_02.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_03.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_04.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_05.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_06.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_07.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_08.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_09.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_10.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_11.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_12.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_13.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_14.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/blind_15.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_01.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_02.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_03.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_04.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_05.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_06.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_07.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_08.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_09.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_10.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_11.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_12.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_13.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_14.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/judged_15.json \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/PREREG_fulllists.md \
  data/experiments/reviewer_eval_x2_2026-10-09/fulllists_test/rubric_fulllists.md \
  data/experiments/reviewer_eval_x2_2026-10-09/judged_c85_316.json \
  data/experiments/reviewer_eval_x2_2026-10-09/judged_sibling_pairs_all.json \
  data/experiments/reviewer_eval_x2_2026-10-09/judged_twin_pairs.json \
  data/experiments/reviewer_eval_x2_2026-10-09/merge_J05_output.txt \
  data/experiments/reviewer_eval_x2_2026-10-09/mrg.py \
  data/experiments/reviewer_eval_x2_2026-10-09/mrg5.py \
  data/experiments/reviewer_eval_x2_2026-10-09/mrg5b.py \
  data/experiments/reviewer_eval_x2_2026-10-09/mrg5c.py \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_01.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_02.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_03.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_04.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_05.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_06.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_07.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_08.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_09.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_10.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_11.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_12.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_13.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_14.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/blind_15.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_01.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_02.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_03.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_04.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_05.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_06.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_07.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_08.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_09.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_10.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_11.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_12.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_13.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_14.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/judged_15.json \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/REPORT_names_test.md \
  data/experiments/reviewer_eval_x2_2026-10-09/names_test/rubric_nameblind.md \
  data/experiments/reviewer_eval_x2_2026-10-09/privanc.py \
  data/experiments/reviewer_eval_x2_2026-10-09/privanc2.py \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_c85_reassessment.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_facets_real.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_merge_J05.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_merge_rule.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_siblings.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_twin_facet_search.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_twin_rules.md \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_twins.md \
  data/experiments/reviewer_eval_x2_2026-10-09/sibling_pairs_all.json \
  data/experiments/reviewer_eval_x2_2026-10-09/tf_eval.py \
  data/experiments/reviewer_eval_x2_2026-10-09/tf_runs.py \
  data/experiments/reviewer_eval_x2_2026-10-09/tf_static.py \
  data/experiments/reviewer_eval_x2_2026-10-09/twin_facet_features_runs.json \
  data/experiments/reviewer_eval_x2_2026-10-09/twin_facet_features_static.json \
  data/experiments/reviewer_eval_x2_2026-10-09/twin_facet_hypotheses_PREREG.md \
  data/experiments/reviewer_eval_x2_2026-10-09/twin_groups.json \
  data/experiments/reviewer_eval_x2_2026-10-09/twin_pairs_sample.json
git diff --cached --quiet || git commit -m "Reviewer twin and facet work 10-12 Oct: the merge rule precision falls to 63 percent"

git add \
  data/experiments/core_reading_lowoverlap_2026-10-11/code/lo_build.py \
  data/experiments/core_reading_lowoverlap_2026-10-11/code/lo_cmp.py \
  data/experiments/core_reading_lowoverlap_2026-10-11/code/lo_count.py \
  data/experiments/core_reading_lowoverlap_2026-10-11/code/lo_score.py \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_01.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_01.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_02.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_02.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_03.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_03.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_04.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_04.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_05.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_05.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_06.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_06.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_07.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_07.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_08.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/compare/C_08.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set1_1.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set1_2.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set1_3.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set1_4.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set1_5.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set2_1.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set2_2.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set2_3.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set2_4.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set2_5.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set3_1.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set3_2.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set3_3.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set3_4.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/inputs/R_set3_5.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/PREREG.md \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set1_1.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set1_2.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set1_3.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set1_4.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set1_5.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set2_1.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set2_2.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set2_3.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set2_4.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set2_5.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set3_1.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set3_2.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set3_3.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set3_4.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/raw/R_set3_5.out.json \
  data/experiments/core_reading_lowoverlap_2026-10-11/REPORT.md \
  data/experiments/core_reading_pilot_2026-10-11/code/cr_build.py \
  data/experiments/core_reading_pilot_2026-10-11/code/cr_cmp.py \
  data/experiments/core_reading_pilot_2026-10-11/code/cr_score.py \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_01.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_01.out.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_02.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_02.out.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_03.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_03.out.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_04.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_04.out.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_05.json \
  data/experiments/core_reading_pilot_2026-10-11/compare/C1_05.out.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s1_01.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s1_02.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s1_03.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s1_04.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s1_05.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s1_06.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s2_01.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s2_02.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s2_03.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s2_04.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s2_05.json \
  data/experiments/core_reading_pilot_2026-10-11/inputs/R1_s2_06.json \
  data/experiments/core_reading_pilot_2026-10-11/PREREG.md \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s1_01.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s1_02.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s1_03.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s1_04.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s1_05.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s1_06.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s2_01.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s2_02.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s2_03.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s2_04.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s2_05.out.json \
  data/experiments/core_reading_pilot_2026-10-11/raw/R1_s2_06.out.json \
  data/experiments/core_reading_pilot_2026-10-11/REPORT_core_reading.md \
  data/experiments/core_reading_pilot_2026-10-11/spec/C1_compare.md \
  data/experiments/core_reading_pilot_2026-10-11/spec/R1_reader.md \
  data/experiments/whole_reading_2026-10-11/code/wr_build.py \
  data/experiments/whole_reading_2026-10-11/code/wr_cmp.py \
  data/experiments/whole_reading_2026-10-11/code/wr_score.py \
  data/experiments/whole_reading_2026-10-11/compare/W2_01.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_01.out.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_02.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_02.out.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_03.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_03.out.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_04.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_04.out.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_05.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_05.out.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_06.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_06.out.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_07.json \
  data/experiments/whole_reading_2026-10-11/compare/W2_07.out.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_01.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_02.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_03.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_04.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_05.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_06.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_07.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set1_08.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_01.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_02.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_03.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_04.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_05.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_06.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_07.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set2_08.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set3_01.json \
  data/experiments/whole_reading_2026-10-11/inputs/W_set3_02.json \
  data/experiments/whole_reading_2026-10-11/PREREG.md \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_01.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_02.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_03.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_04.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_05.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_06.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_07.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set1_08.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_01.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_02.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_03.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_04.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_05.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_06.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_07.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set2_08.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set3_01.out.json \
  data/experiments/whole_reading_2026-10-11/raw/W_set3_02.out.json \
  data/experiments/whole_reading_2026-10-11/REPORT.md \
  data/experiments/whole_reading_2026-10-11/score_output.txt \
  data/experiments/whole_reading_2026-10-11/spec/W1_reader.md \
  data/experiments/whole_reading_2026-10-11/spec/W2_compare.md
git diff --cached --quiet || git commit -m "Core-reading tests: high-overlap siblings tell the same story about what they share"

git add \
  data/experiments/homefit_2026-10-12/code/hf_build.py \
  data/experiments/homefit_2026-10-12/code/hf_decoy.py \
  data/experiments/homefit_2026-10-12/code/hf_score.py \
  data/experiments/homefit_2026-10-12/decoy_check_output.txt \
  data/experiments/homefit_2026-10-12/inputs/HF_01.json \
  data/experiments/homefit_2026-10-12/inputs/HF_02.json \
  data/experiments/homefit_2026-10-12/inputs/HF_03.json \
  data/experiments/homefit_2026-10-12/inputs/HF_04.json \
  data/experiments/homefit_2026-10-12/inputs/HF_05.json \
  data/experiments/homefit_2026-10-12/judged/HF_01.out.json \
  data/experiments/homefit_2026-10-12/judged/HF_02.out.json \
  data/experiments/homefit_2026-10-12/judged/HF_03.out.json \
  data/experiments/homefit_2026-10-12/judged/HF_04.out.json \
  data/experiments/homefit_2026-10-12/judged/HF_05.out.json \
  data/experiments/homefit_2026-10-12/PREREG.md \
  data/experiments/homefit_2026-10-12/REPORT.md \
  data/experiments/homefit_2026-10-12/rubric_homefit.md \
  data/experiments/homefit_2026-10-12/score_output.txt
git diff --cached --quiet || git commit -m "Home-fit test: NOISE as declared, and the decoy was inside the pathway own region"

git add \
  data/experiments/reviewer_notes/HANDOFF_2026-10-12.md \
  data/experiments/reviewer_notes/PROMPT_28_original.md \
  data/experiments/reviewer_notes/PROMPT_31.md \
  data/experiments/reviewer_notes/SPEC_overlap_arm_2026-10-12.md
git diff --cached --quiet || git commit -m "The reviewer handoff, the overlap spec, and prompt 28 as originally given"

git add \
  data/ontology/frozen/working-c85-2026-10-10/all_verdicts_c85.json \
  data/ontology/frozen/working-c85-2026-10-10/CHECKSUMS.sha256 \
  data/ontology/frozen/working-c85-2026-10-10/edges.tsv \
  data/ontology/frozen/working-c85-2026-10-10/excluded_inputs.tsv \
  data/ontology/frozen/working-c85-2026-10-10/floors_L_cal8.json \
  data/ontology/frozen/working-c85-2026-10-10/FROZEN.md \
  data/ontology/frozen/working-c85-2026-10-10/manifest.json \
  data/ontology/frozen/working-c85-2026-10-10/match_to_baseline.tsv \
  data/ontology/frozen/working-c85-2026-10-10/members.tsv \
  data/ontology/frozen/working-c85-2026-10-10/nodes.tsv \
  data/ontology/frozen/working-c85-2026-10-10/repair_map.json \
  data/ontology/frozen/working-c85-2026-10-10/REPORT_c85_reassessment.md \
  data/ontology/frozen/working-c85-2026-10-10/report.txt \
  data/ontology/frozen/working-c85-2026-10-10/trees_build_log.json \
  data/ontology/frozen/working-c85-2026-10-10/universe.json \
  data/ontology/frozen/working-c85-2026-10-10/unplaced.tsv \
  tests/ontology/test_frozen_baseline.py
git diff --cached --quiet || git commit -m "Freeze c85 as the working version, guarded by the same checksum test as the baseline"

git add .gitignore CLAUDE.md DECISIONS.md docs/status/2026-10-09-chain-c85.md docs/status/commit-2026-10-12-handoff.sh
git diff --cached --quiet || git commit -m "c85 is the working version; the sibling merge rule is superseded and the naming run is held"

git tag -a $TAG -m "THEMA working version c85, frozen 2026-10-10: thema_L_x2_c85 on 5,539 atomic pathways. 8,251 themes, 97.64 percent coherent or umbrella, 195 not ok against the baseline 197, 10 giant roots unchanged. Differs from the 2026-10-09 baseline in the chain-collapse rule alone: share 0.85 keeping the higher-support node, against 0.90 always keeping the parent. POST-HOC rule. Frozen at data/ontology/frozen/working-c85-2026-10-10 with CHECKSUMS.sha256 and a test that fails on drift. The 2026-10-09 baseline remains frozen as the fallback. Known limit: 28 percent of collapse pairs are decided by a support margin under 0.05."

git push origin $BRANCH
git push origin $TAG

echo "tag:    $TAG"
echo "commit: $(git rev-list -n 1 $TAG)"
echo "branch: $BRANCH"
