# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-24

---

## RUNNING

**The 31-side rerun on the fast matcher**, into `conf_fast/`, 12 concurrent. Same embeddings, same
seeds, same sides. Every `.tsv` must come back byte-identical to the original E: that is the
end-to-end gate, and **nothing runs on 10,770 until it passes**.

## DONE — E, the confirmatory calibration

**986 themes, overall held-out FDR 0.0030 against a 0.01 cap, no stratum dropped.** Sizes 3 and 4
survive on recurrence alone at m = 0.94 / 0.90. Full table and the declared-m sensitivity in
`docs/status/2026-09-24-matching-performance.md`. Ran 2 h 05 min at four concurrent on the original
code. **Not freezable**: 12 of the 1,850 embeddings carry contaminated descriptions (below).

**Nothing is spending money.** The naming smoke test is finished — Sonnet, 50 themes, $0.34.

**Matching is now the sparse-product implementation** and is proven byte-identical on two sides.
**Families is NOT changed and still runs the old code** — profiled at 342 s, 35% of a side. Its
change and its own three proofs are proposed and not written.

## NEXT ACTION

0. **In this order, and the order matters.** The byte-identical proof of the fast code exists only
   while the inputs are unchanged, so the 31-side rerun on the *current* embeddings comes first.
   Then repair the descriptions; then snapshot and re-embed; then re-run E and compare the two.

0b. **Repair 66 corrupted descriptions.** No API cost — 30 truncate at a stray `</description>`
   tag (all 7 severe cases among them) and 36 need a trailing `</br>` or `</p>` stripped. Nothing
   needs regenerating. `go:GO:0010560` ends in a Nokia 5 phone review; 64 more
   carry trailing HTML, one a blog URL. All v4/opus-5, all `end_turn`. They fed the embeddings.
   The validator needs three rules — a length ceiling, a markup test, and stop-at-tag in the
   extractor. See `docs/status/2026-09-24-naming-smoke.md`.

1. ~~Re-run the naming smoke test.~~ **Done** -- Sonnet, 50 themes, $0.34. The first attempt **failed completely and produced nothing**:
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
| 5 | approve the 66-description repair (price first, as always) | blocks the freeze and the demo |
| 6 | **collapse single-child chains?** measured: 0 of 12 were genuine pass-throughs, so probably not | blocks nothing |

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
