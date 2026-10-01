# Names — `v0.2.2-subset-1850-c50`, levels 0 and 1

*`name-v5`, claude-sonnet-5. Level 0: **287 leaves, 283 named, 4 unnameable**. Level 1: **215 nodes**, re-named under the child-rationale rendering after the reviewer's read. Levels 2+ are unnamed — skipped, not refused.*

Ordered by cohesion, most cohesive first — mean pairwise cosine among members in the centred space, from `scripts/cohesion_reference.py`. Cohesion did not enter the naming; it is shown so refusals can be compared against it.

---

## Reviewer's verdict — level 0, all 287 read

| | share |
|---|---|
| tight and true | **~88%** |
| acceptable | ~8% |
| faulty | **~4%** |

**All four refusals judged correct.** Names are never hand-edited; a faulty name is a finding about the prompt, not something to fix in the file.

The faulty eight, as the reviewer classified them:

| node | fault | name at the time of the read |
|---|---|---|
| `n0031` | invented word | DNA replication and licensing |
| `n0201` | invented word | Kinetochore-driven mitotic chromosome segregation control |
| `n0176` | invented word | CCR7-driven dendritic cell trafficking and survival |
| `n0790` | invented word | Growth hormone, IGF and HPA axis signalling |
| `n0572` | member not covered | Metal ion and xenobiotic homeostasis |
| `n0400` | member not covered | Redox and selenium-dependent peroxide handling |
| `n0601` | member not covered | Regulation of intracellular protein trafficking |
| `n0420` | member not covered | Extracellular matrix and platelet-mediated hemostatic adhesion |

Three of the four *invented word* cases — `licensing`, `CCR7`, `kinetochore` — occur 5, 3 and 5 times in the members' own descriptions. The word was read, not invented; what the reviewer objected to is a word from one or two members being promoted to define the whole cluster. The `invented_word` check tests word presence and therefore catches only `HPA`, which occurs zero times. That limit is stated rather than tuned around.

---

## Reviewer's verdict — level 1, all 215 nodes read

**~85% good.** The dominant fault is one thing: **a parent named NARROWER than one of its own children** — 16 clear and 12 borderline.

The cause is in the data, not the instruction. A direct pathway arrived with a title AND a description; a child arrived as one bare line. The descriptions outweighed the children and pulled the name down to them.

| | nodes |
|---|---|
| clear | `n0206`, `n0426`, `n0618`, `n0486`, `n0593`, `n0642`, `n0104`, `n0273`, `n0506`, `n0531`, `n0620`, `n0719`, `n0474`, `n0716`, `n0625`, `n0193` |
| borderline | `n0557`, `n0596`, `n0775`, `n0398`, `n0044`, `n0493`, `n0244`, `n0592`, `n0037`, `n0453`, `n0581`, `n0622` |

**Acted on, and measured:** each child now carries its rationale under `Child clusters:`, putting the two kinds of member on comparable footing. The system prompt did not change — digest `f3d1f074929df02a` before and after. The A/B is in `docs/status/level1-ab.md`: of the 28, 20 cover their child by the mechanical check and 23 by reading, and the whole level was then re-named under the one rendering. `invented_word` was NOT tuned further.

---

## The four refusals

**`n0640`** · cohesion **0.160** · 6 members

> The members span embryo lineage specification, endometrial/decidual biology, hormone response signalling, general tissue maturation, and erythroid biology, sharing no single specific process beyond generic developmental physiology.

- inner cell mass cell differentiation
- response to erythropoietin
- decidualization
- primitive erythrocyte differentiation
- cellular response to progesterone stimulus
- anatomical structure maturation

**`n0518`** · cohesion **0.180** · 6 members

> The members span unrelated themes—proteolytic maturation and its regulation, peptide biosynthesis, xenobiotic/herbicide and phytoestrogen responses, and copulation physiology—with no single specific process common to all beyond generic biology.

- copulation
- response to herbicide
- protein processing
- regulation of proteolysis
- response to genistein
- peptide biosynthetic process

**`n0508`** · cohesion **0.273** · 7 members

> Most members describe NADPH oxidase-driven respiratory burst and oxidative microbial killing, but the macrophage/microglia identity pathway and the host-metabolism manipulation pathway share no such oxidative-burst theme, so any single name covering all members would be too broad or invented.

- TBA *(untitled BTM module)*
- respiratory burst involved in defense response
- neutrophil-mediated killing of gram-negative bacterium
- regulation of superoxide metabolic process
- RHO GTPases Activate NADPH Oxidases
- Events associated with phagocytolytic activity of PMN cells
- Manipulation of host energy metabolism

**`n0441`** · cohesion **0.392** · 6 members

> The members span unrelated RNA processes—nuclear pre-mRNA splicing, RNA polymerase III transcription/termination/initiation, and mitochondrial RNA turnover—so any single theme covering all would be as broad as 'RNA metabolism', which invents a specificity not shared by every member.

- mRNA 3'-splice site recognition
- regulation of mitochondrial RNA catabolic process
- transcription by RNA polymerase III
- U2-type prespliceosome assembly
- RNA Polymerase III Transcription Termination
- RNA Polymerase III Abortive And Retractive Initiation

---

## Level 0 — 287 leaves

| node | cohesion | name |
|---|---|---|
| `n0022` | 0.808 | Drug-resistant FLT3 kinase mutants |
| `n0192` | 0.778 | Nucleotide biosynthesis and metabolism |
| `n0031` | 0.753 | DNA replication and licensing |
| `n0020` | 0.749 | Base excision repair glycosylase step |
| `n0137` | 0.709 | Metanephric tubule and collecting duct development |
| `n0119` | 0.708 | Specialized pro-resolving lipid mediator biosynthesis |
| `n0023` | 0.707 | Kinetochore-microtubule attachment regulation |
| `n0100` | 0.699 | Postsynaptic density and synapse assembly |
| `n0056` | 0.692 | Triglyceride-rich lipoprotein remodeling and clearance |
| `n0054` | 0.672 | APC/C control of mitotic exit |
| `n0226` | 0.669 | Sister chromatid cohesion maintenance |
| `n0053` | 0.666 | Nucleotide excision repair `copies_member` |
| `n0224` | 0.656 | Cristae architecture and MICOS complex |
| `n0027` | 0.655 | Cell cycle progression and division |
| `n0212` | 0.651 | Cardiac action potential repolarization |
| `n0078` | 0.648 | Homologous recombination repair of DNA double-strand breaks |
| `n0227` | 0.646 | Nef-mediated receptor downregulation |
| `n0076` | 0.640 | Axon and dendrite outgrowth regulation |
| `n0099` | 0.630 | Nephron and kidney morphogenesis |
| `n0079` | 0.620 | Dolichol-linked glycosylation precursor synthesis |
| `n0138` | 0.617 | Drug metabolism and disposition |
| `n0225` | 0.614 | Catecholamine and phenolic amine catabolism |
| `n0201` | 0.612 | Kinetochore-driven mitotic chromosome segregation control |
| `n0139` | 0.610 | Mitochondrial oxidative phosphorylation |
| `n0189` | 0.609 | Lymphocyte migration and chemotaxis regulation |
| `n0030` | 0.600 | TGF-beta/BMP-SMAD signalling regulation |
| `n0028` | 0.600 | Translesion DNA synthesis and its termination |
| `n0177` | 0.599 | Signalling control of mesodermal fate commitment |
| `n0098` | 0.598 | Cardiac septation and outflow tract morphogenesis |
| `n0187` | 0.596 | Intrinsic mitochondrial apoptotic signaling |
| `n0074` | 0.588 | Insulin secretion regulation |
| `n0182` | 0.583 | Excitation-contraction coupling in muscle `duplicate_name` |
| `n0019` | 0.581 | Cardiac conduction system electrical propagation |
| `n0480` | 0.579 | Deoxyribonucleotide synthesis and catabolism |
| `n0146` | 0.577 | Lipoprotein particle assembly and transport |
| `n0326` | 0.576 | Purine and pyrimidine nucleoside salvage and catabolism |
| `n0161` | 0.567 | Lens fiber cell differentiation `copies_member` |
| `n0237` | 0.566 | Nucleoside and nucleotide salvage |
| `n0029` | 0.566 | Small RNA-guided gene silencing |
| `n0049` | 0.564 | IL-6/gp130-JAK-STAT3 signaling |
| `n0170` | 0.561 | Cell-cell and matrix adhesion |
| `n0075` | 0.561 | Lipoprotein particle metabolism and transport |
| `n0114` | 0.559 | Melanocyte pigmentation biology |
| `n0087` | 0.558 | Cardiac muscle cell development and differentiation |
| `n0153` | 0.555 | MHC class I antigen presentation induction |
| `n0228` | 0.554 | Regulation of IRE1/PERK UPR signalling |
| `n0032` | 0.554 | Renin-angiotensin regulation of blood pressure and volume |
| `n0190` | 0.552 | Innate sensing of bacterial molecules |
| `n0026` | 0.547 | Complement cascade activation and regulation |
| `n0159` | 0.547 | Regulation of E-cadherin adhesion `sentence_case` |
| `n0109` | 0.546 | Amino sugar and carbohydrate catabolism |
| `n0140` | 0.542 | Congenital disorders of protein glycosylation |
| `n0173` | 0.541 | DNA damage repair pathways `pathways` |
| `n0052` | 0.536 | Copper ion homeostasis and detoxification |
| `n0167` | 0.536 | Hexose transport and its regulation |
| `n0155` | 0.535 | Translation `copies_member` |
| `n0136` | 0.530 | Defective coagulation factor variants causing bleeding disorders |
| `n0220` | 0.526 | Fatty acid oxidation and ketone body metabolism |
| `n0210` | 0.526 | Smooth muscle contraction regulation |
| `n0149` | 0.526 | RNA polymerase II transcription initiation and elongation, including HIV Tat-dependent control `in_range;sentence_case` |
| `n0072` | 0.525 | Circadian transcriptional feedback loop |
| `n0112` | 0.522 | Hemostasis and thrombin/PAR signalling |
| `n0328` | 0.521 | Recombination-based telomere and genome maintenance |
| `n0175` | 0.520 | Type I interferon antiviral effector response |
| `n0097` | 0.518 | Antimicrobial peptide-mediated humoral defence |
| `n0284` | 0.517 | Nucleotide pool sanitation and catabolism |
| `n0131` | 0.514 | Amino acid transmembrane transport |
| `n0101` | 0.510 | Host-directed viral mRNA translation and transcription |
| `n0051` | 0.510 | Long-chain and very long-chain fatty acid metabolism |
| `n0169` | 0.508 | Death receptor-induced caspase-8 activation |
| `n0188` | 0.507 | Regulation of protein kinase activity |
| `n0110` | 0.507 | Muscle cell proliferation and differentiation |
| `n0151` | 0.505 | Control of glial cell generation |
| `n0069` | 0.500 | Sarcomere assembly and contraction |
| `n0709` | 0.493 | Intestinal lipid and sterol absorption |
| `n0203` | 0.493 | Intracellular vesicle transport |
| `n0088` | 0.492 | Regulation of telomere maintenance |
| `n0057` | 0.491 | Inherited disorders of carbohydrate metabolism |
| `n0287` | 0.488 | RNA polymerase I and III transcription |
| `n0172` | 0.488 | Regulation of cell-matrix adhesion turnover |
| `n0148` | 0.487 | Cytoplasmic mRNA turnover and 3'-end processing |
| `n0184` | 0.487 | MHC-restricted antigen processing and presentation |
| `n0093` | 0.486 | Steroid hormone receptor transcriptional regulation |
| `n0127` | 0.485 | Digestion and intestinal nutrient absorption |
| `n0118` | 0.484 | Mitotic spindle assembly and positioning |
| `n0018` | 0.481 | Mitophagy `copies_member` |
| `n0115` | 0.481 | Myeloid leukocyte degranulation and effector immunity |
| `n0211` | 0.480 | Cholesterol biosynthesis and homeostasis |
| `n0160` | 0.478 | Regulation of leukocyte-endothelial adhesion |
| `n0150` | 0.476 | CD4 T cell activation and lineage differentiation |
| `n0207` | 0.476 | Retinoid metabolism and signaling |
| `n0408` | 0.475 | Central carbon and fasting fuel metabolism |
| `n0145` | 0.473 | Phototransduction in vision |
| `n0133` | 0.473 | Regulation of calcium ion transmembrane transport `copies_member` |
| `n0055` | 0.472 | Rho family GTPase cycle |
| `n0073` | 0.470 | Phospholipid and phosphatidic acid biosynthesis |
| `n0012` | 0.469 | Photoreceptor development and maintenance |
| `n0105` | 0.468 | Sperm-egg fertilization |
| `n0024` | 0.466 | Cell-cell junction assembly and organization |
| `n0064` | 0.465 | Regulation of type I interferon production and signaling |
| `n0168` | 0.464 | Synaptic vesicle cycle and neurotransmitter release |
| `n0174` | 0.461 | B cell identity and receptor signalling |
| `n0689` | 0.459 | Embryonic axis and neural patterning |
| `n0108` | 0.459 | Glomerular mesangial cell and capillary development |
| `n0048` | 0.459 | Adipogenesis and adipose lipid storage |
| `n0129` | 0.458 | Glutamate-driven excitatory synaptic plasticity |
| `n0223` | 0.456 | T cell receptor signalling and activation |
| `n0616` | 0.456 | Cell cycle checkpoint control |
| `n0077` | 0.455 | Prostaglandin synthesis and signaling |
| `n0677` | 0.454 | tRNA and mitochondrial gene expression maturation |
| `n0063` | 0.451 | Cytoskeletal transport of organelles and vesicles |
| `n0336` | 0.451 | Regional patterning of the neural tube |
| `n0191` | 0.450 | Nuclear export of RNA |
| `n0111` | 0.450 | Regulation of neuronal cytoskeletal growth |
| `n0369` | 0.449 | Protein glycosylation and proteoglycan biosynthesis |
| `n0185` | 0.446 | Cellular cholesterol and lipoprotein sensing in foam cell formation |
| `n0050` | 0.446 | Regulation of amyloid-beta production and clearance |
| `n0477` | 0.445 | Regulation of lipid biosynthesis and fatty acid metabolism |
| `n0176` | 0.445 | CCR7-driven dendritic cell trafficking and survival |
| `n0345` | 0.444 | GABA and glutamate/aspartate neurotransmitter transport |
| `n0334` | 0.442 | Early embryonic axis and germ layer formation |
| `n0245` | 0.441 | Toll-like receptor and macrophage activation signalling |
| `n0117` | 0.440 | Nucleolar rRNA processing and ribosome subunit maturation |
| `n0015` | 0.437 | Smooth muscle cell phenotype regulation |
| `n0199` | 0.437 | Endothelial shear stress mechanotransduction |
| `n0272` | 0.437 | T-helper cell subset differentiation and function |
| `n0448` | 0.436 | Chondroitin/dermatan sulfate metabolism and disorders |
| `n0278` | 0.434 | Membrane trafficking dynamics |
| `n0186` | 0.433 | IL-1-driven inflammatory response |
| `n0166` | 0.431 | Calcium handling in muscle relaxation |
| `n0021` | 0.430 | Oxidative stress response and antioxidant defence |
| `n0277` | 0.428 | tRNA maturation and modification |
| `n0198` | 0.427 | ERBB2/EGFR receptor signaling |
| `n0068` | 0.426 | Beta-catenin destruction complex regulation |
| `n0255` | 0.426 | VEGF signalling in vascular and lymphatic development |
| `n0626` | 0.425 | Regulation of Th1 and cytotoxic lymphocyte immunity |
| `n0089` | 0.424 | Transmembrane ion transport and homeostasis |
| `n0410` | 0.422 | Base excision and single-strand break repair |
| `n0317` | 0.421 | Peroxisome biogenesis and protein import |
| `n0355` | 0.419 | Cytoskeletal transport of organelles |
| `n0157` | 0.419 | Branched actin nucleation and lamellipodium formation |
| `n0476` | 0.419 | Regulation of the unfolded protein response |
| `n0194` | 0.418 | mRNA 3' end maturation and decay |
| `n0154` | 0.416 | PI3K/AKT activation downstream of growth factor receptors |
| `n0171` | 0.415 | Regulation of cell surface receptor turnover |
| `n0094` | 0.415 | Gonadotropin control of ovarian and gonadal function |
| `n0499` | 0.415 | Cranial nerve and pharyngeal organ morphogenesis |
| `n0584` | 0.413 | Mitochondrial genome expression and maintenance |
| `n0208` | 0.413 | Non-coding RNA modification and maturation |
| `n0580` | 0.411 | Mitotic cell division |
| `n0731` | 0.410 | Cholesterol homeostasis and sterol sensing |
| `n0559` | 0.410 | Synaptic transmission and plasticity regulation |
| `n0095` | 0.409 | Water balance and aquaporin function |
| `n0219` | 0.409 | Cortical polarity and centrosome positioning |
| `n0196` | 0.408 | FGFR ligand binding and downstream signalling |
| `n0113` | 0.407 | Endomembrane trafficking and autophagy |
| `n0134` | 0.405 | Regulation of insulin-driven glucose uptake and glycogen synthesis |
| `n0264` | 0.403 | Neural response to drugs of abuse |
| `n0135` | 0.403 | Motile cilia biogenesis and beat regulation |
| `n0542` | 0.402 | Nucleotide catabolism and methylation pharmacogenetics |
| `n0209` | 0.402 | Renal amino acid reabsorption and transport |
| `n0599` | 0.401 | Mitochondrial metabolite shuttling and ureagenesis |
| `n0047` | 0.401 | Ubiquitin-dependent proteasomal degradation |
| `n0285` | 0.400 | Ionotropic and inhibitory synaptic signalling |
| `n0358` | 0.400 | Chaperone-mediated protein folding |
| `n0595` | 0.399 | Regional CNS neuron specification and patterning |
| `n0318` | 0.399 | Chromatin and epigenetic regulation |
| `n0130` | 0.398 | Epidermal and appendage differentiation |
| `n0252` | 0.398 | Axon guidance signalling and morphogenesis |
| `n0158` | 0.395 | Chondrocyte differentiation and endochondral ossification |
| `n0690` | 0.393 | p53-mediated cell cycle checkpoint control |
| `n0441` | 0.392 | **UNNAMEABLE** |
| `n0096` | 0.392 | Chromatin-based epigenetic regulation |
| `n0389` | 0.390 | Heme synthesis, catabolism and bilirubin clearance |
| `n0338` | 0.390 | Feedback regulation of Hippo and MAPK signalling `sentence_case` |
| `n0583` | 0.390 | Axial patterning and organogenesis of embryo |
| `n0429` | 0.388 | p53-driven transcriptional and apoptotic response to damage |
| `n0041` | 0.388 | Bile acid and sterol homeostasis |
| `n0654` | 0.384 | Axon guidance and growth cone signalling |
| `n0451` | 0.384 | Collagen and keratin structural assembly |
| `n0551` | 0.382 | rRNA and mRNA processing machinery |
| `n0178` | 0.380 | Cytokine signalling to epithelial barriers |
| `n0454` | 0.378 | TAK1/NIK-driven NF-kB and MAPK signalling |
| `n0200` | 0.376 | Mitochondrial amino acid and nucleobase catabolism disorders |
| `n0550` | 0.376 | Cholinergic and opioid neurotransmission signalling |
| `n0107` | 0.375 | Mammary gland development and morphogenesis |
| `n0061` | 0.374 | Cellular senescence `copies_member` |
| `n0478` | 0.374 | MHC-restricted antigen presentation to T cells |
| `n0222` | 0.373 | Nucleotide triphosphate and phosphate metabolism |
| `n0614` | 0.373 | Host regulation of viral replication and entry |
| `n0733` | 0.373 | Endosomal peptide transport in innate immune sensing |
| `n0202` | 0.373 | Myeloid and leukocyte lineage commitment |
| `n0043` | 0.370 | Selective autophagic clearance of protein aggregates |
| `n0091` | 0.369 | B cell development and antibody diversification |
| `n0221` | 0.367 | Amino acid catabolism to cofactors and mediators |
| `n0356` | 0.367 | TNF-driven NF-kappaB signaling |
| `n0466` | 0.366 | Meiotic chromosome segregation and division |
| `n0465` | 0.365 | NF-kappaB and JNK activation via TAK1/IKK signaling |
| `n0248` | 0.365 | HIF-mediated hypoxia response |
| `n0183` | 0.364 | Immune checkpoint restraint of T cell responses |
| `n0411` | 0.363 | Sex steroid and adrenal corticosteroid synthesis |
| `n0296` | 0.362 | Meiosis in gametogenesis |
| `n0090` | 0.358 | Cellular osmotic and salt stress response |
| `n0516` | 0.357 | Nutrient and stress sensing in growth control |
| `n0779` | 0.357 | TAK1-driven MAPK and NF-kB activation |
| `n0147` | 0.355 | Regulation of osteoclast formation and activity |
| `n0799` | 0.353 | Forebrain regional development and neurogenesis |
| `n0597` | 0.353 | Branching morphogenesis of tubular organs |
| `n0386` | 0.352 | Vesicular transport in the secretory and endocytic pathways `pathways` |
| `n0613` | 0.352 | Organogenesis and body patterning by Hox and craniofacial programs `sentence_case` |
| `n0246` | 0.351 | Receptor tyrosine kinase and cytokine signalling in mesenchymal remodelling |
| `n0247` | 0.349 | Water- and fat-soluble vitamin transport and folate synthesis |
| `n0156` | 0.349 | Endoderm-derived epithelial identity and maturation |
| `n0561` | 0.347 | Glycolysis and related nucleotide-cofactor metabolism `related` |
| `n0128` | 0.347 | Antibody-mediated hypersensitivity and Fc receptor signalling `sentence_case` |
| `n0419` | 0.346 | Organogenesis of head and visceral organs |
| `n0509` | 0.345 | cAMP-calcium signaling to CREB transcription |
| `n0132` | 0.343 | Homeostatic control of progenitor cell numbers |
| `n0433` | 0.341 | GTPase signalling in adhesion and vascular growth |
| `n0653` | 0.341 | Myeloid cytokine production in innate immune defense |
| `n0253` | 0.340 | Ubiquitin-proteasome control of regulatory protein levels |
| `n0378` | 0.340 | Chemotactic leukocyte recruitment |
| `n0570` | 0.340 | Amino acid metabolism and catabolism |
| `n0324` | 0.339 | Sensory transduction across modalities |
| `n0344` | 0.338 | Nuclear pore complex traffic and envelope dynamics |
| `n0452` | 0.336 | Monosaccharide interconversion and redox metabolism |
| `n0611` | 0.335 | Glycosaminoglycan and sulfate handling in connective tissue disease |
| `n0327` | 0.333 | Regulation of cytoplasmic translation |
| `n0401` | 0.333 | Glycosaminoglycan sulfation and chondrodysplasia genetics |
| `n0152` | 0.333 | Sphingomyelin metabolism and ceramide signalling |
| `n0754` | 0.331 | Cellular stress response pathways `pathways` |
| `n0517` | 0.329 | Apical epithelial surface organisation |
| `n0116` | 0.328 | Notch signaling |
| `n0310` | 0.326 | Myogenic differentiation and regeneration |
| `n0320` | 0.322 | Neural regulation of locomotor behavior |
| `n0025` | 0.321 | Attenuation of receptor tyrosine kinase signalling |
| `n0288` | 0.320 | GPCR–cyclic nucleotide signalling via adenylate cyclase |
| `n0663` | 0.320 | B cell development and humoral immune regulation |
| `n0303` | 0.319 | Sensory transduction by stimulus-gated ion channels |
| `n0323` | 0.319 | TP53-mediated damage response and apoptosis |
| `n0319` | 0.319 | T and B lymphocyte development and signalling |
| `n0582` | 0.317 | IgE-mediated allergic effector cell activation |
| `n0691` | 0.314 | Vitamin D and phosphate homeostasis |
| `n0391` | 0.314 | Protein hydroxylation and histidine/lysine methylation |
| `n0659` | 0.313 | Calcium-calcineurin control of cardiac and muscle growth |
| `n0641` | 0.312 | Wnt and Hedgehog signalling regulation `sentence_case` |
| `n0286` | 0.309 | Regulation of RNA polymerase II transcription initiation |
| `n0337` | 0.307 | Mitochondrial permeability and apoptotic signalling |
| `n0243` | 0.306 | Regulation of vascular and epithelial growth |
| `n0254` | 0.305 | Neural regulation of behaviour and physiology |
| `n0376` | 0.304 | TGF-beta tumour suppression via SMAD and RUNX3 |
| `n0624` | 0.300 | Nucleotide and redox cofactor metabolism |
| `n0780` | 0.297 | GPCR-mediated aminergic neurotransmitter signaling |
| `n0379` | 0.297 | Regulation of small GTPase signalling |
| `n0649` | 0.296 | Regulation of vascular growth and matrix remodeling |
| `n0497` | 0.294 | Contractile phenotype and matrix remodeling in fibrosis |
| `n0368` | 0.293 | cAMP-dependent hormonal and nutrient signalling |
| `n0261` | 0.291 | Neutral lipid storage and phospholipid turnover |
| `n0428` | 0.286 | eIF2α-mediated stress translation control |
| `n0621` | 0.276 | Oncogenic kinase fusions and mutants driving cancer |
| `n0508` | 0.273 | **UNNAMEABLE** |
| `n0417` | 0.273 | Coronavirus-host interactions in infection and therapy |
| `n0335` | 0.272 | Tooth and bone mineralization regulation |
| `n0450` | 0.267 | Subunit assembly and editing of glutamate receptors and oligomeric proteins |
| `n0523` | 0.266 | Phosphate transport in mineralized tissue |
| `n0529` | 0.265 | Axon-glia adhesion and myelination |
| `n0623` | 0.259 | Proteasomal and ERAD protein degradation |
| `n0612` | 0.258 | Regulated proteolytic protein maturation |
| `n0543` | 0.258 | Membrane organization and biogenesis |
| `n0343` | 0.257 | Phosphatase regulation and inositol phosphate metabolism |
| `n0572` | 0.257 | Metal ion and xenobiotic homeostasis |
| `n0387` | 0.252 | Extracellular matrix and cytoskeletal structural integrity |
| `n0420` | 0.246 | Extracellular matrix and platelet-mediated hemostatic adhesion |
| `n0560` | 0.243 | Neuroendocrine regulation of growth and steroid hormones |
| `n0498` | 0.239 | Endocrine control of somatic growth |
| `n0400` | 0.239 | Redox and selenium-dependent peroxide handling |
| `n0600` | 0.237 | Membrane protein sorting and surface antigen expression |
| `n0756` | 0.235 | Phagocyte oxidative and nitrosative signalling |
| `n0662` | 0.231 | Steroid hormone response and reproductive tissue programming |
| `n0573` | 0.226 | Organ-specific embryonic morphogenesis |
| `n0532` | 0.226 | GTPase cycle regulation and effector signalling |
| `n0755` | 0.218 | Neurotrophin-driven neuronal growth and survival signalling |
| `n0694` | 0.210 | Neuroendocrine control of growth and appetite |
| `n0790` | 0.204 | Growth hormone, IGF and HPA axis signalling |
| `n0601` | 0.187 | Regulation of intracellular protein trafficking |
| `n0518` | 0.180 | **UNNAMEABLE** |
| `n0640` | 0.160 | **UNNAMEABLE** |

---

## Level 1 — 215 nodes

*Each shows its child clusters and its direct pathways: the two things its prompt contained.*

### `n0010` — Base excision repair

cohesion 0.673 · 1 children · 3 direct pathways · checks failed: `copies_member`

**Child clusters:**

- Base excision repair glycosylase step

**Direct pathways:**

- base-excision repair
- depyrimidination
- Base Excision Repair

### `n0017` — DNA replication initiation and elongation

cohesion 0.637 · 1 children · 3 direct pathways

**Child clusters:**

- DNA replication and licensing

**Direct pathways:**

- DNA replication initiation
- cell cycle DNA replication initiation
- DNA strand elongation

### `n0016` — Lipoprotein lipase-mediated triglyceride lipolysis

cohesion 0.601 · 1 children · 3 direct pathways

**Child clusters:**

- Triglyceride-rich lipoprotein remodeling and clearance

**Direct pathways:**

- regulation of very-low-density lipoprotein particle remodeling
- triglyceride-rich lipoprotein particle remodeling
- Assembly of active LPL and LIPC lipase complexes

### `n0060` — Drug-resistant receptor tyrosine kinase mutants

cohesion 0.589 · 1 children · 3 direct pathways

**Child clusters:**

- Drug-resistant FLT3 kinase mutants

**Direct pathways:**

- Sunitinib-resistant KIT mutants
- Sunitinib-resistant PDGFR mutants
- Drug resistance of ALK mutants

### `n0013` — Cell cycle progression and control

cohesion 0.578 · 1 children · 4 direct pathways

**Child clusters:**

- Cell cycle progression and division

**Direct pathways:**

- mitotic cell cycle
- cell cycle
- regulation of mitotic cell cycle
- HALLMARK_G2M_CHECKPOINT

### `n0040` — Cardiac action potential generation and conduction

cohesion 0.546 · 1 children · 3 direct pathways

**Child clusters:**

- Cardiac conduction system electrical propagation

**Direct pathways:**

- cardiac conduction
- regulation of cardiac muscle cell action potential involved in regulation of contraction
- Cardiac conduction

### `n0500` — Urinary tract and kidney development

cohesion 0.544 · 1 children · 3 direct pathways

**Child clusters:**

- Nephron and kidney morphogenesis

**Direct pathways:**

- nephric duct formation
- ureter development
- obsolete cell differentiation involved in metanephros development

### `n0293` — Nephron segment development and patterning

cohesion 0.527 · 1 children · 4 direct pathways

**Child clusters:**

- Metanephric tubule and collecting duct development

**Direct pathways:**

- distal tubule development
- distal convoluted tubule development
- metanephric nephron epithelium development
- regulation of glomerulus development

### `n0085` — Heart morphogenesis and chamber development

cohesion 0.526 · 1 children · 5 direct pathways

**Child clusters:**

- Cardiac septation and outflow tract morphogenesis

**Direct pathways:**

- heart morphogenesis
- pulmonary valve morphogenesis
- cardiac chamber morphogenesis
- atrial cardiac muscle tissue development
- heart development

### `n0282` — Excitatory synapse assembly and signaling

cohesion 0.523 · 1 children · 4 direct pathways

**Child clusters:**

- Postsynaptic density and synapse assembly

**Direct pathways:**

- synaptic transmission, glutamatergic
- NMDA glutamate receptor clustering
- regulation of trans-synaptic signaling
- Synaptic adhesion-like molecules

### `n0467` — Neuronal outgrowth and guidance

cohesion 0.523 · 1 children · 3 direct pathways

**Child clusters:**

- Axon and dendrite outgrowth regulation

**Direct pathways:**

- cell morphogenesis
- negative regulation of cell projection organization
- Axon guidance

### `n0081` — Purine and pyrimidine salvage metabolism

cohesion 0.515 · 2 children · 1 direct pathways

**Child clusters:**

- Nucleoside and nucleotide salvage
- Purine and pyrimidine nucleoside salvage and catabolism

**Direct pathways:**

- Defective APRT disrupts adenine salvage

### `n0009` — Monoamine neurotransmitter degradation

cohesion 0.501 · 1 children · 5 direct pathways

**Child clusters:**

- Catecholamine and phenolic amine catabolism

**Direct pathways:**

- serotonin metabolic process
- Neurotransmitter clearance
- Biogenic amines are oxidatively deaminated to aldehydes by MAOA and MAOB
- Enzymatic degradation of Dopamine by monoamine oxidase
- Metabolism of serotonin

### `n0707` — Calcium regulation of sarcomeric contraction

cohesion 0.498 · 1 children · 3 direct pathways

**Child clusters:**

- Excitation-contraction coupling in muscle

**Direct pathways:**

- actin-myosin filament sliding
- sarcoplasmic reticulum calcium ion transport
- regulation of calcium ion import into sarcoplasmic reticulum

### `n0071` — Xenobiotic biotransformation and drug disposition

cohesion 0.493 · 1 children · 3 direct pathways

**Child clusters:**

- Drug metabolism and disposition

**Direct pathways:**

- HALLMARK_XENOBIOTIC_METABOLISM
- FMO oxidises nucleophiles
- Ciprofloxacin ADME

### `n0398` — Intestinal cholesterol and lipid absorption

cohesion 0.493 · 1 children · 4 direct pathways

**Child clusters:**

- Lipoprotein particle assembly and transport

**Direct pathways:**

- regulation of intestinal cholesterol absorption
- intestinal lipid absorption
- regulation of intestinal absorption
- Intestinal lipid absorption

### `n0092` — DNA synthesis in replication and repair

cohesion 0.492 · 1 children · 3 direct pathways

**Child clusters:**

- Translesion DNA synthesis and its termination

**Direct pathways:**

- DNA synthesis involved in DNA repair
- DNA replication initiation
- Removal of the Flap Intermediate

### `n0652` — Muscle contractile function and control

cohesion 0.490 · 1 children · 4 direct pathways

**Child clusters:**

- Smooth muscle contraction regulation

**Direct pathways:**

- muscle system process
- muscle contraction
- regulation of muscle contraction
- striated muscle contraction

### `n0405` — Purine nucleoside and nucleotide salvage

cohesion 0.489 · 2 children · 2 direct pathways

**Child clusters:**

- Nucleotide pool sanitation and catabolism
- Deoxyribonucleotide synthesis and catabolism

**Direct pathways:**

- purine ribonucleoside catabolic process
- Defective APRT disrupts adenine salvage

### `n0468` — Mitotic spindle assembly and chromosome segregation

cohesion 0.489 · 1 children · 3 direct pathways

**Child clusters:**

- Kinetochore-driven mitotic chromosome segregation control

**Direct pathways:**

- mitotic sister chromatid separation
- HALLMARK_MITOTIC_SPINDLE
- EML4 and NUDC in mitotic spindle formation

### `n0642` — Cardiac valve development

cohesion 0.486 · 1 children · 3 direct pathways

**Child clusters:**

- Cardiac septation and outflow tract morphogenesis

**Direct pathways:**

- mitral valve development
- pulmonary valve morphogenesis
- atrioventricular valve formation

### `n0777` — Chromosome cohesion and stability maintenance

cohesion 0.485 · 2 children · 0 direct pathways

**Child clusters:**

- Sister chromatid cohesion maintenance
- Recombination-based telomere and genome maintenance

### `n0549` — Acetyl-CoA and ketone body metabolism

cohesion 0.483 · 1 children · 3 direct pathways

**Child clusters:**

- Fatty acid oxidation and ketone body metabolism

**Direct pathways:**

- acetyl-CoA metabolic process
- oxaloacetate metabolic process
- regulation of ketone metabolic process

### `n0045` — Glycogen metabolism and its disorders

cohesion 0.482 · 1 children · 3 direct pathways

**Child clusters:**

- Inherited disorders of carbohydrate metabolism

**Direct pathways:**

- energy reserve metabolic process
- glucan metabolic process
- Glycogen breakdown (glycogenolysis)

### `n0708` — Mismatch repair and double-strand break repair

cohesion 0.479 · 1 children · 4 direct pathways

**Child clusters:**

- Homologous recombination repair of DNA double-strand breaks

**Direct pathways:**

- mismatch repair
- Mismatch Repair
- Defective Mismatch Repair Associated With MSH2
- Defective DNA double strand break response due to BRCA1 loss of function

### `n0046` — Angiotensin-mediated blood pressure regulation

cohesion 0.479 · 1 children · 3 direct pathways

**Child clusters:**

- Renin-angiotensin regulation of blood pressure and volume

**Direct pathways:**

- negative regulation of systemic arterial blood pressure
- angiotensin-activated signaling pathway
- cellular response to angiotensin

### `n0752` — Lipoprotein particle biology

cohesion 0.475 · 2 children · 0 direct pathways

**Child clusters:**

- Lipoprotein particle metabolism and transport
- Lipoprotein particle assembly and transport

### `n0039` — Blood coagulation cascade and its defects

cohesion 0.475 · 1 children · 4 direct pathways

**Child clusters:**

- Defective coagulation factor variants causing bleeding disorders

**Direct pathways:**

- HALLMARK_COAGULATION
- Defects of Coagulation cascade
- Initiation of coagulation cascade
- Amplification and propagation of coagulation cascade

### `n0544` — Leukocyte chemotaxis and migration regulation

cohesion 0.475 · 1 children · 3 direct pathways

**Child clusters:**

- Lymphocyte migration and chemotaxis regulation

**Direct pathways:**

- positive regulation of leukocyte chemotaxis
- leukocyte migration
- positive regulation of mononuclear cell migration

### `n0325` — BCL-2 family regulation of mitochondrial apoptosis

cohesion 0.469 · 1 children · 3 direct pathways

**Child clusters:**

- Intrinsic mitochondrial apoptotic signaling

**Direct pathways:**

- negative regulation of execution phase of apoptosis
- BH3-only proteins associate with and inactivate anti-apoptotic BCL-2 members
- Activation, translocation and oligomerization of BAX

### `n0506` — DNA damage response and repair

cohesion 0.465 · 2 children · 1 direct pathways

**Child clusters:**

- Nucleotide excision repair
- DNA damage repair pathways

**Direct pathways:**

- response to UV-C

### `n0507` — Gastrulation and germ layer patterning

cohesion 0.464 · 1 children · 5 direct pathways

**Child clusters:**

- Signalling control of mesodermal fate commitment

**Direct pathways:**

- gastrulation
- anterior/posterior axis specification
- Epithelial-Mesenchymal Transition (EMT) during gastrulation
- Gastrulation
- Formation of axial mesoderm

### `n0453` — Mitochondrial and nuclear gene expression

cohesion 0.460 · 1 children · 3 direct pathways

**Child clusters:**

- Translation

**Direct pathways:**

- transcription elongation, RNA polymerase II
- Mitochondrial transcription termination
- Transcription from mitochondrial promoters

### `n0014` — Complement activation and humoral defence

cohesion 0.459 · 1 children · 3 direct pathways

**Child clusters:**

- Complement cascade activation and regulation

**Direct pathways:**

- positive regulation of humoral immune response
- regulation of opsonization
- Lectin pathway of complement activation

### `n0715` — Coagulation cascade and haemostasis

cohesion 0.452 · 1 children · 4 direct pathways

**Child clusters:**

- Hemostasis and thrombin/PAR signalling

**Direct pathways:**

- HALLMARK_COAGULATION
- Defects of Coagulation cascade
- Initiation of coagulation cascade
- Amplification and propagation of coagulation cascade

### `n0522` — Chromosome end replication and maintenance

cohesion 0.450 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of telomere maintenance

**Direct pathways:**

- telomere maintenance via recombination
- DNA strand elongation
- positive regulation of chromosome organization

### `n0070` — TGF-beta/BMP-SMAD signalling

cohesion 0.448 · 1 children · 3 direct pathways

**Child clusters:**

- TGF-beta/BMP-SMAD signalling regulation

**Direct pathways:**

- positive regulation of SMAD protein signal transduction
- SMAD protein signal transduction
- HALLMARK_TGF_BETA_SIGNALING

### `n0044` — miRNA biogenesis and silencing

cohesion 0.448 · 1 children · 3 direct pathways

**Child clusters:**

- Small RNA-guided gene silencing

**Direct pathways:**

- pre-miRNA processing
- miRNA processing
- negative regulation of miRNA processing

### `n0789` — Excitation-contraction coupling in muscle

cohesion 0.445 · 1 children · 3 direct pathways · checks failed: `duplicate_name`

**Child clusters:**

- Calcium handling in muscle relaxation

**Direct pathways:**

- striated muscle contraction
- Muscle contraction
- Ion homeostasis

### `n0315` — Regulation of cholesterol and lipid biosynthesis

cohesion 0.445 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of lipid biosynthesis and fatty acid metabolism

**Direct pathways:**

- regulation of cholesterol biosynthetic process
- negative regulation of cholesterol biosynthetic process
- regulation of cholesterol metabolic process

### `n0372` — Digestion and intestinal nutrient uptake

cohesion 0.443 · 2 children · 0 direct pathways

**Child clusters:**

- Digestion and intestinal nutrient absorption
- Intestinal lipid and sterol absorption

### `n0195` — Regulation of mitochondrial respiration and ROS

cohesion 0.443 · 1 children · 3 direct pathways

**Child clusters:**

- Mitochondrial oxidative phosphorylation

**Direct pathways:**

- regulation of cellular respiration
- regulation of mitochondrial electron transport, NADH to ubiquinone
- negative regulation of reactive oxygen species metabolic process

### `n0581` — Chromatin protein targeting and organization control

cohesion 0.441 · 1 children · 3 direct pathways

**Child clusters:**

- Sister chromatid cohesion maintenance

**Direct pathways:**

- establishment of protein localization to chromatin
- regulation of chromatin organization
- SUMO is transferred from E1 to E2 (UBE2I, UBC9)

### `n0103` — Th17 and Th1 lineage differentiation control

cohesion 0.441 · 1 children · 5 direct pathways

**Child clusters:**

- CD4 T cell activation and lineage differentiation

**Direct pathways:**

- T-helper cell lineage commitment
- T-helper 1 type immune response
- T-helper 17 type immune response
- regulation of T-helper 17 cell differentiation
- regulation of T-helper 17 cell lineage commitment

### `n0615` — Protein glycosylation pathways and disorders

cohesion 0.438 · 1 children · 3 direct pathways · checks failed: `pathways`

**Child clusters:**

- Congenital disorders of protein glycosylation

**Direct pathways:**

- protein O-linked glycosylation
- glycoprotein biosynthetic process
- O-glycosylation of TSR domain-containing proteins

### `n0235` — Mitochondrial quality control by autophagy and fission

cohesion 0.437 · 1 children · 3 direct pathways

**Child clusters:**

- Mitophagy

**Direct pathways:**

- macroautophagy
- negative regulation of mitochondrial fission
- negative regulation of autophagy of mitochondrion

### `n0541` — Host-virus interactions in viral replication

cohesion 0.436 · 1 children · 3 direct pathways

**Child clusters:**

- Type I interferon antiviral effector response

**Direct pathways:**

- viral process
- viral genome replication
- regulation of viral genome replication

### `n0083` — Mesoderm formation and somite segmentation

cohesion 0.436 · 1 children · 3 direct pathways

**Child clusters:**

- Early embryonic axis and germ layer formation

**Direct pathways:**

- mesodermal cell fate commitment
- somitogenesis
- Somitogenesis

### `n0241` — Mitotic chromosome condensation and cohesion

cohesion 0.435 · 1 children · 5 direct pathways

**Child clusters:**

- Sister chromatid cohesion maintenance

**Direct pathways:**

- establishment of sister chromatid cohesion
- regulation of chromosome condensation
- establishment of protein localization to chromatin
- positive regulation of chromosome condensation
- Establishment of Sister Chromatid Cohesion

### `n0067` — Epithelial cell junctions and adhesion dynamics

cohesion 0.434 · 1 children · 3 direct pathways

**Child clusters:**

- Cell-cell junction assembly and organization

**Direct pathways:**

- cell cell adhesion
- HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION
- Cell junction organization

### `n0753` — mRNA 3' end formation and stability

cohesion 0.431 · 1 children · 3 direct pathways

**Child clusters:**

- Cytoplasmic mRNA turnover and 3'-end processing

**Direct pathways:**

- mRNA 3'-end processing
- SLBP independent Processing of Histone Pre-mRNAs
- SLBP Dependent Processing of Replication-Dependent Histone Pre-mRNAs

### `n0123` — Cytokine-JAK-STAT signaling

cohesion 0.429 · 1 children · 4 direct pathways

**Child clusters:**

- IL-6/gp130-JAK-STAT3 signaling

**Direct pathways:**

- cytokine-mediated signaling pathway
- regulation of receptor signaling pathway via JAK-STAT
- cell surface receptor signaling pathway via STAT
- Cytokine Signaling in Immune system

### `n0493` — TRIF-dependent TLR signalling to type I interferon

cohesion 0.428 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of type I interferon production and signaling

**Direct pathways:**

- toll-like receptor 3 signaling pathway
- TICAM1-dependent activation of IRF3/IRF7
- Activation of IRF3, IRF7 mediated by TBK1, IKKε (IKBKE)

### `n0124` — Nucleotide-sugar biosynthesis for glycosylation

cohesion 0.426 · 1 children · 4 direct pathways

**Child clusters:**

- Amino sugar and carbohydrate catabolism

**Direct pathways:**

- UDP-N-acetylglucosamine biosynthetic process
- nucleotide-sugar metabolic process
- GDP-mannose metabolic process
- GDP-fucose biosynthesis

### `n0377` — Potassium-driven membrane repolarization

cohesion 0.424 · 1 children · 3 direct pathways

**Child clusters:**

- Cardiac action potential repolarization

**Direct pathways:**

- positive regulation of potassium ion transport
- membrane hyperpolarization
- Phase 1 - inactivation of fast Na+ channels

### `n0463` — Cytosolic nucleic acid sensing and inflammasome activation

cohesion 0.424 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of type I interferon production and signaling

**Direct pathways:**

- cytoplasmic pattern recognition receptor signaling pathway
- positive regulation of interleukin-18 production
- regulation of AIM2 inflammasome complex assembly

### `n0717` — CD4 T cell activation and proliferation control

cohesion 0.423 · 1 children · 3 direct pathways

**Child clusters:**

- CD4 T cell activation and lineage differentiation

**Direct pathways:**

- CD4-positive, alpha-beta T cell activation
- positive regulation of T cell proliferation
- positive regulation of cell activation

### `n0374` — Dendritic spine and arbor structural plasticity

cohesion 0.423 · 1 children · 3 direct pathways

**Child clusters:**

- Glutamate-driven excitatory synaptic plasticity

**Direct pathways:**

- regulation of dendrite morphogenesis
- positive regulation of dendritic spine development
- postsynaptic actin cytoskeleton organization

### `n0692` — Protein synthesis and processing

cohesion 0.422 · 1 children · 3 direct pathways

**Child clusters:**

- Translation

**Direct pathways:**

- mitochondrial ribosome assembly
- Metabolism of proteins
- rRNA processing in the mitochondrion

### `n0365` — Glucose-regulated insulin secretion

cohesion 0.421 · 1 children · 4 direct pathways

**Child clusters:**

- Insulin secretion regulation

**Direct pathways:**

- carbohydrate homeostasis
- protein localization to extracellular region
- export from cell
- HALLMARK_PANCREAS_BETA_CELLS

### `n0571` — Innate recognition of microbial molecules and signalling

cohesion 0.420 · 1 children · 4 direct pathways

**Child clusters:**

- Innate sensing of bacterial molecules

**Direct pathways:**

- TLR and inflammatory signaling
- response to molecule of bacterial origin
- positive regulation of xenophagy
- Activation of IRF3, IRF7 mediated by TBK1, IKKε (IKBKE)

### `n0636` — Embryonic patterning and cell fate specification

cohesion 0.419 · 2 children · 1 direct pathways

**Child clusters:**

- Early embryonic axis and germ layer formation
- Embryonic axis and neural patterning

**Direct pathways:**

- cell fate determination

### `n0530` — Mitotic chromosome segregation and spindle control

cohesion 0.418 · 1 children · 3 direct pathways

**Child clusters:**

- Mitotic spindle assembly and positioning

**Direct pathways:**

- chromosome segregation
- cell division
- Regulation of PLK1 Activity at G2/M Transition

### `n0181` — Platelet activation and adhesion regulation

cohesion 0.415 · 1 children · 3 direct pathways

**Child clusters:**

- Hemostasis and thrombin/PAR signalling

**Direct pathways:**

- platelet degranulation
- negative regulation of platelet activation
- regulation of homotypic cell-cell adhesion

### `n0650` — Glycosaminoglycan and proteoglycan biosynthesis disorders

cohesion 0.415 · 1 children · 5 direct pathways

**Child clusters:**

- Congenital disorders of protein glycosylation

**Direct pathways:**

- chondroitin sulfate proteoglycan metabolic process
- DS-GAG biosynthesis
- Diseases associated with glycosaminoglycan metabolism
- Defective CHSY1 causes TPBS
- O-glycosylation of TSR domain-containing proteins

### `n0558` — Nucleotide metabolism and pharmacogenetics

cohesion 0.413 · 2 children · 0 direct pathways

**Child clusters:**

- Nucleotide pool sanitation and catabolism
- Nucleotide catabolism and methylation pharmacogenetics

### `n0008` — Regulation of ER stress and UPR signalling

cohesion 0.411 · 2 children · 0 direct pathways

**Child clusters:**

- Regulation of IRE1/PERK UPR signalling
- Regulation of the unfolded protein response

### `n0273` — NEIL3-associated DNA lesion repair

cohesion 0.410 · 1 children · 3 direct pathways · checks failed: `associated`

**Child clusters:**

- DNA damage repair pathways

**Direct pathways:**

- single strand break repair
- Defective Base Excision Repair Associated with NEIL3
- NEIL3-mediated resolution of ICLs

### `n0164` — Glucose homeostasis and insulin secretion

cohesion 0.410 · 1 children · 5 direct pathways

**Child clusters:**

- Insulin secretion regulation

**Direct pathways:**

- carbohydrate homeostasis
- HALLMARK_PANCREAS_BETA_CELLS
- Glucagon-like Peptide-1 (GLP1) regulates insulin secretion
- Incretin synthesis, secretion, and inactivation
- Defective ABCC8 can cause hypo- and hyper-glycemias

### `n0660` — Type I interferon signaling and its regulation

cohesion 0.409 · 1 children · 3 direct pathways

**Child clusters:**

- Type I interferon antiviral effector response

**Direct pathways:**

- cellular response to interferon-beta
- regulation of type I interferon-mediated signaling pathway
- Regulation of IFNA/IFNB signaling

### `n0487` — Innate sensing and control of intracellular bacteria

cohesion 0.409 · 1 children · 5 direct pathways

**Child clusters:**

- Innate sensing of bacterial molecules

**Direct pathways:**

- positive regulation of antigen processing and presentation
- positive regulation of dendritic cell antigen processing and presentation
- regulation of nucleotide-binding domain, leucine rich repeat containing receptor signaling pathway
- nucleotide-binding oligomerization domain containing 1 signaling pathway
- positive regulation of xenophagy

### `n0341` — Apoptosis signaling and execution

cohesion 0.409 · 1 children · 4 direct pathways

**Child clusters:**

- Death receptor-induced caspase-8 activation

**Direct pathways:**

- apoptotic signaling pathway
- HALLMARK_APOPTOSIS
- Apoptosis
- Activation, translocation and oligomerization of BAX

### `n0361` — MHC-associated antigen presentation and immune evasion

cohesion 0.408 · 2 children · 0 direct pathways

**Child clusters:**

- MHC-restricted antigen processing and presentation
- Nef-mediated receptor downregulation

### `n0390` — Renal and cellular amino acid transport

cohesion 0.408 · 1 children · 3 direct pathways

**Child clusters:**

- Amino acid transmembrane transport

**Direct pathways:**

- amino acid metabolishm and transport
- Amino acid transport across the plasma membrane
- Defective amino acid transport by SLC7A9 causes cystinuria (CSNU)

### `n0661` — Mitochondrial dynamics and organization

cohesion 0.408 · 1 children · 3 direct pathways

**Child clusters:**

- Cristae architecture and MICOS complex

**Direct pathways:**

- mitochondrion organization
- positive regulation of mitochondrial fusion
- negative regulation of mitochondrial fission

### `n0042` — Fatty alcohol and ether lipid synthesis

cohesion 0.406 · 1 children · 3 direct pathways

**Child clusters:**

- Long-chain and very long-chain fatty acid metabolism

**Direct pathways:**

- ether biosynthetic process
- fatty acid derivative metabolic process
- Wax biosynthesis

### `n0719` — Death receptor apoptosis regulation

cohesion 0.406 · 1 children · 3 direct pathways

**Child clusters:**

- Death receptor-induced caspase-8 activation

**Direct pathways:**

- regulation of activation-induced cell death of T cells
- negative regulation of Fas signaling pathway
- HALLMARK_APOPTOSIS

### `n0354` — Amino acid transport

cohesion 0.406 · 1 children · 3 direct pathways

**Child clusters:**

- Amino acid transmembrane transport

**Direct pathways:**

- isoleucine transport
- phenylalanine transport
- Amino acid transport across the plasma membrane

### `n0302` — Negative regulation of myogenesis and regeneration

cohesion 0.406 · 1 children · 4 direct pathways

**Child clusters:**

- Muscle cell proliferation and differentiation

**Direct pathways:**

- negative regulation of myotube differentiation
- regeneration
- negative regulation of myoblast differentiation
- negative regulation of muscle organ development

### `n0244` — Synaptic vesicle recycling and endocytosis

cohesion 0.405 · 1 children · 3 direct pathways

**Child clusters:**

- Membrane trafficking dynamics

**Direct pathways:**

- synaptic vesicle recycling
- synaptic vesicle recycling via endosome
- presynaptic endocytosis

### `n0062` — RSV and influenza replication and virion assembly

cohesion 0.404 · 1 children · 4 direct pathways

**Child clusters:**

- Host-directed viral mRNA translation and transcription

**Direct pathways:**

- Virus Assembly and Release
- NEP/NS2 Interacts with the Cellular Export Machinery
- Assembly and release of respiratory syncytial virus (RSV) virions
- Respiratory syncytial virus (RSV) genome replication, transcription and translation

### `n0495` — Galactose and pentose metabolism disorders

cohesion 0.403 · 1 children · 4 direct pathways

**Child clusters:**

- Amino sugar and carbohydrate catabolism

**Direct pathways:**

- galactose metabolic process
- glycoside metabolic process
- Essential pentosuria
- Defective GALM causes GALAC4

### `n0065` — Centrosome and spindle positioning

cohesion 0.403 · 1 children · 4 direct pathways

**Child clusters:**

- Mitotic spindle assembly and positioning

**Direct pathways:**

- protein localization to cytoskeleton
- microtubule organizing center localization
- regulation of centriole elongation
- regulation of protein localization to cell cortex

### `n0234` — Regulation of neurotransmitter and glutamate release

cohesion 0.403 · 1 children · 4 direct pathways

**Child clusters:**

- Synaptic vesicle cycle and neurotransmitter release

**Direct pathways:**

- positive regulation of glutamate secretion
- negative regulation of neurotransmitter secretion
- negative regulation of neurotransmitter transport
- regulation of glutamate secretion, neurotransmission

### `n0627` — Glycosaminoglycan biosynthesis and disorders

cohesion 0.401 · 1 children · 3 direct pathways

**Child clusters:**

- Protein glycosylation and proteoglycan biosynthesis

**Direct pathways:**

- DS-GAG biosynthesis
- Diseases associated with glycosaminoglycan metabolism
- Defective CHSY1 causes TPBS

### `n0732` — Vesicular trafficking to the vacuole and lysosome

cohesion 0.401 · 1 children · 4 direct pathways

**Child clusters:**

- Intracellular vesicle transport

**Direct pathways:**

- Golgi to vacuole transport
- vesicle organization
- organelle fusion
- establishment of protein localization to vacuole

### `n0276` — Postsynaptic structural and receptor plasticity

cohesion 0.400 · 1 children · 3 direct pathways

**Child clusters:**

- Glutamate-driven excitatory synaptic plasticity

**Direct pathways:**

- maintenance of postsynaptic specialization structure
- postsynaptic actin cytoskeleton organization
- regulation of receptor localization to synapse

### `n0567` — Dietary nutrient digestion and sugar transport

cohesion 0.398 · 2 children · 0 direct pathways

**Child clusters:**

- Digestion and intestinal nutrient absorption
- Hexose transport and its regulation

### `n0447` — MHC-restricted antigen presentation

cohesion 0.396 · 2 children · 0 direct pathways

**Child clusters:**

- MHC-restricted antigen processing and presentation
- MHC-restricted antigen presentation to T cells

### `n0357` — Regulation of immune cell activation

cohesion 0.396 · 1 children · 3 direct pathways

**Child clusters:**

- T cell receptor signalling and activation

**Direct pathways:**

- gamma-delta T cell activation
- regulation of cell activation
- positive regulation of cell activation

### `n0758` — Cadherin junction dynamics and EMT

cohesion 0.396 · 1 children · 4 direct pathways

**Child clusters:**

- Cell-cell junction assembly and organization

**Direct pathways:**

- adherens junction organization
- regulation of cell-cell adhesion mediated by cadherin
- negative regulation of cell-cell adhesion mediated by cadherin
- HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION

### `n0011` — Redox stress and ferroptosis regulation

cohesion 0.396 · 1 children · 3 direct pathways

**Child clusters:**

- Oxidative stress response and antioxidant defence

**Direct pathways:**

- cellular response to chemical stress
- ferroptosis
- negative regulation of ferroptosis

### `n0409` — Chemokine-driven leukocyte chemotaxis

cohesion 0.396 · 1 children · 4 direct pathways

**Child clusters:**

- CCR7-driven dendritic cell trafficking and survival

**Direct pathways:**

- chemokine cluster (II)
- positive regulation of leukocyte chemotaxis
- positive regulation of mononuclear cell migration
- Chemokine receptors bind chemokines

### `n0439` — Regulation of myeloid cytokine production

cohesion 0.394 · 1 children · 3 direct pathways

**Child clusters:**

- Toll-like receptor and macrophage activation signalling

**Direct pathways:**

- macrophage cytokine production
- positive regulation of macrophage cytokine production
- myeloid leukocyte cytokine production

### `n0788` — Regulation of lipid and lipoprotein receptor homeostasis

cohesion 0.393 · 1 children · 3 direct pathways

**Child clusters:**

- Cellular cholesterol and lipoprotein sensing in foam cell formation

**Direct pathways:**

- positive regulation of lipid metabolic process
- VLDLR internalisation and degradation
- NR1H2 & NR1H3 regulate gene expression to limit cholesterol uptake

### `n0362` — Cytokine-driven acute inflammatory amplification

cohesion 0.390 · 1 children · 3 direct pathways

**Child clusters:**

- IL-1-driven inflammatory response

**Direct pathways:**

- positive regulation of response to external stimulus
- positive regulation of interleukin-1 alpha production
- positive regulation of chemokine (C-X-C motif) ligand 1 production

### `n0515` — Cell motility and projection dynamics

cohesion 0.390 · 1 children · 3 direct pathways

**Child clusters:**

- Axon guidance signalling and morphogenesis

**Direct pathways:**

- regulation of neuron projection development
- locomotion
- regulation of cell projection assembly

### `n0084` — Lipoylation and branched-chain ketoacid dehydrogenase disorders

cohesion 0.389 · 1 children · 5 direct pathways

**Child clusters:**

- Mitochondrial amino acid and nucleobase catabolism disorders

**Direct pathways:**

- protein lipoylation
- Protein lipoylation
- Loss-of-function mutations in DBT cause MSUD2
- Maple Syrup Urine Disease
- Loss-of-function mutations in DLD cause MSUD3/DLDD

### `n0292` — MYC-driven ribosome biogenesis and rRNA synthesis

cohesion 0.388 · 1 children · 4 direct pathways

**Child clusters:**

- Nucleolar rRNA processing and ribosome subunit maturation

**Direct pathways:**

- transcription elongation by RNA polymerase I
- 5S class rRNA transcription by RNA polymerase III
- HALLMARK_MYC_TARGETS_V1
- HALLMARK_MYC_TARGETS_V2

### `n0216` — Cytoskeletal transport of organelles and cargo

cohesion 0.387 · 2 children · 1 direct pathways

**Child clusters:**

- Cytoskeletal transport of organelles and vesicles
- Cytoskeletal transport of organelles

**Direct pathways:**

- anterograde dendritic transport of neurotransmitter receptor complex

### `n0342` — Dendrite and spine morphogenesis

cohesion 0.385 · 1 children · 4 direct pathways

**Child clusters:**

- Regulation of neuronal cytoskeletal growth

**Direct pathways:**

- regulation of dendrite morphogenesis
- positive regulation of dendritic spine development
- postsynaptic actin cytoskeleton organization
- regulation of dendrite extension

### `n0413` — Neural tube regional patterning

cohesion 0.385 · 2 children · 1 direct pathways

**Child clusters:**

- Regional patterning of the neural tube
- Regional CNS neuron specification and patterning

**Direct pathways:**

- neural plate pattern specification

### `n0449` — 3'-UTR and miRNA stability control

cohesion 0.385 · 1 children · 3 direct pathways

**Child clusters:**

- Cytoplasmic mRNA turnover and 3'-end processing

**Direct pathways:**

- regulation of 3'-UTR-mediated mRNA stabilization
- positive regulation of 3'-UTR-mediated mRNA stabilization
- regulation of miRNA catabolic process

### `n0385` — Non-coding RNA processing and modification

cohesion 0.385 · 2 children · 0 direct pathways

**Child clusters:**

- Non-coding RNA modification and maturation
- tRNA maturation and modification

### `n0485` — Innate immune inflammatory signalling

cohesion 0.385 · 1 children · 4 direct pathways

**Child clusters:**

- IL-1-driven inflammatory response

**Direct pathways:**

- Toll signaling pathway
- positive regulation of response to external stimulus
- Toll Like Receptor 4 (TLR4) Cascade
- Interleukin-37 signaling

### `n0206` — Transition metal ion homeostasis and detoxification

cohesion 0.384 · 1 children · 3 direct pathways

**Child clusters:**

- Copper ion homeostasis and detoxification

**Direct pathways:**

- manganese ion transport
- cellular response to manganese ion
- detoxification of cadmium ion

### `n0798` — tRNA modification for translational fidelity

cohesion 0.383 · 1 children · 3 direct pathways

**Child clusters:**

- tRNA maturation and modification

**Direct pathways:**

- tRNA threonylcarbamoyladenosine modification
- obsolete tRNA threonylcarbamoyladenosine metabolic process
- Synthesis of diphthamide-EEF2

### `n0474` — Keratinocyte-driven epidermal wound re-epithelialisation

cohesion 0.382 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of cell-matrix adhesion turnover

**Direct pathways:**

- wound healing, spreading of epidermal cells
- keratinocyte migration
- regulation of wound healing, spreading of epidermal cells

### `n0086` — Steroid hormone receptor transcriptional response

cohesion 0.380 · 1 children · 3 direct pathways

**Child clusters:**

- Steroid hormone receptor transcriptional regulation

**Direct pathways:**

- HALLMARK_ANDROGEN_RESPONSE
- HALLMARK_ESTROGEN_RESPONSE_EARLY
- HALLMARK_ESTROGEN_RESPONSE_LATE

### `n0528` — Vitamin and cofactor metabolism

cohesion 0.377 · 1 children · 3 direct pathways

**Child clusters:**

- Retinoid metabolism and signaling

**Direct pathways:**

- fatty acid alpha-oxidation
- riboflavin transport
- Vitamin E transport

### `n0375` — Glycan biosynthesis and catabolism

cohesion 0.377 · 1 children · 3 direct pathways

**Child clusters:**

- Amino sugar and carbohydrate catabolism

**Direct pathways:**

- lysosome
- Sialic acid metabolism
- N-glycan antennae elongation in the medial/trans-Golgi

### `n0104` — Cytoplasmic translation initiation and regulation

cohesion 0.377 · 1 children · 4 direct pathways

**Child clusters:**

- Regulation of cytoplasmic translation

**Direct pathways:**

- formation of cytoplasmic translation initiation complex
- cytoplasmic translational initiation
- Formation of the ternary complex, and subsequently, the 43S complex
- GTP hydrolysis and joining of the 60S ribosomal subunit

### `n0425` — Neural tube formation and patterning

cohesion 0.375 · 1 children · 3 direct pathways

**Child clusters:**

- Regional patterning of the neural tube

**Direct pathways:**

- neural tube formation
- embryonic neurocranium morphogenesis
- neural plate pattern specification

### `n0524` — rRNA and mRNA processing by exonucleases and snoRNPs

cohesion 0.375 · 1 children · 3 direct pathways

**Child clusters:**

- Non-coding RNA modification and maturation

**Direct pathways:**

- rRNA processing
- mRNA decay by 3' to 5' exoribonuclease
- rRNA processing

### `n0458` — Smooth muscle contractile-synthetic phenotype control

cohesion 0.373 · 1 children · 3 direct pathways

**Child clusters:**

- Smooth muscle cell phenotype regulation

**Direct pathways:**

- muscle contraction, SRF targets
- cytoskeletal remodeling (enriched for SRF targets)
- smooth muscle adaptation

### `n0787` — Presynaptic and dendritic activity regulation

cohesion 0.373 · 1 children · 5 direct pathways

**Child clusters:**

- Synaptic vesicle cycle and neurotransmitter release

**Direct pathways:**

- negative regulation of neurotransmitter secretion
- negative regulation of neurotransmitter transport
- negative regulation of excitatory postsynaptic potential
- regulation of dendrite extension
- Defective SLC9A9 causes autism 16 (AUTS16)

### `n0262` — Vacuole and lysosome trafficking

cohesion 0.373 · 1 children · 5 direct pathways

**Child clusters:**

- Intracellular vesicle transport

**Direct pathways:**

- post-Golgi vesicle-mediated transport
- Golgi to vacuole transport
- establishment of protein localization to vacuole
- lytic vacuole organization
- vacuolar localization

### `n0197` — Regulation of MAPK/JNK cascades

cohesion 0.371 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of protein kinase activity

**Direct pathways:**

- regulation of MAP kinase activity
- positive regulation of MAPK cascade
- positive regulation of JNK cascade

### `n0366` — Osmotic and glycerol transport homeostasis

cohesion 0.370 · 1 children · 3 direct pathways

**Child clusters:**

- Water balance and aquaporin function

**Direct pathways:**

- polyol transmembrane transport
- glycerol transmembrane transport
- response to hydrostatic pressure

### `n0037` — Photoreceptor cilium biology and vision

cohesion 0.369 · 2 children · 1 direct pathways

**Child clusters:**

- Photoreceptor development and maintenance
- Phototransduction in vision

**Direct pathways:**

- regulation of protein localization to cilium

### `n0346` — mRNA transcription, splicing and 3' processing

cohesion 0.367 · 2 children · 1 direct pathways

**Child clusters:**

- RNA polymerase II transcription initiation and elongation, including HIV Tat-dependent control
- mRNA 3' end maturation and decay

**Direct pathways:**

- U2-type prespliceosome assembly

### `n0749` — Nucleotide sugar and glycan precursor metabolism

cohesion 0.366 · 1 children · 7 direct pathways

**Child clusters:**

- Dolichol-linked glycosylation precursor synthesis

**Direct pathways:**

- UDP-N-acetylglucosamine biosynthetic process
- GPI anchor metabolic process
- nucleotide-sugar metabolic process
- N-acetylneuraminate catabolic process
- GDP-mannose metabolic process
- amino sugar catabolic process
- GDP-fucose biosynthesis

### `n0776` — snRNA and rRNA modification and snoRNP assembly

cohesion 0.363 · 1 children · 3 direct pathways

**Child clusters:**

- rRNA and mRNA processing machinery

**Direct pathways:**

- small nucleolar ribonucleoprotein complex assembly
- snRNA modification
- rRNA modification in the nucleus and cytosol

### `n0180` — Endothelial mechanical and adhesive signaling

cohesion 0.361 · 2 children · 0 direct pathways

**Child clusters:**

- Regulation of leukocyte-endothelial adhesion
- Endothelial shear stress mechanotransduction

### `n0294` — Rho-family GTPase cycles and effectors

cohesion 0.360 · 1 children · 3 direct pathways

**Child clusters:**

- Rho family GTPase cycle

**Direct pathways:**

- RHO GTPases Activate Rhotekin and Rhophilins
- CDC42 GTPase cycle
- RHOU GTPase cycle

### `n0778` — Platelet activation and adhesion signalling

cohesion 0.358 · 1 children · 4 direct pathways

**Child clusters:**

- Hemostasis and thrombin/PAR signalling

**Direct pathways:**

- cell adhesion
- platelet degranulation
- Platelet degranulation
- Rap1 signalling

### `n0263` — Chromatin and epigenetic inheritance

cohesion 0.357 · 1 children · 3 direct pathways

**Child clusters:**

- Chromatin-based epigenetic regulation

**Direct pathways:**

- epigenetic programming in the zygotic pronuclei
- genomic imprinting
- Chromatin organization

### `n0283` — Insulin receptor signalling to glucose uptake

cohesion 0.356 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of insulin-driven glucose uptake and glycogen synthesis

**Direct pathways:**

- glucose import in response to insulin stimulus
- IRS activation
- Signal attenuation

### `n0593` — Meiotic cell division

cohesion 0.355 · 1 children · 3 direct pathways

**Child clusters:**

- Mitotic cell division

**Direct pathways:**

- spindle assembly involved in female meiosis
- meiotic cytokinesis
- centromeric sister chromatid cohesion

### `n0415` — Actin cytoskeleton dynamics in cell motility

cohesion 0.355 · 2 children · 1 direct pathways

**Child clusters:**

- Branched actin nucleation and lamellipodium formation
- Regulation of cell-matrix adhesion turnover

**Direct pathways:**

- regulation of actin filament organization

### `n0496` — Host-pathogen metal ion competition

cohesion 0.355 · 1 children · 3 direct pathways

**Child clusters:**

- Antimicrobial peptide-mediated humoral defence

**Direct pathways:**

- iron import into cell
- detoxification of cadmium ion
- Metal ion assimilation from the host

### `n0367` — Hematopoietic and lymphocyte lineage commitment

cohesion 0.352 · 1 children · 4 direct pathways

**Child clusters:**

- Homeostatic control of progenitor cell numbers

**Direct pathways:**

- hematopoietic progenitor cell differentiation
- leukocyte differentiation
- lymphocyte differentiation
- T cell differentiation

### `n0446` — Vesicle-mediated membrane trafficking

cohesion 0.352 · 2 children · 0 direct pathways

**Child clusters:**

- Intracellular vesicle transport
- Vesicular transport in the secretory and endocytic pathways

### `n0622` — Amyloid and tau-driven neurodegeneration in Alzheimer's disease

cohesion 0.352 · 1 children · 3 direct pathways · checks failed: `sentence_case`

**Child clusters:**

- Regulation of amyloid-beta production and clearance

**Direct pathways:**

- hippocampal neuron apoptotic process
- negative regulation of dendritic spine maintenance
- regulation of neurofibrillary tangle assembly

### `n0384` — Wnt/beta-catenin signal transduction

cohesion 0.350 · 1 children · 3 direct pathways

**Child clusters:**

- Beta-catenin destruction complex regulation

**Direct pathways:**

- Wnt signaling pathway
- Wnt signaling pathway
- Negative regulation of TCF-dependent signaling by DVL-interacting proteins

### `n0531` — Smooth muscle tone in reproductive function

cohesion 0.350 · 1 children · 3 direct pathways

**Child clusters:**

- Smooth muscle contraction regulation

**Direct pathways:**

- copulation
- penile erection
- negative regulation of relaxation of muscle

### `n0607` — mRNA 3' end processing and decay

cohesion 0.349 · 2 children · 0 direct pathways

**Child clusters:**

- mRNA 3' end maturation and decay
- *(refused)*

### `n0275` — Calcium-mediated signaling regulation

cohesion 0.348 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of calcium ion transmembrane transport

**Direct pathways:**

- regulation of calcium-mediated signaling
- positive regulation of calcium-mediated signaling
- calcineurin-mediated signaling

### `n0620` — Cilia-dependent left/right patterning of embryonic organs

cohesion 0.347 · 1 children · 3 direct pathways

**Child clusters:**

- Motile cilia biogenesis and beat regulation

**Direct pathways:**

- embryonic heart tube left/right pattern formation
- hindgut development
- determination of digestive tract left/right asymmetry

### `n0426` — NK cell receptor signalling and activation control

cohesion 0.347 · 1 children · 3 direct pathways

**Child clusters:**

- Immune checkpoint restraint of T cell responses

**Direct pathways:**

- enriched in NK cells (receptor activation)
- regulation of natural killer cell activation
- negative regulation of natural killer cell activation

### `n0295` — Nuclear export of RNA and protein

cohesion 0.345 · 1 children · 3 direct pathways

**Child clusters:**

- Nuclear export of RNA

**Direct pathways:**

- nuclear-transcribed mRNA catabolic process, nonsense-mediated decay
- mRNA export from nucleus
- protein export from nucleus

### `n0066` — Regulation of germ cell meiosis and gametogenesis

cohesion 0.344 · 1 children · 3 direct pathways

**Child clusters:**

- Meiosis in gametogenesis

**Direct pathways:**

- oocyte differentiation
- regulation of meiotic nuclear division
- negative regulation of reproductive process

### `n0402` — Myeloid phagocytosis and leukocyte effector immunity

cohesion 0.343 · 1 children · 3 direct pathways

**Child clusters:**

- Myeloid leukocyte degranulation and effector immunity

**Direct pathways:**

- complement and other receptors in DCs
- leukocyte mediated immunity
- phagocytosis

### `n0082` — TRAF-TAK1-IKK NF-kB signaling

cohesion 0.343 · 3 children · 0 direct pathways

**Child clusters:**

- TNF-driven NF-kappaB signaling
- TAK1/NIK-driven NF-kB and MAPK signalling
- NF-kappaB and JNK activation via TAK1/IKK signaling

### `n0797` — Mitochondrial cofactor and amino acid metabolism

cohesion 0.343 · 1 children · 4 direct pathways

**Child clusters:**

- Mitochondrial amino acid and nucleobase catabolism disorders

**Direct pathways:**

- protein lipoylation
- vitamin B6 metabolic process
- Serine metabolism
- Protein lipoylation

### `n0596` — Cytokinesis and cortical polarity signalling

cohesion 0.342 · 1 children · 3 direct pathways

**Child clusters:**

- Cortical polarity and centrosome positioning

**Direct pathways:**

- Rho GTPase cycle
- cytokinesis
- septin ring organization

### `n0475` — Humoral immunity regulation and germinal centre selection

cohesion 0.342 · 1 children · 3 direct pathways

**Child clusters:**

- B cell identity and receptor signalling

**Direct pathways:**

- negative regulation of B cell mediated immunity
- interleukin-21 production
- Affinity selection of immunoglobulins

### `n0718` — Lymphocyte development and adaptive immunity

cohesion 0.342 · 1 children · 4 direct pathways

**Child clusters:**

- B cell identity and receptor signalling

**Direct pathways:**

- T cell differentiation
- B cell development
- B cell proliferation involved in immune response
- adaptive immune memory response

### `n0688` — Endothelial specification and vascular morphogenesis

cohesion 0.341 · 1 children · 4 direct pathways

**Child clusters:**

- VEGF signalling in vascular and lymphatic development

**Direct pathways:**

- morphogenesis of an endothelium
- endothelial cell differentiation
- positive regulation of endothelial cell differentiation
- blood vessel endothelial cell differentiation

### `n0125` — ATG8-dependent membrane sequestration and endosomal sorting

cohesion 0.339 · 1 children · 4 direct pathways

**Child clusters:**

- Endomembrane trafficking and autophagy

**Direct pathways:**

- microautophagy
- piecemeal microautophagy of the nucleus
- multivesicular body sorting pathway
- Metalloprotease DUBs

### `n0706` — Muscle fibre membrane and size homeostasis

cohesion 0.339 · 1 children · 3 direct pathways

**Child clusters:**

- Sarcomere assembly and contraction

**Direct pathways:**

- negative regulation of cell size
- muscle cell cellular homeostasis
- caveolin-mediated endocytosis

### `n0594` — Cortical actin-based apical polarity and protrusions

cohesion 0.339 · 1 children · 4 direct pathways

**Child clusters:**

- Cortical polarity and centrosome positioning

**Direct pathways:**

- microvillus assembly
- septin ring organization
- regulation of microvillus assembly
- positive regulation of microvillus assembly

### `n0388` — Protein phosphorylation and kinase signal activation

cohesion 0.339 · 1 children · 3 direct pathways

**Child clusters:**

- Regulation of protein kinase activity

**Direct pathways:**

- peptidyl-threonine phosphorylation
- obsolete peptidyl-serine modification
- positive regulation of intracellular signal transduction

### `n0619` — Cortical and centrosomal protein targeting for polarity

cohesion 0.338 · 1 children · 4 direct pathways

**Child clusters:**

- Cortical polarity and centrosome positioning

**Direct pathways:**

- septin ring organization
- protein localization to cytoskeleton
- microtubule organizing center localization
- regulation of protein localization to cell cortex

### `n0271` — Mesenchymal adipocyte and osteoblast fate regulation

cohesion 0.338 · 1 children · 3 direct pathways

**Child clusters:**

- Adipogenesis and adipose lipid storage

**Direct pathways:**

- positive regulation of fat cell differentiation
- regulation of osteoblast differentiation
- negative regulation of adipose tissue development

### `n0218` — Insulin-family receptor tyrosine kinase signaling

cohesion 0.335 · 1 children · 4 direct pathways

**Child clusters:**

- PI3K/AKT activation downstream of growth factor receptors

**Direct pathways:**

- Signaling by ALK
- IRS activation
- Signal attenuation
- Signaling by LTK

### `n0651` — Actin-driven cell projections and motility

cohesion 0.335 · 1 children · 4 direct pathways

**Child clusters:**

- Branched actin nucleation and lamellipodium formation

**Direct pathways:**

- regulation of actin filament bundle assembly
- locomotion
- regulation of cell projection assembly
- regulation of actin filament organization

### `n0445` — Embryonic organogenesis and craniofacial-eye morphogenesis

cohesion 0.334 · 2 children · 2 direct pathways

**Child clusters:**

- Cranial nerve and pharyngeal organ morphogenesis
- Organogenesis and body patterning by Hox and craniofacial programs

**Direct pathways:**

- embryonic camera-type eye morphogenesis
- eyelid development in camera-type eye

### `n0591` — Senescence and telomere maintenance

cohesion 0.332 · 2 children · 0 direct pathways

**Child clusters:**

- Cellular senescence
- Regulation of telomere maintenance

### `n0250` — Glycosaminoglycan metabolism and connective tissue disease

cohesion 0.327 · 3 children · 0 direct pathways

**Child clusters:**

- Glycosaminoglycan sulfation and chondrodysplasia genetics
- Chondroitin/dermatan sulfate metabolism and disorders
- Glycosaminoglycan and sulfate handling in connective tissue disease

### `n0290` — B cell development and antibody responses

cohesion 0.321 · 2 children · 0 direct pathways

**Child clusters:**

- B cell development and antibody diversification
- B cell development and humoral immune regulation

### `n0418` — Hair follicle cycling and epidermal desquamation

cohesion 0.321 · 1 children · 3 direct pathways

**Child clusters:**

- Epidermal and appendage differentiation

**Direct pathways:**

- anagen
- biological phase
- delamination

### `n0714` — Amino acid metabolism and glycine conjugation

cohesion 0.321 · 1 children · 4 direct pathways

**Child clusters:**

- Amino acid catabolism to cofactors and mediators

**Direct pathways:**

- amino acid metabolic process
- obsolete organic acid biosynthetic process
- Conjugation of salicylate with glycine
- Conjugation of benzoate with glycine

### `n0486` — Wnt/beta-catenin signalling

cohesion 0.320 · 1 children · 3 direct pathways

**Child clusters:**

- Wnt and Hedgehog signalling regulation

**Direct pathways:**

- Wnt signaling pathway
- canonical Wnt signaling pathway
- HALLMARK_WNT_BETA_CATENIN_SIGNALING

### `n0488` — Sensory perception and stimulus detection

cohesion 0.319 · 1 children · 3 direct pathways

**Child clusters:**

- Sensory transduction by stimulus-gated ion channels

**Direct pathways:**

- sensory perception
- detection of stimulus
- Sensory Perception

### `n0427` — Chaperone-mediated protein folding and stress response

cohesion 0.314 · 1 children · 3 direct pathways

**Child clusters:**

- Selective autophagic clearance of protein aggregates

**Direct pathways:**

- protein folding
- response to heat
- protein refolding

### `n0193` — Taste sensory transduction

cohesion 0.312 · 1 children · 4 direct pathways

**Child clusters:**

- Sensory transduction by stimulus-gated ion channels

**Direct pathways:**

- sensory perception of taste
- sensory perception of sour taste
- Sensory perception of taste
- Sensory perception of sour taste

### `n0106` — RUNX and Notch control of myeloid differentiation

cohesion 0.312 · 1 children · 3 direct pathways · checks failed: `sentence_case`

**Child clusters:**

- Myeloid and leukocyte lineage commitment

**Direct pathways:**

- NOTCH2 intracellular domain regulates transcription
- RUNX1 regulates transcription of genes involved in differentiation of myeloid cells
- RUNX2 regulates genes involved in differentiation of myeloid cells

### `n0540` — Cadherin adhesion and TGFBR3 signalling regulation

cohesion 0.311 · 1 children · 4 direct pathways

**Child clusters:**

- Regulation of E-cadherin adhesion

**Direct pathways:**

- Regulation of Expression and Function of Type II Classical Cadherins
- Regulation of CDH1 mRNA translation by microRNAs
- Signaling by TGFBR3
- TGFBR3 expression

### `n0618` — Vitamin D metabolism and receptor signalling

cohesion 0.311 · 1 children · 4 direct pathways

**Child clusters:**

- Bile acid and sterol homeostasis

**Direct pathways:**

- fat-soluble vitamin catabolic process
- regulation of vitamin D receptor signaling pathway
- Defective CYP24A1 causes HCAI
- Defective CYP27B1 causes VDDR1B

### `n0440` — Skeletal development and osteoblast differentiation

cohesion 0.310 · 1 children · 3 direct pathways

**Child clusters:**

- Chondrocyte differentiation and endochondral ossification

**Direct pathways:**

- regulation of osteoblast differentiation
- cartilage morphogenesis
- Regulation of RUNX2 expression and activity

### `n0716` — Male reproductive endocrine differentiation

cohesion 0.309 · 1 children · 3 direct pathways

**Child clusters:**

- Gonadotropin control of ovarian and gonadal function

**Direct pathways:**

- androgen biosynthetic process
- positive regulation of activin receptor signaling pathway
- male sex differentiation

### `n0126` — GPCR signalling in lipid mediator and nucleotide sensing

cohesion 0.306 · 1 children · 5 direct pathways

**Child clusters:**

- Prostaglandin synthesis and signaling

**Direct pathways:**

- enriched in G-protein coupled receptors
- leukotriene biosynthetic process
- cellular response to prostaglandin E stimulus
- Nucleotide-like (purinergic) receptors
- G beta:gamma signalling through PLC beta

### `n0322` — p53-mediated damage and apoptosis response

cohesion 0.305 · 2 children · 0 direct pathways

**Child clusters:**

- TP53-mediated damage response and apoptosis
- p53-driven transcriptional and apoptotic response to damage

### `n0625` — Cytokine-driven innate immune activation

cohesion 0.303 · 1 children · 3 direct pathways

**Child clusters:**

- Cytokine signalling to epithelial barriers

**Direct pathways:**

- granulocyte macrophage colony-stimulating factor production
- interleukin-33-mediated signaling pathway
- Interleukin-33 signaling

### `n0416` — cAMP-linked GPCR signalling and secretion control

cohesion 0.303 · 1 children · 4 direct pathways

**Child clusters:**

- GPCR–cyclic nucleotide signalling via adenylate cyclase

**Direct pathways:**

- positive regulation of cyclase activity
- regulation of adenylate cyclase activity
- negative regulation of secretion
- Adrenaline signalling through Alpha-2 adrenergic receptor

### `n0693` — Isoprenoid and sphingolipid biosynthesis

cohesion 0.300 · 1 children · 3 direct pathways

**Child clusters:**

- Cholesterol biosynthesis and homeostasis

**Direct pathways:**

- sphingomyelin biosynthetic process
- geranylgeranyl diphosphate metabolic process
- Defective DHDDS causes RP59

### `n0269` — Angiogenesis and vascular growth signalling

cohesion 0.299 · 2 children · 0 direct pathways

**Child clusters:**

- Regulation of vascular and epithelial growth
- VEGF signalling in vascular and lymphatic development

### `n0406` — Amino acid and vitamin B6 metabolism

cohesion 0.297 · 2 children · 2 direct pathways

**Child clusters:**

- Amino acid catabolism to cofactors and mediators
- Amino acid metabolism and catabolism

**Direct pathways:**

- vitamin B6 metabolic process
- Serine metabolism

### `n0314` — Actin-driven membrane protrusion and pathogen entry

cohesion 0.297 · 1 children · 4 direct pathways

**Child clusters:**

- Branched actin nucleation and lamellipodium formation

**Direct pathways:**

- macropinocytosis
- positive regulation of ruffle assembly
- Listeria monocytogenes entry into host cells
- InlA-mediated entry of Listeria monocytogenes into host cells

### `n0291` — Nucleotide biosynthesis regulation and transport

cohesion 0.295 · 1 children · 3 direct pathways

**Child clusters:**

- Nucleotide triphosphate and phosphate metabolism

**Direct pathways:**

- negative regulation of nucleotide biosynthetic process
- positive regulation of nucleotide biosynthetic process
- nucleotide transmembrane transport

### `n0373` — Hypoxia-linked glycolytic and pyruvate metabolism

cohesion 0.295 · 1 children · 4 direct pathways

**Child clusters:**

- HIF-mediated hypoxia response

**Direct pathways:**

- pyruvate metabolic process
- nucleoside diphosphate catabolic process
- HALLMARK_GLYCOLYSIS
- Glycolysis

### `n0281` — Neural circuits of behavior and addiction

cohesion 0.294 · 2 children · 0 direct pathways

**Child clusters:**

- Neural response to drugs of abuse
- Neural regulation of locomotor behavior

### `n0592` — Mechanical stimulus sensing

cohesion 0.294 · 1 children · 3 direct pathways

**Child clusters:**

- Sensory transduction across modalities

**Direct pathways:**

- response to mechanical stimulus
- detection of mechanical stimulus involved in sensory perception
- response to hydrostatic pressure

### `n0703` — FGFR and ERBB receptor tyrosine kinase signaling

cohesion 0.293 · 2 children · 0 direct pathways

**Child clusters:**

- FGFR ligand binding and downstream signalling
- ERBB2/EGFR receptor signaling

### `n0473` — Vitamin D and fat-soluble vitamin metabolism

cohesion 0.292 · 1 children · 4 direct pathways

**Child clusters:**

- Sex steroid and adrenal corticosteroid synthesis

**Direct pathways:**

- fat-soluble vitamin catabolic process
- regulation of vitamin D receptor signaling pathway
- Defective CYP24A1 causes HCAI
- Defective CYP27B1 causes VDDR1B

### `n0236` — Pancreatic endocrine cell development and beta cell homeostasis

cohesion 0.291 · 1 children · 4 direct pathways

**Child clusters:**

- Endoderm-derived epithelial identity and maturation

**Direct pathways:**

- type B pancreatic cell proliferation
- negative regulation of type B pancreatic cell apoptotic process
- Regulation of gene expression in late stage (branching morphogenesis) pancreatic bud precursor cells
- Regulation of gene expression in endocrine-committed (NEUROG3+) progenitor cells

### `n0786` — Phosphate transport and mineral homeostasis

cohesion 0.288 · 1 children · 4 direct pathways

**Child clusters:**

- Transmembrane ion transport and homeostasis

**Direct pathways:**

- phosphate ion homeostasis
- amelogenesis
- Sodium-coupled phosphate cotransporters
- Defective SLC20A2 causes idiopathic basal ganglia calcification 1 (IBGC1)

### `n0233` — Virus-host interactions and antiviral therapeutics

cohesion 0.288 · 1 children · 3 direct pathways

**Child clusters:**

- Host regulation of viral replication and entry

**Direct pathways:**

- Potential therapeutics for SARS
- SARS-CoV-2 Infection
- Dengue Virus-Host Interactions

### `n0687` — GPCR signaling via cyclic nucleotides and amines

cohesion 0.288 · 2 children · 0 direct pathways

**Child clusters:**

- GPCR–cyclic nucleotide signalling via adenylate cyclase
- GPCR-mediated aminergic neurotransmitter signaling

### `n0353` — Allergic and IL-33-driven immune activation

cohesion 0.288 · 2 children · 2 direct pathways

**Child clusters:**

- Antibody-mediated hypersensitivity and Fc receptor signalling
- IgE-mediated allergic effector cell activation

**Direct pathways:**

- interleukin-33-mediated signaling pathway
- Interleukin-33 signaling

### `n0407` — Bioactive lipid mediator turnover and signaling

cohesion 0.287 · 1 children · 4 direct pathways

**Child clusters:**

- Prostaglandin synthesis and signaling

**Direct pathways:**

- monoacylglycerol metabolic process
- N-acylethanolamine metabolic process
- cellular response to prostaglandin E stimulus
- ether catabolic process

### `n0730` — Inositol phosphate and nucleotide phosphate metabolism

cohesion 0.286 · 1 children · 4 direct pathways

**Child clusters:**

- Nucleotide triphosphate and phosphate metabolism

**Direct pathways:**

- nucleotide transmembrane transport
- Inositol phosphate metabolism
- Synthesis of pyrophosphates in the cytosol
- Synthesis of IPs in the nucleus

### `n0704` — Triglyceride and insulin-responsive glucose metabolism

cohesion 0.284 · 1 children · 3 direct pathways

**Child clusters:**

- Neutral lipid storage and phospholipid turnover

**Direct pathways:**

- triglyceride metabolic process
- glucose import in response to insulin stimulus
- positive regulation of triglyceride metabolic process

### `n0639` — Kinase-driven phosphorylation and PI3K/AKT signalling

cohesion 0.282 · 1 children · 5 direct pathways

**Child clusters:**

- PI3K/AKT activation downstream of growth factor receptors

**Direct pathways:**

- phosphorylation
- protein autophosphorylation
- HALLMARK_PI3K_AKT_MTOR_SIGNALING
- Signaling by ALK
- Signaling by LTK

### `n0557` — Mesangial and mesenchymal signalling in glomerular development

cohesion 0.280 · 2 children · 0 direct pathways

**Child clusters:**

- Glomerular mesangial cell and capillary development
- Receptor tyrosine kinase and cytokine signalling in mesenchymal remodelling

### `n0510` — Osmotic homeostasis and water/solute transport

cohesion 0.277 · 3 children · 1 direct pathways

**Child clusters:**

- Transmembrane ion transport and homeostasis
- Cellular osmotic and salt stress response
- Water balance and aquaporin function

**Direct pathways:**

- polyol transmembrane transport

### `n0676` — cAMP signalling generation and turnover

cohesion 0.277 · 1 children · 5 direct pathways

**Child clusters:**

- GPCR–cyclic nucleotide signalling via adenylate cyclase

**Direct pathways:**

- cAMP catabolic process
- positive regulation of cyclase activity
- regulation of adenylate cyclase activity
- cellular response to cAMP
- response to forskolin

### `n0274` — Endocytic control of receptor tyrosine kinase signalling

cohesion 0.276 · 1 children · 3 direct pathways

**Child clusters:**

- Attenuation of receptor tyrosine kinase signalling

**Direct pathways:**

- TBA *(untitled BTM module)*
- regulation of platelet-derived growth factor receptor-beta signaling pathway
- Clathrin-mediated endocytosis

### `n0775` — Ubiquitin-proteasome protein quality control

cohesion 0.275 · 1 children · 4 direct pathways

**Child clusters:**

- Ubiquitin-dependent proteasomal degradation

**Direct pathways:**

- ERAD pathway
- protein unfolding
- obsolete negative regulation of proteolysis involved in protein catabolic process
- negative regulation of ERAD pathway

### `n0590` — Glycerolipid and phospholipid metabolism

cohesion 0.275 · 2 children · 0 direct pathways

**Child clusters:**

- Phospholipid and phosphatidic acid biosynthesis
- Neutral lipid storage and phospholipid turnover

### `n0795` — Cofactor and non-proteinogenic amino acid metabolism

cohesion 0.268 · 1 children · 8 direct pathways

**Child clusters:**

- Amino acid catabolism to cofactors and mediators

**Direct pathways:**

- obsolete methionine biosynthetic process
- folic acid-containing compound biosynthetic process
- folic acid transport
- vitamin B6 metabolic process
- non-proteinogenic amino acid metabolic process
- non-proteinogenic amino acid biosynthetic process
- Methionine salvage pathway
- Serine metabolism

### `n0397` — Regulation of protein localization and modification in signaling

cohesion 0.267 · 1 children · 4 direct pathways

**Child clusters:**

- Ubiquitin-proteasome control of regulatory protein levels

**Direct pathways:**

- negative regulation of protein export from nucleus
- negative regulation of post-translational protein modification
- Constitutive Signaling by AKT1 E17K in Cancer
- Regulation of PTEN localization

### `n0457` — Proteasome assembly and function

cohesion 0.266 · 1 children · 4 direct pathways

**Child clusters:**

- Ubiquitin-dependent proteasomal degradation

**Direct pathways:**

- proteasomal ubiquitin-independent protein catabolic process
- proteasome assembly
- negative regulation of post-translational protein modification
- Proteasome assembly

### `n0165` — Skeletal and dental mineralization control

cohesion 0.259 · 1 children · 5 direct pathways

**Child clusters:**

- Chondrocyte differentiation and endochondral ossification

**Direct pathways:**

- negative regulation of bone mineralization
- cartilage morphogenesis
- regulation of tooth mineralization
- cementum mineralization
- regulation of odontoblast differentiation

### `n0527` — UNNAMEABLE

cohesion 0.257 · 1 children · 4 direct pathways

> The pathways all concern polyamine metabolism and transport, but the sibling child cluster covers unrelated protein hydroxylation/methylation modifications, so no specific theme covers both without inventing a false connection or resorting to an overly broad label.

**Child clusters:**

- Protein hydroxylation and histidine/lysine methylation

**Direct pathways:**

- polyamine biosynthetic process
- spermidine metabolic process
- polyamine transport
- Regulation of ornithine decarboxylase (ODC)

### `n0383` — Neural circuit control of behavior

cohesion 0.255 · 2 children · 0 direct pathways

**Child clusters:**

- Neural regulation of behaviour and physiology
- Neural regulation of locomotor behavior

### `n0647` — Nutrient sensing and growth-stress signaling

cohesion 0.253 · 2 children · 1 direct pathways

**Child clusters:**

- eIF2α-mediated stress translation control
- Nutrient and stress sensing in growth control

**Direct pathways:**

- HALLMARK_MTORC1_SIGNALING

### `n0568` — Leukocyte effector immunity

cohesion 0.252 · 2 children · 1 direct pathways

**Child clusters:**

- Myeloid leukocyte degranulation and effector immunity
- *(refused)*

**Direct pathways:**

- leukocyte mediated immunity

### `n0646` — EGFR and TGF-beta signaling in cancer

cohesion 0.251 · 2 children · 0 direct pathways

**Child clusters:**

- ERBB2/EGFR receptor signaling
- TGF-beta tumour suppression via SMAD and RUNX3

### `n0432` — Intestinal epithelial identity and homeostasis

cohesion 0.239 · 1 children · 4 direct pathways

**Child clusters:**

- Endoderm-derived epithelial identity and maturation

**Direct pathways:**

- leukocyte migration
- intestinal stem cell homeostasis
- intestinal epithelial cell differentiation
- HALLMARK_KRAS_SIGNALING_DN

### `n0598` — Lipid metabolism and secretory trafficking

cohesion 0.234 · 1 children · 3 direct pathways

**Child clusters:**

- Sphingomyelin metabolism and ceramide signalling

**Direct pathways:**

- lipoprotein catabolic process
- regulation of Golgi to plasma membrane protein transport
- Wnt protein secretion

### `n0658` — UNNAMEABLE

cohesion 0.230 · 1 children · 3 direct pathways

> Notch target-gene transcription and NOTCH2-specific signalling share a theme, but the AP-2 transcription factor regulation pathway is biologically unrelated, so no single specific name covers all members without invention.

**Child clusters:**

- Notch signaling

**Direct pathways:**

- positive regulation of transcription of Notch receptor target
- NOTCH2 intracellular domain regulates transcription
- Negative regulation of activity of TFAP2 (AP-2) family transcription factors

### `n0539` — Neuroendocrine regulation of growth and metabolism

cohesion 0.191 · 2 children · 0 direct pathways

**Child clusters:**

- Endocrine control of somatic growth
- Neuroendocrine control of growth and appetite

### `n0670` — Neurotrophin and adhesion signalling in axon and myelin development

cohesion 0.189 · 2 children · 1 direct pathways

**Child clusters:**

- Axon-glia adhesion and myelination
- Neurotrophin-driven neuronal growth and survival signalling

**Direct pathways:**

- BDNF activates NTRK2 (TRKB) signaling

---

## Members, per leaf

### `n0022` — Drug-resistant FLT3 kinase mutants

cohesion 0.808 · 4 members

- KW2449-resistant FLT3 mutants
- gilteritinib-resistant FLT3 mutants
- sorafenib-resistant FLT3 mutants
- sunitinib-resistant FLT3 mutants

### `n0192` — Nucleotide biosynthesis and metabolism

cohesion 0.778 · 3 members

- nucleotide metabolic process
- ribonucleoside monophosphate biosynthetic process
- ribose phosphate metabolic process

### `n0031` — DNA replication and licensing

cohesion 0.753 · 3 members

- DNA replication
- Synthesis of DNA
- DNA Replication

### `n0020` — Base excision repair glycosylase step

cohesion 0.749 · 5 members

- base-excision repair, AP site formation
- DNA modification
- Recognition and association of DNA glycosylase with site containing an affected pyrimidine
- Depyrimidination
- Base-Excision Repair, AP Site Formation

### `n0137` — Metanephric tubule and collecting duct development

cohesion 0.709 · 3 members

- collecting duct development
- metanephric tubule morphogenesis
- metanephric collecting duct development

### `n0119` — Specialized pro-resolving lipid mediator biosynthesis

cohesion 0.708 · 5 members

- Biosynthesis of specialized proresolving mediators (SPMs)
- Biosynthesis of protectins
- Biosynthesis of DPAn-3 SPMs
- Biosynthesis of DPAn-3-derived protectins and resolvins
- Biosynthesis of DPAn-3-derived maresins

### `n0023` — Kinetochore-microtubule attachment regulation

cohesion 0.707 · 4 members

- regulation of attachment of spindle microtubules to kinetochore
- regulation of metaphase plate congression
- regulation of attachment of mitotic spindle microtubules to kinetochore
- positive regulation of attachment of mitotic spindle microtubules to kinetochore

### `n0100` — Postsynaptic density and synapse assembly

cohesion 0.699 · 3 members

- postsynaptic density organization
- postsynaptic specialization assembly
- excitatory synapse assembly

### `n0056` — Triglyceride-rich lipoprotein remodeling and clearance

cohesion 0.692 · 3 members

- chylomicron remodeling
- triglyceride-rich lipoprotein particle clearance
- Chylomicron remodeling

### `n0054` — APC/C control of mitotic exit

cohesion 0.672 · 5 members

- positive regulation of ubiquitin protein ligase activity
- Inactivation of APC/C via direct inhibition of the APC/C complex
- APC/C-mediated degradation of cell cycle proteins
- Cdc20:Phospho-APC/C mediated degradation of Cyclin A
- Regulation of mitotic cell cycle

### `n0226` — Sister chromatid cohesion maintenance

cohesion 0.669 · 3 members

- maintenance of sister chromatid cohesion
- regulation of maintenance of sister chromatid cohesion
- positive regulation of maintenance of sister chromatid cohesion

### `n0053` — Nucleotide excision repair

cohesion 0.666 · 4 members · checks failed: `copies_member`

- nucleotide-excision repair
- HALLMARK_DNA_REPAIR
- Nucleotide Excision Repair
- Dual Incision in GG-NER

### `n0224` — Cristae architecture and MICOS complex

cohesion 0.656 · 3 members

- inner mitochondrial membrane organization
- cristae formation
- Cristae formation

### `n0027` — Cell cycle progression and division

cohesion 0.655 · 3 members

- HALLMARK_E2F_TARGETS
- Cell Cycle
- Cell Cycle, Mitotic

### `n0212` — Cardiac action potential repolarization

cohesion 0.651 · 3 members

- regulation of ventricular cardiac muscle cell membrane repolarization
- regulation of cardiac muscle cell membrane repolarization
- Phase 2 - plateau phase

### `n0078` — Homologous recombination repair of DNA double-strand breaks

cohesion 0.648 · 4 members

- HDR through MMEJ (alt-NHEJ)
- Homologous DNA Pairing and Strand Exchange
- Defective HDR through Homologous Recombination Repair (HRR) due to PALB2 loss of BRCA1 binding function
- Impaired BRCA2 binding to RAD51

### `n0227` — Nef-mediated receptor downregulation

cohesion 0.646 · 3 members

- Nef mediated downregulation of MHC class I complex cell surface expression
- Nef Mediated CD4 Down-regulation
- Nef Mediated CD8 Down-regulation

### `n0076` — Axon and dendrite outgrowth regulation

cohesion 0.640 · 4 members

- regulation of neuron projection development
- regulation of axon extension
- regulation of extent of cell growth
- neuron projection extension

### `n0099` — Nephron and kidney morphogenesis

cohesion 0.630 · 3 members

- kidney morphogenesis
- cell differentiation involved in kidney development
- nephron development

### `n0079` — Dolichol-linked glycosylation precursor synthesis

cohesion 0.620 · 4 members

- Synthesis of dolichyl-phosphate mannose
- Defective RFT1 causes CDG-1n
- Defective DPM1 causes DPM1-CDG
- Defective DOLK causes DOLK-CDG

### `n0138` — Drug metabolism and disposition

cohesion 0.617 · 3 members

- xenobiotic metabolism
- Phase II - Conjugation of compounds
- Drug ADME

### `n0225` — Catecholamine and phenolic amine catabolism

cohesion 0.614 · 3 members

- amine catabolic process
- phenol-containing compound catabolic process
- catechol-containing compound catabolic process

### `n0201` — Kinetochore-driven mitotic chromosome segregation control

cohesion 0.612 · 3 members

- mitotic cell division
- mitotic cell cycle checkpoint signaling
- chromosome separation

### `n0139` — Mitochondrial oxidative phosphorylation

cohesion 0.610 · 4 members

- respiratory electron transport chain (mitochondrion)
- oxidative phosphorylation
- electron transport chain
- HALLMARK_OXIDATIVE_PHOSPHORYLATION

### `n0189` — Lymphocyte migration and chemotaxis regulation

cohesion 0.609 · 3 members

- regulation of lymphocyte chemotaxis
- positive regulation of lymphocyte migration
- regulation of T cell migration

### `n0030` — TGF-beta/BMP-SMAD signalling regulation

cohesion 0.600 · 3 members

- cell surface receptor protein serine/threonine kinase signaling pathway
- negative regulation of BMP signaling pathway
- regulation of SMAD protein signal transduction

### `n0028` — Translesion DNA synthesis and its termination

cohesion 0.600 · 3 members

- DNA synthesis involved in DNA replication
- Translesion synthesis by REV1
- Termination of translesion DNA synthesis

### `n0177` — Signalling control of mesodermal fate commitment

cohesion 0.599 · 3 members

- mesodermal cell fate commitment
- regulation of cell fate specification
- regulation of mesodermal cell fate specification

### `n0098` — Cardiac septation and outflow tract morphogenesis

cohesion 0.598 · 4 members

- outflow tract morphogenesis
- ventricular septum development
- ventricular septum morphogenesis
- regulation of heart morphogenesis

### `n0187` — Intrinsic mitochondrial apoptotic signaling

cohesion 0.596 · 3 members

- intrinsic apoptotic signaling pathway
- positive regulation of endoplasmic reticulum stress-induced intrinsic apoptotic signaling pathway
- Intrinsic Pathway for Apoptosis

### `n0074` — Insulin secretion regulation

cohesion 0.588 · 4 members

- insulin secretion
- regulation of hormone secretion
- regulation of insulin secretion
- Regulation of insulin secretion

### `n0182` — Excitation-contraction coupling in muscle

cohesion 0.583 · 6 members · checks failed: `duplicate_name`

- muscle system process
- muscle contraction
- regulation of muscle contraction
- striated muscle contraction
- Muscle contraction
- Ion homeostasis

### `n0019` — Cardiac conduction system electrical propagation

cohesion 0.581 · 5 members

- atrial cardiac muscle cell to AV node cell communication
- AV node cell to bundle of His cell communication
- bundle of His cell to Purkinje myocyte communication
- regulation of heart rate by cardiac conduction
- regulation of cardiac muscle cell action potential

### `n0480` — Deoxyribonucleotide synthesis and catabolism

cohesion 0.579 · 6 members

- deoxyribonucleoside monophosphate catabolic process
- pyrimidine deoxyribonucleoside monophosphate metabolic process
- pyrimidine deoxyribonucleoside triphosphate metabolic process
- deoxyribonucleotide metabolic process
- dGMP metabolic process
- purine deoxyribonucleoside metabolic process

### `n0146` — Lipoprotein particle assembly and transport

cohesion 0.577 · 5 members

- acylglycerol transport
- chylomicron assembly
- very-low-density lipoprotein particle assembly
- lipoprotein localization
- Chylomicron assembly

### `n0326` — Purine and pyrimidine nucleoside salvage and catabolism

cohesion 0.576 · 6 members

- ribonucleoside metabolic process
- deoxyribonucleoside monophosphate catabolic process
- dGMP metabolic process
- purine deoxyribonucleoside metabolic process
- purine ribonucleoside catabolic process
- Diseases of nucleotide metabolism

### `n0161` — Lens fiber cell differentiation

cohesion 0.567 · 4 members · checks failed: `copies_member`

- lens fiber cell differentiation
- lens fiber cell development
- regulation of lens fiber cell differentiation
- negative regulation of lens fiber cell differentiation

### `n0237` — Nucleoside and nucleotide salvage

cohesion 0.566 · 5 members

- ribonucleoside metabolic process
- nucleotide salvage
- glycosyl compound biosynthetic process
- Nucleotide salvage
- Diseases of nucleotide metabolism

### `n0029` — Small RNA-guided gene silencing

cohesion 0.566 · 3 members

- regulatory ncRNA-mediated gene silencing
- miRNA-mediated gene silencing by mRNA destabilization
- Gene Silencing by RNA

### `n0049` — IL-6/gp130-JAK-STAT3 signaling

cohesion 0.564 · 4 members

- response to interleukin-6
- HALLMARK_IL6_JAK_STAT3_SIGNALING
- Interleukin-6 signaling
- Interleukin-6 family signaling

### `n0170` — Cell-cell and matrix adhesion

cohesion 0.561 · 4 members

- cell adhesion
- homophilic cell-cell adhesion
- cell junction organization
- cell-cell adhesion

### `n0075` — Lipoprotein particle metabolism and transport

cohesion 0.561 · 4 members

- regulation of high-density lipoprotein particle clearance
- high-density lipoprotein particle assembly
- regulation of plasma lipoprotein particle levels
- regulation of lipid localization

### `n0114` — Melanocyte pigmentation biology

cohesion 0.559 · 3 members

- pigmentation
- developmental pigmentation
- MITF-M-regulated melanocyte development

### `n0087` — Cardiac muscle cell development and differentiation

cohesion 0.558 · 7 members

- cardiac muscle tissue development
- muscle cell development
- cardiac cell development
- cardiac muscle cell differentiation
- muscle tissue development
- muscle structure development
- regulation of cardiocyte differentiation

### `n0153` — MHC class I antigen presentation induction

cohesion 0.555 · 3 members

- MHC class I biosynthetic process
- positive regulation of MHC class I biosynthetic process
- HALLMARK_INTERFERON_GAMMA_RESPONSE

### `n0228` — Regulation of IRE1/PERK UPR signalling

cohesion 0.554 · 3 members

- regulation of IRE1-mediated unfolded protein response
- regulation of PERK-mediated unfolded protein response
- negative regulation of PERK-mediated unfolded protein response

### `n0032` — Renin-angiotensin regulation of blood pressure and volume

cohesion 0.554 · 3 members

- regulation of systemic arterial blood pressure by circulatory renin-angiotensin
- regulation of blood volume by renin-angiotensin
- regulation of systemic arterial blood pressure mediated by a chemical signal

### `n0190` — Innate sensing of bacterial molecules

cohesion 0.552 · 3 members

- detection of biotic stimulus
- detection of bacterium
- detection of molecule of bacterial origin

### `n0026` — Complement cascade activation and regulation

cohesion 0.547 · 4 members

- complement activation (I)
- HALLMARK_COMPLEMENT
- Alternative complement activation
- Regulation of Complement cascade

### `n0159` — Regulation of E-cadherin adhesion

cohesion 0.547 · 3 members · checks failed: `sentence_case`

- Regulation of Homotypic Cell-Cell Adhesion
- Regulation of CDH1 Expression and Function
- Degradation of CDH1

### `n0109` — Amino sugar and carbohydrate catabolism

cohesion 0.546 · 4 members

- N-acetylneuraminate catabolic process
- amino sugar catabolic process
- carbohydrate phosphorylation
- glucosamine-containing compound catabolic process

### `n0140` — Congenital disorders of protein glycosylation

cohesion 0.542 · 3 members

- Diseases of glycosylation
- Diseases associated with O-glycosylation of proteins
- DAG1 core M3 glycosylations

### `n0173` — DNA damage repair pathways

cohesion 0.541 · 4 members · checks failed: `pathways`

- DNA repair
- DNA repair
- interstrand cross-link repair
- DNA Repair

### `n0052` — Copper ion homeostasis and detoxification

cohesion 0.536 · 4 members

- intracellular copper ion homeostasis
- detoxification of copper ion
- copper ion homeostasis
- detoxification of inorganic compound

### `n0167` — Hexose transport and its regulation

cohesion 0.536 · 5 members

- carbohydrate transport
- monosaccharide transmembrane transport
- Cellular hexose transport
- Defective SLC2A2 causes Fanconi-Bickel syndrome (FBS)
- Intestinal hexose absorption

### `n0155` — Translation

cohesion 0.535 · 3 members · checks failed: `copies_member`

- mitochondrial translation
- Mitochondrial translation
- Translation

### `n0136` — Defective coagulation factor variants causing bleeding disorders

cohesion 0.530 · 4 members

- Defective F8 accelerates dissociation of the A2 domain
- Defective F8 binding to the cell membrane
- Defective F9 secretion
- Enhanced cleavage of VWF variant by ADAMTS13

### `n0220` — Fatty acid oxidation and ketone body metabolism

cohesion 0.526 · 5 members

- fatty acid beta-oxidation using acyl-CoA dehydrogenase
- HALLMARK_FATTY_ACID_METABOLISM
- Ketone body metabolism
- Synthesis of Ketone Bodies
- Fatty acid metabolism

### `n0210` — Smooth muscle contraction regulation

cohesion 0.526 · 3 members

- smooth muscle contraction
- negative regulation of smooth muscle contraction
- Smooth Muscle Contraction

### `n0149` — RNA polymerase II transcription initiation and elongation, including HIV Tat-dependent control

cohesion 0.526 · 5 members · checks failed: `in_range;sentence_case`

- transcription elongation by RNA polymerase II
- RNA Pol II CTD phosphorylation and interaction with CE during HIV infection
- Transcription of the HIV genome
- Tat-mediated elongation of the HIV-1 transcript
- RNA Polymerase II Transcription Initiation

### `n0072` — Circadian transcriptional feedback loop

cohesion 0.525 · 5 members

- circadian rhythm
- rhythmic process
- Circadian clock
- Expression of BMAL (ARNTL), CLOCK, and NPAS2
- Phosphorylation and nuclear translocation of BMAL1 (ARNTL) and CLOCK

### `n0112` — Hemostasis and thrombin/PAR signalling

cohesion 0.522 · 4 members

- hemostasis
- thrombin-activated receptor signaling pathway
- Hemostasis
- Thrombin signalling through proteinase activated receptors (PARs)

### `n0328` — Recombination-based telomere and genome maintenance

cohesion 0.521 · 5 members

- regulation of mitotic recombination
- telomere maintenance via recombination
- mitotic recombination
- DNA strand elongation
- positive regulation of chromosome organization

### `n0175` — Type I interferon antiviral effector response

cohesion 0.520 · 3 members

- HALLMARK_INTERFERON_ALPHA_RESPONSE
- ISG15 antiviral mechanism
- Antimicrobial mechanism of IFN-stimulated genes

### `n0097` — Antimicrobial peptide-mediated humoral defence

cohesion 0.518 · 4 members

- antibacterial humoral response
- antimicrobial humoral immune response mediated by antimicrobial peptide
- disruption of anatomical structure in another organism
- Antimicrobial peptides

### `n0284` — Nucleotide pool sanitation and catabolism

cohesion 0.517 · 6 members

- nucleoside triphosphate catabolic process
- pyrimidine deoxyribonucleoside monophosphate metabolic process
- pyrimidine deoxyribonucleoside triphosphate metabolic process
- deoxyribonucleotide metabolic process
- Phosphate bond hydrolysis by NUDT proteins
- Nucleotide catabolism

### `n0131` — Amino acid transmembrane transport

cohesion 0.514 · 4 members

- L-amino acid transport
- L-glutamate transmembrane transport
- L-aspartate import across plasma membrane
- L-alpha-amino acid transmembrane transport

### `n0101` — Host-directed viral mRNA translation and transcription

cohesion 0.510 · 3 members

- viral translational termination-reinitiation
- Influenza Viral RNA Transcription and Replication
- Viral mRNA Translation

### `n0051` — Long-chain and very long-chain fatty acid metabolism

cohesion 0.510 · 4 members

- very long-chain fatty acid metabolic process
- alpha-linolenic acid metabolic process
- long-chain fatty acid biosynthetic process
- very long-chain fatty acid catabolic process

### `n0169` — Death receptor-induced caspase-8 activation

cohesion 0.508 · 4 members

- positive regulation of extrinsic apoptotic signaling pathway
- CASP8 activity is inhibited
- Caspase activation via extrinsic apoptotic signalling pathway
- TRAIL  signaling

### `n0188` — Regulation of protein kinase activity

cohesion 0.507 · 3 members

- regulation of phosphorylation
- regulation of protein serine/threonine kinase activity
- negative regulation of protein serine/threonine kinase activity

### `n0110` — Muscle cell proliferation and differentiation

cohesion 0.507 · 4 members

- striated muscle cell proliferation
- muscle cell proliferation
- positive regulation of muscle cell differentiation
- myoblast proliferation

### `n0151` — Control of glial cell generation

cohesion 0.505 · 4 members

- regulation of gliogenesis
- negative regulation of gliogenesis
- astrocyte differentiation
- regulation of glial cell proliferation

### `n0069` — Sarcomere assembly and contraction

cohesion 0.500 · 6 members

- myofibril assembly
- skeletal muscle thin filament assembly
- myosin filament organization
- actin-myosin filament sliding
- pointed-end actin filament capping
- Striated Muscle Contraction

### `n0709` — Intestinal lipid and sterol absorption

cohesion 0.493 · 7 members

- regulation of intestinal cholesterol absorption
- intestinal absorption
- intestinal lipid absorption
- intestinal hexose absorption
- regulation of intestinal absorption
- Intestinal absorption
- Intestinal lipid absorption

### `n0203` — Intracellular vesicle transport

cohesion 0.493 · 3 members

- vesicle-mediated transport
- intracellular transport
- Vesicle-mediated transport

### `n0088` — Regulation of telomere maintenance

cohesion 0.492 · 6 members

- negative regulation of DNA metabolic process
- establishment of protein localization to telomere
- regulation of telomere maintenance via telomere lengthening
- negative regulation of telomere maintenance via telomere lengthening
- Chromosome Maintenance
- Inhibition of DNA recombination at telomere

### `n0057` — Inherited disorders of carbohydrate metabolism

cohesion 0.491 · 3 members

- Glycogen storage diseases
- Glycogen storage disease type 0 (muscle GYS1)
- Diseases of carbohydrate metabolism

### `n0287` — RNA polymerase I and III transcription

cohesion 0.488 · 5 members

- transcription elongation by RNA polymerase I
- transcription by RNA polymerase III
- 5S class rRNA transcription by RNA polymerase III
- RNA Polymerase III Transcription Termination
- RNA Polymerase III Abortive And Retractive Initiation

### `n0172` — Regulation of cell-matrix adhesion turnover

cohesion 0.488 · 4 members

- regulation of cell-matrix adhesion
- negative regulation of cell-substrate adhesion
- regulation of focal adhesion disassembly
- regulation of cell-substrate junction organization

### `n0148` — Cytoplasmic mRNA turnover and 3'-end processing

cohesion 0.487 · 5 members

- mRNA catabolic process
- positive regulation of mRNA 3'-end processing
- RNA decapping
- Deadenylation-dependent mRNA decay
- Deadenylation of mRNA

### `n0184` — MHC-restricted antigen processing and presentation

cohesion 0.487 · 6 members

- antigen processing and presentation
- antigen processing and presentation of peptide antigen via MHC class Ib
- antigen processing and presentation of endogenous peptide antigen
- peptide antigen assembly with MHC protein complex
- antigen processing and presentation
- antigen processing and presentation of endogenous antigen

### `n0093` — Steroid hormone receptor transcriptional regulation

cohesion 0.486 · 5 members

- regulation of intracellular steroid hormone receptor signaling pathway
- negative regulation of intracellular steroid hormone receptor signaling pathway
- regulation of androgen receptor signaling pathway
- negative regulation of androgen receptor signaling pathway
- Estrogen-dependent gene expression

### `n0127` — Digestion and intestinal nutrient absorption

cohesion 0.485 · 6 members

- digestion
- intestinal absorption
- intestinal hexose absorption
- Digestion of dietary lipid
- Digestion
- Intestinal absorption

### `n0118` — Mitotic spindle assembly and positioning

cohesion 0.484 · 3 members

- spindle organization
- establishment of mitotic spindle localization
- Loss of Nlp from mitotic centrosomes

### `n0018` — Mitophagy

cohesion 0.481 · 6 members · checks failed: `copies_member`

- autophagy of mitochondrion
- mitophagy
- type 2 mitophagy
- response to mitochondrial depolarisation
- regulation of autophagy of mitochondrion
- Mitophagy

### `n0115` — Myeloid leukocyte degranulation and effector immunity

cohesion 0.481 · 3 members

- positive regulation of myeloid leukocyte mediated immunity
- neutrophil degranulation
- Neutrophil degranulation

### `n0211` — Cholesterol biosynthesis and homeostasis

cohesion 0.480 · 3 members

- obsolete cholesterol biosynthetic process via desmosterol
- HALLMARK_CHOLESTEROL_HOMEOSTASIS
- Zymostenol biosynthesis via lathosterol (Kandutsch-Russell pathway)

### `n0160` — Regulation of leukocyte-endothelial adhesion

cohesion 0.478 · 4 members

- negative regulation of cellular extravasation
- negative regulation of cell adhesion molecule production
- negative regulation of leukocyte adhesion to vascular endothelial cell
- positive regulation of leukocyte adhesion to arterial endothelial cell

### `n0150` — CD4 T cell activation and lineage differentiation

cohesion 0.476 · 5 members

- T cell activation involved in immune response
- negative regulation of CD4-positive, alpha-beta T cell differentiation
- regulatory T cell differentiation
- regulation of T-helper cell differentiation
- positive regulation of alpha-beta T cell differentiation

### `n0207` — Retinoid metabolism and signaling

cohesion 0.476 · 5 members

- vitamin A metabolic process
- diterpenoid metabolic process
- diterpenoid biosynthetic process
- terpenoid catabolic process
- Defective visual phototransduction due to STRA6 loss of function

### `n0408` — Central carbon and fasting fuel metabolism

cohesion 0.475 · 7 members

- glycerol metabolic process
- acetyl-CoA metabolic process
- oxaloacetate metabolic process
- fatty acid beta-oxidation using acyl-CoA dehydrogenase
- Ketone body metabolism
- Synthesis of Ketone Bodies
- Alanine metabolism

### `n0145` — Phototransduction in vision

cohesion 0.473 · 5 members

- sensory perception of light stimulus
- The phototransduction cascade
- Inactivation, recovery and regulation of the phototransduction cascade
- Defective SLC24A1 causes congenital stationary night blindness 1D (CSNB1D)
- Defective visual phototransduction due to OPN1SW loss of function

### `n0133` — Regulation of calcium ion transmembrane transport

cohesion 0.473 · 3 members · checks failed: `copies_member`

- regulation of calcium ion import
- regulation of calcium ion transmembrane transport
- positive regulation of calcium ion transmembrane transport

### `n0055` — Rho family GTPase cycle

cohesion 0.472 · 4 members

- small GTPase mediated signal transduction
- RHOA GTPase cycle
- RHO GTPase cycle
- RHOF GTPase cycle

### `n0073` — Phospholipid and phosphatidic acid biosynthesis

cohesion 0.470 · 5 members

- phospholipid metabolic process
- phospholipid biosynthetic process
- Synthesis of CL
- Synthesis of PA
- Glycerophospholipid biosynthesis

### `n0012` — Photoreceptor development and maintenance

cohesion 0.469 · 7 members

- retina homeostasis
- photoreceptor cell morphogenesis
- photoreceptor cell outer segment organization
- eye photoreceptor cell development
- photoreceptor cell maintenance
- retinal rod cell development
- retinal cone cell development

### `n0105` — Sperm-egg fertilization

cohesion 0.468 · 6 members

- acrosome reaction
- penetration of zona pellucida
- fertilization
- Fertilization
- Sperm Motility And Taxes
- Interaction With Cumulus Cells And The Zona Pellucida

### `n0024` — Cell-cell junction assembly and organization

cohesion 0.466 · 4 members

- apical junction assembly
- cell-cell junction organization
- HALLMARK_APICAL_JUNCTION
- Cell-cell junction organization

### `n0064` — Regulation of type I interferon production and signaling

cohesion 0.465 · 7 members

- type I interferon production
- negative regulation of interferon-beta production
- cellular response to interferon-beta
- regulation of type I interferon-mediated signaling pathway
- positive regulation of type I interferon-mediated signaling pathway
- positive regulation of RIG-I signaling pathway
- IRF3 mediated activation of type 1 IFN

### `n0168` — Synaptic vesicle cycle and neurotransmitter release

cohesion 0.464 · 5 members

- neurotransmitter transport
- regulation of neurotransmitter uptake
- positive regulation of neurotransmitter transport
- vesicle-mediated transport in synapse
- presynaptic modulation of chemical synaptic transmission

### `n0174` — B cell identity and receptor signalling

cohesion 0.461 · 4 members

- enriched in B cells (I)
- enriched in B cells (IV)
- enriched in B cells (VI)
- enriched in naive and memory B cells

### `n0689` — Embryonic axis and neural patterning

cohesion 0.459 · 8 members

- gastrulation
- anterior/posterior axis specification
- forebrain regionalization
- midbrain-hindbrain boundary development
- Epithelial-Mesenchymal Transition (EMT) during gastrulation
- Gastrulation
- Formation of axial mesoderm
- Formation of the posterior neural plate

### `n0108` — Glomerular mesangial cell and capillary development

cohesion 0.459 · 5 members

- regulation of glomerular filtration
- mesangial cell differentiation
- glomerulus vasculature morphogenesis
- positive regulation of glomerular mesangial cell proliferation
- glomerular mesangial cell development

### `n0048` — Adipogenesis and adipose lipid storage

cohesion 0.459 · 4 members

- nutrient storage
- positive regulation of adipose tissue development
- HALLMARK_ADIPOGENESIS
- Adipogenesis

### `n0129` — Glutamate-driven excitatory synaptic plasticity

cohesion 0.458 · 4 members

- positive regulation of long-term neuronal synaptic plasticity
- regulation of postsynapse organization
- cellular response to L-glutamate
- Post NMDA receptor activation events

### `n0223` — T cell receptor signalling and activation

cohesion 0.456 · 3 members

- T cell activation (IV)
- positive regulation of cell-cell adhesion
- positive regulation of alpha-beta T cell proliferation

### `n0616` — Cell cycle checkpoint control

cohesion 0.456 · 6 members

- regulation of mitotic cell cycle
- mitotic G1/S transition checkpoint signaling
- HALLMARK_G2M_CHECKPOINT
- Polo-like kinase mediated events
- Mitotic G1 phase and G1/S transition
- G1 Phase

### `n0077` — Prostaglandin synthesis and signaling

cohesion 0.455 · 3 members

- positive regulation of prostaglandin biosynthetic process
- phospho-PLA2 pathway
- Prostanoid ligand receptors

### `n0677` — tRNA and mitochondrial gene expression maturation

cohesion 0.454 · 7 members

- tRNA threonylcarbamoyladenosine modification
- tRNA processing
- regulation of mitochondrial gene expression
- regulation of mitochondrial translation
- positive regulation of mitochondrial translation
- obsolete tRNA threonylcarbamoyladenosine metabolic process
- tRNA processing

### `n0063` — Cytoskeletal transport of organelles and vesicles

cohesion 0.451 · 7 members

- establishment of organelle localization
- organelle transport along microtubule
- synaptic vesicle cytoskeletal transport
- vesicle cytoskeletal trafficking
- dense core granule transport
- regulation of organelle transport along microtubule
- anterograde neuronal dense core vesicle transport

### `n0336` — Regional patterning of the neural tube

cohesion 0.451 · 6 members

- dorsal spinal cord development
- spinal cord motor neuron differentiation
- forebrain regionalization
- dorsal/ventral neural tube patterning
- midbrain-hindbrain boundary development
- Formation of the posterior neural plate

### `n0191` — Nuclear export of RNA

cohesion 0.450 · 3 members

- poly(A)+ mRNA export from nucleus
- regulation of nucleobase-containing compound transport
- nuclear export

### `n0111` — Regulation of neuronal cytoskeletal growth

cohesion 0.450 · 4 members

- positive regulation of neuron projection development
- negative regulation of filopodium assembly
- positive regulation of microtubule nucleation
- positive regulation of neuron projection arborization

### `n0369` — Protein glycosylation and proteoglycan biosynthesis

cohesion 0.449 · 5 members

- protein O-linked glycosylation
- glycoprotein biosynthetic process
- chondroitin sulfate proteoglycan metabolic process
- protein O-linked glycosylation via glucose
- Pre-NOTCH Processing in the Endoplasmic Reticulum

### `n0185` — Cellular cholesterol and lipoprotein sensing in foam cell formation

cohesion 0.446 · 5 members

- regulation of macrophage derived foam cell differentiation
- response to sterol
- cellular response to lipid
- cellular response to lipoprotein particle stimulus
- foam cell differentiation

### `n0050` — Regulation of amyloid-beta production and clearance

cohesion 0.446 · 4 members

- amyloid-beta metabolic process
- negative regulation of amyloid-beta clearance
- negative regulation of amyloid precursor protein catabolic process
- positive regulation of amyloid precursor protein catabolic process

### `n0477` — Regulation of lipid biosynthesis and fatty acid metabolism

cohesion 0.445 · 6 members

- regulation of ketone metabolic process
- regulation of fatty acid metabolic process
- positive regulation of fatty acid biosynthetic process
- positive regulation of lipid metabolic process
- positive regulation of lipid biosynthetic process
- negative regulation of lipid biosynthetic process

### `n0176` — CCR7-driven dendritic cell trafficking and survival

cohesion 0.445 · 3 members

- myeloid dendritic cell chemotaxis
- positive regulation of phospholipase C/protein kinase C signal transduction
- negative regulation of dendritic cell apoptotic process

### `n0345` — GABA and glutamate/aspartate neurotransmitter transport

cohesion 0.444 · 5 members

- gamma-aminobutyric acid secretion
- gamma-aminobutyric acid transport
- L-glutamate transmembrane transport
- gamma-aminobutyric acid import
- L-aspartate import across plasma membrane

### `n0334` — Early embryonic axis and germ layer formation

cohesion 0.442 · 7 members

- gastrulation
- anterior/posterior axis specification
- paraxial mesoderm morphogenesis
- axis elongation involved in somitogenesis
- Epithelial-Mesenchymal Transition (EMT) during gastrulation
- Gastrulation
- Formation of axial mesoderm

### `n0245` — Toll-like receptor and macrophage activation signalling

cohesion 0.441 · 6 members

- inflammatory response
- macrophage activation involved in immune response
- negative regulation of lipopolysaccharide-mediated signaling pathway
- toll-like receptor 2 signaling pathway
- negative regulation of toll-like receptor 2 signaling pathway
- macrophage activation

### `n0117` — Nucleolar rRNA processing and ribosome subunit maturation

cohesion 0.440 · 4 members

- ribosomal large subunit export from nucleus
- cleavage in ITS2 between 5.8S rRNA and LSU-rRNA of tricistronic rRNA transcript (SSU-rRNA, 5.8S rRNA, LSU-rRNA)
- rRNA 5'-end processing
- regulation of protein localization to nucleolus

### `n0015` — Smooth muscle cell phenotype regulation

cohesion 0.437 · 6 members

- smooth muscle cell migration
- vascular associated smooth muscle cell differentiation
- negative regulation of smooth muscle cell proliferation
- negative regulation of smooth muscle cell differentiation
- negative regulation of smooth muscle cell chemotaxis
- regulation of phenotypic switching

### `n0199` — Endothelial shear stress mechanotransduction

cohesion 0.437 · 5 members

- response to laminar fluid shear stress
- vascular endothelial cell response to fluid shear stress
- response to oscillatory fluid shear stress
- Cellular responses to mechanical stimuli
- Response of endothelial cells to shear stress

### `n0272` — T-helper cell subset differentiation and function

cohesion 0.437 · 7 members

- T-helper cell lineage commitment
- regulation of T-helper 1 type immune response
- T-helper 1 type immune response
- regulation of T-helper 2 cell differentiation
- T-helper 17 type immune response
- regulation of T-helper 17 cell differentiation
- regulation of T-helper 17 cell lineage commitment

### `n0448` — Chondroitin/dermatan sulfate metabolism and disorders

cohesion 0.436 · 7 members

- DS-GAG biosynthesis
- HS-GAG degradation
- CS/DS degradation
- Diseases associated with glycosaminoglycan metabolism
- Defective CHSY1 causes TPBS
- MPS II - Hunter syndrome (CS/DS degradation)
- MPS VII - Sly syndrome (CS/DS degradation)

### `n0278` — Membrane trafficking dynamics

cohesion 0.434 · 5 members

- inositol phosphate metabolism
- vesicle organization
- organelle fusion
- vesicle uncoating
- regulation of endosome organization

### `n0186` — IL-1-driven inflammatory response

cohesion 0.433 · 5 members

- inflammatory response
- HALLMARK_INFLAMMATORY_RESPONSE
- Interleukin-1 family signaling
- Interleukin-1 processing
- Cell recruitment (pro-inflammatory response)

### `n0166` — Calcium handling in muscle relaxation

cohesion 0.431 · 5 members

- negative regulation of striated muscle contraction
- obsolete positive regulation of sequestering of calcium ion
- sarcoplasmic reticulum calcium ion transport
- regulation of calcium ion import into sarcoplasmic reticulum
- Reduction of cytosolic Ca++ levels

### `n0021` — Oxidative stress response and antioxidant defence

cohesion 0.430 · 5 members

- response to oxygen radical
- cell redox homeostasis
- cellular oxidant detoxification
- HALLMARK_REACTIVE_OXYGEN_SPECIES_PATHWAY
- Cellular response to chemical stress

### `n0277` — tRNA maturation and modification

cohesion 0.428 · 5 members

- tRNA processing
- tRNA pseudouridine synthesis
- RNA (guanine-N7)-methylation
- negative regulation of tRNA metabolic process
- tRNA processing

### `n0198` — ERBB2/EGFR receptor signaling

cohesion 0.427 · 5 members

- ERBB2-EGFR signaling pathway
- Signaling by ERBB2
- EGFR interacts with phospholipase C-gamma
- Signaling by ERBB2 KD Mutants
- Resistance of ERBB2 KD mutants to trastuzumab

### `n0068` — Beta-catenin destruction complex regulation

cohesion 0.426 · 6 members

- canonical Wnt signaling pathway
- HALLMARK_WNT_BETA_CATENIN_SIGNALING
- Degradation of beta-catenin by the destruction complex
- CTNNB1 S33 mutants aren't phosphorylated
- Truncations of AMER1 destabilize the destruction complex
- XAV939 stabilizes AXIN

### `n0255` — VEGF signalling in vascular and lymphatic development

cohesion 0.426 · 5 members

- lymph vessel development
- cellular response to vascular endothelial growth factor stimulus
- vascular endothelial growth factor signaling pathway
- Neuropilin interactions with VEGF and VEGFR
- VEGF binds to VEGFR leading to receptor dimerization

### `n0626` — Regulation of Th1 and cytotoxic lymphocyte immunity

cohesion 0.425 · 6 members

- positive regulation of leukocyte mediated immunity
- positive regulation of T cell mediated immunity
- regulation of T-helper 1 type immune response
- positive regulation of type II interferon production
- regulation of natural killer cell activation
- T-helper 1 type immune response

### `n0089` — Transmembrane ion transport and homeostasis

cohesion 0.424 · 6 members

- positive regulation of sodium ion transport
- sodium ion export across plasma membrane
- sodium ion homeostasis
- inorganic ion homeostasis
- inorganic ion import across plasma membrane
- potassium ion import across plasma membrane

### `n0410` — Base excision and single-strand break repair

cohesion 0.422 · 6 members

- single strand break repair
- POLB-Dependent Long Patch Base Excision Repair
- Resolution of AP sites via the multiple-nucleotide patch replacement pathway
- Resolution of AP sites via the single-nucleotide replacement pathway
- Defective Base Excision Repair Associated with NEIL3
- NEIL3-mediated resolution of ICLs

### `n0317` — Peroxisome biogenesis and protein import

cohesion 0.421 · 7 members

- protein targeting
- protein import into peroxisome matrix, receptor recycling
- protein to membrane docking
- HALLMARK_PEROXISOME
- Peroxisomal protein import
- Class I peroxisomal membrane protein import
- Pexophagy

### `n0355` — Cytoskeletal transport of organelles

cohesion 0.419 · 6 members

- mitochondrion localization
- establishment of organelle localization
- organelle transport along microtubule
- vesicle cytoskeletal trafficking
- regulation of organelle transport along microtubule
- RHOT1 GTPase cycle

### `n0157` — Branched actin nucleation and lamellipodium formation

cohesion 0.419 · 4 members

- actin nucleation
- negative regulation of actin nucleation
- lamellipodium morphogenesis
- positive regulation of lamellipodium morphogenesis

### `n0476` — Regulation of the unfolded protein response

cohesion 0.419 · 6 members

- cellular response to topologically incorrect protein
- positive regulation of endoplasmic reticulum unfolded protein response
- positive regulation of endoplasmic reticulum stress-induced intrinsic apoptotic signaling pathway
- negative regulation of response to endoplasmic reticulum stress
- positive regulation of response to endoplasmic reticulum stress
- HALLMARK_UNFOLDED_PROTEIN_RESPONSE

### `n0194` — mRNA 3' end maturation and decay

cohesion 0.418 · 8 members

- DNA-templated transcription termination
- termination of RNA polymerase II transcription
- mRNA 3'-end processing
- positive regulation of mRNA 3'-end processing
- RNA decapping
- SLBP independent Processing of Histone Pre-mRNAs
- mRNA 3'-end processing
- SLBP Dependent Processing of Replication-Dependent Histone Pre-mRNAs

### `n0154` — PI3K/AKT activation downstream of growth factor receptors

cohesion 0.416 · 3 members

- phosphatidylinositol 3-kinase/protein kinase B signal transduction
- Constitutive Signaling by Aberrant PI3K in Cancer
- IRS-related events triggered by IGF1R

### `n0171` — Regulation of cell surface receptor turnover

cohesion 0.415 · 4 members

- regulation of receptor recycling
- regulation of receptor internalization
- negative regulation of receptor internalization
- receptor catabolic process

### `n0094` — Gonadotropin control of ovarian and gonadal function

cohesion 0.415 · 5 members

- ovulation cycle process
- gonadotropin secretion
- follicle-stimulating hormone secretion
- cellular response to gonadotropin stimulus
- cellular response to follicle-stimulating hormone stimulus

### `n0499` — Cranial nerve and pharyngeal organ morphogenesis

cohesion 0.415 · 6 members

- facial nerve morphogenesis
- vestibulocochlear nerve formation
- thyroid gland development
- semicircular canal morphogenesis
- face development
- semicircular canal development

### `n0584` — Mitochondrial genome expression and maintenance

cohesion 0.413 · 6 members

- transcription elongation, RNA polymerase II
- regulation of mitochondrial RNA catabolic process
- mitochondrial DNA repair
- regulation of mitochondrial DNA metabolic process
- Mitochondrial transcription termination
- Transcription from mitochondrial promoters

### `n0208` — Non-coding RNA modification and maturation

cohesion 0.413 · 5 members

- small nucleolar ribonucleoprotein complex assembly
- RNA (guanine-N7)-methylation
- snRNA modification
- negative regulation of tRNA metabolic process
- rRNA modification in the nucleus and cytosol

### `n0580` — Mitotic cell division

cohesion 0.411 · 7 members

- Rho GTPase cycle
- cytokinesis
- chromosome segregation
- cell division
- mitotic cytokinetic process
- HALLMARK_MITOTIC_SPINDLE
- Regulation of PLK1 Activity at G2/M Transition

### `n0731` — Cholesterol homeostasis and sterol sensing

cohesion 0.410 · 8 members

- response to sterol
- regulation of cholesterol biosynthetic process
- negative regulation of cholesterol biosynthetic process
- negative regulation of lipid biosynthetic process
- cellular response to lipid
- regulation of cholesterol metabolic process
- VLDLR internalisation and degradation
- NR1H2 & NR1H3 regulate gene expression to limit cholesterol uptake

### `n0559` — Synaptic transmission and plasticity regulation

cohesion 0.410 · 7 members

- synaptic transmission, glutamatergic
- synaptic transmission, GABAergic
- negative regulation of excitatory postsynaptic potential
- gamma-aminobutyric acid receptor clustering
- AMPA selective glutamate receptor signaling pathway
- regulation of trans-synaptic signaling
- short-term synaptic potentiation

### `n0095` — Water balance and aquaporin function

cohesion 0.409 · 5 members

- response to water
- intracellular water homeostasis
- negative regulation of urine volume
- regulation of body fluid levels
- Passive transport by Aquaporins

### `n0219` — Cortical polarity and centrosome positioning

cohesion 0.409 · 5 members

- cortical microtubule organization
- establishment of epithelial cell apical/basal polarity
- establishment of centrosome localization
- establishment or maintenance of monopolar cell polarity
- podocyte cell migration

### `n0196` — FGFR ligand binding and downstream signalling

cohesion 0.408 · 6 members

- phosphatidylinositol-mediated signaling
- FGFR1 ligand binding and activation
- FGFR2c ligand binding and activation
- Phospholipase C-mediated cascade: FGFR1
- Downstream signaling of activated FGFR4
- Signaling by FGFR1

### `n0113` — Endomembrane trafficking and autophagy

cohesion 0.407 · 4 members

- intracellular transport
- endosomal vesicle fusion
- reticulophagy
- multivesicular body-lysosome fusion

### `n0134` — Regulation of insulin-driven glucose uptake and glycogen synthesis

cohesion 0.405 · 3 members

- negative regulation of D-glucose transmembrane transport
- negative regulation of glycogen biosynthetic process
- positive regulation of D-glucose import across plasma membrane

### `n0264` — Neural response to drugs of abuse

cohesion 0.403 · 5 members

- response to nicotine
- response to cocaine
- behavioral response to ethanol
- Opioid Signalling
- Highly calcium permeable nicotinic acetylcholine receptors

### `n0135` — Motile cilia biogenesis and beat regulation

cohesion 0.403 · 5 members

- axoneme assembly
- regulation of cilium beat frequency involved in ciliary motility
- de novo centriole assembly involved in multi-ciliated epithelial cell differentiation
- regulation of motile cilium assembly
- Assembly of the 9+2 motile cilia

### `n0542` — Nucleotide catabolism and methylation pharmacogenetics

cohesion 0.402 · 6 members

- nucleoside triphosphate catabolic process
- Methylation
- Phosphate bond hydrolysis by NUDT proteins
- Defective TPMT causes TPMT deficiency
- Nucleotide catabolism
- Ribavirin ADME

### `n0209` — Renal amino acid reabsorption and transport

cohesion 0.402 · 5 members

- amino acid metabolishm and transport
- proline transmembrane transport
- Amino acid transport across the plasma membrane
- Defective SLC36A2 causes iminoglycinuria (IG) and hyperglycinuria (HG)
- Defective amino acid transport by SLC7A9 causes cystinuria (CSNU)

### `n0599` — Mitochondrial metabolite shuttling and ureagenesis

cohesion 0.401 · 7 members

- urea cycle
- tricarboxylic acid transport
- pyruvate transport
- malate-aspartate shuttle
- Urea cycle
- Malate-aspartate shuttle
- ARG1 variants cause hyperargininemia

### `n0047` — Ubiquitin-dependent proteasomal degradation

cohesion 0.401 · 5 members

- protein polyubiquitination
- post-translational protein modification
- obsolete proteolysis involved in protein catabolic process
- protein K48-linked ubiquitination
- Neddylation

### `n0285` — Ionotropic and inhibitory synaptic signalling

cohesion 0.400 · 5 members

- synaptic transmission, GABAergic
- gamma-aminobutyric acid receptor clustering
- short-term synaptic potentiation
- Activation of AMPA receptors
- Ionotropic activity of kainate receptors

### `n0358` — Chaperone-mediated protein folding

cohesion 0.400 · 5 members

- protein folding
- post-chaperonin tubulin folding pathway
- protein refolding
- Post-chaperonin tubulin folding pathway
- Protein folding

### `n0595` — Regional CNS neuron specification and patterning

cohesion 0.399 · 8 members

- dorsal spinal cord development
- spinal cord motor neuron differentiation
- telencephalon development
- subpallium development
- cerebellar granular layer morphogenesis
- hippocampus development
- dorsal/ventral neural tube patterning
- central nervous system neuron differentiation

### `n0318` — Chromatin and epigenetic regulation

cohesion 0.399 · 7 members

- chromatin organization
- methylation
- epigenetic regulation of gene expression
- Epigenetic regulation of gene expression
- PKMTs methylate histone lysines
- Chromatin organization
- Loss of Function of KMT2D in MLL4 Complex Formation in Kabuki Syndrome

### `n0130` — Epidermal and appendage differentiation

cohesion 0.398 · 4 members

- molting cycle process
- epithelial cell differentiation
- regulation of epidermis development
- skin epidermis development

### `n0252` — Axon guidance signalling and morphogenesis

cohesion 0.398 · 7 members

- axon guidance
- cell morphogenesis
- regulation of anatomical structure morphogenesis
- negative regulation of cell projection organization
- Roundabout signaling pathway
- ephrin receptor signaling pathway
- Axon guidance

### `n0158` — Chondrocyte differentiation and endochondral ossification

cohesion 0.395 · 3 members

- chondrocyte development
- positive regulation of chondrocyte differentiation
- endochondral bone morphogenesis

### `n0690` — p53-mediated cell cycle checkpoint control

cohesion 0.393 · 7 members

- mitotic G1/S transition checkpoint signaling
- Autodegradation of the E3 ubiquitin ligase COP1
- Mitotic G1 phase and G1/S transition
- TP53 Regulates Transcription of Genes Involved in G2 Cell Cycle Arrest
- Regulation of TP53 Degradation
- G1 Phase
- Ubiquitin-Mediated Degradation of Phosphorylated Cdc25A

### `n0441` — UNNAMEABLE

cohesion 0.392 · 6 members

> The members span unrelated RNA processes—nuclear pre-mRNA splicing, RNA polymerase III transcription/termination/initiation, and mitochondrial RNA turnover—so any single theme covering all would be as broad as 'RNA metabolism', which invents a specificity not shared by every member.

- mRNA 3'-splice site recognition
- regulation of mitochondrial RNA catabolic process
- transcription by RNA polymerase III
- U2-type prespliceosome assembly
- RNA Polymerase III Transcription Termination
- RNA Polymerase III Abortive And Retractive Initiation

### `n0096` — Chromatin-based epigenetic regulation

cohesion 0.392 · 5 members

- chromatin organization
- epigenetic regulation of gene expression
- negative regulation of heterochromatin organization
- Epigenetic regulation of gene expression
- HDMs demethylate histones

### `n0389` — Heme synthesis, catabolism and bilirubin clearance

cohesion 0.390 · 6 members

- porphyrin-containing compound metabolic process
- heme A biosynthetic process
- HALLMARK_HEME_METABOLISM
- Heme degradation
- Defective UGT1A1 causes hyperbilirubinemia
- Defective SLCO1B1 causes hyperbilirubinemia, Rotor type (HBLRR)

### `n0338` — Feedback regulation of Hippo and MAPK signalling

cohesion 0.390 · 5 members · checks failed: `sentence_case`

- regulation of hippo signaling
- negative regulation of hippo signaling
- positive regulation of hippo signaling
- ERKs are inactivated
- Negative regulation of MAPK pathway

### `n0583` — Axial patterning and organogenesis of embryo

cohesion 0.390 · 6 members

- Hox cluster IV
- skeletal system morphogenesis
- appendage development
- embryonic heart tube left/right pattern formation
- hindgut development
- determination of digestive tract left/right asymmetry

### `n0429` — p53-driven transcriptional and apoptotic response to damage

cohesion 0.388 · 5 members

- intrinsic apoptotic signaling pathway by p53 class mediator
- positive regulation of intrinsic apoptotic signaling pathway in response to DNA damage
- positive regulation of intrinsic apoptotic signaling pathway by p53 class mediator
- HALLMARK_P53_PATHWAY
- Transcriptional Regulation by TP53

### `n0041` — Bile acid and sterol homeostasis

cohesion 0.388 · 7 members

- bile acid signaling pathway
- regulation of bile acid secretion
- HALLMARK_BILE_ACID_METABOLISM
- Bile acid and bile salt metabolism
- Endogenous sterols
- Metabolism of steroids
- NR1H2 & NR1H3 regulate gene expression to control bile acid homeostasis

### `n0654` — Axon guidance and growth cone signalling

cohesion 0.384 · 6 members

- axon guidance
- Roundabout signaling pathway
- ephrin receptor signaling pathway
- positive regulation of small GTPase mediated signal transduction
- Axon guidance
- RND1 GTPase cycle

### `n0451` — Collagen and keratin structural assembly

cohesion 0.384 · 6 members

- keratinization
- intermediate filament organization
- Collagen formation
- Keratinization
- Formation of the cornified envelope
- Collagen chain trimerization

### `n0551` — rRNA and mRNA processing machinery

cohesion 0.382 · 6 members

- rRNA processing
- protein methylation
- mitochondrial ribosome assembly
- mRNA decay by 3' to 5' exoribonuclease
- rRNA processing
- rRNA processing in the mitochondrion

### `n0178` — Cytokine signalling to epithelial barriers

cohesion 0.380 · 3 members

- response to type III interferon
- Other interleukin signaling
- Interleukin-20 family signaling

### `n0454` — TAK1/NIK-driven NF-kB and MAPK signalling

cohesion 0.378 · 7 members

- activation of NF-kappaB-inducing kinase activity
- positive regulation of non-canonical NF-kappaB signal transduction
- Toll Like Receptor 10 (TLR10) Cascade
- Toll Like Receptor 5 (TLR5) Cascade
- TAK1-dependent IKK and NF-kappa-B activation
- JNK (c-Jun kinases) phosphorylation and  activation mediated by activated human TAK1
- NIK-->noncanonical NF-kB signaling

### `n0200` — Mitochondrial amino acid and nucleobase catabolism disorders

cohesion 0.376 · 5 members

- pyrimidine nucleobase catabolic process
- Defective MMAA causes MMA, cblA type
- Interconversion of 2-oxoglutarate and 2-hydroxyglutarate
- Degradation of GABA
- 3-Methylcrotonyl-CoA carboxylase deficiency

### `n0550` — Cholinergic and opioid neurotransmission signalling

cohesion 0.376 · 6 members

- phospholipase C-activating G protein-coupled acetylcholine receptor signaling pathway
- G protein-coupled acetylcholine receptor signaling pathway
- positive regulation of synaptic transmission, cholinergic
- response to nicotine
- Opioid Signalling
- Highly calcium permeable nicotinic acetylcholine receptors

### `n0107` — Mammary gland development and morphogenesis

cohesion 0.375 · 5 members

- mammary gland epithelial cell proliferation
- positive regulation of mammary gland epithelial cell proliferation
- thelarche
- branching involved in mammary gland duct morphogenesis
- mammary gland alveolus development

### `n0061` — Cellular senescence

cohesion 0.374 · 7 members · checks failed: `copies_member`

- cellular senescence
- oncogene-induced cell senescence
- regulation of cellular senescence
- HALLMARK_UV_RESPONSE_UP
- Cellular Senescence
- Formation of Senescence-Associated Heterochromatin Foci (SAHF)
- Evasion of Oxidative Stress Induced Senescence Due to Defective p16INK4A binding to CDK4 and CDK6

### `n0478` — MHC-restricted antigen presentation to T cells

cohesion 0.374 · 6 members

- antigen processing and presentation
- enriched in antigen presentation (III)
- T cell activation via T cell receptor contact with antigen bound to MHC molecule on antigen presenting cell
- peptide antigen assembly with MHC protein complex
- antigen processing and presentation
- antigen processing and presentation of lipid antigen via MHC class Ib

### `n0222` — Nucleotide triphosphate and phosphate metabolism

cohesion 0.373 · 5 members

- GTP biosynthetic process
- phosphorus metabolic process
- nucleoside triphosphate biosynthetic process
- organophosphate metabolic process
- GTP metabolic process

### `n0614` — Host regulation of viral replication and entry

cohesion 0.373 · 6 members

- viral process
- viral genome replication
- regulation of viral genome replication
- regulation of viral entry into host cell
- Reverse Transcription of HIV RNA
- Assembly Of The HIV Virion

### `n0733` — Endosomal peptide transport in innate immune sensing

cohesion 0.373 · 7 members

- dipeptide transmembrane transport
- regulation of nucleotide-binding domain, leucine rich repeat containing receptor signaling pathway
- nucleotide-binding oligomerization domain containing 1 signaling pathway
- endolysosomal toll-like receptor signaling pathway
- Trafficking and processing of endosomal TLR
- Proton/oligopeptide cotransporters
- SLC15A4:TASL-dependent IRF5 activation

### `n0202` — Myeloid and leukocyte lineage commitment

cohesion 0.373 · 3 members

- leukocyte differentiation
- myeloid progenitor cell differentiation
- Transcriptional regulation of granulopoiesis

### `n0043` — Selective autophagic clearance of protein aggregates

cohesion 0.370 · 6 members

- cytoplasmic stress granule disassembly
- aggrephagy
- chaperone-mediated autophagy
- regulation of aggrephagy
- Chaperone Mediated Autophagy
- Aggrephagy

### `n0091` — B cell development and antibody diversification

cohesion 0.369 · 6 members

- somatic diversification of immune receptors
- pro-B cell differentiation
- pre-B cell differentiation
- regulation of immunoglobulin production
- B cell mediated immunity
- isotype switching to IgA isotypes

### `n0221` — Amino acid catabolism to cofactors and mediators

cohesion 0.367 · 5 members

- sulfur amino acid metabolic process
- L-tryptophan catabolic process
- L-tyrosine catabolic process
- sulfur compound metabolic process
- aromatic amino acid metabolic process

### `n0356` — TNF-driven NF-kappaB signaling

cohesion 0.367 · 6 members

- activation of NF-kappaB-inducing kinase activity
- obsolete negative regulation of NF-kappaB transcription factor activity
- tumor necrosis factor-mediated signaling pathway
- positive regulation of non-canonical NF-kappaB signal transduction
- NIK-->noncanonical NF-kB signaling
- TNF signaling

### `n0466` — Meiotic chromosome segregation and division

cohesion 0.366 · 7 members

- spindle assembly involved in female meiosis
- chromosome segregation
- male meiosis I
- meiotic cytokinesis
- cell division
- centromeric sister chromatid cohesion
- Meiotic recombination

### `n0465` — NF-kappaB and JNK activation via TAK1/IKK signaling

cohesion 0.365 · 7 members

- obsolete negative regulation of NF-kappaB transcription factor activity
- tumor necrosis factor-mediated signaling pathway
- Toll Like Receptor 10 (TLR10) Cascade
- Toll Like Receptor 5 (TLR5) Cascade
- TAK1-dependent IKK and NF-kappa-B activation
- JNK (c-Jun kinases) phosphorylation and  activation mediated by activated human TAK1
- TNF signaling

### `n0248` — HIF-mediated hypoxia response

cohesion 0.365 · 5 members

- cellular response to oxygen levels
- HALLMARK_HYPOXIA
- Regulation of gene expression by Hypoxia-inducible Factor
- Cellular response to hypoxia
- Oxygen-dependent proline hydroxylation of Hypoxia-inducible Factor Alpha

### `n0183` — Immune checkpoint restraint of T cell responses

cohesion 0.364 · 6 members

- negative regulation of T cell mediated immunity
- regulation of response to tumor cell
- negative regulation of type II interferon production
- CD4-positive, alpha-beta T cell proliferation
- negative regulation of leukocyte cell-cell adhesion
- negative regulation of CD8-positive, alpha-beta T cell activation

### `n0411` — Sex steroid and adrenal corticosteroid synthesis

cohesion 0.363 · 5 members

- androgen biosynthetic process
- estrogen biosynthetic process
- male sex differentiation
- Defective CYP11B1 causes AH4
- Defective CYP21A2 causes AH3

### `n0296` — Meiosis in gametogenesis

cohesion 0.362 · 5 members

- male meiosis I
- meiotic attachment of telomere to nuclear envelope
- centromeric sister chromatid cohesion
- HALLMARK_SPERMATOGENESIS
- Meiotic recombination

### `n0090` — Cellular osmotic and salt stress response

cohesion 0.358 · 6 members

- intrinsic apoptotic signaling pathway in response to osmotic stress
- response to salt stress
- obsolete regulation of cellular pH reduction
- cellular hyperosmotic response
- cellular response to salt
- cellular response to aldosterone

### `n0516` — Nutrient and stress sensing in growth control

cohesion 0.357 · 7 members

- cellular response to starvation
- TOR signaling
- cellular response to stress
- regulation of translation in response to stress
- MTOR signalling
- Cellular responses to stress
- Cellular response to starvation

### `n0779` — TAK1-driven MAPK and NF-kB activation

cohesion 0.357 · 7 members

- regulation of MAP kinase activity
- positive regulation of MAPK cascade
- positive regulation of JNK cascade
- Toll Like Receptor 10 (TLR10) Cascade
- Toll Like Receptor 5 (TLR5) Cascade
- TAK1-dependent IKK and NF-kappa-B activation
- JNK (c-Jun kinases) phosphorylation and  activation mediated by activated human TAK1

### `n0147` — Regulation of osteoclast formation and activity

cohesion 0.355 · 5 members

- negative regulation of tissue remodeling
- negative regulation of osteoclast differentiation
- negative regulation of bone remodeling
- osteoclast fusion
- regulation of osteoclast proliferation

### `n0799` — Forebrain regional development and neurogenesis

cohesion 0.353 · 7 members

- telencephalon development
- subpallium development
- cerebellar granular layer morphogenesis
- hippocampus development
- central nervous system neuron differentiation
- dopaminergic neuron axon guidance
- neuronal stem cell population maintenance

### `n0597` — Branching morphogenesis of tubular organs

cohesion 0.353 · 7 members

- tube development
- anatomical structure formation involved in morphogenesis
- bud elongation involved in lung branching
- respiratory system development
- dichotomous subdivision of an epithelial terminal unit
- epithelial cell proliferation involved in salivary gland morphogenesis
- regulation of morphogenesis of an epithelium

### `n0386` — Vesicular transport in the secretory and endocytic pathways

cohesion 0.352 · 7 members · checks failed: `pathways`

- post-Golgi vesicle-mediated transport
- obsolete vesicle targeting
- Golgi to plasma membrane protein transport
- plasma membrane to endosome transport
- HALLMARK_PROTEIN_SECRETION
- COPII-mediated vesicle transport
- COPI-dependent Golgi-to-ER retrograde traffic

### `n0613` — Organogenesis and body patterning by Hox and craniofacial programs

cohesion 0.352 · 7 members · checks failed: `sentence_case`

- Hox cluster IV
- facial nerve morphogenesis
- thyroid gland development
- skeletal system morphogenesis
- appendage development
- digestive system development
- face development

### `n0246` — Receptor tyrosine kinase and cytokine signalling in mesenchymal remodelling

cohesion 0.351 · 5 members

- platelet-derived growth factor receptor-alpha signaling pathway
- platelet-derived growth factor receptor-beta signaling pathway
- collagen-activated tyrosine kinase receptor signaling pathway
- interleukin-11-mediated signaling pathway
- regulation of platelet-derived growth factor receptor-beta signaling pathway

### `n0247` — Water- and fat-soluble vitamin transport and folate synthesis

cohesion 0.349 · 5 members

- folic acid-containing compound biosynthetic process
- folic acid transport
- riboflavin transport
- Defective CUBN causes MGA1
- Vitamin E transport

### `n0156` — Endoderm-derived epithelial identity and maturation

cohesion 0.349 · 3 members

- enriched in hepatocyte nuclear factors (I)
- epithelial cell maturation
- exocrine pancreas development

### `n0561` — Glycolysis and related nucleotide-cofactor metabolism

cohesion 0.347 · 6 members · checks failed: `related`

- pyruvate metabolic process
- NADPH regeneration
- nucleoside diphosphate catabolic process
- pyridine-containing compound catabolic process
- HALLMARK_GLYCOLYSIS
- Glycolysis

### `n0128` — Antibody-mediated hypersensitivity and Fc receptor signalling

cohesion 0.347 · 5 members · checks failed: `sentence_case`

- type IV hypersensitivity
- negative regulation of acute inflammatory response to antigenic stimulus
- Fc receptor signaling pathway
- Fc-epsilon receptor signaling pathway
- negative regulation of leukocyte degranulation

### `n0419` — Organogenesis of head and visceral organs

cohesion 0.346 · 6 members

- facial nerve morphogenesis
- thyroid gland development
- digestive system development
- face development
- bud elongation involved in lung branching
- epithelial cell proliferation involved in salivary gland morphogenesis

### `n0509` — cAMP-calcium signaling to CREB transcription

cohesion 0.345 · 6 members

- obsolete positive regulation of CREB transcription factor activity
- cellular response to cAMP
- response to forskolin
- Calmodulin induced events
- Ca-dependent events
- NGF-stimulated transcription

### `n0132` — Homeostatic control of progenitor cell numbers

cohesion 0.343 · 4 members

- negative regulation of cell fate commitment
- negative regulation of immature T cell proliferation in thymus
- homeostasis of number of cells within a tissue
- regulation of cell proliferation in bone marrow

### `n0433` — GTPase signalling in adhesion and vascular growth

cohesion 0.341 · 5 members

- Rap1 signalling
- G alpha (12/13) signalling events
- VEGFA-VEGFR2 Pathway
- VEGFR2 mediated cell proliferation
- RND1 GTPase cycle

### `n0653` — Myeloid cytokine production in innate immune defense

cohesion 0.341 · 6 members

- response to protozoan
- production of molecular mediator involved in inflammatory response
- macrophage cytokine production
- positive regulation of macrophage cytokine production
- myeloid leukocyte cytokine production
- FCGR3A-mediated IL10 synthesis

### `n0253` — Ubiquitin-proteasome control of regulatory protein levels

cohesion 0.340 · 6 members

- regulation of protein modification process
- regulation of protein localization to chromatin
- Autodegradation of the E3 ubiquitin ligase COP1
- Regulation of TP53 Degradation
- Ubiquitin-Mediated Degradation of Phosphorylated Cdc25A
- SPOP-mediated proteasomal degradation of PD-L1(CD274)

### `n0378` — Chemotactic leukocyte recruitment

cohesion 0.340 · 6 members

- integrin mediated leukocyte migration
- leukocyte migration involved in inflammatory response
- leukocyte migration
- positive chemotaxis
- cell chemotaxis
- positive regulation of granulocyte chemotaxis

### `n0570` — Amino acid metabolism and catabolism

cohesion 0.340 · 7 members

- amino acid metabolic process
- L-tryptophan catabolic process
- L-tyrosine catabolic process
- aromatic amino acid metabolic process
- obsolete organic acid biosynthetic process
- non-proteinogenic amino acid metabolic process
- non-proteinogenic amino acid biosynthetic process

### `n0324` — Sensory transduction across modalities

cohesion 0.339 · 7 members

- auditory receptor cell morphogenesis
- sensory perception
- response to gravity
- actin filament-based movement
- detection of stimulus
- Sensory processing of sound
- Sensory Perception

### `n0344` — Nuclear pore complex traffic and envelope dynamics

cohesion 0.338 · 6 members

- protein export from nucleus
- mitotic nuclear membrane organization
- Interactions of Vpr with host cellular proteins
- Vpr-mediated nuclear import of PICs
- IP3 and IP4 transport between cytosol and nucleus
- Nuclear Envelope (NE) Reassembly

### `n0452` — Monosaccharide interconversion and redox metabolism

cohesion 0.336 · 6 members

- galactose metabolic process
- NADPH regeneration
- glycoside metabolic process
- Fructose biosynthesis
- Essential pentosuria
- Defective GALM causes GALAC4

### `n0611` — Glycosaminoglycan and sulfate handling in connective tissue disease

cohesion 0.335 · 7 members

- HS-GAG degradation
- CS/DS degradation
- Defective SLC26A2 causes chondrodysplasias
- Defective SLC2A10 causes arterial tortuosity syndrome (ATS)
- Defective SLCO2A1 causes primary, autosomal recessive hypertrophic osteoarthropathy 2 (PHOAR2)
- MPS II - Hunter syndrome (CS/DS degradation)
- MPS VII - Sly syndrome (CS/DS degradation)

### `n0327` — Regulation of cytoplasmic translation

cohesion 0.333 · 5 members

- cytoplasmic translational elongation
- translation
- positive regulation of translation
- rescue of stalled cytosolic ribosome
- negative regulation of cytoplasmic translation

### `n0401` — Glycosaminoglycan sulfation and chondrodysplasia genetics

cohesion 0.333 · 6 members

- DS-GAG biosynthesis
- Hyaluronan metabolism
- Diseases associated with glycosaminoglycan metabolism
- Defective SLC26A2 causes chondrodysplasias
- Defective CHSY1 causes TPBS
- Defective SLC2A10 causes arterial tortuosity syndrome (ATS)

### `n0152` — Sphingomyelin metabolism and ceramide signalling

cohesion 0.333 · 4 members

- sphingomyelin catabolic process
- sphingomyelin biosynthetic process
- Sphingolipid metabolism
- TNFR1-mediated ceramide production

### `n0754` — Cellular stress response pathways

cohesion 0.331 · 7 members · checks failed: `pathways`

- cellular response to stress
- regulation of translation in response to stress
- cellular response to chemical stress
- regulation of cellular response to stress
- HALLMARK_MTORC1_SIGNALING
- HALLMARK_P53_PATHWAY
- Cellular responses to stress

### `n0517` — Apical epithelial surface organisation

cohesion 0.329 · 6 members

- microvillus assembly
- regulation of microvillus assembly
- protein transport into membrane raft
- basolateral protein secretion
- positive regulation of microvillus assembly
- HALLMARK_APICAL_SURFACE

### `n0116` — Notch signaling

cohesion 0.328 · 5 members

- Notch receptor processing
- regulation of Notch signaling pathway
- HALLMARK_NOTCH_SIGNALING
- Noncanonical activation of NOTCH3
- Negative regulation of NOTCH4 signaling

### `n0310` — Myogenic differentiation and regeneration

cohesion 0.326 · 7 members

- negative regulation of myotube differentiation
- myoblast fusion involved in skeletal muscle regeneration
- regeneration
- negative regulation of myoblast differentiation
- negative regulation of muscle organ development
- HALLMARK_MYOGENESIS
- Myogenesis

### `n0320` — Neural regulation of locomotor behavior

cohesion 0.322 · 5 members

- locomotion involved in locomotory behavior
- exploration behavior
- swimming behavior
- regulation of dopamine receptor signaling pathway
- walking behavior

### `n0025` — Attenuation of receptor tyrosine kinase signalling

cohesion 0.321 · 4 members

- negative regulation of vascular endothelial growth factor receptor signaling pathway
- negative regulation of protein tyrosine kinase activity
- Negative regulation of MET activity
- MET receptor recycling

### `n0288` — GPCR–cyclic nucleotide signalling via adenylate cyclase

cohesion 0.320 · 5 members

- cAMP biosynthetic process
- G protein-coupled receptor signaling pathway, coupled to cyclic nucleotide second messenger
- adenylate cyclase-activating serotonin receptor signaling pathway
- response to caffeine
- adenylate cyclase-activating adrenergic receptor signaling pathway

### `n0663` — B cell development and humoral immune regulation

cohesion 0.320 · 6 members

- pro-B cell differentiation
- pre-B cell differentiation
- negative regulation of B cell mediated immunity
- B cell mediated immunity
- interleukin-21 production
- Affinity selection of immunoglobulins

### `n0303` — Sensory transduction by stimulus-gated ion channels

cohesion 0.319 · 5 members

- detection of mechanical stimulus involved in sensory perception
- obsolete detection of stimulus involved in sensory perception of pain
- cellular response to pH
- Tandem pore domain halothane-inhibited K+ channel (THIK)
- Stimuli-sensing channels

### `n0323` — TP53-mediated damage response and apoptosis

cohesion 0.319 · 7 members

- negative regulation of DNA damage response, signal transduction by p53 class mediator
- intrinsic apoptotic signaling pathway by p53 class mediator
- regulation of intrinsic apoptotic signaling pathway in response to DNA damage by p53 class mediator
- negative regulation of intrinsic apoptotic signaling pathway in response to DNA damage
- Transcriptional Regulation by TP53
- Regulation of TP53 Activity through Acetylation
- Regulation of TP53 Activity through Methylation

### `n0319` — T and B lymphocyte development and signalling

cohesion 0.319 · 7 members

- T cell differentiation
- T cell differentiation via ITK and PKC
- T cell signaling and costimulation
- T cell activation (III)
- B cell development
- T cell surface signature
- positive regulation of CD8-positive, alpha-beta T cell differentiation

### `n0582` — IgE-mediated allergic effector cell activation

cohesion 0.317 · 6 members

- mast cell cytokine production
- Fc receptor signaling pathway
- Fc-epsilon receptor signaling pathway
- negative regulation of leukocyte degranulation
- eosinophil activation
- regulation of T-helper 2 cell differentiation

### `n0691` — Vitamin D and phosphate homeostasis

cohesion 0.314 · 6 members

- fat-soluble vitamin catabolic process
- phosphate ion homeostasis
- regulation of vitamin D receptor signaling pathway
- Sodium-coupled phosphate cotransporters
- Defective CYP24A1 causes HCAI
- Defective CYP27B1 causes VDDR1B

### `n0391` — Protein hydroxylation and histidine/lysine methylation

cohesion 0.314 · 5 members

- protein hydroxylation
- obsolete peptidyl-histidine modification
- Synthesis of diphthamide-EEF2
- Protein methylation
- Protein hydroxylation

### `n0659` — Calcium-calcineurin control of cardiac and muscle growth

cohesion 0.313 · 7 members

- muscle hypertrophy in response to stress
- positive regulation of muscle adaptation
- negative regulation of insulin-like growth factor receptor signaling pathway
- negative regulation of cardiac muscle tissue growth
- positive regulation of cardiac muscle contraction
- calcineurin-mediated signaling
- negative regulation of calcineurin-mediated signaling

### `n0641` — Wnt and Hedgehog signalling regulation

cohesion 0.312 · 6 members · checks failed: `sentence_case`

- Wnt signaling pathway
- negative regulation of smoothened signaling pathway
- HALLMARK_HEDGEHOG_SIGNALING
- Signaling by Hedgehog
- Negative regulation of TCF-dependent signaling by DVL-interacting proteins
- Degradation of GLI2 by the proteasome

### `n0286` — Regulation of RNA polymerase II transcription initiation

cohesion 0.309 · 5 members

- positive regulation of DNA binding
- regulation of RNA polymerase II transcription preinitiation complex assembly
- positive regulation of transcription by RNA polymerase II
- regulation of DNA binding
- positive regulation of RNA metabolic process

### `n0337` — Mitochondrial permeability and apoptotic signalling

cohesion 0.307 · 6 members

- mitochondrial transport
- mitochondrial calcium ion transmembrane transport
- negative regulation of calcium ion transport into cytosol
- negative regulation of membrane potential
- positive regulation of membrane permeability
- intrinsic apoptotic signaling pathway in response to hypoxia

### `n0243` — Regulation of vascular and epithelial growth

cohesion 0.306 · 7 members

- negative regulation of endothelial cell proliferation
- positive regulation of epithelial cell proliferation
- angiogenesis involved in wound healing
- cellular response to endogenous stimulus
- positive regulation of vasculature development
- negative regulation of vascular endothelial cell proliferation
- HALLMARK_ANGIOGENESIS

### `n0254` — Neural regulation of behaviour and physiology

cohesion 0.305 · 5 members

- behavior
- olfactory behavior
- circadian sleep/wake cycle, REM sleep
- regulation of respiratory system process
- biological process involved in intraspecies interaction between organisms

### `n0376` — TGF-beta tumour suppression via SMAD and RUNX3

cohesion 0.304 · 6 members

- regulation of anoikis
- Signaling by TGF-beta Receptor Complex in Cancer
- SMAD2/3 Phosphorylation Motif Mutants in Cancer
- TGFBR2 Kinase Domain Mutants in Cancer
- Regulation of RUNX3 expression and activity
- RUNX3 regulates BCL2L11 (BIM) transcription

### `n0624` — Nucleotide and redox cofactor metabolism

cohesion 0.300 · 7 members

- GTP biosynthetic process
- NADPH regeneration
- phosphorus metabolic process
- nucleoside diphosphate catabolic process
- nucleoside triphosphate biosynthetic process
- NAD+ metabolic process
- pyridine-containing compound catabolic process

### `n0780` — GPCR-mediated aminergic neurotransmitter signaling

cohesion 0.297 · 7 members

- cAMP catabolic process
- adenylate cyclase-activating serotonin receptor signaling pathway
- phospholipase C-activating G protein-coupled acetylcholine receptor signaling pathway
- G protein-coupled acetylcholine receptor signaling pathway
- response to amine
- positive regulation of synaptic transmission, cholinergic
- adenylate cyclase-activating adrenergic receptor signaling pathway

### `n0379` — Regulation of small GTPase signalling

cohesion 0.297 · 5 members

- small GTPase-mediated signal transduction
- negative regulation of GTPase activity
- positive regulation of small GTPase mediated signal transduction
- activation of GTPase activity
- RHO GTPases Activate Rhotekin and Rhophilins

### `n0649` — Regulation of vascular growth and matrix remodeling

cohesion 0.296 · 9 members

- negative regulation of endothelial cell proliferation
- wound healing involved in inflammatory response
- angiogenesis involved in wound healing
- negative regulation of vascular wound healing
- regulation of extracellular matrix organization
- negative regulation of extracellular matrix organization
- positive regulation of vasculature development
- negative regulation of vascular endothelial cell proliferation
- HALLMARK_ANGIOGENESIS

### `n0497` — Contractile phenotype and matrix remodeling in fibrosis

cohesion 0.294 · 7 members

- muscle contraction, SRF targets
- cytoskeletal remodeling (enriched for SRF targets)
- positive regulation of fibroblast migration
- regulation of extracellular matrix organization
- negative regulation of extracellular matrix organization
- regulation of connective tissue replacement
- Fibronectin matrix formation

### `n0368` — cAMP-dependent hormonal and nutrient signalling

cohesion 0.293 · 7 members

- carbohydrate mediated signaling
- response to glucagon
- carbon catabolite regulation of transcription
- cAMP/PKA signal transduction
- response to ketone
- cellular response to ketone
- PKA activation in glucagon signalling

### `n0261` — Neutral lipid storage and phospholipid turnover

cohesion 0.291 · 8 members

- triglyceride storage
- lipophagy
- positive regulation of phospholipid biosynthetic process
- lipid droplet formation
- negative regulation of phospholipid metabolic process
- regulation of phosphatidylcholine biosynthetic process
- Defective ABCA3 causes SMDP3
- Lipophagy

### `n0428` — eIF2α-mediated stress translation control

cohesion 0.286 · 6 members

- cellular response to stress
- regulation of translation in response to stress
- negative regulation of protein kinase activity by regulation of protein phosphorylation
- Cellular responses to stress
- PERK regulates gene expression
- Response of EIF2AK1 (HRI) to heme deficiency

### `n0621` — Oncogenic kinase fusions and mutants driving cancer

cohesion 0.276 · 7 members

- Signaling by cytosolic FGFR1 fusion mutants
- Signaling by ALK
- Signaling by MAP2K mutants
- Signaling by cytosolic PDGFRA and PDGFRB fusion proteins
- Signaling by membrane-tethered fusions of PDGFRA or PDGFRB
- Drug resistance of ALK mutants
- STAT5 activation downstream of FLT3 ITD mutants

### `n0508` — UNNAMEABLE

cohesion 0.273 · 7 members

> Most members describe NADPH oxidase-driven respiratory burst and oxidative microbial killing, but the macrophage/microglia identity pathway and the host-metabolism manipulation pathway share no such oxidative-burst theme, so any single name covering all members would be too broad or invented.

- TBA *(untitled BTM module)*
- respiratory burst involved in defense response
- neutrophil-mediated killing of gram-negative bacterium
- regulation of superoxide metabolic process
- RHO GTPases Activate NADPH Oxidases
- Events associated with phagocytolytic activity of PMN cells
- Manipulation of host energy metabolism

### `n0417` — Coronavirus-host interactions in infection and therapy

cohesion 0.273 · 7 members

- regulation of viral entry into host cell
- Potential therapeutics for SARS
- Maturation of protein E
- Maturation of protein E
- SARS-CoV-2 Infection
- Induction of Cell-Cell Fusion
- Dengue Virus-Host Interactions

### `n0335` — Tooth and bone mineralization regulation

cohesion 0.272 · 6 members

- negative regulation of bone mineralization
- phosphate ion homeostasis
- regulation of tooth mineralization
- cementum mineralization
- amelogenesis
- regulation of odontoblast differentiation

### `n0450` — Subunit assembly and editing of glutamate receptors and oligomeric proteins

cohesion 0.267 · 6 members

- protein homooligomerization
- protein tetramerization
- protein heterooligomerization
- Activation of AMPA receptors
- Ionotropic activity of kainate receptors
- mRNA Editing: A to I Conversion

### `n0523` — Phosphate transport in mineralized tissue

cohesion 0.266 · 6 members

- phosphate ion homeostasis
- proton-transporting two-sector ATPase complex assembly
- regulation of tooth mineralization
- amelogenesis
- Sodium-coupled phosphate cotransporters
- Defective SLC20A2 causes idiopathic basal ganglia calcification 1 (IBGC1)

### `n0529` — Axon-glia adhesion and myelination

cohesion 0.265 · 7 members

- central nervous system myelin formation
- axon ensheathment in central nervous system
- positive regulation of protein tyrosine kinase activity
- protein localization to axon
- NCAM signaling for neurite out-growth
- NCAM1 interactions
- Neurofascin interactions

### `n0623` — Proteasomal and ERAD protein degradation

cohesion 0.259 · 7 members

- proteasomal ubiquitin-independent protein catabolic process
- ERAD pathway
- proteasome assembly
- protein unfolding
- obsolete negative regulation of proteolysis involved in protein catabolic process
- negative regulation of ERAD pathway
- Proteasome assembly

### `n0612` — Regulated proteolytic protein maturation

cohesion 0.258 · 7 members

- protein processing
- insulin processing
- regulation of proteolysis
- peptide biosynthetic process
- Removal of aminoterminal propeptides from gamma-carboxylated proteins
- Gamma-carboxylation, transport, and amino-terminal cleavage of proteins
- Insulin processing

### `n0543` — Membrane organization and biogenesis

cohesion 0.258 · 6 members

- plasma membrane organization
- plasma membrane phospholipid scrambling
- lipid translocation
- proton-transporting two-sector ATPase complex assembly
- endoplasmic reticulum tubular network formation
- endoplasmic reticulum membrane organization

### `n0343` — Phosphatase regulation and inositol phosphate metabolism

cohesion 0.257 · 7 members

- regulation of phosphatase activity
- dephosphorylation
- positive regulation of dephosphorylation
- phosphatidylinositol dephosphorylation
- Inositol phosphate metabolism
- Synthesis of pyrophosphates in the cytosol
- Synthesis of IPs in the nucleus

### `n0572` — Metal ion and xenobiotic homeostasis

cohesion 0.257 · 6 members

- response to symbiont
- iron import into cell
- response to L-ascorbic acid
- detoxification of cadmium ion
- lactone metabolic process
- Metal ion assimilation from the host

### `n0387` — Extracellular matrix and cytoskeletal structural integrity

cohesion 0.252 · 6 members

- intermediate filament organization
- Collagen formation
- Defective SLC26A2 causes chondrodysplasias
- Defective SLC2A10 causes arterial tortuosity syndrome (ATS)
- Defective SLCO2A1 causes primary, autosomal recessive hypertrophic osteoarthropathy 2 (PHOAR2)
- Collagen chain trimerization

### `n0420` — Extracellular matrix and platelet-mediated hemostatic adhesion

cohesion 0.246 · 5 members

- cell adhesion
- regulation of peptidase activity
- Platelet degranulation
- Fibronectin matrix formation
- Regulation of FXIIa and plasma kallikrein activity

### `n0560` — Neuroendocrine regulation of growth and steroid hormones

cohesion 0.243 · 6 members

- negative regulation of glucocorticoid biosynthetic process
- regulation of growth rate
- positive regulation of insulin-like growth factor receptor signaling pathway
- positive regulation of corticotropin secretion
- regulation of steroid hormone secretion
- Defective CYP21A2 causes AH3

### `n0498` — Endocrine control of somatic growth

cohesion 0.239 · 6 members

- multicellular organism growth
- glial cell-derived neurotrophic factor receptor signaling pathway
- regulation of growth rate
- negative regulation of multicellular organism growth
- positive regulation of insulin-like growth factor receptor signaling pathway
- cellular response to peptide hormone stimulus

### `n0400` — Redox and selenium-dependent peroxide handling

cohesion 0.239 · 7 members

- response to symbiont
- regulation of hydrogen peroxide biosynthetic process
- response to L-ascorbic acid
- lactone metabolic process
- Thyroxine biosynthesis
- Metabolism of ingested H2SeO4 and H2SeO3 into H2Se
- Selenocysteine synthesis

### `n0600` — Membrane protein sorting and surface antigen expression

cohesion 0.237 · 6 members

- protein transport into membrane raft
- basolateral protein secretion
- HALLMARK_APICAL_SURFACE
- Defective RHAG causes regulator type Rh-null hemolytic anemia (RHN)
- Defective SLC4A1 causes hereditary spherocytosis type 4 (HSP4),  distal renal tubular acidosis (dRTA) and dRTA with hemolytic anemia (dRTA-HA)
- Blood group systems biosynthesis

### `n0756` — Phagocyte oxidative and nitrosative signalling

cohesion 0.235 · 7 members

- TBA *(untitled BTM module)*
- TBA *(untitled BTM module)*
- respiratory burst involved in defense response
- regulation of superoxide metabolic process
- cellular response to reactive nitrogen species
- Metabolism of nitric oxide: NOS3 activation and regulation
- RHO GTPases Activate NADPH Oxidases

### `n0662` — Steroid hormone response and reproductive tissue programming

cohesion 0.231 · 6 members

- inner cell mass cell differentiation
- decidualization
- cellular response to progesterone stimulus
- HALLMARK_ANDROGEN_RESPONSE
- HALLMARK_ESTROGEN_RESPONSE_EARLY
- HALLMARK_ESTROGEN_RESPONSE_LATE

### `n0573` — Organ-specific embryonic morphogenesis

cohesion 0.226 · 6 members

- TBA *(untitled BTM module)*
- post-embryonic animal morphogenesis
- optic nerve development
- embryonic camera-type eye morphogenesis
- diaphragm development
- eyelid development in camera-type eye

### `n0532` — GTPase cycle regulation and effector signalling

cohesion 0.226 · 6 members

- TBA *(untitled BTM module)*
- regulation of localization (GO)
- negative regulation of GTPase activity
- activation of GTPase activity
- RHO GTPases Activate Rhotekin and Rhophilins
- RHOBTB3 ATPase cycle

### `n0755` — Neurotrophin-driven neuronal growth and survival signalling

cohesion 0.218 · 7 members

- neuromuscular junction development
- peripheral nervous system axon regeneration
- neuron projection regeneration
- neurotrophin production
- positive regulation of protein tyrosine kinase activity
- Cell death signalling via NRAGE, NRIF and NADE
- p75NTR recruits signalling complexes

### `n0694` — Neuroendocrine control of growth and appetite

cohesion 0.210 · 6 members

- TBA *(untitled BTM module)*
- glial cell-derived neurotrophic factor receptor signaling pathway
- negative regulation of multicellular organism growth
- eating behavior
- cellular response to leptin stimulus
- positive regulation of corticotropin secretion

### `n0790` — Growth hormone, IGF and HPA axis signalling

cohesion 0.204 · 7 members

- negative regulation of glucocorticoid biosynthetic process
- multicellular organism growth
- regulation of growth rate
- positive regulation of insulin-like growth factor receptor signaling pathway
- positive regulation of corticotropin secretion
- cellular response to peptide hormone stimulus
- response to insulin-like growth factor stimulus

### `n0601` — Regulation of intracellular protein trafficking

cohesion 0.187 · 6 members

- TBA *(untitled BTM module)*
- negative regulation of intracellular transport
- regulation of protein transport
- regulation of protein localization to cell surface
- RHOBTB GTPase Cycle
- Regulation of NPAS4 gene expression

### `n0518` — UNNAMEABLE

cohesion 0.180 · 6 members

> The members span unrelated themes—proteolytic maturation and its regulation, peptide biosynthesis, xenobiotic/herbicide and phytoestrogen responses, and copulation physiology—with no single specific process common to all beyond generic biology.

- copulation
- response to herbicide
- protein processing
- regulation of proteolysis
- response to genistein
- peptide biosynthetic process

### `n0640` — UNNAMEABLE

cohesion 0.160 · 6 members

> The members span embryo lineage specification, endometrial/decidual biology, hormone response signalling, general tissue maturation, and erythroid biology, sharing no single specific process beyond generic developmental physiology.

- inner cell mass cell differentiation
- response to erythropoietin
- decidualization
- primitive erythrocyte differentiation
- cellular response to progesterone stimulus
- anatomical structure maturation

