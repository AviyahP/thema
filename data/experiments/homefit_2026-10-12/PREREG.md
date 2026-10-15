# Home-fit test: are a pathway's multiple homes real facets? (reviewer pre-registration, 2026-10-12, before any data is built)

Question (Aviyah): is the resampling algorithm worth it for the facets it creates? Descriptive check (REPORT_facets_real.md):
79% of pathways in c85 have 2+ "clearly distinct homes" (smallest themes containing them, pairwise J < 0.4). This test
asks whether those homes are meaningful for the pathway.

## Sample
- Build: thema_L_x2_c85. Home = a theme under 1,000 members containing the pathway, with no smaller theme containing it
  inside it. Distinct homes = greedy by support, pairwise J < 0.4 (as in facets_real.py).
- Eligible pathways: 2+ distinct homes, every distinct home <= 100 members. Report how many are excluded by the size cap.
- 100 pathways, seed 20261013. At most 4 homes per pathway (highest support first); report how often the cap binds.
- Decoy (one per pathway): the theme (<= 100 members) NOT containing the pathway whose member-centroid is most similar
  (cosine, build embedding space) to the pathway's own vector, with J < 0.4 to every home. A hard decoy: it is close in
  text space, so a judge cannot reject it on topic alone.

## Items
The target pathway (name and description, as rendered for earlier tests) and its homes plus the decoy, shuffled, labelled
G1..Gk. Each group is shown as its complete member list with the target pathway removed. No theme names. The key (which
group is the decoy) is never shown to judges.

## Questions
1. For each group: does the target pathway belong in it? yes / partly / no.
2. Over the groups answered yes or partly: do they show different aspects or contexts of the pathway ("different
   aspects"), the same aspect ("same aspect"), or is there no coherent link ("unrelated")?

## Judges
5 in-session subagents, 20 pathways each, one rubric. No API spend. Evaluation only; nothing feeds construction.

## Outcomes and declared reading
- P1 fit rate of real homes (yes or partly), with bootstrap 95% CI over pathways.
- P2 fit rate of decoys.
- P3 among pathways with 2+ real homes judged yes/partly, the share judged "different aspects".
- REAL FACETS if P1 >= 80%, P1 - P2 >= 25 points with CI lower bound > 0, and P3 >= 60%.
- NOISE if P1 < 60% or P1 - P2 CI includes 0.
- Otherwise MIXED. Strict "yes" rates are reported alongside.
Secondary: P1 by home size and by support; examples of homes judged "no".
