# Twin vs facet: pre-registered hypothesis search (reviewer, 2026-10-10, written before any result)

Pairs: the 5,567 judged sibling pairs (J >= 0.4; twin 2,752 / facet 2,815; 7 unclear excluded).
Labels are used ONLY to score fixed formulas. Nothing is fitted, no weights, no thresholds tuned.
Notation: C = A and B (core), a = A only, b = B only, U = A or B, S = smallest non-giant shared parent.
Direction: T = expected higher for twins, F = expected higher for facets.

Variant family (no LLM): connected component of graph G whose nodes are themes and whose edges are
the sibling pairs (non-nested, share a non-giant parent) with J >= 0.4.

## Features
A. Difference blocks: A1 min(|a|,|b|) F; A2 |a|+|b| F; A3 min/max(|a|,|b|) F; A4 |C| T.
B. Inclusion (members.tsv, resampling): B1 mean inclusion of a in A and b in B F; B2 min of the two F;
   B3 mean inclusion of C in A and B T; B4 share of a+b members with inclusion < 0.5 T.
C. Embedding (centred vectors): C1 block contrast (within a, within b) minus cross a-b cosine F;
   C2 cos(centroid a, centroid b) T; C3 silhouette of a vs b F; C4 cos(centroid A, centroid B) T;
   C5 mean within-A/within-B cosine minus mean within-U cosine F.
D. DAG: D1 private child (max over children c of |c and a|/|c|; min over the two sides) F;
   D2 a theme with J >= 0.7 to C exists F; D3 a theme other than S with J >= 0.7 to U exists T;
   D4 min number of children F; D5 |depth A - depth B| F; D7 min number of parents F.
E. Family graph G: E1 common neighbours T; E2 neighbour-set Jaccard T; E3 family size T;
   E4 family edge density T; E5 same community (greedy modularity, J-weighted) T;
   E6 edge betweenness within family F; E7 J minus family median J T.
F. Resampling runs (x2 trees, 200 runs; co-clustered = same cluster of size <= s,
   s = smallest of 8,16,...,512 that is >= |U|): F1 cross a-b co-clustering T;
   F2 (within a, within b) minus cross F; F3 mean co-clustering over all U pairs T;
   F4 F1 at the next scale (2s) T; F5 runs where the modal cluster of A's members equals B's T.

## Scoring and pass rule (declared)
- AUC in the declared direction (0.5 = none). Reference: J = 0.64; judge repeat agreement 87.5%.
- A finding must have AUC >= 0.65 in BOTH random halves (seed 0) AND J-band-stratified AUC >= 0.60
  (bands 0.4-0.5, 0.5-0.6, 0.6-0.7, pooled), i.e. signal beyond overlap.
- Also reported: family-stratified AUC (within families holding both labels).
- No combinations of features are fitted. Anything added after seeing results is labelled post-hoc.
