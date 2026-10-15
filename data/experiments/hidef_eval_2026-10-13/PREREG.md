# HiDeF vs THEMA c85: coherence, nameability, twins, facets (reviewer pre-registration, 2026-10-13, before any result)

Question (Aviyah): for the best HiDeF result, are clusters coherent and easy to name? Are there facets, how do they compare
to THEMA's, and are there twins?

Arms. HiDeF = data/ontology/v0.4-leaves/hidef_L_k4_maxres800 (the setting chosen on the tuning half in the leaves
experiment, 8 Oct; 2,447 themes, universe L, 5,559 leaves). THEMA = thema_L_x2_c85 (8,251 themes; universe x2, 5,539 leaves,
L minus 20 exclusions). Structural comparisons use pathways present in both universes. Giants (>= 1,000 members) excluded
from both, as in all earlier THEMA analyses.

## Part 1, structural (code only, report all)
- Themes by size band (3-6, 7-15, 16-40, 41-100, 101-1000), roots, share with 2+ parents not nested in each other.
- Twins: sibling pairs (share a parent, neither contains the other) at J >= 0.4, >= 0.5, >= 0.6; also any non-nested pair
  at J >= 0.5 regardless of parent; per 1,000 themes.
- Facets: per pathway, homes (smallest themes containing it) and clearly distinct homes (pairwise J < 0.4, greedy by
  size since HiDeF has no support), as in facets_real.py; share of pathways with 2+ and 3+ distinct homes.
- Correspondence: for pathways with 2+ distinct homes in both builds, the share of THEMA's distinct homes matched by a
  HiDeF theme containing the pathway at J >= 0.5, and the reverse.

## Part 2, blind judging (in-session subagents, no API spend)
- Sample: 100 themes per arm, size 3-100, stratified to the same size distribution (bands 3-6, 7-15, 16-40, 41-100, with
  per-band counts set by HiDeF's own distribution in 3-100), seed 20261013. Report the share of each arm above 100.
- Items mixed and shuffled, arm hidden, complete member lists, no names. 5 judges x 40 items.
- Judges give (a) the rubric4 verdict (coherent / umbrella / core_plus_misfits / mixture / incoherent) and (b) a specific
  name (<= 10 words) and nameability: easy (one specific name fits all) / broad (only a general name fits) / hard.
- Primary: ok rate (coherent or umbrella) per arm; "easy" nameability per arm; differences with bootstrap 95% CIs.
- Declared reading: an arm is better on a measure if the difference is >= 10 points and its CI excludes 0; otherwise
  equivalent.
