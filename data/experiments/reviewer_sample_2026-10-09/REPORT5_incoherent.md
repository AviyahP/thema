# The 44 incoherent clusters in thema_L_repair (reviewer analysis, 2026-10-09)

Source: all_verdicts.json (every one of the 8,793 themes judged once; samples 1-3 + census + round-1 big check). Profile per cluster: incoherent_analysis.json. Read-only analysis; nothing in the build changed.

Verdict totals: coherent 7,749, umbrella 811, core+misfits 132, mixture 57, incoherent 44.

## 1. 44 clusters, but only about 11 distinct problems + the 5 giant roots
5 are giant roots (2,138-2,614 members; already known). The other 39 (3-28 members) collapse into 12 families when nested parent/child links between incoherent clusters are followed:
- 1 family of 22 nested clusters (n05867, 28 members, down to n00717 / n00908 / n02265, 7 members): unannotated "housekeeping" blood modules.
- 1 family of 5 (n07386 -> n08787 -> n02521 -> n00421; n02238): BTM M41.x sub-modules + M98.1 + hominoid segmental-duplication genes (TBC1D3, NPIP, NOTCH2NL).
- 2 families of 2: n08490 -> n03087; n08627 -> n03413.
- 8 singletons: n00735, n03375, n04488, n06294, n04339, n08713, n04626, n07120. n04626 and n07120 are not linked as parent/child but share 17 of their 21 members, so in content there are 11 distinct problems.

## 2. What the families are made of: inputs with no specific biology
A. Unannotated blood co-expression modules ("TBA" BTMs). The 22-cluster family and n08713. Recurring members (in 9-15 of the 39): the self-described heterogeneous ones (M153, M72.0, M72.2, M218, M32.5, M211, M221) AND unnamed BTMs the declared rule did not catch, whose descriptions are vague: M137, M174, M72.1, M242, M161, M185, M243, M248 ("in common little more than a shared place in interaction screens"), M32.7, M128, M32.6; plus motif-defined BTMs (M232 TF motif, M32.3 KLF12 targets, M138 ubiquitination).
B. Sets defined by a regulatory signature, not a process: TF-motif and TF-target modules (PAX3 motif/targets, SREBF1 motif, unknown motif, GR targets, SMAD2/3) and Reactome "regulation of transcription of gene X" sets (CDH1, CDH11, PTEN, PD-L1, TGFBR3, RUNX3 targets) with generic GO negative-regulation-of-transcription terms: n04626/n07120, n08490/n03087, n03375. Note: Reactome itself files many of these together under Generic Transcription Pathway; the judges' rubric is stricter than Reactome here.
C. Hominoid segmental-duplication gene families (TBC1D3 paralogs in M241, NPIP in M247, NOTCH2NL) with vague GO terms (adult lifespan, growth rate, bone marrow development, replicative senescence): n02238, n06294, n08627/n03413. A real genomic link, not a functional one.
D. Vague or orphan GO terms: n04339 (response to drug / ethanol / ether / anesthetic / antibiotic, hypoxia, oxidative stress, agmatine); n04488 (magnesium, creatine, inositol transport, protein homo/hetero-tetramerization).
E. Borderline, possibly too strict: n00735 (3 members: regulation of PI biosynthesis, LPA receptors, VEGFR2 proliferation): all are PLC / phosphoinositide-coupled receptor signalling; arguably an umbrella.

Likely mechanism (not proven): these inputs have no specific biology of their own, so their descriptions share generic vocabulary (housekeeping, chromatin, "regulation of transcription", "response to") and end up as each other's nearest neighbours. THEMA groups the leftovers together rather than mixing them into good themes.

## 3. Resampling does not catch them
Median support: coherent 0.15, umbrella 0.06, core+misfits 0.055, mixture 0.045, incoherent 0.08. Some incoherent clusters are very stable (n00421 0.955, n00717 0.90, n00735 0.895, n00908 0.85), because the same leftovers always fall together. Support measures reproducibility, not meaning, and cannot be used to filter them (umbrellas have lower support than incoherent clusters).
Gene overlap does not separate them either: mean pairwise member gene Jaccard in incoherent clusters (0.01-0.04) is in the same range as coherent clusters of the same size (0.04 at 11-20, 0.058 at 6-10); exception n00421 (0.24, overlapping M41.x sub-modules).

## 4. Effect of the 17-BTM drop
It dissolves n00421 (5 -> 1) and thins the others, but does NOT remove the main family: n05867 keeps 21 of 28 members (11 still unnamed BTMs), n04129 keeps 13 of 20 (10 unnamed). Families B, C (partly) and D are untouched (0 of the 17 in n04626, n07120, n04339, n04488).

## 5. Options (decision is Aviyah's)
1. Accept and label: treat these as an honest "low-information inputs" family; report 44 of 8,793 (0.5%) incoherent, 39 of them traceable to inputs without specific biology.
2. Broaden input QC with a second declared, description-level rule for unnamed BTMs (e.g. a blind judgement of each of the 83 TBA descriptions: "does it name one specific process?"), decided BEFORE looking at where they land. Do NOT select inputs by the cluster verdicts: that would use the evaluation to tune construction (double dipping) and inflate the plausibility numbers.
3. Do nothing to categories B-D: motif/target sets and vague GO terms are legitimate source gene sets; their grouping mirrors how Reactome/GO file them.
