# Core-reading, low-overlap siblings: pre-registration (reviewer, 2026-10-11, before any result)

Question (Aviyah): do siblings that share LESS re-read their shared pathways differently (e.g. a platelet core read as
clotting under one sibling and as immune signalling under another)? The first pilot (J 0.4-0.7) found almost none.

Sample: non-nested sibling themes (share >= 1 non-giant parent), each 3-200 members, shared core >= 3 pathways,
J in [0.1, 0.4). Population: 2,087 / 2,313 / 2,343 pairs in J 0.1-0.2 / 0.2-0.3 / 0.3-0.4. Random 80 per band
(240 pairs), seed 20261015. No twin/facet labels exist here; this measures prevalence.

Procedure: same prompts as the first pilot (../core_reading_pilot_2026-10-11/spec/R1_reader.md, C1_compare.md).
Three one-sided readings per pair, each in a separate reader set (no context sees two readings of one pair):
- A: shared + A's additional pathways;  B: shared + B's additional pathways;
- A2 (noise control): shared + A's additional pathways again, different reader, different order.
Comparisons (fresh judges, shuffled, blind to which is which): A vs B (effect) and A vs A2 (noise).
Score same / partly / different.

Primary outcome per band: re-reading rate = share of A-B pairs judged partly-or-different minus the same share for
A-A2; bootstrap 95% CI. Secondary: "different" alone; trend across bands; comparison with the first pilot (J 0.4-0.7:
0% different, 23% partly overall).
Declared reading: re-reading is "present" in a band if the excess is >= 15 points and its CI excludes 0.
