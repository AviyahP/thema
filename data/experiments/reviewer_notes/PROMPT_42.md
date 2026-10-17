Prompt 42: the clean two-level design. The first pass delivers themes up to T, and the areas pass builds everything above T. Declared 17 Oct 2026, before any result. Exploratory: this adopts nothing. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h. If prompt 41 is still running, finish it first.

WHY
Aviyah's design: one rule, no anchors, no special handling of giants.
- The first pass is trusted only up to size T.
- Every O50 theme larger than T is dropped.
- The areas pass builds everything above T from the themes of size T or less.
- The design is justified only if the areas rebuild the good big O50 themes (immune n01027, genome n01279, the metabolism giant n01420, the development giant n01845, and the others) and summary placement holds.

No existing build tests this: rec and rec3 fed the big themes in as units, and rec2fix kept them out together with their sub-themes.

SPEC (reuse rec2fix's code: equal weight, union sets, the seam rules as one structure, transitive reduction)
- **Arms:** T = 200 and T = 100. Add a third arm only if prompt 41 has finished and its measured T differs from both.
- **Items:** the O50 themes of size T or less that are not strictly inside another O50 theme of size T or less, plus any pathway in none of them. Report the count.
- **Dropped:** every O50 theme over T, giants included. These are kept for comparison only.
- **Areas pass:**
  - 200 runs on 80% subsamples, Ward with equal weight, recurrence 0.70 on item sets;
  - floors solved on 20 item scrambles (3001-3020), held out on 4002-4005, target 0.008, caps 0.02 per stratum and 0.01 overall;
  - consensus, then the joint fixed point (twin 0.50, chain 0.85) on pathway union sets;
  - one structure over items and areas, with strict containment.
- **No anchors.** Areas over 1,000 pathways are kept and flagged; nothing is dropped.

REPORT (docs/status/2026-10-17-clean-two-level.md), per arm
1. **Rebuild of the dropped themes:** for every dropped O50 theme, its best-matching area by J and that area's size. Count how many reach J ≥ 0.7 and how many reach 0.5-0.7.
2. **Noise check:** held-out FDR per stratum with counts, and whether a floor exists in every stratum.
3. **Shape:**
   - the number of areas and their sizes in bands;
   - the root count, and the roots with their sizes;
   - children per node, maximum and median;
   - areas over 1,000.
4. **Summary placement:** the pool is items plus areas. Give overall and by band, against O50's 85.3% (giants included) and O50 without giants (54.5%).
5. **Agreement with Reactome's top level:** median best Jaccard.
6. **Comparison with rec2fix:** for each area, its best J to the rec2fix areas.

The reviewer will then run the C6 intruder test and a giant reading on any areas over 1,000. Aviyah judges.

FINAL
- Copy this prompt verbatim into DECISIONS.md as "declared before running", before building.
- Output: data/ontology/v0.4-leaves/thema_L_x2_O50_clean/{T200,T100}/.
- Write docs/status/commit-2026-10-17-clean-two-level.sh, to run after the earlier scripts. It commits the code, tests, builds, status note and data/experiments/reviewer_notes/PROMPT_42.md. No branch operations; no push of main.

END OF PROMPT. Before building, give the item counts for each arm and the time estimate. After the build, give:
- the rebuild table (item 1);
- the FDR summary;
- roots, placement and Reactome agreement per arm;
- the commit script path.
