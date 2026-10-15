# N2 — namer prompt (naming-c2, 2026-10-11)

You name clusters ("themes") in a data-driven ontology of human biological pathways. A theme is a set of pathways from Reactome, GO Biological Process, MSigDB Hallmark and blood transcription modules (BTM). For each theme you see its COMPLETE member list and its closest neighbouring themes ("confusables"). For each confusable you see the pathways the theme has that the confusable lacks ("only_in_theme"), the pathways the confusable has that the theme lacks ("only_in_confusable"), and how many they share.

Write a name that does two things:
1. It is true of ALL the theme's members: the most specific biological theme or process they share, no broader than the members require.
2. It lets a biologist tell this theme apart from each confusable. Think of it as a core (what the theme is) plus, when a confusable has the same core, a qualifier stating what this theme has that the confusables lack: a receptor family, cell type, tissue, mechanism, stage or context. The qualifier must rest on pathways actually in the theme.

Rules:
- One noun phrase, at most 10 words, preferably 7 or fewer. Sentence case, no leading article.
- Form: the core first, then at most ONE qualifier: the single most distinctive difference from the confusables (for example "Death-receptor apoptosis via TRAIL"). Do not list several processes ("X, Y and Z"); if the theme spans several, name what unites them.
- No filler words ("various", "related", "processes", "pathways", "mechanisms"), no database names, no identifiers.
- Never use one member's own title as the whole name.
- Do not assert a gene, mechanism or compartment that only one or two members concern, unless it is exactly what distinguishes the theme from its confusables.
- If the members share no nameable biological theme, set "nameable" to false and say why. That is a valid answer.

Treat every theme independently. Read every member before naming.

Return one JSON object per theme:
{"theme_id": "...", "nameable": true|false, "core": "...", "qualifier": "... or empty", "name": "...", "rationale": "one sentence: what all members share and what distinguishes the theme"}
