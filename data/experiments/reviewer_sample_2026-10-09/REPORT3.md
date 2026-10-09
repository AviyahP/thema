# Third plausibility sample + platelet lattice + heterogeneous-BTM decision (2026-10-09)

## 1. Third sample: 20% of the not-yet-checked themes, bands 3-100
1,400 themes (seed 20261011, no overlap with samples 1-2; sample3.json). Same rubric (rubric4.md), 16 reviewer subagents, judged3.json.

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 77 | 75 | 2 | 0 | 0 | 0 | 100.0% |
| 6-10 | 339 | 305 | 25 | 5 | 2 | 2 | 97.3% |
| 11-20 | 699 | 600 | 82 | 11 | 2 | 4 | 97.6% |
| 21-50 | 251 | 207 | 36 | 4 | 4 | 0 | 96.8% |
| 51-100 | 34 | 27 | 7 | 0 | 0 | 0 | 100.0% |
| all | 1400 | 1214 | 152 | 20 | 8 | 6 | 97.6% |

All three samples together: 3,077 of 3,153 themes ok (97.6%), about 36% of all themes of size 3-100, plus all 42 themes over 100 checked in round 1.
- 5 of 6 incoherent themes contain self-described heterogeneous BTMs (n03171, n05940, n05923, n02238, n03453, n00908; also misfits in n03881). The sixth (n04339) is a set of GO "response to drug/ethanol/anesthetic" terms.
- Mixtures: Notch + Hedgehog (43; strict call, the two share developmental roles but no single mechanism); gonad + placenta (29); protein lipidation + lipid transfer (29); MET + TGF-beta (27); PS scrambling + ER shaping; RUNX3 targets + cadherin transcription; xenobiotic responses + BH4; one heterogeneous-BTM set.
- Recurring near-misses: lipid-transfer vs protein-lipidation themes mix (n06445, n05593, n08093, n07823); generic "transcriptional repression / cadherin" terms attach to TF-target themes.

## 2. Decision: drop self-described heterogeneous BTMs from the next construction (Aviyah, 2026-10-09)
Rule (declared before applying): an unnamed ("TBA") BTM whose generated description (written by our LLM from genes only) states in its first sentence that no single/coherent process unites the genes, or calls the set heterogeneous or loosely connected.
Result: 17 modules: M125, M153, M184.1, M211, M218, M221, M233, M241, M246, M32.5, M41.0, M41.1, M41.3, M70.0, M72.0, M72.2, M98.1.
(Earlier count "18" came from a looser text pattern; the declared rule gives 17. Named BTM M213 "regulation of transcription" also matches the words but has a name and a coherent theme, so it stays.)
Borderline by content but inside the rule: M125 and M233 name a loose shared bias (differentiation, developmental patterning); M184.1 names a JNK core.
Note: removing 17 of the input sets changes the universe; ccode to say whether the cal8 floors need re-validation (cheap: fresh-seed FDR check) rather than full recalibration.

## 3. Lattice above n00150 (the 7 core platelet-receptor pathways)
28 ancestors: 4 are giant roots (n01755, n03678, n05127, n06313; excluded, known bags), 24 judged.
- Coherence: all 24 are coherent platelet/hemostasis themes. One misfit: VEGFR2 cell proliferation in n07791.
- The 6 parents lead into 3 distinct routes:
  A. Platelet activation proper (4 parents: G12/13-actin, cytoskeleton/BTM platelet, GPVI/LDL, Rap1) -> platelet activation and adhesion n00918 (27, support 0.85) -> hemostasis n02115 (77, support 0.86: platelets + coagulation + vitamin K + fibrinolysis).
  B. Prostanoid/GPCR receptor family (n05795) -> hemostasis + eicosanoids n03423 (139).
  C. Gq / G12/13 GPCR signalling (serotonin facet n06563) -> amine and lysophospholipid receptor signalling n07791 (17) -> giant root.
  B and C are real, distinct routes. They rejoin A only through n04419 (52; child of both n02115 and n03423) and the giants.
- Inside route A the levels in between are over-resolved: about 14 nodes of 13-41 members form a staircase of near-nested supersets, each adding 2-6 members, most with support 0.035-0.17. They are the same theme with slightly different edges, not different facets.
  Chain ratios (child/parent size): n07792->n03907 0.89, n03820->n04961 0.87, n03907->n05156 0.86, n03842->n08023 0.85, n00918->n01879 0.84, n05194->n06758 0.82, n01879->n08023 0.80.
- What candidate rules would do here: chain collapse at 0.85 removes 4 rungs (at 0.80, 7 rungs). Sibling merge at J >= 0.6 would merge 3 of the 6 parents (n01638-n03581 0.62, n01638-n05989 0.62, n03581-n05989 0.69) into one cytoskeleton/integrin facet, leaving 4 facets; at J >= 0.7 none merge.
- Correction to the earlier statement "no common ancestor within 3 levels": true for all 6 jointly; 4 of the 6 share n00918 within 2-4 levels.
