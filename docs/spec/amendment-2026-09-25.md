# Fourth amendment, 25 Sep 2026 — greedy consensus before the DAG

*Amends `addendum-2026-09-21.md` §10.7 (node assembly) and §10.8 (edges). `hasse` is unchanged and
stays strict. `families()` is unchanged. Earlier documents are not rewritten.*

---

## What was wrong

The confirmatory export accepted every family that passed the per-size gate and handed the lot to
`hasse`. **Nothing checked that the accepted sets were compatible with one another.** 39 roots came
out. Eleven were near-nested pairs severed by one member landing on opposite sides of the 0.25
cutoff in two different vote populations: `n0610` (302 members) and `n0431` (342) share 301, and
`Signaling by MST1` scored **0.269** in one vote and **0.229** in the other. The smaller set is not
a subset, so it gets no parent.

`hasse` was correct throughout. The member sets handed to it were not mutually compatible.

## The method, and its provenance

This is **majority-rule / greedy consensus**, the standard construction in phylogenetics:
clusters are considered in order of support and admitted only if compatible with what is already
accepted (Bryant 2003, "A classification of consensus methods for phylogenetics"; Felsenstein 2004,
*Inferring Phylogenies*, ch. 30). The classical compatibility test is exact — nested or disjoint.

THEMA's clusters are **fuzzy**: their boundaries come from thresholding a vote, so a member near
the cutoff is noise rather than signal. The extension below keeps the classical structure and
replaces exact compatibility with two declared tolerances.

## The rules — one pass, after the gate, before `hasse`

Parameters, **declared before the run**: `STRAY = 0.10`, `JACCARD = theta = 0.70`. Nothing else.

Process kept themes in decreasing support (ties: larger size, then bitset key). For each pair, with
**A the larger and B the smaller**:

```
strays_B = |B \ A| / |B|        strays_A = |A \ B| / |A|
```

1. **B strictly inside A** → nested; `hasse` draws it.
2. **(`strays_B <= STRAY` or `|B \ A| <= 1`) and `strays_A > STRAY`** → B is a sub-theme of A.
   **`A := A ∪ (B \ A)`.** Added members are flagged `inherited` and carry their inclusion in B.
   Propagate: every accepted ancestor of A, by strict containment *before* the addition, gains the
   same members, to a fixed point. Additions only, so it terminates.
3. **else `Jaccard(A, B) >= JACCARD`** → same theme, neither contains the other: keep the higher
   support, record the other **superseded**.
4. **else** → coexist; multi-parent as §10.8.

**Order matters only in rule 3.** No re-gating: support is untouched, and the floor a theme was
judged against is its evidence, not its final size.

**Identical sets fall to rule 3, not rule 1.** Rule 1 as stated is satisfied by equality, but
accepting both would put two nodes with the same members into `hasse`, which draws no edge between
them and leaves both as roots — reintroducing the defect. Rule 1 therefore requires STRICT
containment. This is the one clause not in the brief as written.

## Why the resolution is asymmetric — the larger theme grows

**A first attempt rejected the loser of each conflict and made things worse: 39 roots became 108,
and 87 pathways were stranded with no theme at all.** The cause is a confound the classical method
does not face. In THEMA, **support is anti-correlated with size: Spearman −0.583, p = 4e-78** over
the 844 candidates — median support 0.94 at sizes 3–5 against 0.49 at 100+. A large theme recurs
*approximately* across resamples; a small tight one recurs *exactly*. Seating strictly by support
therefore let 12- and 9-member themes evict the 953- and 503-member umbrellas above them:

| rejected | support | lost to |
|---|---|---|
| 953 | 0.350 | a 12-member theme at 0.900 |
| 503 | 0.340 | a 9-member theme at 0.850 |
| 342 | 0.690 | a 6-member theme at 0.940 |

Classical consensus assumes support is comparable across clusters; a bootstrap value is not
systematically confounded with clade size. **Here it is.** So nothing may be discarded for having
low support, and the resolution grows the larger set instead. **No theme is ever rejected for being
big**, and rule 2 is additive, which is why nothing becomes unplaced.

## Withdrawn

Two constructs from the first attempt are **withdrawn** and must not reappear:

- **the `is_variant` allowance band** as a consensus rule (`max(2, 10% of the shared part)`
  resolving both-sides-small differences). It remains correct inside `families()`, where it decides
  whether two groupings are the same cluster; it is not the right test for compatibility between
  accepted themes;
- **the minimum-overlap conflict test and its parameter `delta`.** It rejected the lower-support
  theme on overlap alone, which is exactly the move the size confound makes invalid.

## Cost

**None in coverage: 0 pathways unplaced**, unchanged from the pre-consensus export. 36 themes are
superseded and 452 member-slots are inherited across 247 themes (30 of those by propagation). The
inherited members sit at median inclusion **0.308**; 50 of 452 are below the 0.25 cutoff, arriving
because a sub-theme held them and its parent did not.

## Sensitivity — reported, never selected

Grid `STRAY ∈ {0.05, 0.10, 0.15}` × `JACCARD ∈ {0.60, 0.70, 0.80}`, real side and all 30 scrambles:

| STRAY | JAC | nodes | roots | multi-parent | inherited | superseded | unplaced | held-out FDR |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.60 | 778 | 17 | 0.22 | 414 | 66 | 0 | 0.0039 |
| 0.05 | 0.70 | 813 | 17 | 0.25 | 427 | 31 | 0 | 0.0037 |
| 0.05 | 0.80 | 839 | 19 | 0.27 | 437 | 5 | 0 | 0.0036 |
| 0.10 | 0.60 | 777 | 16 | 0.21 | 443 | 67 | 0 | 0.0039 |
| **0.10** | **0.70** | **808** | **16** | **0.24** | **452** | **36** | **0** | **0.0037** |
| 0.10 | 0.80 | 833 | 18 | 0.25 | 478 | 11 | 0 | 0.0036 |
| 0.15 | 0.60 | 782 | 15 | 0.20 | 519 | 62 | 0 | 0.0038 |
| 0.15 | 0.70 | 810 | 16 | 0.23 | 541 | 34 | 0 | 0.0037 |
| 0.15 | 0.80 | 820 | 16 | 0.24 | 564 | 24 | 0 | 0.0037 |

**The primary is inside a flat region.** Across the whole grid roots span 15–19, nodes 777–839,
held-out FDR 0.0036–0.0039, and unplaced is 0 in every cell. No cell is qualitatively different
from its neighbours, so the result does not rest on the parameter choice.

**On the scrambled sides the pass does almost nothing**, which is the check that it is not
manufacturing structure: mean over 30 sides, **3.2 themes through the gate, 3.2 after consensus,
0.0 members inherited, 0.018 themes superseded** — identical in all nine cells. There is nothing
for it to reconcile in a scramble, and it reconciles nothing.

## Error control after consensus — no floor re-solved

| stratum | real | null/side | held-out FDR |
|---|---|---|---|
| 3 | 10 | 0.0 | 0.0000 |
| 4 | 37 | 0.4 | 0.0108 |
| 5 | 45 | 0.4 | 0.0089 |
| 6 | 75 | 1.1 | 0.0147 |
| 7–9 | 182 | 1.1 | 0.0060 |
| 10–14 | 230 | 0.0 | 0.0000 |
| 15–29 | 178 | 0.0 | 0.0000 |
| 30–49 | 24 | 0.0 | 0.0000 |
| 50–99 | 14 | 0.0 | 0.0000 |
| 100–199 | 6 | 0.0 | 0.0000 |
| 200+ | 7 | 0.0 | 0.0000 |
| **total** | **808** | **3.0** | **0.0037** |

Against E's **0.0036** on 844 themes. Every stratum is under its 0.02 cap and the overall is under
0.01. **Sizes changed, so themes moved between strata; no floor was re-solved and no support was
recomputed.**

## Cost to run

**0.2 s** for the consensus pass on 844 themes; 2 m 56 s for all 31 sides including the pools, at
12 concurrent. One sparse-style product plus an O(N²) scan on precomputed counts, with only the
mutated row recomputed after a rule-2 growth.
