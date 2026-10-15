# N1 namer stage: summary (reviewer, completed 14 Oct 2026 23:13 UTC)

- Build: thema_L_x2_O50. Eligible themes (3-200 members): 4591. 11 themes over 200 members are out of scope.
- 552 input files (3 slots x 184 batches, 25 themes each; the last batch per slot has 16) -> 552 outputs in raw/, all validated
  by code/nm_validate.py (theme ids in input order, nameable is a boolean, non-empty name when nameable).
- Candidates: 13773 (3 per theme, every theme exactly 3).
- Not-nameable votes per slot: 13 / 18 / 14. Themes by number of not-nameable votes: {1: 5, 2: 5, 3: 10}
  (unnameable under the algorithm = 2+ of 3 votes).
- candidates_all.tsv: one row per candidate (theme_id, slot, batch, nameable, core, qualifier, name, rationale), sorted.
- raw_rejected/: two first-run outputs that omitted one theme each (s2 b011 missing n01709; s2 b126 missing n03398).
  Both batches were rerun in full; the rejected files are kept for the record and are NOT used.
- Run conditions: in-session subagents (configured model claude-opus-5-5), prompt in RUN_LOG.md, spec/N1_namer.md.
  slot0 b048 retry and slot1/slot2 b048 carried one added context sentence (safety-classifier workaround).
  Paused 18:17-22:20 UTC (usage limit); no data lost.
- Cost (approximate): ~105k subagent tokens per batch, ~58M total.
- Next stages (not yet run): S1 back-match, select (medoid), dedup, evaluation; see spec/ALGORITHM.md and PREREG.md.
