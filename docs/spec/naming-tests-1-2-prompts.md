# Naming validation Tests 1 and 2 — prompts for review before any spend

*Written 27 Sep 2026 against the 861 `name-v3` names of `recurrent_dag_consensus_centred`. **Nothing
has been sent.** These are the prompts as they stand on disk, unchanged since the runs of 26 Sep that
`CLAUDE.md` records as having gone out unreviewed. Both of those runs produced results weaker than
first reported, and in both cases the wording is part of the reason. The defects are named below with
a proposed replacement; approve the wording and the price separately.*

## Prices, measured on the new names

| test | calls | worst case | ceiling |
|---|---|---|---|
| Test 1, name sorting — 50 level-0 + 88 level-1 + 482 finest themes, 25 pathways per call | 222 | **$6.72** | $12.00 |
| Test 2, name DAG — 986 true edges + 986 size-matched non-edges | 1,972 | **$3.08** | $5.00 |
| both | 2,194 | **$9.80** | — |

The ceilings are the existing script defaults. Test 1's earlier ceiling did NOT bound its cost: it
quoted $6.63 worst case and billed $12.16, because output ran 2.4x the assumption and nothing cached.
Treat $6.72 as an estimate of the same shape, not a guarantee, until its estimator is calibrated the
way `name_themes.py`'s now is.

---

## Test 1 — `sort-v1`, in `scripts/test_name_sorting.py`

**What it measures.** A pathway's description is shown with a slate of theme names. If the names
carry the themes' content, the right theme should be findable from the name alone.

### The prompt as it stands

```
\
You are given a numbered list of THEME names from an ontology of human biological pathways, and a
numbered list of pathway DESCRIPTIONS.

For each pathway, say which theme it belongs to, judging only from the theme's name and the
pathway's description.

A pathway may belong to no theme on the list. Answer 0 for it. Do not force a match: answering 0
when nothing fits is correct and useful, and guessing is not.

Answer with one entry per pathway, in the order given.
```

User message, per call:

```
THEMES:
  1. <theme name>
  ... one line per theme on the slate

PATHWAYS:
1. <pathway description>

  ... 25 of them

For each of the 25 pathways give the theme number, or 0 for none.
```

### The defect

**The prompt asks for one theme; the scoring accepts any of several.**
`scripts/test_name_sorting.py:204` builds `truth = {t for t in themes if key in members[t]}` — a
SET, because a pathway really does sit in several themes at one level. The prompt says "say which
theme it belongs to", singular, and the schema permits exactly one integer. So the model is asked a
question with one answer and graded on a question with many, and the reported number is "can the
model find ONE true theme" while it reads as "can the model find the right theme". The looser
question is the easier one, so the measurement flatters the names.

### Proposed replacement — `sort-v2`, the change in full

> For each pathway, say which theme it belongs to, judging only from the theme's name and the
> pathway's description.
>
> **A pathway may genuinely fit more than one theme on the list, because themes overlap. Give the
> one you think fits best. You are not being asked to find every theme that fits.**
>
> A pathway may also belong to no theme on the list. Answer 0 for it. Do not force a match:
> answering 0 when nothing fits is correct and useful, and guessing is not.

Nothing else changes. This makes the instruction match the scoring: the model is told overlap exists
and asked for its best single choice, which is exactly what "in the true set" then scores. The
headline stays comparable to the 26 Sep run only if that run is re-reported as
"accuracy at finding any true theme", which is what it actually measured.

---

## Test 2 — `dag-v1`, in `scripts/test_name_dag.py`

**What it measures.** Two names are shown and the model is asked whether the first is a parent of the
second. Real edges are mixed with size-matched non-edges, so guessing "false" cannot win.

### The prompt as it stands

```
\
You are given two names of themes from a hierarchy of human biological pathways. A theme is a group
of related pathways. A parent theme is BROADER than its child and contains everything the child
contains, plus more.

Answer one question: is the first name a parent of the second?

Judge only from the two names. You have no other information and should not assume any.

Answer true when the first is a genuinely broader theme that would contain the second. Answer false
when they are unrelated, when they are siblings at the same level of generality, when they are the
same theme said differently, or when the SECOND is the broader of the two.
```

User message, per call:

```
First name: "<parent name>"
Second name: "<child name>"

Is the first a parent of the second?
```

### The defect

**The prompt is structurally biased toward `false`.** One sentence says when to answer true; the next
gives FOUR separate grounds for answering false — unrelated, siblings, the same theme said
differently, and the second being broader. A model reading a list of four ways to be wrong and one
way to be right answers false more often, and the headline number of the 26 Sep run was a missed-edge
rate. The prompt invited the caution it then measured.

### Proposed replacement — `dag-v2`, the change in full

> Answer one question: is the first name a parent of the second?
>
> Judge only from the two names. You have no other information and should not assume any.
>
> **Answer true when the first is a genuinely broader theme that would contain the second. Answer
> false otherwise — including when they are unrelated, when they are siblings at the same level of
> generality, when they are the same theme said differently, or when the SECOND is the broader.**
>
> **Both answers are equally expected. Roughly half the pairs you see are real parent-child pairs and
> roughly half are not, so do not lean toward either answer.**

The four grounds are kept but demoted to examples of "otherwise" rather than four parallel
instructions, and the base rate is stated — which is true of the design (986 edges, 986 non-edges)
and is the fact a calibrated judge needs.

---

## What is NOT proposed

Neither test's **statistic** changes, neither's **sample** changes, and neither pass condition is set
after seeing a number. Test 2 had no pass condition declared before its first run and remains
**informational**; saying so is the honest position and inventing one now would be worse.
