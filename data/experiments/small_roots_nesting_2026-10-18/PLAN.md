# Small-root nesting diagnostic. Declared 18 Oct 2026, before running. Read-only; adopts nothing.

Question (Aviyah): for each of the 164 O50s roots of <=50 pathways, does it have a recurring parent group in the 200 Ward runs, how often, and does that parent appear in the O50s DAG; if it does, why is it not the parent.

Per small root s, per run r (x2 universe, persisted subsamples, full Ward dendrogram rebuilt from the centred vectors, as in prompt 44's stability step):
1. Own match: best Jaccard of s (restricted to the run's draw) to any dendrogram node.
2. Parent group: the first ancestor of that node with at least twice the size of s's best-match node.
3. Recurrence of the parent group: the medoid parent group (most other runs' parent groups at J >= 0.70 to it) and its frequency over 200 runs.
4. DAG check of the medoid parent group: best J to any O50s node; that node's share of s and pathways of s missing from it.
5. Nesting frequency for s's 5 largest-share O50s containers P: share of runs in which s's best-match node lies inside P's best-match node.
Reported as distributions over the 164 small roots, and a per-root table.
