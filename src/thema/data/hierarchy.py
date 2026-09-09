"""The two source hierarchies THEMA reads but does not build: Reactome's tree and GO:BP's is_a DAG.

Both are *upward* walks -- given a node, which top-level branch does it sit under? -- which is the
question a stratified sample asks and which nothing in the repo answered before. ``formats.py``
already carries GO's ``is_a`` edges on :class:`~thema.data.formats.OboTerm`, and
``scripts/filter_reactome_membership.py`` already walks Reactome *downward* from one root to find
the infectious-disease subtree; neither goes up, and neither is reusable.

Kept here rather than in a script because the reference-hierarchy evaluation (``docs/eval-plan.md``
2a) needs exactly these walks, and because a stratifier that silently mis-assigns is a bug nobody
sees. Pure stdlib: no network, no model, no ``data/raw/`` dependency in the tests.

Neither hierarchy is a tree. 33 human Reactome pathways reach two top-level roots, and 1,630 of the
7,538 GO:BP terms THEMA loads reach two or more level-1 branches, so every caller must decide what
a multi-branch node means rather than assume a unique answer. These functions return the full set
and leave that decision to the caller.
"""

from collections.abc import Iterable, Mapping, Sequence

from thema.data.formats import OboTerm

#: Reactome's human identifier prefix. ``ReactomePathwaysRelation.txt`` carries all sixteen species
#: it publishes, and human is a minority of its 23,717 lines, so both endpoints must be filtered.
HUMAN_PREFIX = "R-HSA-"

#: The root of GO's Biological Process ontology. THEMA loads BP only (DECISIONS, 2026-08-21).
GO_BP_ROOT = "GO:0008150"


def read_reactome_relation(lines: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Read the human parent-child edges as a child-to-parents mapping.

    The file has no header and two tab-separated columns, ``parent<TAB>child``, one edge per line.
    Both endpoints are filtered to human: a pathway whose parent is bovine is not a human root, and
    keeping the edge would invent one.

    Args:
        lines: Lines of ``ReactomePathwaysRelation.txt``.

    Returns:
        Child stable id to the parents that claim it, in file order.
    """
    parents: dict[str, list[str]] = {}
    for line in lines:
        parent, _, child = line.rstrip("\n").partition("\t")
        if not parent.startswith(HUMAN_PREFIX) or not child.startswith(HUMAN_PREFIX):
            continue
        parents.setdefault(child, []).append(parent)
        parents.setdefault(parent, [])
    return {child: tuple(found) for child, found in parents.items()}


def reactome_roots(parents: Mapping[str, Sequence[str]]) -> frozenset[str]:
    """Find the top-level branches: the nodes no edge claims as a child.

    Args:
        parents: The mapping :func:`read_reactome_relation` returns.

    Returns:
        The root stable ids. There are 29 in the pinned release.
    """
    return frozenset(node for node, found in parents.items() if not found)


def reactome_branches_of(
    source_id: str, parents: Mapping[str, Sequence[str]], roots: frozenset[str]
) -> frozenset[str]:
    """Walk upward from a pathway to every top-level branch above it.

    Args:
        source_id: The pathway's Reactome stable id.
        parents: The mapping :func:`read_reactome_relation` returns.
        roots: The roots :func:`reactome_roots` found.

    Returns:
        Every root reachable by following parents. Usually one; 33 human pathways reach two.
    """
    seen: set[str] = set()
    reached: set[str] = set()
    stack = [source_id]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        if node in roots:
            reached.add(node)
            continue
        stack.extend(parents.get(node, ()))
    return frozenset(reached)


def go_level1_branches(terms: Mapping[str, OboTerm], root: str = GO_BP_ROOT) -> frozenset[str]:
    """Find the ontology's level-1 branches: the direct ``is_a`` children of its root.

    Args:
        terms: Terms by id, from :func:`~thema.data.formats.parse_obo_terms`.
        root: The ontology root. Defaults to Biological Process.

    Returns:
        The branch term ids. This release has 18, all of them represented among THEMA's 7,538 sets.
    """
    return frozenset(
        term.term_id for term in terms.values() if root in term.parents and term.term_id != root
    )


def go_ancestors(term_id: str, terms: Mapping[str, OboTerm]) -> frozenset[str]:
    """Collect a term and EVERY ancestor above it, at every level.

    Accumulation is inclusive and total: each node visited is added, not only the nodes that turn
    out to be terminal. This is the whole point of the function, and getting it wrong fails
    silently. A walk that returns only terminal roots intersects the level-1 branch set emptily --
    every path from a real term ends at ``GO:0008150`` itself, never at one of its children -- so a
    stratifier built on it would collapse all 7,538 GO terms into a single bucket and produce
    exactly the homogeneous sample that stratifying exists to prevent, while reporting no error.

    Args:
        term_id: The term to walk up from.
        terms: Terms by id, from :func:`~thema.data.formats.parse_obo_terms`.

    Returns:
        The term itself and all of its ancestors. Obsolete terms have no ``is_a`` edges at all --
        GO strips them -- so an obsolete term returns just itself and reaches no branch.
    """
    seen: set[str] = set()
    stack = [term_id]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        term = terms.get(node)
        if term is not None:
            stack.extend(term.parents)
    return frozenset(seen)
