# Cluster plausibility review (second sample)

Each item is a cluster of biological pathways / gene sets (Reactome, GO Biological Process, MSigDB Hallmark, blood transcription modules "BTM"). "size" is the true member count; larger clusters show a random sample of up to 15-25 members. Unnamed BTM modules come with a short description (written from their genes) and their first genes: judge them by that biology, like a named pathway.

For EACH cluster choose one verdict, as an experienced biologist would:
- "coherent": the members clearly share one recognisable biological theme (process, mechanism, system, pathway family, cell type). A small minority of odd members is fine.
- "umbrella": two or more sub-themes that are linked by a recognised, SPECIFIC biological connection (shared mechanism, enzyme/cofactor/molecule, cell type/tissue, or physiological axis), e.g. "platelet COX-1 makes thromboxane A2" linking hemostasis and eicosanoids. Vague links ("both are signalling") do not count.
- "core_plus_misfits": one coherent theme plus a substantial minority (roughly a quarter or more) that does not belong.
- "mixture": sub-themes with no recognised specific link.
- "incoherent": no theme at all; a grab-bag.
Give a theme label (max 8 words); for umbrella the specific link; for core_plus_misfits / mixture / incoherent a short reason and a rough misfit fraction (0-1).
Judge only from what is given and your knowledge. Read no other file. No web search.

Output: write ONLY valid JSON to the given path: list of {"id","verdict","label","link","reason","misfit_fraction"}, every input id exactly once.
