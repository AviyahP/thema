#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "At a 20-run bar the largest recurrent tree core is 59 pathways and the 100-199 band is empty" > /dev/null

git add scripts/l1_build.py scripts/l1_report.py
git diff --cached --quiet || git commit -m "Prompt 61: level 1 steps 1-4, the two-sided 70 percent match with its exact size window, and sections A-E"

git add \
  data/experiments/L1_2026-10-24/real/groups.npz \
  data/experiments/L1_2026-10-24/real/themes.npz \
  data/experiments/L1_2026-10-24/real/steps.json \
  data/experiments/L1_2026-10-24/report.json
git diff --cached --quiet || git commit -m "L1 real side: 270,570 seeds, 261,984 cores, 137,008 themes, every step brute force verified"

git add \
  data/experiments/L1_2026-10-24/scramble/seed03001/groups.npz \
  data/experiments/L1_2026-10-24/scramble/seed03001/themes.npz \
  data/experiments/L1_2026-10-24/scramble/seed03001/steps.json \
  data/experiments/L1_2026-10-24/scramble/seed03002/groups.npz \
  data/experiments/L1_2026-10-24/scramble/seed03002/themes.npz \
  data/experiments/L1_2026-10-24/scramble/seed03002/steps.json
git diff --cached --quiet || git commit -m "L1 on the two scramble sides, indicative only"

git add \
  data/experiments/L1_2026-10-24/examples/themes_6-24.md \
  data/experiments/L1_2026-10-24/examples/themes_25plus.md
git diff --cached --quiet || git commit -m "Forty L1 themes with the core marked, for reading later"

git add data/experiments/reviewer_notes/PROMPT_61.md
git diff --cached --quiet || git commit -m "Prompt 61, for the record"

git add docs/status/2026-10-24-L1-steps1-4.md docs/status/commit-2026-10-24-L1.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Level 1 finds large recurrent themes after all, but only about seven distinct ones, and its small end is noise"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "270,570 seeds, 261,984 with a core of 3+, 137,008 themes. No gate, no consensus, no repair."
echo "The ten largest themes found in 10+ runs hold 2,325 to 2,412 pathways, at 10 to 63 runs."
echo "Arm K stopped at 59 pathways. The only difference is that L1 lets the copy miss 30 percent."
echo "But the 237 themes of 800+ found in 10+ runs are 7 distinct sets at J under 0.5, covering all 5,539."
echo "About 5 percent distinct at every size from 25 up: the merge at J 0.9 is not the deduplicator."
echo "Scrambled embeddings beat real at 3-5 on a 5-run bar, 143 percent. Above 24 members, scramble is empty."
echo "Redundancy per theme matches O50s, 14.9 against 15.7 non-nested pairs at J 0.5."
echo "45.8 percent of O50s is reproduced at J 0.9 and 78.9 percent at J 0.7, with no statistics at all."
echo "Steps 1 to 4 verified against brute force on all three sides; five invariants over every theme."
echo "Nothing exceeds 50 MB. Largest here: a scramble themes.npz at 47.4 MB; the directory is 162 MB."
echo "The two scramble themes.npz files are 94.8 MB of that and are the first thing to drop."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
