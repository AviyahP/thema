#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Three pathways separate the seven giants from a two level hierarchy: strict containment cannot see it" > /dev/null

git add scripts/l1m_build.py scripts/l1m_report.py
git diff --cached --quiet || git commit -m "Prompt 64: L1m, the 90 percent each way merge on members repeated to a fixed point, and sections A to E"

git add \
  data/experiments/L1m_2026-10-24/real/themes.npz \
  data/experiments/L1m_2026-10-24/real/build.json \
  data/experiments/L1m_2026-10-24/dag.npz \
  data/experiments/L1m_2026-10-24/report.json
git diff --cached --quiet || git commit -m "L1m real side: 7 passes, 120,180 themes, zero identical member sets, and the DAG"

git add \
  data/experiments/L1m_2026-10-24/scramble/seed03001/themes.npz \
  data/experiments/L1m_2026-10-24/scramble/seed03001/build.json \
  data/experiments/L1m_2026-10-24/scramble/seed03002/themes.npz \
  data/experiments/L1m_2026-10-24/scramble/seed03002/build.json
git diff --cached --quiet || git commit -m "L1m on the two scramble sides, indicative only"

git add \
  data/experiments/L1m_2026-10-24/read_roots/batch_01.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_02.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_03.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_04.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_05.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_06.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_07.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_08.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_09.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_10.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_11.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_12.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_13.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_14.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_15.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_16.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_17.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_18.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_19.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_20.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_21.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_22.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_23.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_24.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_25.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_26.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_27.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_28.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_29.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_30.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_31.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_32.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_33.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_34.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_35.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_36.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_37.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_38.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_39.md \
  data/experiments/L1m_2026-10-24/read_roots/batch_40.md
git diff --cached --quiet || git commit -m "The 40 blind reading batches for every L1m root of 100 or more pathways"

git add data/experiments/reviewer_notes/PROMPT_64.md
git diff --cached --quiet || git commit -m "Prompt 64, for the record"

git add docs/status/2026-10-24-L1m.md docs/status/commit-2026-10-24-L1m.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Merging on members removes every duplicate theme and cuts redundancy below O50s, and the giants stay flat"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "DECISION RECORDED: the L1 merge compares MEMBERS, not cores. Steps 1 and 2 are unchanged."
echo "7 passes, 138,045 merges then 3,481, 253, 22, 2, 1, 0. Cap of 50 not hit."
echo "261,984 groups to 120,180 themes, 41,605 found in 10 or more runs. ZERO identical member sets,"
echo "asserted in the build and the report, against 18,918 for L1 over all its themes."
echo "Mean themes per pathway 102.6 against L1 210.7 and O50s 23.5."
echo "Non nested J 0.5 pairs per theme 5.9, BELOW O50s at 15.7 for the first time."
echo "The DAG: 161,869 edges against 388,287, 82 percent multi parent, 12 levels per pathway."
echo "Roots 617 against 594: removing duplicates removed edges, not roots."
echo "Roots of 200 or more fall from 205 to 75."
echo "All seven large7 sets match an L1m theme at J 0.914 or better and all seven are still roots."
echo "At an absolute tolerance of one or two pathways NOT ONE of the 18 giants gains a parent,"
echo "against 83 percent at prompt 63 proportional 90 percent. The top level near misses were variants."
echo "The new problem is the small end: 3-5 themes grew by 3,200 and scrambled data matches 61.7"
echo "percent of them at the 10 run bar. A size floor near 12 would remove the whole noisy region."
echo "Fixed point, adjacency and zero duplicates verified on all three sides; the whole greedy pass"
echo "is replayed with Python sets on the 6 run smoke and reproduces the assignment exactly."
echo "DAG ancestors and immediate parents verified against set loops on 300 themes, all identical."
echo "Nothing exceeds 50 MB: largest is a scramble themes.npz at 46.1 MB, the directory is 124 MB."
echo "The KEY_DO_NOT_SHARE_L1m_roots.json file is deliberately NOT committed and was never reopened."
