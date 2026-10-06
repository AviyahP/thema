#!/bin/sh
# Run the declared build set sequentially: one arm at a time, one side at a time.
#
# Waits for any arm already running to finish first, so this can be launched mid-flight without
# ever putting two heavy jobs on the machine at once -- the rule that exists because it thrashed.
#
# Usage: scripts/run_all_engine_arms.sh <logroot> [workers] [wait-for-pid]
set -e
LOGS="$1"
WORKERS="${2:-auto}"
# "auto" sizes the pool from genuinely available memory before EACH arm, so a resume on a busy
# machine does not repeat the stall that orphaned workers caused on 6 Oct.
if [ "$WORKERS" = "auto" ]; then
  WORKERS=$(VERBOSE=1 sh scripts/engine_workers.sh)
  echo "### worker count chosen automatically: $WORKERS"
fi

# Wait on an EXPLICIT PID, not a name match. Matching by name races with the driver this chain is
# queued behind: between two sides it has no build_10770 child, and the chain would start a second
# driver on the same arm and both would write the same cache file.
WAIT_PID="${3:-}"
if [ -n "$WAIT_PID" ]; then
  echo "### waiting for PID $WAIT_PID to finish"
  while kill -0 "$WAIT_PID" 2>/dev/null; do
    sleep 30
  done
  echo "### PID $WAIT_PID finished at $(date -u +%H:%M:%SZ)"
fi

for ARM in leiden leiden_persistent pooled bisect infomap; do
  if [ -f "data/ontology/v0.3x_engines/$ARM/nodes.tsv" ] \
     && [ -f "data/ontology/v0.3x_engines/${ARM}_r101-200/nodes.tsv" ]; then
    echo "### $ARM already complete, skipping"
    continue
  fi
  echo "### $ARM starting at $(date -u +%H:%M:%SZ)"
  sh scripts/run_engine_arm.sh "$ARM" "$LOGS/$ARM" "$WORKERS" || echo "### $ARM FAILED"
  echo "### $ARM ended at $(date -u +%H:%M:%SZ)"
done
echo "### ALL ARMS DONE at $(date -u +%H:%M:%SZ)"
