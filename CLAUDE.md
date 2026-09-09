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
uv run scripts/verify_descriptions.py --pilot 100          # price a fact-check of 100
uv run scripts/verify_descriptions.py --pilot 100 --submit # run it, and report the flag rate
uv run scripts/build_ontology.py                           # embed, cluster, write the trees
```

## Conventions

- Type hints everywhere.
- Docstrings on public functions.
- All LLM calls must go through a caching client — never call a provider SDK directly.
- Third-party surfaces stay confined to one module each, and a test checks it: `anthropic` in
  `src/thema/llm.py`, `sentence_transformers`/torch in `src/thema/embed.py`.
- Anything that spends money is gated: report the marginal cost first, spend only on `--submit`.
- No notebooks in `src/`.
