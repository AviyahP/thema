# Twin/facet re-judging with complete unique lists: pre-registration (reviewer, 2026-10-11, before any result)

Why: Aviyah (11 Oct) requires that judging sees at least ALL non-overlapping pathways. Earlier judging showed at most
8 per unique side (27% of pairs truncated) and 10 shared (44% truncated).

Design
- Same 1,500 pairs as names_test (random of the 5,567 judged sibling pairs; seed 20261011), new ids and order
  (seed 20261012). Key: KEY_DO_NOT_SHARE.json, never shown to judges.
- Shown: sizes, number shared, COMPLETE only_A and only_B lists, up to 25 shared pathways (random). No theme names.
- Same twin/facet/unclear rubric as before (rubric_fulllists.md), 15 fresh judges x 100 pairs.

Analyses (full-list labels = primary reference from now on)
1. Agreement with name-blind v1 labels and original labels; separately for pairs whose unique lists were truncated
   before (either side > 8) and pairs that were not.
2. AUC (all, two halves seed 0, J-band stratified) of: md, J, C4, N1 name cosine (article), N2.
3. Accepted cutoff rule (J >= 0.6 & md <= 2): precision with bootstrap 95% CI; pair level and complete linkage.
4. Name rule at matched volume (top 560 N1) vs cutoff rule: precision difference with bootstrap CI.
5. Twin share by md band x J band.
Decision rules unchanged from PREREG_names_test.md (names viable only if AUC >= 0.70 both halves and J-band >= 0.60;
beats cutoff only if CI excludes 0). Post-hoc additions are labelled.
