# THEMA

THEMA is a bioinformatics tool that clusters biological pathways into a hierarchical ontology and
runs enrichment statistics over it. Given a collection of pathways, it groups related ones into a
tree of increasingly general themes, then tests gene sets for statistical enrichment against the
nodes of that hierarchy rather than against a flat pathway list.

## Commands

```sh
uv run pytest        # run the test suite
uv run ruff check    # lint
```

## Conventions

- Type hints everywhere.
- Docstrings on public functions.
- All LLM calls must go through a caching client — never call a provider SDK directly.
- No notebooks in `src/`.
