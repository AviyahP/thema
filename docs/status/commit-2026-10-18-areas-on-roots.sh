#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "The containment bug is fixed and the root count does not move; adopted nothing" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/areas_on_roots.py tests/test_areas_on_roots.py
git diff --cached --quiet || git commit -m "Areas on the 261 O50s roots, giants kept as units, O50s left unchanged"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/area_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/areas_roots_261units_200runs.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/build.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/report.txt
git diff --cached --quiet || git commit -m "Twelve roots, all areas, every giant contained, placement 99.2 percent"

git add \
  data/experiments/areas_on_roots_2026-10-18/areas.tsv \
  data/experiments/areas_on_roots_2026-10-18/roots.tsv \
  data/experiments/areas_on_roots_2026-10-18/small_roots.tsv
git diff --cached --quiet || git commit -m "The reviewer folder: twelve roots, no small roots, 66 areas with full member lists"

git add data/experiments/reviewer_notes/PROMPT_46.md
git diff --cached --quiet || git commit -m "Prompt 46, for the record"

git add docs/status/2026-10-18-areas-on-roots.md docs/status/commit-2026-10-18-areas-on-roots.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Making the giants units gets every one of them contained, at the cost of a root holding 81 percent"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. 12 roots, all areas, every giant contained. The blind reading and C6 remain."
