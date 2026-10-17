Prompt 41: the first pass's resolution limit, i.e. the largest cluster size it can tell from noise. A diagnostic, declared 16 Oct 2026. It is read-only and adopts nothing. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; times in UTC+1. Stop if the estimate is over 2 h.

WHY
We need a measured, not chosen, size threshold T: the largest size at which the first pass (O50's configuration, 0.70 match, cal8 floors) can still separate real clusters from scrambled ones. Above T, first-pass clusters are not vouched for by the method. T will justify where the areas pass takes over. The O50 size distribution already breaks between 100 and 200 (÷4 per doubling up to 100, ÷9 at 100-199, then flat).

STEPS
1. **Collect support for real and scrambled candidates.**
   - Real candidates: data/experiments/consensus_fate_2026-10-16/fate.tsv (support at family level). Use all candidates that reach the gate step.
   - Scrambled candidates: the calibration scrambles used for O50's cal8 floors (seeds 3001-3010). Use the cache if it exists; if not, recompute them exactly and say so.
2. **Bin by size, in doublings:** 10-19, 20-39, 40-79, 80-159, 160-319, 320-639, 640-1,279, 1,280+. Also give a finer split at 80-119, 120-159, 160-239, 240-319.
3. **Per bin, report:**
   - real and scrambled candidate counts (scrambled as the mean per seed);
   - median and 90th-percentile support, real and scrambled;
   - the best FDR the bin can reach on its own: the smallest (mean scrambled ≥ cut) / (real ≥ cut) over all cuts, with that cut and how many real candidates it keeps;
   - how many real candidates pass at FDR ≤ 0.008 within the bin.
4. **Define T** as the upper edge of the largest bin that keeps at least 5 real candidates at a within-bin FDR ≤ 0.008, with every smaller bin also meeting it. Report T, and whether the finer split moves it.

OUTPUT
- data/experiments/resolution_limit_2026-10-16/: the code and the tables.
- docs/status/2026-10-16-resolution-limit.md.
- docs/status/commit-2026-10-16-resolution-limit.sh, to run after commit-2026-10-16-consensus-fate.sh. It commits the folder, the note and data/experiments/reviewer_notes/PROMPT_41.md. No branch operations; no push of main.

END OF PROMPT. Before running, confirm in one line whether the scrambles are cached, and give the time estimate. After the run, give:
- the per-bin table;
- T;
- the commit script path.
