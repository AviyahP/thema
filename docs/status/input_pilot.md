# Blind input pilot -- which input a theme name needs

*Thirty leaf themes of `recurrent_dag_consensus_centred`, seed 20260927, prompt `name-v3`. Each theme was named three times from three different views of the same members. The three candidates below are in a per-theme shuffled order. Which letter is which view is in `input_pilot_key.tsv`; do not open it until the names are judged.*

For each theme, ask of each candidate: is it true of every member at inclusion 0.5 or above, and would it let you find this theme in a list of 873?

---

## pure_go (10 themes)

### n0065 -- 7 members

- **somatic diversification of immune receptors** [go] (inclusion 1.00)
  - Antigen receptor diversity is not inherited but built in each developing lymphocyte, and this somatic diversification of immune receptors is how a limited germline repertoire yields antibodies and T cell receptors against essentially any pathogen.
- **pro-B cell differentiation** [go] (inclusion 1.00)
  - Pro-B cell differentiation is the first committed step of B lymphopoiesis, in which a lymphoid progenitor acquires pro-B identity and begins rearranging the immunoglobulin heavy chain locus by joining D and J segments.
- **pre-B cell differentiation** [go] (inclusion 1.00)
  - Pre-B cell differentiation is the stage at which a pro-B cell rearranges its immunoglobulin heavy chain V, D and J segments and displays the resulting mu chain, the step that decides whether a developing lymphocyte can go on to make antibody.
- **regulation of immunoglobulin production** [go] (inclusion 1.00)
  - Antibody output by B cells is tuned rather than simply switched on, and the regulation of immunoglobulin production covers the signals and machinery that set how much antibody of which class a response generates.
- **B cell mediated immunity** [go] (inclusion 1.00)
  - B cell mediated immunity covers the effector arm of humoral defence: antibody production, isotype diversification, and the downstream systems that translate antibody binding into pathogen clearance.
- **isotype switching to IgA isotypes** [go] (inclusion 0.60)
  - Mucosal immunity depends on B cells abandoning IgM and rewriting their heavy chain locus to produce IgA, the antibody secreted across gut, airway and mammary epithelium to neutralise microbes without provoking inflammation.
- **double-strand break repair via classical nonhomologous end joining** [go] (inclusion 0.27)
  - Double-strand breaks are the most dangerous lesions a genome can carry, and classical nonhomologous end joining is the pathway that rejoins them directly, without needing a homologous template, throughout the cell cycle.

- **A.** B cell development and antibody diversification
  - Core members cover B cell differentiation stages, immunoglobulin production and receptor diversification (including isotype switching at 0.60); the weakly included classical NHEJ (0.27) is excluded from the name though mechanistically linked to these processes.
- **B.** B cell development and antibody diversification
  - Members 1-5 cover V(D)J recombination, B cell developmental checkpoints, and antibody class switching/somatic hypermutation with their downstream regulation and effector function. Member 6 (IgA class switching, 0.60) fits within antibody diversification. Member 7 (0.27, general classical NHEJ) is only loosely tied via its role in V(D)J recombination and is excluded from the core claim.
- **C.** B cell development and antibody diversification
  - Covers B lymphopoiesis (pro-B, pre-B differentiation), immunoglobulin gene recombination/diversification, and regulation of antibody production/class switching shared by all core members; the weakly included IgA-specific switching (0.60) and generic NHEJ repair (0.27) are subsumed as instances of this diversification machinery.

### n0076 -- 6 members

- **ribosomal large subunit export from nucleus** [go] (inclusion 1.00)
  - Ribosome production begins in the nucleolus but translation happens in the cytoplasm, and export of the assembled large subunit is the step that bridges the two.
- **cleavage in ITS2 between 5.8S rRNA and LSU-rRNA of tricistronic rRNA transcript (SSU-rRNA, 5.8S rRNA, LSU-rRNA)** [go] (inclusion 1.00)
  - Ribosomal RNA is transcribed as one long precursor carrying the small subunit rRNA, 5.8S and the large subunit rRNA in tandem, and the spacers between them must be removed for functional ribosomes to be made.
- **rRNA 5'-end processing** [go] (inclusion 1.00)
  - Ribosome production begins with a long polycistronic rRNA precursor that must be cut and trimmed at defined points, and forming the mature 5' end of rRNA is one of those steps.
- **regulation of protein localization to nucleolus** [go] (inclusion 1.00)
  - The nucleolus is where ribosomal RNA is transcribed and pre-ribosomes are assembled, and proteins must be delivered into and retained within it for that work to proceed; regulation of protein localization to the nucleolus controls which factors accumulate there and for how long.
- **5S class rRNA transcription by RNA polymerase III** [go] (inclusion 0.33)
  - Every ribosome needs one copy of 5S rRNA, and this is the transcription route that supplies it.
- **transcription elongation by RNA polymerase I** [go] (inclusion 0.31)
  - Ribosome production begins with the synthesis of the large ribosomal RNA precursor, and transcription elongation by RNA polymerase I is the processive phase in which that long transcript is actually made after the enzyme has cleared the rDNA promoter.

- **A.** Ribosome biogenesis in the nucleolus
  - All members concern nucleolar steps of ribosome production—rRNA processing, subunit assembly, nucleolar protein localization, and export of the large subunit—including the weakly included 5S rRNA transcription (0.33) and Pol I elongation (0.31) pathways, both of which also feed rRNA/ribosome biogenesis.
- **B.** rRNA processing and ribosome biogenesis
  - Members at inclusion ≥0.5 cover rRNA processing/cleavage, ribosomal subunit nuclear export, and nucleolar protein localization, all core steps of ribosome biogenesis; weaker members (Pol III/Pol I transcription of rRNA) fit the same broader process but are excluded from the core name.
- **C.** Ribosome biogenesis and nucleolar rRNA processing
  - Core members (inclusion 1.00) cover pre-60S export, ITS2 spacer cleavage, rRNA 5' processing, and nucleolar protein localization for ribosome assembly; the weaker members (5S rRNA transcription, Pol I elongation, inclusion 0.31-0.33) also feed rRNA supply for ribosome production, so the shared theme is nucleolar rRNA processing and ribosome subunit maturation.

### n0085 -- 7 members

- **cardiac muscle tissue development** [go] (inclusion 1.00)
  - Cardiac muscle tissue development covers the whole trajectory by which mesodermal precursors become beating, force-generating myocardium, from lineage specification through chamber growth, sarcomere assembly and the maturation of conduction and calcium-handling machinery.
- **cardiac cell development** [go] (inclusion 1.00)
  - Cardiac cell development covers the whole trajectory of a heart cell, from specification in the early mesoderm through sarcomere assembly and the growth that follows birth.
- **cardiac muscle cell differentiation** [go] (inclusion 1.00)
  - Cardiac muscle cell differentiation is the route by which mesodermal precursors become striated, spontaneously contracting cardiomyocytes, the cells that generate the heartbeat and that the adult heart cannot readily replace after injury.
- **muscle tissue development** [go] (inclusion 1.00)
  - Muscle tissue development covers the whole path from mesodermal precursors to contractile skeletal, cardiac and smooth muscle, the tissues that move the skeleton, pump blood and control vessel and gut tone.
- **muscle structure development** [go] (inclusion 0.89)
  - Muscle structure development covers the whole arc by which mesodermal progenitors become contractile cells and tissues, from lineage specification through fusion, sarcomere assembly and maturation, in skeletal, cardiac and smooth muscle alike.
- **muscle cell development** [go] (inclusion 0.88)
  - Once a progenitor has already committed to a muscle fate, this programme carries it through to a functional contractile cell: myoblast fusion, assembly of sarcomeres, and the maturation of skeletal, cardiac and smooth muscle into tissue that can generate force.
- **regulation of cardiocyte differentiation** [go] (inclusion 0.76)
  - Cardiac muscle cells are specified from mesodermal progenitors during heart development, and this pathway covers the inputs that set how fast and how far that commitment proceeds.

- **A.** Cardiac and skeletal muscle differentiation
  - All members describe the developmental programme from mesodermal progenitor to differentiated, sarcomere-bearing muscle cell/tissue, spanning cardiac (pathways 1,2,3,7) and broader striated/smooth muscle (4,5,6) lineages, driven by shared transcription factors (NKX2-5, GATA4, TBX5, MEF2C, MYOD1) and structural/calcium-handling maturation.
- **B.** Cardiac and skeletal muscle development
  - All members describe the specification, differentiation and maturation of muscle cells and tissue, including cardiac-specific and broader skeletal/smooth muscle developmental programmes.
- **C.** Cardiac muscle cell development and differentiation
  - All members concern development or differentiation of cardiac/muscle tissue and cells, including regulation of cardiocyte differentiation.

### n0139 -- 3 members

- **negative regulation of D-glucose transmembrane transport** [go] (inclusion 1.00)
  - Glucose uptake into cells is not simply turned on by insulin; it is actively restrained, and this negative regulation of glucose transport across membranes sets how much sugar a tissue takes up at a given hormonal signal.
- **negative regulation of glycogen biosynthetic process** [go] (inclusion 1.00)
  - Glycogen is the cell's rapidly mobilisable glucose store, and this pathway describes the braking side of its synthesis avel keeping storage in check when insulin signalling is low or fuel demand is high.
- **positive regulation of D-glucose import across plasma membrane** [go] (inclusion 1.00)
  - Muscle and fat cells take up glucose from blood only when told to, and this pathway covers the signals that switch that uptake on, raising the rate of glucose import across the plasma membrane.

- **A.** Regulation of glucose transport and glycogen synthesis
  - All three members regulate either glucose transmembrane transport/import or glycogen biosynthesis.
- **B.** Insulin-regulated glucose uptake and glycogen storage
  - All three concern insulin signalling's control over glucose transporter trafficking (positive and negative) and the coupled restraint of glycogen synthesis, sharing overlapping regulators like GRB10 and ENPP1.
- **C.** Insulin regulation of glucose uptake and glycogen synthesis
  - All three concern insulin signalling components (GRB10, ENPP1, PI3K/AKT axis) that regulate either glucose transporter trafficking or glycogen synthase activity, positively or negatively.

### n0172 -- 6 members

- **cortical microtubule organization** [go] (inclusion 1.00)
  - Microtubules that reach the cell periphery must be captured, tethered and their growth restrained at the cortex just under the plasma membrane, and cortical microtubule organization is the machinery that does this.
- **establishment of epithelial cell apical/basal polarity** [go] (inclusion 1.00)
  - Epithelial sheets only work as barriers and secretory surfaces because each cell distinguishes an apical face from a basolateral one, and establishing that apicobasal polarity is what this biology does.
- **establishment or maintenance of monopolar cell polarity** [go] (inclusion 1.00)
  - Cells that build a single dominant axis — a leading edge, an apical surface, an outgrowing neurite — depend on the establishment and maintenance of monopolar polarity, which commits one region of the cortex to growth or specialized structure while suppressing the rest.
- **podocyte cell migration** [go] (inclusion 1.00)
  - Podocytes are the specialized epithelial cells that wrap the glomerular capillaries and, with their interdigitating foot processes, form the final barrier that keeps protein in the blood.
- **establishment of centrosome localization** [go] (inclusion 0.76)
  - Where a cell places its centrosome determines where its microtubules radiate from, and therefore the orientation of the spindle, the direction of migration, and the site of cilium formation.
- **septin ring organization** [go] (inclusion 0.44)
  - Septins form filamentous rings and collars at the cell cortex that act as diffusion barriers and scaffolds, most conspicuously at the cleavage furrow during cytokinesis and at the base of cilia and dendritic spines.

- **A.** Cortical polarity and microtubule anchoring
  - Members 1-3 and 5 (0.76) share establishment of cortical/apicobasal polarity linked to microtubule or centrosome positioning via CDC42/RHOA, ezrin/moesin and cortical scaffolds. Pathway 4 fits via KANK-linked cytoskeletal-adhesion coupling in podocyte polarity/migration. Pathway 6 (0.44, weakly included) concerns septin ring/cytokinesis and is excluded from the name.
- **B.** Cell polarity and cytoskeletal organization
  - Members at 0.5+ concern establishment of cell polarity (epithelial apical/basal, monopolar), cortical microtubule organization, and podocyte migration, all cytoskeleton-dependent polarity processes; centrosome localization also fits as a polarity-related cytoskeletal event. Septin ring organization (0.44) is excluded from the core claim but is cytoskeletal in nature.
- **C.** Cortical polarity and cytoskeletal anchoring
  - Members converge on establishing and maintaining cortical cell polarity (apicobasal, monopolar, microtubule) via cortex-cytoskeleton-adhesion linkages, including centrosome positioning; septin ring organization (0.44) is only weakly included and less central.

### n0193 -- 3 members

- **collecting duct development** [go] (inclusion 1.00)
  - The kidney's collecting duct is the final segment urine passes through, and its development builds the tubule that later answers vasopressin and aldosterone to set water, electrolyte and acid-base balance.
- **metanephric tubule morphogenesis** [go] (inclusion 1.00)
  - Shaping the epithelial tubules of the metanephros is the step that turns induced nephron progenitors into the functional plumbing of the permanent kidney, generating the proximal tubule, loop of Henle and distal segments that reabsorb solutes and water from filtrate.
- **metanephric collecting duct development** [go] (inclusion 1.00)
  - The collecting duct of the metanephros is the final segment of the nephron's drainage route, and its development yields the epithelium that adjusts water, electrolyte and acid-base balance under vasopressin and aldosterone control before urine passes into the ureter.

- **A.** Metanephric collecting duct development  `mechanical: FAIL`
  - All three pathways concern morphogenesis and development of the metanephric collecting duct/tubule system.
- **B.** Kidney tubule and collecting duct morphogenesis
  - All three describe nephron/collecting duct epithelial development from ureteric bud branching and progenitor induction, sharing WNT9B, PAX2/8, hedgehog signalling and PKD1, culminating in mature tubule/duct function and cystic or dysplastic disease when disrupted.
- **C.** Metanephric collecting duct and tubule development
  - All three describe branching morphogenesis and epithelial patterning of the developing kidney's collecting duct and nephron tubules, sharing genes like PAX2/PAX8, WNT9B/WNT7B, hedgehog signalling and PKD1.

### n0247 -- 5 members

- **platelet-derived growth factor receptor-alpha signaling pathway** [go] (inclusion 1.00)
  - Signalling through the alpha-type platelet-derived growth factor receptor drives proliferation, migration and survival in mesenchymal cells, and is the axis by which PDGF-A instructs development of lung alveoli, intestinal villi, oligodendrocyte precursors, and craniofacial and skeletal mesenchyme.
- **platelet-derived growth factor receptor-beta signaling pathway** [go] (inclusion 1.00)
  - Signalling through the beta-type platelet-derived growth factor receptor drives the recruitment, proliferation and migration of mesenchymal cells — pericytes around capillaries, vascular smooth muscle cells, fibroblasts — and so shapes vessel maturation, wound repair and the fibrotic response.
- **interleukin-11-mediated signaling pathway** [go] (inclusion 1.00)
  - Interleukin-11 is a gp130-family cytokine that acts on stromal and epithelial cells to drive tissue remodelling, and interleukin-11-mediated signalling is the route by which that message is read.
- **regulation of platelet-derived growth factor receptor-beta signaling pathway** [go] (inclusion 1.00)
  - PDGF receptor-beta signalling drives proliferation and migration of mesenchymal cells — pericytes, vascular smooth muscle, fibroblasts — and its control determines whether vessels acquire a stable mural coat or whether tissue responds to injury with fibrosis and neointima formation.
- **collagen-activated tyrosine kinase receptor signaling pathway** [go] (inclusion 0.75)
  - Cells read the collagen in their surroundings partly through receptor tyrosine kinases, and this collagen-activated signalling converts that contact into changes in adhesion, migration, matrix remodelling and gene expression.

- **A.** Receptor tyrosine kinase signalling in mesenchymal cells
  - Members 1, 2 and 4 all concern PDGFR-alpha/beta signalling in mesenchymal cells driving proliferation, migration and fibrosis; member 3 (IL-11/gp130-JAK-STAT3) drives the same fibroblast-to-myofibroblast fibrotic outcome in stromal cells; member 5 (DDR1/2 and GP6 collagen receptors) is a weaker (0.75) fit, sharing the theme of matrix-sensing receptor signalling controlling adhesion, migration and fibrotic remodelling rather than classic RTK-driven proliferation.
- **B.** PDGF receptor signalling
  - Three of five members are directly PDGFR-alpha/beta signalling or its regulation; interleukin-11 signalling and collagen-activated tyrosine kinase receptor signalling do not share PDGFR biology, but the core majority defines the theme, with those two noted as weaker or divergent inclusions.
- **C.** Mesenchymal growth factor receptor signalling and fibrosis
  - PDGFR-alpha, PDGFR-beta and its regulation are the core; interleukin-11 signalling and collagen-activated tyrosine kinase receptor signalling (0.75) share the same theme of receptor-driven mesenchymal cell proliferation/migration culminating in tissue remodelling and fibrosis, though via distinct receptors (gp130/JAK-STAT, DDR/GP6) rather than PDGFR itself.

### n0335 -- 5 members

- **locomotion involved in locomotory behavior** [go] (inclusion 1.00)
  - Whole-body movement from place to place, as the motor output of behaviour, depends on intact motor circuitry and on the neuromodulatory signals that set how much an animal moves.
- **exploration behavior** [go] (inclusion 1.00)
  - How an animal responds to a novel environment or stimulus s exploring, rearing, approaching or avoiding s is a readout of arousal, anxiety and motivation, and it is the behavioural assay through which much neuropsychiatric gene function is measured.
- **swimming behavior** [go] (inclusion 1.00)
  - Swimming behaviour is a whole-organism locomotor response to sensory or internal cues, and it is used experimentally as a readout of neural circuit integrity, motivation and stress coping.
- **regulation of dopamine receptor signaling pathway** [go] (inclusion 1.00)
  - Dopamine signalling sets the gain on movement, motivation and reward, and the processes that tune it determine how strongly a dopaminergic input is felt by the receiving neuron.
- **walking behavior** [go] (inclusion 1.00)
  - Walking behavior is the coordinated, alternating limb movement that carries an animal over ground, and it depends on intact spinal locomotor circuitry, cerebellar and basal ganglia control, and healthy motor axons.

- **A.** Locomotor and exploratory behaviour circuits
  - All five pathways concern whole-organism motor behaviours (walking, swimming, exploration, general locomotion) and the neuromodulatory (dopaminergic, peptidergic) and neuronal-integrity genes that set circuit tone and motor output.
- **B.** Locomotory behavior and its dopaminergic regulation
  - Four members are specific locomotory behaviors (walking, swimming, exploration, locomotion in behavior context); the fifth links dopamine receptor signaling, which is a known regulator of these behaviors.
- **C.** Neural circuit control of locomotor behaviour
  - All five pathways describe genes and circuits governing motor behaviours (locomotion, walking, swimming, exploration) and dopaminergic/neuromodulatory tone, with neurodegenerative and synaptic genes included insofar as they disrupt these behavioural outputs.

### n0343 -- 5 members

- **bud elongation involved in lung branching** [go] (inclusion 1.00)
  - Lung airways are built by repeated budding of epithelium into surrounding mesenchyme, and bud elongation is the growth phase in which a newly specified tip extends outward before it branches again.
- **dichotomous subdivision of an epithelial terminal unit** [go] (inclusion 1.00)
  - Branched glandular and tubular organs acquire their form by repeatedly splitting their growing tips in two, and this dichotomous subdivision of an epithelial terminal unit is that splitting event: an epithelial cord, rod or tube bifurcating at its end.
- **epithelial cell proliferation involved in salivary gland morphogenesis** [go] (inclusion 1.00)
  - Salivary glands form by branching morphogenesis, in which an epithelial bud invades surrounding mesenchyme and repeatedly divides and clefts to build the ductal tree and secretory end buds.
- **regulation of morphogenesis of an epithelium** [go] (inclusion 1.00)
  - Epithelial sheets acquire their shape by branching, folding, budding and cavitating, and this pathway covers the signals that set how far and how fast that remodelling goes.
- **ectodermal cell differentiation** [go] (inclusion 0.39)
  - Ectodermal cell differentiation is the commitment and maturation of unspecialized cells into the derivatives of the embryonic ectoderm — epidermis and its appendages, mammary and other surface epithelia, and neural tissue.

- **A.** Epithelial branching morphogenesis
  - The core members (lung bud elongation, terminal unit subdivision, salivary gland epithelial proliferation, epithelium morphogenesis regulation) all describe branching/morphogenesis of epithelial tissue. Ectodermal cell differentiation (0.39) is excluded as it concerns a different, broader process.
- **B.** Branching morphogenesis of epithelial organs
  - Four members at full inclusion describe epithelial tip outgrowth, dichotomous splitting, and its proliferative and regulatory control across lung, salivary gland, kidney and mammary branching. The weakly included ectodermal cell differentiation member (0.39) is excluded, as it concerns broader ectodermal fate specification rather than branching itself.
- **C.** Branching morphogenesis of epithelial organs
  - Pathways 1-4 all concern reciprocal epithelial-mesenchymal signalling controlling tip growth, clefting/splitting, and gland/airway ductal branching (lung, kidney, salivary, mammary). Pathway 5, at low inclusion (0.39), concerns ectodermal cell fate differentiation rather than branching and is excluded.

### n0634 -- 7 members

- **facial nerve morphogenesis** [go] (inclusion 1.00)
  - Formation of the facial nerve builds the seventh cranial nerve that drives the muscles of facial expression, carries taste from the anterior tongue, and supplies lacrimal, nasal and oral secretory glands.
- **thyroid gland development** [go] (inclusion 1.00)
  - The thyroid arises from a patch of pharyngeal endoderm that buds, migrates down the neck, and differentiates into follicles capable of iodinating thyroglobulin, and this developmental programme determines whether an infant can make thyroid hormone at all.
- **semicircular canal morphogenesis** [go] (inclusion 1.00)
  - The semicircular canals are the fluid-filled loops of the inner ear that sense head rotation, and their morphogenesis converts flat epithelial pouches of the otic vesicle into three orthogonal ducts.
- **face development** [go] (inclusion 1.00)
  - Face development is the shaping of the ventral head — jaws, palate, midface, lip and surrounding skeleton — from neural crest cells that migrate into the pharyngeal arches and frontonasal prominence and there condense into cartilage, bone and connective tissue.
- **semicircular canal development** [go] (inclusion 1.00)
  - The semicircular canals are the three looped ducts of the inner ear that sense angular head acceleration and supply the vestibular input needed for balance, gaze stabilisation and posture.
- **vestibulocochlear nerve formation** [go] (inclusion 0.62)
  - Hearing and balance depend on a dedicated cranial nerve linking the inner ear to the brainstem, and vestibulocochlear nerve formation is the developmental step that builds it.
- **digestive system development** [go] (inclusion 0.38)
  - Formation of the gut tube and its derivatives turns a simple endodermal sheet into a regionalized organ system capable of digesting and absorbing food.

- **A.** Cranial and pharyngeal organ morphogenesis
  - Members 1-5 and the weakly included member 6 all concern development of cranial/pharyngeal-derived structures (facial nerve, thyroid, semicircular canals, face, vestibulocochlear nerve) driven by shared patterning genes like TBX1, EYA1, HOXA1 and CHD7. The gut tube development pathway (0.38) is excluded as it concerns endodermal organs unrelated to cranial/pharyngeal patterning.
- **B.** Craniofacial and inner ear development
  - Core members at inclusion ≥0.5 involve facial nerve, face, thyroid gland, semicircular canal, and vestibulocochlear nerve development—cranial and otic structures. Digestive system development (0.38) is excluded as it falls outside this shared craniofacial/otic scope.
- **C.** Cranial and pharyngeal arch-derived organogenesis
  - Core members (facial nerve, thyroid, face, semicircular canal x2) all involve neural crest/pharyngeal arch- and otic vesicle-derived structures of the head, patterned by shared transcription factors like TBX1, EYA1, HOXA1 and CHD7. Vestibulocochlear nerve formation (0.62) fits as another otic/cranial nerve derivative. Digestive system development (0.38) is excluded as it shares only distant transcriptional logic, not craniofacial or otic identity.

## pure_reactome (10 themes)

### n0024 -- 4 members

- **Defective F8 accelerates dissociation of the A2 domain** [reactome] (inclusion 1.00)
  - Activated factor VIII works only as long as it stays assembled: its A2 domain is held non-covalently against the A1 and A3 domains, and once A2 drifts away the cofactor is spent.
- **Defective F8 binding to the cell membrane** [reactome] (inclusion 1.00)
  - Activated factor VIII works only when it is docked on a phospholipid surface, where it serves as the cofactor that accelerates factor IXa-mediated activation of factor X in the intrinsic clotting pathway.
- **Defective F9 secretion** [reactome] (inclusion 1.00)
  - Coagulation factor IX is a vitamin K-dependent protease made by hepatocytes and released into plasma, where it works with factor VIII to activate factor X and sustain thrombin generation at a site of injury.
- **Enhanced cleavage of VWF variant by ADAMTS13** [reactome] (inclusion 1.00)
  - Von Willebrand factor circulates as long multimers that capture platelets at sites of vessel injury, and their size is trimmed by the plasma metalloprotease ADAMTS13, which cuts a single Tyr-Met bond in the A2 domain only when shear force unfolds it.

- **A.** Molecular defects in coagulation factor function
  - All four describe specific mutations or proteolytic mechanisms in clotting factors (VIII, IX, VWF) that impair haemostasis via instability, secretion defects, or altered cleavage, causing hemophilia or von Willebrand disease.
- **B.** Coagulation factor defects in hemostasis
  - All four describe disease-causing molecular defects (protein instability, membrane binding, secretion, or proteolytic regulation) in specific clotting factors (F8, F9, VWF) that impair normal hemostasis.
- **C.** Defective coagulation factor function in hemophilia
  - All four involve dysfunctional coagulation proteins (F8, F9, VWF) with defects in stability, secretion, membrane binding, or turnover.

### n0051 -- 3 members

- **Glycogen storage diseases** [reactome] (inclusion 1.00)
  - Glycogen is the body's rapidly mobilizable glucose store, and its regulated synthesis and breakdown keeps blood glucose stable during fasting and supplies fuel to muscle and brain during exercise and stress.
- **Glycogen storage disease type 0 (muscle GYS1)** [reactome] (inclusion 1.00)
  - Muscle stores glucose as glycogen for rapid use during contraction, and this disease state describes what happens when that store cannot be built.
- **Diseases of carbohydrate metabolism** [reactome] (inclusion 1.00)
  - Inherited defects in carbohydrate handling span the whole route from a meal to usable energy, and this collection of diseases of carbohydrate metabolism covers failures at each step.

- **A.** Glycogen storage diseases  `mechanical: FAIL`
  - All members concern inherited defects in glycogen synthesis or breakdown; the broader 'Diseases of carbohydrate metabolism' member largely consists of glycogen storage disorders alongside a few other carbohydrate defects, but its core overlaps this theme.
- **B.** Glycogen storage diseases  `mechanical: FAIL`
  - All three members concern disease-associated disruptions of glycogen or carbohydrate metabolism, with glycogen storage disease being the specific subset represented.
- **C.** Glycogen storage disease
  - Pathways 1 and 2 concern glycogen synthesis/breakdown enzyme defects and their disease phenotypes; pathway 3 broadens to other carbohydrate metabolism disorders (disaccharidase deficiencies, fructose intolerance, pentose phosphate defects) but still substantially covers glycogen storage disease as a major component, so the shared, nameable core across all three is glycogen metabolism disease.

### n0078 -- 4 members

- **HDR through MMEJ (alt-NHEJ)** [reactome] (inclusion 1.00)
  - Microhomology-mediated end joining, also called alternative nonhomologous end joining, is a mutagenic backup route for repairing DNA double-strand breaks that operates when high-fidelity repair is saturated or genetically compromised.
- **Homologous DNA Pairing and Strand Exchange** [reactome] (inclusion 1.00)
  - Repairing a DNA double-strand break by homologous recombination requires the broken end to find its intact sister chromatid, and homologous DNA pairing and strand exchange is the search-and-invasion step that makes this possible.
- **Defective HDR through Homologous Recombination Repair (HRR) due to PALB2 loss of BRCA1 binding function** [reactome] (inclusion 1.00)
  - Homologous recombination repair fixes DNA double-strand breaks accurately by copying an intact sister chromatid, and PALB2 is the physical link that brings BRCA2 and RAD51 to BRCA1 at the break.
- **Impaired BRCA2 binding to RAD51** [reactome] (inclusion 1.00)
  - Homologous recombination repair of DNA double-strand breaks depends on BRCA2 loading RAD51 onto resected single-stranded DNA, and this describes what happens when that hand-off fails.

- **A.** Homologous recombination repair of DNA double-strand breaks
  - All four concern double-strand break repair via homologous recombination machinery (resection, RAD51 loading, strand exchange) or its alt-NHEJ backup/defective variants, including BRCA2-RAD51 and PALB2-BRCA1 impairments.
- **B.** Homologous recombination and end joining repair of DNA double-strand breaks
  - All four pathways concern double-strand break repair: one via microhomology-mediated end joining, three via homologous recombination (strand invasion, PALB2-BRCA2 bridging, BRCA2-RAD51 loading).
- **C.** Homologous recombination repair
  - All members concern DNA double-strand break repair via homology-directed mechanisms, including strand exchange and defective HRR due to PALB2/BRCA2/RAD51 dysfunction.

### n0080 -- 4 members

- **Synthesis of dolichyl-phosphate mannose** [reactome] (inclusion 1.00)
  - Most mannose that ends up on secreted and membrane proteins arrives through a single lipid-linked donor, dolichyl-phosphate mannose, and this two-step route is how that donor is made.
- **Defective RFT1 causes CDG-1n** [reactome] (inclusion 1.00)
  - N-linked glycosylation begins on the cytosolic face of the endoplasmic reticulum membrane, so the lipid-linked oligosaccharide precursor must be flipped into the ER lumen before the remaining sugars can be added and the finished glycan transferred to nascent proteins.
- **Defective DPM1 causes DPM1-CDG** [reactome] (inclusion 1.00)
  - Dolichol-phosphate mannose is the mannose donor used inside the endoplasmic reticulum for N-linked glycan assembly, GPI anchor synthesis, C-mannosylation and O-mannosylation of proteins such as alpha-dystroglycan, and it is made by a three-subunit enzyme in the ER membrane.
- **Defective DOLK causes DOLK-CDG** [reactome] (inclusion 1.00)
  - Dolichol kinase converts dolichol to dolichyl phosphate in the endoplasmic reticulum membrane, the lipid carrier on which the oligosaccharide precursor for N-linked glycosylation is built and which also supplies O-mannosylation and GPI anchor synthesis.

- **A.** Dolichol-phosphate mannose synthesis and its defects
  - All members concern synthesis of dolichyl-phosphate mannose or congenital disorders of glycosylation arising from defects in this pathway (RFT1, DPM1, DOLK).
- **B.** Dolichol-phosphate synthesis and utilisation in glycosylation
  - All four pathways concern generation or lumenal use of dolichyl-phosphate-linked intermediates (dolichol kinase, DPM synthase, LLO flipping) that feed N-glycosylation, O-mannosylation and GPI anchor synthesis.
- **C.** Dolichol pathway defects in N-glycosylation
  - All members concern dolichol/dolichyl-phosphate synthesis or utilization steps required for lipid-linked oligosaccharide assembly and N-linked glycosylation, including congenital disorders of glycosylation arising from their loss.

### n0081 -- 3 members

- **Diseases of glycosylation** [reactome] (inclusion 1.00)
  - Congenital disorders of glycosylation are inherited failures to build or attach glycans, and because nearly every secreted and membrane protein is glycosylated, the consequences are multisystem: psychomotor retardation, coagulopathy, liver and skeletal disease, and in the N-linked forms a diagnostic shift in the isoelectric focusing pattern of plasma transferrin.
- **Diseases associated with O-glycosylation of proteins** [reactome] (inclusion 1.00)
  - Sugars added to serine and threonine residues shape mucus, muscle attachment and developmental signalling, and the inherited defects grouped here are the congenital disorders of glycosylation that follow when O-linked chains are built incorrectly.
- **DAG1 core M3 glycosylations** [reactome] (inclusion 1.00)
  - Alpha-dystroglycan must be sugar-coated before it can work, and the core M3 glycosylation route is how that coat is built on specific threonines of its mucin-like domain.

- **A.** Congenital disorders of protein glycosylation
  - All three concern inherited defects in building or attaching glycans to proteins (N-linked, O-linked, and dystroglycan matriglycan assembly), producing multisystem or dystroglycanopathy phenotypes.
- **B.** Diseases of protein glycosylation
  - All three concern defective glycosylation of proteins, including O-glycosylation and DAG1-related core M3 glycosylation disorders.
- **C.** Congenital disorders of protein glycosylation
  - All three cover inherited defects in building N- or O-linked glycans (dolichol pathway, O-mannosylation, O-GalNAc, O-fucose, dystroglycan matriglycan assembly) and their disease consequences.

### n0167 -- 4 members

- **KW2449-resistant FLT3 mutants** [reactome] (inclusion 1.00)
  - Activating mutations in the FLT3 receptor tyrosine kinase drive proliferation and survival of myeloid blasts and are among the most common lesions in acute myeloid leukaemia, making the receptor a prime drug target.
- **gilteritinib-resistant FLT3 mutants** [reactome] (inclusion 1.00)
  - Activating mutations in the receptor tyrosine kinase FLT3 drive a large fraction of acute myeloid leukaemia, and gilteritinib is a type I inhibitor used to shut that signalling down.
- **sorafenib-resistant FLT3 mutants** [reactome] (inclusion 1.00)
  - FLT3 is a receptor tyrosine kinase that drives proliferation and survival of hematopoietic progenitors, and activating mutations in it — most often internal tandem duplications in the juxtamembrane region — are among the most common lesions in acute myeloid leukemia, where they predict relapse.
- **sunitinib-resistant FLT3 mutants** [reactome] (inclusion 1.00)
  - FLT3 is a receptor tyrosine kinase whose activating mutations drive a large fraction of acute myeloid leukaemia, and inhibiting it is a mainstay of targeted therapy in that disease.

- **A.** FLT3 inhibitor resistance mutations in AML
  - All four pathways describe drug-resistant FLT3 kinase domain mutants (against KW-2449, gilteritinib, sorafenib, sunitinib) that sustain constitutive FLT3 signalling in acute myeloid leukaemia.
- **B.** Drug-resistant FLT3 mutants
  - All four members describe FLT3 mutant forms conferring resistance to specific kinase inhibitors (KW2449, gilteritinib, sorafenib, sunitinib).
- **C.** Drug-resistant FLT3 kinase mutants
  - All four members describe FLT3 mutant alleles that resist specific kinase inhibitors (KW-2449, gilteritinib, sorafenib, sunitinib) while retaining constitutive downstream signalling in AML.

### n0214 -- 4 members

- **HS-GAG degradation** [reactome] (inclusion 1.00)
  - Heparan sulfate chains on cell-surface and matrix proteoglycans are constantly turned over, and this pathway covers their breakdown from intact proteoglycan to free sugars.
- **CS/DS degradation** [reactome] (inclusion 1.00)
  - Chondroitin sulfate and dermatan sulfate chains on proteoglycans such as decorin, biglycan, versican, brevican and neurocan are continuously turned over, and their final breakdown happens in the lysosome.
- **MPS II - Hunter syndrome (CS/DS degradation)** [reactome] (inclusion 1.00)
  - Hunter syndrome is the X-linked lysosomal storage disease that results when the degradation of chondroitin/dermatan sulfate and heparan sulfate stalls at a single sulfatase step.
- **MPS VII - Sly syndrome (CS/DS degradation)** [reactome] (inclusion 1.00)
  - Mucopolysaccharidosis VII, or Sly syndrome, is the lysosomal storage disease that follows loss of beta-glucuronidase activity during the stepwise breakdown of chondroitin sulfate and dermatan sulfate.

- **A.** Glycosaminoglycan degradation and mucopolysaccharidoses
  - All four describe lysosomal stepwise breakdown of heparan/chondroitin/dermatan sulfate chains and the storage diseases arising from blocking single enzymatic steps.
- **B.** Glycosaminoglycan degradation and mucopolysaccharidoses
  - All members concern lysosomal stepwise breakdown of heparan/chondroitin/dermatan sulfate chains and the storage diseases caused by blocking specific steps.
- **C.** Glycosaminoglycan degradation
  - All members involve breakdown of heparan sulfate or chondroitin/dermatan sulfate GAGs, including two mucopolysaccharidosis disorders of this process.

### n0224 -- 3 members

- **Nef mediated downregulation of MHC class I complex cell surface expression** [reactome] (inclusion 1.00)
  - HIV-infected cells survive cytotoxic T lymphocyte surveillance in part by stripping MHC class I from their surface, and the viral accessory protein Nef is what drives this immune evasion.
- **Nef Mediated CD4 Down-regulation** [reactome] (inclusion 1.00)
  - HIV-1 Nef strips CD4 from the surface of infected cells, and this down-regulation serves the virus: without CD4 on the plasma membrane the receptor cannot engage newly made Env on budding particles, so virions are released more efficiently and are more infectious, and the cell is also protected from superinfection.
- **Nef Mediated CD8 Down-regulation** [reactome] (inclusion 1.00)
  - HIV-1 uses its accessory protein Nef to strip immune recognition molecules from the surface of infected cells, and one target is the beta chain of the CD8 alpha-beta receptor on cytotoxic T lymphocytes.

- **A.** Nef-mediated immune receptor downregulation
  - All three pathways describe HIV-1 Nef hijacking clathrin adaptor trafficking to remove MHC class I, CD4, or CD8 beta from the infected cell surface for immune evasion.
- **B.** Nef-mediated immune receptor downregulation
  - All three pathways describe HIV-1 Nef hijacking clathrin adaptor trafficking to remove MHC class I, CD4, or CD8 from the infected cell surface.
- **C.** Nef-mediated immune receptor downregulation
  - All three members are HIV Nef-mediated downregulation of surface immune molecules (MHC class I, CD4, CD8).

### n0472 -- 6 members

- **Rap1 signalling** [reactome] (inclusion 1.00)
  - Rap1 signalling controls how cells stick to their surroundings: the GTPases RAP1A and RAP1B, when loaded with GTP, recruit effectors that switch integrins to a high-affinity state, so this branch of Ras-superfamily signalling governs platelet aggregation, leukocyte adhesion and arrest on endothelium, cell junction integrity and cell shape.
- **G alpha (12/13) signalling events** [reactome] (inclusion 1.00)
  - Some G protein-coupled receptors, including alpha-1 adrenergic and thromboxane A2 receptors, signal through the G alpha 12/13 family to reshape the actin cytoskeleton rather than to raise calcium or cyclic AMP.
- **VEGFA-VEGFR2 Pathway** [reactome] (inclusion 1.00)
  - New blood vessels sprout from existing ones under the control of vascular endothelial growth factor A acting on its endothelial receptor tyrosine kinase VEGFR2 (KDR), and this axis is the principal driver of angiogenesis in development, wound healing, tumour growth and diabetic retinopathy; loss of the receptor kills mouse embryos for lack of endothelial and blood island formation, while blocking the ligand is standard anti-angiogenic therapy.
- **VEGFR2 mediated cell proliferation** [reactome] (inclusion 1.00)
  - Endothelial cells divide in response to VEGF, and this is the branch of VEGFR2 signalling that drives that proliferation — the basis of angiogenesis in development, wound healing and tumour vascularisation, and the target of anti-VEGF drugs.
- **RND1 GTPase cycle** [reactome] (inclusion 0.55)
  - RND1 is an atypical Rho-family GTPase that stays GTP-loaded and, unlike classical switches, is not toggled by exchange factors or GTPase-activating proteins; its activity is set instead by expression level and by removal from the plasma membrane after phosphorylation-driven binding to 14-3-3 proteins.
- **Thrombin signalling through proteinase activated receptors (PARs)** [reactome] (inclusion 0.25)
  - Thrombin, the protease at the end of the coagulation cascade, also acts as a hormone-like signal by cleaving proteinase-activated receptors on the cell surface, and this route is how a clotting signal becomes a cellular response.

- **A.** Rho/Rap GTPase signalling in adhesion and vascular cell behaviour
  - All core members (Rap1, G12/13, VEGFA-VEGFR2, VEGFR2 proliferation) converge on Rho/Rap GTPase-driven cytoskeletal remodelling controlling adhesion, shape and endothelial/vascular responses; RND1 (0.55) fits as a Rho-antagonising GTPase acting on the same cytoskeletal axis. Thrombin-PAR signalling (0.25) is excluded as only weakly included and broader in scope.
- **B.** Rho/GTPase-mediated cytoskeletal signalling in adhesion and angiogenesis
  - All members converge on small GTPase (Rap1/Rho/RND1) or GPCR/receptor tyrosine kinase pathways that remodel the actin cytoskeleton to control adhesion, platelet activation, and endothelial/angiogenic behaviour. Includes weakly supported thrombin/PAR signalling (0.25) which feeds into the same Rho/PLC-PKC cytoskeletal output.
- **C.** GTPase-mediated VEGF and GPCR signalling
  - Core members (Rap1, G alpha 12/13, VEGFA-VEGFR2, VEGFR2 proliferation, RND1) converge on small GTPase and GPCR-driven signalling downstream of VEGF and related receptors; thrombin/PAR signalling (0.25) is excluded as weakly supported.

### n0473 -- 6 members

- **DS-GAG biosynthesis** [reactome] (inclusion 1.00)
  - Dermatan sulfate chains are built on proteoglycan core proteins and give connective tissue its tensile and hydrating properties, while also shaping growth factor and chemokine availability in the extracellular matrix.
- **Diseases associated with glycosaminoglycan metabolism** [reactome] (inclusion 1.00)
  - Glycosaminoglycan chains attached to proteoglycan cores fill the extracellular matrix, hold water in cartilage and cornea, and tether growth factors at cell surfaces, so inherited defects in making or breaking them produce recognisable skeletal, connective tissue and neurological disease.
- **Defective CHSY1 causes TPBS** [reactome] (inclusion 1.00)
  - Chondroitin sulfate chains are built by alternating addition of glucuronate and N-acetylgalactosamine onto a linker tetrasaccharide, and CHSY1 is a principal polymerizing enzyme of that reaction.
- **Defective SLC26A2 causes chondrodysplasias** [reactome] (inclusion 0.76)
  - Cartilage stiffness and resilience depend on proteoglycans whose glycosaminoglycan chains are heavily sulfated, and chondrocytes obtain the sulfate for that modification by importing it from outside the cell.
- **Defective SLC2A10 causes arterial tortuosity syndrome (ATS)** [reactome] (inclusion 0.48)
  - Arterial tortuosity syndrome follows loss of function of GLUT10, the high-affinity glucose transporter encoded by SLC2A10 and one of the class III facilitative sugar carriers.
- **Hyaluronan metabolism** [reactome] (inclusion 0.33)
  - Hyaluronan is the one glycosaminoglycan made without sulfation and without a protein core, and its metabolism covers both its synthesis at the plasma membrane and its turnover.

- **A.** Glycosaminoglycan biosynthesis and related disorders  `mechanical: FAIL`
  - Core members concern dermatan sulfate/chondroitin GAG biosynthesis and diseases from defective GAG-related genes (CHSY1, SLC26A2); hyaluronan metabolism and SLC2A10/ATS are weakly included (0.33, 0.48) but still relate to GAG or glycan-associated metabolic disease.
- **B.** Glycosaminoglycan sulfation and biosynthesis disorders
  - Core members (CHSY1, DS-GAG biosynthesis, SLC26A2, and the general GAG-disease pathway) all concern sulfated glycosaminoglycan (chondroitin/dermatan sulfate) biosynthesis and its inherited defects. Hyaluronan metabolism (0.33) is excluded as it lacks sulfation, and SLC2A10/arterial tortuosity (0.48) is only loosely linked via connective tissue, not GAG sulfation directly.
- **C.** Glycosaminoglycan synthesis and sulfation
  - Members 1-4 concern chondroitin/dermatan sulfate and GAG chain synthesis, sulfation and the sulfate supply chain underlying proteoglycan matrix assembly; weakly included members 5 (glucose/ascorbate transport in vascular connective tissue) and 6 (hyaluronan, a non-sulfated GAG) sit at the periphery and are not required by the name.

## has_btm_or_hallmark (10 themes)

### n0026 -- 4 members

- **respiratory electron transport chain (mitochondrion)** [btm] (inclusion 1.00)
  - Oxidative phosphorylation is how most ATP in aerobic cells is made, and this is the mitochondrial inner-membrane machinery that does it: electrons stripped from NADH pass along the respiratory chain to oxygen while protons are pumped across the membrane, and the resulting gradient drives ATP synthesis.
- **oxidative phosphorylation** [go] (inclusion 1.00)
  - Aerobic ATP production is completed here: electrons stripped from nutrients pass down the mitochondrial respiratory chain to oxygen, pumping protons across the inner membrane, and the resulting gradient drives ATP synthase.
- **electron transport chain** [go] (inclusion 1.00)
  - Cells recover most of the energy in nutrients by passing electrons down a chain of carriers to a terminal acceptor, and this electron transport chain is that machinery.
- **HALLMARK_OXIDATIVE_PHOSPHORYLATION** [hallmark] (inclusion 1.00)
  - Oxidative phosphorylation is how cells convert the reducing equivalents harvested from fuel oxidation into ATP, and it supplies most of the energy used by heart, brain, and skeletal muscle.

- **A.** Mitochondrial oxidative phosphorylation
  - All four members describe the respiratory chain complexes and ATP synthase driving oxidative ATP production, with shared assembly factors, cofactor delivery, and disease links to mitochondrial encephalomyopathies.
- **B.** Mitochondrial oxidative phosphorylation
  - All four members describe the mitochondrial electron transport chain and ATP synthase machinery that carries out oxidative phosphorylation, including their subunits, assembly factors, and coupling to ATP production.
- **C.** Mitochondrial oxidative phosphorylation
  - All members describe the mitochondrial electron transport chain and oxidative phosphorylation.

### n0079 -- 3 members

- **xenobiotic metabolism** [btm] (inclusion 1.00)
  - Drugs, dietary chemicals and other foreign compounds must be chemically altered before they can be cleared, and xenobiotic metabolism is the set of enzymes that performs that conversion and disposal.
- **Phase II - Conjugation of compounds** [reactome] (inclusion 1.00)
  - Drugs, dietary chemicals and endogenous metabolites are cleared from the body by attaching a water-soluble group to them, and this conjugative arm of biotransformation is where that happens.
- **Drug ADME** [reactome] (inclusion 1.00)
  - The fate of a drug in the body — how it is absorbed, distributed, chemically transformed and excreted — determines its dose, duration of action and toxicity, and this collection of absorption, distribution, metabolism and excretion steps is where that pharmacokinetic handling is carried out.

- **A.** Xenobiotic and drug metabolism
  - All three concern biotransformation and conjugation of xenobiotics/drugs, covering phase II conjugation and overall ADME processes.
- **B.** Drug metabolism and transport
  - All three cover xenobiotic biotransformation (phase I oxidation and phase II conjugation) together with the transporters that move drugs and their metabolites, underlying pharmacokinetics and interindividual variation in drug response.
- **C.** Xenobiotic and drug metabolism
  - All three cover biotransformation and clearance of drugs/xenobiotics: phase I oxidation, phase II conjugation, and overall ADME transport/metabolism.

### n0151 -- 8 members

- **inflammatory response** [go] (inclusion 1.00)
  - The immediate defensive reaction of vertebrate tissue to infection or injury, marked by local vasodilation, leakage of plasma into interstitial spaces, and recruitment of neutrophils and macrophages to the site.
- **HALLMARK_INFLAMMATORY_RESPONSE** [hallmark] (inclusion 1.00)
  - Inflammation is the coordinated tissue response to infection and injury: recognise the insult, recruit leukocytes, raise vascular permeability, and then resolve.
- **Interleukin-1 processing** [reactome] (inclusion 1.00)
  - Interleukin-1 processing is the step that converts an inactive cytoplasmic precursor into a released, receptor-competent inflammatory cytokine, and it sets the threshold for fever, neutrophil recruitment and the acute-phase response.
- **Cell recruitment (pro-inflammatory response)** [reactome] (inclusion 1.00)
  - Pro-inflammatory cell recruitment is how an infected tissue calls in leukocytes that can kill intracellular pathogens, and it sets the balance that decides whether an infection such as Leishmania is contained or becomes chronic.
- **Interleukin-1 family signaling** [reactome] (inclusion 0.83)
  - The interleukin-1 family drives the acute inflammatory response: fever, neutrophil recruitment, acute-phase protein production, and the alarm signalling that follows infection or tissue damage.
- **positive regulation of interleukin-1 alpha production** [go] (inclusion 0.40)
  - Interleukin-1 alpha is an early alarm cytokine released by damaged or stressed epithelium and myeloid cells, and this pathway covers the signals that increase its production.
- **positive regulation of response to external stimulus** [go] (inclusion 0.29)
  - Cells that meet a microbe, an injury or a chemotactic gradient must not only detect it but amplify the reaction, and this collection of positive regulators of the response to external stimuli is what raises the gain.
- **positive regulation of chemokine (C-X-C motif) ligand 1 production** [go] (inclusion 0.27)
  - CXCL1 is a neutrophil-attracting chemokine released by epithelium, fibroblasts and endothelium, and this pathway covers the signals that turn its production up.

- **A.** Inflammasome-driven IL-1 signalling and acute inflammation
  - Core members (1-5) all center on inflammasome/caspase-1 processing of IL-1 family cytokines and the downstream NF-kB-driven acute inflammatory response with leukocyte recruitment. Weakly included members (6-8, inclusion <0.5) extend to IL-1alpha release and chemokine amplification but remain within this same inflammatory signalling axis.
- **B.** Inflammatory response and interleukin-1 signaling
  - Core members (inclusion ≥0.83) cover general inflammatory response and IL-1 processing/signaling and inflammatory cell recruitment; weaker members (IL-1 alpha production, chemokine production, response to external stimulus, all <0.5) fit within this inflammatory/IL-1 axis but are not required to define it.
- **C.** IL-1 inflammasome-driven inflammatory response
  - Core members (inclusion ≥0.83) all concern inflammatory response triggered by pattern recognition receptors and NF-kB, converging on IL-1 family cytokine processing and inflammasome-driven leukocyte recruitment. Lower-inclusion members (0.40 and below, on IL-1 alpha, generic external stimulus response, and CXCL1) fit this same axis loosely but are consistent with it, so the name covers all listed members.

### n0212 -- 3 members

- **leukocyte differentiation** [btm] (inclusion 1.00)
  - Leukocyte differentiation is the process by which haematopoietic progenitors and activated immune cells commit to specialized fates anging from granulocytes and monocytes to dendritic cells and lymphocyte subsets, and it determines the composition of the immune system available to fight infection.
- **myeloid progenitor cell differentiation** [go] (inclusion 1.00)
  - Myeloid progenitor cell differentiation is the step at which multipotent haematopoietic precursors commit to the lineages that produce granulocytes, monocytes and macrophages, erythrocytes, megakaryocytes and mast cells, and it sets the supply of blood and innate immune cells for life.
- **Transcriptional regulation of granulopoiesis** [reactome] (inclusion 1.00)
  - Neutrophils and the other granulocytes are the most abundant leukocytes in blood, and this transcriptional programme is how hematopoietic stem cells are routed through multipotent and common myeloid progenitors into granulocyte-monocyte progenitors and on to mature, granule-laden cells.

- **A.** Myeloid and leukocyte lineage commitment
  - All three describe transcriptional and signalling control of haematopoietic progenitor commitment to myeloid/granulocyte-monocyte or broader leukocyte fates, with disruption causing leukaemia or immunodeficiency.
- **B.** Myeloid and leukocyte differentiation
  - All three concern transcriptional and signalling control of haematopoietic progenitor commitment into myeloid/granulocyte or broader leukocyte lineages.
- **C.** Myeloid and leukocyte differentiation
  - All three concern hematopoietic differentiation, spanning leukocyte differentiation broadly, myeloid progenitor differentiation, and granulopoiesis transcriptional control.

### n0213 -- 4 members

- **protein import into peroxisome matrix, receptor recycling** [go] (inclusion 1.00)
  - Peroxisomal matrix enzymes are made in the cytosol and delivered by shuttling receptors, so the import cycle can only continue if those receptors are released from cargo and returned for reuse.
- **HALLMARK_PEROXISOME** [hallmark] (inclusion 1.00)
  - Peroxisomes are small oxidative organelles that handle lipid chemistry the mitochondria cannot: beta-oxidation of very-long-chain and branched fatty acids, ether phospholipid (plasmalogen) synthesis, bile acid intermediate processing, and disposal of the hydrogen peroxide these reactions generate.
- **Peroxisomal protein import** [reactome] (inclusion 1.00)
  - Peroxisomes carry out fatty acid beta-oxidation, glyoxylate detoxification, hydrogen peroxide breakdown and plasmalogen synthesis, but they make none of their own matrix enzymes; peroxisomal protein import is how roughly four dozen cargo proteins reach the lumen from the cytosol.
- **Class I peroxisomal membrane protein import** [reactome] (inclusion 1.00)
  - Peroxisomes cannot build themselves without first installing their membrane proteins, and class I peroxisomal membrane protein import is the route most of them take.

- **A.** Peroxisomal protein import and biogenesis
  - All members concern the machinery importing matrix or membrane proteins into peroxisomes and the resulting organelle biogenesis/function, including receptor recycling and membrane protein insertion.
- **B.** Peroxisome biogenesis and protein import
  - All four members concern peroxisomal matrix or membrane protein import machinery (PEX proteins) and its role in organelle biogenesis, with loss causing Zellweger spectrum disorders.
- **C.** Peroxisomal protein import  `mechanical: FAIL`
  - All members concern peroxisome biogenesis via import of proteins into the peroxisomal matrix or membrane; the HALLMARK_PEROXISOME set broadly reflects peroxisomal biology dominated by this import machinery.

### n0231 -- 7 members

- **exocrine pancreas development** [go] (inclusion 1.00)
  - The exocrine pancreas is the digestive enzyme factory of the gut: acinar cells synthesise and store zymogens such as trypsinogen and chymotrypsinogen and release them into the duct system, while its failure to form or function causes exocrine insufficiency, malabsorption and pancreatitis.
- **Regulation of gene expression in endocrine-committed (NEUROG3+) progenitor cells** [reactome] (inclusion 1.00)
  - Pancreatic endocrine cells arise from a transient population of progenitors that switch on neurogenin 3, and this transcriptional programme is what commits those cells away from duct and acinar fates toward the hormone-producing islet lineages.
- **negative regulation of type B pancreatic cell apoptotic process** [go] (inclusion 0.94)
  - Insulin-secreting beta cells are few in number and largely irreplaceable in adults, so their survival sets the limit on how much insulin the pancreas can deliver.
- **epithelial cell maturation** [go] (inclusion 0.93)
  - Epithelial cell maturation is the final step by which a committed epithelial cell acquires the secretory, absorptive or barrier capacity that makes a sheet of cells functional, without further change in cell shape.
- **Regulation of gene expression in late stage (branching morphogenesis) pancreatic bud precursor cells** [reactome] (inclusion 0.89)
  - During the branching morphogenesis stage of pancreatic development, committed but still undifferentiated epithelial precursors in the growing ductal tree must be kept proliferating until a subset is released to become hormone-producing endocrine cells.
- **enriched in hepatocyte nuclear factors (I)** [btm] (inclusion 0.78)
  - Hepatocyte nuclear factors are the transcriptional regulators that give liver, pancreas, intestine and kidney epithelium their identity, and this grouping centres on that circuitry: FOXA2 and FOXA3 act as pioneer factors that open chromatin at endoderm-specific enhancers, while HNF1B, HNF4A and HNF4G drive the downstream programmes of bile acid and lipid handling, glucose metabolism, and apical epithelial differentiation.
- **type B pancreatic cell proliferation** [go] (inclusion 0.76)
  - Insulin-secreting beta cells of the pancreatic islets are normally quiescent, but their number can expand during growth, pregnancy, obesity and insulin resistance; this proliferative capacity sets how much insulin a person can secrete and its loss underlies the beta cell deficit of both type 1 and type 2 diabetes.

- **A.** Pancreatic cell development and survival
  - Members cover pancreas organogenesis, endocrine/beta-cell progenitor gene regulation, beta-cell proliferation and apoptosis suppression, and epithelial maturation; the hepatocyte nuclear factor module reflects transcription factors shared with pancreatic development.
- **B.** Pancreatic endocrine and epithelial cell specification
  - All members concern transcriptional programmes governing pancreatic (and related endoderm-derived epithelial) lineage commitment, differentiation, survival or proliferation of beta/acinar/ductal cells, centred on factors like PDX1, NEUROG3, HNF1B/HNF4A, NKX6-1 and FOXA2.
- **C.** Pancreatic endocrine cell development and beta cell maintenance
  - All members concern pancreatic epithelial/endocrine lineage specification, differentiation, or beta cell survival and proliferation, spanning progenitor transcriptional programmes (NEUROG3, HNF factors), organ development, and beta cell homeostasis.

### n0304 -- 5 members

- **fatty acid beta-oxidation using acyl-CoA dehydrogenase** [go] (inclusion 1.00)
  - Mitochondria extract energy from fatty acids by shortening them two carbons at a time, and the flavin-dependent acyl-CoA dehydrogenases catalyse the first, committed oxidation of each round, converting acyl-CoA to trans-2-enoyl-CoA.
- **HALLMARK_FATTY_ACID_METABOLISM** [hallmark] (inclusion 1.00)
  - Fatty acids are both a fuel and a building block, and this programme covers the enzymes that activate, break down, and synthesise them together with the mitochondrial machinery that finishes the job.
- **Ketone body metabolism** [reactome] (inclusion 1.00)
  - During fasting, the liver converts fat-derived acetyl-CoA into water-soluble fuels that can circulate and spare glucose, and ketone body metabolism covers both their synthesis and their oxidation elsewhere.
- **Synthesis of Ketone Bodies** [reactome] (inclusion 1.00)
  - When carbohydrate is scarce, the liver converts acetyl-CoA from fatty acid oxidation into ketone bodies that circulate as fuel, and this ketogenic route is what allows heart and skeletal muscle to burn acetoacetate and beta-hydroxybutyrate while the limited glucose supply is reserved for the brain.
- **Fatty acid metabolism** [reactome] (inclusion 1.00)
  - Fatty acid metabolism supplies much of the body's energy currency, builds the acyl chains used in membranes and storage lipids, and generates the eicosanoid signals that shape inflammation, vascular tone and platelet behaviour.

- **A.** Fatty acid oxidation and ketone body metabolism
  - All members concern mitochondrial fatty acid beta-oxidation and/or hepatic ketogenesis/ketolysis; broader fatty acid metabolism members are included since they explicitly encompass these same oxidative and ketogenic pathways.
- **B.** Fatty acid oxidation and ketone body metabolism
  - All members concern fatty acid beta-oxidation/metabolism or ketone body synthesis and metabolism, closely linked hepatic energy pathways.
- **C.** Fatty acid oxidation and ketone body metabolism
  - All five cover mitochondrial beta-oxidation of fatty acids feeding acetyl-CoA into ketogenesis/ketolysis during fasting; pathway 5 additionally includes lipogenesis and eicosanoid synthesis but shares this oxidative-ketogenic core.

### n0310 -- 7 members

- **negative regulation of endothelial cell proliferation** [go] (inclusion 1.00)
  - Blood vessels only grow when endothelial cells are allowed to divide, and this pathway is the brake: the collected signals, receptors and microRNAs that stop or slow endothelial cell proliferation and so keep the vasculature quiescent.
- **angiogenesis involved in wound healing** [go] (inclusion 1.00)
  - Repair of injured tissue depends on rebuilding its blood supply, and this is the sprouting of new capillaries from existing vessels within a healing wound.
- **positive regulation of vasculature development** [go] (inclusion 1.00)
  - Blood and lymphatic vessels are built and expanded by endothelial cells that proliferate, migrate and assemble into perfused tubes, and this collection captures the signals that drive that expansion forward.
- **negative regulation of vascular endothelial cell proliferation** [go] (inclusion 1.00)
  - Blood vessel growth has to be switched off as well as on, and this is the restraining arm: processes that slow or stop proliferation of vascular endothelial cells so that vessel density matches tissue need.
- **positive regulation of epithelial cell proliferation** [go] (inclusion 0.91)
  - Epithelia renew themselves throughout life, and this collection captures the signals that drive that division upward — the inputs that push epithelial cells, including the endothelium of blood and lymphatic vessels, into cycle during development, wound repair, glandular branching and regeneration of gut and skin surfaces.
- **HALLMARK_ANGIOGENESIS** [hallmark] (inclusion 0.87)
  - New blood vessels sprout from existing ones whenever a tissue outgrows its oxygen supply, and this collection marks the genes induced as that programme runs.
- **cellular response to endogenous stimulus** [go] (inclusion 0.52)
  - Cells constantly adjust their behaviour to cues generated inside the organism itself — hormones, growth factors, cytokines, peptides and metabolites — rather than to external insults, and this broad response programme covers how those internal signals are received and converted into changes in gene expression, metabolism, secretion, growth and movement.

- **A.** Regulation of angiogenesis and vascular endothelial proliferation
  - Pathways 1-4 and 6 directly concern promoting or restraining endothelial proliferation and vessel sprouting/angiogenesis. Pathway 5 (0.91) extends this to epithelial proliferation broadly but explicitly includes vascular endothelium as a core case. Pathway 7 (0.52) is excluded as it describes generic hormone/growth-factor signal transduction not specific to vasculature.
- **B.** Regulation of vascular endothelial cell proliferation and angiogenesis
  - Members center on endothelial cell proliferation control and angiogenesis (including wound healing angiogenesis and vasculature development); epithelial cell proliferation and the generic cellular response to endogenous stimulus are weaker/broader inclusions but consistent with vascular growth regulation context.
- **C.** Regulation of angiogenesis
  - Core members (all at inclusion 0.87-1.00) govern endothelial cell proliferation and vessel sprouting, both positive and negative, in wound healing and vascular development. The broader 'positive regulation of epithelial cell proliferation' and 'cellular response to endogenous stimulus' (0.91 and 0.52) extend beyond vasculature but are excluded from the core name.

### n0440 -- 7 members

- **respiratory burst involved in defense response** [go] (inclusion 1.00)
  - Phagocytes kill ingested microbes by deliberately making reactive oxygen: the respiratory burst that accompanies a defense response, in which oxygen consumption rises sharply and NADPH oxidase output is converted into superoxide, hydrogen peroxide and downstream oxidants.
- **regulation of superoxide metabolic process** [go] (inclusion 1.00)
  - Superoxide is both a weapon and a hazard, and this regulatory programme sets how much of it a cell makes and how fast it is disposed of.
- **RHO GTPases Activate NADPH Oxidases** [reactome] (inclusion 1.00)
  - Superoxide is made deliberately by NADPH oxidase complexes, and small GTPases of the RHO family are the switch that turns them on.
- **neutrophil-mediated killing of gram-negative bacterium** [go] (inclusion 0.97)
  - Neutrophils are the first responders that clear gram-negative bacteria from infected tissue, and this pathway covers the killing step itself: recognition of the microbe followed by deployment of proteolytic and oxidative weapons within phagosomes and at the site of infection.
- **TBA** [btm] (inclusion 0.95)
  - These genes mark the differentiated tissue macrophage and microglial state, the resident phagocyte programme that clears debris and dying cells, handles iron and heme, and shapes local immune tone.
- **Events associated with phagocytolytic activity of PMN cells** [reactome] (inclusion 0.92)
  - Neutrophils kill ingested bacteria inside the phagosome by generating oxidants, and this pathway covers the heme peroxidase step that converts the initial respiratory burst product into the most microbicidal species.
- **Manipulation of host energy metabolism** [reactome] (inclusion 0.49)
  - Mycobacterium tuberculosis does not simply survive inside a macrophage; it rewires the cell's metabolism to suit itself.

- **A.** Neutrophil respiratory burst and NADPH oxidase activation
  - Members at ≥0.5 inclusion converge on the oxidative burst used by neutrophils/PMNs to kill pathogens, driven by RHO GTPase activation of NADPH oxidases and superoxide production. Excluded the weakly included 'Manipulation of host energy metabolism' (0.49), which does not concern respiratory burst biology.
- **B.** Phagocyte respiratory burst and oxidative killing
  - Members at inclusion ≥0.5 all concern NADPH oxidase assembly, RHO GTPase activation, superoxide/peroxide generation, and myeloperoxidase-mediated killing by phagocytes (neutrophils/macrophages), including the macrophage identity theme (btm, 0.95) which centers on CYBB-driven respiratory burst. Excluded the weakly included Manipulation of host energy metabolism (0.49), which concerns pathogen-driven glycolytic rewiring rather than oxidative killing.
- **C.** Phagocyte NADPH oxidase respiratory burst and microbicidal killing
  - Members 1,2,3,4,6 all concern NADPH oxidase-driven superoxide/peroxide generation and its use in phagocyte antimicrobial killing (respiratory burst, oxidase regulation, myeloperoxidase chemistry, neutrophil bactericidal effectors). Member 5 (macrophage/microglia identity programme) is weakly included but touches the same oxidase (CYBB) and phagocytic clearance role. Member 7, on Mtb-driven host glycolytic rewiring, is only weakly included (0.49) and does not share this oxidative killing biology, so it is excluded from the name.

### n0744 -- 9 members

- **regulation of mitotic cell cycle** [go] (inclusion 1.00)
  - Cells divide only when conditions permit, and the regulation of the mitotic cell cycle is the control layer that decides when to advance, when to pause, and when to abandon division altogether.
- **mitotic G1/S transition checkpoint signaling** [go] (inclusion 1.00)
  - Before a cell commits to replicating its genome it must confirm that conditions are suitable, and the G1/S transition checkpoint is the brake that holds it in G1 when they are not.
- **HALLMARK_G2M_CHECKPOINT** [hallmark] (inclusion 1.00)
  - Before a cell commits to dividing, it must finish replicating its DNA, repair any damage, and assemble a bipolar spindle; the G2/M checkpoint enforces that order and delays mitotic entry until those conditions are met.
- **Polo-like kinase mediated events** [reactome] (inclusion 1.00)
  - Entry into mitosis is a switch, and Polo-like kinase 1 is one of the levers that throws it.
- **G1 Phase** [reactome] (inclusion 1.00)
  - G1 phase is the interval in which a cell decides whether to commit to another division, and this decision point is where growth signals, nutrient status and damage checks are integrated before DNA replication becomes irreversible.
- **Mitotic G1 phase and G1/S transition** [reactome] (inclusion 0.78)
  - Between one division and the next, a cell spends G1 deciding whether to replicate its DNA at all, and this G1 phase and G1/S transition programme is where that commitment is made or deferred into quiescence.
- **mitotic cell cycle** [btm] (inclusion 0.47)
  - Somatic cells duplicate their chromosomes and partition them equally into two daughters, and this mitotic cell cycle module covers the commitment to division and the machinery that executes it.
- **TP53 Regulates Transcription of Genes Involved in G2 Cell Cycle Arrest** [reactome] (inclusion 0.41)
  - When DNA damage is detected in the second gap phase, cells must hold off mitosis until repair is finished, and p53-driven transcription is one route to that arrest.
- **The role of GTSE1 in G2/M progression after G2 checkpoint** [reactome] (inclusion 0.38)
  - After DNA damage arrests cells in G2, they must eventually silence the arrest signal and re-enter mitosis, and GTSE1 is one route by which that recovery happens.

- **A.** Cell cycle checkpoint and mitotic entry control
  - All members concern regulation of cell cycle transitions (G1/S, G2/M, mitotic entry/progression) via cyclin-CDK complexes, CDC25/WEE1, p53/checkpoint signalling, and mitotic machinery; includes weaker members 7-9 (GTSE1 recovery from arrest, p53-driven G2 checkpoint, mitotic gene module) that still fit this control theme.
- **B.** Cell cycle checkpoint control
  - All members concern regulation of mitotic cell cycle transitions (G1/S, G2/M) via checkpoint signaling, CDK-cyclin regulation, and DNA damage responses that gate progression through the cell cycle.
- **C.** Mitotic cell cycle checkpoint regulation
  - Members at inclusion ≥0.5 cover mitotic cell cycle regulation and checkpoint transitions (G1/S, G2/M) and mitotic kinase signaling (Polo-like kinase). Excludes weaker members (mitotic cell cycle 0.47, TP53 G2 arrest 0.41, GTSE1 0.38) which fit the same checkpoint theme but are below threshold.

