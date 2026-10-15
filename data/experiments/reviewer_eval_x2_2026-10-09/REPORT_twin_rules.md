# Is there a non-LLM rule that separates twins from facets? (reviewer, 10 Oct 2026)

**Aviyah's constraints:**
- No LLM judgement in the rule.
- No rule trained on LLM labels.

**Her hypothesis:** real facets do not merge up to the same (close) parent.

**Test:** the 5,567 judged sibling pairs (twin 2,752 / facet 2,815) are used ONLY to evaluate fixed, untrained features. Nothing is fitted. AUC = probability that a random twin scores higher than a random facet (0.5 = no signal, 1.0 = perfect).

| feature (no LLM, no fitting) | AUC |
|---|---|
| overlap J | 0.64 |
| parent-set overlap (do they share the same parents?) | 0.52 |
| number of shared parents | 0.50 |
| union fills the smallest shared parent (\|A∪B\| / \|P\|) | 0.49 |
| size of the smallest shared parent (smaller → twin) | 0.62 (as 1 − 0.38) |
| overlap of descendant themes | 0.51 |
| support (minimum; ratio) | 0.52; 0.50 |
| size ratio | 0.54 |
| embedding similarity of A-only vs B-only pathways | 0.55 |
| A-only / B-only similarity to the shared core | 0.52 |

**Result:** no structural feature separates twins from facets. Parent relations, descendants and support carry essentially no signal. Only overlap (0.64) and a smaller shared parent (0.62) carry a weak one, and even the embedding test is weak (0.55).

**The labels are not noise.** 88 pairs were judged twice by independent judges (once in the 240-pair sample, once in the full run), and the two agree on 87.5%. The distinction is real, but it lives in what the pathways mean, which none of the structural measures capture.

## Implication

A clean non-LLM merge rule does not exist in the current structure. The choices are:

1. **No construction merge.** Keep the twins and show twin families as "variants" in the browser. The statistics layer treats overlapping families as one test family (cf. the stats considerations note).
2. **A high overlap-only cutoff** (sibling pairs at J ≥ 0.65: 351 pairs, 28% wrong): a small, imperfect cleanup.
3. **Accept that overlapping alternative boundaries are part of a resampling-built DAG** and report them, e.g. a "variant family" id per theme computed by overlap only (J ≥ 0.5 among siblings), explicitly labelled as possibly mixing twins and facets.

**Reviewer's recommendation:** option 1 (or option 3 as its implementation).

## Addendum (2026-10-10): "facets have distinct parents" test

Hypothesis (Aviyah): real facets, besides their shared parent, also have their own parent within 1-2 levels that does not hold the other cluster; twins share all nearby parents.

Test: 5,567 judged sibling pairs (J >= 0.4; 2,752 twin / 2,815 facet). Private parent = parent of A that is not an ancestor of B (existence at depth 1 equals existence at depth 2-3, since privacy propagates down). Rules fixed, not fitted; LLM labels used only to score.

- Both have a private parent: 1,657 pairs, 53.4% facet (base 50.6%). Either: 51.2%. AUC ~0.48-0.49.
- Ancestor-set Jaccard at depth 1/2/3: AUC 0.52 / 0.54 / 0.56.
- Distinctness of the private parent (J with shared parent; share of the other cluster it contains; overlap of extra members with the shared parent's extras): AUC 0.51-0.58.
- Truly distinct private parent (contains < 60% of the other cluster): 36 pairs, 69% facet. Precision ~70%, but covers ~1% of facets.
- Why: private parents are mostly variants of the shared parent (median J 0.55 with it; they contain ~75-78% of the other cluster) - for twins and facets alike.
- Example where it works (J < 0.4, not a merge candidate): n00940 caspase-8 apoptosis vs n01233 necroptosis, shared parent n01957; n00940 has private parents holding 0% of n01233 (n02890, n05344, n01881). Twin pair n01695|n04613 has no private parents (only n02173).
- Twin families: depth spread 0 levels for 606/987 families; families of >= 10 themes span a median of 3 levels.

Conclusion: the idea holds for clearly separated facets (low overlap) but does not separate twins from facets among high-overlap siblings. Scripts: privanc.py, privanc2.py.
