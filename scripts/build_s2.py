"""S2: O50s's own logic with ONE change -- the same-theme merge restricted to siblings.

Prompt 54, declared 22 Oct 2026, amended the same day before building. Exploratory; nothing is
adopted. The design is Aviyah's.

Prompt 53's S1 changed two things at once: it removed consensus's inheritance **and** restricted the
same-theme merge to siblings, so its 991 roots cannot be attributed to either. The checks after it
showed inheritance adds 11,932 members in O50s and that **55.2% of O50s's edges exist only because
of it**. S2 isolates the other variable: inheritance stays exactly as it is, and only the same-theme
merge is restricted.

What changes against O50s, and nothing else:

* **consensus rule 3** (superseded: non-nested, J >= 0.5, the lower in consensus order dropped)
  applies only if the pair are siblings. A non-sibling pair that rule 3 would have superseded falls
  through to rule 4 and coexists. **Rules 1 and 2 are untouched** and still apply to every pair,
  inheritance and its propagation included.
* **the stale merge** in repair applies only between siblings.

By the amendment of 22 Oct, **consensus runs once**, as in O50s, with the sibling relation taken
from the DAG of the 26,120 gated themes; it is not repeated in rounds. Repair then runs to its joint
fixed point as in O50s, with the stale merge's sibling relation taken from the DAG of the
**current** memberships, rebuilt whenever repair needs it. That removes the second-pass vote
question -- what a merged theme's inclusion vote would be on a second consensus pass -- which
O50s's own code does not answer.

Sibling = two themes sharing at least one immediate parent, or both roots, in the DAG of the theme
set in question (strict containment, immediate parents only).

Usage:
    uv run scripts/build_s2.py --check     # the two declared tests
    uv run scripts/build_s2.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: O50s's own parameters, unchanged.
THETA_SAME = 0.50
COLLAPSE_SHARE = 0.85
SURVIVOR = "support"

#: The four tables the byte-for-byte test compares.
TABLES = ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv")


def sibling_predicate(members: Sequence[np.ndarray], n: int,
                      packed: bool = True) -> Callable[[int, int], bool]:
    """The sibling relation over one theme set, from its DAG.

    Two themes are siblings if they share at least one immediate parent, or if both are roots.
    The relation is never materialised as pairs -- a giant with thousands of children would make
    millions of them -- so it is answered from each theme's parent set on demand.

    Args:
        members: Member bitsets (``packed``) or member id arrays.
        n: Universe size.
        packed: Whether ``members`` holds bitsets.

    Returns:
        ``(i, j) -> bool``.
    """
    from core_construction_c1b import immediate_parents
    from thema.ontology import bitset as bits

    ids = ([np.array(sorted(bits.unpack(block)), dtype=np.int32) for block in members]
           if packed else list(members))
    parents = immediate_parents(ids, n, report=False)
    sets = [frozenset(p) for p in parents]

    def same(left: int, right: int) -> bool:
        """Do these two share an immediate parent, or are both roots?"""
        a, b = sets[left], sets[right]
        if not a and not b:
            return True
        return bool(a & b)

    return same


def build(got: object, restrict: bool, args: argparse.Namespace
          ) -> tuple[list, list, list, dict]:
    """Consensus once, then repair to its joint fixed point.

    Args:
        got: The gated input, from ``restructure_s1.gated_themes``.
        restrict: Whether to apply the sibling restriction. ``False`` is O50s exactly.
        args: Parsed arguments.

    Returns:
        ``(members, supports, inclusions, log)``.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.repair import repair_joint

    width = bits.words_for(got.n) * bits.WORD
    blocks = [bits.pack(m.tolist(), width) for m in got.members]

    clock = time.perf_counter()
    gate_siblings = sibling_predicate(blocks, got.n) if restrict else None
    if restrict:
        print(f"    sibling relation over the {len(blocks):,} gated themes "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)

    verdict = consensus(blocks, got.supports, got.inclusions, width,
                        stray=0.0, jaccard=THETA_SAME, siblings=gate_siblings)
    members = [verdict.members[i] for i in range(len(verdict.accepted))]
    supports = [got.supports[c] for c in verdict.accepted]
    inclusions = [got.inclusions[c] for c in verdict.accepted]
    original = [blocks[c] for c in verdict.accepted]
    inherited = int(sum(int(np.bitwise_count(members[i] & ~original[i]).sum())
                        for i in range(len(members))))
    grew = sum(1 for i in range(len(members))
               if int(np.bitwise_count(members[i] & ~original[i]).sum()))
    print(f"    consensus: {len(blocks):,} -> {len(members):,} "
          f"({len(verdict.superseded):,} superseded, {inherited:,} members inherited into "
          f"{grew:,} themes) ({time.perf_counter() - clock:.0f}s)", flush=True)

    def factory(live: Sequence[np.ndarray]) -> Callable[[int, int], bool]:
        """Rebuild the sibling relation from the current memberships."""
        return sibling_predicate(live, got.n)

    repaired = repair_joint(members, supports, inclusions, COLLAPSE_SHARE, THETA_SAME, SURVIVOR,
                            stale_siblings=factory if restrict else None)
    print(f"    joint fixed point: {len(members):,} -> {len(repaired.members):,} "
          f"({len(repaired.collapsed):,} collapsed, {len(repaired.merged):,} stale merged, "
          f"{repaired.rounds.get('joint', 0)} rounds)", flush=True)

    log = {"gated": len(blocks), "after_consensus": len(members),
           "superseded": len(verdict.superseded), "inherited": inherited, "grew": grew,
           "collapsed": len(repaired.collapsed), "stale_merged": len(repaired.merged),
           "stale_identical": sum(1 for v in repaired.merged_kind.values() if v == "identical"),
           "stale_overlap": sum(1 for v in repaired.merged_kind.values() if v == "overlap"),
           "repair_rounds": repaired.rounds,
           "superseded_map": dict(verdict.superseded),
           "accepted": list(verdict.accepted),
           "consensus_original": original,
           "consensus_members": list(members),
           "collapsed_map": dict(repaired.collapsed),
           "merged_map": dict(repaired.merged),
           "seconds": round(time.perf_counter() - clock, 1)}
    return list(repaired.members), list(repaired.supports), list(repaired.inclusions), log


def export(got: object, members: list, supports: list, inclusions: list, log: dict,
           directory: str, args: argparse.Namespace) -> Path:
    """Final edges and the four tables, in O50s's own format.

    Args:
        got: The gated input.
        members: Member bitsets per surviving theme.
        supports: Support per theme.
        inclusions: Inclusion vote per theme.
        log: The construction record.
        directory: Output directory name.
        args: Parsed arguments.

    Returns:
        Where it was written.
    """
    from build_trees_10770 import peak_mb
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology import export as writer
    from thema.ontology import v04
    from thema.ontology.base import Node, Ontology
    from thema.ontology.recurrent import hasse

    parents = hasse(members)
    ids = [f"n{i:05d}" for i in range(len(members))]
    nodes = tuple(
        Node(id=ids[i], parents=tuple(ids[p] for p in parents[i]),
             members=tuple((got.keys[p], round(float(inclusions[i].get(p, 1.0)), 4))
                           for p in sorted(bits.unpack(block))),
             support=round(supports[i], 6))
        for i, block in enumerate(members))
    placed = {k for node in nodes for k in node.keys}
    unplaced = tuple(k for k in got.keys if k not in placed)
    roots = {node.id for node in nodes if not node.parents}
    multi = sum(1 for node in nodes if len(node.parents) > 1)
    in_nonroot = {k for node in nodes if node.id not in roots for k in node.keys}
    shape = {"n_nodes": len(nodes), "n_roots": len(roots), "n_multi_parent": multi,
             "multi_parent_share": round(multi / len(nodes), 4) if nodes else 0.0,
             "n_unplaced": len(unplaced), "n_root_only": len(placed - in_nonroot),
             "n_effectively_unplaced": len(unplaced) + len(placed - in_nonroot)}
    print(f"  themes {shape['n_nodes']:,}  roots {shape['n_roots']:,}  "
          f"multi-parent {shape['multi_parent_share']:.1%}  "
          f"effectively unplaced {shape['n_effectively_unplaced']:,}", flush=True)

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    genes = {p.key: frozenset(p.genes) for p in collection.pathways}
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    manifest = {
        **v04.parameters(got.n),
        "method": "v0.4-leaves O50s, same-theme merge restricted to siblings (S2)",
        "design": ("Aviyah, 22 Oct 2026: O50s exactly, with consensus rule 3 and the stale merge "
                   "applied only to sibling pairs. Rules 1 and 2, inheritance and its propagation "
                   "included, are untouched. Consensus runs ONCE with the sibling relation from "
                   "the DAG of the gated themes; repair's stale merge rebuilds the relation from "
                   "the current memberships whenever it needs it."),
        "sibling_restricted": True, "n": got.n, "arm": "L",
        "theta_match": 0.70, "theta_same": THETA_SAME, "theta_merge": THETA_SAME,
        "collapse_share": COLLAPSE_SHARE, "survivor": SURVIVOR, "joint_fixed_point": True,
        "runs": args.runs, "rows": f"1-{args.runs}",
        "strata": [list(s) for s in got.strata],
        "floors": list(got.floors), "confirmed": got.confirmed,
        "floors_source": "O50s's stored floors, unchanged; the gate is untouched",
        "universe": "L (every curated summary removed), minus the declared exclusions",
        "construction": {k: v for k, v in log.items()
                         if k not in ("superseded_map", "accepted", "consensus_original",
                                      "consensus_members", "collapsed_map", "merged_map")},
        "leaves_digest": got.meta["leaves_digest"],
        "universe_digest": got.meta["universe_digest"],
        "exclusions_file": got.meta.get("exclusions_file"),
        "n_excluded_inputs": got.meta.get("n_excluded", 0),
        "peak_mb": round(peak_mb(), 1), **shape}
    written = writer.write(
        Ontology(method="v0.4-leaves", params=manifest, nodes=nodes, unplaced=unplaced,
                 manifest=manifest),
        args.data / "ontology", args.out_version, genes, manifest,
        dry_run=False, info=info, directory=directory)
    print(f"  -> {written}  (peak {peak_mb():.0f} MB)", flush=True)
    return Path(written)


def fixture_tests() -> bool:
    """Declared test 2: restricted rule 3 spares non-siblings; rule 2 still fires on them.

    Returns:
        Whether both properties held.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus

    ok = True
    width = 64

    # Two themes overlapping at J = 6/10 = 0.6, neither containing the other, under DIFFERENT
    # parents. Unrestricted, rule 3 drops the weaker; restricted, both must survive.
    sets = [bits.pack(list(range(0, 20)), width),            # 0: a parent
            bits.pack(list(range(20, 40)), width),           # 1: another parent
            bits.pack([0, 1, 2, 3, 4, 5, 6, 7], width),      # 2: child of 0
            bits.pack([0, 1, 2, 3, 4, 5, 8, 9], width)]      # 3: overlaps 2 at 6/10
    support = [0.95, 0.94, 0.80, 0.70]
    votes = [{} for _ in sets]
    plain = consensus(sets, support, votes, width, stray=0.0, jaccard=0.5)
    if 3 not in plain.superseded:
        print("    FAIL: the fixture does not reproduce an unrestricted supersession")
        ok = False

    def never(_a: int, _b: int) -> bool:
        """No pair is a sibling."""
        return False

    held = consensus(sets, support, votes, width, stray=0.0, jaccard=0.5, siblings=never)
    if held.superseded:
        print(f"    FAIL: restricted rule 3 still superseded {held.superseded}")
        ok = False

    # Rule 2 must still fire on a NON-sibling pair. It needs BOTH sides to have members outside
    # the other -- otherwise the pair is strictly nested and rule 1 claims it -- with the smaller
    # having at most STRAY_FLOOR = 1 outside. Here {0..19} keeps 18 and 19; {0..17, 40} strays only
    # on 40, so the larger grows to swallow 40.
    sets2 = [bits.pack(list(range(0, 20)), width),
             bits.pack(list(range(0, 18)) + [40], width)]
    grown = consensus(sets2, [0.9, 0.8], [{}, {40: 0.6}], width, stray=0.0, jaccard=0.5,
                      siblings=never)
    if not grown.inherited:
        print("    FAIL: rule 2 did not fire under the sibling restriction")
        ok = False
    if grown.superseded:
        print(f"    FAIL: rule 2's pair was superseded instead: {grown.superseded}")
        ok = False

    # The reference implementation must agree with the vectorised one under the restriction.
    for method in ("vector", "pairwise"):
        out = consensus(sets, support, votes, width, stray=0.0, jaccard=0.5,
                        siblings=never, method=method)
        if out.superseded:
            print(f"    FAIL: {method} superseded a non-sibling pair")
            ok = False
    return ok


def main(argv: list[str] | None = None) -> int:
    """Run the declared tests, or build S2.

    Args:
        argv: Command line.

    Returns:
        0 on success, 2 if a declared test fails.
    """
    from restructure_s1 import gated_themes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--out-version", default="0.4-leaves")
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--directory", default="thema_L_x2_S2")
    parser.add_argument("--check", action="store_true",
                        help="run the two declared tests and stop")
    args = parser.parse_args(argv)

    print(f"S2: O50s WITH THE SAME-THEME MERGE RESTRICTED TO SIBLINGS. Prompt 54, 22 Oct 2026. "
          f"{'TESTS' if args.check else 'BUILD'}")
    got = gated_themes(args)

    if args.check:
        print("  test 1: the restriction switched OFF reproduces frozen O50s byte for byte",
              flush=True)
        members, supports, inclusions, _log = build(got, restrict=False, args=args)
        written = export(got, members, supports, inclusions, _log,
                         "thema_L_x2_S2_offcheck", args)
        one = True
        for name in TABLES:
            mine = hashlib.sha256((written / name).read_bytes()).hexdigest()
            theirs = hashlib.sha256((args.frozen / name).read_bytes()).hexdigest()
            print(f"    {'identical ' if mine == theirs else 'DIFFERS   '} {name}")
            one = one and mine == theirs
        import shutil
        shutil.rmtree(written)
        print(f"    {'PASSED' if one else 'FAILED'}")
        print("  test 2: restricted rule 3 spares non-siblings; rule 2 still fires on them",
              flush=True)
        two = fixture_tests()
        print(f"    {'PASSED' if two else 'FAILED'}")
        if not (one and two):
            return 2
        print("  BOTH DECLARED TESTS PASS.")
        return 0

    print("  sibling-restricted: consensus rule 3 and the stale merge only, rules 1 and 2 intact",
          flush=True)
    members, supports, inclusions, log = build(got, restrict=True, args=args)
    written = export(got, members, supports, inclusions, log, args.directory, args)
    (written / "s2_construction.json").write_text(
        json.dumps({k: v for k, v in log.items()
                    if k not in ("consensus_original", "consensus_members")},
                   indent=1, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
