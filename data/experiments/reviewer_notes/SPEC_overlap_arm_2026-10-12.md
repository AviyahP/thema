# Overlap arm: one same-theme cutoff inside the build (declared 12 Oct 2026, before any build or result)

Written by the reviewer for Aviyah. It runs on a BRANCH and replaces nothing until the criteria below are met and Aviyah
decides.

## Why

Today the build carries three cutoffs on the same measure, chosen at different times:
- consensus SUPERSEDED rule, non-nested overlap: J >= 0.70 (`v04.THETA_MERGE` -> `consensus.classify`);
- stale-merge pass after consensus: J >= 0.70 (`repair.MERGE_JACCARD`);
- chain collapse, nested: share >= 0.85 (c85; post-pass);
- and a proposed post-hoc sibling merge at J >= 0.6 & md <= 2, which is the consensus rule again at a lower cutoff
  (the highest sibling J in c85 is 0.697 because consensus already removes everything at 0.70).
The post-passes are order-dependent: merging siblings at J >= 0.5 after the build would create 839 new parent-child
near-chains that chain collapse would then absorb (REPORT_merge_J05.md). Aviyah's conclusion: put the overlap rule
inside the algorithm, with one cutoff for non-nested overlap and one for nesting, iterated to a fixed point.

## The arm (O50)

Start from the c85 configuration exactly (thema_L_x2_c85: arm L, x2 universe, cal8 floors, repair, collapse share 0.85,
survivor "support"). Change only:
1. **One same-theme cutoff T_same = 0.50** for non-nested pairs, used in BOTH places: consensus (`THETA_MERGE` as passed
   to `consensus`) and the stale-merge pass (`repair` jaccard). The survivor is what consensus already does: the lower
   support theme is superseded (dropped), not unioned. Nothing else in consensus changes (stray rule, inheritance,
   ordering).
2. **`theta_match` (recurrence for support and lifetime) stays 0.70.** It is a different quantity and must be a separate
   parameter; confirm in the status file which constants were split.
3. **Joint fixed point:** after consensus, repeat [chain collapse at 0.85, then stale merge at T_same] until neither
   changes anything; assert no non-nested pair >= T_same and no containment pair >= 0.85 remains.

Label-free basis of 0.50: J >= 0.5 is exactly "the shared part is at least as large as the two unique parts together".
Disclosure: the idea of lowering the cutoff was motivated after seeing LLM-judged evaluation results (whole-reading test);
the value is declared on the label-free basis and is not tuned. No LLM judgement enters construction.

## Controls and sensitivity

- **Harness proof:** T_same 0.70 without the joint loop must reproduce thema_L_x2_c85 byte-identically (all tables).
  The frozen baseline test must still pass. All defaults stay at today's values.
- **O70 (control):** c85 + joint fixed point at T_same 0.70. Isolates the effect of iterating from the effect of the
  cutoff (the c85 arm changed two things at once; do not repeat that).
- **O60 (report only):** T_same 0.60.
- **Reproducibility (report only):** O50 on the repair universe too, matched to O50-x2 at J >= 0.7, next to the same
  measure for c85. Removing duplicates lowers this by construction; it is reported, not a criterion.

## Criteria (O50 vs c85), declared now

| | criterion | who |
|---|---|---|
| C1 | no non-nested pair (both < 1,000 members) at J >= 0.50, and no containment pair at share >= 0.85 | ccode |
| C2 | no pathway loses all its themes under 1,000 members | ccode |
| C3 | >= 99% of c85 themes absent from O50 have an O50 theme at J >= 0.50 (counterpart) | ccode |
| C4 | plausibility: not-ok themes in O50 <= c85's 195 (verdicts carried for themes identical to judged ones; the rest judged with rubric4) | reviewer |
| C5 | usefulness, blind: see below; O50 must win | reviewer |

**C5 design.** 120 pathways drawn at random (seed 20261012) from those whose set of containing themes (under 200
members) differs between c85 and O50. For each, a judge sees the two sets of themes containing the pathway, each theme
as its full member list, no names, sides randomised, and answers: which set better helps a biologist interpret a hit on
this pathway, A, B or equal. O50 wins if it is preferred in >= 60% of decided items and a two-sided binomial test against
50% gives p < 0.05. Judges are in-session subagents (no API spend); the key is never shown to them.

**Decision rule.** O50 becomes the candidate working version only if C1-C4 pass and C5 is won. A tie on C5 keeps c85
(no change without evidence). Aviyah makes the final call; only then is the branch merged.

## Report only (ccode)

Theme counts by size band; roots; giants (> 1,000); depth distribution; share of themes with 2+ parents not nested in
each other and share reaching 2+ roots (the post-hoc simulation predicted about 38% and 47%, against 51% and 56% in c85);
survivor support margins (share under 0.05); what O70 changed relative to c85; O60 summary; run time and memory.
