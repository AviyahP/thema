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

## The HiDeF verdict, in one line

**THEMA stays**: under a rule declared before the build, THEMA is significantly better on both
Reactome specificity-AUROC cells and misses nothing HiDeF gains on GO, while HiDeF fails the
zero-gene recovery tolerance on Reactome by 9.9 points — but HiDeF is ~4x cheaper, rejects the
scrambled null just as completely, and wins the 51–500-member granularity band, where THEMA has only
141 themes against HiDeF's 249.
