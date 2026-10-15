# Naming style pilot (reviewer pre-registration, 15 Oct 2026, written before any rewrite exists)

**Question (Aviyah):** can names take the form "unifying idea (key parts)", e.g. "Calcium-phosphate homeostasis and mineralization (vitamin D, phosphate, vitamin K)", without losing accuracy or distinctiveness? On the 11 Oct pilot, a style line cut back-matching from 90% to 80%.

**Sample:** the same 200 O50 themes as the S1 sample check (seed 20261015).
- OLD = their current final name in dedup/final_names_O50_lite_unique.tsv.
- NEW = one rewrite per theme with spec/N3_style.md.
- Rewriters see the members, the old name and its 3 candidates, and the 4 confusables (for the 7 themes renamed in the uniqueness pass, the post-dedup confusables).
- Member order is shuffled with seed sha256(theme_id + ":40").

**Evaluation:** fresh judges, never used before. OLD and NEW are judged together, so each judge sees a mix and never knows which is which.
- **E1 back-match:** spec S1_backmatch.md, clusters shuffled with seed sha256(theme_id + ":E" + arm).
- **E2 member fit:** spec E2_fit.md; fit = 1 - misfits / size.
- **P1 pairwise preference:** spec P1_preference.md; OLD and NEW as A/B in random order (seed 20261016).
- **H1 human:** Aviyah rates 30 random pairs blind (seed 20261017), A/B/equal. Done later, when she has time.

**Outcomes:**
- D1 = E1(NEW) - E1(OLD), paired by theme, bootstrap 95% CI.
- D2 = E2(NEW) - E2(OLD).
- P = NEW's share of the decided P1 pairs, with a two-sided binomial test.
- U = the share of themes the rewriter marks "unifying = false".
- Also reported: median words, and the share of list-style heads (a comma or 2+ "and" in the head).

**Declared reading:**
- **STYLE PASSES** if D1's CI lower bound is at least -3 points, E2(NEW) >= 0.90 and D2 >= -0.02, and P > 50% with p < 0.05.
- The final adoption also needs H1: NEW preferred in the majority of Aviyah's decided pairs.
- **STYLE FAILS** if D1's point estimate is below -3 or E2(NEW) < 0.90.
- Otherwise MIXED.
- No full-scale restyle is run on this result; Aviyah decides.
