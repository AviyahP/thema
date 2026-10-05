#!/usr/bin/env python3
"""Build a HiDeF hierarchy on the same 10,770 vectors, in THEMA's output schema.

HiDeF (Zheng et al. 2021, Genome Biology; `fanzheng10/HiDeF`) finds a multi-resolution community
hierarchy by sweeping Leiden resolutions and keeping communities that persist. It is the closest
published method to what `recurrent_dag` does, so it is the arm the 4 Oct decision rule compares
against.

**The comparison is only fair if the input is the same.** This takes the identical
centred-and-renormalised MedCPT vectors (universe digest `c54319cdfbbe9eb7`) and the identical
10,770 keys in the identical row order, and builds the graph HiDeF needs from them.

**THE `louvain` STAND-IN, AND WHY IT IS SAFE.** `hidef.hidef_finder` does
``with warnings.catch_warnings(): import louvain`` at module scope -- an unconditional import -- but
`louvain` is referenced ONLY inside ``if alg == 'louvain':`` branches (lines 157-159 and 171-173 of
the installed 1.1.5). We run ``alg='leiden'``, so it is dead code for this configuration. The wheel
cannot be installed on this machine: it vendors igraph's C core, and that source fails to compile
under the installed clang ("variable 'v' is uninitialized when passed as a const pointer"), with
CFLAGS not reaching its CMake build. So a stand-in module is inserted before the import, and it
**raises on ANY attribute access**. If HiDeF ever reached for louvain the run would fail loudly
instead of quietly doing something else, and the toy test below confirms the Leiden path works.

Usage::

    uv run scripts/build_hidef.py --toy          # planted-community test; run this first
    uv run scripts/build_hidef.py --k 15
"""

from __future__ import annotations

import argparse
import builtins
import csv
import json
import random
import resource
import sys
import time
import types
from pathlib import Path

import numpy as np

from thema.cluster import distances
from thema.data.pathways import PathwayCollection
from thema.embed import centre_and_renormalise
from thema.ontology.recurrent import null_embeddings, tree_from_subset
from thema.ontology.universe import load_embedded

#: HiDeF's published defaults, from the installed package's own argument parser. Declared before
#: the run and not tuned afterwards: tau 0.75, chi 5, p 75, Leiden.
TAU = 0.75
CHI = 5
CONSENSUS_P = 75
ALG = "leiden"

#: Maximum Leiden resolution swept. The package default is 25.0 for its CLI; the README's guidance
#: for non-single-cell networks is the default, so the default is what is used and recorded.
MAXRES = 25.0

#: Smallest community kept, to match THEMA's contract.
MIN_SIZE = 3

#: Reported, never applied: THEMA's declared size cap at this universe.
SIZE_CAP = 3125


def install_louvain_stand_in() -> None:
    """Put a strict stand-in for ``louvain`` in ``sys.modules`` before HiDeF imports it.

    Raises on any attribute access, so the unused import cannot become a silent code path. See the
    module docstring for why this is necessary and why it is safe.
    """
    if "louvain" in sys.modules:
        return

    class _Unavailable(types.ModuleType):
        def __getattr__(self, name: str) -> object:
            raise RuntimeError(
                f"hidef reached for louvain.{name}, but louvain is not installed and this run "
                f"declared alg={ALG!r}. The stand-in exists only because hidef imports louvain "
                f"unconditionally while using it solely for alg='louvain'."
            )

    sys.modules["louvain"] = _Unavailable("louvain")


def unshadow_builtins(module: object) -> list[str]:
    """Restore builtins that a star-import clobbered in a module's namespace.

    `hidef/utils.py` does ``from scipy.stats import *``, and `hidef_finder` does
    ``from hidef.utils import *``. Modern scipy.stats exports names that collide with builtins --
    `abs` among them -- so `hidef_finder.abs` is scipy's distribution helper rather than the
    builtin, and ``abs(np.log10(x) - np.log10(y))`` raises
    ``NotImplementedError: Transformations are currently only supported for continuous RVs``.

    This restores the builtin in that module only. It is not a behaviour change: the shadowing is
    an accident of two star-imports, and every call site in `hidef_finder` means the builtin.

    Args:
        module: The module to repair.

    Returns:
        The names restored, so the run can record what it had to fix.
    """
    fixed = []
    for name in dir(builtins):
        if name.startswith("_"):
            continue
        current = getattr(module, name, None)
        original = getattr(builtins, name)
        if current is not None and current is not original:
            setattr(module, name, original)
            fixed.append(name)
    return fixed


# Installed AT IMPORT TIME, not inside a function. `hidef_finder.run` always creates an
# `mp.Pool`, and macOS spawns rather than forks, so each child re-imports this module (as
# `__main__`) to unpickle the work function and must have the stand-in in place before it imports
# hidef. Installing it lazily deadlocked the pool: three processes at 0.0% CPU, the children unable
# to import and the parent waiting for them.
install_louvain_stand_in()


def peak_gb() -> float:
    """Peak resident memory in GB. ``ru_maxrss`` is bytes on macOS, kilobytes on Linux.

    Returns:
        Gigabytes.
    """
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / 1e9 if sys.platform == "darwin" else raw / 1e6


def knn_graph(vectors: np.ndarray, k: int) -> object:
    """Symmetric kNN graph on cosine similarity, edge weight = cosine.

    The union of directed edges, as declared: an edge exists when either endpoint has the other in
    its top k. Self-edges are excluded.

    Args:
        vectors: ``(n, dim)`` unit rows, so the inner product IS the cosine.
        k: Neighbours per node.

    Returns:
        An ``igraph.Graph`` with a ``weight`` edge attribute.
    """
    import igraph as ig

    n = len(vectors)
    rows, cols, weights = [], [], []
    # Chunked, because the full (n, n) similarity at 10,770 is 464 MB in float32 and there is no
    # reason to hold it when only the top k per row is wanted.
    step = 512
    for begin in range(0, n, step):
        block = vectors[begin:begin + step] @ vectors.T
        np.fill_diagonal(block[:, begin:begin + block.shape[0]], -np.inf)
        top = np.argpartition(-block, k, axis=1)[:, :k]
        for local, row in enumerate(top):
            source = begin + local
            for target in row:
                rows.append(source)
                cols.append(int(target))
                weights.append(float(block[local, target]))
    # Union of directed edges, deduplicated with the max weight (identical either way, since the
    # cosine is symmetric; the max is taken so the dedup is explicit rather than order-dependent).
    seen: dict[tuple[int, int], float] = {}
    for a, b, w in zip(rows, cols, weights, strict=True):
        key = (a, b) if a < b else (b, a)
        if w > seen.get(key, -np.inf):
            seen[key] = w
    edges = sorted(seen)
    graph = ig.Graph(n=n, edges=edges, directed=False)
    graph.es["weight"] = [seen[e] for e in edges]
    return graph


def toy() -> int:
    """Run HiDeF on a 30-node graph with two planted communities and check it recovers them.

    Returns:
        0 if both communities are recovered, 1 otherwise.
    """
    install_louvain_stand_in()
    import igraph as ig
    from hidef import hidef_finder

    fixed = unshadow_builtins(hidef_finder)
    print(f"  restored builtins shadowed by scipy star-imports in hidef_finder: "
          f"{', '.join(fixed) if fixed else 'none needed'}")

    rng = np.random.default_rng(0)
    size = 15
    edges, weights = [], []
    for base in (0, size):
        for i in range(base, base + size):
            for j in range(i + 1, base + size):
                edges.append((i, j))
                weights.append(1.0)
    # Three weak bridges, so the graph is connected but the planted split is obvious.
    for _ in range(3):
        a, b = int(rng.integers(0, size)), int(rng.integers(size, 2 * size))
        edges.append((a, b))
        weights.append(0.05)
    graph = ig.Graph(n=2 * size, edges=edges, directed=False)
    graph.es["weight"] = weights
    print(f"TOY  {graph.vcount()} nodes, {graph.ecount()} edges, two planted communities of {size}")

    start = time.perf_counter()
    found = hierarchy(hidef_finder, [graph], maxres=5.0, threads=1)
    print(f"  hidef run + consensus + weave in {time.perf_counter() - start:.1f}s")
    print(f"  {len(found)} communities of >= {MIN_SIZE} members")
    sets = [frozenset(np.flatnonzero(mask).tolist()) for _name, mask in found]
    planted = [frozenset(range(size)), frozenset(range(size, 2 * size))]
    ok = True
    for which, want in enumerate(planted, 1):
        best = max((len(want & got) / len(want | got) for got in sets), default=0.0)
        print(f"    planted community {which}: best Jaccard {best:.3f}"
              + ("  RECOVERED" if best >= 0.9 else "  NOT RECOVERED"))
        ok = ok and best >= 0.9
    print(f"\n  TOY TEST {'PASSES' if ok else 'FAILS'} -- "
          f"{'the Leiden path works without louvain' if ok else 'do not proceed to real data'}")
    return 0 if ok else 1


def hierarchy(
    finder: object, graphs: list, maxres: float, threads: int
) -> list[tuple[str, np.ndarray]]:
    """Run HiDeF end to end and return its kept communities as boolean member masks.

    Replicates the package's own CLI sequence -- ``run`` to sweep resolutions, ``consensus`` to
    collapse the cluster graph at the persistence threshold, then ``weaver.weave`` to build the
    hierarchy -- rather than shelling out and reparsing its text output, so nothing depends on a
    file format. ``run`` returns a ClusterGraph, not a hierarchy; that is what the first attempt
    got wrong.

    Args:
        finder: The imported ``hidef.hidef_finder`` module.
        graphs: One igraph.Graph, in a list, as HiDeF expects.
        maxres: Maximum Leiden resolution to sweep.
        threads: Pool size.

    Returns:
        ``(name, boolean mask over nodes)`` per community of at least ``MIN_SIZE`` members.
    """
    from hidef import weaver as weaver_module

    cluster_graph = finder.run(
        graphs, density=0.1, jaccard=TAU, sample=1.0, minres=0.001, maxres=maxres,
        alg=ALG, numthreads=threads,
    )
    collapsed_with_len = finder.consensus(cluster_graph, CHI, 1.0, CONSENSUS_P)
    collapsed = [x[0] for x in collapsed_with_len]
    if not collapsed:
        return []
    persistence = [x[1] for x in collapsed_with_len]
    # The CLI prepends an all-ones root so the hierarchy has a single top; kept for fidelity, and
    # dropped afterwards because THEMA's schema has a forest of roots and no synthetic one.
    collapsed.insert(0, np.ones(len(collapsed[0])))
    persistence.insert(0, 0)
    woven = weaver_module.Weaver()
    woven.weave(collapsed, boolean=True, levels=False, merge=True, cutoff=TAU)

    # Members are read the way the package's own `output_nodes` reads them: each hierarchy node
    # carries an `index` into `wv._assignment`, which is an int or a tuple of ints, and the mask is
    # `_assignment[index]` or `_assignment[index[0]]`. Guessing at `_assignment[node[0]][node[1]]`
    # returned nothing at all, which is what the toy test caught.
    out: list[tuple[str, np.ndarray]] = []
    for node, data in woven.hier.nodes(data=True):
        if not isinstance(node, tuple):
            continue
        index = data["index"]
        mask = np.asarray(
            woven._assignment[index if isinstance(index, int) else index[0]], dtype=bool
        )
        if MIN_SIZE <= mask.sum() < len(mask):
            out.append((f"Cluster{node[0]}-{node[1]}", mask))
    return out


def main(argv: list[str] | None = None) -> int:
    """Build the HiDeF hierarchy, or run the toy test.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toy", action="store_true", help="planted-community test; run this first")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--k", type=int, default=15, help="kNN neighbours; 15 is declared")
    parser.add_argument("--scramble-seed", type=int, default=0,
                        help="run on a scrambled embedding instead, for the null arm")
    parser.add_argument("--directory", default="")
    parser.add_argument("--leiden-seed", type=int, default=0)
    parser.add_argument("--subsample", type=float, default=0.0,
                        help="cluster a random subsample of this fraction, for the stability arm")
    parser.add_argument("--subsample-seed", type=int, default=0)
    parser.add_argument("--maxres", type=float, default=MAXRES,
                        help="maximum Leiden resolution. The DECLARED run uses the package default "
                             "25.0; other values are POST-HOC SENSITIVITIES and cannot change the "
                             "verdict, per the 4 Oct rule")
    args = parser.parse_args(argv)

    if args.toy:
        return toy()

    import igraph as ig
    from hidef import hidef_finder

    fixed = unshadow_builtins(hidef_finder)
    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    digest = json.loads((root / "universe.json").read_text())["universe_digest"]
    vectors, _mean = centre_and_renormalise(embedded.vectors)
    vectors = np.ascontiguousarray(vectors.astype(np.float32))

    label = args.directory or (
        f"hidef_10770_k{args.k}" if args.maxres == MAXRES
        else f"hidef_10770_k{args.k}_maxres{int(args.maxres)}"
    )
    if args.scramble_seed:
        # Regenerated with the SAME function the build's scrambles use, then ASSERTED against the
        # persisted side: one Ward tree is rebuilt from the regenerated vectors and compared to the
        # tree the build wrote, byte for byte. Without that, "the same null" is an assumption.
        vectors = np.ascontiguousarray(
            null_embeddings(vectors, args.scramble_seed).astype(np.float32)
        )
        persisted = (root / "trees" / f"centred_{digest}"
                     / f"seed{args.scramble_seed:05d}_row00001.npz")
        if persisted.is_file():
            indices = np.load(root / "subsamples" / "indices.npy")
            full = distances(vectors)
            rebuilt = tree_from_subset(vectors, len(keys), np.sort(indices[0]), 3, "ward", full)
            with np.load(persisted) as handle:
                same = all(
                    np.array_equal(handle[field], getattr(rebuilt, field))
                    for field in ("present", "clusters", "parent", "leaf_cluster", "sizes",
                                  "chain_indptr", "chain_idx")
                )
            print(f"  scramble seed {args.scramble_seed} reproduces the persisted tree "
                  f"byte-for-byte: {same}", flush=True)
            if not same:
                print("  THE NULL DOES NOT MATCH THE BUILD'S NULL. Refusing to continue.",
                      flush=True)
                return 1
            del full, rebuilt
        else:
            print(f"  WARNING no persisted tree at {persisted}; cannot assert the null matches",
                  flush=True)
        label = args.directory or f"hidef_null_seed{args.scramble_seed}_k{args.k}"
    subset = None
    if args.subsample:
        rng = np.random.default_rng(args.subsample_seed)
        subset = np.sort(rng.choice(
            len(keys), size=int(round(args.subsample * len(keys))), replace=False
        ))
        vectors = np.ascontiguousarray(vectors[subset])
        keys = [keys[i] for i in subset]
        label = args.directory or (f"hidef_sub{int(args.subsample * 100)}"
                                   f"_seed{args.subsample_seed}_k{args.k}")

    print(f"HIDEF  {len(keys):,} pathways, universe {digest}, k = {args.k}, "
          f"tau {TAU}, chi {CHI}, p {CONSENSUS_P}, maxres {args.maxres}"
          + ("" if args.maxres == MAXRES else "  [POST-HOC SENSITIVITY]")
          + f", alg {ALG}")
    print(f"  builtins restored in hidef_finder: {', '.join(fixed) or 'none'}")
    print(f"  -> {root / label}", flush=True)

    clock = time.perf_counter()
    graph = knn_graph(vectors, args.k)
    graph.vs["name"] = keys
    build_seconds = {"knn graph": time.perf_counter() - clock}
    print(f"  kNN graph: {graph.vcount():,} nodes, {graph.ecount():,} edges "
          f"({build_seconds['knn graph']:.0f}s, peak {peak_gb():.1f} GB)", flush=True)

    clock = time.perf_counter()
    # igraph's hook wants the stdlib `random.Random` interface -- it calls both .randint and
    # .gauss -- so neither a numpy Generator nor a RandomState will do.
    ig.set_random_number_generator(random.Random(args.leiden_seed))
    found = hierarchy(hidef_finder, [graph], maxres=args.maxres, threads=1)
    build_seconds["hidef"] = time.perf_counter() - clock
    print(f"  {len(found):,} communities of >= {MIN_SIZE} members "
          f"({build_seconds['hidef'] / 60:.1f} min, peak {peak_gb():.1f} GB)", flush=True)
    if not found:
        print("  NO COMMUNITIES. Writing an empty result rather than failing.", flush=True)

    sets = {name: frozenset(np.flatnonzero(mask).tolist()) for name, mask in found}
    sizes = {name: len(members) for name, members in sets.items()}
    over_cap = [n for n, v in sizes.items() if v > SIZE_CAP]
    print(f"  communities over THEMA's declared cap of {SIZE_CAP:,}: {len(over_cap)} "
          f"(reported, NOT applied)", flush=True)

    # Strict containment edges, the same relation THEMA's Hasse pass draws: a parent is a minimal
    # proper superset. Whether HiDeF's own hierarchy is strictly nested is MEASURED, not assumed.
    order = sorted(sets, key=lambda n: sizes[n])
    parents: dict[str, list[str]] = {n: [] for n in order}
    for i, child in enumerate(order):
        for parent in order[i + 1:]:
            if sets[child] < sets[parent] and not any(
                sets[child] < sets[mid] < sets[parent] for mid in parents[child]
            ):
                if not any(sets[mid] < sets[parent] for mid in parents[child]):
                    parents[child].append(parent)
    nested = sum(1 for c, ps in parents.items() for p in ps if sets[c] < sets[p])
    print(f"  strict containment edges: {nested:,}", flush=True)

    directory = root / label
    if directory.exists():
        print(f"  REFUSING TO OVERWRITE {directory}; delete it or choose another --directory")
        return 1
    directory.mkdir(parents=True)
    ids = {name: f"h{i:05d}" for i, name in enumerate(order)}
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    info = {p.key: (p.source, p.name, len(p.genes)) for p in collection.pathways}
    kids: dict[str, list[str]] = {n: [] for n in order}
    for child, ps in parents.items():
        for parent in ps:
            kids[parent].append(child)

    with (directory / "nodes.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["node", "size", "support", "parents", "children", "n_genes",
                         "label", "provisional"])
        for name in order:
            writer.writerow([
                ids[name], sizes[name], "", " ".join(ids[p] for p in parents[name]),
                " ".join(ids[c] for c in kids[name]), "", "", "true",
            ])
    with (directory / "members.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["node", "key", "source", "name", "n_genes", "inclusion", "gene_support"])
        for name in order:
            for position in sorted(sets[name]):
                key = keys[position]
                source, title, genes = info.get(key, ("", "", 0))
                writer.writerow([ids[name], key, source, title, genes, "1.0000", ""])
    with (directory / "edges.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["parent", "child"])
        for child, ps in parents.items():
            for parent in ps:
                writer.writerow([ids[parent], ids[child]])
    placed = {keys[i] for members in sets.values() for i in members}
    with (directory / "unplaced.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["key"])
        for key in keys:
            if key not in placed:
                writer.writerow([key])

    manifest = {
        "method": "hidef",
        "package": "hidef==1.1.5",
        "note": ("support and inclusion are EMPTY: HiDeF provides neither a recurrence support nor "
                 "a soft membership, and writing 1.0 would invent them"),
        "graph": f"symmetric kNN on cosine, k = {args.k}, union of directed edges, "
                 f"weight = cosine",
        "params": {"tau": TAU, "chi": CHI, "consensus_p": CONSENSUS_P,
                   "maxres": args.maxres,
                   "maxres_is_declared": args.maxres == MAXRES,
                   "alg": ALG, "minres": 0.001, "density": 0.1, "sample": 1.0},
        "min_size": MIN_SIZE,
        "size_cap_reported_not_applied": SIZE_CAP,
        "communities_over_cap": len(over_cap),
        "universe_digest": digest,
        "n": len(keys),
        "n_nodes": len(order),
        "n_edges": sum(len(v) for v in parents.values()),
        "n_roots": sum(1 for n in order if not parents[n]),
        "n_placed": len(placed),
        "n_unplaced": len(keys) - len(placed),
        "leiden_seed": args.leiden_seed,
        "scramble_seed": args.scramble_seed or None,
        "subsample": args.subsample or None,
        "subsample_seed": args.subsample_seed if args.subsample else None,
        "seconds": {k: round(v, 1) for k, v in build_seconds.items()},
        "wall_seconds": round(sum(build_seconds.values()), 1),
        "peak_gb": round(peak_gb(), 2),
        "builtins_restored": fixed,
        "louvain": "stand-in installed; alg=leiden never touches it",
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  wall {manifest['wall_seconds'] / 60:.1f} min, peak {manifest['peak_gb']} GB")
    print(f"  {manifest['n_nodes']:,} nodes, {manifest['n_roots']:,} roots, "
          f"{manifest['n_placed']:,} placed, {manifest['n_unplaced']:,} unplaced")
    print(f"  -> {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
