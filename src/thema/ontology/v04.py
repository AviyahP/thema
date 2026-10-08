"""THEMA v0.4 -- the simple version of A, with only the stages that earned their place.

A theme is a group of pathways that stays together across 80% subsamples more often than chance
allows; themes are stacked by containment. That is the whole method. Three knobs: the sample
fraction (0.8), one match threshold (``THETA`` = 0.70) used for both recurrence and merging, and
per-size support floors calibrated once against scrambles and then stored.

v0.3 had seven stages. The ablation of 8 Oct 2026 switched each off in turn and kept a stage only
where removing it worsened a curated cell beyond a 2-point margin with a paired CI excluding zero,
pushed held-out FDR over the declared caps, or dropped between-half stability by more than 2
points. Four stages failed that test and are **absent here**, not switchable:

=========================  ========================================================================
removed stage              what the ablation measured
=========================  ========================================================================
size cap (29.0133%)        FDR 0.00237 against the baseline's 0.00241, stability 0.853 against
                           0.855, no curated cell worse. It removed about two candidates per tree.
TOL extras-only rule       Already inert in the frozen build: ``TOL`` is read only on the
                           ``theta is None`` branch, which no build takes. The ablation confirmed
                           it rather than discovering it.
STRAY (0.10)               FDR 0.00241 -- identical to the baseline -- stability 0.854, no cell
                           worse. Consensus inherits nothing and loses nothing.
partial containment >=0.9  Identical to the baseline on all four statistics, which is what
                           "report-only" was always meant to mean.
=========================  ========================================================================

The three that remain are each individually load-bearing, and each docstring below states the
number that forced it. :data:`STAGES` carries the same justifications as data so a report can print
them without reading this file.

**The byte-identity contract.** :func:`material` and :func:`build` take ``legacy``, and with
``legacy=True`` every removed stage is restored. That mode exists for one purpose: proving this
file reproduces the frozen v0.3 build exactly, so that any later difference is the removal of a
stage and never a reimplementation. ``tests/ontology/test_v04.py`` asserts the parameters match
v0.3's, and ``scripts/v04_run.py --all-stages-on --verify`` asserts the built directory matches
``data/ontology/v0.3/recurrent_dag_10770`` file by file.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

from thema.ontology import bitset as bits
from thema.ontology.consensus import DEFAULT_JACCARD, consensus
from thema.ontology.recurrent import (
    DEFAULTS,
    families,
    family_members_fast,
    family_support,
    hasse,
    prepare,
    score,
)

#: Match threshold, for recurrence and for merging alike. One knob, used twice.
THETA = 0.70
#: Smallest theme. Two pathways are a pair, not a theme.
MIN_SIZE = 3
#: A completed member must appear in at least half the copies that could have held it.
INCLUSION_CUT = 0.50
#: Subsample fraction per run.
SUBSAMPLE = 0.8
#: Size strata the floors are solved over. The last is open-ended.
STRATA: tuple[tuple[int, int], ...] = ((3, 3), (4, 4), (5, 5), (6, 6), (7, 9), (10, 10**9))
#: Overall and per-stratum false discovery caps the floors are solved to.
MAX_FDR_OVERALL = 0.01
MAX_FDR_STRATUM = 0.02
#: v0.3's extras-only tolerance, carried only so ``legacy`` can reproduce the frozen settings.
LEGACY_TOL = 0.15
#: v0.3's stray share, likewise.
LEGACY_STRAY = 0.10
#: v0.3's size cap as a share of the universe, likewise, at the full precision the frozen build
#: recorded. Truncating it to 0.290133 and taking ``int`` rather than ``round`` gives 3,124 where
#: v0.3 used 3,125 -- a one-pathway difference that would have broken byte identity.
#: Written as the same exact rational the frozen build uses rather than as a decimal literal, so
#: it cannot drift. See ``scripts/size_cap_reference.py`` for what it is measured against.
LEGACY_CAP_SHARE = 2 * 469 / 3233
#: Stand-in cap meaning "no cap", large enough that no grouping is ever refused for size.
NO_CAP = 10**9


#: ``(size, support)`` rows, the form the floor solver takes.
Rows = Sequence[tuple[int, float]]
#: Solves one floor per stratum from the real side and the calibration scrambles.
Solver = Callable[[Rows, Sequence[Rows]], list[dict]]
#: Applies solved floors to held-out scrambles, once.
Checker = Callable[[Rows, Sequence[Rows], Sequence[dict]], dict]


class Stage(NamedTuple):
    """One pipeline stage and why it is here.

    Attributes:
        name: Short stage name.
        why: The ablation number that forced it, in one line.
    """

    name: str
    why: str


#: The three kept stages, with the measurement that forced each. Printed by the report.
STAGES: tuple[Stage, ...] = (
    Stage("completion",
          "removing it drops between-half stability to 0.713 from 0.855 and worsens two curated "
          "cells; its better FDR (0.00196) arrives with 1.9x the themes, which the rule flags "
          "rather than credits"),
    Stage("greedy seed absorption",
          "removing it doubles held-out FDR to 0.00482 from 0.00241 and worsens two curated cells"),
    Stage("per-size support floors",
          "a single floor fails on four counts at once: held-out FDR 0.01013 over the 0.01 cap, "
          "worst stratum 0.0500 over the 0.02 cap, stability 0.793, four cells worse"),
)


def cap_for(n: int) -> int:
    """v0.3's size cap in pathways, for ``legacy`` reproduction only.

    Args:
        n: Universe size.

    Returns:
        The cap in pathways.
    """
    return round(LEGACY_CAP_SHARE * n)


def stratum_of(size: int) -> int:
    """Index of the stratum a theme of this size falls in.

    Args:
        size: Theme size in pathways.

    Returns:
        Index into :data:`STRATA`, or -1 below the smallest stratum.
    """
    for index, (low, high) in enumerate(STRATA):
        if low <= size <= high:
            return index
    return -1


@dataclass(frozen=True, slots=True)
class Material:
    """The gate's input: one bitset, one support score and one inclusion vote per candidate.

    ``selections`` is what completion produced: per candidate, the share of eligible copies each
    member appeared in. It is not optional decoration -- v0.3 writes it to ``members.tsv`` as the
    ``inclusion`` column, and a pipeline that drops it and writes 1.0 everywhere differs from the
    frozen build on 40,501 of 98,599 member rows while every node, edge and unplaced row still
    matches. That is exactly how this was found.

    It may be empty when the material was loaded from a cache that stored only blocks and
    supports. That is enough to solve floors, which read only ``(size, support)``, and
    :func:`build` refuses it.

    Attributes:
        blocks: Packed membership, one row per candidate.
        supports: Recurrence support, aligned with ``blocks``.
        selections: Per candidate, ``{pathway index: inclusion}``; may be empty.
        pool: Size of the grouping pool the candidates were drawn from.
    """

    blocks: np.ndarray
    supports: np.ndarray
    selections: tuple[dict[int, float], ...] = ()
    pool: int = -1

    def rows(self) -> list[tuple[int, float]]:
        """``(size, support)`` per candidate, the form the floor solver takes.

        Returns:
            One row per candidate.
        """
        sizes = np.bitwise_count(self.blocks).sum(axis=1).astype(np.int64)
        return list(zip(sizes.tolist(),
                        [round(float(s), 6) for s in self.supports], strict=True))


def settings_for(runs: int, *, legacy: bool = False) -> dict[str, object]:
    """Matching settings for one side.

    Args:
        runs: Number of runs on this side.
        legacy: Restore v0.3's inert ``TOL`` so the frozen build can be reproduced.

    Returns:
        A settings mapping for :func:`~thema.ontology.recurrent.prepare`.
    """
    return {**DEFAULTS, "runs": runs, "min_size": MIN_SIZE, "theta": THETA,
            "families": "joined", "tol": LEGACY_TOL if legacy else 0.0}


def material(runs: Sequence[object], n: int, *, legacy: bool = False) -> Material:
    """Match, complete and absorb: everything the gate needs, for one side.

    The stage order is v0.3's and is the one thing in this pipeline that must not be rearranged.
    Completion runs **first**, over every surviving grouping, and the ``MIN_SIZE`` filter applies
    to the completed membership; absorption then runs over the completed bitsets. Absorbing first
    and completing afterwards inflates families by 60% (259,924 against 161,852) and was the single
    real bug in the v0.4 work.

    The size cap is **not** a parameter here. v0.3 applied it when cutting each tree, so it
    arrives already applied -- or already absent -- in ``runs``. A caller reproducing v0.3 must
    pass runs cut at :func:`cap_for`; v0.4 passes uncapped runs. ``legacy`` therefore cannot
    restore the cap on its own, and :func:`parameters` records which was used.

    Args:
        runs: Loaded per-run records, in run order, cut with or without the cap.
        n: Universe size.
        legacy: Restore v0.3's inert ``TOL``.

    Returns:
        The gate's input.
    """
    conf = settings_for(len(runs), legacy=legacy)
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, conf, 0, records=list(runs))
    pool = score(ready, conf)
    words = ready.present.shape[1] * bits.WORD

    # STAGE 1: completion. A family's membership is the union of its matched copies, keeping only
    # pathways present in at least INCLUSION_CUT of the copies that could have held them.
    completed: dict[int, np.ndarray] = {}
    votes: dict[int, dict[int, float]] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members_fast([grouping], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(candidate)
                         if inclusion.get(p, 0.0) >= INCLUSION_CUT)
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)
            votes[grouping] = inclusion

    # STAGE 2: greedy seed absorption at THETA, over the completed bitsets.
    grouped = families(list(completed), completed, pool, None, conf)

    blocks, supports, selections = [], [], []
    for seed, family in grouped:
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        blocks.append(completed[seed])
        supports.append(float(support))
        selections.append(votes[seed])
    return Material(
        blocks=np.vstack(blocks) if blocks
        else np.zeros((0, ready.present.shape[1]), np.uint64),
        supports=np.array(supports, dtype=np.float64),
        selections=tuple(selections),
        pool=int(len(pool.groupings)))


def calibrate(
    real: Material,
    scrambles: Sequence[Material],
    heldout: Sequence[Material],
    solver: Solver,
    checker: Checker,
) -> dict:
    """STAGE 3: solve the per-size floors once, then confirm them once on held-out scrambles.

    Calibration is a one-time cost per configuration, which is why the result is stored rather
    than recomputed: the floors are a property of the space and the universe, not of a build.
    ``heldout`` is read exactly once, by ``checker``, and never fitted against -- a held-out set
    confirmed against more than once is not held out.

    The solver and checker are injected rather than imported so that this module never depends on
    ``scripts/``; ``scripts/v04_run.py`` supplies ``build_10770.solve`` and ``build_10770.confirm``.

    Args:
        real: The real side.
        scrambles: Calibration scramble sides.
        heldout: Held-out scramble sides, read once.
        solver: Solves one floor per stratum to :data:`MAX_FDR_OVERALL`.
        checker: Applies solved floors to held-out sides.

    Returns:
        ``solved`` floors and the ``confirmed`` held-out report.
    """
    rows = real.rows()
    solved = solver(rows, [s.rows() for s in scrambles])
    return {"solved": solved, "confirmed": checker(rows, [h.rows() for h in heldout], solved)}


def gate(rows: Rows, solved: Sequence[dict]) -> np.ndarray:
    """Which candidates clear their stratum's effective floor.

    The effective threshold is the stratum's own, as solved; a stratum with no floor admits
    nothing rather than everything, so a gap in the calibration cannot silently open the gate.

    Args:
        rows: ``(size, support)`` per candidate.
        solved: Per-stratum entries carrying an ``effective`` threshold.

    Returns:
        Boolean mask over candidates.
    """
    need = []
    for size, _support in rows:
        index = stratum_of(size)
        entry = solved[index] if 0 <= index < len(solved) else None
        value = None if entry is None else entry.get("effective")
        need.append(np.inf if value is None else float(value))
    return np.array([support >= threshold
                     for (_size, support), threshold in zip(rows, need, strict=True)],
                    dtype=bool)


class Built(NamedTuple):
    """A built ontology, before export.

    Attributes:
        members: Packed membership per node.
        supports: Support per node, aligned with ``members``.
        inclusions: Per node, the accepted candidate's own inclusion vote.
        parents: Parent indices per node.
        superseded: How many gated candidates consensus folded away.
        gated: How many candidates cleared the gate.
    """

    members: list[np.ndarray]
    supports: list[float]
    inclusions: list[dict[int, float]]
    parents: list[tuple[int, ...]]
    superseded: int
    gated: int


def build(got: Material, solved: Sequence[dict], *, legacy: bool = False) -> Built:
    """Gate, merge by consensus, then stack by containment.

    Args:
        got: The gate's input.
        solved: Solved per-size floors.
        legacy: Restore v0.3's STRAY. Partial containment is not restorable and does not need to
            be: the ablation produced a build identical to strict containment on all four
            statistics, so strict is both the simpler and the faithful choice.

    Returns:
        The built ontology.

    Raises:
        ValueError: If ``got`` carries no inclusion votes, which would silently write 1.0 for
            every member and differ from v0.3 on most member rows.
    """
    if len(got.selections) != len(got.supports):
        raise ValueError(
            f"material carries {len(got.selections)} inclusion votes for "
            f"{len(got.supports)} candidates; build needs one per candidate")
    rows = got.rows()
    keep = np.flatnonzero(gate(rows, solved)).tolist()
    words = got.blocks.shape[1] * bits.WORD
    blocks = [got.blocks[i] for i in keep]
    supports = [float(got.supports[i]) for i in keep]
    inclusions = [got.selections[i] for i in keep]

    # Consensus merges near-duplicate themes at the same THETA used for recurrence. STRAY is 0:
    # nothing is inherited, and the ablation found nothing lost by that.
    verdict = consensus(blocks, supports, inclusions, words,
                        stray=LEGACY_STRAY if legacy else 0.0, jaccard=DEFAULT_JACCARD)
    members = [verdict.members[i] for i in range(len(verdict.accepted))]
    kept_support = [supports[c] for c in verdict.accepted]
    # The node's inclusion column is the ACCEPTED CANDIDATE's own vote, as v0.3 writes it -- not a
    # recomputation over the merged membership.
    kept_inclusion = [inclusions[c] for c in verdict.accepted]

    # Strict Hasse edges: an edge means the child's pathway set is contained in the parent's.
    # Because a theme is a set of pathways and gene-set union is monotone under inclusion, every
    # edge therefore satisfies gene containment as well -- structurally, not by luck.
    return Built(members=members, supports=kept_support, inclusions=kept_inclusion,
                 parents=hasse(members), superseded=len(verdict.superseded), gated=len(keep))


def parameters(n: int, *, legacy: bool = False) -> dict[str, object]:
    """Every parameter this build used, for the manifest.

    Args:
        n: Universe size.
        legacy: Whether the removed stages were restored.

    Returns:
        A manifest fragment.
    """
    return {"method": "v0.4" if not legacy else "v0.4-legacy-all-stages",
            "theta": THETA, "min_size": MIN_SIZE, "inclusion_cut": INCLUSION_CUT,
            "subsample": SUBSAMPLE, "strata": [list(s) for s in STRATA],
            "max_fdr_overall": MAX_FDR_OVERALL, "max_fdr_stratum": MAX_FDR_STRATUM,
            "kept_stages": [s.name for s in STAGES],
            "removed_stages": ([] if legacy else
                               ["size cap", "TOL extras-only rule", "STRAY",
                                "partial containment"]),
            "size_cap": cap_for(n) if legacy else None,
            "stray": LEGACY_STRAY if legacy else 0.0,
            "tol": LEGACY_TOL if legacy else 0.0,
            "containment": "strict"}
