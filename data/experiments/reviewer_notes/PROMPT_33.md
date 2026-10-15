Prompt 33: put the O50 ontology and its names on the landing page. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not touch frozen folders; working branch leaves-2026-10; times in UTC+1.

PRECONDITION
0. Prompt 32 has run: data/ontology/frozen/working-O50-2026-10-14/ exists, and its commit scripts are written. If not, stop and say so.

1. Read data/experiments/naming_O50_2026-10-14/sample/REPORT_S1_sample.md and select_lite/STATE.md. The names are "naming-c1-lite":
   - all 4,591 themes of 3-200 members are named;
   - 200 of them were selected with back-match, the rest as the medoid of the 3 candidates without back-match;
   - 15 are unnameable;
   - the uniqueness pass is done (dedup/REPORT_dedup.md): 0 duplicates.
   File: dedup/final_names_O50_lite_unique.tsv (theme_id, name, method, unnameable, duplicate_group). It supersedes select_lite/final_names_lite.tsv.
2. Extend scripts/export_landing.py, keeping every default and the current output byte-identical:
   - read the frozen O50 build (add flags; the current v<version>/<method> layout stays the default);
   - take names from a names TSV (new flag) instead of the keyword labels;
   - the 11 themes over 200 members, unnameable themes, and themes in a duplicate group keep provisional keyword labels and the amber chip;
   - record the names file and its sha256 in the manifest.
   Add tests.
3. Re-check both example cards (nfkb, insulin) on O50. If a card's assertions no longer hold, report which ones and why; do not loosen them.
4. Export to demo/preview-O50/ (ontology.js plus a copy of landing.html), never over demo/ontology.js. Rewrite the preview's mockup banner so every sentence is true for O50:
   - the build and its numbers come from the manifest;
   - names are naming-c1-lite, with the sample's 96.5% back-match and 0.924 member fit;
   - say which themes are still provisional.
   Report the file size and check that it opens from file:// at phone width.
5. Write docs/status/commit-2026-10-15-landing-O50.sh (commits the code, tests and the preview folder, plus data/experiments/reviewer_notes/PROMPT_32.md and PROMPT_33.md; no push of main).

Standing rule: never create, switch or delete branches outside a commit script, not even as a dry run; check with read-only commands instead.

END OF PROMPT. Confirm 0-5. Give:
- the manifest numbers;
- named / provisional counts;
- card status;
- preview size;
- the commit script path.
