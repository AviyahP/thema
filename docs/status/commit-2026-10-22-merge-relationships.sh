#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "C1b is not better than O50s: 1,066 roots against 261, and p collapses to 0.1 above 20 pathways" > /dev/null

git add \
  data/ontology/frozen/working-O50s-2026-10-22/CHECKSUMS.sha256 \
  data/ontology/frozen/working-O50s-2026-10-22/FROZEN.md \
  data/ontology/frozen/working-O50s-2026-10-22/edges.tsv \
  data/ontology/frozen/working-O50s-2026-10-22/excluded_inputs.tsv \
  data/ontology/frozen/working-O50s-2026-10-22/floors_o50s.json \
  data/ontology/frozen/working-O50s-2026-10-22/manifest.json \
  data/ontology/frozen/working-O50s-2026-10-22/members.tsv \
  data/ontology/frozen/working-O50s-2026-10-22/nodes.tsv \
  data/ontology/frozen/working-O50s-2026-10-22/repair_map.json \
  data/ontology/frozen/working-O50s-2026-10-22/report.txt \
  data/ontology/frozen/working-O50s-2026-10-22/trees_build_log.json \
  data/ontology/frozen/working-O50s-2026-10-22/universe.json \
  data/ontology/frozen/working-O50s-2026-10-22/unplaced.tsv \
  data/ontology/frozen/working-O50s-2026-10-22/verify.txt \
  tests/ontology/test_frozen_baseline.py
git diff --cached --quiet || git commit -m "O50s adopted and frozen as the working baseline, guarded by checksum; frozen O50 kept as the previous baseline"

git add \
  scripts/o50s_build.py \
  scripts/merge_relationships.py \
  scripts/dropped_parents.py \
  src/thema/ontology/consensus.py \
  src/thema/ontology/v04.py
git diff --cached --quiet || git commit -m "Additive merge-provenance hooks, off by default, and the two prompt 52 analyses"

git add \
  data/experiments/merge_relationships_2026-10-22/pairs.tsv \
  data/experiments/merge_relationships_2026-10-22/potential_parents.tsv
git diff --cached --quiet || git commit -m "Prompt 52 tables: 20,462 merged pairs classified, and every one of the 814 potential parents"

git add \
  data/experiments/merge_relationships_2026-10-22/read_parents/b01.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b02.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b03.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b04.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b05.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b06.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b07.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b08.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b09.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b10.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b11.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b12.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b13.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b14.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b15.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b16.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b17.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b18.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b19.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b20.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b21.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b22.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b23.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b24.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b25.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b26.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b27.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b28.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b29.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b30.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b31.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b32.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b33.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b34.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b35.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b36.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b37.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b38.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b39.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b40.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b41.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b42.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b43.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b44.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b45.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b46.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b47.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b48.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b49.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b50.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b51.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b52.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b53.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b54.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b55.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b56.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b57.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b58.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b59.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b60.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b61.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b62.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b63.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b64.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b65.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b66.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b67.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b68.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b69.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b70.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b71.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b72.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b73.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b74.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b75.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b76.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b77.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b78.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b79.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b80.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b81.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b82.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b83.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b84.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b85.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b86.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b87.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b88.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b89.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b90.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b91.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b92.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b93.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b94.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b95.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b96.md \
  data/experiments/merge_relationships_2026-10-22/read_parents/b97.md
git diff --cached --quiet || git commit -m "Prompt 52 blind reading material: 120 potential parents in 97 batches, 30 per stage"

git add data/experiments/reviewer_notes/PROMPT_51.md data/experiments/reviewer_notes/PROMPT_52.md
git diff --cached --quiet || git commit -m "Prompts 51 and 52, for the record; prompt 51 is on hold"

git add docs/status/2026-10-22-merge-relationships.md docs/status/commit-2026-10-22-merge-relationships.sh DECISIONS.md
git diff --cached --quiet || git commit -m "O50s merges act mostly on unrelated pairs: consensus 54 percent unrelated, chain collapse discards the parent 72 percent of the time"

git tag -a thema-O50s-2026-10-22 -m "THEMA working baseline: O50s, 5,658 themes, frozen 22 Oct 2026"
git push origin leaves-2026-10
git push origin thema-O50s-2026-10-22

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "O50s is the working baseline, frozen and tagged thema-O50s-2026-10-22."
echo "Prompt 52: consensus merges 54 percent unrelated pairs; chain collapse keeps the child 71.9 percent of the time."
echo "LEFT OUT as regenerable caches: merge_relationships_2026-10-22/side.npz (22 MB) and probe.npz (3.2 MB)."
echo "No KEY_DO_NOT_SHARE file is listed. The rebuilt thema_L_x2_O50s_relog is not committed: it is byte-identical to the freeze."
