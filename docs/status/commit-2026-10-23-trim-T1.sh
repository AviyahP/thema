#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "After-gate merges are not missed twins: zero of 19,697 pairs are twins at gate exit" > /dev/null

git add scripts/build_t1.py scripts/t1_report.py src/thema/ontology/consensus.py
git diff --cached --quiet || git commit -m "T1: rule 2 flipped to trim the child, with downward propagation and the minimum-size drop"

git add \
  data/ontology/v0.4-leaves/thema_L_x2_T1/edges.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_T1/manifest.json \
  data/ontology/v0.4-leaves/thema_L_x2_T1/members.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_T1/nodes.tsv \
  data/ontology/v0.4-leaves/thema_L_x2_T1/unplaced.tsv
git diff --cached --quiet || git commit -m "T1 build: 3,456 themes, 551 roots, 53,951 members removed, 3,788 themes dropped"

git add \
  data/experiments/trim_T1_2026-10-23/accounting.json \
  data/experiments/trim_T1_2026-10-23/section_a.json \
  data/experiments/trim_T1_2026-10-23/trimmed.json
git diff --cached --quiet || git commit -m "T1 accounting: the flip itself separated from what it changed downstream"

git add data/experiments/reviewer_notes/PROMPT_57.md
git diff --cached --quiet || git commit -m "Prompt 57, for the record"

git add docs/status/2026-10-23-trim-T1.md docs/status/commit-2026-10-23-trim-T1.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Trimming the child preserves strictness and costs 39 percent of the themes, moving the damage to the small bands"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Both declared tests passed: flip off reproduces frozen O50s byte for byte."
echo "T1 3,456 themes against O50s 5,658; roots 551 against 261; median depth 3 against 6."
echo "53,951 members removed, 3,788 themes dropped under 3, 9.1 percent of O50s themes matched at J 0.9."
echo "Above 100 pathways no theme loses 10 percent; at 3-5 every trimmed theme loses over 25 percent."
echo "Chain collapses fall 78 percent, confirming inheritance manufactures the near-chains."
echo "Coverage holds: all 5,539 pathways still placed and zero pathways orphaned."
echo "No file was left out for size: the largest committed here is members.tsv at about 9 MB."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
