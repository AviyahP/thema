# What merging siblings at J >= 0.5 would do (reviewer, 2026-10-12, simulation only, nothing changed)

Build: thema_L_x2_c85 (8,251 themes). Sibling pairs with J >= 0.5: 3,337. Scripts mrg5.py, mrg5b.py; full output merge_J05_output.txt.
Post-hoc question from Aviyah after the whole-reading test; not pre-registered.

## Size of the change
| rule | linkage | themes removed | biggest group |
|---|---|---|---|
| J >= 0.5 | complete | 1,767 (21%) | 5 |
| J >= 0.5 | single | 2,865 (35%) | 31 (NF-kB chain, mixes activation with deubiquitination/negative regulation) |
| J >= 0.6 | complete | 840 (10%) | 4 |
Single linkage chains distinct themes together; only complete linkage is acceptable.

## Structure (J >= 0.5, complete linkage)
- Merged theme = union of the group: median 1.27x the kept theme's size (max 1.96x).
- 1,145 of 1,539 groups have a parent that does not contain the union (the siblings had different extra parents): 2,594 parent
  links would have to be dropped, so the DAG loses multi-parent links.
- 839 unions would sit within J >= 0.85 of a shared parent, so the existing c85 chain rule would then absorb them into the
  parent too. Total removal after that is about 2,600 themes (about 32%), and those branches lose a level.
- Keep-one instead of union: 7,732 pathway-theme memberships lost (3,673 pathways), 1,709 children must be re-attached higher.
- Children per parent: mean 3.6 -> 3.1; 513 parents left with a single child.
- Spread evenly: every giant bucket loses 20-23%.

## Theme content
- Labels: full-list judges call 54% of the collapsed pairs facets (46% precision); original labels 61% twin.
- Whole-reading test, same pairs: shared pathways used differently in 13% at J 0.4-0.5, 6% at 0.5-0.6, 7% at >= 0.6.
- So the "facets" lost are mostly distinctions carried by the few extra pathways (e.g. kidney nephric duct/ureter vs
  metanephros), not different readings of the shared core. Clear gains: e.g. five type I interferon / RLR variants become one.

## Rule hygiene
J >= 0.5 has a label-free reading (the shared part is larger than the two unique parts together). Choosing it because of the
whole-reading result would be calibration on LLM output, which the working rules forbid; it must be declared on the label-free
basis or not at all.

## Addendum: is it still a multi-parent DAG? (mrg5c.py)
Parents re-attached to the lowest ancestor that contains the merged union; redundant (ancestral) parent links removed.
| | themes | 2+ parents (not nested in each other) | reach 2+ top roots |
|---|---|---|---|
| before | 8,241 | 4,223 (51%) | 56% |
| after merge, drop non-containing parents | 6,475 | 2,306 (36%) | 45% |
| after merge, re-attach upward | 6,475 | 2,446 (38%) | 47% |
- Themes not merged that had 2+ parents: 87% keep them. Of the 291 that lose them, 181 had parents that were all variants
  merged into one (the multi-parentage was duplication), 110 because their parents became nested after the union.
- Merged themes: 467 of 1,539 keep 2+ parents. The union of variants usually fits only under the parent they shared.
