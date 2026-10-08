#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git add .gitignore
git commit -m "Ignore the v0.4 side caches, intermediate rosters and the unblinding key"

git add DECISIONS.md docs/spec/eval-protocol-2026-10.md docs/spec/2026-10-08-reviewer-monotonicity-notes.md docs/spec/2026-10-08-leaves-experiment.md
git commit -m "Declarations: v0.4 verdict, direction pilot failed, names rejected, two new specs"

git add src/thema/ontology/ablate.py src/thema/ontology/evalsets.py scripts/v04_ablate.py scripts/v04_build.py scripts/v04_score.py scripts/v04_pairs.py scripts/v04_ablation_table.py
git commit -m "v0.4 ablation machinery: switches, GO closure, split-half scoring"

git add src/thema/ontology/v04.py scripts/v04_run.py tests/ontology/test_v04.py
git commit -m "THEMA v0.4: three kept stages, proved byte-identical to the frozen v0.3"

git add scripts/monotonicity_check.py scripts/monotonicity_followup.py
git commit -m "Monotonicity checks: containment, placement, the probe controls and GO"

git add \
  data/experiments/v04/ablation_table_tuning.json \
  data/experiments/v04/pairs_test.json \
  data/experiments/v04/scores_test_primary.json \
  data/experiments/v04/scores_test_secondary.json \
  data/experiments/v04/scores_tuning.json \
  data/ontology/v0.3/ablate/baseline/floors.json \
  data/ontology/v0.3/ablate/flat_merge/floors.json \
  data/ontology/v0.3/ablate/flat_merge/real.stages.json \
  data/ontology/v0.3/ablate/flat_merge/seed03001.stages.json \
  data/ontology/v0.3/ablate/flat_merge/seed03002.stages.json \
  data/ontology/v0.3/ablate/flat_merge/seed03003.stages.json \
  data/ontology/v0.3/ablate/flat_merge/seed04001.stages.json \
  data/ontology/v0.3/ablate/flat_merge/seed04002.stages.json \
  data/ontology/v0.3/ablate/no_completion/floors.json \
  data/ontology/v0.3/ablate/no_completion/real.stages.json \
  data/ontology/v0.3/ablate/no_completion/seed03001.stages.json \
  data/ontology/v0.3/ablate/no_completion/seed03002.stages.json \
  data/ontology/v0.3/ablate/no_completion/seed03003.stages.json \
  data/ontology/v0.3/ablate/no_completion/seed04001.stages.json \
  data/ontology/v0.3/ablate/no_completion/seed04002.stages.json \
  data/ontology/v0.3/ablate/no_size_cap/floors.json \
  data/ontology/v0.3/ablate/no_size_cap/real.stages.json \
  data/ontology/v0.3/ablate/no_size_cap/seed03001.stages.json \
  data/ontology/v0.3/ablate/no_size_cap/seed03002.stages.json \
  data/ontology/v0.3/ablate/no_size_cap/seed03003.stages.json \
  data/ontology/v0.3/ablate/no_size_cap/seed04001.stages.json \
  data/ontology/v0.3/ablate/no_size_cap/seed04002.stages.json \
  data/ontology/v0.3/ablate/no_stray/floors.json \
  data/ontology/v0.3/ablate/partial_containment/floors.json \
  data/ontology/v0.3/ablate/single_floor/floors.json \
  data/ontology/v0.4/ablate_baseline_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_baseline_r1-100/manifest.json \
  data/ontology/v0.4/ablate_baseline_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_baseline_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_baseline_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_baseline_r101-200/manifest.json \
  data/ontology/v0.4/ablate_baseline_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_baseline_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_baseline/edges.tsv \
  data/ontology/v0.4/ablate_baseline/manifest.json \
  data/ontology/v0.4/ablate_baseline/nodes.tsv \
  data/ontology/v0.4/ablate_baseline/unplaced.tsv \
  data/ontology/v0.4/ablate_flat_merge_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_flat_merge_r1-100/manifest.json \
  data/ontology/v0.4/ablate_flat_merge_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_flat_merge_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_flat_merge_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_flat_merge_r101-200/manifest.json \
  data/ontology/v0.4/ablate_flat_merge_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_flat_merge_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_flat_merge/edges.tsv \
  data/ontology/v0.4/ablate_flat_merge/manifest.json \
  data/ontology/v0.4/ablate_flat_merge/nodes.tsv \
  data/ontology/v0.4/ablate_flat_merge/unplaced.tsv \
  data/ontology/v0.4/ablate_no_completion_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_no_completion_r1-100/manifest.json \
  data/ontology/v0.4/ablate_no_completion_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_no_completion_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_no_completion_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_no_completion_r101-200/manifest.json \
  data/ontology/v0.4/ablate_no_completion_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_no_completion_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_no_completion/edges.tsv \
  data/ontology/v0.4/ablate_no_completion/manifest.json \
  data/ontology/v0.4/ablate_no_completion/nodes.tsv \
  data/ontology/v0.4/ablate_no_completion/unplaced.tsv \
  data/ontology/v0.4/ablate_no_size_cap_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_no_size_cap_r1-100/manifest.json \
  data/ontology/v0.4/ablate_no_size_cap_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_no_size_cap_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_no_size_cap_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_no_size_cap_r101-200/manifest.json \
  data/ontology/v0.4/ablate_no_size_cap_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_no_size_cap_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_no_size_cap/edges.tsv \
  data/ontology/v0.4/ablate_no_size_cap/manifest.json \
  data/ontology/v0.4/ablate_no_size_cap/nodes.tsv \
  data/ontology/v0.4/ablate_no_size_cap/unplaced.tsv \
  data/ontology/v0.4/ablate_no_stray_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_no_stray_r1-100/manifest.json \
  data/ontology/v0.4/ablate_no_stray_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_no_stray_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_no_stray_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_no_stray_r101-200/manifest.json \
  data/ontology/v0.4/ablate_no_stray_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_no_stray_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_no_stray/edges.tsv \
  data/ontology/v0.4/ablate_no_stray/manifest.json \
  data/ontology/v0.4/ablate_no_stray/nodes.tsv \
  data/ontology/v0.4/ablate_no_stray/unplaced.tsv \
  data/ontology/v0.4/ablate_partial_containment_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_partial_containment_r1-100/manifest.json \
  data/ontology/v0.4/ablate_partial_containment_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_partial_containment_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_partial_containment_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_partial_containment_r101-200/manifest.json \
  data/ontology/v0.4/ablate_partial_containment_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_partial_containment_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_partial_containment/edges.tsv \
  data/ontology/v0.4/ablate_partial_containment/manifest.json \
  data/ontology/v0.4/ablate_partial_containment/nodes.tsv \
  data/ontology/v0.4/ablate_partial_containment/unplaced.tsv \
  data/ontology/v0.4/ablate_single_floor_r1-100/edges.tsv \
  data/ontology/v0.4/ablate_single_floor_r1-100/manifest.json \
  data/ontology/v0.4/ablate_single_floor_r1-100/nodes.tsv \
  data/ontology/v0.4/ablate_single_floor_r1-100/unplaced.tsv \
  data/ontology/v0.4/ablate_single_floor_r101-200/edges.tsv \
  data/ontology/v0.4/ablate_single_floor_r101-200/manifest.json \
  data/ontology/v0.4/ablate_single_floor_r101-200/nodes.tsv \
  data/ontology/v0.4/ablate_single_floor_r101-200/unplaced.tsv \
  data/ontology/v0.4/ablate_single_floor/edges.tsv \
  data/ontology/v0.4/ablate_single_floor/manifest.json \
  data/ontology/v0.4/ablate_single_floor/nodes.tsv \
  data/ontology/v0.4/ablate_single_floor/unplaced.tsv \
  data/ontology/v0.4/calibration/floors.json \
  data/ontology/v0.4/thema_10770_matched4287/edges.tsv \
  data/ontology/v0.4/thema_10770_matched4287/manifest.json \
  data/ontology/v0.4/thema_10770_matched4287/nodes.tsv \
  data/ontology/v0.4/thema_10770_matched4287/unplaced.tsv \
  data/ontology/v0.4/thema_10770_r1-100/edges.tsv \
  data/ontology/v0.4/thema_10770_r1-100/manifest.json \
  data/ontology/v0.4/thema_10770_r1-100/nodes.tsv \
  data/ontology/v0.4/thema_10770_r1-100/unplaced.tsv \
  data/ontology/v0.4/thema_10770_r101-200/edges.tsv \
  data/ontology/v0.4/thema_10770_r101-200/manifest.json \
  data/ontology/v0.4/thema_10770_r101-200/nodes.tsv \
  data/ontology/v0.4/thema_10770_r101-200/unplaced.tsv \
  data/ontology/v0.4/thema_10770/edges.tsv \
  data/ontology/v0.4/thema_10770/manifest.json \
  data/ontology/v0.4/thema_10770/members.tsv \
  data/ontology/v0.4/thema_10770/nodes.tsv \
  data/ontology/v0.4/thema_10770/unplaced.tsv
git commit -m "v0.4 builds, calibration record and the test-half scores"

git add \
  data/experiments/direction_pilot/blinded_descriptions.jsonl \
  data/experiments/direction_pilot/direction_fields_v1.jsonl \
  data/experiments/direction_pilot/direction-v1.md \
  data/experiments/direction_pilot/pilot_pairs.tsv \
  data/experiments/direction_pilot/pilot_result.txt \
  data/experiments/direction_pilot/pilot_summary.txt \
  data/experiments/direction_pilot/score_pilot.py
git commit -m "Direction pilot, as run: 62.5 percent against a 70 percent bar"

git add CLAUDE.md docs/spec/validation-plan.md docs/status/2026-10-07-v04.md docs/status/2026-10-08-monotonicity.md docs/status/commit-2026-10-08-wrapup.sh
git commit -m "v0.4 is the current core; reports for v0.4 and monotonicity"

git push
