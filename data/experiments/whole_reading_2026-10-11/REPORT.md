# Whole-theme reading test: report (reviewer, 2026-10-11)

Pre-registration: PREREG.md (written before any result). Scored by code/wr_score.py; full output in score_output.txt.

## What was done
- 780 themes were each read whole (complete undivided list, no marks) by blind readers (W1), who wrote a short story:
  what the theme is about, what forms its centre, and the role of the other pathways.
- 420 comparisons (W2): the judge saw both complete lists with [shared] marks plus both stories, and said whether the shared
  pathways play the same, a partly shifted, or a different role. All items were mixed and shuffled; one judge per item.
- Sets: HIGH = the same 300 high-overlap pairs as the first core-reading pilot (J 0.4-0.7); LOW = 60 low-overlap pairs
  (20 per J band 0.1-0.4); SYN = 60 synthetic variants (A vs a random 70% of A) as the false-positive floor.

## Results
| set | n | same | partly | different | partly-or-different |
|---|---|---|---|---|---|
| HIGH | 300 | 273 | 27 | 0 | 9.0% (CI 6.0-12.3) |
| LOW | 60 | 36 | 22 | 2 | 40.0% (CI 28.3-51.7) |
| SYN (floor) | 60 | 58 | 2 | 0 | 3.3% (CI 0-8.3) |

1. HIGH minus floor: +5.7 points (CI -0.3 to +10.7).
2. Same 300 pairs, old split design 23.0% -> whole design 9.0%. 52 pairs lost their re-reading, 10 gained one.
3. LOW minus floor: +36.7 points (CI +23.3 to +50.0). By band (new vs old design on the same pairs): 0.1-0.2 60% vs 75%;
   0.2-0.3 25% vs 35%; 0.3-0.4 35% vs 45%.

Declared reading: CONFIRMED (HIGH minus floor <= 30%). Reading the whole theme did not uncover hidden re-readings at high
overlap; it found fewer. The design still detects re-reading where it exists (LOW is clearly above the floor).

Secondary (labels uncertain): twins 5% re-read, facets 13%. AUC vs the full-list labels: whole reading 0.54, old core
reading 0.62, md 0.66. Re-reading does not rise with md inside the high-overlap range (12% / 6% / 7% / 12% at md 2/3/4/5).

## Interpretation
- At J 0.4-0.7, about 9 in 10 sibling pairs tell the same story about their shared pathways when each is read as a whole.
  The ~1 in 10 that do re-read are mostly emphasis or centre swaps (e.g. UV response as the centre vs as the trigger of
  senescence), not different biology; no high-overlap pair was judged "different".
- The old design's 23% was probably partly an artefact of asking readers directly about the role of a marked core: that
  question invites a shift. Caveat: the whole design is also more conservative at low overlap (about 0.75x the old rate),
  so part of the drop at high overlap is design sensitivity; even so HIGH fell more (0.39x) than LOW.
- Re-reading is a property of overlap level, not of the twin/facet label: it is near the floor at J >= 0.4 and common at
  J < 0.4. That supports describing high-overlap siblings as variants of one theme, and the real facets as siblings that share
  little.

## Limits
- One reader per theme and one judge per item; judge severity is known to vary (23-62% twin rates across judges earlier).
- SYN subsets keep 70% of members; real variants differ by both removal and addition, so the floor may be slightly low.
- All readers and judges are LLMs (Claude subagents) used for evaluation only; nothing here feeds construction.
