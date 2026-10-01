"""Naming test 2: can the hierarchy be reconstructed from the names alone?

**A GATE on the named build** (`docs/spec/validation-plan.md`, amended 25 Sep). A hierarchy whose
edges cannot be recovered from its own names is not usable as an ontology whatever its member sets
look like: a reader navigating by name would not find the structure the members encode.

The test shows a model two theme NAMES and nothing else -- no members, no sizes, no descriptions --
and asks whether the first is a parent of the second. Every true edge is asked, and an equal number
of non-edges drawn from **the same level-pair distribution**, so the control differs from the
positives only in whether the edge exists. Without that matching a model could score well by
learning "broad names sit above narrow ones", which is a property of the level pairing rather than
of the edge.

The chance rate is 50% by construction. Disagreements are kept: a true edge the model rejects, or a
non-edge it accepts, is a review item for the HIERARCHY as much as for the name.
"""

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from thema.llm import Ledger, LLMClient, Request

CACHE_DIR = "cache/name_dag"
PROMPT_VERSION = "dag-v1"

SYSTEM_PROMPT = """\
You are given two names of themes from a hierarchy of human biological pathways. A theme is a group
of related pathways. A parent theme is BROADER than its child and contains everything the child
contains, plus more.

Answer one question: is the first name a parent of the second?

Judge only from the two names. You have no other information and should not assume any.

Answer true when the first is a genuinely broader theme that would contain the second. Answer false
when they are unrelated, when they are siblings at the same level of generality, when they are the
same theme said differently, or when the SECOND is the broader of the two.
"""

#: ``parent`` is a BOOLEAN and is also the response key, for the reason recorded in
#: ``thema.naming``: ``llm.extract_text`` returns the whole parsed object only when the keyed field
#: is not a string, so keying on a string field would throw the rest of the reply away.
RESPONSE_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "parent": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["parent", "reason"],
        "additionalProperties": False,
    },
}


def load(directory: Path, names_table: Path) -> tuple[dict, dict, list]:
    """Read the build's edges and its names.

    Args:
        directory: The build directory.
        names_table: ``theme_names.tsv``.

    Returns:
        Node id to name, node id to depth, and the ``(child, parent)`` edges.
    """
    rows = list(csv.DictReader((directory / "nodes.tsv").open(encoding="utf-8"), delimiter="\t"))
    parents = {r["node"]: [p for p in r["parents"].replace(",", " ").split() if p] for r in rows}
    named = {
        r["example_node"]: r["name"]
        for r in csv.DictReader(names_table.open(encoding="utf-8"), delimiter="\t")
        if r["status"] == "current" and r["nameable"] == "true"
    }
    depth: dict[str, int] = {}

    def at(node: str) -> int:
        if node not in depth:
            above = parents[node]
            depth[node] = 0 if not above else 1 + max(at(p) for p in above)
        return depth[node]

    for node in parents:
        at(node)
    edges = [(child, parent) for child, above in parents.items() for parent in above]
    return named, depth, edges


def controls(
    edges: Sequence[tuple[str, str]], depth: dict[str, int], named: dict[str, str], seed: int
) -> list[tuple[str, str]]:
    """Draw one non-edge per true edge, matched on the (parent depth, child depth) pair.

    Matching the level pair is what makes the control informative: an unmatched control could be
    rejected on generality alone, which every name carries and no edge needs.

    Args:
        edges: The true ``(child, parent)`` edges.
        depth: Node depths.
        named: Node id to name, restricted to nameable nodes.
        seed: For reproducibility.

    Returns:
        ``(child, parent)`` pairs that are NOT edges.
    """
    rng = random.Random(seed)
    real = set(edges)
    by_depth: dict[int, list[str]] = defaultdict(list)
    for node in named:
        by_depth[depth[node]].append(node)
    out: list[tuple[str, str]] = []
    for child, parent in edges:
        for _ in range(200):
            other_child = rng.choice(by_depth[depth[child]])
            other_parent = rng.choice(by_depth[depth[parent]])
            if other_child == other_parent or (other_child, other_parent) in real:
                continue
            out.append((other_child, other_parent))
            break
    return out


def main(argv: Sequence[str] | None = None) -> int:
    """Price the test, and run it under --submit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--build", default="v0.2/recurrent_dag_consensus")
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--max-dollars", type=float, default=5.0)
    args = parser.parse_args(argv)

    directory = args.data / "ontology" / args.build
    named, depth, edges = load(directory, args.data / "theme_names.tsv")
    edges = [(c, p) for c, p in edges if c in named and p in named]
    fakes = controls(edges, depth, named, args.seed)
    print(f"  {len(edges):,} true edges, {len(fakes):,} matched non-edges, "
          f"{len(named):,} named themes")

    from thema.llm import PRICES
    rate_in, rate_out = PRICES[args.model]
    per_call_in = 40 + 380
    calls = len(edges) + len(fakes)
    worst = (calls * per_call_in * rate_in + calls * 20 * rate_out) / 1e6
    print(f"  {calls:,} calls, worst case ${worst:,.2f} (ceiling ${args.max_dollars:,.2f})")
    if not args.submit:
        print("\n  nothing submitted; rerun with --submit")
        return 0
    if worst > args.max_dollars:
        print(f"\n  refusing: ${worst:,.2f} exceeds --max-dollars", file=sys.stderr)
        return 1

    ledger = Ledger.open(args.data / CACHE_DIR, args.model, PROMPT_VERSION)
    client = LLMClient(args.model, PROMPT_VERSION, ledger,
                       response_format=RESPONSE_FORMAT, response_key="parent")
    asked = [(c, p, True) for c, p in edges] + [(c, p, False) for c, p in fakes]
    results = []
    def ask(item: tuple[str, str, bool]) -> tuple[str, str, bool, bool] | None:
        child, parent, truth = item
        request = Request(
            key=f"{parent}>{child}",
            system=SYSTEM_PROMPT,
            user=f'First name: "{named[parent]}"\nSecond name: "{named[child]}"\n\n'
                 f"Is the first a parent of the second?",
        )
        try:
            said = bool(json.loads(client.complete(request).text)["parent"])
        except Exception as exc:  # noqa: BLE001
            print(f"    {parent}>{child}: {type(exc).__name__}", file=sys.stderr)
            return None
        return (child, parent, truth, said)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for got in pool.map(ask, asked):
            if got is not None:
                results.append(got)

    hits = [r for r in results if r[2]]
    misses = [r for r in results if not r[2]]
    recall = sum(1 for r in hits if r[3]) / max(len(hits), 1)
    false_positive = sum(1 for r in misses if r[3]) / max(len(misses), 1)
    print(f"\n  answered {len(results):,} of {len(asked):,}")
    print(f"  EDGE RECOVERY (recall on true edges)  {recall:.1%}")
    print(f"  false positives on matched non-edges  {false_positive:.1%}")
    print(f"  accuracy                              "
          f"{(sum(1 for r in hits if r[3]) + sum(1 for r in misses if not r[3]))/len(results):.1%}")
    print("  chance, by construction               50.0%")
    out = args.data / "keys" / "name_dag_disagreements.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(("kind", "parent", "parent_name", "child", "child_name"))
        for child, parent, truth, said in results:
            if truth != said:
                writer.writerow((
                    "missed_edge" if truth else "false_edge",
                    parent, named[parent], child, named[child],
                ))
    print(f"  disagreements -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
