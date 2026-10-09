# Cluster plausibility review (round 2)

Each item is a cluster of biological pathways / gene sets (Reactome, GO Biological Process, MSigDB Hallmark, blood transcription modules "BTM"). "size" is the true number of members; for large clusters only a random sample of members is shown.

Some members are UNNAMED BTM modules. For those you are given a short description of the module (written from its genes) and its first genes. Judge them by that biology, exactly like a named pathway; do not treat "unnamed" as off-theme.

For EACH cluster decide, as an experienced biologist would:
- "coherent": the members clearly share one biological theme a biologist would recognise (process, mechanism, system, pathway family or cell type). A small minority of odd members is fine.
- "partial": a recognisable main theme, but roughly a quarter or more does not fit, or two related themes are mixed.
- "incoherent": no single plausible theme; a grab-bag.
For very large clusters (hundreds of members), "coherent" means one recognisable broad area (e.g. "immune system", "lipid metabolism"); a mix of unrelated areas is "incoherent".
Give a short theme label (max 8 words) and, if not coherent, one short reason.
Judge only from what is given and your biological knowledge. Read no other file. No web search.

Output: write ONLY valid JSON to the given output path: a list of {"id","verdict","label","reason"}, every input id exactly once.
