"""``ward_tree`` -- the existing build, expressed through the builder interface.

This is a re-export, not a new method. Its numbers must not move: the done-condition is that the
member sets it produces at every level are identical to ``data/ontology/clusters_ward.tsv``, which
is committed and is what the demo and every evaluation have been reading. Anything here that
changed a member set would silently invalidate every measurement taken on the v0.1 ontology.

Two things differ from the spec's §9 as written, both by later decision:

- **No synthetic root** (addendum A3). §9.4 gave nodes at the first level a parent called ``root``
  holding every pathway. There is none: the k=10 clusters are the roots, a forest, exactly as
  ``recurrent_dag`` produces. The detail card's "the ontology" summary is a view, not a node.
- **No softening.** ``inclusion`` and ``support`` are 1.0 for every member of every node. A softened
  variant is deliberately not in v1 so the method toggle compares one idea against one idea.
"""

from collections.abc import Sequence

import numpy as np

from thema.cluster import DEFAULT_CUTS, cut, distances, trees
from thema.ontology.base import Node, Ontology, check_invariants, check_single_parent


class WardTree:
    """Ward linkage on L2-normalised embeddings, cut at declared levels.

    Every cluster at every cut is a node. A node's parent is the cluster containing it at the
    previous cut, which is unique because cuts of one dendrogram nest.
    """

    method = "ward_tree"

    def build(
        self,
        x: np.ndarray,
        keys: Sequence[str],
        params: dict[str, object] | None = None,
        seed: int = 0,
    ) -> Ontology:
        """Build the tree.

        Args:
            x: An ``(n, dim)`` array of unit vectors. ``distances`` re-checks that rather than
                trusting it: Ward on unnormalised vectors clusters partly by magnitude, which tracks
                text length, and fails silently.
            keys: The pathway key per row, in row order.
            params: ``{"levels": [...]}``; defaults to :data:`thema.cluster.DEFAULT_CUTS`. Levels
                are sorted coarsest-first and any at or above ``n`` are dropped, since a cut cannot
                ask for more clusters than there are observations.
            seed: Unused -- Ward is deterministic. Accepted so the interface is uniform, and
                recorded in ``params`` so a manifest reader can see it had no effect.

        Returns:
            The ontology. ``unplaced`` is always empty: every pathway is in a cluster at every cut.

        Raises:
            ValueError: If no requested level is usable, or if the result violates an invariant.
        """
        settings = dict(params or {})
        requested = [int(k) for k in settings.get("levels", DEFAULT_CUTS)]  # type: ignore[arg-type]
        levels = sorted({k for k in requested if 1 <= k < len(keys)})
        if not levels:
            raise ValueError(
                f"no usable level in {requested} for {len(keys)} pathways; "
                "a cut cannot ask for more clusters than there are observations"
            )

        tree = trees(distances(x), ("ward",))["ward"]
        labels = {k: cut(tree, k) for k in levels}

        # Members per node, and the parent of each node: the cluster containing it one level up.
        members: dict[str, list[str]] = {}
        parent: dict[str, str] = {}
        for index, key in enumerate(keys):
            for depth, level in enumerate(levels):
                node_id = f"k{level}:{labels[level][index]}"
                members.setdefault(node_id, []).append(key)
                if depth:
                    above = levels[depth - 1]
                    parent[node_id] = f"k{above}:{labels[above][index]}"

        nodes = tuple(
            Node(
                id=node_id,
                parents=(parent[node_id],) if node_id in parent else (),
                members=tuple((key, 1.0) for key in sorted(member_keys)),
                support=1.0,
            )
            for node_id, member_keys in sorted(members.items())
        )

        ontology = Ontology(
            method=self.method,
            params={
                "levels": levels,
                "seed": seed,
                "seed_effective": False,
                # Recorded rather than applied: this method's clusters are whatever the cut gives.
                "min_size": None,
            },
            nodes=nodes,
            unplaced=(),
        )
        check_invariants(ontology, keys, min_size=None)
        check_single_parent(ontology)
        return ontology
