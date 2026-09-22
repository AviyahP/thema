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
