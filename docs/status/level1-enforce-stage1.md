# Level 1: coverage enforced — four attempts, and what each one taught

*2 Oct 2026. Fourth attempt. The mechanical take is replaced by a second re-ask that WIDENS from the uncovered child's name instead of copying it.*

## The four attempts, side by side

| | lenient | strict | split | **split + widen** |
|---|---|---|---|---|
| covered first time | 6 | 1 | 2 | **2** |
| covered after re-ask | 10 | 10 | 2 | **2** |
| covered after widen | — | — | — | **1** |
| took a child's name | 0 | 0 | 3 | **0** |
| unnameable | 2 | 7 | 11 | **13** |
| my count right, of 18 | 11 | 9 | 11 | **7** |
| good controls falsely flagged, of 10 | — | 5 | 1 | **1** |

The reviewer's own count on the lenient run was ~11 of 18, which is where that column's figure comes from.

## The widen re-ask writes good names. The strict child check rejects them anyway

**13 widen re-asks, 1 accepted.** And the 12 rejections are not bad names:

| node | widened to | strict call still rejects |
|---|---|---|
| `n0618` | Sterol and fat-soluble vitamin metabolism | Bile acid and sterol homeostasis |
| `n0474` | Keratinocyte adhesion and migration in wound re-epithelialization | Regulation of cell-matrix adhesion turnover |
| `n0244` | Membrane trafficking including synaptic vesicle recycling | Organelle membrane remodelling and trafficking |
| `n0592` | Mechanical and sensory stimulus detection | Sensory transduction across modalities |
| `n0197` | Regulation of MAP kinase cascade activity | Regulation of serine/threonine kinase phosphorylation |
| `n0218` | Insulin receptor family RTK signaling and attenuation | PI3K/AKT activation downstream of growth factor receptors, Signaling by ALK, Signaling by LTK |
| `n0262` | Vesicular transport to the vacuole/lysosome | Intracellular vesicle transport, lytic vacuole organization |
| `n0706` | Muscle fiber structural and membrane homeostasis | Sarcomere assembly and contraction, negative regulation of cell size |
| `n0495` | Amino sugar, galactose and glycoside metabolism | Amino sugar and carbohydrate catabolism |
| `n0181` | Platelet activation and hemostatic signalling | Hemostasis and thrombin/PAR signalling, regulation of homotypic cell-cell adhesion |
| `n0236` | Transcriptional control of pancreatic endocrine development and beta cell mass | Transcriptional specification of endoderm-derived epithelia, type B pancreatic cell proliferation, negative regulation of type B pancreatic cell apoptotic process |
| `n0125` | Endomembrane trafficking, autophagy and deubiquitination | Endomembrane trafficking and turnover |

`n0618` widened to **Sterol and fat-soluble vitamin metabolism** — the name an earlier run had already produced and which I had flagged as the right answer — and was refused because the child *Bile acid and sterol homeostasis* is not strictly a sub-category of it.

**12 of the 13 failures are the strict CHILD call, not the lenient pathway call.** The widen step did its job; the obstacle moved.

## What the four attempts jointly establish

**The fault is usually in the CHILD's name, not the parent's.** `n0262`'s child is called *Intracellular vesicle transport*, but that child is a specific cluster of vesicle-transport pathways — its name over-claims for its own contents. No parent name can strictly contain it, because the child's name describes more than the child holds. Same for `n0592`'s *Sensory transduction across modalities* and `n0474`'s *Regulation of cell-matrix adhesion turnover*.

Every attempt has tried to fix this from the parent's side and each has failed differently: permitting reuse (0 of 18), copying the child's name (3 of 9 survived), widening from it (1 of 13). **The mechanism that would work — renaming the over-claiming child — exists in the code as the child re-ask, but it only triggers when a parent takes the child's name, which the last two attempts made rare and then impossible.**

## Controls

**1 of 10 flagged**, unchanged from the split run — the split is stable and is not what is failing.

| node | name | flagged |
|---|---|---|
| `n0060` | Drug-resistant receptor tyrosine kinase mutants | — clean |
| `n0708` | Mismatch repair and double-strand break repair | — clean |
| `n0010` | Base excision repair | — clean |
| `n0017` | DNA replication initiation and elongation | DNA replication and licensing |
| `n0040` | Cardiac action potential generation and conduction | — clean |
| `n0039` | Blood coagulation cascade and its defects | — clean |
| `n0070` | TGF-beta/BMP-SMAD signalling | — clean |
| `n0014` | Complement activation and humoral defence | — clean |
| `n0085` | Heart morphogenesis and chamber development | — clean |
| `n0123` | Cytokine-JAK-STAT signaling | — clean |

---

## Per node

### `n0618` — unnameable

- **first name:** Vitamin D metabolism and receptor signalling
- **check 1:** uncovered — Bile acid and sterol homeostasis, fat-soluble vitamin catabolic process
  - *Bile acid and sterol homeostasis is a broader, related metabolic category that only partly overlaps with vitamin D metabolism and receptor signalling, not a subset of it. The other three are specifically about vitamin D regulation or metabolism defects, while the fat-soluble vitamin catabolic process is a broader category not specific to vitamin D.*
- **re-ask 1:** Sterol and fat-soluble vitamin metabolism
- **check 2:** still uncovered — Bile acid and sterol homeostasis
  - *This cluster includes bile acid homeostasis mechanisms that extend beyond sterol metabolism and fat-soluble vitamin metabolism, making it broader than the parent category. All listed pathways relate to fat-soluble vitamin (vitamin D) metabolism or its regulatory and genetic defects, falling under sterol/fat-soluble vitamin metabolism.*
- **re-ask 2, widening from the child** 'Bile acid and sterol homeostasis': Sterol and fat-soluble vitamin metabolism
- **check 3:** still uncovered — Bile acid and sterol homeostasis
  - *This cluster includes bile acid homeostasis mechanisms that extend beyond sterol metabolism and fat-soluble vitamin metabolism, making it broader than the parent category. All listed pathways relate to fat-soluble vitamin (vitamin D) metabolism or its regulatory and genetic defects, falling under sterol/fat-soluble vitamin metabolism.*
- **final:** UNNAMEABLE — *contents have no common name: Bile acid and sterol homeostasis*
- **children:** Bile acid and sterol homeostasis
- **my reading:** no

### `n0474` — unnameable

- **first name:** Keratinocyte-driven epidermal wound re-epithelialisation
- **check 1:** uncovered — Regulation of cell-matrix adhesion turnover
  - *Cell-matrix adhesion turnover regulation is a general cellular process occurring in many contexts beyond keratinocyte wound re-epithelialisation, so it is broader rather than a strict sub-category. All three pathways describe keratinocyte/epidermal cell spreading and migration processes central to re-epithelialisation during wound healing.*
- **re-ask 1:** Keratinocyte adhesion and migration in re-epithelialisation
- **check 2:** still uncovered — Regulation of cell-matrix adhesion turnover
  - *Cell-matrix adhesion turnover regulation is a general cellular process not specific to keratinocytes or re-epithelialisation, so it is broader than and only partly overlapping the parent category. All three pathways directly concern keratinocyte/epidermal cell spreading and migration, which are components of re-epithelialisation adhesion/migration processes.*
- **re-ask 2, widening from the child** 'Regulation of cell-matrix adhesion turnover': Keratinocyte adhesion and migration in wound re-epithelialization
- **check 3:** still uncovered — Regulation of cell-matrix adhesion turnover
  - *Cell-matrix adhesion turnover is a general process occurring in many cell types and contexts, not exclusively within keratinocyte wound re-epithelialization, so it is broader than and not a sub-category of the parent. All three pathways directly concern keratinocyte/epidermal cell spreading and migration, which are core aspects of wound re-epithelialization.*
- **final:** UNNAMEABLE — *contents have no common name: Regulation of cell-matrix adhesion turnover*
- **children:** Regulation of cell-matrix adhesion turnover
- **my reading:** no

### `n0716` — covered after widen

- **first name:** Male reproductive endocrine differentiation
- **check 1:** uncovered — Gonadotropin control of ovarian and gonadal function, positive regulation of activin receptor signaling pathway
  - *This cluster concerns ovarian/gonadal regulation broadly, not specifically male reproductive endocrine differentiation. Androgen biosynthesis and male sex differentiation directly relate to male reproductive endocrine differentiation, while activin receptor signaling regulation is a general TGF-beta pathway not specific to male reproductive endocrine processes.*
- **re-ask 1:** Gonadal hormone signalling and sex differentiation
- **check 2:** still uncovered — Gonadotropin control of ovarian and gonadal function, positive regulation of activin receptor signaling pathway
  - *This cluster concerns gonadotropin (pituitary hormone) regulation of gonadal function, which is broader than and only partly overlaps gonadal hormone signalling and sex differentiation itself. Androgen biosynthesis and male sex differentiation directly relate to gonadal hormone signalling and sex differentiation, while activin receptor signaling is a broader TGF-beta pathway not specific to gonadal hormones or sex differentiation.*
- **re-ask 2, widening from the child** 'Gonadotropin control of ovarian and gonadal function': Reproductive endocrine signaling and sex differentiation
- **check 3:** covers everything
  - *Gonadotropin control of ovarian and gonadal function is a sub-category of reproductive endocrine signaling and sex differentiation. All three pathways relate directly to reproductive hormone biosynthesis/signaling and sex differentiation, fitting the parent theme.*
- **saved:** Reproductive endocrine signaling and sex differentiation
- **passed the check:** Reproductive endocrine signaling and sex differentiation (MATCH)
- **children:** Gonadotropin control of ovarian and gonadal function
- **my reading:** yes

### `n0244` — unnameable

- **first name:** Synaptic vesicle endocytosis and recycling
- **check 1:** uncovered — Organelle membrane remodelling and trafficking
  - *This cluster is a broader general membrane trafficking category, not specific to synaptic vesicle endocytosis and recycling. All three pathways directly pertain to synaptic vesicle endocytosis and recycling processes.*
- **re-ask 1:** Membrane trafficking and synaptic vesicle recycling
- **check 2:** still uncovered — Organelle membrane remodelling and trafficking
  - *This cluster is broader, covering general organelle membrane remodelling beyond synaptic vesicle recycling specifically. All three pathways relate to synaptic vesicle membrane trafficking and recycling, falling under the parent theme.*
- **re-ask 2, widening from the child** 'Organelle membrane remodelling and trafficking': Membrane trafficking including synaptic vesicle recycling
- **check 3:** still uncovered — Organelle membrane remodelling and trafficking
  - *This cluster is broader, covering organelle membrane remodelling generally rather than being strictly a subset of membrane trafficking/synaptic vesicle recycling. All three pathways relate to synaptic vesicle recycling and presynaptic endocytosis, which fall under membrane trafficking including synaptic vesicle recycling.*
- **final:** UNNAMEABLE — *contents have no common name: Organelle membrane remodelling and trafficking*
- **children:** Organelle membrane remodelling and trafficking
- **my reading:** no

### `n0592` — unnameable

- **first name:** Mechanical stimulus sensing
- **check 1:** uncovered — Sensory transduction across modalities
  - *This cluster is broader, covering all sensory modalities rather than being limited to mechanical stimulus sensing. All three pathways relate to sensing or responding to mechanical/hydrostatic force stimuli, fitting the mechanical stimulus sensing theme.*
- **re-ask 1:** Mechanical and sensory stimulus detection
- **check 2:** still uncovered — Sensory transduction across modalities
  - *This cluster is broader, covering all sensory modalities (e.g., chemical, light) not just mechanical and sensory stimulus detection. All three pathways relate to detection/response to mechanical or pressure stimuli, fitting the mechanical and sensory stimulus detection theme.*
- **re-ask 2, widening from the child** 'Sensory transduction across modalities': Mechanical and sensory stimulus detection
- **check 3:** still uncovered — Sensory transduction across modalities
  - *This cluster is broader, covering all sensory modalities (e.g., chemical, light) not just mechanical and sensory stimulus detection. All three pathways relate to detection/response to mechanical or pressure stimuli, fitting the mechanical and sensory stimulus detection theme.*
- **final:** UNNAMEABLE — *contents have no common name: Sensory transduction across modalities*
- **children:** Sensory transduction across modalities
- **my reading:** no

### `n0197` — unnameable

- **first name:** Regulation of MAPK cascade signalling
- **check 1:** uncovered — Regulation of serine/threonine kinase phosphorylation
  - *This cluster covers phosphorylation regulation of serine/threonine kinases broadly, not limited to MAPK cascade components, so it only partly overlaps rather than being a strict subset. All three pathways involve regulation of MAPK cascade activity (including JNK, a MAPK subfamily), so they fall under the parent theme.*
- **re-ask 1:** Regulation of kinase cascade signalling
- **check 2:** still uncovered — Regulation of serine/threonine kinase phosphorylation
  - *Phosphorylation regulation of serine/threonine kinases is a broader upstream regulatory event not confined to kinase cascade signalling. All three pathways concern regulation of kinase cascades (MAPK/JNK) and thus fall under the parent theme.*
- **re-ask 2, widening from the child** 'Regulation of serine/threonine kinase phosphorylation': Regulation of MAP kinase cascade activity
- **check 3:** still uncovered — Regulation of serine/threonine kinase phosphorylation
  - *This cluster broadly covers phosphorylation regulation of all serine/threonine kinases, not specifically MAP kinase cascade components. All three pathways concern regulation of MAP kinase/MAPK/JNK cascade activity, fitting under the parent theme.*
- **final:** UNNAMEABLE — *contents have no common name: Regulation of serine/threonine kinase phosphorylation*
- **children:** Regulation of serine/threonine kinase phosphorylation
- **my reading:** no

### `n0405` — covered

- **first name:** Purine and nucleotide pool homeostasis
- **check 1:** covers everything
  - *Both nucleotide pool sanitation/catabolism and deoxyribonucleotide synthesis/catabolism are sub-processes maintaining the nucleotide pool, falling within purine and nucleotide pool homeostasis. Both pathways relate to purine metabolism and salvage, falling under purine/nucleotide pool homeostasis.*
- **saved:** Purine and nucleotide pool homeostasis
- **passed the check:** Purine and nucleotide pool homeostasis (MATCH)
- **children:** Nucleotide pool sanitation and catabolism, Deoxyribonucleotide synthesis and catabolism
- **my reading:** yes

### `n0302` — covered after re-ask

- **first name:** Negative regulation of myogenesis and regeneration
- **check 1:** uncovered — Muscle cell proliferation and differentiation, regeneration
  - *This cluster is broader, covering general proliferation and differentiation processes rather than being limited to negative regulation of myogenesis and regeneration. The other pathways specifically address negative regulation of myogenic processes, while 'regeneration' alone is a general, unqualified term lacking the negative regulation/myogenesis-specific context.*
- **re-ask 1:** Muscle development and regeneration
- **check 2:** covers everything
  - *Muscle cell proliferation and differentiation is a core sub-process of muscle development and regeneration. All listed pathways relate to muscle differentiation/development regulation or regeneration generally, fitting the parent theme.*
- **saved:** Muscle development and regeneration
- **passed the check:** Muscle development and regeneration (MATCH)
- **children:** Muscle cell proliferation and differentiation
- **my reading:** yes

### `n0218` — unnameable

- **first name:** Insulin-family receptor tyrosine kinase signaling
- **check 1:** uncovered — PI3K/AKT activation downstream of growth factor receptors, Signaling by ALK, Signaling by LTK
  - *This cluster covers PI3K/AKT activation from all growth factor receptors broadly, not exclusively insulin-family receptor signaling, so it only partly overlaps rather than being a strict sub-category. ALK and LTK are receptor tyrosine kinases unrelated to the insulin receptor family, whereas IRS activation and Signal attenuation are part of insulin/IGF receptor signaling.*
- **re-ask 1:** Insulin receptor family RTK signaling
- **check 2:** still uncovered — PI3K/AKT activation downstream of growth factor receptors, Signaling by ALK, Signaling by LTK
  - *This cluster broadly covers PI3K/AKT activation from multiple growth factor receptors, not specifically limited to the insulin receptor family RTKs. ALK and LTK are anaplastic lymphoma kinase family receptors, distinct from insulin receptor family RTKs, whereas IRS activation and Signal attenuation are part of insulin receptor signaling cascade.*
- **re-ask 2, widening from the child** 'PI3K/AKT activation downstream of growth factor receptors': Insulin receptor family RTK signaling and attenuation
- **check 3:** still uncovered — PI3K/AKT activation downstream of growth factor receptors, Signaling by ALK, Signaling by LTK
  - *This cluster covers PI3K/AKT activation downstream of growth factor receptors broadly, not limited to insulin receptor family RTKs, so it is broader than and only partly overlaps the parent. ALK and LTK are receptor tyrosine kinases unrelated to the insulin receptor family, whereas IRS activation and Signal attenuation are part of insulin receptor signaling.*
- **final:** UNNAMEABLE — *contents have no common name: PI3K/AKT activation downstream of growth factor receptors, Signaling by ALK, Signaling by LTK*
- **children:** PI3K/AKT activation downstream of growth factor receptors
- **my reading:** yes

### `n0262` — unnameable

- **first name:** Vacuole and lysosome trafficking
- **check 1:** uncovered — Intracellular vesicle transport
  - *Intracellular vesicle transport is a broader category encompassing many trafficking pathways beyond just vacuole and lysosome trafficking. All listed pathways relate to vacuole/lysosome trafficking and localization, fitting under the parent theme.*
- **re-ask 1:** Post-Golgi and endolysosomal vesicle trafficking
- **check 2:** still uncovered — Intracellular vesicle transport
  - *Intracellular vesicle transport is a broader category encompassing many trafficking routes beyond post-Golgi and endolysosomal pathways, so it is not a sub-category. All listed pathways relate to post-Golgi vesicle transport and vacuolar/endolysosomal trafficking, fitting the parent theme.*
- **re-ask 2, widening from the child** 'Intracellular vesicle transport': Vesicular transport to the vacuole/lysosome
- **check 3:** still uncovered — Intracellular vesicle transport, lytic vacuole organization
  - *Intracellular vesicle transport is a broader category encompassing many trafficking routes beyond just vacuole/lysosome transport, so it is not a strict sub-category. Most pathways relate to vesicle-mediated transport to the vacuole, but lytic vacuole organization concerns vacuole structural maintenance rather than vesicular transport.*
- **final:** UNNAMEABLE — *contents have no common name: Intracellular vesicle transport, lytic vacuole organization*
- **children:** Intracellular vesicle transport
- **my reading:** no

### `n0732` — covered after re-ask

- **first name:** Vesicular trafficking to the vacuole and lysosome
- **check 1:** uncovered — Intracellular vesicle transport
  - *Intracellular vesicle transport is a broader category encompassing many trafficking routes beyond just vacuole/lysosome targeting, so it is not fully a sub-category. All four pathways relate to vesicle-mediated trafficking and fusion processes leading to the vacuole/lysosome, fitting the parent theme.*
- **re-ask 1:** Vesicle trafficking and organelle fusion
- **check 2:** covers everything
  - *Intracellular vesicle transport is a sub-category fully encompassed by vesicle trafficking and organelle fusion. All four pathways directly relate to vesicle trafficking, organelle fusion, or vacuolar protein localization, fitting the parent theme.*
- **saved:** Vesicle trafficking and organelle fusion
- **passed the check:** Vesicle trafficking and organelle fusion (MATCH)
- **children:** Intracellular vesicle transport
- **my reading:** yes

### `n0706` — unnameable

- **first name:** Muscle fibre membrane and size homeostasis
- **check 1:** uncovered — Sarcomere assembly and contraction, caveolin-mediated endocytosis
  - *Sarcomere assembly and contraction pertains to contractile apparatus function, not membrane or fibre size homeostasis, so it is not a sub-category of the parent. Negative regulation of cell size and muscle cell cellular homeostasis fit the membrane/size theme, but caveolin-mediated endocytosis concerns vesicular trafficking rather than muscle fibre membrane or size regulation.*
- **re-ask 1:** Muscle fibre structural and size homeostasis
- **check 2:** still uncovered — Sarcomere assembly and contraction, caveolin-mediated endocytosis
  - *Sarcomere assembly and contraction concerns contractile apparatus function and assembly, which is broader than and only partly overlaps with fibre structural/size homeostasis. Caveolin-mediated endocytosis is a vesicle trafficking process unrelated to muscle fibre structure or size regulation, while the other two pathways relate to cell size/homeostasis regulation applicable to muscle fibres.*
- **re-ask 2, widening from the child** 'Sarcomere assembly and contraction': Muscle fiber structural and membrane homeostasis
- **check 3:** still uncovered — Sarcomere assembly and contraction, negative regulation of cell size
  - *Sarcomere assembly and contraction relates to muscle contractile machinery and force generation, which is broader than and distinct from structural/membrane homeostasis of muscle fibers. Negative regulation of cell size pertains to general growth control rather than muscle fiber structure/membrane homeostasis, while muscle cell cellular homeostasis and caveolin-mediated endocytosis relate to muscle membrane/structural maintenance.*
- **final:** UNNAMEABLE — *contents have no common name: Sarcomere assembly and contraction, negative regulation of cell size*
- **children:** Sarcomere assembly and contraction
- **my reading:** yes

### `n0495` — unnameable

- **first name:** Galactose and pentose metabolism disorders
- **check 1:** uncovered — Amino sugar and carbohydrate catabolism, glycoside metabolic process
  - *Amino sugar and carbohydrate catabolism is a broader category covering general carbohydrate breakdown, not strictly a subset of galactose and pentose metabolism disorders. Glycoside metabolic process concerns general glycosidic bond chemistry unrelated specifically to galactose or pentose metabolism disorders, while the others relate directly to galactose/pentose metabolism themes.*
- **re-ask 1:** Monosaccharide and glycoside metabolism
- **check 2:** still uncovered — Amino sugar and carbohydrate catabolism
  - *This cluster covers broader carbohydrate catabolism beyond just monosaccharides and glycosides, including amino sugars and general carbohydrate breakdown pathways. All listed pathways relate to monosaccharide (galactose, pentose) or glycoside metabolism and its disorders, fitting the parent theme.*
- **re-ask 2, widening from the child** 'Amino sugar and carbohydrate catabolism': Amino sugar, galactose and glycoside metabolism
- **check 3:** still uncovered — Amino sugar and carbohydrate catabolism
  - *This child is broader, covering general carbohydrate catabolism beyond amino sugar, galactose and glycoside metabolism, so it only partially overlaps the parent. All four pathways relate to galactose/amino sugar/glycoside metabolism and its associated disorders, so they fall under the parent theme.*
- **final:** UNNAMEABLE — *contents have no common name: Amino sugar and carbohydrate catabolism*
- **children:** Amino sugar and carbohydrate catabolism
- **my reading:** no

### `n0181` — unnameable

- **first name:** Platelet activation and adhesion regulation
- **check 1:** uncovered — Hemostasis and thrombin/PAR signalling
  - *Hemostasis and thrombin/PAR signalling is a broader coagulation-related process that only partly overlaps with platelet activation and adhesion regulation, rather than being wholly a subset of it. All three pathways relate to platelet activation processes or cell adhesion regulation, fitting the parent theme.*
- **re-ask 1:** Platelet activation and haemostasis
- **check 2:** still uncovered — Hemostasis and thrombin/PAR signalling, regulation of homotypic cell-cell adhesion
  - *Hemostasis is a broader concept encompassing coagulation and vascular processes beyond platelet activation, so it only partly overlaps rather than being a subcategory. Platelet degranulation and negative regulation of platelet activation are directly part of platelet activation/haemostasis, but homotypic cell-cell adhesion regulation is a general cell adhesion process not specific to this theme.*
- **re-ask 2, widening from the child** 'Hemostasis and thrombin/PAR signalling': Platelet activation and hemostatic signalling
- **check 3:** still uncovered — Hemostasis and thrombin/PAR signalling, regulation of homotypic cell-cell adhesion
  - *Hemostasis is a broader process encompassing coagulation cascade and vascular mechanisms beyond platelet activation and hemostatic signalling specifically. Platelet degranulation and negative regulation of platelet activation are directly part of platelet activation/hemostasis, while homotypic cell-cell adhesion regulation is a general adhesion process not specific to platelet/hemostatic signalling.*
- **final:** UNNAMEABLE — *contents have no common name: Hemostasis and thrombin/PAR signalling, regulation of homotypic cell-cell adhesion*
- **children:** Hemostasis and thrombin/PAR signalling
- **my reading:** no

### `n0236` — unnameable

- **first name:** Pancreatic endocrine lineage specification and beta cell mass control
- **check 1:** uncovered — Transcriptional specification of endoderm-derived epithelia
  - *This cluster is broader, covering endoderm-derived epithelia generally (e.g., liver, lung, gut) rather than being limited to pancreatic endocrine lineage specification and beta cell mass control. All four pathways relate to pancreatic endocrine lineage specification or beta cell mass control (proliferation, apoptosis, and progenitor/precursor gene expression regulation).*
- **re-ask 1:** Pancreatic endocrine development and beta cell mass regulation
- **check 2:** still uncovered — Transcriptional specification of endoderm-derived epithelia
  - *This cluster is broader, covering endoderm-derived epithelia generally (e.g., liver, lung, gut), not specifically pancreatic endocrine development and beta cell mass regulation. All listed pathways relate to pancreatic endocrine/beta cell development and mass regulation, fitting the parent theme.*
- **re-ask 2, widening from the child** 'Transcriptional specification of endoderm-derived epithelia': Transcriptional control of pancreatic endocrine development and beta cell mass
- **check 3:** still uncovered — Transcriptional specification of endoderm-derived epithelia, type B pancreatic cell proliferation, negative regulation of type B pancreatic cell apoptotic process
  - *This child is broader, covering endoderm-derived epithelia generally rather than being limited to pancreatic endocrine development and beta cell mass. These concern cellular proliferation and apoptosis regulation rather than transcriptional control of developmental gene expression, while the other two directly describe transcriptional regulation in pancreatic progenitor stages.*
- **final:** UNNAMEABLE — *contents have no common name: Transcriptional specification of endoderm-derived epithelia, type B pancreatic cell proliferation, negative regulation of type B pancreatic cell apoptotic process*
- **children:** Transcriptional specification of endoderm-derived epithelia
- **my reading:** no

### `n0473` — covered

- **first name:** Fat-soluble vitamin and steroid hormone metabolism
- **check 1:** covers everything
  - *Sex steroid and adrenocortical hormone synthesis refers to steroid hormone production, which falls under steroid hormone metabolism. All listed pathways relate to fat-soluble vitamin (vitamin D) metabolism and its regulation/defects, fitting the parent theme.*
- **saved:** Fat-soluble vitamin and steroid hormone metabolism
- **passed the check:** Fat-soluble vitamin and steroid hormone metabolism (MATCH)
- **children:** Sex steroid and adrenocortical hormone synthesis
- **my reading:** yes

### `n0125` — unnameable

- **first name:** Autophagic and endosomal degradative sorting
- **check 1:** uncovered — Endomembrane trafficking and turnover, Metalloprotease DUBs
  - *This cluster is broader, covering general endomembrane trafficking beyond just autophagic and endosomal degradative sorting. The first three pathways directly concern autophagic and endosomal sorting/degradation, while Metalloprotease DUBs relates to deubiquitination enzyme activity, a different biological process.*
- **re-ask 1:** Membrane trafficking and ubiquitin-dependent degradation
- **check 2:** still uncovered — Endomembrane trafficking and turnover
  - *This cluster includes general endomembrane turnover processes beyond just ubiquitin-dependent degradation and trafficking, so it is broader than the parent category. All four pathways relate to membrane trafficking (microautophagy, piecemeal microautophagy of the nucleus, multivesicular body sorting) or ubiquitin-dependent degradation (Metalloprotease DUBs), fitting the parent theme.*
- **re-ask 2, widening from the child** 'Endomembrane trafficking and turnover': Endomembrane trafficking, autophagy and deubiquitination
- **check 3:** still uncovered — Endomembrane trafficking and turnover
  - *This child only covers trafficking and turnover, omitting autophagy and deubiquitination aspects, so it is narrower/partly overlapping rather than fully a sub-category. All listed pathways relate to autophagy, endomembrane trafficking, or deubiquitination processes covered by the parent theme.*
- **final:** UNNAMEABLE — *contents have no common name: Endomembrane trafficking and turnover*
- **children:** Endomembrane trafficking and turnover
- **my reading:** no

### `n0496` — unnameable

- **first name:** Host-pathogen metal ion competition
- **check 1:** uncovered — Antimicrobial peptide-mediated humoral defence, detoxification of cadmium ion
  - *Antimicrobial peptide-mediated humoral defence is a broader innate immune defense mechanism, not specifically a sub-category of metal ion competition between host and pathogen. Cadmium detoxification concerns toxic metal defense rather than host-pathogen competition for essential metal ions, while iron import and host metal assimilation directly relate to that competitive theme.*
- **re-ask 1:** Innate antimicrobial and metal ion defence
- **check 2:** still uncovered — iron import into cell
  - *Antimicrobial peptide-mediated humoral defence is a subset of innate antimicrobial defence mechanisms. Cadmium detoxification and host metal ion assimilation relate to metal/innate defence themes, while iron import into cell is a general nutrient transport process unrelated to antimicrobial or defensive metal handling.*
- **final:** UNNAMEABLE — *contents have no common name: iron import into cell*
- **children:** Antimicrobial peptide-mediated humoral defence
- **my reading:** no

---

## Controls, in full

### `n0060` — Drug-resistant receptor tyrosine kinase mutants

- clean
- *FLT3 is a receptor tyrosine kinase, so drug-resistant FLT3 mutants are a subset of drug-resistant RTK mutants. All three pathways describe receptor tyrosine kinase mutants (KIT, PDGFR, ALK) resistant to drugs, fitting the parent theme.*

### `n0708` — Mismatch repair and double-strand break repair

- clean
- *Homologous recombination repair is a specific mechanism of double-strand break repair, fully falling under the parent category. All listed pathways relate to mismatch repair defects or double-strand break repair/response, matching the parent theme.*

### `n0010` — Base excision repair

- clean
- *The glycosylase step is a specific sub-step entirely within base excision repair, so it is fully covered. All three pathways relate to base excision repair biology, including depyrimidination which is a form of DNA damage addressed by this repair pathway.*

### `n0017` — DNA replication initiation and elongation

- **FLAGGED:** DNA replication and licensing
- *Licensing is a pre-initiation step distinct from initiation and elongation, making this cluster broader than the parent rather than a strict subset. All three pathways directly concern DNA replication initiation or elongation processes, matching the parent theme.*

### `n0040` — Cardiac action potential generation and conduction

- clean
- *Cardiac conduction system electrical propagation is a sub-process fully encompassed by cardiac action potential generation and conduction. All three pathways relate to cardiac action potential generation and conduction, matching the parent theme.*

### `n0039` — Blood coagulation cascade and its defects

- clean
- *Defective coagulation factor variants causing bleeding disorders are a direct subset of blood coagulation cascade defects. All listed pathways relate directly to coagulation cascade processes or their defects, fitting the parent theme.*

### `n0070` — TGF-beta/BMP-SMAD signalling

- clean
- *The regulation of TGF-beta/BMP-SMAD signalling is a sub-category fully contained within the parent pathway. All three pathways concern SMAD-mediated TGF-beta/BMP signal transduction and thus fall under the parent theme.*

### `n0014` — Complement activation and humoral defence

- clean
- *Complement cascade activation and regulation is a sub-category wholly within complement activation and humoral defence. All three pathways relate to complement activation and humoral immune defense mechanisms, including opsonization and complement-mediated humoral response regulation.*

### `n0085` — Heart morphogenesis and chamber development

- clean
- *Cardiac septation and outflow tract morphogenesis is a subset of heart morphogenesis and chamber development processes. All listed pathways concern heart morphogenesis, chamber development, or related cardiac tissue development, fitting the parent theme.*

### `n0123` — Cytokine-JAK-STAT signaling

- clean
- *IL-6/gp130-JAK-STAT3 signaling is a specific sub-pathway of cytokine-JAK-STAT signaling, fully contained within it. All listed pathways relate to cytokine signaling and/or JAK-STAT pathway activity, fitting within the Cytokine-JAK-STAT signaling theme.*

