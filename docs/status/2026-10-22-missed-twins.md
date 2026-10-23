# Are O50s's after-gate merges missed twins? No. 22 Oct 2026

Prompt 56, Part A. Evaluation only; no build changed, nothing adopted.

**The answer is clean and it is a zero.** Of the 19,531 rule-3 supersessions and 166 stale merges,
**not one pair passes the twin test on the sets as they left the gate.** Families missed nothing.
What the after-gate rules merge are pairs that **inheritance made into twins after the gate**: 418
pairs are twins at the moment the rule fires and were not twins at gate exit, and **zero** go the
other way.

So the fix Aviyah was weighing -- strengthen the twin rule in families -- has nothing to act on.
The after-gate rules are doing a different job, and they stay.

**The reviewer's prediction, recorded in DECISIONS before the run, was "near-zero passes at gate
exit, and passes at event time only where inheritance grew a theme first". Both halves hold
exactly**, the first at 0 rather than near-0.

**Scope.** Part A only, by Aviyah's decision: tasks 0, 1 and 2 for the three after-gate merge kinds,
task 3 redefined as the gate-exit test, and task 4. Part B is skipped -- no replay, so no counts for
consensus rules 1, 2 and 4, no rule-2 twin test, and the reconciliation below covers only the rules
that remove themes. Prompt 56's task 5 (forty examples) falls in the skipped part and is not
produced.

## 0. What step 5 compares: completed sets, not raw

`recurrent.py:1180` selects which:

```python
of = (lambda g: member_bits[g]) if member_bits is not None else (lambda g: pool.groupings[g])
```

and `v04.py:299` passes `completed` as `member_bits`, so the first branch is taken:

```python
grouped = families(list(completed), completed, pool, None, conf)
```

The twin rule is `recurrent.py:1067-1086`, **imported here rather than restated**, with
`TWIN_FLOOR = 2` and `TWIN_FRACTION = 0.10`:

```python
shared = bits.count(a & b)
if not shared:
    return False
allowed = max(TWIN_FLOOR, int(TWIN_FRACTION * shared))
return bits.count(a & ~b) <= allowed and bits.count(b & ~a) <= allowed
```

The allowance is on the **shared part**, and `int()` truncates: a shared part of 29 allows 2, not 3.

**One identity does the real work in this note.** A gated theme's members *are* its seed grouping's
completed set -- `v04.material` does `blocks.append(completed[seed])`. Since families compares
completed sets, two gated themes that pass the twin test at gate exit would be two family seeds
whose completed sets are twins, which greedy absorption should already have pooled. A non-zero count
in section 3 would therefore have been an inconsistency inside families, not merely a missed
opportunity. The count is zero, so families is internally consistent on its own rule.

## 1. Event counts, and what reconciles

| | count |
|---|---:|
| consensus rule 3, superseded | 19,531 |
| repair stale merges | 166 |
| repair chain collapses | 765 |
| gated themes | 26,120 |
| after consensus | 6,589 = 26,120 - 19,531 |
| final themes | 5,658 = 6,589 - 765 - 166 |

**Reconciles exactly.** Rules 1, 2 and 4 remove nothing, so they do not enter this arithmetic; their
counts need Part B's replay and are not reported here.

## 2. Twin test at the event

### Rule 3 supersessions: 384 of 19,531 = 2.0%

| J band | events | twin | share |
|---|---:|---:|---:|
| 0.5-0.6 | 10,434 | 4 | 0.0% |
| 0.6-0.7 | 5,383 | 44 | 0.8% |
| 0.7-0.83 | 3,212 | 75 | 2.3% |
| **0.83+** | 502 | **261** | **52.0%** |

| larger band | events | twin | share |
|---|---:|---:|---:|
| 6-11 | 712 | 49 | 6.9% |
| 12-24 | 4,920 | 115 | 2.3% |
| 25-49 | 8,943 | 136 | 1.5% |
| 50-99 | 3,800 | 68 | 1.8% |
| 100-199 | 656 | 9 | 1.4% |
| 200-399 | 289 | 4 | 1.4% |
| 400-799 | 42 | 3 | 7.1% |
| 800-1599 | 137 | 0 | 0.0% |
| 1600+ | 32 | 0 | 0.0% |

**Rule 3 is overwhelmingly not a twin rule.** 98% of its events fail the twin test even at the
moment they fire, and more than half its events sit in the 0.5-0.6 J band where the pass rate is
0.0%. The twin passes concentrate entirely at J >= 0.83, where they are 52%.

### Stale merges: 34 of 166 = 20.5%

| J band | events | twin | share |
|---|---:|---:|---:|
| 0.5-0.6 | 85 | 0 | 0.0% |
| 0.6-0.7 | 27 | 1 | 3.7% |
| 0.7-0.83 | 19 | 0 | 0.0% |
| **0.83+** | 35 | **33** | **94.3%** |

By the larger theme's band the passes sit in 12-24 (16 of 33) and 25-49 (16 of 26); the 61 events
with a 1,600+ partner contain none.

### Chain collapses: 417 of 765 = 54.5%

Every chain event is at J >= 0.83 by construction, so the J breakdown is a single row. The size
ratio is the informative cut:

| size ratio (smaller/larger) | events | twin | share |
|---|---:|---:|---:|
| 0.8-0.91 | 464 | 116 | 25.0% |
| **0.91+** | 301 | **301** | **100.0%** |

**Chain collapse at a ratio above 0.91 is exactly the twin rule**, 301 of 301. Below that it is a
containment rule that the twin test mostly rejects. That is a clean split in one measure.

## 3. Twin test at gate exit, before any inheritance

| kind | events | twin at gate exit | share | twin at the event | share |
|---|---:|---:|---:|---:|---:|
| rule 3 | 19,531 | **0** | **0.0%** | 384 | 2.0% |
| stale merge | 166 | **0** | **0.0%** | 34 | 20.5% |

| | pairs |
|---|---:|
| twin at the event but NOT at gate exit | **418** |
| twin at gate exit but NOT at the event | **0** |

**Zero passes at gate exit, and the effect is perfectly one-directional.** Inheritance only ever
creates twins here; it never destroys one. Task 3's second half -- "for any pair that passes there,
say why families did not pool them" -- has nothing to answer: there are no such pairs. That is the
result, not an omission.

The 418 are the whole of the twin-passing population (384 + 34), so **every twin the after-gate
rules catch was manufactured after the gate by consensus rule 2.** Families had no opportunity to
pool any of them, because at the moment families ran they were not twins.

## 4. Rule-3 supersessions that fail the twin test: would the dropped theme have been a root?

Measured on the set **as dropped** (the event-time set), which is the set actually discarded. A
dropped theme strictly inside no final O50s theme would have had no parent, so it would have been a
root had it been kept.

| dropped band | failing | inside no final theme | share |
|---|---:|---:|---:|
| 6-11 | 888 | 3 | 0.3% |
| 12-24 | 5,480 | 135 | 2.5% |
| 25-49 | 8,556 | 567 | 6.6% |
| 50-99 | 3,240 | 581 | 17.9% |
| 100-199 | 589 | 206 | 35.0% |
| 200-399 | 187 | 84 | 44.9% |
| 400-799 | 73 | 62 | 84.9% |
| 800-1599 | 105 | 103 | 98.1% |
| 1600+ | 29 | 29 | 100.0% |
| **ALL** | **19,147** | **1,770** | **9.2%** |

**The share rises monotonically with size, from 0.3% to 100%.** Nearly every large theme rule 3
dropped would have been a root: 194 of the 207 failing themes above 400 pathways sit inside no final
theme at all. That is the same population prompt 52 found when it counted the 76 superseded parents,
seen from the other side and without the parent predicate -- and it is 1,770 themes, not 76.

## What this settles

1. **The fix does not belong in families.** Zero of 19,697 rule-3 and stale-merge pairs were twins
   when families could have seen them. Strengthening the twin rule would change nothing about these
   merges.
2. **Rule 3 is not a duplicate remover in the twin sense.** 98% of its events are not twins even at
   the moment they fire, and the majority sit at J 0.5-0.6 with a 0.0% twin rate. It is a
   same-theme rule at a much looser notion of sameness.
3. **Chain collapse above a 0.91 size ratio IS the twin rule**, 301 of 301, and below it is not.
   If any after-gate rule is redundant with families, it is that slice -- though families could not
   have caught these either, since they are post-inheritance.
4. **Inheritance is the thing acting here.** It created every one of the 418 twins the after-gate
   rules caught and destroyed none. Prompt 54's checks already found it adds 11,932 members to
   surviving themes and underwrites 55.2% of O50s's edges; this adds that it also manufactures the
   duplicates the later rules remove.
5. **1,770 themes rule 3 dropped would have been roots**, rising to 100% above 1,600 pathways.
   Whether that is correct pruning or lost structure is not measured here and no reading was done.

**Nothing is adopted.**

## Outputs

| what | where |
|---|---|
| per-event records, all three kinds, and task 4 | `data/experiments/missed_twins_2026-10-22/events.json` |
| this note | `docs/status/2026-10-22-missed-twins.md` |

Part A needed **no replay**: prompt 52's probe already holds both sets as they were at each merge
event (`sup_blocks` and `sup_against` for rule 3; `consensus_members` indexed by the collapse and
stale maps, neither of which mutates a membership), and the gated blocks are reconstructed from the
cached x2 real side and asserted identical to prompt 52's logged gate.

```sh
uv run scripts/missed_twins.py
```
