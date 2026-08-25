"""Resolve source gene symbols to stable HGNC identifiers.

THEMA's four gene-set sources ship gene symbols, not identifiers, and they were symbol-mapped at
different dates by different providers. Symbols drift: they are renamed, retired and merged. A
cross-database gene union built on raw symbols therefore under-counts silently, which matters
because a theme's gene set is the union of its members' genes and every enrichment statistic is
computed over that union.

Resolution runs in two hops against one pinned HGNC release.

**Hop 1, the tier match.** A symbol is looked up with precedence ``approved > previous > alias``.
A lower tier is never consulted once a higher one has matched, so a symbol that is some gene's
approved name is never quietly reinterpreted as another gene's alias. Ambiguity *at the winning
tier* returns ``None`` and is recorded rather than guessed -- the resolver refuses, and the
candidates it could not choose between go to the log for a human to adjudicate. A symbol that
matches no tier gets one last chance against ``withdrawn.txt``, which is the only place retired
symbols survive.

**The Entrez fallback.** Consulted only once approved, previous and alias have all failed and the
symbol is absent from ``withdrawn.txt`` too. NCBI names an uncharacterized locus ``LOC<n>`` where
``n`` *is* its Entrez Gene id, so such a symbol is not matched at all but **decoded**, and the id
looked up against the ``entrez_id`` column of the complete set. This is a deterministic decoding of
a documented naming convention, not a heuristic: nothing is inferred from the shape of the name
beyond what the convention already guarantees, and because HGNC's ``entrez_id`` values are unique
the lookup cannot be ambiguous. Results are recorded with ``match_type="entrez"`` so they stay
distinguishable in the log.

**Hop 2, carry forward.** The identifier hop 1 produced is validated against the release: a record
that has since merged is followed to its current identifier (transitively, guarding against
cycles), and one withdrawn without a replacement resolves to ``None``. A record that was *split*
across several genes is ambiguous, not a coin flip. This is what guarantees that all four sources
land in one identifier space.

An earlier design added a per-source "era lens" -- a 2013 reconstruction of the nomenclature that
BTM was read through, meant to stop a 2013 symbol resolving to whichever gene holds that name
today. It was removed because its premise turned out to be false: symbol reassignment was measured
across the whole of HGNC (229 approved/previous collisions, 102 of them adopted by their current
owner after 2013) and none of those reach the only source the lens applied to, while BTM's symbols
turn out to derive from an Affymetrix annotation build rather than from dated HGNC nomenclature at
all -- so the lens's sole measurable effect was to decline four names HGNC approved after 2013.
"""

import csv
import io
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Literal

#: Affymetrix probe-set convention for one probe mapping to several genes, present only in BTM.
MULTI_MAPPING_SEPARATOR = " /// "

#: NCBI names an uncharacterized locus ``LOC<entrez id>``, so the digits decode to the id itself.
_LOC_SYMBOL = re.compile(r"LOC(\d+)")

_MULTI_VALUE_SEPARATOR = "|"
_MERGE_TARGET_SEPARATOR = ","
_MAX_MERGE_DEPTH = 8
_WITHDRAWN_OUTRIGHT = "Entry Withdrawn"

MatchType = Literal["approved", "previous", "alias", "entrez"]
Outcome = Literal[
    "approved", "previous", "alias", "entrez", "ambiguous", "unmapped", "withdrawn", "merged"
]

TIERS: tuple[MatchType, ...] = ("approved", "previous", "alias")
OUTCOMES: tuple[Outcome, ...] = (
    "approved", "previous", "alias", "entrez", "merged", "ambiguous", "withdrawn", "unmapped",
)


@dataclass(frozen=True, slots=True)
class GeneRecord:
    """One approved gene in the HGNC release.

    Attributes:
        hgnc_id: Stable identifier, e.g. ``HGNC:6025``.
        symbol: Approved symbol.
        prev_symbols: Symbols this gene previously held.
        alias_symbols: Undated synonyms.
        entrez_id: NCBI Entrez Gene id, or the empty string when HGNC records none.
        date_approved_reserved: When the symbol was approved or reserved.
        date_symbol_changed: When ``symbol`` was last changed, or None if never.
    """

    hgnc_id: str
    symbol: str
    prev_symbols: tuple[str, ...] = ()
    alias_symbols: tuple[str, ...] = ()
    entrez_id: str = ""
    date_approved_reserved: date | None = None
    date_symbol_changed: date | None = None


@dataclass(frozen=True, slots=True)
class WithdrawnRecord:
    """One withdrawn or merged HGNC identifier, absent from the complete set.

    Attributes:
        hgnc_id: The retired identifier.
        status: Either ``Entry Withdrawn`` or ``Merged/Split``.
        withdrawn_symbol: The symbol the record held when it was retired.
        merged_into: ``(hgnc_id, symbol, status)`` per target; several means a split.
    """

    hgnc_id: str
    status: str
    withdrawn_symbol: str
    merged_into: tuple[tuple[str, str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class GeneRef:
    """A symbol resolved to a gene.

    Attributes:
        hgnc_id: The gene's identifier, after any merge was followed.
        approved_symbol: The gene's approved symbol.
        match_type: Which tier matched the symbol.
        carried_forward: Whether hop 2 changed the identifier by following a merge.
        matched_hgnc_id: The identifier hop 1 produced, before any merge was followed.
    """

    hgnc_id: str
    approved_symbol: str
    match_type: MatchType
    carried_forward: bool
    matched_hgnc_id: str


@dataclass(frozen=True, slots=True)
class Resolution:
    """The full outcome for one symbol, including the failures that produce no ``GeneRef``.

    Attributes:
        symbol: The symbol as resolved; a component, if it came from a multi-mapping entry.
        outcome: What happened.
        ref: The resolved gene, or None for ambiguous, unmapped and withdrawn outcomes.
        candidates: ``(hgnc_id, symbol)`` per gene an ambiguous match could not choose between.
        note: Human-readable provenance, written to the log's ``note`` column.
        origin: The original multi-mapping entry this symbol was split out of, if any.
    """

    symbol: str
    outcome: Outcome
    ref: GeneRef | None = None
    candidates: tuple[tuple[str, str], ...] = ()
    note: str = ""
    origin: str = ""

    @property
    def is_clean_approved(self) -> bool:
        """Whether this needs no human attention, and so no row in the resolution log."""
        return (
            self.outcome == "approved"
            and self.ref is not None
            and not self.ref.carried_forward
            and not self.origin
            and self.ref.approved_symbol == self.symbol
        )


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    """Everything a caller needs to audit one ``resolve_set`` call.

    Attributes:
        resolutions: One entry per symbol resolved, in input order.
        multi_mapping_derived: Identifiers reached *only* via a multi-mapping entry, so a
            future strict mode can exclude them.
    """

    resolutions: tuple[Resolution, ...]
    multi_mapping_derived: frozenset[str]

    @property
    def counts(self) -> dict[str, int]:
        """Number of symbols per outcome, covering every outcome including the zeroes."""
        tally = dict.fromkeys(OUTCOMES, 0)
        for resolution in self.resolutions:
            tally[resolution.outcome] += 1
        return tally

    @property
    def unmapped(self) -> tuple[str, ...]:
        """The symbols that matched nothing, in input order."""
        return tuple(r.symbol for r in self.resolutions if r.outcome == "unmapped")

    @property
    def ambiguous(self) -> tuple[Resolution, ...]:
        """The ambiguous symbols, each carrying the candidates it could not choose between."""
        return tuple(r for r in self.resolutions if r.outcome == "ambiguous")

    @property
    def carried_forward(self) -> int:
        """How many symbols were carried forward through a merge by hop 2."""
        return sum(1 for r in self.resolutions if r.ref is not None and r.ref.carried_forward)

    def by_hgnc_id(self) -> dict[str, tuple[str, ...]]:
        """Group the resolved symbols by the identifier they landed on.

        Two distinct symbols mapping to one identifier means the source's gene sets shrink on
        deduplication, so this is the signal a within-source collision check reads.

        Returns:
            Each identifier mapped to the distinct symbols that reached it, sorted.
        """
        grouped: dict[str, set[str]] = {}
        for resolution in self.resolutions:
            if resolution.ref is not None:
                grouped.setdefault(resolution.ref.hgnc_id, set()).add(resolution.symbol)
        return {hgnc_id: tuple(sorted(s)) for hgnc_id, s in grouped.items()}


def _split_multi_value(value: str) -> tuple[str, ...]:
    """Split a pipe-delimited HGNC field, dropping empties."""
    return tuple(part.strip() for part in value.split(_MULTI_VALUE_SEPARATOR) if part.strip())


def _parse_date(value: str) -> date | None:
    """Parse an HGNC ``YYYY-MM-DD`` date field, returning None when absent or malformed."""
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _hgnc_sort_key(hgnc_id: str) -> tuple[int, str]:
    """Sort identifiers numerically so candidate lists read in a stable, human order."""
    _, _, digits = hgnc_id.partition(":")
    return (int(digits), hgnc_id) if digits.isdigit() else (1 << 62, hgnc_id)


def parse_complete_set(text: str) -> dict[str, GeneRecord]:
    """Parse an ``hgnc_complete_set`` TSV into records keyed by HGNC id.

    Only ``Approved`` records are kept, which in practice is the whole file: withdrawn and merged
    identifiers live in ``withdrawn.txt`` instead.

    Args:
        text: The full contents of the TSV.

    Returns:
        Approved gene records keyed by HGNC id.
    """
    records: dict[str, GeneRecord] = {}
    for row in csv.DictReader(io.StringIO(text), delimiter="\t"):
        hgnc_id = (row.get("hgnc_id") or "").strip()
        symbol = (row.get("symbol") or "").strip()
        status = (row.get("status") or "").strip()
        if not hgnc_id or not symbol or (status and status != "Approved"):
            continue
        records[hgnc_id] = GeneRecord(
            hgnc_id=hgnc_id,
            symbol=symbol,
            prev_symbols=_split_multi_value(row.get("prev_symbol") or ""),
            alias_symbols=_split_multi_value(row.get("alias_symbol") or ""),
            entrez_id=(row.get("entrez_id") or "").strip(),
            date_approved_reserved=_parse_date(row.get("date_approved_reserved") or ""),
            date_symbol_changed=_parse_date(row.get("date_symbol_changed") or ""),
        )
    return records


def parse_withdrawn(text: str) -> dict[str, WithdrawnRecord]:
    """Parse a ``withdrawn`` TSV into records keyed by HGNC id.

    Read positionally, because the merge column's published header is
    ``MERGED_INTO_REPORT(S) (i.e HGNC_ID|SYMBOL|STATUS)``. Targets are comma-separated and each is
    itself pipe-delimited; more than one target means the record was split rather than merged.

    Args:
        text: The full contents of the TSV.

    Returns:
        Withdrawn and merged records keyed by HGNC id.
    """
    records: dict[str, WithdrawnRecord] = {}
    rows = csv.reader(io.StringIO(text), delimiter="\t")
    for index, row in enumerate(rows):
        if index == 0 or len(row) < 3 or not row[0].strip().startswith("HGNC:"):
            continue
        targets: list[tuple[str, str, str]] = []
        for chunk in (row[3] if len(row) > 3 else "").split(_MERGE_TARGET_SEPARATOR):
            parts = [p.strip() for p in chunk.split(_MULTI_VALUE_SEPARATOR)]
            if len(parts) == 3 and parts[0].startswith("HGNC:"):
                targets.append((parts[0], parts[1], parts[2]))
        records[row[0].strip()] = WithdrawnRecord(
            hgnc_id=row[0].strip(),
            status=row[1].strip(),
            withdrawn_symbol=row[2].strip(),
            merged_into=tuple(targets),
        )
    return records


def _placements(records: Mapping[str, GeneRecord]) -> Iterator[tuple[str, MatchType, str]]:
    """Yield every ``(symbol, tier, hgnc_id)`` the release defines."""
    for record in records.values():
        yield (record.symbol, "approved", record.hgnc_id)
        for symbol in record.prev_symbols:
            yield (symbol, "previous", record.hgnc_id)
        for symbol in record.alias_symbols:
            yield (symbol, "alias", record.hgnc_id)


@dataclass(frozen=True, slots=True)
class Snapshot:
    """The pinned HGNC release, indexed for symbol lookup.

    Attributes:
        records: Approved gene records keyed by HGNC id.
        withdrawn: Withdrawn and merged records keyed by HGNC id.
        index: ``tier -> symbol -> hgnc ids``, the lookup hop 1 walks in tier precedence.
        withdrawn_by_symbol: Retired symbol to the ids that held it; hop 1's last resort.
        entrez_index: Entrez Gene id to HGNC id, backing the ``entrez`` fallback tier.
    """

    records: Mapping[str, GeneRecord]
    withdrawn: Mapping[str, WithdrawnRecord]
    index: Mapping[str, Mapping[str, tuple[str, ...]]]
    withdrawn_by_symbol: Mapping[str, tuple[str, ...]]
    entrez_index: Mapping[str, str]

    @classmethod
    def from_tsv_text(cls, complete_set: str, withdrawn: str = "") -> "Snapshot":
        """Build a snapshot from raw TSV text, as published by HGNC.

        Args:
            complete_set: Contents of an ``hgnc_complete_set`` TSV.
            withdrawn: Contents of the matching ``withdrawn`` TSV; optional but needed for
                merge-following and for the withdrawn-symbol fallback.

        Returns:
            An indexed snapshot.
        """
        records = parse_complete_set(complete_set)
        withdrawn_records = parse_withdrawn(withdrawn)

        tiers: dict[str, dict[str, set[str]]] = {tier: {} for tier in TIERS}
        for symbol, tier, hgnc_id in _placements(records):
            if symbol:
                tiers[tier].setdefault(symbol, set()).add(hgnc_id)
        by_symbol: dict[str, set[str]] = {}
        for record in withdrawn_records.values():
            if record.withdrawn_symbol:
                by_symbol.setdefault(record.withdrawn_symbol, set()).add(record.hgnc_id)

        return cls(
            records=records,
            withdrawn=withdrawn_records,
            index={
                tier: {s: tuple(sorted(ids, key=_hgnc_sort_key)) for s, ids in mapping.items()}
                for tier, mapping in tiers.items()
            },
            withdrawn_by_symbol={
                s: tuple(sorted(ids, key=_hgnc_sort_key)) for s, ids in by_symbol.items()
            },
            entrez_index={r.entrez_id: r.hgnc_id for r in records.values() if r.entrez_id},
        )

    @classmethod
    def from_files(cls, complete_set: Path, withdrawn: Path | None = None) -> "Snapshot":
        """Build a snapshot from files on disk.

        Args:
            complete_set: Path to an ``hgnc_complete_set`` TSV.
            withdrawn: Path to the matching ``withdrawn`` TSV, if available.

        Returns:
            An indexed snapshot.
        """
        return cls.from_tsv_text(
            complete_set.read_text(encoding="utf-8", errors="replace"),
            withdrawn.read_text(encoding="utf-8", errors="replace") if withdrawn else "",
        )


def _format_candidates(candidates: Sequence[tuple[str, str]]) -> str:
    """Render candidate genes for the log's ``note`` column."""
    return "candidates: " + "; ".join(f"{hgnc_id}|{symbol}" for hgnc_id, symbol in candidates)


class GeneResolver:
    """Resolves gene symbols to HGNC identifiers against one pinned release."""

    def __init__(self, snapshot: Snapshot) -> None:
        """Store the release this resolver reads through.

        Args:
            snapshot: The pinned HGNC release.
        """
        self._snapshot = snapshot

    @classmethod
    def from_files(cls, complete_set: Path, withdrawn: Path | None = None) -> "GeneResolver":
        """Load the pinned release from disk.

        Args:
            complete_set: Path to the pinned ``hgnc_complete_set`` TSV.
            withdrawn: Path to the matching ``withdrawn`` TSV.

        Returns:
            A resolver ready to use.
        """
        return cls(Snapshot.from_files(complete_set, withdrawn))

    @property
    def snapshot(self) -> Snapshot:
        """The release this resolver reads through."""
        return self._snapshot

    def resolve(self, symbol: str) -> GeneRef | None:
        """Resolve one symbol to a gene.

        Args:
            symbol: The symbol as it appears in the source.

        Returns:
            The resolved gene, or None if it was ambiguous, unmappable or withdrawn. Use
            :meth:`explain` when the reason matters.
        """
        return self.explain(symbol).ref

    def explain(self, symbol: str) -> Resolution:
        """Resolve one symbol and report why, including the outcomes that produce no gene.

        Args:
            symbol: The symbol as it appears in the source.

        Returns:
            The full outcome, suitable for a row of the resolution log.
        """
        snapshot = self._snapshot
        key = symbol.strip()
        if not key:
            return Resolution(symbol, "unmapped", note="empty symbol")

        for tier in TIERS:
            hgnc_ids = snapshot.index[tier].get(key, ())
            if not hgnc_ids:
                continue
            if len(hgnc_ids) > 1:
                candidates = self._describe(hgnc_ids)
                return Resolution(
                    key,
                    "ambiguous",
                    candidates=candidates,
                    note=f"ambiguous at the {tier} tier; " + _format_candidates(candidates),
                )
            return self._carry_forward(key, hgnc_ids[0], tier)

        retired = snapshot.withdrawn_by_symbol.get(key, ())
        if len(retired) > 1:
            candidates = self._describe(retired)
            return Resolution(
                key,
                "ambiguous",
                candidates=candidates,
                note="ambiguous among withdrawn records; " + _format_candidates(candidates),
            )
        if retired:
            return self._carry_forward(key, retired[0], "approved")

        decoded = _LOC_SYMBOL.fullmatch(key)
        if decoded:
            hgnc_id = snapshot.entrez_index.get(decoded.group(1))
            if hgnc_id is not None:
                return self._carry_forward(key, hgnc_id, "entrez")
            return Resolution(
                key,
                "unmapped",
                note=f"decoded to Entrez Gene {decoded.group(1)}, which HGNC does not record",
            )
        return Resolution(key, "unmapped", note="no match in the HGNC release")

    def _describe(self, hgnc_ids: Sequence[str]) -> tuple[tuple[str, str], ...]:
        """Name each candidate gene, preferring its approved symbol."""
        snapshot = self._snapshot
        described: list[tuple[str, str]] = []
        for hgnc_id in hgnc_ids:
            record = snapshot.records.get(hgnc_id)
            if record is not None:
                described.append((hgnc_id, record.symbol))
                continue
            retired = snapshot.withdrawn.get(hgnc_id)
            described.append((hgnc_id, retired.withdrawn_symbol if retired else "?"))
        return tuple(described)

    def _carry_forward(
        self, symbol: str, matched_hgnc_id: str, match_type: MatchType
    ) -> Resolution:
        """Hop 2: validate the matched identifier against the release, following merges."""
        snapshot = self._snapshot
        hgnc_id = matched_hgnc_id
        seen: set[str] = set()
        for _ in range(_MAX_MERGE_DEPTH):
            if hgnc_id in seen:
                return Resolution(symbol, "unmapped", note=f"merge cycle at {hgnc_id}")
            seen.add(hgnc_id)

            record = snapshot.records.get(hgnc_id)
            if record is not None:
                carried = hgnc_id != matched_hgnc_id
                ref = GeneRef(
                    hgnc_id=hgnc_id,
                    approved_symbol=record.symbol,
                    match_type=match_type,
                    carried_forward=carried,
                    matched_hgnc_id=matched_hgnc_id,
                )
                return Resolution(
                    symbol,
                    "merged" if carried else match_type,
                    ref=ref,
                    note=f"{matched_hgnc_id} merged into {hgnc_id}" if carried else "",
                )

            retired = snapshot.withdrawn.get(hgnc_id)
            if retired is None:
                return Resolution(
                    symbol, "unmapped", note=f"{hgnc_id} is absent from the HGNC release"
                )
            if retired.status == _WITHDRAWN_OUTRIGHT or not retired.merged_into:
                return Resolution(
                    symbol,
                    "withdrawn",
                    note=f"{hgnc_id} ({retired.withdrawn_symbol}) withdrawn with no replacement",
                )
            if len(retired.merged_into) > 1:
                candidates = tuple((t[0], t[1]) for t in retired.merged_into)
                return Resolution(
                    symbol,
                    "ambiguous",
                    candidates=candidates,
                    note=f"{hgnc_id} ({retired.withdrawn_symbol}) was split, not merged; "
                    + _format_candidates(candidates),
                )
            hgnc_id = retired.merged_into[0][0]
        return Resolution(
            symbol,
            "unmapped",
            note=f"merge chain from {matched_hgnc_id} exceeded {_MAX_MERGE_DEPTH} hops",
        )

    def resolve_set(self, symbols: Iterable[str]) -> tuple[frozenset[str], ResolutionReport]:
        """Resolve a source's symbols to a set of HGNC identifiers.

        Entries joined by :data:`MULTI_MAPPING_SEPARATOR` are split and each component resolved
        independently; components that resolve contribute their gene, and those that do not are
        reported. Identifiers reached only through such an entry are listed in the report so a
        strict mode can drop them later.

        Args:
            symbols: Symbols as they appear in the source; duplicates are resolved once.

        Returns:
            The HGNC identifiers, and a report covering every symbol.
        """
        resolutions: list[Resolution] = []
        hgnc_ids: set[str] = set()
        from_multi: set[str] = set()
        from_single: set[str] = set()
        seen: set[str] = set()

        for raw in symbols:
            entry = raw.strip()
            if not entry or entry in seen:
                continue
            seen.add(entry)
            components = [p.strip() for p in entry.split(MULTI_MAPPING_SEPARATOR)]
            origin = entry if len(components) > 1 else ""
            for position, component in enumerate(components, start=1):
                resolution = self.explain(component)
                if origin:
                    provenance = (
                        f"multi-mapping component {position} of {len(components)} in "
                        f'"{origin}"'
                    )
                    resolution = replace(
                        resolution,
                        origin=origin,
                        note=f"{provenance}; {resolution.note}" if resolution.note else provenance,
                    )
                resolutions.append(resolution)
                if resolution.ref is not None:
                    hgnc_ids.add(resolution.ref.hgnc_id)
                    (from_multi if origin else from_single).add(resolution.ref.hgnc_id)

        return frozenset(hgnc_ids), ResolutionReport(
            resolutions=tuple(resolutions),
            multi_mapping_derived=frozenset(from_multi - from_single),
        )
