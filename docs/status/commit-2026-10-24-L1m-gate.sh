#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Merging on members removes every duplicate theme and cuts redundancy below O50s, and the giants stay flat" > /dev/null

git add scripts/l1m_gate.py scripts/l1m_build.py scripts/tree_core_bars.py
git diff --cached --quiet || git commit -m "Prompt 65: the L1m gate, O50s procedure reused unchanged, plus light outputs and a seed list for the scramble trees"

git add \
  data/experiments/L1m_gate_2026-10-24/floors_l1m.json \
  data/experiments/L1m_gate_2026-10-24/gated.npz \
  data/experiments/L1m_gate_2026-10-24/report.json
git diff --cached --quiet || git commit -m "The solved floors for all 13 bands, the held-out confirmation, and the gated mask"

git add \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03003/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03003/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03004/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03004/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03005/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03005/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03006/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03006/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03007/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03007/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03008/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03008/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03009/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03009/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03010/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed03010/build.json
git diff --cached --quiet || git commit -m "L1m on calibration scramble seeds 3003 to 3010, light outputs"

git add \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04001/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04001/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04002/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04002/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04003/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04003/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04004/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04004/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04005/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04005/build.json \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04006/themes_light.npz \
  data/experiments/L1m_gate_2026-10-24/scramble/seed04006/build.json
git diff --cached --quiet || git commit -m "L1m on held-out scramble seeds 4001 to 4006, light outputs, read once"

git add data/experiments/reviewer_notes/PROMPT_65.md
git diff --cached --quiet || git commit -m "Prompt 65, for the record"

git add docs/status/2026-10-24-L1m-gate.md docs/status/commit-2026-10-24-L1m-gate.sh DECISIONS.md
git diff --cached --quiet || git commit -m "The calibrated gate replaces the provisional bar on L1m: floors solved per band and confirmed on held-out"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "O50s procedure reused, not reimplemented: O50S_STRATA, TARGET 0.008, RULE_OF_THREE 3.0,"
echo "solve_stratum, confirm_with, CAP_OVERALL 0.01, CAP_STRATUM 0.02, v04.gate and stratum_of."
echo "Two deliberate differences, both because L1m is a different population: all 13 bands are"
echo "solved because there is no earlier L1m calibration to freeze, and support is rounded to six"
echo "decimals on every side before comparison, as Material.rows does in O50s."
echo "Floors solved on seeds 3001 to 3010 only. The held-out seeds 4001 to 4006 are read ONCE."
echo "The reused solver was checked against an explicit loop on four bands."
echo "NOT COMMITTED: the scramble trees under scramble_trees, 348 MB, regenerable by"
echo "tree_core_bars.py --scramble-trees --seeds ... --trees-out ..."
echo "Both held-out caps HOLD: overall FDR 0.00528 against 0.01, worst band 0.01018 against 0.02."
echo "Small bands need far more recurrence than the provisional bar: 97 runs of 200 at 3 pathways,"
echo "against 10. From 10-19 up the floors equal O50s to six decimals, because 6/199 and 2/200 are"
echo "the lowest rungs of the ladder and both calibrations reach the target there."
echo "From 40 pathways up every floor is the rule of three bound: the scrambles are empty, so every"
echo "large theme that exists is admitted. 1600+ goes from 18 themes to 54."
echo "The gate keeps 43,867 against the bar 41,605, removing 16,371 small and admitting 18,633 large."
echo "Themes per pathway rise 102.6 to 365.8. DAG edges 161,869 to 676,623. Roots 617 to 4,164."
echo "Roots of 200 or more: 75 to 1,263. Every surviving 3-5 theme now has a parent, which is new."
echo "So the calibration is sound and the structure is worse: the provisional bar was capping the"
echo "variant cloud by accident. Nothing is adopted."
echo "Total committed here: about 1.2 MB. Largest file: a themes_light.npz at 76 KB."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
