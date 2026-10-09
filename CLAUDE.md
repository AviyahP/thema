# THEMA

THEMA is a bioinformatics tool that clusters biological pathways into a hierarchical ontology and
runs enrichment statistics over it. Given a collection of pathways, it groups related ones into a
tree of increasingly general themes, then tests gene sets for statistical enrichment against the
nodes of that hierarchy rather than against a flat pathway list.

## Commands

```sh
uv run pytest                              # run the test suite
uv run ruff check                          # lint
uv run scripts/download_pathway_data.py    # fetch source data into data/raw/ (idempotent)
uv run scripts/resolve_gene_symbols.py     # resolve source symbols to HGNC ids; writes data/gene_resolution_log.tsv
uv run scripts/build_pathways.py           # load all four sources into one table; writes data/pathways.tsv

# Description generation. --smoke and --full price the run and stop unless --submit is passed;
# --max-dollars refuses above a worst-case ceiling. Both go through the batch API at half price.
uv run scripts/normalize_descriptions.py --sample          # 12-pathway, three-model comparison
uv run scripts/normalize_descriptions.py --smoke           # price a stratified ~17% subset
uv run scripts/normalize_descriptions.py --smoke --submit  # generate it
uv run scripts/normalize_descriptions.py --report          # check the descriptions; no API call
uv run scripts/normalize_descriptions.py --keys FILE       # top up a generation: the keys named in FILE
uv run scripts/check_demo_datasets.py --candidates         # check worked-example datasets; metadata only
uv run scripts/verify_descriptions.py --pilot 100          # price a fact-check of 100
uv run scripts/verify_descriptions.py --pilot 100 --submit # run it, and report the flag rate
uv run scripts/build_ontology.py                           # embed, cluster, write the trees
uv run scripts/export_demo.py                              # write demo/ontology.{json,js} for demo/prototype.html
```

### v0.4 — the current core

**v0.4 is the method THEMA uses.** v0.3 and `data/ontology/v0.3/recurrent_dag_10770` stay frozen as
the reference and are never rebuilt. v0.4 is v0.3 with four stages removed — the size cap, the TOL
extras-only rule, STRAY, and partial containment — each dropped because the 8 Oct ablation found
that removing it changed nothing measurable. Three stages remain and each is load-bearing:
completion, greedy seed absorption, and the per-size support floors. The whole method is
`src/thema/ontology/v04.py`, and the removed stages are absent there rather than switchable.

Three knobs: subsample fraction 0.8, one match threshold θ = 0.70 used for both recurrence and
merging, and the floors — calibrated once per configuration and then stored.

```sh
# The byte-identity proof. Restores every removed stage and must reproduce the frozen v0.3
# exactly, at two levels: the side material first, then all four exported tables. Run this
# before trusting any v0.4 number from changed code.
uv run scripts/v04_run.py --all-stages-on --verify

uv run scripts/v04_run.py --calibrate     # solve the floors once, confirm on held-out, store
uv run scripts/v04_run.py                 # build -> data/ontology/v0.4/thema_10770/
uv run scripts/v04_run.py --rows 1-100    # a stability half
uv run scripts/v04_run.py --match-themes 4287   # post hoc cut to another build's theme count

# What the ablation decided, and the test-half comparison.
uv run scripts/v04_ablate.py --ablation baseline --side real   # one ablation side
uv run scripts/v04_build.py --ablation baseline               # build one ablation
uv run scripts/v04_ablation_table.py --scores SCORES.json
uv run scripts/v04_score.py --half test --relations primary --reference v04 --arm NAME=PATH
uv run scripts/v04_pairs.py --half test --arm NAME=PATH      # near-pair agreement
```

Cost on this machine: 370 s and 7.6 GB for a build with stored floors (307 s of that is the side
material), 64 s if the side is cached. Calibration is the only expensive part and is paid once per
configuration.

**Placement is a known open failure, not a bug to look for.** THEMA does not put curated parent
pathways above their children: among curated pairs whose levels differ, the parent is the higher one
46.1% of the time against a 50% coin flip, and this is true of v0.3, v0.4, Leiden and HiDeF alike.
See `docs/status/2026-10-08-monotonicity.md`. Theme-level gene containment does hold — 100% of
v0.4's 8,422 edges — but that follows from the definitions and is not evidence about placement.

### The leaves experiment (v0.4-leaves) — ANSWERED NO, 8 Oct

Universe L is the 5,559 atomic pathways: the 10,770 with every curated summary removed (a pathway
with at least one universe descendant). The question was whether themes built from the leaves
recreate the summaries. **They do not** — only 8.5% of summaries have any theme matching them at
Jaccard > 0.5, and restricting the full v0.4 build to L afterwards scores *better* than building on
L. The declared decision rule fails all three conditions, so **the full-universe v0.4 stays**. Kept
because the machinery is reusable and because Test T found the one thing that does work: given a
theme that corresponds to a summary, text alone ranks it first 64% of the time out of 2,815.

**L is the first universe where the stored floors do NOT transfer.** The per-stratum held-out check
fails on stratum 5-5 (0.02715 against the 0.02 cap), and recalibrating on L does not clear it
(0.0297). `leaves_build.py` checks before reusing and **raises** rather than defaulting if the
check's shape is unrecognised — reading the wrong key there once made it report "worst stratum 0.0,
PASS" on a build that had failed.

```sh
uv run scripts/leaves_universe.py --sensitivity   # build L; embeddings.npy is RAW, sidecar is centred
uv run scripts/build_trees_10770.py --version 0.4-leaves --space leaves_centred \
    --vectors data/ontology/v0.4-leaves/vectors_leaves_centred.npy --rows 1-200
uv run scripts/leaves_build.py                    # checks v0.4's stored floors on L before using them
uv run scripts/leaves_baseline.py                 # baseline (a): full v0.4 restricted to L
uv run scripts/leaves_score.py --half test --arm L=thema_L --arm restricted=restricted_v04
uv run scripts/leaves_text.py --arm L=thema_L     # Test T: text placement of held-out summaries
```

Recurrence-threshold arms, the re-gate grid, and the repair. `--arm` selects the match threshold
(L 0.70, M5 0.50, MS 0.70 below 50 members and 0.50 at or above); the floor rule comes from whichever
floors file is passed. `--side` computes and caches ONE side, which is how the arms' scramble
material is built without triggering a build.

```sh
uv run scripts/leaves_build.py --arm MS --side seed03004   # cache one side for one arm
uv run scripts/leaves_theta_report.py --arm L=thema_L --arm MS=thema_L_MS

# The re-gate grid: the 0.33 minimum against the calibration alone. DECLARED_M = 0.33 is a constant
# inherited from the 1,850 freeze, and the gate is max(DECLARED_M, floor), so wherever calibration
# lands below 0.33 it is ignored -- on universe L that is three strata, including 10+ at 0.025.
uv run scripts/regate_floors.py                   # three floor rules per arm: current, cal, cal8
uv run scripts/leaves_build.py --arm L --floors-file FLOORS.json --directory DIR
uv run scripts/regate_report.py --arm L=thema_L --arm L_cal8=thema_L_cal8

# Repair route (a): collapse chains at 90%, then re-apply the 0.70 merge on FINAL memberships.
# Both fixes live in src/thema/ontology/repair.py as a post-pass, NOT inside consensus.py, because
# that file is load-bearing for v0.4's byte-identity proof against the frozen build.
uv run scripts/leaves_build.py --arm L --floors-file F.json --repair --directory thema_L_repair
uv run scripts/twins_diagnosis.py                 # why near-duplicate themes survive a 0.70 merge
uv run scripts/repair_big_themes.py               # the 51+ themes: support, support at 0.5, coherence
uv run scripts/repair_node_stats.py               # the same two numbers for EVERY node, cached
uv run scripts/giants_report.py --stats STATS.json          # the giant roots, and the build without them
uv run scripts/export_browse_leaves.py --stats STATS.json   # -> BUILD/browse.html, self-contained

# Merge rules other than Ward, on all of L with no resampling. Step 1 only; step 2 never approved.
uv run scripts/one_linkage_step1.py               # W (Ward) vs C (centroid cosine) vs A (UPGMA)
```

L's vectors are stored **raw**, with the centred matrix as a sidecar, so the tree builder and
`build_hidef.py` each centre exactly once on L. Storing the centred matrix as `embeddings.npy`
makes `build_hidef.py` centre twice and quietly compares two different transformations.

### The 10,770 ontology (v0.3, frozen)

All CPU, no API. The expensive part is the Ward trees, and they are persisted: the cap, the inclusion
cutoff and the floors are all **cut-time** choices, so changing any of them is a re-cut and never a
rebuild. Completions are cached per side and each carries a fingerprint of the code that wrote it —
a mismatch **refuses** to be reused rather than silently serving a side some other implementation
produced.

```sh
# Trees, once. --rows for the real subsamples, --scrambles for the null sides.
uv run scripts/build_trees_10770.py --rows 1-400
uv run scripts/build_trees_10770.py --scrambles --scramble-rows 200
uv run scripts/size_cap_reference.py       # what the declared size cap is measured against

# One build. --rows A-B cuts any block of trees; --confirm-heldout is the CONFIRMATORY BUILD ONLY,
# because a held-out set confirmed against more than once is not held out.
uv run scripts/build_10770.py --rows 1-200 --scramble-rows 200 --completion fast --families joined
uv run scripts/build_10770.py --runs 200 --confirm-heldout --directory recurrent_dag_10770

# The RUNS ladder: two full builds per rung from disjoint blocks, matched on FINAL THEMES.
uv run scripts/runs_ladder.py --rung 1
uv run scripts/theme_match.py BUILD_A BUILD_B      # the statistic the ladder's mark is stated over
uv run scripts/rung3_estimate.py                   # priced from measured sides; does not run it

# Reporting a build.
uv run scripts/freeze_table.py BUILD --floors FLOORS.json   # the FROZEN.md figures
uv run scripts/cap_audit.py BUILD --side SIDE --floors F    # where the size cap stops holding
uv run scripts/cohesion_reference.py --version 0.3 --build BUILD --compare OTHER
uv run scripts/root_profile.py BUILD                        # source mix and children of the roots
uv run scripts/unmatched_profile.py DUMP.tsv                # post hoc: which themes failed to match

# Validation. validate_dag.py is the DAG adapter the validation plan names as missing.
uv run scripts/tfidf_vectors.py                             # test 3's lexical control vectors
uv run scripts/validate_dag.py BUILD --gene-baselines --tfidf-vectors V.npy
uv run scripts/monotonicity_check.py                        # does clustering respect gene containment
uv run scripts/monotonicity_followup.py                     # placement, leaf pairs, the probe controls, GO

# Proving an implementation change byte-identical before it is used.
uv run scripts/verify_completion.py --side SIDE --families
```

## Prompts

**Never send a new or changed prompt to the API without Aviyah seeing the exact text first.**

This is a separate gate from cost. Approving a price is not approving a prompt, and
`--submit` authorises spending, not wording. It applies to every prompt in the repo, not only the
ones called "naming": system prompts, user-message templates, response schemas, and any edit to an
existing one however small.

Established 26 Sep 2026, after two validation tests (`test_name_sorting.py`,
`test_name_dag.py`) were run for $16.50 on prompts Aviyah had never seen. Both results turned out
to be weaker than reported *because* of unreviewed wording -- one asked for a single answer while
the scoring accepted a set, the other explicitly invited the caution that produced its headline
number. An unreviewed prompt is not only a spending problem; it is a validity problem, and the
measurement is worth less than the money.

Show the text, wait, then run.

## Conventions

- Type hints everywhere.
- Docstrings on public functions.
- All LLM calls must go through a caching client — never call a provider SDK directly.
- Third-party surfaces stay confined to one module each, and a test checks it: `anthropic` in
  `src/thema/llm.py`, `sentence_transformers`/torch in `src/thema/embed.py`.
- Anything that spends money is gated: report the marginal cost first, spend only on `--submit`.
- No notebooks in `src/`.
