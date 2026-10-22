#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "O50s merges act mostly on unrelated pairs: consensus 54 percent unrelated, chain collapse discards the parent 72 percent of the time" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50s-2026-10-22/CHECKSUMS.sha256

git add scripts/restructure_s1.py scripts/restructure_s1_report.py
git diff --cached --quiet || git commit -m "Restructured O50s: DAG first, then the sibling rule on real siblings and the chain rule on real parent-child pairs"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_S1p/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S1p/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_S1p/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S1p/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S1p/unplaced.tsv
git diff --cached --quiet || git commit -m "S1p build: parent always survives, 5,815 themes, 991 roots, 5 rounds"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_S1s/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S1s/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_S1s/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S1s/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_S1s/unplaced.tsv
git diff --cached --quiet || git commit -m "S1s build: higher support survives, 5,878 themes, 1,017 roots, 5 rounds"

git add data/experiments/reviewer_notes/PROMPT_53.md
git diff --cached --quiet || git commit -m "Prompt 53, for the record"

git add docs/status/2026-10-22-restructured-S1.md docs/status/commit-2026-10-22-restructured-S1.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Restructured S1: the themes survive within 4 percent but roots go from 261 to about 1,000 and depth falls"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "S1p 5,815 themes 991 roots; S1s 5,878 themes 1,017 roots; O50s 5,658 themes 261 roots."
echo "Both declared tests passed, including byte-for-byte reproduction of frozen O50s with consensus restored."
echo "SECTIONS A-B ONLY. C-G deferred: the full estimate was about 7 h against a 5 h ceiling."
echo "No reviewer material: the prompt gates it on 600 roots or fewer and both arms exceed that."
echo "No file was left out for size: the largest committed here is members.tsv at about 11 MB."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
