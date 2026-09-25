# FROZEN — the 1,850-pathway subset build

**This is a subset build. It is not the THEMA ontology.** The universe is **10,770** pathways;
this build covers the **1,850** that were embedded for method development. Every number in it,
everywhere it is quoted, is the subset's.

| | |
|---|---|
| frozen | 2026-09-25 |
| built from commit | `b1d9c264c55ebd566694a7a91db5bb8a26511b55` |
| build script | `scripts/build_consensus.py` |
| universe digest | `c54319cdfbbe9eb7` |
| descriptions digest | `0c826d92c2d968fa` |
| embeddings sha256[:16] | `e15070710a36a0fa` |
| embedder | `ncbi/MedCPT-Article-Encoder` @ `d05a736da4bb84ee4057b7f7999485be6ed85465` |
| pooling / window | CLS / 512 tokens — **max description 247, nothing truncated** |
| pathways embedded | 1,850 of the 10,770 universe |
| excluded, no genes | 47 |

## The rule this was built under

`RUNS` = 100 resampling runs, subsample 0.80, Ward linkage, `min_size` 3.
Jaccard matching at **theta = 0.70**. Membership cutoff **0.25**.
Declared **m = 0.33**, with a per-size floor solved on the calibration scrambles at FDR <= 0.01;
effective threshold `max(declared, floor)`. Greedy consensus before `hasse`
(`docs/spec/amendment-2026-09-25.md`) at **STRAY = 0.10**, **JACCARD = 0.70**.

Per-size floors: 3 → 0.976744 · 4 → 0.909091 · 5 → 0.720000 · 6 → 0.608247 · 7–9 → 0.450000 ·
10–14 → 0.101010 · 15–29 → 0.020202 · 30+ → 0.020000.

## What it measured

| | |
|---|---|
| themes | **808** (844 before consensus) |
| edges / roots | 998 / **16** |
| multi-parent | 24% |
| max / median depth | 17 / 4 |
| unplaced | **0** |
| **held-out FDR, overall** | **0.0037** against a 0.01 cap |
| held-out FDR, worst stratum | 0.0147 (size 6) against a 0.02 cap |
| calibration | 20 calibration + 10 held-out scrambles |

**Test 2** (shape, informational): 2.0% roots, depth 17/4, 24% multi-parent — between full GO BP
(20% roots, 16/5, 31%) and full Reactome (1% roots, 11/3, 1%) on every statistic.

**Test 9** (seed stability, informational): mean best-match Jaccard **0.841** against master seed 1;
97% of themes match at >= 0.5, 85% at >= 0.7, **45% at >= 0.9**.

## What "frozen" means here

**It applies to the theme set and its nesting**, which reproduce across subsample seeds at the
declared theta. **It does not apply to exact member lists** — only 45% of themes match at >= 0.9, so
a theme's precise boundary moves with the seed. Per-member uncertainty is carried by `inclusion`.
A claim of the form "this theme contains exactly these N pathways" may not be made without the
inclusions beside it. See `DECISIONS.md`, 25 Sep 2026.

## Not done

No naming. No enrichment. Validation tests 3, 4, 5 and 6 not run — 3, 4 and 5 are gates and are
scheduled on the 10,770, not here. Open items are listed in
`docs/status/2026-09-25-consensus-dag-1850.md`.
