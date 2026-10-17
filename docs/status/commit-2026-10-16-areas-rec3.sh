#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Areas fail on 63 roots against 60, and they fail because the giant rule was applied" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/areas_rec3.py tests/test_areas_rec3.py
git diff --cached --quiet || git commit -m "The areas pass as one operator: Ward continued from fixed clusters, weighted by pathway count"

git add scripts/areas_rec3_report.py
git diff --cached --quiet || git commit -m "Report both arms against O50 and against rec2fix with its giants in"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/area_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/areas.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/closure.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/giants.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/items.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/E/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/area_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/areas.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/closure.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/giants.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/items.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/W/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/build.txt \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/null_diagnostic.txt \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec3/report.txt
git diff --cached --quiet || git commit -m "rec3: the size-weighted arm admits nothing, the equal-weight arm gives 317 areas and 47 roots"

git add data/experiments/reviewer_notes/PROMPT_38.md
git diff --cached --quiet || git commit -m "Prompt 38, for the record"

git add \
  data/experiments/giants_reading_2026-10-15/G1_readings.json \
  data/experiments/giants_reading_2026-10-15/G2_judgements.json \
  data/experiments/giants_reading_2026-10-15/PREREG_giants.md \
  data/experiments/giants_reading_2026-10-15/RESULT_giants.tsv \
  data/experiments/giants_reading_2026-10-15/code/build.py \
  data/experiments/giants_reading_2026-10-15/code/o50_roots_and_immune.py \
  data/experiments/giants_reading_2026-10-15/code/score.py \
  data/experiments/giants_reading_2026-10-15/g2_batches/G2_b1.md \
  data/experiments/giants_reading_2026-10-15/g2_batches/G2_b2.md \
  data/experiments/giants_reading_2026-10-15/g2_batches/G2_b3.md \
  data/experiments/giants_reading_2026-10-15/g2_batches/G2_b4.md \
  data/experiments/giants_reading_2026-10-15/giants_index.json \
  data/experiments/giants_reading_2026-10-15/label_inputs/G01.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G02.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G03.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G04.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G05.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G06.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G07.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G08.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G09.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G10.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G11.md \
  data/experiments/giants_reading_2026-10-15/label_inputs/G12.md \
  data/experiments/top_compare_2026-10-16/PREREG.md \
  data/experiments/top_compare_2026-10-16/code/build.py \
  data/experiments/top_compare_2026-10-16/code/score.py \
  data/experiments/top_compare_2026-10-16/inputs/testA.md \
  data/experiments/top_compare_2026-10-16/inputs/testB.md \
  data/experiments/top_compare_2026-10-16/judgements.json \
  data/experiments/top_compare_2026-10-16/roots_options.json \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/facet_or_sub.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/giants_read.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/near_containment_impact.py \
  data/experiments/areas_rec2_giantdrop_2026-10-15/code/roots61.py
git diff --cached --quiet || git commit -m "Reviewer material: the giants reading, the top-level comparison and four later audit scripts"

git add docs/status/2026-10-16-areas-rec3.md docs/status/commit-2026-10-16-areas-rec3.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Size weighting makes the null recur as strongly as the data, so no floor exists and nothing is adopted"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. Arm W admits no candidate at all. O50 stays as it is."
