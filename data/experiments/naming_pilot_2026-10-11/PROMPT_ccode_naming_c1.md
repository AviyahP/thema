Prompt 30: implement the naming-c1 algorithm as code, and prove it reproduces the reviewer's pilot (no spend before Aviyah approves)

Context: the reviewer ran a pre-registered naming pilot on 200 c85 themes. Everything is in
data/experiments/naming_pilot_2026-10-11/: spec/ALGORITHM.md (the algorithm), spec/N1_namer.md, spec/S1_backmatch.md
(prompt templates, use VERBATIM as system prompts; the per-item JSON shown in the pilot inputs is the user message),
code/np_*.py (the reviewer's exact input-building, selection and scoring code), PREREG.md, REPORT_naming_pilot.md.
Results: back-matching 91.5% vs 55.0% for the old labels, member fit 0.917, 0 duplicates; reproducibility at the
"equivalent" level 60% (bar 80%, failed; equivalent-or-nested 98%). A 5-candidate, single-qualifier variant
(naming-c2) was tested and rejected (back-matching 80%, reproducibility no better); A clean test with the original prompt and 5 candidates (naming-c1b) was no better than 3 candidates;
naming-c1 with 3 candidates is the adopted version.

1. Implement naming-c1 as src/thema/naming_c1.py plus scripts/name_themes_c1.py, following spec/ALGORITHM.md sections
   1-5 exactly: inputs built by code (port code/np_build.py: member rendering incl. untitled BTM descriptions, seeded
   shuffles, confusables by member-centroid cosine), 3 independent N1 calls per theme, one S1 back-match call per
   nameable candidate, deterministic selection (port code/np_select.py: medoid by token Jaccard among correct
   candidates, low_confidence flag, unnameable if >= 2 of 3 refuse), uniqueness re-ask (port code/np_dup.py).
   One API call per theme per candidate (no batching). Structured JSON output. Log every raw request and response.
   Model: the same model id as the pilot (claude-opus-5-5); record model id, temperature and prompt digests in a manifest.
   Do not reuse naming.py's prompts; name-v5 stays as it is.
2. Unit tests: input rendering and seeds reproduce the pilot's inputs/namer_slot*_b*.json item-for-item for the same
   theme and candidate index; selection reproduces selection/final_names.json from the pilot's raw outputs and judgements.
3. Do NOT call the API yet. Estimate the cost of the equivalence run (the first 100 themes of inputs/sample_and_confusables.json:
   3 N1 + up to 3 S1 calls each) from your spend ledger and the pricing you can verify, and stop for Aviyah's approval.
4. After approval: run it, write names to data/experiments/naming_pilot_2026-10-11/api_run/final_names_api.json with the
   same structure as the pilot's. The reviewer will evaluate them with fresh judges (ALGORITHM.md section 6).
5. Never open any KEY_DO_NOT_SHARE*.json. No API keys in files or logs. Leave docs/status/commit-2026-10-11-naming-c1.sh;
   do not commit.

END OF PROMPT check: list the files created, test results (pass/fail per test), the cost estimate with its basis,
and confirm that no API call was made.
