# O50 lite names: uniqueness pass (reviewer, 15 Oct 2026)

ALGORITHM.md section 5, applied to the naming-c1-lite selection (select_lite/). The re-asked candidates were selected without a back-match, as medoids, consistent with the lite choice.

- **Input:** 75 duplicate groups, 154 themes, from select_lite/final_names_lite.json.
- **Round 1:**
  - N1 was re-run for all 154 themes, 3 candidates each, seeds `theme_id:ci+20`.
  - The colliding themes were put first among the confusables, and the uniqueness note was attached to each item.
  - 21 files, all validated. No theme became unnameable.
  - One new collision remained: n00337 was renamed into the existing name of n00666.
- **Round 2:**
  - Both themes re-asked, seeds `ci+30`, each other as a confusable.
  - **0 duplicates remain.**
- **Final file: `final_names_O50_lite_unique.tsv`** (theme_id, name, method, unnameable, duplicate_group).
  - 4,591 themes; 15 unnameable; 0 duplicates.
  - methods: medoid_no_s1 4,228; s1_sample 193; medoid_no_s1+dedup1 146; s1_sample+dedup1 7; medoid_no_s1+dedup2 2.
- **Examples:** n02404 / n03053 were both "Adenylate cyclase-cAMP-PKA signaling to CREB". They are now:
  - n02404: "Stimulatory adenylate cyclase-PKA-CREB arm without cAMP turnover";
  - n03053: "cAMP turnover and PKA-CREB signaling with PDE1/DARPP-32 feedback".
- **Caveats:**
  - Set operations use rendered titles as multisets (as in the sample check).
  - The re-asked names were not back-matched or fit-checked.
- **Cost:** 24 namer files, about 2.3M subagent tokens.

Files: dd_build.py, dd_select.py, dd_build2.py, dd_select2.py, inputs/, raw/, final_names_dedup1.*, final_names_O50_lite_unique.*.
