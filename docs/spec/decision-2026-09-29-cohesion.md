## 2026-09-29 — Cohesion of the frozen 0.50 build, the null it was measured against, and why no cohesion threshold is added

**Measured by the reviewer on the frozen `v0.2.2-subset-1850-c50` build, ad hoc, from the same
centred-and-renormalised MedCPT vectors the build clustered.** The code is to be committed as
`scripts/cohesion_reference.py` and this table reproduced from it before this entry is relied on.

**Cohesion** of a theme = mean pairwise cosine among its members in the centred space. It is the
build's own geometry, not gene overlap and not names.

### The build, in shape

800 themes: 61 roots, 513 internal nodes, 287 leaves. Leaves have 3–9 members (median 5). The 61
roots are **three super-domains plus 58 islands**: n0781 (819 members — metabolism, muscle,
neuro, sensory, protein folding, blood pressure), n0552 (301 — immunity, viral, complement,
haemostasis), n0304 (284 — transcription, RNA, cell division, senescence). The islands are 4–62
members, mostly pure GO. Depth to 12, 22% multi-parent, 224 internal nodes with two children and 44
with three or more.

**245 of 513 internal nodes have exactly one child** (parent = child + a median of 3 direct
members; 147 single shells, 46 double, 3 triple). Compared on the superseded 0.25 build: 289 of 588
(49% → 48%), double/triple chains 60/10 → 46/3, mean depth 4.07 → 3.61. **The single-child shape is
a property of the method, not of the cutoff, and 0.50 shortened the chains.** It is recorded as a
shape, not a defect: a parent that is its child plus a few pathways on the same topic is legitimate
biology; the extras did not form their own child because they do not recur as a group. Its one
consequence is for naming: the tightest true name of "child + 3 more" is often the child's own
phrase, which is what the mechanical collision check and re-ask exist for.

### Cohesion by size

| members | themes | median cohesion | p10 |
|---|---|---|---|
| 3–5 | 156 | 0.477 | 0.349 |
| 6–9 | 316 | 0.380 | 0.273 |
| 10–19 | 241 | 0.340 | 0.255 |
| 20–49 | 70 | 0.312 | 0.241 |
| 50–199 | 10 | 0.235 | 0.191 |
| 200+ | 7 | 0.125 | 0.073 |

Leaves: p10 / median / p90 = 0.289 / 0.416 / 0.597 (0.25 build: median 0.415 — unchanged).
All-theme median 0.370 (0.25 build: 0.352).

Cohesion falls with size mechanically. **Any single cosine threshold is therefore a size cap in
disguise.**

Least cohesive leaves: n0640 (0.160: inner cell mass differentiation, response to erythropoietin,
decidualization, primitive erythrocyte differentiation, response to progesterone, structure
maturation), n0518 (0.180: copulation, response to herbicide, protein processing, regulation of
proteolysis, response to genistein, peptide biosynthesis), n0601 (0.187), n0790 (0.204), n0694
(0.210). Most cohesive: n0022 (0.808: four FLT3-inhibitor-resistant mutant sets), n0192 (0.778),
n0031 (0.753: three DNA-replication pathways).

### Two nulls, and which one is informative

**Null 1 — random sets from the actual space.** Random subsets of the 1,850 pathways, same size as
each theme, centred space, 20 draws per leaf and 200 per size stratum (seed 0). Result: **0.000 ±
0.01 at every size.** This is by construction: after centring, the mean cosine over all pairs is
zero. Every theme beats it by an order of magnitude. It answers "is this group better than chance"
with a yes that carries no information, because Ward always groups the nearest things.

**Null 2 — kNN-ball reference.** Pick a random pathway, take its s−1 nearest neighbours in the
centred space, measure the ball's cohesion: the tightest group of size s the space can offer at a
random location. 300 balls per stratum (seed 1). This is the demanding reference: it asks whether
a theme is as related as things get.

| members | kNN-ball p5 | kNN-ball median | themes p10 | themes median | themes below kNN p5 |
|---|---|---|---|---|---|
| 3–5 | 0.268 | 0.440 | 0.349 | **0.477** | 1 of 156 |
| 6–9 | 0.208 | 0.356 | 0.273 | **0.380** | 4 of 316 |
| 10–19 | 0.183 | 0.302 | 0.255 | **0.340** | 1 of 241 |
| 20–49 | 0.136 | 0.243 | 0.241 | **0.312** | 0 of 70 |
| 50–199 | 0.082 | 0.154 | 0.191 | **0.235** | 0 of 10 |
| 200+ | 0.018 | 0.068 | 0.073 | **0.125** | 0 of 7 |

**At every size, the themes are tighter than typical nearest-neighbour balls of the same size, and
6 of 800 fall below the reference's 5th percentile.** Even the 200+ umbrellas are twice as cohesive
as a random 200-ball. The recurrence gate selects groups at least as tight as the space's own
natural neighbourhoods at every scale. This is the measurement behind the claim that the build is
cohesive, and it is a claim about the embedding space, not about biology.

### What a cohesion threshold would do, measured

A cut at cohesion < 0.20, proposed as "too unrelated to stay":

| | 0.25 build | **0.50 build** |
|---|---|---|
| themes removed | 31 | **19** |
| of which roots | 9 | **9** |
| of which every theme ≥ 200 members | 6 of 6 | **7 of 7** |
| of which leaves | 5 | **3** |
| roots after removal | 53 → 158 | **61 → 167** |
| pathways losing their only home | 58 | **87** |

It deletes the top of the tree and leaves the incoherent leaves almost untouched — the five listed
above sit at 0.16–0.21, on the line.

### Decision: no cohesion threshold

1. **A threshold picked by inspection violates the standing rule** that no number in the procedure
   is chosen by its outcome. The support floors are solved against scrambles at a declared FDR;
   "0.20" has no such basis.
2. **It is a size cap, not a relatedness test** (table above), and what it removes is what the
   size already says: the umbrellas.
3. **Against the only informative null, the geometry finds nothing to remove.** The leaves a reader
   would reject ("copulation, response to herbicide, protein processing") are geometrically
   legitimate: the embedder placed those descriptions near each other. That failure is semantic
   and only a reader can see it.

**What judges "too unrelated" instead: the namer's `nameable: false`.** A theme the namer refuses
is shown as an *unnamed umbrella* and never hidden. **Recorded reservation (Aviyah):** she does not
like an LLM verdict acting as the structural filter; it is accepted for now because no measured
geometric rule does the job and every refusal stays visible and auditable.

**Follow-up, declared before the leaf names exist.** After level-0 naming on this build, compare
the cohesion of refused leaves against named ones. If refusals concentrate in the low-cohesion
tail, a **size-aware floor calibrated from those verdicts on the 1,850** may be declared and
applied to the 10,770 — calibrated-then-applied is defensible, picked-by-eye is not. If they do
not concentrate, the idea is closed and this entry says so.

### Reproduction

Inputs: `data/ontology/v0.2/embeddings.npy`, `embedding_keys.txt`, `centre_and_renormalise` from
`thema.embed`, `recurrent_dag_c50/{nodes,members}.tsv` (and `recurrent_dag_consensus_centred` for
the 0.25 column). Seeds: 0 (random sets), 1 (kNN balls). Draws: 20 random sets per leaf, 200
random sets and 300 balls per stratum. Strata: 3–5, 6–9, 10–19, 20–49, 50–199, 200+.

*Amended 2026-09-29.* Reproduced by `scripts/cohesion_reference.py`; the kNN-ball columns above are
the script's (ball p5/median per stratum and 6 of 800 below p5), the ad-hoc figures differed by at
most 0.02 and are superseded. Null 1 spread: sd 0.042 at 3–5, 0.021 at 6–9, below 0.01 above.
