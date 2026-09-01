"""Write description_generated for every pathway, and the committed record of that generation.

Two modes. ``--sample`` generates a 12-pathway, three-model comparison and prints it for a human to
judge: a mechanical scoring table first, then the twelve pathways with their three descriptions
blinded as A/B/C, then a measured cost and time estimate for the full run. ``--full`` generates all
10,817 through the batch API, at half price, once a model has been chosen.

The twelve are chosen to discriminate between models rather than to cover the collection: three
Reactome sets with rich curated prose (does the model stay faithful or drift?), three GO sets with
one-line definitions (does it add real content or filler?), two Hallmark sets whose input is barely
more than a name, two named BTM modules (is gene-derived biology correct?), and two of BTM's 87 TBA
modules, which have neither prose nor a real title and are the hardest case there is.

Unlike every other build table in this repo, the output is COMMITTED. It is LLM output: not a
deterministic function of pinned inputs, not free, and not reproducible, so a user cloning THEMA
must receive it rather than be told to regenerate it.
"""

import argparse
import random
import statistics
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from thema.data.pathways import SOURCES, Pathway, PathwayCollection
from thema.data.tables import SUMMARY_COLUMNS, cell, sha256_file, write_tsv
from thema.llm import (
    BATCH_CHUNK,
    MODELS,
    PRICES,
    Completion,
    Ledger,
    LLMClient,
    Request,
    chunked,
    spend,
)
from thema.normalize import (
    IDENTIFIER_PATTERNS,
    MAX_WORDS,
    MIN_WORDS,
    PROMPT_VERSION,
    REFERENCE_PATTERNS,
    RESIDUE_PATTERNS,
    RESPONSE_FORMAT,
    SYSTEM_PROMPT,
    display_name,
    genes_for_prompt,
    provenance_of,
    render_user_message,
    summarize,
    validate,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"
DESCRIPTIONS_SUMMARY = "pathway_descriptions_summary.tsv"
SAMPLE_TABLE = "description_sample.tsv"
CACHE_DIR = "cache/descriptions"

#: Fixed so the twelve are the same twelve on every run and in every checkout.
SAMPLE_SEED = 0

#: The three models the sample compares.
SAMPLE_MODELS = ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5")

DESCRIPTION_COLUMNS = (
    "key",
    "description_generated",
    "description_generated_from",
    "genes_shown",
    "model",
    "prompt_version",
)

SAMPLE_COLUMNS = (
    "key",
    "source",
    "text_availability",
    "stratum",
    "blind_label",
    "model",
    "words",
    "clean",
    "findings",
    "description_generated",
)


@dataclass(frozen=True, slots=True)
class Check:
    """One stated expectation and what this run measured against it."""

    key: str
    measured: str
    expected: str
    note: str = ""

    @property
    def status(self) -> str:
        """``pass`` or ``FAIL``."""
        return "pass" if self.measured == self.expected else "FAIL"

    def row(self) -> tuple[str, str, str, str]:
        """Render as a summary row."""
        verdict = f"expected {self.expected} [{self.status}]"
        note = f"{verdict} - {self.note}" if self.note else verdict
        return ("sanity", self.key, self.measured, note)


def request_for(pathway: Pathway) -> Request:
    """Build the request for one pathway.

    Args:
        pathway: The pathway.

    Returns:
        The request, keyed by the pathway's cross-source key.
    """
    return Request(key=pathway.key, system=SYSTEM_PROMPT, user=render_user_message(pathway))


# ------------------------------------------------------------------ sample


def choose_sample(
    collection: PathwayCollection, seed: int = SAMPLE_SEED
) -> tuple[tuple[str, Pathway], ...]:
    """Pick the twelve pathways the model comparison runs on.

    Chosen for discrimination rather than coverage, and within the described strata spread across
    the gene-count and description-length ranges rather than clustered at the median -- a model that
    handles a 20-gene set well may still drift on a 900-gene one.

    Args:
        collection: All 10,817 pathways.
        seed: The RNG seed, fixed so the twelve never churn.

    Returns:
        ``(stratum, pathway)`` pairs, twelve of them.
    """
    rng = random.Random(seed)
    picked: list[tuple[str, Pathway]] = []

    def take(stratum: str, candidates: Sequence[Pathway], count: int) -> None:
        pool = sorted(candidates, key=lambda p: p.key)
        for pathway in rng.sample(pool, min(count, len(pool))):
            picked.append((stratum, pathway))

    reactome = collection.of_source("reactome")
    lengths = sorted(len(p.description_source or "") for p in reactome)
    long_prose = lengths[int(0.75 * len(lengths))]
    sizes = sorted(p.n_genes for p in reactome)
    big = sizes[int(0.90 * len(sizes))]

    # One long-prose set, one carrying the HTML markup 982 summations have, one large gene set.
    take(
        "reactome/long_prose",
        [p for p in reactome if len(p.description_source or "") >= long_prose and p.n_genes],
        1,
    )
    take("reactome/markup", [p for p in reactome if "<br>" in (p.description_source or "")], 1)
    take("reactome/large_set", [p for p in reactome if p.n_genes >= big], 1)

    go = collection.of_source("go")
    go_lengths = sorted(len(p.description_source or "") for p in go)
    terse = go_lengths[int(0.10 * len(go_lengths))]
    go_sizes = sorted(p.n_genes for p in go)
    go_big = go_sizes[int(0.90 * len(go_sizes))]

    take("go/terse_def", [p for p in go if len(p.description_source or "") <= terse], 1)
    take("go/typical", [p for p in go if terse < len(p.description_source or "") < 250], 1)
    take("go/large_set", [p for p in go if p.n_genes >= go_big], 1)

    take("hallmark", list(collection.of_source("hallmark")), 2)

    btm = collection.of_source("btm")
    take("btm/name_only", [p for p in btm if p.text_availability == "name_only"], 2)
    take("btm/tba", [p for p in btm if p.text_availability == "no_usable_text"], 2)

    return tuple(picked)


def blind_labels(
    keys: Sequence[str], models: Sequence[str], seed: int
) -> dict[tuple[str, str], str]:
    """Assign A/B/C to the three models, in a different order for every pathway.

    A fixed order across all twelve would let a reader learn the key from one block and carry it to
    the rest, which is not a blind read.

    Args:
        keys: The pathway keys, in presentation order.
        models: The models.
        seed: The RNG seed.

    Returns:
        ``(key, model) -> label``.
    """
    rng = random.Random(seed + 1)
    labels: dict[tuple[str, str], str] = {}
    for key in keys:
        order = list(models)
        rng.shuffle(order)
        for label, model in zip("ABC", order, strict=False):
            labels[(key, model)] = label
    return labels


def render_blind(
    sample: Sequence[tuple[str, Pathway]],
    completions: dict[tuple[str, str], Completion],
    labels: dict[tuple[str, str], str],
    models: Sequence[str],
) -> str:
    """Render the twelve pathways for a blind read.

    Args:
        sample: ``(stratum, pathway)`` pairs.
        completions: ``(key, model) -> completion``.
        labels: ``(key, model) -> A/B/C``.
        models: The models.

    Returns:
        The text to print. The model behind each label appears nowhere in it.
    """
    out: list[str] = []
    for index, (stratum, pathway) in enumerate(sample, start=1):
        native = pathway.description_source or "(none)"
        genes = genes_for_prompt(pathway)
        shown = ", ".join(genes[:12]) + (
            f", ... (+{len(genes) - 12} more)" if len(genes) > 12 else ""
        )
        out.append("=" * 96)
        out.append(f"[{index}/{len(sample)}]  {display_name(pathway)}")
        out.append(f"        stratum: {stratum}    genes: {len(genes)}")
        out.append("")
        out.append(f"  NATIVE: {native}")
        out.append(f"  GENES:  {shown or '(none)'}")
        out.append("")
        by_label = {
            labels[(pathway.key, model)]: completions[(pathway.key, model)]
            for model in models
            if (pathway.key, model) in completions
        }
        for label in "ABC":
            if label not in by_label:
                continue
            completion = by_label[label]
            out.append(f"  {label}. {completion.text}")
            out.append("")
    out.append("=" * 96)
    return "\n".join(out)


# ------------------------------------------------------------- reporting


def scoring_rows(
    sample: Sequence[tuple[str, Pathway]],
    completions: dict[tuple[str, str], Completion],
    models: Sequence[str],
) -> list[tuple[str, ...]]:
    """Build the mechanical scoring table, one row per model."""
    rows: list[tuple[str, ...]] = []
    for model in models:
        results = []
        words: list[int] = []
        for _stratum, pathway in sample:
            completion = completions.get((pathway.key, model))
            if completion is None:
                continue
            result = validate(completion.text, display_name(pathway))
            results.append(result)
            words.append(result.words)
        tally = summarize(results)
        identifiers = sum(tally.get(name, 0) for name, _ in IDENTIFIER_PATTERNS)
        references = sum(tally.get(name, 0) for name, _ in REFERENCE_PATTERNS)
        residue = sum(tally.get(name, 0) for name, _ in RESIDUE_PATTERNS)
        rows.append(
            (
                model,
                f"{min(words)}-{max(words)}" if words else "-",
                f"{statistics.median(words):.0f}" if words else "-",
                str(tally["length"]),
                str(identifiers),
                str(references),
                str(residue),
                str(tally["name_echo"]),
                f"{tally['clean']}/{tally['total']}",
            )
        )
    return rows


def estimate(
    collection: PathwayCollection,
    completions: dict[tuple[str, str], Completion],
    models: Sequence[str],
    clients: dict[str, LLMClient],
) -> list[tuple[str, ...]]:
    """Extrapolate the full run's cost from measured token counts, not from a character heuristic.

    Three quantities are measured rather than assumed. The system prompt is counted exactly, once,
    through the provider's own tokenizer. The per-character rate for the variable half of the prompt
    is fitted over the twelve sampled prompts, also through the tokenizer, and applied to all 10,817
    constructed prompts. Output tokens are the sample's mean, and this is the weakest of the three:
    a long gene list does not produce a longer description, so the mean is doing real work here.

    Prompt caching is modelled from what each model actually did rather than from what it should do.
    A model whose sample shows no cache activity is priced with none -- which is the true case for
    Haiku 4.5, whose minimum cacheable prefix its tier sets above this system prompt's 1,678 tokens.
    """
    chars = [len(render_user_message(p)) for p in collection]
    total_chars = sum(chars)
    total = len(collection)
    chunks = max(1, -(-total // BATCH_CHUNK))
    rows: list[tuple[str, ...]] = []

    for model in models:
        theirs = [c for (_k, m), c in completions.items() if m == model]
        client = clients.get(model)
        if not theirs or client is None:
            continue

        system_tokens = client.count_tokens(Request(key="_", system=SYSTEM_PROMPT, user="."))
        sampled = [p for p in collection if any(c.key == p.key for c in theirs)]
        counted = [client.count_tokens(request_for(p)) - system_tokens for p in sampled]
        per_char = sum(counted) / max(sum(len(render_user_message(p)) for p in sampled), 1)
        content_in = total_chars * per_char
        mean_out = statistics.mean(c.output_tokens for c in theirs)

        cached = any(c.cache_read_tokens or c.cache_creation_tokens for c in theirs)
        if cached:
            reads, writes, uncached_system = total - chunks, chunks, 0
        else:
            reads, writes, uncached_system = 0, 0, total

        rate_in, rate_out = PRICES[model]
        dollars_in = (
            (content_in + uncached_system * system_tokens) * rate_in
            + reads * system_tokens * rate_in * 0.1
            + writes * system_tokens * rate_in * 1.25
        ) / 1e6
        dollars_out = total * mean_out * rate_out / 1e6
        live = dollars_in + dollars_out
        billed_in = content_in + (uncached_system + reads + writes) * system_tokens
        rows.append(
            (
                model,
                f"{billed_in / 1e6:.1f}M",
                f"{total * mean_out / 1e6:.1f}M",
                "yes" if cached else "NO",
                f"${live:.0f}",
                f"${live / 2:.0f}",
            )
        )
    return rows


def _print_table(headers: Sequence[str], rows: Sequence[Sequence[str]], align: str = "") -> None:
    """Print an aligned ASCII table, the shape ``resolve_gene_symbols.py`` uses."""
    widths = [
        max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h))
        for i, h in enumerate(headers)
    ]
    align = align or "<" * len(headers)
    print("  ".join(f"{h:{align[i]}{widths[i]}}" for i, h in enumerate(headers)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(f"{str(c):{align[i]}{widths[i]}}" for i, c in enumerate(row)))


# ---------------------------------------------------------------- running


def run_sample(collection: PathwayCollection, out: Path, models: Sequence[str]) -> int:
    """Generate, score and present the twelve-pathway comparison."""
    sample = choose_sample(collection)
    requests = [request_for(pathway) for _stratum, pathway in sample]
    completions: dict[tuple[str, str], Completion] = {}
    clients: dict[str, LLMClient] = {}

    for model in models:
        ledger = Ledger.open(out / CACHE_DIR, model, PROMPT_VERSION)
        client = LLMClient(model, PROMPT_VERSION, ledger, response_format=RESPONSE_FORMAT)
        clients[model] = client
        print(
            f"{model}: {len(requests) - sum(1 for r in requests if r.key in ledger)} to generate",
            file=sys.stderr,
        )
        started = time.monotonic()
        for completion in client.complete_all(requests):
            completions[(completion.key, model)] = completion
        print(
            f"{model}: {client.calls} call(s) in {time.monotonic() - started:.0f}s", file=sys.stderr
        )

    labels = blind_labels([p.key for _s, p in sample], models, SAMPLE_SEED)

    rows: list[tuple[str, ...]] = []
    for stratum, pathway in sample:
        for model in models:
            completion = completions.get((pathway.key, model))
            if completion is None:
                continue
            result = validate(completion.text, display_name(pathway))
            rows.append(
                (
                    pathway.key,
                    pathway.source,
                    pathway.text_availability,
                    stratum,
                    labels[(pathway.key, model)],
                    model,
                    str(result.words),
                    "yes" if result.clean else "no",
                    cell(";".join(f"{f.kind}={f.detail}" for f in result.findings)),
                    completion.text,
                )
            )
    write_tsv(out / SAMPLE_TABLE, SAMPLE_COLUMNS, rows)

    print(f"\nMECHANICAL SCORING  (n=12 per model, length band {MIN_WORDS}-{MAX_WORDS} words)\n")
    _print_table(
        (
            "model",
            "words",
            "median",
            "too long",
            "identifiers",
            "db refs",
            "residue",
            "no echo",
            "clean",
        ),
        scoring_rows(sample, completions, models),
        "<^^>>>>>>",
    )

    print(f"\n\nFULL-RUN ESTIMATE  ({len(collection):,} pathways, fitted on real sample usage)\n")
    _print_table(
        ("model", "input tokens", "output tokens", "cached", "live", "batch (50%)"),
        estimate(collection, completions, models, clients),
        "<>>^>>",
    )

    print("\n\nBLIND READ\n")
    print(render_blind(sample, completions, labels, models))
    print(f"\nkey withheld; it is in {(out / SAMPLE_TABLE).relative_to(REPO_ROOT)}")
    return 0


def run_full(collection: PathwayCollection, out: Path, model: str) -> int:
    """Generate all 10,817 descriptions through the batch API."""
    ledger = Ledger.open(out / CACHE_DIR, model, PROMPT_VERSION)
    requests = [request_for(p) for p in collection]
    pending = [r for r in requests if r.key not in ledger]
    print(f"{len(pending):,} of {len(requests):,} to generate on {model}", file=sys.stderr)

    client = LLMClient(model, PROMPT_VERSION, ledger, response_format=RESPONSE_FORMAT)

    # Every chunk is submitted before any is awaited. Submitting and draining one at a time would
    # serialise six 24-hour worst cases; submitted together they share one window, and a chunk that
    # fails still costs only itself.
    submitted: list[tuple[str, Sequence[Request]]] = []
    for index, chunk in enumerate(chunked(pending), start=1):
        batch_id = client.submit_batch(chunk)
        submitted.append((batch_id, chunk))
        print(f"  chunk {index}: {len(chunk):,} requests -> {batch_id}", file=sys.stderr)

    batch_ids: list[str] = []
    for index, (batch_id, chunk) in enumerate(submitted, start=1):
        batch_ids.append(batch_id)
        client.await_batch(batch_id)
        collected = client.collect_batch(batch_id, chunk)
        print(f"  chunk {index}: {len(collected):,} of {len(chunk):,} collected", file=sys.stderr)
        if len(collected) < len(chunk):
            print(
                f"  chunk {index}: {len(chunk) - len(collected):,} did not succeed; rerun to retry",
                file=sys.stderr,
            )

    write_descriptions(collection, ledger, out, model, batch_ids)
    return 0


def write_descriptions(
    collection: PathwayCollection,
    ledger: Ledger,
    out: Path,
    model: str,
    batch_ids: Sequence[str],
) -> None:
    """Write the committed descriptions table and its summary."""
    rows: list[tuple[str, ...]] = []
    completions: list[Completion] = []
    for pathway in collection:
        completion = ledger.get(pathway.key)
        if completion is None:
            continue
        completions.append(completion)
        rows.append(
            (
                pathway.key,
                completion.text,
                provenance_of(pathway),
                str(len(genes_for_prompt(pathway))),
                completion.model,
                completion.prompt_version,
            )
        )
    table = out / DESCRIPTIONS_TABLE
    write_tsv(table, DESCRIPTION_COLUMNS, rows)
    write_tsv(
        out / DESCRIPTIONS_SUMMARY,
        SUMMARY_COLUMNS,
        build_summary(collection, ledger, table, model, batch_ids, completions),
    )
    print(f"{len(rows):,} descriptions -> {table}")


def build_summary(
    collection: PathwayCollection,
    ledger: Ledger,
    table: Path,
    model: str,
    batch_ids: Sequence[str],
    completions: Sequence[Completion],
) -> list[tuple[str, ...]]:
    """Build the committed summary rows."""
    rows: list[tuple[str, ...]] = [
        (
            "digest",
            DESCRIPTIONS_TABLE,
            sha256_file(table),
            "sha256 of the committed description table",
        ),
        ("input", "model", model, ""),
        ("input", "prompt_version", PROMPT_VERSION, ""),
        ("input", "length_band", f"{MIN_WORDS}-{MAX_WORDS}", "words, stated in the prompt"),
    ]
    for index, batch_id in enumerate(batch_ids, start=1):
        rows.append(
            ("batch", f"chunk_{index}", batch_id, "the generation run that produced these rows")
        )

    described = [(ledger.get(p.key), p) for p in collection if ledger.get(p.key)]
    for source in SOURCES:
        rows.append(
            ("source", source, str(sum(1 for _c, p in described if p.source == source)), "")
        )
    rows.append(("source", "total", str(len(described)), ""))

    provenance: dict[str, int] = {}
    zero_genes = 0
    for _completion, pathway in described:
        provenance[provenance_of(pathway)] = provenance.get(provenance_of(pathway), 0) + 1
        if not pathway.n_genes:
            zero_genes += 1
    for name, count in sorted(provenance.items()):
        rows.append(("provenance", name, str(count), ""))
    rows.append(
        (
            "provenance",
            "genes_shown=0",
            str(zero_genes),
            "described pathways that resolved to no genes; the count carries what an enum cannot",
        )
    )

    validations = [validate(c.text, display_name(p)) for c, p in described]
    tally = summarize(validations)
    for name in sorted(tally):
        if name not in ("total", "clean"):
            rows.append(("validator", name, str(tally[name]), ""))
    rows.append(
        ("validator", "clean", f"{tally['clean']}/{tally['total']}", "tripped no check at all")
    )

    words = sorted(v.words for v in validations)
    if words:
        marks = [words[int(q * (len(words) - 1))] for q in (0.0, 0.10, 0.50, 0.90, 1.0)]
        rows.append(("length", "words", "/".join(str(m) for m in marks), "min/p10/median/p90/max"))

    priced = spend(completions, model)
    rows.append(("cost", "input_tokens", f"{priced['input_tokens']:.0f}", ""))
    rows.append(("cost", "cache_read_tokens", f"{priced['cache_read_tokens']:.0f}", ""))
    rows.append(("cost", "output_tokens", f"{priced['output_tokens']:.0f}", "thinking included"))
    rows.append(("cost", "dollars", f"{priced['total']:.2f}", "list price; halve for a batch run"))

    checks = [
        Check("every pathway has a description", str(len(described)), str(len(collection))),
        Check(
            "genes_shown equals n_genes everywhere",
            str(sum(1 for _c, p in described if len(genes_for_prompt(p)) != p.n_genes)),
            "0",
            "nothing was truncated",
        ),
    ]
    rows.extend(check.row() for check in checks)
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    """Run the normalizer."""
    parser = argparse.ArgumentParser(
        prog="normalize_descriptions.py",
        description=__doc__.splitlines()[0],
    )
    parser.add_argument(
        "--data", type=Path, default=DEFAULT_DATA, help="data directory (default: %(default)s)"
    )
    parser.add_argument(
        "--sample", action="store_true", help="run the 12-pathway three-model comparison"
    )
    parser.add_argument(
        "--full", action="store_true", help="generate all pathways through the batch API"
    )
    parser.add_argument(
        "--model", default="claude-opus-5", help="model for --full (default: %(default)s)"
    )
    parser.add_argument(
        "--models",
        default=",".join(SAMPLE_MODELS),
        help="models for --sample (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    table = args.data / PATHWAY_TABLE
    if not table.is_file():
        print(f"missing input: {table}", file=sys.stderr)
        print("run scripts/build_pathways.py", file=sys.stderr)
        return 1
    collection = PathwayCollection.from_tsv_text(table.read_text(encoding="utf-8"))

    if args.sample:
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        unknown = [m for m in models if m not in MODELS]
        if unknown:
            print(f"unknown model(s): {', '.join(unknown)}", file=sys.stderr)
            return 1
        return run_sample(collection, args.data, models)
    if args.full:
        return run_full(collection, args.data, args.model)

    print("nothing to do: pass --sample or --full", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
