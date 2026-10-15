# naming-c1 offline mode, and the O50 naming run. 14-15 Oct 2026

The reviewer runs the namers and judges as in-session subagents; **this code builds every input and
makes every decision.** No API call, no client, no key. The split is deliberate: the naming work is
large (13,773 candidates) and the reviewer's subagents cost nothing, while the selection must be
reproducible and auditable, which is code's job.

**Offline mode is trustworthy only because it is proved against the pilot.** Run on the 11 Oct
pilot's own replies, the four stages return the pilot's own files byte for byte.

## 1. The four stages

```sh
uv run scripts/name_themes_c1.py --offline n1       # write the namer items
uv run scripts/name_themes_c1.py --offline s1       # validate replies, write back-match items + keys
uv run scripts/name_themes_c1.py --offline select   # select(), find duplicates, write dedup items
uv run scripts/name_themes_c1.py --offline final    # apply_uniqueness(), write final_names.tsv
```

Every stage uses `src/thema/naming_c1.py` **unchanged** -- `namer_item`, `backmatch_item`, `select`,
`dedup_items`, `apply_uniqueness`, all already proved against the pilot in prompt 30. The stages add
only orchestration: file layout, batching, validation, and reading the replies back.

Defaults: build `data/ontology/v0.4-leaves/thema_L_x2_O50`, output
`data/experiments/naming_O50_2026-10-14/code_run/`. **Offline mode writes only under its own output
directory** and never into `inputs/`, `raw/`, `raw_rejected/`, `sample/` or `select_lite/`; a test
checks that by comparing modification times on the pilot's 69 input and reply files before and
after a run. The API-mode defaults are untouched, and a test still asserts that the
default priced path builds no client.

## 2. Equivalence proof on the 11 Oct pilot — PASS

| stage | compared against | result |
|---|---|---|
| `n1` | the pilot's 24 `inputs/namer_slot*_b*.json` | **24 / 24 byte-identical** |
| `s1` | the pilot's 12 `selection/main_sel_*.json` | **12 / 12 byte-identical** |
| `select` | `dedup_slot{0,1,2}.json` and `confusables_after_dedup.json` | **4 / 4 byte-identical** |
| `final` | `selection/dedup_sel_01.json` | **byte-identical** |
| `final` | `selection/final_names.json` | **`main` 200 / 200 identical**, `duplicates` and `duplicates_after_dedup` both match |

`tests/test_naming_c1.py::test_offline_mode_reproduces_the_pilot_byte_for_byte` is that proof.
**The pilot's answer keys were never opened**: the `s1` stage writes its own key and the test uses
it, exactly as the earlier reproduction did.

Two defects were found by the proof and fixed, both of which would have produced plausible-looking
but wrong files:

1. **`ensure_ascii`.** Writing the items with `ensure_ascii=False` renders a Greek letter or an
   en-dash in a pathway title literally, where the pilot's `json.dump` escaped it as `\uXXXX`.
   Exactly the 12 of 24 files containing non-ASCII differed. The writer now leaves `ensure_ascii`
   at its default.
2. **Dedup item order.** The uniqueness round's back-match items are numbered in the order the
   replies appear in each slot's file; sorting them by theme id instead handed the item ids to the
   wrong themes, so every judgement for that round attached to the wrong candidate. That showed up
   as 198 of 200 final names matching -- the two de-duplicated themes being wrong. Fixed to iterate
   in reply order, with a comment saying why.

## 3. O50: `n1` reproduces the reviewer's inputs exactly

| | |
|---|---|
| build | `thema_L_x2_O50`, 4,602 themes |
| in naming-c1 scope (3-200 members) | **4,591** (11 themes over 200, including the 4 giants, are out of scope) |
| **files written** | **552** (3 slots x 184 batches of 25, the last 16) |
| **items written** | **13,773** (3 candidates per theme, every theme exactly 3) |
| **diff against the reviewer's `inputs/`** | **552 / 552 byte-identical**, and `themes_and_confusables.json` too |
| cost | 9.5 s, 0.6 GB |

So the reviewer's `nm_build.py` and this offline mode agree completely on the confusable choice, the
member and confusable shuffles, the batching and the serialisation.

## 4. O50: `s1` on the reviewer's 552 replies

| | |
|---|---|
| replies read | **13,773** from **552** files |
| **validation** | **PASS** -- every expected item answered exactly once, `nameable` a boolean, a non-empty name whenever nameable, a rationale whenever not |
| not-nameable votes | **45** (13 / 18 / 14 by slot, matching `N1_SUMMARY.md`) |
| **back-match items written** | **13,728** over **275** files |
| answer keys | `code_run/KEY_DO_NOT_SHARE_main.json`, gitignored by an extension-free rule |
| cost | 9.5 s, 0.6 GB |

The reviewer ran S1 on a **200-theme sample only** (`sample/`, built from rendered titles), reported
in `sample/REPORT_S1_sample.md`: **E1 96.5%, E2 0.924** against the pilot's 91.5% and 0.917. That
sample is **not a reproduction target** and was not diffed against.

## 5. Stopped there, deliberately

`select` and `final` were **not run on O50**. Aviyah chose, for now, names without a full
back-match: the lite selection in `select_lite/` ("naming-c1-lite"). **A full back-match can be run
later from the same 552 raw outputs** -- the `s1` stage has already written all 13,728 items and
their keys, so the only missing input is the judgements.

`code_run/` is 121 MB and is **gitignored**: 552 files byte-identical to the committed `inputs/`
plus 275 derived from the committed `raw/`, so it is a function of committed inputs and committed
code and is regenerated rather than stored.

## 6. The reviewer's run, for the record

All namers were in-session subagents -- **no API spend**. 552 files, all validated by
`code/nm_validate.py`. Two first-run outputs each omitted one theme (`slot2 b011` missing `n01709`,
`slot2 b126` missing `n03398`); both batches were rerun in full and the rejected files are kept in
`raw_rejected/` and are not used. `slot0 b048` retry and `slot1`/`slot2 b048` carried one added
context sentence as a safety-classifier workaround. Roughly 58M subagent tokens in total.

Themes by number of not-nameable votes: `{1: 5, 2: 5, 3: 10}`, so **10 themes are unnameable under
the algorithm** (2 or more of 3) and 5 are borderline.

## Reproducing this

```sh
uv run scripts/name_themes_c1.py --offline n1 \
    --offline-build data/ontology/v0.4-leaves/thema_L_x2_O50 \
    --offline-out data/experiments/naming_O50_2026-10-14/code_run
uv run scripts/name_themes_c1.py --offline s1 \
    --offline-build data/ontology/v0.4-leaves/thema_L_x2_O50 \
    --raw data/experiments/naming_O50_2026-10-14/raw --run main \
    --offline-out data/experiments/naming_O50_2026-10-14/code_run
uv run pytest tests/test_naming_c1.py      # the pilot equivalence proof
```
