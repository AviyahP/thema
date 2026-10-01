"""Write a self-contained local page for browsing a named build.

Not the landing page. ``export_landing.py`` renders the designed mockup against its DATA contract;
this is a working tool for reading a build -- the whole DAG, expandable, with every name, member and
caveat on the page. One file, no fetch, no server: ``file://`` blocks fetch, so the data is embedded.

Every number is labelled with the universe it came from. The build is a 1,850-pathway SUBSET of a
10,770 universe, and a page that says "808 themes" without saying that is a page that misleads.
Unnameable themes render as "unnamed umbrella" WITH their members: hiding them would hide the
finding that the largest theme in the build could not be named.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.data import descriptions as descriptions_table
from thema.data.pathways import PathwayCollection
from thema.ontology.universe import load_embedded


def main(argv: Sequence[str] | None = None) -> int:
    """Build the page."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--build", default="v0.2/recurrent_dag_consensus")
    parser.add_argument("--out", type=Path, default=Path("demo/browse.html"))
    args = parser.parse_args(argv)

    directory = args.data / "ontology" / args.build
    rows = list(csv.DictReader((directory / "nodes.tsv").open(encoding="utf-8"), delimiter="\t"))
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    parents = {r["node"]: [p for p in r["parents"].replace(",", " ").split() if p] for r in rows}
    support = {r["node"]: float(r["support"]) for r in rows}
    members = defaultdict(list)
    for row in csv.DictReader((directory / "members.tsv").open(encoding="utf-8"), delimiter="\t"):
        members[row["node"]].append((row["key"], float(row["inclusion"])))

    names = {}
    flags = {}
    for row in csv.DictReader(
        (args.data / "theme_names.tsv").open(encoding="utf-8"), delimiter="\t"
    ):
        if row["status"] != "current":
            continue
        node = row["example_node"]
        names[node] = row["name"] if row["nameable"] == "true" else None
        flags[node] = {"checks": row["checks_failed"], "why": row["rationale"][:400]}

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")

    embedded = load_embedded(args.data / "ontology" / args.build.split("/")[0],
                            args.data / "pathways.tsv")
    row_of = {k: i for i, k in enumerate(embedded.keys)}
    centred = embedded.vectors - embedded.vectors.mean(axis=0, keepdims=True)
    centred = centred / np.linalg.norm(centred, axis=1, keepdims=True)

    def cohesion(keys: Sequence[str]) -> float:
        idx = [row_of[k] for k in keys if k in row_of]
        if len(idx) < 2:
            return 1.0
        block = centred[idx]
        gram = block @ block.T
        count = len(idx)
        return float((gram.sum() - count) / (count * (count - 1)))

    children = defaultdict(list)
    for node, above in parents.items():
        for parent in above:
            children[parent].append(node)
    depth: dict[str, int] = {}

    def at(node: str) -> int:
        if node not in depth:
            above = parents[node]
            depth[node] = 0 if not above else 1 + max(at(p) for p in above)
        return depth[node]

    for node in parents:
        at(node)

    nodes = {}
    for node in parents:
        keys = [k for k, _i in members[node]]
        sources = Counter(by_key[k].source for k in keys if k in by_key)
        genes: set[str] = set()
        for k in keys:
            if k in by_key:
                genes |= by_key[k].genes
        nodes[node] = {
            "id": node,
            "name": names.get(node),
            "size": len(keys),
            "support": round(support[node], 3),
            "cohesion": round(cohesion(keys), 3),
            "depth": depth[node],
            "genes": len(genes),
            "parents": parents[node],
            "children": sorted(children.get(node, []), key=lambda c: -len(members[c])),
            "sources": dict(sources.most_common()),
            "checks": flags.get(node, {}).get("checks", ""),
            "why": flags.get(node, {}).get("why", "") if names.get(node) is None else "",
            "members": [
                {
                    "key": k,
                    "name": by_key[k].name if k in by_key else k,
                    "source": by_key[k].source if k in by_key else "?",
                    "inclusion": round(i, 2),
                    "genes": by_key[k].n_genes if k in by_key else 0,
                    "desc": texts.get(k, "")[:240],
                }
                for k, i in sorted(members[node], key=lambda p: -p[1])
            ],
        }

    roots = sorted((n for n in parents if not parents[n]), key=lambda n: -nodes[n]["size"])
    payload = {
        "nodes": nodes,
        "roots": roots,
        "stats": {
            "themes": len(nodes),
            "edges": sum(len(p) for p in parents.values()),
            "roots": len(roots),
            "embedded": manifest.get("n_embedded"),
            "universe": manifest.get("n_universe"),
            "excluded": manifest.get("n_excluded_no_genes"),
            "named": sum(1 for v in names.values() if v),
            "unnameable": sum(1 for v in names.values() if v is None),
            "failed_checks": sum(1 for f in flags.values() if f["checks"].strip()),
            "multi_parent": sum(1 for p in parents.values() if len(p) >= 2),
            "max_depth": max(depth.values()),
            "fdr": manifest.get("calibration", ""),
            "embedder": manifest.get("embedder", {}),
            "stray": manifest.get("consensus", {}).get("stray"),
            "jaccard": manifest.get("consensus", {}).get("jaccard"),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(PAGE.replace("__DATA__", json.dumps(payload)), encoding="utf-8")
    size = args.out.stat().st_size / 1e6
    print(f"  {len(nodes)} themes, {len(roots)} roots -> {args.out} ({size:.1f} MB)")
    return 0


PAGE = r"""<!doctype html>
<meta charset="utf-8">
<title>THEMA — 1,850-pathway subset</title>
<style>
:root{--bg:#fbfaf8;--fg:#1c1a17;--mut:#6b655c;--line:#e0dcd4;--acc:#7a5cff;--warn:#b4520a;
      --card:#fff;--chip:#f2efe9}
@media (prefers-color-scheme:dark){:root{--bg:#15140f;--fg:#ece8e0;--mut:#9a9388;--line:#2e2b25;
      --card:#1d1b16;--chip:#26231d;--acc:#a58cff;--warn:#e08c3a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
 font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:22px 26px 16px;border-bottom:1px solid var(--line)}
h1{margin:0 0 4px;font-size:19px;letter-spacing:-.01em}
.sub{color:var(--mut);font-size:13px}
.warn{margin:14px 26px 0;padding:11px 14px;border:1px solid var(--warn);border-radius:7px;
 background:color-mix(in srgb,var(--warn) 9%,transparent);font-size:13px;line-height:1.5}
.stats{display:flex;flex-wrap:wrap;gap:7px;padding:14px 26px}
.stat{background:var(--chip);border:1px solid var(--line);border-radius:6px;padding:5px 9px;font-size:12px}
.stat b{font-variant-numeric:tabular-nums}
main{display:grid;grid-template-columns:minmax(330px,1fr) minmax(360px,1.1fr);gap:0;
 align-items:start}
@media (max-width:900px){main{grid-template-columns:1fr}}
#tree{border-right:1px solid var(--line);padding:10px 8px 60px;max-height:78vh;overflow:auto}
#card{padding:16px 22px 60px;max-height:78vh;overflow:auto}
.row{display:flex;align-items:baseline;gap:7px;padding:3px 6px;border-radius:5px;cursor:pointer;
 font-size:13.5px}
.row:hover{background:var(--chip)}
.row.sel{background:color-mix(in srgb,var(--acc) 15%,transparent)}
.tw{width:13px;color:var(--mut);flex:none;font-size:11px}
.nm{flex:1;min-width:0}
.unnamed{color:var(--warn);font-style:italic}
.n{color:var(--mut);font-size:11.5px;font-variant-numeric:tabular-nums;flex:none}
.kids{margin-left:14px;border-left:1px solid var(--line);padding-left:3px}
.hide{display:none}
h2{margin:0 0 3px;font-size:17px;line-height:1.3}
.meta{color:var(--mut);font-size:12.5px;margin-bottom:12px}
.chip{display:inline-block;background:var(--chip);border:1px solid var(--line);border-radius:5px;
 padding:2px 7px;font-size:11.5px;margin:0 5px 5px 0}
.chip.bad{border-color:var(--warn);color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:6px}
th{text-align:left;color:var(--mut);font-weight:500;border-bottom:1px solid var(--line);
 padding:4px 6px;position:sticky;top:0;background:var(--bg)}
td{padding:4px 6px;border-bottom:1px solid var(--line);vertical-align:top}
td.i{font-variant-numeric:tabular-nums;color:var(--mut);white-space:nowrap}
.src{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.d{color:var(--mut);font-size:11.5px;display:block;margin-top:2px}
.sec{margin:16px 0 5px;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
a{color:var(--acc)}
input{width:100%;padding:7px 9px;margin-bottom:8px;border:1px solid var(--line);border-radius:6px;
 background:var(--card);color:var(--fg);font:inherit;font-size:13px}
</style>
<header>
  <h1>THEMA — the 1,850-pathway subset</h1>
  <div class="sub" id="sub"></div>
</header>
<div class="warn" id="caveat"></div>
<div class="stats" id="stats"></div>
<main>
  <div id="tree"><input id="q" placeholder="filter themes by name…"><div id="rows"></div></div>
  <div id="card"><p style="color:var(--mut)">Pick a theme on the left.</p></div>
</main>
<script>
const D = __DATA__;
const N = D.nodes, S = D.stats;
document.getElementById('sub').textContent =
  `${S.themes} themes over ${S.embedded.toLocaleString()} pathways — a SUBSET of the `
  + `${S.universe.toLocaleString()}-pathway universe. Not the THEMA ontology.`;
document.getElementById('caveat').innerHTML =
  `<b>Read this first.</b> Every figure on this page describes the <b>${S.embedded.toLocaleString()}-pathway `
  + `subset</b>, not the ${S.universe.toLocaleString()}-pathway universe. `
  + `<b>The names are generated and unverified:</b> in testing, a pathway was placed in its correct theme `
  + `about <b>45%</b> of the time from the name alone, and only <b>46%</b> of parent–child links were `
  + `recoverable from names. <b>"Frozen" covers the theme set and its nesting, not exact member lists</b> — `
  + `45% of themes match at ≥0.9 across subsample seeds, so a member list is not a fixed object. `
  + `Per-member uncertainty is the <i>inclusion</i> column. Enrichment is not computed.`;
const st = [
  ['themes', S.themes], ['roots', S.roots], ['edges', S.edges],
  ['named', S.named], ['unnameable', S.unnameable], ['failed a name check', S.failed_checks],
  ['multi-parent', S.multi_parent], ['max depth', S.max_depth],
  ['excluded, no genes', S.excluded],
];
document.getElementById('stats').innerHTML = st.map(([k,v])=>
  `<span class="stat">${k} <b>${v.toLocaleString()}</b></span>`).join('')
  + `<span class="stat">held-out FDR <b>0.0037</b></span>`
  + `<span class="stat">encoder <b>MedCPT</b></span>`
  + `<span class="stat">consensus <b>STRAY ${S.stray} / JACCARD ${S.jaccard}</b></span>`;

const label = n => n.name ? n.name : 'unnamed umbrella';
function rowHtml(id, depth){
  const n = N[id], kids = n.children.length;
  return `<div class="row" data-id="${id}" style="padding-left:${2+depth*2}px">`
    + `<span class="tw">${kids?'▸':''}</span>`
    + `<span class="nm ${n.name?'':'unnamed'}">${label(n)}</span>`
    + `<span class="n">${n.size}${kids?' · '+kids+'c':''}</span></div>`
    + (kids?`<div class="kids hide" data-kids="${id}"></div>`:'');
}
const rows = document.getElementById('rows');
rows.innerHTML = D.roots.map(r=>rowHtml(r,0)).join('');
rows.addEventListener('click', e=>{
  const row = e.target.closest('.row'); if(!row) return;
  const id = row.dataset.id, n = N[id];
  document.querySelectorAll('.row.sel').forEach(r=>r.classList.remove('sel'));
  row.classList.add('sel');
  show(id);
  const box = rows.querySelector(`[data-kids="${id}"]`);
  if(box){
    if(!box.dataset.done){
      const d = (parseInt(row.style.paddingLeft)-2)/2 + 1;
      box.innerHTML = n.children.map(c=>rowHtml(c,d)).join('');
      box.dataset.done = '1';
    }
    box.classList.toggle('hide');
    row.querySelector('.tw').textContent = box.classList.contains('hide') ? '▸' : '▾';
  }
});
document.getElementById('q').addEventListener('input', e=>{
  const q = e.target.value.toLowerCase().trim();
  if(!q){ rows.innerHTML = D.roots.map(r=>rowHtml(r,0)).join(''); return; }
  const hits = Object.keys(N).filter(id=>label(N[id]).toLowerCase().includes(q))
    .sort((a,b)=>N[b].size-N[a].size).slice(0,300);
  rows.innerHTML = hits.map(id=>rowHtml(id,0)).join('') ||
    '<p style="color:var(--mut);padding:8px">nothing matches.</p>';
});
function show(id){
  const n = N[id];
  const src = Object.entries(n.sources).map(([k,v])=>`${k} ${v}`).join(' · ');
  let h = `<h2 class="${n.name?'':'unnamed'}">${label(n)}</h2>`;
  h += `<div class="meta">${n.id} · depth ${n.depth} · <b>${n.size}</b> pathways · `
     + `${n.genes.toLocaleString()} genes · support ${n.support} · cohesion ${n.cohesion}</div>`;
  if(!n.name) h += `<div class="warn" style="margin:0 0 12px">`
     + `<b>The namer declined this theme.</b> Its members are shown in full below — nothing is hidden. `
     + `Stated reason: “${n.why}”</div>`;
  if(n.checks && n.checks.trim()) h += `<span class="chip bad">name failed: ${n.checks}</span>`;
  h += `<div>${src.split(' · ').map(s=>`<span class="chip">${s}</span>`).join('')}</div>`;
  if(n.parents.length){
    h += `<div class="sec">parents</div>` + n.parents.map(p=>
      `<span class="chip"><a href="#" data-go="${p}">${label(N[p])}</a> · ${N[p].size}</span>`).join('');
  }
  if(n.children.length){
    h += `<div class="sec">children (${n.children.length})</div>` + n.children.map(c=>
      `<span class="chip"><a href="#" data-go="${c}">${label(N[c])}</a> · ${N[c].size}</span>`).join('');
  }
  h += `<div class="sec">members (${n.size}) — inclusion is this member's uncertainty</div>`;
  h += `<table><tr><th>pathway</th><th>source</th><th>incl</th><th>genes</th></tr>`
     + n.members.map(m=>`<tr><td>${m.name}`
       + (m.desc?`<span class="d">${m.desc.slice(0,230)}${m.desc.length>230?'…':''}</span>`:'')
       + `</td><td class="src">${m.source}</td><td class="i">${m.inclusion}</td>`
       + `<td class="i">${m.genes}</td></tr>`).join('') + `</table>`;
  const card = document.getElementById('card');
  card.innerHTML = h; card.scrollTop = 0;
  card.querySelectorAll('[data-go]').forEach(a=>a.addEventListener('click', ev=>{
    ev.preventDefault(); show(a.dataset.go);
  }));
}
show(D.roots[0]);
</script>
"""

if __name__ == "__main__":
    raise SystemExit(main())
