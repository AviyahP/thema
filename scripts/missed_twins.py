"""Prompt 56 Part A: are O50s's after-gate merges catching twins families should have pooled?

Declared 22 Oct 2026. Evaluation only; no build changes and nothing adopted.

**Task 0, from the code.** Step 5 compares **completed** sets, not raw ones.
``recurrent.py:1180`` picks which::

    of = (lambda g: member_bits[g]) if member_bits is not None else (lambda g: pool.groupings[g])

and ``v04.py:299`` passes ``completed`` as ``member_bits``::

    grouped = families(list(completed), completed, pool, None, conf)

so the first branch is taken. The twin rule is ``recurrent.py:1067-1086``, used here by **import**
rather than restatement, with ``TWIN_FLOOR = 2`` and ``TWIN_FRACTION = 0.10``::

    shared = bits.count(a & b)
    if not shared:
        return False
    allowed = max(TWIN_FLOOR, int(TWIN_FRACTION * shared))
    return bits.count(a & ~b) <= allowed and bits.count(b & ~a) <= allowed

The allowance is on the **shared part** and ``int()`` truncates, so a shared part of 29 allows 2.

**Two moments, kept separate.** The twin test is applied to each merged pair twice:

``at the event``      the sets as they actually were when the rule fired. For rule 3 those are
                      prompt 52's ``sup_blocks`` and ``sup_against``; a newcomer can have grown by
                      inheritance before it met the theme that superseded it, so these are not the
                      gate's sets.
``at gate exit``      the two themes' gated blocks, before any inheritance. This is the moment
                      families is answerable for.

Conflating them would answer the wrong question: "these were twins when the rule fired" does not
imply "families should have pooled them", and the gap between the two columns is precisely the work
inheritance did.

Part B is not run: no replay, so no rule 1, 2 or 4 counts and no rule-2 twin test.

Usage:
    uv run scripts/missed_twins.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

J_BANDS: tuple[tuple[float, float, str], ...] = (
    (0.0, 0.5, "<0.5"), (0.5, 0.6, "0.5-0.6"), (0.6, 0.7, "0.6-0.7"),
    (0.7, 0.83, "0.7-0.83"), (0.83, 1.0001, "0.83+"),
)

RATIO_BANDS: tuple[tuple[float, float, str], ...] = (
    (0.0, 0.5, "<0.5"), (0.5, 0.8, "0.5-0.8"), (0.8, 0.91, "0.8-0.91"), (0.91, 1.0001, "0.91+"),
)

SIZE_BANDS: tuple[tuple[int, int, str], ...] = (
    (3, 5, "3-5"), (6, 11, "6-11"), (12, 24, "12-24"), (25, 49, "25-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def fband(value: float, bands: tuple) -> str:
    """The half-open band a fraction falls in, the last band closed at the top.

    Args:
        value: A fraction.
        bands: ``(low, high, label)`` in order.

    Returns:
        Band label.
    """
    for low, high, name in bands:
        if low <= value < high:
            return name
    return bands[-1][2]


def sband(size: int) -> str:
    """The closed size band a count falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label.
    """
    for low, high, name in SIZE_BANDS:
        if low <= size <= high:
            return name
    return SIZE_BANDS[0][2]


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    """Jaccard of two bitsets.

    Args:
        a: Bitset.
        b: Bitset.

    Returns:
        The Jaccard.
    """
    inter = int(np.bitwise_count(a & b).sum())
    union = int(np.bitwise_count(a | b).sum())
    return inter / union if union else 0.0


def load(args: argparse.Namespace) -> dict[str, object]:
    """Everything Part A needs: the probe, the gated blocks and the final themes.

    Args:
        args: Parsed arguments.

    Returns:
        The loaded material.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.universe import load_embedded
    from thema.ontology.v04 import Material, gate

    frozen = json.loads((args.frozen / "manifest.json").read_text())
    floors = frozen["floors"]
    strata = [tuple(s) for s in frozen["strata"]]
    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    index = {key: i for i, key in enumerate(keys)}
    width = bits.words_for(len(keys)) * bits.WORD

    with np.load(args.space_root / "calibration" / "real.npz") as handle:
        blocks, supports = handle["blocks"], handle["supports"]
        indptr = handle["indptr"]
        vote_keys, vote_vals = handle["vote_keys"], handle["vote_vals"]
    votes = tuple(
        dict(zip(vote_keys[indptr[i]:indptr[i + 1]].tolist(),
                 vote_vals[indptr[i]:indptr[i + 1]].tolist(), strict=True))
        for i in range(len(indptr) - 1))
    material = Material(blocks=blocks, supports=supports, selections=votes)
    keep = np.flatnonzero(gate(material.rows(), floors, strata))

    with np.load(args.probe, allow_pickle=False) as probe:
        got = {k: probe[k] for k in probe.files}
    if not np.array_equal(keep, got["keep"]):
        raise ValueError("the re-gated set is not prompt 52's logged gate")
    gated = blocks[keep]

    with (args.frozen / "nodes.tsv").open(encoding="utf-8") as handle:
        ids = [row["node"] for row in csv.DictReader(handle, delimiter="\t")]
    held: dict[str, list[int]] = defaultdict(list)
    with (args.frozen / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            held[row["node"]].append(index[row["key"]])
    final = np.vstack([bits.pack(sorted(held[node]), width)[None, :] for node in ids])

    with np.load(args.side, allow_pickle=False) as side:
        raw = {k: side[k] for k in ("groupings", "row_seed", "family_seeds",
                                    "completed_keys", "family_flat", "family_offsets")}
    return {"probe": got, "gated": gated, "keep": keep, "final": final, "ids": ids,
            "keys": keys, "width": width, "side": raw}


def event_table(name: str, pairs: list[dict], ratio: bool = False) -> list[str]:
    """Task 2's three breakdowns for one event kind.

    Args:
        name: Event kind.
        pairs: One record per event.
        ratio: Also break down by size ratio, for chain collapses.

    Returns:
        Lines.
    """
    total = len(pairs)
    passes = sum(1 for p in pairs if p["twin_event"])
    out = [f"  {name}: {total:,} events; twin test at the EVENT passes "
           f"{passes:,} = {passes / total:.1%}" if total else f"  {name}: none"]
    if not total:
        return out
    out.append(f"    {'J band':<12}{'events':>9}{'twin':>9}{'share':>9}")
    for _lo, _hi, j in J_BANDS:
        here = [p for p in pairs if p["j_band"] == j]
        if not here:
            continue
        hit = sum(1 for p in here if p["twin_event"])
        out.append(f"    {j:<12}{len(here):>9,}{hit:>9,}{hit / len(here):>9.1%}")
    out.append(f"    {'larger band':<12}{'events':>9}{'twin':>9}{'share':>9}")
    for _lo, _hi, s in SIZE_BANDS:
        here = [p for p in pairs if p["size_band"] == s]
        if not here:
            continue
        hit = sum(1 for p in here if p["twin_event"])
        out.append(f"    {s:<12}{len(here):>9,}{hit:>9,}{hit / len(here):>9.1%}")
    if ratio:
        out.append(f"    {'size ratio':<12}{'events':>9}{'twin':>9}{'share':>9}")
        for _lo, _hi, r in RATIO_BANDS:
            here = [p for p in pairs if p["ratio_band"] == r]
            if not here:
                continue
            hit = sum(1 for p in here if p["twin_event"])
            out.append(f"    {r:<12}{len(here):>9,}{hit:>9,}{hit / len(here):>9.1%}")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run Part A: tasks 0 to 4 for the three after-gate merge kinds.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.ontology.recurrent import TWIN_FLOOR, TWIN_FRACTION, is_variant

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--probe", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/probe.npz"))
    parser.add_argument("--side", type=Path,
                        default=Path("data/experiments/merge_relationships_2026-10-22/side.npz"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/missed_twins_2026-10-22"))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    got = load(args)
    probe, gated, final = got["probe"], got["gated"], got["final"]
    post = probe["consensus_members"]
    accepted = probe["accepted"]

    print("PROMPT 56 PART A: are O50s's after-gate merges missed twins?")
    print(f"  twin rule imported from recurrent.is_variant; TWIN_FLOOR={TWIN_FLOOR}, "
          f"TWIN_FRACTION={TWIN_FRACTION}")
    print(f"  gate {len(gated):,} themes (identical to prompt 52's log); "
          f"post-consensus {len(post):,}; final {len(final):,}")
    print()
    print("=" * 100)
    print("0. WHAT STEP 5 COMPARES")
    print("=" * 100)
    print("  COMPLETED sets, not raw. recurrent.py:1180 selects:")
    print("    of = (lambda g: member_bits[g]) if member_bits is not None "
          "else (lambda g: pool.groupings[g])")
    print("  and v04.py:299 passes `completed` as member_bits:")
    print("    grouped = families(list(completed), completed, pool, None, conf)")
    print("  so a gated theme's members ARE its seed grouping's completed set "
          "(v04.py: blocks.append(completed[seed])).")
    print()

    kinds: dict[str, list[dict]] = {}

    # --- rule 3 supersessions -----------------------------------------------------------------
    rows = []
    for i in range(len(probe["sup_dropped"])):
        a_ev, b_ev = probe["sup_blocks"][i], probe["sup_against"][i]
        a_gate = gated[int(probe["sup_dropped"][i])]
        b_gate = gated[int(probe["sup_kept"][i])]
        sizes = (int(np.bitwise_count(a_ev).sum()), int(np.bitwise_count(b_ev).sum()))
        rows.append({
            "kind": "rule 3", "i": i,
            "twin_event": bool(is_variant(a_ev, b_ev)),
            "twin_gate": bool(is_variant(a_gate, b_gate)),
            "j_event": jaccard(a_ev, b_ev), "j_gate": jaccard(a_gate, b_gate),
            "j_band": fband(jaccard(a_ev, b_ev), J_BANDS),
            "size_band": sband(max(sizes)),
            "dropped_gated": int(probe["sup_dropped"][i]),
            "kept_gated": int(probe["sup_kept"][i]),
            "size_dropped": sizes[0], "size_kept": sizes[1],
        })
    kinds["rule 3"] = rows

    # --- stale merges: post-consensus indices, so the gate sets come via `accepted` ------------
    rows = []
    for d, k in zip(probe["merge_dropped"], probe["merge_kept"], strict=True):
        a_ev, b_ev = post[int(d)], post[int(k)]
        a_gate, b_gate = gated[int(accepted[int(d)])], gated[int(accepted[int(k)])]
        sizes = (int(np.bitwise_count(a_ev).sum()), int(np.bitwise_count(b_ev).sum()))
        rows.append({
            "kind": "stale merge",
            "twin_event": bool(is_variant(a_ev, b_ev)),
            "twin_gate": bool(is_variant(a_gate, b_gate)),
            "j_event": jaccard(a_ev, b_ev), "j_gate": jaccard(a_gate, b_gate),
            "j_band": fband(jaccard(a_ev, b_ev), J_BANDS),
            "size_band": sband(max(sizes)),
            "dropped_gated": int(accepted[int(d)]), "kept_gated": int(accepted[int(k)]),
            "size_dropped": sizes[0], "size_kept": sizes[1],
        })
    kinds["stale merge"] = rows

    # --- chain collapses ----------------------------------------------------------------------
    rows = []
    for v, k in zip(probe["collapse_victim"], probe["collapse_keeper"], strict=True):
        a_ev, b_ev = post[int(v)], post[int(k)]
        sizes = (int(np.bitwise_count(a_ev).sum()), int(np.bitwise_count(b_ev).sum()))
        rows.append({
            "kind": "chain collapse",
            "twin_event": bool(is_variant(a_ev, b_ev)),
            "j_event": jaccard(a_ev, b_ev),
            "j_band": fband(jaccard(a_ev, b_ev), J_BANDS),
            "size_band": sband(max(sizes)),
            "ratio_band": fband(min(sizes) / max(sizes) if max(sizes) else 0.0, RATIO_BANDS),
            "size_dropped": sizes[0], "size_kept": sizes[1],
        })
    kinds["chain collapse"] = rows

    print("=" * 100)
    print("1. EVENT COUNTS (the three after-gate merge kinds; Part B's rules 1, 2, 4 not run)")
    print("=" * 100)
    n3, ns, nc = (len(kinds["rule 3"]), len(kinds["stale merge"]), len(kinds["chain collapse"]))
    print(f"  consensus rule 3, superseded      {n3:>8,}")
    print(f"  repair stale merges               {ns:>8,}")
    print(f"  repair chain collapses            {nc:>8,}")
    print(f"  {'':<34}{'':>8}")
    print(f"  gated themes                      {len(gated):>8,}")
    print(f"  after consensus                   {len(post):>8,}   "
          f"= {len(gated):,} - {n3:,} dropped by rule 3")
    print(f"  final themes                      {len(final):>8,}   "
          f"= {len(post):,} - {nc:,} collapsed - {ns:,} stale merged")
    ok = (len(gated) - n3 == len(post)) and (len(post) - nc - ns == len(final))
    print(f"  reconciles exactly: {ok}")
    print("  NOT reconciled here: rules 1, 2 and 4 remove nothing, so they do not enter the")
    print("  arithmetic; their counts need Part B's replay and are not reported.")
    print()

    print("=" * 100)
    print("2. TWIN TEST AT THE EVENT, BY J BAND AND SIZE BAND")
    print("=" * 100)
    for name in ("rule 3", "stale merge", "chain collapse"):
        for line in event_table(name, kinds[name], ratio=(name == "chain collapse")):
            print(line)
        print()

    print("=" * 100)
    print("3. TWIN TEST AT GATE EXIT, BEFORE ANY INHERITANCE")
    print("=" * 100)
    print("  the moment families is answerable for. A gated theme's members ARE its seed's")
    print("  completed set, so a pass here means two family seeds whose completed sets are twins.")
    print(f"  {'kind':<16}{'events':>9}{'twin at gate':>14}{'share':>9}"
          f"{'twin at event':>15}{'share':>9}")
    for name in ("rule 3", "stale merge"):
        rows = kinds[name]
        g = sum(1 for p in rows if p["twin_gate"])
        e = sum(1 for p in rows if p["twin_event"])
        print(f"  {name:<16}{len(rows):>9,}{g:>14,}{g / len(rows):>9.1%}"
              f"{e:>15,}{e / len(rows):>9.1%}")
    grew = [p for name in ("rule 3", "stale merge") for p in kinds[name]
            if p["twin_event"] and not p["twin_gate"]]
    shrank = [p for name in ("rule 3", "stale merge") for p in kinds[name]
              if p["twin_gate"] and not p["twin_event"]]
    print(f"\n  twin at the event but NOT at gate exit: {len(grew):,} "
          "(inheritance made them twins)")
    print(f"  twin at gate exit but NOT at the event: {len(shrank):,} "
          "(inheritance pulled them apart)")
    print()
    print("=" * 100)
    print("4. RULE 3 SUPERSESSIONS THAT FAIL THE TWIN TEST: WOULD THE DROPPED THEME BE A ROOT?")
    print("=" * 100)
    print("  a dropped theme not strictly inside ANY final O50s theme would have had no parent")
    print("  and so would have been a root had it been kept. Measured on the set AS DROPPED")
    print("  (the event-time set), which is the set that was actually discarded.")
    f_sizes = np.bitwise_count(final).sum(axis=1).astype(np.int64)
    failing = [p for p in kinds["rule 3"] if not p["twin_event"]]
    inside_none: dict[str, int] = defaultdict(int)
    totals: dict[str, int] = defaultdict(int)
    for record in failing:
        block = probe["sup_blocks"][record["i"]]
        size = int(np.bitwise_count(block).sum())
        band_name = sband(size)
        totals[band_name] += 1
        outside = np.bitwise_count(block[None, :] & ~final).sum(axis=1)
        strictly = (outside == 0) & (f_sizes > size)
        if not bool(strictly.any()):
            inside_none[band_name] += 1
    print(f"  {'dropped band':<14}{'failing':>10}{'inside no final theme':>24}{'share':>9}")
    for _lo, _hi, s in SIZE_BANDS:
        if not totals[s]:
            continue
        print(f"  {s:<14}{totals[s]:>10,}{inside_none[s]:>24,}"
              f"{inside_none[s] / totals[s]:>9.1%}")
    tot, orph = sum(totals.values()), sum(inside_none.values())
    print(f"  {'ALL':<14}{tot:>10,}{orph:>24,}{orph / tot:>9.1%}")
    print()

    json.dump({"kinds": {k: [{kk: vv for kk, vv in p.items() if kk != "i"} for p in v]
                         for k, v in kinds.items()},
               "task4": {"failing": tot, "inside_no_final_theme": orph,
                         "by_band": {s: [totals[s], inside_none[s]]
                                     for _l, _h, s in SIZE_BANDS if totals[s]}}},
              (args.out / "events.json").open("w"), indent=0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
