# O50 evaluation: criteria C4 and C5 (reviewer, 2026-10-13)

Spec: data/experiments/reviewer_notes/SPEC_overlap_arm_2026-10-12.md (declared 12 Oct). Presentation details: PREREG_note.md
(before judging). Code: code/. Judgements: judged/. Full output: score_output.txt. In-session subagents, no API spend.

## C2 exception (Aviyah, 13 Oct)
btm:M205, an untitled BTM module of adaptor/scaffold genes with an NF-kB arm (CHUK, BAG4, ZFAND6) and a BMP/TGF-beta arm
(BMPR2, RNF111). In c85 its only small homes were three weak TGF-beta/BMP regulation themes (support 0.055-0.105, 10-14
members) that also held two other BTM modules. At 0.50 they were superseded by tighter TGF-beta/SMAD themes without it.
A mixed module with half its biology outside TGF-beta is a plausible loose fit; accepted as a known exception.

## C4 plausibility: PASS
| | themes | not ok | ok |
|---|---|---|---|
| c85 | 8,251 | 195 | 97.64% |
| O50 | 4,602 | 112 (99 carried from identical c85 themes + 13 of 858 new) | 97.57% |
New themes: 845 of 858 ok (98.5%). The not-ok are mostly the 4 new giants (grab-bags, as before) and a few core plus misfits.

## C5 usefulness: O50 WINS
120 pathways, blind, both theme sets in full, sides randomised. O50 preferred 87, c85 33, equal 0: 72.5% of decided,
binomial p = 9e-7 (bar 60% and p < 0.05).
- Why O50 wins: the same contexts without the near-duplicate repeats.
- Why c85 sometimes wins (28%): it kept a context O50 lost (e.g. a broader CDK4/6-RB theme, ER-phagy, Gq/PLC calcium).
  The cleanup costs some real facets, consistent with distinct homes falling from 79% to 66% of pathways.

## Overall, by the spec's decision rule
C1 pass, C2 fail accepted as an exception by Aviyah, C3 pass, C4 pass, C5 won. O50 qualifies as the candidate working
version. Adoption, freezing and merging the branch are Aviyah's decision.
