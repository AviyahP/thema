# Name-embedding rule vs the accepted cutoff rule: pre-registration (reviewer, 2026-10-10, before any result)

Question (Aviyah): can embeddings of the theme NAMES separate twins from facets, as a standalone ALTERNATIVE to the
accepted cutoff rule (J >= 0.6 and min(|A-B|,|B-A|) <= 2, complete linkage)?

## Inputs
- Names: theme_names_c85.tsv, the existing per-theme labels for all 8,251 c85 themes (written one theme at a time in
  the plausibility census, never seeing pairs). No new naming.
- Embedding (by ccode on the Mac; Hugging Face is unreachable from the reviewer VM): primary = the pinned MedCPT
  article encoder (ncbi/MedCPT-Article-Encoder, revision d05a736d...), name as the title, CLS pooling, L2-normalised.
  Secondary (reported, not decisive) = ncbi/MedCPT-Query-Encoder.
- Reference labels: NEW name-blind twin/facet verdicts on a random 1,500 of the 5,567 judged sibling pairs (seed
  20261011; J bands 592 / 621 / 287). Same rubric and the SAME pathway samples as the original judge, but no theme
  names shown. Key: KEY_DO_NOT_SHARE.json (never shown to judges).

## Features
- N1 = cosine(name A, name B). Higher -> twin.
- N2 = cosine(name A - name P, name B - name P), P = smallest shared parent. Higher -> twin.

## Analyses (all on the name-blind labels unless stated)
1. Agreement of name-blind vs original verdicts (how much the names drove the original judge).
2. AUC of N1, N2 (and J, md, C4 for reference): all, two random halves, J-band stratified.
3. Matched-volume comparison: name rule = the 560 sibling pairs (of 5,574) with the highest N1, i.e. the same number
   of pairs the cutoff rule selects. Compare precision (share twin) and facets selected, on the judged sample,
   pair level and after complete linkage. Bootstrap 95% CI of the precision difference (2,000 resamples).
4. Secondary: same comparison on the blind strength ratings (586 pairs; names never shown there either).

## Decision rule (declared)
- The name rule is a viable alternative only if N1 AUC >= 0.70 in both halves AND J-band-stratified >= 0.60.
- It beats the cutoff rule only if its precision at matched volume is higher and the bootstrap CI excludes 0.
- Otherwise the cutoff rule stands. No thresholds are tuned on the labels; post-hoc additions are labelled.
