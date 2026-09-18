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

from thema.data.tables import write_tsv

#: The generation consumers read.
STATUS_CURRENT = "current"

#: A generation kept for the record. Never deleted, never read by default.
STATUS_SUPERSEDED = "superseded"

#: What identifies one row. Two prompts, or two models, describing the same pathway are two
#: different facts and must not overwrite one another.
ROW_KEY = ("key", "prompt_version", "model")


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
) -> tuple[int, int]:
    """Mark one generation current and every other superseded.

    Run after rows are merged in, because merging replaces only the rows it carries and leaves
    every other generation's ``status`` saying whatever it said before -- which, the moment a new
    generation lands, is a second table claiming to be current.

    Args:
        path: Path to ``pathway_descriptions.tsv``.
        columns: The table's columns, in order.
        current: The ``prompt_version`` consumers should read.
        allow_shrink: Permit a smaller generation to supersede a larger one. Off by default: an
            interrupted run leaves a partial generation behind, and promoting it would silently
            shrink what every consumer sees -- 200 current rows superseding 1,854 complete ones
            looks exactly like a successful run to anything reading the table afterwards.

    Returns:
        How many rows were marked current and how many superseded.

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
            f"{outgoing:,}. An interrupted run looks exactly like this. Finish the generation, or "
            "pass allow_shrink=True if the smaller set is genuinely what consumers should read."
        )
    marked = 0
    for row in rows:
        is_current = row.get("prompt_version") == current
        row["status"] = STATUS_CURRENT if is_current else STATUS_SUPERSEDED
        marked += is_current
    write_tsv(path, columns, [tuple(row.get(c, "") for c in columns) for row in rows])
    return marked, len(rows) - marked


def _rows(path: Path) -> Iterable[dict[str, str]]:
    """Read the table, tolerating its absence."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))
