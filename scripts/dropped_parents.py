"""Dropped parents: which parents that would build the top exist, and where were they lost?

Prompt 52 task 4, declared 22 Oct 2026. Evaluation only; nothing is adopted and no build changes.

A unit -- a grouping or a family -- is a POTENTIAL PARENT if it strictly contains at least two
final O50s themes that are not nested in each other, at least one of which is a final root, and it
is not itself in the final build (no final theme at J >= 0.9). Nothing is filtered on support or
redundancy; both are recorded as attributes instead, which is the point: the question is what exists
anywhere in the data, not what the rules would have kept.

Every unit is attributed to the stage that lost it:

``completion``     its completed set came out under MIN_SIZE, or it was never eligible to score.
``absorbed``       it went into another grouping's family as a variant; the seed is recorded.
``gate``           its family's support fell under its stratum's floor; support, floor and gap kept.
``consensus``      superseded as the same theme; which theme, the Jaccard, and both supports.
``stale``          dropped by the stale-merge repair; which theme, and the kind.
``chain``          collapsed into the other end of a near-chain; which, and that one's support.
``in build``       not lost at all -- it survived, so it is not a dropped parent and is excluded.

The grouping layer is not in the cached side: ``leaves_build.side`` returns the cached ``Material``
and never calls ``v04.material``, so the raw pool, the completion survivors and the families have to
be recomputed. ``--side`` does that once, asserts the result equals the cached side block for block,
and caches the provenance; the analysis then reads it.

Usage:
    uv run scripts/dropped_parents.py --side      # ~6 min, one fresh side with the probe
    uv run scripts/dropped_parents.py             # the analysis
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: Size bands for the potential-parent tables.
PARENT_BANDS: tuple[tuple[int, int, str], ...] = (
    (20, 49, "20-49"), (50, 199, "50-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 10**9, "800+"),
)

#: Runs-found bands.
RUN_BANDS: tuple[tuple[int, int, str], ...] = (
    (1, 1, "1"), (2, 4, "2-4"), (5, 19, "5-19"), (20, 10**9, "20+"),
)

#: Stages, in pipeline order.
STAGES = ("completion", "absorbed", "gate", "consensus", "stale", "chain")


def band(size: int, bands: tuple[tuple[int, int, str], ...]) -> str | None:
    """The band a value falls in, or None if it is outside every band.

    Args:
        size: The value.
        bands: Band edges.

    Returns:
        The label, or None.
    """
    for low, high, name in bands:
        if low <= size <= high:
            return name
    return None


def build_side_probe(args: argparse.Namespace) -> int:
    """Recompute the real side with the material probe on, verify it, and cache the provenance.

    Args:
        args: Parsed arguments.

    Returns:
        0, or 2 if the recomputed side is not the cached one.
    """
    from cut_trees import load_run
    from thema.ontology.v04 import NO_CAP, material

    meta = json.loads((args.space_root / "universe.json").read_text())
    n = meta["n_embedded"]
    trees = args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    labels = [f"row{r:05d}" for r in range(1, args.runs + 1)]
    print(f"recomputing the real side with the probe: n={n:,}, {len(labels)} runs", flush=True)

    runs = [load_run(trees / f"{label}.npz", n, NO_CAP) for label in labels]
    probe: dict = {}
    got = material(runs, n, theta_match=args.theta_match, match_split=None, probe=probe)
    print(f"  pool {len(probe['groupings']):,} groupings -> "
          f"{len(probe['completed_keys']):,} completed -> "
          f"{len(probe['families']):,} families -> {len(got.supports):,} rows", flush=True)

    # The side must be the cached one, or the grouping layer belongs to a different side.
    with np.load(args.space_root / "calibration" / "real.npz") as cached:
        same_blocks = bool(np.array_equal(cached["blocks"], got.blocks))
        same_support = bool(np.allclose(cached["supports"], got.supports, atol=0, rtol=0))
    print(f"  identical to the cached side: blocks {same_blocks}, supports {same_support}")
    if not (same_blocks and same_support):
        print("  REFUSING: the recomputed side is not the cached one")
        return 2

    seeds = np.asarray([seed for seed, _family in probe["families"]], dtype=np.int64)
    flat, offsets = [], [0]
    for _seed, family in probe["families"]:
        flat.extend(family)
        offsets.append(len(flat))
    args.probe_side.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.probe_side,
        groupings=probe["groupings"],
        grouping_support=probe["grouping_support"],
        completed_keys=np.asarray(probe["completed_keys"], dtype=np.int64),
        completed_blocks=probe["completed_blocks"],
        family_seeds=seeds,
        family_flat=np.asarray(flat, dtype=np.int64),
        family_offsets=np.asarray(offsets, dtype=np.int64),
        row_seed=np.asarray(probe["row_seed"], dtype=np.int64),
        grouping_found=probe["grouping_found"],
        grouping_eligible=probe["grouping_eligible"],
        family_found=probe["family_found"],
    )
    print(f"  -> {args.probe_side}")
    return 0


def units_containing_a_root(units: np.ndarray, roots: np.ndarray) -> np.ndarray:
    """Which units strictly contain at least one final root.

    The predicate requires a contained root, and there are only a few hundred roots against
    hundreds of thousands of units, so starting from the roots is exact and far cheaper than
    scanning every unit against every theme.

    Args:
        units: ``(k, words)`` unit bitsets.
        roots: ``(r, words)`` final root bitsets.

    Returns:
        Indices of units that strictly contain some root.
    """
    unit_sizes = np.bitwise_count(units).sum(axis=1).astype(np.int64)
    hit = np.zeros(len(units), dtype=bool)
    for row in range(len(roots)):
        root = roots[row]
        size = int(np.bitwise_count(root).sum())
        inside = np.bitwise_count(root[None, :] & ~units).sum(axis=1) == 0
        hit |= inside & (unit_sizes > size)
    return np.flatnonzero(hit)


def potential_parent(unit: np.ndarray, stack: np.ndarray, sizes: np.ndarray,
                     is_root: np.ndarray) -> dict | None:
    """Test the potential-parent predicate for one unit, and return its attributes.

    Args:
        unit: The unit's member bitset.
        stack: ``(m, words)`` final theme bitsets.
        sizes: Size per final theme.
        is_root: Whether each final theme is a root.

    Returns:
        ``{contained, roots, best_j, redundant_*}`` if the unit qualifies, else None.
    """
    size = int(np.bitwise_count(unit).sum())
    inter = np.bitwise_count(unit[None, :] & stack).sum(axis=1).astype(np.int64)
    inside = (inter == sizes) & (sizes < size)
    contained = np.flatnonzero(inside)
    if len(contained) < 2:
        return None
    if not is_root[contained].any():
        return None

    # At least two of the contained themes must not be nested in each other, or the unit is just
    # one chain and adds no branching.
    pair = False
    for i in range(len(contained)):
        a = stack[contained[i]]
        for j in range(i + 1, len(contained)):
            b = stack[contained[j]]
            if int(np.bitwise_count(a & ~b).sum()) and int(np.bitwise_count(b & ~a).sum()):
                pair = True
                break
        if pair:
            break
    if not pair:
        return None

    union = size + sizes - inter
    jaccard = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    best = float(jaccard.max())
    if best >= 0.9:                      # already in the build, so not a dropped parent
        return None

    # The build's own redundancy rules, recorded and NOT applied.
    not_nested = ~inside & (inter != size)
    redundant_overlap = bool((jaccard[not_nested] >= 0.5).any()) if not_nested.any() else False
    redundant_holds = bool((sizes[contained] >= 0.85 * size).any())
    return {
        "contained": contained,
        "roots": [int(c) for c in contained if is_root[c]],
        "best_j": best,
        "redundant_overlap": redundant_overlap,
        "redundant_holds": redundant_holds,
    }


def stage_tables(units: list[dict], label: str) -> list[str]:
    """Counts by stage x runs found x size band for one unit kind.

    Args:
        units: Qualifying units, each with ``stage``, ``runs`` and ``size``.
        label: ``"groupings"`` or ``"families"``.

    Returns:
        Lines.
    """
    out = [f"  {label}: {len(units):,} potential parents"]
    run_names = [b[2] for b in RUN_BANDS]
    size_names = [b[2] for b in PARENT_BANDS]
    head = f"  {'stage':<13}{'runs':<7}" + "".join(f"{s:>11}" for s in size_names)
    head += f"{'other':>9}{'total':>9}{'redundant':>11}"
    out += [head, "  " + "-" * (len(head) - 2)]
    for stage in STAGES:
        here = [u for u in units if u["stage"] == stage]
        if not here:
            continue
        for run_name in run_names:
            rows = [u for u in here if band(u["runs"], RUN_BANDS) == run_name]
            if not rows:
                continue
            line = f"  {stage:<13}{run_name:<7}"
            counted = 0
            for size_name in size_names:
                n = sum(1 for u in rows if band(u["size"], PARENT_BANDS) == size_name)
                counted += n
                line += f"{n:>11,}"
            other = len(rows) - counted
            red = sum(1 for u in rows
                      if u["redundant_overlap"] or u["redundant_holds"])
            out.append(line + f"{other:>9,}{len(rows):>9,}{red:>11,}")
        line = f"  {stage:<13}{'ALL':<7}"
        counted = 0
        for size_name in size_names:
            n = sum(1 for u in here if band(u["size"], PARENT_BANDS) == size_name)
            counted += n
            line += f"{n:>11,}"
        red = sum(1 for u in here if u["redundant_overlap"] or u["redundant_holds"])
        out.append(line + f"{len(here) - counted:>9,}{len(here):>9,}{red:>11,}")
        out.append("  " + "-" * (len(head) - 2))
    return out


def root_coverage(units: list[dict], small_roots: set[int]) -> list[str]:
    """Per stage, how many distinct current roots the stage's potential parents would contain.

    Args:
        units: Qualifying units.
        small_roots: Final rows that are roots of 50 pathways or fewer.

    Returns:
        Lines.
    """
    out = [f"  {'stage':<13}{'parents':>10}{'roots covered':>16}{'of them <=50':>15}"]
    out.append("  " + "-" * 54)
    for stage in STAGES:
        here = [u for u in units if u["stage"] == stage]
        if not here:
            continue
        covered: set[int] = set()
        for unit in here:
            covered |= set(unit["roots"])
        out.append(f"  {stage:<13}{len(here):>10,}{len(covered):>16,}"
                   f"{len(covered & small_roots):>15,}")
    covered_all: set[int] = set()
    for unit in units:
        covered_all |= set(unit["roots"])
    out.append(f"  {'ANY STAGE':<13}{len(units):>10,}{len(covered_all):>16,}"
               f"{len(covered_all & small_roots):>15,}")
    return out


def analyse(args: argparse.Namespace) -> int:
    """Find every potential parent, attribute it to a stage, and report.

    Args:
        args: Parsed arguments.

    Returns:
        0, or 2 if the index mapping does not check out.
    """
    from merge_relationships import read_nodes

    with np.load(args.probe_side, allow_pickle=False) as side:
        got = {key: side[key] for key in side.files}
    with np.load(args.probe, allow_pickle=False) as probe:
        merge = {key: probe[key] for key in probe.files}

    ids, parent_ids = read_nodes(args.build)
    stack_all = merge["consensus_members"]
    drops = {int(v): int(k) for v, k in zip(merge["collapse_victim"],
                                            merge["collapse_keeper"], strict=True)}
    drops.update({int(d): int(k) for d, k in zip(merge["merge_dropped"],
                                                 merge["merge_kept"], strict=True)})
    survivors = [i for i in range(len(stack_all)) if i not in drops]
    stack = stack_all[survivors]
    sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
    is_root = np.array([not parent_ids[node] for node in ids], dtype=bool)
    if len(ids) != len(stack):
        print("REFUSING: node count does not match the survivor count")
        return 2
    roots = stack[is_root]
    small_roots = {i for i in range(len(ids)) if is_root[i] and sizes[i] <= 50}
    print("DROPPED PARENTS. Prompt 52 task 4, 22 Oct 2026. Evaluation only; adopts nothing.")
    print(f"  final build: {len(ids):,} themes, {int(is_root.sum()):,} roots, "
          f"{len(small_roots):,} of them 50 pathways or fewer")
    print()

    # --- stage attribution -------------------------------------------------------------------
    keep_pos = {int(r): g for g, r in enumerate(merge["keep"])}
    acc_pos = {int(g): p for p, g in enumerate(merge["accepted"])}
    sup_dropped = {int(d): i for i, d in enumerate(merge["sup_dropped"])}
    collapse_at = {int(v): int(k) for v, k in zip(merge["collapse_victim"],
                                                  merge["collapse_keeper"], strict=True)}
    merge_at = {int(d): int(k) for d, k in zip(merge["merge_dropped"],
                                               merge["merge_kept"], strict=True)}

    def stage_of_row(row: int) -> tuple[str, str]:
        """Stage and reason for one Material row."""
        gated = keep_pos.get(row)
        if gated is None:
            return "gate", "support under its stratum floor"
        if gated in sup_dropped:
            i = sup_dropped[gated]
            return "consensus", f"superseded by gated {int(merge['sup_kept'][i])}"
        position = acc_pos[gated]
        if position in collapse_at:
            return "chain", f"collapsed into post-consensus {collapse_at[position]}"
        if position in merge_at:
            return "stale", f"stale-merged into post-consensus {merge_at[position]}"
        return "in build", "survived"

    completed_keys = got["completed_keys"].tolist()
    family_seeds = got["family_seeds"].tolist()
    offsets = got["family_offsets"]
    flat = got["family_flat"]
    family_of: dict[int, int] = {}
    for f in range(len(family_seeds)):
        for g in flat[offsets[f]:offsets[f + 1]].tolist():
            family_of[int(g)] = f
    row_of_seed = {int(s): r for r, s in enumerate(got["row_seed"].tolist())}

    # --- the predicate, started from the roots ------------------------------------------------
    print("=" * 108)
    print("4a. HOW MANY UNITS EVEN CONTAIN A CURRENT ROOT")
    print("=" * 108)
    completed_blocks = got["completed_blocks"]
    cand_completed = units_containing_a_root(completed_blocks, roots)
    print(f"  completed groupings: {len(cand_completed):,} of {len(completed_blocks):,} "
          "strictly contain at least one current root")
    print(flush=True)

    grouping_found = got["grouping_found"]
    family_found = got["family_found"]
    groupings: list[dict] = []
    families_out: list[dict] = []
    for index in cand_completed.tolist():
        gid = completed_keys[index]
        verdict = potential_parent(completed_blocks[index], stack, sizes, is_root)
        if verdict is None:
            continue
        fam = family_of.get(gid)
        seed = family_seeds[fam] if fam is not None else None
        if seed is None:
            stage, reason = "completion", "never entered a family"
        elif seed != gid:
            stage, reason = "absorbed", f"absorbed into the family of grouping {seed}"
        else:
            row = row_of_seed.get(gid)
            if row is None:
                stage, reason = "completion", "family support was not a number"
            else:
                stage, reason = stage_of_row(row)
        size = int(np.bitwise_count(completed_blocks[index]).sum())
        raw = int(np.bitwise_count(got["groupings"][gid]).sum())
        record = {
            "unit": "grouping", "id": int(gid), "size": size, "raw_size": raw, "row": index,
            "runs": int(grouping_found[gid]),
            "support": round(float(got["grouping_support"][gid]), 6),
            "stage": stage, "reason": reason, "best_j": round(verdict["best_j"], 4),
            "roots": verdict["roots"], "contained": verdict["contained"].tolist(),
            "redundant_overlap": verdict["redundant_overlap"],
            "redundant_holds": verdict["redundant_holds"],
        }
        if stage != "in build":
            groupings.append(record)
        # the same set as a FAMILY unit, when this grouping is its seed
        if seed == gid and fam is not None and stage != "in build":
            twin = dict(record)
            twin["unit"] = "family"
            twin["id"] = int(fam)
            twin["runs"] = int(family_found[fam])
            twin["block_row"] = index
            families_out.append(twin)

    print("=" * 108)
    print("4b. POTENTIAL PARENTS BY STAGE, RUNS FOUND AND SIZE")
    print("=" * 108)
    print("  A unit qualifies if it strictly contains at least 2 final themes that are not nested")
    print("  in each other, at least one a final root, and no final theme matches it at J >= 0.9.")
    print("  Nothing is filtered on support or redundancy; both are columns. 'redundant' counts")
    print("  units the build's own rules would call redundant, and is REPORTED, not applied.")
    print()
    for line in stage_tables(groupings, "groupings"):
        print(line)
    print()
    for line in stage_tables(families_out, "families"):
        print(line)
    print()

    print("=" * 108)
    print("4c. CURRENT ROOTS THESE PARENTS WOULD COVER")
    print("=" * 108)
    print("  groupings")
    for line in root_coverage(groupings, small_roots):
        print(line)
    print()
    print("  families")
    for line in root_coverage(families_out, small_roots):
        print(line)
    print()

    print("=" * 108)
    print("4d. PER STAGE, THE 30 THAT CONTAIN THE MOST CURRENT ROOTS")
    print("=" * 108)
    for stage in STAGES:
        here = sorted((u for u in groupings if u["stage"] == stage),
                      key=lambda u: (-len(u["roots"]), -u["size"]))[:30]
        if not here:
            continue
        print(f"\n  {stage}  ({sum(1 for u in groupings if u['stage'] == stage):,} parents)")
        print(f"  {'id':>9}{'size':>7}{'raw':>7}{'runs':>6}{'support':>9}{'roots':>7}"
              f"{'themes':>8}{'bestJ':>7}  reason")
        for unit in here:
            print(f"  {unit['id']:>9}{unit['size']:>7,}{unit['raw_size']:>7,}"
                  f"{unit['runs']:>6}{unit['support']:>9.4f}{len(unit['roots']):>7}"
                  f"{len(unit['contained']):>8}{unit['best_j']:>7.3f}  {unit['reason'][:48]}")
    print()

    path = args.out / "potential_parents.tsv"
    fields = ["unit", "id", "size", "raw_size", "runs", "support", "stage", "reason",
              "best_j", "redundant_overlap", "redundant_holds", "n_contained", "n_roots",
              "contained", "root_nodes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t",
                                 extrasaction="ignore")
        writer.writeheader()
        for unit in groupings + families_out:
            row = dict(unit)
            row["n_contained"] = len(unit["contained"])
            row["n_roots"] = len(unit["roots"])
            row["contained"] = " ".join(ids[c] for c in unit["contained"])
            row["root_nodes"] = " ".join(ids[c] for c in unit["roots"])
            writer.writerow(row)
    print(f"  -> {path}  ({len(groupings) + len(families_out):,} rows)")
    print()
    print("=" * 108)
    print("FOR THE REVIEWER")
    print("=" * 108)
    index_of_unit = {u["id"]: u["block_row"] if u["unit"] == "family" else u["row"]
                     for u in groupings + families_out}
    reviewer_material(groupings + families_out, completed_blocks, index_of_unit, args)
    return 0


def reviewer_material(units: list[dict], blocks: np.ndarray, index_of_unit: dict[int, int],
                      args: argparse.Namespace) -> None:
    """Blind reading inputs: per stage, the 15 widest plus 15 at random.

    Nothing is judged here. The batches carry the member lists and a random id and nothing else --
    no stage, no support, no node id -- and the key that maps the ids back is written once and not
    read again by this session.

    Args:
        units: Qualifying units, groupings and families together.
        blocks: ``(c, words)`` completed grouping bitsets.
        index_of_unit: Unit record id to row in ``blocks``.
        args: Parsed arguments.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}

    # Families preferred over groupings when both exist for the same set, as declared.
    best: dict[tuple[int, ...], dict] = {}
    for unit in units:
        signature = tuple(sorted(unit["contained"]))
        held = best.get(signature)
        if held is None or (held["unit"] == "grouping" and unit["unit"] == "family"):
            best[signature] = unit
    pool = list(best.values())

    rng = np.random.default_rng(20261022)
    chosen: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for stage in STAGES:
        here = [u for u in pool if u["stage"] == stage]
        if not here:
            continue
        widest = sorted(here, key=lambda u: (-len(u["roots"]), -u["size"]))[:15]
        for unit in widest:
            if (unit["unit"], unit["id"]) not in seen:
                seen.add((unit["unit"], unit["id"]))
                chosen.append(unit)
        rest = [u for u in here if (u["unit"], u["id"]) not in seen]
        if rest:
            picked = rng.choice(len(rest), size=min(15, len(rest)), replace=False)
            for i in sorted(int(x) for x in picked):
                seen.add((rest[i]["unit"], rest[i]["id"]))
                chosen.append(rest[i])

    order = rng.permutation(len(chosen))
    ids = [f"P{i + 1:04d}" for i in range(len(chosen))]
    out = args.out / "read_parents"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.md"):
        stale.unlink()

    key: dict[str, dict] = {}
    blocks_out: list[tuple[str, list[str]]] = []
    for slot, position in enumerate(order.tolist()):
        unit = chosen[position]
        row = index_of_unit[unit["id"]] if unit["unit"] == "grouping" else unit["block_row"]
        members = sorted(
            f"{named.get(keys[p], (keys[p], '?'))[0]} [{named.get(keys[p], (keys[p], '?'))[1]}]"
            for p in bits.unpack(blocks[row]))
        blocks_out.append((ids[slot], members))
        key[ids[slot]] = {
            "unit": unit["unit"], "id": unit["id"], "size": unit["size"],
            "raw_size": unit["raw_size"], "runs": unit["runs"], "support": unit["support"],
            "stage": unit["stage"], "reason": unit["reason"], "best_j": unit["best_j"],
            "redundant_overlap": unit["redundant_overlap"],
            "redundant_holds": unit["redundant_holds"],
            "n_roots": len(unit["roots"]),
        }

    batch, lines, number = [], 0, 1
    written = []
    for parent_id, members in blocks_out:
        chunk = [f"## {parent_id}  ({len(members)} pathways)", ""]
        chunk += members + [""]
        if batch and lines + len(chunk) > 2600:
            path = out / f"b{number:02d}.md"
            path.write_text("\n".join(batch) + "\n", encoding="utf-8")
            written.append(path)
            batch, lines, number = [], 0, number + 1
        batch += chunk
        lines += len(chunk)
    if batch:
        path = out / f"b{number:02d}.md"
        path.write_text("\n".join(batch) + "\n", encoding="utf-8")
        written.append(path)

    (args.out / "KEY_DO_NOT_SHARE_parents.json").write_text(
        json.dumps(key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  R: {len(blocks_out)} potential parents in {len(written)} batch(es) -> {out}")
    print(f"  the key is written to {args.out / 'KEY_DO_NOT_SHARE_parents.json'} and is never "
          "read again by this session. Nothing is judged here.")


def main(argv: list[str] | None = None) -> int:
    """Attribute every potential parent to the stage that lost it.

    Args:
        argv: Command line.

    Returns:
        0 on success.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--build", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_relog"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--probe-side", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/side.npz"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--theta-match", type=float, default=0.70)
    parser.add_argument("--side", action="store_true",
                        help="recompute the real side with the material probe and cache it")
    args = parser.parse_args(argv)
    if args.side:
        return build_side_probe(args)
    return analyse(args)


if __name__ == "__main__":
    raise SystemExit(main())
