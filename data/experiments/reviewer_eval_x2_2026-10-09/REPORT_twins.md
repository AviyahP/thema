# Side-by-side twins: what an overlap cutoff would do (reviewer, 10 Oct 2026)

**Working version:** thema_L_x2_c85, themes under 1,000 members.
**Question (Aviyah):** merge side-by-side twins with an overlap-only rule (no LLM judgement in the rule). First assess what it would do. This is analysis only; nothing was changed.

## 1. Where the twins are

The 0.70 consensus merge already removes everything at J ≥ 0.70, so non-nested overlapping pairs sit at J 0.4-0.7:

| J | pairs | of which siblings (share a parent) | themes involved |
|---|---|---|---|
| 0.4-0.5 | 10,853 | 2,761 | 6,597 |
| 0.5-0.6 | 6,638 | 2,531 | 5,515 |
| 0.6-0.7 | 2,500 | 1,286 | 3,294 |

## 2. Merging is transitive, so groups chain

Merge groups if every pair at or above the cutoff is merged:

| cutoff | all pairs: themes -> groups (largest group; largest union) | siblings only |
|---|---|---|
| 0.50 | 5,951 -> 555 (209 themes; 1,104 members) | 4,504 -> 1,235 (31) |
| 0.60 | 3,294 -> 1,027 (21; 1,104) | 2,112 -> 863 (10) |
| 0.65 | 1,289 -> 553 (7) | 744 -> 348 (4) |
| 0.68 | 490 -> 230 (4) | 266 -> 129 (3) |

## 3. The controls overlap in the same range

- **The platelet facets** (parents of the 7-member core n00160) overlap each other at J 0.53-0.54. Any cutoff ≤ 0.54 merges them.
- **The hematopoietic stem cell variants** (25 themes containing GO:1902033 with near-identical labels) overlap at J 0.40-0.64; most pairs are 0.40-0.56.
- So the twins we want merged and the facets we want kept sit at the **same overlap values**.

## 4. Twin or facet, by overlap band

240 random pairs, 80 per band, were judged by blind reviewers. They saw both labels, the shared pathways and the pathways only in A and only in B (judged_twin_pairs.json, rubric_twins.md).

| J band | twin | facet | twin share |
|---|---|---|---|
| 0.50-0.60 | 32 | 48 | 40% |
| 0.60-0.65 | 44 | 36 | 55% |
| 0.65-0.70 | 49 | 30 (+1 unclear) | 61% |

- Siblings are slightly more often twins than other pairs.
- **Twin examples:** ER unfolded protein response / unfolded protein response (J 0.56); heme biosynthesis and erythropoiesis / erythroid heme metabolism (J 0.63).
- **Facet examples:** telomerase trafficking vs C-strand fill-in under telomere maintenance (J 0.57); purine salvage vs de novo purine synthesis (J 0.54); mRNA decapping / decay vs capping / translation initiation (J 0.60).

## 5. Conclusion

**An overlap-only cutoff cannot separate twins from facets.** In every band, 40-60% of the pairs that would be merged are distinct facets.

- A cutoff of 0.60 would merge 3,294 themes into 1,027 groups. About 45% of those merges would erase a real distinction.
- A cutoff of 0.65 still erases one in three.
- Cutoffs low enough to catch the hematopoiesis variants also merge the platelet facets.

## Options (decision: Aviyah)

1. **No merge in construction; group at display / statistics.** Keep all themes. Present overlapping same-theme families (e.g. J ≥ 0.6) as "variants" in the browser, and let the statistics layer treat a family as one test family. Nothing is destroyed.
2. **Overlap-only merge at a high, siblings-only cutoff** (0.65: 744 -> 348). Small effect, and still about one wrong merge in three.
3. **A deterministic, non-LLM second criterion with overlap:** residual similarity, the embedding cosine between the A-only and B-only pathways. The 240 judged pairs are a labelled set to test it on: declare the test first, then calibrate on half and validate on the other half. The rule itself would use no LLM judgement.

**Reviewer's recommendation:** option 1 now; option 3 only if a construction-level merge is wanted later.
