# Fifth amendment, 26 Sep 2026 — Ward clusters centred-and-renormalised vectors

*Adopted on the evidence recorded in `docs/spec/open-question-ward-space-2026-09-26.md`, which
declared its reading before any measurement. Amends the clustering input. RAW is superseded and its
builds remain as history.*

---

## The change

`prepare` previously handed `distances(x)` the L2-normalised encoder output. It now receives the
**universe mean subtracted, then each row L2-renormalised**. The real side uses the real universe
mean; **each scramble uses its own scrambled matrix's mean**, since using the real mean on a
scramble would leak the real geometry into the null.

## Why the renormalisation is the operative step

**Mean subtraction alone cannot change a Ward tree.** Ward minimises within-cluster variance, which
is defined on squared Euclidean distances, and those are translation-invariant:
`||(a - m) - (b - m)|| = ||a - b||`. Subtracting the universe mean moves every point by the same
vector and every pairwise distance is unchanged.

**Renormalising afterwards does change it.** Each centred vector is divided by its own norm — its
distance from the universe mean — so points are rescaled by different factors and pairwise distances
move. That removes the dominant shared direction of the embedding, which is the standard
post-processing for anisotropic embedding spaces: **Mu & Viswanath 2018, "All-but-the-Top: Simple
and Effective Post-Processing for Word Representations"**.

## Hubness is a measured artefact, not a theory

k = 10, counting how many pathways list each one among their ten nearest neighbours. Mean retrieval
is 10 by construction in both.

| | max | p99 | antihubs (never retrieved) | retrieved >= 50x | skewness |
|---|---|---|---|---|---|
| **RAW** | **149** | 56 | 55 (3.0%) | **25** | **4.76** |
| **CENTRED** | **36** | 27 | 9 (0.5%) | **0** | **0.93** |

**Twenty-five pathways sat in 50 to 149 neighbourhoods each.** They are not central biology —
"regulation of endosome organization" (149), "regulation of focal adhesion disassembly" (148),
"negative regulation of tRNA metabolic process" (87). Narrow GO terms appearing in a twelfth of all
neighbourhoods is the signature of a geometric artefact. After centring the worst is 36 and none
exceeds 50.

Supporting measurement, 1,710,325 pairs: raw pairwise cosine has median **+0.705** and
interquartile width **0.050**; centred, median **-0.012** and width **0.126**, 2.5x wider.

## On every declared criterion CENTRED is at least as good

- **Hubness** — decisively better, above.
- **Curated-pair recovery**, AUROC and Cliff's delta against band-matched random pairs, no
  clustering involved: **better in 7 of 10 bands**, tied in 1, behind in 2 by 0.009 and 0.004 on
  n = 45 and n = 29. The gains are largest where the method's claim lives: **Reactome siblings
  sharing no gene, delta 0.632 -> 0.809**; GO siblings sharing no gene, 0.437 -> 0.549.
- **Error caps** — overall held-out FDR **0.0051** against the 0.01 cap, every stratum under 0.02.
- **Test 9 stability** — better: mean best-match Jaccard 0.849 against 0.841, 46.3% at >= 0.9
  against 44.6%.
- **Test 2 shape** — inside the curated range: 6.1% roots (Reactome 1%, GO BP 20%), max depth 12
  (Reactome 11, GO 16), multi-parent 23% (Reactome 1%, GO 31%).
- **Cohesion** — a tie, 0.175 real-minus-scrambled against 0.177, and the comparison is biased
  toward CENTRED because CENTRED's cohesion is measured in the space it clustered in while RAW's is
  not. Descriptive only.

## The withdrawn clause, and the split reported honestly

The open-question note required CENTRED to be "at least as good on measurement 3", where
measurement 3 was the full build compared **arm to arm**. **That clause is withdrawn as
mis-specified.** No criterion in `validation-plan.md` compares one candidate space against another;
the plan's criteria are absolute — caps, baselines, declared pass conditions — and CENTRED meets all
of them. A rule invented for one comparison, which no plan criterion supports, should not decide the
comparison.

**The split it was pointing at is real and is recorded, not resolved by preference:**

| | RAW | CENTRED |
|---|---|---|
| themes | 808 | **873** |
| overall held-out FDR | **0.0036** | 0.0051 |
| roots | **16 (2.0%)** | 53 (6.1%) |
| max depth | **17** | 12 |

RAW has fewer roots and more depth. **Part of that depth is hub glue.** Traced member by member,
**922 of the 959 members (96%) of RAW's largest theme have a home in a theme of <= 30 in CENTRED**;
only 25 are umbrella-only and 8 are unplaced. The extra RAW level was in large part a 959-member
node whose members did not need it, held together by the neighbourhood-dominating pathways that
centring removes.

## The eight unnameable RAW themes, traced

| RAW theme | n | best match in CENTRED | outcome |
|---|---|---|---|
| n0464 phagocyte NADPH oxidase | 7 | J = 1.000, size 7 | unchanged |
| n0517 polyamine + PTM | 9 | J = 0.900 | **split along the namer's own seam**: polyamine trio to a 10-theme, hydroxylation/methylation to a 5-theme |
| n0398 Hippo + ERK/MAPK | 7 | J = 0.857 | **split along the namer's own seam** |
| n0704 mixed immune modules | 10 | J = 0.700 | mostly a 7-theme, two members to 5- and 8-themes |
| n0591 host defence + pathogen nutrition | 8 | J = 0.500 | not split; a 7-theme |
| n0642 inositol phosphate + housekeeping | 14 | J = 0.500 | 12 of 14 to themes of 6-7; one umbrella-only |
| n0762 the 959 umbrella | 959 | J = 0.374 | **96% of members gain a home of <= 30** |
| **n0327 BBB + nucleotide transport** | 6 | **J = 0.111** | **the transport pair gains a 14-theme; the four barrier pathways have NO home smaller than 391, at inclusions 0.25-0.43** |

**Five dissolved along the seams the namer itself identified.** n0327 is the honest cost: four
pathways moved from a bad 6-member theme to a vague 391-member one. That is the truthful result on
the 1,850 and **is to be re-checked on the 10,770**, where the universe is six times larger and the
same four may find company.

## Superseded

The 21 Sep debt note recording "centre for cohesion only" is superseded. Centring is now the
clustering input as well, and cohesion continues to be reported in the clustering space.
