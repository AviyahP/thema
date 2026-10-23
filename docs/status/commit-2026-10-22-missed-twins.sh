#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "S2 against O50s: no computed measure separates them; the readings are the remaining evidence" > /dev/null

git add scripts/missed_twins.py
git diff --cached --quiet || git commit -m "Prompt 56 Part A: the twin test on O50s after-gate merges, at the event and at gate exit"

git add data/experiments/missed_twins_2026-10-22/events.json
git diff --cached --quiet || git commit -m "Prompt 56 per-event records for the three after-gate merge kinds, and task 4"

git add data/experiments/reviewer_notes/PROMPT_56.md
git diff --cached --quiet || git commit -m "Prompt 56, for the record"

git add docs/status/2026-10-22-missed-twins.md docs/status/commit-2026-10-22-missed-twins.sh DECISIONS.md
git diff --cached --quiet || git commit -m "After-gate merges are not missed twins: zero of 19,697 pairs are twins at gate exit"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "ZERO of 19,531 rule-3 supersessions and 166 stale merges are twins at gate exit."
echo "418 pairs are twins at the event and not at the gate; zero go the other way."
echo "Chain collapse at size ratio 0.91 or above is exactly the twin rule: 301 of 301."
echo "1,770 of 19,147 failing rule-3 drops were inside no final theme, rising to 100 percent above 1,600 pathways."
echo "PART A ONLY. Part B (replay, rules 1 2 4, rule-2 twin test) and task 5 are skipped by decision."
echo "No file was left out for size: events.json is the only data file and is well under 50 MB."
echo "No KEY_DO_NOT_SHARE file exists for this prompt and none is listed."
