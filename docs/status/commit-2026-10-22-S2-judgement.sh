#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "The sibling restriction costs almost nothing: S1 roots were an inheritance effect, not a merge effect" > /dev/null

git add \
  scripts/s2_vs_o50s_inputs.py \
  scripts/s2_duplication.py \
  scripts/s2_stability.py \
  scripts/s2_recall_ci.py \
  scripts/s2_sibling_auroc.py \
  scripts/s2_gene_coherence.py \
  scripts/s1_checks.py
git diff --cached --quiet || git commit -m "Prompt 55: the blind inputs where S2 and O50s differ, sections C E F G, and s1_checks carried forward"

git add \
  data/experiments/S2_vs_O50s_2026-10-22/PART1_NOTE.md \
  data/experiments/S2_vs_O50s_2026-10-22/part1_counts.json \
  data/experiments/S2_vs_O50s_2026-10-22/section_c.json \
  data/experiments/S2_vs_O50s_2026-10-22/section_f.json \
  data/experiments/S2_vs_O50s_2026-10-22/section_e_recall.json \
  data/experiments/S2_vs_O50s_2026-10-22/section_e_recall_ci.json \
  data/experiments/S2_vs_O50s_2026-10-22/section_e_auroc.json \
  data/experiments/S2_vs_O50s_2026-10-22/section_g.json
git diff --cached --quiet || git commit -m "Prompt 55 results: PART 1 counts and sections C, E, F and G"

git add \
  data/experiments/S2_vs_O50s_2026-10-22/read_roots/R_b01.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_roots/R_b02.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_roots/R_b03.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_roots/R_b04.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_roots/R_b05.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b01.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b02.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b03.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b04.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b05.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b06.md \
  data/experiments/S2_vs_O50s_2026-10-22/read_themes/T_b07.md \
  data/experiments/S2_vs_O50s_2026-10-22/intruder/I_b01.md \
  data/experiments/S2_vs_O50s_2026-10-22/intruder/I_b02.md \
  data/experiments/S2_vs_O50s_2026-10-22/intruder/I_b03.md \
  data/experiments/S2_vs_O50s_2026-10-22/intruder/I_b04.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b01.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b02.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b03.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b04.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b05.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b06.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b07.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b08.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b09.md \
  data/experiments/S2_vs_O50s_2026-10-22/small_inputs/S_b10.md
git diff --cached --quiet || git commit -m "Prompt 55 blind reading material: 207 roots, 294 themes, 122 intruder items, 174 small roots"

git add \
  data/experiments/S2_vs_O50s_2026-10-22/verdicts/INSTR_I.md \
  data/experiments/S2_vs_O50s_2026-10-22/verdicts/INSTR_RT.md \
  data/experiments/S2_vs_O50s_2026-10-22/verdicts/INSTR_S.md \
  data/experiments/S2_vs_O50s_2026-10-22/verdicts/SCORES.md \
  data/experiments/S2_vs_O50s_2026-10-22/verdicts/score_S2_vs_O50s.py \
  data/experiments/S2_vs_O50s_2026-10-22/verdicts/verdicts_S2_vs_O50s.json
git diff --cached --quiet || git commit -m "Prompt 55 reviewer verdict: S2 equivalent to O50s on every reading, not adopted"
git add data/experiments/reviewer_notes/PROMPT_55.md
git diff --cached --quiet || git commit -m "Prompt 55, for the record"

git add docs/status/2026-10-22-S2-vs-O50s-judgement.md docs/status/commit-2026-10-22-S2-judgement.sh DECISIONS.md
git diff --cached --quiet || git commit -m "S2 against O50s: no computed measure separates them; the readings are the remaining evidence"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "PART 1 complete: R 207, T 294, I 122, S 174. PART 2 complete: C, E, F and G."
echo "F worse direction O50s 0.5862 against S2 0.5817, difference minus 0.0045."
echo "E: 1 of 22 recall and precision cells has a difference CI excluding zero; all 4 AUROC CIs overlap."
echo "G: the builds are within 0.0015 in every band."
echo "REVIEWER VERDICT: S2 equivalent to O50s on every reading. Not adopted. O50s stays the baseline."
echo "The KEY file is deliberately NOT committed, as the prompt requires."
echo "LEFT OUT as regenerable caches: side_1-100.npz and side_101-200.npz, about 9 MB each."
