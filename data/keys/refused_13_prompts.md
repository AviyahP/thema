# The 13 refused pathways still in the exercise — exact v4 requests

*Generated 2026-09-23. Every user block is byte-identical to the `content` the API received under `prompt_version = v4`, from the same `render_user_message()` the batch used.*

## Three pathways are excluded by the universe rule

`reactome:R-HSA-168305`, `reactome:R-HSA-9682708` and `reactome:R-HSA-9683439` have **no genes**.
The universe rule (`DECISIONS.md`, 23 Sep 2026) excludes every pathway with `n_genes = 0`, so they
are out of the universe entirely -- not "deliberately undescribed", and not candidates for
`unplaced.tsv`. No special case applies to them.

The 13 below all have genes and all remain in the universe.

## Where to put the answers

`data/keys/refused_13_answers.tsv`, tab-separated, header exactly `key	model	description`. One line per pathway, no newlines or tabs inside the text, no surrounding quotes. `model` is whatever produced THAT row — rows may differ. They are ingested as `prompt_version = v4-alt`, `status = superseded`; nothing is promoted without a separate decision. A subset is fine; I report what is missing.

## API parameters

| field | value |
|---|---|
| model | `claude-opus-5` |
| **system prompt** | **yes** — the next section, sent as a `system` array element with `cache_control: {type: ephemeral, ttl: 1h}` |
| **temperature** | **not set** — never included, so the API default applies |
| **max_tokens** | **8,000**, shared with thinking tokens |
| thinking | `{"type": "adaptive"}` |
| output_config.effort | `low` |
| output_config.format | structured output, schema below |

The reply is **not free text** — a JSON schema is enforced and the description is read from the `description` key. **Return the VALUE of `description`**: one paragraph, no JSON wrapper, no key name.

```json
{
  "type": "json_schema",
  "schema": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string"
      }
    },
    "required": [
      "description"
    ],
    "additionalProperties": false
  }
}
```

## System prompt

Identical for all 13; sent once per request.

````text
You write short functional descriptions of human biological pathways represented by gene
sets. Each description you write will be embedded and clustered with thousands of others,
so consistency of length and register matters as much as accuracy: every description must
read as though written by the same person on the same day.

You will be given a pathway's name, its curated description when one exists, and its full
list of member genes. You will NOT be told which database the pathway came from, and you
must not speculate about it.

WHAT TO WRITE

Write one paragraph of 90-150 words, targeting about 110. Do not write
a list, headings, or more than one paragraph.

Work the pathway's name into the description where it helps the reader, in whatever wording
and position serve the sentence. Its MEANING must survive -- a reader must be able to tell
which pathway this is -- but the exact phrasing is yours, and it need not come first. Do not
open with the name in quotation marks. If the name is a placeholder such as "TBA" and
carries no meaning, name the biology you infer from the genes instead. Do not mention that
the name was missing, and do not write the placeholder anywhere in the description.

Say in plain English what the pathway is and why it matters before any mechanism. A reader
who knows biology but not this pathway should understand from the first two sentences what
it does and what depends on it.

Describe the pathway's significance -- what it enables and what goes wrong without it: a
physiological function, a cell type it defines, a disease that follows its failure. Filler
adjectives are not significance; "critical", "essential", "plays a key role", "fundamental"
and "important" carry no information and make every description look alike.

Only then add mechanism, and only enough to make the purpose concrete. State the biological
purpose and context of the pathway, and which general cellular or physiological processes
it relates to. "Signal transduction" is not an answer; signal transduction toward what end
is.

Use your own knowledge of biology freely. Curated descriptions are often too terse to carry
thematic meaning, and adding that context is the point of this task. Where a curated
description exists it anchors the content and you must stay faithful to it, but you may and
should extend it. Where the genes tell you something the text does not -- a shared complex,
a compartment, a cell type, a regulatory relationship -- say so. Where there is no text at
all, derive the biology from the genes and say what they support. Do not pad with vague
possibility ("may be involved in various cellular processes") when you have something
definite to say; but where you are genuinely unsure, say the thing you are sure of instead
of guessing. Accuracy comes before confidence.

Do not list gene symbols exhaustively. Naming a few genes that carry the pathway's identity
is useful, especially when making a specific claim about one; transcribing the input is not.

PRECISION ON GENE-LEVEL CLAIMS

Naming a gene and saying what it does is the most useful thing you can write and the easiest
thing to get wrong. Before making such a claim, be sure of four things:

  - its molecular identity -- a demethylase is not a deacetylase, a protease inhibitor is not
    a protease, a GTPase-activating protein does not activate its target
  - the direction of effect -- activates or inhibits, imports or exports, adds or removes,
    raises or lowers
  - the substrate or partner -- which ion, which molecule, which receptor, which effectors
  - that the gene is actually in the list you were given

If you are not certain of all four, write the pathway-level biology instead. A correct
general statement is worth more than a specific one that is wrong: a wrong specific claim is
invisible to every check except a reader who already knows the answer.

Do not claim that expression or activity is restricted to a tissue or cell type unless every
gene in the list is consistent with that restriction. A single gene from another tissue
refutes the claim.

WHAT NOT TO WRITE

Never cite a specific database entry. Do not write ontology identifiers of any kind, and do
not name another pathway, term or gene set AS A DATABASE OBJECT -- not "the Reactome
pathway X", not "the GO term Y", not "this MSigDB set". Do not name the databases
themselves.

This prohibition is narrow and is about citation, not about relationships. Describing how
this biology relates to other biology, in ordinary language, is exactly what is wanted: "a
subtype of apoptosis", "part of cell cycle control", "downstream of interferon signalling",
"one arm of the unfolded protein response". Write those freely.

Do not describe the input. No "this gene set contains", no "the description provided
states", no meta-commentary about what you were given.

EXAMPLES

Input name: Mitochondrial iron-sulfur cluster assembly
Input description: Assembly of [2Fe-2S] and [4Fe-4S] clusters on a scaffold protein and
their transfer to recipient apoproteins.
Input genes: NFS1, ISCU, FXN, LYRM4, FDX2, FDXR, HSPA9, HSCB, GLRX5, ISCA1, ISCA2, IBA57,
NFU1

Output: Dozens of enzymes cannot function without an iron-sulfur cofactor, and mitochondrial
assembly of those clusters is where they are built and handed to the proteins that need
them. A cell without it loses respiratory capacity, cannot repair its own DNA properly, and
misreads its iron status as starvation while iron accumulates. The work happens on a
dedicated scaffold: a cysteine desulfurase supplies sulfur, a ferredoxin pair supplies
electrons, and a chaperone step releases the finished cluster to its recipient. Those
recipients are the workhorses of oxidative metabolism and genome maintenance -- respiratory
chain complexes, aconitase, lipoate synthase, several DNA repair helicases. Failure of
individual components causes progressive mitochondrial disease, which places this chemistry
upstream of cellular energy production rather than inside any one metabolic route.

Input name: TBA
Input description: (none)
Input genes: CD19, MS4A1, CD79A, CD79B, BLNK, BTK, PAX5, EBF1, VPREB1, IGLL1, CR2, FCRL1,
TNFRSF13C

Output: Bone marrow progenitors become mature B cells by assembling an antigen receptor and
then proving that it works. The programme underpins antibody-mediated immunity, and its
components are the markers by which B cells are identified in the clinic and the targets of
B cell depleting therapy. Surface and adaptor machinery transmits antigen binding into
proliferation and survival, while transcription factors commit a progenitor to the lineage
and hold it there. A surrogate receptor tests whether a functional antigen receptor has been
assembled before a cell is permitted to mature, making developmental checkpointing as much a
function of this biology as signalling is.

OUTPUT FORMAT

Return an object with a single key, "description", whose value is the paragraph.

````

---

## User messages — one per pathway


### `reactome:R-HSA-168799` — Neurotoxicity of clostridium toxins

````text
Input name: Neurotoxicity of clostridium toxins
Input description: Clostridial neurotoxins, when taken up by human neurons, block synaptic transmission by cleaving proteins required for the fusion of synaptic vesicles with the plasma membrane. They are remarkably efficient so that very small doses cause paralysis of an affected person (Lalli et al. 2003; Turton et al. 2002). All characterized clostridial neurotoxins are synthesized as products of chromosomal, plasmid or prophage-borne bacterial genes. The nascent toxin may be cleaved into light (LC) and heavy (HC) chain moieties that remain attached by noncovalent interactions and a disulfide bond (Turton et al. 2002). Strains of Clostridium botulinum produce seven serologically distinct toxins, BoNT/A, B, C, D, E, F, and G. An eighth toxin, BoNT/H has recently been identified (Barash & Arnon 2014) but its molecular properties have not yet been described. Human poisoning most commonly result from ingestion of toxin contaminated food. More rarely, it is due to wound infection or clostridial colonization of the gut of an infant whose own gut flora have not yet developed or of an older individual whose flora have been suppressed. While all seven characterized toxins can cleave human target proteins, three, BoNT/A, B, and E, are most commonly associated with human disease (Hatheway 1995; Sakaguchi 1982). BoNT/F is also able to cause human botulism. Once ingested, the botulinum toxin must be taken up from the gut lumen into the circulation, a process mediated by four accessory proteins. These proteins form a complex that mediates transcytosis of the toxin molecule across the gut epithelium, allowing its entry into the circulation. The accessory proteins produced by different C. botulinum strains differ in their affinities for polarized epithelia of different species (e.g., human versus canine), and may thus be a key factor in human susceptibility to the toxins of strains A, B, and E and resistance to the others (Simpson 2004). Clostridium tetani produces TeNT toxin. Human poisoning is the result of toxin secretion by bacteria growing in an infected wound and the toxin is released directly into the circulation. Circulating clostridial toxins are taken up by neurons at neuromuscular junctions. They bind to specific gangliosides (BoNT/C, TeNT) or to both gangliosides and synaptic vesicle proteins (BoNT/A, B, D G) exposed on the neuronal plasma membrane during vesicle exocytosis (Montal 2010). All seven characterized forms of BoNT are thought to be taken up into synaptic vesicles as these re-form at the neuromuscular junction. These vesicles remain close to the site of uptake and are rapidly re-loaded with neurotransmitter and acidified (Sudhoff 2004). TeNT, in contrast, is taken up into clathrin coated vesicles that reach the neuron cell body by retrograde transport and then possibly other neurons before undergoing acidification. Vesicle acidification causes a conformational change in the toxin, allowing its HC part to function as a channel through which its LC part is extruded into the neuronal cytosol. The HC - LC disulfide bond is cleaved and the cytosolic LC functions as a zinc metalloprotease to cleave specific bonds in proteins on the cytosolic faces of synaptic vesicles and plasma membranes that normally mediate exocytosis (Lalli et al. 2003; Montal 2010).
Input genes: SNAP25, STX1A, STX1B, SV2A, SV2B, SV2C, SYT1, SYT2, VAMP1, VAMP2
````

### `reactome:R-HSA-5250955` — Toxicity of botulinum toxin type D (botD)

````text
Input name: Toxicity of botulinum toxin type D (botD)
Input description: Botulinum toxin type D (botD) is only very rarely associated with human disease (Hatheway 1995) and a pathway by which it might enter the circulation from the human gut has not been described. Nevertheless, the toxin itself, a disulfide-bonded heavy chain (HC) - light chain (LC) heterodimer (“dichain”), is capable of binding to neurons by interactions with cell surface ganglioside (Kroken et al. 2011) and synaptic vesicle protein 2 (SV2) (Peng et al. 2011), the bound toxin can enter synaptic vesicles and release its LC moiety into the cytosol of targeted cells (Montal 2010), and the botD LC can cleave vesicle associated membrane proteins 1 and 2 (VAMP1 and 2) on the cytosolic face of the synaptic vesicle membrane (Schiavo et al. 1993; Yamasaki et al. 1994). These four events are annotated here.
Input genes: SV2A, SV2B, SV2C, VAMP1, VAMP2
````

### `reactome:R-HSA-5250958` — Toxicity of botulinum toxin type B (botB)

````text
Input name: Toxicity of botulinum toxin type B (botB)
Input description: Botulinum toxin type B (botB, also known as BoNT/B), a disulfide-bonded heavy chain (HC) - light chain (LC) heterodimer, enters the gut typically as a result of consuming contaminated food (Hatheway 1995), as a complex with nontoxic nonhemagglutinin protein (NTNHA, encoded by the C. botulinum ntnha gene) and multiple copies of three hemagglutinin proteins (HA, encoded by the C. botulinum ha17, ha34, and ha70 genes) (Amatsu et al. 2013). The complex protects the toxin from degradation in the gut and mediates its association with the gut epithelium and transcytosis to enter the circulation (Fujinaga et al. 2013). Circulating toxin molecules associate with gangliosides and synaptotagmin (SYT) proteins exposed by exocytosis at a synapse of a target neuron (Dong et al. 2003; Yowler & Schengrund 2004). Vesicle recycling brings the toxin into the neuron where the vesicle is acidified (Sudhoff 2004). The lowered pH induces a conformational change in the toxin: its HC forms a passage in the vesicle membrane through which its LC is extruded into the neuronal cytosol. Tthe HC - LC disulfide bond is reduced (Montal 2010). The LC then catalyzes the cleavage of vesicle-associated membrane protein 2 (VAMP2) on the cytosolic face of synaptic vesicle membranes (Foran et al. 1994; Schiavo et al. 1992), thereby inhibiting synaptic vesicle fusion with the plasma membrane and exocytosis.
Input genes: SYT1, SYT2, VAMP2
````

### `reactome:R-HSA-5250968` — Toxicity of botulinum toxin type A (botA)

````text
Input name: Toxicity of botulinum toxin type A (botA)
Input description: Botulinum toxin type A (botA, also known as BoNT/A), a disulfide bonded heavy chain (HC) - light chain (LC) heterodimer ("dichain"), enters the gut typically as a result of consuming contaminated food (Hatheway 1995), as a complex with nontoxic nonhemagglutinin protein (NTNHA, encoded by the C. botulinum ntnha gene) and multiple copies of three hemagglutinin proteins (HA, encoded by the C. botulinum ha17, ha34, and ha70 genes) (Lee et al. 2013). The complex protects the toxin from degradation in the gut and mediates its association with the gut epithelium and transcytosis to enter the circulation. Recent studies in vitro raise the possibility that the toxin may also directly disrupt the basolateral membrane of the gut epithelium (Fujinaga et al. 2013). Circulating toxin molecules associate with gangliosides and synaptic vesicle protein 2 (SV2) exposed by exocytosis at a synapse of a target neuron in the neuromuscular junction (Yowler & Schengrund 2004; Dong et al. 2006). Vesicle recycling brings the toxin into the neuron where the vesicle is acidified (Sudhoff 2004). The lowered pH induces a conformational change in the toxin: its HC forms a passage in the vesicle membrane through which its LC is extruded into the neuronal cytosol and released by reduction of the HC - LC disulfide bond (Montal 2010). The cytosolic LC then catalyzes the cleavage of synaptosomal associated protein 25 (SNAP25) on the cytosolic face of the neuronal plasma membrane (Binz et al. 1994; Schiavo et al. 1993), thereby inhibiting synaptic vesicle fusion with the plasma membrane and exocytosis.
Input genes: SNAP25, SV2A, SV2B, SV2C
````

### `reactome:R-HSA-5250971` — Toxicity of botulinum toxin type C (botC)

````text
Input name: Toxicity of botulinum toxin type C (botC)
Input description: Botulinum toxin type C (botC, also known as BoNT/C) is only very rarely associated with human disease (Hatheway 1995) and a pathway by which it might enter the circulation from the human gut has not been described. Nevertheless, the toxin itself, a disulfide-bonded heavy chain (HC) - light chain (LC) heterodimer (“dichain”), is capable of binding to neurons by interactions with cell surface gangliosides (Karalewitz et al. 2012), the bound toxin can enter synaptic vesicles and release its LC moiety into the cytosol of targeted cells (Montal 2010), and the botC LC can cleave synaptosomal associated protein 25 (SNAP25) and syntaxin 1 (STX1) on the cytosolic face of the neuronal plasma membrane (Foran et al. 1996). These four events are annotated here.
Input genes: SNAP25, STX1A, STX1B
````

### `reactome:R-HSA-5250981` — Toxicity of botulinum toxin type F (botF)

````text
Input name: Toxicity of botulinum toxin type F (botF)
Input description: Botulinum toxin type F (botF) is only very rarely associated with human disease (Hatheway 1995) and a pathway by which it might enter the circulation from the human gut has not been described. Nevertheless, the toxin itself, a disulfide-bonded heavy chain (HC) - light chain (LC) heterodimer ("dichain"), is capable of binding to neurons by interactions with cell-surface ganglioside and synaptic vesicle protein 2 (SV2) (Fu et al. 2009; Rummel et al. 2009), the bound toxin can enter synaptic vesicles and release its LC moiety into the cytosol of targeted cells (Montal 2010), and the botF LC can cleave vesicle-associated membrane proteins 1 and 2 (VAMP1 and 2) on the cytosolic face of the synaptic vesicle membrane (Yamasaki et al. 1994). These four events are annotated here.
Input genes: SV2A, SV2B, SV2C, VAMP1, VAMP2
````

### `reactome:R-HSA-5250989` — Toxicity of botulinum toxin type G (botG)

````text
Input name: Toxicity of botulinum toxin type G (botG)
Input description: Botulinum toxin type G (botG) is rarely if ever associated with human disease (Hatheway 1995) and a pathway by which it might enter the circulation from the human gut has not been described. Nevertheless, the toxin itself, a disulfide-bonded heavy chain (HC) - light chain (LC) heterodimer ("dichain"), is capable of binding to neurons by interactions with cell-surface ganglioside and syntagmin 1 (SYT1) (Peng et al. 2012; Willjes et al. 2013), the bound toxin can enter synaptic vesicles and release its LC moiety into the cytosol of targeted cells (Montal 2010), and the botG LC can cleave vesicle-associated membrane proteins 1 and 2 (VAMP1 and 2) on the cytosolic face of the synaptic vesicle membrane (Schiavo et al. 1994; Yamasaki et al. 1994). These four events are annotated here.
Input genes: SYT1, VAMP1, VAMP2
````

### `reactome:R-HSA-5250992` — Toxicity of botulinum toxin type E (botE)

````text
Input name: Toxicity of botulinum toxin type E (botE)
Input description: Botulinum toxin type E (botE, also known as BoNT/E), a disulfide-bonded heavy chain (HC) - light chain (LC) heterodimer (“dichain”), enters the gut typically as a result of consuming contaminated food (Hatheway 1995), as a complex with nontoxic nonhemagglutinin protein (NTNHA, encoded by the C. botulinum ntnha gene) (Benefield et al. 2013). The complex protects the toxin from degradation in the gut and mediates its association with the gut epithelium and transcytosis to enter the circulation (Fujinaga et al. 2013). Circulating toxin molecules associate with gangliosides and synaptic vesicle protein 2 (SV2) exposed by exocytosis at a synapse of a target neuron (Dong et al. 2008; Yowler & Schengrund 2004). Vesicle recycling brings the toxin into the neuron where the vesicle is acidified (Sudhoff 2004). The lowered pH induces a conformational change in the toxin: its HC forms a passage in the vesicle membrane through which its LC is extruded into the neuronal cytosol and released by reduction of the HC - LC disulfide bond (Montal 2010). The LC then catalyzes the cleavage of synaptosome-associated protein 25 (SNAP25) on the cytosolic face of the neuronal plasma membrane (Binz et al. 1994; Schiavo et al. 1993), thereby inhibiting synaptic vesicle fusion with the plasma membrane and exocytosis.
Input genes: SNAP25, SV2A, SV2B
````

### `reactome:R-HSA-9682706` — Replication of the SARS-CoV-1 genome

````text
Input name: Replication of the SARS-CoV-1 genome
Input description: The plus strand RNA genome of the human SARS coronavirus 1 (SARS-CoV-1) is replicated by the viral replication-transcription complex (RTC) composed of nonstructural proteins nsp3-nsp16, encoded by open reading frames ORF1a and ORF1b. Two RTC proteins, nsp8 and nsp12, possess 5'-3' RNA-dependent RNA polymerase activity. nsp12 is the main RNA polymerase, while nsp8 is thought to act as an RNA primase. nsp14 acts as a 3'-5' exonuclease, increasing the fidelity of the RTC. nsp14 also has the RNA capping activity and, in concert with nsp16, it caps viral plus strand and minus strand genomic and subgenomic RNAs, which confers stability to viral RNAs by enabling them to escape interferon-mediated innate immune responses of the host. nsp13 is an RNA helicase which is thought to melt secondary structures in the genomic RNA during replication and transcription. The plus strand genomic RNA is first used to synthesize the minus strand genomic RNA complement, which is subsequently used as a template for synthesis of plus strand viral RNA genomes that are packaged into mature virions. For review, please refer to Yang and Leibowitz 2015, Snijder et al. 2016, Fung and Liu 2019.
Input genes: DDX5, RB1, VHL, ZCRB1
````

### `reactome:R-HSA-9683610` — Maturation of nucleoprotein

````text
Input name: Maturation of nucleoprotein
Input description: Nucleoprotein, the most abundant viral protein expressed during infection, is found in the cytosol and plasma membrane. After phosphorylation and sumoylation it trimerizes and is moved to the Golgi, the virion budding site (Li et al, 2005; Surjit et al, 2005).
Input genes: GSK3A, GSK3B, PARP10, PARP14, PARP16, PARP4, PARP6, PARP8, PARP9, SUMO1, UBE2I
````

### `reactome:R-HSA-9683673` — Maturation of protein 3a

````text
Input name: Maturation of protein 3a
Input description: Protein 3a is associated with protein M and is found in the virion, although its function in the structure seems non-essential. 3a is O-glycosylated and forms a homotetramer with porin function (Oostra et al, 2006; Lu et al, 2006).
Input genes: GALNT1, ST3GAL1, ST3GAL2, ST3GAL3, ST3GAL4, ST6GAL1, ST6GALNAC2, ST6GALNAC3, ST6GALNAC4
````

### `reactome:R-HSA-9683686` — Maturation of spike protein

````text
Input name: Maturation of spike protein
Input description: Spike protein of SARS-Cov is subject to N-glycosylation and palmitoylation. The chaperone calnexin exclusively helps with protein folding. The end product is a homotrimer (Nal et al, 2005).
Input genes: CANX, GANAB, MGAT1, MOGS, PRKCSH
````

### `reactome:R-HSA-9692913` — SARS-CoV-1-mediated effects on programmed cell death

````text
Input name: SARS-CoV-1-mediated effects on programmed cell death
Input description: Programmed cell death (PCD) pathways, including pyroptosis, apoptosis, and necroptosis, are induced in infected host cells as an integral part of host defense to restrict microbial infections and regulate inflammatory responses (reviewed in Jorgensen I et al. 2017; Galluzzi L et al. 2018). Apoptosis is a noninflammatory form of cell death driven by the initiator caspase‑mediated cleavage of executioner caspase‑3 and ‑7. It facilitates degradation of the cellular contents but these are not released to the extracellular space. Necroptosis and pyroptosis are highly inflammatory forms of cell death that lead to cell lysis and release of pro‑inflammatory cytokines such as interleukin (IL)‑1β, tumour necrosis factor alpha (TNF‑α), IL6, IL18 and cellular contents, which can cause severe inflammation (reviewed in Jorgensen I et al. 2017; Galluzzi L et al. 2018; Pasparakis M & Vandenabeele P 2015). Gasdermins (GSDMs) exert pore‑forming activity in inflammasome‑dependent pyroptosis, while the mixed lineage kinase domain‑like (MLKL) protein functions as the executioner during necroptosis (Shi J et AL. 2015; Upton JW et al. 2017). Inflammation is a fundamental protective mechanism in elimination of microorganisms, and is normally tightly regulated by certain mediators, in particular IL10, to promote resolution of inflammation (reviewed in Sugimoto MA et al. 2016). Microbial pathogens are able to trigger and/or modulate host PCD and inflammatory response through multiple mechanisms. This Reactome module describes the roles of severe acute respiratory syndrome‑associated coronavirus type 1 (SARS‑CoV‑1) 3a, E, and 7a proteins in the induction of host cell death pathways. SARS‑CoV‑1 open reading frame‑3a (3a) binds host receptor interacting serine/threonine protein kinase 3 (RIPK3), facilitating RIPK3 oligomerization and the ion channel functionality of viral 3a, inducing inflammatory cell death and release of cellular contents (Yue Y et al. 2018). Enhanced production and release of proinflammatory cytokines leads to the cytokine storm that is considered to play a major role in SARS‑CoV type 1and 2 infections (reviewed in Channappanavar R & Perlman S 2017; Yang L et al. 2020). The module also describes induction of apoptosis by SARS‑CoV‑1 E and 7a proteins through their interaction with anti‑apoptotic BCL2L1 (Yang Y et al. 2005; Tan YX et al. 2007). Low levels of BCL2L1 may lead to enhanced function of pro‑apoptotic molecules, contributing to the depletion of T lymphocytes by apoptosis (Yang Y et al. 2005). This may lead to the lymphopenia observed in SARS patients, particularly in severe cases (Diao B et al. 2020; Chen Z & Wherry EJ 2020).
Input genes: BCL2L1, RIPK1, RIPK3
````
