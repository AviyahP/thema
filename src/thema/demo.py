"""Turn the built ontology into the object ``demo/prototype.html`` renders.

The page is the contract, not this module: ``THEMES`` and ``TREE`` in the prototype were written
by hand as illustrative examples, and everything here exists to produce the same two shapes from
real data so the page can be pointed at a file instead of at a literal.

Two rules govern the output and are enforced here rather than left to the page.

**Nothing is invented.** Every field the ontology cannot supply carries :data:`NOT_COMPUTED`, which
the page renders verbatim. Enrichment, soft membership and the attribution tests are not built yet,
so their fields say so. A plausible-looking number in one of those slots would be indistinguishable
from a real one to any reader, which is the whole reason for the constant.

**Labels are provisional and say so.** No theme has been named. The label a node carries is the
most distinctive vocabulary of its members' names, joined by a separator no curator would write, so
it reads as machine output at a glance. The nearest member to the cluster centre is carried
alongside it, because a real pathway name is a better anchor than three keywords and it costs
nothing to compute.
"""

import math
import re
from collections.abc import Iterable, Mapping, Sequence

import numpy as np

#: What every field goes into when nothing has computed it. The page renders this string as-is.
NOT_COMPUTED = "not computed"

#: What a single cell of a table goes into when nothing has computed it, where the full phrase
#: would not fit and the column header already carries the meaning.
NOT_COMPUTED_CELL = "—"

#: Direction marker for a node whose enrichment has not been computed. The prototype knows
#: ``up``/``down``/``none``/``flag``; ``none`` means *tested and not significant*, which would be a
#: claim, so not-computed needs its own value.
NO_DIRECTION = "na"

#: Separator between the terms of a provisional label. Deliberately not a word: a label that reads
#: like prose invites being mistaken for a curated name.
LABEL_SEPARATOR = " · "

#: Structural words carried by pathway names in every source. Inverse document frequency already
#: demotes the common biological vocabulary; this list only removes words that carry no topic at
#: all, so that the scoring is not spent on them.
STOPWORDS = frozenset(
    """
    a an and as at by for from in into of on or the to via with within without
    hsa homo sapiens human
    tba
    """.split()
)

_TOKEN = re.compile(r"[a-z][a-z0-9]{2,}")


def tokenize(name: str) -> set[str]:
    """Split a pathway name into the distinct terms it contributes.

    Args:
        name: A pathway name as its source publishes it.

    Returns:
        The distinct lowercase terms of three or more characters, minus :data:`STOPWORDS`.
    """
    return {t for t in _TOKEN.findall(name.lower()) if t not in STOPWORDS}


def document_frequency(names: Iterable[str]) -> dict[str, int]:
    """Count how many names each term appears in.

    Args:
        names: Every pathway name in the ontology.

    Returns:
        Term to the number of names containing it.
    """
    counts: dict[str, int] = {}
    for name in names:
        for term in tokenize(name):
            counts[term] = counts.get(term, 0) + 1
    return counts


def distinctive_terms(
    members: Sequence[str],
    background: Mapping[str, int],
    total: int,
    limit: int = 3,
    floor: float = 0.15,
) -> tuple[str, ...]:
    """Rank a cluster's member names by what they say that other clusters' names do not.

    The score is the ordinary product of within-cluster frequency and inverse document frequency.
    The first factor is what keeps a term that one member happens to carry -- a gene symbol, a
    disease -- from winning on rarity alone; ``floor`` makes that explicit rather than relying on
    the arithmetic to be kind.

    Args:
        members: The names of the pathways in this cluster.
        background: Document frequency over every name in the ontology.
        total: How many names the background was counted over.
        limit: How many terms to return.
        floor: The smallest share of members a term may appear in and still be considered.

    Returns:
        Up to ``limit`` terms, most distinctive first. Empty when no term clears ``floor``.
    """
    if not members:
        return ()
    within: dict[str, int] = {}
    for name in members:
        for term in tokenize(name):
            within[term] = within.get(term, 0) + 1

    scored: list[tuple[float, str]] = []
    for term, count in within.items():
        share = count / len(members)
        if share < floor:
            continue
        idf = math.log(total / max(background.get(term, 1), 1))
        scored.append((share * idf, term))
    # Ties broken on the term itself so the label does not depend on dict ordering.
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return tuple(term for _score, term in scored[:limit])


def provisional_label(
    members: Sequence[str], background: Mapping[str, int], total: int, limit: int = 3
) -> str:
    """Build the temporary label a node carries until the namer has run.

    Args:
        members: The names of the pathways in this cluster.
        background: Document frequency over every name in the ontology.
        total: How many names the background was counted over.
        limit: How many terms the label may hold.

    Returns:
        The distinctive terms joined by :data:`LABEL_SEPARATOR`, or ``unlabelled`` when the members
        share no vocabulary at all.
    """
    terms = distinctive_terms(members, background, total, limit=limit)
    return LABEL_SEPARATOR.join(terms) if terms else "unlabelled"


def medoid(rows: Sequence[int], vectors: np.ndarray) -> int:
    """Find the member sitting nearest the centre of its cluster.

    Args:
        rows: Row indices into ``vectors`` for this cluster's members.
        vectors: The unit-length description embeddings, in ownership order.

    Returns:
        The row index of the member closest to the cluster mean.

    Raises:
        ValueError: If the cluster is empty.
    """
    if not rows:
        raise ValueError("a cluster with no members has no medoid")
    block = vectors[list(rows)]
    centre = block.mean(axis=0)
    norm = float(np.linalg.norm(centre))
    if norm > 0:
        centre = centre / norm
    return int(rows[int(np.argmax(block @ centre))])


def source_spread(sources: Iterable[str]) -> list[tuple[str, int]]:
    """Count the members each source contributed, commonest first.

    Args:
        sources: One source name per member.

    Returns:
        Source and count, ordered by count descending then name.
    """
    counts: dict[str, int] = {}
    for source in sources:
        counts[source] = counts.get(source, 0) + 1
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))


def uncomputed_tests() -> list[list[object]]:
    """Render the three attribution tests in their not-yet-built state.

    The prototype shows BASIS, CHILD-UNIQUE and PARENT-BEYOND per theme. None of the three is
    implemented, so all three are shown saying exactly that: an absent section would read as a
    theme that happened to have nothing to report.

    Returns:
        Three rows in the page's ``[name, question, value, carried]`` shape.
    """
    return [
        ["BASIS", "all genes in the theme", NOT_COMPUTED, False],
        ["CHILD-UNIQUE", "genes in no sibling theme", NOT_COMPUTED, False],
        ["PARENT-BEYOND", "genes only in non-significant children", NOT_COMPUTED, False],
    ]
