"""Fact-check the generated descriptions, and repair what survives a second opinion.

A generated description can pass every mechanical check and still be wrong about a gene. The
validator in ``normalize.py`` matches patterns -- identifiers, length, name echo -- and none of
those can see that a copper transporter has been called an iron transporter. This runs a second
model pass over the committed table and reports the claims that are wrong or unsupported, each
with the sentence quoted and a one-line reason.

It goes through the same caching client and ledger as the generator, so it is resumable, priced,
and reproducible from a clean clone, and it carries the same ``--submit`` and ``--max-dollars``
gate. Nothing here bills against a subscription: these are API calls and they cost money.

Run it in two steps, because the second step is the expensive one. ``--pilot N`` verifies a seeded
random N of the table and reports the flag rate split by kind and by source, together with the
measured cost per description and the projected cost of finishing. Only then is there a real number
to decide the rest on.

Repair never happens silently and never on the verifier's word alone. A flagged description is
regenerated with the specific objection appended to its prompt as a correction instruction, the
rewrite goes back through a fresh verification call, and if it still flags, the ORIGINAL is kept
and both the flag and the failed repair are recorded. Several flags in the twelve-pathway run were
arguable rather than clear-cut, which is exactly why a flag is not allowed to be self-executing.
"""

import argparse
import random
import statistics
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from thema.data.pathways import SOURCES, Pathway, PathwayCollection
from thema.data.tables import SUMMARY_COLUMNS, cell, print_table, sha256_file, write_tsv
from thema.llm import (
    Estimate,
    Ledger,
    LLMClient,
    Request,
    chunked,
    price_batch,
    report_cost,
    within_ceiling,
)
from thema.normalize import RESPONSE_FORMAT as GENERATE_FORMAT
from thema.normalize import SYSTEM_PROMPT as GENERATE_SYSTEM
from thema.verify import (
    FLAG_KINDS,
    RECHECK_PROMPT_VERSION,
    REPAIR_PROMPT_VERSION,
    RESPONSE_FORMAT,
    RESPONSE_KEY,
    SYSTEM_PROMPT,
    VERIFY_PROMPT_VERSION,
    Flag,
    parse_flags,
    render_repair_message,
    render_verify_message,
    tally,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"
VERIFICATION_TABLE = "pathway_verification.tsv"
VERIFICATION_SUMMARY = "pathway_verification_summary.tsv"
CACHE_DIR = "cache/verifications"

#: Fixed, so the pilot is the same N in every checkout and a rerun costs nothing.
PILOT_SEED = 0

#: How many descriptions the pilot checks before anything larger is priced. Large enough for a rate
#: to mean something, small enough that being wrong about the cost is cheap.
DEFAULT_PILOT = 100

#: The same ceiling the generator carries, and for the same reason.
DEFAULT_MAX_DOLLARS = 20.00

#: How many prompts the estimate counts exactly through the tokenizer before extrapolating.
ESTIMATE_SAMPLE = 40

#: Fallback output size for a verifier reply, used only before any reply exists to measure.
ASSUMED_OUTPUT_TOKENS = 300

VERIFICATION_COLUMNS = (
    "key",
    "verification_status",
    "flags",
    "repaired",
    "flag_kinds",
    "flag_quotes",
    "flag_reasons",
)


def read_descriptions(table: Path) -> dict[str, str]:
    """Read the generated descriptions out of the committed table.

    Args:
        table: Path to ``pathway_descriptions.tsv``.

    Returns:
        Pathway key to its generated description.
    """
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    key, text = header.index("key"), header.index("description_generated")
    return {row[key]: row[text] for row in (line.split("\t") for line in lines[1:] if line)}


def choose_pilot(keys: Sequence[str], count: int, seed: int = PILOT_SEED) -> tuple[str, ...]:
    """Draw the pilot subset, seeded and recorded so it is the same subset every time.

    Args:
        keys: Every key with a description.
        count: How many to draw.
        seed: The RNG seed.

    Returns:
        The chosen keys, sorted.
    """
    pool = sorted(keys)
    return tuple(sorted(random.Random(seed).sample(pool, min(count, len(pool)))))


def verify_request(pathway: Pathway, description: str) -> Request:
    """Build the verification request for one description.

    Args:
        pathway: The pathway.
        description: Its generated description.

    Returns:
        The request.
    """
    return Request(
        key=pathway.key, system=SYSTEM_PROMPT, user=render_verify_message(pathway, description)
    )


def repair_request(pathway: Pathway, description: str, flags: Sequence[Flag]) -> Request:
    """Build the regeneration request for a flagged description.

    Args:
        pathway: The pathway.
        description: The description that was flagged.
        flags: What the verifier objected to.

    Returns:
        The request, against the ordinary generation system prompt.
    """
    return Request(
        key=pathway.key,
        system=GENERATE_SYSTEM,
        user=render_repair_message(pathway, description, flags),
    )


def _client(
    data: Path, model: str, prompt_version: str, fmt: dict[str, object], key: str
) -> tuple[Ledger, LLMClient | None]:
    """Open a ledger and, if credentials allow, a client against it."""
    ledger = Ledger.open(data / CACHE_DIR, model, prompt_version)
    try:
        return ledger, LLMClient(
            model, prompt_version, ledger, response_format=fmt, response_key=key
        )
    except (RuntimeError, ValueError) as exc:
        print(f"pricing offline ({exc})", file=sys.stderr)
        return ledger, None


def price_verification(
    requests: Sequence[Request],
    pending: Sequence[Request],
    ledger: Ledger,
    client: LLMClient | None,
    model: str,
) -> Estimate:
    """Price the pending verification calls.

    Args:
        requests: Every verification prompt in scope.
        pending: Those not already cached.
        ledger: The verification cache.
        client: The client, or None to price offline.
        model: The model.

    Returns:
        The estimate.
    """
    user_tokens, sampled, basis, system_tokens = 0.0, 0, "none", 0
    if client is not None and pending:
        chosen = random.Random(PILOT_SEED).sample(list(pending), min(ESTIMATE_SAMPLE, len(pending)))
        try:
            system_tokens = client.count_tokens(Request(key="_", system=SYSTEM_PROMPT, user="."))
            counted = [client.count_tokens(r) - system_tokens for r in chosen]
        except Exception as exc:  # noqa: BLE001 - any provider failure prices offline instead
            print(f"tokenizer unavailable ({exc})", file=sys.stderr)
        else:
            user_tokens, sampled, basis = statistics.mean(counted), len(counted), "tokenizer"
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


def run_batch(client: LLMClient, pending: Sequence[Request], label: str) -> None:
    """Submit and drain one set of prompts through the batch API.

    Args:
        client: The client.
        pending: The prompts.
        label: What to call them in the progress lines.
    """
    submitted: list[tuple[str, Sequence[Request]]] = []
    for index, chunk in enumerate(chunked(pending), start=1):
        batch_id = client.submit_batch(chunk)
        submitted.append((batch_id, chunk))
        print(f"  {label} chunk {index}: {len(chunk):,} requests -> {batch_id}", file=sys.stderr)
    for index, (batch_id, chunk) in enumerate(submitted, start=1):
        client.await_batch(batch_id)
        collected = client.collect_batch(batch_id, chunk)
        print(
            f"  {label} chunk {index}: {len(collected):,} of {len(chunk):,} collected",
            file=sys.stderr,
        )


def flags_from(ledger: Ledger, key: str) -> tuple[Flag, ...] | None:
    """Read one cached verification reply into flags.

    Args:
        ledger: The verification cache.
        key: The pathway key.

    Returns:
        The flags, or None when there is no reply or it could not be read. An unreadable reply is
        never reported as "nothing wrong", which would silently pass an unchecked row.
    """
    completion = ledger.get(key)
    if completion is None:
        return None
    try:
        return parse_flags(completion.text)
    except ValueError as exc:
        print(f"unreadable verification for {key}: {exc}", file=sys.stderr)
        return None


def report_rates(
    results: Mapping[str, Sequence[Flag]], by_key: Mapping[str, Pathway], estimate: Estimate
) -> None:
    """Print the flag rate, split by kind and by source.

    Args:
        results: Flags per verified key.
        by_key: The pathways, for their sources.
        estimate: What the run was priced at, for the per-description figure.
    """
    print("\nFLAG RATE\n")
    rows: list[tuple[str, ...]] = []
    for source in (*SOURCES, "all"):
        theirs = [
            flags
            for key, flags in results.items()
            if source == "all" or by_key[key].source == source
        ]
        if not theirs:
            continue
        counts = tally(theirs)
        n = counts["descriptions"]
        rows.append(
            (
                source,
                f"{n:,}",
                f"{counts['flagged']}",
                f"{counts['flagged'] / n:.1%}" if n else "-",
                str(counts["wrong"]),
                str(counts["unsupported"]),
            )
        )
    print_table(
        ("source", "checked", "flagged", "rate", "wrong", "unsupported"), rows, align="<>>>>>"
    )


def project(estimate: Estimate, checked: int, remaining: int) -> None:
    """Print what finishing the table would cost, from what the pilot actually cost.

    Args:
        estimate: The pilot's estimate.
        checked: How many the pilot checked.
        remaining: How many are left.
    """
    if not checked:
        return
    per = estimate.uncached_dollars / checked
    per_cached = estimate.cached_dollars / checked
    print("\nPROJECTION FOR THE REMAINDER\n")
    print_table(
        ("item", "value", "note"),
        [
            ("checked", f"{checked:,}", "the pilot"),
            ("remaining", f"{remaining:,}", "not yet verified"),
            ("$/description", f"${per:,.4f}", "worst case, measured on the pilot"),
            ("remainder, cached", f"${per_cached * remaining:,.2f}", "if the prompt cache holds"),
            ("remainder, uncached", f"${per * remaining:,.2f}", "ceiling"),
        ],
        align="<><",
    )
    print("\nthis is a decision, not a default: rerun with --all --submit to take it")


def repair(
    data: Path,
    model: str,
    flagged: Mapping[str, Sequence[Flag]],
    by_key: Mapping[str, Pathway],
    texts: Mapping[str, str],
    submit: bool,
) -> dict[str, str]:
    """Regenerate the flagged descriptions, re-check them, and keep only what improved.

    Three outcomes per row, and the pessimistic one is the default. A rewrite that comes back clean
    is a repair. A rewrite that flags again means the original is kept and both the flag and the
    failed repair are recorded -- a second wrong answer is not better than a first, and the
    verifier's objection may itself have been the arguable one.

    Args:
        data: The data directory.
        model: The model.
        flagged: Flags per flagged key.
        by_key: The pathways.
        texts: The current descriptions.
        submit: Whether to actually call the API.

    Returns:
        Status per flagged key: ``repaired`` or ``repair_failed``, or ``flagged`` when nothing ran.
    """
    if not flagged:
        return {}
    repair_ledger, repair_client = _client(
        data, model, REPAIR_PROMPT_VERSION, GENERATE_FORMAT, "description"
    )
    recheck_ledger, recheck_client = _client(
        data, model, RECHECK_PROMPT_VERSION, RESPONSE_FORMAT, RESPONSE_KEY
    )

    requests = [repair_request(by_key[k], texts[k], flags) for k, flags in sorted(flagged.items())]
    pending = [r for r in requests if r.key not in repair_ledger]
    if pending and submit and repair_client is not None:
        print(f"\nregenerating {len(pending):,} flagged descriptions", file=sys.stderr)
        run_batch(repair_client, pending, "repair")

    rewritten = {k: repair_ledger.get(k).text for k in flagged if repair_ledger.get(k) is not None}
    rechecks = [
        verify_request(by_key[k], text)
        for k, text in sorted(rewritten.items())
        if k not in recheck_ledger
    ]
    if rechecks and submit and recheck_client is not None:
        print(f"re-verifying {len(rechecks):,} rewrites", file=sys.stderr)
        run_batch(recheck_client, rechecks, "recheck")

    status: dict[str, str] = {}
    for key in flagged:
        if key not in rewritten:
            status[key] = "flagged"
            continue
        again = flags_from(recheck_ledger, key)
        status[key] = "repaired" if again is not None and not again else "repair_failed"
    return status


def write_verification(
    data: Path,
    results: Mapping[str, Sequence[Flag]],
    status: Mapping[str, str],
    by_key: Mapping[str, Pathway],
    model: str,
    scope: str,
) -> None:
    """Write the verification table and its summary.

    Args:
        data: The data directory.
        results: Flags per verified key.
        status: Status per key.
        by_key: The pathways.
        model: The model that verified.
        scope: ``pilot`` or ``all``.
    """
    rows: list[tuple[str, ...]] = []
    for key in sorted(results):
        flags = results[key]
        rows.append(
            (
                key,
                status.get(key, "clean" if not flags else "flagged"),
                str(len(flags)),
                "yes" if status.get(key) == "repaired" else "no",
                cell(";".join(f.kind for f in flags)),
                cell(" | ".join(f.quote for f in flags)),
                cell(" | ".join(f.reason for f in flags)),
            )
        )
    table = data / VERIFICATION_TABLE
    write_tsv(table, VERIFICATION_COLUMNS, rows)

    counts = tally(results.values())
    summary: list[tuple[str, ...]] = [
        ("digest", VERIFICATION_TABLE, sha256_file(table), "sha256 of the committed table"),
        ("input", "scope", scope, "pilot is a seeded subset; all is every described pathway"),
        ("input", "rows", str(len(rows)), "descriptions verified"),
        ("input", "model", model, "the verifier"),
        ("input", "prompt_version", VERIFY_PROMPT_VERSION, ""),
        ("input", "pilot_seed", str(PILOT_SEED), "fixed; the pilot never churns"),
        (
            "method",
            "self_preference_bias",
            "stated",
            "this is Opus checking Opus; the rate is a lower bound, not a measurement. A different "
            "verifier would be independent and cheaper but weaker on single-gene detail",
        ),
    ]
    for kind in FLAG_KINDS:
        summary.append(("flags", kind, str(counts[kind]), ""))
    summary.append(("flags", "total", str(counts["flags"]), ""))
    summary.append(
        ("flags", "descriptions_flagged", f"{counts['flagged']}/{counts['descriptions']}", "")
    )
    for source in SOURCES:
        theirs = [f for k, f in results.items() if by_key[k].source == source]
        if theirs:
            summary.append(
                (
                    "source",
                    source,
                    f"{sum(1 for f in theirs if f)}/{len(theirs)}",
                    "flagged/checked",
                )
            )
    for outcome in ("repaired", "repair_failed", "flagged"):
        summary.append(
            (
                "repair",
                outcome,
                str(sum(1 for s in status.values() if s == outcome)),
                {
                    "repaired": "rewrite came back clean and replaces the original",
                    "repair_failed": "rewrite flagged again; the ORIGINAL is kept",
                    "flagged": "flagged but not yet repaired",
                }[outcome],
            )
        )
    write_tsv(data / VERIFICATION_SUMMARY, SUMMARY_COLUMNS, summary)
    print(f"\n{len(rows):,} verifications -> {table}")


def main(argv: Sequence[str] | None = None) -> int:
    """Verify the generated descriptions."""
    parser = argparse.ArgumentParser(
        prog="verify_descriptions.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument(
        "--pilot",
        type=int,
        default=DEFAULT_PILOT,
        help="verify a seeded random N first (default: %(default)s)",
    )
    parser.add_argument("--all", action="store_true", help="verify every described pathway")
    parser.add_argument("--repair", action="store_true", help="regenerate and re-check what flags")
    parser.add_argument("--model", default="claude-opus-5", help="verifier (default: %(default)s)")
    parser.add_argument("--submit", action="store_true", help="actually call the API")
    parser.add_argument(
        "--max-dollars",
        type=float,
        default=DEFAULT_MAX_DOLLARS,
        help="refuse to submit above this worst-case price (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    pathways = args.data / PATHWAY_TABLE
    table = args.data / DESCRIPTIONS_TABLE
    for path in (pathways, table):
        if not path.is_file():
            print(f"missing input: {path}", file=sys.stderr)
            print("run scripts/normalize_descriptions.py --smoke --submit", file=sys.stderr)
            return 1

    collection = PathwayCollection.from_tsv_text(pathways.read_text(encoding="utf-8"))
    by_key = collection.by_key
    texts = {k: v for k, v in read_descriptions(table).items() if k in by_key}

    scope = "all" if args.all else "pilot"
    keys = sorted(texts) if args.all else list(choose_pilot(sorted(texts), args.pilot))
    print(f"\nVERIFICATION  ({len(keys):,} of {len(texts):,} descriptions, scope={scope})")

    ledger, client = _client(
        args.data, args.model, VERIFY_PROMPT_VERSION, RESPONSE_FORMAT, RESPONSE_KEY
    )
    requests = [verify_request(by_key[k], texts[k]) for k in keys]
    pending = [r for r in requests if r.key not in ledger]
    estimate = price_verification(requests, pending, ledger, client, args.model)
    report_cost(estimate, args.max_dollars, "COST (billed to the API key, not a subscription)")

    if not args.submit:
        print("\nnothing submitted; rerun with --submit")
        return 0
    if not within_ceiling(estimate, args.max_dollars):
        print(
            f"\nrefusing: ${estimate.uncached_dollars:,.2f} exceeds --max-dollars "
            f"${args.max_dollars:,.2f}",
            file=sys.stderr,
        )
        return 1
    if client is None:
        print("\nno client: cannot submit", file=sys.stderr)
        return 1

    if pending:
        run_batch(client, pending, "verify")

    results: dict[str, tuple[Flag, ...]] = {}
    for key in keys:
        flags = flags_from(ledger, key)
        if flags is not None:
            results[key] = flags

    report_rates(results, by_key, estimate)

    status = {k: "clean" for k, f in results.items() if not f}
    flagged = {k: f for k, f in results.items() if f}
    status.update(dict.fromkeys(flagged, "flagged"))
    if args.repair:
        status.update(repair(args.data, args.model, flagged, by_key, texts, args.submit))

    write_verification(args.data, results, status, by_key, args.model, scope)
    if scope == "pilot":
        project(estimate, len(results), len(texts) - len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
