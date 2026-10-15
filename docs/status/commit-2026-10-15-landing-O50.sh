#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Offline mode reproduces the pilot byte for byte and the O50 inputs 552 of 552" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add .gitignore scripts/export_landing.py tests/test_export_landing.py
git diff --cached --quiet || git commit -m "Landing export reads any build directory and takes real names from a TSV"

git add \
  data/experiments/naming_O50_2026-10-14/dedup/dd_build.py \
  data/experiments/naming_O50_2026-10-14/dedup/dd_build2.py \
  data/experiments/naming_O50_2026-10-14/dedup/dd_select.py \
  data/experiments/naming_O50_2026-10-14/dedup/dd_select2.py \
  data/experiments/naming_O50_2026-10-14/dedup/final_names_dedup1.json \
  data/experiments/naming_O50_2026-10-14/dedup/final_names_dedup1.tsv \
  data/experiments/naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.json \
  data/experiments/naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.tsv \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_groups.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b01.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b02.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b03.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b04.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b05.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b06.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot0_b07.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b01.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b02.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b03.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b04.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b05.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b06.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot1_b07.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b01.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b02.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b03.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b04.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b05.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b06.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup_slot2_b07.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup2_groups.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup2_slot0_b01.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup2_slot1_b01.json \
  data/experiments/naming_O50_2026-10-14/dedup/inputs/dedup2_slot2_b01.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b01.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b02.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b03.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b04.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b05.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b06.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot0_b07.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b01.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b02.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b03.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b04.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b05.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b06.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot1_b07.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b01.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b02.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b03.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b04.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b05.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b06.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup_slot2_b07.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup2_slot0_b01.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup2_slot1_b01.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/raw/dedup2_slot2_b01.out.json \
  data/experiments/naming_O50_2026-10-14/dedup/REPORT_dedup.md \
  data/experiments/naming_O50_2026-10-14/RUN_LOG.md
git diff --cached --quiet || git commit -m "The uniqueness pass on the lite names: 75 groups re-asked, 0 duplicates left"

git add \
  demo/preview-O50/landing.html
git diff --cached --quiet || git commit -m "Preview of O50 with its names: 4,576 of 4,602 named, demo/ontology.js untouched"

git add data/experiments/reviewer_notes/PROMPT_32.md data/experiments/reviewer_notes/PROMPT_33.md
git diff --cached --quiet || git commit -m "Prompts 32 and 33, for the record"

git add docs/status/2026-10-15-landing-O50.md docs/status/commit-2026-10-15-landing-O50.sh
git diff --cached --quiet || git commit -m "The preview is 104.6 MB and both example cards no longer hold on O50"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "demo/ontology.js was NOT replaced. The preview ontology.js is 104.6 MB, over the GitHub"
echo "file limit, so it is gitignored and regenerated; see docs/status/2026-10-15-landing-O50.md."
