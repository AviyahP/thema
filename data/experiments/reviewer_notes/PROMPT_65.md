Prompt 65: the gate for L1m, calibrated on scrambles exactly as O50s's gate. Declared 24 Oct 2026, before any result. Exploratory: nothing adopted. Design: Aviyah, 24 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
L1m (prompt 64) uses a provisional bar of 10 runs. Two scramble seeds show it lets in noise among small themes (3-5: 62% of the real count; 6-11: 12%) and none from 12 up. Replace the provisional bar with O50s's own gate procedure, unchanged, applied to L1m. No new numbers.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first, split into coding and compute; for this prompt proceed unless the COMPUTE alone is expected to exceed 3 h. Exact computation, verified as in prompts 61-64; report each check.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_65.md (if not already there), and copy it into DECISIONS.md as "declared before running".

SCRAMBLES: build Ward trees for the remaining calibration seeds 3003-3010 and the held-out seeds 4001-4006, exactly as prompt 60 built 3001-3002 (same procedure, the centred matrix proved against cached real run 1, the real runs' subsamples), in new directories; reuse 3001-3002. Run L1m unchanged (prompt 61 steps 1-2, then prompt 64's members merge to a fixed point) on every scramble side.

GATE (O50s's procedure, unchanged): its 13 size bands (3, 4, 5, 6, 7-9, 10-19, 20-39, 40-79, 80-159, 160-319, 320-639, 640-1,279, 1,280+) by member count; support = runs found / runs able to judge, as L1m computes it. For each band, the floor is the lowest support at which (mean over the 10 calibration seeds of scrambled themes at or above it) / (real themes at or above it) is at most 0.008; where the scrambles never pass, the rule-of-three bound as O50s computes it. Floors are solved on 3001-3010 only, then checked ONCE on 4001-4006: held-out FDR overall (cap 0.01) and per band (cap 0.02). Report any cap failure; never adjust floors using the held-out seeds. Quote the O50s code you reuse.

REPORT (docs/status/2026-10-24-L1m-gate.md)
A. Floors per band (support and the equivalent runs out of 200), next to O50s's floors and next to the provisional 10-run bar.
B. Held-out FDR, overall and per band, with counts.
C. Real themes kept per band (calibrated gate vs the 10-run bar); mean themes per pathway; non-nested J >= 0.5 pairs per theme.
D. DAG on the gated themes (strict containment, immediate parents, memberships unchanged, as prompt 64): themes, edges, roots by band (3-5 ... 1,600+), multi-parent share, children per node (max, median), levels to a root (median, max), roots of 200 or more (count).

FINAL
Write docs/status/commit-2026-10-24-L1m-gate.sh, to run after commit-2026-10-24-L1m.sh. It commits the code, note, small outputs and PROMPT_65.md, listing files explicitly, leaving out the scramble trees and any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give sections A-D as tables and the commit script path. Then stop.
