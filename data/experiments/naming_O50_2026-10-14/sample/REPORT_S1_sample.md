# O50 naming-c1: sample check result (reviewer, 15 Oct 2026)

Pre-registration: PREREG_S1_sample.md, written before any S1 judging. 200 random O50 themes, seed 20261015. All judges were fresh in-session subagents; S1 and E1/E2 used different judges.

## Result: GOOD (declared bars: E1 >= 85%, E2 >= 0.90)

| measure | O50 sample (200) | pilot (200) | bar |
|---|---|---|---|
| P1 candidates that pick their own theme (S1) | 93.3% (560/600) | about 83% (unselected) | report only |
| P2 themes with at least 1 correct candidate | 99.0% (2 low-confidence) | - | report only |
| **P3 E1, selected name picks its own theme among 5** | **96.5% (CI 93.5-98.5)** | 91.5% | >= 85% |
| **P4 E2 mean member fit** | **0.924 (CI 0.910-0.938)** | 0.917 | >= 0.90 |

- None of the sample themes is unnameable.
- n_correct among the 3 candidates: 3/3 for 169 themes, 2 for 24, 1 for 5, 0 for 2.
- E1 by size: 3-10 members 96.0%, 11-50 members 96.8%, 51-200 members 4/4.
- E2 by size: 0.944 / 0.904 / 0.913. 51% of names fit every member.
- E1 failures (7): n01493 and n03222 (both low-confidence, 0 correct candidates); n04181 (2 correct); n01692, n02668, n03058, n04224 (3 correct, so the E1 judge disagreed with three S1 judges).
- Lowest fit: n00658 (0.58, a Mycobacterium phagosome theme); n03902 (0.65, nuclear export of mRNA, tRNA and ribosomal subunits).

## What S1 adds (code only, same sample)
- Choosing the medoid of all 3 candidates WITHOUT S1 changes the pick in 13 of 200 themes (6.5%).
- In all 13 of those, the no-S1 pick is a candidate that failed its back-match.
- So S1 is worth about 6.5% of names. Its full-scale cost is about 264 more judge files (about 30M tokens).

## Duplicates (code only, all 4,591 themes)
- Candidates whose name also appears exactly on another theme in the same slot: 101 / 128 / 121 (about 2.5% per slot).
- The uniqueness step (re-ask for colliding themes) will be needed after selection.

## Caveats
- Judges are the same model family as the namers; no human check.
- S1/E1 items for this sample use rendered member titles as multisets, not keys (55 themes have duplicate titles); declared in the PREREG.
- Cost of this check: 20 judge files, about 2.3M subagent tokens (about 4% of the N1 run).

Files: sample/ (PREREG, code sm_*.py, s1/ + s1out/, eval/ + evalout/, selected_sample.json, scores.json; KEY files kept separate).
