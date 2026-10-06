# Related work and defence

*Created 5 Oct 2026. **No related-work or defence document existed in this repository** — the C8
brief refers to "the repo's related-work/defence doc", and there was none, so this is it. Earlier
citations lived scattered in source docstrings (`consensus.py` cites Bryant 2003 and Felsenstein
2004; `evaluation.py` cites Gower & Legendre 1986) and in `amendment-2026-09-25.md`.*

## Methods that build multi-resolution hierarchies from a similarity graph

- **HiDeF** — Zheng, F., Zhang, S., Churas, C., Pratt, D., Bahar, I. & Ideker, T. (2021).
  *HiDeF: identifying persistent structures in multiscale 'omics data.* **Genome Biology** 22:21.
  Sweeps Leiden resolutions and keeps communities that **persist** across them, then organises them
  by containment. The closest published method to `recurrent_dag`: both ask which groups survive a
  perturbation, HiDeF perturbing the resolution where THEMA perturbs the sample.

- **CliXO** — Kramer, M., Dutkowski, J., Yu, M., Bafna, V. & Ideker, T. (2014).
  *Inferring gene ontologies from pairwise similarity data.* **Bioinformatics** 30(12):i34–i42.
  Builds a DAG by thresholding a similarity matrix downward and extracting maximal cliques, with
  α controlling clique relaxation and β the threshold step. **Not evaluated here: the implementation
  could not be obtained** — absent from PyPI, no binary in DDOT, and four plausible source
  repositories return *Repository not found*.

- **DDOT** — Yu, M. K., Ma, J., Ono, K., Zheng, F., Fong, S. H., Gary, A., Chen, J., Demchak, B.,
  Pratt, D. & Ideker, T. (2019). *DDOT: a Swiss army knife for investigating data-driven biological
  ontologies.* **Cell Systems** 8(3):267–273. The toolkit around CliXO — alignment to curated
  ontologies, I/O, visualisation. Installed cleanly but ships **no CliXO executable**.

- **MuSIC** — Qin, Y., Winsnes, C. F., Huttlin, E. L., Zheng, F., Ouyang, W., Park, J., Pitea, A.,
  Kreisberg, J. F., Gygi, S. P., Harper, J. W., Ma, J., Lundberg, E. & Ideker, T. (2021).
  *A multi-scale map of cell structure fusing protein images and interactions.* **Nature**
  600:536–542. Fuses immunofluorescence images with interaction proteomics into a single similarity,
  then runs the CliXO/HiDeF family over it. The precedent for **embedding two unlike modalities into
  one similarity and clustering that**, which is what THEMA does with curated and generated prose.

- **Multimodal cell maps** — Schaffer, L. V. et al. (2025). Applies **HiDeF to learned embeddings**
  rather than to a measured interaction network. The direct precedent for the comparison run on
  4 Oct: HiDeF on MedCPT vectors is not a misuse of the method but its published mode of use.

## Concurrent work on reconstructing pathway hierarchies from text

- **Bravi et al.** (2026). arXiv:2608.28178, 31 Aug 2026. **SPECTER2 embeddings with agglomerative
  clustering reconstruct Reactome's hierarchy.** Concurrent with this work and independent of it.
  **Scope differs in two ways that matter**: it targets **Reactome only**, where THEMA spans
  Reactome, GO BP, Hallmark and BTM in one universe; and it produces a **tree**, where THEMA
  produces a DAG with soft multi-parent membership. It is the closest published result to THEMA's
  central claim and should be treated as the baseline to beat on Reactome specifically, not as a
  general refutation.

## How data-driven ontologies are evaluated in the literature — the gold standard

Added 6 Oct 2026, alongside the A/B/HiDeF protocol, because THEMA's evaluations to date have rested
on a measure of its own devising (specificity AUROC on curated sibling pairs) and the field has
established ones. Each line below is what the paper actually did, not a paraphrase of its claim.

- **CliXO** (Kramer, Dutkowski, Ono, Ideker & Krogan, *Bioinformatics* 30(12):i246–i254, 2014).
  Alignment to GO scored against **label-permuted ontologies of the same shape** — the null keeps
  the inferred structure and destroys only the mapping from terms to genes — with **precision and
  recall reported at FDR < 5% per size bin**, plus **noise and edge-dropout simulations** to show
  how far the recovery survives degraded input. The per-size-bin FDR and the shape-preserving
  permutation null are the two ideas THEMA's protocol borrows directly.
- **HiDeF** (Zheng, Zhang, Liu, ... & Ideker, *Nature Communications* 12:2971, 2021). **F1 against
  GO and the Cell Ontology, counting a match when Jaccard > 0.5**, and **two-level LFR planted
  benchmarks** with known community structure at two resolutions. The Jaccard > 0.5 match criterion
  is the one the protocol adopts as its floor.
- **NeXO** (Dutkowski, Kramer, Surma, ... & Ideker, *Nature Biotechnology* 31:38–45, 2013) and
  **MuSIC** (Qin, Fisher, Rajan, ... & Ideker, *Nature* 600:536–542, 2021). Both go past alignment to
  **external validation of terms the data-driven ontology proposes and the reference lacks** — NeXO
  by literature and experiment for novel branches, MuSIC by orthogonal imaging and proteomics for
  previously unmapped assemblies. This is the standard a new term has to meet to count as a finding
  rather than an artefact, and THEMA has never attempted it.
- **Ontology-learning metrics.** **Taxonomic precision and recall** (Dellschaft & Staab, *ISWC
  2006*), which score a learned taxonomy by the overlap of each concept's characteristic extract
  against the reference rather than by exact node matching; and **ancestor-pair F1** (Bansal, Burkett,
  de Melo & Klein, *NAACL 2014*), which scores the set of ancestor–descendant pairs the hierarchy
  implies. Both are pair-level and so insensitive to how a hierarchy is cut, which is exactly the
  property THEMA's band-restricted scores had to be engineered to obtain.

**Where THEMA stands against this.** THEMA has had the permutation-null idea since its scramble
floors, but applied to *support* rather than to *alignment*; it has never run a planted benchmark,
never reported precision and recall against curated sets at a controlled FDR per size bin, and never
externally validated a theme the reference lacks. The 6 Oct protocol adds the first three.
Ancestor-pair F1 was specified in the v0.2 plan (§14 item 3) and **has still not been built** — it
remains the clearest gap between THEMA's evaluation and the field's.

## The HiDeF verdict, in one line

**THEMA stays**: under a rule declared before the build, THEMA is significantly better on both
Reactome specificity-AUROC cells and misses nothing HiDeF gains on GO, while HiDeF fails the
zero-gene recovery tolerance on Reactome by 9.9 points — but HiDeF is ~4x cheaper, rejects the
scrambled null just as completely, and wins the 51–500-member granularity band, where THEMA has only
141 themes against HiDeF's 249.
