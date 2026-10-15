# Cluster plausibility review (O50 build; rubric4 categories)

Each item is a cluster of human biological pathways / gene sets (Reactome, GO Biological Process, MSigDB Hallmark, blood
transcription modules "BTM"). "size" is the true member count; clusters up to 200 members are shown in full, larger ones
as a random sample of 60 ("shown"). Unnamed BTM modules come with a short description: judge them by that biology.

For EACH cluster choose one verdict, as an experienced biologist would:
- "coherent": the members clearly share one recognisable biological theme. A small minority of odd members is fine.
- "umbrella": two or more sub-themes linked by a recognised, SPECIFIC biological connection (shared mechanism, molecule,
  cell type/tissue, physiological axis). Vague links ("both are signalling") do not count.
- "core_plus_misfits": one coherent theme plus roughly a quarter or more that does not belong.
- "mixture": sub-themes with no recognised specific link.
- "incoherent": no theme at all; a grab-bag.
Give a theme label (max 8 words) and a one-line reason.
Judge by biological theme, not by shared words. Read every member shown.

Output: ONLY valid JSON, a list of {"id","verdict","label","reason"} with every input id exactly once, in input order.
