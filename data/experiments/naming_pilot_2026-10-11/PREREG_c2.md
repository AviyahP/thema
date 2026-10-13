# naming-c2: pre-registration (reviewer, 2026-10-11, before any result)

Change from naming-c1 (decided by Aviyah after c1 failed P4 reproducibility):
- Prompt N2_namer.md = N1 plus one style line (core first, at most one qualifier, no "X, Y and Z" lists).
- 5 independent candidates per theme instead of 3. Selection rule unchanged (back-match each; medoid by token
  Jaccard among correct candidates against all nameable candidates; low_confidence if none correct).
Test set: the same 60 reproducibility themes as c1 (inputs/repro_subset.json), same confusables.
Two fully independent c2 runs, A (candidate seeds 100-104) and B (110-114), each with its own selection judges.
Evaluation by fresh judges:
- E1 back-matching and E2 member fit on the final names of A and B (120 items each).
- E3: the 60 c2 pairs (A vs B) and the 60 c1 pairs (c1 main vs c1 rerun) judged together, shuffled and blind to
  version, by the same judges, so judge strictness is equal for both.
Pass bars for c2 (all must hold):
- P1 E1 >= 85%;  P3 mean fit >= 0.90;  P4 E3 equivalent >= 80% of the 60 c2 pairs;  P5 no duplicates within each run.
Reported: c1 vs c2 E3 under the same judges; c2 vs c1 E1/E2 on these 60 themes; share of list-style names
(three or more comma/and-joined items); median name length.
If c2 fails P4: fall back to option 1 (accept c1 or c2, whichever scores better, and report the number honestly).
