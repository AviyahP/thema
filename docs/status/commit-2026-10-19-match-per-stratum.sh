#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Making the giants units gets every one of them contained, at the cost of a root holding 81 percent" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/match_per_stratum.py scripts/match_per_stratum_report.py tests/test_match_per_stratum.py
git diff --cached --quiet || git commit -m "Sweep the match threshold per size stratum, resumably, and build both arms"

git add \
  data/experiments/match_per_stratum_2026-10-19/strata.json \
  data/experiments/match_per_stratum_2026-10-19/report.txt \
  data/experiments/match_per_stratum_2026-10-19/M/roots.tsv \
  data/experiments/match_per_stratum_2026-10-19/Mm/roots.tsv
git diff --cached --quiet || git commit -m "The sweep: theta 0.70 below ten pathways and 0.50 above it, 38,434 admitted"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_M/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_M/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_M/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_M/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_M/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_Mm/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_Mm/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_Mm/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_Mm/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_Mm/unplaced.tsv
git diff --cached --quiet || git commit -m "Arm M at 6,884 themes and 394 roots; arm Mm at 2,973 and 94"

git add \
  data/experiments/O50s_roots_reading_2026-10-18/PREREG_O50s_roots.md \
  data/experiments/O50s_roots_reading_2026-10-18/RESULT_O50s_roots.md \
  data/experiments/O50s_roots_reading_2026-10-18/R_readings.json \
  data/experiments/O50s_roots_reading_2026-10-18/S_judgements.json \
  data/experiments/O50s_roots_reading_2026-10-18/S_summary.json \
  data/experiments/O50s_roots_reading_2026-10-18/code/build.py \
  data/experiments/O50s_roots_reading_2026-10-18/code/score_small.py \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b01.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b02.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b03.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b04.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b05.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b06.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b07.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b08.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b09.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b10.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b11.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b12.md \
  data/experiments/O50s_roots_reading_2026-10-18/read_inputs/R_b13.md \
  data/experiments/O50s_roots_reading_2026-10-18/roots_index.json \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b01.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b02.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b03.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b04.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b05.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b06.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b07.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b08.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b09.md \
  data/experiments/O50s_roots_reading_2026-10-18/small_inputs/S_b10.md \
  data/experiments/areas_on_roots_reading_2026-10-18/A_readings.json \
  data/experiments/areas_on_roots_reading_2026-10-18/PREREG_areas_reading.md \
  data/experiments/areas_on_roots_reading_2026-10-18/RESULT_areas_reading.md \
  data/experiments/areas_on_roots_reading_2026-10-18/RESULT_scores.txt \
  data/experiments/areas_on_roots_reading_2026-10-18/code/build.py \
  data/experiments/areas_on_roots_reading_2026-10-18/code/score.py \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b01.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b02.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b03.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b04.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b05.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b06.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b07.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b08.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b09.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b10.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b11.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b12.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b13.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b14.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b15.md \
  data/experiments/areas_on_roots_reading_2026-10-18/read_inputs/A_b16.md \
  data/experiments/small_roots_nesting_2026-10-18/O50s_hennig_stability_10plus.tsv \
  data/experiments/small_roots_nesting_2026-10-18/O50s_support_loose_match.tsv \
  data/experiments/small_roots_nesting_2026-10-18/PLAN.md \
  data/experiments/small_roots_nesting_2026-10-18/RESULT_small_roots_nesting.md \
  data/experiments/small_roots_nesting_2026-10-18/code/nesting.py \
  data/experiments/small_roots_nesting_2026-10-18/per_root.tsv \
  data/experiments/small_roots_nesting_2026-10-18/progress.txt \
  data/experiments/small_roots_nesting_2026-10-18/run.log
git diff --cached --quiet || git commit -m "Reviewer material: the O50s and areas-on-roots readings and the small-root nesting diagnostics"

git add data/experiments/reviewer_notes/PROMPT_47.md
git diff --cached --quiet || git commit -m "Prompt 47, for the record"

git add docs/status/2026-10-19-match-per-stratum.md docs/status/commit-2026-10-19-match-per-stratum.sh DECISIONS.md
git diff --cached --quiet || git commit -m "The threshold must flip at ten pathways, but a looser gate is the wrong lever for the small roots"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. Theta 0.70 below 10 pathways and 0.50 above it. M gives 394 roots, Mm gives 94 but guts the build."
