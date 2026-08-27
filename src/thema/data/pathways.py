"""One uniform record per pathway, across all four sources -- the input the clusterer embeds.

Reactome, GO:BP, Hallmark and BTM agree on almost nothing: different identifier schemes, different
file formats, different prose registers, and one source with no prose at all. This module is where
those four become one shape.

**Two description fields, both permanent.** Curated prose differs sharply in register across the
sources -- Reactome paragraphs at a median of 811 characters, GO one-liners at 143, Hallmark at 58,
BTM none -- so embeddings may cluster partly by *source* rather than by biology. The schema holds
``description_source`` and ``description_generated`` simultaneously so the clusterer can be run over
each and the difference measured, rather than one replacing the other and the question going
unanswered (DECISIONS, 2026-08-21, still open).

**Nothing is filtered here.** Every pathway loads, however degraded, and ``degradation`` records
what happened to it. THEMA clusters on descriptions, so a gene-depleted pathway is still a valid
ontology node; gene content matters at the enrichment stage, where a zero-gene pathway cannot reach
significance and is excluded there. Filtering at load time would bake a statistics-layer judgement
into the representation layer -- and the two layers do not want the same rule. The 10-500 gene bound
DECISIONS records for C5:GO:BP is likewise not applied here; it belongs to the ontology build, where
it can be varied and defended.

Reactome alone does not consult the resolver. Its membership arrives already adjudicated from
``scripts/filter_reactome_membership.py``, whose five-test cascade decides display names the
resolver cannot: ``PB1`` is human PBRM1 in two pathways and influenza polymerase in twenty-five.
"""

import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from thema.data.formats import (
    GeneSet,
    OboTerm,
    parse_obo_terms,
    read_gmt_sets,
    read_msigdb_descriptions,
    read_msigdb_exact_sources,
)
from thema.data.genes import GeneResolver
from thema.data.tables import (
    cell,
    flatten,
    join_bindings,
    join_items,
    optional,
    split_bindings,
    split_items,
)

Source = Literal["reactome", "go", "hallmark", "btm"]
DescriptionOrigin = Literal["reactome_summation", "go_def", "msigdb_xml", "none"]
Degradation = Literal["ok", "depleted", "empty_after_resolution", "no_source_members"]
TextAvailability = Literal["described", "name_only", "no_usable_text"]

#: Source order, fixed so the table and every summary read the same way.
SOURCES: tuple[Source, ...] = ("reactome", "go", "hallmark", "btm")

DEGRADATIONS: tuple[Degradation, ...] = (
    "ok", "depleted", "empty_after_resolution", "no_source_members",
)
TEXT_AVAILABILITIES: tuple[TextAvailability, ...] = ("described", "name_only", "no_usable_text")

#: A pathway losing more than this share of its source members is ``depleted``.
DEPLETED_FRACTION = 0.50

#: BTM names an unnamed module ``TBA``; four of them add a parenthetical hint at the cell type.
BTM_PLACEHOLDER_NAME = "TBA"

#: BTM ends every set name with its module id. Not every id starts with ``M``: twelve are surface
#: signatures ``S0``-``S11``, which a pattern of ``M\d+`` would silently drop.
BTM_MODULE_ID = re.compile(r"\s*\(([MS][\d.]*)\)$")

#: Reactome's species column. Its value describes a pathway's clinical context, not its members'
#: species, so it selects pathways and must never be used to judge whether a member is human.
HUMAN = "Homo sapiens"

PATHWAY_COLUMNS: tuple[str, ...] = (
    "source",
    "source_id",
    "name",
    "n_genes",
    "n_dropped",
    "drop_fraction",
    "degradation",
    "text_availability",
    "description_source_from",
    "description_generated_from",
    "genes",
    "gene_symbols",
    "dropped_symbols",
    "description_source",
    "description_generated",
)


@dataclass(frozen=True, slots=True)
class Pathway:
    """One gene set from one source, in the single representation the clusterer embeds.

    Attributes:
        source: Which database this came from. Also the key the resolver's hand-settled
            adjudications are recorded against, so the two vocabularies must not drift apart.
        source_id: The source's own stable identifier.
        name: The set's title, from its source of record and otherwise unaltered.
        description_source: Curated prose exactly as the source publishes it, or None where the
            source publishes none. Reactome's markup is left in place: it is part of the register
            the normalization A/B is measuring, and removing it is normalization.
        description_source_from: Which file the prose came from; ``none`` when there is none.
        description_generated: LLM-normalized prose, or None until the normalizer has run.
        description_generated_from: What produced it, or None.
        genes: HGNC identifiers, deduplicated.
        gene_symbols: ``(hgnc_id, symbols)`` pairs sorted by identifier, covering exactly ``genes``.
            More than one symbol means two of the source's names met on one gene. Stored as sorted
            pairs rather than a mapping because a dict field would make this record unhashable, and
            because sorting makes the table's byte-stability structural rather than a convention
            the writer has to remember.
        n_genes: How many genes survived. Not ``len(entries) - n_dropped``: symbols collapse.
        n_dropped: How many distinct source symbols contributed no gene.
        dropped_symbols: Those symbols, sorted. For a multi-mapping probe entry these are the
            failed *components*, so an entry can both contribute a gene and record a failure.
        degradation: What happened to this set's membership. See :data:`DEGRADATIONS`.
        drop_fraction: ``n_dropped / (n_genes + n_dropped)``, and 0.0 for a set that never had
            members at all, where the ratio is undefined. Written to the table at full precision
            rather than rounded, so a pathway read back compares equal to the one written.
        text_availability: What text there is to embed. See :data:`TEXT_AVAILABILITIES`.
    """

    source: Source
    source_id: str
    name: str
    description_source: str | None
    description_source_from: DescriptionOrigin
    description_generated: str | None
    description_generated_from: str | None
    genes: frozenset[str]
    gene_symbols: tuple[tuple[str, tuple[str, ...]], ...]
    n_genes: int
    n_dropped: int
    dropped_symbols: tuple[str, ...]
    degradation: Degradation
    drop_fraction: float
    text_availability: TextAvailability

    @property
    def key(self) -> str:
        """Identifier unique across all four sources, for example ``go:GO:0000012``."""
        return f"{self.source}:{self.source_id}"

    @property
    def symbols_by_gene(self) -> dict[str, tuple[str, ...]]:
        """The original symbols behind each gene, as a mapping."""
        return dict(self.gene_symbols)

    def to_row(self) -> tuple[str, ...]:
        """Render this pathway as one row of the build table, in :data:`PATHWAY_COLUMNS` order."""
        return (
            self.source,
            self.source_id,
            self.name,
            str(self.n_genes),
            str(self.n_dropped),
            repr(self.drop_fraction),
            self.degradation,
            self.text_availability,
            self.description_source_from,
            cell(self.description_generated_from),
            join_items(sorted(self.genes)),
            join_bindings(self.gene_symbols),
            join_items(self.dropped_symbols),
            cell(self.description_source),
            cell(self.description_generated),
        )

    @classmethod
    def from_row(cls, row: Sequence[str]) -> "Pathway":
        """Read a pathway back from one row of the build table.

        Args:
            row: The row's cells, in :data:`PATHWAY_COLUMNS` order.

        Returns:
            The pathway the row was written from.

        Raises:
            ValueError: If the row does not have one cell per column.
        """
        if len(row) != len(PATHWAY_COLUMNS):
            raise ValueError(f"expected {len(PATHWAY_COLUMNS)} cells, got {len(row)}")
        return cls(
            source=row[0],  # type: ignore[arg-type]
            source_id=row[1],
            name=row[2],
            description_source=optional(row[13]),
            description_source_from=row[8],  # type: ignore[arg-type]
            description_generated=optional(row[14]),
            description_generated_from=optional(row[9]),
            genes=frozenset(split_items(row[10])),
            gene_symbols=split_bindings(row[11]),
            n_genes=int(row[3]),
            n_dropped=int(row[4]),
            dropped_symbols=split_items(row[12]),
            degradation=row[6],  # type: ignore[arg-type]
            drop_fraction=float(row[5]),
            text_availability=row[7],  # type: ignore[arg-type]
        )


def drop_fraction(n_genes: int, n_dropped: int) -> float:
    """Share of a set's members that contributed no gene.

    Args:
        n_genes: Genes that survived.
        n_dropped: Distinct symbols that did not.

    Returns:
        The share, and 0.0 for a set that never had members, where the ratio is undefined.
    """
    total = n_genes + n_dropped
    return n_dropped / total if total else 0.0


def degradation_of(n_genes: int, n_dropped: int, had_source_members: bool) -> Degradation:
    """Classify what happened to a set's membership.

    The four values are ordered by precedence, most specific first. ``no_source_members`` is
    deliberately not folded into ``empty_after_resolution``: never having had gene content is a
    different fact from having lost it, and only the second says anything about resolution.

    Args:
        n_genes: Genes that survived.
        n_dropped: Distinct symbols that did not.
        had_source_members: Whether the source listed any member for this set at all.

    Returns:
        The classification.
    """
    if not had_source_members:
        return "no_source_members"
    if not n_genes:
        return "empty_after_resolution"
    if drop_fraction(n_genes, n_dropped) > DEPLETED_FRACTION:
        return "depleted"
    return "ok"


def text_availability_of(description: str | None, name_is_placeholder: bool) -> TextAvailability:
    """Classify what text a pathway offers to embed.

    Deliberately not graded by length. Hallmark's descriptions run to a 58-character median, but
    description length is already a number the build reports; anything needing to branch on brevity
    should read the character count rather than a threshold frozen into this vocabulary.

    Args:
        description: The source's curated prose, or None.
        name_is_placeholder: Whether the name is a stand-in rather than a real title.

    Returns:
        ``described`` when there is prose, ``no_usable_text`` when there is neither prose nor a
        real name, and ``name_only`` in between.
    """
    if description:
        return "described"
    return "no_usable_text" if name_is_placeholder else "name_only"


def _pathway(
    source: Source,
    source_id: str,
    name: str,
    description: str | None,
    origin: DescriptionOrigin,
    genes: frozenset[str],
    gene_symbols: Mapping[str, Sequence[str]],
    dropped: Iterable[str],
    had_source_members: bool,
    name_is_placeholder: bool = False,
) -> Pathway:
    """Assemble one pathway, deriving every classification in the one place that does so."""
    dropped_symbols = tuple(sorted(set(dropped)))
    return Pathway(
        source=source,
        source_id=source_id,
        name=name,
        description_source=description,
        description_source_from=origin,
        description_generated=None,
        description_generated_from=None,
        genes=genes,
        gene_symbols=tuple(
            (hgnc_id, tuple(gene_symbols[hgnc_id])) for hgnc_id in sorted(gene_symbols)
        ),
        n_genes=len(genes),
        n_dropped=len(dropped_symbols),
        dropped_symbols=dropped_symbols,
        degradation=degradation_of(len(genes), len(dropped_symbols), had_source_members),
        drop_fraction=drop_fraction(len(genes), len(dropped_symbols)),
        text_availability=text_availability_of(description, name_is_placeholder),
    )


def _resolved(
    source: Source,
    source_id: str,
    name: str,
    description: str | None,
    origin: DescriptionOrigin,
    entries: Sequence[str],
    resolver: GeneResolver,
    name_is_placeholder: bool = False,
) -> Pathway:
    """Resolve a set's symbols and assemble the pathway. The only caller of ``resolve_set``."""
    genes, report = resolver.resolve_set(entries, source)
    return _pathway(
        source=source,
        source_id=source_id,
        name=name,
        description=description,
        origin=origin,
        genes=genes,
        gene_symbols=report.by_hgnc_id(),
        dropped=(r.symbol for r in report.resolutions if r.ref is None),
        had_source_members=bool(entries),
        name_is_placeholder=name_is_placeholder,
    )


def read_reactome_names(lines: Iterable[str]) -> dict[str, str]:
    """Read the human pathways out of ``ReactomePathways.txt``.

    This file is the authority for a Reactome pathway's name, and the only one that is. 28 human
    names carry trailing whitespace and are stripped here; ``ReactomePathways.gmt`` disambiguates
    11 names shared by two pathways by appending ``_<id>``, which would go straight into an
    embedding; and ``reactome_membership.tsv`` inherits the GMT's copy. Take names from here.

    Args:
        lines: The file's lines. It has no header.

    Returns:
        Each human pathway's stable id mapped to its stripped name.
    """
    names: dict[str, str] = {}
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) >= 3 and fields[2].strip() == HUMAN:
            names[fields[0].strip()] = fields[1].strip()
    return names


def read_reactome_summations(lines: Iterable[str]) -> dict[str, str]:
    """Read the curated descriptions out of ``pathway2summation.txt``.

    Two shapes in this file defeat the obvious reader. One row's summation contains a literal
    tab, so it splits into four fields rather than three -- only the first two tabs may be split
    on. And one pathway, ``R-HSA-166016``, carries two rows with different prose; they are joined
    in file order, because a plain ``dict`` assignment would silently keep whichever came last.

    Args:
        lines: The file's lines, including its header.

    Returns:
        Each identifier mapped to its summation, whitespace flattened.
    """
    collected: dict[str, list[str]] = {}
    for index, line in enumerate(lines):
        if index == 0:
            continue
        fields = line.rstrip("\n").split("\t", 2)
        if len(fields) < 3 or not fields[0].strip():
            continue
        collected.setdefault(fields[0].strip(), []).append(fields[2])
    return {key: flatten(" ".join(parts)) for key, parts in collected.items()}


def _reactome_membership(lines: Iterable[str]) -> dict[str, dict[str, list[str]]]:
    """Group the cascade's kept rows into ``pathway -> hgnc id -> source symbols``."""
    kept: dict[str, dict[str, list[str]]] = {}
    for index, line in enumerate(lines):
        if index == 0:
            continue
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 4:
            continue
        symbols = kept.setdefault(fields[0], {}).setdefault(fields[3], [])
        if fields[2] not in symbols:
            symbols.append(fields[2])
    return kept


def _reactome_discards(lines: Iterable[str]) -> dict[str, set[str]]:
    """Group the cascade's discarded rows into ``pathway -> source symbols``."""
    dropped: dict[str, set[str]] = {}
    for index, line in enumerate(lines):
        if index == 0:
            continue
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 3:
            continue
        dropped.setdefault(fields[0], set()).add(fields[2])
    return dropped


def load_reactome_pathways(
    names: Iterable[str],
    membership: Iterable[str],
    discards: Iterable[str],
    summations: Iterable[str],
) -> tuple[Pathway, ...]:
    """Load Reactome's human pathways.

    Reactome never consults the resolver. Its membership arrives already adjudicated by the
    five-test cascade, which uses Reactome's own identifier exports to decide display names no
    symbol resolver could: ``PB1`` is human PBRM1 in two pathways and influenza polymerase in
    twenty-five others. Re-resolving here would throw that away.

    Args:
        names: Lines of ``ReactomePathways.txt``.
        membership: Lines of ``reactome_membership.tsv``, the cascade's kept table.
        discards: Lines of ``reactome_membership_discards.tsv``.
        summations: Lines of ``pathway2summation.txt``.

    Returns:
        One pathway per human pathway, including those the cascade left with no genes.
    """
    titles = read_reactome_names(names)
    kept = _reactome_membership(membership)
    dropped = _reactome_discards(discards)
    prose = read_reactome_summations(summations)

    pathways: list[Pathway] = []
    for pathway_id, title in titles.items():
        symbols = kept.get(pathway_id, {})
        description = prose.get(pathway_id)
        pathways.append(
            _pathway(
                source="reactome",
                source_id=pathway_id,
                name=title,
                description=description or None,
                origin="reactome_summation" if description else "none",
                genes=frozenset(symbols),
                gene_symbols=symbols,
                dropped=dropped.get(pathway_id, set()),
                had_source_members=pathway_id in kept or pathway_id in dropped,
            )
        )
    return tuple(pathways)


def load_go_pathways(
    gmt: Iterable[str],
    term_ids: Mapping[str, str],
    terms: Mapping[str, OboTerm],
    resolver: GeneResolver,
) -> tuple[Pathway, ...]:
    """Load the C5:GO:BP gene sets, joined to their GO terms.

    The join runs through the per-collection JSON, not the GMT: the GMT's second column is a web
    URL and its set names are slugs, so it carries no GO id at all. Name and description come from
    the ontology rather than from MSigDB, which is the authority for both.

    Obsolete terms are kept. GO writes the marker into the text itself -- ``name: obsolete X``,
    ``def: "OBSOLETE. ..."`` -- so those sets carry a source-specific token into the embedding;
    that is a good worked example of what normalizing descriptions is meant to erase, and the build
    reports how many there are.

    Args:
        gmt: Lines of ``c5.go.bp.<release>.symbols.gmt``.
        term_ids: Set name to GO id, from ``read_msigdb_exact_sources``.
        terms: GO terms by identifier, from ``parse_obo_terms``.
        resolver: The pinned HGNC release.

    Returns:
        One pathway per gene set. A set whose term is missing falls back to the MSigDB set name
        and carries no description.
    """
    pathways: list[Pathway] = []
    for gene_set in read_gmt_sets(gmt):
        term_id = term_ids.get(gene_set.name, "")
        term = terms.get(term_id)
        definition = flatten(term.definition) if term and term.definition else ""
        pathways.append(
            _resolved(
                source="go",
                source_id=term_id or gene_set.name,
                name=term.name if term else gene_set.name,
                description=definition or None,
                origin="go_def" if definition else "none",
                entries=gene_set.entries,
                resolver=resolver,
            )
        )
    return tuple(pathways)


def load_hallmark_pathways(
    gmt: Iterable[str],
    descriptions: Mapping[str, str],
    resolver: GeneResolver,
) -> tuple[Pathway, ...]:
    """Load the Hallmark gene sets.

    Descriptions come from the MSigDB XML because nothing else carries them: neither
    ``h.all.<release>.json`` nor ``genesets_<release>.json`` has a description field at all, and
    ``DESCRIPTION_FULL`` is empty for every Hallmark set, so ``DESCRIPTION_BRIEF`` is not the richer
    of two options but the only one there is.

    ``STANDARD_NAME`` serves as both id and name. MSigDB publishes no title field, and prettifying
    ``HALLMARK_APOPTOSIS`` into ``Apoptosis`` would be invented text -- which is exactly what
    ``description_generated`` exists to hold.

    Args:
        gmt: Lines of ``h.all.<release>.symbols.gmt``.
        descriptions: Set name to brief description, from ``read_msigdb_descriptions``.
        resolver: The pinned HGNC release.

    Returns:
        One pathway per gene set.
    """
    pathways: list[Pathway] = []
    for gene_set in read_gmt_sets(gmt):
        description = flatten(descriptions.get(gene_set.name, ""))
        pathways.append(
            _resolved(
                source="hallmark",
                source_id=gene_set.name,
                name=gene_set.name,
                description=description or None,
                origin="msigdb_xml" if description else "none",
                entries=gene_set.entries,
                resolver=resolver,
            )
        )
    return tuple(pathways)


def btm_identity(name: str) -> tuple[str, str, bool]:
    """Split a BTM set name into its module id, its title, and whether the title is a placeholder.

    Args:
        name: The GMT's first column, for example ``integrin cell surface interactions (I) (M1.0)``.

    Returns:
        The module id (the whole name, where none can be parsed), the name with that id removed,
        and whether what remains is BTM's ``TBA`` stand-in rather than a real title.
    """
    match = BTM_MODULE_ID.search(name)
    title = BTM_MODULE_ID.sub("", name).strip() if match else name.strip()
    placeholder = title.upper().split(" ")[0] == BTM_PLACEHOLDER_NAME
    return (match.group(1) if match else name.strip()), title, placeholder


def load_btm_pathways(gmt: Iterable[str], resolver: GeneResolver) -> tuple[Pathway, ...]:
    """Load the blood transcription modules.

    BTM publishes no machine-readable description anywhere -- the GMT's second column is a
    ``mummichog.org`` URL, which is the module id re-encoded as a dead link -- so every set here is
    ``name_only`` at best. 87 are named ``TBA`` and have no usable text at all.

    BTM alone ships Affymetrix multi-mapping probe annotations; ``resolve_set`` splits them, and a
    failure is recorded per failed *component*, so a half-resolving entry both contributes its gene
    and records what was lost.

    Args:
        gmt: Lines of ``BTM_for_GSEA_<date>.gmt``.
        resolver: The pinned HGNC release.

    Returns:
        One pathway per module.
    """
    pathways: list[Pathway] = []
    for gene_set in read_gmt_sets(gmt):
        module_id, title, placeholder = btm_identity(gene_set.name)
        pathways.append(
            _resolved(
                source="btm",
                source_id=module_id,
                name=title,
                description=None,
                origin="none",
                entries=gene_set.entries,
                resolver=resolver,
                name_is_placeholder=placeholder,
            )
        )
    return tuple(pathways)


@dataclass(frozen=True, slots=True)
class PathwayInputs:
    """The files one full build reads.

    No defaults: release-pinned filenames belong to ``scripts/``, where every other pinned string
    in this repository already lives.

    Attributes:
        reactome_names: ``ReactomePathways.txt``.
        reactome_membership: ``reactome_membership.tsv``, the cascade's kept table.
        reactome_discards: ``reactome_membership_discards.tsv``.
        reactome_summations: ``pathway2summation.txt``.
        go_gmt: ``c5.go.bp.<release>.symbols.gmt``.
        go_metadata: ``c5.go.bp.<release>.json``, which carries the GO ids.
        go_obo: ``go-basic.obo``.
        hallmark_gmt: ``h.all.<release>.symbols.gmt``.
        hallmark_xml: ``msigdb_<release>.xml``, the only source of Hallmark prose.
        btm_gmt: ``BTM_for_GSEA_<date>.gmt``.
    """

    reactome_names: Path
    reactome_membership: Path
    reactome_discards: Path
    reactome_summations: Path
    go_gmt: Path
    go_metadata: Path
    go_obo: Path
    hallmark_gmt: Path
    hallmark_xml: Path
    btm_gmt: Path

    @property
    def paths(self) -> tuple[Path, ...]:
        """Every input, so a caller can report all the missing ones in one pass."""
        return (
            self.reactome_names,
            self.reactome_membership,
            self.reactome_discards,
            self.reactome_summations,
            self.go_gmt,
            self.go_metadata,
            self.go_obo,
            self.hallmark_gmt,
            self.hallmark_xml,
            self.btm_gmt,
        )

    @property
    def missing(self) -> tuple[Path, ...]:
        """The inputs that are not on disk, in declaration order."""
        return tuple(path for path in self.paths if not path.is_file())


@dataclass(frozen=True, slots=True)
class PathwayCollection:
    """Every pathway from every source, in one deterministic order.

    Attributes:
        pathways: Sorted by source in :data:`SOURCES` order, then by ``source_id`` lexically.
    """

    pathways: tuple[Pathway, ...]

    def __len__(self) -> int:
        """How many pathways this holds."""
        return len(self.pathways)

    def __iter__(self) -> Iterator[Pathway]:
        """Iterate the pathways in table order."""
        return iter(self.pathways)

    @property
    def by_key(self) -> dict[str, Pathway]:
        """Each pathway by its cross-source key."""
        return {pathway.key: pathway for pathway in self.pathways}

    @property
    def counts_by_source(self) -> dict[str, int]:
        """How many pathways came from each source, covering all four including the zeroes."""
        tally = dict.fromkeys(SOURCES, 0)
        for pathway in self.pathways:
            tally[pathway.source] += 1
        return tally

    @property
    def gene_union(self) -> frozenset[str]:
        """Every gene reached by any pathway."""
        if not self.pathways:
            return frozenset()
        return frozenset().union(*(p.genes for p in self.pathways))

    def of_source(self, source: str) -> tuple[Pathway, ...]:
        """The pathways from one source, in table order.

        Args:
            source: The source key.

        Returns:
            Its pathways, empty if it contributed none.
        """
        return tuple(p for p in self.pathways if p.source == source)

    @classmethod
    def of(cls, *groups: Iterable[Pathway]) -> "PathwayCollection":
        """Assemble a collection, sorting it and checking what must hold of every pathway.

        The stored counts, drop fraction and degradation are derived values held as fields, so this
        is where they are checked against the collections they describe. A contradiction raises
        rather than being repaired: a repaired record hides the bug that produced it.

        Args:
            *groups: Pathways, from one loader per group.

        Returns:
            The sorted collection.

        Raises:
            ValueError: If two pathways share a key, if a stored derived value contradicts what it
                is derived from, or if a description and its stated origin disagree.
        """
        pathways = tuple(
            sorted(
                (p for group in groups for p in group),
                key=lambda p: (SOURCES.index(p.source), p.source_id),
            )
        )
        seen: set[str] = set()
        for pathway in pathways:
            if pathway.key in seen:
                raise ValueError(f"two pathways share the key {pathway.key}")
            seen.add(pathway.key)
            _check(pathway)
        return cls(pathways)

    @classmethod
    def from_files(cls, inputs: PathwayInputs, resolver: GeneResolver) -> "PathwayCollection":
        """Run every loader over the files on disk.

        Args:
            inputs: The files to read.
            resolver: The pinned HGNC release, used by every source except Reactome.

        Returns:
            The full collection.
        """
        with (
            inputs.reactome_names.open(encoding="utf-8", errors="replace") as names,
            inputs.reactome_membership.open(encoding="utf-8", errors="replace") as membership,
            inputs.reactome_discards.open(encoding="utf-8", errors="replace") as discards,
            inputs.reactome_summations.open(encoding="utf-8", errors="replace") as summations,
        ):
            reactome = load_reactome_pathways(names, membership, discards, summations)

        with inputs.go_obo.open(encoding="utf-8", errors="replace") as obo:
            terms = parse_obo_terms(obo, namespace="biological_process")
        term_ids = read_msigdb_exact_sources(inputs.go_metadata.read_text(encoding="utf-8"))
        with inputs.go_gmt.open(encoding="utf-8", errors="replace") as gmt:
            go = load_go_pathways(gmt, term_ids, terms, resolver)

        with inputs.hallmark_gmt.open(encoding="utf-8", errors="replace") as gmt:
            hallmark_sets: tuple[GeneSet, ...] = read_gmt_sets(gmt)
        with inputs.hallmark_xml.open(encoding="utf-8", errors="replace") as xml:
            descriptions = read_msigdb_descriptions(xml, {s.name for s in hallmark_sets})
        with inputs.hallmark_gmt.open(encoding="utf-8", errors="replace") as gmt:
            hallmark = load_hallmark_pathways(gmt, descriptions, resolver)

        with inputs.btm_gmt.open(encoding="utf-8", errors="replace") as gmt:
            btm = load_btm_pathways(gmt, resolver)

        return cls.of(reactome, go, hallmark, btm)

    @classmethod
    def from_tsv_text(cls, text: str) -> "PathwayCollection":
        """Read a collection back from the build table.

        Args:
            text: The file's contents, header included.

        Returns:
            The collection the table was written from.

        Raises:
            ValueError: If the header is not :data:`PATHWAY_COLUMNS`, or a row fails the checks
                :meth:`of` applies.
        """
        lines = text.splitlines()
        if not lines or tuple(lines[0].split("\t")) != PATHWAY_COLUMNS:
            raise ValueError("the table's header does not match PATHWAY_COLUMNS")
        return cls.of(Pathway.from_row(line.split("\t")) for line in lines[1:] if line)

    def to_rows(self) -> tuple[tuple[str, ...], ...]:
        """Render every pathway as a row, in :data:`PATHWAY_COLUMNS` order."""
        return tuple(pathway.to_row() for pathway in self.pathways)


def _check(pathway: Pathway) -> None:
    """Raise if a pathway's stored derived values contradict what they are derived from."""
    if pathway.n_genes != len(pathway.genes):
        raise ValueError(f"{pathway.key}: n_genes {pathway.n_genes} != {len(pathway.genes)} genes")
    if pathway.n_dropped != len(pathway.dropped_symbols):
        raise ValueError(f"{pathway.key}: n_dropped contradicts dropped_symbols")
    if {hgnc_id for hgnc_id, _ in pathway.gene_symbols} != set(pathway.genes):
        raise ValueError(f"{pathway.key}: gene_symbols does not cover exactly genes")
    expected = drop_fraction(pathway.n_genes, pathway.n_dropped)
    if abs(pathway.drop_fraction - expected) > 1e-6:
        raise ValueError(f"{pathway.key}: drop_fraction {pathway.drop_fraction} != {expected}")
    if (pathway.description_source is None) != (pathway.description_source_from == "none"):
        raise ValueError(f"{pathway.key}: description and its stated origin disagree")
    if pathway.degradation not in DEGRADATIONS:
        raise ValueError(f"{pathway.key}: unknown degradation {pathway.degradation}")
    if pathway.text_availability not in TEXT_AVAILABILITIES:
        raise ValueError(f"{pathway.key}: unknown text_availability {pathway.text_availability}")
