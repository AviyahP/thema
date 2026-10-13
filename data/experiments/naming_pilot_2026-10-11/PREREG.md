# Naming pilot naming-c1: pre-registration (reviewer, 2026-10-11, before any result)

Sample: 200 c85 themes (3-200 members, >= 1 sibling), seed 20261011: 150 from the sibling-overlap graph (J >= 0.4
pairs), 50 from the rest. Reproducibility subset: 60 of the 200 (seed 20261013).
Arms evaluated blind and interleaved: NEW = naming-c1 final names; CENSUS = the reviewer's census labels
(theme_names_c85.tsv). Evaluation judges are fresh and never saw naming or selection.

Pass bars for naming-c1 (all must hold):
- P1 E1 back-matching accuracy among T + 4 confusables >= 85% (chance 20%).
- P2 E1 not worse than CENSUS: bootstrap 95% CI of (NEW - CENSUS) lower bound >= -3 points.
- P3 E2 mean member fit >= 0.90.
- P4 E3 equivalent >= 80% of the 60 re-run themes.
- P5 E4 zero duplicate names among the 200 after the uniqueness step.
Reported, not gated: share UNNAMEABLE, share low_confidence, CENSUS on E1/E2/E4, examples side by side.
Post-hoc analyses will be labelled.
