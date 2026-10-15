# Naming style pilot: result (reviewer, 15 Oct 2026)

Pre-registration: PREREG_style.md, written before any rewrite. The 200 sample themes were each judged under both names by the same fresh judges, mixed and blind to which was which.

| | OLD (current lite names) | NEW ("unifying idea (key parts)") |
|---|---|---|
| E1, name picks its own theme among 5 | 97.5% | **98.0%** (D1 +0.5 points, CI -2.0 to +3.0) |
| E2 member fit | 0.932 | **0.952** (D2 +0.019, CI +0.011 to +0.028) |
| P1 pairwise preference, decided pairs | 60 | **127** (67.9%, p = 1e-6); 13 equal |
| list-style names | 67 of 200 | 0 heads |
| median words | 7 | 10 |

**Verdict by the declared rule: STYLE PASSES on the model judges.**
- D1's CI lower bound is -2.0, above the -3 bar.
- E2(NEW) is 0.952, at least 0.90, and D2 is positive.
- P is above 50% with p < 0.05.

Final adoption still needs **H1**: Aviyah's blind rating of 30 pairs (H1_pairs_for_Aviyah.md; key kept separate). It is put aside by her choice.

**Notes:**
- The rewriter marked 4 themes as having no honest unifying idea. Two of them match known mixtures; the flag could become a mixture signal:
  - n03491 HGF-MET + TGF-beta;
  - n03950 gluconeogenic amino acids + choline-carnitine;
  - n04008 ascorbate + thyroid hormonogenesis;
  - n04049 nucleocytoplasmic transport + GTPase gene modules.
- E1 flips: 3 themes went from right to wrong (cohesion, RNA Pol II, DSB response) and 4 from wrong to right.
- Names are longer: a median of 10 words against 7. The brackets carry the parts.
- Cost: 8 rewriter files plus 20 judge files, about 2.7M subagent tokens.
- Not decided: restyling all 4,591 themes (very roughly 15-20M tokens). Aviyah decides after H1.

Files: spec/N3_style.md, spec/P1_preference.md, st_*.py, inputs/, raw/, eval/, evalout/, new_names.json, scores_style.json, H1_pairs_for_Aviyah.md.
