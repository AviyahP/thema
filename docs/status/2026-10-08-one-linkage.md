# One linkage for every level: C passes Step 1, and Step 2 estimates at the 3 h limit. 8 Oct 2026

Declared 8 Oct 2026 before any result. Branch `leaves-2026-10`. Exploratory.
`thema_L`, `v0.3` and `v0.4` untouched.

**Confirmed before starting**, as asked: C keeps **unnormalised running sums**, so
`cos(c_A, c_B) = (s_A · s_B) / (‖s_A‖ ‖s_B‖)` and a merge is one vector addition — exact at every
step, no drift, no re-reading of members. The similarity matrix is held in full as float32 (124 MB at
n = 5,559) with cached per-row maxima and lazy invalidation, which turns the obvious cubic loop into
roughly quadratic work: **3.9 s per tree instead of 64 s**. It is proved merge-for-merge and
height-for-height identical to a cubic reference that shares none of that bookkeeping.

**Step 1's verdict: C meets all three declared conditions, and so does A.** On the primary statistic
C wins by a wide margin — **1,085 nodes of 51–1000 members against Ward's 169**.

**Step 2 is NOT run.** Measured estimate **~3.0 h**, at the declared "stop if over 3 h" boundary
rather than under it. The numbers behind that are below, and two caveats worth weighing before
authorising it are in *What to weigh* at the end.

## Step 1 — one tree per engine on all 5,559 leaves, no resampling

| | W (Ward) | **C (normalised-centroid cosine)** | A (UPGMA on cosine) |
|---|---:|---:|---:|
| runtime | 2.8 s | 4.0 s | 0.2 s |
| height inversions | 0 | **1,335** of 5,558 merges | 0 |
| internal nodes | 5,558 | 5,558 | 5,558 |
| **nodes of 51–1000** | **169** | **1,085** | **235** |

C's inversions are expected and were declared: merging A and B can leave the result *more* similar
to some C than A and B were to each other. They are counted and reported; the containment DAG orders
nodes by membership and never by height, and `run_from_merges` reads only the merge structure.

### Node sizes per band

| engine | 3–5 | 6–10 | 11–20 | 21–50 | 51–100 | 101–300 | 301–1000 | 1001+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W | 1,823 | 731 | 405 | 251 | 87 | 59 | 23 | 7 |
| **C** | 1,309 | 778 | 582 | 472 | **257** | **433** | **395** | 28 |
| A | 1,801 | 824 | 465 | 299 | 116 | 88 | 31 | 9 |

This is the result the experiment was for. Ward produces 23 nodes of 301–1000 members on this data;
C produces **395**. The middle is not missing from the vectors — Ward's merge rule does not express
it.

### Gene coherence — mean pairwise gene Jaccard against a size-matched null

The null must be size-matched: mean pairwise Jaccard falls with set size for purely combinatorial
reasons, so an unmatched null would make every large node look incoherent. 150 nodes per band,
seed 0, 10 null draws each.

| band | W | **C** | A | null |
|---|---:|---:|---:|---:|
| 3–5 | 110.8× | **212.4×** | 125.9× | 0.0011 |
| 6–10 | 75.3× | **136.9×** | 99.7× | 0.0012 |
| 11–20 | 56.1× | **105.0×** | 94.5× | 0.0011 |
| 21–50 | 30.3× | **45.1×** | 40.5× | 0.0012 |
| 51–100 | 17.4× | 19.9× | **24.0×** | 0.0012 |
| 101–300 | 10.3× | **14.2×** | 11.8× | 0.0012 |
| 301–1000 | 4.7× | **5.2×** | 5.2× | 0.0012 |
| 1001+ | 1.6× | 1.7× | **1.9×** | 0.0012 |

**C is at or above W in every band**, and strictly above in seven of eight. So the 395 nodes of
301–1000 that C adds are not bought by diluting coherence — at that size C is *more* gene-coherent
than Ward's 23. A is also at or above W everywhere.

All three collapse to near-random at 1001+ (1.6–1.9×), the same result the theta arms gave. The top
of this hierarchy is not gene-coherent under any merge rule tried so far.

### Children per node, after collapsing chain links

A child holding more than 70% of its parent is the same group with something added, not a branch, so
collapsing it lifts its own children into the parent. A long absorption chain therefore shows up as a
node with many children.

| engine | median raw | median collapsed | **max collapsed** |
|---|---:|---:|---:|
| W | 2 | 2 | **4** |
| **C** | 2 | 2 | **72** |
| A | 2 | 2 | **6** |

**This contradicts the brief's premise, and it is the most important caveat in this report.** The
brief expects Ward to absorb small groups one at a time into blobs. On the raw tree it is **C** that
has the long absorption chain — one node with 72 collapsed children against Ward's 4. The median is
2 for all three, so this is a tail phenomenon rather than the typical node, but it is C's tail, not
Ward's.

The brief's "giant roots with 100–227 children" is a property of the *built ontology's* DAG, after
recurrence, completion, absorption and consensus — not of the raw Ward tree, where every node has
exactly two children. Step 1 measures raw trees, so it cannot confirm or refute that figure; what it
can say is that the chain behaviour is not visible in Ward's tree and is visible in C's.

### Leaves by the largest node of 1,000 or fewer they belong to

| engine | 11–20 | 101–300 | 301–1000 | none/other |
|---|---:|---:|---:|---:|
| W | 0 | 0 | **5,559** | 0 |
| **C** | 14 | **1,015** | 4,508 | 22 |
| A | 0 | 732 | 4,765 | 0 |

Every single leaf in Ward's tree has its largest sub-1000 node in the 301–1000 band — there is
nothing finer to place it in. C gives 1,015 leaves a home in a node of 101–300. That is the same
finding as the band table, seen from the leaf's side.

### Cut at 30 — the dominance condition, and what the cuts actually look like

25% of 5,559 leaves is 1,389.

| engine | largest | share | 2nd | 3rd | clusters < 3 members | condition |
|---|---:|---:|---:|---:|---:|---|
| W | 430 | 7.7% | 352 | 344 | 0 | **PASS** |
| **C** | 1,350 | **24.3%** | 1,143 | 809 | **19** | **PASS**, by 0.7 points |
| A | 798 | 14.4% | 741 | 693 | 0 | **PASS** |

**C passes the letter of the condition and is degenerate in a way the condition does not measure.**
Its 30 clusters are really **8 substantial ones plus 22 scraps**, 19 of them singletons, and the top
four hold 73.7% of all leaves. Ward's cut at 30 is beautifully even (every cluster 59–430) and A's
is reasonable (5–798). The condition tests one cluster's share; C's problem is the shape of the rest.

C's eight substantial clusters are, however, legible and cross-database — which is the thing the
reviewer's check was pointing at:

| n | share | nearest the centroid |
|---:|---:|---|
| 1,350 | 24.3% | neural plate morphogenesis; ventricular compact myocardium morphogenesis; limb bud formation; notochord morphogenesis |
| 1,143 | 20.6% | medium-chain fatty acid catabolic process; Glycine degradation; metabolism in mitochondria, peroxisome |
| 809 | 14.5% | DNA strand elongation involved in DNA replication; telomere maintenance via recombination |
| 797 | 14.3% | positive regulation of T-helper 1 cell differentiation; TLR and inflammatory signaling |
| 538 | 9.7% | positive regulation of synaptic vesicle exocytosis; regulation of presynaptic membrane potential |
| 371 | 6.7% | regulation of endosome organization; late endosome to lysosome transport; Lysosome Vesicle Biogenesis |
| 292 | 5.2% | AKT-mediated inactivation of FOXO1A; FOXO-mediated transcription of oxidative stress |
| 205 | 3.7% | sunitinib-resistant FLT3 mutants; Signaling by ERBB2 TMD/JMD mutants |

Eight coherent areas, not the "about 30" the reviewer's centroid check suggested. Full cuts at 20,
30 and 50 for all three engines, with the seven nearest names each:
`data/experiments/one_linkage/cuts.txt`.

### Curated recall at Jaccard > 0.5, secondary closure, by any node of the tree

| engine | re 3–10 | re 11–50 | re 51–200 | go 3–10 | go 11–50 |
|---|---:|---:|---:|---:|---:|
| W | 0.334 | 0.189 | **0.053** | **0.117** | 0.004 |
| **C** | 0.313 | **0.216** | 0.000 | 0.088 | 0.004 |
| A | **0.364** | **0.225** | **0.053** | 0.114 | 0.007 |

**Not part of the declared criterion, and it does not favour C.** C is slightly worse than Ward on
the two 3–10 cells (−0.021 Reactome, −0.029 GO) and loses the `re 51-200` cell entirely. A is the
best arm here, beating Ward on three cells of five. C's gain is in the 11–50 band (+0.027).

Note what this says about the mid-sized nodes C adds: they are gene-coherent but they are **not** the
curated summaries. More structure in 51–1000 did not convert into recovering more curated sets.

## The declared Step 1 criterion, applied

> Step 2 only if C or A beats W: more nodes of 51–1000 members, gene coherence in each band not
> below W's, and cuts at 30 not dominated by one cluster holding more than 25% of the leaves.

| | more 51–1000 nodes | coherence ≥ W in every band | cut-at-30 ≤ 25% | **qualifies** |
|---|---|---|---|---|
| **C** | yes — 1,085 vs 169 | yes — 7 of 8 strictly above | yes — 24.3% | **YES** |
| **A** | yes — 235 vs 169 | yes | yes — 14.4% | **YES** |

**Both qualify, so the criterion is met and Step 2 is authorised by the brief.** C is the engine the
experiment is about and it dominates the primary statistic 6.4-fold, so C is the one Step 2 would
run.

## Step 2 — estimated, not run

Step 2 needs one new piece, which is built and proved: `linkage.run_from_merges`.
`recurrent.tree_from_subset` calls scipy's `linkage` itself, so there is no way to hand it a tree
built by another rule; `run_from_merges` does the identical bookkeeping over a supplied merge
sequence. Feeding Ward's own merges through it produces a `Run` that is **field-for-field identical**
to `tree_from_subset`'s — all seven arrays — so the duplicated logic is checked rather than trusted.

Measured, not guessed:

| | measured | |
|---|---|---|
| C on one 80% subsample of L (4,448 points) | **2.54–2.69 s**, mean 2.61 s | agglomerate 2.57 s + `Run` 0.04 s |
| recorded clusters per tree | C 3,399 against Ward's 2,703 | **1.26×** Ward's pool |

| cost | arithmetic | hours |
|---|---|---:|
| trees: 200 real + 12 scramble sides × 200 | 2,600 × 2.61 s | **1.89** |
| side material, 13 sides, at C's 1.26× pool | 160 s + 12 × 210 s | **0.75** |
| floors on 10 seeds, build, two halves, metrics | | **0.35** |
| **total** | | **≈ 2.98** |

**That is at the 3 h limit, not under it**, and the side-material term is the uncertain one — C's
larger pool makes matching superlinearly slower, and 1.26× on the pool is the measured ratio rather
than the measured cost. So I am stopping here per the declared rule rather than starting a job whose
own estimate touches the boundary and which would leave nothing finished if it overran.

The 10 calibration seeds are what makes it expensive: 2,000 of the 2,600 trees are scrambles. That is
declared, so I have not traded it away. If you want Step 2 run, the cheapest honest reductions are
yours to choose — fewer calibration seeds (at the cost of the noisy-FDR problem that bit `thema_L`'s
5-5 stratum), or 100 runs instead of 200.

## What to weigh before authorising Step 2

Three things in C's favour: **1,085 mid-sized nodes against Ward's 169**, gene coherence at or above
Ward's **in every band**, and eight legible cross-database areas at a 30-cut.

Three things against: **curated recall is not better** and is slightly worse at 3–10, so the new
structure is coherent without being the curated summaries; the **30-cut is degenerate** — 8 real
clusters and 19 singletons, top four holding 73.7%; and the **chain behaviour the brief attributes to
Ward appears in C**, which has a node with 72 collapsed children against Ward's 4.

A is the quieter alternative: it qualifies too, it is the **best arm on curated recall**, its cuts are
well-formed at every level, it costs 0.2 s a tree, and it needs no new engine code at all — it is one
`method="average"` call on cosine distance. It gains 235 mid-sized nodes rather than 1,085.

Nothing is frozen. **Aviyah decides.**

Written: `data/experiments/one_linkage/step1.json` (every number above, plus the cuts at 20, 30 and
50 for all three engines with source mixes), `data/experiments/one_linkage/cuts.txt`.
