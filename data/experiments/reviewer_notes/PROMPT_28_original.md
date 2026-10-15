# Prompt 28 as given on 10 Oct 2026 (never executed; kept for the record)

Status 12 Oct: Parts A and B still stand and are carried out by prompt 31. Part C is obsolete (superseded by the
reviewer's twin/facet work, HANDOFF_2026-10-12.md sections 2-7).

---

Three parts: record, freeze, then measure twins (measurement only, no merging). No rebuild, no commit; leave a commit script. No external API calls. Do not touch data/ontology/frozen/baseline-2026-10-09/.

PART A - record (Aviyah, 2026-10-10)
1. Add to docs/status/2026-10-09-chain-c85.md a section "Corrected assessment (2026-10-10)" that copies data/experiments/reviewer_eval_x2_2026-10-09/REPORT_c85_reassessment.md verbatim. Leave the original pass / fail table unchanged. Add REPORT_c85_reassessment.md and judged_c85_316.json to the commit script.
2. DECISIONS entries:
   - Criteria (b) and (d) were mis-specified by the reviewer. Corrected post hoc, as definitions only: (d) withdrawn; a facet = a theme containing the pathway that is not merely a step up the same chain.
   - Corrected result: of the 805 removed baseline themes, 802 have a surviving counterpart at J >= 0.7 (750 at >= 0.85); 3 are borderline (J 0.68-0.69). No real facet is lost.
   - Plausibility: the reviewer judged the 316 unjudged themes (314 ok). All 8,251 themes: 97.64% vs 97.75%. The difference is composition (801 good duplicates removed; bad themes 197 -> 195). No re-evaluation is needed: 7,935 themes are identical to judged baseline themes and the other 316 are now judged.
   - DECISION: thema_L_x2_c85 (chain collapse 0.85, keep the higher-support node unless tied or the parent is top level; POST-HOC) is adopted as the WORKING VERSION. The 2026-10-09 baseline remains frozen as the fallback.
   - Known limit: 28% of collapse pairs are decided by a support margin under 0.05, so the surviving twin can differ between builds.

PART B - freeze the working version
3. Freeze thema_L_x2_c85 at data/ontology/frozen/working-c85-2026-10-10/ in the same way as the baseline:
   - the build files and the manifest;
   - the inputs (excluded_inputs.tsv, floors record, universe.json);
   - the verdicts: one all_verdicts_c85.json combining the 7,935 carried verdicts and judged_c85_316.json;
   - REPORT_c85_reassessment.md;
   - a FROZEN.md with every parameter and the difference from the baseline (the chain rule only);
   - CHECKSUMS.sha256.
   Extend the frozen-baseline test (or add one) so this folder is checksum-guarded too.
4. In the commit script, create an annotated tag "thema-c85-2026-10-10" on the freeze commit and push the branch and the tag.

PART C - side-by-side twins: MEASURE ONLY (no rule, no merge)
[obsolete; not reproduced]
