"""The TSV conventions every THEMA build table follows.

Three scripts already write tables of this shape, and each carries its own copy of the writer and
the digest helper -- copies that have begun to drift. This module is the one place those live for
new work, together with the cell conventions that were previously tribal knowledge spread across
``scripts/``: a lone ``-`` means empty, ``;`` separates list items, ``,`` separates several symbols
bound to one identifier, and ``=`` binds them.

The existing copies in ``scripts/`` are deliberately left in place; the cascade and the downloader
are not modified. ``tests/test_tables.py`` pins this writer against one of them byte for byte, so
"we chose not to touch that script" is a machine-checked statement rather than a comment.
"""

import hashlib
from collections.abc import Iterable, Sequence
from pathlib import Path

#: A cell holding nothing. Chosen over the empty string so a missing value is visible in a terminal.
EMPTY = "-"

#: Separates the items of a list-valued cell.
LIST_SEPARATOR = ";"

#: Separates several source symbols that resolved to one identifier.
SYMBOL_SEPARATOR = ","

#: Binds an identifier to the symbols that reached it.
BINDING_SEPARATOR = "="

#: Header of every committed summary table.
SUMMARY_COLUMNS = ("section", "key", "value", "note")


def flatten(text: str) -> str:
    """Collapse the whitespace a TSV cell cannot hold.

    Applied when prose is *loaded*, not when it is written, so what is in memory and what is on
    disk are the same string and the round-trip is exact.

    Args:
        text: Prose as the source published it.

    Returns:
        The same prose with every run of whitespace reduced to one space, and the ends stripped.
    """
    return " ".join(text.split())


def cell(value: str | None) -> str:
    """Render an optional value, writing :data:`EMPTY` for nothing.

    Args:
        value: The value, or None.

    Returns:
        The value, or :data:`EMPTY` if it is None or blank.
    """
    return value if value else EMPTY


def optional(value: str) -> str | None:
    """Read a cell back, turning :data:`EMPTY` into None.

    Args:
        value: The cell as read from the file.

    Returns:
        The value, or None if the cell held :data:`EMPTY` or nothing.
    """
    return None if value in ("", EMPTY) else value


def join_items(items: Iterable[str]) -> str:
    """Render a list-valued cell.

    Args:
        items: The items, in the order they should appear.

    Returns:
        The items joined by :data:`LIST_SEPARATOR`, or :data:`EMPTY` if there are none.
    """
    joined = LIST_SEPARATOR.join(items)
    return joined if joined else EMPTY


def split_items(value: str) -> tuple[str, ...]:
    """Read a list-valued cell back.

    Args:
        value: The cell as read from the file.

    Returns:
        The items, empty if the cell held :data:`EMPTY`.
    """
    return () if value in ("", EMPTY) else tuple(value.split(LIST_SEPARATOR))


def join_bindings(bindings: Iterable[tuple[str, Sequence[str]]]) -> str:
    """Render identifiers bound to the symbols that reached them.

    Args:
        bindings: ``(identifier, symbols)`` pairs, in the order they should appear.

    Returns:
        ``id=sym,sym;id=sym`` form, or :data:`EMPTY` if there are none.
    """
    return join_items(
        f"{key}{BINDING_SEPARATOR}{SYMBOL_SEPARATOR.join(values)}" for key, values in bindings
    )


def split_bindings(value: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Read bound identifiers back.

    Args:
        value: The cell as read from the file.

    Returns:
        ``(identifier, symbols)`` pairs in file order, empty if the cell held :data:`EMPTY`.
    """
    pairs: list[tuple[str, tuple[str, ...]]] = []
    for item in split_items(value):
        key, _, symbols = item.partition(BINDING_SEPARATOR)
        pairs.append((key, tuple(s for s in symbols.split(SYMBOL_SEPARATOR) if s)))
    return tuple(pairs)


def write_tsv(path: Path, columns: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Write a TSV atomically, header first.

    Args:
        path: Destination.
        columns: Header row.
        rows: Rows in final order.
    """
    text = "\n".join(["\t".join(columns), *("\t".join(r) for r in rows)]) + "\n"
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    """Return the hex sha256 digest of a file, read in chunks.

    Args:
        path: The file to digest.

    Returns:
        The digest as 64 lowercase hex characters.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 16):
            digest.update(chunk)
    return digest.hexdigest()
