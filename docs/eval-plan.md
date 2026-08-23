# THEMA — Evaluation Plan

*Written 22 Aug 2026, before Phase 2, so the build logs what evaluation needs. Synthesizes two literature sweeps (20 & 22 Aug 2026; sources at bottom). The repo's `DECISIONS.md` and `docs/brief.md` remain authoritative for design; this document is authoritative for how THEMA is judged.*

---

## 0. The framing: four separable claims, four evaluations

"Is THEMA good?" decomposes into four claims that are tested independently — a tool can pass one and fail another, and reporting them separately is what makes the evaluation honest:

1. **Structure** — the ontology's clusters and hierarchy reflect real biology.
2. **Naming** — the LLM names faithfully describe what's in each theme.
3. **Statistics** — the analysis finds planted truth with the error control it claims.
4. **Utility** — on real data, the output is more usable than the alternatives, per an expert.

## 1. What the field does (from the 20 Aug sweep) — and where it's weak

Five evaluation families exist in the literature: (a) ARI vs. a hand-curated ground truth — only MAPA does this, on a tiny 44-pathway/12-module set partly derived from the ontologies themselves (circular); (b) internal cluster-quality indices (silhouette etc.) — circular by construction, each tool wins its own metric (simplifyEnrichment, SummArIzeR, Transcripta); (c) separation statistics between within/cross-module similarity (MAPA's Cliff's δ — good, rarely done); (d) naming quality via semantic-similarity percentile rank against all GO names (Hu et al. Nat Methods 2025 with SapBERT; GeneAgent 2025 with MedCPT — the best-developed protocol in the area); (e) negative controls and adversarial stress (random/contaminated gene sets, context swaps — Hu, MAPA, LLM-PathwayCurator; cheapest high-signal tests, almost never done). No shared benchmark exists; no tool evaluates against the reference hierarchies; commercial tools (QIAGEN IPA's AI) publish no evaluation at all.

**THEMA's evaluative stance:** score against *external* references wherever one exists, use internal indices never as headline numbers, and always include negative controls. Each subsection below names its gold standard, metric, baseline, and cost.

## 2. Claim 1 — Structure: does the ontology recover known biology?

The ontology-first pivot makes this the flagship evaluation, and it's the one nobody in the field runs.

**2a. Reference-hierarchy recovery (primary).** We possess two expert-built hierarchies over our own leaves: Reactome's curated pathway tree and GO:BP's is_a DAG. Test: does THEMA's tree, built from text+embeddings alone, recover them?
- **Metric 1 — Ancestor-pair F1** (taxonomy-induction standard; Bansal ACL 2014, TaxoRL): compare the sets of leaf pairs that share ancestry in our tree vs. the reference; needs no correspondence between our invented theme nodes and reference nodes; DAG-native for GO. Headline number.
- **Metric 2 — ARI/AMI curves across cuts**: our tree cut at k vs. Reactome levels 1–3 / GO slims, plotted over k (never one cherry-picked cut). Reviewer-familiar; the Phase-3 QC anchor check is a mini version of this.
- **Metric 3 — Cophenetic Spearman**: our merge heights vs. Reactome path distance and GO Resnik/Lin similarity on ~10⁶ sampled pairs (precedent: Anc2vec, OWL2Vec* subsumption evaluations).
- **Circularity caveat, stated**: Reactome/GO descriptions were written by the same curators who built the hierarchies — recovery is partly "the text encodes the tree." This makes recovery a *validity floor*, not proof of discovery. The non-circular complement is 2b.

**2b. Cross-database merging (the product's core claim).** THEMA claims to merge redundant biology *across* sources. Gold standards among our v1 sources:
- **reactome2go** (official, versioned, CC BY; current.geneontology.org/ontology/external2go/reactome2go): curated Reactome-pathway↔GO-term mappings. Test: mapped pairs should co-cluster (same theme / low tree distance) far more than random cross-source pairs. Metrics: pairwise AUROC on tree distance; % mapped pairs sharing a theme at the tested cut, vs. matched random pairs. **This is the single best non-circular test we have** — the mapping is human-curated and external to our inputs' prose.
- **Hallmark founder sets** (secondary; Liberzon 2015): each Hallmark set lists the Reactome/GO sets it was derived from — a "should co-cluster" signal, not strict equivalence. Scrape/registration required; treat as soft.
- ComPath: verified *not* usable for v1 (covers KEGG/WikiPathways pairs only). BTM↔GO: no machine-readable mapping exists (Li 2014 shipped HTML); any mapping is build-it-yourself via gene overlap — excluded from gold standards to avoid circularity with our own methods.

**2c. Embedding-level checks** (before any clustering): Cliff's δ / AUROC separating known-same pairs (reactome2go; sibling terms in GO) from known-different pairs — evaluates the similarity signal independent of the clustering algorithm (MAPA's move, done on non-circular pairs). Plus the **source-leakage A/B** (already an OPEN decision): classifier predicting source DB from embedding; cluster–source stratification — decides embed-as-is vs. LLM-normalized descriptions.

**2d. Comparability with the field:** run THEMA's pipeline on MAPA's public 44/12 benchmark set and report ARI beside their published numbers (MAPA 0.95, aPEAR 0.33, PAVER 0.23) — small and partly circular, but the only number that lets a reader place us on the existing map.

**Baselines for all of 2a–2b:** (i) gene-overlap Jaccard + average-linkage (the Metascape-style classic), (ii) name-only embeddings without descriptions, (iii) random trees (floor). LLM methods look good against nothing; these make the comparison honest.

## 3. Claim 2 — Naming: are theme names faithful?

Adopt the field-standard percentile protocol, on clusters with known answers:
- **Known-parent test**: take a reference node (GO parent / Reactome parent), give the namer its children as a cluster; gold = the parent's own name. Score = semantic similarity of generated vs. gold name, expressed as the **percentile against all ~12k GO:BP names** (raw cosines between biomedical strings are uniformly high and meaningless; percentile is what's interpretable). Report both **SapBERT** (Hu et al.) and **MedCPT** (GeneAgent) encoders, plus ROUGE-L as a cheap token-overlap secondary. Report fraction of names at ≥90th / ≥98th percentile.
- **Abstention negative control**: feed deliberately incoherent clusters (random pathways, size-matched); the namer should invoke its abstention ("would break cluster into sub-clusters") — report abstention rate on random vs. real clusters. (Hu et al.: GPT-4 zeroed confidence on 87% of random sets while enrichment tools "annotated" 73% of contaminated ones — this contrast is the model.)
- **Stability**: 5–10 reruns; pairwise cosine of names per node; one prompt-wording perturbation (SPINDOCTOR documented real prompt fragility; nobody re-measures it).

## 4. Claim 3 — Statistics: does the pipeline deliver its claimed error control?

- **Planted-truth simulation** (first item, already in DECISIONS): synthetic DEG lists / rankings with chosen truly-enriched nodes → full pipeline → measure realized false-discovery proportion vs. claimed FDR, power by effect size, and **attribution accuracy** (does credit land at the planted node — child vs. parent — per the three-test protocol?). Sweep: signal strength, contamination fraction, planted-node depth.
- **Empirical-FDR audit vs. BH** (already in DECISIONS): agreement validates BH on our tree; disagreement ships as the honest number.
- **Contamination sweep** (Hu-style): replace 25/50/75/100% of a truly-enriched node's signal genes with random ones; plot detection and attribution vs. contamination.

## 5. Claim 4 — Utility: is it better to use, on real data?

Small, honest, labelled as such:
- **Known-biology checks** (evoGO-style): on the demo datasets (public GSEA example; TCGA enrichment tables), the top themes should contain the a-priori-expected biology (e.g., proliferation/cell-cycle themes in a tumor contrast). Keyword-defined truth; crude, transparent.
- **Side-by-side vs. defaults**: same input through THEMA, Metascape-style clustering, and simplifyEnrichment; compare output size (nodes to read), redundancy index, and coverage of the known-biology keywords. Report a table, not a victory lap.
- **Expert read** (n=1, declared): Aviyah — the target user — blind-ranks the three outputs for "what would I trust to brief a team." n=1 stated plainly; inter-rater work is listed as future.
- **Cost/latency**: tokens and wall-clock per 500-term input, reported (nobody reports cost; users care).

## 6. What runs when

- **In the sprint (already planned, now formalized):** Phase 2 — source-leakage A/B (2c) decides the normalization question; Phase 3 — the QC anchor check *is* a first ARI-at-cuts vs. Reactome (2a-lite) and gates the go/no-go.
- **Phase 2 of the project (the evaluation suite proper, ~3–5 days):** Day 1: structure metrics vs. both references + baselines (2a, 2b, 2d). Day 2: naming protocol + abstention + stability (3). Day 3: planted-truth + FDR audit + contamination (4). Day 4: utility table + expert read + cost (5). Day 5: write-up with figures; every number lands in the README with its caveat attached.
- **Explicitly out of scope** (stated so nobody pretends): downstream biological-decision utility; multi-expert panels; wet-lab validation. Nobody in the field has these either; we say so instead of implying otherwise.

## 7. The one-line answers to "compared to what, on what data, against which gold standard"

**Compared to:** gene-overlap clustering (the classic), name-only embeddings, random floors — plus MAPA's published ARI on their own benchmark for field placement, and Metascape/simplifyEnrichment outputs for the utility table. **Data:** entirely from our frozen v1 sources + two public demo enrichment inputs + simulation. **Gold standards:** Reactome's own tree and GO's is_a DAG (structure, with the circularity caveat stated); the curated **reactome2go** mapping (cross-source merging — the strongest non-circular standard we have); reference node names (naming, percentile protocol); and planted truth we control (statistics). All free, all versioned, all already on disk or one small download away.

---

*Key sources: MAPA (bioRxiv 2025.08.23.671949); Hu et al., Nat Methods 2025 (s41592-024-02525-x) + code (idekerlab/llm_evaluation_for_gene_set_interpretation); GeneAgent, Nat Methods 2025 (s41592-025-02748-6); Bansal et al. ACL 2014 (P14-1099); SemEval TExEval-2 2016; Anc2vec (Brief Bioinform 2022); OWL2Vec* (Mach Learn 2021); reactome2go (current.geneontology.org/ontology/external2go/reactome2go); Liberzon et al. 2015 (Hallmark founders); ComPath (npj Syst Biol Appl 2019 — verified not applicable to v1 sources); Li et al. 2014 BTM supplement (no machine-readable GO mapping); simplifyEnrichment (GPB 2023); SetRank (BMC Bioinf 2017); evoGO (bioRxiv 2025); Transcripta Bio post (Oct 2025 — internal-metrics-only precedent); Wijesooriya et al. 2022 (backgrounds); Goeman & Bühlmann 2007 (nulls).*
