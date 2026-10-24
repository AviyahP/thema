#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Trimming the child preserves strictness and costs 39 percent of the themes, moving the damage to the small bands" > /dev/null

git add scripts/core_merge.py scripts/core_merge_pairs.py scripts/core_merge_report.py
git diff --cached --quiet || git commit -m "Prompt 58: merge by core, arms CI and CT, with the near-copy counts by exact sparse products"

git add \
  data/experiments/core_merge_2026-10-23/arms.json \
  data/experiments/core_merge_2026-10-23/section_c_s2.json \
  data/experiments/core_merge_2026-10-23/section_c_s2-floors.json \
  data/experiments/core_merge_2026-10-23/section_c_s3.json \
  data/experiments/core_merge_2026-10-23/section_c_CI.json \
  data/experiments/core_merge_2026-10-23/section_c_CI-floors.json \
  data/experiments/core_merge_2026-10-23/section_c_CT.json \
  data/experiments/core_merge_2026-10-23/section_c_CT-floors.json \
  data/experiments/core_merge_2026-10-23/themes_CI.npz \
  data/experiments/core_merge_2026-10-23/themes_CT.npz \
  data/experiments/core_merge_2026-10-23/examples/CI_examples.md \
  data/experiments/core_merge_2026-10-23/examples/CT_examples.md
git diff --cached --quiet || git commit -m "Prompt 58 arms, counts and examples"

git add data/experiments/reviewer_notes/PROMPT_58.md
git diff --cached --quiet || git commit -m "Prompt 58, for the record"

git add docs/status/2026-10-23-core-merge.md docs/status/commit-2026-10-23-core-merge.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Merging by core gives the same theme count with more near-copies: for most themes the core is the membership"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "CT 98,817 themes against O50s 99,951 families, with 29 percent MORE non-nested near-copies."
echo "CI 183,091 themes, 5x the near-copies, median 1.0 groupings per theme."
echo "Median core share is 1.000 from 12 members to 799: for most themes the core IS the membership."
echo "All seven section C runs verified exactly against a brute-force loop on 2,000 themes."
echo "No ontology was built and nothing is adopted."
echo "No file was left out for size: the largest committed here is themes_CI.npz at about 17 MB."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
