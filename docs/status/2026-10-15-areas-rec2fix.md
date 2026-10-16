# The areas layer, corrected (rec2fix). 15 Oct 2026

**One of five criteria fails: 63 roots against the declared 20-60.** The other four pass. And the
failure has a single, measurable cause — **it fails because Aviyah's giant rule was applied.** With
the eight giant areas left in, the structure has **exactly 42 roots**, a pass; dropping them promotes
26 areas whose only parents were giants, and 42 − 5 + 26 = 63.

By the declaration that is a fail, and **the working view is O50 without giants, about 660 flat
roots**. Nothing here is adopted. But the number to argue about is 63 against 60, not a broken top.

| criterion, measured on the view | result |
|---|---|
| held-out FDR within the caps, every stratum and overall | **PASS** — overall **0.00429**, worst stratum 0.00459 |
| 20-60 roots, anchors included | **FAIL** — **63** (42 with the giants in) |
| no node with more than 60 direct children | **PASS** — max **18** |
| ≥95% of the 476 giant-only themes and of all 661 units parented, or roots of the view | **PASS** — 100% and 100%; **parented alone 99.4% and 98.6%** |
| no two roots at pathway Jaccard ≥ 0.50 | **PASS** — highest of 1,953 pairs **0.488** |
| C6 blind intruder test | the reviewer's, rerun under the 15 Oct pre-registration |
| the top is intuitive | Aviyah's |

**Aviyah's giant rule is now on the record**, as the prompt asked: *areas over 1,000 pathways are
giants and are kept out of the working view, exactly as O50's giants are.* It is what turns rec2's
"8 areas over 1,000 = criterion failure" into "8 giants, flagged and dropped" — and, as above, what
turns 42 roots into 63.

## 1. The two gaps, audited

The prompt named two implementation gaps. **One of them was not what it looked like.**

### Gap 1 was a reporting error, not a build error

The audit read rec2's stored sets as showing a *trimmed* pathway set for 188 of 343 areas. The
disagreement is real and the count is exactly right, but the direction is the other way round:

| | rec2 | rec2fix |
|---|---|---|
| areas | 343 | **343, the same ids** |
| area pathway sets | — | **identical, all 343, set for set** |
| areas whose stored `units_union` ≠ stored pathway set | **188** | 0 |
| areas whose unit list differs from rec2fix's | **188**, a strict **superset** every time | — |
| extra units in those lists | **3,247** (median 10, max 172) | — |
| areas whose pathway set ≠ the union of its units | **188** | **0** |

rec2's **pathway sets were already correct unions** — `as_pathway_blocks` built them that way and
`consensus` never trims. What rec2 got wrong was the **unit lists**, which it recovered from
provenance after the fact and over-credited; the "union" it then reported was computed from those
inflated lists and exceeded the pathway set by a median of 89 pathways. So **the same-theme cutoff,
chain collapse and containment at level 2 all ran on the correct union sets in rec2**, and this
re-run reproduces them set for set. Correction 1 therefore changes **no area and no pathway**; it
changes what the build can truthfully say about itself, and it is now asserted rather than reported.

Two audit figures follow from the inflated lists rather than from the build:

- **"With union sets, 9 roots are strictly inside another root."** Measured on the real pathway sets,
  **0 of rec2's 42 roots is strictly inside another**, and 0 of rec2fix's 63. Measured on rec2's
  inflated sets, 6 roots are — all but one of them inside `b2_00161`, which those sets credit with
  2,401 pathways against its true 2,009.
- **R43 / R04 = `b2_00313` / `b2_00198`.** `b2_00313` holds 202 pathways and **98.02%** of them are
  in `b2_00198`; **4 are not**, so it is correctly not nested, in rec2 and in rec2fix alike. The
  inflated reading gave `b2_00198` 1,081 pathways instead of 851, which swallowed those 4.

### Gap 2 was entirely real, and fixing it is what changed the structure

Every item in the audit's second list reproduced, and all four are now closed:

| | rec2 | rec2fix |
|---|---|---|
| anchors compared with each other and with areas | never | **every pair** |
| an area collapsed into one of its own units | never | **3 collapses** |
| units strictly inside an area with no edge saying so | 27 | **0** — every containment is reachable |
| `area_edges.tsv` | every area→unit pair, transitive | **direct edges only**, 1,871 |
| closure | not written | **`closure.tsv`, 7,301 pairs** |
| children per node | **181** (inflated by the transitive listing) | **18 direct** (164 through the closure) |

## 2. Level 2 — unchanged, by construction

Same units, same 200 Ward runs, same subsample scheme, same 20 calibration and 4 held-out scrambles,
same cal8 target, same floors. The figures are rec2's because they are the same computation:

| | rec2fix | rec2 |
|---|---:|---:|
| units clustered | 655 | 655 |
| anchors | 6 | 6 |
| candidates | 5,691 | 5,691 |
| through the gate | 1,398 | 1,398 |
| after consensus | 418 | 418 |
| **areas** | **343** | **343** |
| wall time | 251 s | 251 s |

### Held-out FDR per stratum — PASS, every stratum and overall

| stratum | floor | calib FDR | **held-out** | real | cap | rec2 |
|---|---:|---:|---:|---:|---:|---:|
| 3-3 | none | — | — | 0 | 0.02 | — |
| 4-4 | 0.940 | 0.00588 | **0.0** | 17 | 0.02 | 0.0 |
| 5-5 | 0.815 | 0.00588 | **0.0** | 17 | 0.02 | 0.0 |
| 6-6 | 0.770 | 0.00556 | **0.0** | 18 | 0.02 | 0.0 |
| 7-9 | 0.485 | 0.00652 | **0.00272** | 92 | 0.02 | 0.00272 |
| 10+ | 0.055276 | 0.00682 | **0.00459** | 1,254 | 0.02 | 0.00459 |
| **overall** | | | **0.00429** | | 0.01 | 0.00429 |

Stratum 3-3 gets no floor at all — no cut reached the 0.008 target — so it admits nothing, which is
why its real count is 0.

## 3. Anchors

| anchor | pathways | support | O50 children | in the view |
|---|---:|---:|---:|---|
| `n01027` | 813 | 0.805 | 105 | **root** |
| `n01279` | 781 | 0.695 | 59 | **root** |
| `n03315` | 349 | 0.105 | 14 | **root** |
| `n03959` | 290 | 0.045 | 33 | **root** (giant-only in O50) |
| `n03376` | 280 | 0.095 | 12 | **root** (giant-only in O50) |
| `n02017` | 206 | 0.410 | 7 | **root** (giant-only in O50) |

2,079 pathways between them. All six survive the seam rules and all six are roots. The pair the audit
flagged, `n03376` inside `n01279`, **was compared** this time: at J = 0.357 and 99.64% containment it
neither merges (below 0.50) nor nests (one pathway short), so it stays a separate root. That is O50's
own arithmetic, not an omission — see §7.

## 4. Giants — eight areas, 82% of the universe between them

| area | pathways | units | support | share of the 5,539 |
|---|---:|---:|---:|---:|
| `b2_00147` | 2,618 | 281 | 0.690 | **47.3%** |
| `b2_00076` | 2,197 | 237 | 0.930 | 39.7% |
| `b2_00161` | 2,009 | 305 | 0.665 | 36.3% |
| `b2_00338` | 1,903 | 224 | 0.060 | 34.4% |
| `b2_00112` | 1,340 | 179 | 0.830 | 24.2% |
| `b2_00251` | 1,288 | 184 | 0.195 | 23.3% |
| `b2_00307` | 1,177 | 101 | 0.080 | 21.2% |
| `b2_00211` | 1,083 | 95 | 0.410 | 19.6% |

Their union holds **4,540 of 5,539 pathways = 82.0%**. These are the same eight areas rec2 built;
the only change is that the rule now names them. Five of them were roots in rec2.

## 5. Merges and collapses at the seams

**Three events, all collapses, all at a seam, and no merges anywhere.**

| rule | victim | kind | size | keeper | kind | size | share |
|---|---|---|---:|---|---|---:|---:|
| collapse | `n02940` | unit | 43 | `b2_00029` | area | 49 | 0.878 |
| collapse | `n03083` | unit | 94 | `b2_00064` | area | 99 | 0.949 |
| collapse | `n04061` | unit | 65 | `b2_00023` | area | 75 | 0.867 |

Exactly the three the audit predicted ("3 areas are 85-95% one unit"). The area survives each time —
it is top level among the pair, so the survivor rule keeps it — and the unit is absorbed. All three
victims are giant-only O50 themes, which is why the coverage table counts them separately.

**Zero merges** over 1,004 nodes. Nothing in the combined set is a non-nested near-duplicate at
J ≥ 0.50, which is a property inherited from O50: its own build already merged at 0.50, so no two
units can be, and areas built from units of the same universe did not produce one either.

## 6. The view

993 nodes — **335 areas, 6 anchors, 652 units**. 1,871 direct edges, 7,301 containment pairs.

| | rec2fix view | rec2 |
|---|---|---|
| **roots** | **63** (57 areas + 6 anchors + 0 units) | 42 (36 areas + 6 anchors) |
| roots with the giants left in | **42** | 42 |
| children per node, max / median | **18** / 0 | 181 / 7 |
| multi-parent | 55.9% | 45.5% |
| size in pathways, all nodes | 1 / 25 / 977 | — |
| size in pathways, roots only | 68 / 267 / **977** | 27 / — / 3,053 |

**No root exceeds 977 pathways** — against rec2's 3,053 — because every 1,000-plus area is a giant.
Every unit has a parent: **0 of the 63 roots is a unit.**

The 15 largest roots:

| root | kind | pathways | units | support | children |
|---|---|---:|---:|---:|---:|
| `b2_00242` | area | 977 | 102 | 0.250 | 9 |
| `b2_00252` | area | 958 | 103 | 0.610 | 18 |
| `b2_00156` | area | 919 | 84 | 0.675 | 7 |
| `b2_00198` | area | 851 | 91 | 0.475 | 14 |
| `b2_00281` | area | 818 | 120 | 0.130 | 8 |
| `n01027` | anchor | 813 | 1 | 0.805 | 0 |
| `n01279` | anchor | 781 | 1 | 0.695 | 0 |
| `b2_00283` | area | 745 | 73 | 0.120 | 5 |
| `b2_00318` | area | 680 | 61 | 0.070 | 12 |
| `b2_00326` | area | 659 | 80 | 0.065 | 10 |
| `b2_00319` | area | 609 | 52 | 0.070 | 5 |
| `b2_00226` | area | 517 | 30 | 0.320 | 4 |
| `b2_00328` | area | 506 | 35 | 0.065 | 8 |
| `b2_00329` | area | 505 | 48 | 0.065 | 7 |
| `b2_00263` | area | 445 | 57 | 0.170 | 5 |

The full list of 63 is in the build's `report.txt`; the smallest is `b2_00256` at 68 pathways.

### Why 63 and not 42

| | |
|---|---:|
| roots of the combined structure **with the giants in** | **42** |
| of which are giants | 5 |
| areas promoted to roots when the 8 giants are dropped | **26** |
| of those, with no non-giant parent at all | **26** |
| **42 − 5 + 26** | **63** |

Every one of the 26 had only giant parents. **This is the same mechanism that created the 476
giant-only themes in O50** and the reason an areas layer was wanted in the first place: a node whose
only parents are grab-bags is a root of the real hierarchy. The areas layer re-parents 470 of those
476 — and then creates 26 of the same kind one level up.

## 7. Root overlap

| | rec2fix | rec2 |
|---|---|---|
| **highest root pair** | **0.488** | 0.492 |
| pairs at ≥0.50 | **0** of 1,953 | 0 of 861 |
| pairs at ≥0.30 | 43 | 19 |
| roots per pathway, median / mean / max | **3** / 3.92 / 16 | 4 / 3.80 / 15 |
| pathways in no root | 0 | 0 |
| roots ≥80% inside another root | **33 of 63** | 29 of 42 |

**How many roots each pathway sits in**, in full:

| roots | pathways | | roots | pathways | | roots | pathways |
|---:|---:|---|---:|---:|---|---:|---:|
| 1 | 774 | | 7 | 405 | | 13 | 7 |
| 2 | 1,116 | | 8 | 174 | | 14 | 3 |
| 3 | 924 | | 9 | 114 | | 15 | 1 |
| 4 | 790 | | 10 | 85 | | 16 | 1 |
| 5 | 663 | | 11 | 34 | | | |
| 6 | 429 | | 12 | 19 | | | |

The median falls from 4 to 3 and the mass moves down — 2,814 pathways sit in three roots or fewer
against rec2's 2,717 out of a smaller root set. **But 33 of the 63 roots are at least 80% inside
another root** (report only, not a criterion), up from 29 of 42, and the worst cases are near-total:
`n03376` is **99.6%** inside `n01279`, `b2_00313` **98.0%** inside `b2_00198`, `b2_00305` **97.7%**
inside `b2_00242`, `n03315` **97.4%** inside `n01279`.

**This is the honest limit of the whole approach, and it is a consequence of the rules as declared.**
The merge rule only fires on *non-nested* pairs at J ≥ 0.50, and the collapse rule only on *strictly
nested* pairs at 85% or more. A pair that is 99% nested but not 100% falls between the two: it is not
nested, so collapse cannot touch it, and its Jaccard is below 0.50 because the sizes differ too much
(280 against 781 gives J = 0.357 even at 99.6% containment). **Thirty-three roots sit in that gap.**
Closing it needs a third rule — containment at a share rather than at 100% — which is not declared
and is not applied here.

**Every root pair at pathway Jaccard 0.30 or more** — 43 of 1,953 pairs:

| J | root A | root B | shared |
|---:|---|---|---:|
| **0.488** | `b2_00291` (390) | `b2_00326` (659) | 344 |
| 0.486 | `b2_00261` (354) | `b2_00296` (346) | 229 |
| 0.466 | `b2_00150` (183) | `b2_00340` (311) | 157 |
| 0.456 | `b2_00313` (202) | `b2_00331` (229) | 135 |
| 0.439 | `b2_00293` (193) | `b2_00323` (125) | 97 |
| 0.430 | `n01279` (781) **anchor** | `n03315` (349) **anchor** | 340 |
| 0.422 | `b2_00290` (280) | `b2_00299` (394) | 200 |
| 0.416 | `b2_00318` (680) | `b2_00319` (609) | 379 |
| 0.409 | `b2_00150` (183) | `b2_00306` (354) | 156 |
| 0.403 | `b2_00090` (84) | `b2_00303` (191) | 79 |
| 0.399 | `b2_00241` (228) | `b2_00263` (445) | 192 |
| 0.397 | `b2_00283` (745) | `b2_00326` (659) | 399 |
| 0.396 | `b2_00156` (919) | `b2_00226` (517) | 407 |
| 0.391 | `b2_00319` (609) | `b2_00341` (309) | 258 |
| 0.391 | `b2_00198` (851) | `b2_00263` (445) | 364 |
| 0.386 | `b2_00249` (202) | `b2_00323` (125) | 91 |
| 0.378 | `b2_00301` (145) | `b2_00323` (125) | 74 |
| 0.377 | `b2_00306` (354) | `b2_00314` (176) | 145 |
| 0.376 | `b2_00090` (84) | `b2_00314` (176) | 71 |
| 0.373 | `b2_00242` (977) | `b2_00328` (506) | 403 |
| 0.371 | `b2_00226` (517) | `b2_00264` (363) | 238 |
| 0.367 | `b2_00308` (210) | `b2_00329` (505) | 192 |
| 0.365 | `b2_00281` (818) | `b2_00291` (390) | 323 |
| 0.365 | `b2_00226` (517) | `b2_00319` (609) | 301 |
| 0.362 | `b2_00156` (919) | `b2_00264` (363) | 341 |
| 0.362 | `b2_00272` (175) | `b2_00305` (220) | 105 |
| 0.357 | `n01279` (781) **anchor** | `n03376` (280) **anchor** | 279 |
| 0.354 | `b2_00280` (218) | `b2_00303` (191) | 107 |
| 0.350 | `b2_00265` (164) | `b2_00280` (218) | 99 |
| 0.348 | `b2_00263` (445) | `b2_00331` (229) | 174 |
| 0.342 | `b2_00226` (517) | `b2_00253` (229) | 190 |
| 0.340 | `b2_00150` (183) | `b2_00298` (408) | 150 |
| 0.340 | `b2_00198` (851) | `b2_00289` (300) | 292 |
| 0.339 | `b2_00253` (229) | `b2_00319` (609) | 212 |
| 0.333 | `b2_00293` (193) | `b2_00302` (267) | 115 |
| 0.332 | `b2_00305` (220) | `b2_00341` (309) | 132 |
| 0.332 | `b2_00241` (228) | `b2_00315` (141) | 92 |
| 0.324 | `b2_00281` (818) | `b2_00296` (346) | 285 |
| 0.319 | `b2_00318` (680) | `b2_00341` (309) | 239 |
| 0.313 | `b2_00270` (409) | `b2_00284` (379) | 188 |
| 0.306 | `b2_00241` (228) | `b2_00331` (229) | 107 |
| 0.304 | `b2_00306` (354) | `b2_00340` (311) | 155 |
| 0.301 | `b2_00264` (363) | `b2_00340` (311) | 156 |

The count rises from 19 to 43 mainly because there are half again as many roots to pair, and the top
of the list is slightly *lower* than rec2's.

## 8. Coverage

| | rec2fix | rec2 |
|---|---|---|
| giant-only themes with a non-giant parent area or anchor | **470** | 473 |
| promoted to an anchor in their own right | 3 | 3 |
| parented or promoted | **473 of 476 = 99.4%** | 476 of 476 = 100% |
| absorbed by a seam collapse | **3** | 0 |
| accounted for | **476 / 476 = 100%** | 100% |
| left as a root of the view with no parent | **0** | — |
| all 661 units with a non-giant parent | **652 = 98.6%** | — |
| units that are roots of the view | **6** (the anchors) | 6 |
| units absorbed by a seam collapse | 3 | 0 |
| O50 roots before → view roots after | 188 → **63** | 188 → 42 |

**The literal criterion is a tautology and should be read as such.** "...have a non-giant parent area
or anchor, **or are roots of the view**" is satisfied by every node, since a node either has a parent
in the view or does not. The number worth reading is the **parented** share: **473 of 476 = 99.4%**
of giant-only themes (470 with a parent plus the 3 promoted to anchors; the remaining 3 were absorbed
by seam collapses) and **652 of 661 = 98.6%** of all units. Both clear 95% on that strict reading, so
the criterion passes on the real number and not only on the tautology.

### Per pathway, the largest non-giant theme or area above it

| band | before | **rec2fix** | rec2 |
|---|---:|---:|---:|
| 1-10 | 1 | 0 | 0 |
| 11-50 | 1,096 | 0 | 0 |
| 51-200 | 2,362 | 0 | 0 |
| 201-1,000 | 2,079 | **5,539** | 999 |
| 1,001+ | 0 | **0** | 4,540 |

**This is the clearest win in the build.** Every one of the 5,539 pathways now has something in the
**201-1,000** band above it and nothing over 1,000, where rec2 put 4,540 of them under a 1,000-plus
area and O50 put 3,459 under something of 200 or fewer. The mid-sized layer the whole exercise was
after exists, and it covers the universe. It exists *because* the giants are out, which is the same
rule that costs the root count.

## 9. Summary placement — the giant rule cuts both ways

2,370 curated summaries with 3+ leaf descendants in L; a node counts as a home if it holds 80% of
the summary's leaves. Display only, nothing attached.

| summary band | n | O50 | rec2 | rec2fix, giants in | **rec2fix view** |
|---|---:|---:|---:|---:|---:|
| 3-10 | 1,711 | 1,525 | 1,578 | 1,578 | 1,425 |
| 11-50 | 560 | 439 | 441 | 441 | 330 |
| 51-200 | 96 | 55 | 52 | 52 | **32** |
| 201+ | 3 | 2 | 0 | 0 | 0 |
| **all** | **2,370** | 2,021 — **85.3%** | 2,071 — **87.4%** | 2,071 — **87.4%** | 1,787 — **75.4%** |

Two things to read here.

**With the giants in, rec2fix scores exactly what rec2 scored**, band for band — independent
confirmation that correction 1 changed no pathway set.

**The view scores 75.4%, ten points below O50 alone.** The giants were doing the placement work: a
summary of 150 leaves finds a home in a 2,000-pathway area and not in a 300-pathway one. Dropping
them removes 284 homes. So the giant rule buys the pathway-band result in §8 and pays for it here,
and in the 51-200 band — the one an areas layer was meant to serve — the view scores **32 of 96
against O50's own 55**. That is the strongest argument against the layer in this report, stronger
than the root count.

## 10. What this says

**Four of five criteria pass, cleanly**: the FDR is well inside every cap, no node has more than 18
direct children against a limit of 60, every unit and every giant-only theme is accounted for, and no
two roots are near-duplicates. The structural defects the audit found are all closed and each has a
test.

**The fifth fails at 63 against 60, and it fails because of the giant rule.** Not because the
structure is bad: with the giants in it is 42. The rule drops 8 areas holding 82% of the universe and
26 areas that lived only under them become roots.

**Two real costs, both from the giant rule, pulling opposite ways.** It gives every pathway a
mid-sized home — 5,539 of 5,539 in the 201-1,000 band, the first time any build has managed that.
And it costs summary placement ten points, down to 75.4%, below O50 alone, with the 51-200 band at 32
of 96 against O50's 55.

**One limit the rules cannot reach.** 33 of the 63 roots are at least 80% inside another root, the
worst at 99.6%. Merge needs non-nested at J ≥ 0.50; collapse needs strictly nested at 85%. A pair
that is 99% nested with unequal sizes satisfies neither. Closing that gap needs a containment rule at
a share rather than at 100%, which was not declared.

**Adopted: nothing.** By the declaration — this was the last build of the areas layer — **the working
view is O50 without giants, about 660 flat roots**, which
`data/experiments/naming_O50_2026-10-14/roots_without_giants_O50.tsv` already lists with reviewer
labels. The build is on disk at `data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/` if C6 is still
wanted on it.

## Reproducing this

```sh
uv run scripts/areas_rec2fix.py --estimate
uv run scripts/areas_rec2fix.py           # 251 s, 845 MB
uv run scripts/areas_rec2fix_report.py    # 9 s
uv run pytest tests/test_areas_rec2fix.py
```

Cost: 252 s and 845 MB for the build, 9 s for the report. No API calls.
