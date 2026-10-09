#!/bin/zsh
set -euo pipefail
cd ~/code/thema

TAG=thema-baseline-2026-10-09

git add DECISIONS.md docs/status/2026-10-09-reviewer-full-report.md docs/status/2026-10-09-x2-evaluation.md data/experiments/reviewer_sample_2026-10-09/REVIEW_FULL_REPORT.md
git diff --cached --quiet || git commit -m "Record the full review with sections 14 to 17, the x2 evaluation, and step 3 done"

git add \
  data/experiments/reviewer_eval_x2_2026-10-09/all_verdicts_x2.json \
  data/experiments/reviewer_eval_x2_2026-10-09/carried_verdicts.json \
  data/experiments/reviewer_eval_x2_2026-10-09/judged_new.json \
  data/experiments/reviewer_eval_x2_2026-10-09/REPORT_x2.md \
  data/experiments/reviewer_eval_x2_2026-10-09/rubric4_x2.md \
  data/experiments/reviewer_eval_x2_2026-10-09/to_judge.json
git diff --cached --quiet || git commit -m "Step 3 material: all 8,740 x2 verdicts, carried verdicts and the x2 rubric"

git add data/excluded_inputs.tsv data/experiments/reviewer_sample_2026-10-09/rubric5_exclusion2.md scripts/exclusion2_screen.py
git diff --cached --quiet || git commit -m "Exclusion 2: the rule, its screen, six exclusions, and GO 0010800 marked to reinstate"

git add scripts/leaves_universe.py scripts/leaves_build.py scripts/repair_node_stats.py scripts/export_browse_leaves.py scripts/compare_x2.py
git diff --cached --quiet || git commit -m "Build universe L minus listed exclusions, write beside the build compared with"

git add \
  data/experiments/exclusion2/candidates.json \
  data/experiments/exclusion2/collected.txt \
  data/experiments/exclusion2/containment_test.txt \
  data/experiments/exclusion2/list.txt \
  data/experiments/exclusion2/verdicts.json \
  data/experiments/exclusion2/x2_node_stats.json \
  data/ontology/v0.4-leaves-x2/trees/leaves_centred_x2_c54319cdfbbe9eb7/build_log.json \
  data/ontology/v0.4-leaves-x2/universe.json \
  data/ontology/v0.4-leaves/thema_L_x2/browse.html \
  data/ontology/v0.4-leaves/thema_L_x2/compare_to_repair.json \
  data/ontology/v0.4-leaves/thema_L_x2/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2/match_to_repair.tsv \
  data/ontology/v0.4-leaves/thema_L_x2/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2/unplaced.tsv
git diff --cached --quiet || git commit -m "thema_L_x2: the rebuild on 5,539 leaves, its browser and the mapping to repair"

git add .gitignore CLAUDE.md data/ontology/v0.4-leaves/README.md docs/status/2026-10-09-exclusion2-rebuild.md docs/status/commit-2026-10-09-exclusion2.sh docs/status/commit-2026-10-09-baseline.sh
git diff --cached --quiet || git commit -m "x2 evaluates at 97.7 percent; the churn is low-support themes, not structure"

git add \
  data/ontology/frozen/baseline-2026-10-09/all_verdicts_x2.json \
  data/ontology/frozen/baseline-2026-10-09/browse.html \
  data/ontology/frozen/baseline-2026-10-09/CHECKSUMS.sha256 \
  data/ontology/frozen/baseline-2026-10-09/compare_to_repair.json \
  data/ontology/frozen/baseline-2026-10-09/edges.tsv \
  data/ontology/frozen/baseline-2026-10-09/excluded_inputs.tsv \
  data/ontology/frozen/baseline-2026-10-09/floors_L_cal8.json \
  data/ontology/frozen/baseline-2026-10-09/FROZEN.md \
  data/ontology/frozen/baseline-2026-10-09/manifest.json \
  data/ontology/frozen/baseline-2026-10-09/match_to_repair.tsv \
  data/ontology/frozen/baseline-2026-10-09/members.tsv \
  data/ontology/frozen/baseline-2026-10-09/nodes.tsv \
  data/ontology/frozen/baseline-2026-10-09/REPORT_x2.md \
  data/ontology/frozen/baseline-2026-10-09/trees_build_log.json \
  data/ontology/frozen/baseline-2026-10-09/universe.json \
  data/ontology/frozen/baseline-2026-10-09/unplaced.tsv \
  tests/ontology/test_frozen_baseline.py
git diff --cached --quiet || git commit -m "Freeze thema_L_x2 as THEMA baseline 2026-10-09, checksummed and guarded by a test"

git add docs/plans/2026-10-09-stats-implementation-considerations.md data/experiments/reviewer_notes/2026-10-09-stats-implementation-considerations.md
git diff --cached --quiet || git commit -m "Record the statistics-layer implementation considerations as possibilities, not decisions"

git tag -a $TAG -m "THEMA baseline 2026-10-09: thema_L_x2 on 5,539 atomic pathways. 8,740 themes, 97.7 percent coherent or linked umbrella, 10 roots over 1,000 members. Frozen at data/ontology/frozen/baseline-2026-10-09 with CHECKSUMS.sha256 and a test that fails on drift. Keeps go:GO:0010800 excluded, marked to reinstate at the next rebuild, so the build stands on 23 exclusions while 22 are effective. Every later change goes in a new directory and reports a comparison against this build."

git push origin leaves-2026-10
git push origin $TAG

echo "tag:    $TAG"
echo "commit: $(git rev-list -n 1 $TAG)"
