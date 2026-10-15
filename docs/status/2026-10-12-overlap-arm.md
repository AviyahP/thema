# The overlap arm: one same-theme cutoff inside the build. 12-13 Oct 2026

**EXPLORATORY, on branch `overlap-2026-10`. Nothing is adopted.** The specification was declared by
the reviewer on 12 Oct before any build and is copied verbatim into DECISIONS; the criteria below are
its criteria, unchanged.

| | criterion | owner | result |
|---|---|---|---|
| **C1** | no non-nested pair under 1,000 at J >= 0.50, and no containment pair at >= 0.85 | ccode | **PASS** — 0 and 0 |
| **C2** | no pathway loses all its themes under 1,000 members | ccode | **FAIL** — 1 pathway, `btm:M205` |
| **C3** | >= 99% of c85 themes absent from O50 have an O50 counterpart at J >= 0.50 | ccode | **PASS** — 99.64% |
| C4 | plausibility | **reviewer** | not judged here; input written |
| C5 | usefulness, blind | **reviewer** | not judged here |

**One of the three criteria ccode owns fails.** By the spec's decision rule — "O50 becomes the
candidate working version only if C1-C4 pass and C5 is won" — that is already decisive unless Aviyah
treats a single stranded pathway as acceptable. The failure is small and specific, and is described
in full below rather than rounded away.

## 1. What was changed in the code

Three constants governed the same measure at values chosen at different times. The arm separates what
they mean and lets one of them be set once.

| constant | was | now |
|---|---|---|
| `v04.THETA_MATCH` | 0.70, recurrence | **unchanged at 0.70**, and now provably separate |
| `v04.THETA_MERGE` | 0.70, hardcoded into `v04.build` | the **default** of a new `theta_same` parameter |
| `repair.MERGE_JACCARD` | 0.70, the stale pass's own constant | **receives the same `theta_same`** |
| `repair.COLLAPSE_SHARE` | 0.85, nesting | unchanged |

- `v04.build(..., theta_same=THETA_MERGE)` passes the cutoff to `consensus`; **the same value** goes
  to the stale-merge pass, so one number now governs non-nested overlap in both places.
- `repair.repair_joint()` is new: it repeats `[chain collapse at 0.85, stale merge at theta_same]`
  until neither changes anything, then asserts that no non-nested pair at or above `theta_same` and
  no containment pair at or above 0.85 survive. `repair.assert_no_chain_pair()` is the second of
  those assertions. **`repair.repair()` is untouched**, which is what keeps the harness proof honest.
- `scripts/leaves_build.py` gains `--theta-same` and `--joint-fixed-point`, both recorded in the
  manifest (`theta_same`, `theta_merge`, `joint_fixed_point`, and `repair.joint_fixed_point`).
- **Every default is unchanged**: omitting both flags runs exactly what every build before 12 Oct ran.

## 2. Harness proof — PASS

| check | result |
|---|---|
| same-theme 0.70, no joint loop, vs `thema_L_x2_c85` | **all four tables byte-identical** |
| `tests/ontology/test_frozen_baseline.py` | **passes**, both freezes |

315 s and 1.3 GB. So the new code path reproduces c85 exactly, and any difference below is the arm
and not the refactor.

## 3. Theme counts

| build | `theta_same` | joint loop | themes | edges | roots | giants |
|---|---:|---|---:|---:|---:|---:|
| **c85** | 0.70 | no | **8,251** | 18,707 | 121 | 10 |
| **O70** (control) | 0.70 | yes | **8,251** | 18,707 | 121 | 10 |
| **O60** (report only) | 0.60 | yes | **6,350** | 12,646 | 194 | 7 |
| **O50** (the arm) | 0.50 | yes | **4,602** | 7,525 | 188 | 4 |

**The control answers cleanly: O70 is byte-identical to c85 in all four tables.** At a 0.70 cutoff
the joint fixed point changes nothing, so **every difference between O50 and c85 is the cutoff, not
the iteration** — which is exactly what the spec asked the control to establish. This was predictable
and was predicted before the builds: because the merge *supersedes* the weaker theme rather than
unioning the pair, no sub-pass ever changes a member set, so the set of qualifying pairs is fixed from
the start and both sub-passes are already internally fixed points. A 8,000-fixture random search over
the two passes found no case where iterating differs from one pass. The extra rounds are confirming
no-ops (collapse 5 rounds against 4, merge 3 against 2).

Giant root sizes: c85 and O70 `[2673, 2522, 2366, 2304, 2047, 2044, 2042, 1433, 1245, 1187]`;
O60 `[2647, 2498, 2354, 2035, 2029, 1423, 1316]`; **O50 `[2332, 2018, 2015, 1412]`**. The arm is the
first change in this project that reduces the giants — 10 to 4 — because merging at 0.50 absorbs the
overlapping variants the giants were built out of.

### By size band

| band | c85 | O70 | O60 | O50 | O50 − c85 |
|---|---:|---:|---:|---:|---:|
| 3-5 | 524 | 524 | 524 | 524 | +0 |
| 6-10 | 2,101 | 2,101 | 2,028 | 1,636 | −465 |
| 11-20 | 4,061 | 4,061 | 2,775 | 1,711 | **−2,350** |
| 21-50 | 1,324 | 1,324 | 869 | 615 | −709 |
| 51-100 | 193 | 193 | 120 | 95 | −98 |
| 101-300 | 32 | 32 | 23 | 14 | −18 |
| 301-1000 | 6 | 6 | 4 | 3 | −3 |
| 1001+ | 10 | 10 | 7 | 4 | −6 |

Removal is concentrated in 11-20 members, the band the twin work identified as near-duplicate
variants. Nothing is removed at 3-5.

## 4. C1 — PASS

Checked over **every** pair, not only the DAG's direct edges, because that is what the rules
themselves consider.

| build | non-nested pairs at J >= 0.50 (both under 1,000) | containment pairs at >= 0.85 |
|---|---:|---:|
| c85 | **9,138** | 0 |
| O70 | 9,138 | 0 |
| O60 | 2,982 | 0 |
| **O50** | **0** | **0** |

The 9,138 pairs in c85 are the redundancy the arm exists to remove, and it removes all of them. O60
still leaves 2,982 at 0.50, as it must: its own cutoff is 0.60.

## 5. C2 — FAIL, on one pathway

| | |
|---|---|
| pathways with at least one theme under 1,000 | c85 **5,539**, O50 **5,538** |
| pathways that lost at least one level | 5,522 (median 12, max 47) |
| **pathways left with none** | **1 — `btm:M205`** |

`btm:M205` had three small homes in c85 — `n04672` (10 members, support 0.105), `n05438` (14, 0.070)
and `n06033` (14, 0.055) — all three weak, and all three merged away at 0.50. In O50 it survives only
inside three giants (`n01845` 2,332, `n03867` 2,018, `n02670` 2,015), so a hit on it can no longer be
interpreted through anything but a bag.

**This is a real failure of a declared criterion and is reported as one.** Two things are worth
stating next to it without softening it: the criterion is a floor of exactly one, and the pathway
that falls through it was held only by themes whose support was 0.055-0.105, i.e. at the bottom of
the distribution. Whether a single stranded pathway should sink the arm is Aviyah's call, not a
number ccode can settle.

Median levels lost is 12, which is large; that is the arithmetic consequence of removing 9,138
overlapping pairs, and it is the same effect C3 shows from the other side.

## 6. C3 — PASS

4,507 of c85's 8,251 themes are absent from O50. Of those, **4,491 (99.64%) have an O50 theme at
J >= 0.50**, against a bar of 99%. The 16 without one are all in the 0.44-0.47 band, just under the
cutoff: `n06119` (58 members, best J 0.444), `n05029` (18, 0.458), `n06800` (18, 0.458), `n07699`
(22, 0.458), `n02228` (11, 0.462), `n05830` (13, 0.462), `n03054` (8, 0.467), `n06092` (11, 0.467),
`n06059` (12, 0.471), `n06372` (34, 0.471), and six more.

## 7. Report-only measurements

### Multi-parent structure, and a correction to how it is quoted

| build | 2+ non-nested parents | reaching 2+ roots | 2+ parents, giants excluded | 2+ roots, giants excluded |
|---|---:|---:|---:|---:|
| c85 | 64.8% | 93.2% | **51.2%** | **55.7%** |
| O70 | 64.8% | 93.2% | 51.2% | 55.7% |
| O60 | 55.7% | 78.2% | 43.1% | 42.6% |
| **O50** | **43.7%** | **53.1%** | **36.8%** | **41.9%** |

**The spec's "51% and 56% in c85" are the giants-excluded numbers.** Measured literally, c85 is 64.8%
and 93.2% — almost every theme reaches two giants, so the literal root measure says little. Compared
on the spec's own definition, the post-hoc simulation's prediction of "about 38% and 47%" was close on
parents (36.8%) and **optimistic on roots (41.9%)**. Both definitions are given above so the
comparison is checkable rather than asserted.

Themes whose every parent is a root: c85 1,084, O70 1,084, O60 1,036, O50 749. O50's manifest records
4 themes as effectively unplaced (`n_root_only` 4), against 0 in c85.

### Depth

| depth | c85 | O70 | O60 | O50 | | depth | c85 | O70 | O60 | O50 |
|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 0 | 121 | 121 | 194 | 188 | | 7 | 679 | 679 | 402 | 301 |
| 1 | 1,084 | 1,084 | 1,036 | 749 | | 8 | 422 | 422 | 231 | 156 |
| 2 | 1,141 | 1,141 | 934 | 698 | | 9 | 253 | 253 | 100 | 60 |
| 3 | 1,144 | 1,144 | 941 | 701 | | 10 | 120 | 120 | 29 | 18 |
| 4 | 1,164 | 1,164 | 959 | 681 | | 11 | 43 | 43 | 8 | 2 |
| 5 | 1,107 | 1,107 | 852 | 602 | | 12 | 11 | 11 | 2 | 0 |
| 6 | 958 | 958 | 662 | 446 | | 13 | 4 | 4 | 0 | 0 |

The lattice gets shallower and wider: more roots (121 to 188) and a tail cut off above depth 11.

### Survivor support margins

| build | collapses | child kept | parent kept | median margin | margin under 0.05 |
|---|---:|---:|---:|---:|---:|
| c85 | 1,147 | 742 | 405 | 0.120 | **28.3%** |
| O70 | 1,147 | 742 | 405 | 0.120 | 28.3% |
| O60 | 776 | 522 | 254 | 0.140 | 25.3% |
| **O50** | **587** | 408 | 179 | **0.185** | **19.4%** |

The arm **improves** the known limit it inherited: fewer collapse decisions, and the share decided by
a near-tie falls from 28.3% to 19.4%. It does not remove it.

### Reproducibility between two independent builds, projected

| | matched at J >= 0.70 | share |
|---|---|---:|
| c85 vs `thema_L_repair` | 6,358 of 8,251 | **77.1%** |
| O50 vs `thema_L_repair_O50` | 3,229 of 4,602 | **70.2%** |

Reported, not a criterion: the spec says so explicitly, because removing duplicates lowers a
share-matched measure by construction — the same reason criterion (d) was withdrawn from the c85
assessment. The 7-point drop is consistent with that and is not evidence either way.

### O60

6,350 themes, 194 roots, 7 giants, 55.7% with 2+ non-nested parents (43.1% giants-excluded), 42.6%
reaching 2+ roots giants-excluded. It leaves 2,982 non-nested pairs at 0.50 and 0 containment pairs.
Report only; no criteria are evaluated against it.

### Cost

| build | wall time | peak RAM |
|---|---:|---:|
| harness proof (c85 reproduction) | 315 s | 1.3 GB |
| O70 | 326 s | 1.2 GB |
| O60 | 181 s | 1.4 GB |
| O50 | 94 s | 1.5 GB |
| `thema_L_repair_O50` | 92 s | 1.3 GB |
| this report | 3 s | 0.2 GB |

Lower cutoffs are **faster**, because consensus supersedes more candidates earlier and the DAG it
stacks is smaller.

## 8. C4's input, for the reviewer

`data/ontology/v0.4-leaves/thema_L_x2_O50/O50_new_themes.json` — **858 of O50's 4,602 themes are not
identical to any c85 theme**; 3,744 are. Each of the 858 carries its node id, size, support, full
member list as titles, and the pathway keys. Nothing about them is judged here.

## 9. What this says, and what it does not

The arm does what it was designed to do, and more than was asked:

- **every one of the 9,138 overlapping pairs is gone**, and no new offending pair of either kind
  survives;
- **the giants drop from 10 to 4** — the first change in this project that moves them at all;
- the near-tie fragility falls from 28.3% to 19.4%;
- **the control is clean**: O70 is byte-identical to c85, so the result is the cutoff and nothing
  else, and the architectural complaint the arm was built on — three cutoffs on one measure, applied
  in an order-dependent sequence — is answered by one cutoff in two places.

Against that:

- **C2 fails on one pathway**, `btm:M205`, which loses all three of its weak small homes;
- the ontology is **44% smaller** and a pathway sits in a median of 12 fewer themes, which is either
  the redundancy going away or resolution going away, and **C4 and C5 are what decide which**;
- the prediction for multi-parent roots was optimistic: 41.9% against "about 47%".

**Adopted: nothing.** C4 and C5 are the reviewer's, and by the spec's own decision rule the arm cannot
become the candidate working version while a C1-C4 criterion fails. c85 remains the working version
and the 2026-10-09 baseline remains the fallback.

## Reproducing this

```sh
# harness proof: must return c85 byte for byte
uv run scripts/leaves_build.py --arm L --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --out-version 0.4-leaves --floors-file data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
    --repair --collapse-share 0.85 --survivor support --directory thema_L_x2_harness

# the arm, its control, and the sensitivity point
uv run scripts/leaves_build.py --arm L --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --out-version 0.4-leaves --floors-file data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
    --repair --collapse-share 0.85 --survivor support \
    --theta-same 0.70 --joint-fixed-point --directory thema_L_x2_O70
#   ... --theta-same 0.50 ... --directory thema_L_x2_O50
#   ... --theta-same 0.60 ... --directory thema_L_x2_O60
uv run scripts/leaves_build.py --arm L \
    --floors-file data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
    --repair --collapse-share 0.85 --survivor support \
    --theta-same 0.50 --joint-fixed-point --directory thema_L_repair_O50

uv run scripts/overlap_arm_report.py      # every number above, and O50_new_themes.json
```
