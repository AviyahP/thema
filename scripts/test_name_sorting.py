"""Naming test 1: given only the theme names, can a pathway be placed in the right theme?

A GATE on the named build. Test 2 asks whether the names encode the HIERARCHY; this asks the prior
question -- whether a name describes its own contents. If this passes and test 2 fails, the names
are sound and the hierarchy is what cannot be expressed in them.

Three levels, each a separate task: the 16 roots, the 91 themes at level 1, and the FINEST level --
each pathway's smallest containing theme, a 456-way discrimination.

**Scoring, declared before the run.** At levels 0 and 1 a pathway is scored against EVERY theme at
that level containing it, since a pathway sits in several; "none of these" is correct for the 524
pathways absent from that level. At the finest level the target is the single smallest containing
theme, and "none" is correct when that theme is one of the 7 unnameable. No pathway is dropped at
any level, and the "none" cases are reported separately so they cannot inflate the score.

Pathway DESCRIPTIONS are shown, not pathway names: the theme names were generated partly from
member pathway names, so sorting by name would be the circular version of this test.
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
from thema.llm import PRICES, Ledger, LLMClient, Request

CACHE_DIR = "cache/name_sort"
PROMPT_VERSION = "sort-v1"
BATCH = 25

SYSTEM_PROMPT = """\
You are given a numbered list of THEME names from an ontology of human biological pathways, and a
numbered list of pathway DESCRIPTIONS.

For each pathway, say which theme it belongs to, judging only from the theme's name and the
pathway's description.

A pathway may belong to no theme on the list. Answer 0 for it. Do not force a match: answering 0
when nothing fits is correct and useful, and guessing is not.

Answer with one entry per pathway, in the order given.
"""

RESPONSE_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "assignments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pathway": {"type": "integer"},
                        "theme": {"type": "integer"},
                    },
                    "required": ["pathway", "theme"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["assignments"],
        "additionalProperties": False,
    },
}


def build_levels(
    directory: Path, names_table: Path
) -> tuple[dict, dict, dict, dict, list, dict]:
    """Themes per level, each pathway's memberships, and its finest containing theme.

    Args:
        directory: The build directory.
        names_table: ``theme_names.tsv``.

    Returns:
        Parents, members, names, depths, sorted pathway keys, and each key's finest theme.
    """
    rows = list(csv.DictReader((directory / "nodes.tsv").open(encoding="utf-8"), delimiter="\t"))
    parents = {r["node"]: [p for p in r["parents"].replace(",", " ").split() if p] for r in rows}
    size = {r["node"]: int(r["size"]) for r in rows}
    members = defaultdict(set)
    for r in csv.DictReader((directory / "members.tsv").open(encoding="utf-8"), delimiter="\t"):
        members[r["node"]].add(r["key"])
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
    keys = sorted({k for v in members.values() for k in v})
    finest = {}
    for key in keys:
        holding = [n for n in parents if key in members[n]]
        finest[key] = min(holding, key=lambda n: (size[n], n)) if holding else None
    return parents, members, named, depth, keys, finest


def main(argv: Sequence[str] | None = None) -> int:
    """Price the test, and run it under --submit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--build", default="v0.2/recurrent_dag_consensus")
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--max-dollars", type=float, default=12.0)
    args = parser.parse_args(argv)

    directory = args.data / "ontology" / args.build
    parents, members, named, depth, keys, finest = build_levels(
        directory, args.data / "theme_names.tsv"
    )
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")

    levels = {
        "level 0": [n for n in parents if depth[n] == 0 and n in named],
        "level 1": [n for n in parents if depth[n] == 1 and n in named],
        "finest": sorted({t for t in finest.values() if t and t in named}),
    }
    rate_in, rate_out = PRICES[args.model]
    calls = len(levels) * ((len(keys) + BATCH - 1) // BATCH)
    worst = sum(
        ((len(keys) + BATCH - 1) // BATCH)
        * ((BATCH * 264 + len(t) * 6) * rate_in + BATCH * 18 * rate_out)
        for t in levels.values()
    ) / 1e6
    for label, themes in levels.items():
        print(f"  {label:<9} {len(themes):>4} named themes")
    print(f"  {calls} calls, worst case ${worst:,.2f} (ceiling ${args.max_dollars:,.2f})")
    if not args.submit:
        print("\n  nothing submitted; rerun with --submit")
        return 0
    if worst > args.max_dollars:
        print(f"\n  refusing: ${worst:,.2f} exceeds --max-dollars", file=sys.stderr)
        return 1

    ledger = Ledger.open(args.data / CACHE_DIR, args.model, PROMPT_VERSION)
    client = LLMClient(args.model, PROMPT_VERSION, ledger,
                       response_format=RESPONSE_FORMAT, response_key="assignments")
    report = {}
    for label, themes in levels.items():
        slate = "\n".join(f"{i+1}. {named[t]}" for i, t in enumerate(themes))
        batches = [keys[i:i + BATCH] for i in range(0, len(keys), BATCH)]

        def ask(
            batch: list[str], slate: str = slate, themes: list = themes,
            label: str = label,
        ) -> list:
            body = "\n\n".join(
                f"{j+1}. {texts.get(k,'(no description)')}" for j, k in enumerate(batch)
            )
            request = Request(
                key=f"{label}:{batch[0]}:{len(batch)}",
                system=SYSTEM_PROMPT,
                user=f"THEMES:\n{slate}\n\nPATHWAYS:\n{body}\n\n"
                     f"For each of the {len(batch)} pathways give the theme number, or 0 for none.",
            )
            try:
                got = json.loads(client.complete(request).text)["assignments"]
            except Exception as exc:  # noqa: BLE001
                print(f"    {label} {batch[0]}: {type(exc).__name__}: {str(exc)[:70]}",
                      file=sys.stderr)
                return []
            out = []
            for entry in got:
                idx = int(entry.get("pathway", 0)) - 1
                pick = int(entry.get("theme", 0))
                if 0 <= idx < len(batch):
                    out.append((batch[idx], themes[pick - 1] if 1 <= pick <= len(themes) else None))
            return out

        answers = {}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for got in pool.map(ask, batches):
                answers.update(dict(got))

        hits = none_right = none_wrong = wrong = 0
        scored = 0
        for key in keys:
            if key not in answers:
                continue
            scored += 1
            said = answers[key]
            if label == "finest":
                target = finest[key]
                truth = {target} if target and target in named else set()
            else:
                truth = {t for t in themes if key in members[t]}
            if not truth:
                if said is None:
                    none_right += 1
                else:
                    none_wrong += 1
            elif said in truth:
                hits += 1
            else:
                wrong += 1
        placeable = hits + wrong
        report[label] = {
            "themes": len(themes), "scored": scored,
            "accuracy_on_placeable": hits / max(placeable, 1),
            "placeable": placeable, "hits": hits, "wrong": wrong,
            "none_correct": none_right, "none_missed": none_wrong,
            "chance": 1 / max(len(themes), 1),
        }
        r = report[label]
        print(f"\n  {label.upper()}  ({r['themes']} themes, chance {r['chance']:.1%})")
        print(f"    placed correctly       {hits:,} of {placeable:,}"
              f"  = {r['accuracy_on_placeable']:.1%}")
        print(f"    'none' correct         {none_right:,}")
        print(f"    'none' missed          {none_wrong:,}  (said a theme when none contains it)")
    (args.data / "keys" / "name_sort_report.json").write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
