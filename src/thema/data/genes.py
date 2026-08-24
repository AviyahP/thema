"""Resolve source gene symbols to stable HGNC identifiers.

THEMA's four gene-set sources ship gene symbols, not identifiers, and they were symbol-mapped at
three different dates by three different providers. Symbols drift: they are renamed, retired,
merged, and -- worst of all -- *reassigned* from one gene to another. A cross-database gene union
built on raw symbols therefore under-counts silently, which matters because a theme's gene set is
the union of its members' genes and every enrichment statistic is computed over that union.

Resolution runs in two hops, and each hop exists to defeat a different failure.

**Hop 1, the era lens.** A symbol is matched inside the snapshot of the nomenclature that was
current when its source was compiled, with precedence ``approved > previous > alias`` *as defined
inside that snapshot*. Without this, a symbol that was gene A's approved name in 2013 but is gene
B's approved name today resolves cleanly and confidently to B -- the wrong gene, with no signal
that anything went wrong. Reading it through a 2013 lens makes it a clean approved match for A, and
it never falls through to another gene's alias. Ambiguity at the winning tier returns ``None`` and
is recorded rather than guessed, and a lower tier is never consulted once a higher one matched.

**Hop 2, carry forward.** The identifier hop 1 produces belongs to the era, so it is validated
against the current release: a record that has since merged is followed to its current identifier,
and one withdrawn without replacement resolves to ``None``. This is what guarantees that all four
sources unify on one current identifier space no matter which lens resolved them.

Loaders never choose a lens ad hoc; they consult :data:`SOURCE_SNAPSHOT`.

The 2013 lens is a reconstruction, not an archive
-------------------------------------------------
No pre-2020 HGNC snapshot exists. This was verified, not assumed: the ``ftp.ebi.ac.uk`` genenames
tree is retired and 404s on every path, exhaustive enumeration of the current host's ``hgnc/``
prefix (5,700 objects) found nothing dated before 2020-07-01, and the Wayback Machine holds no
captures of the old tree. The earliest real snapshot of any kind postdates BTM by nearly seven
years, so it would not help.

:meth:`Snapshot.derived` therefore reconstructs the era lens from the current release's own
``date_approved_reserved`` and ``date_symbol_changed`` columns: a gene's current symbol occupies
the approved tier only if the gene demonstrably held it on the cutoff date, and otherwise that
symbol is demoted in favour of the gene's previous symbols. Three limitations follow, and each is
recorded in the resolution log rather than hidden:

1. Only the *most recent* rename is dated, so a gene renamed more than once contributes all of its
   previous symbols to the approved tier. Such matches are flagged ``approximate``.
2. Genes withdrawn outright since the cutoff are absent from the current release and cannot be
   reconstructed this way. Genes that *merged* are partially recoverable, because ``withdrawn.txt``
   maps the retired symbol to its identifier and that identifier to its merge target; this is the
   ``merged`` outcome.
3. Aliases carry no dates at all and are treated as cumulative. HGNC also sometimes re-approves a
   record under a new symbol without recording a previous symbol, leaving the old name only as an
   alias -- so some era-correct matches land at the alias tier rather than the approved one.

A source's symbols are not guaranteed to be drawn from HGNC at its compilation date, either: BTM's
come from Affymetrix probe annotations and include a handful of names HGNC only approved *after*
2013. The era lens correctly declines these, and the log records them.

The derivation is computed from a pinned release, so it is reproducible. It is also largely robust
to newer releases, since a rename after the cutoff re-resolves through the previous-symbol tier;
residual drift comes from withdrawn records, accumulated multi-renames, and HGNC corrections.
"""

import csv
import io
import warnings
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Literal

CURRENT = "current"
ERA_2013 = "2013-10"

#: Compilation date of ``BTM_for_GSEA_20131008.gmt``, and so the cutoff for the ``2013-10`` lens.
BTM_CUTOFF = date(2013, 10, 8)

#: The snapshot each source must be read through. Loaders consult this table; they never choose.
SOURCE_SNAPSHOT: dict[str, str] = {
    "btm": ERA_2013,
    "reactome": CURRENT,
    "hallmark": CURRENT,
    "go": CURRENT,
}

#: Affymetrix probe-set convention for one probe mapping to several genes, present only in BTM.
MULTI_MAPPING_SEPARATOR = " /// "

_MULTI_VALUE_SEPARATOR = "|"
_MERGE_TARGET_SEPARATOR = ","
_MAX_MERGE_DEPTH = 8
_WITHDRAWN_OUTRIGHT = "Entry Withdrawn"

MatchType = Literal["approved", "previous", "alias"]
Outcome = Literal[
    "approved", "previous", "alias", "ambiguous", "unmapped", "withdrawn", "merged"
]

TIERS: tuple[MatchType, ...] = ("approved", "previous", "alias")
OUTCOMES: tuple[Outcome, ...] = (
    "approved", "previous", "alias", "merged", "ambiguous", "withdrawn", "unmapped",
)


@dataclass(frozen=True, slots=True)
class GeneRecord:
    """One approved gene in an HGNC release.

    Attributes:
        hgnc_id: Stable identifier, e.g. ``HGNC:6025``.
        symbol: Approved symbol in this release.
        prev_symbols: Symbols this gene previously held, most recent first.
        alias_symbols: Undated synonyms.
        date_approved_reserved: When the gene entered the nomenclature.
        date_symbol_changed: When ``symbol`` was last changed, or None if never.
    """

    hgnc_id: str
    symbol: str
    prev_symbols: tuple[str, ...] = ()
    alias_symbols: tuple[str, ...] = ()
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
    """A symbol resolved to a gene in the current identifier space.

    Attributes:
        hgnc_id: The gene's identifier in the *current* release.
        approved_symbol: The gene's approved symbol in the *current* release.
        match_type: Which tier of the era lens matched the symbol.
        snapshot: Label of the snapshot that resolved it.
        carried_forward: Whether hop 2 changed the identifier by following a merge.
        era_hgnc_id: The identifier hop 1 produced, before any merge was followed.
    """

    hgnc_id: str
    approved_symbol: str
    match_type: MatchType
    snapshot: str
    carried_forward: bool
    era_hgnc_id: str


@dataclass(frozen=True, slots=True)
class Resolution:
    """The full outcome for one symbol, including the failures that produce no ``GeneRef``.

    Attributes:
        symbol: The symbol as resolved; a component, if it came from a multi-mapping entry.
        outcome: What happened.
        ref: The resolved gene, or None for ambiguous, unmapped and withdrawn outcomes.
        candidates: ``(hgnc_id, symbol)`` per gene an ambiguous match could not choose between.
        note: Human-readable provenance, written to the log's ``note`` column.
        approximate: Whether the era lens could not date this match precisely.
        origin: The original multi-mapping entry this symbol was split out of, if any.
    """

    symbol: str
    outcome: Outcome
    ref: GeneRef | None = None
    candidates: tuple[tuple[str, str], ...] = ()
    note: str = ""
    approximate: bool = False
    origin: str = ""

    @property
    def is_clean_current_approved(self) -> bool:
        """Whether this needs no human attention, and so no row in the resolution log."""
        return (
            self.outcome == "approved"
            and self.ref is not None
            and not self.ref.carried_forward
            and not self.approximate
            and not self.origin
            and self.ref.approved_symbol == self.symbol
        )


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    """Everything a caller needs to audit one ``resolve_set`` call.

    Attributes:
        snapshot: The lens the symbols were resolved through.
        resolutions: One entry per symbol resolved, in input order.
        multi_mapping_derived: Identifiers reached *only* via a multi-mapping entry, so a
            future strict mode can exclude them.
    """

    snapshot: str
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


@dataclass(frozen=True, slots=True)
class Snapshot:
    """One release of the HGNC nomenclature, indexed for symbol lookup.

    Attributes:
        label: How :data:`SOURCE_SNAPSHOT` refers to this snapshot.
        records: Approved gene records keyed by HGNC id.
        withdrawn: Withdrawn and merged records keyed by HGNC id.
        index: ``tier -> symbol -> hgnc ids``, the lookup hop 1 walks in tier precedence.
        withdrawn_by_symbol: Retired symbol to the ids that held it; hop 1's last resort.
        approximate: Ids whose placement in this snapshot could not be dated precisely.
    """

    label: str
    records: Mapping[str, GeneRecord]
    withdrawn: Mapping[str, WithdrawnRecord]
    index: Mapping[str, Mapping[str, tuple[str, ...]]]
    withdrawn_by_symbol: Mapping[str, tuple[str, ...]]
    approximate: frozenset[str]

    @classmethod
    def _build(
        cls,
        label: str,
        records: Mapping[str, GeneRecord],
        withdrawn: Mapping[str, WithdrawnRecord],
        placements: Iterable[tuple[str, MatchType, str]],
        approximate: frozenset[str],
    ) -> "Snapshot":
        tiers: dict[str, dict[str, set[str]]] = {tier: {} for tier in TIERS}
        for symbol, tier, hgnc_id in placements:
            if symbol:
                tiers[tier].setdefault(symbol, set()).add(hgnc_id)
        by_symbol: dict[str, set[str]] = {}
        for record in withdrawn.values():
            if record.withdrawn_symbol:
                by_symbol.setdefault(record.withdrawn_symbol, set()).add(record.hgnc_id)
        return cls(
            label=label,
            records=dict(records),
            withdrawn=dict(withdrawn),
            index={
                tier: {s: tuple(sorted(ids, key=_hgnc_sort_key)) for s, ids in mapping.items()}
                for tier, mapping in tiers.items()
            },
            withdrawn_by_symbol={
                s: tuple(sorted(ids, key=_hgnc_sort_key)) for s, ids in by_symbol.items()
            },
            approximate=approximate,
        )

    @classmethod
    def from_tsv_text(cls, label: str, complete_set: str, withdrawn: str = "") -> "Snapshot":
        """Build a snapshot from raw TSV text, as published by HGNC.

        Args:
            label: How :data:`SOURCE_SNAPSHOT` will refer to this snapshot.
            complete_set: Contents of an ``hgnc_complete_set`` TSV.
            withdrawn: Contents of the matching ``withdrawn`` TSV; optional but needed for
                merge-following and for the withdrawn-symbol fallback.

        Returns:
            An indexed snapshot.
        """
        records = parse_complete_set(complete_set)
        return cls._build(
            label, records, parse_withdrawn(withdrawn), _natural_placements(records), frozenset()
        )

    @classmethod
    def from_files(
        cls, label: str, complete_set: Path, withdrawn: Path | None = None
    ) -> "Snapshot":
        """Build a snapshot from files on disk.

        Args:
            label: How :data:`SOURCE_SNAPSHOT` will refer to this snapshot.
            complete_set: Path to an ``hgnc_complete_set`` TSV.
            withdrawn: Path to the matching ``withdrawn`` TSV, if available.

        Returns:
            An indexed snapshot.
        """
        return cls.from_tsv_text(
            label,
            complete_set.read_text(encoding="utf-8", errors="replace"),
            withdrawn.read_text(encoding="utf-8", errors="replace") if withdrawn else "",
        )

    def derived(self, label: str, cutoff: date) -> "Snapshot":
        """Reconstruct the nomenclature as it stood on ``cutoff``, from this snapshot's dates.

        A gene's current symbol earns the approved tier only if the gene actually held it on the
        cutoff date -- that is, if both ``date_approved_reserved`` and ``date_symbol_changed`` fall
        on or before it. Otherwise that symbol is dropped from the approved tier and the gene's
        previous symbols take its place, since one of them was approved then. This is what stops a
        gene that took a name after the cutoff from capturing it from the gene that held it.

        Aliases stay reachable at the alias tier regardless of dates, and no gene is dropped
        wholesale. That matters because ``date_approved_reserved`` records when the *symbol* was
        approved, not when the gene entered the nomenclature: HGNC sometimes re-approves a record
        under a new symbol and clears its history, leaving the old name only as an alias. SELENOF
        is the worked example -- approved 2016-09-18, no previous symbols, and its pre-2016 name
        SEP15 survives only as an alias. Dropping such genes would lose the old name entirely while
        buying no extra protection, because their current symbol is already out of the approved
        tier.

        See the module docstring for the limitations that remain.

        Args:
            label: Label for the derived snapshot, e.g. ``"2013-10"``.
            cutoff: The date to reconstruct.

        Returns:
            A snapshot of the nomenclature as reconstructed for ``cutoff``.
        """
        placements: list[tuple[str, MatchType, str]] = []
        approximate: set[str] = set()
        for record in self.records.values():
            approved = record.date_approved_reserved
            changed = record.date_symbol_changed
            held_at_cutoff = (approved is None or approved <= cutoff) and (
                changed is None or changed <= cutoff
            )
            if held_at_cutoff:
                placements.append((record.symbol, "approved", record.hgnc_id))
                placements.extend((s, "previous", record.hgnc_id) for s in record.prev_symbols)
            else:
                placements.extend((s, "approved", record.hgnc_id) for s in record.prev_symbols)
                if len(record.prev_symbols) > 1:
                    approximate.add(record.hgnc_id)
            placements.extend((s, "alias", record.hgnc_id) for s in record.alias_symbols)
        return Snapshot._build(
            label, self.records, self.withdrawn, placements, frozenset(approximate)
        )


def _natural_placements(
    records: Mapping[str, GeneRecord],
) -> Iterator[tuple[str, MatchType, str]]:
    """Yield the tier placements of a released snapshot, where each field means what it says."""
    for record in records.values():
        yield (record.symbol, "approved", record.hgnc_id)
        for symbol in record.prev_symbols:
            yield (symbol, "previous", record.hgnc_id)
        for symbol in record.alias_symbols:
            yield (symbol, "alias", record.hgnc_id)


def _format_candidates(candidates: Sequence[tuple[str, str]]) -> str:
    """Render candidate genes for the log's ``note`` column."""
    return "candidates: " + "; ".join(f"{hgnc_id}|{symbol}" for hgnc_id, symbol in candidates)


class GeneResolver:
    """Resolves gene symbols to current HGNC identifiers through per-source era lenses.

    Construct from one or more snapshots keyed by label. A ``current`` snapshot is mandatory,
    because hop 2 validates every era identifier against it.
    """

    def __init__(self, snapshots: Mapping[str, Snapshot]) -> None:
        """Store the snapshots this resolver can read through.

        Args:
            snapshots: Snapshots keyed by label, which must include ``current``.

        Raises:
            ValueError: If no ``current`` snapshot was supplied.
        """
        if CURRENT not in snapshots:
            message = f"a {CURRENT!r} snapshot is required; hop 2 validates era ids against it"
            raise ValueError(message)
        self._snapshots: dict[str, Snapshot] = dict(snapshots)

    @classmethod
    def from_files(
        cls,
        complete_set: Path,
        withdrawn: Path | None = None,
        *,
        eras: Mapping[str, date] | None = None,
    ) -> "GeneResolver":
        """Load the current release and derive the era lenses from it.

        Args:
            complete_set: Path to the pinned ``hgnc_complete_set`` TSV.
            withdrawn: Path to the matching ``withdrawn`` TSV.
            eras: Label to cutoff date for each derived lens; defaults to the BTM lens.

        Returns:
            A resolver holding ``current`` plus one snapshot per requested era.
        """
        current = Snapshot.from_files(CURRENT, complete_set, withdrawn)
        wanted = {ERA_2013: BTM_CUTOFF} if eras is None else eras
        snapshots = {CURRENT: current}
        for label, cutoff in wanted.items():
            snapshots[label] = current.derived(label, cutoff)
        return cls(snapshots)

    @property
    def labels(self) -> tuple[str, ...]:
        """Labels of the snapshots this resolver holds."""
        return tuple(self._snapshots)

    def snapshot_for(self, source: str) -> str:
        """Return the snapshot label ``source`` must be read through.

        Falls back to ``current`` with a warning when the assigned snapshot was not loaded, so a
        missing era lens degrades loudly rather than silently changing which genes a source maps to.

        Args:
            source: A key of :data:`SOURCE_SNAPSHOT`.

        Returns:
            The label to pass as ``as_of``.
        """
        label = SOURCE_SNAPSHOT.get(source, CURRENT)
        if label not in self._snapshots:
            warnings.warn(
                f"snapshot {label!r} for source {source!r} is unavailable; resolving through "
                f"{CURRENT!r}. Symbols reassigned between genes since then will resolve to the "
                "current owner of the symbol, not the one the source meant.",
                RuntimeWarning,
                stacklevel=2,
            )
            return CURRENT
        return label

    def resolve(self, symbol: str, as_of: str) -> GeneRef | None:
        """Resolve one symbol to a gene in the current identifier space.

        Args:
            symbol: The symbol as it appears in the source.
            as_of: Snapshot label, from :meth:`snapshot_for`.

        Returns:
            The resolved gene, or None if it was ambiguous, unmappable or withdrawn. Use
            :meth:`explain` when the reason matters.
        """
        return self.explain(symbol, as_of).ref

    def explain(self, symbol: str, as_of: str) -> Resolution:
        """Resolve one symbol and report why, including the outcomes that produce no gene.

        Args:
            symbol: The symbol as it appears in the source.
            as_of: Snapshot label, from :meth:`snapshot_for`.

        Returns:
            The full outcome, suitable for a row of the resolution log.

        Raises:
            KeyError: If ``as_of`` names a snapshot this resolver does not hold.
        """
        if as_of not in self._snapshots:
            message = f"unknown snapshot {as_of!r}; have {sorted(self._snapshots)}"
            raise KeyError(message)
        snapshot = self._snapshots[as_of]
        key = symbol.strip()
        if not key:
            return Resolution(symbol, "unmapped", note="empty symbol")

        for tier in TIERS:
            hgnc_ids = snapshot.index[tier].get(key, ())
            if not hgnc_ids:
                continue
            if len(hgnc_ids) > 1:
                candidates = self._describe(hgnc_ids, snapshot)
                return Resolution(
                    key,
                    "ambiguous",
                    candidates=candidates,
                    note=f"ambiguous at the {tier} tier of snapshot {snapshot.label}; "
                    + _format_candidates(candidates),
                )
            return self._carry_forward(key, hgnc_ids[0], tier, snapshot)

        retired = snapshot.withdrawn_by_symbol.get(key, ())
        if len(retired) > 1:
            candidates = self._describe(retired, snapshot)
            return Resolution(
                key,
                "ambiguous",
                candidates=candidates,
                note="ambiguous among withdrawn records; " + _format_candidates(candidates),
            )
        if retired:
            return self._carry_forward(key, retired[0], "approved", snapshot)
        return Resolution(key, "unmapped", note=f"no match in snapshot {snapshot.label}")

    def _describe(self, hgnc_ids: Sequence[str], snapshot: Snapshot) -> tuple[tuple[str, str], ...]:
        """Name each candidate gene, preferring its current approved symbol."""
        current = self._snapshots[CURRENT]
        described: list[tuple[str, str]] = []
        for hgnc_id in hgnc_ids:
            record = current.records.get(hgnc_id) or snapshot.records.get(hgnc_id)
            if record is not None:
                described.append((hgnc_id, record.symbol))
                continue
            retired = current.withdrawn.get(hgnc_id)
            described.append((hgnc_id, retired.withdrawn_symbol if retired else "?"))
        return tuple(described)

    def _carry_forward(
        self, symbol: str, era_hgnc_id: str, match_type: MatchType, snapshot: Snapshot
    ) -> Resolution:
        """Hop 2: validate an era identifier against the current release, following merges."""
        current = self._snapshots[CURRENT]
        approximate = era_hgnc_id in snapshot.approximate
        hgnc_id = era_hgnc_id
        seen: set[str] = set()
        for _ in range(_MAX_MERGE_DEPTH):
            if hgnc_id in seen:
                return Resolution(
                    symbol, "unmapped", note=f"merge cycle at {hgnc_id}", approximate=approximate
                )
            seen.add(hgnc_id)

            record = current.records.get(hgnc_id)
            if record is not None:
                carried = hgnc_id != era_hgnc_id
                ref = GeneRef(
                    hgnc_id=hgnc_id,
                    approved_symbol=record.symbol,
                    match_type=match_type,
                    snapshot=snapshot.label,
                    carried_forward=carried,
                    era_hgnc_id=era_hgnc_id,
                )
                notes: list[str] = []
                if carried:
                    notes.append(f"{era_hgnc_id} merged into {hgnc_id}")
                if approximate:
                    era_record = current.records.get(era_hgnc_id)
                    others = era_record.prev_symbols if era_record is not None else ()
                    detail = f" ({', '.join(others)})" if others else ""
                    notes.append(
                        "era placement approximate: only the most recent rename is dated, and "
                        f"{era_hgnc_id} has several previous symbols{detail}"
                    )
                return Resolution(
                    symbol,
                    "merged" if carried else match_type,
                    ref=ref,
                    note="; ".join(notes),
                    approximate=approximate,
                )

            retired = current.withdrawn.get(hgnc_id)
            if retired is None:
                return Resolution(
                    symbol,
                    "unmapped",
                    note=f"{hgnc_id} is in snapshot {snapshot.label} but absent from the current "
                    "release",
                    approximate=approximate,
                )
            if retired.status == _WITHDRAWN_OUTRIGHT or not retired.merged_into:
                return Resolution(
                    symbol,
                    "withdrawn",
                    note=f"{hgnc_id} ({retired.withdrawn_symbol}) withdrawn with no replacement",
                    approximate=approximate,
                )
            if len(retired.merged_into) > 1:
                candidates = tuple((t[0], t[1]) for t in retired.merged_into)
                return Resolution(
                    symbol,
                    "ambiguous",
                    candidates=candidates,
                    note=f"{hgnc_id} ({retired.withdrawn_symbol}) was split, not merged; "
                    + _format_candidates(candidates),
                    approximate=approximate,
                )
            hgnc_id = retired.merged_into[0][0]
        return Resolution(
            symbol,
            "unmapped",
            note=f"merge chain from {era_hgnc_id} exceeded {_MAX_MERGE_DEPTH} hops",
            approximate=approximate,
        )

    def resolve_set(
        self, symbols: Iterable[str], as_of: str
    ) -> tuple[frozenset[str], ResolutionReport]:
        """Resolve a source's symbols to a set of current HGNC identifiers.

        Entries joined by :data:`MULTI_MAPPING_SEPARATOR` are split and each component resolved
        independently; components that resolve contribute their gene, and those that do not are
        reported. Identifiers reached only through such an entry are listed in the report so a
        strict mode can drop them later.

        Args:
            symbols: Symbols as they appear in the source; duplicates are resolved once.
            as_of: Snapshot label, from :meth:`snapshot_for`.

        Returns:
            The current HGNC identifiers, and a report covering every symbol.
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
                resolution = self.explain(component, as_of)
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
            snapshot=as_of,
            resolutions=tuple(resolutions),
            multi_mapping_derived=frozenset(from_multi - from_single),
        )
