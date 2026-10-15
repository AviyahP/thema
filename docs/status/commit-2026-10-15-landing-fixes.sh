#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "The preview is 104.6 MB and both example cards no longer hold on O50" > /dev/null

git add .gitignore scripts/export_landing.py tests/test_export_landing.py
git diff --cached --quiet || git commit -m "Landing export: deduplicated payload, a deterministic tie-break, and two honest defaults"

git add demo/landing.html
git diff --cached --quiet || git commit -m "The page declares a charset and a viewport, reads either payload shape, and marks edited names"

git add scripts/card_candidates.py docs/status/2026-10-15-card-candidates.md
git diff --cached --quiet || git commit -m "Example-card candidates on O50: 3,114 and 3,896 themes qualify, no card changed"

git add \
  demo/preview-O50/landing.html \
  demo/preview-O50/ontology.js
git diff --cached --quiet || git commit -m "O50 preview at 12.8 MB: deduplicated payload, deduplicated names, one hand-edited name"

git add \
  data/experiments/naming_O50_2026-10-14/name_overrides.tsv \
  data/experiments/naming_O50_2026-10-14/roots_without_giants_O50.tsv \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_01.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_02.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_03.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_04.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_05.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_06.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_07.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E1_08.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_01.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_02.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_03.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_04.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_05.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_06.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_07.json \
  data/experiments/naming_O50_2026-10-14/style/eval/E2_08.json \
  data/experiments/naming_O50_2026-10-14/style/eval/P1_01.json \
  data/experiments/naming_O50_2026-10-14/style/eval/P1_02.json \
  data/experiments/naming_O50_2026-10-14/style/eval/P1_03.json \
  data/experiments/naming_O50_2026-10-14/style/eval/P1_04.json \
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
  data/experiments/naming_O50_2026-10-14/style/evalout/P1_04.out.json \
  data/experiments/naming_O50_2026-10-14/style/H1_pairs_for_Aviyah.md \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b01.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b02.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b03.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b04.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b05.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b06.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b07.json \
  data/experiments/naming_O50_2026-10-14/style/inputs/style_b08.json \
  data/experiments/naming_O50_2026-10-14/style/new_names.json \
  data/experiments/naming_O50_2026-10-14/style/PREREG_style.md \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b01.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b02.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b03.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b04.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b05.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b06.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b07.out.json \
  data/experiments/naming_O50_2026-10-14/style/raw/style_b08.out.json \
  data/experiments/naming_O50_2026-10-14/style/REPORT_style.md \
  data/experiments/naming_O50_2026-10-14/style/scores_style.json \
  data/experiments/naming_O50_2026-10-14/style/spec/N3_style.md \
  data/experiments/naming_O50_2026-10-14/style/spec/P1_preference.md \
  data/experiments/naming_O50_2026-10-14/style/st_build.py \
  data/experiments/naming_O50_2026-10-14/style/st_eval_build.py \
  data/experiments/naming_O50_2026-10-14/style/st_score.py \
  data/experiments/reviewer_notes/PROMPT_35.md
git diff --cached --quiet || git commit -m "Reviewer material: the name override, the root list, and the style test"

git add docs/status/2026-10-15-landing-fixes.md docs/status/commit-2026-10-15-landing-fixes.sh
git diff --cached --quiet || git commit -m "104.6 MB to 12.8 MB, 84 ms to parse, no overflow at 360 px in headless Chrome"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "No card was changed. The candidates are in docs/status/2026-10-15-card-candidates.md."
