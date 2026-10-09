#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git add DECISIONS.md docs/status/2026-10-09-reviewer-plausibility.md
git commit -m "Record all four judging rounds, the BTM drop, floors reuse, and three corrections"

git add data/excluded_inputs.tsv data/ontology/v0.4-leaves/README.md data/ontology/v0.4-leaves/regate/floors_L_cal8.json
git commit -m "Exclude 17 heterogeneous BTMs by config; record the cal8 floors reuse in three places"

git add \
  data/experiments/reviewer_sample_2026-10-09/all_verdicts.json \
  data/experiments/reviewer_sample_2026-10-09/big_all.json \
  data/experiments/reviewer_sample_2026-10-09/incoherent_analysis.json \
  data/experiments/reviewer_sample_2026-10-09/judged.json \
  data/experiments/reviewer_sample_2026-10-09/judged2.json \
  data/experiments/reviewer_sample_2026-10-09/judged3.json \
  data/experiments/reviewer_sample_2026-10-09/judged4_rest.json \
  data/experiments/reviewer_sample_2026-10-09/REPORT.md \
  data/experiments/reviewer_sample_2026-10-09/REPORT2.md \
  data/experiments/reviewer_sample_2026-10-09/REPORT3.md \
  data/experiments/reviewer_sample_2026-10-09/REPORT4.md \
  data/experiments/reviewer_sample_2026-10-09/REPORT5_incoherent.md \
  data/experiments/reviewer_sample_2026-10-09/round2.json \
  data/experiments/reviewer_sample_2026-10-09/round3.json \
  data/experiments/reviewer_sample_2026-10-09/rubric.md \
  data/experiments/reviewer_sample_2026-10-09/rubric2.md \
  data/experiments/reviewer_sample_2026-10-09/rubric3.md \
  data/experiments/reviewer_sample_2026-10-09/rubric4.md \
  data/experiments/reviewer_sample_2026-10-09/sample.json \
  data/experiments/reviewer_sample_2026-10-09/sample2.json \
  data/experiments/reviewer_sample_2026-10-09/sample3.json \
  data/experiments/reviewer_sample_2026-10-09/sample4_rest.json \
  data/experiments/reviewer_sample_2026-10-09/tba_rejudge.json
git commit -m "Reviewer samples 1 to 3 and the full census; judgements, rubrics, no keys"

git add scripts/redundancy_measure.py scripts/fan_ancestors.py scripts/n00150_worked_example.py scripts/chain_survivor.py
git commit -m "Measure chain ratios, sibling twins, fans and the chain survivor rule"

git add \
  data/experiments/redundancy/chain_survivor.json \
  data/experiments/redundancy/fan.json \
  data/experiments/redundancy/measure.json \
  data/experiments/redundancy/n00150_rules.json \
  data/experiments/redundancy/n00150_siblings.txt
git commit -m "Redundancy measurements, the n00150 lattice and the survivor comparison"

git add CLAUDE.md docs/status/2026-10-09-redundancy-measure.md docs/status/commit-2026-10-09-plausibility.sh
git commit -m "Chain collapse keeps the less stable node on 62 percent of edges in 0.85 to 0.90"

git push
