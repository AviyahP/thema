#!/bin/sh
# Print a safe worker count for engine candidate generation, from GENUINELY available memory.
#
# This exists because the run stalled once: 24 orphaned workers at ~1.5 GB each exhausted a 36 GB
# machine, and the Mac slept. The sizing below leaves room for the PARENT, which is the larger
# consumer -- arm C's real side peaked at 15.5 GB on its own.
#
# "Available" is free + inactive pages. Inactive pages are reclaimable without paging, so they do
# count; `free` alone reads near zero on a warm machine and would always give one worker.
RESERVE_GB=${RESERVE_GB:-17}   # for the parent process and the OS
PER_WORKER_GB=${PER_WORKER_GB:-1.8}
MAX=${MAX:-6}

AVAIL_GB=$(vm_stat | awk '
  /Pages free/      {gsub(/\./,"",$3); f=$3}
  /Pages inactive/  {gsub(/\./,"",$3); i=$3}
  END {printf "%.1f", (f+i)*16384/1073741824}')

N=$(awk -v a="$AVAIL_GB" -v r="$RESERVE_GB" -v w="$PER_WORKER_GB" -v m="$MAX" 'BEGIN{
  n = int((a - r) / w);
  if (n < 1) n = 1;
  if (n > m) n = m;
  print n
}')
if [ "${VERBOSE:-0}" = "1" ]; then
  echo "available ${AVAIL_GB} GB, reserve ${RESERVE_GB} GB, ${PER_WORKER_GB} GB/worker -> ${N} workers" >&2
fi
echo "$N"
