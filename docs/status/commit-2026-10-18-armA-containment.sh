#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Stability rises with size, so arm B cuts the wrong end; arm A survives on the numbers ccode owns" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/arm_a_containment.py tests/test_arm_a_containment.py
git diff --cached --quiet || git commit -m "Arm A omitted the O50s giants, so five anchors had no possible parent"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A1/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A1/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A1/view.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A2/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A2/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A2/propagated_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_top/A2/view.json
git diff --cached --quiet || git commit -m "A1 strict at 47 roots with five giants replacing five anchors; A2 at 41 for 22 invented memberships"

git add data/experiments/top_two_arms_2026-10-17/A1/roots.tsv
git diff --cached --quiet || git commit -m "The reviewer file for A1: ten of the 47 roots differ from arm A"

git add data/experiments/reviewer_notes/PROMPT_45.md
git diff --cached --quiet || git commit -m "Prompt 45, for the record"

git add docs/status/2026-10-18-armA-containment.md docs/status/commit-2026-10-18-armA-containment.sh DECISIONS.md
git diff --cached --quiet || git commit -m "The containment bug is fixed and the root count does not move; adopted nothing"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. A1 has 47 roots, five of them now O50s giants. Ten roots differ from arm A."
