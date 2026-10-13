#!/usr/bin/env python3
"""Run naming-c1 through the API, reproducing the reviewer's pilot of 11 Oct 2026.

The algorithm is :mod:`thema.naming_c1`, a tested port of
``data/experiments/naming_pilot_2026-10-11/spec/ALGORITHM.md`` sections 1-5. This script is only the
execution route: it builds the inputs, makes the calls, logs every one, and writes the names in the
pilot's own shape so the reviewer's fresh judges can score the two side by side (spec section 6).

**The prompts are the reviewer's two template files, used verbatim as system prompts.** They are
read from disk, never restated here, and their sha256 goes in the manifest. The per-item JSON is the
user message. ``naming.py`` and name-v5 are untouched.

**Spend is gated.** Nothing is sent without ``--submit``: the default run prices the work and stops,
and ``--max-dollars`` refuses above a ceiling. One call per theme per candidate and one per
back-match, as the spec requires -- no Batch API, so no batch discount applies and the estimate says
so. Model, temperature, prompt digests and the price basis are all recorded.

The pilot's answer keys are never read. This script opens the specification, the sample file and the
build; ``KEY_DO_NOT_SHARE*`` is not among them and a guard refuses if it ever is.

Usage::

    uv run scripts/name_themes_c1.py --themes 100            # price it and stop
    uv run scripts/name_themes_c1.py --themes 100 --submit    # run it
    uv run scripts/name_themes_c1.py --themes 100 --submit --max-dollars 40
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thema import llm, naming_c1  # noqa: E402

#: The pilot folder: specification, inputs, and the sample the equivalence run reuses.
PILOT = Path("data/experiments/naming_pilot_2026-10-11")

#: The build the pilot named on.
BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_c85")

#: Where the x2 universe's key list and centred vectors live.
SPACE = Path("data/ontology/v0.4-leaves-x2")

#: The model the pilot session was configured with.
PILOT_MODEL = "claude-opus-5-5"

#: Filename fragments this script must never open.
BARRED = ("KEY_DO_NOT_SHARE",)

#: N1's reply. ``nameable`` is a boolean and is therefore also the response key: ``extract_text``
#: hands back the whole object only when the keyed field is not a string, the same mechanism
#: ``naming.py`` documents. With every field a string the rest of the reply is unrecoverable.
N1_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "theme_id": {"type": "string"},
            "nameable": {"type": "boolean"},
            "core": {"type": "string"},
            "qualifier": {"type": "string"},
            "name": {"type": "string"},
            "rationale": {"type": "string"},
        },
        "required": ["theme_id", "nameable", "core", "qualifier", "name", "rationale"],
        "additionalProperties": False,
    },
}
N1_RESPONSE_KEY = "nameable"

#: S1's reply, exactly the two fields the template asks for. ``choice`` is a string, so the client
#: hands back the letter itself, which is all selection needs; the full reply is in the log.
S1_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "item_id": {"type": "string"},
            "choice": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
        },
        "required": ["item_id", "choice"],
        "additionalProperties": False,
    },
}
S1_RESPONSE_KEY = "choice"

#: Prompt version strings, which are part of the ledger's cache key. Bumping a prompt must bump
#: these or a changed prompt would be served an old reply.
N1_VERSION = "naming-c1-N1"
S1_VERSION = "naming-c1-S1"

#: Input characters per token, MEASURED in this repo rather than assumed: the v4 description system
#: prompt is 6,946 characters and billed 2,511 cached input tokens on the 10,801-call v4 run, so
#: 2.766. Cache-block overhead makes the true ratio slightly higher, which makes a token count
#: derived from it an over-estimate -- the safe direction for a spend gate.
CHARS_PER_TOKEN = 6946 / 2511

#: Output tokens per call, thinking included, taken from this repo's opus-5 ledgers. N1 writes a
#: name plus a rationale, about 450 characters, so it is bracketed by ``adjudicate-v1`` (401
#: characters: median 255, p90 411) and the v4 descriptions (969 characters: median 366, p90 412).
#: S1 returns one letter and is bracketed by ``verify-v1`` (276 characters: median 165, p90 419).
N1_OUTPUT_TOKENS = 420
S1_OUTPUT_TOKENS = 250

#: The same two, at the p90 of those ledgers, for the ceiling figure.
N1_OUTPUT_CEILING = 700
S1_OUTPUT_CEILING = 500


def sha256_text(text: str) -> str:
    """Hex sha256 of a string.

    Args:
        text: The text.

    Returns:
        The digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def assert_nothing_barred(paths: Sequence[Path]) -> None:
    """Refuse if any path is an answer key.

    Args:
        paths: Every path this run reads.

    Raises:
        ValueError: If one of them is barred.
    """
    bad = [p for p in paths if any(fragment in p.name for fragment in BARRED)]
    if bad:
        raise ValueError(f"this script must not open {[p.name for p in bad]}")


def tokens_from_chars(text: str) -> int:
    """Input tokens a string will bill, from its length.

    Args:
        text: The message.

    Returns:
        The estimated token count, rounded up.
    """
    return int(len(text) / CHARS_PER_TOKEN + 0.5)


def user_message(item: Mapping[str, object]) -> str:
    """One item serialised as the user message, in the pilot's own rendering.

    The pilot wrote its batches with ``json.dump(..., indent=1)``; one item per call is the same
    text for one item.

    Args:
        item: The N1 or S1 item.

    Returns:
        The user message.
    """
    return json.dumps(item, indent=1)


def log_call(directory: Path, name: str, payload: Mapping[str, object]) -> None:
    """Write one call's request and response.

    The API key is never part of ``payload`` and never reaches a log: only the system prompt's
    digest, the user message, and what came back.

    Args:
        directory: The log directory.
        name: The file stem.
        payload: What to record.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def estimate(
    n1_messages: Sequence[str],
    n1_system: str,
    s1_system: str,
    themes: int,
    model: str,
    price_as: str,
) -> dict[str, object]:
    """Price the run both ways, without sending anything.

    S1's messages cannot be built before N1 has produced names, so S1's input size is taken from the
    pilot's own selection items for the same themes -- measured text, not a guess.

    Args:
        n1_messages: Every N1 user message, already built.
        n1_system: The N1 system prompt.
        s1_system: The S1 system prompt.
        themes: How many themes are in scope.
        model: The model that will run.
        price_as: Which :data:`llm.PRICES` entry to price with.

    Returns:
        The estimate, for printing and for the manifest.
    """
    rate_in, rate_out = llm.PRICES[price_as]
    n1_user = [tokens_from_chars(message) for message in n1_messages]
    n1_system_tokens = tokens_from_chars(n1_system)
    s1_system_tokens = tokens_from_chars(s1_system)

    selection_items: list[int] = []
    for path in sorted(PILOT.glob("selection/main_sel_*.json")):
        if path.name.endswith(".out.json"):
            continue
        for item in json.loads(path.read_text()):
            selection_items.append(tokens_from_chars(user_message(item)))
    s1_user_mean = sum(selection_items) / len(selection_items) if selection_items else 0.0
    s1_calls = len(n1_messages)  # one back-match per nameable candidate; the pilot refused none

    def dollars(cached_system: bool, ceiling: bool) -> float:
        n1_out = N1_OUTPUT_CEILING if ceiling else N1_OUTPUT_TOKENS
        s1_out = S1_OUTPUT_CEILING if ceiling else S1_OUTPUT_TOKENS
        n1_in = sum(n1_user) + n1_system_tokens * (1 if cached_system else len(n1_user))
        n1_cached = n1_system_tokens * (len(n1_user) - 1) * 0.1 if cached_system else 0.0
        s1_in = s1_user_mean * s1_calls + s1_system_tokens * (1 if cached_system else s1_calls)
        s1_cached = s1_system_tokens * (s1_calls - 1) * 0.1 if cached_system else 0.0
        billed_in = n1_in + n1_cached + s1_in + s1_cached
        billed_out = n1_out * len(n1_user) + s1_out * s1_calls
        return (billed_in * rate_in + billed_out * rate_out) / 1e6

    return {
        "themes": themes,
        "n1_calls": len(n1_messages),
        "s1_calls_max": s1_calls,
        "calls_max": len(n1_messages) + s1_calls,
        "n1_system_tokens": n1_system_tokens,
        "s1_system_tokens": s1_system_tokens,
        "n1_user_tokens_mean": round(sum(n1_user) / len(n1_user), 1) if n1_user else 0,
        "n1_user_tokens_max": max(n1_user) if n1_user else 0,
        "s1_user_tokens_mean": round(s1_user_mean, 1),
        "n1_output_tokens_assumed": N1_OUTPUT_TOKENS,
        "s1_output_tokens_assumed": S1_OUTPUT_TOKENS,
        "model": model,
        "price_as": price_as,
        "rates_per_mtok": {"input": rate_in, "output": rate_out},
        "batch_discount_applied": False,
        "central_dollars": round(dollars(cached_system=True, ceiling=False), 2),
        "uncached_system_dollars": round(dollars(cached_system=False, ceiling=False), 2),
        "ceiling_dollars": round(dollars(cached_system=False, ceiling=True), 2),
        "basis": (
            f"input tokens from measured characters at {CHARS_PER_TOKEN:.3f} chars/token (this "
            "repo's v4 system prompt: 6,946 chars billed as 2,511 cached input tokens over "
            "10,801 calls); output tokens from this repo's claude-opus-5 ledgers, thinking "
            "included; list price, no batch discount"
        ),
    }


def report(figures: Mapping[str, object], ceiling: float | None) -> bool:
    """Print the estimate and say whether it is under the ceiling.

    Args:
        figures: The estimate.
        ceiling: The refusal ceiling in dollars, or None for no ceiling.

    Returns:
        True if the run may proceed.
    """
    print("COST ESTIMATE (nothing has been sent)")
    print(f"  themes                 {figures['themes']:,}")
    print(f"  N1 calls               {figures['n1_calls']:,}  (3 per theme)")
    print(f"  S1 calls, at most      {figures['s1_calls_max']:,}  (1 per nameable candidate)")
    print(f"  calls, at most         {figures['calls_max']:,}")
    print(f"  model                  {figures['model']}  priced as {figures['price_as']}")
    print(f"  rates $/Mtok           in {figures['rates_per_mtok']['input']}, "
          f"out {figures['rates_per_mtok']['output']}  (no batch discount)")
    print(f"  N1 input tokens        system {figures['n1_system_tokens']:,}, "
          f"user mean {figures['n1_user_tokens_mean']:,}, max {figures['n1_user_tokens_max']:,}")
    print(f"  S1 input tokens        system {figures['s1_system_tokens']:,}, "
          f"user mean {figures['s1_user_tokens_mean']:,}")
    print(f"  output tokens assumed  N1 {figures['n1_output_tokens_assumed']}, "
          f"S1 {figures['s1_output_tokens_assumed']}  (thinking included)")
    print()
    print(f"  CENTRAL                ${figures['central_dollars']:.2f}   system prompt cached")
    print(f"  system prompt uncached ${figures['uncached_system_dollars']:.2f}")
    print(f"  CEILING                ${figures['ceiling_dollars']:.2f}   "
          "uncached system and p90 output")
    print()
    print(f"  basis: {figures['basis']}")
    if ceiling is not None and float(figures["ceiling_dollars"]) > ceiling:
        print(f"\n  REFUSED: the ceiling ${figures['ceiling_dollars']:.2f} is above "
              f"--max-dollars ${ceiling:.2f}")
        return False
    return True


def run_n1(
    client: llm.LLMClient,
    items: Sequence[tuple[str, int, dict[str, object]]],
    system: str,
    log: Path,
) -> dict[tuple[str, int], dict[str, object]]:
    """Call N1 once per theme per candidate and return the parsed replies.

    Args:
        client: The caching client.
        items: ``(theme, candidate_index, item)`` triples.
        system: The N1 system prompt, used verbatim.
        log: Where to write each call.

    Returns:
        ``(theme, candidate_index)`` to the model's object.
    """
    requests = [
        llm.Request(key=f"n1:{theme}:{index}", system=system, user=user_message(item))
        for theme, index, item in items
    ]
    completions = client.complete_all(requests)
    digest = sha256_text(system)
    out: dict[tuple[str, int], dict[str, object]] = {}
    for (theme, index, _built), request, completion in zip(
        items, requests, completions, strict=True
    ):
        reply = json.loads(completion.text)
        out[(theme, index)] = reply
        log_call(
            log / "n1",
            f"{theme}_c{index:02d}",
            {
                "key": request.key,
                "system_sha256": digest,
                "user": request.user,
                "model": completion.model,
                "response": reply,
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cache_read_tokens": completion.cache_read_tokens,
                "stop_reason": completion.stop_reason,
                "request_id": completion.request_id,
            },
        )
    return out


def run_s1(
    client: llm.LLMClient,
    items: Sequence[tuple[str, int, str, dict[str, object], str]],
    system: str,
    log: Path,
) -> dict[tuple[str, int], bool]:
    """Back-match one item per nameable candidate and return whether each picked its own theme.

    Args:
        client: The caching client.
        items: ``(theme, candidate_index, item_id, item, correct_letter)`` tuples.
        system: The S1 system prompt, used verbatim.
        log: Where to write each call.

    Returns:
        ``(theme, candidate_index)`` to whether the judge chose the theme.
    """
    requests = [
        llm.Request(key=f"s1:{theme}:{index}", system=system, user=user_message(item))
        for theme, index, _item_id, item, _letter in items
    ]
    completions = client.complete_all(requests)
    digest = sha256_text(system)
    out: dict[tuple[str, int], bool] = {}
    for (theme, index, item_id, _item, letter), request, completion in zip(
        items, requests, completions, strict=True
    ):
        choice = completion.text.strip()
        out[(theme, index)] = choice == letter
        log_call(
            log / "s1",
            f"{theme}_c{index:02d}",
            {
                "key": request.key,
                "item_id": item_id,
                "system_sha256": digest,
                "user": request.user,
                "model": completion.model,
                "choice": choice,
                "correct_letter": letter,
                "correct": choice == letter,
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cache_read_tokens": completion.cache_read_tokens,
                "stop_reason": completion.stop_reason,
                "request_id": completion.request_id,
            },
        )
    return out


def main(argv: list[str] | None = None) -> int:
    """Price the run, and with ``--submit`` run it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, default=PILOT)
    parser.add_argument("--build", type=Path, default=BUILD)
    parser.add_argument("--space", type=Path, default=SPACE)
    parser.add_argument("--descriptions", type=Path, default=Path("data/pathway_descriptions.tsv"))
    parser.add_argument("--pathways", type=Path, default=Path("data/pathways.tsv"),
                        help="the universe the embeddings are verified against")
    parser.add_argument("--themes", type=int, default=100,
                        help="how many of the pilot sample's themes, in file order")
    parser.add_argument("--model", default=PILOT_MODEL,
                        help=f"the pilot used {PILOT_MODEL}; it must be a key of llm.MODELS")
    parser.add_argument("--price-as", default=None,
                        help="which llm.PRICES entry to price with; defaults to --model")
    parser.add_argument("--out", type=Path, default=None,
                        help="output directory; defaults to <pilot>/api_run")
    parser.add_argument("--ledger", type=Path, default=Path("data/cache/naming_c1"))
    parser.add_argument("--max-dollars", type=float, default=None)
    parser.add_argument("--submit", action="store_true",
                        help="actually send the calls; without it nothing is sent")
    args = parser.parse_args(argv)

    spec = args.pilot / "spec"
    sample_file = args.pilot / "inputs/sample_and_confusables.json"
    n1_file, s1_file = spec / "N1_namer.md", spec / "S1_backmatch.md"
    opened = [sample_file, n1_file, s1_file, args.descriptions, args.pathways,
              args.build / "members.tsv", args.build / "nodes.tsv"]
    assert_nothing_barred(opened)

    n1_system = n1_file.read_text(encoding="utf-8")
    s1_system = s1_file.read_text(encoding="utf-8")
    sample = json.loads(sample_file.read_text())
    themes = list(sample["sample"])[: args.themes]
    stored = sample["confusables"]

    keys, vectors = naming_c1.load_space(args.space, args.pathways)
    universe = naming_c1.Universe.load(args.build, args.descriptions, keys, vectors)
    print(f"NAMING-C1 over {len(themes):,} themes from {sample_file}")
    print(f"  build {args.build}  ({len(universe.members):,} themes, "
          f"{len(universe.eligible()):,} eligible)")
    print(f"  N1 prompt {n1_file}  sha256 {sha256_text(n1_system)[:16]}")
    print(f"  S1 prompt {s1_file}  sha256 {sha256_text(s1_system)[:16]}")

    rebuilt = {theme: universe.confusables(theme) for theme in themes}
    drift = [theme for theme in themes if rebuilt[theme] != stored[theme]]
    if drift:
        raise ValueError(
            f"{len(drift)} themes' confusables differ from the pilot's stored list, e.g. "
            f"{drift[:3]}. The build or the universe has moved; do not run until that is resolved."
        )
    print(f"  confusables rebuilt and identical to the pilot's for all {len(themes):,} themes")

    items = [
        (theme, index, naming_c1.namer_item(universe, theme, index, rebuilt[theme]))
        for theme in themes
        for index in (0, 1, 2)
    ]
    figures = estimate(
        [user_message(item) for _t, _i, item in items],
        n1_system, s1_system, len(themes), args.model, args.price_as or args.model,
    )
    print()
    allowed = report(figures, args.max_dollars)

    # CLAUDE.md: a prompt is never sent before Aviyah has seen the exact text. The estimate run
    # writes the first call of each kind out in full -- system prompt and user message as they
    # would be transmitted -- so approving the price and approving the wording are separate acts
    # she can actually perform.
    out = args.out or (args.pilot / "api_run")
    out.mkdir(parents=True, exist_ok=True)
    first_theme, first_index, first_item = items[0]
    sample_selection = json.loads(
        next(
            path for path in sorted((args.pilot / "selection").glob("main_sel_*.json"))
            if not path.name.endswith(".out.json")
        ).read_text()
    )[0]
    (out / "example_request.json").write_text(
        json.dumps(
            {
                "note": "the exact text that would be sent; no call has been made",
                "N1": {
                    "model": args.model,
                    "system": n1_system,
                    "system_sha256": sha256_text(n1_system),
                    "user": user_message(first_item),
                    "user_for": {"theme": first_theme, "candidate_index": first_index},
                    "response_format": N1_FORMAT,
                },
                "S1": {
                    "model": args.model,
                    "system": s1_system,
                    "system_sha256": sha256_text(s1_system),
                    "user": user_message(sample_selection),
                    "user_for": "one of the pilot's own selection items, shown for its shape",
                    "response_format": S1_FORMAT,
                },
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n  exact text that would be sent -> {out / 'example_request.json'}")
    if not args.submit:
        print("  --submit was not passed: NO API CALL WAS MADE.")
        return 0
    if not allowed:
        return 1

    log = out / "log"
    args.ledger.mkdir(parents=True, exist_ok=True)

    n1_ledger = llm.Ledger.open(args.ledger, args.model, N1_VERSION)
    n1_client = llm.LLMClient(
        args.model, N1_VERSION, n1_ledger,
        response_format=N1_FORMAT, response_key=N1_RESPONSE_KEY,
    )
    replies = run_n1(n1_client, items, n1_system, log)

    s1_ledger = llm.Ledger.open(args.ledger, args.model, S1_VERSION)
    s1_client = llm.LLMClient(
        args.model, S1_VERSION, s1_ledger,
        response_format=S1_FORMAT, response_key=S1_RESPONSE_KEY,
    )
    s1_items: list[tuple[str, int, str, dict[str, object], str]] = []
    for position, (theme, index, _namer_item) in enumerate(items):
        reply = replies[(theme, index)]
        if not reply.get("nameable", True):
            continue
        item_id = f"A{position:04d}"
        item, letter = naming_c1.backmatch_item(
            universe, theme, str(reply["name"]), f"S{index}", item_id, rebuilt[theme]
        )
        s1_items.append((theme, index, item_id, item, letter))
    correct = run_s1(s1_client, s1_items, s1_system, log)

    by_theme: dict[str, dict[int, dict[str, object]]] = defaultdict(dict)
    for (theme, index), reply in replies.items():
        by_theme[theme][index] = reply
    finals = {
        theme: naming_c1.select(
            replies_for, {index: correct.get((theme, index), False) for index in replies_for}
        )
        for theme, replies_for in by_theme.items()
    }

    confusables = {theme: list(rebuilt[theme]) for theme in themes}
    rounds: list[dict[str, object]] = []
    for round_number in range(1, naming_c1.MAX_DEDUP_ROUNDS + 1):
        collisions = naming_c1.duplicate_names(finals)
        rounds.append({"round": round_number, "collisions": collisions})
        if not collisions:
            break
        print(f"\n  uniqueness round {round_number}: {len(collisions)} colliding name(s)")
        dedup, confusables = naming_c1.dedup_items(universe, finals, confusables)
        dedup_replies = run_n1(
            n1_client, [(item["theme_id"], index, item) for index, item in dedup],
            n1_system, log,
        )
        dedup_s1: list[tuple[str, int, str, dict[str, object], str]] = []
        for position, ((theme, index), reply) in enumerate(sorted(dedup_replies.items())):
            if not reply.get("nameable", True):
                continue
            item_id = f"R{round_number}{position:03d}"
            item, letter = naming_c1.backmatch_item(
                universe, theme, str(reply["name"]), f"S{index}", item_id, confusables[theme]
            )
            dedup_s1.append((theme, index, item_id, item, letter))
        dedup_correct_raw = run_s1(s1_client, dedup_s1, s1_system, log)
        grouped: dict[str, dict[int, dict[str, object]]] = defaultdict(dict)
        for (theme, index), reply in dedup_replies.items():
            grouped[theme][index] = reply
        grouped_correct: dict[str, dict[int, bool]] = defaultdict(dict)
        for (theme, index), ok in dedup_correct_raw.items():
            grouped_correct[theme][index] = ok
        finals = naming_c1.apply_uniqueness(finals, grouped, grouped_correct, round_number)

    residual = naming_c1.duplicate_names(finals)
    payload = {
        "main": finals,
        "duplicates": rounds[0]["collisions"],
        "duplicates_after_dedup": residual,
    }
    (out / "final_names_api.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    completions = tuple(n1_ledger.completions()) + tuple(s1_ledger.completions())
    spent = llm.spend(completions, args.price_as or args.model)
    manifest = {
        "written_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "algorithm": "naming-c1",
        "spec": str(spec / "ALGORITHM.md"),
        "spec_sha256": sha256_text((spec / "ALGORITHM.md").read_text(encoding="utf-8")),
        "model": args.model,
        "model_note": (
            "the id the pilot session was configured with; whether it resolves at the provider was "
            "not verified before the run, because verifying it means an API call"
        ),
        "temperature": "not set; provider default. Adaptive thinking at effort low, per llm.MODELS",
        "thinking": llm.MODELS[args.model],
        "max_tokens": llm.MAX_TOKENS,
        "price_as": args.price_as or args.model,
        "price_basis": (
            "claude-opus-5-5 rates are ASSUMED EQUAL TO claude-opus-5 and are not verified"
            if (args.price_as or args.model) == PILOT_MODEL
            else "list price for the named model"
        ),
        "prompts": {
            "N1": {"path": str(n1_file), "sha256": sha256_text(n1_system),
                   "version": N1_VERSION, "used": "verbatim as the system prompt"},
            "S1": {"path": str(s1_file), "sha256": sha256_text(s1_system),
                   "version": S1_VERSION, "used": "verbatim as the system prompt"},
        },
        "response_formats": {"N1": N1_FORMAT, "S1": S1_FORMAT},
        "build": str(args.build),
        "space": str(args.space),
        "themes": len(themes),
        "theme_ids": themes,
        "n1_calls": len(items),
        "s1_calls": len(s1_items),
        "unnameable": sum(1 for v in finals.values() if v["unnameable"]),
        "low_confidence": sum(1 for v in finals.values() if v.get("low_confidence")),
        "uniqueness_rounds": rounds,
        "residual_duplicates": residual,
        "estimate": figures,
        "actual_spend": spent,
        "files_read": [str(p) for p in opened],
        "answer_keys_read": "none; KEY_DO_NOT_SHARE* is barred and guarded",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\n  -> {out / 'final_names_api.json'}")
    print(f"  -> {out / 'manifest.json'}")
    print(f"  spent ${spent['total']:.2f}; residual duplicates {residual or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
