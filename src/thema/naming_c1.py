"""naming-c1: contrastive naming, three candidates, back-match selected.

A port of the reviewer's pilot of 11 Oct 2026, specified in
``data/experiments/naming_pilot_2026-10-11/spec/ALGORITHM.md`` sections 1-5 and implemented there by
``code/np_build.py``, ``code/np_sel.py``, ``code/np_select.py``, ``code/np_dup.py`` and
``code/np_dedupsel.py``. The pilot ran on in-session subagents with no API spend; this module is the
API implementation, and its only job is to produce **the same inputs, the same selection and the
same uniqueness step** so that the two runs differ by the execution route and nothing else.

**Nothing here calls a model.** Everything is deterministic: rendering, seeded shuffles, confusable
choice, back-match item construction, selection and the uniqueness re-ask. The model calls live in
``scripts/name_themes_c1.py``, which goes through the caching client in :mod:`thema.llm` like every
other spend in this project.

**Fidelity before tidiness.** Several things here would be written differently from scratch and are
kept because the pilot's bytes depend on them. Each is marked ``PILOT:`` at the point it matters:
the description-table precedence quirk, one ``random.Random`` shuffling members and then confusables
from the same stream, confusables left unshuffled in the de-duplication round, and the medoid
measured against all nameable candidates while chosen from the correct ones. Changing any of them
silently breaks the reproduction test and nothing else, which is the worst kind of change.

The prompts are **not** in this module. They are the reviewer's two template files, used verbatim as
system prompts, and the runner reads them from disk and records their digests. ``naming.py`` and
name-v5 are untouched: a second naming method sits beside the first rather than editing it.
"""

from __future__ import annotations

import csv
import hashlib
import random
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

#: Size window for a nameable theme (ALGORITHM.md section 1). Larger themes need their own
#: procedure and are out of scope.
MIN_SIZE = 3
MAX_SIZE = 200

#: A theme this large is a bag, not a theme: never a parent and never a confusable.
GIANT = 1000

#: How many confusables an item carries at most.
MAX_CONFUSABLES = 4

#: Stop words dropped before the medoid's token-set Jaccard (ALGORITHM.md section 4).
STOP_WORDS = frozenset(
    {"a", "an", "the", "of", "and", "in", "to", "by", "for", "via", "with", "on", "from", "at"}
)

#: The sentence between a colliding name and the re-ask, appended verbatim as the item's ``note``.
COLLISION_NOTE = (
    "The name '{name}' is already used by another theme; "
    "give a name that distinguishes this theme."
)

#: Candidate-index offset for the uniqueness round, so a re-ask never reuses a first-round seed.
DEDUP_OFFSET = 20

#: What a BTM module with no title is rendered as.
UNTITLED_BTM = "[untitled BTM module] "

#: The centred sidecar the x2 build actually clusters on, and therefore the matrix whose member
#: centroids decide confusables. ``embeddings.npy`` beside it holds the RAW vectors.
CENTRED_VECTORS = "vectors_leaves_centred.npy"

#: The placeholder a BTM module carries instead of a title.
NO_TITLE = "TBA"

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_NOT_ALNUM = re.compile(r"[^a-z0-9 ]")


def seed_int(text: str) -> int:
    """The shuffle seed for a label: the first 8 hex digits of its sha256.

    Args:
        text: The seed label, for example ``n02310:0`` or ``n02310:S1``.

    Returns:
        The seed as an integer.
    """
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


def first_two_sentences(text: str) -> str:
    """The first two sentences of a description.

    Args:
        text: The description.

    Returns:
        The first two sentences, joined by a single space. Shorter text is returned whole.
    """
    return " ".join(_SENTENCE_END.split(text.strip())[:2])


def tokens(text: str) -> set[str]:
    """Lowercased content words of a name, stop words removed.

    Args:
        text: The name.

    Returns:
        The token set the medoid's Jaccard is computed on.
    """
    return {word for word in _WORD.findall(text.lower()) if word not in STOP_WORDS}


def jaccard(left: set[str], right: set[str]) -> float:
    """Jaccard similarity of two token sets, with two empty sets counted identical.

    Args:
        left: One token set.
        right: The other.

    Returns:
        The similarity.
    """
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def normalise_name(name: str) -> str:
    """A name reduced to what a collision is judged on: lowercase, alphanumeric, single spaces.

    Args:
        name: The name.

    Returns:
        The normalised form.
    """
    return " ".join(_NOT_ALNUM.sub(" ", name.lower()).split())


def read_titles(members_tsv: Path) -> dict[str, str]:
    """Pathway titles, read from a build's member table.

    Args:
        members_tsv: A build's ``members.tsv``.

    Returns:
        Pathway key to title.
    """
    with members_tsv.open(encoding="utf-8") as handle:
        return {row["key"]: row["name"] for row in csv.DictReader(handle, delimiter="\t")}


def read_descriptions(descriptions_tsv: Path) -> dict[str, str]:
    """Generated descriptions, under the pilot's own precedence rule.

    PILOT: the reviewer's condition is
    ``if key.startswith('btm:') and status in ('current','ok','',None) or key not in DESC``, which
    Python reads as ``(btm and status_ok) or unseen``. So the first row for any key wins, and a
    later BTM row with an acceptable status overwrites it. Reproduced exactly rather than tidied,
    because the rendered text of every untitled BTM module depends on it.

    Args:
        descriptions_tsv: ``data/pathway_descriptions.tsv``.

    Returns:
        Pathway key to generated description.
    """
    accepted: tuple[str | None, ...] = ("current", "ok", "", None)
    out: dict[str, str] = {}
    with descriptions_tsv.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            key = row["key"]
            if (key.startswith("btm:") and row.get("status", "") in accepted) or key not in out:
                out[key] = row["description_generated"]
    return out


def load_space(directory: Path, pathways: Path) -> tuple[tuple[str, ...], np.ndarray]:
    """Verified row keys, and the centred matrix those keys index.

    The keys come through :func:`thema.ontology.universe.load_embedded`, which recomputes the
    universe from ``pathways.tsv`` and raises if the artifact has drifted -- the check that exists
    because two runs were once calibrated on a superseded universe. The matrix is the **centred
    sidecar**, not the raw ``embeddings.npy`` the loader returns: the centred vectors are what the
    build clusters and therefore what the pilot's member centroids were computed from. Reading the
    keys through the loader keeps the verification while still using the right matrix.

    Args:
        directory: A versioned universe directory.
        pathways: Path to ``pathways.tsv``.

    Returns:
        ``(keys, centred_vectors)``.

    Raises:
        ValueError: If the sidecar has a different number of rows from the verified key list.
    """
    from thema.ontology.universe import load_centred

    return load_centred(directory, pathways)


@dataclass
class Universe:
    """A build, plus the text and geometry naming needs.

    Attributes:
        members: Theme to its member pathway keys.
        parents: Theme to its parents, **giants excluded**, as the pilot's ``par`` is.
        titles: Pathway key to title.
        descriptions: Pathway key to generated description.
        centroids: Theme to its unit-length member centroid, for eligible themes only.
    """

    members: dict[str, set[str]]
    parents: dict[str, set[str]]
    titles: dict[str, str]
    descriptions: dict[str, str]
    centroids: dict[str, np.ndarray] = field(default_factory=dict)
    _children: dict[str, set[str]] = field(default_factory=dict, repr=False)
    _eligible: frozenset[str] = field(default_factory=frozenset, repr=False)

    @classmethod
    def load(
        cls,
        build: Path,
        descriptions_tsv: Path,
        keys: Sequence[str] | None = None,
        vectors: np.ndarray | None = None,
    ) -> Universe:
        """Load a build's tables, and optionally its member geometry.

        Args:
            build: A built ontology directory holding ``nodes.tsv`` and ``members.tsv``.
            descriptions_tsv: ``data/pathway_descriptions.tsv``.
            keys: Embedding row keys, in row order. Omit to skip centroids.
            vectors: The matrix those keys index. Rows are L2-normalised here, as the pilot does.

        Returns:
            The universe.

        Raises:
            ValueError: If keys and vectors disagree on how many rows there are.
        """
        members: dict[str, set[str]] = defaultdict(set)
        with (build / "members.tsv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                members[row["node"]].add(row["key"])
        nodes: dict[str, dict[str, str]] = {}
        with (build / "nodes.tsv").open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                nodes[row["node"]] = row
        giants = {node for node, held in members.items() if len(held) >= GIANT}
        parents = {node: set(row["parents"].split()) - giants for node, row in nodes.items()}
        universe = cls(
            members=dict(members),
            parents=parents,
            titles=read_titles(build / "members.tsv"),
            descriptions=read_descriptions(descriptions_tsv),
        )
        if keys is not None and vectors is not None:
            if len(keys) != vectors.shape[0]:
                raise ValueError(
                    f"{len(keys):,} embedding keys but {vectors.shape[0]:,} rows; the artifact is "
                    "inconsistent with itself"
                )
            universe.add_centroids(keys, vectors)
        universe.index()
        return universe

    def add_centroids(self, keys: Sequence[str], vectors: np.ndarray) -> None:
        """Compute a unit-length member centroid for every eligible theme.

        Rows are L2-normalised first and the centroid normalised after, which is the pilot's order
        and matters: a mean of unnormalised rows weights long vectors more.

        Args:
            keys: Embedding row keys, in row order.
            vectors: The matrix.
        """
        matrix = np.asarray(vectors, dtype=np.float32)
        matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
        row = {key: i for i, key in enumerate(keys)}
        for theme in self.eligible():
            rows = [row[key] for key in self.members[theme] if key in row]
            centre = matrix[rows].mean(0)
            self.centroids[theme] = centre / (np.linalg.norm(centre) + 1e-9)

    def index(self) -> None:
        """Build the child map and the eligible set, both derived from members and parents."""
        children: dict[str, set[str]] = defaultdict(set)
        for node, above in self.parents.items():
            for parent in above:
                children[parent].add(node)
        self._children = dict(children)
        self._eligible = frozenset(
            node for node, keys in self.members.items() if MIN_SIZE <= len(keys) <= MAX_SIZE
        )

    def eligible(self) -> frozenset[str]:
        """Themes inside the size window.

        Returns:
            The eligible theme ids.
        """
        if not self._eligible:
            self.index()
        return self._eligible

    def nested(self, left: str, right: str) -> bool:
        """Whether either theme's members contain the other's.

        Args:
            left: One theme.
            right: The other.

        Returns:
            True if one contains the other, equal sets included.
        """
        mine, theirs = self.members[left], self.members[right]
        return mine <= theirs or theirs <= mine

    def siblings(self, theme: str) -> set[str]:
        """Eligible, non-nested themes sharing at least one non-giant parent.

        Args:
            theme: The theme.

        Returns:
            The sibling set.
        """
        return {
            other
            for parent in self.parents.get(theme, ())
            for other in self._children.get(parent, ())
            if other != theme and other in self.eligible() and not self.nested(other, theme)
        }

    def render(self, key: str) -> str:
        """One member's line, as the prompt sees it.

        Args:
            key: The pathway key.

        Returns:
            Its title, or the untitled-BTM form with the first two sentences of its description.
        """
        title = self.titles[key]
        if title.strip() == NO_TITLE:
            return UNTITLED_BTM + first_two_sentences(self.descriptions.get(key, ""))
        return title

    def confusables(self, theme: str) -> list[str]:
        """Up to four closest confusables: siblings first, then global neighbours.

        ALGORITHM.md section 2c: rank by member-centroid cosine; if fewer than four siblings exist,
        fill from all non-nested eligible themes whose size is within a third and triple of this
        one's.

        Args:
            theme: The theme.

        Returns:
            The confusables, closest first among the siblings, then the fill.

        Raises:
            ValueError: If centroids were never computed.
        """
        if not self.centroids:
            raise ValueError("confusables need member centroids; load the universe with vectors")
        centre = self.centroids[theme]
        chosen = sorted(
            self.siblings(theme), key=lambda other: -float(self.centroids[other] @ centre)
        )[:MAX_CONFUSABLES]
        if len(chosen) < MAX_CONFUSABLES:
            pool = sorted(self.eligible())
            matrix = np.stack([self.centroids[node] for node in pool])
            size = len(self.members[theme])
            for position in np.argsort(-(matrix @ centre)):
                other = pool[position]
                if other == theme or other in chosen or self.nested(other, theme):
                    continue
                if not size / 3 <= len(self.members[other]) <= 3 * size:
                    continue
                chosen.append(other)
                if len(chosen) == MAX_CONFUSABLES:
                    break
        return chosen


def namer_item(
    universe: Universe,
    theme: str,
    candidate_index: int,
    confusables: Sequence[str],
    note: str | None = None,
) -> dict[str, object]:
    """One N1 user message: the theme's full member list and its confusables, both shuffled.

    PILOT: a single ``random.Random`` shuffles the members and then the confusables, drawing from
    one stream, so the two shuffles are not independent and the order of the two calls is part of
    the output. A ``note`` is appended only in the uniqueness round, and then the confusables are
    **not** shuffled -- that is the pilot's ``np_dup.py``, not an oversight here.

    Args:
        universe: The build.
        theme: The theme to name.
        candidate_index: Which of the independent candidates this is; part of the seed.
        confusables: The confusables, in the order they were chosen.
        note: The collision sentence, for a uniqueness re-ask. Omit for a first-round item.

    Returns:
        The item, ready to serialise as the user message.
    """
    rng = random.Random(seed_int(f"{theme}:{candidate_index}"))
    members = [universe.render(key) for key in sorted(universe.members[theme])]
    rng.shuffle(members)
    order = list(confusables)
    if note is None:
        rng.shuffle(order)
    item: dict[str, object] = {
        "theme_id": theme,
        "size": len(universe.members[theme]),
        "members": members,
        "confusables": [
            {
                "confusable": f"C{position + 1}",
                "n_shared": len(universe.members[theme] & universe.members[other]),
                "only_in_theme": sorted(
                    universe.render(key)
                    for key in universe.members[theme] - universe.members[other]
                ),
                "only_in_confusable": sorted(
                    universe.render(key)
                    for key in universe.members[other] - universe.members[theme]
                ),
            }
            for position, other in enumerate(order)
        ],
    }
    if note is not None:
        item["note"] = note
    return item


def backmatch_item(
    universe: Universe,
    theme: str,
    name: str,
    seed_tag: str,
    item_id: str,
    confusables: Sequence[str],
) -> tuple[dict[str, object], str]:
    """One S1 user message, and which letter is the theme itself.

    The theme and its confusables are shuffled into A-E, what all of them share is shown once, and
    each cluster's remainder follows. The returned letter is the answer; it belongs in a key file
    that no judge sees.

    Args:
        universe: The build.
        theme: The theme the name was written for.
        name: The candidate name being tested.
        seed_tag: The seed suffix, ``S<candidate_index>`` for selection.
        item_id: The item's id.
        confusables: The theme's confusables.

    Returns:
        The item, and the letter that is the theme.
    """
    clusters = [theme, *confusables]
    random.Random(seed_int(f"{theme}:{seed_tag}")).shuffle(clusters)
    shared = set.intersection(*(universe.members[node] for node in clusters))
    letters = "ABCDE"[: len(clusters)]
    item = {
        "item_id": item_id,
        "name": name,
        "in_all": sorted(universe.render(key) for key in shared),
        "also_in": {
            letter: sorted(universe.render(key) for key in universe.members[node] - shared)
            for letter, node in zip(letters, clusters, strict=True)
        },
    }
    return item, letters[clusters.index(theme)]


def select(
    candidates: Mapping[int, Mapping[str, object]],
    correct: Mapping[int, bool],
) -> dict[str, object]:
    """Pick one theme's name from its candidates and their back-match verdicts.

    ALGORITHM.md section 4, and a port of ``np_select.select`` for one theme. Two or more refusals
    make the theme unnameable. Otherwise the pool is the candidates that back-matched, or every
    nameable candidate if none did, in which case the theme is flagged ``low_confidence``.

    PILOT: the medoid is **chosen from the pool but scored against every nameable candidate**, so a
    correct candidate can win on agreeing with incorrect ones. Ties go to the lowest candidate
    index. The unnameable branch reports the lowest-index candidate's rationale: the pilot hardcodes
    index 0, which would raise on the re-run arm where indices start at 10, and no theme was ever
    unnameable so the two never differed.

    Args:
        candidates: Candidate index to the model's object for it.
        correct: Candidate index to whether its back-match picked the theme. Missing is False.

    Returns:
        The selection, in the pilot's ``final_names.json`` shape.

    Raises:
        ValueError: If there are no candidates at all.
    """
    if not candidates:
        raise ValueError("no candidates to select from")
    order = sorted(candidates)
    nameable = [index for index in order if candidates[index].get("nameable", True)]
    if len(candidates) - len(nameable) >= 2:
        lowest = candidates[min(candidates)]
        return {"unnameable": True, "rationale": lowest.get("rationale", "")}
    pool = [index for index in nameable if correct.get(index)]
    low_confidence = not pool
    if low_confidence:
        pool = nameable
    token_sets = {index: tokens(str(candidates[index]["name"])) for index in nameable}
    best = min(
        pool,
        key=lambda index: (
            -sum(
                jaccard(token_sets[index], token_sets[other])
                for other in nameable
                if other != index
            ),
            index,
        ),
    )
    return {
        "unnameable": False,
        "name": candidates[best]["name"],
        "cand": best,
        "n_correct": sum(bool(correct.get(index)) for index in nameable),
        "n_nameable": len(nameable),
        "low_confidence": low_confidence,
        "candidates": [candidates[index]["name"] for index in order],
        "correct_flags": [bool(correct.get(index)) for index in order],
    }


def duplicate_names(finals: Mapping[str, Mapping[str, object]]) -> dict[str, int]:
    """Normalised names held by more than one nameable theme.

    Args:
        finals: Theme to its selection.

    Returns:
        Normalised name to how many themes hold it.
    """
    counts: dict[str, int] = defaultdict(int)
    for selection in finals.values():
        if not selection["unnameable"]:
            counts[normalise_name(str(selection["name"]))] += 1
    return {name: count for name, count in counts.items() if count > 1}


def collision_groups(finals: Mapping[str, Mapping[str, object]]) -> list[list[str]]:
    """Themes grouped by the normalised name they collide on.

    Args:
        finals: Theme to its selection.

    Returns:
        One list of theme ids per colliding name, in the order the names were found.
    """
    return [
        [
            theme
            for theme, selection in finals.items()
            if not selection["unnameable"] and normalise_name(str(selection["name"])) == name
        ]
        for name in duplicate_names(finals)
    ]


def dedup_items(
    universe: Universe,
    finals: Mapping[str, Mapping[str, object]],
    confusables: Mapping[str, Sequence[str]],
    candidate_indices: Iterable[int] = (0, 1, 2),
) -> tuple[list[tuple[int, dict[str, object]]], dict[str, list[str]]]:
    """The uniqueness round's N1 items, and the confusable lists they were built against.

    Each colliding theme is re-asked with its rivals promoted to the front of its confusables and
    the collision sentence appended. PILOT: the promoted list replaces the theme's stored
    confusables, which the later back-match then uses, and the confusables are not shuffled.

    Args:
        universe: The build.
        finals: The first round's selections.
        confusables: Theme to its confusables, before the round.
        candidate_indices: Which candidate slots to re-ask. The seed adds
            :data:`DEDUP_OFFSET` to each.

    Returns:
        ``(items, confusables_after)`` where each item is ``(candidate_index, item)`` with the
        candidate index already offset, and ``confusables_after`` is the updated mapping.
    """
    updated = {theme: list(entries) for theme, entries in confusables.items()}
    groups = collision_groups(finals)
    items: list[tuple[int, dict[str, object]]] = []
    for index in candidate_indices:
        for group in groups:
            for theme in group:
                rivals = [other for other in group if other != theme]
                promoted = (
                    rivals + [other for other in updated[theme] if other not in rivals]
                )[:MAX_CONFUSABLES]
                note = COLLISION_NOTE.format(name=finals[theme]["name"])
                items.append(
                    (
                        index + DEDUP_OFFSET,
                        namer_item(
                            universe, theme, index + DEDUP_OFFSET, promoted, note=note
                        ),
                    )
                )
                updated[theme] = promoted
    return items, updated


#: How many uniqueness rounds the algorithm allows before residual collisions are reported
#: (ALGORITHM.md section 5). Residual collisions are never silently suffixed.
MAX_DEDUP_ROUNDS = 2


def apply_uniqueness(
    finals: Mapping[str, Mapping[str, object]],
    candidates: Mapping[str, Mapping[int, Mapping[str, object]]],
    correct: Mapping[str, Mapping[int, bool]],
    round_number: int = 1,
) -> dict[str, dict[str, object]]:
    """Replace the re-asked themes' selections with the uniqueness round's result.

    The re-selected entry carries ``dedup_round`` so a name that came out of a re-ask is never
    mistaken for a first-round name. The pilot's ``final_names.json`` records the same field.

    Args:
        finals: The previous round's selections, for every theme.
        candidates: Re-asked theme to candidate index to the model's object.
        correct: Re-asked theme to candidate index to whether its back-match picked the theme.
        round_number: Which uniqueness round this is, counting from 1.

    Returns:
        A new mapping with the re-asked themes replaced.
    """
    out = {theme: dict(selection) for theme, selection in finals.items()}
    for theme, by_index in candidates.items():
        chosen = select(by_index, correct.get(theme, {}))
        chosen["dedup_round"] = round_number
        out[theme] = chosen
    return out
