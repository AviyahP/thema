"""PART 1 of prompt 55: blind reading inputs where S2 and O50s differ.

Declared 22 Oct 2026. Nothing is judged here, and nothing is adopted.

Four input kinds, each reproducing a format the reviewer has already used:

``R``  roots that differ -- every S2 root with no O50s ROOT at J >= 0.9 and vice versa, pooled.
``T``  middle themes unique to one build (best J below 0.9 to ANY theme of the other), in the
       12-24, 25-49, 50-99 and 100-199 bands, 40 per band per build.
``I``  the C6 intruder test over the same T themes, reproducing
       ``data/experiments/O50s_review_2026-10-17/code/build_review.py`` exactly: the candidate units
       are the MAXIMAL strict subsets of the theme among themes of 5 to 150 pathways, five are
       drawn, and one intruder is drawn from themes less than half of which lies inside the theme;
       the six are shuffled and lettered, and batches are taken by stride.
``S``  the small-root test of ``PREREG_O50s_roots.md`` over every S2 root of 50 or fewer: the root's
       full list plus its three largest-share larger containers, ties broken by smaller size,
       labelled P, Q, R in random order, each with a sample of up to 40 members not in the root.

Shares, missing counts, build labels, node ids and sizes-by-build go only into the key, which is
written once and not read again by this session.

Usage:
    uv run scripts/s2_vs_o50s_inputs.py
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The seed the prompt declares.
SEED = 20261022

#: Bands the T sample is drawn from.
T_BANDS: tuple[tuple[int, int, str], ...] = (
    (12, 24, "12-24"), (25, 49, "25-49"), (50, 99, "50-99"), (100, 199, "100-199"),
)

#: Per band per build.
PER_BAND = 40

#: The C6 intruder test's pool bounds and its unit count.
INTRUDER_MIN, INTRUDER_MAX = 5, 150
INTRUDER_PICK = 5

#: Lines per batch, as every earlier reading used.
BATCH_LINES = 2600


def read_build(
    directory: Path,
) -> tuple[list[str], dict[str, set[str]], dict[str, tuple[str, ...]]]:
    """Node ids, memberships and immediate parents.

    Args:
        directory: A build directory.

    Returns:
        ``(ids, members, parents)``.
    """
    with (directory / "nodes.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    parents = {r["node"]: tuple(p for p in (r["parents"] or "").split() if p) for r in rows}
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return [r["node"] for r in rows], dict(members), parents


def pack_all(ids: Sequence[str], members: Mapping[str, set[str]],
             index: Mapping[str, int], width: int) -> np.ndarray:
    """Stack of member bitsets in node order.

    Args:
        ids: Node ids.
        members: Node to member keys.
        index: Pathway key to universe position.
        width: Bitset width in bits.

    Returns:
        ``(n, words)`` bitsets.
    """
    from thema.ontology import bitset as bits

    return np.vstack([
        bits.pack(sorted(index[k] for k in members.get(node, ())), width)[None, :]
        for node in ids])


def best_against(left: np.ndarray, right: np.ndarray, chunk: int = 256) -> np.ndarray:
    """For every row of ``left``, its highest Jaccard against any row of ``right``.

    Args:
        left: ``(n, words)`` bitsets.
        right: ``(m, words)`` bitsets.
        chunk: Rows per vectorised block.

    Returns:
        ``(n,)`` best Jaccard.
    """
    out = np.zeros(len(left), dtype=np.float64)
    r_size = np.bitwise_count(right).sum(axis=1).astype(np.int64)
    for start in range(0, len(left), chunk):
        block = left[start:start + chunk]
        l_size = np.bitwise_count(block).sum(axis=1).astype(np.int64)
        inter = np.zeros((len(block), len(right)), dtype=np.int64)
        for word in range(left.shape[1]):
            inter += np.bitwise_count(
                block[:, word][:, None] & right[None, :, word]).astype(np.int64)
        union = l_size[:, None] + r_size[None, :] - inter
        jac = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
        out[start:start + chunk] = jac.max(axis=1)
    return out


def render(keys: Sequence[str], named: Mapping[str, tuple[str, str]]) -> list[str]:
    """Member lines as ``- name [source]``, sorted by name.

    Args:
        keys: Pathway keys.
        named: Key to ``(name, source)``.

    Returns:
        Lines.
    """
    return sorted(f"- {named.get(k, (k, '?'))[0]} [{named.get(k, (k, '?'))[1]}]" for k in keys)


def write_batches(items: Sequence[str], out: Path, stem: str,
                  stride: bool = False) -> list[Path]:
    """Write items into batches of about ``BATCH_LINES`` lines, never splitting an item.

    Args:
        items: Rendered items.
        out: Destination directory.
        stem: Filename stem.
        stride: Batch by stride, as the C6 intruder test does, rather than contiguously.

    Returns:
        The files written.
    """
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob(f"{stem}_*.md"):
        stale.unlink()
    written: list[Path] = []
    if stride:
        total = sum(item.count("\n") + 1 for item in items)
        count = max(1, round(total / 4000))
        for j in range(count):
            path = out / f"{stem}_b{j + 1:02d}.md"
            path.write_text("\n\n".join(items[j::count]) + "\n", encoding="utf-8")
            written.append(path)
        return written
    batch: list[str] = []
    lines = 0
    for item in items:
        size = item.count("\n") + 1
        if batch and lines + size > BATCH_LINES:
            path = out / f"{stem}_b{len(written) + 1:02d}.md"
            path.write_text("\n\n".join(batch) + "\n", encoding="utf-8")
            written.append(path)
            batch, lines = [], 0
        batch.append(item)
        lines += size
    if batch:
        path = out / f"{stem}_b{len(written) + 1:02d}.md"
        path.write_text("\n\n".join(batch) + "\n", encoding="utf-8")
        written.append(path)
    return written


def intruder_items(targets: Sequence[tuple[str, str]],
                   members: Mapping[str, Mapping[str, set[str]]],
                   named: Mapping[str, tuple[str, str]], rng: random.Random
                   ) -> tuple[list[str], dict[str, dict], list[tuple[str, int, int]]]:
    """The C6 intruder test over the given themes, each within its OWN build.

    Reproduces ``O50s_review_2026-10-17/code/build_review.py``: candidate units are the maximal
    strict subsets of the theme among themes of 5 to 150 pathways; five are drawn; the intruder is
    drawn from themes less than half of which lies inside the theme; the six are shuffled.

    Args:
        targets: ``(build, node)`` pairs.
        members: Per build, node to member keys.
        named: Key to ``(name, source)``.
        rng: Seeded generator.

    Returns:
        ``(items, key, excluded)`` -- excluded carries ``(build:node, size, candidates)``.
    """
    items: list[str] = []
    key: dict[str, dict] = {}
    excluded: list[tuple[str, int, int]] = []
    for build, node in targets:
        pool_members = members[build]
        mine = pool_members[node]
        pool = [c for c in pool_members
                if INTRUDER_MIN <= len(pool_members[c]) <= INTRUDER_MAX]
        inside = [c for c in pool if c != node and pool_members[c] < mine]
        inside = [c for c in inside
                  if not any(c != d and pool_members[c] < pool_members[d] for d in inside)]
        if len(inside) < 4:
            excluded.append((f"{build}:{node}", len(mine), len(inside)))
            continue
        pick = rng.sample(inside, min(INTRUDER_PICK, len(inside)))
        outside = [c for c in pool
                   if len(pool_members[c] & mine) < 0.5 * len(pool_members[c])]
        if not outside:
            excluded.append((f"{build}:{node}", len(mine), -1))
            continue
        intruder = rng.choice(outside)
        units = [*pick, intruder]
        rng.shuffle(units)
        letters = "ABCDEF"[:len(units)]
        item_id = f"I{len(items) + 1:03d}"
        key[item_id] = {"build": build, "node": node, "size": len(mine),
                        "intruder": letters[units.index(intruder)],
                        "units": {letter: {"node": unit, "size": len(pool_members[unit])}
                                  for letter, unit in zip(letters, units, strict=True)}}
        text = [f"## ITEM {item_id}"]
        for letter, unit in zip(letters, units, strict=True):
            text.append(f"### Unit {letter} ({len(pool_members[unit])} pathways)")
            text += render(pool_members[unit], named)
        items.append("\n".join(text))
    rng.shuffle(items)
    return items, key, excluded


def small_root_items(roots: Sequence[str], members: Mapping[str, set[str]],
                     named: Mapping[str, tuple[str, str]], rng: random.Random
                     ) -> tuple[list[str], dict[str, dict]]:
    """The small-root test of PREREG_O50s_roots.md, over one build.

    Args:
        roots: Root ids of 50 pathways or fewer.
        members: Node to member keys for that build.
        named: Key to ``(name, source)``.
        rng: Seeded generator.

    Returns:
        ``(items, key)``.
    """
    items: list[str] = []
    key: dict[str, dict] = {}
    for position, node in enumerate(roots, 1):
        mine = members[node]
        cands = [(len(mine & members[c]) / len(mine), len(members[c]), c)
                 for c in members if c != node and len(members[c]) > len(mine)]
        cands.sort(key=lambda row: (-row[0], row[1]))
        top = cands[:3]
        rng.shuffle(top)
        item_id = f"R{position:03d}"
        text = [f"## ITEM {item_id}", f"### Small theme ({len(mine)} pathways)"]
        text += render(mine, named)
        key[item_id] = {"build": "S2", "root": node, "size": len(mine), "containers": {}}
        for letter, (share, size, other) in zip("PQR", top, strict=False):
            rest = sorted(members[other] - mine)
            sample = rest if len(rest) <= 40 else rng.sample(rest, 40)
            text.append(f"### Larger theme {letter} ({size} pathways; sample of "
                        f"{len(sample)} members not in the small theme)")
            text += render(sample, named)
            key[item_id]["containers"][letter] = {
                "node": other, "size": size, "share": round(share, 4),
                "missing": len(mine - members[other])}
        items.append("\n".join(text))
    return items, key


def main(argv: list[str] | None = None) -> int:
    """Write R, T, I, S and the key.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology import bitset as bits
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--s2", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/S2_vs_O50s_2026-10-22"))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}

    builds = {}
    for name, path in (("O50s", args.o50s), ("S2", args.s2)):
        ids, members, parents = read_build(path)
        builds[name] = {"ids": ids, "members": members, "parents": parents,
                        "stack": pack_all(ids, members, index, width)}
    print("PART 1: reading inputs where S2 and O50s differ. Nothing judged here.")
    for name in ("O50s", "S2"):
        print(f"  {name}: {len(builds[name]['ids']):,} themes, "
              f"{sum(1 for n in builds[name]['ids'] if not builds[name]['parents'][n]):,} roots",
              flush=True)

    # --- cross-build best Jaccard, theme to theme and root to root ----------------------------
    cross = {
        "S2": best_against(builds["S2"]["stack"], builds["O50s"]["stack"]),
        "O50s": best_against(builds["O50s"]["stack"], builds["S2"]["stack"]),
    }
    root_rows = {name: [i for i, node in enumerate(builds[name]["ids"])
                        if not builds[name]["parents"][node]] for name in builds}
    root_cross = {
        "S2": best_against(builds["S2"]["stack"][root_rows["S2"]],
                           builds["O50s"]["stack"][root_rows["O50s"]]),
        "O50s": best_against(builds["O50s"]["stack"][root_rows["O50s"]],
                             builds["S2"]["stack"][root_rows["S2"]]),
    }
    print("  cross-build Jaccard computed", flush=True)

    rng = random.Random(SEED)
    key: dict[str, dict] = {}

    # --- R: roots that differ -----------------------------------------------------------------
    r_targets: list[tuple[str, str]] = []
    counts_r = {}
    for name in ("S2", "O50s"):
        rows = [root_rows[name][i] for i, best in enumerate(root_cross[name]) if best < 0.9]
        counts_r[name] = len(rows)
        r_targets += [(name, builds[name]["ids"][row]) for row in rows]
    rng.shuffle(r_targets)
    r_items = []
    for position, (name, node) in enumerate(r_targets, 1):
        item_id = f"D{position:03d}"
        mine = builds[name]["members"][node]
        key[item_id] = {"kind": "R", "build": name, "node": node, "size": len(mine)}
        r_items.append("\n".join([f"## {item_id} ({len(mine)} pathways)"]
                                 + render(mine, named)))
    r_files = write_batches(r_items, args.out / "read_roots", "R")
    print(f"  R: S2 roots unmatched by any O50s root {counts_r['S2']:,}; "
          f"O50s roots unmatched by any S2 root {counts_r['O50s']:,}; "
          f"{len(r_items):,} items in {len(r_files)} batch(es)", flush=True)

    # --- T: middle themes unique to one build -------------------------------------------------
    t_targets: list[tuple[str, str]] = []
    short: list[str] = []
    for name in ("S2", "O50s"):
        sizes = [len(builds[name]["members"].get(node, ())) for node in builds[name]["ids"]]
        for low, high, band in T_BANDS:
            pool = [i for i in range(len(sizes))
                    if low <= sizes[i] <= high and cross[name][i] < 0.9]
            take = pool if len(pool) <= PER_BAND else rng.sample(pool, PER_BAND)
            if len(pool) <= PER_BAND:
                short.append(f"{name} {band}: {len(pool)} available, all taken")
            t_targets += [(name, builds[name]["ids"][i]) for i in take]
    rng.shuffle(t_targets)
    t_items = []
    for position, (name, node) in enumerate(t_targets, 1):
        item_id = f"T{position:03d}"
        mine = builds[name]["members"][node]
        key[item_id] = {"kind": "T", "build": name, "node": node, "size": len(mine)}
        t_items.append("\n".join([f"## {item_id} ({len(mine)} pathways)"]
                                 + render(mine, named)))
    t_files = write_batches(t_items, args.out / "read_themes", "T")
    print(f"  T: {len(t_items):,} items in {len(t_files)} batch(es)")
    for line in short:
        print(f"    short band -- {line}")

    # --- I: the C6 intruder test over the same T themes ---------------------------------------
    members_by_build = {name: builds[name]["members"] for name in builds}
    i_items, i_key, i_excluded = intruder_items(t_targets, members_by_build, named, rng)
    i_files = write_batches(i_items, args.out / "intruder", "I", stride=True)
    for item_id, record in i_key.items():
        key[item_id] = {"kind": "I", **record}
    print(f"  I: {len(i_items):,} items in {len(i_files)} batch(es); "
          f"{len(i_excluded):,} T themes excluded for too few candidate units", flush=True)

    # --- S: the small-root test over S2's roots of 50 or fewer --------------------------------
    s2_small = [builds["S2"]["ids"][row] for row in root_rows["S2"]
                if len(builds["S2"]["members"].get(builds["S2"]["ids"][row], ())) <= 50]
    s_items, s_key = small_root_items(s2_small, builds["S2"]["members"], named, rng)
    s_files = write_batches(s_items, args.out / "small_inputs", "S")
    for item_id, record in s_key.items():
        key[item_id] = {"kind": "S", **record}
    print(f"  S: {len(s_items):,} S2 roots of 50 or fewer in {len(s_files)} batch(es)",
          flush=True)

    (args.out / "KEY_DO_NOT_SHARE_S2_vs_O50s.json").write_text(
        json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (args.out / "part1_counts.json").write_text(json.dumps({
        "roots_unmatched": counts_r,
        "R_items": len(r_items), "R_batches": len(r_files),
        "T_items": len(t_items), "T_batches": len(t_files), "T_short_bands": short,
        "I_items": len(i_items), "I_batches": len(i_files),
        "I_excluded": [list(x) for x in i_excluded],
        "S_items": len(s_items), "S_batches": len(s_files),
        "seed": SEED,
    }, indent=1) + "\n", encoding="utf-8")
    print(f"  key -> {args.out / 'KEY_DO_NOT_SHARE_S2_vs_O50s.json'}; "
          "written once and not read again by this session. Nothing is judged here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
