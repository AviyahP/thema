# Reviewer notes on monotonicity and direction: 7–8 Oct 2026

*Written by Aviyah's reviewer (Claude, architect role) for the record and for ccode. Everything below is EXPLORATORY: quick read-only checks run by the reviewer on the Mac in `/tmp/qs/*.py`, not part of the declared protocol. Each number names its script so it can be reproduced.*

## 1. The concern, stated precisely

Curated parents are summaries by construction. A Reactome parent's genes contain its children's (100% of edges, confirmed in `2026-10-08-monotonicity.md`). In GO, annotations propagate upward. So a parent pathway such as "Signaling by Receptor Tyrosine Kinases" (RTK, 532 genes) contains the genes of "Signaling by SCF-KIT" (43 genes).

Aviyah's concern is **pathway-level placement**: THEMA does not put such parent pathways above their children. Their genes therefore end up scattered across the DAG, which users will see as a serious flaw. **Theme-level containment is a different property**, and it holds automatically (see §3a).

## 2. What the reviewer measured

### 2a. Gene-nested pairs are grouped together (good)

**Script:** `nested3.py`.

**Pairs:** 82,940 pairs where ≥ 90% of pathway a's genes are in b, and b has ≥ 1.5× a's genes.

**Null:** random pairs, size-matched on gene count.

| larger set | A: some theme holds both | random | A: together in a theme ≤ 50 members | random |
|---|---|---|---|---|
| ≤ 50 genes | 92.2% | 24.0% | 72.2% | 0.2% |
| 51–200 | 84.8% | 21.7% | 46.8% | 0.3% |
| 201–500 | 81.6% | 22.7% | 27.4% | 0.3% |
| > 500 | 71.2% | 22.6% | 7.5% | 0.2% |
| all | 78.3% | 22.6% | 26.2% | 0.3% |

- HiDeF k5/800 scores 91.7% together, but its random baseline is 56.0%, because it has near-global roots. Its tight rate is 25.3%.
- Relative to chance, A is about 3.5× and HiDeF about 1.6×.

### 2b. The larger (general) pathway is NOT placed at the same or a higher level (the actual problem)

**Script:** `nested4.py`. Pairs that share a theme: 64,903.

A pathway's level is defined two ways: (i) the size of the smallest theme it enters at; (ii) the depth of the deepest theme it is in.

| | same-or-higher, by entry size | random | same-or-higher, by depth | random |
|---|---|---|---|---|
| A | 60.6% | 56.8% | 67.8% | 63.0% |
| HiDeF k5/800 | 62.8% | 59.5% | 60.4% | 56.2% |

- The small excess over random is mostly ties.
- "Strictly higher" is at chance.

### 2c. Mechanism: general pathways cluster with general pathways

**Script:** `nested5.py`.

- Take the 25,578 pairs where the larger pathway enters at a smaller theme. The median member gene-size of the larger pathway's entry theme is 261; for the smaller pathway's entry theme it is 18.
- The RTK case:
  - RTK sits in a 3-member theme with its two GO synonyms ("enzyme-linked receptor protein signaling", "cell surface receptor protein tyrosine kinase signaling"), then climbs into PI3K/AKT themes.
  - SCF-KIT climbs a separate ladder: KIT, then KIT mutants, then KIT/FLT3, then KIT/PDGFR/ALK, then "RTKs in cancer" (80 members).
  - They first meet in a 2,966-member theme in A; at 428 members in B (Leiden); at 458 in HiDeF.
- Reactome's own RTK group has 152 pathways. The best-matching theme (Reactome members only) has Jaccard 0.28 in A, 0.48 in Leiden and 0.38 in HiDeF. **There is no middle-level "RTK signalling" theme in any build.**

### 2d. Parents sometimes add the covering pathway one level up

**Script:** `parentcover.py`.

- In 20.0% of A's 8,208 edges, the parent adds a broader pathway covering ≥ 70% of the child's genes. Size-matched random pathways do so 3.0% of the time.
- More often, the general pathway is already inside the child (64% of small children).

### 2e. Direction from text alone is weak

**Free embedding signals** (`dirtest.py`; curated direct pairs, text neighbours, random half seed 1234):

| signal | Reactome | GO |
|---|---|---|
| local density | 61% | 61% |
| rank asymmetry | 61% | 62% |
| hub count | 58–59% | 62–63% |
| distance from the corpus centre | 44% (inverted) | 44% (inverted) |

- Holding the confound fixed (pairs where the parent's description is shorter) does not change the results.
- Name inclusion scores 99.7% on GO (applies to 43% of pairs). **Rejected by Aviyah as double dipping**: GO names encode curator structure.

**LLM direction pilot** (`data/experiments/direction_pilot/`):
- Setup: blinded descriptions, with no names or databases. Fresh agents wrote broader + ≤ 5 narrower phrases. Scoring: MedCPT query encoder on the phrases against the article embeddings.
- Accuracy is **62.5%** (Reactome 64.0%, GO 61.0%), below the pre-declared 70% bar.
- **Leakage alarm:** 63.3% of GO "broader" phrases are verbatim a TRUE curated GO ancestor's name, although the name was hidden. The LLM recites GO vocabulary.

**Pre-existing leak:** 3.2% of Reactome and 11.2% of GO child descriptions already contain their parent's exact name (tuning half).

### 2f. Size of the parent population

**Script:** `leaves.py`. "Internal" means having ≥ 1 curated descendant in the universe; for GO this uses full links.

| source | internal | leaves |
|---|---|---|
| GO | 4,370 of 7,538 (58%); median 43 genes | 3,168; median 9 genes |
| Reactome | 848 of 2,883 (29%); median 51 genes | 2,035; median 10 genes |
| Hallmark / BTM | 0 | all |

Removing all internal pathways leaves 5,599.

## 3. Critique of `docs/status/2026-10-08-monotonicity.md`

The note's numbers look correct, but it answers a different question from the one asked.

- **a. Theme-level containment (§2 of the note, 100%) is true by construction.** Parent theme ⊇ child theme as pathway sets, and gene union is monotone. So it carries no information about whether the distances respect gene containment. The 89.1% "strictly adds genes" figure is fine, but it does not address placement.
- **b. The concern was pathway-level placement of curated parents** (§1 above), and the note does not test it. The reviewer's §2b–2c shows that placement is near chance and explains why.
- **c. The linear probe (85.4%) is supervised on the answer key.**
  - It was trained on curated parent–child pairs, so it shows that the information is linearly present. It cannot be used in construction without training on GO/Reactome labels.
  - Two further risks inflate it: (i) cross-validation folds are not grouped by parent, and the same parent appears in many pairs, which leaks across folds; (ii) it may exploit style proxies (description length, source-specific phrasing, "general-sounding" wording).
  - Required if it is reported: grouped CV by top-level branch; train-on-Reactome / test-on-GO and the reverse; a length- and source-matched control.
- **d. The direction benchmark is not "flawed because gene counts answer it".** Gene-set size orders curated pairs perfectly because sizes are *produced by* the curated hierarchy (Reactome unions, GO propagation). It is a leaky baseline, not a reason to discard the benchmark. A text method must be judged on text.
- **e. Co-themed pairs share genes (84.5% vs 14.7% random).** This is partly inflated by parent + child pairs co-themed together. Report leaf–leaf pairs separately.
- **f. The note is Reactome only.** GO is not tested, as the note itself says.

## 4. Consequence

Theme-level monotonicity holds, but pathway-level placement of curated summaries fails for every engine tested (A, Leiden, HiDeF), and text-only direction is weak or contaminated. This motivates the **leaves experiment** (`docs/spec/2026-10-08-leaves-experiment.md`): build from the atomic pathways and test whether THEMA recreates the curated summaries.
