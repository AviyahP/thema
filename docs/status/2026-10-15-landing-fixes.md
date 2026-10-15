# Making the O50 landing preview shippable. 15 Oct 2026

The preview is **12.8 MB raw / 3.2 MB gzipped**, down from 104.6 MB, parses in **84 ms** on **73 MB**
of heap, opens from `file://`, and has **no horizontal overflow at 360 px** — checked in headless
Chrome, not asserted. The published page is untouched apart from the two `<meta>` lines and the
three defect fixes. **No example card was changed**; the candidate search is a report.

## 1. The payload — each pathway emitted once

| | raw | gzipped | reduction |
|---|---:|---:|---|
| **old, inline** | 109,867,992 B — **104.8 MB** | 24,307,570 B — **23.2 MB** | |
| **new, deduped** | 13,374,738 B — **12.8 MB** | 3,339,236 B — **3.2 MB** | **8.2x raw, 7.3x gzipped** |

| | old | new |
|---|---:|---:|
| read + evaluate (node) | 561 ms | **84 ms** |
| heap after parsing | 471 MB | **73 MB** |
| pathway objects emitted | 61,218 | **5,539** |

The cause was never the tree: 98% of the old payload was pathway objects inlined once per
occurrence, 11.1 copies of each because a multi-parent theme is emitted under every parent. The new
shape emits each object **once** into a top-level `pathways` map and leaves an id in the node.
Capping depth was the alternative and was measured as useless — depth 2 still gave 70.1 MB.

**Nothing about the design moved.** The order of every pathway list is unchanged, so the rendered
page is identical; a test resolves both shapes and asserts object-for-object equality in order.
`landing.html` reads **either** shape:

```js
const POOL = EXPORT && EXPORT.pathways ? EXPORT.pathways : null;
const kidsOf = n => n.children
  || (n.pathways ? (POOL ? n.pathways.map(id => POOL[id]) : n.pathways) : []) || [];
```

so an older `ontology.js` keeps working untouched. **No `fetch`** — decision A1 holds, verified in the
browser as well as in the source.

**The old exporter output is behind a flag.** `--payload inline` reproduces the previous shape;
`deduped` is the new default. Inline output matches the previous content exactly apart from two
additive fields — `manifest.payload`, and `edited` on every node — plus the tie-break below.

## 2. Example-card candidates — a search, not a choice

`docs/status/2026-10-15-card-candidates.md`. **No card was changed.**

| card | themes qualifying | with meaningful gene sets |
|---|---:|---:|
| 1, names that look unrelated | **3,114** | 1,940 (every member 5+ genes) |
| 2, the same observation twice | **3,896** | 1,320 (every member 10+ genes) |

Top 15 of each, ranked as specified — smallest theme first, then support — with member names,
sources, gene counts, pairwise kappa, shared-gene counts, and the theme id, size and support.

**The specified ranking puts degenerate sets on top, and the file says so.** The smallest themes are
full of one-gene Reactome variant pathways: "every pair below kappa 0.05" is then true because there
is almost nothing to share, and "nested" is true because both sets are the same single gene — which
cannot carry the current card's figures (104/6/46/200 genes; 21 shared against 57 new). Worse for
card 1, the structural criteria say nothing about names, and the top candidate `n00290` is three Wnt
pathways, whose names obviously do connect.

So each card gets **two** lists: **A** exactly as ranked, and **B** the same ranking with a gene
floor. A "content words shared by any pair" column is reported for card 1 as a crude proxy for how
unrelated the names look. List B's top card-1 candidate is `n00543` — *Acrosome Reaction and
Sperm:Oocyte Membrane Binding* (Reactome, 6 genes), *Interaction With Cumulus Cells And The Zona
Pellucida* (Reactome, 11), *regulation of sperm capacitation* (GO, 6) — **all three pairs share no
gene at all**, one content word in common, in a 3-member theme at support 0.935.

## 3. The three pre-existing defects, fixed

**A deterministic tie-break.** Sorting pathways on the lowercased name alone left case-tied names
("Gap junction assembly" against "gap junction assembly") to `set` iteration order, which Python
randomises per process — so two runs of the exporter produced different bytes. The key is now the
tie-break. Two runs **without** `PYTHONHASHSEED` are now identical. Against the previously shipped
bytes this moved **30 of 4,451 pathway slots (0.674%)**, all of them case-tied, with the multiset
unchanged.

**The broken default.** `--method ward_tree` raised `KeyError: 'parents'` — a cut-based export has
no parents column — so the documented default invocation did not work at all. Two changes: the
column is skipped when absent (not defaulted to `""`, which would make the DAG test read a parentless
DAG), and **the default is now `recurrent_dag_consensus`**, which is what actually generates the
page. `ward_tree` now also exports cleanly (4.2 MB) and its example cards even resolve to `k200:147`.

**The unrecorded prompt version.** `manifest.get("prompt_version", "v4-repaired")` asserted a prompt
version whenever a manifest omitted one — and the published build's manifest omits it, so the live
page has been stating a version nothing recorded. The default is gone; the page now omits the clause
rather than printing a blank, falling back to the description digest alone when there is one. The
O50 preview's build line shows no prompt version, because its manifest records none.

35 tests in `tests/test_export_landing.py` cover all of this, including that the hardcoded default
cannot come back and that both payload shapes render identically.

## 4. The missing head lines

`demo/landing.html` had **no `<meta charset>` and no `<meta name="viewport">`**. Without the viewport
line a phone uses a 980 px virtual viewport and scales the page down, so the `max-width: 760px` and
`max-width: 980px` rules never fire. Both are now in the real page and in the preview, and a
parametrised test asserts them on both.

## 5. The preview, re-exported

`demo/preview-O50/` — `ontology.js` **13,374,738 B (12.8 MB)** and `landing.html` 46,345 B.

Names are the deduplicated `dedup/final_names_O50_lite_unique.tsv` (sha256 `5a9c3e43…`) with
`name_overrides.tsv` (sha256 `5e6c5c42…`) applied on top. **4,576 of 4,602 themes named, 1
hand-edited.** `n02960` carries Aviyah's name — *Calcium–phosphate homeostasis and mineralization
(vitamin D, phosphate, vitamin K)* — and is marked **`edited`** in the manifest (`n_edited`,
`edited_names`, `overrides_file`, `overrides_sha256`) and with an `edited` chip on the page, because
a hand-edited name is a different claim from a generated one. 26 themes stay provisional: 15 the
namer declined, 11 over 200 members.

### The browser check — headless Chrome 155, a real 360 px viewport

No Playwright is installed, so the check runs Chrome's own headless mode. `--window-size=360,800`
does **not** give a 360 px viewport under `--headless=new` (it reported 500), so the page is loaded
in a 360 px-wide iframe with `--allow-file-access-from-files` and measured from inside it.

| check | result |
|---|---|
| viewport | **360 x 4000** |
| `documentElement.scrollWidth` | **360** — **no horizontal scroll** |
| elements whose box extends past the viewport | **0** |
| also checked at 390 px and 768 px | scrollWidth equals the viewport at both; 0 wide elements |
| deduped pool resolved in the browser | `PAYLOAD deduped`, `POOL 5539`, `THEMES 4602` |
| root rows rendered | **188** |
| `edited` chip rendered | **1** |
| `fetch(` in the loaded source | **no** |
| build line | shows no prompt version, as intended |
| opening a theme | 2,120 → 2,233 elements, so ids resolve interactively |

One false alarm worth recording: the first run reported horizontal overflow and a 697 px scroll
width from a `<pre>` with `white-space: pre`. That `<pre>` was **my own probe's output element**,
appended by the measurement script — not part of the page. Re-run against the clean page, the
overflow is zero. The page contains no `<pre>` at all.

## 6. Cost

| | |
|---|---|
| export, deduped | 0.95 s, 293 MB |
| card-candidate search | 3.2 s, 174 MB |
| browser check | about 10 s per viewport |

## Commands

```sh
uv run scripts/export_landing.py \
    --build data/ontology/frozen/working-O50-2026-10-14 \
    --names data/experiments/naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.tsv \
    --name-overrides data/experiments/naming_O50_2026-10-14/name_overrides.tsv \
    --version 0.4-leaves --method thema_L_x2_O50 --out demo/preview-O50

uv run scripts/export_landing.py --payload inline --out /tmp/old   # the previous shape
uv run scripts/card_candidates.py
uv run pytest tests/test_export_landing.py
```
