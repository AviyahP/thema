#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Restructured S1: the themes survive within 4 percent but roots go from 261 to about 1,000 and depth falls" > /dev/null

git add scripts/build_s2.py scripts/s2_report.py src/thema/ontology/consensus.py src/thema/ontology/repair.py
git diff --cached --quiet || git commit -m "S2: the same-theme merge restricted to siblings, as an optional restriction on consensus rule 3 and the stale merge"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_S2/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S2/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_S2/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S2/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S2/s2_construction.json \
  data/ontology/v0.4-leaves/thema_L_x2_S2/unplaced.tsv
git diff --cached --quiet || git commit -m "S2 build: 5,646 themes, 270 roots, 2,018 of O50s supersessions became coexist"

git add data/experiments/reviewer_notes/PROMPT_54.md
git diff --cached --quiet || git commit -m "Prompt 54 and its amendment, for the record"

git add docs/status/2026-10-22-S2-sibling-restricted.md docs/status/commit-2026-10-22-S2.sh DECISIONS.md
git diff --cached --quiet || git commit -m "The sibling restriction costs almost nothing: S1 roots were an inheritance effect, not a merge effect"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "S2 5,646 themes 270 roots; O50s 5,658 and 261; S1p 5,815 and 991."
echo "Both declared tests passed, including byte-for-byte frozen O50s with the restriction off."
echo "Only 2,018 of 19,531 O50s supersessions were non-sibling against the gated DAG: 10.3 percent."
echo "The 76 superseded parents do NOT come back: 1 of 76 in S2, 3 of 76 in S1p."
echo "Sections C, F, G and reviewer material were not run, as the prompt says."
echo "No file was left out for size: the largest committed here is members.tsv at about 11 MB."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
