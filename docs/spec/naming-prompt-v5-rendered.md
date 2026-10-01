# The naming prompt, rendered: `name-v5`

*Written 29 Sep 2026 from `data/ontology/v0.2/recurrent_dag_c50`. **Nothing has been sent.***

There is ONE prompt. The system prompt below is used for every call -- leaf, internal node and
collision re-ask alike. The user message is data with a single line of instruction: no worked
examples, no source tags, no inclusion values, no identifiers, title and description only.

- system prompt: **314 words**
- leaf message shown: `n0022`, 4 pathways, **544 words**
- internal message shown: `n0424`, 2 children and 3 direct pathways, **453 words**

---

## System prompt

```
You name clusters in an ontology of human biological pathways. The ontology is a DAG: a
hierarchy of clusters, each made of pathways and/or child clusters. A pathway is a set of genes
co-acting in a specific biological process, given here with its title and a description.

The name you give a cluster must state the biological theme or process shared by ALL of its
members — every pathway and every child cluster listed — as tightly as possible: the most specific
theme that is true of all of them. Do not generalise further than the members require; a broader
name belongs to the parent, one level up. What drives the name is shared biological meaning, not
shared wording.

Name only what the members contain. Do not assert a gene, mechanism, compartment or pathway that
only one or two members concern. A name that is too broad is a minor fault; a name that invents is
a serious one, because a reader cannot tell.

Every name will sit beside hundreds of others in a browsable hierarchy, so every name must read as
though written by the same person on the same day. Up to 10 words, fewer than 6 preferred; sentence
case; no leading article; a noun phrase unless a short clause is tighter. No filler words
("various", "related", "processes", "pathways", "mechanisms"), no database names, no identifiers,
no bare category words ("Metabolism", "Signalling"), and never one member's own title as the name.
A name must not be identical to any other name in the hierarchy.

If the members share no nameable biological theme — if the only name covering all of them would
cover much else besides, or would be an invention — say so. That is a real and useful answer.

Return an object: {"nameable": true|false, "name": "<name, or empty>", "rationale": "<one
sentence: what the members share, or why they cannot be named>"}.
```

## A leaf message

```
Name this cluster. Its pathways:

KW2449-resistant FLT3 mutants
Activating mutations in the FLT3 receptor tyrosine kinase drive proliferation and survival of myeloid blasts and are among the most common lesions in acute myeloid leukaemia, making the receptor a prime drug target. KW-2449 is a type I inhibitor that binds the active kinase conformation and blocks signalling through several mutant FLT3 alleles, including internal tandem duplications of the juxtamembrane region, but certain substitutions in the kinase domain and activation loop alter the ATP pocket so that the drug no longer engages productively. Cells carrying these KW-2449-resistant variants retain constitutive, ligand-independent FLT3 signalling to STAT5, RAS-MAPK and PI3K-AKT despite treatment, and such alleles account for relapse after targeted therapy. Cataloguing them matters for choosing between type I and type II inhibitors and for interpreting resistance mutations that emerge under selection.

gilteritinib-resistant FLT3 mutants
Activating mutations in the receptor tyrosine kinase FLT3 drive a large fraction of acute myeloid leukaemia, and gilteritinib is a type I inhibitor used to shut that signalling down. Clinical benefit is often lost when the receptor acquires secondary changes that no longer permit effective drug binding, and this grouping describes gilteritinib-resistant FLT3 mutants, which restore ligand-independent kinase activity and downstream proliferative and survival signalling through STAT5, RAS-MAPK and PI3K routes despite continued treatment. Because type I inhibitors engage the active kinase conformation, substitutions in the activation loop and kinase domain, as well as alternative resistance alleles arising on the background of internal tandem duplications, are the usual cause of relapse. Understanding which variants confer resistance guides the choice between inhibitor classes and explains the limited durability of single-agent FLT3-targeted therapy in myeloid leukaemia.

sorafenib-resistant FLT3 mutants
FLT3 is a receptor tyrosine kinase that drives proliferation and survival of hematopoietic progenitors, and activating mutations in it — most often internal tandem duplications in the juxtamembrane region — are among the most common lesions in acute myeloid leukemia, where they predict relapse. Sorafenib, a type II inhibitor that binds the inactive kinase conformation, suppresses such mutants and can produce responses in FLT3-mutant disease, but treatment selects for sorafenib-resistant FLT3 variants. Substitutions in the activation loop and at the gatekeeper position stabilize the active conformation or occlude the drug pocket, so the receptor continues to autophosphorylate and signal through STAT5, RAS–MAPK and PI3K–AKT despite drug exposure. This resistance underlies loss of response in the clinic and motivates type I and next-generation FLT3 inhibitors, illustrating how mutational escape within a single oncogenic kinase shapes targeted leukemia therapy.

sunitinib-resistant FLT3 mutants
FLT3 is a receptor tyrosine kinase whose activating mutations drive a large fraction of acute myeloid leukaemia, and inhibiting it is a mainstay of targeted therapy in that disease. Sunitinib, a type II inhibitor that binds the kinase only in its inactive conformation, blocks many FLT3 variants but not all: certain point mutations in the kinase domain, particularly at the activation loop and gatekeeper positions, stabilise the active conformation or occlude the drug pocket so that sunitinib-resistant FLT3 mutants continue to signal. The consequence is sustained ligand-independent autophosphorylation and downstream STAT5, RAS-MAPK and PI3K-AKT output, driving proliferation and blocking myeloid differentiation despite treatment. Such variants explain relapse on kinase inhibitor therapy and motivate the use of later-generation or type I inhibitors that engage the receptor differently.
```

## An internal-node message

*The two child names below are illustrative: this build is unnamed, so no real child name
exists yet. Everything else is real.*

```
Name this cluster. Its child clusters (already named) and its direct pathways:

Child clusters:

Beta cell insulin secretion and glucose sensing
Islet endocrine cell differentiation

Direct pathways:

negative regulation of type B pancreatic cell apoptotic process
Insulin-secreting beta cells are few in number and largely irreplaceable in adults, so their survival sets the limit on how much insulin the pancreas can deliver. Suppressing beta cell apoptosis preserves islet mass, and when this protection fails the resulting cell loss produces diabetes: falling secretory capacity, hyperglycaemia, and in severe cases insulin dependence. The genes involved act at several levels. Lineage transcription factors such as PDX1 and NEUROD1 maintain the differentiated, stress-tolerant beta cell state, and their loss compromises both identity and viability. WFS1 supports endoplasmic reticulum homeostasis in cells with an extreme secretory protein load, and its mutation causes Wolfram syndrome with early beta cell death. A calpain inhibitor and a splicing factor contribute further, while TCF7L2 links this survival programme to the strongest common genetic risk for type 2 diabetes.

type B pancreatic cell proliferation
Insulin-secreting beta cells of the pancreatic islets are normally quiescent, but their number can expand during growth, pregnancy, obesity and insulin resistance; this proliferative capacity sets how much insulin a person can secrete and its loss underlies the beta cell deficit of both type 1 and type 2 diabetes. The genes here act as drivers and brakes on beta cell replication rather than on insulin release itself: hepatokine and secreted growth-regulatory signals, IGF-binding proteins that sequester and modulate IGF availability, a hepatocyte-derived protease inhibitor that stimulates beta cell mitosis, and apoptotic and stress regulators such as BAD that couple nutrient sensing and survival to cycle entry. Nuclear receptors of the NR4A family and a circadian factor place proliferative decisions under transcriptional and daily metabolic control, while NKX6-1 maintains the mature beta cell identity that expanding cells must retain.

Regulation of gene expression in endocrine-committed (NEUROG3+) progenitor cells
Pancreatic endocrine cells arise from a transient population of progenitors that switch on neurogenin 3, and this transcriptional programme is what commits those cells away from duct and acinar fates toward the hormone-producing islet lineages. Without it no beta, alpha, delta or PP cells form; loss-of-function mutations in humans cause congenital malabsorptive diarrhoea with permanent neonatal diabetes, and the same programme is the target of efforts to make beta cells from stem cells. NEUROG3 acts as a short-lived pioneer factor that directly induces a second tier of regulators, including PAX4, NEUROD1, NKX2-2 and the zinc-finger factor INSM1, which together consolidate endocrine identity, drive exit from the cell cycle, and bias progenitors toward particular hormone subtypes. The pathway illustrates how a brief pulse of one factor is converted into a stable differentiated state.
```

## A collision re-ask

*The same system prompt and the same data, with one line appended. There is no second prompt.*

```
Name this cluster. Its pathways:

KW2449-resistant FLT3 mutants
Activating mutations in the FLT3 receptor tyrosine kinase drive proliferation and survival of myeloid blasts and are among the most common lesions in acute myeloid leukaemia, making the receptor a prime drug target. KW-2449 is a type I inhibitor that binds the active kinase conformation and blocks signalling through several mutant FLT3 alleles, including internal tandem duplications of the juxtamembrane region, but certain substitutions in the kinase domain and activation loop alter the ATP pocket so that the drug no longer engages productively. Cells carrying these KW-2449-resistant variants retain constitutive, ligand-independent FLT3 signalling to STAT5, RAS-MAPK and PI3K-AKT despite treatment, and such alleles account for relapse after targeted therapy. Cataloguing them matters for choosing between type I and type II inhibitors and for interpreting resistance mutations that emerge under selection.

gilteritinib-resistant FLT3 mutants
Activating mutations in the receptor tyrosine kinase FLT3 drive a large fraction of acute myeloid leukaemia, and gilteritinib is a type I inhibitor used to shut that signalling down. Clinical benefit is often lost when the receptor acquires secondary changes that no longer permit effective drug binding, and this grouping describes gilteritinib-resistant FLT3 mutants, which restore ligand-independent kinase activity and downstream proliferative and survival signalling through STAT5, RAS-MAPK and PI3K routes despite continued treatment. Because type I inhibitors engage the active kinase conformation, substitutions in the activation loop and kinase domain, as well as alternative resistance alleles arising on the background of internal tandem duplications, are the usual cause of relapse. Understanding which variants confer resistance guides the choice between inhibitor classes and explains the limited durability of single-agent FLT3-targeted therapy in myeloid leukaemia.

sorafenib-resistant FLT3 mutants
FLT3 is a receptor tyrosine kinase that drives proliferation and survival of hematopoietic progenitors, and activating mutations in it — most often internal tandem duplications in the juxtamembrane region — are among the most common lesions in acute myeloid leukemia, where they predict relapse. Sorafenib, a type II inhibitor that binds the inactive kinase conformation, suppresses such mutants and can produce responses in FLT3-mutant disease, but treatment selects for sorafenib-resistant FLT3 variants. Substitutions in the activation loop and at the gatekeeper position stabilize the active conformation or occlude the drug pocket, so the receptor continues to autophosphorylate and signal through STAT5, RAS–MAPK and PI3K–AKT despite drug exposure. This resistance underlies loss of response in the clinic and motivates type I and next-generation FLT3 inhibitors, illustrating how mutational escape within a single oncogenic kinase shapes targeted leukemia therapy.

sunitinib-resistant FLT3 mutants
FLT3 is a receptor tyrosine kinase whose activating mutations drive a large fraction of acute myeloid leukaemia, and inhibiting it is a mainstay of targeted therapy in that disease. Sunitinib, a type II inhibitor that binds the kinase only in its inactive conformation, blocks many FLT3 variants but not all: certain point mutations in the kinase domain, particularly at the activation loop and gatekeeper positions, stabilise the active conformation or occlude the drug pocket so that sunitinib-resistant FLT3 mutants continue to signal. The consequence is sustained ligand-independent autophosphorylation and downstream STAT5, RAS-MAPK and PI3K-AKT output, driving proliferation and blocking myeloid differentiation despite treatment. Such variants explain relapse on kinase inhibitor therapy and motivate the use of later-generation or type I inhibitors that engage the receptor differently.

The name 'FLT3 inhibitor resistance mutations' is already used by another cluster; give a different name that is still true of every member and no broader.
```

