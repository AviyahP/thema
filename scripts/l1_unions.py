"""Prompt 62: are L1's large themes unions of smaller themes? Declared 24 Oct 2026.

**Evaluation only: no rule is applied and nothing is removed.**

The set is the 90%-each-way themes found in at least 10 runs -- a **provisional working bar**, not a
calibrated one. For every accepted theme of 25 or more pathways:

* its **inner themes** are the accepted themes smaller than it with at least 90% of themselves
  inside it;
* **single cover** is the largest share of it that one inner theme covers;
* **greedy cover** repeatedly takes the inner theme covering the most still-uncovered pathways,
  recording coverage after one, two and three picks;
* the **two-block pattern** is coverage of at least 90% by the first two picks with those two below
  Jaccard 0.5 of each other, and the three-block pattern is the same with three mutually distant
  picks.

Ties in the greedy are broken, in order, by: larger overlap with the target, then larger inner
theme, then lower theme index. Declared here so the pick sequence is reproducible rather than
dependent on an argmax's internals.

**Containment, not Jaccard, defines an inner theme**, so a near-variant of the target qualifies: an
accepted theme one pathway smaller and otherwise identical is 100% inside it. That is what the
measure says, and it is reported rather than filtered -- see the note for what it does to the first
pick of the biggest sets.

Every step is checked against an explicit loop over sets on a random sample (seed 20261024).

Usage:
    uv run scripts/l1_unions.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SEED = 20261024
FOUND_BAR = 10
TARGET_MIN = 25
INNER_CONTAIN = 0.90
COVER_BLOCK = 0.90
BLOCK_J = 0.50
PICKS = 3
EXAMPLES = 20
EXAMPLE_MIN = 100
SAMPLE_TARGETS = 200
CHUNK = 192

BANDS: tuple[tuple[int, int, str], ...] = (
    (25, 49, "25-49"), (50, 99, "50-99"), (100, 199, "100-199"), (200, 399, "200-399"),
    (400, 799, "400-799"), (800, 1599, "800-1599"), (1600, 10**9, "1600+"),
)


def band_of(size: int) -> str:
    """The band a size falls in.

    Args:
        size: Pathway count.

    Returns:
        Band label, or ``"under 25"``.
    """
    for low, high, name in BANDS:
        if low <= size <= high:
            return name
    return "under 25"


def accepted_side(where: Path) -> dict[str, object]:
    """The accepted themes of one side: members, sizes, and the matrix.

    Args:
        where: A directory ``l1_build`` wrote.

    Returns:
        ``{rows, sizes, matrix, which, n}``.
    """
    from scipy import sparse

    from l1_report import load_l1

    side = load_l1(where)
    which = np.flatnonzero(side["t_found"] >= FOUND_BAR)
    ptr, path = side["t_member_indptr"], side["t_member_pathway"]
    rows = [path[ptr[int(t)]:ptr[int(t) + 1]] for t in which]
    sizes = np.array([len(r) for r in rows], dtype=np.int64)
    n = int(path.max()) + 1 if len(path) else 0
    return {"rows": rows, "sizes": sizes, "which": which, "side": side, "n": n,
            "matrix": sparse.csr_matrix(
                (np.ones(int(sizes.sum()), dtype=np.int32),
                 np.concatenate(rows), np.concatenate([[0], np.cumsum(sizes)])),
                shape=(len(rows), max(n, 1)))}


def inner_themes(accepted: dict[str, object], targets: list[np.ndarray], n: int,
                 report: bool = True) -> list[tuple[np.ndarray, np.ndarray]]:
    """For each target, the accepted themes smaller than it and 90% inside it.

    ``|S inter T| >= 0.9 |S|`` and ``|S| < |T|``. Integer arithmetic, and no size window is used:
    the containment test puts no lower bound on ``|T|`` relative to ``|S|`` beyond ``|S| < |T|``,
    which is applied directly.

    Args:
        accepted: As :func:`accepted_side` returns.
        targets: Member arrays of the targets.
        n: Universe size.
        report: Print progress.

    Returns:
        Per target, ``(inner theme indices, their overlap with the target)``.
    """
    from scipy import sparse

    sizes = accepted["sizes"]
    target_sizes = np.array([len(t) for t in targets], dtype=np.int64)
    block = sparse.csr_matrix(
        (np.ones(int(target_sizes.sum()), dtype=np.int32),
         np.concatenate(targets), np.concatenate([[0], np.cumsum(target_sizes)])),
        shape=(len(targets), n)).T.tocsc()
    out: list[tuple[np.ndarray, np.ndarray]] = [None] * len(targets)   # type: ignore[list-item]
    clock = time.perf_counter()
    for begin in range(0, len(targets), CHUNK):
        stop = min(begin + CHUNK, len(targets))
        got = (accepted["matrix"] @ block[:, begin:stop]).tocoo()
        left, right = got.row, got.col + begin
        inter = got.data.astype(np.int64)
        keep = (sizes[left] < target_sizes[right]) & (10 * inter >= 9 * sizes[left])
        left, right, inter = left[keep], right[keep], inter[keep]
        order = np.lexsort((left, right))
        left, right, inter = left[order], right[order], inter[order]
        bounds = np.searchsorted(right, np.arange(begin, stop + 1))
        for local in range(stop - begin):
            a, b = bounds[local], bounds[local + 1]
            out[begin + local] = (left[a:b], inter[a:b])
        if report and (begin // CHUNK) % 10 == 0:
            print(f"      inner themes {stop:,}/{len(targets):,} "
                  f"({time.perf_counter() - clock:.0f}s)", flush=True)
    if report:
        counts = np.array([len(i) for i, _o in out])
        print(f"    inner themes: median {np.median(counts):.0f}, max {counts.max():,} "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return out


def greedy_cover(accepted: dict[str, object], targets: list[np.ndarray],
                 inner: list[tuple[np.ndarray, np.ndarray]], n: int,
                 exclude_near: bool = False, report: bool = True) -> dict[str, object]:
    """The greedy cover of each target by its inner themes, three picks deep.

    ``exclude_near`` drops inner themes that are themselves near-copies of the target, at the same
    ``J < 0.5`` the block patterns use. **This is an addition to the prompt, not its measure.** It
    exists because the declared measure's first pick is usually a variant of the target -- an
    accepted theme one or two pathways smaller is fully contained and covers 98% on its own -- which
    answers "can one theme cover T" rather than "is T two unrelated blocks". Both passes are
    reported, and the declared one is the one labelled declared.

    Args:
        accepted: As :func:`accepted_side` returns.
        targets: Member arrays of the targets.
        inner: As :func:`inner_themes` returns.
        n: Universe size.
        exclude_near: Drop inner themes with ``J >= 0.5`` against the target.
        report: Print progress.

    Returns:
        ``{picks, covered, single, jaccard, two_block, three_block}``.
    """
    matrix, sizes = accepted["matrix"], accepted["sizes"]
    rows = accepted["rows"]
    total = len(targets)
    picks = -np.ones((total, PICKS), dtype=np.int64)
    covered = np.zeros((total, PICKS), dtype=np.float64)
    single = np.zeros(total, dtype=np.float64)
    clock = time.perf_counter()
    for t, members in enumerate(targets):
        where, overlap = inner[t]
        if exclude_near and len(where):
            union = sizes[where] + len(members) - overlap
            far = overlap * 2 < union
            where, overlap = where[far], overlap[far]
        if not len(where):
            continue
        single[t] = overlap.max() / len(members)
        block = matrix[where]
        mask = np.zeros(n, dtype=np.int32)
        mask[members] = 1
        taken = np.zeros(len(where), dtype=bool)
        done = 0
        for round_at in range(PICKS):
            gains = block @ mask
            gains[taken] = -1
            if gains.max() <= 0:
                covered[t, round_at:] = done / len(members)
                break
            order = np.lexsort((where, -sizes[where], -overlap, -gains))
            chosen = int(order[0])
            taken[chosen] = True
            picks[t, round_at] = where[chosen]
            done += int(gains[chosen])
            mask[rows[where[chosen]]] = 0
            covered[t, round_at] = done / len(members)
        if report and t and t % 2000 == 0:
            print(f"      greedy {t:,}/{total:,} ({time.perf_counter() - clock:.0f}s)", flush=True)
    jaccard = np.zeros(total, dtype=np.float64)
    for t in range(total):
        if picks[t, 0] >= 0 and picks[t, 1] >= 0:
            jaccard[t] = _jaccard(rows[picks[t, 0]], rows[picks[t, 1]])
    two = (covered[:, 1] >= COVER_BLOCK) & (jaccard < BLOCK_J) & (picks[:, 1] >= 0)
    three = np.zeros(total, dtype=bool)
    for t in range(total):
        if covered[t, 2] >= COVER_BLOCK and picks[t, 2] >= 0:
            trio = picks[t]
            three[t] = all(_jaccard(rows[trio[i]], rows[trio[j]]) < BLOCK_J
                           for i in range(PICKS) for j in range(i + 1, PICKS))
    if report:
        print(f"    greedy: {int(two.sum()):,} two-block, {int(three.sum()):,} three-block "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"picks": picks, "covered": covered, "single": single, "jaccard": jaccard,
            "two_block": two, "three_block": three}


def _jaccard(a: np.ndarray, b: np.ndarray) -> float:
    """Jaccard of two sorted index arrays.

    Args:
        a: One set.
        b: The other.

    Returns:
        The Jaccard.
    """
    inter = len(np.intersect1d(a, b, assume_unique=True))
    union = len(a) + len(b) - inter
    return inter / union if union else 0.0


def brute_check(accepted: dict[str, object], targets: list[np.ndarray],
                inner: list[tuple[np.ndarray, np.ndarray]], got: dict[str, object],
                exclude_near: bool = False,
                sample: int = SAMPLE_TARGETS) -> dict[str, object]:
    """Inner sets and the greedy by explicit set loops, on a random sample of targets.

    Args:
        accepted: As :func:`accepted_side` returns.
        targets: Member arrays of the targets.
        inner: As :func:`inner_themes` returns.
        got: As :func:`greedy_cover` returns.
        exclude_near: Match the pass being checked.
        sample: How many targets to check.

    Returns:
        The comparison.
    """
    rng = random.Random(SEED)
    rows, sizes = accepted["rows"], accepted["sizes"]
    sets = None
    pick = rng.sample(range(len(targets)), min(sample, len(targets)))
    inner_same = picks_same = cover_same = flags_same = 0
    for t in pick:
        target = set(targets[t].tolist())
        if sets is None:
            sets = [set(r.tolist()) for r in rows]
        slow_inner = [i for i in range(len(rows))
                      if sizes[i] < len(target) and 10 * len(sets[i] & target) >= 9 * sizes[i]]
        inner_same += sorted(slow_inner) == sorted(inner[t][0].tolist())
        if exclude_near:
            slow_inner = [i for i in slow_inner
                          if len(sets[i] & target) * 2
                          < len(sets[i]) + len(target) - len(sets[i] & target)]
        uncovered = set(target)
        slow_picks, slow_cover = [], []
        for _round in range(PICKS):
            best, best_key = None, None
            for i in slow_inner:
                if i in slow_picks:
                    continue
                gain = len(sets[i] & uncovered)
                key = (gain, len(sets[i] & target), int(sizes[i]), -i)
                if gain > 0 and (best_key is None or key > best_key):
                    best, best_key = i, key
            if best is None:
                slow_cover += [1 - len(uncovered) / len(target)] * (PICKS - len(slow_picks))
                break
            slow_picks.append(best)
            uncovered -= sets[best]
            slow_cover.append(1 - len(uncovered) / len(target))
        fast_picks = [int(p) for p in got["picks"][t] if p >= 0]
        picks_same += fast_picks == slow_picks
        cover_same += all(abs(a - b) < 1e-9
                          for a, b in zip(got["covered"][t][:len(slow_cover)], slow_cover,
                                          strict=False))
        two = (len(slow_cover) > 1 and slow_cover[1] >= COVER_BLOCK and len(slow_picks) > 1
               and _jaccard(rows[slow_picks[0]], rows[slow_picks[1]]) < BLOCK_J)
        flags_same += bool(two) == bool(got["two_block"][t])
    return {"targets": len(pick), "inner_sets_agree": inner_same, "picks_agree": picks_same,
            "coverage_agrees": cover_same, "two_block_agrees": flags_same,
            "identical": (inner_same == len(pick) and picks_same == len(pick)
                          and cover_same == len(pick) and flags_same == len(pick))}


def table_one(targets: list[np.ndarray], got: dict[str, object],
              label: str = "DECLARED") -> dict[str, object]:
    """Table 1: the measures by band.

    Args:
        targets: Member arrays of the targets.
        got: As :func:`greedy_cover` returns.
        label: Which pass this is.

    Returns:
        The table as data.
    """
    sizes = np.array([len(t) for t in targets], dtype=np.int64)
    bands = np.array([band_of(int(s)) for s in sizes])
    print("=" * 112)
    print(f"1. BY BAND, {label}. Accepted = 90%-each-way themes found in >= 10 runs "
          "(PROVISIONAL working bar)")
    print("=" * 112)
    print(f"  {'band':<12}{'themes':>9}{'med single':>12}{'med 1 pick':>12}{'med 2 picks':>13}"
          f"{'med 3 picks':>13}{'two-block':>12}{'three-block':>13}")
    rows = {}
    for _lo, _hi, band in BANDS:
        where = bands == band
        if not where.any():
            continue
        count = int(where.sum())
        cells = {
            "themes": count,
            "median_single": float(np.median(got["single"][where])),
            "median_1": float(np.median(got["covered"][where, 0])),
            "median_2": float(np.median(got["covered"][where, 1])),
            "median_3": float(np.median(got["covered"][where, 2])),
            "two_block": int(got["two_block"][where].sum()),
            "three_block": int(got["three_block"][where].sum()),
        }
        print(f"  {band:<12}{count:>9,}{cells['median_single']:>12.3f}"
              f"{cells['median_1']:>12.3f}{cells['median_2']:>13.3f}{cells['median_3']:>13.3f}"
              f"{cells['two_block'] / count:>11.1%}{cells['three_block'] / count:>13.1%}")
        rows[band] = cells
    total = len(targets)
    print(f"  {'ALL':<12}{total:>9,}{np.median(got['single']):>12.3f}"
          f"{np.median(got['covered'][:, 0]):>12.3f}{np.median(got['covered'][:, 1]):>13.3f}"
          f"{np.median(got['covered'][:, 2]):>13.3f}"
          f"{got['two_block'].sum() / total:>11.1%}{got['three_block'].sum() / total:>13.1%}")
    print()
    return {"by_band": rows, "all": {"themes": total,
                                     "two_block": int(got["two_block"].sum()),
                                     "three_block": int(got["three_block"].sum())}}


def table_two(accepted: dict[str, object], large: list[np.ndarray], n: int,
              args: argparse.Namespace, exclude_near: bool = False) -> dict[str, object]:
    """Table 2: the seven distinct large sets, pick by pick.

    The seven sets come from `large7/`, which the 24 Oct follow-up built from the **Jaccard** side,
    because that is what the blind reading was of. The inner themes come from the accepted
    90%-each-way themes, as this prompt's SET says. So the targets and the candidates come from
    different sides on purpose, and a set is therefore not necessarily an accepted theme itself.

    Args:
        accepted: As :func:`accepted_side` returns.
        large: The seven member arrays, largest first.
        n: Universe size.
        args: Parsed arguments.
        exclude_near: Drop inner themes that are near-copies of the set itself.

    Returns:
        The table as data.
    """
    rows = accepted["rows"]
    inner = inner_themes(accepted, large, n, report=False)
    got = greedy_cover(accepted, large, inner, n, exclude_near=exclude_near, report=False)
    print("=" * 112)
    print("2. THE SEVEN DISTINCT SETS ABOVE 800 PATHWAYS (large7/, from the Jaccard side)"
          + (" -- NEAR-COPIES OF THE SET DROPPED" if exclude_near else " -- DECLARED"))
    print("=" * 112)
    print(f"  {'set':<7}{'size':>7}  {'pick':<5}{'pick size':>10}{'covers':>9}"
          f"{'J to the set':>14}{'other sets at J >= 0.5':>24}{'cumulative':>12}")
    out: dict[str, object] = {}
    for i, members in enumerate(large):
        record = []
        for r in range(PICKS):
            p = int(got["picks"][i, r])
            if p < 0:
                break
            overlap = len(np.intersect1d(rows[p], members, assume_unique=True))
            others = [j for j in range(len(large)) if j != i
                      and _jaccard(rows[p], large[j]) >= BLOCK_J]
            record.append({"theme": p, "size": int(len(rows[p])),
                           "covers": overlap / len(members),
                           "j_to_set": _jaccard(rows[p], members),
                           "other_sets": [j + 1 for j in others],
                           "cumulative": float(got["covered"][i, r])})
            print(f"  {'set_' + str(i + 1):<7}{len(members):>7,}  {r + 1:<5}"
                  f"{len(rows[p]):>10,}{overlap / len(members):>9.1%}"
                  f"{_jaccard(rows[p], members):>14.3f}"
                  f"{(str([j + 1 for j in others]) if others else 'none'):>24}"
                  f"{got['covered'][i, r]:>12.1%}")
        out[f"set_{i + 1}"] = {"size": int(len(members)), "picks": record,
                               "single": float(got["single"][i]),
                               "j_pick1_pick2": float(got["jaccard"][i]),
                               "two_block": bool(got["two_block"][i]),
                               "three_block": bool(got["three_block"][i]),
                               "inner": int(len(inner[i][0]))}
        print(f"  {'':<7}{'':>7}  J(pick 1, pick 2) {got['jaccard'][i]:.3f}; "
              f"two-block {bool(got['two_block'][i])}; three-block "
              f"{bool(got['three_block'][i])}; {len(inner[i][0]):,} inner themes")
    print()
    print("  Do sets 5, 6 and 7 -- the three that read as single broad domains -- appear among the")
    print("  picks of sets 1-4? And, since the three picks can be near-variants of the target, the")
    print("  best match to each of them anywhere in the target's inner themes:")
    print(f"  {'target':<9}{'domain':<9}{'as a pick?':<12}{'best inner J':>14}"
          f"{'its size':>10}{'covers target':>15}")
    domains: dict[str, object] = {}
    matched: dict[int, list[int]] = {}
    for i in range(min(4, len(large))):
        for j in (4, 5, 6):
            if j >= len(large):
                continue
            as_pick = "no"
            for r in range(PICKS):
                p = int(got["picks"][i, r])
                if p >= 0 and _jaccard(rows[p], large[j]) >= BLOCK_J:
                    as_pick = f"yes, pick {r + 1}"
            where, _overlap = inner[i]
            best, best_j = -1, 0.0
            for s in where.tolist():
                value = _jaccard(rows[s], large[j])
                if value > best_j:
                    best, best_j = s, value
            share = (len(np.intersect1d(rows[best], large[i], assume_unique=True))
                     / len(large[i])) if best >= 0 else 0.0
            close = best >= 0 and best_j >= BLOCK_J
            if close:
                matched.setdefault(i, []).append(best)
            print(f"  {'set_' + str(i + 1):<9}{'set_' + str(j + 1):<9}{as_pick:<12}"
                  f"{best_j:>14.3f}"
                  f"{(f'{len(rows[best]):,}' if close else '--'):>10}"
                  f"{(f'{share:.1%}' if close else '--'):>15}")
            domains[f"set_{i + 1} vs set_{j + 1}"] = {
                "as_pick": as_pick, "best_inner_j": best_j,
                "best_inner_size": int(len(rows[best])) if close else None,
                "covers_target": share if close else None}
    print()
    print("  size and covers are left blank where the best inner match is below J = 0.5, because a")
    print("  weak best match says the domain is not inside the target at all.")
    print()
    print("  taken together, how much of each giant do the domains it does contain cover?")
    print(f"  {'target':<9}{'domains matched at J >= 0.5':<32}{'union covers target':>20}")
    for i in range(min(4, len(large))):
        got_them = matched.get(i, [])
        if not got_them:
            print(f"  {'set_' + str(i + 1):<9}{'none':<32}{'--':>20}")
            domains[f"set_{i + 1} union"] = None
            continue
        union = np.unique(np.concatenate([rows[s] for s in got_them]))
        share = len(np.intersect1d(union, large[i], assume_unique=True)) / len(large[i])
        names = ", ".join(f"set_{j + 1}" for j in (4, 5, 6)
                          if any(_jaccard(rows[s], large[j]) >= BLOCK_J for s in got_them))
        print(f"  {'set_' + str(i + 1):<9}{names:<32}{share:>20.1%}")
        domains[f"set_{i + 1} union"] = {"domains": names, "covers_target": share}
    print()
    out["domains_in_giants"] = domains
    return out


def examples(accepted: dict[str, object], targets: list[np.ndarray], got: dict[str, object],
             args: argparse.Namespace, suffix: str = "") -> list[Path]:
    """Forty accepted themes written out, with the first two picks marked.

    Args:
        accepted: As :func:`accepted_side` returns.
        targets: Member arrays of the targets.
        got: As :func:`greedy_cover` returns.
        args: Parsed arguments.
        suffix: Appended to each file name, to keep the two passes apart.

    Returns:
        The files written.
    """
    from thema.data.pathways import PathwayCollection
    from thema.ontology.universe import load_embedded

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    table = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    named = {p.key: (p.name, p.source) for p in table.pathways}
    rows = accepted["rows"]
    sizes = np.array([len(t) for t in targets], dtype=np.int64)
    out = args.out / "unions" / "examples"
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob(f"*{suffix}.md"):
        stale.unlink()
    rng = random.Random(SEED)
    written = []
    for label, flag in (("two_block", True), ("not_two_block", False)):
        pool = np.flatnonzero((sizes >= EXAMPLE_MIN) & (got["two_block"] == flag))
        pick = sorted(rng.sample(pool.tolist(), min(EXAMPLES, len(pool))))
        lines = []
        for position, t in enumerate(pick, 1):
            first = set(rows[got["picks"][t, 0]].tolist()) if got["picks"][t, 0] >= 0 else set()
            second = set(rows[got["picks"][t, 1]].tolist()) if got["picks"][t, 1] >= 0 else set()
            lines.append(f"## {label}-{position:02d}  ({len(targets[t])} members; "
                         f"pick 1 {len(first)} pathways, pick 2 {len(second)}; coverage "
                         f"{got['covered'][t, 0]:.0%} then {got['covered'][t, 1]:.0%}; "
                         f"J(pick 1, pick 2) {got['jaccard'][t]:.2f})")
            lines.append("")
            body = []
            for p in targets[t].tolist():
                name, source = named.get(keys[p], (keys[p], "?"))
                mark = ("[1+2] " if p in first and p in second else
                        "[1]   " if p in first else
                        "[2]   " if p in second else
                        "[ ]   ")
                body.append(f"- {mark}{name} [{source}]")
            rank = {"[1+2] ": 0, "[1]   ": 1, "[2]   ": 2, "[ ]   ": 3}
            lines += sorted(body, key=lambda s: (rank[s[2:8]], s))
            lines.append("")
        path = out / f"{label}{suffix}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
        print(f"  examples {label}: {len(pick)} of {len(pool):,} available -> {path}")
    return written


def main(argv: list[str] | None = None) -> int:
    """Measures a-d, tables 1 and 2, and the examples.

    Args:
        argv: Command line.

    Returns:
        0, or 1 if the brute-force check disagrees.
    """
    from l1_merge_rule import distinct, members_of
    from l1_report import load_l1

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/L1_2026-10-24"))
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args(argv)

    n = int(json.loads((args.space_root / "universe.json").read_text())["n_embedded"])
    print("PROMPT 62: ARE L1'S LARGE THEMES UNIONS OF SMALLER THEMES?")
    print("  evaluation only; no rule is applied and nothing is removed")
    accepted = accepted_side(args.out / "real_bothways")
    print(f"  {len(accepted['rows']):,} accepted themes (90% each way, found in >= {FOUND_BAR} "
          f"runs -- a PROVISIONAL working bar), {int(accepted['sizes'].sum()):,} member slots")
    order = np.flatnonzero(accepted["sizes"] >= TARGET_MIN)
    targets = [accepted["rows"][int(i)] for i in order]
    print(f"  {len(targets):,} of them have {TARGET_MIN}+ pathways and are measured")
    print()
    inner = inner_themes(accepted, targets, n)
    print("  pass 1, DECLARED: every inner theme is a candidate")
    got = greedy_cover(accepted, targets, inner, n)
    print("  pass 2, ADDED: inner themes that are near-copies of the target (J >= 0.5) dropped")
    far = greedy_cover(accepted, targets, inner, n, exclude_near=True)
    print()

    checks: dict[str, object] = {}
    if not args.no_verify:
        clock = time.perf_counter()
        checks["declared"] = brute_check(accepted, targets, inner, got)
        checks["near_copies_dropped"] = brute_check(accepted, targets, inner, far,
                                                    exclude_near=True)
        print(f"  VERIFICATION against explicit set loops, seed {SEED} "
              f"({time.perf_counter() - clock:.0f}s)")
        for name, check in checks.items():
            print(f"    {name:<20}{'IDENTICAL' if check['identical'] else 'MISMATCH'}  {check}")
        print()

    record: dict[str, object] = {"accepted": len(accepted["rows"]), "targets": len(targets),
                                 "found_bar": FOUND_BAR, "verification": checks}
    record["table1"] = table_one(targets, got, "DECLARED")
    record["table1_near_copies_dropped"] = table_one(targets, far, "NEAR-COPIES OF THE TARGET "
                                                     "DROPPED (an addition, not the prompt)")

    jaccard_side = load_l1(args.out / "real")
    which = np.flatnonzero((jaccard_side["t_size"] >= 800) & (jaccard_side["t_found"] >= FOUND_BAR))
    big = members_of(jaccard_side, which)
    kept = distinct(big, n)
    large = [big[i] for i in sorted(kept["kept"], key=lambda j: -len(big[j]))]
    stated = [int(line.split("--")[1].split()[0].replace(",", ""))
              for line in sorted((args.out / "large7").glob("set_*.md"),
                                 key=lambda p: int(p.stem.split("_")[1]))
              for line in [line.read_text(encoding="utf-8").split("\n")[0]]]
    same = [len(s) for s in large] == stated
    print(f"  the seven sets rebuilt from the Jaccard side match large7/ exactly: {same} "
          f"({[len(s) for s in large]})")
    record["large7_sizes_match"] = same
    record["table2"] = table_two(accepted, large, n, args)
    record["table2_near_copies_dropped"] = table_two(accepted, large, n, args,
                                                     exclude_near=True)

    examples(accepted, targets, got, args)
    examples(accepted, targets, far, args, suffix="_near_copies_dropped")
    (args.out / "unions").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out / "unions" / "measures.npz",
                        target=order, size=accepted["sizes"][order], picks=got["picks"],
                        covered=got["covered"], single=got["single"], jaccard=got["jaccard"],
                        two_block=got["two_block"], three_block=got["three_block"],
                        inner_counts=np.array([len(i) for i, _o in inner], dtype=np.int64))
    (args.out / "unions" / "unions.json").write_text(
        json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'unions'}")
    return 0 if all(v["identical"] for v in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
