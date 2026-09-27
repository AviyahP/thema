# The three arms of the input pilot, rendered on one real theme (n0065)

*Seed 20260927. Nothing sent. The worked-examples preamble is identical in all three and is
elided here after its first line; everything below the instruction is the whole difference.*

## arm `names`

```
Example input: four pathways -- Interferon alpha/beta signalling; Interferon gamma signalling;
  [... worked examples, identical in all three arms ...]

Name the theme.

  [go] somatic diversification of immune receptors  (inclusion 1.00)

  [go] pro-B cell differentiation  (inclusion 1.00)

  [go] pre-B cell differentiation  (inclusion 1.00)

  [go] regulation of immunoglobulin production  (inclusion 1.00)

  [go] B cell mediated immunity  (inclusion 1.00)

  [go] isotype switching to IgA isotypes  (inclusion 0.60)

  [go] double-strand break repair via classical nonhomologous end joining  (inclusion 0.27)

```

## arm `descriptions`

```
Example input: four pathways -- Interferon alpha/beta signalling; Interferon gamma signalling;
  [... worked examples, identical in all three arms ...]

Name the theme.

  [go] pathway 1  (inclusion 1.00)
      Antigen receptor diversity is not inherited but built in each developing lymphocyte, and this somatic diversification of immune receptors is how a limited germline repertoire yields antibodies and T cell receptors against essentially any pathogen. The same DNA-breaking chemistry also switches antibody isotypes and refines affinity in germinal centres. RAG1 and RAG2 initiate V(D)J recombination, and the resulting breaks are sealed by non-homologous end joining involving DNA-PKcs, Artemis, LIG4, XRCC4 and the shieldin complex under 53BP1 control; AID deaminates cytosine in immunoglobulin loci, and uracil glycosylase plus mismatch repair factors convert those lesions into mutations or class switch recombination. Cytokine and costimulatory inputs such as IL4, CD40 ligation and TGFB1 direct which isotype is chosen. Loss of these steps produces severe combined immunodeficiency, hyper-IgM syndromes, or radiosensitivity with lymphoid malignancy.

  [go] pathway 2  (inclusion 1.00)
      Pro-B cell differentiation is the first committed step of B lymphopoiesis, in which a lymphoid progenitor acquires pro-B identity and begins rearranging the immunoglobulin heavy chain locus by joining D and J segments. Without it there are no mature B cells and no antibody response, and the severe combined immunodeficiency caused by defective DNA repair at this stage illustrates the dependence directly: DNA-PKcs and DNA ligase IV complete the non-homologous end joining that seals the breaks made during V(D)J recombination. Cytokine input through the FLT3 receptor and the RAS exchange factors SOS1 and SOS2 drives progenitor expansion, while Notch signalling and its HES targets bias cells away from the B lineage toward T cell fates, so commitment requires that this pressure be relieved. SOX4 and the folliculin-FNIP1 nutrient-sensing module are further requirements for progression past this checkpoint.

  [go] pathway 3  (inclusion 1.00)
      Pre-B cell differentiation is the stage at which a pro-B cell rearranges its immunoglobulin heavy chain V, D and J segments and displays the resulting mu chain, the step that decides whether a developing lymphocyte can go on to make antibody. Everything downstream of it — a diverse antibody repertoire, mature B cells, humoral immunity — depends on this recombination succeeding, and its failure produces B cell aplasia and agammaglobulinaemia. The recombinase encoded by RAG1 and RAG2 introduces the double-strand breaks at recombination signal sequences, and ATM couples those breaks to the DNA damage response so that joining is completed faithfully and cells with unrepaired breaks are arrested or removed; defects here cause immunodeficiency with genomic instability. Expression of membrane IGHM marks successful rearrangement, while other components support the surface signalling and trafficking that accompany the transition.

  [go] pathway 4  (inclusion 1.00)
      Antibody output by B cells is tuned rather than simply switched on, and the regulation of immunoglobulin production covers the signals and machinery that set how much antibody of which class a response generates. It matters for vaccine responses and mucosal defence, and its dysregulation gives hypogammaglobulinaemia at one extreme and autoantibody disease or IgE-driven allergy at the other. T cell help provides much of the input: costimulatory and TNF-family ligand-receptor pairs such as CD40 with its ligand, CD28-CD86 and OX40 engagement, together with cytokines including IL-4, IL-21, IL-6, IL-10 and TGF-beta acting through STAT6 and lineage factors like BCL6, TBX21 and FOXP3. Inhibitory receptors including CD22 and the low-affinity Fc gamma receptor IIB damp the response. Class switching and somatic diversification require double-strand break repair and mismatch repair components, notably the shieldin complex, 53BP1, RIF1 and MLH1-MSH2-PMS2, while XBP1, MZB1 and DNAJB9 support the secretory expansion of plasma cells.

  [go] pathway 5  (inclusion 1.00)
      B cell mediated immunity covers the effector arm of humoral defence: antibody production, isotype diversification, and the downstream systems that translate antibody binding into pathogen clearance. Immunoglobulin heavy and light chain constant and variable segments dominate here, and with them the machinery of class switch recombination and somatic hypermutation — AICDA deaminates cytosine in switched loci, uracil-DNA glycosylase and mismatch repair proteins process the lesion, and non-homologous end joining with 53BP1, RIF1 and the shieldin complex resolves the resulting breaks. Costimulation through CD40 and its ligand plus cytokines such as IL-4, IL-21 and IL-10 direct which isotype is made, while BCL6 and BATF shape germinal centre fate. Secreted antibody then engages Fcγ and Fcε receptors and the complement cascade, from C1q recognition to the lytic C5b-C9 pore, with regulators like CD55, CD46 and factor I restraining self-damage. Defects produce hyper-IgM syndromes, antibody deficiency and lupus-like autoimmunity.

  [go] pathway 6  (inclusion 0.60)
      Mucosal immunity depends on B cells abandoning IgM and rewriting their heavy chain locus to produce IgA, the antibody secreted across gut, airway and mammary epithelium to neutralise microbes without provoking inflammation. Isotype switching to IgA isotypes is the recombination event that makes this possible: an intrachromosomal deletion joins the switch region upstream of IgM to an IgA switch region, permanently replacing the constant region while leaving antigen specificity intact. TGFB1 is the principal cytokine directing B cells toward this choice, with APRIL (TNFSF13) supplying additional class-switch and survival signals, and CCR6 positioning responding cells in gut-associated lymphoid tissue. Mismatch repair proteins MLH1, MSH2 and PMS2 process the staggered breaks so that switch regions resolve correctly, and chromatin modification by NSD2 helps make the target region accessible. Defects impair secretory antibody defence at mucosal surfaces.

  [go] pathway 7  (inclusion 0.27)
      Double-strand breaks are the most dangerous lesions a genome can carry, and classical nonhomologous end joining is the pathway that rejoins them directly, without needing a homologous template, throughout the cell cycle. It is the route used to seal the programmed breaks of V(D)J recombination, so its loss causes immunodeficiency alongside radiation sensitivity and genome instability. The Ku70 subunit encoded by XRCC6 binds broken ends and recruits the ligase IV complex that performs the final religation, while the chromatin ubiquitin ligase RNF168 and the reader 53BP1 mark damaged nucleosomes and bias repair away from homologous recombination and end resection. Additional factors here couple end joining to transcription-associated damage, checkpoint signalling through TOPBP1, and transcriptional control of repair capacity. Unlike alternative, microhomology-mediated end joining, this pathway rejoins the correct partners and does not generate chromosomal translocations.

```

## arm `both`

```
Example input: four pathways -- Interferon alpha/beta signalling; Interferon gamma signalling;
  [... worked examples, identical in all three arms ...]

Name the theme.

  [go] somatic diversification of immune receptors  (inclusion 1.00)
      Antigen receptor diversity is not inherited but built in each developing lymphocyte, and this somatic diversification of immune receptors is how a limited germline repertoire yields antibodies and T cell receptors against essentially any pathogen. The same DNA-breaking chemistry also switches antibody isotypes and refines affinity in germinal centres. RAG1 and RAG2 initiate V(D)J recombination, and the resulting breaks are sealed by non-homologous end joining involving DNA-PKcs, Artemis, LIG4, XRCC4 and the shieldin complex under 53BP1 control; AID deaminates cytosine in immunoglobulin loci, and uracil glycosylase plus mismatch repair factors convert those lesions into mutations or class switch recombination. Cytokine and costimulatory inputs such as IL4, CD40 ligation and TGFB1 direct which isotype is chosen. Loss of these steps produces severe combined immunodeficiency, hyper-IgM syndromes, or radiosensitivity with lymphoid malignancy.

  [go] pro-B cell differentiation  (inclusion 1.00)
      Pro-B cell differentiation is the first committed step of B lymphopoiesis, in which a lymphoid progenitor acquires pro-B identity and begins rearranging the immunoglobulin heavy chain locus by joining D and J segments. Without it there are no mature B cells and no antibody response, and the severe combined immunodeficiency caused by defective DNA repair at this stage illustrates the dependence directly: DNA-PKcs and DNA ligase IV complete the non-homologous end joining that seals the breaks made during V(D)J recombination. Cytokine input through the FLT3 receptor and the RAS exchange factors SOS1 and SOS2 drives progenitor expansion, while Notch signalling and its HES targets bias cells away from the B lineage toward T cell fates, so commitment requires that this pressure be relieved. SOX4 and the folliculin-FNIP1 nutrient-sensing module are further requirements for progression past this checkpoint.

  [go] pre-B cell differentiation  (inclusion 1.00)
      Pre-B cell differentiation is the stage at which a pro-B cell rearranges its immunoglobulin heavy chain V, D and J segments and displays the resulting mu chain, the step that decides whether a developing lymphocyte can go on to make antibody. Everything downstream of it — a diverse antibody repertoire, mature B cells, humoral immunity — depends on this recombination succeeding, and its failure produces B cell aplasia and agammaglobulinaemia. The recombinase encoded by RAG1 and RAG2 introduces the double-strand breaks at recombination signal sequences, and ATM couples those breaks to the DNA damage response so that joining is completed faithfully and cells with unrepaired breaks are arrested or removed; defects here cause immunodeficiency with genomic instability. Expression of membrane IGHM marks successful rearrangement, while other components support the surface signalling and trafficking that accompany the transition.

  [go] regulation of immunoglobulin production  (inclusion 1.00)
      Antibody output by B cells is tuned rather than simply switched on, and the regulation of immunoglobulin production covers the signals and machinery that set how much antibody of which class a response generates. It matters for vaccine responses and mucosal defence, and its dysregulation gives hypogammaglobulinaemia at one extreme and autoantibody disease or IgE-driven allergy at the other. T cell help provides much of the input: costimulatory and TNF-family ligand-receptor pairs such as CD40 with its ligand, CD28-CD86 and OX40 engagement, together with cytokines including IL-4, IL-21, IL-6, IL-10 and TGF-beta acting through STAT6 and lineage factors like BCL6, TBX21 and FOXP3. Inhibitory receptors including CD22 and the low-affinity Fc gamma receptor IIB damp the response. Class switching and somatic diversification require double-strand break repair and mismatch repair components, notably the shieldin complex, 53BP1, RIF1 and MLH1-MSH2-PMS2, while XBP1, MZB1 and DNAJB9 support the secretory expansion of plasma cells.

  [go] B cell mediated immunity  (inclusion 1.00)
      B cell mediated immunity covers the effector arm of humoral defence: antibody production, isotype diversification, and the downstream systems that translate antibody binding into pathogen clearance. Immunoglobulin heavy and light chain constant and variable segments dominate here, and with them the machinery of class switch recombination and somatic hypermutation — AICDA deaminates cytosine in switched loci, uracil-DNA glycosylase and mismatch repair proteins process the lesion, and non-homologous end joining with 53BP1, RIF1 and the shieldin complex resolves the resulting breaks. Costimulation through CD40 and its ligand plus cytokines such as IL-4, IL-21 and IL-10 direct which isotype is made, while BCL6 and BATF shape germinal centre fate. Secreted antibody then engages Fcγ and Fcε receptors and the complement cascade, from C1q recognition to the lytic C5b-C9 pore, with regulators like CD55, CD46 and factor I restraining self-damage. Defects produce hyper-IgM syndromes, antibody deficiency and lupus-like autoimmunity.

  [go] isotype switching to IgA isotypes  (inclusion 0.60)
      Mucosal immunity depends on B cells abandoning IgM and rewriting their heavy chain locus to produce IgA, the antibody secreted across gut, airway and mammary epithelium to neutralise microbes without provoking inflammation. Isotype switching to IgA isotypes is the recombination event that makes this possible: an intrachromosomal deletion joins the switch region upstream of IgM to an IgA switch region, permanently replacing the constant region while leaving antigen specificity intact. TGFB1 is the principal cytokine directing B cells toward this choice, with APRIL (TNFSF13) supplying additional class-switch and survival signals, and CCR6 positioning responding cells in gut-associated lymphoid tissue. Mismatch repair proteins MLH1, MSH2 and PMS2 process the staggered breaks so that switch regions resolve correctly, and chromatin modification by NSD2 helps make the target region accessible. Defects impair secretory antibody defence at mucosal surfaces.

  [go] double-strand break repair via classical nonhomologous end joining  (inclusion 0.27)
      Double-strand breaks are the most dangerous lesions a genome can carry, and classical nonhomologous end joining is the pathway that rejoins them directly, without needing a homologous template, throughout the cell cycle. It is the route used to seal the programmed breaks of V(D)J recombination, so its loss causes immunodeficiency alongside radiation sensitivity and genome instability. The Ku70 subunit encoded by XRCC6 binds broken ends and recruits the ligase IV complex that performs the final religation, while the chromatin ubiquitin ligase RNF168 and the reader 53BP1 mark damaged nucleosomes and bias repair away from homologous recombination and end resection. Additional factors here couple end joining to transcription-associated damage, checkpoint signalling through TOPBP1, and transcriptional control of repair capacity. Unlike alternative, microhomology-mediated end joining, this pathway rejoins the correct partners and does not generate chromosomal translocations.

```

