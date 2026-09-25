# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-24

---

## RUNNING

Nothing.

## CURRENT BUILD — `recurrent_dag_consensus`

**808 themes, 998 edges, 16 roots, 24% multi-parent, depth 17 (median 4), 0 unplaced.** MedCPT
vectors, the locked selection rule, plus the greedy-consensus pass
(`docs/spec/amendment-2026-09-25.md`, STRAY 0.10 / JACCARD 0.70). Held-out FDR **0.0037**, every
stratum under 0.02. `recurrent_dag_confirmatory` (844 themes, 39 roots) is kept as the
pre-consensus baseline.

## RESOLVED — the encoder is replaced

`BioLORD-2023` read only the first **128** tokens; the median description is **231**, so all 1,850
were truncated and ~45% of each was discarded. **Replaced by `ncbi/MedCPT-Article-Encoder`, pinned
to `d05a736da4bb84ee4057b7f7999485be6ed85465`**, CLS pooling, `max_length=512`, description text
only. Basis: a Nature Communications 2026 benchmark on gene-set / GO-BP functional descriptions;
OpenAI-TE3 scored higher and was refused because a frozen ontology needs a pinnable open-weights
embedder. **No in-project benchmark was run.**

**Checked this time:** across all 10,770, median **180** MedCPT tokens, max **247**, nothing
truncates, 265 tokens of headroom. Asserted in `tests/ontology/test_universe.py`.

**Every earlier build and E are labelled a truncated-text baseline.** The selection rule is
unchanged; only the vectors. E is being re-run under the identical rule.

### How it was found, in full

`BioLORD-2023` truncates at **128 tokens**. The median description is **231**; **all 1,850 exceed
the cap**, so roughly **45% of every description has never been embedded**. The 90-150 word band
the prompt and validator enforce describes text the encoder never sees.

Raising the cap to 512 works (MPNet has 514 position embeddings) but **changes the nearest
neighbour for 43% of pathways** — a different embedding space, so every threshold and the whole
calibration would be redone against it. Four options and a no-cost AUC test to decide between them
are in `docs/status/2026-09-24-embedding-truncation.md`. **Nothing chosen; nothing run.**

## THE END-TO-END GATE HAS PASSED

The 31-side calibration was rerun twice, same embeddings and same seeds, and **every `.tsv` came
back byte-identical to the original E both times**: 31/31 on fast matching (24 min 13 s) and 31/31
on fast matching plus fast families (**3 min 03 s**, against the original 2 h 05 min -- **41x**).
The gate on the 10,770 universe is satisfied.

## DONE — E, the confirmatory calibration

**986 themes, overall held-out FDR 0.0030 against a 0.01 cap, no stratum dropped.** Sizes 3 and 4
survive on recurrence alone at m = 0.94 / 0.90. Full table and the declared-m sensitivity in
`docs/status/2026-09-24-matching-performance.md`. Ran 2 h 05 min at four concurrent on the original
code. **Not freezable**: 12 of the 1,850 embeddings carry contaminated descriptions (below).

**Nothing is spending money.** The naming smoke test is finished — Sonnet, 50 themes, $0.34.

**Matching is the sparse-product implementation and families is the prefix-filtered one.** Both
carry their three proofs and both keep the original callable (`matching="tree"`,
`families="pairwise"`). A null side is 64 s, of which `prepare` is 25 s — **Ward is now the floor**
and nothing further is proposed.

## NEXT ACTION

0. **In this order, and the order matters.** The byte-identical proof of the fast code exists only
   while the inputs are unchanged, so the 31-side rerun on the *current* embeddings comes first.
   Then repair the descriptions; then snapshot and re-embed; then re-run E and compare the two.

0a. **DONE — descriptions repaired.** **205 rows**, not the 66 first reported: 152 truncations at a
   stray closing tag, 53 markup or trailing-quote strips. No regeneration, no API cost. Every
   original kept as `superseded`; every repair is a new `v4-repaired` row naming the row it came
   from. `read()` still returns 10,770 and **0 rows trip the validator**. The write gate is in:
   `normalize_descriptions.py` now refuses a row the validator rejects and keeps it in the ledger.

0c. **DONE — E2.** The calibration re-run on the repaired embeddings reproduces E exactly: 986
   themes, held-out 0.0030, no stratum dropped, all 31 sides byte-identical on `(arm, size,
   support)`. **The corruption's measured effect is zero**, because the junk sat past token 128.

0z. ~~Repair 66 corrupted descriptions.~~ No API cost — 30 truncate at a stray `</description>`
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
- `recurrent_dag_single_banded/` — committed 25 Sep as a historical build; superseded, on the
  1,854 pre-universe subset and on truncated BioLORD vectors. Do not quote it.

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
