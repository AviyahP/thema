# naming-c1b clean test: pre-registration (reviewer, 2026-10-11, before any result)

Question (Aviyah): was c2's result due to 5 candidates or to the new prompt? c1b isolates the candidate count:
the ORIGINAL N1 prompt with 5 candidates instead of 3. Everything else as naming-c1.
Construction: the same 60 reproducibility themes. Run M = c1 main candidates (slots 0-2, existing) + 2 new candidates
(seeds 3, 4). Run R = c1 rerun candidates (seeds 10-12, existing) + 2 new (seeds 13, 14). New candidates get their own
back-match selection judgements; existing judgements reused. Final = medoid among correct of 5 (rule unchanged).
Evaluation by fresh judges, blind to version, all items mixed:
- E1 and E2 on four sets of finals: c1b-M, c1b-R, c1-M (3 cand), c1-R (3 cand) (240 items each).
- E3 on 60 c1b pairs (M vs R) and 60 c1 pairs (main vs rerun), mixed.
Pass bars for c1b: E1 >= 85%; E2 >= 0.90; E3 equivalent >= 80%; no duplicates within a run.
Decision rule: adopt c1b over c1 only if it passes all bars, or if it is not worse on E1/E2 (difference within 3 points
/ 0.02) AND better on E3 equivalent by >= 10 points under the same judges. Otherwise keep c1 (3 candidates, cheaper).
