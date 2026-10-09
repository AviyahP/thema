# Measuring the three redundancy shapes before choosing a rule. 9 Oct 2026

Declared 9 Oct before any result. **Report only — nothing was rebuilt.** Read from the cached
`thema_L_repair` build and the cached per-node stats. **No rule is applied**; the candidate counts
in
§4 are arithmetic on the existing build.

The reviewer's plausibility review left four open issues
(`docs/status/2026-10-09-reviewer-plausibility.md`); three are structure that looks redundant by eye
and sits **below every threshold the build applies**. Here is how much of it there is.

**Three results worth having up front.**

1. **The chain histogram is empty above 0.90** — the declared collapse already took that range, so
   "is there a valley near 0.85–0.95?" cannot be answered above 0.90 from this build. Below it the
   counts fall smoothly with one shallow local minimum, at **0.800–0.825**, not at 0.85–0.95.
2. **The repair worked exactly as specified**: of 37,239 non-nested sibling pairs, **zero** are at
or
   above 0.70. The population is all below the merge, by construction.
3. **A fan merge is not local.** Merging `n00150`'s six parents into their union would leave only
   **4 of the 17 ancestors above them distinct** — 13 would themselves become near-duplicates. The
   lattice collapses with the fan.

## 1. Chain ratios: |child| / |parent|

19,134 edges fall in 0.5–1.0; a further **7,683 edges are below 0.5**.

| bin | all | parent 3–10 | 11–50 | 51–300 | 301–1000 | 1001+ |
|---|---:|---:|---:|---:|---:|---:|
| 0.500–0.525 | 991 | 294 | 663 | 34 | 0 | 0 |
| 0.525–0.550 | 715 | 0 | 688 | 27 | 0 | 0 |
| 0.550–0.575 | 732 | 187 | 517 | 27 | 0 | 1 |
| 0.575–0.600 | 1,031 | 231 | 775 | 25 | 0 | 0 |
| 0.600–0.625 | 693 | 139 | 528 | 25 | 0 | 1 |
| 0.625–0.650 | 896 | 0 | 879 | 17 | 0 | 0 |
| 0.650–0.675 | 873 | 191 | 662 | 20 | 0 | 0 |
| 0.675–0.700 | 1,057 | 351 | 687 | 19 | 0 | 0 |
| 0.700–0.725 | 606 | 0 | 588 | 18 | 0 | 0 |
| 0.725–0.750 | 1,177 | 4 | 1,146 | 27 | 0 | 0 |
| 0.750–0.775 | 551 | 0 | 535 | 16 | 0 | 0 |
| 0.775–0.800 | 793 | 21 | 749 | 23 | 0 | 0 |
| **0.800–0.825** | **415** | 0 | 396 | 19 | 0 | 0 |
| 0.825–0.850 | 417 | 0 | 391 | 26 | 0 | 0 |
| 0.850–0.875 | 323 | 0 | 304 | 19 | 0 | 0 |
| 0.875–0.900 | 181 | 0 | 161 | 20 | 0 | 0 |
| 0.900–1.000 | **0** | 0 | 0 | 0 | 0 | 0 |

**edges in 0.85–0.90: 550. edges in 0.80–0.85: 1,052.**

**Is there a natural gap or valley near 0.85–0.95?** No — and the question is partly unanswerable on
this build. The shape over 0.75–1.0 is `551, 793, 415, 417, 323, 181, 0, 0, 0, 0`: a decline from
0.775–0.800 down to 0.875–0.900, then nothing, because the 90% collapse removed everything above.
The **only local minimum is 0.800–0.825**, and it is shallow (415 against 793 and 417 either side).
There is no clean valley to justify 0.85 over 0.90 or 0.80 on the shape of this distribution.

Note also that almost all of it is **parent band 11–50**: the 301–1000 and 1001+ columns are
essentially empty, so chain structure is a small- and mid-theme phenomenon, not what makes the
giants.

### Examples, 0.85–0.90 — four of five have an identical nearest-name triple

| child | parent | ratio | support child / parent | nearest the centroid |
|---|---|---:|---|---|
| `n03209` (121) | `n03679` (135) | 0.896 | 0.235 / 0.185 | **identical**: negative regulation of meiotic cell cycle phase transition; regulation of meiosis I; positive regulation of fertilization |
| `n04214` (102) | `n05613` (114) | 0.895 | 0.130 / 0.065 | **identical**: mitochondrial tRNA modification; mitochondrial translational elongation; mitochondrial translational termination |
| `n01319` (83) | `n02794` (96) | 0.865 | 0.675 / 0.290 | **identical**: DNA strand elongation involved in DNA replication; HALLMARK_DNA_REPAIR; nucleotide-excision repair |
| `n03476` (78) | `n03797` (89) | 0.876 | 0.205 / 0.170 | near-identical: vesicle fusion with Golgi apparatus / protein localization to Golgi membrane; COPI-coated vesicle budding; HALLMARK_PROTEIN_SECRETION |
| `n04348` (71) | `n01319` (83) | 0.855 | 0.120 / 0.675 | **identical** to its parent, which is itself the child in row 3 — a chain of three |

That last row matters: `n04348 → n01319 → n02794` is a three-link chain at 0.855 and 0.865, all
three with the same nearest names. A 0.90 collapse leaves all three.

### Examples, 0.80–0.85

| child | parent | ratio | support |
|---|---|---:|---|
| `n07994` (170) | `n06035` (201) | 0.846 | 0.030 / 0.055 |
| `n03723` (147) | `n00135` (180) | 0.817 | 0.235 / 0.990 |

Full lists in `data/experiments/redundancy/measure.json`.

## 2. Sibling near-twins

**37,239 pairs** share a parent and are not nested.

| bin | count |
|---|---:|
| 0.400–0.425 | 965 |
| 0.425–0.450 | 832 |
| 0.450–0.475 | 756 |
| 0.475–0.500 | 1,017 |
| 0.500–0.525 | 255 |
| 0.525–0.550 | 780 |
| 0.550–0.575 | 579 |
| 0.575–0.600 | 644 |
| 0.600–0.625 | 463 |
| 0.625–0.650 | 423 |
| 0.650–0.675 | 251 |
| 0.675–0.700 | 225 |

| threshold | pairs at or above |
|---|---:|
| 0.50 | **4,345** |
| 0.60 | **1,572** |
| 0.65 | **514** |
| 0.70 | **0** |

**Zero at or above 0.70 is the repair's signature** — fix 1 guaranteed it and the independent count
confirms it.

### Examples, 0.60–0.70

| pair | sizes | supports | J | nearest names |
|---|---|---|---:|---|
| `n04423` / `n08076` | 29, 27 | 0.470 / **0.030** | 0.697 | **same three**, reordered: STAT5 Activation; response to interleukin-3; interleukin-3-mediated signaling |
| `n02740` / `n03135` | 25, 31 | 0.300 / 0.245 | 0.697 | estrogen response, differing only in *PTK6 Expression* |
| `n01798` / `n07023` | 25, 31 | 0.510 / **0.040** | 0.697 | BRCA1/BRCA2 homologous recombination defects |
| `n07013` / `n07019` | 38, 40 | 0.040 / 0.040 | 0.696 | **same three**, reordered: Acyl chain remodelling of PG; Synthesis of PA; phosphatidylglycerol acyl-chain remodeling |
| `n06128` / `n06141` | 19, 20 | 0.055 / 0.055 | 0.696 | phospholipid translocation, differing on *aminophospholipid* vs *sphingolipid* |

The pattern in three of five: **a well-supported theme beside a near-copy at support 0.03–0.055.**

### The named pair

**`n02333` (50, support 0.620) / `n03211` (52, support 0.235): Jaccard 0.594.**

Both are specialised pro-resolving mediators — *Biosynthesis of aspirin-triggered D-series
resolvins; Biosynthesis of E-series 18(R)- and 18(S)-resolvins; lipoxin A4 metabolic process* — the
same four nearest names in a different order. **It sits just below 0.60, so a sibling rule at 0.60
would not catch it.** 0.59 is also where 463 pairs sit in the 0.600–0.625 bin immediately above, so
this pair is on the wrong side of a line drawn through a dense region.

## 3. Fans

**274 nodes** have three or more parents where *every* parent is the child plus at most 5 members.

| parents per fan node | nodes |
|---|---:|
| 3 | 197 |
| 4 | 50 |
| 5 | 19 |
| 6 | 8 |

**Fan parents' support: median 0.159, mean 0.259, and 56.2% are at or below 0.2.**

The shape is consistent across every example: **a very high-support core surrounded by low-support
near-identical variants.**

| fan node | size | support | parents and their supports |
|---|---:|---:|---|
| **`n00150`** | 7 | **0.990** | 0.555, 0.200, 0.140, 0.065, 0.060, 0.050 |
| `n00143` | 8 | **0.990** | 0.350, 0.070, 0.035, 0.030, 0.030, 0.030 |
| `n00271` | 8 | **0.975** | 0.400, 0.065, 0.056, 0.055, 0.045, 0.030 |
| `n00345` | 8 | **0.965** | 0.385, 0.170, 0.110, 0.055, 0.055, 0.035 |
| `n01910` | 8 | 0.480 | 0.210, 0.140, 0.135, 0.085, 0.055, 0.045 |

`n00143` is the starkest: a cell-cycle core at support 0.990, and **five of its six parents have the
identical nearest-name triple** (*Phosphorylation of proteins involved in G1/S transition by active
Cyclin E:Cdk2 complexes; Defective binding of RB1 mutants to E2F1; Inhibition of replication
initiation of damaged DNA by RB1/E2F1*) at supports 0.070, 0.035, 0.030, 0.030, 0.030. `n00271`
(methionine/folate) and `n00345` (spinal cord patterning) are the same pattern.

## 4. What each candidate rule would remove — counts only, nothing applied

**Amended 9 Oct, after Aviyah's decision: there is no fan-merge candidate.** A fan of facet parents
around a stable core is **intended multi-parent DAG behaviour, not redundancy**, so fans are
measured
and described in §3 and §5 and **no removal rule is proposed for them**. The two candidates are:

| candidate rule | what qualifies |
|---|---|
| **chain collapse at 0.85** | **550 edges**, touching **550 distinct children** — 6.3% of themes |
| **sibling merge at Jaccard ≥ 0.60** | **1,572 pairs**, at most **1,393 themes** dropped if one of each pair goes |
| ~~fan merge~~ | **not proposed.** 274 fans over 897 parent themes, measured not gated |

Two observations, neither a recommendation.

- Chain collapse at 0.85 is **small and safe-looking**: 550 edges, and the examples are
  name-identical pairs. It does not reach the three-link chain `n04348 → n01319 → n02794` in one
  pass, since each link is 0.855–0.865; iterating to a fixed point would, as the 0.90 collapse
  already does.
- Sibling merge at 0.60 is **an order of magnitude larger** — up to 1,393 themes, 16% of the build —
  and it cuts through a dense part of the distribution rather than a gap. It would also **miss** the
  `n02333`/`n03211` pair at 0.594 while removing 1,572 others.

### The sibling rule against `n00150`'s six parents

> Superseded in scope by **"Worked example"** below, which covers all 24 non-giant ancestors and both
> readings of the rule. This subsection covers the six parents only.

Because fans are now declared intended structure, a sibling rule has to be chosen knowing what it
would do to one. `n00150`'s six parents, with the reviewer's facet judgement:

| parent | size | support | reviewer's judgement |
|---|---:|---:|---|
| `n01638` | 10 | 0.555 | shape change via G12/13 — distinct |
| `n03581` | 11 | 0.200 | BTM platelet-activation modules — distinct; adds *platelet activation (II)*, *cytoskeletal remodeling* |
| `n04153` | 11 | 0.140 | GPVI + GPCR convergence on PLC — distinct |
| `n05795` | 10 | 0.065 | prostanoid receptor family — distinct, thin |
| `n05989` | 11 | 0.060 | Rap1 integrin activation — only Rap1 is new |
| `n06563` | 11 | 0.050 | Gq–PLC–IP3 / 5-HT2A — distinct, overlaps `n04153` |

**Only 3 of the 15 pairs among the six are siblings** — `n03581`/`n05989` (J 0.692),
`n01638`/`n06563` (0.500) and `n01638`/`n04153` (0.500). The other twelve do **not** share a parent,
so **a sibling rule cannot reach them at any threshold**: the fan is held together by `n00150` as
their common *child*, not by a common parent.

| threshold | sibling pairs merged | which parents absorbed | facets lost |
|---|---:|---|---:|
| 0.50 | 3 | `n04153`, `n05989`, `n06563` | **3** |
| 0.55 | 1 | `n05989` | 1 |
| 0.60 | 1 | `n05989` | 1 |
| 0.65 | 1 | `n05989` | 1 |
| 0.70 | 0 | none | 0 |

**And the rule deletes a facet that contributes something no other does.** At 0.55–0.65 it merges
`n03581`/`n05989` and drops the lower-support one — `n05989` at 0.060 — which is the only parent
carrying Rap1 signalling (`reactome:R-HSA-392517`). Corrected 9 Oct: the reviewer never judged
`n03581` not distinct. **Every one of the six parents adds at least one pathway no co-parent has**
-- `n03581` adds *platelet activation (II)* and *cytoskeletal remodeling* (`btm:M32.1`,
`btm:M32.8`); `n05989` adds Rap1 signalling (`reactome:R-HSA-392517`). ccode's unique-contribution
measurement confirms it independently: 2, 2, 2, 3, 1 and 3 unique members respectively, none of
the six at zero. So support-based
tie-breaking is not facet-aware: it removes a parent for recurring less often, not for adding
nothing.

At 0.50 it would remove three of the six declared facets. At 0.70 it removes nothing, which is where
the build already is.

## 5. The lattice above `n00150`

> **Scope note, added 9 Oct.** This section counts ancestors **within three levels** and finds 17.
> `REPORT3.md` §3 counts **all** ancestors at any depth and finds 28, of which 4 are giant roots and
> 24 are judged. The **"Worked example"** section below uses the full scope and agrees with REPORT3
> exactly. The 17 here is not wrong, it is a narrower question; the figure to quote is 24.

Six parents: `n01638` (10 members, support 0.555), `n03581` (11, 0.200), `n04153` (11, 0.140),
`n05795` (10, 0.065), `n05989` (11, 0.060), `n06563` (11, 0.050).

**17 distinct ancestors within three levels**, and **not one covers all six**:

| ancestor | level | size | support | covers | nearest the centroid |
|---|---:|---:|---:|---:|---|
| `n03820` | 2 | 13 | 0.170 | 1/6 | ADP signalling through P2Y purinoceptor 1; Thrombin signalling through PARs |
| `n01273` | 2 | 14 | 0.690 | 2/6 | ADP / thrombin signalling |
| `n05194` | 2 | 14 | 0.080 | 1/6 | ADP signalling; platelet activation (III) |
| `n04961` | 2 | 15 | 0.090 | 2/6 | ADP / thrombin signalling |
| `n07792` | 2 | 16 | 0.035 | 2/6 | ADP signalling; platelet activation (I) |
| `n06758` | 3 | 17 | 0.045 | 1/6 | platelet activation (III); thrombin-activated receptor signalling |
| `n07791` | 2 | 17 | 0.035 | 2/6 | ADP / thrombin signalling |
| `n03907` | 2 | 18 | 0.160 | 3/6 | ADP / thrombin signalling |
| `n02906` | 3 | 20 | 0.275 | 2/6 | ADP signalling; thrombin-activated receptor signalling |
| `n05156` | 3 | 21 | 0.080 | 3/6 | ADP / thrombin signalling |
| **`n07565`** | 3 | 26 | 0.035 | **4/6** | Thrombin signalling through PARs; platelet activation |
| **`n00918`** | 2 | 27 | **0.845** | 3/6 | ADP signalling; platelet activation (III) |
| `n01879` | 3 | 32 | 0.485 | 3/6 | thrombin-activated receptor signalling; platelet activation (III) |
| `n03842` | 3 | 35 | 0.375 | 4/6 | platelet activation (I); Thrombin signalling through PARs |
| **`n02115`** | 3 | 77 | **0.855** | **4/6** | Defective F9 activation; platelet activation and degranulation; Fibrin formation |
| `n03423` | 2 | 139 | 0.210 | 4/6 | thrombin-activated receptor signalling; cyclooxygenase pathway |
| `n01755` | 3 | **2,527** | 0.520 | 5/6 | neural plate morphogenesis; Ephrin signaling; Activation of RAC1 — **a giant root** |

**Ancestors covering all six: NONE.** The reviewer's account is confirmed, with two small
corrections: there are **17** ancestors within three levels, not about twenty, and **`n02115` covers
4 of 6, not 3**. `n07565` (26, 4/6) and `n00918` (27, support 0.845, 3/6) are exactly as reported.
Fifteen of the seventeen are 13–35 members; above them it is `n02115` (77), `n03423` (139), and then
the giant root.

### If the six parents became their union

The union is **24 members**. Of the 17 ancestors, **only 4 would remain distinct** — Jaccard below
0.70 both to the union and to every other ancestor. **13 would themselves become near-duplicates**,
either of the union or of each other: `n03820` (J 0.42 to the union but near another ancestor),
`n01273` (0.58, near one), `n05194` (0.41, near two), `n04961` (0.50, near two), `n07792` (0.48,
near
two), `n06758` (0.37, near one), and seven more.

**So a fan merge cascades.** Collapsing the six would not leave a clean platelet-activation node
under a tidy lattice — it would leave one 24-member node and thirteen ancestors that are then
redundant with it or with each other. The redundancy is not located in the fan; the fan is the
bottom of it.

### Support above a fan vs size-matched others

3,051 nodes sit above at least one fan; 5,515 do not. **Size-matched**, because support falls with
size on its own:

| size band | n above a fan | median support | n other | median support | delta |
|---|---:|---:|---:|---:|---:|
| 3–10 | 301 | 0.340 | 2,103 | 0.530 | **−0.190** |
| 11–20 | 1,574 | 0.090 | 2,764 | 0.070 | +0.020 |
| 21–50 | 953 | 0.090 | 615 | 0.070 | +0.020 |
| 51–300 | 209 | 0.080 | 33 | 0.075 | +0.005 |

**This corrects an inference in the reviewer's addendum.** They wrote that many of the lattice nodes
have support ≤ 0.2 and that this points at the low cal8 floors. The first half is true — but nodes
above a fan are **not** systematically lower-support than other nodes of the same size. They are
0.19 lower only in the 3–10 band, and marginally *higher* in every band above it.

The low support is in the **fan parents themselves** (median 0.159, 56.2% ≤ 0.2), not in the lattice
above them. So the cal8 floors are what admit the fan's near-identical variants; the ancestors above
are ordinary nodes for their size, and they look redundant because of what is beneath them rather
than because they are weakly supported.

## Worked example: the whole `n00150` lattice under each candidate rule

Added 9 Oct per the addendum. Scope follows `REPORT3.md` §3: **all** ancestors of `n00150` at any
depth, with the four giant roots excluded as known bags. **28 ancestors: 4 giants
(`n06313`, `n03678`, `n01755`, `n05127`), 6 direct parents, 18 lattice nodes — 24 judged.** That
matches REPORT3's 28 / 4 / 24 exactly, and supersedes the "17 ancestors" in §5 above, which counted
only three levels.

Full per-node output: `data/experiments/redundancy/n00150_rules.json`.

### The 18 lattice nodes

| node | size | support | covers | nearest the centroid |
|---|---:|---:|---:|---|
| `n03820` | 13 | 0.170 | 1/6 | ADP signalling through P2Y purinoceptor 1 |
| `n01273` | 14 | **0.690** | 2/6 | ADP / thrombin signalling |
| `n05194` | 14 | 0.080 | 1/6 | ADP signalling; platelet activation (II) |
| `n04961` | 15 | 0.090 | 2/6 | ADP / thrombin signalling |
| `n07792` | 16 | 0.035 | 2/6 | ADP signalling; platelet activation (I) |
| `n06758` | 17 | 0.045 | 1/6 | platelet activation (III) |
| `n07791` | 17 | 0.035 | 2/6 | ADP / thrombin signalling |
| `n03907` | 18 | 0.160 | 3/6 | ADP / thrombin signalling |
| `n02906` | 20 | 0.275 | 2/6 | ADP signalling; thrombin-activated receptor signalling |
| `n05156` | 21 | 0.080 | 3/6 | ADP / thrombin signalling |
| `n07565` | 26 | 0.035 | 4/6 | Thrombin signalling through PARs |
| `n00918` | 27 | **0.845** | 3/6 | ADP signalling; platelet activation (II) |
| `n01879` | 32 | 0.485 | 3/6 | thrombin-activated receptor signalling |
| `n03842` | 35 | 0.375 | 4/6 | platelet activation (I) |
| `n08023` | 41 | 0.140 | 4/6 | cell movement, Adhesion & Platelet activation |
| `n04419` | 52 | 0.115 | 3/6 | platelet activation and degranulation |
| `n02115` | 77 | **0.855** | 4/6 | Defective F9 activation; Fibrin formation |
| `n03423` | 139 | 0.210 | 4/6 | thrombin-activated receptor signalling; cyclooxygenase pathway |

### Chain collapse — prunes the staircase, touches no facet

| share | absorbed | of 18 lattice | **of 6 parents** | which |
|---|---:|---:|---:|---|
| **0.80** | 6 | 6 | **0** | `n07792`→`n03907` 0.889, `n03820`→`n04961` 0.867, `n03907`→`n05156` 0.857, `n03842`→`n08023` 0.854, `n00918`→`n01879` 0.844, `n05194`→`n06758` 0.824 |
| **0.85** | 4 | 4 | **0** | the first four above |
| **0.90** | 0 | 0 | **0** | none — the build's own collapse already took this range |

**At every share, chain collapse removes zero of the six parents.** It only prunes the
over-resolved staircase REPORT3 describes inside route A — nodes that are the same theme with two to
six extra members. That is the cleanest result in this report: **the rule aimed at chains does not
touch the structure Aviyah declared intended.**

**Correction, 9 Oct.** An earlier version of this paragraph said `n00918` is absorbed "at 0.80 and
0.85". **That was wrong.** The ratio is **27/32 = 0.84375**, which is below 0.85, so `n00918` is
absorbed at the **0.80 share only** — as the table above correctly shows and the prose did not. The
figure I quoted, 0.844, is that same ratio rounded; I then described it as clearing a threshold it
does not clear. Aviyah caught it.

The substantive point survives the correction and moves to the 0.80 row: at 0.80, `n00918`
(27 members, support **0.845**) is absorbed into `n01879` (32, support 0.485). It is the node
REPORT3 names "platelet activation and adhesion" and the one four of the six parents share, and the
collapse keeps the containing parent — the less stable of the two. That is an instance of the
general pattern measured in 5a below, and it is a reason to look at the survivor rule before
choosing 0.80 over 0.85.

**One count corrected against REPORT3.** It reports "4 rungs at 0.85, 7 at 0.80". The 0.85 figure
matches exactly. At 0.80 I measure **6**, not 7: the seventh ratio it lists, `n01879`→`n08023`, is
**0.780**, which is below a 0.80 threshold. All seven are genuine strict-containment edges — I
checked — so the ratios are right and only the threshold arithmetic differs.

Finding that required fixing my own loop: when a node's target parent is itself absorbed, the child
must be re-pointed at the surviving ancestor. Without that re-link the first pass lost
`n07792`→`n03907` entirely and reported 3 at 0.85 instead of 4. The reviewer's hand count is what
exposed it.

### Sibling merge — eats facets, and the reading matters

Reported two ways, because they differ sharply here. **Strict** is the definition used everywhere
else in this report: only pairs that *share a parent*. **Loose** is any pair above the threshold,
which is what REPORT3 §3 applies to the six parents.

| threshold | reading | pairs | dropped | **of 6 parents** | of 18 lattice |
|---|---|---:|---:|---:|---:|
| **0.60** | strict | 6 | 5 | **1** — `n05989` | 4 |
| **0.60** | loose | 10 | 7 | **2** — `n05989`, `n03581` | 5 |
| **0.70** | strict | 0 | 0 | 0 | 0 |
| **0.70** | loose | 0 | 0 | 0 | 0 |

Under the **loose** reading at 0.60, three parents are involved — `n01638`/`n03581` (J 0.615),
`n01638`/`n05989` (0.615), `n03581`/`n05989` (0.692) — and two are dropped, leaving `n01638` as the
survivor. **Six facets become four.** That is REPORT3's "merge 3 of the 6 into one, leaving 4
facets", measured and confirmed; its Jaccards (0.62, 0.62, 0.69) match mine to the third decimal.

Under the **strict** reading only `n03581`/`n05989` qualifies, so one parent goes and five facets
remain.

**And in both readings the rule deletes a facet nothing else carries.** `n05989` goes because its
support is 0.060 against `n03581`'s 0.200 — but it is the only parent carrying Rap1 signalling
(`reactome:R-HSA-392517`). Corrected 9 Oct: the reviewer never judged `n03581` not distinct.
**Every one of the six parents adds at least one pathway no co-parent has** -- `n03581` adds
*platelet activation (II)* and *cytoskeletal remodeling* (`btm:M32.1`, `btm:M32.8`); `n05989` adds
Rap1 signalling (`reactome:R-HSA-392517`). ccode's unique-contribution measurement confirms it
independently: 2, 2, 2, 3, 1 and 3 unique members respectively, none of the six at zero.
Support-based tie-breaking removes a parent for
recurring less often, not for adding nothing — which is why §6 below records the
unique-contribution test as the shape a facet-aware rule would need.

At **0.70 nothing merges in either reading**, which is where the build already sits.

### The contrast this draws

| | chain collapse | sibling merge |
|---|---|---|
| what it removes here | 4–6 staircase rungs | 1–2 **declared facets** plus 4–5 lattice nodes |
| parents touched | **none, at any share** | 1 strict, 2 loose, at 0.60 |
| gets the choice right? | **no** — see 5a below: keeps the less stable node on 62% of edges | **no** — deletes the only parent carrying Rap1 |

**Chain collapse addresses the over-resolution without touching intended structure. Sibling merge at
0.60 cannot, on this evidence, be applied without deleting facets Aviyah has declared intended — and
it picks the wrong member of the pair it does catch.**

## Chain collapse: which node survives

Added 9 Oct per the follow-up. The declared rule keeps the **parent's membership** — the containing
set — and takes the higher of the two supports. Because it is a statement about membership, the node
that survives *as a node* is always the parent, whatever its own support was.

On the `n00150` lattice at 0.85, three of the four collapses drop the **more stable** node:
`n03820` (0.170) into `n04961` (0.090); `n03907` (0.160) into `n05156` (0.080); `n03842` (0.375)
into `n08023` (0.140). That is what prompted the measurement.

### (a) How often does the absorbed node have the higher support?

Over **all 550** chain edges with ratio in [0.85, 0.90):

| | edges | share |
|---|---:|---:|
| **absorbed child's support HIGHER than the surviving parent's** | **341** | **62.0%** |
| lower | 201 | 36.5% |
| equal | 8 | 1.5% |

Where the child is higher, the **median gap is +0.115** and the **maximum is +0.960** — a node at
support ~0.96 absorbed into one near zero.

**So the declared rule keeps the less stable node on 62% of the edges in this window.** It is not a
quirk of the one lattice. The rule is doing exactly what it says — the containing set survives — but
"which set contains the other" and "which theme recurs" are different questions, and on this
distribution they disagree about two times in three.

### (b) The `n00150` lattice under each survivor rule — POST-HOC

**Labelled post-hoc, and the label is not a formality:** the alternative below was written *after*
seeing that three of four collapses drop the more stable node. It is not a pre-registered rule, it
was not declared before the result, and **its performance here is not evidence for it** — it was
constructed to fix exactly these four cases and does so by construction.

| | declared rule | POST-HOC: keep the higher-support node, tie → parent |
|---|---|---|
| collapses | 4 | 4 |
| **survivor is the more stable node** | **1 of 4** | **4 of 4** |
| | drops `n03820` 0.170 → keeps `n04961` 0.090 | drops `n04961` 0.090 → keeps `n03820` **0.170** |
| | drops `n07792` 0.035 → keeps `n03907` 0.160 | drops `n07792` 0.035 → keeps `n03907` 0.160 *(tie → parent)* |
| | drops `n03907` 0.160 → keeps `n05156` 0.080 | drops `n05156` 0.080 → keeps `n03907` **0.160** |
| | drops `n03842` 0.375 → keeps `n08023` 0.140 | drops `n08023` 0.140 → keeps `n03842` **0.375** |

Both rules make the same four collapses and prune the same staircase; they differ only in which of
each pair is kept. The post-hoc rule keeps the more stable node in all four, which is what it was
written to do.

**What it does not address, and what makes it more than cosmetic.** Keeping the child means keeping
the *smaller* set, so the merged node no longer contains everything its former parent did — the
collapse stops being a containment-preserving operation, and `hasse` would have to be re-run over
a node set that is no longer nested the same way. The declared rule's choice is not arbitrary: it
keeps containment exact. A rule that keeps the higher-support node has to say what happens to the
members only the parent had. **That question is unanswered here and is the reason this is recorded
as a measurement, not a proposal.**

## IDEA, NOT ADOPTED: a unique-contribution test for fan parents

Recorded with its measurement. Rule as contemplated: remove a fan parent **only if every member it
adds is already present in a co-parent**.

On `n00150`, unique members added per parent — measured, not asserted:

| parent | support | members added | **unique to it** | which |
|---|---:|---:|---:|---|
| `n01638` | 0.555 | 3 | **2** | `btm:M30`, `reactome:R-HSA-416482` |
| `n03581` | 0.200 | 4 | **2** | `btm:M32.1`, `btm:M32.8` |
| `n04153` | 0.140 | 4 | **2** | `btm:M42`, `reactome:R-HSA-114604` |
| `n05795` | 0.065 | 3 | **3** | `btm:M130`, `btm:M155`, `reactome:R-HSA-391908` |
| `n05989` | 0.060 | 4 | **1** | `reactome:R-HSA-392517` (Rap1) |
| `n06563` | 0.050 | 4 | **3** | `go:GO:0007208`, `go:GO:0010511`, `go:GO:0032960` |

**It removes none of the six.** Every parent clears it.

Worth recording anyway, because it is the only candidate so far whose criterion is **what a node
contributes** rather than how often it recurs or how much it overlaps. The support tie-break fails
on precisely this case — it deletes `n05989` for having support 0.060 while that parent is the sole
carrier of Rap1 signalling. A rule of this shape could not make that mistake. Whether it is useful
at scale is **unmeasured**: it has been run on one fan.

## OPEN TO-DO: the floors after the 17-BTM drop

> **Consider re-running scrambles on the current universe and updating the floors later; until then
> all builds after the 17-BTM drop use the previous (cal8) floors.**

Aviyah's decision of 9 Oct: reuse the cal8 floors, calibrated on universe 10,770, for builds made
after the 17 self-described heterogeneous BTMs are dropped (universe becomes 10,753; universe L
becomes 5,542). ccode recommended a full recalibration; the decision overrides that knowingly and
the argument is kept in `docs/status/2026-10-09-reviewer-plausibility.md`.

**No check will remind anyone.** Nothing in the pipeline compares a floors file's universe against
the build's, and `pathways.tsv` is unedited because the exclusion lives in
`data/excluded_inputs.tsv` — so `universe.load_embedded`'s digest test still passes. The reuse is
recorded in four places: `DECISIONS.md`, `data/ontology/v0.4-leaves/README.md`, the `source` string
inside `regate/floors_L_cal8.json` (which `leaves_build.py` copies into every manifest it writes, so
future builds carry it automatically), and here.

## What this means

**For the chain rule.** 550 edges in 0.85–0.90, name-identical in the examples, concentrated in
parent band 11–50. There is **no valley at 0.85–0.95** to justify the cut on distributional grounds,
and the range above 0.90 is empty because the current rule already cleared it. A choice between 0.85
and 0.90 is a judgement about how much near-copy to tolerate, not a reading of the data.

The worked example adds the thing the histogram cannot show: on the one lattice anyone has
inspected,
**chain collapse removes 4 rungs at 0.85 and 6 at 0.80 and touches none of the six declared
facets.**
It prunes over-resolution without reaching intended structure.

**For the sibling rule — settled.** Aviyah decided on 9 Oct that it **stays at 0.70**, where
nothing merges in the `n00150` lattice under either reading and the build already sits. The
measured case for not lowering it: 0.60 touches 1,572 pairs and up to 1,393 themes (16% of the
build), cuts through a dense region rather than a gap, still misses the `n02333`/`n03211` pair the
review singled out, and deletes `n05989` — the only parent carrying Rap1 — for recurring less often
rather than for adding nothing.

**For fans — no rule, by decision.** Aviyah ruled on 9 Oct that a fan of facet parents around a
stable core is intended multi-parent DAG behaviour, so the 274 fans are measured and not gated. The
§5 cascade measurement is kept as evidence about the lattice rather than as an argument for merging:
it says that *if* anyone did merge a fan, 13 of the 17 ancestors above `n00150` would become
redundant too, so the fan and its lattice are one structure and a fan rule could never be local.

That decision does not mean every parent in a fan is earned. `n03581` was judged **not** a distinct
facet — it duplicates `n01638` and `n05989` at Jaccard 0.62 and 0.69. The shape is intended; an
individual redundant parent inside it is still a defect, and the sibling rule above is the wrong
instrument for finding it.

**And one thing all three share.** In every example the redundant partner carries support 0.03–0.07
while the stable member carries 0.3–0.99. The discriminating quantity is not Jaccard or ratio but
**support** — which is the same conclusion the big-theme description reached from the other end,
that
the informative number about a theme is how reliably it recurs.

**With two warnings against using support naively, and they point opposite ways.**

The sibling rule shows support deleting the wrong node: it keeps `n03581` (0.200) and removes
`n05989` (0.060), the sole carrier of Rap1. Support says which theme recurs more reliably; it does
not say which carries information the others do not. The unique-contribution idea above is the only
candidate that asks the second question, and it removes nothing on the one fan it has been run on.

The chain rule shows the opposite failure: it ignores support entirely, keeping the containing set,
and so **keeps the less stable node on 62% of the 550 edges in [0.85, 0.90)** — median gap 0.115,
maximum 0.960. Fixing that is not free: keeping the higher-support node means keeping the smaller
set, which breaks the containment the collapse is defined on. Neither rule is simply wrong; each is
answering a different question from the one the shape poses.

No rule is proposed and none is applied. Nothing is frozen. **Aviyah decides.**

Written: `data/experiments/redundancy/measure.json` (full histograms, all examples, all 274 fans),
`fan.json` (the `n00150` lattice and the size-matched support comparison).
