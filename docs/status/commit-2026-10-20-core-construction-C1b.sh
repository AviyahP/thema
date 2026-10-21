#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "M unique themes are less redundant than O50s but more weakly supported; prompt 49 withdrawn" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/core_construction_c1b.py scripts/core_construction_c1b_report.py tests/test_core_construction_c1b.py
git diff --cached --quiet || git commit -m "C1b: the core-based construction, per-stratum copy matching, the mutual core rule and its report"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_C1b/c1b.json \
  data/ontology/v0.4-leaves/thema_L_x2_C1b/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_C1b/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_C1b/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_C1b/unplaced.tsv
git diff --cached --quiet || git commit -m "C1b build: 73,484 themes, 1,066 roots, 1,362,498 edges; members.tsv and themes_detail.tsv omitted over the size limit"

git add \
  data/experiments/core_construction_C1b_2026-10-20/p_table.json \
  data/experiments/core_construction_C1b_2026-10-20/p_table.tsv \
  data/experiments/core_construction_C1b_2026-10-20/roots.tsv
git diff --cached --quiet || git commit -m "C1b reviewer tables: the p table and the roots with inclusion and core flags"

git add \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b01.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b02.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b03.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b04.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b05.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b06.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b07.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b08.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b09.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b10.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b11.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b12.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b13.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b14.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b15.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b16.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b17.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b18.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b19.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b20.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b21.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b22.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b23.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b24.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b25.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b26.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b27.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b28.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b29.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b30.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b31.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b32.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b33.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b34.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b35.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b36.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b37.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b38.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b39.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b40.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b41.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b42.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b43.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b44.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b45.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b46.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b47.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b48.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b49.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b50.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b51.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b52.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b53.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b54.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b55.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b56.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b57.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b58.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b59.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b60.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b61.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b62.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b63.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b64.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b65.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b66.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b67.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b68.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b69.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b70.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b71.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b72.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b73.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b74.md \
  data/experiments/core_construction_C1b_2026-10-20/read_roots/b75.md
git diff --cached --quiet || git commit -m "C1b reading material R: 300 roots in 75 batches"

git add \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b01.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b02.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b03.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b04.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b05.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b06.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b07.md \
  data/experiments/core_construction_C1b_2026-10-20/read_themes/b08.md
git diff --cached --quiet || git commit -m "C1b reading material T: 227 pooled non-root themes in 8 batches"

git add data/experiments/reviewer_notes/PROMPT_50.md data/experiments/reviewer_notes/PROMPT_50_AMENDMENT.md
git diff --cached --quiet || git commit -m "Prompt 50 and its amendment, for the record"

git add docs/status/2026-10-20-core-construction-C1b.md docs/status/commit-2026-10-20-core-construction-C1b.sh DECISIONS.md
git diff --cached --quiet || git commit -m "C1b is not better than O50s: 1,066 roots against 261, and p collapses to 0.1 above 20 pathways"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "C1b ANSWERED NO. Criterion 2 fails: 1,066 roots against the required under 261. O50s stays."
echo "Omitted over 50 MB: thema_L_x2_C1b/members.tsv, thema_L_x2_C1b/themes_detail.tsv, the reviewer themes.tsv, and the sides and themes caches."
echo "No KEY_DO_NOT_SHARE file is listed, and the KEY is gitignored as well."
