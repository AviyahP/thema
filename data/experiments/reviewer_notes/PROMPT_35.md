Prompt 35: make the O50 landing preview shippable. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not touch frozen folders; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; times in UTC+1.

Aviyah's decisions on your prompt-33 report:
1. Payload: yes.
   - Emit each pathway once and reference it by id from the nodes. Change landing.html (and the preview copy) to read the new shape.
   - Layout, typography, colours and behaviour must stay as designed.
   - The page must still open from file:// (decision A1, no fetch).
   - Report the new size raw and gzipped, the parse time and the heap.
   - Keep the old exporter output available behind a flag, so the current published page can still be regenerated.
2. Example cards: search, do not choose.
   - Card 1 ("names that look unrelated"): candidate sets of 3-5 pathways in O50. Each set is from at least 2 databases, all pairwise gene kappa below 0.05 (or no shared gene), and all members share one theme of 50 members or fewer.
   - Card 2 ("the same observation counted twice"): candidate nested or heavily overlapping pathway pairs or triples in one theme, with the gene figures the current card states.
   - Rank by the smallest theme size and then by support.
   - Write the top 15 of each to docs/status/2026-10-15-card-candidates.md, with member names, sources, gene counts, kappa and the theme id and size. Aviyah picks. Change no card.
3. Fix the three pre-existing defects you found:
   - a deterministic tie-break in the exporter (output identical across runs without PYTHONHASHSEED);
   - the broken --method ward_tree default, or change the documented default to what actually generates the page;
   - the live page's unrecorded prompt_version: show nothing rather than a hardcoded value.
   Add tests.
4. Add the missing meta charset and viewport lines to demo/landing.html.
5. Re-export the preview with the deduplicated names (dedup/final_names_O50_lite_unique.tsv), plus a new optional --name-overrides flag that applies naming_O50_2026-10-14/name_overrides.tsv on top (hand-edited names, marked as edited by Aviyah in the manifest and on the page). Check it opens from file:// and that no element overflows at 360 px width, using a headless browser if one is available (Playwright or similar). If none is available, say so.
6. Write docs/status/commit-2026-10-15-landing-fixes.sh. The preview's ontology.js may be committed only if it is under 50 MB.

END OF PROMPT. Confirm 1-6. Give:
- the old and new sizes (raw / gzip), parse time and heap;
- card candidate counts;
- test counts;
- the browser check result;
- the commit script path.
