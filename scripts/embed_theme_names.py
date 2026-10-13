#!/usr/bin/env python3
"""Embed the c85 theme names twice, for the reviewer's name-embedding test. Analysis input only.

**This changes no build.** The vectors are an input to the reviewer's pre-registered test of whether
name embeddings can separate twins from facets
(``data/experiments/reviewer_eval_x2_2026-10-09/names_test/PREREG_names_test.md``). Nothing in
``src/thema/ontology`` reads them, and the accepted sibling merge rule is **not** run here.

Two encodings, because the pre-registration names two arms:

**primary**
    The pinned MedCPT **article** encoder, the same model and revision every frozen artifact was
    embedded with, with the name in the **title** slot and an empty abstract. This is not the same
    input shape as :func:`thema.embed.embed_medcpt`, which passes a single segment -- the tokenizer
    builds ``[CLS] name [SEP] [SEP]`` here against ``[CLS] text [SEP]`` there -- so the two are not
    comparable and the manifest records which was used.

**secondary**
    The MedCPT **query** encoder, single segment. Reported, not decisive.

Both are CLS-pooled and L2-normalised, float32, in the input file's row order.

The barred files in that directory -- the answer key and the blind and judged chunks -- are never
opened: this script reads exactly one input and asserts as much. Usage::

    uv run scripts/embed_theme_names.py
    uv run scripts/embed_theme_names.py --dry-run     # token census only, writes nothing
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

#: The one directory this script works in.
NAMES_TEST = Path("data/experiments/reviewer_eval_x2_2026-10-09/names_test")

#: Filename fragments this script must never open. Checked, not just intended: the answer key and
#: the blind and judged chunks belong to a blind test and reading them here would contaminate it.
BARRED: tuple[str, ...] = ("KEY_DO_NOT_SHARE", "blind_", "judged_", "rubric")

#: How many rows the input is expected to carry, from the brief. A mismatch is reported, not fixed.
EXPECTED_ROWS = 8251


def sha256(path: Path) -> str:
    """Hex sha256 of a file.

    Args:
        path: The file.

    Returns:
        The digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_names(path: Path) -> tuple[list[str], list[str]]:
    """Node ids and names, in file order.

    Args:
        path: The ``node``/``name`` TSV.

    Returns:
        ``(nodes, names)``, order preserved exactly as the file has it.

    Raises:
        ValueError: If the columns are not the two expected ones, or a name is empty.
    """
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["node", "name"]:
            raise ValueError(f"expected columns node, name; found {reader.fieldnames}")
        rows = list(reader)
    nodes = [row["node"] for row in rows]
    names = [row["name"] for row in rows]
    blank = [node for node, name in zip(nodes, names, strict=True) if not name.strip()]
    if blank:
        raise ValueError(f"{len(blank)} names are empty, first {blank[0]}")
    return nodes, names


def assert_nothing_barred(opened: list[Path]) -> None:
    """Refuse if any opened path is one of the barred files.

    Args:
        opened: Every path this run read.

    Raises:
        ValueError: If a barred file was opened.
    """
    bad = [p for p in opened if any(fragment in p.name for fragment in BARRED)]
    if bad:
        raise ValueError(f"this script must not open {[p.name for p in bad]}")


def census(label: str, counts: list[int], window: int) -> dict[str, int]:
    """Print a token-length census and say whether anything truncates.

    Args:
        label: Which encoder.
        counts: Token counts.
        window: The encoder's window.

    Returns:
        The census, for the manifest.
    """
    over = sum(1 for c in counts if c > window)
    print(f"  {label}: tokens min {min(counts)}, median {int(np.median(counts))}, "
          f"max {max(counts)}; window {window}; over the window {over}")
    if over:
        print(f"    WARNING: {over} names would be truncated at {window} tokens")
    return {"min": min(counts), "median": int(np.median(counts)), "max": max(counts),
            "window": window, "over_window": over}


def main(argv: list[str] | None = None) -> int:
    """Embed the names twice and write the four outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names-test", type=Path, default=NAMES_TEST)
    parser.add_argument("--input", default="theme_names_c85.tsv")
    parser.add_argument("--dry-run", action="store_true",
                        help="token census only; write nothing")
    args = parser.parse_args(argv)

    from thema import embed

    source = args.names_test / args.input
    opened = [source]
    assert_nothing_barred(opened)

    nodes, names = read_names(source)
    print(f"INPUT {source}")
    print(f"  {len(names):,} names, sha256 {sha256(source)[:16]}")
    if len(names) != EXPECTED_ROWS:
        print(f"  NOTE: {len(names):,} rows, not the expected {EXPECTED_ROWS:,}")
    if len(set(nodes)) != len(nodes):
        print(f"  NOTE: {len(nodes) - len(set(nodes))} duplicate node ids")
    duplicate_names = len(names) - len(set(names))
    print(f"  distinct names {len(set(names)):,}; exact duplicates {duplicate_names:,}")

    print("\nTOKEN CENSUS")
    article_tokens = census("article encoder", embed.medcpt_token_counts(names),
                            embed.MODEL_MAX_TOKENS)
    query_tokens = census("query encoder", embed.medcpt_query_token_counts(names),
                          embed.QUERY_MAX_TOKENS)
    if args.dry_run:
        print("\n  --dry-run: nothing written")
        return 0

    print("\nEMBEDDING")
    clock = time.perf_counter()
    article = embed.embed_medcpt_titles(names)
    article_seconds = time.perf_counter() - clock
    print(f"  article (name as title, empty abstract): {article.shape} "
          f"{article.dtype}  ({article_seconds:.0f}s)")
    clock = time.perf_counter()
    query = embed.embed_medcpt_query(names)
    query_seconds = time.perf_counter() - clock
    print(f"  query   (single segment):                {query.shape} "
          f"{query.dtype}  ({query_seconds:.0f}s)")

    for label, matrix in (("article", article), ("query", query)):
        lengths = np.linalg.norm(matrix, axis=1)
        print(f"  {label}: row norms min {lengths.min():.6f} max {lengths.max():.6f}; "
              f"non-finite {int((~np.isfinite(matrix)).sum())}")

    article_path = args.names_test / "name_vecs_article.npy"
    query_path = args.names_test / "name_vecs_query.npy"
    keys_path = args.names_test / "name_keys.txt"
    manifest_path = args.names_test / "name_vecs_manifest.json"

    np.save(article_path, article)
    np.save(query_path, query)
    keys_path.write_text("\n".join(nodes) + "\n", encoding="utf-8")

    manifest = {
        "written": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d"),
        "written_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": "analysis input for the reviewer name-embedding test; no build reads these",
        "prereg": str(args.names_test / "PREREG_names_test.md"),
        "merge_rule_run": False,
        "input": {"path": str(source), "sha256": sha256(source), "n": len(names),
                  "distinct_names": len(set(names)), "duplicate_names": duplicate_names,
                  "order": "file order, unchanged"},
        "n": len(names),
        "dim": int(article.shape[1]),
        "dtype": str(article.dtype),
        "arms": {
            "article": {
                "role": "primary",
                "model": embed.MEDCPT_MODEL,
                "revision": embed.MEDCPT_REVISION,
                "pooling": embed.MEDCPT_POOLING,
                "input": "name in the TITLE slot with an EMPTY abstract, i.e. the pair "
                         "[name, ''] -- NOT the single-segment form the frozen artifacts used",
                "max_tokens": embed.MODEL_MAX_TOKENS,
                "tokens": article_tokens,
                "normalised": "L2, rows to unit length",
                "shape": list(article.shape),
                "seconds": round(article_seconds, 1),
                "file": article_path.name,
                "sha256": sha256(article_path)},
            "query": {
                "role": "secondary, reported not decisive",
                "model": embed.MEDCPT_QUERY_MODEL,
                "revision": embed.MEDCPT_QUERY_REVISION,
                "pooling": embed.MEDCPT_POOLING,
                "input": "name as a single segment",
                "max_tokens": embed.QUERY_MAX_TOKENS,
                "tokens": query_tokens,
                "normalised": "L2, rows to unit length",
                "shape": list(query.shape),
                "seconds": round(query_seconds, 1),
                "file": query_path.name,
                "sha256": sha256(query_path)}},
        "keys_file": keys_path.name,
        "files_read": [str(p) for p in opened],
        "files_not_read": "KEY_DO_NOT_SHARE.json, blind_*.json, judged_*.json, rubric_nameblind.md",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("\nWROTE")
    for path in (article_path, query_path, keys_path, manifest_path):
        print(f"  {path}  ({path.stat().st_size:,} bytes)")

    print("\nSANITY CHECKS")
    pairs = {}
    for position, name in enumerate(names):
        pairs.setdefault(name, []).append(position)
    repeats = [v for v in pairs.values() if len(v) > 1]
    for label, matrix in (("article", article), ("query", query)):
        if repeats:
            left, right = repeats[0][0], repeats[0][1]
            cosine = float(matrix[left] @ matrix[right])
            print(f"  {label}: cosine of the identical names "
                  f"{nodes[left]} and {nodes[right]} ({names[left]!r}) = {cosine:.10f}")
        own = float(matrix[0] @ matrix[0])
        print(f"  {label}: cosine of row 0 with itself = {own:.10f}")
        probe = embed.embed_medcpt_titles([names[0]]) if label == "article" \
            else embed.embed_medcpt_query([names[0]])
        print(f"  {label}: re-embedding name 0 reproduces its row, cosine "
              f"{float(probe[0] @ matrix[0]):.10f}")
    print(f"\n  MERGE RULE RUN: {manifest['merge_rule_run']}  "
          "(the accepted sibling merge is not applied here)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
