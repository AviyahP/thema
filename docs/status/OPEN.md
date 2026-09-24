# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-24

---

## RUNNING

**E — the confirmatory calibration**, pre-registered in `docs/spec/amendment-2026-09-24c.md`.
Real + 30 scrambles (20 calibration, 10 held-out) over the corrected **1,850** universe.

- **ONE arm, theta = 0.70.** It was launched with three arms (0.70 / 0.74 / 0.80) and killed at
  ~15 min. The sensitivity arms were exploration, and exploration is closed: theta is a *declared*
  parameter, so arms at other values can only invite re-choosing it after seeing the result. The
  one-arm run is also 3x cheaper — ~8.5 CPU hours against ~26.
- 4 concurrent, `nice -n 5`. Real side done: **prepare 18 s + match 353 s = 371 s, 15,630 rows.**
  Null sides are slower (~970 s) because a scramble produces far more groupings — **58,540** against
  the real side's fewer. Projected **~2 h 05 min wall**.
- **Pool persistence was added mid-run** (below). Sides 4–29 write their pool; `real` and sides 0–3
  were already in flight and do not, so `pool_topup.sh` waits for `ALLDONE` and recomputes just
  those five for their pools.

**Profiling one null side**, to decide whether the 10,770 run can be made shorter before it
launches. Through completion: prepare 17.1 s (Ward 16.9), **matching 616.6 s**, completion 3.5 s.
Families still to land. Matching is the target and it is not close.

**Nothing is spending money.** The naming smoke test is stopped — see below.

## NEXT ACTION

1. **Re-run the naming smoke test.** The first attempt **failed completely and produced nothing**:
   the per-model `LLMClient` in the two-model loop was constructed without `response_key`, so every
   call parsed against the default `"description"` key and failed. 100 theme-model pairs x 2
   attempts = **200 failed calls, roughly $2, zero usable output.** Fixed in
   `scripts/name_themes.py`; `data/keys/naming_blind*.md|tsv` and `data/theme_names.tsv` on disk are
   from the failed run and are overwritten on re-run. **Not committed.**
2. **Report E** when it lands — per stratum and overall, at `max(declared m = 0.33, floor)`.
3. **Decide on the inverted-index/matching optimisation** before the 10,770 run is launched.

## WAITING ON YOU

| # | decision | blocked? |
|---|---|---|
| 1 | run the commits in this checkpoint | no |
| 2 | membership cutoff **0.25 or 0.50** — 0.25 wins on every structural measure; test 8 would settle it | blocks the freeze |
| 3 | approve **enrichment datasets** (validation plan test 5) | blocks that test only |
| 4 | accept or refuse the **matching optimisation** (output-identical, must be proven on a side) | blocks the 10,770 runtime |
| 5 | re-run the naming smoke test at ~$2 | blocks the naming decision |

## NEEDED BEFORE ANY FREEZE, in order

1. **Rebuild** over the universe of 10,770. Every existing build except the v0.2 embeddings contains
   4 now-excluded pathways.
2. **Re-derive thresholds** on that rebuild — all current numbers are for a superseded universe.
3. **Regenerate demo artifacts** — `demo/ontology.json` and `demo/ontology.js` still say 10,817.
4. **Validation plan** — 9 tests written and pre-registered, **0 implemented, 0 run**. Gates: 1, 3,
   4, 5, 6, 7.

## DECIDED — do not reopen without saying so

- universe = pathways with >= 1 gene; 10,817 rows, **10,770 universe**
- v4 is the prompt; **name-prepending rejected**
- the 13 refused pathways are **v4-alt, promoted**; `read()` = 10,770
- **no size bands in the criteria.** One statistic (support), null conditioned on size
- **recurrence is the only gate. Cohesion is descriptive, never a gate** — Ward optimises tightness,
  so it is not independent evidence
- **matching is Jaccard >= theta**, uniform at every size; **theta = 0.70, declared not derived**
- declared **m = 0.33** at every size; per-size floor solved from the scramble at FDR <= 0.01;
  effective threshold = **max(declared m, floor)**
- **20 calibration + 10 held-out** scrambles at 1,850; **10 + 5** at 10,770 (count-based floor,
  ~6x more null families per stratum at that scale)
- a null gate based on a **maximum** is refused — proposed twice, rejected twice
- error target **q = 0.02**; ward linkage
- **analysis code may not filter the universe at read time** — `ontology/universe.py` raises instead,
  and `tests/ontology/test_universe.py` greps for any path that bypasses it

## PARKED (in `docs/debt.md`)

- support granularity: 100 runs → 101 values → tied p-values → BH/BY lose power
- small themes are 98% nested; the null may be too lenient for them
- umbrella members dominating gene unions
- small-set statistics, almost all Reactome
- splitting `pathway_descriptions.tsv` at the third live generation
- `recurrent_dag_single_banded/` — deliberately uncommitted, superseded by the rebuild

## ARTIFACTS BUILT ON THE SUPERSEDED UNIVERSE — DO NOT QUOTE

The universe rule (10,770) excludes 47 zero-gene pathways, **4 of which are in the 1,854 subset**:
`reactome:R-HSA-1222541`, `R-HSA-1660510`, `R-HSA-9679509`, `R-HSA-9727281`.

| artifact | keys | excluded present |
|---|---|---|
| `data/ontology/v0.2/embedding_keys.txt` + `embeddings.npy` | **1,850** | **0 — CORRECTED** |
| `data/ontology/embedding_keys.txt` + `embeddings.npy` | 1,854 | 4 |
| `data/ontology/clusters_ward.tsv` | 1,854 | 4 |
| `data/ontology/v0.2/ward_tree/` | 1,854 | 4 |
| `data/ontology/v0.2/recurrent_dag_ward_t15_m33/` | 1,706 | 4 |
| `data/ontology/v0.2/recurrent_dag_single_banded/` | 1,854 | 4 |

The corrected v0.2 artifact is recorded in `data/ontology/v0.2/universe.json` (digest
`c54319cdfbbe9eb7`), which names the 4 dropped keys and the superseded file it replaced. The
superseded vectors and key list are kept on disk beside it and are **git-ignored**, like every
derived artifact.

Also superseded, because they were computed from the 1,854 vectors: the **31-side tightness
calibration** and the **theta sweep** (`docs/status/2026-09-24-runs-performed.md`). Both test methods
rather than produce final values, so their conclusions stand; their numbers do not.

**`data/ontology/v0.1/` is EXEMPT** — the frozen v3-era reference. Its contents are history, not a
current claim, and it must not be filtered.

## KNOWN CONSTRAINTS ON RE-ANALYSIS

**Being fixed, from side 4 of E onward.** Each side now writes `conf/pool_<tag>.npz`: every
grouping's member set and support after matching, every completed set, and every family's seed and
support — the matched pool, which is the ~10-minute object. With the rule locked, E's 30 scrambles
become the permanent null for the 1,850 universe and any later question about `m`, about a size
stratum, or about cohesion reads from disk instead of re-running a side.

Sets are stored CSR (`indptr` + `uint16` indices), not dense bitsets, and the conversion was checked
against `bitset.unpack` at widths 7, 64, 65, 1850 and 10770 before it went in. What is **not**
persisted is `Pool.copies` — the per-run matched cluster for every grouping, which is ~600 MB a side
uncompressed. It is only needed to change `theta` or the 0.25 inclusion cutoff, and both are
declared. Changing either still costs a full re-run.
