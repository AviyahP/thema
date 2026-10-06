#!/bin/sh
# Build one engine arm end to end, SEQUENTIALLY, as a single job.
#
# Sides are cut one at a time into the completion cache, then the full build reads them back, then
# the two G2 stability halves are built. Sequential because the machine thrashed once with two
# heavy jobs in parallel; the parallelism that remains is inside a single side's candidate
# generation, which is what --engine-workers does.
#
# Usage: scripts/run_engine_arm.sh <engine> <logdir> [workers]
set -e
ENGINE="$1"
LOGS="$2"
WORKERS="${3:-6}"
CAL="3001 3002 3003 3004 3005 3006 3007 3008 3009 3010"
HELD="4001 4002 4003 4004 4005"
TREES=data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7
FLOORS="$TREES/completions/cap3125_inc050_${ENGINE}/floors_r1-200_n200.json"
mkdir -p "$LOGS"
B="nice -n 19 uv run scripts/build_10770.py --engine $ENGINE --completion fast --families joined --engine-workers $WORKERS"

echo "=== $ENGINE: sides ==="
for S in real_r00001-00200 $(for s in $CAL $HELD; do echo "seed0${s}_n200"; done); do
  if [ -f "$TREES/completions/cap3125_inc050_${ENGINE}/${S}.npz" ]; then
    echo "  $S cached"; continue
  fi
  echo "  cutting $S"
  /usr/bin/time -l $B --runs 200 --cut-side "$S" > "$LOGS/side_${S}.log" 2>&1
  grep -E "families \(|maximum resident" "$LOGS/side_${S}.log" | tr '\n' ' '; echo
done

echo "=== $ENGINE: the build (floors solved, held-out read ONCE) ==="
/usr/bin/time -l $B --runs 200 --confirm-heldout --directory "$ENGINE" \
  > "$LOGS/build.log" 2>&1
grep -E "nodes |maximum resident|HELD-OUT|overall" "$LOGS/build.log" | head -6

echo "=== $ENGINE: G2 stability halves ==="
for R in 1-100 101-200; do
  LO=$(echo "$R" | cut -d- -f1); HI=$(echo "$R" | cut -d- -f2)
  SIDE="real_r$(printf %05d "$LO")-$(printf %05d "$HI")"
  if [ ! -f "$TREES/completions/cap3125_inc050_${ENGINE}/${SIDE}.npz" ]; then
    /usr/bin/time -l $B --rows "$R" --cut-side "$SIDE" > "$LOGS/side_${SIDE}.log" 2>&1
    grep -E "families \(|maximum resident" "$LOGS/side_${SIDE}.log" | tr '\n' ' '; echo
  fi
  /usr/bin/time -l $B --rows "$R" --floors-from "$FLOORS" --half-build-floors \
    --directory "${ENGINE}_r${R}" > "$LOGS/half_${R}.log" 2>&1
  grep -E "nodes |maximum resident" "$LOGS/half_${R}.log" | head -2
done
echo "=== $ENGINE: DONE ==="
