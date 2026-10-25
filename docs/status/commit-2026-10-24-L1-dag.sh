#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Mid-sized L1 themes are unions of unrelated blocks and the giants are not: set_3 contains set_6 exactly" > /dev/null

git add scripts/l1_dag.py
git diff --cached --quiet || git commit -m "Prompt 63: the strict containment DAG over L1 themes, with an exact transitive reduction"

git add \
  data/experiments/L1_2026-10-24/dag/dag.npz \
  data/experiments/L1_2026-10-24/dag/dag.json
git diff --cached --quiet || git commit -m "The DAG: 388,287 edges from 5,541,622 ancestor pairs, 594 roots, and the tolerance pairs"

git add \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_01.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_02.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_03.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_04.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_05.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_06.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_07.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_08.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_09.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_10.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_11.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_12.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_13.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_14.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_15.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_16.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_17.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_18.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_19.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_20.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_21.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_22.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_23.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_24.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_25.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_26.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_27.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_28.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_29.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_30.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_31.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_32.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_33.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_34.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_35.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_36.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_37.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_38.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_39.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_40.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_41.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_42.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_43.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_44.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_45.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_46.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_47.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_48.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_49.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_50.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_51.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_52.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_53.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_54.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_55.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_56.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_57.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_58.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_59.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_60.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_61.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_62.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_63.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_64.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_65.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_66.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_67.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_68.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_69.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_70.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_71.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_72.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_73.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_74.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_75.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_76.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_77.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_78.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_79.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_80.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_81.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_82.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_83.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_84.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_85.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_86.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_87.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_88.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_89.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_90.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_91.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_92.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_93.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_94.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_95.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_96.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_97.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_98.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_99.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_100.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_101.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_102.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_103.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_104.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_105.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_106.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_107.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_108.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_109.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_110.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_111.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_112.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_113.md \
  data/experiments/L1_2026-10-24/dag/read_roots/batch_114.md
git diff --cached --quiet || git commit -m "The 114 blind reading batches for every root of 50 or more pathways"

git add data/experiments/reviewer_notes/PROMPT_63.md
git diff --cached --quiet || git commit -m "Prompt 63, for the record"

git add docs/status/2026-10-24-L1-dag.md docs/status/commit-2026-10-24-L1-dag.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Three pathways separate the seven giants from a two level hierarchy: strict containment cannot see it"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "52,001 themes, 388,287 edges, 594 roots, 91.16 percent multi parent, levels 16 median per pathway."
echo "All seven large7 sets match an L1 theme at J 0.90 or better and all seven are roots with NO parent."
echo "set_6 is 99.56 percent inside set_3, missing 5 pathways. set_7 is 99.65 percent inside set_4,"
echo "missing 3. So strict containment cannot express the hierarchy prompt 62 measured."
echo "555,728 of the 777,123 near miss pairs miss by exactly ONE pathway, across 26,899 children."
echo "A 90 percent tolerance would give 418 of 594 roots a parent and empty the top completely:"
echo "100 percent of 400-799 roots, 99 percent of 800-1599, 83 percent of 1600+. One pathway alone"
echo "would still reparent 218 roots, 20 of them above 800."
echo "17,433 of 52,001 themes repeat another theme membership exactly: only 34,568 distinct sets."
echo "The merge rule compares cores, so same membership different core is never merged."
echo "18.5 percent of edges are near chains, child holding 85 percent or more of its parent."
echo "Every pathway is placed and every pathway sits in a theme of at least 2,021 members."
echo "Ancestors and immediate parents verified against explicit set loops on 300 themes, all identical."
echo "Nothing exceeds 50 MB: largest is dag.npz at 2.9 MB, the dag directory is 14 MB."
echo "The KEY_DO_NOT_SHARE_L1_roots.json file is deliberately NOT committed and was never reopened."
