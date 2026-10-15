#!/bin/zsh
set -euo pipefail
cd ~/code/thema

START=$(git rev-parse --abbrev-ref HEAD)

git log --format=%s | grep -cFx "c85 is the working version; the sibling merge rule is superseded and the naming run is held" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-c85-2026-10-10/CHECKSUMS.sha256

git switch -c overlap-2026-10

git add src/thema/ontology/repair.py src/thema/ontology/v04.py tests/ontology/test_repair.py
git diff --cached --quiet || git commit -m "One same-theme cutoff for consensus and the stale pass, and a joint fixed point"

git add scripts/leaves_build.py scripts/overlap_arm_report.py
git diff --cached --quiet || git commit -m "Build takes --theta-same and --joint-fixed-point, both recorded, both defaulted off"

git add \
  data/ontology/v0.4-leaves/thema_L_repair_O50/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_repair_O50/manifest.json \
  data/ontology/v0.4-leaves/thema_L_repair_O50/members.tsv \
  data/ontology/v0.4-leaves/thema_L_repair_O50/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_repair_O50/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_repair_O50/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50/O50_new_themes.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50/report.txt \
  data/ontology/v0.4-leaves/thema_L_x2_O50/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O60/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O60/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O60/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O60/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O60/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_x2_O60/unplaced.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O70/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O70/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O70/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O70/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O70/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_x2_O70/unplaced.tsv
git diff --cached --quiet || git commit -m "The four overlap builds: O70 control, O50 arm, O60 sensitivity, O50 on the repair universe"

git add DECISIONS.md docs/status/2026-10-12-overlap-arm.md docs/status/commit-2026-10-12-overlap-arm.sh
git diff --cached --quiet || git commit -m "Overlap arm: C1 and C3 pass, C2 fails on one pathway, giants 10 to 4, nothing adopted"

git push origin overlap-2026-10

git switch $START

echo "branch overlap-2026-10 pushed; back on $START"
echo "NOT MERGED. C4 and C5 are the reviewer. C2 failed. Nothing is adopted."
