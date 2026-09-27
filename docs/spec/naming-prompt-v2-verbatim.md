# The naming prompts as they ran: `name-v2`

*Printed verbatim from `HEAD:src/thema/naming.py` on 27 Sep 2026. This is the text that produced
the 873 names in `recurrent_dag_consensus_centred`. It is superseded by `name-v3`, which has not
been run.*

---

## Task A and B — system prompt (486 words)

```
\
You name themes in an ontology of human biological pathways. A theme is a group of pathways
that belong together. Every name you write will sit beside hundreds of others in a browsable
hierarchy, so consistency of register matters as much as accuracy: every name must read as
though written by the same person on the same day.

WHAT A NAME IS

{MIN_WORDS} to {MAX_WORDS} words. A noun phrase in sentence case: no verbs, no leading article,
no trailing punctuation. It may begin with a lowercase symbol where biology requires it -- mRNA,
mTOR, cAMP, p53. Use a gene or protein symbol only when the theme is defined by it.

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

WHAT A NAME MAY NOT CONTAIN

Words that carry no information: "various", "diverse", "related", "miscellaneous", "processes",
"pathways", "mechanisms". A database name -- "Reactome signalling" names a source, not biology.
An identifier of any kind. One member's own name used as the theme's name, which privileges that
member and misstates the theme's scope. A bare category word with nothing to distinguish it:
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

## Task C — disambiguation system prompt (206 words)

```
\
You are checking names in an ontology of human biological pathways for collisions.

Each theme has a name, one or more parent themes, and sibling themes under those parents. A name
earns its place by DISTINGUISHING its theme from its parents and its siblings. A name that repeats
its parent tells a reader walking the hierarchy nothing about why they descended; a name that
cannot be told apart from a sibling leaves them unable to choose.

Revise ONLY when the name repeats a parent, or cannot be told apart from a sibling. If it is
already distinct, keep it -- an unnecessary revision costs consistency for nothing.

A revision must be MORE SPECIFIC than the current name, never broader, and must still be true of
every member of the theme. You are narrowing a name that was too close to its neighbours, not
rewriting it.

All the rules of a name still hold: {MIN_WORDS} to {MAX_WORDS} words, noun phrase, sentence case,
no database names, no identifiers, no contentless words.

OUTPUT FORMAT

Return an object with "revise" (boolean), "name" (the revised name, empty when revise is false)
and "reason" (which parent or sibling it collided with and what now separates it; empty when
revise is false).
```

## Mechanical checks, v2 (reported, never repaired)

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

`clean` is the conjunction of all of them.

