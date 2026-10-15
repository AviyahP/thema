# Naming O50 run state (reviewer)
- Inputs: /home/claude/nm/inputs/namer_slot{0,1,2}_b{001..184}.json (552 files, 25 themes each); spec in /home/claude/nm/spec/.
- Mac copies: ~/code/thema/data/experiments/naming_O50_2026-10-14/ (inputs, spec, PREREG.md, code/nm_build.py).
- Outputs: /home/claude/nm/raw/<same name>.out.json; validate theme_id order vs input; back up as tar to
  ~/code/thema/data/cache/reviewer_transfer/nm_raw_backup.tgz (gitignored) every ~50 files.
- Agent prompt: namer, read spec/N1_namer.md, one input file, scratch tmp/sS_NNN, output raw/...; reply count.
- Known: b048 slot0 hit a safety classifier once; retry with a context sentence worked.
- Next stages after all 552: S1 back-match items via pilot np_sel.py logic (adapt paths), judges, np_select,
  np_dup/dedup, final; then evaluation per PREREG; ccode prompt 32 reproduces files.
- slot1 b048 was run with the context sentence preemptively (same as the s0 b048 retry).
- 18:17 UTC hit session usage limit (reset 22:20 UTC); wave aborted; 5 files written & valid; missing s1 b182, s2 b001 b003 b005 b006.
- s2 b011 first run omitted n01709 (24/25); moved to rejected/, rerun whole batch.
- s2 b126 first run omitted n03398 (24/25); moved to rejected/, rerun whole batch.
- 23:13 UTC N1 COMPLETE: 552 files, all valid.
- 23:14 UTC Mac offline; S1 needs pilot scripts from Mac (naming_pilot*/code). Retry scheduled 23:45 UTC (trig_016vbHvZR34ARWX7dW9gUZe1).
- 23:45 UTC retry: Mac still offline. Next retry 06:45 UTC (trig_01VVNARLdqKpb13NaWsu7mYG).
- 06:46 UTC second retry: Mac still offline. Stopped retrying; waiting for Aviyah.
- 07:31 UTC Mac back: final backup (552) committed; pilot scripts staged to nm/pilotcode/.
- 09:06 UTC sample check: PREREG written; S1 items built (600 items, 12 files).
- 09:08 UTC S1 judged (P1 93.3%, P2 99.0%); selection done; E1/E2 items built (200 each).
- 09:10 UTC sample check DONE: GOOD (E1 96.5%, E2 0.924). REPORT in sample/.
- 09:20 UTC option 2 (lite): medoid without S1 for 4,376 themes + S1 picks for the 200 sample themes; 15 unnameable; 75 duplicate groups (154 themes). select_lite/.
