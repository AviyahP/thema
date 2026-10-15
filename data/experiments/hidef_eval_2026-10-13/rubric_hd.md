# Cluster coherence and nameability

Each item is a cluster of human biological pathways / gene sets (Reactome, GO Biological Process, MSigDB Hallmark, blood
transcription modules "BTM"), shown with its COMPLETE member list. Unnamed BTM modules come with a short description: judge
them by that biology.

For EACH cluster, as an experienced biologist:
1. verdict:
- "coherent": the members clearly share one recognisable biological theme. A small minority of odd members is fine.
- "umbrella": two or more sub-themes linked by a recognised, SPECIFIC biological connection (shared mechanism, molecule,
  cell type/tissue, physiological axis). Vague links ("both are signalling") do not count.
- "core_plus_misfits": one coherent theme plus roughly a quarter or more that does not belong.
- "mixture": sub-themes with no recognised specific link.
- "incoherent": no theme at all.
2. name: the most specific name (max 10 words) that fits the whole cluster.
3. nameability:
- "easy": one specific name fits all or nearly all members;
- "broad": only a general name fits (e.g. "immune signalling");
- "hard": no single name fits.
Judge by biological theme, not by shared words. Read every member.

Output: ONLY valid JSON, a list of {"id","verdict","name","nameability","reason"} with every input id exactly once,
in input order.
