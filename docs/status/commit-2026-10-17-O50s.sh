#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Above 40 pathways the scrambles never recur twice, so the pooled 10 plus floor is the limit" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add src/thema/ontology/v04.py scripts/build_trees_10770.py
git diff --cached --quiet || git commit -m "The gate takes its stratification as a parameter, and the tree builder takes a seed list"

git add scripts/o50s_build.py scripts/o50s_report.py tests/test_o50s.py
git diff --cached --quiet || git commit -m "O50s: eight doubling strata above 10, solved with a rule-of-three bound, proved against the frozen O50"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/floors_o50s.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/report.txt \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s/verify.txt
git diff --cached --quiet || git commit -m "O50s: 5,658 themes, 100 to 199 up six fold, placement 85.3 to 92.6 percent"

git add \
  data/experiments/O50s_review_2026-10-17/PREREG_O50s_large.md \
  data/experiments/O50s_review_2026-10-17/code/build_review.py \
  data/experiments/O50s_review_2026-10-17/intruder_inputs/I_b01.md \
  data/experiments/O50s_review_2026-10-17/intruder_inputs/I_b02.md \
  data/experiments/O50s_review_2026-10-17/intruder_inputs/I_b03.md \
  data/experiments/O50s_review_2026-10-17/large_themes.tsv \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b01.md \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b02.md \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b03.md \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b04.md \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b05.md \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b06.md \
  data/experiments/O50s_review_2026-10-17/read_inputs/R_b07.md \
  data/experiments/O50s_review_2026-10-17/review_index.json
git diff --cached --quiet || git commit -m "The reviewer folder for the 87 large O50s themes, key file excluded"

git add data/experiments/reviewer_notes/PROMPT_42.md
git diff --cached --quiet || git commit -m "Prompt 42, ON HOLD and not run, for the record"

git add data/experiments/reviewer_notes/PROMPT_43.md
git diff --cached --quiet || git commit -m "Prompt 43, for the record"

git add docs/status/2026-10-17-O50s-strata.md docs/status/commit-2026-10-17-O50s.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Splitting the 10 plus stratum recovers 1,056 themes and 7.3 points of placement; adopted nothing"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTS NOTHING. Three criteria pass; the reviewer reading, the intruder test and Aviyah remain."
