#!/usr/bin/env python3
"""Exclusion 2, stage 1: the mechanical screen that fixes the candidate set. Read-only.

The rule declared on 9 Oct 2026 excludes an input set if neither its source name nor its generated
description identifies one specific biological theme. Judging all 10,770 sets would be wasteful, so
stage 1 narrows mechanically -- **by a written pattern, not by eye** -- and stage 2 judges what it
returns. Recording the screen is what makes the candidate set reproducible: anyone can re-run it and
get the same list.

Two ways in:

- every unnamed BTM, i.e. one whose source name is ``TBA`` -- by the rule, a set with no usable name
  must carry the whole burden on its description, so all of them are candidates;
- every set whose description contains one of :data:`HEDGES` -- the phrases a description uses when
  it is declining to name a single theme.

A candidate is only a candidate. Stage 2 decides, and a hedge can appear in a description that goes
on to name a theme perfectly well.

Usage::

    uv run scripts/exclusion2_screen.py --out CANDIDATES.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.descriptions import read as read_descriptions
from thema.data.pathways import PathwayCollection, partition_universe
from thema.ontology.universe import load_embedded

#: Hedging phrases, declared in DECISIONS before the screen was run.
HEDGES: tuple[str, ...] = (
    "no single", "no coherent", "heterogeneous", "loosely", "mixed", "little more than",
    "best read", "rather than a single", "grab", "miscellaneous", "uncharacterised")
#: A source name of this is no name at all.
UNNAMED = "TBA"


def main(argv: list[str] | None = None) -> int:
    """Run the screen and report candidates per source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    kept, _excluded = partition_universe(collection)
    universe = {p.key: p for p in kept}
    desc = read_descriptions(args.data / "pathway_descriptions.tsv")
    # Through the verifying loader rather than reading the stored key list directly. The guard in
    # tests/ontology/test_universe.py exists because two runs were once calibrated on a superseded
    # universe, and a screen that decides which inputs to exclude is the last place to bypass it.
    leaves = set(load_embedded(args.data / "ontology" / "v0.4-leaves",
                               args.data / "pathways.tsv").keys)

    rows = []
    for key, pathway in sorted(universe.items()):
        text = (desc.get(key) or "")
        low = text.lower()
        unnamed = pathway.name.strip() == UNNAMED
        hits = [h for h in HEDGES if h in low]
        if not unnamed and not hits:
            continue
        rows.append({"key": key, "source": pathway.source, "name": pathway.name,
                     "unnamed": unnamed, "hedges": hits, "in_L": key in leaves,
                     "description": text})

    print(f"EXCLUSION 2, STAGE 1: screened all {len(universe):,} sets in the universe")
    print(f"  candidates: {len(rows):,}")
    print(f"\n  {'source':<10}{'universe':>10}{'candidates':>12}{'unnamed':>9}"
          f"{'hedge only':>12}{'in L':>7}")
    per_source = Counter(p.source for p in kept)
    for source in sorted(per_source):
        mine = [r for r in rows if r["source"] == source]
        un = sum(1 for r in mine if r["unnamed"])
        print(f"  {source:<10}{per_source[source]:>10,}{len(mine):>12,}{un:>9,}"
              f"{len(mine) - un:>12,}{sum(1 for r in mine if r['in_L']):>7,}")
    print(f"  {'TOTAL':<10}{len(universe):>10,}{len(rows):>12,}"
          f"{sum(1 for r in rows if r['unnamed']):>9,}"
          f"{sum(1 for r in rows if not r['unnamed']):>12,}"
          f"{sum(1 for r in rows if r['in_L']):>7,}")
    print("\n  which hedge caught them (a set may hit several):")
    tally = Counter(h for r in rows for h in r["hedges"])
    for hedge, n in tally.most_common():
        print(f"    {hedge:<24}{n:>5}")
    print(f"    {'(none -- unnamed only)':<24}"
          f"{sum(1 for r in rows if not r['hedges']):>5}")
    no_desc = [r for r in rows if not r["description"].strip()]
    if no_desc:
        print(f"\n  WARNING: {len(no_desc)} candidate(s) have no description at all: "
              f"{[r['key'] for r in no_desc][:5]}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"hedges": list(HEDGES), "n_universe": len(universe),
                                        "candidates": rows}, indent=1) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
