#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "The large candidates die at the gate on support 0.005 against a floor of 0.025" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add \
  data/experiments/resolution_limit_2026-10-16/bins.tsv \
  data/experiments/resolution_limit_2026-10-16/code/resolution.py \
  data/experiments/resolution_limit_2026-10-16/report.txt \
  data/experiments/resolution_limit_2026-10-16/summary.json \
  docs/status/2026-10-16-resolution-limit.md \
  docs/status/commit-2026-10-16-resolution-limit.sh
git diff --cached --quiet || git commit -m "Above 40 pathways the scrambles never recur twice, so the pooled 10 plus floor is the limit"

git add data/experiments/reviewer_notes/PROMPT_41.md
git diff --cached --quiet || git commit -m "Prompt 41, for the record"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "READ-ONLY DIAGNOSTIC. No build changed. T is 39 on the solver ladder, unbounded on the full one."
