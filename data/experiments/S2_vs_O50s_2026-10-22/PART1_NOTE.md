# Prompt 55 PART 1: reading inputs where S2 and O50s differ

Written as soon as PART 1 finished, as the prompt asks. **Nothing is judged here.** Shares, missing
counts, build labels, node ids and sizes-by-build are only in
`KEY_DO_NOT_SHARE_S2_vs_O50s.json`, written once and not read again by this session.

Seed 20261022 throughout. Builds: frozen O50s (5,658 themes, 261 roots) and S2
(5,646 themes, 270 roots).

| input | what | items | batches | paths |
|---|---|---:|---:|---|
| **R** | roots with no root of the other build at J >= 0.9, pooled and shuffled | **207** | 5 | `read_roots/R_b01.md` ... `R_b05.md` |
| **T** | themes unique to one build (best J < 0.9 to ANY theme of the other), bands 12-24 to 100-199 | **294** | 7 | `read_themes/T_b01.md` ... `T_b07.md` |
| **I** | the C6 intruder test over the same T themes | **122** | 4 | `intruder/I_b01.md` ... `I_b04.md` |
| **S** | the small-root test over every S2 root of 50 or fewer | **174** | 10 | `small_inputs/S_b01.md` ... `S_b10.md` |

## R: the roots that differ

**108 of S2's 270 roots have no O50s ROOT at J >= 0.9, and
99 of O50s's 261 roots have no S2 root at J >= 0.9.** Both are pooled
and shuffled into 207 items with no build label, so the reading cannot tell which build a
root came from. Note this is root-to-root by construction, as the prompt specifies: a root of one
build may well match a non-root theme of the other.

## T: short bands, stated

Two of the eight band-build cells had fewer than 40 unique themes available and were taken whole:

* S2 100-199: 24 available, all taken
* O50s 100-199: 30 available, all taken

The other six cells supplied the full 40.

## I: 172 of the 294 T themes could not get an intruder item

The C6 recipe needs at least four **maximal strict subsets** of the target among themes of 5 to 150
pathways. 172 of the T themes have fewer than four, which is expected for the
smaller bands -- a 12-pathway theme rarely contains four distinct sub-themes of 5 or more. That is
a property of the recipe, not of either build, and it falls on both builds alike. The surviving
122 items carry five candidate units plus one intruder, shuffled and lettered, with
batches taken by stride exactly as the 17 Oct run did.

## Mechanical checks on the blind inputs

* every item id appears exactly once as a header, and every other line is `- name [source]`
* **no node id and no build label appears in any batch** -- the only `S2` substrings are gene names
  (`NPAS2`, `PAPSS2`, `TRPS2`, `NEP/NS2`), and the string `O50s` appears nowhere
* S: 174 items, each with exactly 3 container headers labelled P, Q, R
* I: 122 items, 710 unit headers, so every item has at most six units
* no root, theme or item is split across batches
