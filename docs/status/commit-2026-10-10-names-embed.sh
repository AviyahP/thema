#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git add .gitignore
git diff --cached --quiet || git commit -m "Ignore every answer key by name, not only the tsv one"

git add src/thema/embed.py tests/test_embed_names.py scripts/embed_theme_names.py
git diff --cached --quiet || git commit -m "Embed theme names: the query encoder, and the name as a title with an empty abstract"

git add data/experiments/reviewer_eval_x2_2026-10-09/names_test/PREREG_names_test.md data/experiments/reviewer_eval_x2_2026-10-09/names_test/theme_names_c85.tsv data/experiments/reviewer_eval_x2_2026-10-09/REPORT_twin_merge_decision_record.md
git diff --cached --quiet || git commit -m "Record the names-test pre-registration and the accepted sibling merge rule"

git add data/experiments/reviewer_eval_x2_2026-10-09/names_test/name_vecs_article.npy data/experiments/reviewer_eval_x2_2026-10-09/names_test/name_vecs_query.npy data/experiments/reviewer_eval_x2_2026-10-09/names_test/name_keys.txt data/experiments/reviewer_eval_x2_2026-10-09/names_test/name_vecs_manifest.json
git diff --cached --quiet || git commit -m "Name vectors for the reviewer: 8,251 by 768 twice, analysis input only"

git add CLAUDE.md DECISIONS.md docs/status/commit-2026-10-10-names-embed.sh
git diff --cached --quiet || git commit -m "Sibling merge rule accepted and NOT run; names test in progress"

git push
