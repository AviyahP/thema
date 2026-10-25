#!/bin/zsh
set -euo pipefail
cd ~/code/thema

git log --format=%s | grep -cFx "The calibrated gate replaces the provisional bar on L1m: floors solved per band and confirmed on held-out" > /dev/null

git add scripts/scramble_cache.py scripts/tree_core_bars.py scripts/tree_cores.py scripts/l1_build.py scripts/l1m_build.py
git diff --cached --quiet || git commit -m "The scramble trees become a permanent cache: one module owns the path and every reader takes --scramble-seed"

git add .gitignore
git diff --cached --quiet || git commit -m "Keep data/cache out of git: the scramble trees are regenerable and 397 MB"

git add \
  docs/status/2026-10-23-tree-cores.md \
  docs/status/2026-10-24-L1-steps1-4.md \
  docs/status/2026-10-24-L1m.md \
  docs/status/2026-10-24-L1m-gate.md
git diff --cached --quiet || git commit -m "Repoint the notes at the cache and record that the gate reran from it identically"

git add docs/status/commit-2026-10-25-scramble-cache.sh DECISIONS.md
git diff --cached --quiet || git commit -m "Scramble trees are a permanent cache, never rebuilt unless the universe or the matrix changes"

git push origin leaves-2026-10

echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "All 16 scramble sides now live in data/cache/scramble_trees_x2_centred: 3,200 trees, 397 MB."
echo "Calibration 3001 to 3010 from prompt 60 and prompt 65, held out 4001 to 4006."
echo "Nothing was rebuilt in the move. The folder is chmod a-w and data/cache is in .gitignore,"
echo "so it is neither committed nor writable by accident."
echo "scripts/scramble_cache.py is the only place that knows the path. trees_for RAISES on a"
echo "missing or short side rather than returning a path that would read as empty."
echo "tree_cores.py, l1_build.py and l1m_build.py now take --scramble-seed N; --trees still works."
echo "MANIFEST.md in the cache records seeds, 200 trees each, the universe c54319cdfbbe9eb7, the"
echo "centred matrix and its sha256, that the subsamples are the real runs, null_embeddings as the"
echo "procedure, the proof against real run 1 at 2,681 clusters, and the regeneration command."
echo "VERIFIED: rebuilding seeds 3003, 4006 and 3001 from the cache reproduced their existing"
echo "archives array for array, and prompt 65 gate rerun gives a floors file and a printed report"
echo "that are IDENTICAL byte for byte to before the move."
echo "No KEY_DO_NOT_SHARE file exists for this change and none is listed."
