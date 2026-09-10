"""Curator-declared related pairs, and the machinery for judging how good each source of them is.

THEMA's structural claim is that it co-clusters pathways curators call related, especially the ones
that share few or no genes. Testing that needs pairs a human declared related, and the sources
differ sharply in how much they are worth:

**Cross-database (strong).** ``reactome2go`` maps Reactome pathways to GO terms. The prose THEMA
embeds comes from Reactome; the judgement that a pathway matches a GO term came from GO curators
working on a different vocabulary. Nothing in the input told the model these two belong together.

**Same-curator siblings (weak, and labelled weak wherever they are reported).** Two Reactome
pathways under one parent are related because Reactome says so -- but Reactome's curators wrote
both the hierarchy AND the summations THEMA embeds, so recovering a sibling pair is partly "the
text encodes the tree" rather than a discovery. The same applies to GO. Siblings are a supplementary
source that shows whether a method is in the right region at all; they are never the headline.

**Name collisions (strong for redundancy, circular for anything name-shaped).** Pathways different
databases give the same name are the redundancy THEMA exists to collapse. But their positives are
defined BY the name, so any arm that sees the name scores at ceiling by construction -- which is
why the v3 prompt's "repeat the name" rule inflates this metric and why a name-only baseline must
be excluded from it.

A pair that is BOTH a curated mapping and a name collision is not independent evidence of the first
kind; :func:`shares_name` marks those so they can be reported apart rather than averaged in.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations

from thema.data.formats import OboTerm
from thema.data.pathways import Pathway, PathwayCollection, collision_groups, normalized_name

#: Gene-set Jaccard bands. Exact zero is its own band because gene-overlap clustering cannot
#: succeed there by construction, and averaging it into a neighbour hides that.
BANDS: tuple[tuple[float, float], ...] = (
    (0.0, 0.0),
    (0.0, 0.01),
    (0.01, 0.05),
    (0.05, 0.15),
    (0.15, 1.01),
)

#: Below this many pairs a percentage is misleading and the raw fraction is printed instead.
QUOTABLE = 10

_MAPPING_LINE = re.compile(r"^Reactome:(\S+)\s*>\s*GO:.*?;\s*(GO:\d+)\s*$")


@dataclass(frozen=True, slots=True)
class PairSource:
    """One set of curator-declared related pairs, with what it is worth.

    Attributes:
        name: Short label for tables.
        pairs: ``(key, key)`` tuples, each sorted and deduplicated.
        strength: ``strong`` for cross-database evidence, ``weak`` for same-curator siblings,
            ``redundancy`` for name collisions.
        caveat: Why the strength is what it is, printed with every report that uses the source.
    """

    name: str
    pairs: tuple[tuple[str, str], ...]
    strength: str
    caveat: str


def band_of(value: float) -> tuple[float, float]:
    """Which band a Jaccard value falls in.

    Args:
        value: A gene-set Jaccard.

    Returns:
        The band bounds.
    """
    for low, high in BANDS:
        if (low == high == 0.0 and value == 0.0) or (low < value <= high and high > 0):
            return (low, high)
    return BANDS[-1]


def band_label(low: float, high: float) -> str:
    """Render a band for a table.

    Args:
        low: Lower bound.
        high: Upper bound.

    Returns:
        A short label.
    """
    return "exactly 0" if low == high == 0.0 else f"{low:g} < J <= {min(high, 1.0):g}"


def jaccard(a: Pathway, b: Pathway) -> float | None:
    """Gene-set Jaccard, or None when either set is empty and the ratio is undefined.

    Args:
        a: One pathway.
        b: The other.

    Returns:
        The Jaccard, or None. Returning 0.0 for an empty set would be a claim rather than a
        measurement, and would put undefined pairs into the band the product claim rests on.
    """
    if not a.genes or not b.genes:
        return None
    return len(a.genes & b.genes) / len(a.genes | b.genes)


def shares_name(a: Pathway, b: Pathway) -> bool:
    """Whether two pathways carry the same normalised name.

    Args:
        a: One pathway.
        b: The other.

    Returns:
        True when the pair is also a name collision, and so not independent of that test.
    """
    return normalized_name(a) == normalized_name(b)


def _clean(pairs: Iterable[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    """Sort each pair, drop self-pairs, and deduplicate."""
    return tuple(sorted({tuple(sorted(p)) for p in pairs if p[0] != p[1]}))


def collision_pairs(collection: PathwayCollection) -> PairSource:
    """Cross-source name collisions, expanded to pairs.

    Args:
        collection: All pathways.

    Returns:
        The pair source. Only cross-source pairs count: two Reactome pathways sharing a name are a
        curation artefact, not two databases describing one piece of biology.
    """
    pairs = [
        (a.key, b.key)
        for members in collision_groups(collection).values()
        for a, b in combinations(members, 2)
        if a.source != b.source
    ]
    return PairSource(
        "collision",
        _clean(pairs),
        "redundancy",
        "positives are DEFINED by a shared name, so any arm that sees the name scores at ceiling "
        "by construction",
    )


def reactome2go_pairs(lines: Iterable[str]) -> PairSource:
    """Curated Reactome-to-GO mappings.

    Args:
        lines: Lines of the ``reactome2go`` external2go file.

    Returns:
        The pair source, keyed to THEMA's ``source:source_id`` convention.
    """
    pairs = [
        (f"reactome:{m.group(1)}", f"go:{m.group(2)}")
        for line in lines
        if not line.startswith("!") and (m := _MAPPING_LINE.match(line.strip()))
    ]
    return PairSource(
        "reactome2go",
        _clean(pairs),
        "strong",
        "cross-database: Reactome prose judged against GO curation, so nothing in the input told "
        "the model these belong together",
    )


def sibling_pairs(
    parents: Mapping[str, Sequence[str]],
    prefix: str,
    name: str,
    caveat: str,
    max_children: int | None = None,
) -> PairSource:
    """Pairs sharing at least one parent in a hierarchy.

    Args:
        parents: Child to its parents.
        prefix: The key prefix for this source, e.g. ``reactome:``.
        name: The source's label.
        caveat: Why this source is weak evidence.
        max_children: Ignore parents with more than this many children. A broad parent
            manufactures pairs that are not really related -- GO's ``cellular process`` alone
            contributes 66 pairs of near-arbitrary relation -- and about 22% of all sibling pairs
            come from parents with more than ten children. Capping fan-out trades quantity for
            precision; None keeps everything.

    Returns:
        The pair source.
    """
    children: dict[str, list[str]] = {}
    for child, found in parents.items():
        for parent in found:
            children.setdefault(parent, []).append(child)
    pairs = [
        (f"{prefix}{a}", f"{prefix}{b}")
        for group in children.values()
        if max_children is None or len(group) <= max_children
        for a, b in combinations(sorted(group), 2)
    ]
    return PairSource(name, _clean(pairs), "weak", caveat)


def go_parents(terms: Mapping[str, OboTerm]) -> dict[str, tuple[str, ...]]:
    """Child-to-parents over the GO terms, for :func:`sibling_pairs`.

    Args:
        terms: Terms by id.

    Returns:
        Term id to its ``is_a`` parents.
    """
    return {term.term_id: term.parents for term in terms.values() if term.parents}


def restrict(source: PairSource, keys: Iterable[str]) -> PairSource:
    """Keep only the pairs whose members are both present.

    Args:
        source: The pair source.
        keys: The keys available in this run.

    Returns:
        The source with its pairs filtered.
    """
    present = set(keys)
    return PairSource(
        source.name,
        tuple(p for p in source.pairs if p[0] in present and p[1] in present),
        source.strength,
        source.caveat,
    )
