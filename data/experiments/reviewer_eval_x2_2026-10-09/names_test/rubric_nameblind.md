# Twin or distinct facet? (pair review, no cluster names)

Each item is a PAIR of overlapping, non-nested clusters of biological pathways (A and B). You see each cluster's size, a sample of pathways in both ("shared"), and samples of pathways only in A ("only_A") and only in B ("only_B"). The clusters have no names; judge from the pathways.

Judge as an experienced biologist whether A and B describe:
- "twin": the SAME biological theme. The only_A and only_B pathways belong to the same theme, so one merged cluster would lose nothing a biologist cares about.
- "facet": DIFFERENT aspects of related biology (e.g. different receptor families, different cell types, a different mechanism or tissue). Merging them would lose a distinction a biologist would want to keep.
- "unclear": you cannot tell.

Judge by biological theme, not by gene overlap. Give a one-sentence reason naming what distinguishes or unites only_A and only_B.
Read no other file. No web search.

Output: write ONLY valid JSON to the given path: a list of {"id","verdict","reason"}, with every input id exactly once.
