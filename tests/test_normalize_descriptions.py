from pathlib import Path

from normalize_descriptions import (
    SMOKE_FLOOR,
    SMOKE_FRACTION,
    choose_smoke,
    main,
    smoke_draw,
    smoke_strata,
)
from test_hierarchy import OBO, RELATION
from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import reactome_roots, read_reactome_relation
from thema.data.pathways import (
    PATHWAY_COLUMNS,
    Pathway,
    PathwayCollection,
    collision_groups,
)
from thema.data.tables import write_tsv
from thema.llm import Completion, Ledger
from thema.normalize import PROMPT_VERSION, genes_for_prompt


def _pathway(
    source="reactome",
    source_id="R-HSA-1",
    name="Alpha",
    description="Alpha does a thing.",
    availability="described",
):
    symbols = (("HGNC:1", ("AAA",)),)
    return Pathway(
        source=source,
        source_id=source_id,
        name=name,
        description_source=description,
        description_source_from="reactome_summation" if description else "none",
        description_generated=None,
        description_generated_from=None,
        genes=frozenset({"HGNC:1"}),
        gene_symbols=symbols,
        n_genes=1,
        n_dropped=0,
        dropped_symbols=(),
        degradation="ok",
        drop_fraction=0.0,
        text_availability=availability,
    )


# R-HSA-100 is the big branch (its subtree has 3 members here), R-HSA-200 the small one, and
# R-HSA-130 sits under both -- the multi-root case largest-wins has to resolve.
def _collection():
    pathways = [
        _pathway("reactome", "R-HSA-100", "Root one"),
        _pathway("reactome", "R-HSA-110", "Middle"),
        _pathway("reactome", "R-HSA-120", "Deep"),
        _pathway("reactome", "R-HSA-130", "Shared child"),
        _pathway("reactome", "R-HSA-200", "Root two"),
        _pathway("reactome", "R-HSA-210", "Under root two"),
        _pathway("go", "GO:0060000", "Deep term"),
        _pathway("go", "GO:0050000", "Mid term"),
        _pathway("go", "GO:0009987", "Cellular process"),
        _pathway("go", "GO:0070000", "Two branches"),
        _pathway("go", "GO:0002376", "Immune system process"),
        _pathway("go", "GO:0000002", "obsolete something", "OBSOLETE. It did a thing."),
        _pathway("hallmark", "HALLMARK_APOPTOSIS", "HALLMARK_APOPTOSIS"),
        _pathway("hallmark", "HALLMARK_HYPOXIA", "HALLMARK_HYPOXIA"),
        _pathway("hallmark", "HALLMARK_DEEP", "HALLMARK_DEEP"),
        _pathway("hallmark", "HALLMARK_MID", "HALLMARK_MID"),
        _pathway("btm", "M1", "Named module", None, "name_only"),
        _pathway("btm", "M2", "Another module", None, "name_only"),
        _pathway("btm", "M3", "Third module", None, "name_only"),
        _pathway("btm", "M4", "TBA", None, "no_usable_text"),
        _pathway("btm", "M5", "TBA", None, "no_usable_text"),
    ]
    return PathwayCollection.of(pathways)


def _strata(collection=None):
    collection = collection or _collection()
    parents = read_reactome_relation(RELATION.splitlines())
    terms = parse_obo_terms(OBO.splitlines(), namespace="biological_process")
    return collection, smoke_strata(collection, parents, reactome_roots(parents), terms)


def _keys(selection):
    return tuple(pathway.key for _stratum, pathway in selection)


# ------------------------------------------------------------------ draw


# These two are the numbers the design was specified against, and they are what pins the rounding
# rule: GO's 124 obsolete terms and BTM's 87 TBA modules.
def test_the_draw_rule_reproduces_the_two_counts_the_design_was_specified_against():
    assert smoke_draw("go/obsolete", 124) == 19
    assert smoke_draw("btm/tba", 87) == 13


def test_the_floor_beats_the_share_on_a_small_stratum():
    assert smoke_draw("reactome/R-HSA-1", 2) == 2, "a stratum cannot yield more than it holds"
    assert smoke_draw("reactome/R-HSA-1", 6) == SMOKE_FLOOR
    assert smoke_draw("reactome/R-HSA-1", 100) == round(SMOKE_FRACTION * 100)


def test_hallmark_is_drawn_whole_rather_than_sampled():
    assert smoke_draw("hallmark", 50) == 50


# --------------------------------------------------------------- strata


def test_every_source_is_stratified_the_way_the_design_names():
    _collection_, strata = _strata()
    assert {n for n in strata if n.startswith("reactome/")} == {
        "reactome/R-HSA-100",
        "reactome/R-HSA-200",
    }
    assert "go/obsolete" in strata, (
        "obsolete terms are detached from the DAG and get a pile of their own"
    )
    assert {n for n in strata if n.startswith("btm/")} == {"btm/named", "btm/tba"}
    assert "hallmark" in strata


def test_a_node_under_two_branches_is_filed_into_the_larger_one():
    _collection_, strata = _strata()
    shared = [
        n for n, members in strata.items() if any(p.source_id == "R-HSA-130" for p in members)
    ]
    assert shared == ["reactome/R-HSA-100"], (
        "largest-wins keeps the narrow branch's quota for the pathways only it has"
    )


def test_a_go_term_under_two_branches_is_filed_into_the_larger_one():
    _collection_, strata = _strata()
    shared = [
        n for n, members in strata.items() if any(p.source_id == "GO:0070000" for p in members)
    ]
    assert shared == ["go/GO:0009987"]


def test_every_pathway_lands_in_exactly_one_stratum():
    collection, strata = _strata()
    filed = [p.key for members in strata.values() for p in members]
    assert sorted(filed) == sorted(p.key for p in collection)
    assert len(filed) == len(set(filed)), "a pathway in two strata would be drawn twice"


# ------------------------------------------------------------ selection


def test_the_selection_is_identical_on_a_second_run():
    collection, strata = _strata()
    assert _keys(choose_smoke(collection, strata)) == _keys(choose_smoke(collection, strata))


# The pool is sorted by key before it is sampled precisely so this holds. Without that sort the
# selection would depend on table order and a clean clone could get a different subset.
def test_the_selection_does_not_depend_on_the_order_the_collection_arrived_in():
    collection, strata = _strata()
    reversed_collection = PathwayCollection.of(reversed(list(collection)))
    _c, reversed_strata = _strata(reversed_collection)
    assert _keys(choose_smoke(collection, strata)) == _keys(
        choose_smoke(reversed_collection, reversed_strata)
    )


def test_a_different_seed_selects_a_different_subset():
    collection, strata = _strata()
    assert _keys(choose_smoke(collection, strata, seed=0)) != _keys(
        choose_smoke(collection, strata, seed=99)
    )


# Both members or the group is useless: a collision group with one member present cannot show
# whether the clusterer merges the pair, which is the thing THEMA exists to do.
def test_both_members_of_every_collision_group_are_included():
    collection, strata = _strata()
    chosen = set(_keys(choose_smoke(collection, strata)))
    groups = collision_groups(collection)
    assert groups, "the fixture must contain at least one cross-source collision to test"
    for name, members in groups.items():
        present = [m.key for m in members if m.key in chosen]
        assert len(present) == len(members), f"collision group {name!r} came through partial"


def test_every_stratum_contributes_at_least_one_pathway():
    collection, strata = _strata()
    chosen = set(_keys(choose_smoke(collection, strata)))
    for name, members in strata.items():
        assert any(p.key in chosen for p in members), f"stratum {name!r} contributed nothing"


def test_all_of_hallmark_is_selected():
    collection, strata = _strata()
    chosen = set(_keys(choose_smoke(collection, strata)))
    hallmark = {p.key for p in collection.of_source("hallmark")}
    assert hallmark <= chosen, "hallmark is drawn whole, not sampled"


# ---------------------------------------------------------- the spend gate


class _FakeClient:
    """Stands in for the provider: records what was asked of it, and fills the ledger like the real
    client does, so a second run genuinely sees a warm cache rather than an empty one."""

    submitted: list = []
    counted: list = []
    #: Keys the provider will not return a usable result for, as an unparseable batch row does.
    fails: set = set()

    def __init__(self, model, prompt_version, ledger, **kwargs):
        self.model = model
        self.prompt_version = prompt_version
        self.ledger = ledger

    def count_tokens(self, request):
        _FakeClient.counted.append(request.key)
        return 100

    def submit_batch(self, requests):
        _FakeClient.submitted.append(list(requests))
        return "msgbatch_fake"

    #: What batch_status reports; a test flips this to exercise the not-ready path.
    status: str = "ended"

    def await_batch(self, batch_id):
        return "ended"

    def batch_status(self, batch_id):
        return _FakeClient.status

    def collect_batch(self, batch_id, requests):
        collected = []
        for request in requests:
            if request.key in _FakeClient.fails:
                continue
            completion = Completion(
                key=request.key,
                model=self.model,
                prompt_version=self.prompt_version,
                text="Alpha is a biological process that does a thing in the cell. " * 20,
                input_tokens=100,
                output_tokens=300,
                batch_id=batch_id,
            )
            self.ledger.append(completion)
            collected.append(completion)
        return tuple(collected)


def _data_dir(tmp_path: Path) -> tuple[Path, Path]:
    data, raw = tmp_path / "data", tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    collection = _collection()
    write_tsv(data / "pathways.tsv", PATHWAY_COLUMNS, collection.to_rows())
    (raw / "ReactomePathwaysRelation.txt").write_text(RELATION + "\n", encoding="utf-8")
    (raw / "go-basic.obo").write_text(OBO + "\n", encoding="utf-8")
    return data, raw


def _run(tmp_path, monkeypatch, *extra):
    data, raw = _data_dir(tmp_path)
    _FakeClient.submitted, _FakeClient.counted, _FakeClient.fails = [], [], set()
    _FakeClient.status = "ended"
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    code = main(["--smoke", "--data", str(data), "--raw", str(raw), *extra])
    return code, data


def test_smoke_without_submit_writes_no_table_and_submits_no_batch(tmp_path, monkeypatch):
    code, data = _run(tmp_path, monkeypatch)
    assert code == 0
    assert not (data / "pathway_descriptions.tsv").exists(), (
        "a dry run must not write the committed table"
    )
    assert _FakeClient.submitted == [], "a dry run must not submit anything billable"


def test_the_dry_run_prints_the_marginal_count_and_both_prices(tmp_path, monkeypatch, capsys):
    _run(tmp_path, monkeypatch)
    out = capsys.readouterr().out
    assert "to generate" in out, "the marginal count is the number that costs money"
    assert "batch cost, cached" in out and "batch cost, uncached" in out
    assert "nothing submitted; rerun with --submit" in out


def test_submit_refuses_above_the_ceiling_and_says_so(tmp_path, monkeypatch, capsys):
    code, data = _run(tmp_path, monkeypatch, "--submit", "--max-dollars", "0")
    assert code == 1, "a run priced above the ceiling must refuse rather than spend"
    assert _FakeClient.submitted == []
    assert not (data / "pathway_descriptions.tsv").exists()
    assert "exceeds --max-dollars" in capsys.readouterr().err


def test_submit_within_the_ceiling_goes_through(tmp_path, monkeypatch):
    code, _data = _run(tmp_path, monkeypatch, "--submit", "--max-dollars", "1000")
    assert code == 0
    assert _FakeClient.submitted, "inside the ceiling the batch must actually be submitted"


def test_the_gate_guards_full_as_well_as_smoke(tmp_path, monkeypatch, capsys):
    data, _raw = _data_dir(tmp_path)
    _FakeClient.submitted = []
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    code = main(["--full", "--data", str(data), "--submit", "--max-dollars", "0"])
    assert code == 1, "--full is the larger spend and needs the guard more, not less"
    assert _FakeClient.submitted == []


def test_no_mode_names_all_three(tmp_path, capsys):
    data, _raw = _data_dir(tmp_path)
    assert main(["--data", str(data)]) == 1
    assert "--sample, --smoke, --full or --report" in capsys.readouterr().err


# Rerunning with everything cached is how the table gets rewritten after a repair. It must cost
# nothing, measure nothing, and above all not crash on an empty sample.
def test_a_rerun_with_everything_cached_prices_at_zero_and_still_writes(tmp_path, monkeypatch):
    data, raw = _data_dir(tmp_path)
    _FakeClient.submitted = []
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    args = ["--smoke", "--data", str(data), "--raw", str(raw), "--submit", "--max-dollars", "1000"]
    assert main(args) == 0
    first = (data / "pathway_descriptions.tsv").read_bytes()
    assert first, "the first run must write the table"

    _FakeClient.submitted = []
    assert main(args) == 0, "a fully cached rerun must succeed, not divide by an empty sample"
    assert _FakeClient.submitted == [], "a fully cached rerun must submit nothing"
    assert (data / "pathway_descriptions.tsv").read_bytes() == first, (
        "the rewrite must be byte-identical when nothing changed"
    )


# ------------------------------------------------- the checks that lied


def _summary(data):
    rows = {}
    text = (data / "pathway_descriptions_summary.tsv").read_text(encoding="utf-8")
    for line in text.splitlines()[1:]:
        fields = line.split("\t")
        if len(fields) >= 4:
            rows[(fields[0], fields[1])] = (fields[2], fields[3])
    return rows


# The exact condition that made this check lie. It counted every ledger row inside the collection,
# and the ledger also holds the --sample run's twelve -- so stale rows OUTSIDE the selection
# partly cancelled real failures INSIDE it and turned "6 missing" into a confusing "+4".
def test_stale_ledger_rows_outside_the_selection_do_not_mask_a_missing_description(
    tmp_path, monkeypatch
):
    data, raw = _data_dir(tmp_path)
    _FakeClient.submitted, _FakeClient.fails = [], set()
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    args = ["--smoke", "--data", str(data), "--raw", str(raw), "--submit", "--max-dollars", "1000"]

    collection = PathwayCollection.from_tsv_text(
        (data / "pathways.tsv").read_text(encoding="utf-8")
    )
    _c, strata = _strata(collection)
    selected = {p.key for _s, p in choose_smoke(collection, strata)}
    outside = [p for p in collection if p.key not in selected]
    assert outside, "the fixture must contain a pathway outside the selection to stand in for one"

    # A stale row from an earlier --sample run, outside this selection entirely.
    ledger = Ledger.open(data / "cache/descriptions", "claude-opus-5", PROMPT_VERSION)
    ledger.append(
        Completion(
            key=outside[0].key,
            model="claude-opus-5",
            prompt_version=PROMPT_VERSION,
            text="A stale row from the --sample run, outside this selection entirely. " * 8,
        )
    )
    # And one selected pathway whose batch result never comes back, as six did on 2026-09-09.
    missing = sorted(selected)[0]
    _FakeClient.fails = {missing}
    assert main(args) == 0

    measured, note = _summary(data)[("sanity", "every selected pathway has a description")]
    assert "[FAIL]" in note, "one selected pathway has no description; that must not pass"
    assert measured == str(len(selected) - 1), (
        f"the check must count over the selection ({len(selected) - 1}), not over the ledger -- "
        "counting the ledger lets the stale row cancel the missing one out"
    )


# The other check asserted genes_shown == n_genes, which is false by design: genes_shown counts
# SYMBOLS and n_genes counts identifiers, so they differ wherever two of a source's symbols met on
# one gene. DDX58/RIGI is the real case. Truncation is shown < genes, and only that.
def test_two_symbols_meeting_on_one_gene_is_not_reported_as_truncation(tmp_path, monkeypatch):
    data, raw = _data_dir(tmp_path)
    collection = PathwayCollection.from_tsv_text(
        (data / "pathways.tsv").read_text(encoding="utf-8")
    )
    merged = Pathway(
        source="reactome",
        source_id="R-HSA-210",
        name="Under root two",
        description_source="Alpha does a thing.",
        description_source_from="reactome_summation",
        description_generated=None,
        description_generated_from=None,
        genes=frozenset({"HGNC:1"}),
        gene_symbols=(("HGNC:1", ("DDX58", "RIGI")),),
        n_genes=1,
        n_dropped=0,
        dropped_symbols=(),
        degradation="ok",
        drop_fraction=0.0,
        text_availability="described",
    )
    rebuilt = PathwayCollection.of(
        [p for p in collection if p.source_id != "R-HSA-210"] + [merged]
    )
    write_tsv(data / "pathways.tsv", PATHWAY_COLUMNS, rebuilt.to_rows())
    assert len(genes_for_prompt(merged)) > merged.n_genes, "the fixture must exercise the case"

    _FakeClient.submitted = []
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    code = main(
        ["--smoke", "--data", str(data), "--raw", str(raw), "--submit", "--max-dollars", "1000"]
    )
    assert code == 0
    measured, note = _summary(data)[("sanity", "no gene list was truncated")]
    assert measured == "0" and "[FAIL]" not in note, (
        "shown > genes is symbols collapsing onto a gene, not truncation"
    )


# A batch is billed when the provider runs it, not when its results are read. A run killed between
# submission and collection strands paid-for results, and resubmitting pays for them twice. This
# happened on 2026-09-09.
def test_collect_drains_an_existing_batch_instead_of_submitting_a_new_one(tmp_path, monkeypatch):
    data, raw = _data_dir(tmp_path)
    _FakeClient.submitted, _FakeClient.fails, _FakeClient.status = [], set(), "ended"
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    base = ["--smoke", "--data", str(data), "--raw", str(raw)]

    code = main([*base, "--collect", "msgbatch_stranded"])
    assert code == 0
    assert _FakeClient.submitted == [], "collecting must not submit anything"
    assert (data / "pathway_descriptions.tsv").is_file(), "collected results must reach the table"
    assert ("batch", "batch_1") in _summary(data), "the collected batch id must be recorded"


def test_collect_does_not_need_submit_because_it_spends_nothing(tmp_path, monkeypatch, capsys):
    data, raw = _data_dir(tmp_path)
    _FakeClient.submitted, _FakeClient.fails, _FakeClient.status = [], set(), "ended"
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    # A ceiling of zero would refuse a submission; collecting is not a submission.
    code = main(
        ["--smoke", "--data", str(data), "--raw", str(raw), "--collect", "msgbatch_x",
         "--max-dollars", "0"]
    )
    assert code == 0, "the spend gate must not block a collection, which bills nothing new"
    assert "nothing new is billed" in capsys.readouterr().out


# A batch that has not finished must not look like a batch with no results. Blocking until it does
# is what got two recovery processes killed on 2026-09-09; asking and returning is what replaced it.
def test_collecting_an_unfinished_batch_says_so_and_writes_nothing(tmp_path, monkeypatch, capsys):
    data, raw = _data_dir(tmp_path)
    _FakeClient.submitted, _FakeClient.fails, _FakeClient.status = [], set(), "in_progress"
    monkeypatch.setattr("normalize_descriptions.LLMClient", _FakeClient)
    code = main(["--smoke", "--data", str(data), "--raw", str(raw), "--collect", "msgbatch_x"])
    _FakeClient.status = "ended"
    assert code == 0
    assert "in_progress" in capsys.readouterr().out
    assert not (data / "pathway_descriptions.tsv").exists(), (
        "an unfinished batch must not write a table that looks complete"
    )
