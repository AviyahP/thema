# Open question, 26 Sep 2026 — does Ward cluster raw or centred vectors?

*Recorded BEFORE any measurement, with the reading declared in advance. Nothing is changed until
Aviyah decides. This is a NEW decision, not a correction of an error.*

---

## The question

`prepare` hands `distances(x)` the L2-normalised encoder output. There is no mean subtraction
anywhere before it — verified in code. Centring appears only in the **cohesion statistic**, which is
computed after the fact and reports nothing back into the build.

So Ward clusters in one space and we describe themes in another.

## This is not a bug that was overlooked

The 21 Sep note centred embeddings **for cohesion only** and left Ward on raw, deliberately. That
was a decision about what cohesion should measure, not an oversight about what Ward should cluster.
Extending centring to the clustering is a new choice with new consequences — every theme in every
build changes — and it is recorded here as such.

## Why the operative step is the renormalisation, not the subtraction

**Mean subtraction alone cannot change a Ward tree.** Ward minimises within-cluster variance, which
is defined on squared Euclidean distances, and those are invariant under translation:
`||(a - m) - (b - m)|| = ||a - b||`. Subtracting the universe mean moves every point by the same
vector and leaves every pairwise distance identical.

What changes the tree is **renormalising afterwards**. Dividing each centred vector by its own norm
rescales each point by a different factor — the distance of that pathway from the universe mean — so
pairwise distances do change. That step removes the dominant shared direction of the embedding, which
is what makes an embedding space anisotropic and produces **hubs**: a few points that appear in
everyone's neighbour list because they sit near the mean direction rather than near any particular
neighbour. The reference is Mu & Viswanath 2018, *"All-but-the-Top: Simple and Effective
Post-Processing for Word Representations"*.

Measured on the 1,850 (1,710,325 pairs): raw pairwise cosine has median **+0.705** and an
interquartile width of **0.050**; after centring and renormalising, median **-0.012** and
interquartile width **0.126**, 2.5x wider. The raw space is compressed, which is the symptom the
post-processing addresses.

## The two arms

Identical in every respect except the matrix handed to `distances()`.

- **RAW** — the current pipeline. The L2-normalised encoder output.
- **CENTRED** — subtract the universe mean, then L2-renormalise. The **real side uses the real
  universe mean; each scramble uses its own scrambled matrix's mean**, exactly as the cohesion
  statistic already does. Using the real mean on a scramble would leak the real geometry into the
  null.

Floors are re-solved **in-arm**. Nothing is carried over from E, because a floor solved against one
space does not apply to another.

## The declared reading — written before the numbers

**CENTRED is adopted if and only if it is at least as good on measurement 2 and measurement 3 AND
reduces hubness. Otherwise RAW stays.**

A split result — better on one, worse on another — **is reported as a split result and not resolved
by preference.** If the evidence does not decide, the incumbent stays, because the incumbent is what
every existing measurement was made against.

## What is measured

1. **Hubness.** Per pathway, how many others list it in their top-10 neighbours. Distribution (max,
   p99, share with zero) and the 20 worst hubs by name, per arm.
2. **Curated-pair recovery, cut-free.** AUROC and Cliff's delta for curated pairs against
   band-matched random pairs, on pairwise similarity alone — no clustering. Three pair sources:
   `reactome2go` mappings, Reactome siblings, GO siblings. Banded by gene overlap, with the **(0,0)
   band** — pairs sharing no gene — reported separately, since that band is where the method's claim
   lives.
3. **Full build per arm.** Real + 20 calibration + 10 held-out scrambles, floors re-solved in-arm,
   same locked rule, consensus included. Held-out FDR per stratum and overall, themes, roots,
   multi-parent fraction, depth, and test 9 stability against a seed-1 rebuild. Plus: where n0327's
   six members land in the centred arm.
