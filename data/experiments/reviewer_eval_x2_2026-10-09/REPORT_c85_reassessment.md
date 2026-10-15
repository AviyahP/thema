# Chain collapse c85: reviewer re-assessment with corrected criteria (10 Oct 2026)

Builds: frozen baseline (8,740 themes) vs data/ontology/v0.4-leaves/thema_L_x2_c85 (8,251 themes; threshold 0.85, keep the higher-support node unless tied or the parent is top level).
ccode's original pass / fail table (docs/status/2026-10-09-chain-c85.md) stands as declared. This is the corrected assessment Aviyah asked for. The definitions are corrected post hoc; the rule is unchanged.

## Corrected definitions (Aviyah, 10 Oct)

- **Reproducibility:** withdrawn as irrelevant to this rule (removing near-duplicates lowers a "share matched" measure by construction).
- **Facet:** a cluster a pathway is in that is not merely a step up the same chain. It is measured as the number of mutually non-nested themes (under 1,000 members) that contain the pathway.

## 1. Facets: no real facet is lost

- **The facet count per pathway** (max antichain of its themes): baseline mean 9.63, median 9; c85 mean 9.34, median 9. 3,822 pathways unchanged, 1,504 lower (mostly by 1), 213 higher.
- **But the count is inflated by near-duplicate variants of the same theme.** Example: "regulation of hematopoietic stem cell proliferation" sits in 9 overlapping hematopoiesis themes with near-identical labels.
- **Every removed theme was checked for a surviving counterpart.** Of the 805 baseline themes absent from c85:
  - 750 have a surviving theme at Jaccard ≥ 0.85;
  - 52 at 0.70-0.85;
  - 3 at 0.68-0.69: n05820 mitochondrial FA and BCAA catabolism (40), n05176 type I interferon antiviral response (65), n05887 Rho GTPase cycles (23).
- **Examples:** a pathway "losing" 2 facets lost, e.g., "Endothelial differentiation and VEGF vascular development" (n=22) while "…" (n=20, J 0.91) survives. Every case inspected was a near-twin of a surviving theme with the same label.
- **Conclusion:** under the corrected definition, no real facet is lost. At most 3 borderline themes (J 0.68-0.69) are near the edge.

## 2. Plausibility: no cluster got worse; the drop is composition

- **ccode's 97.6%** excluded the 316 surviving themes that are not in the baseline (unjudged). The reviewer judged all 316 with rubric4 (judged_c85_316.json): 283 coherent, 31 umbrella, 2 core + misfits, so **314/316 ok (99.4%)**.
- **All 8,251 themes:** 8,056 ok = **97.64%**, against the baseline's 8,543 / 8,740 = 97.75%.
- **Why it is lower:** the rule removed 805 themes, 801 of them ok (near-duplicates of good themes), and added 316 good ones. The bad themes stay: 197 in the baseline, 195 in c85.
- **Conclusion:** the share dips only because good duplicates were removed. No theme got worse, and there are 2 fewer bad themes.

## 3. Levels

4,646 pathways lose a median of 2 levels. The removed levels are near-duplicate rungs (section 1), so what is lost is staircase steps, not facets. This is the intended effect.

## 4. What it does not do

- **Giants:** the 10 roots over 1,000 members are unchanged.
- **Twin redundancy is still present:** pathways sit in a median of 9 mutually non-nested themes, many of them overlapping same-theme variants (sibling near-twins, not chains). Chain collapse cannot remove these.
- **Stability of the survivor choice:** ccode notes that 28% of pairs are decided by a support margin under 0.05, so which twin survives can differ between builds.

## Reviewer's reading

By the corrected criteria the c85 rule does what it was meant to do:
- (a) the staircase is removed;
- no real facet is lost;
- no pathway is orphaned;
- the clusters are no less plausible.

**Decision pending (Aviyah).**
