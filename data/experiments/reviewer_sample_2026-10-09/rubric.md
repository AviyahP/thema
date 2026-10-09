# Cluster plausibility review

Each item is a cluster of biological pathways / gene sets (names from Reactome, GO Biological Process, MSigDB Hallmark and blood transcription modules "BTM"). For large clusters only a random sample of up to 15 member names is shown; "size" is the true number of members.

For EACH cluster decide, as an experienced biologist would:
- "coherent": the members clearly share one biological theme a biologist would recognise (a process, mechanism, system or pathway family). Minor odd members are fine if they are a small minority.
- "partial": a recognisable main theme, but a substantial minority (roughly a quarter or more) does not fit, or the cluster mixes two related themes.
- "incoherent": no single plausible theme; a grab-bag.
Also give a short theme label (max 8 words) and, if not coherent, one short reason.
Judge only from the names and your biological knowledge. Do not read any other file. No web search.

Output: write ONLY valid JSON to the given output path: a list of {"id": ..., "verdict": "coherent"|"partial"|"incoherent", "label": "...", "reason": "..."} with every input id exactly once.
