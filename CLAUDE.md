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
