#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Size weighting makes the null recur as strongly as the data, so no floor exists and nothing is adopted" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add \
  data/experiments/consensus_fate_2026-10-16/code/fate.py \
  data/experiments/consensus_fate_2026-10-16/fate.tsv \
  data/experiments/consensus_fate_2026-10-16/report.txt \
  data/experiments/consensus_fate_2026-10-16/step4_areas.tsv \
  data/experiments/consensus_fate_2026-10-16/step4_groups.tsv \
  data/experiments/consensus_fate_2026-10-16/summary.json \
  docs/status/2026-10-16-consensus-fate.md \
  docs/status/commit-2026-10-16-consensus-fate.sh
git diff --cached --quiet || git commit -m "The large candidates die at the gate on support 0.005 against a floor of 0.025"

git add data/experiments/reviewer_notes/PROMPT_40.md
git diff --cached --quiet || git commit -m "Prompt 40, for the record"

git add data/experiments/reviewer_notes/REVIEWER_LOG_2026-10-12_to_16.md
git diff --cached --quiet || git commit -m "Reviewer log, 12 to 16 Oct"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "READ-ONLY DIAGNOSTIC. No build changed. Large groupings recur once in 200 subsamples."
