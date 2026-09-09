"""Write description_generated for every pathway, and the committed record of that generation.

Three modes. ``--sample`` generates a 12-pathway, three-model comparison and prints it for a human
to judge: a mechanical scoring table first, then the twelve pathways with their three descriptions
blinded as A/B/C, then a measured cost and time estimate for the full run. ``--smoke`` generates a
reproducible stratified subset -- about 17% of the collection, drawn within Reactome's top-level
branches, GO:BP's level-1 branches, and BTM's named and TBA halves, plus both members of every
cross-source name collision -- so the clusterer can be built and a tree read before the full spend
is committed. ``--full`` generates all 10,817, once a model has been chosen.

``--smoke`` and ``--full`` both go through the batch API at half price, and both refuse to spend
without ``--submit``. Without it they price the run and stop. The price is marginal: completions
already in the ledger are free to reuse, so a rerun shows what is left to pay for rather than what
the whole run would have cost. ``--max-dollars`` is a second guard, checked against the worst case
rather than the likely one, because a batch that dies halfway is worse than one that never starts.

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
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from thema.data.formats import OboTerm, parse_obo_terms
from thema.data.hierarchy import (
    go_ancestors,
    go_level1_branches,
    reactome_branches_of,
    reactome_roots,
    read_reactome_relation,
)
from thema.data.pathways import (
    SOURCES,
    Pathway,
    PathwayCollection,
    collision_groups,
)
from thema.data.tables import (
    SUMMARY_COLUMNS,
    cell,
    print_table,
    sha256_file,
    write_tsv,
)
from thema.llm import (
    BATCH_CHUNK,
    MODELS,
    PRICES,
    Completion,
    Estimate,
    Ledger,
    LLMClient,
    Request,
    chunked,
    price_batch,
    report_cost,
    spend,
    within_ceiling,
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
DEFAULT_RAW = REPO_ROOT / "data" / "raw"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"
DESCRIPTIONS_SUMMARY = "pathway_descriptions_summary.tsv"
SAMPLE_TABLE = "description_sample.tsv"
CACHE_DIR = "cache/descriptions"

#: Fixed so the twelve are the same twelve on every run and in every checkout.
SAMPLE_SEED = 0

#: The three models the sample compares.
SAMPLE_MODELS = ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5")

#: The share of each stratum the smoke run draws. Chosen so a clusterer can be built and a tree read
#: before the full spend is committed, and so every stratum contributes something.
SMOKE_FRACTION = 0.15

#: Fixed so the selection is the same subset in every checkout, as SAMPLE_SEED is for the twelve.
SMOKE_SEED = 0

#: Strata drawn whole rather than sampled. Hallmark is 50 sets against Reactome's 2,883 and GO's
#: 7,538, so taking all of it costs almost nothing; and it is the coarsest, most-used collection
#: there is, which makes it the arm most worth having complete when the tree is read.
SMOKE_WHOLE = ("hallmark",)

#: No stratum contributes fewer than this, however small it is. A two-member Reactome branch must
#: still reach the tree, or the sample cannot show the cross-branch structure it exists to test.
SMOKE_FLOOR = 3

#: How many pending prompts the estimate counts exactly through the provider's tokenizer. A seeded
#: random subsample of what will actually be sent, so the mean is unbiased; the calls are metering
#: rather than inference and are not billed.
ESTIMATE_SAMPLE = 60

#: The credit on the account when this was written. A batch that dies halfway is worse than one that
#: never starts, so a run priced above this refuses until the ceiling is raised deliberately.
DEFAULT_MAX_DOLLARS = 20.00

#: Fallbacks, used only when neither the tokenizer nor a cached completion is reachable, and named
#: in the report when they are. Both measured over the twelve v3 prompts on claude-opus-5.
SYSTEM_PROMPT_TOKENS = 2112
ASSUMED_OUTPUT_TOKENS = 383

#: Written into the summary so a partial table can never be mistaken for a complete one.
SCOPE_SMOKE = "smoke"
SCOPE_FULL = "full"

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


# ------------------------------------------------------------------- smoke


def smoke_strata(
    collection: PathwayCollection,
    parents: Mapping[str, Sequence[str]],
    roots: frozenset[str],
    terms: Mapping[str, OboTerm],
) -> dict[str, tuple[Pathway, ...]]:
    """Partition the collection into the strata the smoke run samples within.

    Reactome is stratified by top-level branch (29 of them), GO:BP by level-1 branch (18, plus one
    bucket for the obsolete terms GO has detached from the DAG), Hallmark not at all, and BTM by
    whether a module has a real name or is one of the 87 named ``TBA``.

    Neither source hierarchy is a tree: 33 Reactome pathways reach two top-level roots and 1,630 GO
    terms reach two or more level-1 branches. A node reaching several is filed into the LARGEST
    branch it reaches, ties broken on lowest id.

    The reason is the per-stratum floor. Above the floor, filing a shared node into its largest or
    its smallest branch gives identical expected unique-member coverage; the two rules differ only
    where the floor bites, which is the small branches. There, filing shared terms into the small
    pile spends that pile's quota on generalists that also live in the mega-pile -- a branch with 2
    unique and 5 shared members yields about 0.9 distinctive pathways under most-specific and 2
    under most-general. Filing into the largest keeps each narrow branch's quota for the pathways
    only it has, and the shared terms lose nothing: they sit in the mega-pile and are drawn at the
    same rate.

    THE STRATUM IS A SAMPLING DEVICE, NOT A BIOLOGICAL CLASSIFICATION. Nothing downstream may read
    it as one. A pathway's stratum says which pile it was drawn from, not what kind of biology it
    is, and for the 1,663 multi-branch nodes it is one arbitrary choice among several correct
    answers.

    Args:
        collection: All 10,817 pathways.
        parents: Reactome child-to-parents, from
            :func:`~thema.data.hierarchy.read_reactome_relation`.
        roots: Reactome's top-level branches.
        terms: GO terms by id, from :func:`~thema.data.formats.parse_obo_terms`.

    Returns:
        Stratum name to its members, sorted by key.
    """
    level1 = go_level1_branches(terms)

    reactome_reach = {
        p: reactome_branches_of(p.source_id, parents, roots)
        for p in collection.of_source("reactome")
    }
    go_reach = {p: go_ancestors(p.source_id, terms) & level1 for p in collection.of_source("go")}

    sizes: Counter[str] = Counter()
    for reached in (*reactome_reach.values(), *go_reach.values()):
        sizes.update(reached)

    def largest(reached: frozenset[str]) -> str:
        """The biggest pile the node reaches; lowest id breaks a tie."""
        return min(reached, key=lambda branch: (-sizes[branch], branch))

    strata: dict[str, list[Pathway]] = {}
    for pathway, reached in reactome_reach.items():
        strata.setdefault(f"reactome/{largest(reached)}", []).append(pathway)
    for pathway, reached in go_reach.items():
        name = f"go/{largest(reached)}" if reached else "go/obsolete"
        strata.setdefault(name, []).append(pathway)
    for pathway in collection.of_source("hallmark"):
        strata.setdefault("hallmark", []).append(pathway)
    for pathway in collection.of_source("btm"):
        name = "btm/tba" if pathway.text_availability == "no_usable_text" else "btm/named"
        strata.setdefault(name, []).append(pathway)

    return {
        name: tuple(sorted(members, key=lambda p: p.key))
        for name, members in sorted(strata.items())
    }


def smoke_draw(stratum: str, size: int) -> int:
    """How many pathways one stratum contributes.

    Args:
        stratum: The stratum's name, which decides whether it is drawn whole.
        size: The stratum's membership.

    Returns:
        The whole stratum where it is small enough to take entire, and otherwise the share -- but
        never fewer than the floor. The floor is what makes a two-member branch visible in the tree
        at all; without it the narrow branches vanish and the sample cannot show the cross-branch
        structure it exists to test.
    """
    if stratum in SMOKE_WHOLE:
        return size
    return min(size, max(SMOKE_FLOOR, round(SMOKE_FRACTION * size)))


def choose_smoke(
    collection: PathwayCollection,
    strata: Mapping[str, Sequence[Pathway]],
    seed: int = SMOKE_SEED,
) -> tuple[tuple[str, Pathway], ...]:
    """Pick the stratified subset the smoke run generates.

    Every candidate pool is sorted by pathway key before it is sampled, so the draw is a function of
    the pinned inputs and the seed alone -- collection order cannot leak in, and a clean clone
    reproduces the same subset.

    Both members of every cross-source name-collision group are then force-included. Without them
    the redundancy THEMA exists to collapse would be almost absent from the sample and the test
    could not fail: 94 groups and 191 members appear identical only after normalizing, against 18
    in the source files as shipped.

    Args:
        collection: All 10,817 pathways.
        strata: The partition :func:`smoke_strata` built.
        seed: The RNG seed, fixed so the selection never churns.

    Returns:
        ``(stratum, pathway)`` pairs, sorted by key. A pathway drawn by its stratum and also part of
        a collision group keeps its stratum; the collision stratum names only the additions.
    """
    rng = random.Random(seed)
    picked: dict[str, tuple[str, Pathway]] = {}

    for name, members in sorted(strata.items()):
        pool = sorted(members, key=lambda p: p.key)
        for pathway in rng.sample(pool, smoke_draw(name, len(pool))):
            picked[pathway.key] = (name, pathway)

    for name, members in sorted(collision_groups(collection).items()):
        for pathway in members:
            picked.setdefault(pathway.key, (f"collision/{name}", pathway))

    return tuple(picked[key] for key in sorted(picked))


# ------------------------------------------------------------------ pricing


def _measured_user_tokens(
    pending: Sequence[Request],
    client: LLMClient | None,
    ledger: Ledger,
    collection: PathwayCollection,
) -> tuple[float, int, str]:
    """Measure mean input tokens per prompt, preferring the provider's own tokenizer.

    A seeded random subsample of the PENDING prompts is counted exactly, which is unbiased by
    construction. The fallback fits against completions already in the ledger, whose stored
    ``input_tokens`` is the user message alone once the system prompt is cached -- offline, but
    biased by whichever twelve pathways the model comparison happened to pick, which were chosen
    for discrimination rather than for being typical.

    Args:
        pending: The prompts that will actually be sent.
        client: The client, or None to force the offline fallback.
        ledger: The cache, read for the fallback.
        collection: All pathways, for mapping a cached completion back to its prompt.

    Returns:
        Mean user tokens per prompt, how many prompts were counted, and which method was used.
    """
    if client is not None:
        rng = random.Random(SMOKE_SEED)
        sampled = rng.sample(list(pending), min(ESTIMATE_SAMPLE, len(pending)))
        try:
            system_only = client.count_tokens(Request(key="_", system=SYSTEM_PROMPT, user="."))
            counted = [client.count_tokens(request) - system_only for request in sampled]
        except Exception as exc:  # noqa: BLE001 - any provider failure falls back, never crashes
            print(f"tokenizer unavailable ({exc}); falling back to the cached fit", file=sys.stderr)
        else:
            return statistics.mean(counted), len(counted), "tokenizer"

    by_key = collection.by_key
    chars, tokens = 0, 0
    for key in ledger.keys():
        pathway = by_key.get(key)
        completion = ledger.get(key)
        if pathway is None or completion is None or not completion.input_tokens:
            continue
        chars += len(render_user_message(pathway))
        tokens += completion.input_tokens
    if not chars:
        return 0.0, 0, "none"
    per_char = tokens / chars
    mean_chars = statistics.mean(len(r.user) for r in pending)
    return mean_chars * per_char, 0, "cached fit"


def price(
    requests: Sequence[Request],
    pending: Sequence[Request],
    ledger: Ledger,
    client: LLMClient | None,
    collection: PathwayCollection,
    model: str,
) -> Estimate:
    """Estimate what the pending half of a description run will cost.

    Args:
        requests: Every prompt the mode selected.
        pending: Those not already in the ledger.
        ledger: The cache.
        client: The client, or None to price offline.
        collection: All pathways.
        model: The model, for its rates.

    Returns:
        The estimate.
    """
    user_tokens, sampled, basis = _measured_user_tokens(pending, client, ledger, collection)
    system_tokens = SYSTEM_PROMPT_TOKENS
    if client is not None and basis == "tokenizer":
        system_tokens = client.count_tokens(Request(key="_", system=SYSTEM_PROMPT, user="."))
    outputs = [c.output_tokens for c in ledger.completions() if c.output_tokens]
    return price_batch(
        len(requests),
        len(pending),
        user_tokens,
        system_tokens,
        statistics.mean(outputs) if outputs else ASSUMED_OUTPUT_TOKENS,
        model,
        sampled=sampled,
        basis=basis,
    )


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
        repaired = sum(
            1
            for _stratum, pathway in sample
            for c in (completions.get((pathway.key, model)),)
            if c is not None and c.repaired
        )
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
                str(repaired),
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
    Haiku 4.5, whose minimum cacheable prefix its tier sets above this system prompt's 1,933 tokens.
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
    print_table(
        (
            "model",
            "words",
            "median",
            "too long",
            "identifiers",
            "db refs",
            "residue",
            "repaired",
            "no echo",
            "clean",
        ),
        scoring_rows(sample, completions, models),
        "<^^>>>>>>>",
    )

    print(f"\n\nFULL-RUN ESTIMATE  ({len(collection):,} pathways, fitted on real sample usage)\n")
    print_table(
        ("model", "input tokens", "output tokens", "cached", "live", "batch (50%)"),
        estimate(collection, completions, models, clients),
        "<>>^>>",
    )

    print("\n\nBLIND READ\n")
    print(render_blind(sample, completions, labels, models))
    print(f"\nkey withheld; it is in {(out / SAMPLE_TABLE).relative_to(REPO_ROOT)}")
    return 0


def load_hierarchies(
    raw: Path,
) -> tuple[dict[str, tuple[str, ...]], frozenset[str], dict[str, OboTerm]]:
    """Read the two source hierarchies the smoke strata are built from.

    Args:
        raw: The ``data/raw`` directory.

    Returns:
        Reactome child-to-parents, its top-level roots, and the GO:BP terms by id.
    """
    relation = raw / "ReactomePathwaysRelation.txt"
    obo = raw / "go-basic.obo"
    parents = read_reactome_relation(relation.read_text(encoding="utf-8").splitlines())
    with obo.open("r", encoding="utf-8") as handle:
        terms = parse_obo_terms(handle, namespace="biological_process")
    return parents, reactome_roots(parents), terms


def report_selection(
    collection: PathwayCollection,
    strata: Mapping[str, Sequence[Pathway]],
    selection: Sequence[tuple[str, Pathway]],
) -> None:
    """Print what the smoke run selected, per source, with the coverage each source claims.

    Args:
        collection: All 10,817 pathways.
        strata: The partition the draw sampled within.
        selection: The chosen ``(stratum, pathway)`` pairs.
    """
    chosen = {pathway.key: pathway for _stratum, pathway in selection}
    groups = collision_groups(collection)
    covered = sum(1 for members in groups.values() if all(m.key in chosen for m in members))

    print("\nSMOKE SELECTION\n")
    rows: list[tuple[str, ...]] = []
    for source in SOURCES:
        picked = sum(1 for p in chosen.values() if p.source == source)
        total = len(collection.of_source(source))
        names = [n for n in strata if n.split("/")[0] == source]
        drawn = {n for n in names if any(p.key in chosen for p in strata[n])}
        note = f"{len(drawn)}/{len(names)} strata" if len(names) > 1 else ""
        rows.append((source, f"{picked:,}", f"of {total:,}", f"{picked / total:.1%}", note))
    rows.append(("collisions", "", "", "", f"{covered}/{len(groups)} groups fully included"))
    rows.append(
        (
            "total",
            f"{len(chosen):,}",
            f"of {len(collection):,}",
            f"{len(chosen) / len(collection):.1%}",
            "",
        )
    )
    print_table(("source", "picked", "", "share", "coverage"), rows, align="<>><<")

    # The hard cases, counted rather than assumed: these are the strata a homogeneous sample would
    # quietly drop, and the reason the stratification exists at all.
    picked_list = list(chosen.values())
    detail = [
        (
            "BTM TBA modules",
            str(
                sum(
                    1
                    for p in picked_list
                    if p.source == "btm" and p.text_availability == "no_usable_text"
                )
            ),
            "neither prose nor a real title; the hardest case there is",
        ),
        (
            "obsolete GO terms",
            str(
                sum(
                    1
                    for p in picked_list
                    if p.source == "go" and (p.description_source or "").startswith("OBSOLETE.")
                )
            ),
            "detached from the DAG, so their own stratum",
        ),
        (
            "zero-gene pathways",
            str(sum(1 for p in picked_list if not p.n_genes)),
            "described, but nothing resolved; genes_shown will be 0",
        ),
    ]
    print()
    print_table(("hard case", "picked", "why it is one"), detail, align="<><")


def run_smoke(
    collection: PathwayCollection,
    raw: Path,
    out: Path,
    model: str,
    submit: bool,
    ceiling: float,
) -> int:
    """Select the stratified subset, report it and its price, and generate it only if told to."""
    parents, roots, terms = load_hierarchies(raw)
    strata = smoke_strata(collection, parents, roots, terms)
    selection = choose_smoke(collection, strata)
    pathways = [pathway for _stratum, pathway in selection]

    report_selection(collection, strata, selection)
    return _generate(collection, pathways, out, model, submit, ceiling, SCOPE_SMOKE, strata)


def run_full(
    collection: PathwayCollection, out: Path, model: str, submit: bool, ceiling: float
) -> int:
    """Generate all 10,817 descriptions through the batch API."""
    return _generate(collection, list(collection), out, model, submit, ceiling, SCOPE_FULL, {})


def _generate(
    collection: PathwayCollection,
    pathways: Sequence[Pathway],
    out: Path,
    model: str,
    submit: bool,
    ceiling: float,
    scope: str,
    strata: Mapping[str, Sequence[Pathway]],
) -> int:
    """Price a selection, then generate it through the batch API if the gate allows.

    The gate is the same for both modes on purpose. ``--full`` is the larger spend and needs the
    guard more than ``--smoke`` does.

    Args:
        collection: All pathways, which the output table is written against.
        pathways: The subset to generate.
        out: The data directory.
        model: The model.
        submit: Whether to actually call the API.
        ceiling: The ``--max-dollars`` limit.
        scope: ``smoke`` or ``full``, recorded in the summary.
        strata: The smoke partition, for the summary; empty for a full run.

    Returns:
        0 on success, 1 when the gate refuses.
    """
    ledger = Ledger.open(out / CACHE_DIR, model, PROMPT_VERSION)
    requests = [request_for(p) for p in pathways]
    pending = [r for r in requests if r.key not in ledger]

    client: LLMClient | None = None
    if pending:
        try:
            client = LLMClient(model, PROMPT_VERSION, ledger, response_format=RESPONSE_FORMAT)
        except (RuntimeError, ValueError) as exc:
            print(f"pricing offline ({exc})", file=sys.stderr)

    estimate = price(requests, pending, ledger, client, collection, model)
    report_cost(estimate, ceiling)

    if not submit:
        print("\nnothing submitted; rerun with --submit")
        return 0
    if not within_ceiling(estimate, ceiling):
        print(
            f"\nrefusing: ${estimate.uncached_dollars:,.2f} exceeds --max-dollars ${ceiling:,.2f}",
            file=sys.stderr,
        )
        print("raise the ceiling deliberately if that is what you want", file=sys.stderr)
        return 1
    if client is None:
        print("\nno client: cannot submit", file=sys.stderr)
        return 1

    print(f"\n{len(pending):,} of {len(requests):,} to generate on {model}", file=sys.stderr)

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

    write_descriptions(collection, pathways, ledger, out, model, batch_ids, scope, strata)
    return 0


def write_descriptions(
    collection: PathwayCollection,
    pathways: Sequence[Pathway],
    ledger: Ledger,
    out: Path,
    model: str,
    batch_ids: Sequence[str],
    scope: str,
    strata: Mapping[str, Sequence[Pathway]],
) -> None:
    """Write the committed descriptions table and its summary.

    Args:
        collection: All 10,817 pathways, which fixes the table's row order.
        pathways: The subset this run generated.
        ledger: The cache the rows are read out of.
        out: The data directory.
        model: The model.
        batch_ids: The batches that produced this run's completions.
        scope: ``smoke`` or ``full``.
        strata: The smoke partition, for the summary; empty for a full run.
    """
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
        build_summary(
            collection, pathways, ledger, table, model, batch_ids, completions, scope, strata
        ),
    )
    print(f"{len(rows):,} descriptions -> {table}")


def build_summary(
    collection: PathwayCollection,
    pathways: Sequence[Pathway],
    ledger: Ledger,
    table: Path,
    model: str,
    batch_ids: Sequence[str],
    completions: Sequence[Completion],
    scope: str,
    strata: Mapping[str, Sequence[Pathway]],
) -> list[tuple[str, ...]]:
    """Build the committed summary rows.

    The scope block comes first and states the row count against the collection's, because the
    smoke and full runs write the same file and a partial table must never be mistaken for a
    complete one by anything that reads it later.

    Args:
        collection: All 10,817 pathways.
        pathways: The subset this run generated.
        ledger: The cache.
        table: The table just written, for its digest.
        model: The model.
        batch_ids: The batches behind this run.
        completions: The completions the table was built from.
        scope: ``smoke`` or ``full``.
        strata: The smoke partition; empty for a full run.

    Returns:
        The summary rows.
    """
    rows: list[tuple[str, ...]] = [
        (
            "digest",
            DESCRIPTIONS_TABLE,
            sha256_file(table),
            "sha256 of the committed description table",
        ),
        ("input", "scope", scope, "smoke is a stratified subset; full is every pathway"),
        ("input", "model", model, ""),
        ("input", "prompt_version", PROMPT_VERSION, ""),
        ("input", "length_band", f"{MIN_WORDS}-{MAX_WORDS}", "words, stated in the prompt"),
    ]
    described = [(ledger.get(p.key), p) for p in collection if ledger.get(p.key)]
    rows.append(("input", "rows", str(len(described)), "rows in the table this summary pins"))
    rows.append(
        (
            "input",
            "collection_rows",
            str(len(collection)),
            "pathways in data/pathways.tsv; equal to rows only on a full run",
        )
    )
    if scope == SCOPE_SMOKE:
        rows.append(("input", "smoke_fraction", str(SMOKE_FRACTION), "share drawn per stratum"))
        rows.append(("input", "smoke_seed", str(SMOKE_SEED), "fixed; the selection never churns"))
        rows.append(("input", "smoke_floor", str(SMOKE_FLOOR), "minimum drawn from any stratum"))
        rows.append(("input", "smoke_strata", str(len(strata)), "piles the draw sampled within"))
    for index, batch_id in enumerate(batch_ids, start=1):
        rows.append(
            ("batch", f"chunk_{index}", batch_id, "the generation run that produced these rows")
        )

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
    repaired = [c for c in completions if c.repaired]
    rows.append(
        (
            "validator",
            "envelope_repaired",
            str(len(repaired)),
            "responses whose value re-closed the envelope; trimmed on parse, never silently",
        )
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

    chosen = {p.key for p in pathways}
    groups = collision_groups(collection)
    whole = sum(1 for members in groups.values() if all(m.key in chosen for m in members))
    branches = {name.split("/")[0]: 0 for name in strata}
    drawn = dict(branches)
    for name, members in strata.items():
        source = name.split("/")[0]
        branches[source] += 1
        drawn[source] += any(p.key in chosen for p in members)

    checks = [
        Check(
            "every selected pathway has a description",
            str(len(described)),
            str(len(pathways)),
            "a batch result that did not parse would show here",
        ),
        Check(
            "every collision group is whole",
            f"{whole}/{len(groups)}",
            f"{len(groups)}/{len(groups)}",
            "one member of a pair would make the redundancy test unfailable",
        ),
    ]
    checks.extend(
        Check(
            f"{source} strata represented",
            f"{drawn[source]}/{branches[source]}",
            f"{branches[source]}/{branches[source]}",
        )
        for source in sorted(branches)
        if branches[source] > 1
    )
    checks += [
        Check(
            "genes_shown equals n_genes everywhere",
            str(sum(1 for _c, p in described if len(genes_for_prompt(p)) != p.n_genes)),
            "0",
            "nothing was truncated",
        ),
    ]
    rows.extend(check.row() for check in checks)
    return rows


# ------------------------------------------------------------------- report


def read_descriptions(table: Path) -> dict[str, str]:
    """Read the generated descriptions back out of the committed table.

    Args:
        table: Path to ``pathway_descriptions.tsv``.

    Returns:
        Pathway key to its generated description.
    """
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    key, text = header.index("key"), header.index("description_generated")
    return {row[key]: row[text] for row in (line.split("\t") for line in lines[1:] if line)}


def _marks(values: Sequence[int]) -> str:
    """Render min/p10/median/p90/max of a sample, the spread idiom the build tables use."""
    if not values:
        return "-"
    ordered = sorted(values)
    return "/".join(str(ordered[int(q * (len(ordered) - 1))]) for q in (0.0, 0.10, 0.50, 0.90, 1.0))


def run_report(collection: PathwayCollection, out: Path, model: str) -> int:
    """Check the generated descriptions mechanically, before anything is clustered on them.

    Clustering is downstream of text quality, and a bad batch looks exactly like a bad clusterer
    from the tree end. Everything here is measured from the committed table and the ledger, with no
    API call, so it can be run the moment a batch lands and again after any repair.

    Args:
        collection: All pathways.
        out: The data directory.
        model: Which ledger to read repair and stop-reason counts from.

    Returns:
        0, or 1 when there is no table to report on.
    """
    table = out / DESCRIPTIONS_TABLE
    if not table.is_file():
        print(f"missing input: {table}", file=sys.stderr)
        print("run scripts/normalize_descriptions.py --smoke --submit", file=sys.stderr)
        return 1

    texts = read_descriptions(table)
    described = [p for p in collection if p.key in texts]
    ledger = Ledger.open(out / CACHE_DIR, model, PROMPT_VERSION)

    print(f"\nDESCRIPTION REPORT  ({len(described):,} rows of {len(collection):,} pathways)\n")

    rows: list[tuple[str, ...]] = []
    for source in (*SOURCES, "all"):
        theirs = described if source == "all" else [p for p in described if p.source == source]
        if not theirs:
            continue
        validations = [validate(texts[p.key], display_name(p)) for p in theirs]
        tally = summarize(validations)
        completions = [c for c in (ledger.get(p.key) for p in theirs) if c is not None]
        rows.append(
            (
                source,
                f"{len(theirs):,}",
                _marks([v.words for v in validations]),
                f"{tally['clean']}/{tally['total']}",
                str(sum(1 for c in completions if c.repaired)),
                str(sum(1 for c in completions if c.stop_reason not in ("end_turn", ""))),
            )
        )
    print_table(
        ("source", "rows", "words min/p10/med/p90/max", "clean", "repaired", "odd stop"),
        rows,
        align="<>>>>>",
    )

    # Broken out by kind rather than as one clean/not-clean number: a length miss and an invented
    # database identifier are different failures with different fixes, and the aggregate hides both.
    print("\nVALIDATOR HITS BY KIND\n")
    kinds = sorted(
        {name for name, _pattern in (*IDENTIFIER_PATTERNS, *REFERENCE_PATTERNS, *RESIDUE_PATTERNS)}
        | {"length", "name_echo"}
    )
    hit_rows: list[tuple[str, ...]] = []
    for kind in kinds:
        per_source = []
        total = 0
        for source in SOURCES:
            theirs = [p for p in described if p.source == source]
            count = (
                summarize([validate(texts[p.key], display_name(p)) for p in theirs])[kind]
                if theirs
                else 0
            )
            per_source.append(str(count))
            total += count
        if total:
            hit_rows.append((kind, str(total), *per_source))
    if not hit_rows:
        hit_rows.append(("(none)", "0", *["0"] * len(SOURCES)))
    print_table(("kind", "total", *SOURCES), hit_rows, align="<" + ">" * (len(SOURCES) + 1))

    print("\nTEN DESCRIPTIONS IN FULL\n")
    for pathway in _spanning_sample(described, texts):
        print("=" * 96)
        print(f"{pathway.key}  [{pathway.source} / {provenance_of(pathway)}]  {pathway.name}")
        print(f"genes: {len(genes_for_prompt(pathway))}")
        print()
        print(texts[pathway.key])
        print()
    return 0


def _spanning_sample(
    described: Sequence[Pathway], texts: Mapping[str, str], count: int = 10
) -> list[Pathway]:
    """Pick descriptions to read that span every source and every provenance value present.

    One from each (source, provenance) cell first, so no arm of the prompt goes unread, then the
    remainder drawn at random from what is left. Seeded, so two people reading the report are
    reading the same ten.

    Args:
        described: The pathways that have a description.
        texts: Their descriptions.
        count: How many to show.

    Returns:
        The chosen pathways, in key order.
    """
    rng = random.Random(SMOKE_SEED)
    picked: dict[str, Pathway] = {}
    cells: dict[tuple[str, str], list[Pathway]] = {}
    for pathway in described:
        cells.setdefault((pathway.source, provenance_of(pathway)), []).append(pathway)
    for cell_key in sorted(cells):
        pool = sorted(cells[cell_key], key=lambda p: p.key)
        picked[pool[0].key] = rng.choice(pool)
    chosen = {p.key: p for p in picked.values()}
    rest = sorted((p for p in described if p.key not in chosen), key=lambda p: p.key)
    for pathway in rng.sample(rest, min(max(0, count - len(chosen)), len(rest))):
        chosen[pathway.key] = pathway
    return [chosen[k] for k in sorted(chosen)][:count]


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
        "--smoke", action="store_true", help="generate a stratified subset through the batch API"
    )
    parser.add_argument(
        "--report", action="store_true", help="check the generated descriptions; no API call"
    )
    parser.add_argument(
        "--full", action="store_true", help="generate all pathways through the batch API"
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW,
        help="raw data directory, for the two source hierarchies (default: %(default)s)",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="actually call the API; without it --smoke and --full price the run and stop",
    )
    parser.add_argument(
        "--max-dollars",
        type=float,
        default=DEFAULT_MAX_DOLLARS,
        help="refuse to submit above this worst-case price (default: %(default)s)",
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
    if args.report:
        return run_report(collection, args.data, args.model)
    if args.smoke:
        missing = [
            p
            for p in (args.raw / "ReactomePathwaysRelation.txt", args.raw / "go-basic.obo")
            if not p.is_file()
        ]
        if missing:
            for path in missing:
                print(f"missing input: {path}", file=sys.stderr)
            print("run scripts/download_pathway_data.py", file=sys.stderr)
            return 1
        return run_smoke(collection, args.raw, args.data, args.model, args.submit, args.max_dollars)
    if args.full:
        return run_full(collection, args.data, args.model, args.submit, args.max_dollars)

    print("nothing to do: pass --sample, --smoke, --full or --report", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
