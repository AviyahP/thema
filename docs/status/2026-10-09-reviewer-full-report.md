<!-- Recorded by ccode on 2026-10-09. Verbatim copy of
     data/experiments/reviewer_sample_2026-10-09/REVIEW_FULL_REPORT.md. Nothing appended.
     RE-COPIED after sections 14-17 landed; the first copy was of an incomplete save. -->

> **EXPLORATORY — recorded by ccode, not produced or reproduced by it.** The reviewer's full
> plausibility review of `thema_L_repair` and `thema_L_x2`, copied verbatim. LLM-judge assessments
> made with Aviyah outside ccode: not a declared test, not run under the protocol, not reproduced
> here. Judges saw member names (and, for unnamed BTMs, the generated description and genes); names
> are never used in construction, which is what makes it an independent check.
>
> Raw material in `data/experiments/reviewer_sample_2026-10-09/`; the file index is §13 below. The
> step-3 evaluation of `thema_L_x2` has its own folder and its own copy at
> `docs/status/2026-10-09-x2-evaluation.md`.
>
> **This copy replaces an earlier one that stopped at §13.** Aviyah's save of §14–17 had not landed
> when ccode first copied the file, and ccode noted at the time that the sections the prompt referred
> to were absent and went by content instead. They are present now: **§14** chain-collapse survivor,
> **§15** the agreed plan, **§16** the step-3 result, **§17** the follow-up questions. The earlier
> note about missing sections is removed because it is no longer true.

---

# Biological plausibility review of thema_L_repair: full report

Reviewer: Claude (reviewer role), at Aviyah's request. Written 2026-10-09.
Build evaluated: `data/ontology/v0.4-leaves/thema_L_repair/` (cal8 floors + repair fixes 1 and 2), 8,793 themes.
Status: evaluation only. Nothing in the build was changed by this review.
All files: `data/experiments/reviewer_sample_2026-10-09/` (index in section 13).

---

## 1. Question and bottom line

**Question (Aviyah):** "Look at the clusters at every level. Would a biologist recognise a coherent, plausible biological theme in each?"

**Answer:** every one of the 8,793 themes has now been judged once. **8,560 (97.4%) are coherent or a linked umbrella.**

The problems are concentrated in three places:

- **5 of the 9 giant roots** (over 1,000 members): incoherent bags, already known.
- **About 11 distinct families of small incoherent clusters** (39 clusters), almost all built from inputs that carry no specific biology of their own.
- **57 mixtures and 132 "core plus misfits" clusters**, spread thinly across sizes.

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 483 | 472 | 6 | 3 | 0 | 2 | 99.0% |
| 6-10 | 2121 | 1932 | 125 | 37 | 13 | 14 | 97.0% |
| 11-20 | 4365 | 3816 | 429 | 72 | 27 | 21 | 97.3% |
| 21-50 | 1568 | 1337 | 196 | 20 | 13 | 2 | 97.8% |
| 51-100 | 214 | 161 | 51 | 0 | 2 | 0 | 99.1% |
| 101-300 | 28 | 25 | 3 | 0 | 0 | 0 | 100% |
| 301-1000 | 5 | 4 | 1 | 0 | 0 | 0 | 100% |
| 1000+ | 9 | 2 | 0 | 0 | 2 | 5 | 22% |
| **all** | **8793** | **7749** | **811** | **132** | **57** | **44** | **97.4%** |

The final verdict for every theme is in `all_verdicts.json`.

## 2. Method

**Judges.**
- Reviewer subagents (LLM) judged each cluster, with a written rubric, from its member pathway names.
- Pathway names are never used in construction (embeddings are built from generated descriptions; names and genes are not construction signals), so this check is independent of how the clusters were made.
- Genes were used only for evaluation.

**What the judges saw.**
- Clusters of 1-50 members: up to 15 members (random order). Clusters of 51-100: up to 25 members. Clusters over 100: 40 random members.
- 83 BTM modules are named "TBA" by the source. For these, from round 2 on, judges were shown the module's generated description (first 400 characters) and its first 10 genes, and were told to judge them by that biology.
- No web search, no other files.

**Rubrics** (all in the folder):
- `rubric.md`, round 1: coherent / partial / incoherent.
- `rubric2.md`: the same three verdicts, with TBA descriptions and genes shown.
- `rubric3.md`, round 3: re-judged partials with one question: "Is there a recognised, specific biological link between the sub-themes (a shared mechanism, enzyme or cofactor, cell type or tissue, or physiological axis)?" Vague links ("both are signalling") did not count.
- `rubric4.md`, samples 2-3 and the census: five verdicts.
  - **coherent**: one recognisable theme; a small minority of odd members is fine.
  - **umbrella**: two or more sub-themes joined by a specific, recognised link, which must be stated.
  - **core_plus_misfits**: one theme plus roughly a quarter or more that does not belong.
  - **mixture**: sub-themes with no specific link.
  - **incoherent**: no theme at all.

**Reviewer checks.** I spot-checked verdicts by hand in every round (17 in round 1, plus the umbrella links and every non-ok cluster in samples 2-3) and agreed with them. Where I now think a judge was too strict, I say so below (section 9).

**Caveats.**
- The judges are LLMs of the same family as the model that wrote the input descriptions.
- Judges saw a member sample, not every member, of clusters over 15 (or 25) members.
- The rubric is stricter than Reactome or GO in places. For example, Notch + Hedgehog was called a mixture, and Reactome files gene-specific transcription regulation sets together.

## 3. Chronology

| step | what | n | result |
|---|---|---|---|
| Round 1 | 10% random sample per size band (3-100) | 879 | 89% coherent, 93 partial, 6 incoherent |
| Round 2a | Every sampled cluster containing a TBA module, re-judged with descriptions and genes | 102 | 22 of the 29 partial/incoherent became coherent |
| Round 2b | **All** themes over 100 members (40 random members shown) | 42 | 101-300: 25 coherent, 3 partial; 301-1000: 4 + 1; 1000+: 2 coherent, 2 partial, 5 incoherent |
| Round 3 | All 99 partials re-judged with the "specific link" question | 99 | sampled partials: 74 umbrella, 15 core+misfits, 4 mixtures; big: 4 umbrella, 2 mixtures (the 1,444 and 1,047 housekeeping bags) |
| Sample 1 final | | 879 | 854 ok (97.2%), 15 core+misfits, 10 incoherent or mixture |
| Sample 2 | New 10%, seed 20261010, rubric4 | 874 | 98.1% ok |
| Sample 3 | 20% of the still-unchecked themes, seed 20261011 | 1,400 | 97.6% ok |
| Census | All remaining themes of size 3-100 | 5,603 | 97.3% ok |

**Sample 2 (874):**

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 48 | 46 | 1 | 1 | 0 | 0 | 97.9% |
| 6-10 | 212 | 193 | 12 | 3 | 2 | 2 | 96.7% |
| 11-20 | 436 | 376 | 53 | 4 | 2 | 1 | 98.4% |
| 21-50 | 157 | 138 | 18 | 1 | 0 | 0 | 99.4% |
| 51-100 | 21 | 13 | 7 | 0 | 1 | 0 | 95.2% |

**Sample 3 (1,400):**

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 77 | 75 | 2 | 0 | 0 | 0 | 100% |
| 6-10 | 339 | 305 | 25 | 5 | 2 | 2 | 97.3% |
| 11-20 | 699 | 600 | 82 | 11 | 2 | 4 | 97.6% |
| 21-50 | 251 | 207 | 36 | 4 | 4 | 0 | 96.8% |
| 51-100 | 34 | 27 | 7 | 0 | 0 | 0 | 100% |

**Census (5,603):**

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 310 | 305 | 2 | 2 | 0 | 1 | 99.0% |
| 6-10 | 1358 | 1237 | 79 | 24 | 9 | 9 | 96.9% |
| 11-20 | 2794 | 2451 | 260 | 50 | 20 | 13 | 97.0% |
| 21-50 | 1003 | 862 | 119 | 12 | 8 | 2 | 97.8% |
| 51-100 | 138 | 107 | 30 | 0 | 1 | 0 | 99.3% |

The sample estimates (97.2-98.1%) predicted the census (97.3%) well.

## 4. What good clusters look like: umbrella examples

Umbrella themes join sub-themes through a specific, stated link. Examples the judges gave, all checked by the reviewer:

- thyroid hormone + large neutral amino acids: the same transporters (LAT1/LAT2, MCT10);
- EMT transcription factors + the cadherin switch;
- the HPA stress axis + neuroendocrine behaviour; glucocorticoid secretion + the circadian clock (the SCN clock gates the ACTH-cortisol rhythm);
- renin-angiotensin + vasopressin fluid balance;
- proteasome + MHC class I antigen presentation;
- MECP2 + Rett-syndrome behaviour;
- heat-shock proteins + axon maintenance;
- the epidermal melanin unit;
- heavy metals + metallothionein / HMOX1;
- O-glycosylation of GAG linkers and of Notch;
- methyltransferases (INMT, TPMT) in both xenobiotic and selenium excretion;
- hemostasis + eicosanoids (platelet COX-1 makes thromboxane A2);
- mitochondria + translation (mitochondrial tRNA modification and translation);
- host RNA processing + viral replication.

## 5. Structure below a mixed node, the platelet fan, and the lattice above it

**The hemostasis + lipid mediators node (139 members) splits cleanly one level down** into:

- eicosanoids / SPMs (66 members, support 0.95);
- coagulation (57);
- platelet adhesion / activation (52);
- platelet GPCR signalling (10).

**The fan.** n00150 is a 7-member node (ADP-P2Y1/P2Y12, thrombin-PAR, TP and IP receptor signalling, positive regulation of platelet activation; support 0.99). It has 6 parents of 10-11 members each (support 0.05-0.56). Each parent is the core 7 plus 3-4 extras:

- G12/13 + actin;
- cytoskeleton + BTM platelet modules;
- GPVI + LDL sensitisation;
- prostanoid GPCR family;
- Rap1 integrin activation;
- 5-HT2A / Gq-PLC-IP3.

All six are plausible, distinct facets. Every one adds at least one pathway no other parent has: n03581 adds platelet activation (II) and cytoskeletal remodeling; n05989 adds Rap1 signalling. Pairwise Jaccard between the parents is 0.47-0.69.

**Decision (Aviyah, 9 Oct): fans of facet parents around a stable core are intended multi-parent DAG behaviour, not redundancy.** The reviewer's earlier word "redundant" is withdrawn.

**The lattice above n00150.** n00150 has 28 ancestors: the 4 giant roots plus 24 others, all judged.

- **All 24 are coherent platelet / hemostasis themes.** The one stray member is VEGFR2 cell proliferation in n07791.
- **The six facets go up three distinct routes:**
  - **A. Platelet activation proper (4 facets).** Up through activation + adhesion (n00918, 27 members, support 0.85; n03842, 35), then platelets + VWF / coagulation (n08023, n04419), to hemostasis n02115 (77 members, support 0.86).
  - **B. The prostanoid / GPCR receptor family.** Up to hemostasis + eicosanoids n03423 (139).
  - **C. Gq / G12/13 GPCR signalling (the serotonin facet).** Up to amine + lysophospholipid receptor signalling n07791, then a giant root.
- **Inside route A the levels are over-resolved.** About 14 nodes of 13-41 members form a staircase of near-nested supersets, each adding 2-6 members, mostly with support 0.035-0.17.
- **Chain ratios (child size / parent size):**
  - n07792 to n03907: 0.889;
  - n03820 to n04961: 0.867;
  - n03907 to n05156: 0.857;
  - n03842 to n08023: 0.854;
  - n00918 to n01879: 0.844;
  - n05194 to n06758: 0.824;
  - n01879 to n08023: 0.780.
- **Effect of candidate rules (ccode's worked example, confirmed):**
  - chain collapse at 0.85 removes 4 rungs and no facet;
  - chain collapse at 0.80 removes 6 rungs and no facet;
  - sibling merge at 0.60 would delete 1-2 of the 6 facets, and picks the wrong one by support. It is rejected; the sibling threshold stays at 0.70.
- **Open question (measurement requested in prompt 22):** at 0.85, 3 of the 4 collapses drop the *more* stable node (for example n03842, support 0.375, into n08023, support 0.14). Should the survivor be the higher-support node?

## 6. Where the non-ok clusters come from (all 233)

| verdict | n | main sources |
|---|---|---|
| incoherent | 44 | 5 giant roots; 39 small clusters in about 11 families of low-information inputs (section 7) |
| mixture | 57 | 2 big housekeeping bags (1,444 and 1,047); then see the list below |
| core + misfits | 132 | a coherent theme plus generic or neighbouring terms. Recurring: generic "transcription regulation" terms attached to TF-target themes; lipid transfer vs protein lipidation; inherited-defect pathway sets attached by enzyme family |

The main sources of the 57 mixtures:

- developmental-signalling pairs judged strictly: Wnt + Notch (58 members), Notch + Hedgehog (38, 43), MET + TGF-beta + Hippo (27-32);
- kynurenine-NAD + polyamines (24, 28);
- gonad + placenta (29);
- trophoblast + eye (30);
- surfactant + Rh transport (21);
- olfaction + hearing (21);
- peroxisomal fatty-acid oxidation + steroidogenesis (70);
- CD4 T-cell proliferation + B-cell Ig diversification;
- vitamin K + vitamin C;
- several clusters built from heterogeneous BTMs.

## 7. The 44 incoherent clusters

Full profile per cluster: `incoherent_analysis.json`. Short version: `REPORT5_incoherent.md`.

### 7.1 Few distinct problems

- **5 are the giant roots** (2,138-2,614 members).
- **The other 39 (3-28 members) form 12 families** when parent/child links between incoherent clusters are followed:
  - **one family of 22 nested clusters**: n05867 (28 members) down to n00717, n00908 and n02265 (7 each);
  - **one family of 5**: n07386 to n08787 to n02521 to n00421, plus n02238;
  - **two families of 2**: n08490 to n03087; n08627 to n03413;
  - **8 singletons**: n00735, n03375, n04488, n06294, n04339, n08713, n04626, n07120.
- n04626 and n07120 share 17 of their 21 members, so there are **about 11 distinct problems**.

### 7.2 What they are made of

**A. Unnamed blood co-expression modules (TBA BTMs).** This is the 22-cluster family plus n08713. Its core members are:

- **the self-described heterogeneous modules:** M153, M72.0, M72.2, M218, M32.5, M211, M221;
- **unnamed modules with vague descriptions that the first rule did not catch:** M137, M174, M72.1, M242, M161, M185, M243, M248 (described as having "in common little more than a shared place in interaction screens"), M32.7, M128, M32.6;
- **motif-defined modules:** M232 (TF motif), M32.3 (KLF12 targets), M138 (ubiquitination).

**B. Sets defined by a regulatory signature, not a process** (n04626 / n07120, n08490 / n03087, n03375):

- PAX3 motif and targets, the SREBF1 motif, an unknown motif, glucocorticoid-receptor targets, SMAD2/3;
- Reactome "regulation of transcription of gene X" sets (CDH1, CDH11, PTEN, PD-L1, TGFBR3, RUNX3 targets);
- generic GO "negative regulation of transcription" terms.

Reactome itself files many of these together under the Generic Transcription Pathway. **Aviyah (9 Oct): these are acceptable, since co-regulation by the same factor is a biological relation.** Keep them.

**C. Human / ape-specific duplicated gene families plus vague GO terms** (n02238, n06294, n08627 / n03413). See section 9.1.

**D. Vague or orphan GO terms:** n04339 (response to drug / ethanol / ether / anesthetic) and n04488 (magnesium / creatine / inositol / protein tetramerization). See sections 9.2 and 9.3.

**E. Borderline:** n00735 (3 members: regulation of phosphatidylinositol biosynthesis, LPA receptors, VEGFR2-mediated proliferation). All three are phospholipase C / phosphoinositide receptor signalling. The reviewer would call it an umbrella.

**Likely mechanism (not proven):** inputs without a specific theme get generic descriptions ("housekeeping", "chromatin", "regulation of transcription", "response to"), so they end up as each other's nearest neighbours. THEMA groups the leftovers together instead of mixing them into good themes, which is the less harmful failure.

### 7.3 Neither resampling support nor gene overlap separates them

- **Median support** (themes under 1,000 members): coherent 0.15, umbrella 0.06, core+misfits 0.055, mixture 0.045, incoherent 0.08.
- **Some incoherent clusters are very stable** (n00421 0.955, n00717 0.90, n00735 0.895, n00908 0.85), because the same leftovers always fall together. Support measures reproducibility, not meaning, and cannot serve as a filter: umbrellas have lower support than incoherent clusters.
- **Mean pairwise gene Jaccard** of members is 0.01-0.04 in incoherent clusters, the same range as coherent clusters of the same size (0.04 at 11-20 members, 0.058 at 6-10). The exception is n00421 (0.24), whose members are overlapping M41.x sub-modules.

### 7.4 Effect of the first exclusion (17 modules)

- **It dissolves n00421** (5 members down to 1) and thins the rest of the 22-cluster family.
- **It does not remove that family:** n05867 keeps 21 of 28 members (11 of them still unnamed BTMs), and n04129 keeps 13 of 20.
- **Categories B-D are untouched.**

## 8. Input exclusions (for the Methods section)

### 8.1 Exclusion 1: self-described heterogeneous unnamed BTMs (decided, 9 Oct)

- **Rule** (declared before it was applied): an unnamed ("TBA") BTM whose generated description, written by our LLM from its genes alone because the module has no name, says in its first sentence that no single or coherent process unites the genes, or calls the set heterogeneous or loosely connected.
- **17 modules:** M125, M153, M184.1, M211, M218, M221, M233, M241, M246, M32.5, M41.0, M41.1, M41.3, M70.0, M72.0, M72.2, M98.1.
- **How it was found:** the second plausibility sample. All 3 incoherent themes there were built from these modules.
- **Earlier count:** "18" came from a looser text search; the declared rule gives 17. BTM M213 ("regulation of transcription, transcription factors") matches the words but has a name and a coherent theme, so it stays.
- **Borderline but inside the rule:** M125 and M233 (a loose shared bias), M184.1 (a JNK core).
- **File:** `data/excluded_inputs.tsv`, written by ccode. Columns: key, source, excluded_on, decided_by, rule, evidence_first_sentence. `pathways.tsv` is unchanged.
- **Effect:** universe 10,770 to 10,753 (universe L: 5,542).
- **Floors (Aviyah, 9 Oct):** the previous cal8 floors are reused; there is no recalibration for now.
  - Reason: the floors come from the scramble side only, and removing 0.16% of the inputs should leave the scramble null essentially unchanged.
  - To be recorded in DECISIONS, in each build's metadata, and as an open to-do: "consider re-running scrambles and updating the floors later."

### 8.2 Exclusion 2: unnamed modules that cannot be described coherently (agreed in principle by Aviyah, 9 Oct; list not yet made)

- **Intent:** inputs that have neither a name nor a coherent description (example: M248) are excluded like the first 17.
- **To keep this honest, the list must be made by a rule applied to all 83 unnamed BTMs from their descriptions alone, decided before looking at where they land.** M248 and the other examples in 7.2A were noticed through the cluster verdicts. Choosing inputs by cluster verdicts would let the evaluation tune the construction (double dipping) and inflate the plausibility numbers.
- **Suggested rule:** a blind judgement of each TBA description, "does it name one specific biological process or system?", using a fixed rubric, recorded with its evidence sentence.
- **Output:** append to `data/excluded_inputs.tsv` with rule id "exclusion-2".
- **Named sets stay:** named BTMs, including motif- and target-defined ones (category B), and all GO / Reactome / Hallmark sets.

### 8.3 Draft Methods paragraph

> **Input curation.** Blood transcription modules without a source annotation ("TBA", 83 modules) were described by the language model from their gene lists alone. Modules whose generated description stated that no single or coherent process unites their genes (rule 1, n = 17), or that the description could not attribute to one specific process (rule 2, n = TBD), were excluded before construction. Both rules were applied to the descriptions only, without reference to the resulting ontology. The excluded modules, the rule applied and the evidence sentence are listed in Supplementary Table X (`data/excluded_inputs.tsv`). Noise floors calibrated on the full universe (10,770 sets) were reused for the reduced universe (10,753 sets).
>
> **Plausibility evaluation.** Every theme was judged once by language-model reviewers who saw member pathway names (not used in construction) and, for unannotated modules, their descriptions and genes. The rubric had five verdicts (coherent, umbrella with a specific stated link, core with misfits, mixture, incoherent). 97.4% of themes were coherent or linked umbrellas.

## 9. Reviewer's second look at categories C and D (answers to Aviyah, 9 Oct)

### 9.1 C: human / ape-specific duplicated gene families

**What they are.**

- Over the last few million years, large stretches of DNA were copied in the ape and human lineage (segmental duplications). Genes inside them became families of near-identical copies:
  - TBC1D3 on chromosome 17 (in BTM M241);
  - NPIP, the "nuclear pore complex interacting proteins", on chromosome 16 (BTM M247);
  - NOTCH2NL on 1q21 (the Reactome set "Expression of NOTCH2NL genes").
- VENTX ("Transcriptional regulation by VENTX", in n08627 / n03413) is a homeobox factor present in humans but absent in rodents.
- What these genes share is their **evolutionary origin**: recent, primate- or human-specific, multi-copy, poorly annotated. Their descriptions say so ("primate-expanded", "human-specific", "absent in rodents"), which is very likely why the embedding puts them together.

**Do they share function?** Mostly not.

- TBC1D3 is a Rab-GAP, NOTCH2NL modulates Notch signalling, NPIP's function is largely unknown, and VENTX acts mainly in blood.
- One real functional link exists: NOTCH2NL and TBC1D3 have both been reported to drive expansion of cortical progenitors in human brain development.

**What else is in these clusters.**

- A second, coherent sub-theme: **genome maintenance, telomeres, aging and marrow failure.**
  - "Determination of adult lifespan" (ATM, ERCC1/2, WRN...);
  - "replicative senescence" (ATM, ATR, CDKN2A, TERT, CTC1);
  - "regulation of growth rate" (WRN, GHRL);
  - "bone marrow development" (SBDS, CTC1, TP53);
  - "inner cell mass proliferation" (BRCA2, PALB2, CHEK1);
  - ORC assembly.
- Plus odd single terms: "negative regulation of syncytium formation" (mostly ribosomal proteins), "cell-cell adhesion in gastrulation", "Defective SLC22A18".
- And the heterogeneous modules M221 and M241, both in the 17 being dropped.

**Reviewer's reading.** These are mixtures of two things:

1. a real aging / genome-maintenance theme;
2. a group defined by evolutionary origin, not by a biological process.

A grouping by origin is like grouping genes by chromosome: real, but not what a process ontology is for. M221 and M241 leave with the first exclusion; M247 and NOTCH2NL stay.

**Follow-up (Aviyah's question, 9 Oct): do these pathways also sit in clusters that match their function, and do their descriptions talk about function?**

- **VENTX: yes, on both counts.** Its description is almost all function: it restrains hematopoietic stem-cell proliferation and pushes cells toward myeloid fate. It sits in 23 themes. 17 of them are coherent hematopoiesis / myeloid-differentiation themes (for example n02005, bone marrow and stem-cell homeostasis; n03255, myeloid differentiation and granulopoiesis; n03053, hematopoiesis, 77 members). Only 2 are incoherent, and the other 4 are giant roots. Multi-parent placement works as intended here.
- **NPIP (M247): mostly.** Its description is mostly about origin, says "limited shared function", and mentions the nuclear pore. Its nearest embedding neighbours are nuclear-pore / RNA-transport and miRNA-processing sets. Apart from the duplication clusters, it sits in two coherent themes, AU-rich-element mRNA decay (n04139, n05166).
- **TBC1D3 (M241):** its description is heterogeneous. It leaves with exclusion 1.
- **NOTCH2NL: no. This is a real miss.**
  - Its description is mostly function: Notch signalling in radial glia, delayed progenitor differentiation, cortex expansion, microcephaly / macrocephaly.
  - The embedding agrees. Its nearest neighbours in the build universe are forebrain radial glial cell differentiation, forebrain neuroblast and ventricular-zone progenitor division, Notch-HLH transcription, and Notch receptor processing. M247 is only its 25th neighbour, and M241 its 203rd.
  - Yet NOTCH2NL appears in no Notch or cortical-development theme. Its 12 themes are the duplication trio n00892 (with M241 and M247; support 0.855; judged an umbrella), the 5 incoherent clusters, the 2 mRNA-decay themes, and 4 giant roots. It always travels with M241 and M247.
  - **A likely mechanism, checked on this one case: Ward makes loners pair with loners.** Ward's merge cost is n_a·n_b/(n_a+n_b) × the squared centroid distance.
    - As single items, NOTCH2NL's functional neighbours are closer than M247: merge cost 0.21-0.23 vs 0.238.
    - But those neighbours quickly form their own tight groups (n02161 cortical development; n00296 Notch signalling; n00127 / n03083 neural-progenitor division). Joining one of those groups costs NOTCH2NL 0.29-0.32.
    - So pairing with another loner (M247, 0.238) is cheaper, and Ward does that, reproducibly.
    - The resampling then confirms the pair as stable, and the functional placement never forms, so no second parent is possible.
  - **Checked in the 200 resampling runs (Aviyah asked whether resampling should place it correctly at least sometimes).**
    - NOTCH2NL is present in 164 runs. In 147 of them, its smallest cluster contains TBC1D3 (M241) or NPIP (M247). In only 5 (3%) does it contain members of the brain / Notch themes.
    - Even in the 5 runs where neither partner was present, it did not go to a brain / Notch group.
    - It first shares a cluster with two or more brain / Notch theme members only at a median cluster size of about 200.
    - A 3% placement cannot become membership anyway: an item enters a theme only if it is in at least 50% of that theme's matched instances (inclusion cut 0.5).
  - **Why resampling does not rescue it.** Resampling changes which items are present, not the distances. It produces alternative placements for items that sit near a boundary between two groups.
    - NOTCH2NL is far from everything. In the build's (centred) space, its nearest-neighbour cosine is 0.29; that is in the bottom 1-2% (all items: median 0.56, 5th percentile 0.39).
    - Its closest items (Notch-HLH transcription, forebrain neuroblast division) are much closer to their own groups than to it, so they always group first.
    - Likely reason (hypothesis): its description covers several topics (evolution, Notch, cortex, microcephaly, repeat-expansion disease, neutrophils), so its embedding is an average that sits near none of them.
  - **How common this is (measured on all 5,559 items):** only 8 items have themes (under 1,000 members) that contain none of their 5 nearest neighbours. All 8 are extreme loners (nearest-neighbour cosine 0.29-0.39): NOTCH2NL; GO negative regulation of syncytium formation; HALLMARK_KRAS_SIGNALING_DN; Intestinal infectious diseases; M247; peptidyl-serine autophosphorylation; reactive gliosis; negative regulation of amine metabolic process.
  - **Items placed only in bad themes:** 14 items appear only in incoherent or mixture themes (apart from giant roots). All 14 are unnamed or motif BTMs (M70.0, M211, M246, M153, M185, M32.5, M242, M72.0-72.2, M62.1, M178, M74) plus one GO term (cellular response to lithium ion), and 7 of them are in exclusion 1.
  - **Conclusion:** functional misplacement of this kind is rare (8 items) and confined to loners. Resampling cannot fix it, because the placement is stable rather than uncertain. Stability is not correctness.

### 9.2 D: "response to drug / ethanol / ether / anesthetic" (n04339)

**By name, yes, they belong together.**

- GO files them all under "response to chemical".
- Ethanol, ether and volatile anesthetics share molecular targets: GABA-A and glycine receptors and NMDA receptors. GLRA1/2 are in the ethanol set; GABRB3 is in the anesthetic set.

**By genes, no.**

- No gene is shared by three or more of the 11 members.
- These GO terms are annotated from single expression experiments, so each holds an arbitrary handful of genes. "Negative regulation of response to drug" is 14 microRNAs; "cellular response to ether" is AKT1, CAV3, CD4, CDK4, LRRK2 and others.
- The cluster also holds: negative regulation of NO biosynthesis, positive regulation of the hypoxia response, negative regulation of the oxidative-stress response, developmental apoptosis, negative regulation of amine metabolism, and agmatine biosynthesis.
- Agmatine is an endogenous NOS inhibitor and NMDA modulator, so it has a loose link to the NO and drug terms.

**Reviewer's reading (revised after Aviyah's correction, 9 Oct).** THEMA clusters by theme, not by shared genes, so gene sparseness is not evidence against coherence. My first answer leaned on gene sharing; that was the wrong criterion. By theme, this is an **umbrella: cellular responses to drugs, CNS depressants and chemical / oxidative stress**. Ethanol, ether and anesthetics share receptor targets, and NO, hypoxia, oxidative stress and agmatine belong to the same stress-response family. The judge was too strict.

### 9.3 D: magnesium + creatine (+ inositol, protein tetramerization) (n04488)

**Magnesium + creatine: a real but generic link.**

- Creatine kinase uses Mg-ATP, as do all kinases, and both matter in muscle and brain energetics.
- They are not one pathway: magnesium transport (CNNM, TRPM7, SLC41A1, NIPA) and creatine synthesis and shuttling (GATM, GAMT, CK isoforms, SLC6A8) share no genes.

**Inositol transport fits loosely** with the small-solute theme (SLC5A3 / SMIT and HMIT accumulate myo-inositol as an osmolyte and phosphoinositide precursor).

**"Protein homotetramerization / heterotetramerization / hexamerization" do not belong.** These terms describe a structural form, not a process. Their genes are any protein that happens to form a tetramer or hexamer: aquaporins, acetyl-CoA carboxylase, aldolase, glutamate receptors, LRRC8 channels.

**Reviewer's reading (revised, thematic criterion).** Magnesium, creatine and inositol share a theme: small-solute / ion homeostasis and the cell's energy buffer (Mg-ATP in creatine kinase; inositol and creatine as accumulated solutes). That makes a weak but real umbrella. The structural-form terms (tetramerization, hexamerization) describe a shape, not a process, and do not belong. Overall: **core + misfits** rather than incoherent.

### 9.4 Revised tally of the 39 small incoherent clusters (reviewer's view)

| cluster group | reviewer's view |
|---|---|
| 22-cluster family, n08713, n00421 family | genuinely incoherent; built from unnamed modules; addressed by exclusions 1 and 2 |
| n04626 / n07120, n08490 / n03087, n03375 | acceptable regulatory-signature groupings (Aviyah) |
| n02238, n06294, n08627 / n03413 | mixtures: an aging / genome-maintenance theme + a duplicated-gene-family group |
| n04339 | umbrella (responses to drugs, CNS depressants, chemical / oxidative stress) |
| n04488 | core + misfits (small-solute / ion and energy homeostasis; structural-form terms misfit) |
| n00735 | umbrella (phosphoinositide receptor signalling) |

## 10. Decisions made during this review (all Aviyah, 9 Oct)

- **Principle: coherence means a shared theme, not shared genes.** THEMA is thematic clustering; gene overlap is reported for information only and is not a criterion for plausibility.

- **Fans are intended DAG behaviour:** not a removal target.
- **Sibling merge stays at 0.70.** Sibling merge is the wrong tool for fans.
- **The 17 self-described heterogeneous BTMs are dropped** from the next construction, with a documented rule and file.
- **Unnamed modules that cannot be described coherently are also to be excluded** (exclusion 2: rule and list to be made blind to the results).
- **Regulatory-signature sets (category B) are kept.**
- **The previous cal8 floors are reused after the drop**, noted as a candidate for a later re-run of the scrambles.
- **Chain collapse at 0.85 is under consideration,** pending the survivor measurement.

## 11. Errata (reviewer statements corrected during the review)

- In section 9 the reviewer first judged n04339 and n04488 partly by gene sharing. Corrected to thematic judgement (Aviyah).

- "18 heterogeneous TBA BTMs" corrected to **17** under the declared rule.
- "Chain collapse at 0.80 removes 7 rungs" corrected to **6**; I had used de-duplicated member counts (n01879 to n08023 is 32/41 = 0.780).
- "The 6 platelet parents are redundant" is withdrawn: they are distinct facets.
- "No common ancestor of the 6 parents within 3 levels" is true for all six jointly. The 4 route-A facets do share n03842 within 3-4 levels.
- On recalibration, the reviewer first agreed with ccode that a full recalibration was needed. That was wrong: it mixed the real trees (part of the build) into calibration. The floors depend on the scrambles only (Aviyah).
- ccode twice wrote that the reviewer judged n03581 "not distinct". The reviewer never did; every parent adds a unique pathway.
- The round-1 headline (89% coherent) was before TBA descriptions were shown and before partials were re-judged; the final sample-1 figure is 97.2%.

## 12. Open items

0. **ccode measurements (9 Oct, after prompt 22):**
   - Floors: the reuse note is written in DECISIONS, in the floors record `regate/floors_L_cal8.json` (copied automatically into every build manifest as `floors_source`), in a new `data/ontology/v0.4-leaves/README.md`, and as an open to-do in `docs/status/2026-10-09-redundancy-measure.md`. No code checks a floors file against the universe, so no override was needed.
   - Chain survivor: over all 550 chain edges with ratios in [0.85, 0.90), the absorbed child has higher support than the surviving parent in 341 (62%), lower in 201, and equal in 8 (median gap +0.115). On the n00150 lattice, the declared rule keeps the more stable node in 1 of 4 collapses; "keep higher support" keeps it in 4 of 4 (post-hoc). ccode is concerned that keeping the child breaks containment; this is not yet shown (see the reviewer note in the chat of 9 Oct).
   - n00918 is 27/32 = 0.84375, so it is absorbed only at 0.80, not at 0.85.
   - Unique-contribution test on n00150: every parent adds 1-3 unique pathways, so it removes none of the 6.

1. Exclusion 2: rule and blind run over the 83 unnamed BTMs; append the result to `data/excluded_inputs.tsv`.
2. Chain-collapse survivor rule: measure, then decide; then decide on 0.85.
3. Rebuild with the exclusions and the chosen structural rules (reused floors, noted).
4. Giant roots: the recursive top level (prompt 19).
5. Later: consider re-running the scrambles and updating the floors.

## 13. File index (`data/experiments/reviewer_sample_2026-10-09/`)

| file | content |
|---|---|
| rubric.md, rubric2.md, rubric3.md, rubric4.md | judging rubrics |
| sample.json, judged.json | round 1 sample and verdicts |
| tba_rejudge.json, round2.json | TBA re-judging; all themes over 100 |
| round3.json | partials re-judged with the specific-link question |
| sample2.json, judged2.json | sample 2 |
| sample3.json, judged3.json | sample 3 |
| sample4_rest.json, judged4_rest.json | census of the remaining 5,603 |
| all_verdicts.json | final verdict for all 8,793 themes |
| incoherent_analysis.json | profile of the 44 incoherent clusters |
| REPORT.md, REPORT2.md, REPORT3.md, REPORT4.md, REPORT5_incoherent.md | per-round reports |
| REVIEW_FULL_REPORT.md | this report |

## 14. Chain-collapse survivor: reviewer analysis (9 Oct, after ccode's measurement)

- **What a chain pair is:** a child holding at least 85-90% of its parent's members. The two nodes are near-duplicates, so chain collapse deletes one. The declared rule keeps the parent (the larger set).
- **ccode's measurement:** over all 550 pairs with ratios in [0.85, 0.90), the deleted child has higher support than the kept parent in 341 (62%), lower in 201, and equal in 8. Median gap +0.115.
- **Why the parent is usually less stable:** the parent is the child plus a few loosely attached pathways, which land in different places from run to run. So the larger version reappears less often.
- **Verdicts for both nodes of all 550 pairs** (from `all_verdicts.json`, reviewer):
  - both coherent or umbrella: 541;
  - child ok, parent not: 4;
  - both bad: 5;
  - child bad, parent ok: 0.
- **In 7 pairs the parent is a top-level node** (no parents).
- **Reviewer's recommendation:** keep the node with higher support; if they tie, or the parent has no parents, keep the parent. Reasons:
  1. It matches THEMA's own evidence standard (recurrence).
  2. Biologically the two are interchangeable, and the child is never worse.
  3. The parent's extras stay in the higher ancestors, so only one in-between grouping is lost.
- **Counter-arguments, recorded:**
  - Keeping the parent gives each theme more members and a gentler step up to the next level.
  - It is also the rule declared before looking. Any change must be labelled post-hoc in the paper.
- **ccode says keeping the child "breaks containment."** The reviewer disputes this: removing a node from a nested family cannot break containment among the remaining nodes. ccode is to give a concrete case if one exists.
- **Status:** NOT decided. Deferred to the decision point in section 15.

## 15. Agreed plan (Aviyah, 9 Oct)

1. Document everything up to this point (this report, plus ccode's records).
2. ccode reviews the descriptions of all pathways (the 10,770 universe, which includes leaves universe L) and makes the exclusion-2 list. The rule is declared before it is applied, the judging is blind to the clusters and to the reviewer's verdicts, and the result is documented in `data/excluded_inputs.tsv`, with the list and findings reported to Aviyah. Then ccode rebuilds universe L minus all exclusions, with the current algorithm (as thema_L_repair) and the current cal8 floors, and produces the DAG.
3. The reviewer re-runs the cluster evaluation on the new DAG. Themes whose member set is identical to a judged theme in thema_L_repair keep their verdict; all others are judged with rubric4.
4. **STOP for review and discussion.** The decisions after that:
   - chain threshold 0.90 vs 0.85, and the survivor rule (keep the higher-support node unless the parent is top-level);
   - the giant bucket roots;
   - whether to build the top level by recursive re-clustering (prompt 19).

## 16. Step 3 result: evaluation of thema_L_x2 (9 Oct)

Full write-up: `data/experiments/reviewer_eval_x2_2026-10-09/REPORT_x2.md`.

- **Exclusions:** 23 sets excluded from the 10,770 (17 + 6); 20 were in L, so L goes 5,559 → 5,539. GO:0010800 should be reinstated (its name is specific).
- **thema_L_x2: 8,740 themes, 97.7% coherent or umbrella** (thema_L_repair: 97.4%). Incoherent 44 → 18; small incoherent 39 → 8. The housekeeping-BTM family is gone.
- **The top got worse:** all 10 roots over 1,000 members are bad (9 incoherent, 1 mixture), and 4 of the 6 themes of 301-1,000 are bad. Up to 300 members, every band is 97.7-100% ok.
- **Judge consistency:** 98.9% agreement on matched themes (about 1% noise).
- **Stability:** 89-91% of themes with support ≥ 0.1 reproduce in this independent build. The churn is in low-support themes.
- **STOP here** for the step-4 discussion (chains and survivor, giant roots, recursive top level).

## 17. Follow-up questions on thema_L_x2 (Aviyah, 9 Oct)

### 17.1 The 5-member "leftover" cluster n01292 (support 0.695)

Members: btm:M138 (enriched for ubiquitination), M161, M174, M243, M248 (the last four unnamed).

Their descriptions:
- **M138:** ubiquitin ligases and deubiquitinases, plus RAS / PI3K / S6K growth signalling.
- **M161:** RB1 and BCL2L1, proliferation vs survival, plus RNF6 / HERC4 ligases.
- **M174:** Polycomb chromatin repression, plus CUL5 / RNF6 / RNF138 ligases and ER translocation.
- **M243:** mitochondrial housekeeping, plus a proteasome subunit.
- **M248:** centrosome / mitosis, Fanconi repair and E3 ligases.

**Shared thread by description:** each one mentions ubiquitin-dependent protein turnover in proliferating cells. That is a generic but real "proliferative housekeeping and protein turnover" theme, so the cluster is a weak umbrella rather than incoherent. All five are blood co-expression modules whose descriptions list several arms.

### 17.2 Did the top get worse? Mostly no: it is a judging difference, not a structural one

- **Every large x2 theme has a close counterpart in thema_L_repair** (Jaccard 0.72-0.93):
  - metabolism 1,433 ↔ 1,405 (J 0.92);
  - immune 814 ↔ 826 (J 0.92);
  - nuclear genome / gene expression 789 ↔ 800 (J 0.93);
  - the 7 giant bags ↔ the old giant bags (J 0.56-0.91).
- **The verdicts changed, not the clusters.** The old large themes were judged in round 2 (rubric2: coherent / partial / incoherent). The new ones were judged with rubric4, which is stricter: an umbrella needs a stated specific link. Both used a 40-member random sample from 800-2,600 members.
- **Examples:** metabolism 1,433 went coherent → "incoherent"; nuclear genome 789 went coherent → "mixture"; immune 814 went coherent → umbrella.
- **Reviewer's view:** the metabolism and nuclear-genome themes are area-level themes, which the strict rubric penalises because 40 random members of an area look diverse. One real loss: the 1,751-member "development, adhesion, ECM, migration" theme of thema_L_repair (coherent) has no clean counterpart in x2.

### 17.3 Do we have clean area levels ("immune system", "cell signalling", ...)?

A name-keyword check (evaluation only) over themes of 80 or more members found:

| area | pathways named for it | best theme | recall | precision | support | verdict |
|---|---|---|---|---|---|---|
| immune | 427 | n01014 (814) | 0.88 | 0.46 | 0.805 | **yes: a clean immune area** |
| metabolism | 766 | n01438 (1,433) | 0.78 | 0.42 | 0.63 | **yes: a metabolism / transport area** |
| cell cycle / DNA | 137 | n04626 (369) | 0.80 | 0.30 | 0.105 | **yes: genome maintenance and cell division** |
| signalling | 669 | only the giant bags (2,000+) | 0.6-0.7 | ~0.2 | low | **no** |
| development | 440 | giant bags; the best clean one is 116 members | 0.18 | 0.67 | | **no** |
| neuro | 266 | giant bags; the best clean one is 98 members | 0.23 | 0.61 | | **no** |

Also present: nuclear genome / gene expression (789, support 0.695), RNA processing / translation (289), RTK signalling (213), DNA repair (181), glycosylation (180), hemostasis + eicosanoids (155).

**Why signalling, development and neuro have no area:**
- They form one large continuum in the embedding: signalling pathways run through development, neuro and cancer.
- Ward cuts that continuum differently in every run, so no stable 300-800-member sub-area recurs.
- What recurs, rarely (support 0.04-0.47), is "half of the universe", and the 10+ floor (0.025) lets those halves through as overlapping giant bags.
- This is the reviewer's working explanation, consistent with the low support and heavy overlap of the giants; it is not yet tested.
- It is the case for the recursive top level (prompt 19): cluster the good middle themes into areas, instead of relying on Ward's top splits.
