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
