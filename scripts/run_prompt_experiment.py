"""Run the v4 prompt experiment: three arms over the same 100 pathways that produced the baseline.

The baseline is 27 wrong claims across 26 of 100 descriptions, verified under ``verify-v1``. This
runs the v4 prompt three ways over that identical 100 and, later, scores them with the byte-
identical protocol so the numbers are comparable.

Two hazards this script exists to avoid, both found by measurement rather than by reasoning:

**The verification cache is keyed by pathway alone.** ``verify_descriptions.verify_request`` sets
``Request.key = pathway.key``, so the description text never enters the cache key. Re-verifying a
DIFFERENT description for the same pathway returns the OLD verdict, makes zero API calls, and
rewrites the verification table with quotes from text that no longer exists. Nothing detects it.
Every verification here is text-addressed: the key carries a digest of the description being judged,
so a verdict can never outlive the text it was about.

**Adding rows to ``pathway_descriptions.tsv`` would silently re-draw "the same 100".**
``choose_pilot`` samples from every key in that table. Experiment output therefore goes to
``data/experiments/`` and the committed descriptions table is never touched.

Nothing bills without ``--submit``. Costs are marginal (completions already in a ledger are
free) and every batch is priced before it is sent.
"""

import argparse
import collections
import csv
import hashlib
import json
import random
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from thema.data.pathways import Pathway, PathwayCollection
from thema.data.tables import cell, flatten, merge_tsv, print_table, write_tsv
from thema.experiment import ARMS, Arm
from thema.llm import (
    Estimate,
    Ledger,
    LLMClient,
    Request,
    chunked,
    price_batch,
    within_ceiling,
)
from thema.normalize import display_name, render_user_message
from thema.stats import describe, mcnemar
from thema.verify import (
    ADJUDICATE_FORMAT,
    ADJUDICATE_KEY,
    ADJUDICATE_PROMPT_VERSION,
    ADJUDICATE_SYSTEM_PROMPT,
    REPAIR_PROMPT_VERSION,
    VERIFY_PROMPT_VERSION,
    Flag,
    parse_flags,
    parse_label,
    render_adjudicate_message,
    render_repair_message,
    render_verify_message,
    tally,
)
from thema.verify import RESPONSE_FORMAT as VERIFY_FORMAT
from thema.verify import RESPONSE_KEY as VERIFY_KEY
from thema.verify import SYSTEM_PROMPT as VERIFY_SYSTEM

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"
VERIFICATION_TABLE = "pathway_verification.tsv"
FLAGS_TABLE = "pathway_verification_flags.tsv"
EXPERIMENT_DIR = "experiments"
CACHE_DIR = "cache/experiment"

#: Fixed, so the ten shown are the same ten for anyone who reruns this.
SHOW_SEED = 0
SHOW_COUNT = 10

#: How many pending prompts the estimate counts exactly through the tokenizer.
ESTIMATE_SAMPLE = 40

ARM_COLUMNS = ("key", "arm", "description", "checks", "words", "model", "prompt_version")

WORKSHEET_COLUMNS = (
    "n",
    "key",
    "source",
    "name",
    "kind",
    "quote",
    "reason",
    "label",
    "label_source",
)

#: How the hand labels were produced, carried on every worksheet row and printed with every gate
#: result. The labels were DRAFTED BY A MODEL from the flag quotes and reasons, then reviewed and
#: accepted by a human -- they are not an independent human split produced from scratch. So if
#: adjudicate-v1 agrees with them, part of that agreement is two models agreeing, and the
#: calibration gate is weaker evidence than a purely human split would be.
LABEL_PROVENANCE = "model-drafted, human-reviewed and accepted; not independent human labels"

#: Worksheet rows the human labeller flagged as close calls when supplying the labels. A
#: disagreement here means something different from a disagreement on a clear-cut row.
BORDERLINE = ("2", "24")

FLAG_COLUMNS = ("key", "arm", "kind", "quote", "reason")

#: Output tokens a verification reply is assumed to take before any exists to measure.
ASSUMED_VERIFY_OUTPUT = 300


def text_key(pathway_key: str, description: str) -> str:
    """Build a verification cache key that carries the text being judged.

    Args:
        pathway_key: The pathway.
        description: The description under verification.

    Returns:
        A key of the form ``go:GO:1#a1b2c3d4e5f6``. Keying on the pathway alone is what would let a
        stale verdict be served for text that has since changed.
    """
    digest = hashlib.sha256(description.encode("utf-8")).hexdigest()[:12]
    return f"{pathway_key}#{digest}"


def pilot_keys(data: Path) -> list[str]:
    """Read the exact 100 pathway keys the baseline was measured on.

    Taken from the committed verification table rather than recomputed, because ``choose_pilot``
    samples from the descriptions table and would draw a different hundred if that table changed.

    Args:
        data: The data directory.

    Returns:
        The pathway keys, sorted.
    """
    lines = (data / VERIFICATION_TABLE).read_text(encoding="utf-8").splitlines()
    index = lines[0].split("\t").index("key")
    return sorted(line.split("\t")[index] for line in lines[1:] if line)


def read_descriptions(table: Path) -> dict[str, str]:
    """Read generated descriptions out of a table with ``key`` and ``description_generated``."""
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    key, text = header.index("key"), header.index("description_generated")
    return {row[key]: row[text] for row in (line.split("\t") for line in lines[1:] if line)}


@dataclass(frozen=True, slots=True)
class Generated:
    """One arm's output for one pathway.

    Attributes:
        key: The pathway key.
        description: The text that will be graded, and the only thing kept downstream.
        checks: Arm C's pre-writing notes, or "" -- scaffolding, never an artifact.
    """

    key: str
    description: str
    checks: str


def unpack(arm: Arm, text: str) -> tuple[str, str]:
    """Split a stored completion into the graded description and any scaffolding.

    Args:
        arm: The arm that produced it.
        text: The stored completion text.

    Returns:
        ``(description, checks)``. For arms whose payload is a plain string the completion IS the
        description; arm C stores the whole envelope, so it is parsed here.

    Raises:
        ValueError: If arm C's envelope cannot be read. A malformed envelope is never returned as
            though it were a description.
    """
    if arm.response_key == "description":
        return text, ""
    try:
        parsed = json.loads(text)
        return str(parsed["description"]), " | ".join(str(c) for c in parsed.get("checks", ()))
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"unreadable {arm.name} envelope: {error}") from error


def build_client(
    data: Path, model: str, version: str, fmt: dict, key: str
) -> tuple[Ledger, LLMClient | None]:
    """Open a ledger and, if credentials allow, a client against it."""
    ledger = Ledger.open(data / CACHE_DIR, model, version)
    try:
        return ledger, LLMClient(model, version, ledger, response_format=fmt, response_key=key)
    except (RuntimeError, ValueError) as exc:
        print(f"pricing offline ({exc})", file=sys.stderr)
        return ledger, None


def price(
    requests: list[Request],
    pending: list[Request],
    ledger: Ledger,
    client: LLMClient | None,
    model: str,
    system: str,
    assumed_output: int,
) -> Estimate:
    """Price the pending half of one arm through the provider's own tokenizer."""
    user_tokens, system_tokens, sampled, basis = 0.0, 0, 0, "nothing pending"
    if pending and client is not None:
        chosen = random.Random(SHOW_SEED).sample(pending, min(ESTIMATE_SAMPLE, len(pending)))
        try:
            system_tokens = client.count_tokens(Request(key="_", system=system, user="."))
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
        statistics.mean(outputs) if outputs else assumed_output,
        model,
        sampled=sampled,
        basis=basis,
    )


def run_batch(client: LLMClient, pending: list[Request], label: str) -> None:
    """Submit and drain one set of prompts through the batch API."""
    submitted = []
    for index, chunk in enumerate(chunked(pending), start=1):
        batch_id = client.submit_batch(chunk)
        submitted.append((batch_id, chunk))
        print(f"  {label} chunk {index}: {len(chunk):,} -> {batch_id}", file=sys.stderr)
    for index, (batch_id, chunk) in enumerate(submitted, start=1):
        client.await_batch(batch_id)
        collected = client.collect_batch(batch_id, chunk)
        print(f"  {label} chunk {index}: {len(collected):,}/{len(chunk):,}", file=sys.stderr)
        if len(collected) < len(chunk):
            print(f"  {label}: {len(chunk) - len(collected):,} did not succeed", file=sys.stderr)


def generate(
    data: Path,
    arm: Arm,
    pathways: list[Pathway],
    model: str,
    submit: bool,
    ceiling: float,
    collect: str | None = None,
) -> tuple[dict[str, Generated], Estimate]:
    """Generate one arm's descriptions, pricing before any submission.

    Args:
        data: The data directory.
        arm: The arm.
        pathways: The pathways to describe.
        model: The model.
        submit: Whether to actually call the API.
        ceiling: The per-run ``--max-dollars`` limit.
        collect: A batch id to drain instead of submitting, for a run interrupted after submission.
            A batch is billed when the provider runs it, not when its results are read, so draining
            one already submitted costs nothing while resubmitting pays for it twice.

    Returns:
        The arm's output by pathway key, and what the run was priced at.
    """
    ledger, client = build_client(
        data, model, arm.prompt_version, arm.response_format, arm.response_key
    )
    requests = [
        Request(key=p.key, system=arm.system, user=render_user_message(p)) for p in pathways
    ]
    pending = [r for r in requests if r.key not in ledger]
    estimate = price(requests, pending, ledger, client, model, arm.system, arm.assumed_output)

    if collect and pending:
        if client is None:
            print(f"\n{arm.name}: no client, cannot collect", file=sys.stderr)
            return {}, estimate
        status = client.batch_status(collect)
        if status != "ended":
            print(f"\n{arm.name}: batch {collect} is {status}; rerun this command later")
            return {}, estimate
        collected = client.collect_batch(collect, pending)
        print(f"  {arm.name}: collected {len(collected):,}/{len(pending):,}", file=sys.stderr)
        pending = [r for r in requests if r.key not in ledger]

    if submit and pending:
        if client is None:
            print(f"\n{arm.name}: no client, cannot submit", file=sys.stderr)
            return {}, estimate
        if not within_ceiling(estimate, ceiling):
            print(
                f"\n{arm.name}: refusing, ${estimate.uncached_dollars:,.2f} exceeds "
                f"--max-dollars ${ceiling:,.2f}",
                file=sys.stderr,
            )
            return {}, estimate
        run_batch(client, pending, arm.name)

    out: dict[str, Generated] = {}
    for request in requests:
        completion = ledger.get(request.key)
        if completion is None:
            continue
        try:
            description, checks = unpack(arm, completion.text)
        except ValueError as exc:
            print(f"  {exc}", file=sys.stderr)
            continue
        out[request.key] = Generated(request.key, description, checks)
    return out, estimate


def write_arm(
    data: Path, arm: Arm, produced: dict[str, Generated], model: str, suffix: str = ""
) -> Path:
    """Write one arm's output to the experiment directory.

    Never to ``pathway_descriptions.tsv``: ``choose_pilot`` samples from that table, so adding rows
    would silently re-draw the hundred this experiment is defined on. Arm C's ``checks`` are written
    here for inspection only and are not part of any artifact a consumer reads.

    Every cell is flattened. ``write_tsv`` does no escaping -- cells must already be free of tabs
    and newlines, and ``flatten`` is normally applied when prose is LOADED rather than written
    (``tables.py``). Text generated in-process has never been through that path, and arm C's
    multi-line checks turned 100 rows into 104 before this was added.

    Args:
        data: The data directory.
        arm: The arm.
        produced: Its output.
        model: The model.
        suffix: Distinguishes samples. Without it a fresh-sample run overwrites the pilot run's
            file, which is the same overwrite class that has already cost this experiment three
            separate reruns.

    Returns:
        The path written.
    """
    out = data / EXPERIMENT_DIR
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"v4_{arm.name.split()[0].lower()}{suffix}.tsv"
    rows = [
        (
            g.key,
            arm.name,
            cell(flatten(g.description)),
            cell(flatten(g.checks)),
            str(len(g.description.split())),
            model,
            arm.prompt_version,
        )
        for g in (produced[k] for k in sorted(produced))
    ]
    write_tsv(path, ARM_COLUMNS, rows)
    return path


def show_sample(produced: dict[str, dict[str, Generated]], by_key: dict[str, Pathway]) -> None:
    """Print ten randomly drawn descriptions in full, before anything is scored.

    A random draw rather than a selection: the point is to catch the prompt producing something
    structurally odd, and a curated sample cannot do that.

    Args:
        produced: Arm name to its output.
        by_key: Pathways by key.
    """
    pool = [(arm, g.key) for arm, out in produced.items() for g in out.values()]
    if not pool:
        print("\nnothing generated to show")
        return
    drawn = random.Random(SHOW_SEED).sample(pool, min(SHOW_COUNT, len(pool)))
    print(f"\n{'=' * 96}")
    print(f"TEN DESCRIPTIONS, RANDOMLY DRAWN ({len(drawn)} of {len(pool)} generated)")
    print("=" * 96)
    for arm, key in sorted(drawn):
        pathway = by_key[key]
        generated = produced[arm][key]
        print(f"\n{'-' * 96}")
        print(f"{key}  [{pathway.source}]  {display_name(pathway)}")
        print(f"arm: {arm}   words: {len(generated.description.split())}")
        print("-" * 96)
        print(generated.description)
        if generated.checks:
            print("\n  [checks: scaffolding only, not graded, not kept downstream]")
            print(f"  {generated.checks[:600]}")


def write_worksheet(data: Path) -> tuple[Path, int]:
    """Emit the v3 wrong claims for hand-labelling, numbered and ready to mark.

    Reads the normalised flags table, one row per flag. The earlier shape kept three
    delimiter-joined lists in one row, which only stays readable while no quote contains the
    delimiter and every consumer pairs the three by index -- and a consumer that filters one list
    before indexing another silently reads the wrong quote.

    Args:
        data: The data directory.

    Returns:
        The path written and how many claims it holds.
    """
    collection = PathwayCollection.from_tsv_text((data / PATHWAY_TABLE).read_text(encoding="utf-8"))
    by_key = collection.by_key
    flags = list(csv.DictReader((data / FLAGS_TABLE).open(encoding="utf-8"), delimiter="\t"))

    out = data / EXPERIMENT_DIR
    worksheet = out / "adjudication_worksheet.tsv"
    rows: list[tuple[str, ...]] = []
    for flag in flags:
        if flag["kind"] != "wrong":
            continue
        pathway = by_key[flag["key"]]
        rows.append(
            (
                str(len(rows) + 1),
                pathway.key,
                pathway.source,
                cell(flatten(display_name(pathway))),
                flag["kind"],
                cell(flatten(flag["quote"])),
                cell(flatten(flag["reason"])),
                "",
                LABEL_PROVENANCE,
            )
        )
    out.mkdir(parents=True, exist_ok=True)
    # `label` belongs to a human: a regeneration leaves it empty, and merge_tsv keeps whatever is
    # already there. Blanking 27 hand labels is how this function first went wrong.
    merge_tsv(worksheet, WORKSHEET_COLUMNS, rows, key=("n",), preserve=("label",))
    return worksheet, len(rows)


def verify_arm(
    data: Path,
    arm_name: str,
    produced: dict[str, Generated],
    by_key: dict[str, Pathway],
    model: str,
    submit: bool,
    ceiling: float,
    collect: str | None = None,
) -> tuple[dict[str, tuple[Flag, ...]], Estimate]:
    """Verify one arm with the frozen protocol.

    The prompt, model, schema and flag rules are ``verify.py``'s, untouched -- that file has one
    commit and has never been modified, which is what makes these numbers comparable to the 27/100
    baseline. The ONLY difference is the cache key, which carries a digest of the description being
    judged so a verdict can never be served for text that has since changed.

    Args:
        data: The data directory.
        arm_name: Which arm is being verified.
        produced: Its descriptions.
        by_key: Pathways by key.
        model: The verifier.
        submit: Whether to actually call the API.
        ceiling: The per-run ``--max-dollars`` limit.
        collect: A batch id to drain instead of submitting.

    Returns:
        Flags per pathway key, and what the run was priced at.
    """
    ledger, client = build_client(data, model, VERIFY_PROMPT_VERSION, VERIFY_FORMAT, VERIFY_KEY)
    requests = [
        Request(
            key=text_key(g.key, g.description),
            system=VERIFY_SYSTEM,
            user=render_verify_message(by_key[g.key], g.description),
        )
        for g in (produced[k] for k in sorted(produced))
    ]
    pending = [r for r in requests if r.key not in ledger]
    estimate = price(requests, pending, ledger, client, model, VERIFY_SYSTEM, ASSUMED_VERIFY_OUTPUT)

    if collect and pending and client is not None:
        status = client.batch_status(collect)
        if status != "ended":
            print(f"\n{arm_name}: verify batch {collect} is {status}; rerun later")
            return {}, estimate
        client.collect_batch(collect, pending)
        pending = [r for r in requests if r.key not in ledger]

    if submit and pending:
        if client is None:
            print(f"\n{arm_name}: no client, cannot submit", file=sys.stderr)
            return {}, estimate
        if not within_ceiling(estimate, ceiling):
            print(
                f"\n{arm_name}: refusing, ${estimate.uncached_dollars:,.2f} exceeds "
                f"--max-dollars ${ceiling:,.2f}",
                file=sys.stderr,
            )
            return {}, estimate
        run_batch(client, pending, f"verify {arm_name}")

    results: dict[str, tuple[Flag, ...]] = {}
    for key in sorted(produced):
        completion = ledger.get(text_key(key, produced[key].description))
        if completion is None:
            continue
        try:
            results[key] = parse_flags(completion.text)
        except ValueError as exc:
            print(f"  unreadable verification for {key}: {exc}", file=sys.stderr)
    return results, estimate


def report_flags(
    arm_name: str, results: dict[str, tuple[Flag, ...]], by_key: dict[str, Pathway]
) -> None:
    """Print one arm's flags verbatim, grouped by pathway.

    Args:
        arm_name: The arm.
        results: Flags per key.
        by_key: Pathways by key.
    """
    counts = tally(results.values())
    print(f"\n{'=' * 96}")
    print(f"{arm_name.upper()} -- VERIFY-V1 RESULT")
    print("=" * 96)
    print(f"\n  descriptions verified : {counts['descriptions']}")
    print(f"  flagged               : {counts['flagged']}")
    print(f"  claims total          : {counts['flags']}")
    print(f"    wrong               : {counts['wrong']}")
    print(f"    unsupported         : {counts['unsupported']}")

    flagged = {k: f for k, f in results.items() if f}
    if not flagged:
        print("\n  no claims flagged")
        return
    print(f"\n{'-' * 96}\nCLAIMS, GROUPED BY PATHWAY\n{'-' * 96}")
    for key in sorted(flagged):
        pathway = by_key[key]
        print(f"\n{key}  [{pathway.source}]  {display_name(pathway)}")
        for flag in flagged[key]:
            print(f"  [{flag.kind}]")
            print(f"    claim : {flag.quote}")
            print(f"    reason: {flag.reason}")


def compare_to_baseline(
    data: Path, results: dict[str, tuple[Flag, ...]], by_key: dict[str, Pathway]
) -> None:
    """Say which of the hand-labelled unambiguous v3 errors are fixed, persist, or are new.

    Matching is by PATHWAY, not by claim: a v4 flag on a pathway that carried a v3 error is not
    necessarily the same error, so both claims are printed and the judgement is left to a reader.
    Counting them as identical would overstate "persists" and understate "new".

    Args:
        data: The data directory.
        results: The arm's flags per pathway key.
        by_key: Pathways by key.
    """
    rows = list(
        csv.DictReader(
            (data / EXPERIMENT_DIR / "adjudication_worksheet.tsv").open(encoding="utf-8"),
            delimiter="\t",
        )
    )
    labelled = [r for r in rows if r["label"] == "unambiguous"]
    v3_pathways = {r["key"] for r in labelled}
    v4_wrong = {k: [f for f in fs if f.kind == "wrong"] for k, fs in results.items()}
    v4_wrong = {k: v for k, v in v4_wrong.items() if v}

    print(f"\n{'=' * 96}")
    print(f"AGAINST THE {len(labelled)} HAND-LABELLED UNAMBIGUOUS v3 ERRORS")
    print("=" * 96)

    fixed, persists = [], []
    for row in labelled:
        (persists if row["key"] in v4_wrong else fixed).append(row)
    new = sorted(set(v4_wrong) - v3_pathways)

    print(f"\n  fixed    : {len(fixed)}/{len(labelled)}   no v4 'wrong' flag on that pathway")
    print(f"  persists : {len(persists)}/{len(labelled)}   a v4 'wrong' flag on the same pathway")
    print(f"  new      : {len(new)}          v4 'wrong' flags on pathways v3 got right")

    if fixed:
        print(f"\n{'-' * 96}\nFIXED\n{'-' * 96}")
        for row in fixed:
            print(f"  {row['key']}  {row['name']}")
            print(f"      was: {row['quote'][:110]}")
    if persists:
        print("\n" + "-" * 96)
        print("STILL FLAGGED (same pathway -- NOT necessarily the same error)")
        print("-" * 96)
        for row in persists:
            print(f"\n  {row['key']}  {row['name']}")
            print(f"      v3: {row['quote']}")
            for flag in v4_wrong[row["key"]]:
                print(f"      v4: {flag.quote}")
                print(f"          {flag.reason}")
    if new:
        print(f"\n{'-' * 96}\nNEW IN v4\n{'-' * 96}")
        for key in new:
            print(f"\n  {key}  {display_name(by_key[key])}")
            for flag in v4_wrong[key]:
                print(f"      {flag.quote}")
                print(f"      {flag.reason}")


def run_gate(args: argparse.Namespace, by_key: dict[str, Pathway]) -> int:
    """Run the calibration gate: does adjudicate-v1 reproduce the hand split?

    Args:
        args: Parsed arguments.
        by_key: Pathways by key.

    Returns:
        0, or 1 when the worksheet is unlabelled.
    """
    path = args.data / EXPERIMENT_DIR / "adjudication_worksheet.tsv"
    rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
    unlabelled = [r for r in rows if not r["label"]]
    if unlabelled:
        print(
            f"{len(unlabelled)} worksheet rows are unlabelled; the gate needs all of them",
            file=sys.stderr,
        )
        return 1

    ledger, client = build_client(
        args.data, args.model, ADJUDICATE_PROMPT_VERSION, ADJUDICATE_FORMAT, ADJUDICATE_KEY
    )
    requests = [
        Request(
            key=text_key(r["key"], r["quote"] + r["reason"]),
            system=ADJUDICATE_SYSTEM_PROMPT,
            user=render_adjudicate_message(by_key[r["key"]], r["quote"], r["reason"]),
        )
        for r in rows
    ]
    pending = [r for r in requests if r.key not in ledger]
    estimate = price(requests, pending, ledger, client, args.model, ADJUDICATE_SYSTEM_PROMPT, 200)
    print(f"\nCALIBRATION GATE: {len(rows)} claims, {len(pending)} to adjudicate")
    print(
        f"  cost: ${estimate.cached_dollars:,.2f} cached"
        f" / ${estimate.uncached_dollars:,.2f} ceiling"
    )
    if not args.submit:
        print("  nothing submitted; rerun with --submit")
        return 0
    if pending and client is not None:
        if not within_ceiling(estimate, args.max_dollars):
            print("  refusing: over --max-dollars", file=sys.stderr)
            return 1
        run_batch(client, pending, "adjudicate")

    agree = disagree = unread = 0
    splits: list[tuple[str, ...]] = []
    for row, request in zip(rows, requests, strict=True):
        completion = ledger.get(request.key)
        if completion is None:
            unread += 1
            continue
        try:
            label, basis = parse_label(completion.text)
        except ValueError as exc:
            print(f"  unreadable adjudication for row {row['n']}: {exc}", file=sys.stderr)
            unread += 1
            continue
        if label == row["label"]:
            agree += 1
        else:
            disagree += 1
            splits.append((row["n"], row["key"], row["name"], row["label"], label, basis))

    scored = agree + disagree
    print(f"\n{'=' * 96}\nCALIBRATION GATE RESULT\n{'=' * 96}\n")
    print(
        f"  claims adjudicated : {scored}/{len(rows)}"
        + (f"  ({unread} unreadable)" if unread else "")
    )
    print(
        f"  agreement          : {agree}/{scored}" + (f" ({agree / scored:.0%})" if scored else "")
    )
    hand = collections.Counter(r["label"] for r in rows)
    print(f"  hand split         : {hand['unambiguous']} unambiguous / {hand['arguable']} arguable")

    if splits:
        print(f"\n{'-' * 96}\nROWS WHERE THEY DIFFER\n{'-' * 96}")
        for n, key, name, mine, theirs, basis in splits:
            mark = "  <-- one of the two you flagged as borderline" if n in BORDERLINE else ""
            print(f"\n  row {n}  {key}  {name}{mark}")
            print(f"      you: {mine}    adjudicator: {theirs}")
            print(f"      basis: {basis[:240]}")
        borderline_hits = [n for n, *_ in splits if n in BORDERLINE]
        print(
            f"\n  of the {len(splits)} disagreements, {len(borderline_hits)} fall on the rows you "
            f"already called borderline ({', '.join(BORDERLINE)})."
        )
    print(f"\n  {LABEL_PROVENANCE.upper()}.")
    print("  The hand labels were drafted by a model and then reviewed and accepted by a human, so")
    print("  agreement here is partly two models agreeing. This gate is weaker evidence than a")
    print("  purely human split would be, and should be read that way.")
    return 0


def adjudicate_arm(args: argparse.Namespace, by_key: dict[str, Pathway], arm_name: str) -> int:
    """Split one arm's `wrong` flags into unambiguous and arguable.

    Uses the same ``adjudicate-v1`` prompt, model and cache namespace as the calibration gate, so
    the split applied to v4 is the one the gate measured against the hand labels. Whatever the gate
    says about that adjudicator's calibration applies here unchanged, and is printed with the
    result rather than left in a previous message.

    Args:
        args: Parsed arguments.
        by_key: Pathways by key.
        arm_name: Which arm's flags to adjudicate.

    Returns:
        0, or 1 when the arm has no flags file.
    """
    path = args.data / EXPERIMENT_DIR / "v4_flags.tsv"
    if not path.is_file():
        print(f"missing input: {path}", file=sys.stderr)
        return 1
    rows = [
        r
        for r in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t")
        if r["kind"] == "wrong" and r["arm"] == arm_name
    ]
    ledger, client = build_client(
        args.data, args.model, ADJUDICATE_PROMPT_VERSION, ADJUDICATE_FORMAT, ADJUDICATE_KEY
    )
    requests = [
        Request(
            key=text_key(r["key"], r["quote"] + r["reason"]),
            system=ADJUDICATE_SYSTEM_PROMPT,
            user=render_adjudicate_message(by_key[r["key"]], r["quote"], r["reason"]),
        )
        for r in rows
    ]
    pending = [r for r in requests if r.key not in ledger]
    estimate = price(requests, pending, ledger, client, args.model, ADJUDICATE_SYSTEM_PROMPT, 200)
    print(f"\nADJUDICATING {arm_name}: {len(rows)} wrong claims, {len(pending)} to send")
    print(
        f"  cost: ${estimate.cached_dollars:,.2f} cached"
        f" / ${estimate.uncached_dollars:,.2f} ceiling"
    )
    if not args.submit:
        print("  nothing submitted; rerun with --submit")
        return 0
    if pending and client is not None:
        if not within_ceiling(estimate, args.max_dollars):
            print("  refusing: over --max-dollars", file=sys.stderr)
            return 1
        run_batch(client, pending, "adjudicate")

    labelled: list[tuple[str, ...]] = []
    counts: collections.Counter = collections.Counter()
    for index, (row, request) in enumerate(zip(rows, requests, strict=True), start=1):
        completion = ledger.get(request.key)
        label, basis = "unread", ""
        if completion is not None:
            try:
                label, basis = parse_label(completion.text)
            except ValueError as exc:
                print(f"  unreadable adjudication for {row['key']}: {exc}", file=sys.stderr)
        counts[label] += 1
        labelled.append(
            (
                str(index),
                row["key"],
                display_name(by_key[row["key"]]),
                label,
                row["quote"],
                row["reason"],
                basis,
            )
        )

    print(f"\n{'=' * 96}")
    print(f"{arm_name.upper()} -- {len(rows)} WRONG CLAIMS, ADJUDICATED")
    print("=" * 96 + "\n")
    print(f"  unambiguous : {counts['unambiguous']}")
    print(f"  arguable    : {counts['arguable']}")
    if counts["unread"]:
        print(f"  unread      : {counts['unread']}")
    for n, key, name, label, quote, reason, basis in labelled:
        print(f"\n{'-' * 96}")
        print(f"{n:>2}. {key}  {name}   [{label}]")
        print(f"    claim : {quote}")
        print(f"    reason: {reason}")
        if basis:
            print(f"    basis : {basis[:200]}")
    write_tsv(
        args.data / EXPERIMENT_DIR / "v4_adjudicated.tsv",
        ("n", "key", "name", "label", "quote", "reason", "basis"),
        [tuple(cell(flatten(c)) for c in row) for row in labelled],
    )
    print(f"\n  {LABEL_PROVENANCE.upper()}.")
    print("  Whatever the calibration gate says about this adjudicator applies to these numbers")
    print("  unchanged: it was measured against labels a model drafted and a human accepted.")
    return 0


def repair_arm(
    args: argparse.Namespace,
    by_key: dict[str, Pathway],
    base: dict[str, Generated],
    flags: dict[str, tuple[Flag, ...]],
) -> tuple[dict[str, Generated], Estimate, int]:
    """Regenerate every flagged description with the verifier's objection appended.

    The rewrite replaces the original UNCONDITIONALLY. The alternative -- rewrite, re-check, and
    keep the original when the rewrite still flags -- would consult verify-v1 a third time, once to
    find the fault, once to decide whether the repair took, and once to score. That compounds the
    circularity this arm already carries rather than reducing it, so the repair is applied and the
    single scoring pass is left to judge it.

    Args:
        args: Parsed arguments.
        by_key: Pathways by key.
        base: The arm's descriptions before repair.
        flags: Flags per pathway key from the scoring pass over ``base``.

    Returns:
        The repaired descriptions (unflagged ones carried through unchanged), the estimate, and how
        many were actually repaired. The count is not decoration: a pricing run repairs nothing, and
        a caller that wrote the result out anyway would persist arm A's text under arm B's name and
        then "verify" it from cache, producing a perfect score for a pass that never ran.
    """
    flagged = {k: f for k, f in flags.items() if f and k in base}
    ledger, client = build_client(
        args.data, args.model, REPAIR_PROMPT_VERSION, ARMS["A plain"].response_format, "description"
    )
    requests = [
        Request(
            key=text_key(k, base[k].description),
            system=ARMS["A plain"].system,
            user=render_repair_message(by_key[k], base[k].description, flagged[k]),
        )
        for k in sorted(flagged)
    ]
    pending = [r for r in requests if r.key not in ledger]
    estimate = price(requests, pending, ledger, client, args.model, ARMS["A plain"].system, 420)
    print(f"\nREPAIR PASS: {len(flagged)} flagged of {len(base)}, {len(pending)} to send")
    print(
        f"  cost: ${estimate.cached_dollars:,.2f} cached"
        f" / ${estimate.uncached_dollars:,.2f} ceiling"
    )
    if args.submit and pending and client is not None:
        if not within_ceiling(estimate, args.max_dollars):
            print("  refusing: over --max-dollars", file=sys.stderr)
            return {}, estimate, 0
        run_batch(client, pending, "repair")
    if not args.submit:
        print("  nothing submitted; rerun with --submit")
        return {}, estimate, 0

    out: dict[str, Generated] = dict(base)
    repaired = 0
    for key, request in zip(sorted(flagged), requests, strict=True):
        completion = ledger.get(request.key)
        if completion is None:
            continue
        out[key] = Generated(key, completion.text, "")
        repaired += 1
    print(f"  {repaired}/{len(flagged)} descriptions repaired; the rest carried through")
    return out, estimate, repaired


def fresh_keys(data: Path, exclude: list[str], count: int, seed: int = 1) -> list[str]:
    """Draw a fresh sample by the same method as the original, excluding it.

    The original hundred was NOT stratified -- ``choose_pilot`` is a uniform draw from the described
    keys -- so "the same stratification" means the same uniform draw with the first hundred removed.
    A different seed is used so the two samples cannot coincide by construction.

    Args:
        data: The data directory.
        exclude: Keys already used.
        count: How many to draw.
        seed: The RNG seed.

    Returns:
        The chosen keys, sorted.
    """
    pool = sorted(set(read_descriptions(data / DESCRIPTIONS_TABLE)) - set(exclude))
    return sorted(random.Random(seed).sample(pool, min(count, len(pool))))


def carries_wrong(data: Path, arm: str, keys: list[str]) -> dict[str, bool]:
    """Whether each pathway's description carries at least one `wrong` claim.

    Args:
        data: The data directory.
        arm: ``v3`` for the baseline, otherwise an arm name in the flags table.
        keys: The pathways in scope.

    Returns:
        Pathway key to outcome, over exactly ``keys``.
    """
    if arm == "v3":
        path, key_col, arm_col = data / "pathway_verification_flags.tsv", "key", None
    else:
        path, key_col, arm_col = data / EXPERIMENT_DIR / "v4_flags.tsv", "key", "arm"
    wrong: set[str] = set()
    if path.is_file():
        for row in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"):
            if row["kind"] != "wrong":
                continue
            if arm_col and row[arm_col] != arm:
                continue
            wrong.add(row[key_col])
    return {k: k in wrong for k in keys}


def report_stats(args: argparse.Namespace, keys: list[str]) -> int:
    """Run the paired comparisons and print them.

    The arms describe the SAME pathways, so the comparison is paired: an unpaired test would
    discard that structure and answer a question nobody asked. The discordant counts are printed
    before the p-value because they are what the result actually rests on -- a net improvement built
    from many fixes and many new errors is a different finding from one built from fixes alone.

    Args:
        args: Parsed arguments.
        keys: The pathways in scope for this sample.

    Returns:
        0.
    """
    print(f"\n{'=' * 96}")
    print(f"PAIRED COMPARISON -- {args.sample} sample, n={len(keys)}")
    print("=" * 96)
    print("\n  outcome: does the description carry at least one 'wrong' claim, per frozen")
    print("  verify-v1. This is the metric the decision rule uses; it needs no adjudicator.\n")

    v3 = carries_wrong(args.data, "v3", keys)
    for arm in ("A plain", "B repair"):
        other = carries_wrong(args.data, arm, keys)
        if not any(other.values()) and not any(v3.values()):
            continue
        try:
            result = mcnemar(v3, other)
        except ValueError as exc:
            print(f"  {arm}: {exc}")
            continue
        print(f"\n  v3 vs {arm}")
        print("\n".join(describe(result, "v3", arm.split()[0])))
        if ARMS[arm].caveat:
            print(f"\n  {ARMS[arm].caveat}")
    return 0


def name_conditions(produced: dict[str, Generated], by_key: dict[str, Pathway]) -> tuple[str, str]:
    """Measure the two name done-conditions from the queue.

    Args:
        produced: One arm's output.
        by_key: Pathways by key.

    Returns:
        The shared-opening fraction and the verbatim-name fraction, rendered.
    """
    if not produced:
        return "-", "-"
    openings: dict[str, int] = {}
    for g in produced.values():
        opening = " ".join(g.description.lower().split()[:8])
        openings[opening] = openings.get(opening, 0) + 1
    shared = sum(n for n in openings.values() if n > 1)
    verbatim = sum(
        1 for g in produced.values() if display_name(by_key[g.key]).lower() in g.description.lower()
    )
    total = len(produced)
    return (
        f"{shared}/{total} ({shared / total:.0%})",
        f"{verbatim}/{total} ({verbatim / total:.0%})",
    )


def main(argv: list[str] | None = None) -> int:
    """Run one step of the prompt experiment."""
    parser = argparse.ArgumentParser(
        prog="run_prompt_experiment.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--step", type=int, default=2, choices=(2, 3), help="which step to run")
    parser.add_argument("--model", default="claude-opus-5", help="model (default: %(default)s)")
    parser.add_argument("--submit", action="store_true", help="actually call the API")
    parser.add_argument(
        "--max-dollars", type=float, default=4.0, help="per-run ceiling (default: %(default)s)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="run the paired comparisons over whatever has been scored",
    )
    parser.add_argument(
        "--sample",
        choices=("pilot", "fresh"),
        default="pilot",
        help="which hundred to act on: the original sample or a fresh draw excluding it",
    )
    parser.add_argument(
        "--adjudicate",
        action="store_true",
        help="split one arm's wrong claims into unambiguous and arguable",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="run the calibration gate: does adjudicate-v1 reproduce the hand-labelled split?",
    )
    parser.add_argument(
        "--arm",
        action="append",
        default=[],
        help="which arm to act on; repeatable. Defaults to every arm that has output",
    )
    parser.add_argument(
        "--collect",
        metavar="ARM=BATCH_ID",
        action="append",
        default=[],
        help="drain an already-submitted batch for one arm instead of submitting a new one; "
        "repeatable. Use after a run is interrupted between submission and collection, since "
        "resubmitting pays for the same batch twice",
    )
    args = parser.parse_args(argv)
    if not args.arm:
        args.arm = ["A plain"]

    collecting = dict(pair.split("=", 1) for pair in args.collect)
    unknown = [name for name in collecting if name not in ARMS]
    if unknown:
        print(f"unknown arm(s) in --collect: {', '.join(unknown)}", file=sys.stderr)
        print(f"known: {', '.join(ARMS)}", file=sys.stderr)
        return 1

    for required in (PATHWAY_TABLE, VERIFICATION_TABLE):
        if not (args.data / required).is_file():
            print(f"missing input: {args.data / required}", file=sys.stderr)
            return 1

    collection = PathwayCollection.from_tsv_text(
        (args.data / PATHWAY_TABLE).read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    keys = pilot_keys(args.data)
    if args.sample == "fresh":
        keys = fresh_keys(args.data, keys, len(keys))
    pathways = [by_key[k] for k in keys]
    print(f"\nV4 PROMPT EXPERIMENT -- STEP {args.step}  [{args.sample} sample]")
    if args.sample == "pilot":
        print(f"{len(keys)} pathways, the same hundred that produced 27 wrong claims under v3.\n")
    else:
        print(f"{len(keys)} pathways drawn by the same uniform method, none of them in the")
        print("original hundred. The v3 control on this sample is what says whether it is")
        print("simply an easier draw.\n")

    if args.stats:
        return report_stats(args, keys)
    if args.adjudicate:
        return adjudicate_arm(args, by_key, args.arm[0])
    if args.gate:
        return run_gate(args, by_key)
    suffix = "" if args.sample == "pilot" else f"_{args.sample}"
    if args.step == 3:
        return run_step_3(args, by_key, keys)

    produced: dict[str, dict[str, Generated]] = {}
    estimates: dict[str, Estimate] = {}
    for arm in ARMS.values():
        if arm.name == "B repair":
            # B is A plus a repair pass, so it starts from A's text by construction rather than by
            # a second generation that could differ. The repair pass itself is step 2b.
            continue
        if arm.name not in args.arm:
            # Arm C is parked. Generating it because the loop happens to reach it would spend money
            # on an arm the operator did not ask for.
            continue
        produced[arm.name], estimates[arm.name] = generate(
            args.data,
            arm,
            pathways,
            args.model,
            args.submit,
            args.max_dollars,
            collecting.get(arm.name),
        )

    print("COST BY ARM (marginal -- anything already cached is free)\n")
    rows = []
    total_cached = total_uncached = 0.0
    for name, estimate in estimates.items():
        rows.append(
            (
                name,
                f"{estimate.scope:,}",
                f"{estimate.pending:,}",
                f"{estimate.user_tokens:,.0f}",
                f"{estimate.system_tokens:,}",
                f"{estimate.output_tokens:,.0f}",
                f"${estimate.cached_dollars:,.2f}",
                f"${estimate.uncached_dollars:,.2f}",
            )
        )
        total_cached += estimate.cached_dollars
        total_uncached += estimate.uncached_dollars
    rows.append(
        ("B repair", "100", "-", "-", "-", "-", "shares A's generation", "repair pass is step 2b")
    )
    rows.append(("TOTAL", "", "", "", "", "", f"${total_cached:,.2f}", f"${total_uncached:,.2f}"))
    print_table(
        ("arm", "scope", "pending", "in/prompt", "system", "out/prompt", "if cached", "ceiling"),
        rows,
        align="<>>>>>>>",
    )
    print(f"\nper-run --max-dollars: ${args.max_dollars:,.2f}")

    if not args.submit and not collecting:
        print("\nnothing submitted; rerun with --submit")
        return 0

    for arm in ARMS.values():
        if arm.name in produced:
            path = write_arm(args.data, arm, produced[arm.name], args.model, suffix)
            print(f"{len(produced[arm.name]):,} descriptions -> {path}")

    print("\nNAME DONE-CONDITIONS (both should fall substantially versus v3)\n")
    condition_rows = []
    v3 = read_descriptions(args.data / DESCRIPTIONS_TABLE)
    v3_here = {k: Generated(k, v3[k], "") for k in keys if k in v3}
    for label, out in (("v3 baseline", v3_here), *produced.items()):
        shared, verbatim = name_conditions(out, by_key)
        condition_rows.append((label, shared, verbatim))
    print_table(
        ("arm", "share first 8 words", "contains name verbatim"), condition_rows, align="<>>"
    )

    show_sample(produced, by_key)
    print(f"\n{'=' * 96}")
    print("STOP. Read the ten above before any scoring runs. Step 3 is not started.")
    print("=" * 96)
    return 0


def run_step_3(args: argparse.Namespace, by_key: dict[str, Pathway], keys: list[str]) -> int:
    """Verify the named arms with the frozen protocol, and emit the adjudication worksheet.

    Args:
        args: Parsed arguments.
        by_key: Pathways by key.
        keys: The pilot pathway keys.

    Returns:
        0, or 1 when an arm's descriptions are missing.
    """
    path, count = write_worksheet(args.data)
    print(f"\nADJUDICATION WORKSHEET: {count} v3 wrong claims -> {path}")
    print("  Mark each row's `label` column `unambiguous` or `arguable`. The calibration gate")
    print("  compares adjudicate-v1 against those labels before it scores anything.\n")

    collecting = dict(pair.split("=", 1) for pair in args.collect)
    results: dict[str, dict[str, tuple[Flag, ...]]] = {}
    estimates: dict[str, Estimate] = {}
    for arm_name in args.arm:
        table = args.data / EXPERIMENT_DIR / f"v4_{arm_name.split()[0].lower()}.tsv"
        if ARMS[arm_name].repairs and not table.is_file():
            # Arm B is arm A plus a repair pass, so it is built here rather than generated: it must
            # start from arm A's exact text, and a second generation could not guarantee that.
            base_table = args.data / EXPERIMENT_DIR / "v4_a.tsv"
            flags_table = args.data / EXPERIMENT_DIR / "v4_flags.tsv"
            for required in (base_table, flags_table):
                if not required.is_file():
                    print(f"missing input: {required}", file=sys.stderr)
                    print("arm B needs arm A generated and verified first", file=sys.stderr)
                    return 1
            base = {
                r["key"]: Generated(r["key"], r["description"], "")
                for r in csv.DictReader(base_table.open(encoding="utf-8"), delimiter="\t")
                if r["key"] in by_key
            }
            base_flags: dict[str, list[Flag]] = {}
            for row in csv.DictReader(flags_table.open(encoding="utf-8"), delimiter="\t"):
                if row["arm"] == "A plain":
                    base_flags.setdefault(row["key"], []).append(
                        Flag(row["quote"], row["kind"], row["reason"])
                    )
            repaired, _estimate, count = repair_arm(
                args, by_key, base, {k: tuple(v) for k, v in base_flags.items()}
            )
            if not count:
                print("\nno descriptions were repaired; arm B is not written", file=sys.stderr)
                return 0
            write_arm(args.data, ARMS[arm_name], repaired, args.model)
        if not table.is_file():
            print(f"missing input: {table}", file=sys.stderr)
            print("run --step 2 first", file=sys.stderr)
            return 1
        rows = list(csv.DictReader(table.open(encoding="utf-8"), delimiter="\t"))
        produced = {
            r["key"]: Generated(r["key"], r["description"], r.get("checks", ""))
            for r in rows
            if r["key"] in by_key
        }
        results[arm_name], estimates[arm_name] = verify_arm(
            args.data,
            arm_name,
            produced,
            by_key,
            args.model,
            args.submit,
            args.max_dollars,
            collecting.get(arm_name),
        )

    print("VERIFICATION COST (frozen verify-v1 protocol; only the cache key differs)\n")
    print_table(
        ("arm", "scope", "pending", "in/prompt", "system", "out/prompt", "if cached", "ceiling"),
        [
            (
                name,
                f"{e.scope:,}",
                f"{e.pending:,}",
                f"{e.user_tokens:,.0f}",
                f"{e.system_tokens:,}",
                f"{e.output_tokens:,.0f}",
                f"${e.cached_dollars:,.2f}",
                f"${e.uncached_dollars:,.2f}",
            )
            for name, e in estimates.items()
        ],
        align="<>>>>>>>",
    )
    print(f"\nper-run --max-dollars: ${args.max_dollars:,.2f}")

    if not args.submit and not collecting:
        print("\nnothing submitted; rerun with --submit")
        return 0

    flag_rows: list[tuple[str, ...]] = []
    for arm_name, found in results.items():
        report_flags(arm_name, found, by_key)
        arm = ARMS[arm_name]
        if arm.caveat:
            print(f"\n  {arm.caveat}")
        for key in sorted(found):
            for flag in found[key]:
                flag_rows.append(
                    (
                        key,
                        arm_name,
                        flag.kind,
                        cell(flatten(flag.quote)),
                        cell(flatten(flag.reason)),
                    )
                )
    if flag_rows:
        out = args.data / EXPERIMENT_DIR / "v4_flags.tsv"
        held = merge_tsv(out, FLAG_COLUMNS, flag_rows, key=("key", "arm", "quote"))
        print(f"\n{held:,} flags -> {out}  (every arm previously scored is kept)")
    for found in results.values():
        compare_to_baseline(args.data, found, by_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
