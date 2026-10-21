#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "The threshold must flip at ten pathways, but a looser gate is the wrong lever for the small roots" > /dev/null
git cat-file -e HEAD:data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256

git add scripts/m_vs_o50s_inputs.py tests/test_m_vs_o50s_inputs.py
git diff --cached --quiet || git commit -m "Part A: blind reading inputs and two descriptive measures for M against O50s"

git add \
  data/experiments/m_vs_o50s_2026-10-19/index.json \
  data/experiments/m_vs_o50s_2026-10-19/measures.json \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b01.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b02.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b03.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b04.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b05.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b06.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b07.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b08.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b09.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b10.md \
  data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b11.md \
  data/experiments/m_vs_o50s_2026-10-19/redundancy.tsv \
  data/experiments/m_vs_o50s_2026-10-19/support.tsv
git diff --cached --quiet || git commit -m "Part A material: 120 blind items in 11 batches, redundancy and support"

git add data/experiments/reviewer_notes/PROMPT_48_49.md
git diff --cached --quiet || git commit -m "Prompts 48 and 49, for the record"

git add docs/status/2026-10-19-m-vs-o50s-inputs.md docs/status/commit-2026-10-20-prompts-48-49.sh DECISIONS.md
git diff --cached --quiet || git commit -m "M unique themes are less redundant than O50s but more weakly supported; prompt 49 withdrawn"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "PART A ONLY. Prompt 49 withdrawn before building. The blind reading decides."
