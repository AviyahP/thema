# O50s restructured as designed: S1p and S1s, 22 Oct 2026

Prompt 53, exploratory. Nothing is adopted. The design is Aviyah's, and the chain-survivor arm is
hers to choose on her return.

**Scope: the build and sections A-B only.** The full A-G estimate came to about **7 h** against the
prompt's 5 h ceiling, and the prompt's instruction for that case is to do the build and sections
A-B and stop. C to G are deferred. The reviewer material is **not** prepared either, and that needs
no judgement call: the prompt prepares it "only if that arm has 600 roots or fewer", and **S1p has
991 roots and S1s has 1,017**.

## Both declared tests pass

1. **The sibling rule on fixtures.** It never merges non-siblings -- two themes overlapping at high
   Jaccard under *different* parents are both kept -- it does resolve a true sibling pair under a
   shared parent, and it is order-stable over 8 random fixtures.
2. **Consensus restored plus today's repair reproduces frozen O50s byte for byte.** From this
   module's own gated input: consensus 26,120 -> 6,589 (19,531 superseded), joint fixed point
   6,589 -> 5,658 (765 collapsed, 166 merged), and `nodes.tsv`, `members.tsv`, `edges.tsv` and
   `unplaced.tsv` all identical to `data/ontology/frozen/working-O50s-2026-10-22/`.

Test 2 is the one that matters: it proves the gated input **and** the export path, so the S1 numbers
below differ from O50s only by the restructure. The input itself is also checked directly -- the
26,120 gated themes are rebuilt from the cached x2 real side and O50s's stored floors and asserted
**identical to prompt 52's logged gate**, supports included. No side was recomputed.

## A. Construction

| | O50s | S1p | S1s |
|---|---:|---:|---:|
| gated themes (input) | 26,120 | 26,120 | 26,120 |
| consensus supersessions | 19,531 | **none (removed)** | **none (removed)** |
| chain collapses | 765 | 1,720 | 1,508 |
| sibling drops | 166 (stale merge) | **18,585** | **18,734** |
| rounds to a fixed point | 2 | 5 | 5 |
| **final themes** | **5,658** | **5,815** | **5,878** |
| held-out FDR overall | 0.00233 | 0.00233 | 0.00233 |

**The gate is untouched** -- all three carry the same floors and the same held-out report, checked
mechanically, so the FDR is unchanged by construction and confirmed rather than assumed.

Per round:

| round | S1p chain | S1p siblings | S1p alive | S1s chain | S1s siblings | S1s alive |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1,720 | 17,514 | 6,886 | 1,474 | 17,694 | 6,952 |
| 2 | 0 | 979 | 5,907 | 32 | 970 | 5,950 |
| 3 | 0 | 88 | 5,819 | 2 | 68 | 5,880 |
| 4 | 0 | 4 | 5,815 | 0 | 2 | 5,878 |
| 5 | 0 | 0 | 5,815 | 0 | 0 | 5,878 |

**Round 1 does almost all the work**, and the fixed point is reached in five rounds. The later
rounds matter only a little, but they are not nothing: 1,071 further themes go in rounds 2-4 of S1p,
which is what the DAG-rebuild between rounds buys.

**The restructure lands on almost the same theme count as O50s** -- 5,815 and 5,878 against 5,658,
within 3 to 4%. 19,531 relationship-blind merges are replaced by 18,585 relationship-checked ones
and the total barely moves.

## B. Size and shape

| band | O50s | S1p | S1s | S1p-O50s | S1s-O50s |
|---|---:|---:|---:|---:|---:|
| 3-5 | 524 | 518 | 518 | -6 | -6 |
| 6-11 | 1,908 | 1,863 | 1,880 | -45 | -28 |
| 12-24 | 1,804 | 1,882 | 1,918 | +78 | +114 |
| 25-49 | 1,059 | 1,132 | 1,134 | +73 | +75 |
| 50-99 | 267 | 310 | 319 | +43 | +52 |
| 100-199 | 67 | 79 | 78 | +12 | +11 |
| 200-399 | 19 | 13 | 13 | -6 | -6 |
| 400-799 | 2 | 7 | 7 | +5 | +5 |
| 800-1599 | 3 | 5 | 5 | +2 | +2 |
| 1600+ | 5 | 6 | 6 | +1 | +1 |
| **TOTAL** | **5,658** | **5,815** | **5,878** | **+157** | **+220** |

| | O50s | S1p | S1s |
|---|---:|---:|---:|
| themes | 5,658 | 5,815 | 5,878 |
| **roots** | **261** | **991** | **1,017** |
| **roots of 50 or fewer** | **164** | **754** | **772** |
| giants over 1,280 | 5 | **9** | **9** |
| children per node, max | 382 | 554 | 533 |
| children per node, median | 2.0 | 1.0 | 1.0 |
| multi-parent share | 0.6329 | 0.6169 | 0.6094 |
| mean themes per pathway | 23.30 | 26.44 | 26.67 |
| **levels to a root, median** | **6.0** | **4.0** | **5.0** |
| levels to a root, max | 11 | 9 | 10 |

Giants. O50s: `n01843` 2,564, `n02672` 2,172, `n03878` 2,135, `n04994` 2,096, `n01419` 1,603.
Both arms have the **same nine giant sets** (different ids): 2,809, 2,197, 1,995, 1,928, 1,904,
1,656, 1,402, 1,304, 1,303. The largest, 2,809, is the largest gated theme there is -- it survives
the restructure intact in both arms, where O50s's consensus had merged it away.

## What this says, with the limits stated

1. **The band profile barely moves, but the top fragments.** Theme counts are within 4% of O50s in
   every band. **Roots go from 261 to 991 and 1,017, and small roots from 164 to 754 and 772** --
   nearly five times as many parentless themes, mostly small. Median depth falls from 6 to 4 and 5.
   The restructure keeps the themes and loses the hierarchy above them.
2. **The reason is visible in the mechanism, not a surprise.** Consensus merged *any* pair at
   J >= 0.5, and prompt 52 showed 54% of those pairs were neither siblings nor nested. Those
   relationship-blind merges were also, transitively, what tied the upper structure together.
   Restricting the rule to real siblings leaves those pairs standing as separate themes, and a
   theme that nothing contains is a root.
3. **The two arms differ very little from each other** -- 5,815 against 5,878 themes, 991 against
   1,017 roots, the same nine giants. The chain survivor, which was consequential in O50s (prompt 52
   found it discards the parent 71.9% of the time), is nearly immaterial once the sibling rule only
   fires on siblings: S1p collapses 1,720 chains and S1s 1,508, and the outcomes converge. **That
   is useful for the choice ahead: it is close to a free choice on these two measures**, and S1p is
   the simpler rule.
4. **Giants get worse, not better: 5 to 9.** Including the 2,809-pathway theme that consensus used
   to absorb.
5. **Limits.** This is sections A-B only. Whether the 991 roots read as coherent themes, whether
   the 76 parents consensus superseded now survive (section D, the question the design was aimed
   at), duplication (C), agreement and placement (E), stability (F) and gene coherence (G) are all
   unmeasured. **A build with more roots and shallower structure is not self-evidently worse** --
   O50s's own 261 roots came partly from merges prompt 52 showed to be relationship-blind -- and
   nothing here tests which is more faithful. That is what C-G and the blind reading are for.

**Nothing is adopted.** Aviyah chooses the arm, and C-G remain to be run.

## Outputs

| what | where |
|---|---|
| S1p build | `data/ontology/v0.4-leaves/thema_L_x2_S1p/` |
| S1s build | `data/ontology/v0.4-leaves/thema_L_x2_S1s/` |
| this note | `docs/status/2026-10-22-restructured-S1.md` |

No existing evaluation script covers section A's construction counts or section B's level
distribution; both are computed in `scripts/restructure_s1_report.py` and the method is stated in
its docstring. Everything else in B is read from the three builds' own `nodes.tsv` and
`members.tsv` by the same code, so the three columns are comparable.

```sh
uv run scripts/restructure_s1.py --check        # the two declared tests
uv run scripts/restructure_s1.py --arm S1p
uv run scripts/restructure_s1.py --arm S1s
uv run scripts/restructure_s1_report.py         # sections A and B
```
