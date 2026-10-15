# Core-reading pilot: pre-registration (reviewer, 2026-10-11, before any result)

Idea (Aviyah): a real facet re-reads the SHARED pathways differently depending on its additional pathways; a twin keeps
the same reading of the shared core and only adds pathways.

Sample: 300 sibling pairs from the full-list re-judged set (fulllists_test, name-blind, complete unique lists):
150 twin + 150 facet, stratified by J band (0.4-0.5 / 0.5-0.6 / 0.6-0.7) proportional to the band's share; seed 20261014.
Procedure (prompts in spec/):
- R1 reader, one-sided: COMPLETE shared list + COMPLETE additional list of ONE side. Each pair's two sides are read by
  different reader contexts (side-1 batches and side-2 batches never share a context); no names, no labels.
- C1 comparator (fresh contexts): the complete shared list + the two readings (theme + core_role); additional lists not
  shown. Verdict same / partly / different.
Score: 0 / 1 / 2 (same / partly / different); higher = facet.
Primary: AUC of the score for facet vs twin (full-list labels), all pairs, two random halves (seed 0), J-band stratified.
Pass bar: AUC >= 0.75 in both halves and J-band-stratified >= 0.70.
Reported: AUC of md and of name cosine N1 on the same pairs; AUC against the original labels; distribution by label.
Reference ceiling: independent judging rounds agree on ~82-88% of pairs.
Use if it passes: labelling / variant flag and the basis for a next naming version; not a construction rule.
