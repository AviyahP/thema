#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Areas fail on size and children: 2618 pathways and 181 children. No third try." > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/areas_rec2fix.py tests/test_areas_rec2fix.py
git diff --cached --quiet || git commit -m "Union sets everywhere and one structure over areas, anchors and units"

git add scripts/areas_rec2fix_report.py
git diff --cached --quiet || git commit -m "Report rec2fix beside rec2, and measure why the giant rule costs 21 roots"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/anchors.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/area_edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/area_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/areas.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/closure.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/giants.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/o50_nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/report.txt
git diff --cached --quiet || git commit -m "The rec2fix build: 63 roots, 8 giants, children 18, every pathway under a 201 to 1000 node"

git add data/experiments/reviewer_notes/PROMPT_37.md
git diff --cached --quiet || git commit -m "Prompt 37, for the record"

git add \
  data/experiments/areas_rec2_giantdrop_2026-10-15/PREREG_C6.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/roots.tsv \
  data/experiments/areas_rec2_giantdrop_2026-10-15/root_labels.json \
  data/experiments/areas_rec2_giantdrop_2026-10-15/ROOTS_for_Aviyah.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/C6_judgements.json \
  data/experiments/areas_rec2_giantdrop_2026-10-15/C6_misses.tsv \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/build_c6.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/build_roots.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/facets_mito.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/o50_mostly_inside.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/pair_children.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/root_nesting.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/rule_audit.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/rule_audit2.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/rule_audit3.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/score_c6.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/stray_audit.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R01.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R02.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R03.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R04.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R05.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R06.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R07.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R08.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R09.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R10.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R11.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R12.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R13.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R14.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R15.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R16.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R17.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R18.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R19.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R20.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R21.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R22.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R23.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R24.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R25.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R26.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R27.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R28.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R29.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R30.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R31.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R32.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R33.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R34.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R35.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R36.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R37.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R38.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R39.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R40.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R41.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R42.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R43.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R44.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R45.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R46.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R47.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R48.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R49.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R50.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R51.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R52.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R53.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R54.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R55.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R56.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R57.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R58.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R59.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R60.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R61.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R62.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/inputs/R63.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b01.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b02.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b03.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b04.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b05.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b06.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b07.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b08.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/batches/L_b09.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b01.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b02.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b03.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b04.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b05.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b06.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b07.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b08.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b09.md \
  data/experiments/areas_rec2_giantdrop_2026-10-15/c6_batches/C6_b10.md
git diff --cached --quiet || git commit -m "Reviewer material: the giant-drop roots, the C6 pre-registration and its judgements"

git add docs/status/2026-10-15-areas-rec2fix.md docs/status/commit-2026-10-15-areas-rec2fix.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Areas fail on 63 roots against 60, and they fail because the giant rule was applied"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. Four of five criteria pass. The working view is O50 without giants."
