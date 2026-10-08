# direction-v1 — instructions for writing direction fields (blinded)

You receive biological process descriptions, one per line, as JSON {"id": ..., "description": ...}.
The process name and source database are deliberately hidden. Work ONLY from the description text and your general biological understanding.

For each description, output one JSON line:
{"id": "<same id>", "broader": "<phrase>", "narrower": ["<phrase>", ...]}

- "broader": ONE short phrase (at most 8 words) naming the more general biological process that the described process is a part of or a kind of. Use "none" only if the description is already a top-level process (e.g., metabolism as a whole).
- "narrower": UP TO 5 short phrases (each at most 8 words) naming more specific processes that occur within, or are kinds of, the described process. Fewer is fine; use [] if the description is already very specific.
- Plain biological language. Do NOT write database names (Reactome, GO, Gene Ontology, MSigDB, Hallmark, KEGG, BTM), identifiers (R-HSA-..., GO:...), or gene-set codes.
- Do not copy the description's opening words as the broader phrase; name the more general process.
- Do not look anything up: no web, no files other than your assigned batch.
