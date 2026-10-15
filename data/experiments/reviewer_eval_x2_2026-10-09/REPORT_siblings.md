# All sibling pairs: twin or facet? (reviewer, 10 Oct 2026)

**Working version:** thema_L_x2_c85.

**Pairs judged:** every pair of themes (each under 1,000 members) that are NOT nested, share a parent (giant roots not counted as parents) and overlap at J ≥ 0.4. That is **5,574 pairs**, all judged; this is not a sample.

**Rubric:** rubric_twins.md.
- "twin" = the same theme; merging loses nothing a biologist cares about.
- "facet" = a distinct aspect; keep both.

Judges saw both labels, the shared pathways and the pathways only in A and only in B.

**Files** (data/experiments/reviewer_eval_x2_2026-10-09/):
- judged_sibling_pairs_all.json (every pair, its verdict and reason);
- twin_groups.json (connected groups of twin pairs).

## Results

| J | pairs | twin | facet | unclear | twin share |
|---|---|---|---|---|---|
| 0.40-0.50 | 2,237 | 822 | 1,409 | 6 | 37% |
| 0.50-0.60 | 2,198 | 1,141 | 1,056 | 1 | 52% |
| 0.60-0.65 | 788 | 535 | 253 | 0 | 68% |
| 0.65-0.70 | 351 | 254 | 97 | 0 | 72% |
| **all** | **5,574** | **2,752** | **2,815** | **7** | **49%** |

- **The twins involve 3,291 themes**, forming 987 connected groups. Merging every group would remove a net 2,304 themes (28% of the DAG).
- **But merging is transitive.** Inside those groups, 336 of the 3,088 judged pairs (11%) are facets: A is a twin of B and B of C, yet A and C are distinct.

## An overlap-only cutoff (merge every sibling pair at J ≥ cutoff)

| cutoff | pairs merged | true twins | precision | share of all twins caught |
|---|---|---|---|---|
| 0.50 | 3,337 | 1,930 | 58% | 70% |
| 0.55 | 1,988 | 1,271 | 64% | 46% |
| 0.60 | 1,139 | 789 | 69% | 29% |
| 0.65 | 351 | 254 | 72% | 9% |

The best overlap-only rule is wrong on 28% of its merges and catches only 9% of the twins. A cutoff that catches most twins (0.50) is wrong on 42% of its merges.

## The biggest twin families: one theme split into many variants

- **33 themes:** antiviral innate sensing / type I IFN induction (RIG-I, IRF, nucleic-acid sensing...).
- **25:** B cell activation / plasma cell differentiation.
- **25:** xenobiotic / drug metabolism (CYP, conjugation).
- **25:** DNA replication initiation / E2F / G1-S.
- **21:** RAS-MAPK signalling and its negative regulation.
- **20:** adherens junctions / cadherin adhesion.

## Examples

**Twins (merge):**
- MHC class II antigen presentation || MHC class II presentation by APCs (J 0.48)
- p53 and DNA damage checkpoint || DNA damage G2 checkpoint and p53 regulation (J 0.47)
- Monocyte recruitment and inflammation || monocyte chemotaxis, adhesion and extravasation (J 0.56)
- Death receptor apoptosis and necroptosis || death receptor extrinsic apoptosis and necrosis (J 0.61)
- Deubiquitination and NF-kB regulation || deubiquitination and TNFR1 NF-kB signalling (J 0.64)

**Facets (keep):**
- Iron homeostasis and transport || iron and heme transport: heme scavenging vs iron import (J 0.46)
- B cell activation and plasma cell differentiation || B cell activation and germinal centre: plasma-cell output vs BCR signalling (J 0.48)
- Hexose transport || carbohydrate digestion: transporters vs enzymatic hydrolysis (J 0.50)
- Negative regulation of type I IFN || cGAS-STING sensing: feedback vs activation (J 0.50)
- Hair follicle development || ectodermal appendages: hair vs tooth (J 0.62)
- Vascular smooth muscle switching || shear-stress remodelling (J 0.67)

## Reading

- **About half of the high-overlap sibling pairs are real twins**, and they cluster into large families of variants of one theme. That is genuine over-fragmentation.
- **Overlap alone cannot separate them from facets** at any cutoff.
- The 5,574 labelled pairs are a ready test set for a deterministic second criterion (e.g. embedding similarity of the A-only vs B-only pathways): calibrate on half, validate on the other half, declared first.

**Decision: Aviyah.**
