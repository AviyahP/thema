# Level 1 A/B: naming a parent with its children's rationales

*29 Sep 2026. The level-1 read found the dominant fault: **a parent named NARROWER than one of its own children**, 16 clear and 12 borderline of 215. The cause is in the data, not the instruction — a direct pathway arrived with a title AND a description, a child arrived as one bare line, so the descriptions outweighed the children.*

**The change is to the DATA only.** Under `Child clusters:` each child now carries the rationale sentence it returned when it was named, so the two kinds of member are on comparable footing. No instruction text changed and the system prompt is byte-identical — digest `f3d1f074929df02a` before and after.

Two columns judge coverage. **mech** is `covers_children`, which asks only whether every child still shares a content word — deliberately weak, used to reject and never to accept. **read** is my own reading of whether the new name is true of the child. They differ on three of the 28, all cases where the cover is real but the wording does not overlap.

Old names are **not** deleted: every superseded row stays in `data/theme_names.tsv` marked superseded, and both renderings stay in the ledger.

---

## Stage 1 — the 28 the reviewer flagged

**20 of 28 by the mechanical check** — the gate for stage 2 was 20. **23 of 28 by my reading.** 24 of the 28 names changed.

| node | flagged | old name | new name | mech | read |
|---|---|---|---|---|---|
| `n0206` | clear | Manganese and cadmium ion handling | Transition metal ion homeostasis and detoxification | yes | **yes** |
| `n0426` | clear | NK cell activation regulation | NK cell receptor signalling and activation control | yes | **yes** |
| `n0618` | clear | Vitamin D activation and catabolism | Vitamin D metabolism and receptor signalling | no | **no** |
| `n0486` | clear | Wnt/beta-catenin signalling | Wnt/beta-catenin signalling | yes | **yes** |
| `n0593` | clear | Meiotic chromosome segregation and cytokinesis | Meiotic cell division | yes | **yes** |
| `n0642` | clear | Heart valve development | Cardiac valve development | yes | **yes** |
| `n0104` | clear | Cytoplasmic translation initiation | Cytoplasmic translation initiation and regulation | yes | **yes** |
| `n0273` | clear | NEIL3-associated DNA repair | NEIL3-associated DNA lesion repair | yes | **yes** |
| `n0506` | clear | UV-induced DNA damage response and repair | DNA damage response and repair | yes | **yes** |
| `n0531` | clear | Smooth muscle tone in reproductive function | Smooth muscle tone in reproductive function | yes | **yes** |
| `n0620` | clear | Ciliary control of embryonic left/right patterning | Cilia-dependent left/right patterning of embryonic organs | yes | **yes** |
| `n0719` | clear | Regulation of Fas-mediated T cell apoptosis | Death receptor apoptosis regulation | yes | **yes** |
| `n0474` | clear | Keratinocyte migration and adhesion in re-epithelialization | Keratinocyte-driven epidermal wound re-epithelialisation | no | **no** |
| `n0716` | clear | Androgen-driven male reproductive development | Male reproductive endocrine differentiation | no | **no** |
| `n0625` | clear | GM-CSF and IL-33 driven inflammation | Cytokine-driven innate immune activation | yes | **yes** |
| `n0193` | clear | Taste perception and transduction | Taste sensory transduction | yes | **yes** |
| `n0557` | borderline | Mesenchymal signalling in renal vascular development | Mesangial and mesenchymal signalling in glomerular development | yes | **yes** |
| `n0596` | borderline | Cleavage furrow formation and abscission | Cytokinesis and cortical polarity signalling | yes | **yes** |
| `n0775` | borderline | ER-associated degradation and protein unfolding | Ubiquitin-proteasome protein quality control | yes | **yes** |
| `n0398` | borderline | Intestinal cholesterol and lipid absorption | Intestinal cholesterol and lipid absorption | no | **yes** |
| `n0044` | borderline | miRNA biogenesis and its regulation | miRNA biogenesis and silencing | yes | **yes** |
| `n0493` | borderline | TRIF-dependent TLR signaling to type I interferon | TRIF-dependent TLR signalling to type I interferon | yes | **yes** |
| `n0244` | borderline | Synaptic vesicle endocytosis and recycling | Synaptic vesicle recycling and endocytosis | no | **no** |
| `n0592` | borderline | Mechanical stimulus sensing and response | Mechanical stimulus sensing | no | **no** |
| `n0037` | borderline | Photoreceptor cilium biology | Photoreceptor cilium biology and vision | yes | **yes** |
| `n0453` | borderline | Mitochondrial gene expression | Mitochondrial and nuclear gene expression | no | **yes** |
| `n0581` | borderline | Chromatin protein targeting and organization control | Chromatin protein targeting and organization control | no | **yes** |
| `n0622` | borderline | Alzheimer's-associated neuronal and synaptic pathology | Amyloid and tau-driven neurodegeneration in Alzheimer's disease | yes | **yes** |

### The ones still not covering, with the child they miss

- `n0618` — **Vitamin D metabolism and receptor signalling**
  - child: Bile acid and sterol homeostasis
- `n0474` — **Keratinocyte-driven epidermal wound re-epithelialisation**
  - child: Regulation of cell-matrix adhesion turnover
- `n0716` — **Male reproductive endocrine differentiation**
  - child: Gonadotropin control of ovarian and gonadal function
- `n0244` — **Synaptic vesicle recycling and endocytosis**
  - child: Membrane trafficking dynamics
- `n0592` — **Mechanical stimulus sensing**
  - child: Sensory transduction across modalities

---

## Stage 2 — the remaining 187 level-1 nodes

Run under the same rendering so the whole level is named one way. **185 named of 187**; 143 cover their children by the mechanical check (77%). These have not been read one by one — that is for the reviewer.

| node | old name | new name | mech |
|---|---|---|---|
| `n0008` | Unfolded protein response regulation | Regulation of ER stress and UPR signalling | no |
| `n0009` | Monoamine catabolism and clearance | Monoamine neurotransmitter degradation | no |
| `n0010` | Base excision repair | Base excision repair | yes |
| `n0011` | Ferroptosis regulation and oxidative stress response | Redox stress and ferroptosis regulation | yes |
| `n0013` | Cell cycle progression and checkpoint control | Cell cycle progression and control | yes |
| `n0014` | Complement activation and opsonization control | Complement activation and humoral defence | yes |
| `n0016` | Lipoprotein lipase-mediated triglyceride lipolysis | Lipoprotein lipase-mediated triglyceride lipolysis | yes |
| `n0017` | DNA replication initiation and elongation | DNA replication initiation and elongation | yes |
| `n0039` | Blood coagulation cascade and its disorders | Blood coagulation cascade and its defects | yes |
| `n0040` | Cardiac action potential and conduction | Cardiac action potential generation and conduction | yes |
| `n0042` | Fatty acid and ether lipid biosynthesis | Fatty alcohol and ether lipid synthesis | yes |
| `n0045` | Glycogen metabolism and its disorders | Glycogen metabolism and its disorders | yes |
| `n0046` | Angiotensin signalling and blood pressure control | Angiotensin-mediated blood pressure regulation | yes |
| `n0060` | Drug-resistant receptor tyrosine kinase mutants | Drug-resistant receptor tyrosine kinase mutants | yes |
| `n0062` | Respiratory virus assembly, export and release | RSV and influenza replication and virion assembly | no |
| `n0065` | Centrosome and spindle positioning machinery | Centrosome and spindle positioning | yes |
| `n0066` | Regulation of germ cell meiosis and maturation | Regulation of germ cell meiosis and gametogenesis | yes |
| `n0067` | Epithelial cell-cell and cell-matrix adhesion | Epithelial cell junctions and adhesion dynamics | yes |
| `n0070` | TGF-beta/BMP-SMAD signal transduction | TGF-beta/BMP-SMAD signalling | yes |
| `n0071` | Xenobiotic and drug metabolism | Xenobiotic biotransformation and drug disposition | yes |
| `n0081` | Purine and pyrimidine salvage pathways | Purine and pyrimidine salvage metabolism | yes |
| `n0082` | TAK1-dependent NF-kB and MAPK activation | TRAF-TAK1-IKK NF-kB signaling | yes |
| `n0083` | Paraxial mesoderm segmentation and fate commitment | Mesoderm formation and somite segmentation | yes |
| `n0084` | Lipoylation and branched-chain ketoacid dehydrogenase disorders | Lipoylation and branched-chain ketoacid dehydrogenase disorders | yes |
| `n0085` | Heart morphogenesis and chamber development | Heart morphogenesis and chamber development | yes |
| `n0086` | Sex hormone receptor transcriptional response | Steroid hormone receptor transcriptional response | yes |
| `n0092` | DNA synthesis in replication and repair | DNA synthesis in replication and repair | yes |
| `n0103` | Th1/Th17 differentiation and effector responses | Th17 and Th1 lineage differentiation control | yes |
| `n0106` | RUNX and NOTCH control of myeloid differentiation | RUNX and Notch control of myeloid differentiation | yes |
| `n0123` | Cytokine-JAK-STAT signaling | Cytokine-JAK-STAT signaling | yes |
| `n0124` | Nucleotide sugar biosynthesis and metabolism | Nucleotide-sugar biosynthesis for glycosylation | yes |
| `n0125` | Autophagic and endosomal membrane trafficking | ATG8-dependent membrane sequestration and endosomal sorting | no |
| `n0126` | GPCR and lipid mediator signalling | GPCR signalling in lipid mediator and nucleotide sensing | no |
| `n0164` | Glucose-stimulated insulin secretion | Glucose homeostasis and insulin secretion | yes |
| `n0165` | Skeletal and dental tissue mineralization | Skeletal and dental mineralization control | no |
| `n0180` | Endothelial adhesion and mechanotransduction | Endothelial mechanical and adhesive signaling | yes |
| `n0181` | Platelet activation and adhesion control | Platelet activation and adhesion regulation | no |
| `n0195` | Regulation of mitochondrial respiration and ROS | Regulation of mitochondrial respiration and ROS | yes |
| `n0197` | Regulation of MAPK cascade activity | Regulation of MAPK/JNK cascades | no |
| `n0216` | Cytoskeletal transport of organelles and receptor complexes | Cytoskeletal transport of organelles and cargo | yes |
| `n0218` | Insulin receptor family signaling | Insulin-family receptor tyrosine kinase signaling | no |
| `n0233` | Viral hijacking of host pathways and antiviral drug targets | Virus-host interactions and antiviral therapeutics | yes |
| `n0234` | Regulation of presynaptic neurotransmitter release | Regulation of neurotransmitter and glutamate release | yes |
| `n0235` | Regulation of mitochondrial quality control by autophagy | Mitochondrial quality control by autophagy and fission | no |
| `n0236` | Pancreatic endocrine lineage development and beta cell homeostasis | Pancreatic endocrine cell development and beta cell homeostasis | no |
| `n0241` | Mitotic chromosome condensation and cohesion | Mitotic chromosome condensation and cohesion | yes |
| `n0250` | Glycosaminoglycan metabolism and disorders | Glycosaminoglycan metabolism and connective tissue disease | yes |
| `n0262` | Vacuolar and lysosomal protein trafficking | Vacuole and lysosome trafficking | no |
| `n0263` | Epigenetic chromatin regulation and imprinting | Chromatin and epigenetic inheritance | yes |
| `n0269` | VEGF-driven vascular and epithelial growth | Angiogenesis and vascular growth signalling | yes |
| `n0271` | Mesenchymal fate: adipocyte and osteoblast commitment | Mesenchymal adipocyte and osteoblast fate regulation | no |
| `n0274` | Endocytic control of receptor tyrosine kinase signalling | Endocytic control of receptor tyrosine kinase signalling | yes |
| `n0275` | Regulation of calcium-mediated signaling | Calcium-mediated signaling regulation | yes |
| `n0276` | Postsynaptic structural organization and receptor trafficking | Postsynaptic structural and receptor plasticity | yes |
| `n0281` | Neural regulation of behavioral responses | Neural circuits of behavior and addiction | yes |
| `n0282` | Excitatory synapse assembly and signaling | Excitatory synapse assembly and signaling | yes |
| `n0283` | Insulin receptor signal transduction to glucose uptake | Insulin receptor signalling to glucose uptake | yes |
| `n0290` | B cell development and diversification | B cell development and antibody responses | yes |
| `n0291` | Nucleotide biosynthesis regulation and transport | Nucleotide biosynthesis regulation and transport | yes |
| `n0292` | MYC-driven ribosome biogenesis | MYC-driven ribosome biogenesis and rRNA synthesis | yes |
| `n0293` | Nephron segment patterning and development | Nephron segment development and patterning | yes |
| `n0294` | Rho family GTPase signalling | Rho-family GTPase cycles and effectors | yes |
| `n0295` | Nucleocytoplasmic RNA and protein export | Nuclear export of RNA and protein | yes |
| `n0302` | Negative regulation of myogenesis and regeneration | Negative regulation of myogenesis and regeneration | no |
| `n0314` | Actin-driven membrane ruffling and macropinocytic entry | Actin-driven membrane protrusion and pathogen entry | yes |
| `n0315` | Regulation of cholesterol and lipid biosynthesis | Regulation of cholesterol and lipid biosynthesis | yes |
| `n0322` | p53-mediated damage response and apoptosis | p53-mediated damage and apoptosis response | yes |
| `n0325` | Mitochondrial apoptosis regulation via BCL-2 family | BCL-2 family regulation of mitochondrial apoptosis | yes |
| `n0341` | Apoptosis signaling and execution | Apoptosis signaling and execution | no |
| `n0342` | Dendrite and spine morphogenesis | Dendrite and spine morphogenesis | no |
| `n0346` | Pre-mRNA transcription and processing | mRNA transcription, splicing and 3' processing | yes |
| `n0353` | IL-33 and allergic immune activation | Allergic and IL-33-driven immune activation | no |
| `n0354` | Amino acid transport across membranes | Amino acid transport | yes |
| `n0357` | Regulation of lymphocyte activation | Regulation of immune cell activation | yes |
| `n0361` | Antigen presentation and viral immune evasion | MHC-associated antigen presentation and immune evasion | no |
| `n0362` | Positive regulation of innate inflammatory mediator production | Cytokine-driven acute inflammatory amplification | yes |
| `n0365` | Glucose-regulated insulin secretion | Glucose-regulated insulin secretion | yes |
| `n0366` | Osmotic and hydrostatic stress transport | Osmotic and glycerol transport homeostasis | no |
| `n0367` | Hematopoietic and lymphocyte lineage commitment | Hematopoietic and lymphocyte lineage commitment | no |
| `n0372` | Intestinal nutrient absorption | Digestion and intestinal nutrient uptake | yes |
| `n0373` | Glycolysis and pyruvate metabolism in hypoxia | Hypoxia-linked glycolytic and pyruvate metabolism | yes |
| `n0374` | Dendritic spine and arbor morphogenesis | Dendritic spine and arbor structural plasticity | yes |
| `n0375` | Glycan and sialic acid metabolism | Glycan biosynthesis and catabolism | yes |
| `n0377` | Potassium-driven membrane repolarization | Potassium-driven membrane repolarization | yes |
| `n0383` | Neural control of behaviour and physiology | Neural circuit control of behavior | yes |
| `n0384` | Wnt signal transduction and its regulation | Wnt/beta-catenin signal transduction | yes |
| `n0385` | Non-coding RNA processing and modification | Non-coding RNA processing and modification | yes |
| `n0388` | Kinase-mediated activation of signal transduction | Protein phosphorylation and kinase signal activation | yes |
| `n0390` | Renal and epithelial amino acid handling | Renal and cellular amino acid transport | yes |
| `n0397` | Post-translational control of signaling protein activity and localization | Regulation of protein localization and modification in signaling | yes |
| `n0402` | Phagocytic and effector leukocyte immunity | Myeloid phagocytosis and leukocyte effector immunity | yes |
| `n0405` | Purine nucleoside and nucleotide salvage | Purine nucleoside and nucleotide salvage | no |
| `n0406` | Amino acid and vitamin B6 metabolism | Amino acid and vitamin B6 metabolism | yes |
| `n0407` | Bioactive lipid mediator metabolism and signalling | Bioactive lipid mediator turnover and signaling | yes |
| `n0409` | Chemokine-driven leukocyte recruitment | Chemokine-driven leukocyte chemotaxis | yes |
| `n0413` | Neural tube patterning and regional specification | Neural tube regional patterning | yes |
| `n0415` | Actin cytoskeleton remodeling in adhesion and motility | Actin cytoskeleton dynamics in cell motility | yes |
| `n0416` | cAMP-mediated GPCR signalling and secretion control | cAMP-linked GPCR signalling and secretion control | yes |
| `n0418` | Hair follicle cycling and epidermal turnover | Hair follicle cycling and epidermal desquamation | yes |
| `n0425` | Neural tube formation and patterning | Neural tube formation and patterning | yes |
| `n0427` | Proteostasis under stress | Chaperone-mediated protein folding and stress response | yes |
| `n0432` |  | Intestinal epithelial identity and homeostasis | yes |
| `n0439` | Regulation of myeloid cytokine production | Regulation of myeloid cytokine production | no |
| `n0440` | Skeletal cell fate and ossification regulation | Skeletal development and osteoblast differentiation | yes |
| `n0445` | Craniofacial and organ-specific morphogenesis | Embryonic organogenesis and craniofacial-eye morphogenesis | yes |
| `n0446` | Vesicle-mediated intracellular transport | Vesicle-mediated membrane trafficking | no |
| `n0447` | MHC-restricted antigen presentation | MHC-restricted antigen presentation | yes |
| `n0449` | 3'-UTR-mediated mRNA and miRNA stability control | 3'-UTR and miRNA stability control | no |
| `n0457` | Proteasome assembly and regulation | Proteasome assembly and function | no |
| `n0458` | Smooth muscle contractile phenotype and remodeling | Smooth muscle contractile-synthetic phenotype control | yes |
| `n0463` | Cytosolic nucleic acid sensing and inflammasome regulation | Cytosolic nucleic acid sensing and inflammasome activation | no |
| `n0467` | Cell projection and axon morphogenesis | Neuronal outgrowth and guidance | yes |
| `n0468` | Mitotic spindle assembly and chromosome segregation | Mitotic spindle assembly and chromosome segregation | yes |
| `n0473` | Vitamin D and steroid hormone metabolism | Vitamin D and fat-soluble vitamin metabolism | no |
| `n0475` | Germinal centre B cell regulation | Humoral immunity regulation and germinal centre selection | no |
| `n0485` | Innate immune signalling in inflammation | Innate immune inflammatory signalling | yes |
| `n0487` | Bacterial sensing and antigen presentation licensing | Innate sensing and control of intracellular bacteria | yes |
| `n0488` | Sensory perception and stimulus detection | Sensory perception and stimulus detection | yes |
| `n0495` | Galactose and pentose sugar metabolism | Galactose and pentose metabolism disorders | no |
| `n0496` | Host-pathogen metal ion trafficking and defence | Host-pathogen metal ion competition | no |
| `n0500` | Urinary tract and kidney development | Urinary tract and kidney development | yes |
| `n0507` | Germ layer formation and axis patterning | Gastrulation and germ layer patterning | no |
| `n0510` | Osmolyte and water transport across membranes | Osmotic homeostasis and water/solute transport | yes |
| `n0515` | Cell motility and projection dynamics | Cell motility and projection dynamics | no |
| `n0522` | Telomere maintenance and chromosome replication | Chromosome end replication and maintenance | yes |
| `n0524` | rRNA processing and mRNA turnover | rRNA and mRNA processing by exonucleases and snoRNPs | no |
| `n0527` |  | UNNAMEABLE | no |
| `n0528` | Vitamin and fat-soluble compound metabolism | Vitamin and cofactor metabolism | yes |
| `n0530` | Mitotic and meiotic chromosome segregation | Mitotic chromosome segregation and spindle control | yes |
| `n0539` | Neuroendocrine regulation of growth | Neuroendocrine regulation of growth and metabolism | yes |
| `n0540` |  | Cadherin adhesion and TGFBR3 signalling regulation | yes |
| `n0541` | Host-virus interactions in viral replication | Host-virus interactions in viral replication | no |
| `n0544` | Leukocyte migration and chemotaxis | Leukocyte chemotaxis and migration regulation | yes |
| `n0549` | Acetyl-CoA and ketone body metabolism | Acetyl-CoA and ketone body metabolism | yes |
| `n0558` | Nucleotide metabolism and turnover | Nucleotide metabolism and pharmacogenetics | yes |
| `n0567` | Nutrient digestion and transport | Dietary nutrient digestion and sugar transport | yes |
| `n0568` | Leukocyte effector immune responses | Leukocyte effector immunity | yes |
| `n0571` | Innate immune sensing of bacteria | Innate recognition of microbial molecules and signalling | yes |
| `n0590` | Glycerolipid biosynthesis and turnover | Glycerolipid and phospholipid metabolism | yes |
| `n0591` | Cellular senescence and telomere regulation | Senescence and telomere maintenance | yes |
| `n0594` | Apical actin cortex and microvillus organization | Cortical actin-based apical polarity and protrusions | yes |
| `n0598` | Lipid-linked protein trafficking and secretion | Lipid metabolism and secretory trafficking | yes |
| `n0607` | mRNA cleavage and polyadenylation control | mRNA 3' end processing and decay | yes |
| `n0615` | Protein glycosylation and its disorders | Protein glycosylation pathways and disorders | yes |
| `n0619` | Cortical and cytoskeletal protein targeting | Cortical and centrosomal protein targeting for polarity | yes |
| `n0627` | Glycosaminoglycan biosynthesis and disorders | Glycosaminoglycan biosynthesis and disorders | yes |
| `n0636` | Embryonic patterning and cell fate commitment | Embryonic patterning and cell fate specification | yes |
| `n0639` | Receptor tyrosine kinase signaling via phosphorylation | Kinase-driven phosphorylation and PI3K/AKT signalling | yes |
| `n0646` | ERBB and TGF-beta signaling in cancer | EGFR and TGF-beta signaling in cancer | yes |
| `n0647` | mTORC1 and nutrient stress signaling in growth control | Nutrient sensing and growth-stress signaling | yes |
| `n0650` | Glycosaminoglycan and proteoglycan disorders | Glycosaminoglycan and proteoglycan biosynthesis disorders | yes |
| `n0651` | Actin-driven cell projection and motility | Actin-driven cell projections and motility | yes |
| `n0652` | Muscle contraction and its regulation | Muscle contractile function and control | yes |
| `n0658` |  | UNNAMEABLE | no |
| `n0660` | Type I interferon signaling and its regulation | Type I interferon signaling and its regulation | yes |
| `n0661` | Mitochondrial dynamics and organization | Mitochondrial dynamics and organization | no |
| `n0670` | Neurotrophin and glial signalling in neuronal development | Neurotrophin and adhesion signalling in axon and myelin development | yes |
| `n0676` | cAMP signalling regulation and turnover | cAMP signalling generation and turnover | yes |
| `n0687` | GPCR signaling via cAMP and aminergic ligands | GPCR signaling via cyclic nucleotides and amines | yes |
| `n0688` | Endothelial specification and morphogenesis | Endothelial specification and vascular morphogenesis | yes |
| `n0692` | Protein and mitochondrial ribosome biogenesis | Protein synthesis and processing | no |
| `n0693` | Isoprenoid and sphingolipid biosynthesis | Isoprenoid and sphingolipid biosynthesis | yes |
| `n0703` | Receptor tyrosine kinase signaling | FGFR and ERBB receptor tyrosine kinase signaling | yes |
| `n0704` | Triglyceride and lipid storage regulation | Triglyceride and insulin-responsive glucose metabolism | no |
| `n0706` | Muscle fibre homeostasis and size control | Muscle fibre membrane and size homeostasis | no |
| `n0707` | Calcium regulation of sarcomeric contraction | Calcium regulation of sarcomeric contraction | yes |
| `n0708` | DNA mismatch and double-strand break repair | Mismatch repair and double-strand break repair | yes |
| `n0714` | Amino acid metabolism and conjugation reactions | Amino acid metabolism and glycine conjugation | yes |
| `n0715` | Coagulation cascade regulation | Coagulation cascade and haemostasis | no |
| `n0717` | T cell activation and proliferation control | CD4 T cell activation and proliferation control | yes |
| `n0718` | Lymphocyte development and adaptive immunity | Lymphocyte development and adaptive immunity | no |
| `n0730` | Inositol phosphate and nucleotide metabolism | Inositol phosphate and nucleotide phosphate metabolism | yes |
| `n0732` | Vesicle trafficking to lysosome and vacuole | Vesicular trafficking to the vacuole and lysosome | no |
| `n0749` | Nucleotide-sugar and glycan precursor metabolism | Nucleotide sugar and glycan precursor metabolism | yes |
| `n0752` | Lipoprotein particle metabolism | Lipoprotein particle biology | yes |
| `n0753` | mRNA 3'-end formation and histone pre-mRNA processing | mRNA 3' end formation and stability | yes |
| `n0758` | Cadherin-mediated cell-cell adhesion dynamics | Cadherin junction dynamics and EMT | yes |
| `n0776` | Small nuclear and nucleolar RNP biogenesis | snRNA and rRNA modification and snoRNP assembly | yes |
| `n0777` | Chromosome cohesion and telomere maintenance | Chromosome cohesion and stability maintenance | yes |
| `n0778` | Platelet activation and adhesion signalling | Platelet activation and adhesion signalling | yes |
| `n0786` | Ion transport in mineralization and homeostasis | Phosphate transport and mineral homeostasis | yes |
| `n0787` | Regulation of synaptic transmission and neuronal excitability | Presynaptic and dendritic activity regulation | no |
| `n0788` | Regulation of lipoprotein receptor turnover and lipid metabolism | Regulation of lipid and lipoprotein receptor homeostasis | yes |
| `n0789` | Calcium-driven muscle contraction and relaxation | Excitation-contraction coupling in muscle | yes |
| `n0795` | Amino acid and cofactor vitamin metabolism | Cofactor and non-proteinogenic amino acid metabolism | yes |
| `n0797` | Mitochondrial cofactor and amino acid metabolism disorders | Mitochondrial cofactor and amino acid metabolism | yes |
| `n0798` | tRNA modification | tRNA modification for translational fidelity | yes |

