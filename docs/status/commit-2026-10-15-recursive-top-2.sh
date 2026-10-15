#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "104.6 MB to 12.8 MB, 84 ms to parse, no overflow at 360 px in headless Chrome" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/recursive_top_O50_rec2.py tests/test_recursive_top2.py
git diff --cached --quiet || git commit -m "Areas second try: six anchors, the cutoff measured on pathways, and twenty calibration seeds"

git add scripts/recursive_top_report2.py
git diff --cached --quiet || git commit -m "Report every rec2 figure beside rec, with both children attributions side by side"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/anchors.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/area_edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/area_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/areas.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/o50_nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/report.txt
git diff --cached --quiet || git commit -m "The rec2 build: 42 roots, 343 areas, held-out FDR 0.00429, largest area 2618 pathways"

git add data/experiments/reviewer_notes/PROMPT_36.md
git diff --cached --quiet || git commit -m "Prompt 36, for the record"

git add \
  data/experiments/naming_O50_2026-10-14/style/PREREG_style.md \
  data/experiments/naming_O50_2026-10-14/style/REPORT_style.md \
  data/experiments/naming_O50_2026-10-14/style/H1_pairs_for_Aviyah.md \
  data/experiments/naming_O50_2026-10-14/style/new_names.json \
  data/experiments/naming_O50_2026-10-14/style/scores_style.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b01.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b02.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b03.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b04.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b05.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b06.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b07.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b08.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b01.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b02.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b03.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b04.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b05.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b06.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b07.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b08.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_01.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_02.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_03.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_04.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_05.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_06.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_07.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E1_08.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_01.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_02.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_03.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_04.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_05.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_06.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_07.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/E2_08.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/P1_01.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/P1_02.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/P1_03.out.json \
  data/experiments/naming_O50_2026-10-14/style/evalout/P1_04.out.json
git diff --cached --quiet || git commit -m "Reviewer style material, for the record"

git add docs/status/2026-10-15-recursive-top-2.md docs/status/commit-2026-10-15-recursive-top-2.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Areas fail on size and children: 2618 pathways and 181 children. No third try."

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. Four criteria pass, two fail. The working view is O50 with the giants dropped."
