# Which relationships do O50s's merges act on? 22 Oct 2026

Prompt 52, evaluation only. No build changed, nothing adopted.

**The headline: the merge designed for siblings acts on unrelated pairs more often than on
siblings.** Consensus is 19,531 of the 20,462 merges, and against the final DAG **54.0% of its
pairs are unrelated** -- neither nested nor sharing a parent -- against 40.0% siblings. The two
repair passes do act on what they were built for: chain collapse is **99.3% nested immediate**, and
the stale merge is **100% siblings** on identical pairs and **89.6%** on overlapping ones.

That is the WHY of the prompt confirmed by measurement. Consensus runs *before any DAG exists*, so
it cannot test a relationship even in principle; it compares two member sets at J >= 0.50 and drops
the weaker. The repair passes run on final memberships, where containment is available, and they
land on relationships.

**Verification: O50s reproduced BYTE FOR BYTE** from the cached trees and re-solved floors, with
every logging hook in place -- `nodes.tsv`, `members.tsv`, `edges.tsv` and `unplaced.tsv` all
identical to `data/ontology/frozen/working-O50s-2026-10-22/`. Separately,
`scripts/o50s_build.py --verify` still reproduces the **frozen O50** byte for byte (PROOF 1 and
PROOF 2 both pass). The hooks are therefore inert, which is the only thing that makes the rest of
this note trustworthy.

## How the merges were logged, and why so little instrumentation was needed

Neither `repair.collapse_chains` nor `repair.merge_stale` mutates a membership -- both only ever
drop rows -- and `repair_joint` already maps every drop back to its post-consensus index. So both
member sets of every collapse and every stale merge are recoverable from the post-consensus stack by
index, with **no instrumentation of the repair pass at all**. The script asserts this rather than
assuming it: every surviving row's membership equals its post-consensus membership, 0 disagreements
against `members.tsv`.

Only consensus needed a hook, because a newcomer grows by inheritance before it meets the theme
that supersedes it, so the pair actually compared is not `member_sets[candidate]`. Two write-only
fields were added to `consensus.Outcome` (`superseded_blocks`, `superseded_against`), plus
`probe=None` hooks on `v04.build`, `v04.material` and `o50s_build.write_build`. Every one defaults
to off and nothing in the build reads any of them.

## 1. Merge kind by relationship

| merge kind | siblings | nested immediate | nested deeper | unrelated | total |
|---|---:|---:|---:|---:|---:|
| consensus | 7,813 (40.0%) | 1,126 (5.8%) | 40 (0.2%) | **10,552 (54.0%)** | 19,531 |
| stale identical | 32 (100.0%) | 0 | 0 | 0 | 32 |
| stale overlap | 120 (89.6%) | 1 (0.7%) | 0 | 13 (9.7%) | 134 |
| chain | 3 (0.4%) | **760 (99.3%)** | 0 | 2 (0.3%) | 765 |
| **ALL** | **7,968 (38.9%)** | 1,887 (9.2%) | 40 (0.2%) | **10,567 (51.6%)** | **20,462** |

Consensus by size band of the kept node -- the unrelated share is worst in the middle and falls away
at the top:

| kept band | siblings | nested immediate | nested deeper | unrelated | total |
|---|---:|---:|---:|---:|---:|
| 3-9 | 140 (44.7%) | 0 | 0 | 173 (55.3%) | 313 |
| 10-19 | 1,607 (34.3%) | 227 (4.8%) | 1 (0.0%) | **2,850 (60.8%)** | 4,685 |
| 20-49 | 3,636 (35.7%) | 626 (6.1%) | 11 (0.1%) | **5,912 (58.0%)** | 10,185 |
| 50-199 | 2,017 (53.1%) | 258 (6.8%) | 28 (0.7%) | 1,499 (39.4%) | 3,802 |
| 200+ | **413 (75.6%)** | 15 (2.7%) | 0 | 118 (21.6%) | 546 |

Stale overlap concentrates at the top: 95 of its 134 pairs have a kept node of 200+, and 94 of
those 95 are siblings. Chain collapse never fires above 199 members at all.

## 2. The pairs classed unrelated

10,567 of 20,462 = **51.6%**. Two Jaccards, and the difference is worth stating:

| | min | q1 | median | q3 | max |
|---|---|---|---|---|---|
| **at merge** (what the rule acted on) | **0.500** | 0.524 | 0.571 | 0.643 | 0.933 |
| final (against the kept node's finished set) | 0.152 | 0.518 | 0.565 | 0.636 | 0.910 |

| | 0.0-0.5 | 0.5-0.6 | 0.6-0.7 | 0.7-0.8 | 0.8-0.9 | 0.9-1.0 |
|---|---:|---:|---:|---:|---:|---:|
| at merge | **0** | 6,428 | 2,806 | 1,089 | 241 | 3 |
| final | 711 | 5,890 | 2,796 | 982 | 186 | 2 |

**At merge the minimum is exactly 0.500, the cutoff, and nothing sits below it** -- the rule did what
it says. The final column drops 711 pairs under 0.5 only because a consensus keeper goes on growing
by inheritance after it supersedes someone. Reporting the final figure alone would have looked like
a bug in the merge; it is an artefact of when you measure. **Most unrelated merges happen just above
the cutoff**: 6,428 of 10,567 are in 0.50-0.60.

Ten examples, largest kept node first:

| merge | kept node | kept | dropped | J merge | J final | kept sup | drop sup |
|---|---|---:|---:|---:|---:|---:|---:|
| consensus | n01027 | 923 | 795 | 0.895 | 0.778 | 0.8050 | 0.2350 |
| consensus | n01027 | 923 | 678 | 0.788 | 0.711 | 0.8050 | 0.0250 |
| consensus | n01027 | 923 | 485 | 0.500 | 0.488 | 0.8050 | 0.0100 |
| consensus | n01278 | 886 | 748 | 0.751 | 0.707 | 0.6950 | 0.0450 |
| consensus | n01278 | 886 | 603 | 0.791 | 0.677 | 0.6950 | 0.0500 |
| consensus | n01278 | 886 | 646 | 0.768 | 0.687 | 0.6950 | 0.0300 |
| consensus | n04526 | 820 | 610 | 0.516 | 0.516 | 0.0200 | 0.0150 |
| stale overlap | n04526 | 820 | 707 | 0.502 | 0.471 | 0.0150 | 0.0100 |
| consensus | n03316 | 386 | 379 | 0.759 | 0.727 | 0.1050 | 0.0300 |
| consensus | n03316 | 386 | 308 | 0.826 | 0.757 | 0.1050 | 0.0300 |

`n04526` is worth a second look: an 820-member theme at support **0.0200** -- four runs of 200 --
absorbing a 610-member rival at 0.0150. That is the open minimum-support question from the O50s
freeze showing up inside the merge log.

## 3. Chain collapses: which end survived

| parent band | kept parent | kept child | total | child kept |
|---|---:|---:|---:|---:|
| 10-19 | 32 | 92 | 124 | 74.2% |
| 20-49 | 158 | 410 | 568 | 72.2% |
| 50-199 | 25 | 48 | 73 | 65.8% |
| **ALL** | **215** | **550** | **765** | **71.9%** |

**The survivor rule discards the parent 71.9% of the time.** `survivor="support"` keeps whichever
end has more support, and the child usually does. So the stage that acts most cleanly on a real
relationship -- 99.3% nested immediate -- resolves it by deleting the more general node in roughly
five cases out of seven. That is a mechanism for losing the top of the hierarchy, and it is the one
stage of the three whose pairs are unambiguously parent and child.

## 4. Dropped parents: which parents that would build the top exist, and where were they lost

A unit -- a grouping or a family -- is a **potential parent** if it strictly contains at least two
final themes that are not nested in each other, at least one of them a final root, and no final
theme matches it at J >= 0.9. Nothing is filtered on support or redundancy; both are recorded as
columns.

The pipeline, now visible: **270,570 groupings -> 264,897 completed -> 99,951 families -> 26,120
through the gate -> 6,589 after consensus -> 5,658 after repair.**

**Potential parents are very rare. Only 587 of 264,897 completed groupings strictly contain even one
current root**, and of those, **570 qualify as groupings and 244 as families**.

| stage | groupings | families | redundant by the build's own rules |
|---|---:|---:|---|
| completion | **0** | 0 | - |
| absorbed | 326 | - | 319 of 326 = 97.9% |
| gate | 120 | 120 | **15 of 120 = 12.5%** |
| consensus | 76 | 76 | 74 of 76 = 97.4% |
| stale | 48 | 48 | 38 of 48 = 79.2% |
| chain | **0** | 0 | - |
| **total** | **570** | **244** | |

**Completion loses nothing, by construction**: a unit is lost at completion precisely because its
completed set came out under MIN_SIZE 3, and a set that small cannot strictly contain two themes of
three or more. **Chain collapse loses no potential parents either** -- it never fires above 199
members, and a potential parent here is almost never that small.

### The gate is the stage that matters, and its parents are single-run

The 120 gate-lost parents are the only group that is **not** redundant: 105 of 120 pass the build's
own redundancy rules. And **117 of the 120 were found by exactly one run of 200** -- support 0.0050,
their stratum floor being 0.01. They are 937 to 1,867 pathways, containing 87 to 249 final themes
and 1 to 3 current roots each.

| stage | runs 1 | 2-4 | 5-19 | 20+ |
|---|---:|---:|---:|---:|
| gate | **117** | 2 | 1 | 0 |
| absorbed | 0 | 20 | 122 | 184 |
| consensus | 0 | 38 | 27 | 11 |
| stale | 0 | 44 | 3 | 1 |

**So the parents that would build the top do exist in the data, and they mostly do not recur.** The
gate is not throwing away evidence; it is declining candidates that one subsample in two hundred
proposed. That is the gate working as designed, and it is also the answer to why the top is thin.

### What the other three stages lost

* **absorbed (326)** is almost entirely one variant cloud: the great majority were absorbed into the
  family of a single grouping, 146168, at best-J around 0.60-0.63 to the finished build. These are
  not distinct lost parents, they are redrawings of one giant -- 97.9% redundant.
* **consensus (76)** is the group that should give pause. These are **well-supported**: grouping
  41505 was found by **62 runs of 200** (support 0.3100), 146168 by 53, 129323 by 52, 230732 by 52 --
  and each was superseded as "the same theme" by one of just two gated candidates, 1286 and 1663.
  Each contains 4 to 21 current roots and up to 1,840 final themes.
* **stale (48)** is similar at lower support: grouping 2680, 2,809 pathways containing 15 roots,
  merged away at 4 runs.

### Roots these parents would cover

| stage | parents | distinct current roots contained | of them 50 or fewer |
|---|---:|---:|---:|
| absorbed | 326 | 89 | 71 |
| gate | 120 | 17 | 17 |
| consensus | 76 | **74** | 64 |
| stale | 48 | 49 | 40 |
| **any stage (groupings)** | **570** | **110 of 261** | **85 of 164** |
| any stage (families) | 244 | 97 | 79 |

**Consensus alone superseded parents that between them contain 74 of the 261 current roots**, 64 of
them small. The gate's 120 single-run parents, despite being the largest and least redundant group,
cover only 17 roots -- they are big but they overlap each other.

## What this says, with the limits stated

1. **Consensus is the stage that acts on relationships it cannot see**, and it is 95% of all merges.
   54% of its pairs are unrelated in the finished DAG, and it superseded parents covering 74 of the
   261 roots -- some found by 50 to 62 runs out of 200. It is the one merge whose design premise
   (twins are siblings) is not borne out.
2. **Chain collapse acts on exactly the relationship it was built for and then discards the parent
   71.9% of the time.** Both halves of that sentence are measured here.
3. **The gate's losses are real parents but single-run ones.** 117 of 120 at one run in 200. No
   change to the floors would recover them without admitting the null.
4. **Limits.** The relationship classes are computed against the *final* DAG, which did not exist
   when consensus ran -- that is the point of the measurement, not a flaw, but it means "unrelated"
   describes the outcome, not a mistake visible at the time. The dropped set is placed as a
   pseudo-node by its smallest strict containers; where a dropped set has no container and the kept
   node has no parent, both are roots and the pair is counted as siblings. Nothing here tests
   coherence: whether these parents read as real themes is the reviewer's blind reading.

**Nothing is adopted.** This note measures the existing build and proposes no rule.

## Outputs

| what | where |
|---|---|
| per-pair table, 20,462 rows | `data/experiments/merge_relationships_2026-10-22/pairs.tsv` |
| every potential parent, 814 rows | `.../potential_parents.tsv` |
| blind reading inputs, 120 parents in 97 batches | `.../read_parents/b01.md` ... `b97.md` |
| the key, written once and not read again | `.../KEY_DO_NOT_SHARE_parents.json` |
| merge provenance cache (3.2 MB) | `.../probe.npz` |
| side provenance cache (22 MB) | `.../side.npz` |
| the rebuild, byte-identical to the freeze | `data/ontology/v0.4-leaves/thema_L_x2_O50s_relog/` |

Reviewer material: per stage, the 15 potential parents containing the most current roots plus 15
drawn at random (seed 20261022), families preferred over groupings for the same set -- **30 per
stage across the four stages that lost any, 120 in total**. Member lists are `name [source]` sorted
by name, with a random id and nothing else: no stage, no support, no node id. Verified mechanically
-- every line is either a header or a `name [source]` row, no node id and no support value appears,
and no parent is split across batches.

```sh
uv run scripts/o50s_build.py --verify                                    # PROOF against frozen O50
uv run scripts/o50s_build.py --directory thema_L_x2_O50s_relog \
    --probe data/experiments/merge_relationships_2026-10-22/probe.npz
uv run scripts/merge_relationships.py                                    # tasks 1-3
uv run scripts/dropped_parents.py --side                                 # one fresh side, ~2 min
uv run scripts/dropped_parents.py                                        # task 4 + reviewer
```
