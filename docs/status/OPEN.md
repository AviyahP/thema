# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-23, 14:45

---

## RUNNING (nothing needed from you)

| what | detail | ETA |
|---|---|---|
| tightness calibration | 31 sides, 4 concurrent, driver pid 96452. 1 done, 30 to go. Produces c*(3), c*(4), held-out FDR, 20 leave-one-out values, A7 overall. | ~2.5 h |

## WAITING ON YOU

| # | decision | why it matters | blocked? |
|---|---|---|---|
| 1 | run the 3 commits | work is done and tested, nothing committed | no |
| 2 | membership cutoff **0.25 or 0.50** | 0.25 wins on every structural measure; only test 8 (contested members) would settle it properly | blocks the freeze |
| 3 | approve **enrichment datasets** (validation plan test 5) | the test the tool exists for; protocol proposed, datasets not approved | blocks that test only |
| 4 | should `docs/status/OPEN.md` exist | this file — say if it is noise and I will delete it | no |

## NEEDED BEFORE ANY FREEZE, in order

1. **Rebuild** over the new universe (10,770). Every current build includes 4 now-excluded pathways.
2. **Recalibrate** thresholds on that rebuild.
3. **Regenerate demo artifacts** — `demo/ontology.json` and `demo/ontology.js` still say 10,817.
4. **Validation plan tests** — 9 written and pre-registered, **0 run**. Gates: 1, 3, 4, 5, 6, 7.

## DECIDED — do not reopen without saying so

- universe = pathways with >= 1 gene; 10,817 rows, **10,770 universe**
- v4 is the prompt; **name-prepending rejected** (circular gain, builds a syntax theme)
- the 13 refused pathways are **v4-alt, promoted**; `read()` = 10,770
- tightness cut is **solved from FDR <= 0.02**, not a chosen percentile
- 3-4 band: cohesion **replaces** recurrence; m stays at the floor 0.20
- 5-9 band: **no cohesion test** — recurrence alone meets the target
- error target **<= 0.01 overall, <= 0.02 per band**
- **mean gene overlap within themes REJECTED** as a quality metric
- ward linkage; tol 0.15

## PARKED

- 16 zero-gene refusals — out of universe, nothing to do
- 5% build `recurrent_dag_single_banded/` — uncommitted, superseded by the rebuild
- umbrella members dominating gene unions (`docs/debt.md`)
- small-set statistics, almost all Reactome (`docs/debt.md`)
- splitting `pathway_descriptions.tsv` at the third live generation (`docs/debt.md`)
