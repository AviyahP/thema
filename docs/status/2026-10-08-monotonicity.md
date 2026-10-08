# Does thematic clustering preserve gene containment? 8 Oct 2026

Aviyah's concern, in full: *"if thematic clustering/distances don't preserve monotonicity (gene
containment) we might as well throw them to the bin."*

It is the right question to ask, and it is the sharpest one asked of THEMA so far, because it is not
about how well the method scores — it is about whether the thing it produces is an ontology at all.
Curated hierarchies are built on containment. If a parent's genes contain its child's and THEMA's
distances are indifferent to that, then the themes are groupings of *wordings* and the DAG is a
stack of verbal similarities with biological labels on it.

**The answer is that monotonicity holds, in every form it can be tested, and the approach does not
go in the bin.** But the question has four distinct parts that do not stand or fall together, and
one of them is weak in a way worth knowing about. Reproduce all of it with:

```sh
uv run scripts/monotonicity_check.py                                    # the frozen v0.3 build
uv run scripts/monotonicity_check.py --build data/ontology/v0.4/ablate_baseline
```

Read-only, no API spend, ~90 s.

## 1. The ground truth is *perfectly* monotone, so this is a hard property, not a soft one

| | |
|---|---|
| Reactome parent–child edges with genes on both sides | 2,852 |
| parent genes contain child genes | **100.0%** |
| median share of the child's genes present in the parent | 1.00 |

Not 97%, not "mostly" — every single curated edge satisfies containment exactly. So there is no
slack to hide in: a method that violated containment would be violating something the reference
never does.

## 2. THEMA's DAG is also perfectly monotone — and it is not monotone by triviality

| build | edges | parent ⊇ child in genes | parent adds ≥1 gene |
|---|---:|---:|---:|
| A (frozen v0.3, `recurrent_dag_10770`) | 8,208 | **100.0%** | 89.1% |
| v0.4 baseline | 8,185 | **100.0%** | 89.1% |

Every edge in both builds satisfies containment. This is structural rather than lucky: a theme is a
*set of pathways*, an edge means the child's pathway set is contained in the parent's, and gene-set
union is monotone under set inclusion — so gene containment follows for free. **The architecture
cannot violate monotonicity**, which is the single most important fact in this note.

The 89.1% matters as much as the 100%. If the DAG were a chain of themes with identical gene sets,
containment would hold vacuously and mean nothing. Instead nearly nine edges in ten have the parent
*strictly* adding genes, so each step up the hierarchy is a real generalisation.

## 3. The grouping is strongly gene-coherent, against a random baseline that is stark

Within-theme pathway pairs, themes of 3–10 members:

| build | pairs | share **no** gene | one set nests in the other | median gene Jaccard |
|---|---:|---:|---:|---:|
| A (frozen v0.3) | 72,725 | **15.5%** | 32.7% | 0.119 |
| HiDeF k5/maxres800 | 43,577 | 15.9% | 32.8% | 0.114 |
| KC2 | 7,247 | 15.8% | 42.3% | 0.200 |
| naive K | 7,996 | 13.4% | 44.8% | 0.217 |
| *random pathway pairs* | 20,000 | *85.3%* | — | — |

84.5% of co-themed pairs share at least one gene, against 14.7% for random pairs — a **5.8×
enrichment**. And a third of co-themed pairs are in an outright containment relation. The themes are
not verbal artefacts; the text and the genes agree far more often than chance allows.

This also reframes a claim from the 5 Oct work. The specificity AUROC was computed deliberately on
*zero-gene-overlap* sibling pairs, and that was presented as THEMA finding relationships genes miss.
That framing survives, but it needs the number above beside it: those pairs are the **15.5%
minority**, not the typical case. The honest statement is that THEMA groups gene-related pathways
most of the time and occasionally groups gene-disjoint ones — not that it routinely ignores genes.

## 4. Distances grow with containment depth — but orientation is a separate question

**Magnitude — monotone, decisively.** For curated chains child ⊆ parent ⊆ grandparent, monotone
distance requires d(child, parent) < d(child, grandparent):

| | |
|---|---|
| chains | 2,720 |
| d(child, parent) < d(child, grandparent) | **83.8%** (p = 1.4 × 10⁻²⁹⁶) |
| restricted to *strict* containment at both steps (2,443) | 83.8% |
| mean distance to parent / grandparent | 0.148 / 0.192 |

Chance is 50%. Containment depth is legible in the embedding geometry, and the effect does not
depend on the loose-containment cases.

**Orientation — present, but not where you would first look for it.** Given a containment pair, can
the embedding say which one is the *general* one?

| rule | accuracy |
|---|---|
| "the parent has more genes" | **100.0%** (true by construction) |
| linear probe on the pair difference vector, 5-fold CV | **85.4% ± 1.7%** |
| "the parent sits nearer the corpus centroid" | 46.1% |

The centroid heuristic fails — worse than a coin flip. But that is the heuristic failing, not the
embedding: a trained linear probe recovers direction at 85.4%, so the information is there and is
simply not a radial property of the space. The first measurement would have been a false alarm, and
it is the reason this note reports a probe rather than stopping at one intuition.

**The real caveat is about the benchmark, not the method.** Gene counts settle direction at 100% for
free. So any direction benchmark built from curated parent–child pairs is solvable without reading a
word of text, which is the same thing the direction pilot ran into — it scored 62.5% against a 70%
bar while "the parent has more genes" scored 96.5% on those very pairs. **A text-direction benchmark
whose answer is a free function of gene-set size cannot tell you whether your text model is good.**
That measurement needs redesigning before it is worth spending on again.

## What this means

THEMA never asks the distances to carry direction. Themes come from distances; the **ordering comes
from pathway-set containment**, which is exact and is where the 100% in §2 comes from. The one
property the distances are weakest at is the one property the architecture does not depend on.

So, against the concern as posed:

| | |
|---|---|
| curation is gene-monotone | 100% — a hard constraint |
| THEMA's DAG is gene-monotone | **100%**, structurally, 89.1% strictly |
| co-theming implies gene relatedness | 84.5% vs 14.7% random — 5.8× |
| distance tracks containment depth | 83.8%, p ≈ 10⁻²⁹⁶ |
| direction recoverable from text | 85.4% probe (46.1% for the naive rule) |

Nothing here goes in the bin. What *should* go in the bin is the direction benchmark in its current
form, because gene counts answer it for free.

**One thing this does not test.** Every number above uses Reactome's relation file, because it is the
only reference whose containment is exact by construction. The GO closure is a different structure —
`part_of` and the three `regulates` relations do not imply gene containment the way Reactome's
hierarchy does — so GO-based monotonicity is a separate measurement and is not claimed here.

---

# Reviewer critique, 8 Oct

The reviewer's notes are at [`docs/spec/2026-10-08-reviewer-monotonicity-notes.md`](../spec/2026-10-08-reviewer-monotonicity-notes.md).
They accept the numbers above and argue the note answered a different question from the one asked.
**On the main charge they are right.** Point by point, with the measurements that settle each:

```sh
uv run scripts/monotonicity_followup.py     # read-only, ~3 min, all four checks below
```

## (a) "Theme-level containment is true by construction" — AGREE

It is, and §2 above says so in its own text ("structural rather than lucky"). But I then called it
"the single most important fact in this note", and that was the wrong framing: a property that
follows from the definitions cannot be evidence that the distances respect gene containment. It
rules out one failure mode a priori; it confirms nothing empirically. I should have presented it as
a precondition and moved on.

One qualification I do stand behind: the **89.1% strictly-adds-genes** figure is not construction.
It rules out the vacuous case where parents repeat their children's gene sets, which containment
alone permits. It says the hierarchy generalises; it says nothing about placement.

## (b) "The concern was pathway-level placement, and the note does not test it" — AGREE, and worse than reported

This is the real failure and I missed it. Re-measured independently rather than quoted, over
curated parent→child pairs where the parent's genes strictly contain the child's:

| build | parent at/above child, by entry size | matched random | by depth | matched random |
|---|---:|---:|---:|---:|
| v0.3 `recurrent_dag_10770` | 68.1% | 57.1% | 70.6% | 54.5% |
| **v0.4** `thema_10770` | 67.7% | 57.1% | 69.9% | 54.9% |
| HiDeF k5/800 | 71.9% | 61.1% | 71.3% | 57.1% |

My aggregate numbers come out higher than the reviewer's §2b (68.1% against 60.6%) because the pair
populations differ — they used any gene-nested pair at ≥90% containment, I used curated parent–child
pairs — but that difference is immaterial, because the aggregate is the wrong statistic. The
reviewer says the excess is "mostly ties". It is, and the sharp version makes it unambiguous:

| build | tied | **among untied pairs, parent is the higher one** |
|---|---:|---:|
| v0.3 | 40.7% | **46.2%** of 7,686 |
| **v0.4** | 40.1% | **46.1%** of 7,997 |
| HiDeF k5/800 | 46.1% | **48.0%** of 7,535 |

Chance is 50%. Every engine is at or slightly *below* it. **Placement of curated parents is
direction-blind, and v0.4 does not fix it** — it is not a tuning problem or an engine problem, it is
a property of clustering on description similarity. This is the finding that matters most in this
document and it is the reviewer's, not mine.

## (c) "The linear probe is supervised on the answer key" — AGREE; all three controls run

**LABEL, as required: the probe is supervised on the answer key and is not usable in construction.**
It shows the information is linearly present in the embedding; it cannot order anything without
first being trained on curated GO/Reactome labels, which is the structure one is trying to recover.

The three required controls, on 14,703 pairs (Reactome 2,675, GO 12,028):

| control | accuracy |
|---|---|
| folds grouped by top-level branch (5 folds) | **84.7% ± 3.0%** |
| *(the ungrouped figure the note reported)* | *85.4% ± 1.7%* |
| train Reactome → test GO | 80.8% |
| train GO → test Reactome | 85.3% |
| **description length alone** | **71.7%** |
| length-matched quartile (3,773 pairs), full vectors | 79.2% |

The reviewer named two inflation risks. **Risk (i), fold leakage across a shared parent, is not
confirmed**: grouping by top-level branch moves 85.4% to 84.7%, inside the fold spread. **Risk (ii),
style proxies, is substantially confirmed**: description length *alone* reaches 71.7%, so most of
the margin over chance is length, not content. The vectors add about 13 points over length, and
79.2% survives length matching — so there is real signal beyond style, but far less than 85% implied.
Demanding these controls was correct and it changed the number's meaning.

## (d) "The benchmark is not flawed because gene counts answer it" — PARTLY DISAGREE

I concede the main point. "What should go in the bin is the direction benchmark" was too strong, and
I withdraw it. Gene-set size orders curated pairs perfectly because Reactome unions and GO
propagation *produce* those sizes; that makes it a leaky baseline for validation, and a leaky
baseline is a reason to report it alongside, not to discard the task. A text method must be judged
on text, as the notes say.

Where I still differ is a distinction the notes do not draw. **Gene sets are input data, not labels.**
They are present in `data/pathways.tsv` before any curated hierarchy is consulted, so
"the parent has more genes" is available *at construction time* — unlike the probe in (c), which
needs the answer key. That makes gene-set size circular as *validation* and legitimate as a
*construction signal*. Two consequences follow, and only the first is the reviewer's:

1. The benchmark stays, and must always be reported beside the leaky baseline. Agreed.
2. A separate question remains open: if an ordering signal is free at construction time, what is
   text-only direction *for*? That is not an argument against measuring it — it is an argument that
   the measurement should not be on the critical path until there is a reason to prefer text over a
   signal already in hand. I do not think (d) settles this, and I am not claiming it settles it
   either way.

## (e) "Co-themed gene sharing is inflated by parent+child pairs" — AGREE, and measured

Correct in direction. Splitting the within-theme pairs (themes of 3–10):

| pair kind | v0.3 | v0.4 | HiDeF k5/800 |
|---|---:|---:|---:|
| curated parent–child pairs | 100.0% | 100.0% | 100.0% |
| **pairs with no curated relation** | **81.3%** | **81.2%** | **80.7%** |
| random pairs | 15.2% | 15.2% | 15.2% |

So the note's pooled 84.5% was inflated — by about 3 points. After removing every curated relative,
co-themed pairs still share a gene 81.3% of the time against 15.2% at random, a 5.3× enrichment.
The correction is real and the conclusion it was supporting is unchanged.

## (f) "The note is Reactome only" — AGREE, and GO now measured

The note flagged this, which is not the same as doing it. Over the primary closure (clarification 9:
`is_a`, `part_of` and the three `regulates` relations), 12,050 GO edges with genes on both sides:

| | |
|---|---|
| parent genes contain child genes | **99.8%** |
| parent and child share a gene | 100.0% |
| median share of the child's genes in the parent | 1.00 |

So GO behaves like Reactome, and the Reactome-only scope was not hiding a different answer. The
0.2% that fail — about two dozen edges — are the cases where `part_of` or `regulates` links terms
whose annotation sets are not nested, which is the mechanism the note predicted would break
containment if anything did.

## Where this leaves the note

Corrected standing of each claim:

| claim | standing |
|---|---|
| curation is gene-monotone (Reactome 100%, **GO 99.8%**) | holds, now both sources |
| THEMA's DAG is gene-monotone | holds, but **true by construction** — not evidence |
| co-theming implies gene relatedness | holds at **81.3%** vs 15.2% once relatives are removed |
| distance tracks containment depth (83.8%) | holds |
| direction recoverable from text | **84.7%** grouped, but **71.7% from length alone**, and supervised |
| **curated parents are placed at or above their children** | **FAILS — 46.1% among untied pairs, at chance** |

The distances do not go in the bin: they group gene-related pathways far better than chance and
they track containment depth. What fails is **placement** — THEMA builds a coherent hierarchy that
does not put curated summaries above what they summarise, because general pathways cluster with
general pathways. The reviewer's §2c explains the mechanism and their §4 draws the consequence,
which is the leaves experiment: build from the atomic pathways and test whether the summaries are
recreated rather than scattered.
