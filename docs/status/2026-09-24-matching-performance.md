# Matching made fast, with identical output

*24 Sep 2026. Branch `perf/matching`. The standard here is not "reasonable" but "identical":
the change exists only for speed, so anything other than byte-identical output is a failure.*

---

## Where the time went

Profiled on one null side of the confirmatory calibration, 1,850 pathways, 100 runs:

| stage | seconds | share |
|---|---|---|
| prepare (100 Ward runs + dedup + eligibility) | 17.1 | 2% |
| **matching** | **616.6** | **63%** |
| completion (56,929 groupings) | 3.5 | 0% |
| **families (56,929 -> 38,390)** | **342.0** | **35%** |
| family support | 0.1 | 0% |
| **total** | **979** | |

Ward itself is 16.9 s of the 17.1. Matching was the target; families is now the ceiling and is
**not** addressed here -- it gets its own change and its own proof.

## The rule, stated before it was reimplemented

`_best_overlap` picks **the recorded cluster of that run with the greatest intersection with the
grouping's members that this run drew, ties broken toward the smaller cluster** (smaller total
size, not smaller intersection).

It is **not** greatest Jaccard and **not** smallest containing ancestor. Jaccard decides only
whether the winner is *accepted*. Reimplementing the selection as max-Jaccard would be a different
algorithm, and the numbers would move.

## What replaced the walk

The walk asked one question per (grouping, run) pair and rebuilt the candidate list every time.
Every quantity it needed is a set intersection, and all of them are rows of two products. With `B`
the candidate cluster, `j` the judging run and `i` the grouping's origin run, using `B` subset of
`present[j]` and `A` subset of `present[i]`:

```
cover  = |A & B|                = I[A, B]
shared = |A & present[j]|       = C[A, j]
extras = |B & present[i] & ~A|  = C[B, i] - I[A, B]
union  = shared + extras        = C[A, j] + C[B, i] - I[A, B]
```

`C = M @ D.T` is already computed by `prepare` for eligibility and was being thrown away; it is now
kept. `I = M @ M.T` is needed only for run *j*'s recorded clusters, and **every recorded cluster is
itself a pool row**, so the whole stage is one sparse product per run against a few hundred columns.
No bitset arithmetic survives in the loop.

**The candidate set is unchanged, and that is the load-bearing claim.** The walk visited every
recorded cluster containing at least one drawn member, because the nodes of a dendrogram containing
a given pathway form a chain. A sparse product visits exactly the pairs sharing at least one
pathway. Same set, reached differently -- which is the inverted index the walk was approximating,
obtained without building one.

The winner is selected by a single sortable key -- `cover`, then smaller size, then lowest index for
determinism -- so the per-row argmax is `np.maximum.reduceat` rather than a Python scan.

Also precomputed once per run, which the walk recomputed per pair: **cluster sizes** (the old code
called `bits.count` on the same few hundred clusters millions of times) and **each pathway's
ancestor chain**.

## The three proofs

All required, all passed. `matching = "tree" | "matrix"` keeps both callable; the tree walk is
**not deleted**.

**a. A hand-computed fixture** (`tests/ontology/test_matching_equivalence.py`). Ten pathways, two
runs, four groupings, worked out on paper in the module docstring. It exercises the origin
shortcut, a real Jaccard decision, and **a cover tie that must break toward the smaller cluster**.
At theta 0.70 the support is `1.0 / 0.5 / 1.0 / 0.5`; at 0.80 every value is `0.5`. Both
implementations return exactly that. Randomised builds additionally agree on groupings, eligible
counts, support (NaN-equal) and **every `copies` bitset** at theta None, 0.70 and 0.85.

**b. A persisted null side** (side 7 of the confirmatory run, 58,540 groupings) and
**c. the real side**, each scored both ways off one `Prepared`:

| | real side | null side 7 |
|---|---|---|
| matching, original code | 353 s | 950 s |
| matching, tree + precomputation | 227.7 s | 407.4 s |
| **matching, matrix** | **4.4 s** | **5.7 s** |
| speed-up vs original | **80x** | **167x** |
| peak RSS | 720 MB | 589 MB |
| groupings / eligible / support identical | yes | yes |
| **`copies` differing** | **0** | **0** |
| **side `.tsv` byte-identical to the original code's output** | **yes**, 15,630 rows | **yes**, 38,327 rows |

The `.tsv` comparison is the one that matters: those files were written by the original code before
any of this existed.

## What it buys, and what it does not

A null side goes 979 s -> **~370 s**, an overall **2.6x** -- not the 3-6x estimated before the
profile, because families is untouched and now dominates.

Families was then given the same treatment on its own branch, with its own three proofs -- see
"Families" below.

## The matched pool is now persisted

Each side writes `pool_<tag>.npz`: every grouping's member set, its support and eligible count after
matching, every completed set, and each family's seed and support. Sets are stored **CSR**
(`indptr` + `uint16` indices), verified against `bitset.unpack` at widths 7, 64, 65, 1850 and 10770
before use, with NaN support preserved across the round trip.

**Measured: 2.8 MB per side, 83 MB for all 31**, verified complete -- every pool self-consistent,
carrying the right universe digest, theta and cut, with its non-NaN family count matching its
side's `.tsv` row count exactly. The estimate beforehand was 15-25 MB a side; it
assumed 150-member groupings, and real ones are far smaller. The 10,770 figure scales from the
measurement, not from the estimate.

With the rule locked, these 30 scrambles are the permanent null for the 1,850 universe: any later
question about `m`, about a size stratum, or about cohesion reads from disk. **Not** persisted is
`Pool.copies` (~600 MB a side), needed only to change `theta` or the 0.25 inclusion cutoff -- both
declared. Changing either still costs a full re-run.


---

## What E produced, and one caveat on it

The confirmatory calibration completed on the original code before any of this landed: real + 20
calibration + 10 held-out, theta 0.70, **2 h 05 min at four concurrent.** Scored exactly as
`amendment-2026-09-24c.md` pre-registers.

| stratum | real | null/side | floor | m_eff | kept | FDR held-out |
|---|---|---|---|---|---|---|
| 3 | 230 | 299.0 | 0.94 | **0.94** | 12 | 0.0167 |
| 4 | 231 | 1008.8 | 0.90 | **0.90** | 46 | 0.0065 |
| 5 | 257 | 2005.3 | 0.72 | **0.72** | 50 | 0.0100 |
| 6 | 332 | 2462.3 | 0.63 | **0.63** | 61 | 0.0033 |
| 7-9 | 1,208 | 9808.2 | 0.43 | **0.43** | 217 | 0.0083 |
| 10-14 | 2,050 | 7888.5 | 0.10 | **0.33** | 263 | 0.0000 |
| 15-29 | 4,494 | 7815.8 | 0.03 | **0.33** | 239 | 0.0000 |
| 30-49 | 2,808 | 3012.8 | 0.02 | **0.33** | 54 | 0.0000 |
| 50-99 | 2,334 | 2254.0 | 0.02 | **0.33** | 28 | 0.0000 |
| 100-199 | 1,095 | 1114.0 | 0.02 | **0.33** | 7 | 0.0000 |
| 200+ | 591 | 823.4 | 0.02 | **0.33** | 9 | 0.0000 |

**986 themes. Overall held-out FDR 0.0030 against a 0.01 cap. No stratum dropped.**

**Sizes 3 and 4 survive on recurrence alone**, with no cohesion gate, at `m = 0.94` and `0.90` --
58 themes between them. The earlier finding that recurrence carried no signal at 3-4 (285 real
against 286 scrambled) was an artefact of the matching rule rounding its tolerance to zero below
size 7. With Jaccard the signal is there; it sits at the very top of the support range, and a
size-3 theme must recur in 94 runs of 100.

`max(declared, floor)` cut both ways, which is what it was for: below size 10 the null demands far
more than the declared 0.33 and the floor binds; at 10 and above the null asks for 0.02-0.10 and
the declared value binds instead.

Declared-`m` sensitivity -- **reported, not used**: 0.20 keeps 1,387 at 0.0025; 0.25 keeps 1,185 at
0.0027; **0.33 keeps 982 at 0.0031**; 0.40 keeps 866 at 0.0035. Every value passes, so the choice
is not load-bearing for validity; it costs ~400 themes against 0.20 and is carried over from the
earlier builds rather than chosen now. The theta sensitivity arms cannot be reported -- they were
killed when E was relaunched as one arm, recorded in `DECISIONS.md` as a same-day withdrawal.

**Thinnest result in the table:** size 3, held-out 0.0167 against its 0.02 cap, on 12 themes. It
passes as pre-registered and nothing is re-solved.

### CAVEAT -- E ran on twelve contaminated embeddings

**12 of the 1,850 embedded pathways have descriptions carrying text appended after a correct
description, and 3 of those are severe** (`go:GO:0010560`, `go:GO:0034766`, `go:GO:0043267` --
10,752, 4,455 and 6,062 characters against a median of 969, the appended text being a smartphone
review, Java API documentation and Zulu-language chatbot output). Their vectors encode that
content, not biology. See `docs/debt.md`.

E's margin is wide -- 0.0030 against 0.01 -- so the conclusion is unlikely to turn on 12 rows of
1,850, but **the numbers in the table above are not final** and this build is not freezable on
them. The sequence is: prove the fast code byte-identical on these same embeddings first, because
that proof is only possible while the inputs are unchanged; then repair the descriptions, snapshot
and rebuild the embeddings, and re-run E. Comparing the two runs then measures directly whether
the contamination mattered.


---

## Families, on the same discipline

**The rule, before anything was rewritten.** Two groupings are *variants* when their intersection
is non-empty and each one's members outside the intersection number at most
`max(2, int(0.10 x |A n B|))`; seeds are taken in order of **descending support, then descending
size, then ascending bitset key**, and each still-unclaimed seed claims every still-unclaimed
variant **of the seed's own set** -- never of the growing family -- with the family's member set
being **the seed's set**. Pooling buys evidence, not membership.

**What was wrong with the old search.** The pairwise version walks a window in size order around
each seed, `max(2, int(0.10 x |seed|)) x 2` wide, testing `is_variant` on everything in it. Size is
a weak filter: two groupings of identical size may share nothing at all, and at ~57,000 groupings
most of the window is wasted.

**The prefix filter, which is exact and not a heuristic.** If `|A \ B| <= k` then among ANY `k + 1`
members of `A` at least one must lie in `B`, since `k + 1` members all outside `B` would already
exceed the allowance. The intersection can never exceed `|A|`, so `k = max(2, int(0.10 x |A|))`
bounds the allowance from above, and a grouping holding none of `A`'s `k + 1` rarest members cannot
qualify. Rarest-first only makes the list short -- any other `k + 1` members would be equally
correct and slower. `is_variant` still decides every surviving pair; the shortlist is a superset,
never a filter on the rule. The size window is applied unchanged.

**One detail that mattered:** the pairwise walk emits a family *ordered* -- smaller side
descending, then larger side ascending. That ordering is reproduced, so family LISTS match, not
merely family partitions.

**The three proofs.** `families = "pairwise" | "indexed"`, default `indexed`; the walk is not
deleted.

**a.** A hand-computed fixture covering the three cases that decide faithfulness: a **support tie
broken by size** (two groupings at 0.90, the larger seeds first), a variant at **exactly** the
boundary (`|A n B| = 30`, allowance 3, three extras qualify and four do not), and a grouping
**claimed by an earlier seed** so a later seed's family is itself alone. Both return
`[(2, [2, 1]), (0, [0]), (3, [3, 4])]`. Three randomised pools also agree exactly.

**b/c.** Both sides, off one `Prepared`:

| | real side | null side 7 |
|---|---|---|
| families, pairwise | 36.4 s | 310.3 s |
| **families, indexed** | **7.0 s** | **18.7 s** |
| speed-up | 5.2x | **16.6x** |
| families | 15,630 = 15,630 | 38,327 = 38,327 |
| seeds, **lists including order**, member sets, support | identical | identical |
| **side `.tsv` byte-identical** | **yes** | **yes** |
| peak RSS | 1,023 MB | 1,340 MB |

## End to end

The full 31-side calibration, same embeddings, same seeds, **every `.tsv` byte-identical to the
original E**, run three ways:

| run | wall | sides identical |
|---|---|---|
| original, 4 concurrent | **2 h 05 min** | -- |
| fast matching, 12 concurrent | **24 min 13 s** | 31 / 31 |
| **fast matching + fast families, 12 concurrent** | **3 min 03 s** | **31 / 31** |

**41x end to end.** Peak combined RSS 7.9 GB of 39 GB at 12 concurrent.

A null side is now 64 s, of which **`prepare` is 25 s**. Ward is the floor: ~100 clusterings per
side, and every other stage is now small beside it. Nothing further is proposed here.
