# Does resampling create real facets? Pathway homes after removing variants (reviewer, 2026-10-12, post-hoc, descriptive)

Script facets_real.py; output facets_real_output.txt. "Home" = a smallest theme (under 1,000 members) containing the
pathway, i.e. no smaller theme containing it sits inside. "Clearly distinct" = homes with pairwise J < 0.4 (greedy, by support).
| build | themes | homes per pathway (median) | only one home | median J between a pathway's homes | 2+ clearly distinct homes | 3+ |
|---|---|---|---|---|---|---|
| c85 | 8,241 | 3 | 20% | 0.14 | 79% | 54% |
| c85 with J >= 0.5 variants merged | 6,475 | 3 | 23% | 0.14 | 75% | 51% |
Reading: the variants sit mostly at the same place as one home; removing them barely changes the pathway's multiple homes.
Three in four pathways keep two or more clearly different homes. A single Ward tree would give every pathway exactly one.
Not shown here: whether the pathway fits each home and whether the homes are different aspects of it (proposed test).
