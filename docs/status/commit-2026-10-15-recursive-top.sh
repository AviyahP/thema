#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add src/thema/ontology/universe.py src/thema/naming_c1.py \
  scripts/recursive_top_O50.py scripts/recursive_top_report.py tests/test_recursive_top.py
git diff --cached --quiet || git commit -m "THEMA on its own themes: units, level 2 and the combined DAG"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/area_edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/area_members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/areas.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/levels.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/o50_nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_O50_rec/report.txt
git diff --cached --quiet || git commit -m "The recursive top on O50: 661 units, 470 areas, 30 roots"

git add DECISIONS.md docs/status/2026-10-15-recursive-top-O50.md data/experiments/reviewer_notes/PROMPT_34.md docs/status/commit-2026-10-15-recursive-top.sh
git diff --cached --quiet || git commit -m "Recursive top: 476 of 476 re-parented and summaries 85 to 93 percent, but held-out FDR fails"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ADOPTED NOTHING. Held-out FDR breaches two strata; C6 and the intuitiveness call are open."
