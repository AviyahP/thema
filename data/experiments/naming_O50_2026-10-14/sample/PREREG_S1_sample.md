# O50 naming-c1: sample check of the full-scale N1 names (reviewer pre-registration, 15 Oct 2026, written before any S1 judging)

**Question (Aviyah):** are the full-scale N1 candidates as good as the pilot's, before paying for S1 on all 13,773 candidates?

## Sample
- 200 themes drawn with random.Random(20261015).sample(sorted eligible O50 theme ids, 200), from the 4,591 eligible themes (3-200 members).
- No stratification. Themes that are unnameable (2+ of 3 not-nameable votes) stay in the sample and are counted as unnameable.

## Selection (S1), exactly as in spec/ALGORITHM.md section 4 and pilot code np_sel.py / np_select.py
- Each nameable candidate is back-matched once: name + the theme + its 4 confusables (themes_and_confusables.json, in that order) as A-E, shuffled with seed sha256(theme_id + ":S" + slot); shown as in_all + also_in.
- Item order: random.Random(99) over the sorted (theme, slot) pairs. 50 items per file. Judges: fresh in-session subagents using spec/S1_backmatch.md. Keys stay in KEY_DO_NOT_SHARE_* files.
- Medoid selection, low_confidence and unnameable exactly as np_select.py.
- **Deviation, declared:** set operations use rendered member titles taken from the namer inputs as multisets (55 of 4,591 themes contain two members with the same title), not pathway keys. This can differ from ccode's key-based items only in those themes. The sample is an evaluation, not the reproduction test.

## Evaluation (fresh judges, never used for S1)
- **E1 back-match** of the selected names: the same 5 clusters, re-shuffled with seed sha256(theme_id + ":ENEW"). Spec S1_backmatch.md. Shuffled with random.Random(11), 50 per file.
- **E2 member fit** of the selected names: the full member list, shuffled with the same seeded generator. Spec E2_fit.md. fit = 1 - misfits / size. Shuffled with random.Random(12), 50 per file.
- **Code only, all 4,591 themes, no judges:** duplicate rate among each slot's candidate names (normalised as ALGORITHM section 5).

## Outcomes and declared reading
- P1 = S1 candidate correct rate (pilot: unselected candidates were right about 83%).
- P2 = share of nameable sample themes with at least 1 correct candidate (not low_confidence).
- P3 = E1, the selected name picks its own theme. Bar >= 85%; pilot 91.5%. Report the bootstrap 95% CI over themes.
- P4 = E2 mean member fit. Bar >= 0.90; pilot 0.917.
- **GOOD** if P3 >= 85% and P4 >= 0.90. **NOT GOOD** if either is missed. If P3's CI lower bound is below 85% while its point estimate passes, the verdict is reported as GOOD but marginal.
- No decision about the remaining 4,391 themes is pre-committed here; Aviyah decides after seeing the result.
