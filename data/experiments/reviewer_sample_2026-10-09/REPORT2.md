# Second 10% plausibility sample — thema_L_repair (2026-10-09)

Scope: bands 3–100 (101+ were already checked in full in round 1). 874 themes, seed 20261010, no overlap with sample 1.
TBA BTM members shown with their generated description + first 10 genes. Judged by 10 reviewer subagents with rubric4.md
(coherent / umbrella with a specific stated link / core_plus_misfits / mixture / incoherent). Spot-checked by the reviewer.

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 48 | 46 | 1 | 1 | 0 | 0 | 97.9% |
| 6-10 | 212 | 193 | 12 | 3 | 2 | 2 | 96.7% |
| 11-20 | 436 | 376 | 53 | 4 | 2 | 1 | 98.4% |
| 21-50 | 157 | 138 | 18 | 1 | 0 | 0 | 99.4% |
| 51-100 | 21 | 13 | 7 | 0 | 1 | 0 | 95.2% |
| all | 874 | 766 | 91 | 9 | 5 | 3 | 98.1% |

Consistent with sample 1 (97.2% after three rounds).

## Not ok (17)
Incoherent (3): n02640, n02521, n06864 — all built from BTM modules whose own descriptions say they are heterogeneous / housekeeping.
Mixtures (5): n06797 acidification + PS scrambling; n03530 membrane tethering/docking; n07448 (70) peroxisomal FA oxidation + steroidogenesis;
n02119 CD4 T-cell proliferation + B-cell Ig diversification; n03466 PAX3 targets + ALK/STAT3.
Core+misfits (9): n06291, n03203, n06867, n07243, n01368, n07374, n06442, n06190, n00094 (misfit fraction 0.30–0.50).
Heterogeneous BTMs also are the misfits in n06190 and n02521: 5 of 17 problems trace to them.

## Heterogeneous BTMs
18 of the 83 TBA BTMs have generated descriptions that state no single theme (e.g. M125, M153, M184.1, M211, M218, M221).
Candidate: flag them as low-information inputs (or drop them) before the next build. Not decided.

## Umbrella spot-checks (links specific and valid)
proteasome → MHC-I presentation; MECP2 / Rett behaviour; HSPs in axon maintenance; epidermal melanin unit;
heavy metals → metallothionein / HMOX1; O-glycosylation of GAG linkers and Notch; methyltransferases in xenobiotic + selenium excretion.

## Correction on the n00150 fan (Aviyah, 2026-10-09)
The 6 parents of n00150 were judged plausible, each a different facet, and the 7 shared pathways fit in each.
That is the multi-parent DAG working as intended, not redundancy. The lack of a common ancestor within 3 levels is consistent
with the facets leading into different routes upward. Decision: fans are NOT a removal target. Only a parent pair that is a near-twin
of each other (same facet, high Jaccard) is a merge candidate; that falls under the sibling near-twin measurement.
