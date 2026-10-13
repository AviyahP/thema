# Sibling twins vs facets: full search record and the accepted merge rule

Reviewer record, 10 Oct 2026. **Decision:** Aviyah accepted the merge rule in §6 on 10 Oct 2026. **It has NOT been run.** Do not apply it until she says so.

Build: thema_L_x2_c85 (8,251 themes; the working version after chain collapse at 0.85).

## 1. The problem

- **Twin:** two sibling themes that tell the same story with a slightly different boundary.
- **Facet:** a theme containing the pathway that shows a distinct aspect, rather than a step up the same chain.
- **Why twins exist:**
  - Consensus merge (THETA_MERGE 0.70) already merges non-nested themes at overlap J ≥ 0.70.
  - Nested pairs are handled by chain collapse (c85).
  - So twins live between J 0.4 and 0.7: 10,853 non-nested pairs at 0.4–0.5, 6,638 at 0.5–0.6, 2,500 at 0.6–0.7, none at ≥ 0.7.
- **The candidate set:** 5,574 sibling pairs (non-nested, sharing a parent of under 1,000 members, J ≥ 0.4).

## 2. Constraints set by Aviyah

1. No LLM judgement in the construction rule.
2. No rule trained or calibrated on LLM labels ("the half learns from llm judgement"). Labels may only score fixed formulas.
3. Declare rules before results, and label anything post-hoc.
4. Facets of a parent (fans) are intended. Plausibility means a shared theme, not shared genes.

## 3. The reference labels (evaluation only)

- An LLM judge labelled all 5,574 pairs: **twin 2,752, facet 2,815, unclear 7**.
- The judge saw both theme labels, a sample of the shared pathways, and the A-only and B-only pathways.
- Consistency: 88 pairs were judged twice by independent runs, with 87.5% agreement. That is roughly the ceiling any rule can reach against these labels.
- Twin share by overlap band: 37% (0.4–0.5), 52% (0.5–0.6), 68% (0.6–0.65), 72% (0.65–0.7).
- Twin families (from the labels): 987 groups, 3,291 themes. 11% of judged pairs inside a family are facets.

## 4. The search, in order

### 4.1 Overlap cutoff alone

| J ≥ | precision (share twins) | recall (share of twins caught) |
|---|---|---|
| 0.50 | 58% | 70% |
| 0.55 | 64% | 46% |
| 0.60 | 69% | 29% |
| 0.65 | 72% | 9% |

Overlap alone is a weak separator.

### 4.2 First structural features

These are untrained. AUC = probability that a random twin scores above a random facet; 0.5 = no signal.

| feature | AUC |
|---|---|
| overlap J | 0.64 |
| smaller shared parent | 0.62 |
| size ratio | 0.54 |
| parent-set overlap | 0.52 |
| descendant overlap | 0.51 |
| fill of the shared parent | 0.49 |
| support | 0.50–0.52 |
| embedding: A-only vs B-only | 0.55 |
| embedding: residual to core | 0.52 |

Aviyah's first hypothesis ("facets don't merge up to the same close parent") was not supported.

### 4.3 Aviyah's refined hypothesis: facets also have their own distinct parent 1–2 levels up

- A **private parent** is a parent of A that does not hold B. Whether one exists is the same at depths 1, 2 and 3, because privacy propagates down the DAG.
- Both siblings have a private parent: 1,657 pairs, 53% facet (base rate 51%); AUC 0.48.
- Ancestor-set overlap at depths 1/2/3: AUC 0.52 / 0.54 / 0.56.
- Distinctness of the private parent: AUC 0.51–0.58.
- A truly distinct private parent (holding < 60% of the other cluster) occurs in only 36 pairs (69% facet).
- **Why it fails:** private parents are mostly variants of the shared parent. They overlap it by a median J of 0.55 and contain 75–78% of the other cluster.
- **Where it does work:** low-overlap facets. Example: n00940 (caspase-8 apoptosis) vs n01233 (necroptosis); their private parents hold 0% of each other. The twin pair n01695|n04613 has no private parents.

### 4.4 Pre-registered search: 32 fixed features

The file `twin_facet_hypotheses_PREREG.md` was written before any result. It fixed the features, the expected direction of each (T = higher for twins, F = higher for facets), and the pass rule.

- **Pass rule:** AUC ≥ 0.65 in both random halves (seed 0), AND J-band-stratified AUC ≥ 0.60, i.e. signal beyond overlap.
- **Variant family (no LLM):** a connected component of the sibling-overlap graph at J ≥ 0.4.
  - 1,041 families covering 5,225 themes.
  - Sizes: 450 single pairs; 16 families above 30 themes (the largest has 82).
  - 410 families mix twin and facet edges.
- **Notation:** a = A only, b = B only, C = the shared core, U = A ∪ B.

| id | feature | dir | AUC | half1 | half2 | J-band | within family | pass |
|---|---|---|---|---|---|---|---|---|
| J | overlap | T | 0.641 | 0.656 | 0.626 | – | 0.675 | ref |
| A1 | min(\|a\|,\|b\|) | F | **0.700** | 0.706 | 0.695 | 0.676 | 0.725 | **yes** |
| A2 | \|a\|+\|b\| | F | **0.710** | 0.717 | 0.703 | 0.664 | 0.710 | **yes** |
| A3 | min/max(\|a\|,\|b\|) | F | 0.490 | 0.483 | 0.498 | 0.522 | 0.536 | no |
| A4 | \|C\| | T | 0.406 | 0.414 | 0.399 | 0.353 | 0.442 | no (reversed) |
| B1 | inclusion of a, b members | F | 0.528 | 0.517 | 0.538 | 0.511 | 0.527 | no |
| B2 | min block inclusion | F | 0.506 | 0.494 | 0.518 | 0.487 | 0.517 | no |
| B3 | core inclusion | T | 0.502 | 0.501 | 0.503 | 0.514 | 0.530 | no |
| B4 | share of low-inclusion differing members | T | 0.485 | 0.482 | 0.487 | 0.482 | 0.453 | no |
| C1 | embedding block contrast a vs b | F | 0.627 | 0.619 | 0.635 | 0.642 | 0.566 | no |
| C2 | cosine of centroid a vs b | T | 0.550 | 0.551 | 0.548 | 0.583 | 0.488 | no |
| C3 | silhouette a vs b | F | 0.617 | 0.614 | 0.621 | 0.639 | 0.567 | no |
| C4 | cosine of centroid A vs B | T | **0.669** | 0.679 | 0.660 | 0.604 | 0.696 | **yes** |
| C5 | cohesion gain | F | 0.626 | 0.641 | 0.612 | 0.598 | 0.602 | no |
| D1 | private child | F | 0.615 | 0.614 | 0.616 | 0.600 | 0.649 | no |
| D2 | the core exists as its own theme | F | 0.554 | 0.547 | 0.560 | 0.564 | 0.538 | no |
| D3 | the union exists as a theme | T | 0.522 | 0.540 | 0.504 | 0.523 | 0.528 | no |
| D4 | min number of children | F | 0.594 | 0.593 | 0.596 | 0.614 | 0.585 | no |
| D5 | depth difference | F | 0.521 | 0.518 | 0.523 | 0.517 | 0.506 | no |
| D7 | min number of parents | F | 0.505 | 0.499 | 0.511 | 0.500 | 0.478 | no |
| E1 | common neighbours in family | T | 0.557 | 0.565 | 0.549 | 0.543 | 0.535 | no |
| E2 | neighbour-set overlap | T | 0.558 | 0.568 | 0.548 | 0.541 | 0.537 | no |
| E3 | family size | T | 0.496 | 0.502 | 0.490 | 0.493 | 0.500 | no |
| E4 | family density | T | 0.514 | 0.509 | 0.520 | 0.516 | 0.500 | no |
| E5 | same community | T | 0.514 | 0.515 | 0.513 | 0.504 | 0.522 | no |
| E6 | edge betweenness | F | 0.534 | 0.541 | 0.527 | 0.521 | 0.532 | no |
| E7 | J minus the family's median J | T | 0.626 | 0.637 | 0.615 | 0.527 | 0.675 | no |
| F1 | run co-clustering of a with b | T | 0.571 | 0.582 | 0.560 | 0.588 | 0.528 | no |
| F2 | run block contrast | F | 0.603 | 0.607 | 0.599 | 0.615 | 0.550 | no |
| F3 | run cohesion of U | T | 0.539 | 0.554 | 0.525 | 0.546 | 0.525 | no |
| F4 | F1 at twice the scale | T | 0.565 | 0.576 | 0.553 | 0.580 | 0.523 | no |
| F5 | same modal run cluster | T | 0.593 | 0.607 | 0.579 | 0.567 | 0.615 | no |

**Passed:** A1, A2 and C4.

- "Twins are more connected to each other" (E1, E2) is weak.
- Resampling-run, inclusion and DAG-position features fail.

### 4.5 Post-hoc diagnostics (labelled post-hoc)

- Theme size |U| on its own reaches AUC 0.66: larger pairs are judged facets more often.
- Stratified by J band × size: A1 drops to 0.60, while C4 holds at 0.67.

Number of differing pathways on the smaller side vs the share judged twin:

| min(\|a\|,\|b\|) | 1 | 2 | 3 | 4–5 | 6–8 | 9–15 | 16+ |
|---|---|---|---|---|---|---|---|
| pairs | 74 | 1,644 | 1,886 | 1,367 | 437 | 144 | 15 |
| twin share | 92% | 69% | 52% | 36% | 15% | 4% | 7% |

The same, split by J band:

| J band | ≤ 2 differing | 3–5 differing | 6+ differing |
|---|---|---|---|
| 0.4–0.5 | 55% (509) | 36% (1,393) | 11% (329) |
| 0.5–0.6 | 69% (649) | 49% (1,339) | 15% (209) |
| 0.6–0.7 | 84% (560) | 60% (521) | 10% (58) |

C4 by quantile bin, as twin share: 29%, 40%, 50%, 57%, 67%, 74%.

### 4.6 Merge simulation

- **Single linkage:** merges chain transitively.
- **Complete linkage:** greedy, in descending J; a group merges only if every pair inside it meets the rule.
- md = min(|a|,|b|).

| rule | linkage | themes removed | twins collapsed (of 2,752) | facets collapsed (of 2,815) | precision | unjudged pairs swept in |
|---|---|---|---|---|---|---|
| J ≥ 0.70 (with or without md ≤ 2) | – | 0 | 0 | 0 | – | – |
| J ≥ 0.65 & md ≤ 2 | complete | 177 | 154 (5.6%) | 23 (0.8%) | 87.0% | 0 |
| J ≥ 0.65 | complete | 307 | 222 (8.1%) | 86 (3.1%) | 72.1% | 0 |
| J ≥ 0.65 | single | 350 | 272 (9.9%) | 114 (4.0%) | 70.5% | 13 |
| **J ≥ 0.6 & md ≤ 2** | **complete** | **454** | **386 (14.0%)** | **74 (2.6%)** | **83.9%** | **0** |
| J ≥ 0.6 & md ≤ 2 | single | 554 | 528 (19.2%) | 114 (4.0%) | 82.2% | 75 |
| J ≥ 0.5 & md ≤ 2 | complete | 842 | 678 (24.6%) | 195 (6.9%) | 77.7% | 0 |
| J ≥ 0.5 & md ≤ 2 | single | 1,159 | 1,043 (37.9%) | 389 (13.8%) | 72.8% | 556 |
| md ≤ 2 | complete | 1,093 | 812 (29.5%) | 322 (11.4%) | 71.6% | 0 |
| md ≤ 2 | single | 1,636 | 1,383 (50.3%) | 686 (24.4%) | 66.8% | 1,472 |

- Under complete linkage, a group has at most 3 themes.
- **J ≥ 0.70 yields nothing.** The highest J among sibling pairs is 0.697, because consensus merge already merges every non-nested pair at ≥ 0.70.

### 4.7 Are the facets a rule eliminates weaker?

- **Method:** six agents rated pairs blind (shuffled; no labels, J, theme names or group shown).
- **Scale:** 1 = weak/same story; 2 = moderate, a secondary aspect; 3 = strong, a distinct process or context a biologist would keep.
- The key file was never shown to the agents.

| group | n | mean | weak | moderate | strong |
|---|---|---|---|---|---|
| facets eliminated by J ≥ 0.6 & md ≤ 2 | 74 | 2.45 | 2.7% | 50.0% | 47.3% |
| added by J ≥ 0.5 & md ≤ 2 | 121 | 2.48 | 3.3% | 45.5% | 51.2% |
| added by md ≤ 2 alone | 131 | 2.45 | 0.8% | 53.4% | 45.8% |
| facets that remain (random) | 200 | 2.65 | 1.0% | 33.5% | 65.5% |
| twin controls | 60 | 1.73 | 31.7% | 63.3% | 5.0% |

- Eliminated facets are weaker than those that remain (Mann-Whitney p = 0.0005–0.009) but far above twins.
- About half of the eliminated facets are rated strong.
- Strong examples lost under the accepted rule:
  - APOBEC3G antiviral editing vs DNA alkylation repair;
  - post-lanosterol cholesterol synthesis vs vitamin K carboxylation;
  - histamine receptors vs GI smooth-muscle motility;
  - desmosome/invadopodia vs CDH11/Listeria entry.
- Moderate examples: FGFR4/βKlotho vs FGFR1; hindgut vs coronary mesoderm.
- Weak examples: bicarbonate exchangers plus stray transporter diseases; glial proliferation vs amyloid clearance.

### 4.8 Whole families

- 591 families have ≥ 3 themes; 85 of them are all-twin.
- A family's twin share correlates only with difference size (median md, Spearman −0.37). It does not correlate with union expansion (−0.08), core (+0.03), density (+0.04) or size (+0.03).
- Family-level rules:
  - every edge md ≤ 2: 24 families, 82 themes, 69% precision;
  - median edge md ≤ 2: 88 families, 403 themes, 69% precision.
- **Decision:** do not collapse whole families. Families mix twins and facets; the pair is the right unit.

### 4.9 Direction idea (Aviyah; post-hoc; member embeddings)

Cosine of each sibling's displacement:

| displacement | AUC | J-band stratified |
|---|---|---|
| from the shared parent's centroid | 0.56 | 0.53 |
| from the core | 0.49 | – |
| unique blocks, from the parent | 0.59 | 0.55 |

There is no usable direction signal in member embeddings.

## 5. How the rule was chosen

1. **Feature:** md, the number of differing pathways on the smaller side. It was among the pre-registered features (A1) and passed the declared bar.
   - **The md ≤ 2 cutoff has a label-free basis:** the pipeline's minimum cluster size is 3, so a difference of ≤ 2 pathways cannot be a theme of its own.
   - It also matches Aviyah's naming criterion: one or two pathways rarely make a nameable aspect.
2. **J ≥ 0.6 (post-hoc, read off labelled tables):**
   - Within J ≥ 0.6, md ≤ 2 pairs are 84% twin.
   - Compared with J ≥ 0.65 & md ≤ 2: 0.6 removes 2.5× more twins (386 vs 154) for 51 more facets. The marginal precision of the 0.60–0.65 band is 82%.
   - Going down to 0.5 raises facet losses 2.6× (195) at 78% precision.
3. **Complete linkage, not single:** no chaining and no unjudged pairs swept in; groups of at most 3.
4. **Keep the higher-support theme** (as in c85).
5. **Cost accepted knowingly:** about 35 strong facets among the 74 eliminated. Preferred implementation: a reversible "variant_of" flag rather than deletion (reviewer recommendation; flag vs deletion still to be confirmed).

## 6. The accepted rule (exact specification)

- **Candidate pairs:** sibling themes A, B in the c85 build that are non-nested, share a parent with < 1,000 members, and have J ≥ 0.4.
- **Pair condition:** J(A,B) ≥ 0.60 AND min(|A∖B|, |B∖A|) ≤ 2.
- **Grouping:** complete linkage. Process qualifying pairs in descending J. Join two groups only if every cross pair qualifies.
- **In each group:** keep the theme with the highest support. Ties go to the larger theme, then the lower node id. The others become variants of the kept theme.
- **If implemented as deletion:** drop the variants; their children stay attached to their other parents (re-link to the kept theme only where contained).
- **Expected effect:**
  - 454 themes flagged or removed out of 8,251;
  - twins collapsed 386 of 2,752 (14.0%);
  - facets collapsed 74 of 2,815 (2.6%).
- **Status:** accepted by Aviyah on 10 Oct 2026; not run.

## 7. Caveats

- The labels come from an LLM judge that saw the A-only/B-only lists. Short lists may bias it toward "twin".
- The J cutoff and the rule choice were partly read off labelled tables. Only the md ≤ 2 cutoff is label-free.
- The strength ratings are LLM-blind ratings, not human ones. A blinded human-biologist check is still pending.

## 8. Open: Aviyah's naming idea (not run)

- **Idea:** have the LLM name each cluster, embed the names, and treat siblings whose names point the same way as twins.
- **Status of the inputs:**
  - Names already exist for every c85 theme. They were written per theme in the plausibility census, independently of the pairs.
  - MedCPT runs only in the Mac venv; Hugging Face is blocked from the cloud workspace, so ccode must run the embedding.
- **Proposed pre-registration:**
  - N1 = cosine of the MedCPT query embeddings of names A and B (T);
  - N2 = cosine of the name displacements from the shared parent's name (T).
  - Pass: AUC ≥ 0.70 in both halves and J-band ≥ 0.60 against the verdicts.
  - Because the twin/facet judge saw these names, the primary clean check is against the blind strength ratings (586 pairs; names not shown): twin controls vs remaining facets AUC, and Spearman with strength.
  - Secondary use: a veto inside the accepted rule (do not merge if the names diverge). Check how many of the 74 facets it would save.
- **Constraint note:** names are LLM-written text, like the pathway descriptions, not LLM judgement. Using them in construction makes the build depend on a versioned naming step (fixed prompt, model and stored outputs).

## 9. Files (Mac: data/experiments/reviewer_eval_x2_2026-10-09/)

- **Pre-registration and reports:** twin_facet_hypotheses_PREREG.md; REPORT_twin_rules.md (§4.2–4.3); REPORT_twin_facet_search.md (§4.4–4.5); REPORT_merge_rule.md (§4.6–4.9).
- **Scripts:** privanc.py, privanc2.py, tf_common.py, tf_static.py, tf_runs.py, tf_eval.py, mrg.py, fam2.py, dirfeat.py.
- **Feature files:** twin_facet_features_static.json, twin_facet_features_runs.json.
- **Blind judging:** facet_strength/ (blind_chunk*.json, judged_chunk*.json, KEY_DO_NOT_SHARE.json).
- **Labels:** sibling_pairs_all.json, judged_sibling_pairs_all.json.

## 10. Addendum (10 Oct, later): name-blind re-judging. The accepted rule's precision was overstated

- **Setup:** 15 new judges re-judged a random 1,500 of the 5,567 pairs.
  - Same rubric and the same pathway samples as the original judge, but no theme names shown.
  - Pre-registered in names_test/PREREG_names_test.md. Key never shown to the judges.
- **Effect of the names on the original judge:**
  - Name-blind twin share is 42.2%; the original judge gave 49.6% on the same pairs.
  - Agreement 82.2%. 189 original twins became facets; 78 original facets became twins.
- **AUC against the name-blind labels (vs the original labels):**

| feature | name-blind | original |
|---|---|---|
| J | 0.59 | 0.65 |
| md | 0.70 | 0.69 |
| C4 | 0.64 | 0.68 |

  Difference size (md) is robust. Overlap J mostly carried name similarity.
- **Accepted rule (J ≥ 0.6 & md ≤ 2) on the name-blind labels:**
  - precision 70.2% (95% CI 61.8–77.9), n = 131 sampled pairs; the original labels gave 88.5% on the same sample;
  - after complete linkage, 68.9% (n = 106).
- **Twin share by J band, md ≤ 2, name-blind (original in brackets):**

| J band | twin share | n |
|---|---|---|
| 0.4–0.5 | 52% (49%) | 133 |
| 0.5–0.6 | 68% (71%) | 168 |
| 0.6–0.65 | 70% (90%) | 89 |
| 0.65–0.7 | 71% (86%) | 42 |

  Above J 0.5, overlap no longer raises twin share once names are hidden.
- **Implication:** the accepted rule's expected cost is closer to 30% facets among the merged pairs (about 165 facets rather than 74). The choice of J ≥ 0.6 over J ≥ 0.5 is not supported by the name-blind labels. md ≤ 2 remains the robust part.
- **Status:** the accepted rule is flagged for re-decision by Aviyah. The name-embedding comparison awaits ccode's name vectors (prompt 29).

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

## 12. Caveat (11 Oct): the judges and the namers saw samples, not full member lists

- **Theme names** (plausibility census): small themes were shown in full; larger ones as a random sample of up to 15–40 members, depending on the round. In c85, 34% of themes have more than 15 members, 12% more than 25 and 5% more than 40.
- **Twin/facet judging** (original and name-blind): up to 10 shared pathways and up to 8 per unique side were shown.
  - In 27% of the 5,574 sibling pairs, the A-only or B-only list was cut to 8.
  - In 44%, the shared list was cut to 10.
  - The median largest unique side is 6.
- **Aviyah's requirement (11 Oct):** naming and twin/facet judging must see at least all non-overlapping pathways.
- **Consequence:** the reference labels behind §4–§11 are sample-based for about a quarter of the pairs and should be re-made with complete unique lists before any final decision.

## 13. Re-judging with complete unique lists (11 Oct; pre-registered in fulllists_test/PREREG_fulllists.md)

- **Setup:** the same 1,500 pairs, judged by 15 fresh judges.
  - Shown: the COMPLETE A-only and B-only lists and up to 25 shared pathways. No names.
  - 1,494 decided: twin 39.4%, facet 60.6%.
- **Seeing complete lists changed little.** Agreement with the sample-based name-blind round was 84.5%:
  - 85.5% on pairs that had been truncated;
  - 84.1% on pairs that had not.
  - Agreement with the original round (names and samples): 80.1%.
- **Judge-to-judge calibration is the dominant noise.** Pairs were randomly assigned, yet the twin share per judge (100 pairs each) ranged from 23% to 62% (chi-square p = 7e-12). The sample-based name-blind round ranged from 32% to 54%.
- **AUC against the full-list labels:**

| feature | AUC | half1 / half2 | J-band | within-judge |
|---|---|---|---|---|
| md (fewest differing pathways) | 0.667 | 0.672 / 0.661 | 0.653 | 0.676 |
| N1 name cosine | 0.659 | 0.656 / 0.661 | 0.655 | 0.659 |
| C4 member-centroid cosine | 0.651 | 0.642 / 0.660 | 0.631 | 0.646 |
| J | 0.576 | 0.576 / 0.575 | 0.511 | 0.574 |
| N2 name direction | 0.500 | 0.513 / 0.488 | 0.499 | 0.500 |

  No feature reaches 0.70.
- **Accepted cutoff rule (J ≥ 0.6 & md ≤ 2):**
  - precision 62.8% (95% CI 54.0–70.6, n = 129 sampled pairs);
  - after complete linkage, 59.6% (CI 50.0–68.5).
- **Name rule at matched volume:** 61.4%. Difference −1.4 points (CI −11.2 to +9.1), so a tie again.
- **Twin share by J band and md (full lists):**

| J band | md 1–2 | md 3–5 | md 6+ |
|---|---|---|---|
| 0.4–0.5 | 48% (133) | 32% (375) | 10% (81) |
| 0.5–0.6 | 58% (168) | 38% (388) | 11% (64) |
| 0.6–0.7 | 63% (129) | 44% (142) | 0% (14) |

- **Reading:**
  - Truncation was not the cause of the disagreements.
  - The twin/facet call is a graded judgement on which LLM judges differ in calibration. Agreement between independent rounds is about 80–85%.
  - With complete lists, the accepted rule would merge about 40% facets.
  - **Reviewer recommendation:** withdraw the merge. Keep all themes, and expose variants as a continuous, label-free score (md, plus name and centroid similarity) and a "variant family" grouping for display and statistics.
  - Decision pending with Aviyah.

## 14. Status (12 Oct): superseded

The accepted sibling merge rule (section 6) is superseded and must not be run. After the whole-reading test and the J >= 0.5
simulation (REPORT_merge_J05.md), Aviyah concluded that post-hoc merge steps on top of the build are incoherent: the
same-theme overlap cutoff belongs inside the algorithm. That is tested as a branch arm:
data/experiments/reviewer_notes/SPEC_overlap_arm_2026-10-12.md.
