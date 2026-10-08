"""Curated evaluation sets, with clarification 9's relations option and clarification 10's pairs.

Two things live here that did not exist before.

**The GO closure over more than `is_a`.** `thema.data.formats.parse_obo_terms` reads only `is_a`, so
every GO figure reported before 7 Oct used the `is_a`-only closure. Clarification 9 makes the
closure over `is_a`, `part_of`, `regulates`, `positively_regulates` and `negatively_regulates`
primary, because 36% of GO pathways are regulation terms and `is_a` alone files them away from the
process they regulate: *negative regulation of anoikis* is not an `is_a` descendant of *anoikis*.
The relations are present in `go-basic.obo` -- 6,270 `part_of`, 2,820 `regulates`, 2,475 each of
the signed ones -- and were simply never parsed.

**Pair distance**, clarification 10: for a same-source pair, how small a curated set contains both,
and how small a theme does. Near-pair recall and precision at a size cutoff then ask whether an
ontology puts things that belong together close together, which is a different question from whether
whole sets are recovered -- a theme can miss every curated set and still get the pairs right.

This is a NEW module: `recurrent.py`, the naming code and `scripts/kc2_report.py` are untouched, so
old reports stay reproducible on the old default.
"""

from __future__ import annotations

import numpy as np

#: Clarification 9's primary relation set, and the secondary one every earlier report used.
PRIMARY_RELATIONS: tuple[str, ...] = (
    "is_a", "part_of", "regulates", "positively_regulates", "negatively_regulates",
)
SECONDARY_RELATIONS: tuple[str, ...] = ("is_a",)

#: Clarification 10's near-pair cutoffs.
NEAR_THRESHOLDS: tuple[int, ...] = (10, 50)


def go_edges(
    lines: list[str], relations: tuple[str, ...] = PRIMARY_RELATIONS
) -> dict[str, set[str]]:
    """Child-to-parent edges from an OBO file, over the chosen relations.

    Args:
        lines: The ``go-basic.obo`` lines.
        relations: Which relations to follow. ``is_a`` is read from its own stanza key; the others
            from ``relationship:`` lines.

    Returns:
        Term id to the set of ids it points at.
    """
    wanted = set(relations)
    out: dict[str, set[str]] = {}
    current: str | None = None
    obsolete = False
    for raw in lines:
        line = raw.strip()
        if line == "[Term]":
            current, obsolete = None, False
            continue
        if line.startswith("id: "):
            current = line[4:].strip()
            continue
        if line.startswith("is_obsolete: true"):
            obsolete = True
            if current is not None:
                out.pop(current, None)
            continue
        if current is None or obsolete:
            continue
        if line.startswith("is_a: ") and "is_a" in wanted:
            out.setdefault(current, set()).add(line[6:].split("!")[0].strip())
        elif line.startswith("relationship: "):
            parts = line[14:].split()
            if len(parts) >= 2 and parts[0] in wanted:
                out.setdefault(current, set()).add(parts[1].strip())
    return out


def descendant_sets(
    edges: dict[str, set[str]], present: dict[str, int], prefix: str, min_size: int = 3
) -> list[set[int]]:
    """Each term's descendant closure, as universe indices.

    A term's set is itself plus everything that reaches it by following child-to-parent edges
    upward. So the set of *anoikis* contains *regulation of anoikis* once ``regulates`` is in the
    relation set, and does not when only ``is_a`` is.

    Args:
        edges: Child to parents.
        present: Universe key to row index.
        prefix: ``go:`` or ``reactome:``.
        min_size: Smallest set kept.

    Returns:
        One index set per term with at least ``min_size`` members in the universe.
    """
    children: dict[str, list[str]] = {}
    for child, parents in edges.items():
        for parent in parents:
            children.setdefault(parent, []).append(child)
    out: list[set[int]] = []
    for node in set(edges) | set(children):
        stack, seen = [node], set()
        while stack:
            at = stack.pop()
            if at in seen:
                continue
            seen.add(at)
            stack.extend(children.get(at, ()))
        members = {present[f"{prefix}{t}"] for t in seen if f"{prefix}{t}" in present}
        if len(members) >= min_size:
            out.append(members)
    return out


def split_half(
    sets: list[set[int]], bands: list[str], seed: int = 0
) -> tuple[list[int], list[int]]:
    """Split curated sets in half, stratified by band.

    Stratified rather than plain, so a band with 26 sets does not land 20/6 by luck and make a
    tuning decision on six of them.

    Args:
        sets: The curated sets.
        bands: Band label per set, same length.
        seed: RNG seed.

    Returns:
        ``(tuning, test)`` index lists.
    """
    rng = np.random.default_rng(seed)
    tuning: list[int] = []
    test: list[int] = []
    for band in sorted(set(bands)):
        members = [i for i, b in enumerate(bands) if b == band]
        order = rng.permutation(len(members))
        cut = len(members) // 2
        tuning.extend(members[i] for i in order[:cut].tolist())
        test.extend(members[i] for i in order[cut:].tolist())
    return sorted(tuning), sorted(test)


def smallest_containing(pairs: np.ndarray, sets: list[set[int]], n: int) -> np.ndarray:
    """For each pair, the size of the smallest set containing both members, else inf.

    Args:
        pairs: ``(p, 2)`` universe indices.
        sets: Candidate sets.
        n: Universe size.

    Returns:
        One size per pair.
    """
    holders: list[list[int]] = [[] for _ in range(n)]
    for index, members in enumerate(sets):
        for member in members:
            holders[member].append(index)
    sizes = np.array([len(s) for s in sets], dtype=np.int64)
    out = np.full(len(pairs), np.inf)
    for position, (a, b) in enumerate(pairs.tolist()):
        best = np.inf
        for candidate in holders[a]:
            if b in sets[candidate] and sizes[candidate] < best:
                best = float(sizes[candidate])
        out[position] = best
    return out


def near_pair_scores(
    curated_d: np.ndarray, theme_d: np.ndarray, threshold: int
) -> dict[str, float | int]:
    """Clarification 10's near-pair recall and precision at one cutoff.

    Recall: of the pairs the curation puts within a set of at most ``threshold``, the share the
    ontology also puts within a theme of at most ``threshold``. Precision is the converse.

    Args:
        curated_d: Smallest curated set containing each pair.
        theme_d: Smallest theme containing each pair.
        threshold: The size cutoff.

    Returns:
        Recall, precision and both denominators.
    """
    near_curated = curated_d <= threshold
    near_theme = theme_d <= threshold
    both = int((near_curated & near_theme).sum())
    return {
        "recall": round(both / int(near_curated.sum()), 4) if near_curated.any() else None,
        "precision": round(both / int(near_theme.sum()), 4) if near_theme.any() else None,
        "n_curated_near": int(near_curated.sum()),
        "n_theme_near": int(near_theme.sum()),
        "n_both": both,
    }
