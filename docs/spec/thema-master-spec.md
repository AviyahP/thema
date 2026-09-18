# THEMA — master specification for Claude Code

*18 Sep 2026. Status: **for the record.** Read it, log it in the repo (`docs/spec/`), and keep it in mind as we build. Nothing in it is a build instruction until Aviyah says so, section by section. Repo rules apply to everything here: never commit (Aviyah commits); no API spend without her explicit per-command approval; every writer obeys the no-overwrite convention in `DECISIONS.md`; dry runs write nothing.*

Files that accompany this spec:

- `demo/landing.html` — the landing-page mockup (Part C). Design and behaviour to follow; data inside it is illustrative.
- `demo/_stash/method-section.html` — the "How the hierarchy was built" section, removed from the landing page, for the separate methods page.
- `demo/_stash/tool-page-sections.html` — the input-tier cards and worked-example cards, removed from the landing page, for the tool page.

Contents:

- Part A — product shape, the input ladder, the analysis engine (§1–§5)
- Part B — ontology builders (`ward_tree`, `recurrent_dag`), output contract, tests, evaluation (§6–§16)
- Part C — landing page and demo handoff (§17–§20)
- Part D — sequencing and open decisions (§21–§22)

---

# Part A — product shape, inputs, analysis engine

## 1. What THEMA is

THEMA lays a user's enrichment or expression results over a **frozen, pre-built ontology** of ~10,800 pathways from Reactome, Gene Ontology BP, MSigDB Hallmark and the Blood Transcriptional Modules, grouped by the meaning of their descriptions rather than by gene overlap. Two things follow that no enrichment tool does:

1. Related biology scattered across pathways that read as unrelated is pulled into one theme (the NF-κB four on the landing page: all pairwise κ < 0.04, two pairs sharing no gene).
2. Because THEMA holds every pathway's gene list, it can say whether a second enriched pathway is a second observation or the same one again (the insulin three on the landing page).

The ontology is built before any experiment is analysed; a user's data is laid over it, never used to build it. That is what makes theme-level statistics valid rather than circular (`DECISIONS.md`, ontology-first reversal).

Two surfaces: the **landing page** (Part C) and the **tool page**, where a user supplies data and gets the overlay. Everything the tool computes is also available as a Python function and a CLI for pipeline users.

## 2. The input ladder

THEMA takes whatever the user has and says **only what that input allows**. Each rung adds inputs and unlocks outputs. The tool always states which rung it is on and what the next rung would unlock, rendering anything it cannot compute as **not computed — <what would unlock it>**. Never a borrowed number.

| rung | user provides | THEMA computes | THEMA renders as "not computed" |
|---|---|---|---|
| **0** | a pathway table: names/ids + p-values (possibly thresholded) | themes the hits fall into; hits that are *provably* redundant (one annotation set nested in another); count of independent hits per theme | everything statistical |
| **1** | + the gene column (DE genes overlapping each pathway) | distinct genes supporting each theme (gene-level de-duplication of evidence) | theme significance |
| **2** | + the **full, unthresholded** table run over THEMA's own gene sets, + universe size N, + hit-list size k | BASIS at every node; CHILD-UNIQUE and PARENT-BEYOND per (child, parent) edge; effect sizes; BH or BY FDR | empirical-FDR audit |
| **3** | the DE gene list and the **universe** (list of measured genes) | everything in rung 2, plus the empirical-FDR audit; THEMA runs the enrichment itself | — |
| **3r** | a **ranked** list of all measured genes with scores | rank-based test (fgsea machinery) at every node, attribution, FDR — the GSEA user's rung 3 | — |

Why rung 2 is exact (derivation, keep it in the docs): every test in the protocol is a hypergeometric on a gene set S built from the ontology alone, needing |S|, |DE ∩ S|, N, k. With gene identities per pathway, DE ∩ genes(c) = ∪ hit(P) over members; DE ∩ unique(T) = hit(T) minus ∪ hit(siblings); the same for the leftover. Only the empirical-FDR audit needs the universe's *identities* (to draw random gene lists from it), hence rung 3.

Two conditions for rung 2, stated on the tool page:

- **Coverage.** The table must have a row for every pathway in THEMA's collection, significant or not. THEMA publishes its gene sets as `thema.gmt` (versioned with the ontology) so any ORA pipeline can run on exactly that collection and export the full table.
- **Gene-column semantics.** The column must be DE ∩ pathway, not a GSEA leading edge. GSEA users take rung 3r.

Rung 0 is the CytoReason v1 use case — organisation, not inference — and is legitimate on its own terms; it must never display a theme p-value.

## 3. Analysis engine — modular by design

Same pattern as the ontology builders (Part B): method is a parameter; THEMA's contribution is what happens across the DAG.

### 3.1 Interfaces

```python
# src/thema/analysis/engine.py
class EnrichmentTest(Protocol):
    name: str                       # "ora_hypergeom" | "rank_fgsea"
    def node_test(self, node_genes: set[str], data: Input) -> TestResult: ...   # p, effect, n_overlap...

class FdrMethod(Protocol):
    name: str                       # "bh" | "by" | "empirical"
    def adjust(self, pvals: np.ndarray, family: str, ctx: Context) -> np.ndarray: ...

@dataclass
class Input:
    rung: int                       # 0..3, or "3r"
    table: pd.DataFrame | None      # rungs 0-2
    hits: set[str] | None           # rung 3
    universe: set[str] | None       # rung 3
    N: int | None; k: int | None    # rung 2 (derived on rung 3)
    ranked: pd.Series | None        # rung 3r
```

Registry: `TESTS = {"ora_hypergeom": ..., "rank_fgsea": ...}`, `FDR = {"bh": ..., "by": ..., "empirical": ...}`. CLI: `thema overlay --ontology v0.1/ward_tree --test ora_hypergeom --fdr bh input.tsv`. The engine refuses combinations that are not valid for the rung (e.g. any test on rung 0; `empirical` below rung 3) with a message that names the missing input.

### 3.2 The three-test protocol, on any DAG

Definitions are unchanged from `DECISIONS.md` ("Hierarchical reporting protocol"); this only fixes how they run on a structure where a node may have several parents.

- **BASIS** — every node, on all its genes; no significance-gated descent; one BH family across all basis tests (BY as the guaranteed switch).
- **CHILD-UNIQUE** — per (child, parent) edge: child tested on genes in no sibling *under that parent*; siblings are the parent's other children. A child with two parents is tested once per parent; both results are reported.
- **PARENT-BEYOND** — per parent: parent tested on genes in its non-significant children only (leftover after removing genes unique to significant children under that parent).
- Attribution p-values get their own per-layer BH; effect sizes are mandatory beside every attribution test; attribution never gates basis significance.
- **Shared-member note.** When two co-significant nodes share members, report the shared members and each node's BASIS recomputed on its genes minus the other's. A tool built to stop double counting must not reintroduce it at theme level.

### 3.3 FDR modes

- `bh` — default; validity under the nested dependence is unproven (PRDS not established) but field standard.
- `by` — guaranteed under arbitrary dependence, ~ln m power cost.
- `empirical` — random gene lists of matched size drawn from the universe, run through the whole DAG (~10³ draws); reports realised FDP at the chosen threshold; serves as the audit of BH. Requires rung 3.

### 3.4 The universe rule

Never borrowed, never assumed. Rung 2 takes N and k as user-supplied numbers; rung 3 takes the list. If absent, the affected outputs render as not computed. This is `DECISIONS.md` policy and is not negotiable in code paths.

### 3.5 "Your numbers reproduce" panel

On rungs 2 and 3, THEMA recomputes every *pathway-level* p-value from the same inputs and shows them beside the user's own. Agreement makes the theme layer credible; disagreement is almost always the universe, and the panel says so. This is cheap and is the single most trust-building display in the tool.

## 4. Analysis output contract

```json
{
  "manifest": { "ontology": "v0.1/ward_tree", "test": "ora_hypergeom", "fdr": "bh",
                "rung": 2, "N": 16826, "k": 412, "date": "...", "hash": "..." },
  "nodes": [
    { "id": "n0412", "basis": { "p": 1.2e-6, "q": 4.8e-5, "fold": 2.7, "overlap": 38, "size": 517,
                                "status": "computed" },
      "parent_beyond": { "status": "not computed", "needs": "rung 2" } }
  ],
  "edges": [
    { "child": "n0412", "parent": "n0077",
      "child_unique": { "p": 0.03, "q": 0.11, "fold": 1.9, "overlap": 9, "size": 61, "status": "computed" } }
  ],
  "pathways": [ { "key": "go:GO:0030073", "user_p": 3e-4, "thema_p": 3.1e-4, "in_nodes": ["n0412"] } ],
  "shared": [ { "a": "n0412", "b": "n0388", "members": ["..."], "a_minus_b_p": 0.002, "b_minus_a_p": 0.4 } ],
  "unplaced_hits": ["..."]
}
```

Every statistic carries `status` = `computed` | `not computed` with `needs`. The demo renders `not computed` literally, with the reason.

## 5. Worked examples

Three published contrasts with known answers (the placeholders in the stashed tool-page section): an autoimmune whole-blood contrast (one signature described by all four databases — the collapse is visible), an infection-severity contrast (innate up, adaptive down — direction at theme level), a tumour-versus-normal contrast (the obvious answer; a tool that misses it is not trusted on a subtle one). Each ships with the DE list and its measured universe (rung 3), so the full output is demonstrable. Dataset choice is Aviyah's; Claude Code proposes candidates with GEO accessions and universe availability.

---

# Part B — ontology builders

*Originally `claude/thema-ontology-builders-spec.md`; design rationale and method survey in `claude/thema-soft-membership-plan.md`.*

## 6. What this builds

THEMA's ontology — the structure a user's enrichment is laid over — becomes **pluggable**. The way the hierarchy is built is a parameter. Two builders ship now, with the same inputs and the same output contract, so the demo can load either and the user can toggle between them:

| method id | what it is | structure |
|---|---|---|
| `ward_tree` | the current build: Ward on L2-normalised embeddings, cut at declared levels | tree, one parent per node |
| `recurrent_dag` | Ward on 100 resampled runs; groupings that recur are the nodes; ordered by containment | DAG, multiple parents allowed, no fixed levels |

The demo stays on `ward_tree` until `recurrent_dag` passes §14. Nothing in this spec touches descriptions, naming, or the statistics protocol's definitions.

---

## 7. Architecture

### 1.1 Interface

```python
# src/thema/ontology/base.py
class OntologyBuilder(Protocol):
    method: str                                  # "ward_tree" | "recurrent_dag"
    def build(self, X: np.ndarray, keys: list[str], params: dict, seed: int) -> Ontology: ...

@dataclass
class Ontology:
    method: str
    params: dict                                 # every parameter, frozen
    nodes: list[Node]                            # id, parents[], members[], support
    unplaced: list[str]                          # pathway keys in no node of ≥ min_size
    manifest: dict                               # embedder, revision, n, seeds, hashes, date
```

`Node.members` is a list of `(key, inclusion)`; `inclusion` is 1.0 for every member under `ward_tree`. `Node.support` is 1.0 under `ward_tree`.

### 1.2 Registry and CLI

```
src/thema/ontology/registry.py      BUILDERS = {"ward_tree": WardTree, "recurrent_dag": RecurrentDag}
scripts/build_ontology.py --method recurrent_dag --version 0.2 [--dry-run] [--params params.yaml]
```

Output goes to `data/ontology/v<version>/<method>/` — the two builders never write to the same directory. Each directory holds `nodes.tsv`, `members.tsv`, `edges.tsv`, `unplaced.tsv`, `manifest.json`, and `ontology.json` (§8). All writes through `merge_tsv` with the key columns given in §8.

### 1.3 Shared post-processing (method-independent)

After any builder returns an `Ontology`:

1. **Gene unions.** `genes(node)` = ∪ gene symbols over members. Stored as counts in `nodes.tsv` and as lists in `ontology.json`.
2. **Gene support** for every member with `inclusion < 1`: the highest overlap coefficient between the pathway's genes and any member with `inclusion == 1` of that node. Annotation only; never a filter (THEMA's thesis includes groupings that share no genes).
3. **Invariant checks** (fail the build, never warn):
   - the edge relation is acyclic;
   - every edge (child, parent) satisfies members(child) ⊆ members(parent);
   - every node has ≥ `min_size` members;
   - every pathway is in ≥ 1 node or in `unplaced`;
   - under `ward_tree`, every node has exactly one parent or is the single root.
4. **Export** `ontology.json` (§8).

---

## 8. Output contract

Identical for every method. This is what the demo loads.

```json
{
  "manifest": {
    "method": "recurrent_dag", "version": "0.2", "date": "2026-09-18",
    "embedders": ["BioLORD-2023@<rev>"], "n_pathways": 1854,
    "params": { "...": "every builder parameter, see §9/§4" },
    "seeds": "sha256 of the seed list", "hash": "sha256 of nodes+members+edges"
  },
  "nodes": [
    { "id": "n0412", "parents": ["n0077", "n0102"], "label": null, "provisional": true,
      "support": 0.62, "n_members": 23, "n_genes": 517,
      "members": [ { "key": "go:GO:0030073", "inclusion": 1.0 },
                   { "key": "reactome:R-HSA-422356", "inclusion": 0.71, "gene_support": 0.22 } ],
      "genes": ["..."] }
  ],
  "pathways": [
    { "key": "go:GO:0030073", "source": "go", "sid": "GO:0030073", "name": "insulin secretion",
      "n_genes": 204,
      "memberships": [ { "node": "n0412", "inclusion": 1.0 },
                       { "node": "n0388", "inclusion": 0.84, "gene_support": 0.09 } ] }
  ],
  "unplaced": ["btm:M9.99"]
}
```

TSV keys for `merge_tsv`: `nodes.tsv` on `id`; `members.tsv` on `(key, node)`; `edges.tsv` on `(child, parent)`; `unplaced.tsv` on `key`. Columns: `nodes.tsv` = id, support, n_members, n_genes, label, provisional; `members.tsv` = key, node, inclusion, gene_support; `edges.tsv` = child, parent.

Rules: `parents` is a list (may be empty — a root); there is no level field; `label` is null until naming runs; membership is binary and `inclusion`/`support` are annotations; `ward_tree` is the special case with every list of length one, every `inclusion` 1.0, every `support` 1.0, one root.

---

## 9. Method A — `ward_tree`

The existing build, expressed through the interface. Do not change its numbers; this is a re-export.

1. Inputs: `X` (n × d, L2-normalised), `keys`, params `{levels: [10, 25, 50, 100, 200]}`.
2. `scipy.cluster.hierarchy.linkage(X, method="ward")` on Euclidean distance of unit vectors (‖a−b‖² = 2 − 2·cos, as recorded in `DECISIONS.md`).
3. For each k in `levels`, `fcluster(Z, k, criterion="maxclust")` gives a partition. Every cluster at every level is a node: id `k<k>:<c>`.
4. Parent of a node at level k = the node at the previous level in `levels` that contains it (unique, because cuts of one dendrogram nest). Nodes at the first level have parent = the root node `root` whose members are all pathways.
5. Members = the cluster; `inclusion` = 1.0; `support` = 1.0. `unplaced` = [] (every pathway is somewhere).
6. `min_size` is not applied to this method (its clusters are whatever the cut gives); record that in the manifest.

Done when: the export reproduces `data/ontology/clusters_ward.tsv` exactly (same member sets per level) and the demo renders it unchanged.

No softening in this method. A softened variant (`ward_tree_soft`) is a possible third builder later; it is deliberately not in v1 so the toggle compares one idea against one idea.

---

## 10. Method B — `recurrent_dag`

### 4.1 Inputs and parameters

- `X` (n × d, L2-normalised), `keys`. Optionally a second matrix `X2` from a second embedder (§10.9).
- `params`:

| name | default | meaning |
|---|---|---|
| `runs` | 100 | number of resampled runs |
| `subsample` | 0.80 | fraction of pathways per run |
| `min_size` | 5 | smallest grouping that counts |
| `min_shared` | 3 | a run is eligible to judge grouping g only if it had ≥ this many of g's members |
| `tol` | 0.0 | extra shared members allowed, as a fraction of g's shared size (§10.4) |
| `m` | set from null (§10.6) | support threshold; must be < 0.5 |
| `inclusion_threshold` | 0.5 | majority inclusion for membership (§10.7) |
| `embedder_split` | false | half the runs on `X2` (§10.9) |
| `seed` | recorded | master seed; per-run seeds derived and stored |

### 4.2 Runs

For r in 1..runs: draw S_r, a uniformly random subset of ⌈subsample·n⌉ pathways (seeded). Ward on `X[S_r]` as in §9.2. Record:

- `present[r]`: bitset over all n pathways, 1 where in S_r;
- `clusters[r]`: every internal node of the dendrogram with ≥ `min_size` members, as a bitset over all n (bits only inside S_r), plus for each cluster its parent cluster index (the merge above it) so ancestor walks are possible;
- `leaf_cluster[r][p]`: for each pathway p in S_r, the smallest recorded cluster containing p (or none).

Bitsets: `numpy` `uint64` arrays of length ⌈n/64⌉; popcount via `np.unpackbits` or a lookup; at n = 10,817 that is 170 words per set.

### 4.3 The grouping pool

Every `(r, c)` with c in `clusters[r]` is a candidate grouping g with member bitset `B_g` and origin run r. Before scoring, **deduplicate exact duplicates within the pool**: identical bitsets from different runs are the same grouping (this happens for stable clusters whose members were all present in both runs); keep one, remember its origin runs. This alone removes most of the pool for stable structure.

### 4.4 "Found in run s" — the matching rule

For grouping g (origin r) and any run s ≠ r:

```
shared  = present[r] & present[s]
g_s     = B_g & present[s]                      # g's members that run s had
if popcount(g_s) < min_shared: run s is not eligible for g; skip
D       = smallest cluster in clusters[s] with g_s ⊆ D
          # walk up from leaf_cluster[s][p] for any p in g_s until the cluster contains all of g_s;
          # clusters on one root path are nested, so the first superset is the smallest
if no such D (g_s not inside any recorded cluster): not found
extra   = popcount(D & shared) - popcount(g_s)   # shared members D has that g lacks
found   = extra <= tol * popcount(g_s)
```

Members that run r never had (not in `shared`) do not count either way. `tol = 0` is exact-on-shared. Record `copy(g, s) = D` when found; it is needed in §10.7.

For g's own origin run(s), found = true by definition.

### 4.5 Support

```
eligible(g) = { s : popcount(B_g & present[s]) >= min_shared }
support(g)  = |{ s in eligible(g) : found(g, s) }| / |eligible(g)|
```

If `|eligible(g)| < runs / 2`, mark g not evaluable (it happens only for tiny groupings) and drop it.

### 4.6 The threshold m, from a null

`m` must be below 0.5: two groupings each found in a majority of runs co-occur in some run, where they are clusters of one Ward tree and therefore nested or disjoint — majority rule can only produce a tree. Overlap lives below 0.5.

Null: permute each embedding dimension independently across pathways (structure destroyed, marginal geometry kept); run §10.2–4.5 once with the same seeds; `null_max` = highest support reached by any grouping of ≥ `min_size` members. Set `m = max(0.20, 3 × null_max)` and record both numbers. Also produce the ontology at m ∈ {0.25, 0.33, 0.50} for §14; the 0.50 output is the consensus tree and is the honest comparison against `ward_tree`.

### 4.7 Nodes — merging copies (seed absorption)

Robust groupings: `support ≥ m`. The same underlying grouping appears as many robust copies (one per run that found it). Merge them without chaining:

1. Sort robust groupings by support desc, then size desc, then a stable hash of the bitset.
2. Take the top unconsumed grouping as **seed**. Its node = seed ∪ { copy(seed, s) for every s where found }. Mark all consumed.
3. Repeat until nothing is unconsumed.

Do **not** use connected components of the "found" relation: with `tol > 0` it chains and one node swallows a ladder of distinct groupings.

Members: for each pathway p,

```
inclusion(p) = #(copies of the node containing p) / #(copies from runs where p was present)
member iff inclusion(p) >= inclusion_threshold
```

Do **not** take the union of copies as membership: with `tol > 0` each copy can carry a different extra member and the union bloats by up to `tol` again. Node `support` = the seed's support. Nodes whose member sets come out identical are merged, keeping the higher support. Nodes with fewer than `min_size` members after the inclusion rule are dropped.

### 4.8 Edges — containment order

A is a parent of B iff members(B) ⊂ members(A) (strict) and no node C has members(B) ⊂ members(C) ⊂ members(A). This is the Hasse diagram of the node set; it is acyclic by construction (strict inclusion is a strict partial order) — assert it anyway. Nodes with no parent are roots; there may be several; **no artificial root is added.** Multiple parents arise wherever two nodes overlap without either containing the other.

Implementation: sort nodes by size descending; for each node B, candidates A are larger nodes with `B & A == B`; keep the minimal ones (remove any candidate that contains another candidate). With ~1–3k nodes this is a few million bitset ops.

`unplaced` = pathways in no node.

### 4.9 Optional second embedder

If `embedder_split`, runs alternate between `X` and `X2` (same S_r draw discipline, separate seeds). Everything else is unchanged; a grouping must then recur across representations as well as across samples. Recommended, decided by Aviyah before the run, recorded in the manifest.

### 4.10 Complexity

Pool size ≈ runs × (clusters per run) ≈ 100 × ~900 at n = 1,854 before dedup; each grouping is judged against ≤ 99 runs with one ancestor walk each. Python-level loops over ~10⁷ (grouping, run) pairs are minutes with numpy bitsets; at n = 10,817 (pool ~5×10⁵ before dedup) use `numba` for §10.4 or it will take hours. Dedup (§10.3) first — it is the biggest saving.

---

## 11. Plain-language notes (shown in the demo beside the toggle)

**ward_tree.** "Every pathway is placed once, by hierarchical clustering of its description. Themes nest inside broader themes. A pathway has one home."

**recurrent_dag.** "The clustering was repeated 100 times on random 80% samples of the pathways. A theme exists only if the same grouping came back in at least m of the runs; the number beside each theme is how often. Where the runs kept disagreeing about which of two themes a pathway belongs to, it is in both. Themes can have more than one parent."

---

## 12. Demo integration

- Loader reads `ontology.json` for the selected method; a toggle in the explorer toolbar switches methods and re-renders. Both files ship with the page.
- Rendering rules already in the explorer: a node with several parents appears under each; a member with `inclusion < 1` shows its number; the node card shows `support`; roots render as a forest (no synthetic "All themes" row); `unplaced` pathways are listed under a final "Not placed" heading, never hidden.
- The theme chips on the landing page (NF-κB four, insulin three) are computed from `ward_tree` today; when `recurrent_dag` passes §14, recompute them for both and show the method beside the chip.

---

## 13. Tests (toy fixtures, all in `tests/ontology/`)

1. **Two stable groups + one straddler + noise.** 40 points: two tight clusters of 15, one point equidistant between them, 9 uniform noise points. `recurrent_dag` must return exactly two nodes, the straddler in both with `inclusion < 1` in each, noise in `unplaced`. `ward_tree` must return the straddler in exactly one.
2. **Compatibility.** With `m = 0.5` on fixture 1, the output must be a tree (no node with two parents).
3. **Matching rule.** Hand-built two runs with known present sets; assert found/not-found for the cases: member missing from one run (found), extra shared member at `tol = 0` (not found), same at `tol = 0.2` (found), fewer than `min_shared` shared (ineligible).
4. **No chaining.** Three groupings g₁, g₂, g₃ where g₁~g₂ and g₂~g₃ within tol but g₁≁g₃: seed absorption must produce two nodes, not one.
5. **Invariants.** Every build passes §7.3 checks; `ward_tree` export equals `clusters_ward.tsv`.
6. **Idempotence.** Two builds from the same seeds produce byte-identical TSVs; a dry run writes nothing.

---

## 14. Evaluation and go/no-go for `recurrent_dag`

On the 1,854 smoke build, at each m in {chosen, 0.25, 0.33, 0.50}:

1. **Fragmentation at `tol = 0`:** histogram of support over the pool. If mass sits just under m in ladders, try `tol` 0.05 and 0.10 and record the value chosen and why.
2. **Independent validation with gene overlap:** for members with `inclusion < 1`, Jaccard(pathway genes, genes of the node's `inclusion == 1` members); compare against settled members and random non-members. **Go** if contested sits between the two with a clear gap from random (medians, Mann–Whitney p). **No-go** if contested ≈ random.
3. **Existing evals:** ancestor-pair F1 vs Reactome/GO; reactome2go recovery — for both methods. `recurrent_dag` should not lose.
4. **Shape:** nodes, roots, depth distribution, fraction of pathways in ≥ 2 nodes, nodes with ≥ 2 parents, `unplaced` count, `null_max` beside m.
5. **Cross-check:** restrict 20 runs to their common pathways, export as Newick, `phangorn::consensusNet` at the same m; the split network should carry the same overlaps on that set. One figure.
6. **Hand inspection:** every node with two parents and 20 contested members at random, both nodes' member lists printed. Aviyah judges; Claude Code does not.

Go = 2 passes and 3 does not regress. Then v0.2 is frozen and `DECISIONS.md` gets the entry with the numbers.

---

## 15. Build order, each with a done-condition

1. `src/thema/ontology/{base,registry}.py` and the `ward_tree` builder + export. **Done when** §3's done-condition holds and the demo loads `ontology.json` instead of the mock `DATA`.
2. `src/thema/ontology/recurrent.py` — §10.2–4.8. **Done when** tests 1–4 pass.
3. `scripts/build_ontology.py` with `--dry-run`, `--method`, `--version`, `--params`; null run as `--null`. **Done when** tests 5–6 pass and a real build on the smoke set writes v0.2 under both methods.
4. `scripts/eval_ontology.py` — §14 items 1–4 to `data/experiments/ontology_eval.tsv` under the no-overwrite convention. **Done when** the numbers and the two plots exist.
5. Demo toggle (§12). **Done when** both ontologies render from their JSON and the toggle switches without reload.
6. §14.5 cross-check and §14.6 sample for Aviyah.
7. Draft the `DECISIONS.md` entry; Aviyah decides and commits.

Cost: zero API. CPU: minutes on 1,854; about an hour on 10,817 with numba.

---

## 16. Decisions Aviyah makes, not Claude Code

- `embedder_split` on or off for v0.2.
- `tol` after reading §14.1.
- Which m is the shipped default after reading §14.4.
- Whether the landing page's "ten broad themes" survives contact with the DAG's actual roots.

---

# Part C — landing page and demo handoff

## 17. Files and what is real in them

`demo/landing.html` is the design mockup, published and iterated with Aviyah. It is the reference for layout, typography, colour, copy and interaction. Treat it as **design truth and data fiction**:

- **Real:** the two example cards (the NF-κB four; the insulin three) — those pathways cluster together in the current 1,854-pathway build and every number on them was verified against `clusters_ward.tsv` and `pathways.tsv`.
- **Illustrative:** everything in the explorer — theme labels (naming has not run), member counts, gene-union counts, the one secondary membership on the GO interferon pathway, and the `DATA` constant in the script. Replace it with the exported ontology; do not "fix" the numbers by hand.
- **Placeholders:** the two buttons in the call to action link to `#`; the "Learn how the THEMA ontology was built" link goes to `#` (that page is built from `demo/_stash/method-section.html`).

The mockup banner at the top of the page (`.mock`) says exactly this. It is removed only when every illustrative element has been replaced with real data.

## 18. Design system (source of truth: the `:root` block in `landing.html`)

- **Typefaces carry meaning.** Source Serif 4 = machine-written prose and theme names; IBM Plex Mono = any measured or counted value (p-values, gene counts, identifiers, support); IBM Plex Sans = interface chrome and explanatory text. Do not mix them.
- **Colour carries meaning.** Deep teal `--accent` (#0D6B66 light / #4FB5AC dark) is the interface accent — selection, links, the theme chip — and is **never used to encode data**. `--up` brick-oxide = enriched/up; `--down` steel-blue = depleted/down; `--flag` amber = abstention, provisional, or not-computed. Source colours: `--reactome` purple, `--go` green, `--hallmark` amber-brown, `--btm` steel-blue — used only for source badges and the composition bar.
- **Light and dark** are both defined; every new element must define both. The page is built at phone width upward; no horizontal scroll at any width.
- **Honesty markers.** Anything uncomputed renders as text ("not computed — needs …") in `--flag`, never as a blank or a zero. Provisional labels carry the amber `provisional` chip.

## 19. Page structure to preserve

1. Masthead — mark, expansion, build line (ontology version, n of 10,817, source versions). The build line is generated from the ontology manifest, never typed.
2. Headline with the marker swipe on "couldn't make sense of".
3. The two example cards, hover swaps content for explanation without changing size. Their numbers come from a script over the ontology + `pathways.tsv`; when the ontology changes (v0.2), recompute and show the method beside the chip.
4. Three intro paragraphs (approved copy — do not edit without Aviyah) and the method-page link.
5. **Explore the ontology** — toolbar (search, collapse all, count, legend), the unfolding tree with dendrogram connectors, the sticky detail card. Rules already implemented in the script and to be kept when wiring real data: branches stay open beside siblings; rows show pathways + gene-union counts for themes and source badge + gene count for pathways; pathway lists show 8 then "Show all N"; a member in several nodes carries the "in N themes" chip and the card lists the others with navigation; a node with several parents appears under each; roots render as a forest; `unplaced` pathways appear under a final heading; the card is always shown whole (no internal scroll).
6. Call to action — one title, one line, two buttons (own data / worked example) → tool page.
7. Footer and the "Report a problem" sheet — every theme and pathway card carries the report control; the sheet is not wired to a backend yet and says so.

Removed from the landing page by decision (kept in `_stash/`): "What you can give it" (→ tool page, as the input ladder), "Worked examples" (→ tool page), "How the hierarchy was built" (→ methods page).

## 20. Wiring order for the demo

1. Export `ontology.json` for `ward_tree` from the current build (Part B §8, §15 step 1). Swap the mock `DATA` for a fetch of that file. Everything renders; labels remain `null` → the tree shows the provisional placeholder text until naming runs.
2. Recompute the two example cards' numbers from the export; assert they match the verified values before publishing.
3. Tool page: the ladder (§2) as the input form with rung detection stated on screen; the stashed tier cards become the ladder's explanation; the three worked examples as buttons that preload rung-3 inputs.
4. Rung 0–1 overlay on the tree (organisation only), then rung 2–3 with BASIS + BH and attribution as they land, each statistic rendered with its `status`.
5. Ontology method toggle once `recurrent_dag` passes Part B §14.

---

# Part D — sequencing and decisions

## 21. Order of work (not authorised yet; for planning)

1. Complete v4 descriptions for the 1,854 (after the status check; Aviyah approves each `--submit`).
2. `ward_tree` export + landing page on real data (Part C §19 steps 1–2).
3. Tool page with rung 0–1 (no statistics) and the ladder stated honestly.
4. Analysis engine: `ora_hypergeom` + `bh`, BASIS only; then attribution per edge; then `by` and `empirical`; then `rank_fgsea`.
5. Submit the 10,817 descriptions as a batch as soon as the prompt is confirmed frozen — independent of everything above.
6. `recurrent_dag` builder, evaluation, go/no-go, toggle.
7. Naming run (LLM, with abstention) only on the ontology version that is going to ship.

## 22. Decisions that are Aviyah's

- Which worked-example datasets.
- `embedder_split` for `recurrent_dag`; `tol`; the shipped m.
- Whether "ten broad themes" survives contact with the DAG's real roots.
- Default `fdr` mode shown to users (recommendation: `bh` with `empirical` reported beside it when available).
- The name shown for rung 0 on the tool page (recommendation: "organise existing results").
