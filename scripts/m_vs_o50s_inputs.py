#!/usr/bin/env python3
"""Part A, prompt 48: blind-reading inputs and two descriptive measures for M against O50s.

Prompt 47's arm M admits 47% more candidates than O50s and its top level is already known to be
worse (394 roots against 261). The open question is **below** the top: are M's extra themes coherent
and distinct, or near-copies that only just pass? **The reviewer reads them blind. This script
prepares the inputs and computes two descriptive measures, and judges nothing.**

A theme is *unique* to its build if its best Jaccard to any theme of the other build is below 0.9.
The reading sample is 15 unique themes per size band per side, drawn and shuffled under seed
20261019, with every identifying mark stripped: no build label, node id, theme name or support, and
the member lists sorted by pathway name so the ordering cannot leak the source either.

Usage::

    uv run scripts/m_vs_o50s_inputs.py
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

#: The declared size bands.
BANDS = ((10, 19), (20, 49), (50, 199), (200, 10 ** 9))

#: A theme with a counterpart at or above this is not unique to its build.
SAME = 0.90

#: The near-copy bar for the redundancy measure.
NEAR = 0.80

#: Redundancy only compares themes whose sizes are within this factor.
SIZE_FACTOR = 1.5

#: The support share the report calls out.
WEAK = 0.02

#: Themes drawn per band per side for the blind reading.
PER_BAND = 15

#: The declared seed, for the draw and the shuffle.
SEED = 20261019

#: Roughly how many lines a reading batch holds; a theme is never split.
BATCH_LINES = 2600


def band_of(size: int) -> str | None:
    """The band a size falls in, or None below the smallest.

    Args:
        size: Theme size in pathways.

    Returns:
        The band label, or None.
    """
    for low, high in BANDS:
        if low <= size <= high:
            return f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
    return None


def read_build(path: Path) -> dict[str, object]:
    """One build's nodes and members.

    Args:
        path: The build directory.

    Returns:
        ``nodes``, ``members`` and ``manifest``.
    """
    with (path / "nodes.tsv").open(encoding="utf-8") as handle:
        nodes = {row["node"]: row for row in csv.DictReader(handle, delimiter="\t")}
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    return {"nodes": nodes, "members": dict(members),
            "manifest": json.loads((path / "manifest.json").read_text())}


def pack(group: Mapping[str, set[str]], index: Mapping[str, int], words: int
         ) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Ids, a bitset matrix and sizes for a node set.

    Args:
        group: Node id to member keys.
        index: Pathway key to bit position.
        words: Bitset width in 64-bit words.

    Returns:
        ``(ids, bitsets, sizes)``.
    """
    ids = sorted(group)
    out = np.zeros((len(ids), words), dtype=np.uint64)
    for row, node in enumerate(ids):
        for key in group[node]:
            position = index[key]
            out[row, position // 64] |= np.uint64(1) << np.uint64(position % 64)
    return ids, out, np.bitwise_count(out).sum(axis=1).astype(np.int64)


def best_against(mine: np.ndarray, size: int, other: np.ndarray, other_sizes: np.ndarray
                 ) -> tuple[int, float]:
    """The row of ``other`` with the highest Jaccard against one bitset.

    Args:
        mine: One theme's bitset.
        size: Its member count.
        other: The other build's bitsets.
        other_sizes: Their sizes.

    Returns:
        ``(row, jaccard)``, or ``(-1, 0.0)`` if the other build is empty.
    """
    if not len(other):
        return (-1, 0.0)
    shared = np.bitwise_count(mine[None, :] & other).sum(axis=1).astype(np.int64)
    union = size + other_sizes - shared
    with np.errstate(divide="ignore", invalid="ignore"):
        scores = np.where(union > 0, shared / union, 0.0)
    pick = int(np.argmax(scores))
    return (pick, float(scores[pick]))


def redundancy(ids: Sequence[str], stack: np.ndarray, sizes: np.ndarray
               ) -> dict[str, tuple[str, float]]:
    """Each theme's best Jaccard to another theme of the same build of comparable size.

    "Comparable" is the declared factor of 1.5 either way, which is what makes this a measure of
    redundancy rather than of nesting: a theme is not called a near-copy of something three times
    its size.

    Args:
        ids: Node ids.
        stack: Their bitsets.
        sizes: Their sizes.

    Returns:
        Node id to ``(partner id, Jaccard)``.
    """
    out: dict[str, tuple[str, float]] = {}
    for row, node in enumerate(ids):
        low = sizes[row] / SIZE_FACTOR
        high = sizes[row] * SIZE_FACTOR
        near = np.flatnonzero((sizes >= low) & (sizes <= high))
        near = near[near != row]
        if not len(near):
            out[node] = ("", 0.0)
            continue
        shared = np.bitwise_count(stack[row][None, :] & stack[near]).sum(axis=1).astype(np.int64)
        union = sizes[row] + sizes[near] - shared
        with np.errstate(divide="ignore", invalid="ignore"):
            scores = np.where(union > 0, shared / union, 0.0)
        pick = int(np.argmax(scores))
        out[node] = (ids[near[pick]], float(scores[pick]))
    return out


def floor_for(size: int, floors: Sequence[Mapping[str, object]],
              strata: Sequence[tuple[int, int]]) -> tuple[str, object]:
    """The stratum label and effective floor a theme of this size was gated by.

    Args:
        size: Theme size.
        floors: The build's solved floors, aligned with ``strata``.
        strata: The stratum edges.

    Returns:
        ``(stratum label, effective floor)``.
    """
    for index, (low, high) in enumerate(strata):
        if low <= size <= high:
            entry = floors[index] if index < len(floors) else {}
            label = f"{low}-{high}" if high < 10 ** 9 else f"{low}+"
            return (label, entry.get("effective"))
    return ("", None)


def main(argv: list[str] | None = None) -> int:
    """Write the reading inputs and the two measures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s"))
    parser.add_argument("--m", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_M"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/m_vs_o50s_2026-10-19"))
    args = parser.parse_args(argv)

    import o50s_build as o50s

    builds = {"O50s": read_build(args.o50s), "M": read_build(args.m)}
    allk = sorted({k for b in builds.values() for v in b["members"].values() for k in v})
    index = {key: i for i, key in enumerate(allk)}
    words = (len(allk) + 63) // 64
    print("PART A (prompt 48): M against O50s below the top. Judges nothing.")
    print(f"  O50s {len(builds['O50s']['members']):,} themes; "
          f"M {len(builds['M']['members']):,} themes; {len(allk):,} pathways", flush=True)

    packed = {}
    for name, build in builds.items():
        inband = {node: one for node, one in build["members"].items()
                  if band_of(len(one)) is not None}
        packed[name] = pack(inband, index, words)
        print(f"  {name}: {len(inband):,} themes of 10+ pathways", flush=True)

    unique: dict[str, dict[str, tuple[str, float]]] = {}
    for name, other in (("O50s", "M"), ("M", "O50s")):
        ids, stack, sizes = packed[name]
        _oids, ostack, osizes = packed[other]
        got: dict[str, tuple[str, float]] = {}
        for row, node in enumerate(ids):
            pick, score = best_against(stack[row], int(sizes[row]), ostack, osizes)
            got[node] = (_oids[pick] if pick >= 0 else "", score)
        unique[name] = got

    print("\n  UNIQUE THEMES (best J to the other build below "
          f"{SAME}), by band")
    labels = [f"{a}-{b}" if b < 10 ** 9 else f"{a}+" for a, b in BANDS]
    counts: dict[str, Counter[str]] = {}
    totals: dict[str, Counter[str]] = {}
    for name in builds:
        ids, _stack, sizes = packed[name]
        counts[name] = Counter()
        totals[name] = Counter()
        for row, node in enumerate(ids):
            one = band_of(int(sizes[row]))
            totals[name][one] += 1
            if unique[name][node][1] < SAME:
                counts[name][one] += 1
    print(f"  {'band':<10}" + "".join(f"{n + ' uniq':>12}{n + ' all':>11}" for n in builds))
    for one in labels:
        print(f"  {one:<10}" + "".join(
            f"{counts[n].get(one, 0):>12,}{totals[n].get(one, 0):>11,}" for n in builds))
    print(f"  {'TOTAL':<10}" + "".join(
        f"{sum(counts[n].values()):>12,}{sum(totals[n].values()):>11,}" for n in builds))
    return finish(args, builds, packed, unique, counts, totals, labels, index, allk, o50s)


def finish(args: argparse.Namespace, builds: Mapping[str, Mapping[str, object]],
           packed: Mapping[str, tuple[list[str], np.ndarray, np.ndarray]],
           unique: Mapping[str, Mapping[str, tuple[str, float]]],
           counts: Mapping[str, Counter], totals: Mapping[str, Counter],
           labels: Sequence[str], index: Mapping[str, int], allk: Sequence[str],
           o50s: object) -> int:
    """A1's reading inputs, A2's redundancy and A3's support.

    Args:
        args: Parsed arguments.
        builds: Both builds.
        packed: Per build, ``(ids, bitsets, sizes)`` over themes of 10+ pathways.
        unique: Per build, each theme's best counterpart in the other build.
        counts: Unique counts per band.
        totals: All-theme counts per band.
        labels: The band labels.
        index: Pathway key to bit position.
        allk: Every pathway key.
        o50s: The ``o50s_build`` module, for its strata.

    Returns:
        0.
    """
    with (args.data / "pathways.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    info = {f"{r['source']}:{r['source_id']}": (r["name"], r["source"]) for r in rows}

    print("\n  A2. REDUNDANCY: best J to another theme of the same build within a size factor "
          f"of {SIZE_FACTOR}")
    red: dict[str, dict[str, tuple[str, float]]] = {}
    for name in builds:
        ids, stack, sizes = packed[name]
        red[name] = redundancy(ids, stack, sizes)
    print(f"  {'band':<10}" + "".join(
        f"{n + ' uniq >=.8':>14}{n + ' med':>10}{n + ' all >=.8':>13}{n + ' med':>10}"
        for n in builds))
    red_table: list[dict[str, object]] = []
    for one in labels:
        cells = ""
        for name in builds:
            ids, _stack, sizes = packed[name]
            u = [red[name][n][1] for row, n in enumerate(ids)
                 if band_of(int(sizes[row])) == one and unique[name][n][1] < SAME]
            a = [red[name][n][1] for row, n in enumerate(ids)
                 if band_of(int(sizes[row])) == one]
            cells += (f"{(sum(1 for v in u if v >= NEAR) / len(u) if u else 0):>13.1%} "
                      f"{(statistics.median(u) if u else 0):>9.3f}"
                      f"{(sum(1 for v in a if v >= NEAR) / len(a) if a else 0):>12.1%} "
                      f"{(statistics.median(a) if a else 0):>9.3f}")
            red_table.append({"band": one, "build": name, "n_unique": len(u), "n_all": len(a),
                              "unique_near_share": round(
                                  sum(1 for v in u if v >= NEAR) / len(u), 4) if u else None,
                              "unique_median": round(statistics.median(u), 4) if u else None,
                              "all_near_share": round(
                                  sum(1 for v in a if v >= NEAR) / len(a), 4) if a else None,
                              "all_median": round(statistics.median(a), 4) if a else None})
        print(f"  {one:<10}{cells}")

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "redundancy.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["build", "node", "size", "band", "unique",
                                            "best_j", "partner"])
        writer.writeheader()
        for name in builds:
            ids, _stack, sizes = packed[name]
            for row, node in enumerate(ids):
                partner, score = red[name][node]
                writer.writerow({
                    "build": name, "node": node, "size": int(sizes[row]),
                    "band": band_of(int(sizes[row])),
                    "unique": "yes" if unique[name][node][1] < SAME else "no",
                    "best_j": round(score, 4), "partner": partner})

    print("\n  A3. SUPPORT of the unique themes, under their own build's gate")
    floors = {"O50s": json.loads((args.o50s / "floors_o50s.json").read_text())["solved"],
              "M": builds["M"]["manifest"]["floors"]}
    thetas = builds["M"]["manifest"].get("theta_match_per_stratum", {})
    print(f"  {'band':<10}" + "".join(f"{n + ' median':>14}{n + ' <=.02':>12}" for n in builds))
    sup_table: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    for one in labels:
        cells = ""
        for name in builds:
            ids, _stack, sizes = packed[name]
            vals = []
            for row, node in enumerate(ids):
                if band_of(int(sizes[row])) != one or unique[name][node][1] >= SAME:
                    continue
                value = float(builds[name]["nodes"][node]["support"])
                vals.append(value)
                stratum, floor = floor_for(int(sizes[row]), floors[name], o50s.O50S_STRATA)
                support_rows.append({
                    "build": name, "node": node, "size": int(sizes[row]), "band": one,
                    "support": round(value, 6), "stratum": stratum, "floor": floor,
                    "theta": thetas.get(stratum, 0.70) if name == "M" else 0.70})
            cells += (f"{(statistics.median(vals) if vals else 0):>13.4f} "
                      f"{(sum(1 for v in vals if v <= WEAK) / len(vals) if vals else 0):>11.1%}")
            sup_table.append({
                "band": one, "build": name, "n": len(vals),
                "median_support": round(statistics.median(vals), 4) if vals else None,
                "share_at_or_below_002": round(
                    sum(1 for v in vals if v <= WEAK) / len(vals), 4) if vals else None})
        print(f"  {one:<10}{cells}")
    with (args.out / "support.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["build", "node", "size", "band", "support",
                                            "stratum", "floor", "theta"])
        writer.writeheader()
        for row in support_rows:
            writer.writerow({k: ("" if row[k] is None else row[k]) for k in writer.fieldnames})

    rng = np.random.default_rng(SEED)
    drawn: list[tuple[str, str, int, str]] = []
    short: list[str] = []
    for name in builds:
        ids, _stack, sizes = packed[name]
        for one in labels:
            pool = [(node, int(sizes[row])) for row, node in enumerate(ids)
                    if band_of(int(sizes[row])) == one and unique[name][node][1] < SAME]
            pool.sort()
            if len(pool) <= PER_BAND:
                take = pool
                short.append(f"{name} {one}: {len(pool)} available, all taken")
            else:
                picked = rng.choice(len(pool), PER_BAND, replace=False)
                take = [pool[i] for i in sorted(picked.tolist())]
            drawn.extend((name, node, size, one) for node, size in take)
    order = rng.permutation(len(drawn))
    shuffled = [drawn[i] for i in order.tolist()]
    print(f"\n  A1. READING INPUTS: {len(shuffled)} themes drawn "
          f"({PER_BAND} per band per side where available)")
    for line in short:
        print(f"    short band -- {line}")

    reading = args.out / "read_inputs"
    reading.mkdir(parents=True, exist_ok=True)
    for old in reading.glob("T_b*.md"):
        old.unlink()
    key: dict[str, object] = {}
    listing: dict[str, int] = {}
    blocks: list[tuple[str, list[str]]] = []
    for position, (name, node, size, one) in enumerate(shuffled, 1):
        tid = f"T{position:03d}"
        key[tid] = {"build": name, "node": node, "size": size, "band": one,
                    "support": float(builds[name]["nodes"][node]["support"])}
        listing[tid] = size
        lines = [f"## {tid}  ({size} pathways)", ""]
        for pathway in sorted(builds[name]["members"][node],
                              key=lambda k: (info.get(k, (k, ""))[0].lower(), k)):
            label, source = info.get(pathway, (pathway, "?"))
            lines.append(f"{label} [{source}]")
        lines.append("")
        blocks.append((tid, lines))
    batch, count, written = [], 0, []
    for tid, lines in blocks:
        if batch and count + len(lines) > BATCH_LINES:
            path = reading / f"T_b{len(written) + 1:02d}.md"
            path.write_text("\n".join(batch) + "\n", encoding="utf-8")
            written.append((path, count))
            batch, count = [], 0
        batch.extend(lines)
        count += len(lines)
        del tid
    if batch:
        path = reading / f"T_b{len(written) + 1:02d}.md"
        path.write_text("\n".join(batch) + "\n", encoding="utf-8")
        written.append((path, count))
    (args.out / "index.json").write_text(json.dumps(listing, indent=1) + "\n", encoding="utf-8")
    (args.out / "KEY_DO_NOT_SHARE_m_vs_o50s.json").write_text(
        json.dumps(key, indent=1) + "\n", encoding="utf-8")
    (args.out / "measures.json").write_text(json.dumps({
        "same": SAME, "near": NEAR, "size_factor": SIZE_FACTOR, "weak": WEAK,
        "per_band": PER_BAND, "seed": SEED, "bands": [list(b) for b in BANDS],
        "unique_counts": {n: dict(counts[n]) for n in builds},
        "all_counts": {n: dict(totals[n]) for n in builds},
        "redundancy": red_table, "support": sup_table,
        "short_bands": short, "n_drawn": len(shuffled),
        "batches": [{"path": str(p), "lines": c} for p, c in written],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"  {len(written)} batch(es):")
    for path, lines in written:
        print(f"    {path}  {lines:,} lines")
    print(f"  -> {args.out / 'index.json'}, the key, redundancy.tsv, support.tsv")
    print("  The key is written and is never read again by this session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
