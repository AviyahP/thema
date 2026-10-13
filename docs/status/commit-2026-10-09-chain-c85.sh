#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git add src/thema/ontology/repair.py tests/ontology/test_repair.py
git diff --cached --quiet || git commit -m "Chain collapse gains a survivor rule, keep-the-parent still the default"

git add scripts/leaves_build.py scripts/chain_c85_report.py
git diff --cached --quiet || git commit -m "Build takes --survivor and records which node of each collapsed pair died"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_c85/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_c85/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_c85/match_to_baseline.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_c85/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_c85/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_c85/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_x2_c85/report.txt \
  data/ontology/v0.4-leaves/thema_L_x2_c85/unplaced.tsv
git diff --cached --quiet || git commit -m "thema_L_x2_c85: the 0.85 arm on the baseline material, 8,251 themes"

git add \
  data/ontology/v0.4-leaves/thema_L_repair_c85/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_repair_c85/manifest.json \
  data/ontology/v0.4-leaves/thema_L_repair_c85/members.tsv \
  data/ontology/v0.4-leaves/thema_L_repair_c85/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_repair_c85/repair_map.json \
  data/ontology/v0.4-leaves/thema_L_repair_c85/unplaced.tsv
git diff --cached --quiet || git commit -m "thema_L_repair_c85: the same rule on the independent build, for criterion d"

git add .gitignore CLAUDE.md DECISIONS.md docs/status/2026-10-09-chain-c85.md docs/status/commit-2026-10-09-chain-c85.sh
git diff --cached --quiet || git commit -m "Chain collapse 0.85 with a support survivor fails three of five criteria, not adopted"

git push
