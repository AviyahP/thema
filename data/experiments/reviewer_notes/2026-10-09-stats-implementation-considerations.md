# Statistics layer: possibilities to consider when implementing (reviewer, 9 Oct 2026)

**Status:** suggestions, NOT decisions. Decide them, and declare each before seeing results, when the statistics layer is implemented on the multi-facet DAG.

**The existing plan stays authoritative:** thema-master-spec.md (input ladder, analysis engine), thema-brief.md section 5 (BASIS / CHILD-UNIQUE / PARENT-BEYOND, BH / BY, empirical-FDR audit, planted truth), thema-soft-membership-plan.md (one attribution test per child-parent edge), and the paper's stats section. This note only adds what the multi-facet DAG of Oct 2026 raises.

## 1. Adapting the plan to the new DAG

- **A larger family of tests.** The plan was written for about 30-50 themes. The baseline has 8,740 themes and many more child-parent edges, so the BH family is far larger and power drops.
- **Options:**
  - **(a) A declared testing resolution.** For example: test only themes with support ≥ s, and/or within a size range; never test the giant bag roots.
  - **(b) DAG-structured multiple testing.** Test top-down, descending only below rejected nodes. Candidates to read:
    - Goeman & Mansmann 2008, the focus-level method for GO;
    - Meijer & Goeman 2015, multiple testing on a directed acyclic graph;
    - Ramdas et al. 2019 (DAGGER), sequential FDR control on DAGs;
    - Benjamini & Bogomolov 2014, selective inference on families, already named in the brief for attribution.

    Check the exact references when implementing.
  - **(c) Both:** a declared resolution plus structured testing within it.
- **Giant bag roots:** exclude them from testing, or report them as non-thematic containers. Their gene unions cover a large share of the genome, so "enrichment" there is meaningless.

## 2. Using support

- **Option: weighted BH** (Genovese, Roeder & Wasserman 2006), using theme support as the prior weight (weights averaging 1, declared before results). More reproducible themes get more power.
- **Simpler option:** use support only as a filter (the resolution in 1a) and always report support beside each result.
- **Reporting:** flag themes with low support as less reproducible. Evidence: 89-91% of themes with support ≥ 0.1 reproduce in an independent build; below that, churn is high.

## 3. Facet attribution in fans

- **What the plan already gives:** PARENT-BEYOND per (child, parent) edge is the gene set a facet adds beyond the shared core. Example: the 6 platelet parents give 6 tests.
- **Possible addition, facet-distinctive genes:** for each co-parent, the genes in that facet and in no other co-parent of the same child. This answers "which facet is distinctive", not just "which adds beyond the core".
- **Power:** facet-unique gene sets can be tiny. Declare a minimum size, and below it report "not attributable" rather than a weak p-value.
- **Effect sizes are mandatory** beside every attribution test, as in the brief.

## 4. Multi-membership in the descriptive layer (rung 0, table only)

- A hit pathway with several parents counts in each facet. Show it as shared, not as independent evidence.
- Report per facet: hits, of which shared with co-facets, and independent signals (the brief's de-nesting count).

## 5. Known placement limits to surface in outputs

- **Loners:** about 8 pathways (e.g. NOTCH2NL) whose stable placement is not their functional one. Flag them in results so a user does not over-read their themes.
- **Excluded inputs** (data/excluded_inputs.tsv): list them when a user's table contains them, rather than silently dropping them.

## 6. Validation of the statistics layer

- **Planted truth on the actual frozen DAG**, including signal planted in ONE facet only. Check that attribution picks that facet and not its siblings or the core.
- **Public datasets with known biology** (for example a platelet-activation dataset, or an interferon response). Compare THEMA's summary and attribution with GO slim and Reactome top levels.
- **A blinded human-biologist check** of 100-200 themes, reporting agreement next to the AI judges' 98.9%.

## 7. Versioning

- Every result carries the frozen ontology version (e.g. the baseline-2026-10-09 tag).
- Tests are valid only against the frozen version they were run on.
