# Decisions

A dated log of design decisions for THEMA — what we chose, and why. Append-only: newest entries
go at the bottom, and superseded decisions stay put with a note pointing at the entry that
replaced them.

Format: `## YYYY-MM-DD — <decision>`, followed by a short rationale.

## 2026-08-21 — Name: THEMA

THEMA = Thematic Hierarchical Enrichment Mapping & Analysis. Chosen because it
says what the tool does, is pronounceable, and is Greek for "theme."
Checked for collisions in bioinformatics, GitHub, and PyPI before adopting.
Rejected: THEMIS (collides with a T-cell gene — our users' own search space),
PANTHEON, CANOPY (weaker descriptions of the tool).

## 2026-08-21 — Project scaffold

- **Python 3.12** (`requires-python = ">=3.12"`) — broadest wheel coverage across the
  bioinformatics stack (numpy, scipy, pandas, statsmodels) while still allowing modern typing
  syntax.
- **uv + hatchling, src layout** — `src/thema/` keeps the installed package distinct from the
  repo root, so tests exercise the built package rather than accidentally importing from cwd.
- **ruff enforces the conventions** — the rule set includes `D` (docstrings, google convention)
  and `ANN` (type annotations) so "type hints everywhere, docstrings on public functions" is
  machine-checked rather than review-only. `tests/` is exempt from both.
- **`uv.lock` is committed** — THEMA is a tool, not a library dependency; reproducible resolution
  matters more than floating versions.

## 2026-08-21 — Architecture: frozen global ontology first (v1), per-experiment clustering later (v2)

The ontology (embed pathway descriptions → hierarchical clustering → LLM
naming) is built ONCE from database content only, touching no experiment
data, then version-frozen. Statistics run against the frozen release.
Rationale: themes defined before any experiment exists make theme-level
enrichment tests exactly as valid as standard ORA — the alternative
(clustering each experiment's significant pathways, then testing those
themes on the same data) is circular ("double dipping", Kriegeskorte et al.
2009, Nat Neurosci 12:535), and no p-value or FDR computed that way controls
anything. Per-experiment adaptive clustering is deferred to v2 as a
qualitative/exploratory feature. Full derivation and literature survey in
docs/brief.md (D2, D4).

## 2026-08-21 — Hierarchical reporting protocol (three tests)

1. BASIS — EVERY node in the tree is tested on all its genes (no
   significance-gated descent: a parent can be diluted below significance by
   cold siblings while a child is genuinely enriched — gating would prune
   real findings). One BH-FDR family across all basis tests. The basis layer
   is the INFERENCE: it decides which nodes are enriched. The tree is the
   REPORTING structure — results summarized top-down with minimal-node
   logic — never a testing gate.

2. CHILD-UNIQUE (attribution) — for every significant child: enrichment test
   + fold enrichment (with interval) on its unique genes (appearing in no
   sibling under the same parent). Contributing → distinct finding, report
   the child. Not contributing → the child's signal lives in shared genes →
   the PARENT is reported as the finding ("common biology"), the child shown
   as shared-driven detail. Construction: conditional re-test per
   fgsea::collapsePathways (Korotkevich et al., bioRxiv 060012) and SetRank
   (Simillion et al. 2017, BMC Bioinformatics 18:151) — never a difference
   of enrichment scores, which has no null distribution.

3. PARENT-BEYOND (attribution) — for every parent of significant children:
   enrichment test + effect size on genes appearing in non-significant
   children but in NO significant child. Contributing → the parent holds
   additional signal beyond its enriched children (e.g. branches too weak to
   clear alone) — report the parent as carrying "more." Construction:
   conditional hyperGTest, GOstats (Falcon & Gentleman 2007, Bioinformatics
   23:257).

Layer rules. Attribution (tests 2–3) decides LABELS, not discoveries — but
labels are still threshold decisions, so attribution p-values receive their
own BH correction across all test-2/test-3 values in a run: a separate
hypothesis family from the basis layer, each family its own unit of
interpretation. Stated caveat: the attribution family's membership is
selected by the basis results; the exact correction for testing within
data-selected families is Benjamini & Bogomolov 2014 (JRSS-B 76:297) — the
planned phase-2 upgrade. Every attribution test is accompanied by an effect
size (small gene sets are underpowered — the reason test 2 never gates a
child's significance, which test 1 decides on the full set). When distinct
children are reported and test 3 shows nothing, the parent appears as a
grouping line with no claim of its own.

## 2026-08-21 — FDR under dependence: BH default, BY switch, permutation audit

(PROVISIONAL — final decision deferred until implementation; revisit at Phase 4)

Honest status of BH on our tree: its guarantee holds under independence or
PRDS (Benjamini & Yekutieli 2001, Ann. Statist. 29:1165); PRDS is NOT proven
for nested overlapping set tests. BH on such families is field standard
(all GO tooling) and empirically robust under positive dependence, but not
theoretically guaranteed here. Policy:

- BH is the default (field-comparable, full power).
- BY available as a switch: guaranteed under ANY dependence, at ~ln(m)
  stringency cost (~7x for ~500 nodes). Kept for users who want a
  theorem-backed number; otherwise dominated by the audit below (worst-case
  insurance is for when measurement is impossible; ours is cheap).
- EMPIRICAL-FDR AUDIT: random gene lists of matched size run through the
  entire tree (~10^3 draws) give the exact joint null of all node statistics
  under the gene-sampling null, dependence included (cf. g:Profiler's
  g:SCS). Agreement with BH validates BH for this tree; disagreement ships
  as the honest number. GSEA tier: same audit by permuting rankings;
  vectorized cost is minutes (v1-stretch).

Known limits, disclosed: (a) calibration is exact under the COMPLETE
gene-sampling null; partial-null spillover (null nodes overlapping truly
enriched ones receive signal through shared genes) is a semantics question
of the competitive null, handled by the attribution layer, stated in the
README; (b) FDR is an average-case guarantee — under strong dependence the
realized false-discovery fraction spreads around it (Owen 2005); (c) Monte
Carlo resolution ~1/draws; (d) the urn-model/co-expression caveat of all
ORA is untouched by any of this (Goeman & Bühlmann 2007, Bioinformatics
23:980); background must be the measured universe (Wijesooriya et al. 2022,
PLoS Comput Biol 18:e1009935); DEG-cutoff dependence avoided by preferring
the ranked-list (GSEA) input tier.

DEFINITIVE CHECK (phase-2 evaluation suite, first item): planted-truth
simulation — synthetic DEG lists with chosen truly-enriched nodes through
the full pipeline; measure realized FDP vs claimed FDR and attribution
error rates, end to end.

## 2026-08-21 — Protocol authorship note

Protocol designed by Aviyah, 21 Aug 2026, converging over five iterations
from a leftover-test draft (topGO elim heritage: Alexa et al. 2006,
Bioinformatics 22:1600). Key simplifications and corrections along the way,
all hers: remove only child-SPECIFIC genes so co-significant siblings'
shared evidence survives; a separate "shared genes" test is unnecessary
(the shared-driven case is inferred from test-2 negatives); attribution
layers need their own multiple-testing correction despite being
descriptive; no significance-gated descent (dilution hides real children);
BH's dependence assumptions challenged → audit-by-permutation policy.
