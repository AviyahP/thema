"""Name every theme in a build: bottom-up generation, then a top-down disambiguation pass.

Naming is SEQUENTIAL ACROSS LEVELS -- a parent cannot be named until its children are -- and the
build has ten naming levels plus ten disambiguation levels. That makes the batch API impractical
here: a batch takes hours and level k+1 cannot be submitted until level k returns, so twenty
levels is days rather than minutes. Live calls with the client's own concurrency finish in about
a quarter of an hour at roughly double the price, which on a single-digit total is not a close
call. ``--batch`` is available for anyone who would rather wait; the price gate reports both.

Nothing is spent without ``--submit``. The price is reported first, as everywhere else.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from thema.data import descriptions as descriptions_table
from thema.data import names as names_table
from thema.data.pathways import PathwayCollection
from thema.data.tables import merge_tsv, print_table
from thema.llm import BATCH_CHUNK, Ledger, LLMClient, Request, price_batch
from thema.naming import (
    DISAMBIGUATION_FORMAT,
    DISAMBIGUATION_RESPONSE_KEY,
    DISAMBIGUATION_SYSTEM_PROMPT,
    NAME_FORMAT,
    NAME_PROMPT_VERSION,
    NAME_RESPONSE_KEY,
    SYSTEM_PROMPT,
    check,
    disambiguation_key,
    render_disambiguation,
    render_internal,
    render_leaf,
    theme_key,
)
from thema.ontology.order import children_of, disambiguation_order, naming_order, siblings_of

CACHE_DIR = "cache/names"
NAMES_TABLE = "theme_names.tsv"

#: How many member descriptions an internal node is shown. Three, per the design: enough that one
#: bad child name cannot compound upward, few enough that the input stays bounded.
INTERNAL_SAMPLES = 3

#: Refuse to submit above this worst-case price without being told otherwise.
DEFAULT_MAX_DOLLARS = 20.0


def read_build(directory: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Read a build's structure.

    Args:
        directory: A versioned method directory holding ``nodes.tsv`` and ``members.tsv``.

    Returns:
        Node id to parent ids, and node id to member pathway keys.
    """
    csv.field_size_limit(1 << 30)
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, list[str]] = defaultdict(list)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    return parents, dict(members)


def leaf_request(node: str, member_keys: list[str], by_key: dict, texts: dict[str, str]) -> Request:
    """Build the Task A prompt for one leaf."""
    shown = [
        (by_key[k].source, by_key[k].name, texts.get(k, "(no description)"))
        for k in member_keys
        if k in by_key
    ]
    return Request(
        key=theme_key(member_keys), system=SYSTEM_PROMPT, user=render_leaf(shown)
    )


def internal_request(
    node: str,
    member_keys: list[str],
    child_names: list[str],
    unnamed: int,
    by_key: dict,
    texts: dict[str, str],
    direct_keys: Sequence[str] = (),
) -> Request:
    """Build the Task B prompt for one internal node.

    ``direct_keys`` are the members belonging to no child -- what makes the parent broader than
    its children, and without which a single-child node can only be refused as a restatement.
    """
    samples = [
        (by_key[k].source, by_key[k].name, texts.get(k, "(no description)"))
        for k in member_keys[:INTERNAL_SAMPLES]
        if k in by_key
    ]
    direct = [(by_key[k].source, by_key[k].name) for k in direct_keys if k in by_key]
    return Request(
        key=theme_key(member_keys, [*child_names, f"direct:{len(direct)}"]),
        system=SYSTEM_PROMPT,
        user=render_internal(child_names, samples, len(member_keys), unnamed, direct),
    )


def run_level(client: LLMClient, requests: list[Request], workers: int) -> dict[str, dict]:
    """Complete one level, tolerating per-request failure.

    Args:
        client: The caching client.
        requests: One request per node in this level.
        workers: Concurrency.

    Returns:
        Node id to the parsed response, omitting any request that failed. ``complete_all`` raises
        on the first unparseable reply, which would abandon a whole level for one refusal, so each
        request is completed on its own.
    """
    out: dict[str, dict] = {}

    def one(request: Request) -> tuple[str, dict | None]:
        try:
            return request.key, json.loads(client.complete(request).text)
        except Exception as exc:  # noqa: BLE001 -- one bad reply must not end the level
            print(f"    {request.key}: {type(exc).__name__}: {str(exc)[:80]}", file=sys.stderr)
            return request.key, None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for key, parsed in pool.map(one, requests):
            if parsed is not None:
                out[key] = parsed
    return out


def generate(
    client: LLMClient,
    parents: dict[str, list[str]],
    members: dict[str, list[str]],
    by_key: dict,
    texts: dict[str, str],
    workers: int,
    dry_run: bool,
) -> tuple[dict[str, dict], list[Request]]:
    """Bottom-up generation, level by level.

    Args:
        client: The caching client.
        parents: Node id to parent ids.
        members: Node id to member pathway keys.
        by_key: Pathway key to Pathway.
        texts: Pathway key to its description.
        workers: Concurrency.
        dry_run: Build every request but call nothing, so the run can be priced.

    Returns:
        Node id to its parsed response, and every request that would be sent. Under ``dry_run``
        the responses are empty and the requests are what pricing measures -- the levels above the
        leaves use placeholder child names, because the real ones do not exist until the run
        happens, which makes the estimate approximate and says so.
    """
    kids = children_of(parents)
    levels = naming_order(parents)
    got: dict[str, dict] = {}
    every: list[Request] = []
    for depth, level in enumerate(levels):
        requests, back = [], {}
        for node in level:
            cs = kids.get(node, [])
            if not cs:
                leaf = leaf_request(node, members.get(node, []), by_key, texts)
                back[leaf.key] = node
                requests.append(leaf)
                continue
            named = [
                got[c]["name"]
                for c in cs
                if got.get(c, {}).get("nameable") and got[c].get("name")
            ]
            if dry_run:  # the real child names do not exist yet; length is what pricing needs
                named = [f"child theme {i}" for i, _ in enumerate(cs)]
            unnamed = len(cs) - len(named)
            covered = {k for c in cs for k in members.get(c, [])}
            direct_keys = [k for k in members.get(node, []) if k not in covered]
            internal = internal_request(
                node, members.get(node, []), named, unnamed, by_key, texts, direct_keys
            )
            back[internal.key] = node
            requests.append(internal)
        every.extend(requests)
        if dry_run:
            continue
        print(f"  level {depth} ({'leaves' if depth == 0 else 'internal'}): "
              f"{len(requests):,} themes", flush=True)
        for rkey, parsed in run_level(client, requests, workers).items():
            got[back[rkey]] = parsed
    return got, every


def disambiguate(
    client: LLMClient,
    parents: dict[str, list[str]],
    generated: dict[str, dict],
    workers: int,
) -> tuple[dict[str, dict], int]:
    """Top-down pass: rewrite only where a name repeats a parent or collides with a sibling.

    Args:
        client: The caching client.
        parents: Node id to parent ids.
        generated: Node id to its generated response.
        workers: Concurrency.

    Returns:
        Node id to the disambiguation response, and how many PARENTS had a child renamed. That
        count is reported rather than acted on: revisions are not fed back into parents, because
        that would loop, so the scale of the compromise is made visible instead of assumed.
    """
    kids = children_of(parents)
    final = {n: r["name"] for n, r in generated.items() if r.get("nameable") and r.get("name")}
    out: dict[str, dict] = {}
    for depth, level in enumerate(disambiguation_order(parents)):
        requests, back = [], {}
        for node in level:
            if node not in final:
                continue
            ps = [final[p] for p in parents.get(node, ()) if p in final]
            sibs = [final[s] for s in siblings_of(node, parents, kids) if s in final]
            if not ps and not sibs:
                continue
            requests.append(
                Request(
                    key=disambiguation_key(final[node], ps, sibs),
                    system=DISAMBIGUATION_SYSTEM_PROMPT,
                    user=render_disambiguation(final[node], ps, sibs),
                )
            )
            back[requests[-1].key] = node
        if not requests:
            continue
        print(f"  disambiguation level {depth}: {len(requests):,} themes", flush=True)
        for rkey, parsed in run_level(client, requests, workers).items():
            node = back[rkey]
            out[node] = parsed
            if parsed.get("revise") and parsed.get("name"):
                final[node] = parsed["name"]
    revised = {n for n, r in out.items() if r.get("revise")}
    touched = {p for n in revised for p in parents.get(n, ())}
    return out, len(touched)


def _cost(model: str, calls: float, user_tokens: float, system_tokens: int) -> float:
    """Batch-rate cost of a run, assuming the provider's prompt cache holds on the system prompt.

    Args:
        model: A key of :data:`thema.llm.PRICES`.
        calls: How many requests.
        user_tokens: Mean input tokens per request, system prompt excluded.
        system_tokens: The system prompt, sent with every request.
        
    Returns:
        Dollars at the batch rate. Double it for live.
    """
    from thema.llm import PRICES

    rate_in, rate_out = PRICES[model]
    tokens_in = calls * user_tokens + system_tokens  # cached: billed once
    return (tokens_in * rate_in + calls * 60 * rate_out) / 1e6 * 0.5


def smoke_sample(
    parents: dict[str, list[str]], want: int, seed: int = 20260924
) -> list[str]:
    """Pick a BOTTOM-UP CLOSED subset: every selected node has all its children selected too.

    Args:
        parents: Node id to parent ids.
        want: How many themes to select.
        seed: For reproducibility; recorded in the report.

    Returns:
        Selected node ids, leaves and internal nodes both.

    A random sample of themes would be untestable: an internal node is named from its children's
    names, so a parent whose children are not in the sample has no input. Leaves are drawn first
    and internal nodes are admitted only once every child of theirs is already in -- which makes
    the smoke test a real bottom-up run on a smaller DAG rather than a set of disconnected calls.
    """
    import random

    kids = children_of(parents)
    rng = random.Random(seed)

    def descendants(root: str) -> set[str]:
        out, stack = {root}, [root]
        while stack:
            for child in kids.get(stack.pop(), []):
                if child not in out:
                    out.add(child)
                    stack.append(child)
        return out

    # Whole SUBTREES, not scattered leaves. A subtree is closed by construction, so every
    # internal node in it has all its children present; scattered leaves almost never complete
    # a parent, so that sampling yields no internal nodes and never exercises Task B.
    internal = sorted(n for n in parents if kids.get(n))
    rng.shuffle(internal)
    chosen: set[str] = set()
    for root in internal:
        block = descendants(root)
        if len(block) > want:
            continue
        if len(chosen | block) <= want:
            chosen |= block
        if len(chosen) >= want:
            break
    if not chosen:  # no subtree fits; fall back to leaves so the run is still possible
        leaves = sorted(n for n in parents if not kids.get(n))
        chosen = set(rng.sample(leaves, min(want, len(leaves))))
    return sorted(chosen)


def rows_for(
    generated: dict[str, dict],
    revised: dict[str, dict],
    parents: dict[str, list[str]],
    members: dict[str, list[str]],
    model: str,
) -> list[tuple[str, ...]]:
    """Render the names table's rows.

    Args:
        generated: Node id to its generation response.
        revised: Node id to its disambiguation response.
        parents: Node id to parent ids.
        members: Node id to member pathway keys.
        model: The model that produced them.

    Returns:
        Rows in :data:`thema.data.names.NAME_COLUMNS` order, keyed by THEME KEY so a rebuild
        reuses every name whose theme is unchanged.
    """
    kids = children_of(parents)
    rows = []
    for node, response in sorted(generated.items()):
        cs = kids.get(node, [])
        child_names = sorted(
            generated[c]["name"]
            for c in cs
            if generated.get(c, {}).get("nameable") and generated[c].get("name")
        )
        key = theme_key(members.get(node, []), child_names)
        nameable = bool(response.get("nameable"))
        name = response.get("name", "") or ""
        rev = revised.get(node, {})
        if rev.get("revise") and rev.get("name"):
            name = rev["name"]
        failed = ()
        if nameable and name:
            member_names = [str(k) for k in members.get(node, [])]
            result = check(name, member_names)
            failed = tuple(
                f for f in ("in_range", "sentence_case") if not getattr(result, f)
            ) + tuple(
                f
                for f in ("leading_article", "trailing_punctuation", "bare_category")
                if getattr(result, f)
            ) + result.identifiers + result.source_words + result.empty_words
        rows.append(
            (
                key,
                name,
                "true" if nameable else "false",
                (rev.get("reason") or response.get("rationale", "")),
                str(len(members.get(node, []))),
                "leaf" if not cs else "internal",
                node,
                ";".join(failed),
                model,
                NAME_PROMPT_VERSION,
                names_table.STATUS_SUPERSEDED,
            )
        )
    return rows


def write_blind(
    path: Path,
    per_model: dict[str, dict[str, dict]],
    members: dict[str, list[str]],
    by_key: dict,
    seed: int = 20260924,
) -> dict[str, str]:
    """Write the two models' names side by side, with the models hidden.

    Args:
        path: Where to write the readable comparison.
        per_model: Model name to {node id: response}.
        members: Node id to member pathway keys.
        by_key: Pathway key to Pathway.
        seed: Controls which model is A and which is B per theme.

    Returns:
        Node id to the arm ordering used, so the key file can be written separately.

    The arm order is shuffled PER THEME, not once for the file: a single ordering means noticing
    one model's habit on the first theme tells the reader every other answer.
    """
    import random

    rng = random.Random(seed)
    models = sorted(per_model)
    order: dict[str, str] = {}
    lines = [
        "# Blind naming comparison\n",
        f"*{len(members)} themes, two models, which is which withheld. "
        "Arm order is shuffled per theme.*\n",
    ]
    for node in sorted(members):
        arms = models[:]
        rng.shuffle(arms)
        order[node] = ",".join(arms)
        names = [per_model[m].get(node, {}) for m in arms]
        if not any(names):
            continue
        lines.append(f"\n## {node} — {len(members[node])} pathways\n")
        for key in members[node][:8]:
            if key in by_key:
                lines.append(f"- {by_key[key].source}: {by_key[key].name}")
        if len(members[node]) > 8:
            lines.append(f"- ... {len(members[node]) - 8} more")
        lines.append("")
        for label, response in zip("AB", names, strict=False):
            if not response:
                lines.append(f"**{label}** — (no answer)")
            elif response.get("nameable"):
                lines.append(f"**{label}** — {response.get('name', '')}")
                lines.append(f"  - {response.get('rationale', '')}")
            else:
                lines.append(f"**{label}** — *declined to name*")
                lines.append(f"  - {response.get('rationale', '')}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return order


def main(argv: list[str] | None = None) -> int:
    """Name every theme in a build."""
    parser = argparse.ArgumentParser(prog="name_themes.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument(
        "--build",
        default="v0.2/recurrent_dag_single_banded",
        help="versioned method directory under data/ontology (default: %(default)s)",
    )
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("--workers", type=int, default=8, help="live concurrency")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="use the batch API at half price. Naming is SEQUENTIAL across ~20 levels and a batch "
        "takes hours, so this turns about 15 minutes into days. Available, not advised.",
    )
    parser.add_argument(
        "--smoke",
        type=int,
        metavar="N",
        help="name only a bottom-up CLOSED subset of N themes, for a readable sample",
    )
    parser.add_argument(
        "--second-model",
        metavar="MODEL",
        help="name every theme a second time with this model, for a blind comparison",
    )
    parser.add_argument(
        "--production-themes",
        type=int,
        default=7000,
        help="theme count to price a production run at (default: %(default)s)",
    )
    parser.add_argument("--submit", action="store_true", help="actually call the API")
    parser.add_argument("--max-dollars", type=float, default=DEFAULT_MAX_DOLLARS)
    args = parser.parse_args(argv)

    directory = args.data / "ontology" / args.build
    if not (directory / "nodes.tsv").is_file():
        print(f"no build at {directory}", file=sys.stderr)
        return 1
    parents, members = read_build(directory)
    full_themes = len(parents)
    if args.smoke:
        keep = set(smoke_sample(parents, args.smoke))
        parents = {n: [p for p in ps if p in keep] for n, ps in parents.items() if n in keep}
        members = {n: v for n, v in members.items() if n in keep}
        kids_now = children_of(parents)
        print(f"\nSMOKE: {len(parents)} themes of {full_themes:,} "
              f"({sum(1 for n in parents if not kids_now[n])} leaves, "
              f"{sum(1 for n in parents if kids_now[n])} internal), "
              "bottom-up closed, seed 20260924")
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")
    print(f"\nNAMING  {args.build}: {len(parents):,} themes, "
          f"{sum(1 for n in parents if not children_of(parents)[n]):,} leaves")

    ledger = Ledger.open(args.data / CACHE_DIR, args.model, NAME_PROMPT_VERSION)
    client = LLMClient(
        args.model, NAME_PROMPT_VERSION, ledger,
        response_format=NAME_FORMAT, response_key=NAME_RESPONSE_KEY,
    )

    _dry, requests = generate(client, parents, members, by_key, texts, args.workers, dry_run=True)
    n_disambig = sum(
        1 for n in parents if parents.get(n) or siblings_of(n, parents, children_of(parents))
    )
    # Sample ACROSS the requests, not the first N. Level 0 is emitted first and is all leaves,
    # which carry a full description per member; internal nodes carry three samples and a list of
    # short child names. Taking the first 40 prices the whole run at the leaf rate.
    step = max(1, len(requests) // 40)
    sample = requests[::step][:40]
    user_tokens = sum(client.count_tokens(r) for r in sample) / len(sample)
    # The API rejects an empty user message, so the system prompt is measured against a
    # single-character one and the difference is below the rounding of the estimate.
    system_tokens = client.count_tokens(Request(key="_", system=SYSTEM_PROMPT, user="."))
    estimate = price_batch(
        scope=len(requests) + n_disambig,
        pending=len(requests) + n_disambig,
        user_tokens=user_tokens,
        system_tokens=system_tokens,
        output_tokens=60,
        model=args.model,
        sampled=len(sample),
        basis="tokenizer",
    )
    live_low, live_high = estimate.cached_dollars * 2, estimate.uncached_dollars * 2
    print_table(
        ("item", "value", "note"),
        [
            ("themes to name", f"{len(requests):,}", "bottom-up, one call each"),
            ("disambiguation calls", f"{n_disambig:,}",
             "top-down, where a parent or sibling exists"),
            ("input/prompt", f"{user_tokens:,.0f}", "tok, measured by tokenizer on a sample"),
            ("system prompt", f"{system_tokens:,}", "tok, sent with every request"),
            ("batch cost, cached", f"${estimate.cached_dollars:,.2f}",
             "but ~20 sequential levels x hours"),
            ("batch cost, uncached", f"${estimate.uncached_dollars:,.2f}", "ceiling for --batch"),
            ("LIVE cost, cached", f"${live_low:,.2f}", "the default; ~15 min"),
            ("LIVE cost, uncached", f"${live_high:,.2f}", "ceiling, and what the gate checks"),
            ("ceiling", f"${args.max_dollars:,.2f}", "--max-dollars"),
        ],
    )
    models = [args.model] + ([args.second_model] if args.second_model else [])
    if len(models) > 1 or args.production_themes:
        calls = len(requests) + n_disambig
        per_theme = calls / max(len(parents), 1)
        prod_calls = args.production_themes * per_theme
        print()
        print_table(
            ("model", "this run (live)", f"production, {args.production_themes:,} themes (live)",
             "production (batch)"),
            [
                (
                    m,
                    f"${_cost(m, calls, user_tokens, system_tokens) * 2:,.2f}",
                    f"${_cost(m, prod_calls, user_tokens, system_tokens) * 2:,.2f}",
                    f"${_cost(m, prod_calls, user_tokens, system_tokens):,.2f}",
                )
                for m in models
            ],
        )
        print("  live is 2x batch; batch is impractical here (~20 sequential levels x hours).")
    worst = estimate.uncached_dollars if args.batch else live_high
    if not args.submit:
        print("\nnothing submitted; rerun with --submit")
        return 0
    if worst > args.max_dollars:
        print(f"\nrefusing: worst case ${worst:,.2f} exceeds --max-dollars "
              f"${args.max_dollars:,.2f}", file=sys.stderr)
        return 1
    if args.batch:
        print(
            f"\n--batch ({BATCH_CHUNK:,}-request chunks) is not implemented for the level-wise "
            "flow: naming is sequential across levels, so each level is its own batch and the "
            "run becomes days. Use the live default.",
            file=sys.stderr,
        )
        return 1

    per_model: dict[str, dict[str, dict]] = {}
    for model in models:
        print(f"\ngenerating (live) with {model}")
        mc = LLMClient(
            model,
            NAME_PROMPT_VERSION,
            Ledger.open(args.data / CACHE_DIR, model, NAME_PROMPT_VERSION),
            response_format=NAME_FORMAT,
            response_key=NAME_RESPONSE_KEY,
        )
        per_model[model], _ = generate(
            mc, parents, members, by_key, texts, args.workers, dry_run=False
        )
    client = LLMClient(
        args.model,
        NAME_PROMPT_VERSION,
        Ledger.open(args.data / CACHE_DIR, args.model, NAME_PROMPT_VERSION),
        response_format=NAME_FORMAT,
        response_key=NAME_RESPONSE_KEY,
    )
    generated = per_model[args.model]
    if len(models) > 1:
        blind = args.data / "keys" / "naming_blind.md"
        blind.parent.mkdir(parents=True, exist_ok=True)
        order = write_blind(blind, per_model, members, by_key)
        keyfile = args.data / "keys" / "naming_blind_key.tsv"
        keyfile.write_text(
            "node\tarm_A_then_B\n" + "".join(f"{n}\t{o}\n" for n, o in sorted(order.items())),
            encoding="utf-8",
        )
        print(f"\nblind comparison -> {blind}")
        print(f"key (do not open until read) -> {keyfile}")
    print("\ndisambiguating")
    # A DIFFERENT response schema: {action, name, reason}, not {nameable, name, rationale}.
    # Reusing the naming client here would enforce the wrong contract on every reply.
    disambig = LLMClient(
        args.model,
        NAME_PROMPT_VERSION,
        Ledger.open(args.data / CACHE_DIR, args.model, f"{NAME_PROMPT_VERSION}-disambig"),
        response_format=DISAMBIGUATION_FORMAT,
        response_key=DISAMBIGUATION_RESPONSE_KEY,
    )
    revised, touched_parents = disambiguate(disambig, parents, generated, args.workers)

    table = args.data / NAMES_TABLE
    rows = rows_for(generated, revised, parents, members, args.model)
    held = merge_tsv(table, names_table.NAME_COLUMNS, rows, key=names_table.ROW_KEY)
    marked, superseded = names_table.restamp(table, names_table.NAME_COLUMNS, NAME_PROMPT_VERSION)

    named = sum(1 for r in generated.values() if r.get("nameable"))
    refused = len(generated) - named
    revisions = sum(1 for r in revised.values() if r.get("revise"))
    failed = sum(1 for r in rows if r[7])
    print_table(
        ("item", "value", "note"),
        [
            ("themes named", f"{named:,}", ""),
            ("declared unnameable", f"{refused:,}", "a finding, not a failure"),
            ("names revised", f"{revisions:,}", "repeated a parent or collided with a sibling"),
            ("parents with a renamed child", f"{touched_parents:,}",
             "NOT regenerated; revisions are terminal"),
            ("failed a mechanical check", f"{failed:,}", "reported, never repaired"),
            ("rows in table", f"{held:,}", f"{marked:,} current, {superseded:,} earlier kept"),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
