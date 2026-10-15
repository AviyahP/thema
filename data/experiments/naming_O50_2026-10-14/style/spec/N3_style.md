# N3: style rewrite prompt (naming style pilot, 15 Oct 2026)

You rewrite the name of a cluster ("theme") in a data-driven ontology of human biological pathways. A theme is a set of pathways from Reactome, GO Biological Process, MSigDB Hallmark and blood transcription modules (BTM).

For each theme you see:
- its COMPLETE member list;
- its current name and the three candidate names it was chosen from;
- its closest neighbouring themes ("confusables"). For each, the pathways the theme has that the confusable lacks ("only_in_theme"), the pathways the confusable has that the theme lacks ("only_in_confusable"), and how many they share.

Write the name in this form:

  HEAD (part, part, part)

**HEAD** names the one biological idea that unites the members: the system, process or purpose they serve together. It should be what a biologist would call this topic.
- At most 6 words, sentence case, no leading article.
- Not a list of the parts. At most one "and", and only if it joins two aspects of a single process (e.g. "Calcium-phosphate homeostasis and mineralization").

**Brackets** (optional) hold up to 3 short key parts or the distinguishing context: the components, receptor family, cell type, tissue or mechanism a biologist would want to see.
- Use them for whatever separates this theme from its confusables, if the head does not already do that.
- Leave them out if the head is enough.

Example: members on phosphate transporters and FGF23-Klotho, vitamin D activation and breakdown, vitamin K gamma-carboxylation and bone and tooth mineralization were named "Phosphate homeostasis, vitamin D/K metabolism and tissue mineralization". The rewrite is "Calcium-phosphate homeostasis and mineralization (vitamin D, phosphate, vitamin K)".

Rules:
- The name must stay true of all members and must still tell the theme apart from each confusable. Keep the distinguishing information of the current name; move it into the brackets if needed.
- Do not invent a unifying idea that the members do not support.
- If the members fall into two or more unrelated topics with no honest unifying idea, set "unifying" to false and give the most accurate name you can. That is a valid answer.
- No filler words ("various", "related", "processes", "pathways", "mechanisms"), no database names, no identifiers.
- Total length at most 14 words.

Treat every theme independently. Read every member before writing.

Return one JSON object per theme:
{"theme_id": "...", "head": "...", "parts": ["...", "..."], "name": "head (part, part)" or "head", "unifying": true|false, "rationale": "one sentence: the unifying idea and what distinguishes the theme"}
