# Naming prompt v3 — proposal, not applied

*26 Sep 2026. Every change below answers a measurement from the v2 run on the 808-theme consensus
DAG. Nothing here is applied; `name-v2` is still what produced `data/theme_names.tsv`.*

## What v2 measured, and what each number demands

| finding | change |
|---|---|
| **415 of 808 names (51%) were revised for repeating a parent.** GO does exactly that in 25% of its parent–child pairs, and 94% share a content word. Compositionality is what makes a hierarchy navigable by name. | **Repeating a parent is ALLOWED** when the child adds a qualifier. Only a name that fails to discriminate is revised. |
| **8 themes refused, including the 959-member root.** Its stated reason: *"no shared biology tighter than 'cellular regulatory processes', which is too vacuous to serve as a name."* GO ships "cellular process" and "biological regulation" and is navigable because of it. | **An honest umbrella name is a valid answer.** Refusal is reserved for genuinely incoherent unions. |
| **59 of 87 check failures were the 6-word limit**, on names like "Nucleic acid sensing and type I interferon signalling". Compositional and umbrella names need room. | **Limit relaxed to 8 words**, advisory above 6. |
| **Test 1: a pathway was placed in its correct theme 30% of the time at level 0**, 50% at level 1, 44% at the finest — from the name alone. | **A tightness self-check is required in the response**, naming a member the name would NOT fit. |
| **Test 2: 46% of parent–child edges recoverable from names.** | Compositionality (above), plus the sibling check below. |
| A 471-member theme was named "Glucose and lipid metabolic regulation" while its largest members are phosphorus metabolism and post-translational modification. | The tightness check is what catches this: the name must be checked against the members, not composed from an impression of them. |

## Task A — a leaf theme

```
You are naming one theme in an ontology of human biological pathways. A theme is a group of
pathways that recurred together across resampled clusterings. You are shown every member.

Write the name a working biologist would want to see on this group in a browsable hierarchy.

WHAT A NAME MUST DO

1 to 8 words, a noun phrase in sentence case. No verbs, no leading article, no trailing
punctuation. Six words or fewer if it can be done without losing accuracy; up to eight when the
theme genuinely spans two things.

It must be TRUE OF EVERY MEMBER. Not of most of them. A name that fits nine of eleven members is
wrong, and the two it fails are what a reader will trust it about.

It must be the TIGHTEST true description. If every member concerns sterol transport, the name is
about sterol transport, not about lipid metabolism.

THEN CHECK YOURSELF, AND REPORT THE CHECK

Before answering, name the member your name fits WORST, and say whether it still fits. If it does
not, your name is too tight or too loose and you must change it. Report that member in
`weakest_member` and your judgement in `weakest_fits`. A name whose worst member does not fit is
not an answer.

WHEN NO SINGLE NAME IS TRUE OF EVERYTHING

Say so in `nameable: false` with the reason. Reserve this for unions that share no honest
description at all -- two unrelated signalling systems, a mixed bag of housekeeping modules. Do
NOT refuse merely because the only true description is broad: see Task B.
```

## Task B — an internal theme (its children plus its direct members)

```
[Task A's rules, and then:]

You are shown this theme's already-named children AND its DIRECT MEMBERS -- the pathways in it that
sit in no child. The direct members are why this theme exists as something broader than its
children. Name the union of children and direct members.

YOU MAY EXTEND A CHILD'S NAME, AND OFTEN SHOULD

A parent named "Notch signalling" above a child named "Non-canonical Notch signalling" is a GOOD
pair: a reader can see the relationship from the names alone. Curated ontologies do this
deliberately -- a quarter of GO's parent-child pairs repeat the parent's name verbatim and add a
qualifier. Do not avoid a word because a child or parent uses it. Reuse is how a hierarchy reads.

AN HONEST BROAD NAME IS A REAL ANSWER

Some themes ARE broad. A theme spanning proteostasis, membrane trafficking, apoptosis regulation
and transcriptional programmes has no tight name, and that is a fact about the theme, not a failure.
Name it honestly at the level it actually sits: "Cellular regulatory processes" is a better answer
than a refusal, and a far better answer than a specific name that is false.

Set `umbrella: true` when you do this, so the name is displayed as the broad label it is. An
umbrella name must still be TRUE of every member -- broad is allowed, wrong is not.

`nameable: false` is now only for unions with no honest description at any level of generality.
```

## Task C — discrimination, replacing the collision check

```
You are given one theme's name, its members, and the names and members of its SIBLINGS -- the
other themes under the same parent.

Answer one question: does this name describe any sibling as well as it describes its own theme?

This is not a check for repeated words. Two siblings may share vocabulary and still be clearly
distinguished -- "Canonical Wnt signalling" and "Non-canonical Wnt signalling" are fine. What is
not fine is a name a reader would apply to the wrong theme: if "Immune signalling" would fit the
sibling's members just as well as its own, it fails, and needs the qualifier that separates them.

Revise ONLY when the name fails to discriminate. Report which sibling it collided with. Repeating a
parent's name is not a fault and is not grounds for revision.
```

## What the procedure must also do

- **Show siblings' MEMBERS in Task C, not only their names.** The v2 pass compared strings, which is
  why it revised 415 names for repetition while leaving names that genuinely fail to discriminate.
- **Persist every revision.** The v2 run printed "354 parents with a renamed child" and stored
  nothing, so that cut is unrecoverable. The names table needs a `revised_from` column.
- **Response format** gains `umbrella` (boolean), `weakest_member` (string), `weakest_fits`
  (boolean). Keyed on a boolean per the `extract_text` constraint.

## What this does NOT fix

Test 1's level-0 score was 30% on only 15 candidate themes, and those themes are the largest and
vaguest in the build. If the top of the hierarchy is genuinely broad, honest umbrella names will
read correctly and STILL not discriminate between one another -- "Cellular regulatory processes"
against "Cellular stress and modification" does not tell a reader where a pathway goes. **Naming
cannot fix a coarse top.** That is a separate question about the hierarchy, and this proposal does
not address it.
