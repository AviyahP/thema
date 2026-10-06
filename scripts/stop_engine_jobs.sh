#!/bin/sh
# Stop every engine job AND every worker it spawned, then prove it by PID.
#
# This exists because of a real failure. Stopping a driver by PID three times over left its spawned
# worker processes alive, reparented to init: 24 orphans at ~1.5 GB each on a 36 GB machine, with
# 5h27m elapsed and 27s of CPU. They exhausted memory, which is what put the Mac to sleep and wedged
# the pool that was running -- a parent at 0.0% CPU having accumulated 1.55s in 43 minutes.
#
# A ProcessPoolExecutor's children do not die with the parent when the parent is signalled, so the
# workers must be named explicitly. `spawn` is what makes them findable: every one runs
# multiprocessing.spawn_main.
set -e
echo "=== stopping drivers and chains ==="
for PATTERN in run_all_engine_arms.sh run_engine_evaluation.sh chain_tables.sh \
               run_engine_arm.sh "build_10770.py --engine" \
               testr_sides.sh test_r_pool.py test_r_transfer.py test_r_heights.py \
               test_r_biolord.py; do
  for P in $(pgrep -f "$PATTERN" 2>/dev/null); do
    kill "$P" 2>/dev/null && echo "  TERM $P ($PATTERN)"
  done
done
sleep 5
echo "=== stopping orphaned workers ==="
for P in $(pgrep -f spawn_main 2>/dev/null); do
  kill -9 "$P" 2>/dev/null && echo "  KILL $P (worker)"
done
sleep 3
echo "=== verification, by PID ==="
LEFT=0
for PATTERN in run_all_engine_arms.sh run_engine_evaluation.sh chain_tables.sh \
               run_engine_arm.sh "build_10770.py --engine" spawn_main \
               testr_sides.sh test_r_pool.py test_r_transfer.py test_r_heights.py \
               test_r_biolord.py; do
  for P in $(pgrep -f "$PATTERN" 2>/dev/null); do
    echo "  STILL ALIVE: $P ($PATTERN)"
    LEFT=$((LEFT + 1))
  done
done
[ "$LEFT" = "0" ] && echo "  clean: no engine process and no worker remains"
exit 0
