"""The ontology builder interface, and the invariants every builder's output must satisfy.

The way THEMA's hierarchy is built is a parameter. Two methods ship -- ``ward_tree``, one parent per
node, and ``recurrent_dag``, several parents allowed -- behind one interface and one output
contract, so the demo can load either and a reader can compare them without holding two mental
models (``docs/spec/thema-master-spec.md`` §6-§8).

**The invariants fail the build, they never warn.** A tree whose edges disagree with its membership,
or a pathway in no node and not recorded as unplaced, looks exactly like a correct ontology from the
outside. Everything downstream -- the demo, the statistics, the evaluation -- reads this structure
and cannot tell. So it is checked here, once, and a violation raises.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np

#: A member of a node: the pathway key, and how much of the node's evidence includes it. Always 1.0
#: under ``ward_tree``; between ``inclusion_threshold`` and 1.0 under ``recurrent_dag``.
Member = tuple[str, float]


@dataclass(frozen=True, slots=True)
class Node:
    """One grouping in an ontology.

    Attributes:
        id: Stable within a build. ``k<cut>:<cluster>`` under ``ward_tree``; ``n<NNNN>`` under
            ``recurrent_dag``, where ids are generated and carry no meaning across builds.
        parents: Node ids containing this one, as the Hasse diagram gives them. Empty for a root,
            and there may be several roots -- no synthetic "all themes" node is ever added
            (addendum A3).
        members: ``(key, inclusion)`` pairs.
        support: How often the grouping recurred across resampled runs, in ``[0, 1]``. Always 1.0
            under ``ward_tree``, where there is no resampling to recur across.
    """

    id: str
    parents: tuple[str, ...]
    members: tuple[Member, ...]
    support: float

    @property
    def keys(self) -> frozenset[str]:
        """The member pathway keys, without their inclusions."""
        return frozenset(key for key, _inclusion in self.members)

    @property
    def settled(self) -> frozenset[str]:
        """The members every copy of this grouping agreed on -- ``inclusion == 1``.

        The evaluation's gene-overlap check compares contested members against these, so the
        distinction is part of the contract rather than a detail of one method.
        """
        return frozenset(key for key, inclusion in self.members if inclusion >= 1.0)


@dataclass(frozen=True, slots=True)
class Ontology:
    """A built hierarchy, method-independent.

    Attributes:
        method: Which builder produced it.
        params: Every parameter the build used, frozen. What makes a build reproducible rather
            than merely repeatable.
        nodes: The groupings.
        unplaced: Pathway keys in no node. Reported, never hidden: a pathway THEMA cannot place is
            a fact about the method, and the demo lists them under their own heading.
        manifest: Provenance -- embedder and revision, prompt version, input digests, seeds, date.
    """

    method: str
    params: dict[str, object]
    nodes: tuple[Node, ...]
    unplaced: tuple[str, ...]
    manifest: dict[str, object] = field(default_factory=dict)

    @property
    def by_id(self) -> dict[str, Node]:
        """Nodes by id."""
        return {node.id: node for node in self.nodes}

    @property
    def roots(self) -> tuple[Node, ...]:
        """Nodes with no parent. A forest, not a single tree."""
        return tuple(node for node in self.nodes if not node.parents)

    @property
    def edges(self) -> tuple[tuple[str, str], ...]:
        """``(child, parent)`` pairs."""
        return tuple(
            (node.id, parent) for node in self.nodes for parent in node.parents
        )


@runtime_checkable
class OntologyBuilder(Protocol):
    """What a builder must provide.

    The embedding matrix arrives as an argument rather than being loaded here, which is what keeps
    every builder testable on synthetic vectors with no model download -- and keeps
    ``sentence_transformers`` confined to ``thema.embed``, as ``tests/test_cluster.py`` asserts.
    """

    method: str

    def build(
        self, x: np.ndarray, keys: Sequence[str], params: dict[str, object], seed: int
    ) -> Ontology:
        """Build an ontology from unit-length embeddings.

        Args:
            x: An ``(n, dim)`` array of L2-normalised vectors.
            keys: The pathway key for each row, in row order.
            params: Method parameters; a builder fills its own defaults for anything absent.
            seed: Master seed. Any derived seeds are recorded in ``Ontology.params``.

        Returns:
            The built ontology, already satisfying :func:`check_invariants`.
        """
        ...


def check_invariants(ontology: Ontology, keys: Sequence[str], min_size: int | None) -> None:
    """Refuse an ontology that is internally inconsistent (spec §7.3).

    Containment is NON-strict here, and deliberately: a cut that does not split its parent gives a
    child with identical membership, which is a true fact about that tree and is what §9.4 means by
    "the node at the previous level that contains it". ``recurrent_dag`` forbids equal member sets
    instead -- it merges them (§10.7) -- so that rule lives in :func:`check_distinct_members`, to be
    applied by the method that wants it.

    Args:
        ontology: The built ontology.
        keys: Every pathway key the build was given.
        min_size: The smallest permitted node, or None when the method does not apply one
            (``ward_tree`` takes whatever a cut gives).

    Raises:
        ValueError: On the first violation found, naming it. Each of these would otherwise produce
            a structure that reads as correct everywhere downstream.
    """
    by_id = ontology.by_id
    if len(by_id) != len(ontology.nodes):
        raise ValueError("duplicate node ids")

    for node in ontology.nodes:
        if not node.members:
            raise ValueError(f"{node.id} has no members")
        if len({k for k, _ in node.members}) != len(node.members):
            raise ValueError(f"{node.id} lists a member twice")
        if min_size is not None and len(node.members) < min_size:
            raise ValueError(
                f"{node.id} has {len(node.members)} members, below min_size {min_size}"
            )
        for parent in node.parents:
            if parent not in by_id:
                raise ValueError(f"{node.id} names a parent that does not exist: {parent}")
            if not node.keys <= by_id[parent].keys:
                raise ValueError(f"members({node.id}) are not contained in members({parent})")

    _check_acyclic(ontology)

    placed = {key for node in ontology.nodes for key in node.keys}
    unplaced = set(ontology.unplaced)
    if placed & unplaced:
        raise ValueError(
            f"{len(placed & unplaced)} pathway(s) are both placed and listed unplaced"
        )
    missing = set(keys) - placed - unplaced
    if missing:
        raise ValueError(
            f"{len(missing)} pathway(s) in no node and not recorded as unplaced, e.g. "
            f"{sorted(missing)[:3]}"
        )
    stray = placed - set(keys)
    if stray:
        raise ValueError(f"node(s) hold {len(stray)} key(s) that were never given to the build")


def check_distinct_members(ontology: Ontology) -> None:
    """Refuse two nodes with identical member sets.

    ``recurrent_dag`` merges equal groupings rather than keeping both (§10.7), so a duplicate here
    means the merge did not happen. Not applied to ``ward_tree``, where a level that fails to split
    legitimately repeats its parent's membership.

    Args:
        ontology: The built ontology.

    Raises:
        ValueError: If any member set appears on more than one node.
    """
    seen: dict[frozenset[str], str] = {}
    for node in ontology.nodes:
        first = seen.setdefault(node.keys, node.id)
        if first != node.id:
            raise ValueError(
                f"{node.id} and {first} have identical members; equal groupings are merged"
            )


def check_single_parent(ontology: Ontology) -> None:
    """Refuse a ``ward_tree`` output that is not a forest of single-parent nodes.

    Addendum A3 removed the synthetic root, so the condition is "at most one parent" rather than
    the spec's original "exactly one parent or the single root".

    Args:
        ontology: The built ontology.

    Raises:
        ValueError: If any node has more than one parent.
    """
    many = [node.id for node in ontology.nodes if len(node.parents) > 1]
    if many:
        raise ValueError(f"{ontology.method} must be a forest; {len(many)} node(s) have >1 parent")


def _check_acyclic(ontology: Ontology) -> None:
    """Assert the edge relation is a DAG.

    Containment makes cycles impossible by construction, which is exactly why this is asserted
    rather than assumed: if one ever appears, the containment computation is wrong.

    Raises:
        ValueError: If a cycle is reachable from any node.
    """
    by_id = ontology.by_id
    state: dict[str, int] = {}

    def visit(node_id: str, trail: list[str]) -> None:
        if state.get(node_id) == 2:
            return
        if state.get(node_id) == 1:
            cycle = " -> ".join([*trail[trail.index(node_id) :], node_id])
            raise ValueError(f"cycle in the edge relation: {cycle}")
        state[node_id] = 1
        for parent in by_id[node_id].parents:
            visit(parent, [*trail, node_id])
        state[node_id] = 2

    for node in ontology.nodes:
        visit(node.id, [])
