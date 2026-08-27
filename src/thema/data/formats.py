"""Readers for the file formats the pathway sources ship: GMT, OBO, and MSigDB's JSON and XML.

These know one file's grammar each and nothing about THEMA -- the same seam ``genes.py`` draws
between ``parse_complete_set`` and ``GeneResolver``. What a GO id *means* belongs in
``pathways.py``; how to get one out of an ``.obo`` stanza belongs here.

One deliberate deviation from the parsers in ``genes.py``, which take ``text: str``:
``go-basic.obo`` is 32 MB and ``msigdb_v2026.1.Hs.xml`` is 221 MB, so the readers here take
``lines: Iterable[str]`` and stream. Tests still pass a module-level literal through
``.splitlines()``, so nothing gains a dependency on ``data/raw/``.
"""

import html
import json
import re
from collections.abc import Container, Iterable
from dataclasses import dataclass

#: One ``KEY="value"`` pair on an XML element line.
_ATTRIBUTE = re.compile(r'(\w+)="([^"]*)"')

_STANDARD_NAME = re.compile(r'\bSTANDARD_NAME="([^"]*)"')
_DESCRIPTION_BRIEF = re.compile(r'\bDESCRIPTION_BRIEF="([^"]*)"')

#: An OBO ``def`` value: the definition in quotes, then a bracketed reference list.
_DEFINITION = re.compile(r'^"(.*)"\s*(?:\[[^\]]*\])?\s*$', re.DOTALL)


@dataclass(frozen=True, slots=True)
class GeneSet:
    """One line of a GMT file.

    Attributes:
        name: Column one, the set's name.
        secondary: Column two, whose meaning is per-source -- a stable id in Reactome's GMT, a
            web URL in GO's, Hallmark's and BTM's.
        entries: Columns three onward in file order, blanks dropped. Called entries rather than
            genes because BTM ships multi-mapping probe annotations here, not bare symbols.
    """

    name: str
    secondary: str
    entries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OboTerm:
    """One ``[Term]`` stanza of an OBO file.

    Attributes:
        term_id: The stanza's ``id``, for example ``GO:0000012``.
        name: The ``name`` line. Obsolete terms carry an ``obsolete `` prefix here, from the source.
        definition: The quoted part of ``def``, with the trailing reference list dropped.
        namespace: The ``namespace`` line.
        is_obsolete: Whether the stanza carries ``is_obsolete: true``.
        parents: The ``is_a`` targets, without their trailing ``! name`` comment. This is the DAG.
        alt_ids: Identifiers this term has absorbed, which resolve to it.
    """

    term_id: str
    name: str
    definition: str
    namespace: str
    is_obsolete: bool
    parents: tuple[str, ...]
    alt_ids: tuple[str, ...]


def read_gmt_sets(lines: Iterable[str]) -> tuple[GeneSet, ...]:
    """Read a GMT as one record per set.

    Two other GMT readers exist in ``scripts/`` and neither has this shape: the cascade's returns
    one row per member, and the resolver script's returns the inverted symbol-to-sets map. A
    per-set loader needs the set itself.

    Args:
        lines: The file's lines.

    Returns:
        One :class:`GeneSet` per line carrying at least one member, in file order.
    """
    sets: list[GeneSet] = []
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 3:
            continue
        entries = tuple(entry.strip() for entry in fields[2:] if entry.strip())
        if entries:
            sets.append(GeneSet(fields[0].strip(), fields[1].strip(), entries))
    return tuple(sets)


def _definition(value: str) -> str:
    """Extract the quoted definition from an OBO ``def`` value, dropping its reference list."""
    match = _DEFINITION.match(value)
    text = match.group(1) if match else value
    return text.replace('\\"', '"').replace("\\\\", "\\")


def parse_obo_terms(lines: Iterable[str], namespace: str = "") -> dict[str, OboTerm]:
    """Read the ``[Term]`` stanzas of an OBO file.

    A stanza is flushed on *any* line opening a new one, not only on ``[Term]``: ``go-basic.obo``
    carries ``[Typedef]`` stanzas between terms, and matching ``[Term]`` alone would let a typedef's
    keys leak into the term before it. Lines ahead of the first stanza are the file header and are
    ignored.

    Obsolete terms are kept and flagged rather than dropped -- what to do about them is a decision
    for the caller, and GO marks obsolescence inside the ``name`` and ``def`` text as well.

    Args:
        lines: The file's lines.
        namespace: Keep only terms in this namespace; empty keeps every namespace.

    Returns:
        Terms keyed by ``term_id`` and, where they do not collide with a primary id, by each of
        their ``alt_ids``, so a stale identifier still resolves.
    """
    terms: dict[str, OboTerm] = {}
    fields: dict[str, str] | None = None
    parents: list[str] = []
    alt_ids: list[str] = []

    def flush() -> None:
        if fields is None or "id" not in fields:
            return
        if namespace and fields.get("namespace", "") != namespace:
            return
        terms[fields["id"]] = OboTerm(
            term_id=fields["id"],
            name=fields.get("name", ""),
            definition=_definition(fields["def"]) if "def" in fields else "",
            namespace=fields.get("namespace", ""),
            is_obsolete=fields.get("is_obsolete", "") == "true",
            parents=tuple(parents),
            alt_ids=tuple(alt_ids),
        )

    for raw in lines:
        line = raw.rstrip("\n")
        if line.startswith("["):
            flush()
            fields, parents, alt_ids = ({} if line.strip() == "[Term]" else None), [], []
            continue
        if fields is None or ": " not in line:
            continue
        key, _, value = line.partition(": ")
        value = value.strip()
        if key == "is_a":
            parents.append(value.split("!")[0].strip())
        elif key == "alt_id":
            alt_ids.append(value)
        elif key in ("id", "name", "namespace", "def", "is_obsolete"):
            fields[key] = value
    flush()

    for term in list(terms.values()):
        for alt in term.alt_ids:
            terms.setdefault(alt, term)
    return terms


def parse_geneset_attributes(line: str) -> dict[str, str]:
    """Read every ``KEY="value"`` attribute off one MSigDB ``GENESET`` line.

    Args:
        line: The line, which need not be well-formed XML. See
            :func:`read_msigdb_descriptions` for why that matters.

    Returns:
        Each attribute, with HTML entities unescaped.
    """
    return {key: html.unescape(value) for key, value in _ATTRIBUTE.findall(line)}


def read_msigdb_descriptions(lines: Iterable[str], names: Container[str]) -> dict[str, str]:
    """Read ``DESCRIPTION_BRIEF`` for the named gene sets out of MSigDB's XML export.

    **The file is not well-formed XML and cannot be parsed as XML.** Attribute values carry raw
    unescaped ``<`` -- ``EXACT_SOURCE="Table 3S: fold change (log2) < 0"`` is one of several -- and
    ``xml.etree.ElementTree`` raises ``ParseError`` on it, ``iterparse`` included, so streaming does
    not help. It is however strictly one self-closing ``<GENESET .../>`` element per line, 35,361 of
    them in the 2026.1.Hs release, which makes a line-oriented attribute scan both correct and fast.

    Only the requested sets have their description read. A blanket attribute scan of every line
    would materialise all 35,361 ``MEMBERS`` lists -- hundreds of megabytes of strings -- to reach
    the fifty descriptions Hallmark needs.

    Args:
        lines: The file's lines.
        names: The ``STANDARD_NAME`` values wanted.

    Returns:
        Each requested set that was found, mapped to its brief description. A set present with no
        description maps to the empty string; a set absent from the file is absent here, so the
        caller can tell the two apart.
    """
    found: dict[str, str] = {}
    for line in lines:
        name = _STANDARD_NAME.search(line)
        if name is None or name.group(1) not in names:
            continue
        description = _DESCRIPTION_BRIEF.search(line)
        found[name.group(1)] = html.unescape(description.group(1)) if description else ""
    return found


def read_msigdb_exact_sources(text: str) -> dict[str, str]:
    """Map each set name in a per-collection MSigDB JSON to its ``exactSource``.

    This is how a C5 gene set reaches its GO term: the ``.symbols.gmt`` carries only a web URL in
    column two, and its set names are slugs rather than identifiers, so the GMT alone cannot join
    to ``go-basic.obo``. The per-collection JSON can, and at 8 MB it spares the 221 MB XML.

    Args:
        text: The JSON file's contents.

    Returns:
        Each set name mapped to its source identifier, omitting sets that carry none.
    """
    entries: dict[str, dict[str, object]] = json.loads(text)
    sources = ((name, str(entry.get("exactSource", ""))) for name, entry in entries.items())
    return {name: source for name, source in sources if source}
