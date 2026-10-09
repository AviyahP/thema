<!-- Recorded by ccode on 2026-10-09. Verbatim copy of
     data/experiments/reviewer_eval_x2_2026-10-09/REPORT_x2.md. Nothing appended. -->

> **EXPLORATORY — recorded by ccode, not produced or reproduced by it.** The reviewer's step-3
> evaluation of `thema_L_x2`, copied verbatim. LLM-judge assessments made with Aviyah outside ccode,
> using Claude Code subagents: not a declared test, not run under the protocol, not reproduced here.
>
> Raw material in `data/experiments/reviewer_eval_x2_2026-10-09/`: `to_judge.json`,
> `carried_verdicts.json`, `judged_new.json`, `all_verdicts_x2.json`, `rubric4_x2.md`.
>
> The build it judges is `data/ontology/v0.4-leaves/thema_L_x2`, whose construction and comparison
> with `thema_L_repair` are in `docs/status/2026-10-09-exclusion2-rebuild.md`. The 1,310 carried
> verdicts are the themes that compare **identical** in that report's mapping table.

---

# Plausibility evaluation of thema_L_x2 (step 3 of the agreed plan, 2026-10-09)

**Build:** `data/ontology/v0.4-leaves/thema_L_x2`. Universe L minus all exclusions: 5,559 → 5,539 sets, 8,740 themes. Algorithm and cal8 floors are the same as thema_L_repair.

**Exclusions applied:** 23 of the 10,770 sets (exclusion 1: 17; exclusion 2: 6 new); 20 of them were in L.
- Reviewer note: GO:0010800 ("positive regulation of peptidyl-threonine phosphorylation", in L) has a specific name. Under the declared rule ("neither name nor description identifies a theme") it should not have been excluded. It should be reinstated.
- Reviewer note: btm:M248, the example given in the rule, was judged "yes" by the blind judges and stays in. The rule decides, not the example.

## Method

- **Carried verdicts:** 1,310 themes whose member set is identical to a judged thema_L_repair theme keep that verdict.
- **Newly judged:** the other 7,430 themes (rubric4_x2.md), using 53 subagents.
  - Same rubric as before, plus one line: judge by shared biological theme, not by gene overlap.
  - Members shown: up to 15 (sizes 3-50), 25 (51-100) or 40 (over 100).

Files in `data/experiments/reviewer_eval_x2_2026-10-09/`: to_judge.json, carried_verdicts.json, judged_new.json, all_verdicts_x2.json.

## Results (all 8,740 themes)

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 524 | 513 | 3 | 4 | 2 | 2 | 98.5% |
| 6-10 | 2100 | 1948 | 108 | 31 | 10 | 3 | 97.9% |
| 11-20 | 4287 | 3807 | 382 | 67 | 28 | 3 | 97.7% |
| 21-50 | 1550 | 1341 | 179 | 24 | 6 | 0 | 98.1% |
| 51-100 | 229 | 185 | 41 | 1 | 2 | 0 | 98.7% |
| 101-300 | 34 | 25 | 9 | 0 | 0 | 0 | 100% |
| 301-1000 | 6 | 0 | 2 | 1 | 2 | 1 | 33% |
| 1000+ | 10 | 0 | 0 | 0 | 1 | 9 | 0% |
| **all** | **8740** | **7819** | **724** | **128** | **51** | **18** | **97.7%** |

**Compared with thema_L_repair:** 97.4% → 97.7% ok, and incoherent 44 → 18.

**Small incoherent clusters: 39 → 8.**
- The 22-cluster family of unnamed housekeeping modules is gone.
- The 8 that remain:
  - drug / ethanol / anesthetic response sets: n03778, n06006, n07868. The judges still call these incoherent; on 9 Oct Aviyah and the reviewer judged them a thematic umbrella;
  - magnesium / creatine / oligomerization orphan terms: n08351, n03096;
  - motif-defined BTMs: n02615 (category B, accepted by Aviyah);
  - a 5-member leftover-BTM cluster: n01292 (support 0.695);
  - the 3-member phosphoinositide receptor cluster: n00637 (reviewer: an umbrella).

**The top got worse.**
- Every theme over 1,000 members is bad: 10 roots (1,187-2,673 members), 9 incoherent and 1 mixture. thema_L_repair had 9 roots, 2 of them coherent.
- Between 301 and 1,000 members, 4 of the 6 are bad: n07399 (927, incoherent), n01281 (789, mixture), n06571 (301, mixture), plus 1 core + misfits.
- **The middle (up to 300 members) is 97.7-100% ok in every band.**

**Mixtures of 20 or more members (excluding the roots):**
- Wnt + Notch + Hedgehog (83);
- Wnt + Notch (57);
- eye + placenta (34);
- phosphate transport + biomineralization + pH (29);
- tRNA / translation + protein methylation (29);
- MET + TGF-beta (28);
- kynurenine-NAD + polyamines (22);
- surfactant + Rh transport (21);
- Ig diversification + PD-L1 (20);
- protein lipidation + lipid transfer (20);
- pancreatic lineage + urogenital glands (20).

The developmental-signalling pairs are strict calls (see the main report).

## Judge consistency (a free check)

For the 5,465 newly judged themes that match a thema_L_repair theme at Jaccard ≥ 0.7, the two independent judgements agree on ok vs not-ok in 5,405 cases (98.9%). 36 went ok → not, and 24 went not → ok. So the judging noise is about 1%.

## Plausibility by match class

| class | n | ok |
|---|---|---|
| identical | 1,310 | 98.4% |
| matched at J ≥ 0.7 | 5,465 | 98.3% |
| new (no match at 0.7) | 1,965 | 95.7% |

The new themes are mostly low-support (median 0.045) and slightly less plausible.

## Stability (from ccode's comparison, reviewer's breakdown)

- 22.5% of themes have no counterpart at J ≥ 0.7. This churn is concentrated in low-support themes: new themes have median support 0.045, against 0.685 for identical ones.
- Among themes with support ≥ 0.1, 89% match; at support ≥ 0.5, 91%.
- The changed universe changes every subsample, so this is effectively a comparison of two independent builds.

## For the step-4 discussion

1. The middle levels are in good shape. The remaining problem is the top: 10 incoherent roots plus 3-4 large bags of 300-1,000 members.
2. Chain survivor and threshold: the measurements are in the main report, section 14.
3. Reinstate GO:0010800 (a rule misapplication), at the next rebuild.
