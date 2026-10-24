#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "Merging by core gives the same theme count with more near-copies: for most themes the core is the membership" > /dev/null

git add scripts/tree_cores.py scripts/tree_core_bars.py
git diff --cached --quiet || git commit -m "Prompts 59 and 60: tree cores at two covers, three recurrence bars, and a two-seed noise check"

git add \
  data/experiments/tree_cores_2026-10-23/candidates_census.json \
  data/experiments/tree_cores_2026-10-23/candidates.npz \
  data/experiments/tree_cores_2026-10-23/scored.npz \
  data/experiments/tree_cores_2026-10-23/step3.json \
  data/experiments/tree_cores_2026-10-23/cover50/candidates_census.json \
  data/experiments/tree_cores_2026-10-23/cover50/scored.npz \
  data/experiments/tree_cores_2026-10-23/cover50/step3.json
git diff --cached --quiet || git commit -m "Tree core candidates and scores at cover 0.70 and 0.50"

git add \
  data/experiments/tree_cores_2026-10-23/bars/bars.json \
  data/experiments/tree_cores_2026-10-23/bars/examples/runs_5-9.md \
  data/experiments/tree_cores_2026-10-23/bars/examples/runs_10-19.md \
  data/experiments/tree_cores_2026-10-23/bars/examples/runs_20plus.md \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03001/candidates_census.json \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03001/candidates.npz \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03001/scored.npz \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03001/step3.json \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03002/candidates_census.json \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03002/candidates.npz \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03002/scored.npz \
  data/experiments/tree_cores_2026-10-23/bars/scramble/seed03002/step3.json
git diff --cached --quiet || git commit -m "Prompt 60 bars, the twenty examples per recurrence group, and the two scramble sides"

git add data/experiments/reviewer_notes/PROMPT_59.md data/experiments/reviewer_notes/PROMPT_60.md
git diff --cached --quiet || git commit -m "Prompts 59 and 60, for the record"

git add docs/status/2026-10-23-tree-cores.md docs/status/commit-2026-10-23-tree-cores.sh DECISIONS.md
git diff --cached --quiet || git commit -m "At a 20-run bar the largest recurrent tree core is 59 pathways and the 100-199 band is empty"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Bars of 5, 10 and 20 runs retain 681,363 then 496,556 then 294,749 of 921,420 candidates."
echo "Largest retained core: 115 pathways at 5 runs, 113 at 10, 59 at 20. The 100-199 band empties."
echo "Coverage stays total: 5,537 of 5,539 pathways sit in some core even at the 20-run bar."
echo "Redundancy per core is flat across bars, about 696 non-nested near-copies each, against 15.7"
echo "for O50s gated themes. All three 1d runs verified exactly against a brute force sample of 2,000."
echo "Noise check, INDICATIVE ONLY, two seeds: scrambled retains 4.31, 2.33, 1.30 percent of real."
echo "Scrambled cores live in 3-5 and 6-11. From 25 pathways up the scramble is empty at every bar."
echo "The first scramble side was built from the RAW embeddings and discarded: the real trees come"
echo "from the centred sidecar. build_scramble_trees now proves its matrix against cached real run 1."
echo "NOT COMMITTED, both regenerable: cover50/candidates.npz at 129 MB and scramble_trees at 50 MB."
echo "Largest file committed here: cover50/scored.npz at about 16 MB."
echo "No ontology was built, nothing is adopted, and no KEY file exists or is listed for this prompt."
