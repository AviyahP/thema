#!/bin/sh
# §3: evaluate the built arms and apply the declared rule. Runs after the arm chain, one job at a
# time, so it never competes with a build.
#
# Usage: scripts/run_engine_evaluation.sh <logdir> [wait-for-pid]
set -e
LOGS="$1"
WAIT_PID="${2:-}"
mkdir -p "$LOGS"
if [ -n "$WAIT_PID" ]; then
  echo "### waiting for the arm chain, PID $WAIT_PID"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 30; done
  echo "### arm chain finished at $(date -u +%H:%M:%SZ)"
fi

# Only arms that actually produced a build enter the evaluation. An arm that failed to build is
# reported as not built rather than silently omitted.
ARGS=""
for PAIR in "A=v0.3/recurrent_dag_10770" "B=v0.3x_engines/leiden" \
            "B2=v0.3x_engines/leiden_persistent" "C=v0.3x_engines/pooled" \
            "G=v0.3x_engines/bisect" "H=v0.3x_engines/infomap"; do
  ARGS="$ARGS --arm $PAIR"
done

echo "### G4: STRING coherence"
nice -n 19 uv run scripts/string_coherence.py $ARGS --reference A \
  --out "$LOGS/string_coherence.json" > "$LOGS/g4.log" 2>&1 || echo "### G4 FAILED"
tail -20 "$LOGS/g4.log" || true

echo "### gates G1-G4"
nice -n 19 uv run scripts/engine_gates.py $ARGS --reference A \
  --string "$LOGS/string_coherence.json" --out "$LOGS/gates.json" > "$LOGS/gates.log" 2>&1 \
  || echo "### gates FAILED"
cat "$LOGS/gates.log" || true

ELIGIBLE=$(nice -n 19 uv run python -c "
import json
print(','.join(json.load(open('$LOGS/gates.json'))['eligible']))
" 2>/dev/null || echo "")
echo "### eligible: $ELIGIBLE"

echo "### the 16 scores and the declared rule"
nice -n 19 uv run scripts/engine_scores.py $ARGS --reference A --eligible "$ELIGIBLE" \
  --out "$LOGS/scores.json" --tsv data/experiments/engine_scores.tsv \
  > "$LOGS/scores.log" 2>&1 || echo "### SCORES FAILED"
tail -40 "$LOGS/scores.log" || true

echo "### labelled diagnostic: arm A at theta 0.70 / 0.60 / 0.50"
nice -n 19 uv run scripts/theta_diagnostic.py --thetas 0.70,0.60,0.50 \
  --out "$LOGS/theta_diagnostic.json" > "$LOGS/theta.log" 2>&1 || echo "### THETA FAILED"
tail -14 "$LOGS/theta.log" || true

echo "### EVALUATION DONE at $(date -u +%H:%M:%SZ)"
