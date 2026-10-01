# name-v6 stage 1: may a parent take its child's name?

*29 Sep 2026. `name-v6` changes ONE sentence of the system prompt — a cluster may take one of its children's names when that is the tightest true name, and the child is then renamed. Digest `f3d1f074929df02a` → `19074b71ad0d429e`; nothing else in the prompt moved.*

Run on the 18 residual-narrowing level-1 nodes with `--only-nodes`; every other node kept its name-v5 name.

## The headline: the new permission fired on nothing

**0 of 18 parents took a child's name.** The rule is implemented and was exercised — `parent_took_child` ran, the child re-ask path was live — and no parent chose to reuse a child's name. Permitting reuse does not make the model prefer it: it still writes a distinct name, and on these 18 that name is still often narrower than a child.

16 of 18 names changed anyway, and **5 of 18 now cover every child by my reading**.

**Why it could not have worked on most of these.** In at least nine of the 18 the child is genuinely BROADER than the parent — `Membrane trafficking machinery` under `Synaptic vesicle trafficking`, `Sensory transduction across modalities` under `Mechanotransduction`, `Intracellular vesicle transport` under `Vesicle trafficking to lysosomes`. That is not a parent repeating its child; it is the DAG placing a broader cluster beneath a narrower one. No prompt can name its way out of it, and no rename of the child would help, because the child's name is correct for the child.

| node | old parent name | new parent name | took child's name? | child | covers child (my reading) |
|---|---|---|---|---|---|
| `n0618` | Vitamin D metabolism and receptor signalling | Vitamin D metabolism and receptor signalling | no | Bile acid and sterol homeostasis | **no** |
| `n0474` | Keratinocyte-driven epidermal wound re-epithelialisation | Keratinocyte spreading and migration in wound re-epithelialization | no | Regulation of cell-matrix adhesion turnover | **no** |
| `n0716` | Male reproductive endocrine differentiation | Male reproductive development and androgen signaling | no | Gonadotropin control of ovarian and gonadal function | **no** |
| `n0244` | Synaptic vesicle recycling and endocytosis | Synaptic vesicle trafficking | no | Membrane trafficking machinery | **no** |
| `n0592` | Mechanical stimulus sensing | Mechanotransduction | no | Sensory transduction across modalities | **no** |
| `n0197` | Regulation of MAPK/JNK cascades | Regulation of MAPK/JNK cascades | no | Regulation of protein kinase activity | **yes** |
| `n0405` | Purine nucleoside and nucleotide salvage | Purine nucleotide salvage and catabolism | no | Nucleotide pool sanitation and catabolism · Deoxyribonucleotide synthesis and catabolism | **yes** |
| `n0302` | Negative regulation of myogenesis and regeneration | Negative regulation of muscle development and regeneration | no | Muscle cell proliferation and differentiation | **yes** |
| `n0218` | Insulin-family receptor tyrosine kinase signaling | Insulin receptor family signaling | no | PI3K/AKT activation downstream of growth factor receptors | **no** |
| `n0262` | Vacuole and lysosome trafficking | Vacuolar and lysosomal protein trafficking | no | Intracellular vesicle transport | **yes** |
| `n0732` | Vesicular trafficking to the vacuole and lysosome | Vesicle trafficking to lysosomes | no | Intracellular vesicle transport | **yes** |
| `n0706` | Muscle fibre membrane and size homeostasis | Muscle fibre membrane and size homeostasis | no | Sarcomere assembly and contraction | **no** |
| `n0495` | Galactose and pentose metabolism disorders | Galactose and pentose metabolism | no | Amino sugar and carbohydrate catabolism | **no** |
| `n0181` | Platelet activation and adhesion regulation | Platelet activation and adhesion control | no | Hemostasis and thrombin/PAR signalling | **no** |
| `n0236` | Pancreatic endocrine cell development and beta cell homeostasis | Pancreatic endocrine lineage development and beta cell mass | no | Endoderm-derived epithelial identity and maturation | **no** |
| `n0473` | Vitamin D and fat-soluble vitamin metabolism | Vitamin D and steroid hormone metabolism | no | Sex steroid and adrenocortical hormone synthesis | **no** |
| `n0125` | ATG8-dependent membrane sequestration and endosomal sorting | Lysosomal degradation and ubiquitin-dependent sorting | no | Endomembrane trafficking and turnover | **no** |
| `n0496` | Host-pathogen metal ion competition | Host-pathogen metal ion homeostasis | no | Antimicrobial peptide-mediated humoral defence | **no** |

No child was re-asked, so there is no child old/new name to report and **no `same_theme` row was written**. Multi-parent children not re-run: none, because no child was renamed.

## Cost, and an overrun

Quoted **$0.32**, approved to **$0.75**, **billed $0.81.** The overrun is mine: the invented-word pass walked every node in each level rather than the 18 in scope, and under a new prompt version every `:invented:` cache key is a miss, so 65 out-of-scope nodes were re-asked. The gate checks the estimate, not the running total, so nothing stopped it. The pass is now restricted to the nodes a run actually names.

Two other defects surfaced and are fixed. Adding the `same_theme` column made `merge_tsv` discard every existing row — **`theme_names.tsv` was wiped to 0 rows** and restored from a backup taken immediately before the run; a column added at the end now pads instead. And `--only-nodes` read reusable names under the NEW version, found none, and issued no requests at all on the first attempt.

