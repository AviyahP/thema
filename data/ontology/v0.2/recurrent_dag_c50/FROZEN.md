# FROZEN — `v0.2.2-subset-1850-c50`, inclusion 0.50, CENTRED clustering space

**A subset build, not the THEMA ontology.** The universe is **10,770** pathways; this covers the
**1,850** embedded for method development. Every figure here is the subset's.

**Supersedes `recurrent_dag_consensus_centred` (tag `v0.2.1-subset-1850`), which used inclusion
0.25.** That build stays as history. The cutoff decision and the reasoning it replaced are in
`DECISIONS.md`, 29 Sep 2026 — including that the recommendation for 0.25 was withdrawn after the
argument behind it was found to be false.

| | |
|---|---|
| frozen | 2026-09-29 |
| built from commit | `a33f5b3cf7f28871b04702a3f80c18096f0eb63b` |
| build script | `scripts/build_consensus.py --space centred` |
| clustering space | centred-and-renormalised MedCPT vectors |
| inclusion cutoff | **0.50** |
| floors | `FLOORS[centred, 0.50]` — 0.880 / 0.930 / 0.600 / 0.400 at sizes 3/4/5/6 |
| floors calibrated | **40 calibration + 20 held-out scrambles**, held-out FDR **0.00333** |
| runs / theta / declared m | 100 / 0.70 / 0.33 |

**The floors were solved AT this cutoff and at no other.** A floor is solved against the family
population its cutoff produces, and moving 0.25 → 0.50 shifts a floor by more than seed noise does
at every stratum, so the 0.25 floors would have been wrong here rather than merely approximate.
`recurrent_dag_cal050` — an earlier 0.50 build using in-arm 20+10 floors — is **not** this build and
must not be read as frozen.

## Shape

| | `v0.2.1` (0.25) | **this build (0.50)** |
|---|---|---|
| themes | 873 | **800** |
| roots | 53 (6.1%) | **61 (7.6%)** |
| themes with >1 parent | 202 (23.1%) | **176 (22.0%)** |
| max depth | 12 | **12** |
| median theme size | 10 | **8** |
| largest theme | 933 | **819** |
| largest root, direct members | 65 | **64** |
| straddlers (≥2 non-nested homes) | 852 | **682** |

## Placement — reported three ways, because one number hides the cost

| | `v0.2.1` (0.25) | **this build (0.50)** |
|---|---|---|
| pathways placed | 1,842 | **1,831** |
| **unplaced (strict)** | 8 | **19** |
| **root-only** — in no theme that has a parent | 53 | **106** |
| **effectively unplaced** — the sum | 61 | **125** |

A root-only pathway has been placed by the letter of the algorithm and told a reader almost
nothing: it has a top-level bucket and no theme within it. Raising the cutoff moves pathways into
that state faster than it moves them out of the build — **106 against 53** — so a freeze reporting
only the strict count would hide most of what the cutoff cost. It is doubled here rather than
buried.

## Test 9 — seed stability

Seed 0 against seed 1, everything else identical.

| | `v0.2.1` (0.25) | **this build (0.50)** |
|---|---|---|
| mean best-match Jaccard | 0.849 | **0.862** |
| median | 0.889 | **0.909** |
| matched at ≥ 0.9 | 46.3% | **53.2%** |
| matched at ≥ 0.7 | 85.2% | **86.9%** |
| member agreement | 0.849 | **0.862** |

**"Frozen" applies to the theme set and its nesting, not to exact member lists** — 53% of themes
match at ≥ 0.9 across seeds, which is better than the 46% of the build this supersedes and still not
identity.

## Test 2 — shape against curated ontologies

Informational, never a gate. Roots 7.6% (Reactome 1%, GO BP 20%), max depth 12 (Reactome 11, GO 16),
multi-parent 22.0% (Reactome 1%, GO 31%). Inside the curated range on all three.

## What was NOT re-solved

Nothing beyond the floors at this cutoff. Theta stays 0.70, declared m stays 0.33, the strata are the
amendment's, the consensus parameters are unchanged (STRAY 0.10, JACCARD 0.70), and the encoder and
its revision are unchanged. **The names are not carried over**: membership changes at every level, so
all 861 `name-v3` names refer to themes that no longer exist and this build is unnamed.
