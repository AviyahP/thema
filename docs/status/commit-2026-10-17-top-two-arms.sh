#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Splitting the 10 plus stratum recovers 1,056 themes and 7.3 points of placement; adopted nothing" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/areas_rec2fix.py
git diff --cached --quiet || git commit -m "rec2fix takes its anchor bar and its giant rule as parameters, defaults unchanged"

git add scripts/top_two_arms.py scripts/top_two_arms_report.py tests/test_top_two_arms.py
git diff --cached --quiet || git commit -m "Clusterwise Jaccard over rebuilt dendrograms, and the two ways to build a top on O50s"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/B/dropped_themes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/B/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/B/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/B/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/areas_A_848items_200runs.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/areas_B_1330items_200runs.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/report.txt \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/stability.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/stability.tsv
git diff --cached --quiet || git commit -m "Arm A gives 47 roots and 97.5 percent placement; arm B gives 49 and fails its 3 to 3 stratum"

git add \
  data/experiments/top_two_arms_2026-10-17/A/areas.tsv \
  data/experiments/top_two_arms_2026-10-17/A/roots.tsv \
  data/experiments/top_two_arms_2026-10-17/A/small_roots.tsv \
  data/experiments/top_two_arms_2026-10-17/B/areas.tsv \
  data/experiments/top_two_arms_2026-10-17/B/roots.tsv \
  data/experiments/top_two_arms_2026-10-17/B/small_roots.tsv
git diff --cached --quiet || git commit -m "The reviewer folder for both tops: roots, small roots and areas with full member lists"

git add data/experiments/reviewer_notes/PROMPT_44.md
git diff --cached --quiet || git commit -m "Prompt 44, for the record"

git add docs/status/2026-10-17-top-two-arms.md docs/status/commit-2026-10-17-top-two-arms.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Stability rises with size, so arm B cuts the wrong end; arm A survives on the numbers ccode owns"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. Arm A passes both ccode criteria; the blind reading and C6 remain."
