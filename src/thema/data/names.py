"""The theme-names table: one row per (theme key, prompt version, model).

Mirrors ``descriptions.py`` deliberately. A name is a paid artefact produced by one prompt and
one model, and the same rules apply: every generation is kept, merging never replaces, and a
``status`` column names the one consumers read.

The key is the THEME KEY -- a digest of the theme's members, and of its children's names for an
internal node -- not a node id. Node ids are assigned per build, so keying on them would throw
every name away at the next rebuild. See ``thema.naming.theme_key``.
"""

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path

from thema.data.tables import write_tsv

#: The generation consumers read.
STATUS_CURRENT = "current"

#: Kept for the record, never read by default.
STATUS_SUPERSEDED = "superseded"

#: One row per theme key, prompt version and model. Two prompts or two models naming the same
#: theme are two different facts and must not overwrite one another.
ROW_KEY = ("theme_key", "prompt_version", "model")

NAME_COLUMNS = (
    "theme_key",
    "name",
    "nameable",
    "rationale",
    "n_members",
    "kind",
    "example_node",
    "checks_failed",
    "model",
    "prompt_version",
    "status",
)


def read(path: Path, *, version: str | None = None) -> dict[str, str]:
    """Read one generation of names.

    Args:
        path: Path to ``theme_names.tsv``.
        version: A ``prompt_version``, or None for whichever is current.

    Returns:
        Theme key to its name. Themes returned as unnameable are ABSENT rather than present with
        an empty name, so a caller cannot mistake a refusal for a name it failed to read.
    """
    rows = _rows(path)
    if version is None:
        wanted = [r for r in rows if r.get("status") == STATUS_CURRENT]
    else:
        wanted = [r for r in rows if r.get("prompt_version") == version]
    return {
        r["theme_key"]: r["name"]
        for r in wanted
        if r.get("nameable") == "true" and r.get("name")
    }


def unnameable(path: Path, *, version: str | None = None) -> dict[str, str]:
    """The themes a generation declined to name, and why.

    Args:
        path: Path to ``theme_names.tsv``.
        version: A ``prompt_version``, or None for whichever is current.

    Returns:
        Theme key to the rationale for refusing. Reported separately from :func:`read` because a
        refusal is a finding about the theme, not a missing value.
    """
    rows = _rows(path)
    wanted = (
        [r for r in rows if r.get("status") == STATUS_CURRENT]
        if version is None
        else [r for r in rows if r.get("prompt_version") == version]
    )
    return {r["theme_key"]: r.get("rationale", "") for r in wanted if r.get("nameable") == "false"}


def versions(path: Path) -> dict[str, int]:
    """How many rows each ``prompt_version`` holds."""
    counts: dict[str, int] = {}
    for row in _rows(path):
        name = row.get("prompt_version", "?")
        counts[name] = counts.get(name, 0) + 1
    return counts


def restamp(path: Path, columns: Sequence[str], current: str) -> tuple[int, int]:
    """Mark one generation current and every other superseded.

    Args:
        path: Path to ``theme_names.tsv``.
        columns: The table's columns, in order.
        current: The ``prompt_version`` consumers should read.

    Returns:
        Rows marked current, and rows superseded.

    Raises:
        ValueError: If nothing carries ``current``.
    """
    rows = list(_rows(path))
    if not any(r.get("prompt_version") == current for r in rows):
        have = sorted({r.get("prompt_version", "?") for r in rows})
        raise ValueError(f"{path} holds no {current!r} names; it has {', '.join(have)}")
    marked = 0
    for row in rows:
        is_current = row.get("prompt_version") == current
        row["status"] = STATUS_CURRENT if is_current else STATUS_SUPERSEDED
        marked += is_current
    write_tsv(path, columns, [tuple(r.get(c, "") for c in columns) for r in rows])
    return marked, len(rows) - marked


def _rows(path: Path) -> Iterable[dict[str, str]]:
    """Read the table, tolerating its absence."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))
