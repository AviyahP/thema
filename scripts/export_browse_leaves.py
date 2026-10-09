#!/usr/bin/env python3
"""A self-contained page for reading a universe-L build. Read-only; writes one HTML file.

``export_browse.py`` renders the named 1,850-pathway v0.2 build and expects theme names from the
namer. A universe-L build has **no names** -- the namer has never been run on one -- and needs two
numbers that script does not compute, support at Jaccard 0.5 and gene coherence. So this is a
separate exporter that keeps the same principles: one file, no fetch (``file://`` blocks it, so the
data is embedded), and **every number labelled with the universe it came from**.

What the page is honest about, on the page:

- the universe is the 5,559 ATOMIC pathways, not the 10,770 -- every curated summary was removed;
- themes are unnamed, so each is shown by the member names nearest its centroid;
- **support** is at the build's match threshold 0.70 and **support at 0.5** beside it, because the
  gap between them is the most informative thing about a large theme;
- **coherence** is against a size-matched null, and the eight giant roots are flagged as
  gene-incoherent rather than presented as areas.

Usage::

    uv run scripts/export_browse_leaves.py --stats STATS.json
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.pathways import PathwayCollection
from thema.ontology.universe import load_embedded

#: A root of at least this size is flagged on the page.
GIANT = 1000
#: Coherence below this is flagged as not distinguishable from a random set of the same size.
COHERENT = 3.0

PAGE = """<title>THEMA universe L -- @@BUILD@@</title>
<style>
:root {
  --ink: #1b1f23; --dim: #5b6670; --line: #d8dde2; --bg: #fbfaf8; --card: #ffffff;
  --accent: #1f6f78; --warn: #9a4b16; --good: #2f6b3a;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ink: #e8e6e3; --dim: #9aa4ae; --line: #343a40; --bg: #15181b; --card: #1c2024;
    --accent: #6fc3cc; --warn: #e0945c; --good: #7fc08c;
  }
}
:root[data-theme="dark"] {
  --ink: #e8e6e3; --dim: #9aa4ae; --line: #343a40; --bg: #15181b; --card: #1c2024;
  --accent: #6fc3cc; --warn: #e0945c; --good: #7fc08c;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.55 ui-sans-serif, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
main { max-width: 62rem; margin: 0 auto; padding: 2rem 1.25rem 6rem; }
h1 { font-size: 1.5rem; margin: 0 0 .3rem; letter-spacing: -.01em; }
.sub { color: var(--dim); margin: 0 0 1.5rem; }
.caveat { background: var(--card); border: 1px solid var(--line);
  border-left: 3px solid var(--warn);
  padding: .9rem 1.1rem; margin: 0 0 1.5rem; border-radius: 3px; }
.caveat p { margin: .35rem 0; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr)); gap: .75rem;
  margin: 0 0 1.75rem; }
.stat { background: var(--card); border: 1px solid var(--line); border-radius: 3px;
  padding: .6rem .75rem; }
.stat b { display: block; font-size: 1.2rem; font-variant-numeric: tabular-nums; }
.stat span { color: var(--dim); font-size: .8rem; }
details { border-bottom: 1px solid var(--line); }
details > summary { cursor: pointer; padding: .5rem .25rem; list-style: none;
  display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; }
summary::-webkit-details-marker { display: none; }
summary:hover { background: var(--card); }
summary:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.id { font-family: ui-monospace, Menlo, monospace; font-size: .8rem; color: var(--dim); }
.n { font-variant-numeric: tabular-nums; font-weight: 600; }
.tag { font-size: .72rem; padding: .08rem .4rem; border-radius: 2px; border: 1px solid var(--line);
  color: var(--dim); white-space: nowrap; font-variant-numeric: tabular-nums; }
.tag.bad { color: var(--warn); border-color: var(--warn); }
.tag.ok { color: var(--good); border-color: var(--good); }
.tag.giant { color: var(--warn); border-color: var(--warn); font-weight: 600; }
.gist { color: var(--dim); font-size: .85rem; flex: 1 1 18rem; min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.body { padding: .25rem 0 .75rem 1.25rem; }
.members { columns: 2 18rem; column-gap: 1.5rem; font-size: .85rem; margin: .4rem 0 0;
  padding: 0; list-style: none; }
.members li { break-inside: avoid; color: var(--dim); padding: .05rem 0; }
.members li b { color: var(--ink); font-weight: 500; }
.hint { color: var(--dim); font-size: .8rem; margin: .3rem 0 .6rem; }
footer { color: var(--dim); font-size: .8rem; border-top: 1px solid var(--line);
  margin-top: 2.5rem; padding-top: 1rem; }
</style>
<main>
<h1>THEMA &middot; universe L &middot; @@BUILD@@</h1>
<p class="sub">@@N_THEMES@@ themes over the <b>@@N_LEAVES@@ atomic pathways</b>. Click any theme to
open it.</p>

<div class="caveat">
<p><b>Read these before the numbers.</b></p>
<p><b>The universe is not the 10,770.</b> It is the @@N_LEAVES@@ <i>atomic</i> pathways &mdash;
every curated summary (a pathway with at least one descendant in the universe) was removed before
building. Recall figures here are not comparable with any 10,770 number.</p>
<p><b>Themes are unnamed.</b> The namer has never been run on a universe-L build, so each theme is
shown by the member names nearest its centroid. Those are members, not a label.</p>
<p><b>support</b> is the share of 200 resampled runs holding a matching theme at Jaccard 0.70, the
build's own threshold. <b>s@0.5</b> is the same at Jaccard 0.50. A large gap means the theme recurs
in a slightly different form each run rather than being absent.</p>
<p><b>coh</b> is mean pairwise gene overlap against a <i>size-matched</i> random set. Below
@@COHERENT@@&times; a theme is not distinguishable from a random set of its size; those are
flagged.</p>
<p><b>The @@N_GIANTS@@ roots of @@GIANT@@+ members are flagged.</b> They are gene-incoherent
(@@GIANT_COH@@) while their children are not (median @@KID_COH@@&times;), and they share most of
their children with each other, so they read better as overlapping bags than as areas.</p>
</div>

<div class="stats">@@STAT_CARDS@@</div>
<p class="hint">Top level: @@N_ROOTS@@ roots, largest first. Shared children appear under more
than one root.</p>
<div id="tree"></div>
<footer>Built from <code>@@BUILD@@</code>. Generated by
<code>scripts/export_browse_leaves.py</code>; no network, no fetch, nothing tracked.</footer>
</main>
<script id="data" type="application/json">@@PAYLOAD@@</script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const fmt = n => n.toLocaleString();
const f3 = v => v === null || v === undefined ? "–" : v.toFixed(3);
const open = new Set();

function tags(k) {
  const s = D.nodes[k], out = [];
  out.push(`<span class="tag">support ${f3(s[1])}</span>`);
  out.push(`<span class="tag">s@0.5 ${f3(s[2])}</span>`);
  const coh = s[3];
  const cls = coh === null ? "" : (coh < D.coherent ? " bad" : " ok");
  out.push(`<span class="tag${cls}">coh ${coh === null ? "–" : coh.toFixed(1) + "×"}</span>`);
  if (D.giants.includes(k)) out.push(`<span class="tag giant">giant root</span>`);
  if (s[5].length > 1) out.push(`<span class="tag">${s[5].length} parents</span>`);
  return out.join("");
}

function render(k, depth) {
  const s = D.nodes[k];
  const kids = s[4], gist = D.gist[k] || "";
  const d = document.createElement("details");
  d.innerHTML = `<summary><span class="id">${k}</span>`
    + `<span class="n">${fmt(s[0])}</span>`
    + tags(k)
    + `<span class="gist">${gist}</span></summary>`
    + `<div class="body"></div>`;
  const body = d.querySelector(".body");
  let filled = false;
  d.addEventListener("toggle", () => {
    if (!d.open || filled) return;
    filled = true;
    if (kids.length) {
      const h = document.createElement("p");
      h.className = "hint";
      h.textContent = `${kids.length} direct ${kids.length === 1 ? "child" : "children"}`
        + (depth > 6 ? " (nesting deep; expand with care)" : "");
      body.appendChild(h);
      for (const c of kids) body.appendChild(render(c, depth + 1));
    }
    const ul = document.createElement("ul");
    ul.className = "members";
    const names = D.members[k].map(i => D.names[i]);
    ul.innerHTML = names.map(n => `<li>${n}</li>`).join("");
    const h2 = document.createElement("p");
    h2.className = "hint";
    h2.textContent = `${names.length} member pathways`;
    body.appendChild(h2);
    body.appendChild(ul);
  });
  return d;
}

const host = document.getElementById("tree");
for (const r of D.roots) host.appendChild(render(r, 0));
</script>
"""


def main(argv: list[str] | None = None) -> int:
    """Write the page."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--build-version", default=None,
                        help="the version directory the BUILD lives under, when it differs from "
                             "--version (which supplies the universe, vectors and trees). An "
                             "exclusion rebuild reads one universe and is written beside another")
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    path = (args.data / "ontology" / f"v{args.build_version}" / args.build
            if args.build_version else root / args.build)
    stats = json.loads(args.stats.read_text())["nodes"]
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)
    index_of = {k: i for i, k in enumerate(keys)}
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    names = {p.key: p.name for p in collection.pathways}

    members: dict[str, list[str]] = defaultdict(list)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].append(row["key"])
    parents: dict[str, set[str]] = defaultdict(set)
    children: dict[str, list[str]] = defaultdict(list)
    with (path / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
            children[row["parent"]].append(row["child"])

    sizes = {node: len(keys_) for node, keys_ in members.items()}
    roots = sorted((n for n in members if not parents.get(n)), key=lambda n: -sizes[n])
    giants = [n for n in roots if sizes[n] >= GIANT]
    kid_coh = [stats[c]["coherence_ratio"] for g in giants for c in children.get(g, [])
               if stats.get(c, {}).get("coherence_ratio")]
    kid_coh.sort()

    nodes = {
        node: [sizes[node], stats.get(node, {}).get("support"),
               stats.get(node, {}).get("support_at_0.5"),
               stats.get(node, {}).get("coherence_ratio"),
               sorted(children.get(node, []), key=lambda c: -sizes[c]),
               sorted(parents.get(node, []))]
        for node in members}
    payload = {
        "nodes": nodes,
        "members": {node: [index_of[k] for k in members[node]] for node in members},
        "names": [html.escape(names.get(k, k)) for k in keys],
        "gist": {node: html.escape("; ".join((stats.get(node, {}).get("nearest") or [])[:4]))
                 for node in members},
        "roots": roots, "giants": giants, "coherent": COHERENT,
    }
    cards = [
        ("themes", f"{len(members):,}"),
        ("atomic pathways", f"{len(keys):,}"),
        ("roots", f"{len(roots):,}"),
        ("giant roots", f"{len(giants)}"),
        ("themes 51-1000", f"{sum(1 for s in sizes.values() if 51 <= s <= 1000):,}"),
        ("multi-parent",
         f"{100 * sum(1 for n in members if len(parents.get(n, ())) > 1) / len(members):.0f}%"),
    ]
    # Placeholder replacement rather than str.format: the template carries CSS braces and JS
    # template literals, and .format() reads both as fields.
    fields = {
        "BUILD": html.escape(args.build), "N_THEMES": f"{len(members):,}",
        "N_LEAVES": f"{len(keys):,}", "N_ROOTS": f"{len(roots):,}",
        "N_GIANTS": str(len(giants)), "GIANT": f"{GIANT:,}", "COHERENT": f"{COHERENT:g}",
        "GIANT_COH": "&ndash;".join(
            f"{v:.1f}&times;" for v in (min(stats[g]["coherence_ratio"] for g in giants),
                                        max(stats[g]["coherence_ratio"] for g in giants))),
        "KID_COH": (f"{kid_coh[len(kid_coh) // 2]:.0f}" if kid_coh else "n/a"),
        "STAT_CARDS": "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
                              for k, v in cards),
        "PAYLOAD": json.dumps(payload, separators=(",", ":")),
    }
    page = PAGE
    for name, value in fields.items():
        page = page.replace(f"@@{name}@@", value)
    if "@@" in page:
        leftover = re.findall(r"@@[A-Z_]+@@", page)
        raise ValueError(f"unfilled placeholders in the page template: {sorted(set(leftover))}")
    destination = args.out or (path / "browse.html")
    destination.write_text(page, encoding="utf-8")
    print(f"  {len(members):,} themes, {len(keys):,} pathways -> {destination} "
          f"({destination.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
