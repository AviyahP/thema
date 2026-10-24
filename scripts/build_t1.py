r"""T1: trim the child instead of growing the parent.

Prompt 57, declared 23 Oct 2026. Exploratory; nothing is adopted. The design is Aviyah's.

O50s's consensus rule 2 makes containment strict by **growing** the larger theme to swallow the
smaller one's stray member, and propagating that growth up to every ancestor. Prompt 54's checks
measured what this costs: 11,932 members added to surviving themes, and **55.2% of O50s's edges
exist only because of it**. Prompt 56 Part A added that it manufactures every one of the 418 twins
the after-gate rules then merge away.

T1 keeps strict containment -- a hard requirement, since downstream statistics need a parent's genes
to include its child's -- and flips the edit: the **smaller** theme drops the stray, and the removal
propagates DOWN to every kept theme inside it, which is the mirror of today's upward propagation and
is what stops those themes from ceasing to be contained.

**The trigger is untouched.** Rule 2 fires only when the smaller theme has *exactly* one member
outside the larger: with ``stray = 0.0`` the ``strays_b <= stray`` branch needs ``|B \\ A| == 0``,
which ``classify`` has already returned as rule 1, so the live condition is
``out_of_a <= STRAY_FLOOR`` with ``STRAY_FLOOR = 1``. Each edit therefore removes one member from
the smaller theme, plus that same member from its kept descendants.

Everything else is O50s: rules 1, 3 and 4, the stale merge at J >= 0.5, chain collapse at 0.85 with
survivor "support" and the joint fixed point, and final edges by strict containment.

**Two effects are accounted separately**, because conflating them would overstate the flip. The
*direct* effect is the members the flipped rule removed. The *indirect* effect is every later rule
whose outcome changed because the sets it saw had been trimmed -- supersessions, collapses and
stale merges that O50s did not make, or made differently. ``--check`` runs the build twice, flip off
and flip on, so the two can be differenced rather than asserted.

Usage:
    uv run scripts/build_t1.py --check     # the two declared tests
    uv run scripts/build_t1.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

THETA_SAME = 0.50
COLLAPSE_SHARE = 0.85
SURVIVOR = "support"
MIN_SIZE = 3
TABLES = ("nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv")


def run(got: object, trim: bool) -> dict[str, object]:
    """Consensus then repair, with the flip on or off.

    Args:
        got: The gated input from ``restructure_s1.gated_themes``.
        trim: Whether to flip rule 2.

    Returns:
        The build and its accounting.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.repair import repair_joint

    width = bits.words_for(got.n) * bits.WORD
    blocks = [bits.pack(m.tolist(), width) for m in got.members]
    clock = time.perf_counter()
    verdict = consensus(blocks, got.supports, got.inclusions, width, stray=0.0,
                        jaccard=THETA_SAME, trim=trim, min_size=MIN_SIZE)
    members = list(verdict.members)
    supports = [got.supports[c] for c in verdict.accepted]
    inclusions = [got.inclusions[c] for c in verdict.accepted]
    print(f"    consensus{' (TRIMMED)' if trim else ''}: {len(blocks):,} -> {len(members):,} "
          f"({len(verdict.superseded):,} superseded, {len(verdict.trimmed):,} members removed, "
          f"{len(verdict.dropped_small):,} dropped under {MIN_SIZE}) "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)
    repaired = repair_joint(members, supports, inclusions, COLLAPSE_SHARE, THETA_SAME, SURVIVOR)
    print(f"    joint fixed point: {len(members):,} -> {len(repaired.members):,} "
          f"({len(repaired.collapsed):,} collapsed, {len(repaired.merged):,} stale merged)",
          flush=True)
    return {"verdict": verdict, "repaired": repaired, "blocks": blocks,
            "members": list(repaired.members), "supports": list(repaired.supports),
            "inclusions": list(repaired.inclusions),
            "rules": dict(verdict.rules),
            "trimmed": list(verdict.trimmed),
            "dropped_small": sorted(verdict.dropped_small),
            "n_after_consensus": len(members),
            "n_superseded": len(verdict.superseded),
            "n_collapsed": len(repaired.collapsed),
            "n_stale": len(repaired.merged),
            "seconds": round(time.perf_counter() - clock, 1)}


def export(got: object, built: dict, directory: str, args: argparse.Namespace) -> Path:
    """Final edges and the four tables, in O50s's format.

    Args:
        got: The gated input.
        built: The result of :func:`run`.
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

    members, supports = built["members"], built["supports"]
    inclusions = built["inclusions"]
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
        "method": "v0.4-leaves O50s, rule 2 flipped: trim the child (T1)",
        "design": ("Aviyah, 23 Oct 2026: rule 2's trigger is unchanged, but instead of the larger "
                   "theme growing to swallow the smaller one's stray and propagating up, the "
                   "SMALLER theme drops the stray and the removal propagates DOWN to every kept "
                   "theme inside it. Strict containment is preserved; the edited side is flipped."),
        "trim": True, "min_size": MIN_SIZE, "n": got.n, "arm": "L",
        "theta_match": 0.70, "theta_same": THETA_SAME, "theta_merge": THETA_SAME,
        "collapse_share": COLLAPSE_SHARE, "survivor": SURVIVOR, "joint_fixed_point": True,
        "runs": args.runs, "rows": f"1-{args.runs}",
        "strata": [list(s) for s in got.strata],
        "floors": list(got.floors), "confirmed": got.confirmed,
        "floors_source": "O50s's stored floors, unchanged; the gate is untouched",
        "universe": "L (every curated summary removed), minus the declared exclusions",
        "construction": {
            "gated": len(built["blocks"]), "after_consensus": built["n_after_consensus"],
            "rules": built["rules"], "n_superseded": built["n_superseded"],
            "n_members_removed": len(built["trimmed"]),
            "n_removed_direct": sum(1 for _t, _m, prop in built["trimmed"] if not prop),
            "n_removed_propagated": sum(1 for _t, _m, prop in built["trimmed"] if prop),
            "n_dropped_small": len(built["dropped_small"]),
            "n_collapsed": built["n_collapsed"], "n_stale": built["n_stale"]},
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
    """Declared test 2: the flipped rule never adds a member, and edges stay strict.

    Returns:
        Whether both properties held.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.recurrent import hasse

    ok = True
    width = 64
    # Ordering matters and is easy to get wrong. Consensus walks candidates by descending support
    # and acts on the LOWEST seated position that fires, so for the downward propagation to be
    # exercised the container must be trimmed BEFORE the theme inside it -- which means the
    # container must be seated first, which means it needs the higher support.
    #   B = {0..9, 40}  seated first, holds the stray, and contains C
    #   C = {0,1,2,40}  seated second, nested in B so rule 1 claims it untouched
    #   A = {0..19}     arrives last and is LARGER, so rule 2 trims the seated B of {40},
    #                   and C -- inside B and holding {40} -- must lose it too.
    sets = [bits.pack(list(range(0, 10)) + [40], width),
            bits.pack([0, 1, 2, 40], width),
            bits.pack(list(range(0, 20)), width)]
    support = [0.95, 0.90, 0.85]
    votes = [{40: 0.6}, {40: 0.6}, {}]

    plain = consensus(sets, support, votes, width, stray=0.0, jaccard=0.5)
    if not plain.inherited:
        print("    FAIL: the fixture does not fire rule 2 unflipped")
        ok = False

    flipped = consensus(sets, support, votes, width, stray=0.0, jaccard=0.5,
                        trim=True, min_size=MIN_SIZE)
    if flipped.inherited:
        print(f"    FAIL: the flipped rule still inherited {len(flipped.inherited)} members")
        ok = False
    if not flipped.trimmed:
        print("    FAIL: the flipped rule removed nothing")
        ok = False

    # Never adds a member: every kept theme must be a SUBSET of its own input set.
    for position, candidate in enumerate(flipped.accepted):
        if bits.count(flipped.members[position] & ~sets[candidate]):
            print(f"    FAIL: theme from candidate {candidate} gained a member")
            ok = False
    # The downward propagation must have reached the theme inside B.
    if not any(prop for _t, _m, prop in flipped.trimmed):
        print("    FAIL: nothing propagated downward to a contained theme")
        ok = False
    # Every final edge is strict containment.
    for child, ups in enumerate(hasse(flipped.members)):
        for parent in ups:
            inner, outer = flipped.members[child], flipped.members[parent]
            if bits.count(inner & ~outer) or bits.count(outer) <= bits.count(inner):
                print(f"    FAIL: edge {child} -> {parent} is not strict containment")
                ok = False

    # A theme trimmed below the minimum is dropped.
    tiny = [bits.pack(list(range(0, 9)), width), bits.pack([0, 1, 40], width)]
    dropped = consensus(tiny, [0.9, 0.8], [{}, {40: 0.5}], width, stray=0.0, jaccard=0.5,
                        trim=True, min_size=MIN_SIZE)
    if 1 not in dropped.dropped_small:
        print(f"    FAIL: a theme trimmed to 2 members was kept: {dropped.dropped_small}")
        ok = False
    return ok


def main(argv: list[str] | None = None) -> int:
    """Run the declared tests, or build T1.

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
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/trim_T1_2026-10-23"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--directory", default="thema_L_x2_T1")
    parser.add_argument("--check", action="store_true",
                        help="run the two declared tests and stop")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"T1: TRIM THE CHILD INSTEAD OF GROWING THE PARENT. Prompt 57, 23 Oct 2026. "
          f"{'TESTS' if args.check else 'BUILD'}")
    got = gated_themes(args)

    if args.check:
        print("  test 1: the flip switched OFF reproduces frozen O50s byte for byte", flush=True)
        plain = run(got, trim=False)
        written = export(got, plain, "thema_L_x2_T1_offcheck", args)
        one = True
        for name in TABLES:
            mine = hashlib.sha256((written / name).read_bytes()).hexdigest()
            theirs = hashlib.sha256((args.frozen / name).read_bytes()).hexdigest()
            print(f"    {'identical ' if mine == theirs else 'DIFFERS   '} {name}")
            one = one and mine == theirs
        import shutil
        shutil.rmtree(written)
        print(f"    {'PASSED' if one else 'FAILED'}")
        print("  test 2: the flipped rule never adds a member; every final edge is strict",
              flush=True)
        two = fixture_tests()
        print(f"    {'PASSED' if two else 'FAILED'}")
        if not (one and two):
            return 2
        print("  BOTH DECLARED TESTS PASS.")
        return 0

    print("  flip ON: the smaller theme drops its stray, propagated downward", flush=True)
    off = run(got, trim=False)
    on = run(got, trim=True)
    written = export(got, on, args.directory, args)

    # --- the separated accounting -------------------------------------------------------------
    direct = [(t, m) for t, m, prop in on["trimmed"] if not prop]
    prop = [(t, m) for t, m, prop in on["trimmed"] if prop]
    record = {
        "direct": {
            "members_removed": len(direct),
            "distinct_themes_edited": len({t for t, _m in direct}),
            "propagated_removals": len(prop),
            "distinct_themes_propagated_into": len({t for t, _m in prop}),
            "themes_dropped_under_min": len(on["dropped_small"]),
        },
        "indirect": {
            "rules_off": off["rules"], "rules_on": on["rules"],
            "superseded_off": off["n_superseded"], "superseded_on": on["n_superseded"],
            "collapsed_off": off["n_collapsed"], "collapsed_on": on["n_collapsed"],
            "stale_off": off["n_stale"], "stale_on": on["n_stale"],
            "after_consensus_off": off["n_after_consensus"],
            "after_consensus_on": on["n_after_consensus"],
            "final_off": len(off["members"]), "final_on": len(on["members"]),
        },
        "inherited_off": len(off["verdict"].inherited),
    }
    (args.out / "accounting.json").write_text(json.dumps(record, indent=1) + "\n",
                                              encoding="utf-8")
    trimmed_rows = [{"theme": int(t), "member": int(m), "propagated": bool(prop)}
                    for t, m, prop in on["trimmed"]]
    (args.out / "trimmed.json").write_text(json.dumps(trimmed_rows, indent=0) + "\n",
                                           encoding="utf-8")
    print()
    print("=" * 100)
    print("SEPARATED ACCOUNTING: the flip itself, and what it changed downstream")
    print("=" * 100)
    print("  DIRECT -- what the flipped rule did")
    print(f"    members removed, the pair's own smaller theme   {len(direct):>9,}")
    print(f"    members removed by downward propagation         {len(prop):>9,}")
    print(f"    distinct themes edited directly                 "
          f"{record['direct']['distinct_themes_edited']:>9,}")
    print(f"    distinct themes propagated into                 "
          f"{record['direct']['distinct_themes_propagated_into']:>9,}")
    print(f"    themes dropped for falling under {MIN_SIZE}              "
          f"{len(on['dropped_small']):>9,}")
    print(f"    for comparison, members O50s ADDED              "
          f"{len(off['verdict'].inherited):>9,}")
    print()
    print("  INDIRECT -- later rules whose outcome the flip changed")
    print(f"    {'':<28}{'O50s':>12}{'T1':>12}{'change':>12}")
    for label, a, b in (
            ("rule 1 nested", off["rules"].get("nested", 0), on["rules"].get("nested", 0)),
            ("rule 2 inherited (events)", off["rules"].get("inherited", 0),
             on["rules"].get("inherited", 0)),
            ("rule 3 superseded", off["n_superseded"], on["n_superseded"]),
            ("rule 4 coexist", off["rules"].get("coexist", 0), on["rules"].get("coexist", 0)),
            ("after consensus", off["n_after_consensus"], on["n_after_consensus"]),
            ("chain collapses", off["n_collapsed"], on["n_collapsed"]),
            ("stale merges", off["n_stale"], on["n_stale"]),
            ("final themes", len(off["members"]), len(on["members"]))):
        print(f"    {label:<28}{a:>12,}{b:>12,}{b - a:>+12,}")
    print(f"\n  -> {args.out / 'accounting.json'} and trimmed.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
