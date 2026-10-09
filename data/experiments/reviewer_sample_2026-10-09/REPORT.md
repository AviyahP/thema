# Reviewer plausibility review of thema_L_repair (9 Oct 2026)

*Written by the reviewer (Claude, claude.ai project) at Aviyah's request. EXPLORATORY: LLM-judge assessments, not declared tests and not reproduced by ccode. All raw files are in this folder: sample.json, judged.json (round 1), tba_rejudge.json + big_all.json + round2.json (round 2), round3.json (round 3), rubric.md / rubric2.md / rubric3.md.*

## Method

- **Build judged:** `data/ontology/v0.4-leaves/thema_L_repair` (8,793 themes over the 5,559 leaves; cal8 floors, stale-merge fix, chain collapse at 90%).
- **Sample:** 10% of themes per size band, seed 20261009: 879 themes. "Level" means size band; the DAG has no fixed depth levels.
- **Judges:** ten blinded subagents, given member names only (up to 15 random members per theme), with rubric.md (coherent / partial / incoherent plus a label).
  - Names are never used in construction, so this is an independent check.
  - The reviewer hand-checked 17 verdicts and agreed; if anything the judges were slightly strict.
- **Round 2a:** the 83 BTM modules named "TBA" have no names. Every sampled theme containing one (102 themes) was re-judged with each TBA module's generated description (from pathway_descriptions.tsv) and its first genes (rubric2.md).
- **Round 2b:** ALL 42 themes over 100 members were judged, with 40 random members shown each (rubric2.md; for very large themes, "coherent" means one recognisable broad area).
- **Round 3:** all 99 remaining "partial" verdicts were re-judged with one question (rubric3.md): is there a recognised, specific biological link between the sub-themes (a shared mechanism, enzyme/cofactor, cell type or physiological axis)?
  - umbrella = linked broader theme;
  - core_plus_misfits = one coherent theme plus misfits;
  - mixture = no link.

## Round 1 (names only)

| band | n | coherent | partial | incoherent |
|---|---|---|---|---|
| 3-5 | 48 | 46 (96%) | 1 | 1 |
| 6-10 | 212 | 193 (91%) | 17 | 2 |
| 11-20 | 436 | 380 (87%) | 52 | 4 |
| 21-50 | 157 | 123 (78%) | 34 | 0 |
| 51-100 | 21 | 14 (67%) | 7 | 0 |
| sampled 101+ | 5 | see round 2b | | |
| **all** | 879 | 759 | 112 | 8 |

## Round 2a: TBA modules shown with their description and genes

Old -> new verdict counts (102 themes): coherent->coherent: 69, coherent->partial: 1, incoherent->coherent: 1, incoherent->incoherent: 5, incoherent->partial: 1, partial->coherent: 21, partial->partial: 4

**Of the 29 that had been partial or incoherent, 22 became coherent.** The unnamed modules are mostly on-theme once their biology is shown.

## Round 2b: all 42 themes over 100 members

| size | verdict | label | reason |
|---|---|---|---|
| 2614 | incoherent | Mixed development, signaling, chromatin, cytoskeleton | Unrelated areas: development, cancer signaling, telomeres, metabolism, cytoskeleton. |
| 2586 | incoherent | Mixed development, immune and signaling processes | Unrelated areas: organ morphogenesis, immunity, coagulation, synaptic, sperm, chromatin. |
| 2527 | incoherent | Mixed signaling, development and physiology | Spans metabolism, ion channels, vascular, neural, bone, hormones, drug resistance |
| 2261 | incoherent | Mixed metabolism, signaling, mitochondria, neuro | Grab-bag of metabolic disorders, GPCR/calcium signaling, mitochondria, neuronal and secretion terms. |
| 2138 | incoherent | Mixed immune, cell cycle and stress signaling | Immune signaling mixed with DNA repair, cell cycle, folding, RNA modification, development. |
| 1751 | coherent | Development, cell adhesion, ECM and migration |  |
| 1444 | partial | Nuclear and mitochondrial housekeeping machinery | Genome/RNA/mitochondrial upkeep mixed with inositol phosphates, vesicle traffic, autophagy, viral budding. |
| 1405 | coherent | Metabolism and solute transport, incl. inborn errors |  |
| 1047 | partial | DNA damage, p53 and cell-cycle stress | About a third is translation, tRNA, protein modification, mitochondrial |
| 838 | coherent | Small-molecule metabolism, transporters, inborn errors |  |
| 826 | coherent | Innate and adaptive immune responses |  |
| 800 | coherent | Nuclear DNA/RNA processing and maintenance |  |
| 400 | partial | RNA processing, translation and viral replication | RNA/gene-expression core mixed with viral assembly/budding and odd enzymatic terms. |
| 373 | coherent | DNA repair, replication and cell cycle |  |
| 294 | coherent | Transcription, RNA processing and translation |  |
| 211 | coherent | RTK-RAS-MAPK/PI3K signaling and oncogenic mutants |  |
| 201 | coherent | RNA processing, transcription and translation |  |
| 180 | coherent | Glycosylation, glycosaminoglycans and CDG disorders |  |
| 179 | coherent | DNA repair and replication stress response |  |
| 170 | coherent | RNA processing, modification and translation |  |
| 167 | coherent | Mitotic and meiotic cell cycle, replication |  |
| 151 | coherent | Axon guidance, neurotrophins and myelination |  |
| 147 | coherent | Glycosylation and glycan/GAG metabolism disorders |  |
| 145 | coherent | RNA processing, ribosome biogenesis, translation |  |
| 139 | partial | Hemostasis, platelets and eicosanoid lipid mediators | Two related themes mixed: coagulation/platelets and eicosanoid/resolvin biosynthesis. |
| 138 | coherent | Receptor tyrosine kinase signaling (FGFR/ERBB/MET, PI3K/RAS) |  |
| 135 | coherent | Reproduction, gametogenesis and early embryo |  |
| 130 | coherent | DNA repair (HR, MMR, TLS, NER) |  |
| 124 | coherent | Insulin secretion, adipocyte and lipid energy metabolism |  |
| 123 | coherent | Branching epithelial organ development |  |
| 121 | coherent | Reproduction: germline meiosis, gonad, placenta |  |
| 114 | coherent | Mitosis: centrosome, spindle, nuclear pore |  |
| 114 | coherent | Lipoprotein and cholesterol metabolism (APOE-related) |  |
| 114 | partial | Mitochondrial respiration, heme, Fe-S clusters | About a third is cytosolic tRNA/RNA modification and diphthamide |
| 108 | coherent | Axon guidance and neural/glial development |  |
| 108 | coherent | RNA processing, splicing, ribosome biogenesis |  |
| 105 | coherent | Proteostasis: chaperones, ubiquitin, heat shock |  |
| 104 | coherent | Viral infection and host-virus interactions |  |
| 104 | coherent | Branching organ and mesenchyme development |  |
| 102 | coherent | Glycosylation pathways and glycosylation disorders |  |
| 102 | coherent | Cholesterol, lipoprotein and bile acid homeostasis |  |
| 102 | partial | Mitochondrial OXPHOS and mitochondrial gene expression | About a quarter is nuclear/cytosolic tRNA, snRNA, rRNA modification |

## Round 3: re-judging all 99 partials

- sample partials: {'umbrella': 74, 'core_plus_misfits': 15, 'mixture': 4}
- big partials: {'mixture': 2, 'umbrella': 4}

### All mixtures (no recognised link)

- Broad genome maintenance and stress grab-bag (misfits about 0.6): GPER1 signaling; tRNA transport; 'de novo' protein folding; cellular detoxification of aldehyde
- Heterogeneous housekeeping: DNA, RNA, mitochondria, trafficking (misfits about 0.7): Budding and maturation of HIV virion; clathrin coat assembly; meiotic mismatch repair; Mitochondrial tRNA aminoacylation
- Osmotic stress, magnesium transport, oligomerisation (misfits about 0.6): protein hexamerization; protein homotetramerization; magnesium ion transport
- MET/RON and TGF-beta receptor signalling (misfits about 0.4): TGFBR3 regulates FGF2 signaling; SMAD2/3 MH2 Domain Mutants in Cancer
- Heterogeneous BTMs plus nucleocytoplasmic transport (misfits about 0.5): enriched for TF motif PAX3; BTM M32.5 (unnamed module)
- TFAP2 and RUNX transcription factor programs (misfits about 0.35): Activation of the TFAP2 (AP-2) family of transcription factors; TFAP2 (AP-2) family regulates transcription of other transcription factors

### All core-plus-misfits

- Non-vesicular lipid transfer at ER-Golgi contacts (misfits about 0.33): WNT ligand biogenesis and trafficking; LGK974 inhibits PORCN; RAB GEFs exchange GTP for GDP on RABs; RAB geranylgeranylation
- Stress granules and mRNA stabilisation (misfits about 0.25): diadenosine polyphosphate catabolic process; GDP metabolic process; PML body organization
- Cellular zinc transport and homeostasis (misfits about 0.33): disaccharide catabolic process; Digestion of dietary carbohydrate; Lactose synthesis; Intestinal saccharidase deficiencies
- Transcription and chromatin housekeeping modules (misfits about 0.3): cytosolic ribosome assembly; inner cell mass cell proliferation; BTM M248 (unnamed module); enriched for ubiquitination
- OTU-family deubiquitination of K48/K11 chains (misfits about 0.15): PKR-mediated signaling
- Ubiquitin conjugation and deubiquitination (misfits about 0.15): PKR-mediated signaling; positive regulation of protein binding
- Receptor PTP regulation of protein phosphorylation (misfits about 0.2): GDP metabolic process; Invadopodia formation
- MET/EGFR signalling via PTK6 and STAT3 (misfits about 0.2): positive regulation of hippo signaling; Signaling by Hippo; YAP1- and WWTR1 (TAZ)-stimulated gene expression
- Stress granules and mRNA stabilisation (misfits about 0.25): diadenosine polyphosphate catabolic process; GDP metabolic process; PML body organization
- Sphingolipid synthesis, transfer and turnover (misfits about 0.1): obsolete peptidyl-cysteine modification; obsolete amide biosynthetic process
- Nutrient/stress repression of rRNA transcription (misfits about 0.15): TFAP2A acts as a transcriptional repressor during retinoic acid induced cell differentiation
- Ceramide signalling in apoptosis (misfits about 0.4): cellular response to insulin-like growth factor stimulus; response to insulin-like growth factor stimulus; cellular response to peptide
- Organelle acidification and SLC ion transporter disorders (misfits about 0.1): Post-translational protein phosphorylation
- Protein lipidation (palmitoylation, prenylation) (misfits about 0.3): glycolipid transport; ceramide 1-phosphate transport; Glycosphingolipid transport
- Small GTPase regulation in lymphocytes (misfits about 0.2): negative regulation of peptidyl-threonine phosphorylation; regulation of localization (GO)

### Umbrella themes and their stated links (all)

- **HPA-axis glucocorticoid secretion and circadian clock**: SCN/BMAL1:CLOCK clock gates the diurnal ACTH-cortisol rhythm, and glucocorticoids in turn reset peripheral clocks
- **IGF signalling in bone and cartilage mineralization**: GH/IGF-1 via IGF1R drives growth-plate chondrocyte maturation and osteoblast bone mineralization
- **Protein lysine/arginine acetylation and methylation**: lysine residues (histones, p53) are competing substrates for acetyltransferases and methyltransferases; methionine supplies the SAM methyl donor
- **PI3K-AKT-PTEN and inositol pyrophosphate signalling**: IP6K-made inositol pyrophosphate IP7 competes with PIP3 for the AKT PH domain; NUDT/DIPP hydrolases degrade both diphosphoinositol polyphosphates and diadenosine polyphosphates
- **Histone acetylation and nucleosome/CENP-A assembly**: HAT1 acetylates new histone H4 K5/K12 before replication-dependent deposition; histone chaperone-mediated nucleosome and CENP-A deposition
- **PTEN-PI3K regulation and inositol pyrophosphates**: lncRNA/ceRNA control of PTEN translation and IP7 competition with PIP3 for AKT both tune PI3K-AKT output; NUDT hydrolases degrade PP-InsPs and Ap(n)A
- **TGF-beta control of fibroblasts, ECM and miRNAs**: TGF-beta/SMAD2/3 drives fibroblast ECM programmes and binds the Drosha/p68 complex to promote pri-miR-21 processing; miRNAs (miR-21, miR-29) regulate fibrosis
- **Thyroid hormone and large neutral amino acid transport**: T3/T4 cross membranes via LAT1/LAT2 (SLC7A5/SLC7A8) and MCT10 (SLC16A10), the same transporters for leucine, isoleucine, phenylalanine and tryptophan
- **MAPK and IL-6 signalling with DUSP feedback**: immediate-early DUSPs (e.g. DUSP1) dephosphorylate Thr/Tyr on ERK/p38/JNK as negative feedback; IL-6/STAT3 and AP-1/NR4A are co-induced immediate-early programmes
- **Ca2+-activated scrambling, mechanosensing and ATP release**: mechanical/osmotic stress (PIEZO1) raises Ca2+, activating TMEM16F/ANO6 scrambling, blebbing and membrane repair, and ATP release via connexin/pannexin channels hydrolysed by NTPDases
- **Fat-soluble vitamins, steroid hormones, mineral homeostasis**: vitamin D/PTH/NaPi-II axis controls phosphate for bone and enamel, vitamin K gamma-carboxylates osteocalcin/MGP, and vitamin D is a secosteroid hydroxylated by CYP enzymes like sex steroids
- **Transcriptional control of the cadherin switch**: EMT TFs (SNAIL/ZEB/TWIST) bind E-box promoters to repress CDH1 and induce CDH11; ID proteins block DNA binding of E-proteins
- **Stromal fibroblast ECM and adhesion programme**: RAS-ERK-induced FOSL1/AP-1 drives ECM, MMP and adhesion genes in mesenchymal/stromal cells
- **TGF-beta/activin receptor signalling and SMAD partners**: RUNX3 and FOXO are SMAD3 partners that together induce CDKN1A (p21) in TGF-beta growth arrest; TGFBR3 and follistatin modulate TGF-beta/activin ligand access
- **Scavenger receptors: efferocytosis and oxLDL uptake**: CD36, SR-A and SR-BI recognise oxidised phospholipid/PS on apoptotic cells and on oxLDL, driving both corpse clearance and foam-cell formation
- **Pancreatobiliary and endocrine lineage development**: shared PDX1/SOX9/NOTCH-HES1 progenitor programme gives ductal, biliary and NEUROG3+ endocrine lineages
- **p53/mTORC1 control of glycolysis and PPP**: p53 target TIGAR lowers fructose-2,6-bisphosphate to divert glucose from glycolysis to the pentose-phosphate shunt; mTORC1/PGC-1alpha regulate glycolytic and oxidative genes
- **tRNA processing and mitochondrial gene expression**: mitochondrial RNase P (TRMT10C/HSD17B10/PRORP) and ELAC2 excise mt-tRNAs punctuating polycistronic mt transcripts; tRNA processing/modification enzymes are shared or dual-localised
- **Pluripotency, early lineages and placentation**: OCT4/SOX2/NANOG maintain ICM/epiblast and primordial germ cells while repressing CDX2-driven trophectoderm that forms trophoblast/placenta
- **Myelination and node of Ranvier organisation**: neurofascin/NrCAM/L1-CAMs anchor to ankyrin-G at nodes and paranodes; Schwann cell connexin-32 gap junctions in myelin (CMTX)
- **Renin-angiotensin, vasopressin and osmotic fluid balance**: angiotensin II stimulates aldosterone and vasopressin release to retain salt and water; natriuretic peptide cGMP opposes; renal epithelial chloride transport executes it
- **Endocrine and neuroendocrine organ development**: shared neuroendocrine TFs (PAX6, ISL1, NEUROD1, NKX2-2) in islets, adenohypophysis and forebrain; pancreas and stomach arise from foregut endoderm
- **Ca2+/mechanical membrane signals: ATP release, PS exposure**: Apoptotic and stressed cells release ATP via pannexin-1 as a P2Y 'find-me' signal (hydrolysed by NTPDases) and expose PS via TMEM16F/ANO6 Ca2+-activated scrambling as an 'eat-me' signal; PIEZO1 Ca2+ influx under shear drives both ATP release and TMEM16F scrambling
- **Vitamin A and D hormone metabolism**: Both are fat-soluble vitamin-derived nuclear-receptor ligands (RAR/VDR, each heterodimerising with RXR) whose activation/inactivation is controlled by cytochrome P450s (CYP27B1/CYP24A1 for calcitriol, CYP26 for retinoic acid)
- **Axonal ER shaping and microtubule organelle transport**: Hereditary spastic paraplegia/motor neuron genes: atlastin (ER fusion), REEP1 (membrane bending), spastin (microtubule severing, endosome tubulation) and KIF5A/Miro (RHOT) mitochondrial axonal transport maintain long corticospinal axons
- **Epithelial polarized trafficking, CFTR and organelle acidification**: V-ATPase-driven Golgi/endosomal acidification is required for polarized apical/basolateral sorting of cargo such as CFTR; CFTR/anion conductance supplies counter-ions for luminal acidification and drives transepithelial fluid transport
- **PLP-dependent sulfur amino acid metabolism and cofactors**: Pyridoxal phosphate is the cofactor of CBS/CSE in transsulfuration and H2S production and of serine dehydratase; sulfide oxidation to sulfate ends with molybdenum-cofactor sulfite oxidase
- **Hepatic mitochondrial amino acid and amine catabolism**: Threonine and choline catabolism (via betaine/sarcosine) yield glycine that mitochondrial glycine N-acyltransferase uses to conjugate benzoate/salicylate; choline and carnitine are trimethylammonium compounds, histidine/choline feed one-carbon pools
- **Cellular Na+/K+ and pH homeostasis**: Na+/K+-ATPase (cardiac glycoside target) sets the Na+ gradient that drives NHE proton extrusion; carbonic anhydrase supplies H+/HCO3-; V-ATPase acidifies organelles with NHE6/9 as counter-leak
- **Neural crest-derived enteric and sympathoadrenal development**: RET/GDNF and endothelin-3/EDNRB are jointly required for enteric neural crest migration (Hirschsprung disease); neural crest also forms sympathetic ganglia and adrenal medulla making catecholamines
- **Nephron glomerular and brush-border epithelial development**: Glomerular filtration barrier (podocyte nephrin, mesangial cells) and proximal-tubule brush border are nephron epithelial specialisations; podocalyxin/NHERF2/ezrin apical actin scaffold is shared by podocytes and microvilli
- **Acetyl-CoA production with NAD+ and CoA cofactors**: Pyruvate dehydrogenase requires CoA (from pantothenate) and NAD+ (from salvage), and its lipoate cofactor is made by mitochondrial fatty acid synthesis from malonyl-CoA producing octanoyl chains
- **HPA stress axis and neuroendocrine behaviour**: Hypothalamic CRH-ACTH-cortisol axis with glucocorticoid feedback mediates stress responses, and hypothalamic neuropeptides (CRH, vasopressin, oxytocin) modulate fear, aggression, drinking, wakefulness and social/parental behaviour
- **TCA cycle metabolites and HIF oxygen sensing**: 2-oxoglutarate is the co-substrate of PHD prolyl hydroxylases that degrade HIF-alpha; succinate, fumarate and 2-hydroxyglutarate inhibit PHDs causing pseudohypoxia
- **MET and ERBB2 receptor tyrosine kinase signalling**: MET and ERBB2 share adaptors GRB2, GAB1 and GRB7 to activate PI3K/AKT, RAS and PTK2/PTK6 downstream
- **Neuropeptide GPCR control of sleep and reproduction**: Hypothalamic neuropeptides acting on GPCRs: orexin drives wakefulness/REM regulation, oxytocin (and relaxin) control uterine contraction, parturition, mating and maternal behaviour
- **Mitochondrial adenine nucleotide and NAD+ handling**: Mitochondrial SLC25 carriers exchange ATP/ADP (ANT) and import NAD+ (SLC25A51); ANT is coupled to mitochondrial creatine kinase for phosphocreatine and is targeted by HIV Vpr and influenza PB1-F2 to trigger MOMP
- **TYK2-dependent IFN and IL-10/IL-12 family cytokines**: Type III IFNs (IL-28/29) belong to the IL-10 family sharing IL-10R2; type I IFN, IL-10 family and IL-12/IL-23 receptors all signal through TYK2
- **Nucleotide and inositol pyrophosphate phosphoanhydride turnover**: Nudix DIPP hydrolases (NUDT3/4/10/11) cleave both diphosphoinositol polyphosphates and diadenosine polyphosphates; IP6K/PPIP5K and NDPK/adenylate kinase transfer ATP phosphoanhydride groups
- **Limbic synaptic transmission and behaviour**: Glutamatergic/GABAergic synapses in amygdala and hippocampus underlie exploratory, anxiety-like and psychomotor behaviours; kainate receptor overactivation causes hippocampal excitotoxic neuron death; NCAM regulates these synapses
- **Transepithelial anion and water transport**: SLC26 anion exchangers (SLC26A3/A6/A4) create osmotic gradients that aquaporins follow in gut, kidney proximal tubule and inner ear; SLC26A3 loss causes watery chloride diarrhoea; lens transparency relies on AQP0 and gap-junction fluid circulation
- **Mitochondrial gene expression and respiratory chain biogenesis**: Mitochondrial transcription/translation produce core OXPHOS subunits whose assembly needs heme A, Fe-S clusters and ubiquinone cofactors made by the same organelle
- **Hypothalamic neuropeptide GPCR control of feeding/sleep**: Hypothalamic peptide hormones (CRH, relaxin-3, calcitonin/amylin, somatostatin) act via Gs/Gi-coupled GPCRs that tune cAMP/PKA in hypothalamic circuits governing feeding, sleep/wake, stress and reproductive behaviour
- **Specialised modifications of translation machinery**: Unusual residue/nucleotide modifications of translation components tune elongation and termination fidelity: hypusine on eIF5A, diphthamide on eEF2 (diphtheria toxin target), wybutosine in tRNA-Phe, selenocysteine tRNA, and 2-oxoglutarate oxygenase hydroxylation of eRF1/RPS23 affecting readthrough
- **Phosphate/vitamin D axis and mitochondrial P450s**: Mitochondrial cytochrome P450s (CYP11A1 for pregnenolone/glucocorticoids, CYP27B1/CYP24A1 for vitamin D) share the adrenodoxin reductase-adrenodoxin (NADPH-ferredoxin) electron chain; vitamin D, PTH and FGF23-FGFR (FAM20C-phosphorylated) regulate Na+/Pi cotransport and mineralisation
- **Golgi O-glycosylation of dystroglycan and proteoglycans**: Both are protein O-glycosylation pathways building extracellular-matrix-binding glycans; LARGE1 makes xylose-glucuronic acid matriglycan on alpha-dystroglycan, analogous to the xylose-initiated GAG linkage region (XYLT/B4GALT7/B3GALT6/B3GAT3) of proteoglycans
- **Immediate-early AP-1 response in liver regeneration**: TNF/NF-kB and growth-factor/RAS signals induce immediate-early genes (FOS/JUN AP-1, NR4A, EGR1) in the priming phase of liver regeneration, driving hepatocyte proliferation and survival
- **MECP2 chromatin regulation and Rett-like neurobehaviour**: MECP2 binds 5mC/5hmC and recruits NCoR/SMRT-HDAC3 repressors; its loss (Rett syndrome, mouse models) produces motor, sensory-gating (prepulse inhibition), vocalisation and striatal/amygdala phenotypes
- **Hypothalamic stress axis and motivated behaviour**: Hypothalamic neuropeptides (CRH driving ACTH-cortisol in the HPA axis, orexin, QRFP/NPFF) act via GPCRs to coordinate stress responses, arousal/sleep and reproductive/parental behaviour
- **Class B GPCR-cAMP control of growth hormone axis**: GHRH acts via a glucagon-family class B GPCR (Gs-cAMP) to drive GH secretion, opposed by somatostatin (Gi), with GH-IGF1 setting growth rate; calcitonin/CGRP/amylin receptors are related class B GPCRs signalling via cAMP
- **Proteasome, antigen presentation and PD-L1 turnover**: Proteasome generates MHC-I peptides for CD8 T cell recognition (incl. cross-presentation), and proteasomal/ERAD degradation of PD-L1 (GSK3B, SPOP, AMPK) controls T cell antitumour responses
- **Ocular vascular development and barrier formation**: Norrin/WNT-FZD4-LRP5 signalling builds retinal vessels and the blood-retina/blood-brain barrier, and macrophage WNT7b-induced endothelial apoptosis regresses the hyaloid vasculature; eye development depends on these vessels
- **Actin-bundle apical protrusions: microvilli and stereocilia**: Brush border microvilli and hair cell stereocilia are parallel actin bundle protrusions built by homologous machinery (Usher complex harmonin/MYO7, protocadherin links, espin); podocyte foot processes are polarised actin-based epithelial specialisations
- **Microglial clearance of apoptotic neurons**: Microglia recognise phosphatidylserine on apoptotic neurons (e.g. after kainate excitotoxicity) via receptors such as TREM2/MERTK and engulf them (efferocytosis), with activation/proliferation coupled to clearance
- **Epithelial-mesenchymal branching organ morphogenesis**: Shared FGF10-FGFR2b, SHH and BMP4 epithelial-mesenchymal signalling drives branching of lung, mammary, prostate and pancreatic buds; hedgehog/androgen signalling also patterns Leydig cells and male genitalia
- **Adipocyte lipolysis, glycerol export and thermogenesis**: Cold-induced thermogenesis drives adipocyte lipolysis releasing fatty acids (FATP transport, UCP1 fatty-acid cycling, PM20D1 N-acyl amino acids like oleoyl-Phe) and glycerol via aquaglyceroporin AQP7/AQP9 (which also carry urea); HCA receptors feed back to inhibit lipolysis
- **Craniofacial and limb morphogenesis**: Limb buds and facial prominences share outgrowth/patterning signals (SHH, FGF8, BMP, MSX/DLX/TBX) and are co-affected in acrofacial syndromes
- **AID/APOBEC cytidine deamination and uracil repair**: AID/APOBEC cytidine deaminases convert C to U in Ig genes (somatic hypermutation), retroviral minus-strand DNA (APOBEC3 restriction of HIV) and apoB mRNA (APOBEC1 editosome); resulting uracils are processed by base excision/mismatch repair
- **Host RNA processing, translation and viral replication**: Viruses (HIV, SARS-CoV-2) depend on host transcription (Tat-P-TEFb elongation), RNA processing, nuclear export and translation machinery, which form one gene-expression system with rRNA/tRNA/mRNA processing
- **Mitochondrial gene expression and OXPHOS**: mtDNA-encoded OXPHOS subunits require mitochondrial transcription, modified mt-tRNA/rRNA and mitoribosome translation; several tRNA-modifying enzymes (e.g. PUS1, TRMT family) act in both nuclear and mitochondrial tRNA
- **Cation channels, transporters and cell-volume osmoregulation**: Tetrameric K+ and TRP channels plus Na/K/Cl cotransporters set cell volume; myo-inositol is an osmolyte; claudin paracellular pathway reabsorbs Mg2+/Na+
- **Hypothalamic control of feeding, stress and growth**: Leptin acts on arcuate POMC/AgRP neurons controlling feeding and the HPA (CRH-ACTH-cortisol) axis; relaxin-3/RXFP3 is a hypothalamic orexigenic, stress-modulating peptide
- **HPA stress axis with growth and feeding control**: CRH-R1 (Gs-cAMP/PKA) drives ACTH and glucocorticoid release; glucocorticoids/CRH suppress GH-IGF growth and food intake
- **Hypothalamic appetite and POMC-HPA regulation**: POMC is cleaved to alpha-MSH (MC4R satiety) and ACTH (cortisol); leptin acts on POMC neurons; POMC/ACTH defects cause obesity and adrenal insufficiency
- **Endocrine FGF-Klotho and vitamin D axis**: FGF23 via FGFR1c/alpha-Klotho represses CYP27B1 and induces CYP24A1, while calcitriol induces FGF23; FGF19/21 use betaKlotho with FGFR4/FGFR1c
- **Sulfur/selenium amino acid and glutathione metabolism**: PLP-dependent CBS/CTH transsulfuration makes cysteine for glutathione (GST aflatoxin conjugation) and Moco sulfur; SeMet/Sec use the same enzymes
- **Immediate-early stress gene response**: UV, PMA, NO and TNF converge on p38/JNK/NF-kB to induce immediate-early genes (FOS, JUN, EGR1, NR4A, ATF3)
- **Thyroid hormone activation and selenoproteins**: Iodothyronine deiodinases DIO1-3 are selenocysteine enzymes needing UGA recoding; GPx selenoproteins clear H2O2 used by thyroid peroxidase
- **Eye and inner-ear sensory epithelium development**: Usher genes (MYO7A, USH1C, CDH23, PCDH15) build hair-cell stereocilia (modified microvilli) and photoreceptor structures; shared retina/hair-cell degeneration
- **Magnesium transport via tight junctions and channels**: Claudin-16/19 tight junctions form a paracellular Mg2+ pore in the thick ascending limb; tetrameric TRPM6/7 carry transcellular Mg2+
- **IL-1 family and IL-17 inflammatory axis**: IL-18/IL-36 (IL-1 family) promote Th17/IL-17 production and IL-38 antagonizes IL-36R; IL-17 induces CXCL1 (psoriasis axis)
- **Y-linked spermatogenesis and histone crotonylation**: Y-linked testis-specific CDY genes (and paralog CDYL) are crotonyl-CoA hydratases that regulate histone crotonylation in spermatogenesis
- **HGF/MET and Hippo-YAP growth control**: HGF/MET mitogenic signalling and Hippo-YAP density sensing jointly control hepatocyte proliferation and liver size in regeneration
- **Angiogenesis and vascular wound repair**: VEGF/VEGFR2 drives endothelial migration and tube formation in wound neovascularization, with fibroblast FGF/TGF-beta2 repair signals
- **P450/lipoxygenase oxidation of fatty acids and eicosanoids**: CYP4/CYP2 omega-hydroxylases and epoxygenases, TBXAS1 (CYP5A1) and LOX/hepoxilin pathways oxidize arachidonate; CYP4F22 and FATP4 supply skin-barrier lipids
- **SUMOylation and nuclear pore complex**: RanBP2/Nup358 is a SUMO E3 anchoring SUMO-RanGAP1:UBC9 at the NPC; SENP desumoylases localize to nuclear pores
- **Cholinergic transmission and K+ channel control**: Nicotinic AChRs mediate neuromuscular transmission; muscarinic M2 activates GIRK and Gq-coupled muscarinic receptors inhibit TASK channels
- **Platelet activation, coagulation and eicosanoids**: Platelet cPLA2 releases arachidonate for COX-1/TBXAS1 thromboxane A2 and 12-LOX products, amplifying platelet-driven coagulation

## Final verdict on the 10% sample (879)

{'umbrella': 75, 'coherent': 779, 'core_plus_misfits': 15, 'incoherent': 6, 'mixture': 4}

- coherent + umbrella = 854 of 879 (97.2%)
- core_plus_misfits = 15; incoherent + mixture = 10

## Examples of coherent themes (round 1, random)

- PTEN/PI3K/AKT signalling regulation (6-10, 8 members)
- Appetite and feeding regulation (11-20, 18 members)
- RNA Pol I/III rRNA transcription (11-20, 12 members)
- Glycogen metabolism and storage diseases (11-20, 19 members)
- SLC26/SLC12 anion transport (6-10, 9 members)
- Aquaporin water and glycerol transport (6-10, 6 members)
- Regulation of glycolysis and glucose metabolism (11-20, 16 members)
- Purine nucleotide metabolism and thiopurines (11-20, 17 members)
- miRNA-mediated gene silencing (3-5, 4 members)
- mTORC1 nutrient sensing (6-10, 8 members)
- Cardiac contraction and calcium regulation (11-20, 15 members)
- PI3K/AKT/PTEN signaling (6-10, 6 members)
- Wnt signaling (21-50, 30 members)
- B cell development and memory (21-50, 34 members)
- Integrated stress response and UPR translation control (6-10, 10 members)
- RNA Pol III and snRNA transcription (6-10, 8 members)
- Bilirubin conjugation and organic anion transport (11-20, 14 members)
- Monocyte/myeloid cell modules (11-20, 11 members)
- Monoamine/acetylcholine GPCR second-messenger signaling (21-50, 29 members)
- Glycerolipid and glycerophospholipid metabolism (21-50, 23 members)
- FGFR signaling cascades (11-20, 16 members)
- GPCR regulation of insulin/glucagon secretion (11-20, 12 members)
- Prostaglandin/COX synthesis (3-5, 5 members)
- Mitochondrial protein import and processing (21-50, 21 members)
- Cholinergic neuromuscular transmission (6-10, 7 members)
- Purine and pyrimidine nucleotide biosynthesis (11-20, 17 members)
- Ammonium, urea and gas transmembrane transport (Rh/aquaporins) (11-20, 12 members)
- Neural cell adhesion, myelination, nodes of Ranvier (11-20, 18 members)
- Antiviral innate sensing and interferon (11-20, 11 members)
- Retina and photoreceptor development (11-20, 14 members)
- Peroxisomal VLCFA and ether lipid metabolism (21-50, 22 members)
- Myeloid/dendritic cell inflammatory activation (6-10, 7 members)
- Fucosylation and glycan biosynthesis (21-50, 27 members)
- VEGF signaling and angiogenesis (11-20, 19 members)
- Selective autophagy (11-20, 11 members)
- FGFR3 signaling (3-5, 5 members)
- TGF-beta/BMP signaling and cancer mutants (21-50, 28 members)
- NMDA receptor signaling (6-10, 7 members)
- Ion and osmotic homeostasis, cation-chloride cotransport (11-20, 15 members)
- Cardiac muscle morphogenesis (11-20, 14 members)

## Incoherent themes after rounds 2-3

- 11-20, 11 members: Unrelated terms (lifespan, ORC assembly, VENTX, NOTCH2NL, grab-bag BTMs)
- 3-5, 3 members: Three unrelated signaling terms with only a loose link
- 11-20, 12 members: Mostly BTMs described as mixed housekeeping functions; no shared theme
- 6-10, 7 members: Heterogeneous BTMs plus unrelated NPC, embryo, bone marrow, NOTCH2NL members
- 11-20, 11 members: Mostly grab-bag BTMs plus unrelated GO/Reactome terms
## Structure below mixed nodes (deep dives)

### Hemostasis + lipid mediators (n03423, 139 members, support 0.21)

**Judged an umbrella.** The link: platelet cPLA2 releases arachidonate; COX-1 and TBXAS1 make thromboxane A2 (the aspirin target); endothelial prostacyclin inhibits platelets; platelet 12-LOX makes 12-HETE; SPMs (resolvins, lipoxins) regulate thrombo-inflammation. Bridging members include TP-receptor signalling, the TBXAS1 defect, prostacyclin signalling, PAF metabolism and arachidonate secretion. Real outliers number about 5 of 139 (two ichthyosis CYP4F22/SLC27A4 defects; contact-system angioedema; amyloid-FXII).

Reactome (Hemostasis vs Metabolism of lipids) and GO separate these two areas; THEMA joins them along a physiological axis.

**One level down, it separates into the curated branches:**
- eicosanoids & SPMs, n00436 (66, support 0.95). Its children:
  - SPMs, n02333 (50, 0.62), with a 52-member sibling near-twin n03211 (0.235);
  - prostanoids/leukotrienes/HETEs/EETs, n04219 (46) and n06338 (35).
- coagulation, n02668 (57). Its children:
  - n00950 (41, 0.835);
  - n04068 (17);
  - factor defects n00994 (16, 0.815);
  - vitamin K gamma-carboxylation, n00552 (4, 0.93).
- platelet adhesion/activation, n04419 (52), with child n01879 (32, 0.485).
- platelet GPCR signalling, n05795 (10).

**The 6-parent node n00150** (7 members, support 0.99): ADP-P2Y1, ADP-P2Y12, thrombin-PAR x2, TP, IP, positive regulation of platelet activation. Each of its 6 parents is the core plus 3-4 members, and all are biologically plausible facets:

| parent | size | support | adds | facet |
|---|---|---|---|---|
| n01638 | 10 | 0.555 | Galpha12/13, actin | shape change |
| n03581 | 11 | 0.20 | cytoskeletal remodelling, BTM platelet activation | cytoskeleton |
| n04153 | 11 | 0.14 | GPVI, LDL sensitisation, PLC-activating GPCR | GPVI / GPCR convergence on PLC |
| n05795 | 10 | 0.065 | prostanoid receptors, GPCR clusters | receptor family |
| n05989 | 11 | 0.06 | Rap1 signalling | integrin inside-out activation |
| n06563 | 11 | 0.05 | 5-HT2A-PLC, IP3/PI synthesis | Gq-PLC-IP3 amplification |

The parents overlap pairwise at about Jaccard 0.47, so the 0.70 merge does not touch them, and 4 of 6 have support <= 0.2. This is real biology, but over-fragmented: a "fan" of small overlapping variants around one stable core.

### Mitochondria + translation machinery (n05613, 114, support 0.065; n04214, 102, 0.13)

**Judged an umbrella.** The links:
- NFS1 is the sulfur donor for both Fe-S assembly and tRNA thiolation;
- radical-SAM Fe-S enzymes make wybutosine (TYW1) and diphthamide (DPH1/2);
- tRNA-modification disease genes (TRMU, MTO1, GTPBP3, PUS1, TRIT1, ELAC2) cause OXPHOS deficiency, and several act in both cytosol and mitochondria;
- the hydroxylases JMJD4 (eRF1) and OGFOD1 (RPS23) act on translation termination and fidelity.

Real outliers: Pol II elongation, arylsulfatase activation, perhaps snoRNA localisation.

**n04214 is n05613 minus its 12 heme members (89.5% of its parent).** It is a near-copy that survives because the declared chain collapse is at 90%.

One level down, it separates into:
- mitochondrial gene expression + cytosolic tRNA/translation, n04781 (76, 0.555);
- OXPHOS assembly / CoQ / Fe-S, n01379 (30, 0.65);
- heme & Fe-S cofactor biogenesis, n04731 (19).
The intermediate nodes overlap (n04983, 60, mixes OXPHOS with mitochondrial gene expression).

## Related reviewer checks this cycle (for the record)

- **Multi-parent check, read-only, on thema_L (8 Oct):** 1,038 multi-parent themes; 1,305 parent pairs.
  - 1% of parent pairs are near-twins (J > 0.7) and 0% nested.
  - 75% overlap substantially (J 0.3-0.7, median 0.46): a shared core extended in two directions (e.g. beige/brown fat under thermogenesis vs fat-cell regulation; prostanoid receptors under COX vs eicosanoid catabolism).
  - 24% are distinct parents.
  - Most multiple parents are real shared-core structure, not twinning.
- **Curated axes (8 Oct):** Reactome groups by protagonist molecule or mechanism stage; GO by logical class. Text groupings that disagree with them are as gene-coherent or more (Reactome: curated 0.140, text Ward 0.149, LLM 0.155, random 0.051). See the reviewer log.

## Conclusions

1. **thema_L_repair is biologically plausible from 3 to about 1,000 members:**
   - 97.2% of the 10% sample is coherent or a linked umbrella;
   - 1.7% is a core with misfits;
   - 1.1% is incoherent or a mixture;
   - 29 of 33 themes of 101-1000 members are coherent, and the other 4 are umbrellas.
2. **Systematically bad nodes:** 5 of the 8 giant roots (incoherent), plus 2 large housekeeping bags (1,444 and 1,047; mixtures).
3. **Unnamed TBA BTMs are mostly fine** once described. The few remaining incoherent small themes combine BTMs that are themselves described as mixed housekeeping modules.
4. **Mixed (umbrella) nodes separate into curated-like sub-themes one level below,** with bridging pathways placed under both, which is the intended multi-parent DAG behaviour.
5. **Remaining structural issues** (not biological):
   - (a) giant roots, to be addressed by the recursive top (prompt 19);
   - (b) fans of small overlapping variants around a stable core (the 6 platelet parents);
   - (c) sibling near-twins just under the 0.70 merge (the 50/52 SPM nodes);
   - (d) chain nodes just under the 90% collapse (the 89.5% mitochondrial node).

## Open questions (Aviyah, 9 Oct)

- Whether to merge sibling near-twins and fans. To be decided from their measured frequency, not from examples.
- Whether to change the 90% chain-collapse threshold. To be decided from the distribution of child/parent ratios (look for a natural gap), not from the 89.5% example.
