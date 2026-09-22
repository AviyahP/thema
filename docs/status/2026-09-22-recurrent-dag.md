# `recurrent_dag` — state as of 22 Sep 2026

Where the method stands, what the numbers are, and what is still open. The algorithm itself is in
`docs/spec/addendum-2026-09-21.md`; this file is the evidence and the to-do list.

**Nothing here is committed to as a shipping choice.** The demo remains on `ward_tree`.

---

## The Ward scan — two-sided matching, member cutoff 0.5, families-first

v0.2 embeddings (v4 descriptions), 1,854 pathways, 100 runs, subsample 0.80. Each cell has its own
scrambled control through the identical procedure.

| tol | m | real | null | FDR | nodes | placed | roots | multi | med/max | immune 100+ |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.25 | 1,218 | 33 | 0.027 | 417 | 94% | 190 | 20 | 8/221 | 221 @ 96% |
| 0.05 | 0.33 | 901 | 9 | 0.010 | 334 | 88% | 198 | 7 | 8/40 | none |
| 0.15 | 0.25 | 2,135 | 33 | 0.015 | 491 | 97% | 189 | 55 | 9/250 | 250 @ 85%, 222 @ 96% |
| **0.15** | **0.33** | **1,563** | **9** | **0.006** | **391** | **92%** | **158** | **19** | **9/253** | **253 @ 84%, 222 @ 96%** |
| 0.25 | 0.25 | 3,334 | 66 | 0.020 | 593 | 100% | 41 | 193 | 10/687 | 222, 144, 126 |

**`tol = 0.15, m = 0.33` is the best cell measured**: the lowest FDR anywhere (0.006), 92% placed,
and both immune themes present. It beats `tol = 0.05, m = 0.33` on every axis.

**`tol = 0.25` is over-merging**: 100% placed, but a 687-member node, 193 multi-parent nodes, roots
collapsing to 41, and the FDR doubling.

---

## The immune finding

The earlier report identified 215 pathways excluded from the runaway node — every BTM blood-cell
module, seven immune Hallmark sets, the interleukin/TLR/complement cascades, ~150 GO immune terms.
214 resolve inside the 1,854.

**The set is coherent.** On mean-centred embeddings (per `docs/debt.md`):

| | raw | mean-centred |
|---|---|---|
| silhouette, immune vs rest | +0.0993 | +0.0782 |
| mean within-immune | 0.4829 | 0.3235 |
| mean immune-to-other | 0.2250 | **-0.0438** |
| within minus between | +0.2579 | **+0.3673** |

Centring makes the separation clearer: immune-to-other goes below zero while within-immune holds at
0.32.

**The immune members do not scatter — the contamination does.**

```
share of appearances outside the best-matching cluster
  immune members:      2%   (1,499 of 68,325)
  non-immune members: 68%   (13,929 of 20,393)
```

A 34-fold difference. The large immune-majority groupings are ~75% immune plus ~25% unrelated
material — viral pathways, `TBA` placeholders, wound healing — and it is that minority which moves
every run and drags the whole grouping below threshold.

**Two-sided matching recovers the theme.** At tol=0.05, m=0.25: a **221-member node, 96% immune,
support 0.42**, labelled `activation · production · interleukin`, with `regulation of cell
activation`, `immuregulation - monocytes, T and B cells` and `leukocyte differentiation` at its
centre. Under the one-sided rule this theme was rejected in 99 of 100 runs.

**The 0.5 cutoff does the complementary work.** The non-immune members that survive sit at
0.54–1.00 — present in a majority of the matched copies. The 68%-scattering material is excluded.

**A correction, recorded so it is not repeated.** An earlier report concluded "a 220-member immune
grouping is not stable across resampling — immunity at this granularity genuinely doesn't recur."
**That was wrong.** The immune core is stable at 98%. The same report mislabelled a table of 20
scattering pathways as immune; none of the 20 were in the 215.

---

## Open

**1. Average linkage.** The scan was killed after the Ward half. Under the OLD one-sided matching,
average beat Ward structurally (97% vs 96% placed, 191 vs 229 roots, 27 vs 21 multi-parent) but
produced no immune theme over 36 members, and no null table was ever run for it. The average half
of the two-sided scan is in flight. **Until its FDR exists, "average produces more themes" and
"average produces better themes" are indistinguishable.**

**2. Same biology at two sizes.** Not caught by the variant rule and not yet characterised. Ward at
tol=0.05: cardiac at 45 and 40; interferon/viral at 44, 32 and 30. Average linkage is worse: muscle
three times (44, 39, 33), photoreceptor twice (41, 37). At tol=0.15, m=0.25 two immune themes
coexist at 250 and 222.

**The specific question to answer: are these pairs NESTED or OVERLAPPING?** Nested pairs are a
legitimate hierarchy — a theme and its sub-theme — and belong in the DAG as parent and child.
Overlapping pairs that are neither nested nor variants are redundancy with no defensible reading.
The counts have not been taken, and the answer decides whether a rule is needed at all.

**3. Checks before any 10,817 spend.**

*Description stability* — 300 of the 1,854 regenerated under a fresh ledger namespace (same prompt,
so it measures LLM non-determinism rather than a prompt change), re-embedded, ward_tree rebuilt with
those 300 swapped, ARI against v0.2 at k=10/30/100. **Priced at $3.87 cached, $5.44 ceiling.
Not submitted.**

*v3 vs v4 ontology evaluation* — implemented and run. **v3 scores better on both external measures:**

| | v3 | v4 |
|---|---|---|
| ancestor-pair F1 vs Reactome | **0.2614** | 0.2114 |
| ancestor-pair F1 vs GO | **0.2113** | 0.1936 |
| reactome2go recovery, k=50 | **90.8%** | 86.8% |
| reactome2go recovery, k=100 | **90.8%** | 82.9% |

This contradicts the assumption behind adopting v4: fewer factual errors (20 vs 27 wrong claims per
100, replicated) did not produce a better-structured ontology by these measures.

**Two reasons not to treat it as settled.** reactome2go supplies only 76 usable pairs here, and
`docs/eval-plan.md` records that 57 of them are also name collisions — so most of that signal is the
pathway name appearing in both texts. And both metrics reward text echoing the curators' own
hierarchy, which is precisely what v4 removed by dropping the verbatim name. **The name-free
ablation (prompt queue item 2) should run before concluding v4's ontology is worse.**
