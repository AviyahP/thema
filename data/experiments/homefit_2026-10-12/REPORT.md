# Home-fit test: report (reviewer, 2026-10-13)

Pre-registration: PREREG.md (written 12 Oct before any item was built). Build: code/hf_build.py. Score: code/hf_score.py,
full output score_output.txt. 5 judges (in-session subagents, no API spend), 20 pathways each; key never shown.

Sample: 4,354 c85 pathways have 2+ clearly distinct homes; 4,180 eligible (all homes <= 100 members); 100 drawn (seed
20261013). The 4-home cap bound in 31 items. Decoy = the nearest theme in embedding space not containing the pathway, with
J < 0.4 to every home.

## Results
| | yes or partly (primary) | strict yes |
|---|---|---|
| P1 real homes fit | 94.0% (CI 90.8-96.8) | 50.4% (CI 44.7-56.1) |
| P2 decoy fits | 95.0% (CI 90.0-99.0) | 38.0% (CI 29.0-48.0) |
| P1 - P2 | -1.0 (CI -5.8 to +3.7) | +12.4 (CI +1.8 to +23.2) |
- P3: of 97 pathways with 2+ fitting homes, 83.5% judged "different aspects", 16.5% "same aspect".
- Home fit falls only for the largest homes (41-100 members: 56%, n = 9); it rises with support (89% / 91% / 97%).

**Declared reading: NOISE** (the P1 - P2 CI includes 0).

## What it means
- The homes fit and mostly show different aspects of the pathway (94% fit; 84% different aspects). They are not random.
- But the judges accept the nearest non-home just as readily, so the test cannot show that resampling's choice of homes is
  better than "the closest themes in text space". On strict "yes" the real homes do win (+12 points, CI excluding 0), a
  modest edge, post-hoc.
- Two readings, not separable with this design: (a) the decoy is itself a legitimate home the build missed (it was chosen
  as the closest theme, so it is a hard, partly valid control); (b) the judges' "partly" is too lenient to discriminate.
- Consequence: the facets are plausible, but their added value over a cheap nearest-theme assignment is not demonstrated.

## Proposed follow-up (not run; to be pre-registered)
Same items plus a RANDOM decoy (size-matched, far in embedding space) to check that judges can say no at all; and a
head-to-head of resampling homes vs nearest-theme homes for the same pathways.

## Addendum (13 Oct, post-hoc; Aviyah's objection): the decoy was mostly inside the pathway's own region
Aviyah pointed out that the nearest themes are pre-cleanup and full of variants. Checked (code/hf_decoy.py,
decoy_check_output.txt):
- 85% of decoys lie entirely inside a larger theme that DOES contain the pathway; 87% have >= 80% of their members inside one.
- 60% have J >= 0.5 with some theme containing the pathway (a variant of a theme the pathway is in).
So the "decoy" was usually a sub-part or variant of the pathway's own neighbourhood, not a non-home. The control was
confounded by the redundancy, and the NOISE verdict does not count against the algorithm. It stands as recorded, with this
caveat. Separately, on the 13 decoys that were outside the region the judges still said no 0 times (5 yes, 8 partly):
small n, but it suggests "partly" is lenient.
Redo needed: decoys outside the pathway's region (no theme containing the pathway contains or overlaps them at J >= 0.4),
and a forced choice (which of two groups is the better home) instead of yes/partly/no.
