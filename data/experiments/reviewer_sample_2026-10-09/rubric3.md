# Re-judging "partial" clusters (round 3)

Each item is a cluster of biological pathways / gene sets (Reactome, GO BP, MSigDB Hallmark, blood transcription modules "BTM"; unnamed BTMs come with a description and first genes). "size" is the true member count; large clusters show a random sample of members.

These clusters were earlier judged "partial": a main theme plus misfits, or two related themes mixed. Re-judge each with this question in mind:
Is there a recognised biological link between the sub-themes, such as a shared mechanism, shared enzyme/cofactor/molecule, shared cell type or tissue, or a physiological axis that a biologist would accept?

Verdicts:
- "umbrella": the members form sub-themes that are linked by a recognised biological connection; the cluster is a sensible broader theme. Name the link concretely.
- "mixture": the sub-themes have no recognised link (or only a superficial word overlap); the grouping is not biologically meaningful as a whole.
- "core_plus_misfits": one coherent theme plus a minority of members that genuinely do not belong (list a few).
Give a theme label (max 8 words), the link (or "none"), and the fraction of members you consider misfits (rough, 0-1).
Be rigorous: a link must be specific (e.g. "platelet COX-1 makes thromboxane A2"), not vague ("both are signalling"). Judge only from what is given and your knowledge. Read no other file. No web search.

Output: write ONLY valid JSON to the given path: list of {"id","verdict","label","link","misfit_fraction","misfit_examples"}, every input id exactly once.
