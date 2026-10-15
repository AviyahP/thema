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

**Offline mode** (``--offline``) is the same algorithm with the model calls taken out: the reviewer
runs the namers and judges as in-session subagents, and this script builds every input and makes
every decision. No client is built and **no API key is read**. The stages hand off through files:

``n1``
    write the namer items for 3 candidate slots;
``s1``
    read the namer replies, validate them, write the back-match items and their answer keys;
``select``
    read the back-match judgements, apply :func:`~thema.naming_c1.select`, write the dedup items;
``final``
    read those judgements, apply :func:`~thema.naming_c1.apply_uniqueness`, write the names.

Offline mode writes **only** under ``--out``; it never writes into the reviewer's own folders.
``tests/test_naming_c1.py`` proves the four stages reproduce the 11 Oct pilot's files byte for byte.

Usage::

    uv run scripts/name_themes_c1.py --themes 100            # price it and stop
    uv run scripts/name_themes_c1.py --themes 100 --submit    # run it
    uv run scripts/name_themes_c1.py --offline n1             # no API, no key, no client
    uv run scripts/name_themes_c1.py --offline s1 --raw .../raw
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
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

#: Where offline mode writes. Never inside the reviewer's own directories.
OFFLINE_OUT = Path("data/experiments/naming_O50_2026-10-14/code_run")

#: The adopted working build, which offline mode names by default.
O50_BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_O50")

#: Themes per namer file per slot, and the three candidate slots.
BATCH = 25
SLOTS = (0, 1, 2)

#: Items per back-match file. The pilot used 50 for its main arm and 45 for the re-run arm.
S1_BATCH = 50

#: Theme order is shuffled with this seed before batching, which is what the pilot does.
ORDER_SEED = 7

#: The back-match item order is shuffled with ``99 + candidate offset``, as the pilot does.
S1_ORDER_SEED = 99

#: The uniqueness round's own back-match shuffle seed.
DEDUP_ORDER_SEED = 5

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


# ------------------------------------------------------------------ offline mode
#
# The reviewer answers; this code decides. Every stage is deterministic given the replies, and every
# shuffle, seed and filename convention is the pilot's -- which is why the equivalence test can hold
# the four stages to reproducing the 11 Oct pilot's files byte for byte.


def write_json(path: Path, payload: object, indent: int = 1) -> None:
    r"""Write JSON the way the pilot's scripts write it.

    Two details are not cosmetic, because the equivalence check is on bytes. ``indent=1`` is what
    the pilot's ``json.dump(..., indent=1)`` produced, and ``ensure_ascii`` is left at its default
    **True**, so a Greek letter or an en-dash in a pathway title is escaped as ``\\uXXXX`` exactly
    as the pilot escaped it. Writing the same text unescaped differs in half the files.

    Args:
        path: Destination.
        payload: What to write.
        indent: Indent level.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=indent), encoding="utf-8")


def eligible_themes(universe: naming_c1.Universe) -> list[str]:
    """The themes naming-c1 is in scope for: 3 to 200 members, sorted.

    Args:
        universe: The build.

    Returns:
        Theme ids, sorted.
    """
    return sorted(
        node
        for node, keys in universe.members.items()
        if naming_c1.MIN_SIZE <= len(keys) <= naming_c1.MAX_SIZE
    )


def batched_order(themes: Sequence[str], seed: int = ORDER_SEED) -> list[str]:
    """The themes in the order the namer files take them.

    Args:
        themes: Theme ids.
        seed: The shuffle seed; the pilot uses 7.

    Returns:
        The shuffled order.
    """
    order = list(themes)
    random.Random(seed).shuffle(order)
    return order


def stage_n1(
    universe: naming_c1.Universe,
    themes: Sequence[str],
    confusables: Mapping[str, Sequence[str]],
    out: Path,
    *,
    prefix: str = "namer",
    batch: int = BATCH,
    width: int = 3,
    candidate_offset: int = 0,
) -> dict[str, object]:
    """Write the namer items for three candidate slots.

    Args:
        universe: The build.
        themes: Themes to name, in the order the batches take them.
        confusables: Theme to its confusables.
        out: Output directory.
        prefix: Filename prefix.
        batch: Themes per file.
        width: Zero-padding of the batch number. The pilot used 2, the O50 run 3.
        candidate_offset: Added to the slot to make the candidate index; the pilot's re-run arm
            uses 10, which changes the seeds but not the filenames.

    Returns:
        Counts, for the caller to print.
    """
    files = 0
    items = 0
    for slot in SLOTS:
        for start in range(0, len(themes), batch):
            block = themes[start : start + batch]
            payload = [
                naming_c1.namer_item(
                    universe, theme, slot + candidate_offset, confusables[theme]
                )
                for theme in block
            ]
            name = f"{prefix}_slot{slot}_b{start // batch + 1:0{width}d}.json"
            write_json(out / name, payload)
            files += 1
            items += len(payload)
    return {"files": files, "items": items, "themes": len(themes), "slots": len(SLOTS)}


def read_namer_replies(
    raw: Path, prefix: str = "namer"
) -> tuple[dict[tuple[str, int], dict[str, object]], list[Path]]:
    """Every namer reply, keyed by ``(theme, slot)``.

    Args:
        raw: Directory of ``<prefix>_slot<N>_b<NNN>.out.json`` files.
        prefix: Filename prefix.

    Returns:
        ``(replies, files)``.

    Raises:
        ValueError: If two files answer the same theme and slot.
    """
    out: dict[tuple[str, int], dict[str, object]] = {}
    files = sorted(raw.glob(f"{prefix}_slot*_b*.out.json"))
    for path in files:
        slot = int(path.name.split("_slot")[1][0])
        for reply in json.loads(path.read_text()):
            key = (reply["theme_id"], slot)
            if key in out:
                raise ValueError(f"{path.name}: {key} is answered more than once")
            out[key] = reply
    return out, files


def validate_replies(
    expected: Sequence[tuple[str, int]],
    replies: Mapping[tuple[str, int], Mapping[str, object]],
) -> list[str]:
    """Check every expected item is answered exactly once, with a usable schema.

    Returns failures rather than raising, so a run can report all of them at once instead of
    stopping at the first.

    Args:
        expected: Every ``(theme, slot)`` the inputs asked for.
        replies: What came back.

    Returns:
        One line per failure, empty if there are none.
    """
    failures: list[str] = []
    wanted = set(expected)
    for key in sorted(wanted - set(replies)):
        failures.append(f"missing: theme {key[0]} slot {key[1]}")
    for key in sorted(set(replies) - wanted):
        failures.append(f"unexpected: theme {key[0]} slot {key[1]} was not asked for")
    for key in sorted(wanted & set(replies)):
        reply = replies[key]
        where = f"theme {key[0]} slot {key[1]}"
        if reply.get("theme_id") != key[0]:
            failures.append(f"{where}: theme_id is {reply.get('theme_id')!r}")
        if not isinstance(reply.get("nameable"), bool):
            failures.append(f"{where}: nameable is {reply.get('nameable')!r}, not a boolean")
            continue
        if reply["nameable"] and not str(reply.get("name", "")).strip():
            failures.append(f"{where}: nameable but the name is empty")
        if not reply["nameable"] and not str(reply.get("rationale", "")).strip():
            failures.append(f"{where}: not nameable but no rationale")
    return failures


def stage_s1(
    universe: naming_c1.Universe,
    replies: Mapping[tuple[str, int], Mapping[str, object]],
    confusables: Mapping[str, Sequence[str]],
    out: Path,
    *,
    run: str = "main",
    candidate_offset: int = 0,
    batch: int = S1_BATCH,
) -> dict[str, object]:
    """Write the back-match items and their answer key.

    The item order, the id format and the per-item seed are the pilot's: candidates sorted by
    ``(theme, slot)``, shuffled with ``99 + offset``, ids ``<R><NNNN>`` numbered over **every**
    candidate including the ones skipped for being unnameable, so the ids carry gaps exactly where
    the pilot's do.

    Args:
        universe: The build.
        replies: Namer replies by ``(theme, slot)``.
        confusables: Theme to its confusables.
        out: Output directory.
        run: Run tag; the first letter prefixes the item ids and names the key file.
        candidate_offset: Added to the slot for the seed, as the re-run arm does.
        batch: Items per file.

    Returns:
        Counts, for the caller to print.
    """
    order = sorted(replies)
    random.Random(S1_ORDER_SEED + candidate_offset).shuffle(order)
    items: list[dict[str, object]] = []
    key: dict[str, dict[str, object]] = {}
    skipped = 0
    for position, (theme, slot) in enumerate(order):
        reply = replies[(theme, slot)]
        if not reply.get("nameable", True):
            skipped += 1
            continue
        item_id = f"{run[0].upper()}{position:04d}"
        item, letter = naming_c1.backmatch_item(
            universe, theme, str(reply["name"]), f"S{slot + candidate_offset}",
            item_id, confusables[theme],
        )
        items.append(item)
        key[item_id] = {"theme": theme, "cand": slot, "correct": letter}
    write_json(out / f"KEY_DO_NOT_SHARE_{run}.json", key, indent=None)
    files = 0
    for start in range(0, len(items), batch):
        write_json(out / f"{run}_sel_{start // batch + 1:02d}.json", items[start : start + batch])
        files += 1
    return {"items": len(items), "files": files, "unnameable_skipped": skipped,
             "key": f"KEY_DO_NOT_SHARE_{run}.json"}


def read_choices(directory: Path, pattern: str) -> dict[str, str]:
    """Judges' letter choices, keyed by item id.

    Args:
        directory: Where the ``.out.json`` files are.
        pattern: Glob for them.

    Returns:
        Item id to letter.
    """
    out: dict[str, str] = {}
    for path in sorted(directory.glob(pattern)):
        for reply in json.loads(path.read_text()):
            out[reply["item_id"]] = reply["choice"]
    return out


def correctness(
    key: Mapping[str, Mapping[str, object]], choices: Mapping[str, str]
) -> dict[str, dict[int, bool]]:
    """Whether each candidate's back-match picked its own theme.

    Args:
        key: The answer key written by :func:`stage_s1`.
        choices: The judges' choices.

    Returns:
        Theme to candidate index to whether it was correct.
    """
    out: dict[str, dict[int, bool]] = defaultdict(dict)
    for item_id, entry in key.items():
        theme, cand = str(entry["theme"]), int(entry["cand"])
        out[theme][cand] = choices.get(item_id) == entry["correct"]
    return dict(out)


def stage_select(
    universe: naming_c1.Universe,
    replies: Mapping[tuple[str, int], Mapping[str, object]],
    correct: Mapping[str, Mapping[int, bool]],
    confusables: Mapping[str, Sequence[str]],
    out: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, list[str]], dict[str, object]]:
    """Select one name per theme, then write the uniqueness round's namer items.

    Args:
        universe: The build.
        replies: Namer replies by ``(theme, slot)``.
        correct: Back-match correctness by theme and candidate.
        confusables: Theme to its confusables.
        out: Output directory.

    Returns:
        ``(selections, confusables_after, counts)``.
    """
    by_theme: dict[str, dict[int, Mapping[str, object]]] = defaultdict(dict)
    for (theme, slot), reply in replies.items():
        by_theme[theme][slot] = reply
    selections = {
        theme: naming_c1.select(
            candidates, {slot: correct.get(theme, {}).get(slot, False) for slot in candidates}
        )
        for theme, candidates in by_theme.items()
    }
    duplicates = naming_c1.duplicate_names(selections)
    items, after = naming_c1.dedup_items(universe, selections, confusables)
    for slot in SLOTS:
        block = [item for index, item in items if index == slot + naming_c1.DEDUP_OFFSET]
        if block:
            write_json(out / f"dedup_slot{slot}.json", block)
    write_json(out / "confusables_after_dedup.json", after, indent=None)

    counts = {
        "themes": len(selections),
        "unnameable": sum(1 for v in selections.values() if v["unnameable"]),
        "low_confidence": sum(1 for v in selections.values() if v.get("low_confidence")),
        "duplicates": duplicates,
        "dedup_themes": len({str(item["theme_id"]) for _i, item in items}),
        "dedup_items": len(items),
    }
    return selections, after, counts


def stage_dedup_backmatch(
    universe: naming_c1.Universe,
    dedup_replies: Mapping[tuple[str, int], Mapping[str, object]],
    after: Mapping[str, Sequence[str]],
    out: Path,
) -> dict[str, object]:
    """Write the uniqueness round's back-match items and key.

    Args:
        universe: The build.
        dedup_replies: The re-ask replies, keyed by ``(theme, slot)``.
        after: Confusables as the uniqueness round left them.
        out: Output directory.

    Returns:
        Counts.
    """
    items: list[dict[str, object]] = []
    key: dict[str, dict[str, object]] = {}
    for slot in SLOTS:
        # Insertion order, NOT sorted: the pilot numbers these items in the order the replies
        # appear in each slot's file, so sorting by theme id would hand the ids to the wrong themes
        # and silently mismatch every judgement.
        for (theme, other), reply in dedup_replies.items():
            if other != slot:
                continue
            item_id = f"D{len(items):03d}"
            item, letter = naming_c1.backmatch_item(
                universe, theme, str(reply["name"]),
                f"S{slot + naming_c1.DEDUP_OFFSET}", item_id, after[theme],
            )
            items.append(item)
            key[item_id] = {"theme": theme, "cand": slot, "correct": letter}
    random.Random(DEDUP_ORDER_SEED).shuffle(items)
    write_json(out / "dedup_sel_01.json", items)
    write_json(out / "KEY_DO_NOT_SHARE_dedup.json", key, indent=None)
    return {"items": len(items)}


def write_final(
    selections: Mapping[str, Mapping[str, object]],
    out: Path,
    rerun: Mapping[str, Mapping[str, object]] | None = None,
    first_round_duplicates: Mapping[str, int] | None = None,
) -> dict[str, object]:
    """Write ``final_names.tsv``, ``final_names.json`` and a summary.

    Args:
        selections: The final selection per theme.
        out: Output directory.
        rerun: The re-run arm's selections, for the pilot's ``final_names.json`` shape.
        first_round_duplicates: The collisions found before the uniqueness round.

    Returns:
        The summary.
    """
    residual = naming_c1.duplicate_names(selections)
    payload: dict[str, object] = {
        "main": {theme: dict(entry) for theme, entry in selections.items()},
        "rerun": {theme: dict(entry) for theme, entry in (rerun or {}).items()},
        "duplicates": dict(first_round_duplicates or {}),
        "duplicates_after_dedup": residual,
    }
    write_json(out / "final_names.json", payload)

    rows = []
    for theme in sorted(selections):
        entry = selections[theme]
        rows.append({
            "node": theme,
            "name": "" if entry["unnameable"] else str(entry["name"]),
            "n_correct": "" if entry["unnameable"] else entry["n_correct"],
            "n_nameable": "" if entry["unnameable"] else entry["n_nameable"],
            "low_confidence": "" if entry["unnameable"] else int(bool(entry["low_confidence"])),
            "unnameable": int(bool(entry["unnameable"])),
        })
    destination = out / "final_names.tsv"
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, delimiter="\t", lineterminator="\n",
            fieldnames=["node", "name", "n_correct", "n_nameable", "low_confidence", "unnameable"],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "themes": len(selections),
        "named": sum(1 for v in selections.values() if not v["unnameable"]),
        "unnameable": sum(1 for v in selections.values() if v["unnameable"]),
        "low_confidence": sum(1 for v in selections.values() if v.get("low_confidence")),
        "n_correct_distribution": dict(sorted(Counter(
            v["n_correct"] for v in selections.values() if not v["unnameable"]
        ).items())),
        "duplicates_before_dedup": dict(first_round_duplicates or {}),
        "duplicates_after_dedup": residual,
    }
    write_json(out / "final_summary.json", summary, indent=2)
    return summary


def offline_universe(args: argparse.Namespace) -> tuple[
    naming_c1.Universe, list[str], dict[str, list[str]]
]:
    """Load the build and settle the theme list and confusables for an offline stage.

    Args:
        args: Parsed arguments.

    Returns:
        ``(universe, themes_in_batch_order, confusables)``.
    """
    keys, vectors = naming_c1.load_space(args.space, args.pathways)
    universe = naming_c1.Universe.load(args.offline_build, args.descriptions, keys, vectors)
    if args.themes_file is not None:
        stored = json.loads(args.themes_file.read_text())
        themes = list(stored.get("themes") or stored["sample"])
        confusables = {theme: list(entries) for theme, entries in stored["confusables"].items()}
    else:
        themes = eligible_themes(universe)
        confusables = {theme: universe.confusables(theme) for theme in themes}
    return universe, batched_order(themes), confusables


def run_offline(args: argparse.Namespace) -> int:
    """Run one offline stage. No client, no API key, no network.

    Args:
        args: Parsed arguments.

    Returns:
        Process exit status.
    """
    out = args.offline_out
    universe, order, confusables = offline_universe(args)
    print(f"OFFLINE {args.offline}  build {args.offline_build}")
    print(f"  {len(universe.members):,} themes in the build, {len(order):,} in naming-c1 scope "
          f"(3-200 members)")
    print(f"  writing to {out}  (never into the reviewer's own folders)")

    if args.offline == "n1":
        counts = stage_n1(
            universe, order, confusables, out,
            prefix=args.prefix, batch=args.batch, width=args.batch_width,
            candidate_offset=args.candidate_offset,
        )
        if args.themes_file is None:
            write_json(
                out / "themes_and_confusables.json",
                {"themes": sorted(confusables), "confusables": confusables}, indent=0,
            )
        print(f"  N1: {counts['items']:,} items over {counts['files']} files "
              f"({counts['slots']} slots x {counts['themes']:,} themes)")
        return 0

    raw = args.raw or (out / "raw")
    replies, files = read_namer_replies(raw, args.prefix)
    expected = [(theme, slot) for theme in order for slot in SLOTS]
    failures = validate_replies(expected, replies)
    print(f"  read {len(replies):,} replies from {len(files)} files in {raw}")
    print(f"  validation: {'PASS' if not failures else f'{len(failures)} FAILURE(S)'}")
    for line in failures[:20]:
        print(f"      {line}")
    if len(failures) > 20:
        print(f"      ... and {len(failures) - 20} more")
    if failures:
        return 1
    refused = sum(1 for reply in replies.values() if not reply.get("nameable", True))
    print(f"  not-nameable votes: {refused}")

    if args.offline == "s1":
        counts = stage_s1(
            universe, replies, confusables, out,
            run=args.run, candidate_offset=args.candidate_offset, batch=args.s1_batch,
        )
        print(f"  S1: {counts['items']:,} items over {counts['files']} files; "
              f"{counts['unnameable_skipped']} candidates skipped as not nameable")
        print(f"  answer key: {out / str(counts['key'])}")
        return 0

    selection = args.selection or out
    key = json.loads((out / f"KEY_DO_NOT_SHARE_{args.run}.json").read_text())
    choices = read_choices(selection, f"{args.run}_sel_*.out.json")
    print(f"  back-match judgements: {len(choices):,} of {len(key):,} items")
    correct = correctness(key, choices)

    if args.offline == "select":
        selections, after, counts = stage_select(universe, replies, correct, confusables, out)
        write_json(out / "selections_before_dedup.json", selections)
        print(f"  select: {counts['themes']:,} themes, {counts['unnameable']} unnameable, "
              f"{counts['low_confidence']} low confidence")
        print(f"  duplicates: {counts['duplicates'] or 'none'}")
        print(f"  dedup items: {counts['dedup_items']} over {counts['dedup_themes']} themes")
        del after
        return 0

    selections = {
        theme: entry
        for theme, entry in json.loads((out / "selections_before_dedup.json").read_text()).items()
    }
    first_round = naming_c1.duplicate_names(selections)
    after = json.loads((out / "confusables_after_dedup.json").read_text())
    dedup_replies, dedup_files = read_namer_replies(raw, "dedup") if (
        list(raw.glob("dedup_slot*_b*.out.json"))
    ) else ({}, [])
    if not dedup_replies:
        for path in sorted(raw.glob("dedup_slot*.out.json")):
            slot = int(path.name.split("_slot")[1][0])
            for reply in json.loads(path.read_text()):
                dedup_replies[(reply["theme_id"], slot)] = reply
            dedup_files.append(path)
    print(f"  uniqueness replies: {len(dedup_replies)} from {len(dedup_files)} file(s)")
    if dedup_replies:
        stage_dedup_backmatch(universe, dedup_replies, after, out)
        dedup_key = json.loads((out / "KEY_DO_NOT_SHARE_dedup.json").read_text())
        dedup_choices = read_choices(selection, "dedup_sel_*.out.json")
        dedup_correct = correctness(dedup_key, dedup_choices)
        grouped: dict[str, dict[int, Mapping[str, object]]] = defaultdict(dict)
        for (theme, slot), reply in dedup_replies.items():
            grouped[theme][slot] = reply
        selections = naming_c1.apply_uniqueness(selections, grouped, dedup_correct)
    summary = write_final(selections, out, first_round_duplicates=first_round)
    print(f"  final: {summary['named']:,} named, {summary['unnameable']} unnameable, "
          f"{summary['low_confidence']} low confidence")
    print(f"  duplicates after the uniqueness round: "
          f"{summary['duplicates_after_dedup'] or 'none'}")
    print(f"  -> {out / 'final_names.tsv'}")
    return 0


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
    parser.add_argument("--offline", choices=["n1", "s1", "select", "final"], default=None,
                        help="run one offline stage: no client is built and no API key is read")
    parser.add_argument("--offline-out", type=Path, default=OFFLINE_OUT,
                        help="where offline mode writes; never the reviewer's own folders")
    parser.add_argument("--offline-build", type=Path, default=O50_BUILD,
                        help="the build to name; defaults to the adopted O50 working version")
    parser.add_argument("--themes-file", type=Path, default=None,
                        help="JSON holding the theme list and confusables, instead of computing "
                             "them. Used to reproduce the pilot, whose themes were a sample")
    parser.add_argument("--raw", type=Path, default=None,
                        help="offline s1/select/final: where the replies are")
    parser.add_argument("--selection", type=Path, default=None,
                        help="offline select/final: where the back-match judgements are")
    parser.add_argument("--prefix", default="namer", help="namer filename prefix")
    parser.add_argument("--run", default="main", help="run tag for back-match ids and the key file")
    parser.add_argument("--batch", type=int, default=BATCH, help="themes per namer file")
    parser.add_argument("--batch-width", type=int, default=3,
                        help="zero-padding of the batch number; the pilot used 2")
    parser.add_argument("--s1-batch", type=int, default=S1_BATCH, help="items per back-match file")
    parser.add_argument("--candidate-offset", type=int, default=0,
                        help="added to the slot to form the candidate index; the pilot's re-run "
                             "arm uses 10")
    args = parser.parse_args(argv)

    if args.offline:
        return run_offline(args)

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
