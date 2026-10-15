# Sibling merge rule: simulation, facet strength, families, direction (reviewer, 2026-10-10)

Totals (judged sibling pairs, J >= 0.4): twins 2,752; facets 2,815. Build: thema_L_x2_c85 (8,251 themes).
Scripts: mrg.py, fam2.py, dirfeat.py; blind judging in facet_strength/ (KEY_DO_NOT_SHARE.json never shown to agents).

## Rules simulated (md = fewest pathways that differ on one side)
Single linkage = transitive closure; complete linkage = a group merges only if EVERY pair in it meets the rule.
| rule | linkage | themes removed | twins collapsed / 2,752 | facets collapsed / 2,815 | precision | unjudged pairs swept in |
|---|---|---|---|---|---|---|
| J>=0.65 | single | 350 | 272 (9.9%) | 114 (4.0%) | 70.5% | 13 |
| J>=0.65 | complete | 307 | 222 (8.1%) | 86 (3.1%) | 72.1% | 0 |
| J>=0.6 & md<=2 | single | 554 | 528 (19.2%) | 114 (4.0%) | 82.2% | 75 |
| **J>=0.6 & md<=2** | **complete** | **454** | **386 (14.0%)** | **74 (2.6%)** | **83.9%** | 0 |
| J>=0.5 & md<=2 | single | 1,159 | 1,043 (37.9%) | 389 (13.8%) | 72.8% | 556 |
| J>=0.5 & md<=2 | complete | 842 | 678 (24.6%) | 195 (6.9%) | 77.7% | 0 |
| md<=2 | single | 1,636 | 1,383 (50.3%) | 686 (24.4%) | 66.8% | 1,472 |
| md<=2 | complete | 1,093 | 812 (29.5%) | 322 (11.4%) | 71.6% | 0 |
Complete-linkage groups have at most 3 themes.

## Are eliminated facets weaker? (blind, 6 agents, strength 1 weak / 2 moderate / 3 strong; shuffled, no labels/J/group)
| group | n | mean | weak | moderate | strong |
|---|---|---|---|---|---|
| E1 eliminated by J>=0.6&md<=2 | 74 | 2.45 | 2.7% | 50.0% | 47.3% |
| E2 added by J>=0.5&md<=2 | 121 | 2.48 | 3.3% | 45.5% | 51.2% |
| E3 added by md<=2 | 131 | 2.45 | 0.8% | 53.4% | 45.8% |
| facets that remain (random) | 200 | 2.65 | 1.0% | 33.5% | 65.5% |
| twin controls | 60 | 1.73 | 31.7% | 63.3% | 5.0% |
Eliminated facets are weaker than remaining ones (Mann-Whitney p 0.0005-0.009) but far above twins; about half are strong.
Strong examples lost under the J>=0.6&md<=2 rule: APOBEC3G antiviral editing vs DNA alkylation repair; cholesterol
post-lanosterol synthesis vs vitamin K carboxylation; histamine receptors vs GI smooth-muscle motility; desmosome/
invadopodia vs CDH11/Listeria entry.

## Families (connected components, J >= 0.4; 591 with >= 3 themes; 85 all-twin)
Family twin share correlates only with difference size (median md, Spearman -0.37); not with expansion, core, density
or size. Family-level rules: 'every edge md<=2' 24 families/82 themes, 69% precision; 'median edge md<=2' 88/403, 69%.
No family-level rule beats the pair rule; families mix twins and facets, so collapse whole families: no.

## Direction idea (post-hoc, member embeddings)
cos of each sibling's displacement from the shared parent centroid: AUC 0.56 (J-band 0.53); from the core: 0.49;
unique blocks from the parent: 0.59 (0.55). No usable direction signal in member embeddings.

## Recommendation
J >= 0.6 and md <= 2, complete linkage, keep the higher-support theme (as in c85); preferably as a reversible
'variant of' flag rather than deletion, since ~35 strong facets are among the 74 eliminated.
md <= 2 has a label-free basis (minimum cluster size 3); the J >= 0.6 cutoff was read off LLM-labelled tables.
