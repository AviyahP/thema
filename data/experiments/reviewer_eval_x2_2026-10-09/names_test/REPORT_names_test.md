
## 11. Name-embedding test (pre-registered; run 10 Oct)

- **Inputs:**
  - ccode embedded all 8,251 theme names (prompt 29; manifest names_test/name_vecs_manifest.json).
    - Primary: the MedCPT article encoder, name as the title.
    - Secondary: the MedCPT query encoder.
  - 249 sibling pairs have identical names.
- **Labels:** name-blind verdicts (1,499 pairs).

| feature | AUC | half1 / half2 | J-band | AUC vs original labels |
|---|---|---|---|---|
| N1 name cosine (article) | 0.670 | 0.651 / 0.687 | 0.660 | 0.709 |
| N1 name cosine (query) | 0.659 | 0.633 / 0.685 | 0.648 | 0.704 |
| N2 name direction from parent (article) | 0.510 | 0.515 / 0.506 | 0.507 | 0.536 |
| md (fewest differing pathways) | 0.698 | 0.715 / 0.681 | 0.684 | 0.694 |
| C4 member-centroid cosine | 0.640 | 0.649 / 0.633 | 0.610 | 0.680 |
| J | 0.588 | 0.591 / 0.585 | 0.519 | 0.652 |

### Matched-volume comparison (560 pairs each; name threshold N1 ≥ 0.9877)

| | cutoff rule | name rule |
|---|---|---|
| precision on the sample | 70.2% (131 sampled) | 69.7% (145 sampled) |
| extrapolated, twins / facets | 393 / 167 | 390 / 170 |

- Difference (name − cutoff): −0.7 points, 95% CI −10.5 to +9.0.
- The two selections share only 96 pairs, so they pick different pairs.
- The name rule's selection by J band: 130 (0.4–0.5), 267 (0.5–0.6), 163 (0.6–0.7). Only 38% of it has md ≤ 2.

### Blind strength set (names never shown)

- N1 separates twin controls from facets that remain: AUC 0.667.
- N1 does not track facet strength: Spearman 0.00.

### Pre-registered verdict

- Names fail the viability bar: AUC 0.65 / 0.69 in the two halves, below 0.70.
- Names do not beat the cutoff rule at matched volume.
- **The cutoff rule stands by the declared rule.** Both rules run at about 70% precision.
- Name direction (N2) carries no signal.

### Post-hoc (labelled)

Names and md are complementary signals. Twin share (name-blind) by md and by name-similarity tercile:

| | lowest third of name similarity | middle third | top third |
|---|---|---|---|
| md ≤ 2 | 52% | 63% | 75% |
| md 3–5 | 20% | 38% | 56% |
| md ≥ 6 | 3% | 10% | 14% |

- md ≤ 2 and top third of name similarity: 644 pairs in the population, 75% twin.
- md ≤ 2 and identical names: 96% twin (n = 23 sampled).
- These combinations were not pre-registered.
