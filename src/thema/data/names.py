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
    # name-v6: the node this one was merged with, when a parent took its child's name and the child
    # declined to narrow itself. Empty for every other row. It is recorded rather than resolved:
    # nothing invents a difference, and the two are shown merged.
    "same_theme",
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


def restamp(
    path: Path, columns: Sequence[str], current: str, keep: dict[str, str] | None = None
) -> tuple[int, int]:
    """Mark one generation current and every other superseded -- ONE row per node.

    Marking by ``prompt_version`` alone left a node with SEVERAL current rows. A row is keyed by
    ``theme_key``, which changes when a node's children are renamed, so a re-run writes a new row
    and the old one survives under the same version. 35 of 502 nodes ended with two current rows,
    and a reader keyed by node silently got whichever came last in the file -- which is how three
    enforced names appeared not to have been saved at all.

    Args:
        path: Path to ``theme_names.tsv``.
        columns: The table's columns, in order.
        current: The ``prompt_version`` consumers should read.
        keep: Node id to the ``theme_key`` this run wrote for it. A row for that node carrying any
            other key is superseded even though its version matches. Omit and every matching row is
            marked current, which is the old behaviour.

    Returns:
        Rows marked current, and rows superseded.

    Raises:
        ValueError: If nothing carries ``current``, or if a node still ends with more than one
            current row -- the condition this function exists to prevent.
    """
    rows = list(_rows(path))
    if not any(r.get("prompt_version") == current for r in rows):
        have = sorted({r.get("prompt_version", "?") for r in rows})
        raise ValueError(f"{path} holds no {current!r} names; it has {', '.join(have)}")
    chosen = keep or {}
    marked = 0
    for row in rows:
        node = row.get("example_node", "")
        is_current = row.get("prompt_version") == current and (
            node not in chosen or row.get("theme_key") == chosen[node]
        )
        row["status"] = STATUS_CURRENT if is_current else STATUS_SUPERSEDED
        marked += is_current
    seen: dict[str, int] = {}
    for row in rows:
        if row["status"] == STATUS_CURRENT:
            seen[row.get("example_node", "")] = seen.get(row.get("example_node", ""), 0) + 1
    many = sorted(n for n, c in seen.items() if c > 1)
    if many:
        raise ValueError(
            f"{path}: {len(many)} node(s) would have more than one current row "
            f"({', '.join(many[:5])}{'...' if len(many) > 5 else ''}). Pass keep= with the "
            "theme_key this run wrote per node."
        )
    write_tsv(path, columns, [tuple(r.get(c, "") for c in columns) for r in rows])
    return marked, len(rows) - marked


def _rows(path: Path) -> Iterable[dict[str, str]]:
    """Read the table, tolerating its absence."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))
