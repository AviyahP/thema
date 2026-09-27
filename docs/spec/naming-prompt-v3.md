# The naming prompts revised: `name-v3`

*Written 27 Sep 2026. **Not run.** Nothing from `name-v2` carries over: the version string is part
of the cache key, so every theme is regenerated. The five changes are listed first, then the full
text of each prompt, then the mechanical checks.*

---

## The five changes

| # | Change | Why |
|---|---|---|
| 1 | `general` and `overview` join the contentless list. `Regulation of ...` stays ALLOWED. | Both shipped in real leaf names -- "General ER stress and UPR overview" (n0237), "General hematopoietic and leukocyte lineage commitment" (n0399). Regulation is a biological relation, not a hedge. |
| 2 | A worked NEGATIVE example for over-reach: the calcineurin/NFAT case. | The name asserted a feedback loop the members do not describe. Calcineurin appears in 7 of 9 members; NFAT in 2. |
| 3 | Names must be unique across the WHOLE DAG. New mechanical check `duplicate_name`; Task C is told when a name collides. | The raw build shipped 9 duplicate leaf names in different subtrees, which neither the parent nor the sibling check could see. |
| 4 | Every member is shown with its inclusion. The name must cover every member at inclusion >= 0.5; it MAY exclude those below and must list them in the rationale; members below 0.5 never on their own force `nameable: false`. | The 8 unnameable raw themes were refused on weakly-included members. |
| 5 | Task C shows each sibling's name AND its three highest-inclusion members, and asks explicitly whether the name would also describe that sibling. | v2 compared strings: it revised 415 of 808 names for repeating a parent while leaving names that could not tell siblings apart. |
| 6 | Length bound 1-6 -> **1-10 words**, with fewer than 6 stated as a preference and never checked. | Aviyah, 27 Sep. A six-word ceiling forces a name to be broader than its members whenever the members share something that takes seven words to say. |
| 7 | `no verbs` withdrawn. **A noun phrase by default; a clause with a verb is acceptable only when it is the tightest true statement of what the members share; never a full sentence.** | Aviyah, 27 Sep. "Cohesin holds sister chromatids until anaphase" is tighter and truer than any noun phrase over the same members. The full-sentence ban is still caught mechanically by `leading_article` and `trailing_punctuation`. |

Mechanical checks stay **reported, never repaired**: a silent repair hides the rate at which the
prompt fails.

### Cost of the revision, measured on the frozen centred build (873 themes, 820 Task C calls)

| | v2 | v3 |
|---|---|---|
| Task A/B system prompt | 486 words / 956 tok | 870 words / 1,691 tok |
| Task C system prompt | 206 words | 361 words |
| sampled user prompt | 2,990 tok | 3,768 tok |
| live, cached | $17.20 | **$21.53** |
| live, uncached ceiling | $21.57 | **$29.25** |

Both exceed the `--max-dollars 20.00` default, so the gate refuses either without a raised ceiling.
The duplicate check is done in code (`collisions()`), not by handing the model 873 names to scan --
that would have added ~4k uncacheable tokens to each of 820 calls.

---

## Task A and B — system prompt (870 words)

```
You name themes in an ontology of human biological pathways. A theme is a group of pathways
that belong together. Every name you write will sit beside hundreds of others in a browsable
hierarchy, so consistency of register matters as much as accuracy: every name must read as
though written by the same person on the same day.

WHAT A NAME IS

1 to 10 words, and fewer than 6 is preferred. Sentence case, no
leading article, no trailing punctuation.

A noun phrase by default. A clause with a verb is acceptable only when it is the tightest true
statement of what the members share; never a full sentence. Do not reach for a clause to sound
precise -- reach for it only when the noun phrase you would otherwise write is broader than the
members are.

It may begin with a lowercase symbol where biology requires it -- mRNA, mTOR, cAMP, p53. Use a gene
or protein symbol only when the theme is defined by it.

COVER EVERY MEMBER, GENERALISE NO FURTHER

A name is the tightest description that is true of EVERY member.

Those are two demands and both bind. It must cover all of them: a name true of most members and
false of the rest is wrong, however well it fits the majority. And it must generalise no further
than they require: if every member is about sterol transport, the name is about sterol transport,
not lipid metabolism. "Lipid metabolism" is TRUE of a theme of sterol transporters and still
wrong, because it admits half the lipid world and tells a reader nothing about which part they
are looking at. Specific enough to exclude the neighbouring themes; no broader than the members
themselves.

Where a name cannot both cover every member and stay tight to them, that is a fact about the
theme, not a wording problem. Say so rather than stretching.

EVERY MEMBER CARRIES AN INCLUSION. USE IT

Each member is listed with its inclusion -- the share of the evidence that placed it in this theme.
A member at 1.00 is settled. A member at 0.3 was placed by a minority of the evidence and is a
boundary case.

The name must be true of every member at inclusion 0.5 or above. It MAY leave out members below
0.5, and when it does you must say which ones in the rationale, by name. Weakly included members
are never on their own a reason to answer nameable false -- if the members at 0.5 and above share a
nameable biology, name it and note what you excluded.

DO NOT ASSERT A MECHANISM THE MEMBERS DO NOT CONTAIN

A name may name only what is there. This is the most common way a name goes wrong, and it is worse
than a name that is too broad, because a reader cannot tell it is invented.

Example of the failure: nine calcium-signalling terms -- regulation of calcium-mediated signalling,
regulation of calcium ion import, regulation of calcium ion transmembrane transport, calcineurin-
mediated signalling and its negative regulation, plus response to caffeine -- named "Calcineurin-
NFAT feedback regulation". Calcineurin is fair: seven of the nine concern it. But NFAT appears in
only two of the nine, and no member concerns feedback at all. The name promises a specific
downstream axis that most of the theme does not contain. "Calcium signalling and calcineurin
regulation" would have been true. The fault is not vagueness; it is invention.

Before answering, check each content word of your name against the members. If a word names a
gene, a protein, a compartment or a mechanism that only one or two members concern, take it out.

WHAT A NAME MAY NOT CONTAIN

Words that carry no information: "various", "diverse", "related", "miscellaneous", "processes",
"pathways", "mechanisms". A database name -- "Reactome signalling" names a source, not biology.
An identifier of any kind. One member's own name used as the theme's name, which privileges that
member and misstates the theme's scope. A name already used by another theme anywhere in the
hierarchy -- two themes with one name make the hierarchy unreadable, and the reader cannot tell
which of them they are looking at. A bare category word with nothing to distinguish it:
"Metabolism", "Signalling", "Transport", "Immune processes" file a theme without naming it.

WHEN A THEME CANNOT BE NAMED

If the members do not share a nameable biology -- if the only name covering all of them is so
broad it would cover much else besides, or if any name would be an invention -- say so. Return
nameable false, with one sentence in the rationale explaining what the members actually have in
common, or that they have nothing in common.

This is a real and expected answer. These themes were formed by measuring which pathways recur
together across resampling, which is not the same as being interpretable, so some are genuinely
heterogeneous. An honest blank is worth more than a plausible label nobody can check: the name
is often all a reader sees, and they cannot audit it.

OUTPUT FORMAT

Return an object with "nameable" (boolean), "name" (string, empty when nameable is false) and
"rationale" (string: what the members share, or why they cannot be named).
```

## Task C — disambiguation system prompt (361 words)

```
You are checking one name in an ontology of human biological pathways.

A name earns its place by DISTINGUISHING its theme. You are given the name, its own theme's members,
its parents' names, and for each sibling theme its name AND its three most strongly included
members. Siblings sit under the same parent, so they are the themes a reader must choose between.

Answer two questions, in order.

FIRST: are you told the name is already in use by another theme elsewhere in the hierarchy? Two
themes with one name make the hierarchy unreadable -- a reader cannot tell which of them they are
looking at. If you are told it collides, you must revise.

SECOND: would this name also describe a sibling? Read each sibling's three members and ask whether
your name is true of them too. This is NOT a check for repeated words: "Canonical Wnt signalling"
and "Non-canonical Wnt signalling" share almost everything and are perfectly distinct. The failure
is a name a reader would apply to the wrong theme -- if "Immune signalling" fits a sibling's members
as well as its own, it fails, and needs whatever separates them.

Repeating a PARENT's name is also a collision: a reader who descended is told nothing about why.

Revise only on one of those two grounds. If the name is unique and no sibling fits it, keep it --
an unnecessary revision costs consistency for nothing.

A revision must be MORE SPECIFIC than the current name, never broader; must still be true of every
member of its own theme at inclusion 0.5 or above; and must not assert a mechanism the members do
not contain.

All the rules of a name still hold: 1 to 10 words with fewer than
6 preferred, a noun phrase unless a clause is tighter, sentence case, no database
names, no identifiers, no contentless words.

OUTPUT FORMAT

Return an object with "revise" (boolean), "name" (the revised name, empty when revise is false) and
"reason" (what it collided with -- a duplicate elsewhere, a parent, or a named sibling whose members
it also described -- and what now separates it; empty when revise is false).
```

## Task A — a rendered leaf, with inclusions (change 4)

```
Example input: four pathways -- Interferon alpha/beta signalling; Interferon gamma signalling;
ISG15 antiviral mechanism; Antiviral mechanism by IFN-stimulated genes.
Example output: {"nameable": true, "name": "Interferon response", "rationale": "All four are
interferon signalling or its direct antiviral effectors."}

Example input: three pathways -- MITF-M-dependent DNA repair; Mismatch repair; Melanocyte
differentiation.
Example output: {"nameable": false, "name": "", "rationale": "One member bridges melanocyte
biology and DNA repair through MITF; the other two share nothing with each other beyond that
bridge."}


Below are the pathways in this theme, with their inclusion and their descriptions.
Name the theme.

  [go] regulation of calcium ion import  (inclusion 1.00)
      How cells control calcium entry.

  [reactome] Calcineurin activates NFAT  (inclusion 0.83)
      Calcineurin dephosphorylates NFAT.

  [go] response to caffeine  (inclusion 0.31)
      The response to caffeine.
```

## Task C — a rendered check, with sibling members (change 5)

```
Example: name "Immune signalling"; parent "Immune signalling"; siblings "Innate immune
signalling", "Cytokine signalling".
Example output: {"revise": true, "name": "Adaptive immune signalling", "reason": "Repeated the
parent; the members are T and B cell receptor pathways, which separates it from both siblings."}


This theme is currently named "Immune signalling".

Its own members:
  - TLR4 cascade
  - MyD88-dependent signalling
  - NF-kB activation

Its parent themes are named: Cell communication

Its siblings, each with its three most strongly included members:
  "Interferon response"
      - type I interferon signalling
      - ISG induction
      - IRF3 activation
  "Inflammasome assembly"
      - NLRP3 inflammasome
      - caspase-1 activation
      - IL-1b maturation

Is this name a duplicate of one already in use, or a name that would also describe one of those siblings? Revise only on those grounds.
```

## Mechanical checks

- `words`
- `in_range`
- `leading_article`
- `trailing_punctuation`
- `sentence_case`
- `identifiers`
- `source_words`
- `empty_words`
- `bare_category`
- `copies_member`
- `repeats_parent`
- `clashes_sibling`
- `duplicate_name`  **NEW in v3**

`clean` is the conjunction of all of them.

