# Debt

Things deliberately not done, with enough context to pick them up. Each entry says what it is, why
it was deferred, and what would settle it.

## Per-node cohesion is not measured

*Logged 2026-09-21.*

Neither builder reports how tight a node actually is. `recurrent_dag` carries `support` — how often a
grouping recurred — and `inclusion` per member, but nothing says whether a node's members are close
to each other in embedding space or merely ended up in the same branch. `ward_tree` carries nothing
at all beyond the cut that produced it.

**Why it matters.** Two nodes can have identical support and very different quality: one a tight
cluster, the other a ragged group that happened to survive resampling. A reader browsing the demo
cannot tell them apart, and the naming step will be asked to name both.

**Why deferred.** The tol × m grid decides whether `recurrent_dag` ships at all. Measuring cohesion
on a method that may not ship is work that may not be needed, and it is not required to choose
`m` or `tol`.

**What would settle it.** Mean pairwise cosine within a node against a size-matched random baseline,
reported per node in `nodes.tsv` and surfaced on the node card. The gene-overlap evaluation
(`eval-plan.md` §14 item 2) is the independent check; cohesion is the cheap internal one, and being
internal it is circular on its own — a node is cohesive in the space it was clustered in. It is a
triage signal, not evidence.

## Cohesion must be measured on mean-centred embeddings

*Logged 2026-09-21.*

Measure cohesion on **mean-centred** embeddings -- for the cohesion calculation only, never for the
vectors Ward clusters -- before using it for any decision.

**Why.** BioLORD vectors occupy a narrow cone: mean pairwise cosine over 100 random 1,639-pathway
subsets was 0.2734 with a standard deviation of 0.0009. Against that, the runaway node scored 0.2827
-- z = 10.8, and meaningless, since the node was 88% of the collection and could not have been
anything else. The statistic has almost no dynamic range because every pair starts out similar.
Centring removes the shared component and lets a real difference in tightness show.

**Not yet needed.** It was used once, to confirm the runaway node was not a genuine theme, and the
answer did not rest on it: no grouping within 20 of that size existed in the pool before the merge,
which settled it. The next use -- ranking nodes by quality, or gating the namer -- is the one that
needs the centred version first.

## Statistics engine: umbrella members dominate theme gene unions

*Logged 2026-09-22. **Open question, not a decision.** Nothing is implemented, and no rule is
adopted in the ontology.*

Theme gene unions are dominated by one member in **265 of 391 nodes**; in **93%** the dominant
member does not contain the others, it just outweighs them by size. Open: whether and how this
should affect theme-level statistics. To be discussed before the engine is designed. Candidate
directions noted, none chosen:

- report per-member contributions;
- a leave-largest-out test;
- a different theme gene set than the plain union.

### The measurement behind it

Taken on `data/ontology/v0.2/recurrent_dag_ward_t15_m33/` (ward, tol 0.15, m 0.33, 391 nodes).
A node counts as dominated when its largest member's gene set is more than half the union of all
its members' genes.

| | |
|---|---|
| nodes dominated | 265 of 391 (68%) |
| of those, dominant member IS effectively the whole union (share >= 0.99) | 9 |
| dominant member contains >= 90% of the other members' genes | 19 of 265 (7%) |
| dominant member merely outweighs the others | **246 of 265 (93%)** |
| dominant member's source | GO 204, Reactome 52, Hallmark 9 |

The 7% figure is the one that matters. The obvious explanation for a dominated union is GO's own
hierarchy -- a general term clustering with its specialisations, where the union equalling the
parent is correct arithmetic and not a defect. **That explains only 19 of 265.** In the rest the
large member sits beside the smaller ones without containing them: `n0271`, 7 members, union 237,
dominated 0.81 by "cellular response to starvation" (192 genes), which shares **0%** of its genes
with the other six.

### Why no threshold was adopted

A fixed gene-count cut was measured and rejected as insufficient rather than wrong:

| cut | pathways in build | nodes touched | dominated nodes it would address |
|---|---|---|---|
| 200 | 160 / 1854 | 184 / 391 | 158 / 265 (60%) |
| 300 | 112 / 1854 | 141 / 391 | 128 / 265 (48%) |
| 500 | 62 / 1854 | 95 / 391 | 88 / 265 (33%) |
| 1000 | 21 / 1854 | 32 / 391 | 31 / 265 (12%) |

No fixed count reaches most cases, because the effect is **relative** -- a member's size against
*its own theme's* union -- and a global threshold cannot express that. A relative criterion would
target it better, which is an observation about the shape of the problem, not a proposal.
