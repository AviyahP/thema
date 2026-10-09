#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git add .gitignore
git commit -m "Ignore unblinding keys anywhere, calibration stores and regenerable rosters"

git add DECISIONS.md docs/status/2026-10-08-reviewer-log.md docs/spec/2026-10-08-leaves-centroid.md
git commit -m "Record the reviewer log, repair route a, and the two late-transcribed grids"

git add src/thema/ontology/v04.py tests/ontology/test_v04.py
git commit -m "Split THETA into THETA_MATCH and THETA_MERGE, byte-identical at 0.70"

git add src/thema/ontology/leaves.py tests/ontology/test_leaves.py tests/ontology/test_universe.py
git commit -m "Universe L: the summary rule, its answer key, and the producer exemption"

git add src/thema/ontology/linkage.py tests/ontology/test_linkage.py scripts/one_linkage_step1.py
git commit -m "Normalised-centroid cosine linkage, exact via running sums, and its step 1 diagnostic"

git add src/thema/ontology/repair.py tests/ontology/test_repair.py
git commit -m "Repair route a: stale-merge fix and chain collapse, outside consensus"

git add scripts/leaves_universe.py scripts/leaves_build.py scripts/leaves_baseline.py scripts/leaves_score.py scripts/leaves_text.py scripts/leaves_theta_report.py scripts/regate_floors.py scripts/regate_report.py scripts/twins_diagnosis.py scripts/repair_big_themes.py scripts/repair_node_stats.py scripts/giants_report.py scripts/export_browse_leaves.py
git commit -m "Leaves, re-gate, twins, repair and giants scripts, plus the universe L browser"

git add \
  data/experiments/giants/giants.json \
  data/experiments/giants/node_stats.json \
  data/experiments/giants/summary.txt \
  data/experiments/leaves_theta/cross_applied_floors.txt \
  data/experiments/leaves_theta/M5_cannot_borrow_L_floors.txt \
  data/experiments/leaves_theta/scores_test_primary.json \
  data/experiments/leaves_theta/scores_test_secondary.json \
  data/experiments/leaves_theta/theta_report.json \
  data/experiments/leaves/floors_stored_failed_on_L.json \
  data/experiments/leaves/scores_test_primary.json \
  data/experiments/leaves/scores_test_secondary.json \
  data/experiments/leaves/scores_tuning.json \
  data/experiments/leaves/stratum_5-5_floor_tradeoff.txt \
  data/experiments/leaves/testN_price.txt \
  data/experiments/leaves/text_test.json \
  data/experiments/one_linkage/cuts.txt \
  data/experiments/one_linkage/step1.json \
  data/experiments/regate/examples.txt \
  data/experiments/regate/floors_summary.json \
  data/experiments/regate/regate_report.json \
  data/experiments/regate/rule.txt \
  data/experiments/regate/scores_test_secondary.json \
  data/experiments/repair/big_themes.json \
  data/experiments/repair/collapse80.txt \
  data/experiments/repair/fresh_floors.txt \
  data/experiments/repair/scores.json \
  data/experiments/repair/shape.json \
  data/experiments/repair/toplevel.txt \
  data/experiments/twins/alt_cost.txt \
  data/experiments/twins/growth.txt \
  data/experiments/twins/twins.json \
  data/ontology/v0.4-leaves/calibration_M5/floors.json \
  data/ontology/v0.4-leaves/calibration_MS/floors.json \
  data/ontology/v0.4-leaves/calibration/floors.json \
  data/ontology/v0.4-leaves/hidef_L_k4_maxres800/edges.tsv \
  data/ontology/v0.4-leaves/hidef_L_k4_maxres800/manifest.json \
  data/ontology/v0.4-leaves/hidef_L_k4_maxres800/members.tsv \
  data/ontology/v0.4-leaves/hidef_L_k4_maxres800/nodes.tsv \
  data/ontology/v0.4-leaves/hidef_L_k4_maxres800/unplaced.tsv \
  data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
  data/ontology/v0.4-leaves/regate/floors_L_calibrated.json \
  data/ontology/v0.4-leaves/regate/floors_L_current.json \
  data/ontology/v0.4-leaves/regate/floors_M5_cal8.json \
  data/ontology/v0.4-leaves/regate/floors_M5_calibrated.json \
  data/ontology/v0.4-leaves/regate/floors_M5_current.json \
  data/ontology/v0.4-leaves/regate/floors_MS_cal8.json \
  data/ontology/v0.4-leaves/regate/floors_MS_calibrated.json \
  data/ontology/v0.4-leaves/regate/floors_MS_current.json \
  data/ontology/v0.4-leaves/regate/summary.json \
  data/ontology/v0.4-leaves/restricted_v04/edges.tsv \
  data/ontology/v0.4-leaves/restricted_v04/manifest.json \
  data/ontology/v0.4-leaves/restricted_v04/members.tsv \
  data/ontology/v0.4-leaves/restricted_v04/nodes.tsv \
  data/ontology/v0.4-leaves/restricted_v04/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_cal/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_cal/manifest.json \
  data/ontology/v0.4-leaves/thema_L_cal/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_cal/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_cal8/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_cal8/manifest.json \
  data/ontology/v0.4-leaves/thema_L_cal8/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_cal8/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_g_cur/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_g_cur/manifest.json \
  data/ontology/v0.4-leaves/thema_L_g_cur/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_g_cur/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_cal/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_cal/manifest.json \
  data/ontology/v0.4-leaves/thema_L_M5_cal/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_cal/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_cal8/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_cal8/manifest.json \
  data/ontology/v0.4-leaves/thema_L_M5_cal8/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_cal8/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_g_cur/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_g_cur/manifest.json \
  data/ontology/v0.4-leaves/thema_L_M5_g_cur/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_g_cur/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_r1-100/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_r1-100/manifest.json \
  data/ontology/v0.4-leaves/thema_L_M5_r1-100/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_r1-100/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_r101-200/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_r101-200/manifest.json \
  data/ontology/v0.4-leaves/thema_L_M5_r101-200/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_M5_r101-200/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_M5/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_M5/manifest.json \
  data/ontology/v0.4-leaves/thema_L_M5/members.tsv \
  data/ontology/v0.4-leaves/thema_L_M5/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_M5/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_matched2447/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_matched2447/manifest.json \
  data/ontology/v0.4-leaves/thema_L_matched2447/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_matched2447/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_cal/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_cal/manifest.json \
  data/ontology/v0.4-leaves/thema_L_MS_cal/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_cal/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_cal8/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_cal8/manifest.json \
  data/ontology/v0.4-leaves/thema_L_MS_cal8/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_cal8/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_g_cur/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_g_cur/manifest.json \
  data/ontology/v0.4-leaves/thema_L_MS_g_cur/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_g_cur/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_r1-100/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_r1-100/manifest.json \
  data/ontology/v0.4-leaves/thema_L_MS_r1-100/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_r1-100/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_r101-200/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_r101-200/manifest.json \
  data/ontology/v0.4-leaves/thema_L_MS_r101-200/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_MS_r101-200/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_MS/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_MS/manifest.json \
  data/ontology/v0.4-leaves/thema_L_MS/members.tsv \
  data/ontology/v0.4-leaves/thema_L_MS/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_MS/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_r1-100/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_r1-100/manifest.json \
  data/ontology/v0.4-leaves/thema_L_r1-100/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_r1-100/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_r101-200/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_r101-200/manifest.json \
  data/ontology/v0.4-leaves/thema_L_r101-200/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_r101-200/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_repair/browse.html \
  data/ontology/v0.4-leaves/thema_L_repair/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_repair/manifest.json \
  data/ontology/v0.4-leaves/thema_L_repair/members.tsv \
  data/ontology/v0.4-leaves/thema_L_repair/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_repair/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L/edges.tsv \
  data/ontology/v0.4-leaves/thema_L/manifest.json \
  data/ontology/v0.4-leaves/thema_L/members.tsv \
  data/ontology/v0.4-leaves/thema_L/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L/unplaced.tsv \
  data/ontology/v0.4-leaves/trees/leaves_centred_c54319cdfbbe9eb7/build_log.json \
  data/ontology/v0.4-leaves/universe.json
git commit -m "Leaves through giants: every build shape, floor record, score and the browsable export"

git add \
  data/experiments/llm_grouping_pilot/batch_00_desc.json \
  data/experiments/llm_grouping_pilot/batch_00_names.json \
  data/experiments/llm_grouping_pilot/batch_01_desc.json \
  data/experiments/llm_grouping_pilot/batch_01_names.json \
  data/experiments/llm_grouping_pilot/batch_02_desc.json \
  data/experiments/llm_grouping_pilot/batch_02_names.json \
  data/experiments/llm_grouping_pilot/batch_03_desc.json \
  data/experiments/llm_grouping_pilot/batch_03_names.json \
  data/experiments/llm_grouping_pilot/batch_04_desc.json \
  data/experiments/llm_grouping_pilot/batch_04_names.json \
  data/experiments/llm_grouping_pilot/batch_05_desc.json \
  data/experiments/llm_grouping_pilot/batch_05_names.json \
  data/experiments/llm_grouping_pilot/batch_06_desc.json \
  data/experiments/llm_grouping_pilot/batch_06_names.json \
  data/experiments/llm_grouping_pilot/batch_07_desc.json \
  data/experiments/llm_grouping_pilot/batch_07_names.json \
  data/experiments/llm_grouping_pilot/batch_08_desc.json \
  data/experiments/llm_grouping_pilot/batch_08_names.json \
  data/experiments/llm_grouping_pilot/batch_09_desc.json \
  data/experiments/llm_grouping_pilot/batch_09_names.json \
  data/experiments/llm_grouping_pilot/batch_10_desc.json \
  data/experiments/llm_grouping_pilot/batch_10_names.json \
  data/experiments/llm_grouping_pilot/batch_11_desc.json \
  data/experiments/llm_grouping_pilot/batch_11_names.json \
  data/experiments/llm_grouping_pilot/batch_12_desc.json \
  data/experiments/llm_grouping_pilot/batch_12_names.json \
  data/experiments/llm_grouping_pilot/batch_13_desc.json \
  data/experiments/llm_grouping_pilot/batch_13_names.json \
  data/experiments/llm_grouping_pilot/batch_14_desc.json \
  data/experiments/llm_grouping_pilot/batch_14_names.json \
  data/experiments/llm_grouping_pilot/batch_15_desc.json \
  data/experiments/llm_grouping_pilot/batch_15_names.json \
  data/experiments/llm_grouping_pilot/embed_reductions.py \
  data/experiments/llm_grouping_pilot/embed_rewrites.py \
  data/experiments/llm_grouping_pilot/out/batch_00_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_00_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_01_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_01_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_02_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_02_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_03_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_03_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_04_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_04_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_05_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_05_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_06_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_06_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_07_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_07_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_08_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_08_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_09_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_09_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_10_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_10_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_11_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_11_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_12_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_12_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_13_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_13_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_14_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_14_names_out.json \
  data/experiments/llm_grouping_pilot/out/batch_15_desc_out.json \
  data/experiments/llm_grouping_pilot/out/batch_15_names_out.json \
  data/experiments/llm_grouping_pilot/reductions/batch_00_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_01_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_02_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_03_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_04_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_05_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_06_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_07_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_08_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_09_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_10_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_11_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_12_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_13_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_14_red.json \
  data/experiments/llm_grouping_pilot/reductions/batch_15_red.json \
  data/experiments/llm_grouping_pilot/reductions/compare_reductions.html \
  data/experiments/llm_grouping_pilot/reductions/emb_disease.npz \
  data/experiments/llm_grouping_pilot/reductions/emb_joined.npz \
  data/experiments/llm_grouping_pilot/reductions/emb_process.npz \
  data/experiments/llm_grouping_pilot/reductions/emb_tissue.npz \
  data/experiments/llm_grouping_pilot/rewrites/batch_00_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_00_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_01_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_01_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_02_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_02_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_03_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_03_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_04_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_04_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_04_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_05_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_05_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_05_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_06_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_06_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_06_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_07_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_07_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_07_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_08_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_08_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_09_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_09_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_10_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_10_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_11_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_11_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_12_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_12_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_12_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_13_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_13_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_13_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_14_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_14_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_14_process.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_15_context.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_15_neutral.json \
  data/experiments/llm_grouping_pilot/rewrites/batch_15_process.json \
  data/experiments/llm_grouping_pilot/rewrites/compare_rewrites.html \
  data/experiments/llm_grouping_pilot/rewrites/emb_context.npz \
  data/experiments/llm_grouping_pilot/rewrites/emb_neutral.npz \
  data/experiments/llm_grouping_pilot/rewrites/emb_orig.npz \
  data/experiments/llm_grouping_pilot/rewrites/emb_process.npz
git commit -m "LLM grouping pilot material, the only reviewer artefacts that survive; key excluded"

git add CLAUDE.md docs/status/2026-10-08-leaves.md docs/status/2026-10-08-leaves-theta.md docs/status/2026-10-08-one-linkage.md docs/status/2026-10-08-regate.md docs/status/2026-10-08-twins-diagnosis.md docs/status/2026-10-09-repair.md docs/status/2026-10-09-giants.md docs/status/commit-2026-10-09-giants.sh
git commit -m "The eight giants are overlapping bags, not areas; removing them leaves 905 roots"

git push
