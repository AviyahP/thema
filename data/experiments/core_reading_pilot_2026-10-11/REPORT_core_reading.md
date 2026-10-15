# Core-reading pilot — results (reviewer, 2026-10-11). Pre-registration: PREREG.md

Idea (Aviyah): a facet re-reads the SHARED pathways differently depending on its additional pathways; a twin keeps the
same reading. Test: 300 sibling pairs (150 twin, 150 facet by the full-list name-blind labels, stratified by J band).
Two one-sided readers per pair (shared + one side's additional pathways, separate contexts), then a blind comparator
(shared list + the two readings): same / partly / different.

| verdict | twins (150) | facets (150) |
|---|---|---|
| same | 134 | 97 |
| partly | 16 | 53 |
| different | 0 | 0 |

| signal | AUC | halves | J-band |
|---|---|---|---|
| core-reading (0/1/2) | 0.623 | 0.613 / 0.632 | 0.629 |
| md (fewest differing pathways) | 0.664 | 0.673 / 0.657 | 0.669 |
| name cosine N1 | 0.635 | 0.575 / 0.684 | 0.637 |
| J | 0.511 | | |
Core-reading minus md: -0.04 (95% CI -0.11 to +0.03). Against the original labels: 0.630.
Rule "partly = facet": accuracy 62%, facet recall 35%, twin recall 89%.

Verdict vs pass bar (AUC >= 0.75): FAIL. Not better than the label-free md signal.

Reading:
- Among high-overlap siblings (J 0.4-0.7) readers almost always describe the shared core the same way: no pair was
  judged "different"; 65% of judged facets and 89% of twins got "same". The facet calls made by earlier judges rest
  mostly on what the additional pathways add, not on a re-reading of the core.
- Under Aviyah's definition (facet = the core is re-read), most high-overlap sibling facets would count as
  "same core + extension"; only about a third show even a partial re-reading.
- Design limits: readers saw the full shared list, which anchors similar core descriptions; the comparator saw no
  additional pathways (by design). Low-overlap facets (e.g. platelet core under several parents, J < 0.4) were not in
  the sample.
Raw readings: raw/; comparisons: compare/; code: code/cr_*.py.
