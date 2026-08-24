# Data licensing and attribution

THEMA builds its ontology from four public pathway and gene-set resources, and resolves their gene
symbols against a fifth, HGNC. This file records what each one is, the licence it is distributed
under, the attribution its licence requires, and the exact bytes THEMA was built from.

It covers **third-party data only** — not THEMA's own source code, which carries its own licence.

The facts below are taken from `data/raw/VERSIONS.txt`, the manifest written by
`scripts/download_pathway_data.py`. That manifest is gitignored along with the rest of `data/raw/`,
so this file is the committed record of the frozen release: sha256 digests are reproduced in full
here so a build can be traced without re-downloading anything. Re-run the script and the manifest
regenerates identically from disk.

**Frozen release identifiers.** Reactome V97 · GO 2026-08-05 · MSigDB 2026.1.Hs · BTM commit
`94d5288` · HGNC quarterly 2026-07-07. If any of those change, this file and `VERSIONS.txt` must be
updated together.

Licence terms were verified against each provider's own published terms on 23 August 2026 — GO's
citation-policy page, MSigDB's license-terms pages, Reactome's license agreement, and the BTM
repository's `LICENSE` file — and HGNC's licence page on 24 August 2026.

---

## Reactome — CC0 1.0

All data in the Reactome database, and files derived from that data, are released into the public
domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): copy, modify and
redistribute freely, including commercially, with attribution encouraged but not required. THEMA
attributes it anyway, and cites it, as the project's brief directs.

Note that CC0 covers Reactome's **data files only** — which is all THEMA uses. Reactome's pathway
illustrations, icon library, art and branding materials are separately licensed under CC BY 4.0,
so any future use of Reactome diagrams or logos carries an attribution obligation this file does
not currently discharge.

> Reactome (<https://reactome.org>), release V97, is made available under the terms of the CC0 1.0
> public domain dedication.

**Cite:** Ragueneau E, Gong C, Sinquin P, et al. The Reactome Knowledgebase 2026. *Nucleic Acids
Research*. 2025 Nov 18. doi:[10.1093/nar/gkaf1223](https://doi.org/10.1093/nar/gkaf1223)

**Used for:** the pathway list, the curated parent/child hierarchy, human gene sets, and curated
pathway descriptions. Reactome's hierarchy also serves as THEMA's built-in QC anchor — the learned
themes should broadly recover its top levels.

| File | Bytes | sha256 |
|---|---:|---|
| `ReactomePathways.txt` | 1,592,393 | `f6d7a2bf89b5bcfe0250a0bc7f51bff94641447911712b8ff129f5b55e52df3a` |
| `ReactomePathwaysRelation.txt` | 634,259 | `fd49a624d80c14eb37ae57a02e141d574d5ede3f60022bb99edbd909448a3f1e` |
| `ReactomePathways.gmt` | 1,032,186 | `89983d5c1f0af11c52edfeee7323eb425580ac6281d387a528562ab1787ce56b` |
| `pathway2summation.txt` | 3,574,435 | `b036d5b81fa510bf45cd8ea213763f8c729a49ca72618bc096fb7ff46a7bf1c2` |
| `reactome_release.txt` | 2 | `d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091` |

Downloaded from `https://reactome.org/download/current/`. Reactome publishes no stable
per-release download path for these files, so the release number is captured separately from
its ContentService into `reactome_release.txt` — this frozen build is **V97**.

---

## Gene Ontology — CC BY 4.0

GO data is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The licence requires identifying the
creator, a notice referring to the licence, and a link to the material. GO additionally asks that
the specific release be stated, since ontology content changes between releases.

> Gene Ontology data from the 2026-08-05 release
> (<https://release.geneontology.org/2026-08-05/>, archived at
> doi:[10.5281/zenodo.1205166](https://doi.org/10.5281/zenodo.1205166)) is made available by the
> Gene Ontology Consortium under the terms of the
> [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) licence.

The DOI above is GO's concept DOI, which resolves to all versions; each monthly release also
carries its own versioned DOI, obtainable from the Zenodo record for this release date.

**Cite both**, as GO's citation policy requires:

- Ashburner M, Ball CA, Blake JA, et al. Gene ontology: tool for the unification of biology.
  *Nature Genetics*. 2000;25(1):25–29. doi:[10.1038/75556](https://doi.org/10.1038/75556)
- The Gene Ontology Consortium. The Gene Ontology knowledgebase in 2026. *Nucleic Acids Research*.
  2025 Dec 18. doi:[10.1093/nar/gkaf1292](https://doi.org/10.1093/nar/gkaf1292)

**Used for:** GO term names, definitions, and the Biological Process DAG. THEMA filters to
`namespace: biological_process`; MF and CC are deliberately excluded.

| File | Bytes | sha256 |
|---|---:|---|
| `go-basic.obo` | 32,227,785 | `b08d45b268b8c24ccb2513dbbbc7d4df9f6521c099b413f79eb31e06e0fa3bcc` |

Downloaded from `https://release.geneontology.org/2026-08-05/ontology/go-basic.obo` — a pinned
dated release directory, never the floating `current.geneontology.org` alias. Note that the file's
own `data-version` header reads `releases/2026-07-26`, which differs from the directory date; both
are recorded in `VERSIONS.txt`.

---

## MSigDB — CC BY 4.0 (for the collections THEMA uses)

MSigDB contents are copyright © 2004–2026 Broad Institute, Inc., Massachusetts Institute of
Technology, and Regents of the University of California, and for releases v6.0–v7.5.1 and v2022.1
and above are distributed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — **with further restrictions on some
gene sets**, detailed under "Excluded collections" below.

> MSigDB 2026.1.Hs gene sets are copyright © 2004–2026 Broad Institute, Inc., Massachusetts
> Institute of Technology, and Regents of the University of California, made available under the
> terms of the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) licence.

**Cite:**

- Subramanian A, Tamayo P, Mootha VK, et al. Gene set enrichment analysis: a knowledge-based
  approach for interpreting genome-wide expression profiles. *PNAS*. 2005;102(43):15545–15550.
  doi:[10.1073/pnas.0506580102](https://doi.org/10.1073/pnas.0506580102)
- Liberzon A, Birger C, Thorvaldsdóttir H, et al. The Molecular Signatures Database hallmark gene
  set collection. *Cell Systems*. 2015;1(6):417–425.
  doi:[10.1016/j.cels.2015.12.004](https://doi.org/10.1016/j.cels.2015.12.004)

**Used for:** the Hallmark (H) collection and C5 GO:BP gene sets, plus per-set metadata. The C5
metadata's `exactSource` field carries each set's GO term id, which joins to `go-basic.obo`.

| File | Bytes | sha256 |
|---|---:|---|
| `h.all.v2026.1.Hs.symbols.gmt` | 48,686 | `eecaf6dad908334ae885406ec72bdc0646d8917588ed7c219fac92fc5363f596` |
| `c5.go.bp.v2026.1.Hs.symbols.gmt` | 4,872,550 | `9be09dd06d6652566eb52eed530d62e6dfecc4365c1e81afd6f0b7f2e86dd4f9` |
| `genesets_v2026.1.Hs.json` | 8,545 | `d7edbb7b90a93e7f46e0e79742bb73b759411fde598f52a95cded3069d71d3b7` |
| `h.all.v2026.1.Hs.json` | 73,082 | `bc465ea8f94009689abdff725ffa16bbd9a38a7d13a876d046727fae49f61f2c` |
| `c5.go.bp.v2026.1.Hs.json` | 8,127,866 | `ff73a093fc175272f5ccdc424dbf3a6d138810ebfcb8fa90d3b0f13f631f34c0` |
| `msigdb_v2026.1.Hs.xml` | 220,619,850 | `3e11bf461a6f3743aa1a9c6d82ef7ca250963f7b932c0224c15a16d9af892644` |

Downloaded from `https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2026.1.Hs/`.

### Excluded collections, and one caveat about the XML

MSigDB's CC BY 4.0 grant does not cover everything it distributes. THEMA deliberately uses **only**
Hallmark and C5:GO:BP, both of which are clean CC BY 4.0. The restricted subsets, all in C2, are
excluded from THEMA's ontology:

| Subset | Prefix | Terms |
|---|---|---|
| KEGG MEDICUS | `KEGG_MEDICUS_` | © 2009–2023 Kanehisa Laboratories — CC BY-**SA** 4.0 (share-alike) |
| KEGG legacy | `KEGG_` | © 1995–2017 Kanehisa Laboratories — licensed to Broad only, subject to Kanehisa's academic/commercial policies |
| BioCarta | `BIOCARTA_` | © 2000–2017 BioCarta — licensed to Broad only, subject to BioCarta's disclaimer |

**The caveat.** `msigdb_v2026.1.Hs.xml` is a whole-database file: it is the only source of
per-gene-set prose descriptions, and it therefore contains entries for *every* collection,
including the three restricted subsets above. Holding the file is fine; what matters is that
downstream code must read only the `H` and `C5:GO:BP` entries from it. Anything that ingests this
XML should filter on the `CATEGORY_CODE` / collection field rather than consuming it wholesale,
or the share-alike and restricted-licence sets will silently enter the ontology.

WikiPathways (`C2:CP:WIKIPATHWAYS`) is also clean CC BY but is deferred to v1.1; it is not
downloaded.

---

## Blood Transcription Modules (BTM) — see note on licensing

The BTM gene sets are the supplementary data of Li et al. 2014, redistributed by the paper's first
author at <https://github.com/shuzhao-li/BTM>. THEMA pins the file to commit `94d5288`, which makes
the download content-addressable.

**Cite:** Li S, Rouphael N, Duraisingham S, et al. Molecular signatures of antibody responses
derived from a systems biology study of five human vaccines. *Nature Immunology*.
2014;15(2):195–204. doi:[10.1038/ni.2789](https://doi.org/10.1038/ni.2789) · PMID 24336226

**Used for:** immunology-focused gene sets that are more granular than pathway databases. BTM ships
module *names* but no descriptions, so it is also the source that exercises THEMA's LLM-expansion
path.

| File | Bytes | sha256 |
|---|---:|---|
| `BTM_for_GSEA_20131008.gmt` | 68,196 | `dff51cc7df3c30f26ad75ba75ca89081c08300d38a5ba2649087477b22408b67` |

**Licensing note — this one is less clean than the others.** The gene sets were published as
supplementary material to a Nature Immunology paper and are freely and widely redistributed
(they ship in the `tmod` R package among others), but there is no explicit data licence attached
to them. The GitHub repository carries a `LICENSE` file whose text is an MIT licence reading
"Copyright (c) 2018 The Python Packaging Authority" — boilerplate left over from a Python packaging
template, which plainly was not written to cover this dataset. Treat BTM as freely usable with
attribution to the paper, and do not rely on that MIT file as the grant. If THEMA is ever
redistributed commercially, confirm the position with the authors.

---

## HGNC — CC0 1.0

The HUGO Gene Nomenclature Committee assigns the approved symbols and the permanent `HGNC:` gene
identifiers that THEMA resolves every source symbol to. It is not a source of gene *sets*; it is the
identifier space the four sources above are unified into, without which a cross-database gene union
silently under-counts.

> All HGNC data is released under the Creative Commons Public Domain (CC0) License; any form of
> reuse of the content is permitted. Attribution is not mandatory but is recommended.

**Cite:** Seal RL, Braschi B, Gray K, Jones TEM, Tweedie S, Haim-Vilmovsky L, Bruford EA.
Genenames.org: the HGNC resources in 2023. *Nucleic Acids Research*. 2023;51(D1):D1003–D1009.
doi:[10.1093/nar/gkac888](https://doi.org/10.1093/nar/gkac888) · RRID:SCR_002827

**Used for:** resolving gene symbols to stable HGNC ids in `src/thema/data/genes.py`, including the
derived 2013 era lens that BTM is read through. `hgnc_complete_set` holds approved records only, so
`withdrawn.txt` is downloaded alongside it — it is the only source of the merge map that carries a
retired identifier forward to its current one.

| File | Bytes | sha256 |
|---|---:|---|
| `hgnc_complete_set_2026-07-07.txt` | 16,913,890 | `e73e9259177884b5994fc81ed733c1b3d4df34c84290bc9dddc86e960d5d6419` |
| `withdrawn_2026-07-07.txt` | 258,931 | `77235063bba9492d09997e58387a50b6f750aed2de67a44c519c920b48f7ff87` |

**A note on pinning.** HGNC's advertised current-release URL carries no version identifier at all,
so THEMA pins the dated quarterly `2026-07-07` instead, in the same spirit as the GO release
directory and the BTM commit. `2026-07-07` specifically because it is the most recent quarterly that
publishes *both* files: `withdrawn_2026-07-03.txt` does not exist. Note that HGNC's archive is not
guaranteed permanent — no snapshot before 2020-07-01 survives anywhere, the historical
`ftp.ebi.ac.uk` tree is retired, and the Wayback Machine never captured it. If a build must be
reproducible years from now, mirror these two files rather than trusting the URL.

---

## Summary

| Source | Release | Licence | Attribution required |
|---|---|---|---|
| Reactome | V97 | CC0 1.0 | No (given voluntarily) |
| Gene Ontology | 2026-08-05 | CC BY 4.0 | Yes — creator, licence notice, link, release date |
| MSigDB (H, C5:GO:BP) | 2026.1.Hs | CC BY 4.0 | Yes — copyright notice and licence |
| BTM | commit `94d5288` | No explicit data licence; public | Cite Li et al. 2014 |
| HGNC | quarterly 2026-07-07 | CC0 1.0 | No (recommended, given voluntarily) |

Deliberately excluded for licensing: **KEGG** (all variants) and **BioCarta**.
Deferred to v1.1: **WikiPathways**.
