# FROZEN — the 1,850-pathway subset, CENTRED clustering space

**A subset build, not the THEMA ontology.** The universe is **10,770** pathways; this covers the
**1,850** embedded for method development. Every figure here is the subset's.

**Supersedes `recurrent_dag_consensus` (tag `v0.2-subset-1850`), which clustered RAW vectors.**
That build stays as history — see `docs/spec/amendment-2026-09-26.md` for the evidence and for the
one clause of the decision rule that was withdrawn as mis-specified.

| | |
|---|---|
| frozen | 2026-09-26 |
| built from commit | `9ca3cf64013665575e45cb9d199970f32fe47cfe` |
| build script | `scripts/build_consensus.py --space centred` |
| **clustering space** | **centred-and-renormalised** (amendment 2026-09-26) |
| universe mean sha256[:16] | recorded in `manifest.json` |
| universe digest | `c54319cdfbbe9eb7` |
| descriptions digest | `0c826d92c2d968fa` |
| embeddings sha256[:16] | `e15070710a36a0fa` |
| embedder | `ncbi/MedCPT-Article-Encoder` @ `d05a736da4bb84ee4057b7f7999485be6ed85465` |
| pooling / window | CLS / 512 tokens — max description 247, nothing truncated |
| pathways | 1,850 of 10,770; 47 excluded for having no genes |

## The rule

`RUNS` 100, subsample 0.80, Ward, `min_size` 3. Jaccard matching **theta = 0.70**. Membership
cutoff **0.25**. Declared **m = 0.33** with a per-size floor solved **in-arm** at FDR <= 0.01;
effective threshold `max(declared, floor)`. Greedy consensus before `hasse` at **STRAY = 0.10**,
**JACCARD = 0.70**.

Floors, solved on this space's own 20 calibration scrambles — **they do not transfer from the RAW
build**: 3 → 0.838 · 4 → 0.890 · 5 → 0.670 · 6 → 0.530 · 7–9 → 0.370 · 10–14 → 0.101 ·
15–29 → 0.0202 · 30+ → 0.020.

## What it measured

| | |
|---|---|
| themes | **873** (902 through the gate, 29 superseded) |
| inherited members | 489 |
| **held-out FDR, overall** | **0.0051** against a 0.01 cap |
| worst stratum | 0.0136 (7–9) against a 0.02 cap |
| calibration | 20 calibration + 10 held-out scrambles |
| **unplaced** | **8** |

**Test 2** (shape, informational): 6.1% roots, max depth 12, median 4, 23% multi-parent — inside the
range set by full Reactome (1% roots, depth 11/3, 1%) and full GO BP (20%, 16/5, 31%).

**Test 9** (seed stability, informational): mean best-match Jaccard **0.849** against master seed 1;
96.9% of themes match at >= 0.5, 85.2% at >= 0.7, **46.3% at >= 0.9**.

**Hubness**, the reason for the space change: at k = 10 no pathway sits in more than **36**
neighbourhoods, against **149** under RAW.

## What "frozen" means here

**The theme set and its nesting.** Not exact member lists — only 46% of themes match at >= 0.9
across subsample seeds, so a theme's boundary moves with the seed. Per-member uncertainty is the
`inclusion` column. "This theme contains exactly these N pathways" may not be claimed without the
inclusions beside it. See `DECISIONS.md`, 25 Sep.

## Not done

No naming on this build yet. No enrichment. Validation gates 3, 4, 5 and 6 unrun. **Known cost,
recorded rather than hidden:** four blood-brain-barrier and drug-response pathways that RAW grouped
into a 6-member theme have no home smaller than 391 members here, at inclusions 0.25–0.43
(`docs/spec/amendment-2026-09-26.md`). To be re-checked on the 10,770.
