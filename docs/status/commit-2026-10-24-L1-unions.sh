#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Level 1 finds large recurrent themes after all, but only about seven distinct ones, and its small end is noise" > /dev/null

git add scripts/l1_unions.py
git diff --cached --quiet || git commit -m "Prompt 62: inner themes, single and greedy cover, and the two and three block patterns"

git add \
  data/experiments/L1_2026-10-24/unions/measures.npz \
  data/experiments/L1_2026-10-24/unions/unions.json
git diff --cached --quiet || git commit -m "Union measures for all 7,958 accepted themes of 25 or more pathways, both passes"

git add \
  data/experiments/L1_2026-10-24/unions/examples/two_block.md \
  data/experiments/L1_2026-10-24/unions/examples/not_two_block.md \
  data/experiments/L1_2026-10-24/unions/examples/two_block_near_copies_dropped.md \
  data/experiments/L1_2026-10-24/unions/examples/not_two_block_near_copies_dropped.md
git diff --cached --quiet || git commit -m "Forty themes with the first two picks marked, under each pass, for reading later"

git add data/experiments/reviewer_notes/PROMPT_62.md
git diff --cached --quiet || git commit -m "Prompt 62, for the record"

git add docs/status/2026-10-24-L1-unions.md docs/status/commit-2026-10-24-L1-unions.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Mid-sized L1 themes are unions of unrelated blocks and the giants are not: set_3 contains set_6 exactly"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "DECISION RECORDED: the L1 merge rule is 90 percent each way. Working side real_bothways."
echo "52,001 accepted themes at the provisional 10-run bar; 7,958 of 25 or more pathways measured."
echo "Declared pass: median single cover 0.929, because inner themes are defined by containment"
echo "so the near-copies of a theme qualify. An added pass drops inner themes within J 0.5 of"
echo "the target; both are reported and neither removes anything from any build."
echo "Added pass: three unrelated blocks cover 97 percent of a 25-49 theme and 79 percent of a giant."
echo "Three-block share is 57 to 62 percent below 200 pathways, 4.1 percent at 800-1599, 2.8 at 1600+."
echo "Median single cover is 0.485 to 0.501 in every band from 25 to 1599. Half is the recurring number."
echo "set_3 contains set_6 at J 1.000, exactly, as half of itself; they are separate themes because"
echo "1,143 is under 90 percent of 2,271. set_4 is 86.7 percent set_5 plus set_7."
echo "So the missing relationship is hierarchy, not duplication."
echo "Both passes verified against explicit set loops on 200 targets, seed 20261024, all identical."
echo "Nothing left out for size: the unions directory is 864 KB. No KEY_DO_NOT_SHARE file is listed."
