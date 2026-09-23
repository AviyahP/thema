"""The descriptions table: every generation kept, exactly one marked current.

``pathway_descriptions.tsv`` used to hold one row per pathway and was rewritten wholesale on every
run. That made a prompt change destructive -- generating under v4 replaced 1,854 v3 descriptions
that had been paid for, and an interrupted run replaced them with a partial set. It also threw away
the only record of what earlier prompts produced, which is the comparison every later argument
needs.

The table now holds one row per ``(key, prompt_version, model)``. Nothing is ever deleted. A
``status`` column names the one generation consumers may read, and :func:`read` returns only that
generation unless a caller asks for a specific one by name -- which the experiment runner does, to
hold the v3 control steady while v4 becomes current.

Reading the table any other way is how a consumer silently picks up whichever row happened to be
written last. There is one reader, and it is this one.
"""

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import NamedTuple

from thema.data.tables import write_tsv

#: The generation consumers read.
STATUS_CURRENT = "current"

#: A generation kept for the record. Never deleted, never read by default.
STATUS_SUPERSEDED = "superseded"

#: The pathway itself is no longer in the universe, so no generation of its description may be
#: read, promoted or regenerated -- but the rows are kept, because they are the record of what was
#: written and paid for. Distinct from ``superseded``: that means a NEWER generation exists, this
#: means there is nothing left to describe. Set for the zero-gene pathways excluded by the
#: universe rule (DECISIONS.md, 23 Sep 2026).
STATUS_OUT_OF_UNIVERSE = "out_of_universe"

#: What identifies one row. Two prompts, or two models, describing the same pathway are two
#: different facts and must not overwrite one another.
ROW_KEY = ("key", "prompt_version", "model")


class Promotion(NamedTuple):
    """What a promotion did.

    Attributes:
        marked: Rows set current from the incoming generation.
        superseded: Rows set superseded because a newer row for the same key arrived.
        retained: Keys whose current row was LEFT ALONE because the incoming generation had no
            row for them. These are the pathways a partial generation would otherwise blank.
        retained_versions: Which generations those retained rows belong to, and how many each.
    """

    marked: int
    superseded: int
    retained: int
    retained_versions: dict[str, int]


def read(
    path: Path, *, version: str | None = None, model: str | None = None
) -> dict[str, str]:
    """Read one generation of descriptions.

    Args:
        path: Path to ``pathway_descriptions.tsv``.
        version: Which ``prompt_version`` to read. ``None`` reads whatever is marked
            :data:`STATUS_CURRENT`, which is what every consumer wants except the experiment
            runner's v3 control.
        model: Restrict to one model as well, when several described the same pathway.

    Returns:
        Pathway key to its generated description.

    Raises:
        ValueError: If ``version`` is given and the table holds no such generation. Returning an
            empty dict would let a caller carry on against nothing.
    """
    rows = list(_rows(path))
    if not rows:
        return {}
    # A table written before versioning has no status column; every row in it is the only one.
    versioned = "status" in rows[0]
    if version is None:
        wanted = [r for r in rows if not versioned or r["status"] == STATUS_CURRENT]
    else:
        wanted = [r for r in rows if r.get("prompt_version") == version]
        if not wanted:
            have = sorted({r.get("prompt_version", "?") for r in rows})
            raise ValueError(f"{path} holds no {version!r} descriptions; it has {', '.join(have)}")
    if model is not None:
        wanted = [r for r in wanted if r.get("model") == model]
    return {r["key"]: r["description_generated"] for r in wanted}


def versions(path: Path) -> dict[str, int]:
    """Count the rows each generation contributed.

    Args:
        path: Path to ``pathway_descriptions.tsv``.

    Returns:
        ``prompt_version`` to row count, so a reader can see what the table is keeping.
    """
    counts: dict[str, int] = {}
    for row in _rows(path):
        name = row.get("prompt_version", "?")
        counts[name] = counts.get(name, 0) + 1
    return counts


def restamp(
    path: Path, columns: Sequence[str], current: str, *, allow_shrink: bool = False
) -> Promotion:
    """Promote one generation, without ever leaving a universe key unreadable.

    Run after rows are merged in, because merging replaces only the rows it carries and leaves
    every other generation's ``status`` saying whatever it said before -- which, the moment a new
    generation lands, is a second table claiming to be current.

    **A key the incoming generation does not cover keeps the current row it already has.** The
    earlier rule -- everything not in ``current`` becomes superseded -- meant a generation that
    missed some pathways silently blanked them: they would have no current row at all and
    :func:`read` would stop returning them, with nothing in the table recording that anything had
    been lost. A generation can miss pathways for entirely ordinary reasons (a refusal, a
    truncation, an interrupted chunk), so the invariant is enforced here rather than left to
    whoever runs the next promotion to remember.

    Args:
        path: Path to ``pathway_descriptions.tsv``.
        columns: The table's columns, in order.
        current: The ``prompt_version`` consumers should read.
        allow_shrink: Permit a smaller generation to be promoted over a larger one. Off by
            default: an interrupted run leaves a partial generation behind, and promoting it makes
            the readable table a mixture of generations. Since retention landed this no longer
            LOSES anything -- omitted keys keep their rows -- but a mixture is rarely what a
            promotion intends, so it stays something you have to ask for.

    Rows already marked :data:`STATUS_OUT_OF_UNIVERSE` are left alone and counted as neither: a
    pathway that left the universe stays out of it.

    Returns:
        A :class:`Promotion` -- rows marked, rows superseded, keys retained from an older
        generation, and which generations those came from.

    Raises:
        ValueError: If no row carries ``current``, or if promoting it would shrink the readable
            table and ``allow_shrink`` is not set. Failing here beats failing in eight consumers.
    """
    rows = list(_rows(path))
    counts: dict[str, int] = {}
    for row in rows:
        name = row.get("prompt_version", "?")
        counts[name] = counts.get(name, 0) + 1
    if current not in counts:
        raise ValueError(
            f"nothing in {path} carries prompt_version {current!r}; it has "
            f"{', '.join(sorted(counts))}. Refusing to leave the table with no current generation."
        )
    outgoing = max((n for v, n in counts.items() if v != current), default=0)
    if outgoing > counts[current] and not allow_shrink:
        raise ValueError(
            f"{current!r} has {counts[current]:,} rows but would supersede a generation of "
            f"{outgoing:,}. An interrupted run looks exactly like this. Nothing would be BLANKED "
            "-- keys the smaller generation omits keep the rows they have -- but the readable "
            "table would become a mixture of generations, which is rarely what a promotion "
            "intends. Finish the generation, or pass allow_shrink=True if the mixture is."
        )
    covered = {row["key"] for row in rows if row.get("prompt_version") == current}
    marked = superseded = 0
    retained_versions: dict[str, int] = {}
    for row in rows:
        # A pathway that left the universe stays out of it. Without this, the next promotion
        # rewrites every status unconditionally and silently restores rows whose pathway no
        # longer exists to describe -- the marking would survive exactly until the next
        # generation landed.
        if row.get("status") == STATUS_OUT_OF_UNIVERSE:
            continue
        if row["key"] not in covered:
            # The incoming generation says nothing about this key, so it may not demote it.
            if row.get("status") == STATUS_CURRENT:
                version = row.get("prompt_version", "?")
                retained_versions[version] = retained_versions.get(version, 0) + 1
            continue
        is_current = row.get("prompt_version") == current
        row["status"] = STATUS_CURRENT if is_current else STATUS_SUPERSEDED
        marked += is_current
        superseded += not is_current
    write_tsv(path, columns, [tuple(row.get(c, "") for c in columns) for row in rows])
    return Promotion(marked, superseded, sum(retained_versions.values()), retained_versions)


def _rows(path: Path) -> Iterable[dict[str, str]]:
    """Read the table, tolerating its absence."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))
