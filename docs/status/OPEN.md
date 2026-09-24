# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-24

---

## RUNNING

Nothing.

## NEXT ACTION

**The matching-rule sweep**, pre-registered in `docs/spec/amendment-2026-09-24.md` §6 and not yet
run. Real + 5 scrambles, five arms off one `prepare` per side: Jaccard theta **0.70 (primary)**,
0.74, 0.77, 0.80, and the current `floor(0.15 s)` rule as reference. Reports, for sizes 3 and 4,
whether real and scrambled support distributions separate, and per-theme empirical null p-values.
**Estimated 75–85 min**; actual per-side times to be reported against the estimate.

## WAITING ON YOU

| # | decision | blocked? |
|---|---|---|
| 1 | run the commits below | no |
| 2 | membership cutoff **0.25 or 0.50** — 0.25 wins on every structural measure; test 8 would settle it properly | blocks the freeze |
| 3 | approve **enrichment datasets** (validation plan test 5) | blocks that test only |
| 4 | say go on the sweep | blocks the 3–4 question |

## NEEDED BEFORE ANY FREEZE, in order

1. **Rebuild** over the universe of 10,770. Every existing build contains 4 now-excluded pathways.
2. **Re-derive thresholds** on that rebuild — all current numbers are for a superseded universe.
3. **Regenerate demo artifacts** — `demo/ontology.json` and `demo/ontology.js` still say 10,817.
4. **Validation plan** — 9 tests written and pre-registered, **0 implemented, 0 run**. Gates: 1, 3,
   4, 5, 6, 7.

## DECIDED — do not reopen without saying so

- universe = pathways with ≥ 1 gene; 10,817 rows, **10,770 universe**
- v4 is the prompt; **name-prepending rejected**
- the 13 refused pathways are **v4-alt, promoted**; `read()` = 10,770
- **no size bands in the criteria.** One statistic (support), empirical null conditioned on size,
  one correction at q = 0.02, BH and BY both reported with actual cost
- **cohesion is a descriptor, not a gate** — Ward optimises tightness, so it is not independent
  evidence
- **matching becomes Jaccard ≥ theta**, uniform at every size; **theta = 0.70 primary, declared not
  derived**; size-3 result is conditional on theta ≤ 0.75
- a null gate based on a **maximum** is refused — proposed twice, rejected twice
- **the 3–4 band stays dropped** until Aviyah says otherwise
- error target **q = 0.02**
- ward linkage; tol 0.15 (until the sweep replaces it)

## PARKED (in `docs/debt.md`)

- support granularity: 100 runs → 101 values → tied p-values → BH/BY lose power
- small themes are 98% nested; the null may be too lenient for them; scrambled side unmeasured
- umbrella members dominating gene unions
- small-set statistics, almost all Reactome
- splitting `pathway_descriptions.tsv` at the third live generation
- `recurrent_dag_single_banded/` — uncommitted, superseded by the rebuild

## KNOWN CONSTRAINTS ON RE-ANALYSIS

`Prepared` objects and scrambled member sets were **not persisted**
(`docs/status/2026-09-24-runs-performed.md` §5). Any change to `tol` or the matching rule requires
re-running every side (~1,240 s each), and no subset analysis on the null is possible without it.
