#!/usr/bin/env python3
"""Blind input pilot: does a theme name need member NAMES, member DESCRIPTIONS, or both?

Three arms over the same 30 leaf themes of the frozen centred build, the same model, the same
``name-v3`` prompt. The only thing that varies is what the model is shown:

- ``names`` -- member pathway names only
- ``descriptions`` -- member descriptions only, no names
- ``both`` -- what the pipeline sends today

The output is deliberately unreadable as a scorecard. Per theme it prints the members, then the
three candidate names in an order shuffled per theme, labelled A/B/C. Which label is which arm goes
to a SEPARATE file, so the names can be judged without knowing what produced them. Nothing in the
comparison file says or implies which arm is the incumbent.

Usage::

    uv run scripts/pilot_naming_input.py              # price it and stop
    uv run scripts/pilot_naming_input.py --submit     # spend
    uv run scripts/pilot_naming_input.py --report     # read back a completed pilot
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from thema.data import descriptions as descriptions_table
from thema.data.pathways import PathwayCollection
from thema.llm import PRICES, Ledger, LLMClient, Request
from thema.naming import (
    MAX_WORDS,
    MIN_WORDS,
    NAME_FORMAT,
    NAME_PROMPT_VERSION,
    NAME_RESPONSE_KEY,
    SYSTEM_PROMPT,
    WORKED_EXAMPLES,
    check,
    theme_key,
)

#: The three arms, in a fixed order. This order is the ARM KEY's order, never the display order.
ARMS = ("names", "descriptions", "both")

#: Themes sampled per stratum.
PER_STRATUM = 10

#: The strata, by what the theme's members are drawn from.
STRATA = ("pure_go", "pure_reactome", "has_btm_or_hallmark")

#: The seed, recorded in both output files. Change it and the pilot is a different pilot.
SEED = 20260927

#: Output tokens per naming call, measured over 820 real Sonnet calls in the production run.
OUTPUT_TOKENS = 112

#: What the provider's cache actually holds: the system prompt plus the worked-examples preamble.
CACHED_TOKENS = 1180

CACHE_DIR = Path("llm_cache")


def read_build(directory: Path) -> tuple[dict[str, list[str]], dict[str, dict[str, float]]]:
    """Read a build's members and inclusions.

    Args:
        directory: A build directory holding ``nodes.tsv`` and ``members.tsv``.

    Returns:
        Node id to member keys, and node id to key to inclusion.
    """
    csv.field_size_limit(1 << 30)
    members: dict[str, list[str]] = defaultdict(list)
    inclusions: dict[str, dict[str, float]] = defaultdict(dict)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
            inclusions[row["node"]][row["key"]] = float(row["inclusion"])
    return dict(members), dict(inclusions)


def leaves_of(directory: Path) -> list[str]:
    """Every node with no child, read from the build's edges.

    Args:
        directory: A build directory.

    Returns:
        Leaf node ids, sorted, so the sample is reproducible independent of file order.
    """
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    has_child = {p for ps in parents.values() for p in ps}
    return sorted(n for n in parents if n not in has_child)


def stratum_of(sources: Sequence[str]) -> str | None:
    """Which stratum a theme belongs to, from its members' sources.

    Args:
        sources: One source per member.

    Returns:
        A member of :data:`STRATA`, or ``None`` when the theme is a GO/Reactome mixture -- which is
        neither pure nor a small-source case, and is left out so the three strata stay disjoint.
    """
    unique = set(sources)
    if unique & {"btm", "hallmark"}:
        return "has_btm_or_hallmark"
    if unique == {"go"}:
        return "pure_go"
    if unique == {"reactome"}:
        return "pure_reactome"
    return None


def sample(
    leaves: Sequence[str],
    members: dict[str, list[str]],
    by_key: dict,
    seed: int = SEED,
) -> dict[str, list[str]]:
    """Draw :data:`PER_STRATUM` leaves per stratum.

    Args:
        leaves: Candidate leaf node ids.
        members: Node id to member keys.
        by_key: Pathway key to pathway.
        seed: The recorded seed.

    Returns:
        Stratum to node ids, sorted within each stratum. A stratum with fewer than
        :data:`PER_STRATUM` candidates yields all of them, and the caller reports the shortfall.
    """
    buckets: dict[str, list[str]] = {s: [] for s in STRATA}
    for node in leaves:
        keys = [k for k in members.get(node, ()) if k in by_key]
        if len(keys) < 2:
            continue
        stratum = stratum_of([by_key[k].source for k in keys])
        if stratum is not None:
            buckets[stratum].append(node)
    rng = random.Random(seed)
    return {
        s: sorted(rng.sample(nodes, min(PER_STRATUM, len(nodes)))) for s, nodes in buckets.items()
    }


def render_arm(
    arm: str, members: Sequence[tuple[str, str, str]], inclusions: Sequence[float]
) -> str:
    """Render one theme for one arm.

    The three renderings differ only in what is shown per member. Everything else -- the worked
    examples, the instruction, the inclusions -- is held constant, so the comparison is about the
    input and not about the framing.

    Args:
        arm: A member of :data:`ARMS`.
        members: ``(source, name, description)`` per member.
        inclusions: One inclusion per member, in the same order.

    Returns:
        The user message.
    """
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    lines = [
        WORKED_EXAMPLES,
        "",
        "Below are the pathways in this theme, with their inclusion"
        + (
            "."
            if arm == "names"
            else " and their descriptions."
            if arm == "both"
            else ". Their names are withheld; the descriptions are your only evidence."
        ),
        "Name the theme.",
        "",
    ]
    for index, (source, name, description) in enumerate(members):
        share = f"  (inclusion {inclusions[index]:.2f})"
        if arm == "descriptions":
            lines.append(f"  [{source}] pathway {index + 1}{share}")
            lines.append(f"      {description}")
        elif arm == "names":
            lines.append(f"  [{source}] {name}{share}")
        else:
            lines.append(f"  [{source}] {name}{share}")
            lines.append(f"      {description}")
        lines.append("")
    return "\n".join(lines)


def name_leakage(
    drawn: dict[str, list[str]],
    members: dict[str, list[str]],
    by_key: dict,
    texts: dict[str, str],
) -> tuple[int, int, int]:
    """How often a member's description reveals that member's own name.

    The ``descriptions`` arm is not blind to names, because the descriptions were generated FROM the
    names and half of them quote it. This is a property of the descriptions rather than a fault in
    the arm -- dropping names from the prompt really would leave the model this text -- but any
    conclusion drawn from the arm has to state the rate, so the rate is computed and printed.

    Args:
        drawn: Stratum to node ids.
        members: Node id to member keys.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.

    Returns:
        ``(verbatim, near, total)``: descriptions containing the name exactly, containing at least
        three quarters of its content words, and the number of members examined.
    """
    verbatim = near = total = 0
    for stratum in STRATA:
        for node in drawn[stratum]:
            for key in members.get(node, ()):
                if key not in by_key:
                    continue
                total += 1
                name, description = by_key[key].name.lower(), texts.get(key, "").lower()
                if name in description:
                    verbatim += 1
                    continue
                words = re.findall(r"[a-z]{4,}", name)
                if words and sum(w in description for w in words) / len(words) >= 0.75:
                    near += 1
    return verbatim, near, total


def requests_for(
    drawn: dict[str, list[str]],
    members: dict[str, list[str]],
    inclusions: dict[str, dict[str, float]],
    by_key: dict,
    texts: dict[str, str],
) -> tuple[list[Request], dict[str, tuple[str, str]]]:
    """Build one request per (theme, arm).

    Args:
        drawn: Stratum to node ids.
        members: Node id to member keys.
        inclusions: Node id to key to inclusion.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.

    Returns:
        Every request, and request key to ``(node, arm)``. The request key carries the arm, so the
        three arms of one theme never collide in the ledger.
    """
    out: list[Request] = []
    back: dict[str, tuple[str, str]] = {}
    for stratum in STRATA:
        for node in drawn[stratum]:
            keys = [k for k in members[node] if k in by_key]
            keys.sort(key=lambda k: (-inclusions[node].get(k, 1.0), k))
            shown = [
                (by_key[k].source, by_key[k].name, texts.get(k, "(no description)")) for k in keys
            ]
            shares = [inclusions[node].get(k, 1.0) for k in keys]
            for arm in ARMS:
                request = Request(
                    key=f"{theme_key(keys)}:input-pilot:{arm}",
                    system=SYSTEM_PROMPT,
                    user=render_arm(arm, shown, shares),
                )
                out.append(request)
                back[request.key] = (node, arm)
    return out, back


def price(model: str, requests: Sequence[Request], client: LLMClient) -> float:
    """Live-rate cost of the pilot, with prompt caching priced as the API bills it.

    Args:
        model: A key of :data:`thema.llm.PRICES`.
        requests: Every request.
        client: The client, for its tokenizer.

    Returns:
        Dollars, live rate. This prices REQUESTS, so a re-run the ledger already holds costs less.
    """
    counted = [client.count_tokens(r) for r in requests[: min(9, len(requests))]]
    mean_in = sum(counted) / len(counted)
    rate_in, rate_out = PRICES[model]
    cached = min(CACHED_TOKENS, mean_in)
    uncached = max(0.0, mean_in - cached)
    calls = len(requests)
    return (
        calls * uncached * rate_in
        + calls * cached * rate_in * 0.1
        + 3 * cached * rate_in * 1.25
        + calls * OUTPUT_TOKENS * rate_out
    ) / 1e6


def write_comparison(
    path: Path,
    drawn: dict[str, list[str]],
    got: dict[tuple[str, str], dict],
    members: dict[str, list[str]],
    inclusions: dict[str, dict[str, float]],
    by_key: dict,
    texts: dict[str, str],
    order: dict[str, list[str]],
    leakage: tuple[int, int, int],
) -> None:
    """Write the blind comparison file.

    Args:
        path: Output path.
        drawn: Stratum to node ids.
        got: ``(node, arm)`` to parsed response.
        members: Node id to member keys.
        inclusions: Node id to key to inclusion.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.
        order: Node id to the arms in DISPLAY order, so A/B/C means something different per theme.
        leakage: ``(verbatim, near, total)`` from :func:`name_leakage`, stated in the header.
    """
    lines = [
        "# Blind input pilot -- which input a theme name needs",
        "",
        f"*Thirty leaf themes of `recurrent_dag_consensus_centred`, seed {SEED}, prompt "
        f"`{NAME_PROMPT_VERSION}`. Each theme was named three times from three different views of "
        "the same members. The three candidates below are in a per-theme shuffled order. Which "
        "letter is which view is in `input_pilot_key.tsv`; do not open it until the names are "
        "judged.*",
        "",
        "For each theme, ask of each candidate: is it true of every member at inclusion 0.5 or "
        "above, and would it let you find this theme in a list of 873?",
        "",
        "---",
        "",
    ]
    for stratum in STRATA:
        lines += [f"## {stratum} ({len(drawn[stratum])} themes)", ""]
        for node in drawn[stratum]:
            keys = [k for k in members[node] if k in by_key]
            keys.sort(key=lambda k: (-inclusions[node].get(k, 1.0), k))
            lines += [f"### {node} -- {len(keys)} members", ""]
            for key in keys:
                first = texts.get(key, "").split(". ")[0].strip()
                lines.append(
                    f"- **{by_key[key].name}** [{by_key[key].source}] "
                    f"(inclusion {inclusions[node].get(key, 1.0):.2f})"
                )
                if first:
                    lines.append(f"  - {first}.")
            lines.append("")
            for label, arm in zip("ABC", order[node], strict=True):
                parsed = got.get((node, arm), {})
                if not parsed.get("nameable") or not parsed.get("name"):
                    lines.append(f"- **{label}.** *(refused as unnameable)*")
                    continue
                result = check(parsed["name"], [by_key[k].name for k in keys])
                flags = "" if result.clean else "  `mechanical: FAIL`"
                lines.append(f"- **{label}.** {parsed['name']}{flags}")
                if parsed.get("rationale"):
                    lines.append(f"  - {parsed['rationale']}")
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_key(
    path: Path,
    order: dict[str, list[str]],
    got: dict[tuple[str, str], dict],
    by_key: dict,
    members: dict[str, list[str]],
) -> None:
    """Write the arm key, separately from the comparison.

    Args:
        path: Output path.
        order: Node id to arms in display order.
        got: ``(node, arm)`` to parsed response.
        by_key: Pathway key to pathway.
        members: Node id to member keys.
    """
    rows = [("node", "label", "arm", "name", "nameable", "mechanical_clean")]
    for node, arms in order.items():
        names = [by_key[k].name for k in members[node] if k in by_key]
        for label, arm in zip("ABC", arms, strict=True):
            parsed = got.get((node, arm), {})
            name = parsed.get("name", "") if parsed.get("nameable") else ""
            clean = check(name, names).clean if name else False
            rows.append(
                (node, label, arm, name, str(bool(parsed.get("nameable"))), str(clean))
            )
    path.write_text(
        "\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8"
    )


def summarise(
    got: dict[tuple[str, str], dict], by_key: dict, members: dict[str, list[str]]
) -> None:
    """Print one line per arm: unnameable count and mechanical-check failures.

    Args:
        got: ``(node, arm)`` to parsed response.
        by_key: Pathway key to pathway.
        members: Node id to member keys.
    """
    print(f"\n{'arm':<14} {'named':>6} {'unnameable':>11} {'mech FAIL':>10}  {'mean words':>10}")
    print("-" * 58)
    for arm in ARMS:
        rows = [(n, r) for (n, a), r in got.items() if a == arm]
        named = [(n, r) for n, r in rows if r.get("nameable") and r.get("name")]
        bad = 0
        words = 0
        for node, parsed in named:
            names = [by_key[k].name for k in members[node] if k in by_key]
            result = check(parsed["name"], names)
            bad += 0 if result.clean else 1
            words += result.words
        mean = words / len(named) if named else 0.0
        print(
            f"{arm:<14} {len(named):>6} {len(rows) - len(named):>11} {bad:>10}  {mean:>10.1f}"
        )
    print(
        f"\n(a name is {MIN_WORDS}-{MAX_WORDS} words; mechanical failures are reported, "
        "never repaired)"
    )


def main(argv: list[str] | None = None) -> int:
    """Run the pilot, or price it and stop.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--build", default="v0.2/recurrent_dag_consensus_centred")
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--submit", action="store_true", help="spend; without it, price and stop")
    parser.add_argument("--report", action="store_true", help="read a completed pilot from cache")
    parser.add_argument("--max-dollars", type=float, default=2.00)
    parser.add_argument("--out", type=Path, default=Path("docs/status"))
    args = parser.parse_args(argv)

    directory = args.data / "ontology" / args.build
    if not directory.is_dir():
        print(f"no build at {directory}", file=sys.stderr)
        return 1

    members, inclusions = read_build(directory)
    leaves = leaves_of(directory)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")

    drawn = sample(leaves, members, by_key, SEED)
    print(f"INPUT PILOT  {args.build}: {len(leaves):,} leaves, seed {SEED}, {NAME_PROMPT_VERSION}")
    for stratum in STRATA:
        got = len(drawn[stratum])
        note = "" if got == PER_STRATUM else f"  (SHORT of {PER_STRATUM}: that is all there are)"
        print(f"  {stratum:<20} {got:>3} themes{note}")
    total = sum(len(v) for v in drawn.values())
    verbatim, near, examined = name_leakage(drawn, members, by_key, texts)
    print(
        f"\n  CAVEAT, measured on these {examined} members: the descriptions-only arm is not blind "
        f"to names.\n  {verbatim} descriptions ({verbatim / examined:.0%}) quote their pathway's "
        f"name verbatim and {near} more\n  ({near / examined:.0%}) carry three quarters of its "
        f"content words -- {(verbatim + near) / examined:.0%} together. The arm\n  measures "
        "descriptions AS THEY EXIST, which is the input a names-free pipeline would send."
    )

    requests, back = requests_for(drawn, members, inclusions, by_key, texts)
    ledger = Ledger.open(args.data / CACHE_DIR, args.model, NAME_PROMPT_VERSION)
    client = LLMClient(
        args.model,
        NAME_PROMPT_VERSION,
        ledger,
        response_format=NAME_FORMAT,
        response_key=NAME_RESPONSE_KEY,
    )
    pending = [r for r in requests if r.key not in ledger]
    dollars = price(args.model, pending, client) if pending else 0.0
    print(
        f"\n  {total} themes x {len(ARMS)} arms = {len(requests)} calls, "
        f"{len(pending)} not already cached"
    )
    print(f"  live cost: ${dollars:,.2f}   ceiling ${args.max_dollars:,.2f}")

    if not args.report and not args.submit:
        print("\nnothing submitted; rerun with --submit")
        return 0
    if args.submit and dollars > args.max_dollars:
        print(f"\nrefusing: ${dollars:,.2f} is above --max-dollars", file=sys.stderr)
        return 1
    if args.report and pending:
        print(f"\n{len(pending)} of {len(requests)} calls are not in the cache; nothing to report",
              file=sys.stderr)
        return 1

    completions = client.complete_all(requests)
    got: dict[tuple[str, str], dict] = {}
    for completion in completions:
        node, arm = back[completion.key]
        try:
            got[(node, arm)] = json.loads(completion.text)
        except json.JSONDecodeError:
            got[(node, arm)] = {}

    rng = random.Random(SEED + 1)
    order = {}
    for stratum in STRATA:
        for node in drawn[stratum]:
            arms = list(ARMS)
            rng.shuffle(arms)
            order[node] = arms

    args.out.mkdir(parents=True, exist_ok=True)
    comparison = args.out / "input_pilot.md"
    key = args.out / "input_pilot_key.tsv"
    write_comparison(
        comparison,
        drawn,
        got,
        members,
        inclusions,
        by_key,
        texts,
        order,
        (verbatim, near, examined),
    )
    write_key(key, order, got, by_key, members)
    summarise(got, by_key, members)
    print(f"\n  blind comparison: {comparison}")
    print(f"  arm key (do not open first): {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
