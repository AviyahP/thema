# Task B input: name-v3 render against name-v4 render, on 20 real internal nodes

*Generated 28 Sep 2026. Nothing sent. Twenty internal nodes of
`recurrent_dag_consensus_centred`, chosen to span the DIRECT-member count evenly,
because that is the quantity the change acts on. The worked-examples preamble is identical in
both renders and is included in the word counts, so the counts understate the relative change.*

**The change.** v3 showed the children's names, each direct member as a bare
`[source] name (inclusion)`, and three "representative members" that were
`member_keys[:3]` in FILE ORDER. v4 drops those three and gives every direct member its
source, name, inclusion and full description, highest inclusion first.

| node | children | direct | v3 words | v4 words | change |
|---|---|---|---|---|---|
| `n0000` | 2 | 0 | 711 | 341 | -52% |
| `n0238` | 2 | 0 | 686 | 339 | -51% |
| `n0383` | 2 | 0 | 687 | 339 | -51% |
| `n0547` | 2 | 0 | 696 | 344 | -51% |
| `n0737` | 2 | 0 | 695 | 341 | -51% |
| `n0034` | 2 | 1 | 685 | 473 | -31% |
| `n0515` | 2 | 1 | 672 | 470 | -30% |
| `n0766` | 2 | 1 | 697 | 474 | -32% |
| `n0405` | 1 | 2 | 682 | 608 | -11% |
| `n0767` | 2 | 2 | 695 | 613 | -12% |
| `n0109` | 1 | 3 | 689 | 737 | +7% |
| `n0334` | 1 | 3 | 728 | 771 | +6% |
| `n0494` | 1 | 3 | 740 | 777 | +5% |
| `n0633` | 1 | 3 | 698 | 746 | +7% |
| `n0728` | 1 | 3 | 698 | 742 | +6% |
| `n0861` | 1 | 3 | 695 | 741 | +7% |
| `n0467` | 1 | 4 | 732 | 923 | +26% |
| `n0761` | 1 | 4 | 724 | 888 | +23% |
| `n0783` | 2 | 5 | 739 | 1,040 | +41% |
| `n0845` | 44 | 65 | 1,464 | 9,755 | +566% |

Median words: v3 697, v4 737.

## Why the three samples were not representative

They were `member_keys[:3]` -- the first three rows of `members.tsv` for that node, which is
grouping order, not medoid order and not inclusion order. The test that matters is whether a
sample was even a DIRECT member, because a sample that sits inside a child tells the model
nothing about what the parent adds -- the children's names already covered it.

**10 of 60 samples across these 20 nodes were direct members.** The other 50 described
biology the model could already see through a child's name.

| node | sample 1 | direct? | sample 2 | direct? | sample 3 | direct? |
|---|---|---|---|---|---|---|
| `n0000` | nucleotide metabolic process | no | ribonucleoside metabolic process | no | pyrimidine nucleoside monophosph | no |
| `n0238` | platelet degranulation | no | hemostasis | no | negative regulation of platelet  | no |
| `n0383` | fatty acid alpha-oxidation | no | vitamin A metabolic process | no | folic acid-containing compound b | no |
| `n0547` | cellular response to starvation | no | TOR signaling | no | cellular response to stress | no |
| `n0737` | cell fate determination | no | somitogenesis | no | gastrulation | no |
| `n0034` | retina homeostasis | no | photoreceptor cell morphogenesis | no | photoreceptor cell outer segment | no |
| `n0515` | galactose metabolic process | no | UDP-N-acetylglucosamine biosynth | no | nucleotide-sugar metabolic proce | no |
| `n0766` | activation of NF-kappaB-inducing | no | peptidyl-threonine phosphorylati | no | obsolete peptidyl-serine modific | no |
| `n0405` | post-Golgi vesicle-mediated tran | no | Golgi to vacuole transport | no | obsolete vesicle targeting | no |
| `n0767` | triglyceride metabolic process | **yes** | regulation of very-low-density l | no | regulation of intestinal cholest | no |
| `n0109` | very long-chain fatty acid metab | no | alpha-linolenic acid metabolic p | no | long-chain fatty acid biosynthet | no |
| `n0334` | complement and other receptors i | **yes** | leukocyte mediated immunity | **yes** | positive regulation of myeloid l | no |
| `n0494` | intrinsic apoptotic signaling pa | no | positive regulation of intrinsic | **yes** | positive regulation of endoplasm | no |
| `n0633` | protein polyubiquitination | no | cytoplasmic stress granule disas | **yes** | ERAD pathway | **yes** |
| `n0728` | post-Golgi vesicle-mediated tran | **yes** | obsolete vesicle targeting | no | Golgi to plasma membrane protein | **yes** |
| `n0861` | neurotransmitter transport | no | positive regulation of glutamate | no | negative regulation of neurotran | no |
| `n0467` | protein export from nucleus | **yes** | viral translational termination- | no | Virus Assembly and Release | no |
| `n0761` | cAMP biosynthetic process | no | cAMP catabolic process | **yes** | G protein-coupled receptor signa | no |
| `n0783` | TBA | no | regulation of localization (GO) | no | phosphorylation | no |
| `n0845` | axon guidance | no | golgi membrane (I) | no | inositol phosphate metabolism | no |

---

## The two renders in full, on one node

`n0783`: 2 children, 5 direct members.

### name-v3

```
  [worked examples, identical in both renders, elided]

Child themes:
  - RTK family signaling: ERBB, FGFR, ALK, IGF1R
  - Kinase-driven growth signalling and its regulation

Direct members (5) -- in this theme but in NO child:
  - [reactome] VEGFR2 mediated cell proliferation  (inclusion 0.33)
  - [reactome] TGFBR2 Kinase Domain Mutants in Cancer  (inclusion 0.29)
  - [reactome] VEGFA-VEGFR2 Pathway  (inclusion 0.29)
  - [reactome] SMAD2/3 Phosphorylation Motif Mutants in Cancer  (inclusion 0.25)
  - [reactome] Constitutive Signaling by AKT1 E17K in Cancer  (inclusion 0.25)

Representative members:

  [btm] TBA
      These genes converge on the braking and tuning of growth-factor signalling as it feeds into transcription, a control layer whose loss produces overgrowth, cancer and neurodevelopmental disease. Two GTPase-activating proteins, RASA2 for Ras and ACAP2 for an Arf-family GTPase, terminate signalling at the membrane, while MAP3K2 relays kinase input downstream and sorting nexins SNX13 and SNX14 govern endosomal trafficking and receptor fate. In the nucleus, the CREBBP acetyltransferase and the Mediator subunit MED1 couple activated signals to RNA polymerase II, and the NF-kappaB family member REL drives inflammatory and lymphoid transcription. Degradative and phosphorylation-based control comes from the FBXW7 ubiquitin ligase substrate receptor, which destroys short-lived growth regulators, and the DYRK1A kinase; STRN3 links the module to striatin-containing phosphatase complexes and Hippo pathway output. Many members are recurrently mutated in developmental disorders and tumours.

  [btm] regulation of localization (GO)
      Cells constantly decide where proteins, vesicles and lipids should be, and this collection covers the control of that positioning rather than transport itself. The genes span several routes by which a signal changes a molecule's location: kinase signalling that drives effectors to membranes, as with AKT1 and its substrate TSC2 or the MAP2K2 arm of the MAPK cascade; small GTPase regulation, where ARHGDIA sequesters Rho GTPases in the cytosol and ARAP1 acts as a GTPase-activating protein toward Arf and Rho family members; sorting and recycling of internalised receptors through the endosomal adaptor SNX17; and membrane fusion steps needed for regulated secretion, including SNAP-alpha and the Munc18 family member STXBP2 required for cytotoxic granule release. Filamin A anchors receptors to actin, while TGFB1 and the nuclear receptor NR1H2 link extracellular and lipid cues to these placement decisions.

  [go] phosphorylation
      Attaching a phosphate group to a protein, sugar or lipid substrate is the cell's most widely used switch, and this collection spans essentially the whole enzymology of that reaction. Protein kinases dominate: receptor tyrosine kinases for growth factors and cytokines (EGFR, FGFRs, PDGFRs, KIT, INSR), the cytoplasmic tyrosine kinases and JAK family that relay them, and serine/threonine cascades running through RAF-MEK-ERK, PI3K-AKT-MTOR, the polo, aurora, NEK and cyclin-dependent kinases that time mitosis, and checkpoint kinases such as ATM and CHEK1/2. Alongside them sit metabolic phosphotransferases -- hexokinases, phosphofructokinase-2 family enzymes, galactokinase, nucleotide and sugar kinases -- that trap and commit substrates to glycolysis and other routes. Also present are the phosphatases, pseudokinase decoys and inhibitory subunits that reverse or restrain the reaction, since the biological information lies in the balance. Deregulated kinase activity underlies much of oncogenesis and is the target of a large share of modern drugs.

```

### name-v4

```
  [worked examples, identical in both renders, elided]

Child themes (2), already named:
  - RTK family signaling: ERBB, FGFR, ALK, IGF1R
  - Kinase-driven growth signalling and its regulation

Direct members (5) -- in this theme but in NO child:

  [reactome] VEGFR2 mediated cell proliferation  (inclusion 0.33)
      Endothelial cells divide in response to VEGF, and this is the branch of VEGFR2 signalling that drives that proliferation — the basis of angiogenesis in development, wound healing and tumour vascularisation, and the target of anti-VEGF drugs. VEGFA binding to the KDR receptor triggers Src-dependent phosphorylation of the receptor tail, which recruits and activates phospholipase C gamma; the resulting inositol trisphosphate opens IP3 receptor channels on the endoplasmic reticulum, releasing calcium that, with calmodulin, cooperates with diacylglycerol to activate conventional protein kinase C isoforms. PKC then feeds into the Ras/Raf/MEK/ERK cascade, either by phosphorylating Raf directly or by acting on Ras itself — here through relief of GTPase-activating protein restraint rather than exchange-factor recruitment. Sphingosine kinase and PDPK1 add further lipid and kinase input, linking the same receptor to survival as well as growth.

  [reactome] TGFBR2 Kinase Domain Mutants in Cancer  (inclusion 0.29)
      TGF-beta normally restrains epithelial proliferation, and tumours frequently escape that restraint by damaging the receptor that receives the signal. Missense changes in the kinase domain of the type II TGF-beta receptor, TGFBR2, occur in a substantial minority of microsatellite stable colorectal cancers and in esophageal carcinoma, and they abolish the growth-inhibitory response to TGFB1 while leaving the ligand and the type I receptor intact. In the normal sequence, TGFB1 binding brings TGFBR2 and TGFBR1 into a heteromeric complex in which TGFBR2 kinase activity transphosphorylates TGFBR1 to launch SMAD-dependent transcription of cell cycle inhibitors. Kinase-domain mutants cannot perform that step; some appear to act dominant-negatively by sequestering partners in a non-signalling complex. Loss of this cytostatic arm removes a tumour-suppressive brake on epithelial cells, which is one route by which colorectal and esophageal tumours acquire unchecked proliferation.

  [reactome] VEGFA-VEGFR2 Pathway  (inclusion 0.29)
      New blood vessels sprout from existing ones under the control of vascular endothelial growth factor A acting on its endothelial receptor tyrosine kinase VEGFR2 (KDR), and this axis is the principal driver of angiogenesis in development, wound healing, tumour growth and diabetic retinopathy; loss of the receptor kills mouse embryos for lack of endothelial and blood island formation, while blocking the ligand is standard anti-angiogenic therapy. Ligand binding triggers receptor autophosphorylation and recruitment of adaptors such as SHB, NCK and SRC, feeding PLCG1-calcium-PKC signalling, RAS-p38 MAPK activation through MAPKAPK2 and HSPB1, and PI3K-AKT-mTOR survival signalling. Rho-family GTPases with WAVE complex and PAK/ROCK effectors remodel actin for endothelial migration and sprouting, focal adhesion and VE-cadherin junction components govern adhesion and permeability, and eNOS activation supplies nitric oxide for vasodilation.

  [reactome] SMAD2/3 Phosphorylation Motif Mutants in Cancer  (inclusion 0.25)
      TGF-beta signalling normally restrains epithelial proliferation, and cancers frequently escape that restraint by breaking the step at which the receptor writes its signal onto its effectors. Ligand-bound TGFBR2 recruits and activates the TGFBR1 kinase, which phosphorylates the conserved C-terminal Ser-Ser-X-Ser motif of SMAD2 and SMAD3 after the anchoring protein ZFYVE9 presents them at the membrane; phosphorylated SMAD2/3 then assemble heterotrimers with SMAD4 and enter the nucleus to direct growth-inhibitory transcription. Cancer-associated mutants of this phosphorylation motif substitute, delete or truncate the critical serines, so the receptor complex can no longer activate them, the heterotrimer never forms, and the antiproliferative arm of the pathway is silenced. Loss of this input contributes to tumour growth and to the switch of residual TGF-beta signalling toward invasion, while leaving receptor activation itself intact.

  [reactome] Constitutive Signaling by AKT1 E17K in Cancer  (inclusion 0.25)
      AKT sits at the centre of growth factor signalling, and a single glutamate-to-lysine change at position 17 of AKT1 turns that node on permanently, driving the survival and proliferation programmes that underlie breast, ovarian and other cancers. Normally AKT must wait for PI3K to generate PIP3 before its PH domain docks at the membrane; the E17K substitution lets the kinase bind the abundant lipid PIP2 instead, so membrane recruitment no longer reports on receptor activity. Once there it is phosphorylated by PDPK1 and by the rapamycin-insensitive mTOR complex containing RICTOR, MLST8 and MAPKAP1, and becomes constitutively active. The downstream consequences are the familiar ones: FOXO transcription factors and GSK3 are inactivated, BAD and caspase-9 are silenced to block apoptosis, MDM2 is activated against p53, TSC2 is relieved so mTORC1 drives translation, and CDKN1A and CDKN1B are held away from the cell cycle machinery.

```

