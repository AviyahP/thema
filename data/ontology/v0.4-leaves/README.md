# Universe L builds

`L` is the **atomic** universe: the 10,770 with every curated summary removed (a pathway with at
least one descendant in the universe). **5,559 pathways.** No figure in this directory is comparable
with a 10,770 number.

## Floors in use, and a caveat that no check will tell you about

**All builds here made after the 17-BTM drop use the cal8 floors calibrated on universe 10,770.**

> floors: cal8, calibrated on universe 10,770, reused after the 17-BTM drop

Aviyah decided on 2026-10-09 to reuse them rather than recalibrate, on the grounds that the floors
are solved from the scramble side and removing 17 of 10,770 inputs (0.16%) should leave the scramble
null essentially unchanged. ccode's recommendation was a full recalibration; the decision overrides
it knowingly. The argument is in `docs/status/2026-10-09-reviewer-plausibility.md`.

**Nothing in the pipeline enforces or reports this.** No digest check compares a floors file's
universe against the build's: `leaves_build.py` applies whatever `--floors-file` it is given, and
`universe.load_embedded` only checks the artifact against `pathways.tsv`, which is unedited because
the 17 are excluded by config in `data/excluded_inputs.tsv`. So the reuse is silent, and this file,
`DECISIONS.md`, and each build's own `floors_source` are the only places it is recorded.

**Open to-do:** consider re-running scrambles on the current universe and updating the floors later;
until then all builds after the 17-BTM drop use the previous (cal8) floors.

## What is here

- `thema_L` -- the leaves build, 2,815 themes, 3-seed floors (its own 5-5 check failed at 0.0297).
- `thema_L_M5`, `thema_L_MS` -- recurrence-threshold arms.
- `thema_L_cal`, `thema_L_cal8`, and the `_g_cur` arms -- the re-gate grid.
- `thema_L_repair` -- cal8 floors plus the stale-merge fix and chain collapse at 90%. 8,793 themes.
  `browse.html` beside it is a self-contained reader for the whole DAG.
- `restricted_v04`, `hidef_L_*` -- the leaves experiment's baselines.
- `calibration*/` -- side material (gitignored) and `floors.json` (kept) per arm.
- `regate/` -- the grid's floor sets, including `floors_L_cal8.json` and its reuse note.

Member rosters for the grid arms and stability halves are gitignored and regenerable; see
`.gitignore` for which and why.
