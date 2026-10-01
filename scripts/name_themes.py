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
import hashlib
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
    LEAF_PROMPT_VERSION,
    NAME_FORMAT,
    NAME_PROMPT_VERSION,
    NAME_RESPONSE_KEY,
    SYSTEM_PROMPT,
    _norm,
    check,
    collisions,
    covers_children,
    invented_words,
    narrow_child,
    render_internal,
    render_leaf,
    theme_key,
)
from thema.ontology.order import children_of, naming_order

CACHE_DIR = "cache/names"

#: What a child contributes to its parent's prompt. 1 = its name alone; 2 = its name and the
#: rationale it returned when it was named. Part of the request key, so a change cannot be served
#: from entries made under the old rendering.
CHILD_RENDERING = 2
NAMES_TABLE = "theme_names.tsv"

#: name-v4 removed the "representative members" an internal node was shown. They were
#: ``member_keys[:3]`` in file order, so the word "representative" was not true of them, and three
#: arbitrary descriptions out of a 933-member theme competed with the children for attention. What a
#: parent adds is its DIRECT members, and those are now shown in full instead.

#: Refuse to submit above this worst-case price without being told otherwise.
DEFAULT_MAX_DOLLARS = 20.0


def read_names(path: Path, version: str | None = None) -> tuple[dict[str, dict], str]:
    """Names to REUSE from the table, and which version they came from.

    ``version=None`` takes whatever version is marked current, which is what a run under a NEW
    prompt version needs: asking for the new version returns nothing, every child looks unnamed,
    and --only-nodes then issues no requests at all. That is exactly what happened on the first
    name-v6 run.

    Args:
        path: ``theme_names.tsv``.
        version: A prompt version, or None for whichever is marked current.

    Returns:
        Node id to ``{"nameable", "name", "rationale"}``, and the version read.
    """
    if not path.is_file():
        return {}, ""
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle, delimiter="\t") if r["status"] == "current"]
    if version is None:
        present = {r["prompt_version"] for r in rows}
        version = sorted(present)[-1] if present else ""
    out: dict[str, dict] = {}
    for row in rows:
        if row["prompt_version"] != version:
            continue
        out[row["example_node"]] = {
            "nameable": row["nameable"] == "true",
            "name": row["name"],
            "rationale": row["rationale"],
        }
    return out, version


def read_build(
    directory: Path,
) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, dict[str, float]]]:
    """Read a build's structure.

    Args:
        directory: A versioned method directory holding ``nodes.tsv`` and ``members.tsv``.

    Returns:
        Node id to parent ids, node id to member pathway keys, and node id to each member's
        inclusion in the same order. v3 shows the model the inclusion of every member.
    """
    csv.field_size_limit(1 << 30)
    parents: dict[str, list[str]] = {}
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["node"]] = row["parents"].split()
    members: dict[str, list[str]] = defaultdict(list)
    inclusions: dict[str, dict[str, float]] = defaultdict(dict)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
            inclusions[row["node"]][row["key"]] = float(row["inclusion"])
    return parents, dict(members), dict(inclusions)


#: BTM modules whose title is literally "TBA" -- 83 of them, unannotated at source. A title that
#: says nothing is worse than no title: the model reads it as a member it must cover and cannot.
#: From level 1 onward such a member is rendered by its description alone. The LEAVES are not
#: re-rendered for this: they are already named and re-running them would spend money to change
#: prompts whose output has been read and judged.
UNTITLED = "TBA"


def _shown(title: str, description: str) -> tuple[str, str] | None:
    """How one member is rendered, or ``None`` if it cannot be rendered at all.

    Args:
        title: The pathway title.
        description: Its description.

    Returns:
        ``(title, description)``, or ``(first sentence, description)`` when the title is
        :data:`UNTITLED`, or ``None`` when there is neither a usable title nor a description.
    """
    if title.strip().upper() != UNTITLED:
        return title, description
    if not description or description.startswith("(no description"):
        return None
    head = description.split(". ")[0].strip().rstrip(".")
    return head, description


def _request_key(
    base: str, collides_with: str, invented: Sequence[str], narrow: str = ""
) -> str:
    """The cache key for a request, distinguishing a re-ask from the original.

    A re-ask sends different bytes, so it must not answer from the original's entry -- and two
    different re-asks of the same node must not answer from each other's.

    Args:
        base: The node's theme key.
        collides_with: A colliding name, if this is a collision re-ask.
        invented: Unsupported words, if this is an invented-word re-ask.
        narrow: The narrow-child instruction, if the parent took this node's name. Keyed on a digest
            of it, because it carries the parent's name and its added pathways -- change either and
            this is a different question.

    Returns:
        The key.
    """
    if narrow:
        return f"{base}:narrow:{hashlib.sha256(narrow.encode()).hexdigest()[:12]}"
    if collides_with:
        return f"{base}:collision:{_norm(collides_with)}"
    if invented:
        return f"{base}:invented:{'-'.join(sorted(invented))}"
    return base


def leaf_request(
    node: str,
    member_keys: list[str],
    by_key: dict,
    texts: dict[str, str],
    inclusions: dict[str, float] | None = None,
    collides_with: str = "",
    invented: Sequence[str] = (),
    narrow: str = "",
) -> Request:
    """Build the leaf prompt: title and description per pathway, nothing else.

    name-v5 sends no source tag, no inclusion and no identifier. ``inclusions`` is still accepted
    because it orders the members -- most strongly included first, so a truncated read still sees
    the centre of the theme -- but its values are not rendered.

    Args:
        node: Node id, for the caller's bookkeeping.
        member_keys: Member pathway keys.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.
        inclusions: Key to inclusion, for ordering only.
        collides_with: A colliding name, which turns this into the collision re-ask.
        invented: Unsupported words, which turn this into the invented-word re-ask.
        narrow: The narrow-child instruction, when this child's parent took its name.

    Returns:
        The request.
    """
    shares = inclusions or {}
    kept = sorted((k for k in member_keys if k in by_key), key=lambda k: (-shares.get(k, 1.0), k))
    shown = [
        row
        for k in kept
        if (row := _shown(by_key[k].name, texts.get(k, "(no description)"))) is not None
    ]
    return Request(
        key=_request_key(theme_key(member_keys), collides_with, invented, narrow),
        system=SYSTEM_PROMPT,
        user=render_leaf(shown, collides_with, invented, narrow),
    )


def internal_request(
    node: str,
    member_keys: list[str],
    child_names: Sequence[tuple[str, str]] | list[str],
    unnamed: int,
    by_key: dict,
    texts: dict[str, str],
    direct_keys: Sequence[str] = (),
    inclusions: dict[str, float] | None = None,
    collides_with: str = "",
    invented: Sequence[str] = (),
    narrow: str = "",
) -> Request:
    """Build the internal prompt: child names, then every direct pathway in full.

    Args:
        node: Node id, for the caller's bookkeeping.
        member_keys: Every member key, for the cache key.
        child_names: ``(name, rationale)`` per named child, or plain names. The pair form renders
            the child's rationale under its name; see :func:`thema.naming.render_internal`.
        unnamed: Children that came back unnameable. Recorded in the cache key so a node is
            regenerated once they are named, but NOT rendered: name-v5's user message is data only.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.
        direct_keys: Members belonging to no child.
        inclusions: Key to inclusion, for ordering only.
        collides_with: A colliding name, which turns this into the collision re-ask.
        invented: Unsupported words, which turn this into the invented-word re-ask.
        narrow: The narrow-child instruction, when this node's parent took its name.

    Returns:
        The request. The cache key carries the child names and the direct-member count, so a renamed
        child or a changed direct set forces regeneration.
    """
    shares = inclusions or {}
    kept = sorted((k for k in direct_keys if k in by_key), key=lambda k: (-shares.get(k, 1.0), k))
    direct = [
        row
        for k in kept
        if (row := _shown(by_key[k].name, texts.get(k, "(no description)"))) is not None
    ]
    # CHILD_RENDERING is part of the key. The rationale rendering sends different bytes for the
    # same members and the same child names, so without it a node would answer from the entry made
    # under the bare rendering -- the one the level-1 read found naming parents below their own
    # children. Bump it whenever what a child contributes to the prompt changes.
    flat = [c if isinstance(c, str) else c[0] for c in child_names]
    base = theme_key(
        member_keys,
        [*flat, f"direct:{len(direct)}", f"unnamed:{unnamed}", f"childrender:{CHILD_RENDERING}"],
    )
    return Request(
        key=_request_key(base, collides_with, invented, narrow),
        system=SYSTEM_PROMPT,
        user=render_internal(child_names, direct, collides_with, invented, narrow),
    )


def reask_invented(
    client: LLMClient,
    leaf_client: LLMClient,
    got: dict[str, dict],
    level: Sequence[str],
    kids: dict[str, list[str]],
    members: dict[str, list[str]],
    by_key: dict,
    texts: dict[str, str],
    inclusions: dict[str, dict[str, float]] | None,
    workers: int,
) -> dict[str, tuple[str, str, tuple[str, ...]]]:
    """Re-ask ONCE every name in this level that uses words the members never say.

    Same system prompt, same data, one added line. Mirrors the collision re-ask, and runs per level
    so a corrected name reaches the parent that will quote it.

    A re-asked name is accepted whatever it comes back as: the model may keep a genuine synonym, and
    the line says so. What is NOT done is a second re-ask or a hand edit -- one chance, then the
    result stands and its remaining flags are reported.

    Args:
        client: Client for internal nodes.
        leaf_client: Client for leaves.
        got: Node id to response, updated in place for names that change.
        level: The nodes just named.
        kids: Node id to child ids.
        members: Node id to member keys.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.
        inclusions: Node id to key to inclusion, for member ordering.
        workers: Concurrency.

    Returns:
        Node id to ``(before, after, the words flagged)``, for every node re-asked.
    """
    shares = inclusions or {}
    # ONCE means once. A node that already has an :invented: entry in either ledger has had its
    # re-ask, and 18 of the 283 leaves still flag after theirs -- re-asking those would bill a
    # second attempt at a name the model has already defended, and the rule is one chance.
    spent = {
        key.split(":invented:")[0]
        for led in (client.ledger, leaf_client.ledger)
        for key in led.keys()
        if ":invented:" in key
    }
    flagged: dict[str, tuple[str, tuple[str, ...]]] = {}
    for node in level:
        response = got.get(node)
        if not response or not response.get("nameable") or not response.get("name"):
            continue
        cs = kids.get(node, [])
        child_names = [
            got[c]["name"] for c in cs if got.get(c, {}).get("nameable") and got[c].get("name")
        ]
        cs_all = kids.get(node, [])
        covered = {k for c in cs_all for k in members.get(c, ())}
        n_direct = len([k for k in members.get(node, []) if k not in covered and k in by_key])
        base = (
            theme_key(
                members.get(node, []),
                [*child_names, f"direct:{n_direct}", f"unnamed:{len(cs_all) - len(child_names)}"],
            )
            if cs_all
            else theme_key(members.get(node, []))
        )
        if base in spent:
            continue
        words = invented_words(
            response["name"], corpus_for(node, members, by_key, texts, child_names)
        )
        if words:
            flagged[node] = (response["name"], words)
    if not flagged:
        return {}
    print(f"    invented-word re-ask: {len(flagged):,} of {len(level):,}", flush=True)
    requests, back = [], {}
    for node, (_name, words) in sorted(flagged.items()):
        cs = kids.get(node, [])
        child_names = [
            got[c]["name"] for c in cs if got.get(c, {}).get("nameable") and got[c].get("name")
        ]
        if cs:
            covered = {k for c in cs for k in members.get(c, ())}
            request = internal_request(
                node, members.get(node, []), child_names, len(cs) - len(child_names),
                by_key, texts, [k for k in members.get(node, []) if k not in covered],
                shares.get(node, {}), invented=words,
            )
        else:
            request = leaf_request(
                node, members.get(node, []), by_key, texts, shares.get(node, {}), invented=words,
            )
        requests.append(request)
        back[request.key] = node
    out: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    which = client if any(kids.get(n) for n in flagged) else leaf_client
    for rkey, parsed in run_level(which, requests, workers).items():
        node = back[rkey]
        before, words = flagged[node]
        if parsed.get("nameable") and parsed.get("name"):
            got[node] = parsed
            out[node] = (before, parsed["name"], words)
        else:
            out[node] = (before, before, words)
    return out


def corpus_for(
    node: str,
    members: dict[str, list[str]],
    by_key: dict,
    texts: dict[str, str],
    child_names: Sequence[str] = (),
) -> list[str]:
    """The members' own wording, for the invented-word check.

    Args:
        node: Node id.
        members: Node id to member keys.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.
        child_names: For an internal node, its children's names, which are part of what it may say.

    Returns:
        Titles, descriptions and child names.
    """
    out = list(child_names)
    for key in members.get(node, ()):
        if key in by_key:
            out.append(by_key[key].name)
            out.append(texts.get(key, ""))
    return out


def naming_clients(data: Path, model: str) -> tuple[LLMClient, LLMClient]:
    """The internal-node client and the leaf client, on their own prompt versions.

    Leaves are cached under :data:`LEAF_PROMPT_VERSION`, which name-v4 did NOT bump, because a leaf
    request is byte-identical to name-v3's: the shared system prompt and ``render_leaf`` are
    untouched and ``theme_key`` never depended on the version. Only the ledger FILE differs, so
    every leaf completion is reused and every internal node is a miss.

    Args:
        data: The data directory.
        model: The model id.

    Returns:
        ``(internal, leaf)``. They are the same object when the two versions are equal.
    """
    internal = LLMClient(
        model,
        NAME_PROMPT_VERSION,
        Ledger.open(data / CACHE_DIR, model, NAME_PROMPT_VERSION),
        response_format=NAME_FORMAT,
        response_key=NAME_RESPONSE_KEY,
    )
    if LEAF_PROMPT_VERSION == NAME_PROMPT_VERSION:
        return internal, internal
    leaf = LLMClient(
        model,
        LEAF_PROMPT_VERSION,
    _norm,
        Ledger.open(data / CACHE_DIR, model, LEAF_PROMPT_VERSION),
        response_format=NAME_FORMAT,
        response_key=NAME_RESPONSE_KEY,
    )
    return internal, leaf


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
    inclusions: dict[str, dict[str, float]] | None = None,
    leaf_client: LLMClient | None = None,
    max_level: int | None = None,
    only_nodes: set[str] | None = None,
    prior: dict[str, dict] | None = None,
) -> tuple[dict[str, dict], list[Request], dict[int, dict[str, tuple[str, str, tuple[str, ...]]]]]:
    """Bottom-up generation, level by level.

    Args:
        client: The caching client for INTERNAL nodes.
        parents: Node id to parent ids.
        members: Node id to member pathway keys.
        by_key: Pathway key to Pathway.
        texts: Pathway key to its description.
        workers: Concurrency.
        dry_run: Build every request but call nothing, so the run can be priced.
        inclusions: Node id to key to inclusion. v3 shows each member's inclusion; omit and the
            prompt reverts to unweighted members, which is what v2 sent.
        leaf_client: The caching client for LEAVES, opened on :data:`LEAF_PROMPT_VERSION`.
            Defaults to ``client``.
        only_nodes: Issue requests for these nodes ONLY. Every other node takes its name from
            ``prior``, so a run can re-name a named subset without re-billing the rest. A node in
            neither is left unnamed, exactly as a skipped level is.
        prior: Node id to a previous response, used for nodes outside ``only_nodes``.
        max_level: Stop after this level; 0 is the leaves alone. An internal node whose children
            are not all named is SKIPPED, not refused -- a refusal is a claim about biology and
            would be cached as one, while a skip simply leaves the node unnamed for a later run.
            Because a request is keyed by its members and its children's names, a later run at a
            higher level reuses every completion already in the ledger.

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
    leaves = leaf_client or client
    if only_nodes is not None:
        got.update({n: r for n, r in (prior or {}).items() if n not in only_nodes})
    skipped = 0
    invented: dict[int, dict[str, tuple[str, str, tuple[str, ...]]]] = {}
    for depth, level in enumerate(levels):
        if max_level is not None and depth > max_level:
            skipped += sum(len(rest) for rest in levels[depth:])
            print(f"  stopping at level {max_level}: {skipped:,} nodes left unnamed for a later "
                  "run (skipped, not refused)", flush=True)
            break
        requests, back, is_leaf = [], {}, {}
        for node in level:
            if only_nodes is not None and node not in only_nodes:
                continue
            cs = kids.get(node, [])
            if not cs:
                leaf = leaf_request(
                    node,
                    members.get(node, []),
                    by_key,
                    texts,
                    None if inclusions is None else inclusions.get(node, {}),
                )
                back[leaf.key] = node
                is_leaf[leaf.key] = True
                requests.append(leaf)
                continue
            named = [
                (got[c]["name"], got[c].get("rationale", ""))
                for c in cs
                if got.get(c, {}).get("nameable") and got[c].get("name")
            ]
            # A child that was SKIPPED (not yet run) leaves this node un-nameable for now. Skip it
            # too rather than naming a parent from a hole, and never record a refusal for it.
            if not dry_run and any(c not in got for c in cs):
                continue
            if dry_run and not named:  # nothing named yet; length is what pricing needs
                named = [(f"child theme {i}", "A placeholder rationale.") for i, _ in enumerate(cs)]
            unnamed = len(cs) - len(named)
            covered = {k for c in cs for k in members.get(c, [])}
            direct_keys = [k for k in members.get(node, []) if k not in covered]
            internal = internal_request(
                node,
                members.get(node, []),
                named,
                unnamed,
                by_key,
                texts,
                direct_keys,
                None if inclusions is None else inclusions.get(node, {}),
            )
            back[internal.key] = node
            requests.append(internal)
        every.extend(requests)
        if dry_run:
            continue
        print(f"  level {depth} ({'leaves' if depth == 0 else 'internal'}): "
              f"{len(requests):,} themes", flush=True)
        # Leaves and internal nodes are cached under DIFFERENT prompt versions, so each goes to its
        # own ledger. Routing is per request, not per level, so it stays correct if the level
        # structure ever changes.
        for group, which in (
            ([r for r in requests if is_leaf.get(r.key)], leaves),
            ([r for r in requests if not is_leaf.get(r.key)], client),
        ):
            if not group:
                continue
            for rkey, parsed in run_level(which, group, workers).items():
                got[back[rkey]] = parsed
        # INVENTED-WORD RE-ASK, once, before the next level sees these names. It runs here rather
        # than after the whole run because a parent's prompt carries its children's names: a
        # correction made after the fact would never reach the parent that quoted the old one.
        # Restricted to the nodes THIS run named. Without it the pass walked every node in the
        # level, including ones whose name came from the reused table -- under a new prompt version
        # every :invented: key is a miss, so 65 out-of-scope nodes were re-asked and the run went
        # 8% over an approved ceiling. The gate checks the estimate, so a scope error here costs
        # real money and is not caught.
        in_scope = [n for n in level if only_nodes is None or n in only_nodes]
        invented[depth] = reask_invented(
            client, leaves, got, in_scope, kids, members, by_key, texts, inclusions, workers
        )
    return got, every, invented


#: Members shown for a leaf in Task C, highest inclusion first.
LEAF_MEMBERS = 8


def top_members(
    node: str,
    members: dict[str, list[str]],
    inclusions: dict[str, dict[str, float]],
    by_key: dict,
    limit: int = LEAF_MEMBERS,
) -> list[tuple[str, float]]:
    """The node's most strongly included members as ``(name, inclusion)``, highest first.

    Args:
        node: Node id.
        members: Node id to member keys.
        inclusions: Node id to key to inclusion.
        by_key: Pathway key to pathway.
        limit: How many to return.

    Returns:
        Up to ``limit`` pairs. Ties break on the key, so the choice is reproducible.
    """
    shares = inclusions.get(node, {})
    keys = [k for k in members.get(node, ()) if k in by_key]
    keys.sort(key=lambda k: (-shares.get(k, 1.0), k))
    return [(by_key[k].name, shares.get(k, 1.0)) for k in keys[:limit]]


def parent_took_child(
    final: dict[str, str], kids: dict[str, list[str]]
) -> dict[str, str]:
    """Children whose name their own parent has taken.

    Under name-v6 this is permitted and is NOT a fault in the parent: if the child's name is the
    tightest true name for the parent too, the parent keeps it and the CHILD moves. Forbidding it
    was what drove a parent either to invent a difference or to name itself after its direct
    pathways, which the level-1 read found in 28 of 215 nodes.

    Args:
        final: Node id to its current name.
        kids: Node id to child ids.

    Returns:
        Child id to the parent id that took its name. A child with several such parents is reported
        against the first by id, so the pairing is deterministic.
    """
    out: dict[str, str] = {}
    for parent, children in sorted(kids.items()):
        if parent not in final:
            continue
        for child in sorted(children):
            if child in final and collisions(final[parent], [final[child]]) and child not in out:
                out[child] = parent
    return out


def narrow_displaced(
    client: LLMClient,
    leaf_client: LLMClient,
    final: dict[str, str],
    parents: dict[str, list[str]],
    kids: dict[str, list[str]],
    members: dict[str, list[str]],
    inclusions: dict[str, dict[str, float]],
    by_key: dict,
    texts: dict[str, str],
    workers: int,
) -> tuple[dict[str, dict], dict[str, str], list[tuple[str, str]]]:
    """Re-ask each child whose parent took its name, ONCE, for a narrower name.

    The child is shown its own data plus what the parent added, so the difference it must express is
    on the page rather than guessed at. If it declines, parent and child are recorded as
    ``same_theme`` and NOTHING is renamed: no difference is invented, and the landing page shows
    them merged.

    Args:
        client: Client for internal nodes.
        leaf_client: Client for leaves.
        final: Node id to current name, updated in place for children that narrow.
        parents: Node id to parent ids.
        kids: Node id to child ids.
        members: Node id to member keys.
        inclusions: Node id to key to inclusion.
        by_key: Pathway key to pathway.
        texts: Pathway key to description.
        workers: Concurrency.

    Returns:
        Child id to its response; child id to parent id for the pairs recorded ``same_theme``; and
        the ``(child, other parent)`` pairs NOT re-run -- a renamed child's other parents keep the
        name they were given against the child's old one, and that is reported, not fixed.
    """
    taken = parent_took_child(final, kids)
    if not taken:
        print("  no parent took a child's name", flush=True)
        return {}, {}, []
    print(f"  {len(taken)} parent(s) took a child's name; re-asking the CHILD", flush=True)
    requests, back = [], {}
    for child, parent in sorted(taken.items()):
        covered = {k for c in kids.get(parent, []) for k in members.get(c, ())}
        added = [
            row
            for k in members.get(parent, [])
            if k not in covered
            and k in by_key
            and (row := _shown(by_key[k].name, texts.get(k, "(no description)"))) is not None
        ]
        line = narrow_child(final[parent], added)
        cs = kids.get(child, [])
        if cs:
            child_kids = [
                (final[c], "") for c in cs if c in final
            ]
            own_covered = {k for c in cs for k in members.get(c, ())}
            request = internal_request(
                child, members.get(child, []), child_kids, len(cs) - len(child_kids),
                by_key, texts, [k for k in members.get(child, []) if k not in own_covered],
                inclusions.get(child, {}), narrow=line,
            )
        else:
            request = leaf_request(
                child, members.get(child, []), by_key, texts, inclusions.get(child, {}),
                narrow=line,
            )
        requests.append(request)
        back[request.key] = child
    out: dict[str, dict] = {}
    merged: dict[str, str] = {}
    which = client if any(kids.get(c) for c in taken) else leaf_client
    for rkey, parsed in run_level(which, requests, workers).items():
        child = back[rkey]
        out[child] = parsed
        if parsed.get("nameable") and parsed.get("name"):
            final[child] = parsed["name"]
        else:
            merged[child] = taken[child]
    # A renamed child may have OTHER parents, named while it still held its old name. They are not
    # re-run: doing so would cascade up the DAG on every rename. Reported instead.
    stale = [
        (child, other)
        for child in out
        if child not in merged
        for other in parents.get(child, ())
        if other != taken[child] and other in final
    ]
    return out, merged, sorted(stale)


def find_collisions(
    final: dict[str, str], parents: dict[str, list[str]]
) -> dict[str, tuple[tuple[str, ...], bool]]:
    """Every name that mechanically collides, found by string comparison alone.

    This replaces name-v3's full disambiguation pass, which sent 806 of that run's 1,676 calls to
    ask a question two string comparisons answer.

    Args:
        final: Node id to its current name.
        parents: Node id to parent ids.

    Returns:
        Node id to ``(the identical names elsewhere, whether it repeats a parent)``, for colliding
        nodes only. A node absent from the mapping needs no call.
    """
    out: dict[str, tuple[tuple[str, ...], bool]] = {}
    for node, name in final.items():
        elsewhere = collisions(name, [v for n, v in final.items() if n != node])
        repeats = bool(collisions(name, [final[p] for p in parents.get(node, ()) if p in final]))
        if elsewhere or repeats:
            out[node] = (elsewhere, repeats)
    return out


def disambiguate(
    client: LLMClient,
    parents: dict[str, list[str]],
    generated: dict[str, dict],
    workers: int,
    members: dict[str, list[str]],
    inclusions: dict[str, dict[str, float]],
    by_key: dict,
    texts: dict[str, str],
) -> tuple[dict[str, dict], dict[str, int]]:
    """Re-ask the model ONLY about names that mechanically collide.

    Detection is string comparison: a name identical to another anywhere in the DAG, or identical to
    one of its own parents. Everything else is left alone, which is the name-v4 change -- the full
    pass cost more than half the run and made the result worse, creating 20 duplicates, narrowing
    parents below their own children, and producing one false refusal.

    A replacement for a node WITH CHILDREN is accepted only if it still covers every child's name,
    checked by :func:`thema.naming.covers_children`. A replacement that fails is DISCARDED and the
    colliding original kept, because a parent narrower than its own children states something false
    about the hierarchy while a duplicate only reads badly. Every discard is reported.

    Args:
        client: The caching client.
        parents: Node id to parent ids.
        generated: Node id to its generated response.
        workers: Concurrency.
        members: Node id to member keys.
        inclusions: Node id to key to inclusion.
        by_key: Pathway key to pathway.
        texts: Pathway key to description -- the re-ask resends the same data.

    Returns:
        Node id to the response, and a tally: ``asked``, ``revised``, ``rejected_narrowing``,
        ``unresolved`` and the collisions still standing afterwards.
    """
    kids = children_of(parents)
    final = {n: r["name"] for n, r in generated.items() if r.get("nameable") and r.get("name")}
    colliding = find_collisions(final, parents)
    out: dict[str, dict] = {}
    tally = {"asked": len(colliding), "revised": 0, "rejected_narrowing": 0, "unresolved": 0}
    if not colliding:
        print("  no mechanical collisions; nothing re-asked", flush=True)
        return out, {**tally, "collisions_before": 0, "collisions_after": 0}
    print(f"  {len(colliding):,} colliding names of {len(final):,} -- only these are re-asked",
          flush=True)
    requests, back = [], {}
    for node, (_elsewhere, _repeats) in sorted(colliding.items()):
        # name-v5: NO separate prompt. The same system prompt and the same data, plus one line
        # naming the collision. A node is re-asked exactly as it was asked.
        child_names = [final[c] for c in kids.get(node, []) if c in final]
        if child_names:
            covered = {k for c in kids.get(node, []) for k in members.get(c, ())}
            request = internal_request(
                node,
                members.get(node, []),
                child_names,
                len(kids.get(node, [])) - len(child_names),
                by_key,
                texts,
                [k for k in members.get(node, []) if k not in covered],
                inclusions.get(node, {}),
                collides_with=final[node],
            )
        else:
            request = leaf_request(
                node, members.get(node, []), by_key, texts, inclusions.get(node, {}),
                collides_with=final[node],
            )
        requests.append(request)
        back[request.key] = node
    for rkey, parsed in run_level(client, requests, workers).items():
        node = back[rkey]
        out[node] = parsed
        if not (parsed.get("nameable") and parsed.get("name")):
            tally["unresolved"] += 1
            continue
        child_names = [final[c] for c in kids.get(node, []) if c in final]
        if not covers_children(parsed["name"], child_names):
            tally["rejected_narrowing"] += 1
            out[node] = {**parsed, "revise": False, "rejected": "would not cover every child"}
            continue
        final[node] = parsed["name"]
        out[node] = {**parsed, "revise": True}
        tally["revised"] += 1
    after = find_collisions(final, parents)
    return out, {**tally, "collisions_before": len(colliding), "collisions_after": len(after)}


#: The provider's minimum system-prompt length for prompt caching. Below it nothing is cached, so
#: the cached and uncached quotes are the same number and the table must not imply a discount.
MIN_CACHEABLE_TOKENS = 1024

#: Output tokens per naming call. MEASURED, never assumed. 60 was a guess; 112 was measured over
#: 820 real name-v2 Sonnet calls; 136 is the mean over the 90 calls of the name-v3 input pilot on
#: 27 Sep, and name-v3 is what runs now. The rise is the widened length bound being used -- 17 of
#: those 90 names exceed six words, which v2 could not produce.
OUTPUT_TOKENS = 136

#: What the provider's prompt cache actually holds, measured on the same run: the system prompt
#: plus the worked-examples preamble that opens every user message. It exceeds the system prompt
#: alone, which is why this is measured rather than derived.
CACHED_TOKENS = 1180


def _cost(model: str, calls: float, user_tokens: float, system_tokens: int) -> float:
    """Batch-rate cost of a run, with prompt caching priced as the API actually bills it.

    **The previous version claimed caching in its docstring and did not apply it**, charging every
    token of every call at the full input rate and then adding the system prompt once more. It
    over-quoted the 808-theme run by 40%. Cached reads bill at 0.1x and the one-off writes at
    1.25x, so the cached portion is nearly free rather than nearly free-of-charge-once.

    **This still prices REQUESTS, not cache misses.** A run whose prompts repeat -- a top-up, a
    re-run, anything the content-addressed ledger already holds -- costs less than this says, and
    the 808-theme run came in at $6.60 against $11.91 for exactly that reason. It is an upper
    bound, and it is meant to be.

    Args:
        model: A key of :data:`thema.llm.PRICES`.
        calls: How many requests.
        user_tokens: Mean input tokens per request, INCLUDING the system prompt, as
            ``count_tokens`` reports it.
        system_tokens: The system prompt. Kept for the caller's reporting; the cached share is
            :data:`CACHED_TOKENS`, which is larger.

    Returns:
        Dollars at the batch rate. Double it for live.
    """
    from thema.llm import PRICES

    rate_in, rate_out = PRICES[model]
    cached = min(CACHED_TOKENS, user_tokens)
    uncached = max(0.0, user_tokens - cached)
    dollars = (
        calls * uncached * rate_in
        + calls * cached * rate_in * 0.1
        + 20 * cached * rate_in * 1.25          # cache re-writes over a run, 5-minute TTL
        + calls * OUTPUT_TOKENS * rate_out
    ) / 1e6
    return dollars * 0.5


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
    by_key: dict | None = None,
    merged: dict[str, str] | None = None,
) -> list[tuple[str, ...]]:
    """Render the names table's rows.

    Args:
        generated: Node id to its generation response.
        revised: Node id to its disambiguation response.
        parents: Node id to parent ids.
        members: Node id to member pathway keys.
        model: The model that produced them.
        merged: Child id to the parent it shares a name with, for children that declined to
            narrow. Written to ``same_theme`` and NOT resolved: nothing invents a difference.
        by_key: Pathway key to pathway. Needed for two checks that CANNOT FIRE WITHOUT IT, and did
            not fire in the first name-v3 run: ``copies_member`` compares the name against member
            NAMES and was being handed member keys, and ``duplicate_name`` needs the final name set.

    Returns:
        Rows in :data:`thema.data.names.NAME_COLUMNS` order, keyed by THEME KEY so a rebuild
        reuses every name whose theme is unchanged.
    """
    kids = children_of(parents)
    # The final name of every theme, AFTER revisions. Built first because duplicate_name is a
    # property of the whole set and cannot be evaluated one row at a time. The first name-v3 run
    # reported 36 mechanical failures against a true 56: it never passed `taken`, so the check
    # added for exactly this purpose was inert, and every one of the 20 duplicates it would have
    # caught was created by the disambiguation pass revising two themes onto one name.
    settled: dict[str, str] = {}
    for node, response in generated.items():
        if not response.get("nameable") or not response.get("name"):
            continue
        rev = revised.get(node, {})
        settled[node] = (
            rev["name"] if rev.get("revise") and rev.get("name") else response["name"]
        )
    same = merged or {}
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
            member_names = [
                by_key[k].name if by_key and k in by_key else str(k)
                for k in members.get(node, [])
            ]
            result = check(
                name,
                member_names,
                taken=[v for n, v in settled.items() if n != node],
            )
            failed = tuple(
                f for f in ("in_range", "sentence_case") if not getattr(result, f)
            ) + tuple(
                f
                for f in (
                    "leading_article",
                    "trailing_punctuation",
                    "bare_category",
                    "copies_member",
                    "duplicate_name",
                )
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
                same.get(node, ""),
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
    # Sonnet by default: it named 808 themes for $6.60 with 8 unnameable, and the
    # three-model comparison on 23 Sep found no quality gap that justified Opus here.
    parser.add_argument("--model", default="claude-sonnet-5")
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
    parser.add_argument(
        "--reuse-version", default=None, metavar="V",
        help="prompt version whose names are reused for nodes outside --only-nodes "
             "(default: whichever is current in the table)",
    )
    parser.add_argument(
        "--only-nodes", nargs="+", default=None, metavar="ID",
        help="name ONLY these node ids; every other node keeps its current name",
    )
    parser.add_argument(
        "--max-level", type=int, default=None, metavar="N",
        help="name only up to level N (0 = leaves); higher levels reuse the ledger later",
    )
    parser.add_argument("--submit", action="store_true", help="actually call the API")
    parser.add_argument("--max-dollars", type=float, default=DEFAULT_MAX_DOLLARS)
    args = parser.parse_args(argv)

    directory = args.data / "ontology" / args.build
    if not (directory / "nodes.tsv").is_file():
        print(f"no build at {directory}", file=sys.stderr)
        return 1
    parents, members, inclusions = read_build(directory)
    only_nodes = set(args.only_nodes) if args.only_nodes else None
    prior, prior_version = read_names(args.data / NAMES_TABLE, args.reuse_version)
    if only_nodes is not None:
        missing = sorted(only_nodes - set(parents))
        if missing:
            print(f"not in this build: {', '.join(missing)}", file=sys.stderr)
            return 1
        print(f"  --only-nodes: {len(only_nodes)} nodes; the other "
              f"{len(parents) - len(only_nodes):,} keep their current name "
              f"({len(prior):,} reused from {prior_version or 'nothing'})")
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

    client, leaf_client = naming_clients(args.data, args.model)

    _dry, requests, _inv = generate(
        client,
        parents,
        members,
        by_key,
        texts,
        args.workers,
        dry_run=True,
        inclusions=inclusions,
        leaf_client=leaf_client,
        max_level=args.max_level,
        only_nodes=only_nodes,
        prior=prior,
    )
    # name-v4 re-asks ONLY about names that mechanically collide, which cannot be counted before
    # the names exist. v3 sent one call per theme with a parent or sibling -- 806 of its 1,676
    # calls -- and its own output, scored by v4's detector, collides on just 20 names (2.3%).
    # Pricing at the v3 rate would quote 48% of the run for calls v4 will not make, so the estimate
    # uses the measured rate and says that it is an estimate.
    DISAMBIG_RATE = 0.023
    # PRICE THE MARGINAL, not the scope. A level-1 run re-issues all 287 leaf requests, every one
    # of which the ledger already holds; charging for them quotes $4.41 for about $1.40 of new
    # calls. The ledger is content-addressed, so what a run costs is exactly what is not in it.
    held = leaf_client.ledger, client.ledger
    cached_already = sum(1 for r in requests if any(r.key in led for led in held))
    pending = [r for r in requests if not any(r.key in led for led in held)]
    # Scaled to the themes THIS run names, not the whole build: --max-level 0 names 287 leaves of
    # 800, and charging the collision rate against 800 would over-quote it nearly threefold.
    n_disambig = round(len(pending) * DISAMBIG_RATE)
    # The invented-word re-ask applies to EVERY name this level produces, cached or not: the check
    # runs over the level's names, and a name served from the ledger is still checked. So this is
    # scaled to the themes named, not to the new calls -- which is why a fully cached level still
    # costs something. Rate measured on the 283 name-v5 leaf names: 45 flagged, 15.9%.
    INVENTED_RATE = 0.159
    # Only NEW names can produce a re-ask. A cached name has already been through the check: it
    # either passed -- and the check is deterministic, so it passes again -- or it was re-asked and
    # will not be again. Scaling to all 502 at level 1 quoted 80 re-asks when at most 215 names are
    # even eligible.
    n_invented = round(len(pending) * INVENTED_RATE)
    # name-v6: at most one child re-ask per node named, since a parent takes at most one child's
    # name. Quoted at the BOUND rather than a rate: the rate is unmeasured, this is the first run.
    n_narrow = len(pending)
    # Sample ACROSS the requests, not the first N. Level 0 is emitted first and is all leaves,
    # which carry a full description per member; internal nodes carry three samples and a list of
    # short child names. Taking the first 40 prices the whole run at the leaf rate.
    step = max(1, max(len(pending), 1) // 40)
    sample = (pending or requests)[::step][:40]
    # The API rejects an empty user message, so the system prompt is measured against a
    # single-character one and the difference is below the rounding of the estimate.
    system_tokens = client.count_tokens(Request(key="_", system=SYSTEM_PROMPT, user="."))
    # SUBTRACT the system prompt. price_batch's contract is that user_tokens is the user message
    # ALONE -- it adds the system prompt back itself, as a cached read or an uncached one. This
    # caller passed the full count_tokens(request), which already contains the system prompt, so
    # the system prompt was billed twice and the gate line over-quoted the run by 29%. The other
    # three callers of price_batch all subtract it; this one did not.
    user_tokens = max(
        0.0, sum(client.count_tokens(r) for r in sample) / len(sample) - system_tokens
    )
    estimate = price_batch(
        scope=len(requests) + n_disambig + n_invented + n_narrow,
        pending=len(pending) + n_disambig + n_invented + n_narrow,
        user_tokens=user_tokens,
        system_tokens=system_tokens,
        output_tokens=OUTPUT_TOKENS,
        model=args.model,
        sampled=len(sample),
        basis="tokenizer",
    )
    # PROMPT CACHING HAS A FLOOR. The provider does not cache a system prompt below
    # MIN_CACHEABLE_TOKENS, so quoting the cached rate for a short prompt understates the bill --
    # name-v5's 577-token prompt cached NOTHING and its level-0 run came in 24% over a cached
    # quote. When the prompt is too short, the cached line IS the uncached line, and the table says
    # so rather than the reader discovering it from the invoice. The prompt is not padded to reach
    # the floor: a prompt's length should be decided by what it has to say.
    cacheable = system_tokens >= MIN_CACHEABLE_TOKENS
    live_low = (estimate.cached_dollars if cacheable else estimate.uncached_dollars) * 2
    live_high = estimate.uncached_dollars * 2
    print_table(
        ("item", "value", "note"),
        [
            ("themes to name", f"{len(requests):,}", "bottom-up, one call each"),
            ("already in the ledger", f"{cached_already:,}",
             "free; only the rest is billed" if cached_already else "nothing cached yet"),
            ("new calls", f"{len(pending):,}", "what this run actually costs"),
            ("child re-asks, at most", f"{n_narrow:,}",
             "one per node: a parent takes at most one child's name"),
            ("invented-word re-asks", f"~{n_invented:,}",
             f"ESTIMATE at {INVENTED_RATE:.1%} of the {len(pending):,} new names; a cached name "
             "was already checked"),
            ("collision re-asks", f"~{n_disambig:,}",
             f"ESTIMATE at 2.3% of the {len(requests):,} named here; v3's own collision rate"),
            ("input/prompt", f"{user_tokens:,.0f}", "tok, measured by tokenizer on a sample"),
            ("system prompt", f"{system_tokens:,}", "tok, sent with every request"),
            ("batch cost, cached", f"${estimate.cached_dollars:,.2f}",
             "but ~20 sequential levels x hours"),
            ("batch cost, uncached", f"${estimate.uncached_dollars:,.2f}", "ceiling for --batch"),
            (
                "LIVE cost, cached" if cacheable else "LIVE cost, NO caching",
                f"${live_low:,.2f}",
                "the default; ~15 min" if cacheable
                else f"system prompt {system_tokens:,} tok < {MIN_CACHEABLE_TOKENS:,} minimum",
            ),
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
                    # _cost's contract is the TOTAL per request, system prompt included;
                    # price_batch's is the user message alone. Feed each the one it names.
                    f"${_cost(m, calls, user_tokens + system_tokens, system_tokens) * 2:,.2f}",
                    f"${_cost(m, prod_calls, user_tokens + system_tokens, system_tokens) * 2:,.2f}",
                    f"${_cost(m, prod_calls, user_tokens + system_tokens, system_tokens):,.2f}",
                )
                for m in models
            ],
        )
        print("  live is 2x batch; batch is impractical here (~20 sequential levels x hours).")
        # The two models above disagree and the disagreement is now calibrated rather than argued.
        # CALIBRATED against the 90-call name-v3 input pilot of 27 Sep, actual bill $0.72:
        # price_batch cached x2 predicted $0.69 (-5%), _cost x2 predicted $0.89 (+24%), and the
        # uncached ceiling $1.09 (+51%). _cost charges 20 cache re-writes for the 5-minute TTL over
        # a level-wise run; the provider re-wrote far fewer. Trust LIVE cost cached; read this row
        # as conservative and the uncached line as the ceiling it is meant to be.
        print(
            "  calibration, 90-call name-v3 pilot billed $0.72: 'LIVE cost, cached' model was "
            "5% low,\n  this row 24% high, the uncached ceiling 51% high. The cached line is the "
            "one to plan against."
        )
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
        mc, mc_leaf = naming_clients(args.data, model)
        per_model[model], _reqs, invented = generate(
            mc,
            parents,
            members,
            by_key,
            texts,
            args.workers,
            dry_run=False,
            inclusions=inclusions,
            leaf_client=mc_leaf,
            max_level=args.max_level,
            only_nodes=only_nodes,
            prior=prior,
        )
    client, _leaf = naming_clients(args.data, args.model)
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
    # name-v5 re-asks with the SAME prompt and the same response contract, so the collision calls
    # share the naming ledger: a re-ask is keyed by the colliding name and cannot collide with the
    # original request for the same node.
    collision_client, _cl = naming_clients(args.data, args.model)
    # name-v6: a parent may take its child's name, and the CHILD is then re-asked for a narrower
    # one. This runs BEFORE the ordinary collision pass, because it resolves parent-child pairs
    # that pass would otherwise try to fix by moving the parent.
    final_names = {
        n: r["name"] for n, r in generated.items() if r.get("nameable") and r.get("name")
    }
    narrowed, merged, stale_parents = narrow_displaced(
        client, _leaf, final_names, parents, children_of(parents), members, inclusions,
        by_key, texts, args.workers,
    )
    for node, response in narrowed.items():
        if response.get("nameable") and response.get("name"):
            generated[node] = response
    if merged:
        print(f"  {len(merged)} child(ren) declined to narrow; recorded as same_theme: "
              + ", ".join(f"{c}={p}" for c, p in sorted(merged.items())))
    if stale_parents:
        print(f"  {len(stale_parents)} other parent(s) of a renamed child NOT re-run: "
              + ", ".join(f"{c}<-{o}" for c, o in stale_parents))

    revised, tally = disambiguate(
        collision_client, parents, generated, args.workers, members, inclusions, by_key, texts
    )

    table = args.data / NAMES_TABLE
    rows = rows_for(generated, revised, parents, members, args.model, by_key, merged)
    held = merge_tsv(table, names_table.NAME_COLUMNS, rows, key=names_table.ROW_KEY)
    marked, superseded = names_table.restamp(table, names_table.NAME_COLUMNS, NAME_PROMPT_VERSION)

    changed_by_invented = sum(
        1 for level in invented.values() for before, after, _w in level.values() if before != after
    )
    named = sum(1 for r in generated.values() if r.get("nameable"))
    refused = len(generated) - named
    revisions = sum(1 for r in revised.values() if r.get("revise"))
    failed = sum(1 for r in rows if r[7])
    print_table(
        ("item", "value", "note"),
        [
            ("themes named", f"{named:,}", ""),
            ("declared unnameable", f"{refused:,}", "a finding, not a failure"),
            ("Task C calls", f"{tally['asked']:,}",
             "ONLY mechanically colliding names, not every theme"),
            ("names revised", f"{revisions:,}", "a duplicate elsewhere, or a repeat of a parent"),
            ("revisions rejected", f"{tally['rejected_narrowing']:,}",
             "would not cover every child; original kept"),
            ("collisions unresolved", f"{tally['collisions_after']:,}",
             f"of {tally['collisions_before']:,} before; reported, never repaired"),
            ("parent took a child's name", f"{len(narrowed):,}",
             "the CHILD was re-asked narrower, not the parent"),
            ("children merged (same_theme)", f"{len(merged):,}",
             "declined to narrow; no difference invented"),
            ("other parents not re-run", f"{len(stale_parents):,}",
             "listed above; a rename does not cascade"),
            ("invented-word re-asks", f"{sum(len(v) for v in invented.values()):,}",
             "a word no member says; re-asked once, never edited"),
            ("names changed by it", f"{changed_by_invented:,}",
             "the rest kept a genuine synonym"),
            ("failed a mechanical check", f"{failed:,}", "reported, never repaired"),
            ("rows in table", f"{held:,}", f"{marked:,} current, {superseded:,} earlier kept"),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
