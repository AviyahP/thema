"""naming-c1, checked against the reviewer's pilot rather than against my reading of the spec.

The tests that matter are the reproduction ones: the pilot of 11 Oct 2026 ran the algorithm on 200
c85 themes through in-session subagents, and every input it built and every selection it made is on
disk. This port is only trustworthy if it returns the same bytes from the same build, so it is held
to exactly that -- item for item, theme for theme, including the uniqueness round.

Those tests need the x2 universe's vectors and key list, which are deliberately not committed
(``.gitignore`` treats embeddings as a reproducible function of the committed inputs). They skip
rather than fail when the artifacts are absent, and the pure-function tests above them always run.

Not tested here: anything that calls a model. The algorithm's randomness is all seeded and all in
:mod:`thema.naming_c1`; the model calls live in ``scripts/name_themes_c1.py``.
"""

from __future__ import annotations

import glob
import json
import random
from pathlib import Path

import pytest

from thema import naming_c1

PILOT = Path("data/experiments/naming_pilot_2026-10-11")
BUILD = Path("data/ontology/v0.4-leaves/thema_L_x2_c85")
X2 = Path("data/ontology/v0.4-leaves-x2")
DESCRIPTIONS = Path("data/pathway_descriptions.tsv")
PATHWAYS = Path("data/pathways.tsv")

NEEDED = (
    PILOT / "inputs/sample_and_confusables.json",
    PILOT / "selection/final_names.json",
    BUILD / "members.tsv",
    BUILD / "nodes.tsv",
    X2 / naming_c1.CENTRED_VECTORS,
    DESCRIPTIONS,
    PATHWAYS,
)

pilot_data = pytest.mark.skipif(
    not all(path.exists() for path in NEEDED),
    reason="the pilot material or the x2 embeddings are not in this checkout",
)


# ------------------------------------------------------------------ the deterministic pieces


def test_the_seed_is_the_first_eight_hex_digits_of_sha256() -> None:
    import hashlib

    assert naming_c1.seed_int("n02310:0") == int(
        hashlib.sha256(b"n02310:0").hexdigest()[:8], 16
    )


def test_the_seed_depends_on_the_candidate_index() -> None:
    assert naming_c1.seed_int("n1:0") != naming_c1.seed_int("n1:1")
    assert naming_c1.seed_int("n1:0") != naming_c1.seed_int("n1:S0")


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("One. Two. Three.", "One. Two."),
        ("Only one sentence.", "Only one sentence."),
        (
            "Ends in a question? Then a statement. And more.",
            "Ends in a question? Then a statement.",
        ),
        ("  leading space. second. third.", "leading space. second."),
        ("", ""),
    ],
)
def test_first_two_sentences(text: str, want: str) -> None:
    assert naming_c1.first_two_sentences(text) == want


def test_tokens_drop_the_stop_words_and_keep_hyphens() -> None:
    assert naming_c1.tokens("Regulation of the RIG-I-like receptor by TRAF6") == {
        "regulation",
        "rig-i-like",
        "receptor",
        "traf6",
    }


def test_jaccard_counts_two_empty_sets_as_identical() -> None:
    assert naming_c1.jaccard(set(), set()) == 1.0
    assert naming_c1.jaccard({"a"}, set()) == 0.0
    assert naming_c1.jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)


def test_normalise_name_strips_punctuation_and_case() -> None:
    assert (
        naming_c1.normalise_name("Wnt ligand secretion and non-canonical Wnt/calcium signaling")
        == "wnt ligand secretion and non canonical wnt calcium signaling"
    )


def _candidate(name: str, nameable: bool = True, rationale: str = "") -> dict[str, object]:
    return {"name": name, "nameable": nameable, "rationale": rationale}


def test_two_refusals_make_a_theme_unnameable() -> None:
    got = naming_c1.select(
        {
            0: _candidate("", nameable=False, rationale="no shared process"),
            1: _candidate("", nameable=False),
            2: _candidate("Something"),
        },
        {},
    )
    assert got == {"unnameable": True, "rationale": "no shared process"}


def test_one_refusal_is_not_enough_to_refuse_the_theme() -> None:
    got = naming_c1.select(
        {0: _candidate("Alpha beta"), 1: _candidate("", nameable=False), 2: _candidate("Alpha")},
        {0: True, 2: True},
    )
    assert got["unnameable"] is False
    assert got["n_nameable"] == 2


def test_the_unnameable_rationale_comes_from_the_lowest_index_present() -> None:
    # The pilot hardcodes candidate 0, which cannot exist on the re-run arm; the lowest index is
    # the same thing wherever candidate 0 is present.
    got = naming_c1.select(
        {
            10: _candidate("", nameable=False, rationale="from ten"),
            11: _candidate("", nameable=False, rationale="from eleven"),
        },
        {},
    )
    assert got["rationale"] == "from ten"


def test_the_winner_is_the_medoid_among_the_correct_candidates() -> None:
    got = naming_c1.select(
        {
            0: _candidate("alpha beta gamma"),
            1: _candidate("alpha beta delta"),
            2: _candidate("completely unrelated wording"),
        },
        {1: True, 2: True},
    )
    assert got["cand"] == 1, "candidate 1 agrees with 0 and 2 more than 2 does"
    assert got["name"] == "alpha beta delta"
    assert got["low_confidence"] is False
    assert got["n_correct"] == 2
    assert got["correct_flags"] == [False, True, True]


def test_the_medoid_is_scored_against_all_nameable_candidates_not_just_the_pool() -> None:
    # PILOT behaviour: candidate 2 is the only correct one, so it wins regardless, but the score
    # that ranks the pool is measured against every nameable candidate including incorrect ones.
    got = naming_c1.select(
        {0: _candidate("alpha beta"), 1: _candidate("alpha beta"), 2: _candidate("zeta")},
        {2: True},
    )
    assert got["cand"] == 2 and got["low_confidence"] is False


def test_no_correct_candidate_flags_low_confidence_and_pools_everything() -> None:
    got = naming_c1.select(
        {0: _candidate("alpha beta"), 1: _candidate("alpha beta gamma"), 2: _candidate("zeta")},
        {},
    )
    assert got["low_confidence"] is True
    assert got["n_correct"] == 0
    assert got["cand"] in (0, 1)


def test_a_tie_goes_to_the_lowest_candidate_index() -> None:
    got = naming_c1.select(
        {0: _candidate("alpha beta"), 1: _candidate("alpha beta"), 2: _candidate("alpha beta")},
        {0: True, 1: True, 2: True},
    )
    assert got["cand"] == 0


def test_selecting_with_no_candidates_is_refused() -> None:
    with pytest.raises(ValueError, match="no candidates"):
        naming_c1.select({}, {})


def test_duplicates_and_collision_groups_ignore_unnameable_themes() -> None:
    finals = {
        "a": {"unnameable": False, "name": "Wnt/calcium signaling"},
        "b": {"unnameable": False, "name": "Wnt calcium signaling"},
        "c": {"unnameable": False, "name": "Something else"},
        "d": {"unnameable": True, "rationale": "no"},
    }
    assert naming_c1.duplicate_names(finals) == {"wnt calcium signaling": 2}
    assert naming_c1.collision_groups(finals) == [["a", "b"]]


def test_the_collision_note_names_the_colliding_name() -> None:
    assert naming_c1.COLLISION_NOTE.format(name="Alpha") == (
        "The name 'Alpha' is already used by another theme; "
        "give a name that distinguishes this theme."
    )


# ------------------------------------------------------------------ the pilot reproduction


@pytest.fixture(scope="module")
def universe() -> naming_c1.Universe:
    keys, vectors = naming_c1.load_space(X2, PATHWAYS)
    return naming_c1.Universe.load(BUILD, DESCRIPTIONS, keys, vectors)


@pytest.fixture(scope="module")
def sample() -> dict[str, list[str]]:
    return json.load((PILOT / "inputs/sample_and_confusables.json").open())["confusables"]


def _inputs(pattern: str) -> list[str]:
    """Input files only: the ``.out.json`` replies sit beside them and match the same glob."""
    return sorted(f for f in glob.glob(str(PILOT / pattern)) if not f.endswith(".out.json"))


def _candidates(prefix: str) -> dict[tuple[str, int], dict[str, object]]:
    out: dict[tuple[str, int], dict[str, object]] = {}
    for path in glob.glob(str(PILOT / f"raw/{prefix}_slot*_b*.out.json")):
        slot = int(path.split("_slot")[1][0])
        for reply in json.load(open(path)):
            out[(reply["theme_id"], slot)] = reply
    return out


def _backmatch(
    universe: naming_c1.Universe,
    sample: dict[str, list[str]],
    prefix: str,
    run: str,
    offset: int,
) -> tuple[list[dict[str, object]], dict[str, tuple[str, int, str]]]:
    """Rebuild one run's back-match items and their answers, as ``np_sel.py`` ordered them."""
    cands = _candidates(prefix)
    order = sorted(cands)
    random.Random(99 + offset).shuffle(order)
    items: list[dict[str, object]] = []
    answers: dict[str, tuple[str, int, str]] = {}
    for position, (theme, slot) in enumerate(order):
        reply = cands[(theme, slot)]
        if not reply.get("nameable", True):
            continue
        item_id = f"{run[0].upper()}{position:04d}"
        item, letter = naming_c1.backmatch_item(
            universe, theme, str(reply["name"]), f"S{slot + offset}", item_id, sample[theme]
        )
        items.append(item)
        answers[item_id] = (theme, slot, letter)
    return items, answers


def _choices(pattern: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in glob.glob(str(PILOT / pattern)):
        for reply in json.load(open(path)):
            out[reply["item_id"]] = reply["choice"]
    return out


@pilot_data
def test_the_build_is_the_one_the_pilot_named_on(universe: naming_c1.Universe) -> None:
    assert len(universe.members) == 8251, "the pilot named on c85's 8,251 themes"
    assert len(universe.eligible()) == 8231


@pilot_data
def test_confusables_reproduce_the_pilots_choices(
    universe: naming_c1.Universe, sample: dict[str, list[str]]
) -> None:
    wrong = {
        theme: (want, universe.confusables(theme))
        for theme, want in sample.items()
        if universe.confusables(theme) != want
    }
    assert not wrong, f"{len(wrong)} themes chose different confusables, e.g. {list(wrong)[:3]}"


@pilot_data
def test_namer_items_reproduce_the_pilots_inputs_item_for_item(
    universe: naming_c1.Universe, sample: dict[str, list[str]]
) -> None:
    checked = 0
    for path in _inputs("inputs/namer_slot*_b*.json"):
        slot = int(path.split("_slot")[1][0])
        for want in json.load(open(path)):
            theme = want["theme_id"]
            got = naming_c1.namer_item(universe, theme, slot, sample[theme])
            assert got == want, f"{Path(path).name} {theme} candidate {slot}"
            checked += 1
    assert checked == 600, f"expected 3 candidates x 200 themes, checked {checked}"


@pilot_data
def test_rerun_items_reproduce_the_pilots_inputs(
    universe: naming_c1.Universe, sample: dict[str, list[str]]
) -> None:
    # The re-run files are named slot0-2 but their candidate indices are 10-12 (ALGORITHM.md 6).
    checked = 0
    for path in _inputs("inputs/rerun_slot*_b*.json"):
        slot = int(path.split("_slot")[1][0])
        for want in json.load(open(path)):
            theme = want["theme_id"]
            got = naming_c1.namer_item(universe, theme, slot + 10, sample[theme])
            assert got == want, f"{Path(path).name} {theme} candidate {slot + 10}"
            checked += 1
    assert checked == 180, f"expected 3 candidates x 60 themes, checked {checked}"


@pilot_data
@pytest.mark.parametrize(
    ("prefix", "run", "offset", "expected"),
    [("namer", "main", 0, 600), ("rerun", "rerun", 10, 180)],
)
def test_backmatch_items_reproduce_the_pilots_selection_inputs(
    universe: naming_c1.Universe,
    sample: dict[str, list[str]],
    prefix: str,
    run: str,
    offset: int,
    expected: int,
) -> None:
    got, _answers = _backmatch(universe, sample, prefix, run, offset)
    want = [
        item
        for path in _inputs(f"selection/{run}_sel_*.json")
        for item in json.load(open(path))
    ]
    assert len(got) == expected and len(want) == expected
    assert got == want


@pilot_data
@pytest.mark.parametrize(
    ("prefix", "run", "offset"), [("namer", "main", 0), ("rerun", "rerun", 10)]
)
def test_selection_reproduces_the_pilots_names(
    universe: naming_c1.Universe,
    sample: dict[str, list[str]],
    prefix: str,
    run: str,
    offset: int,
) -> None:
    cands = _candidates(prefix)
    _items, answers = _backmatch(universe, sample, prefix, run, offset)
    choices = _choices(f"selection/{run}_sel_*.out.json")
    correct = {
        (theme, slot): choices[item_id] == letter
        for item_id, (theme, slot, letter) in answers.items()
    }
    by_theme: dict[str, dict[int, dict[str, object]]] = {}
    for (theme, slot), reply in cands.items():
        by_theme.setdefault(theme, {})[slot] = reply
    got = {
        theme: naming_c1.select(
            replies, {slot: correct.get((theme, slot), False) for slot in replies}
        )
        for theme, replies in by_theme.items()
    }
    want = json.load((PILOT / "selection/final_names.json").open())[run]
    if run == "main":
        # The pilot's main entries are POST-uniqueness, so the two re-asked themes differ here and
        # are checked by the uniqueness test below.
        reasked = {theme for theme, entry in want.items() if "dedup_round" in entry}
        assert len(reasked) == 2
        want = {theme: entry for theme, entry in want.items() if theme not in reasked}
        got = {theme: entry for theme, entry in got.items() if theme not in reasked}
    assert got == want


@pilot_data
def test_the_uniqueness_round_reproduces_the_pilots_final_names(
    universe: naming_c1.Universe, sample: dict[str, list[str]]
) -> None:
    cands = _candidates("namer")
    _items, answers = _backmatch(universe, sample, "namer", "main", 0)
    choices = _choices("selection/main_sel_*.out.json")
    correct = {
        (theme, slot): choices[item_id] == letter
        for item_id, (theme, slot, letter) in answers.items()
    }
    by_theme: dict[str, dict[int, dict[str, object]]] = {}
    for (theme, slot), reply in cands.items():
        by_theme.setdefault(theme, {})[slot] = reply
    first = {
        theme: naming_c1.select(
            replies, {slot: correct.get((theme, slot), False) for slot in replies}
        )
        for theme, replies in by_theme.items()
    }
    want_final = json.load((PILOT / "selection/final_names.json").open())

    assert naming_c1.duplicate_names(first) == want_final["duplicates"]

    items, after = naming_c1.dedup_items(universe, first, sample)
    assert after == json.load((PILOT / "inputs/confusables_after_dedup.json").open())
    for index in (0, 1, 2):
        built = [item for offset, item in items if offset == index + naming_c1.DEDUP_OFFSET]
        assert built == json.load((PILOT / f"inputs/dedup_slot{index}.json").open())

    dedup_cands: dict[str, dict[int, dict[str, object]]] = {}
    dedup_items: list[dict[str, object]] = []
    dedup_answers: dict[str, tuple[str, int, str]] = {}
    for slot in (0, 1, 2):
        for reply in json.load((PILOT / f"raw/dedup_slot{slot}.out.json").open()):
            theme = reply["theme_id"]
            dedup_cands.setdefault(theme, {})[slot] = reply
            item, letter = naming_c1.backmatch_item(
                universe,
                theme,
                str(reply["name"]),
                f"S{slot + naming_c1.DEDUP_OFFSET}",
                f"D{len(dedup_items):03d}",
                after[theme],
            )
            dedup_items.append(item)
            dedup_answers[f"D{len(dedup_items) - 1:03d}"] = (theme, slot, letter)
    random.Random(5).shuffle(dedup_items)
    assert dedup_items == json.load((PILOT / "selection/dedup_sel_01.json").open())

    dedup_choices = _choices("selection/dedup_sel_01.out.json")
    dedup_correct: dict[str, dict[int, bool]] = {}
    for item_id, (theme, slot, letter) in dedup_answers.items():
        dedup_correct.setdefault(theme, {})[slot] = dedup_choices[item_id] == letter
    final = naming_c1.apply_uniqueness(first, dedup_cands, dedup_correct)

    assert final == want_final["main"]
    assert naming_c1.duplicate_names(final) == want_final["duplicates_after_dedup"] == {}


# ------------------------------------------------------------------ the spend gate


@pilot_data
def test_the_default_run_cannot_reach_the_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without ``--submit`` the client is never built, so there is nothing to send with."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "name_themes_c1", Path("scripts/name_themes_c1.py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def refuse(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("the estimate path must not construct an LLM client")

    monkeypatch.setattr(module.llm, "LLMClient", refuse)
    monkeypatch.setattr(module.llm, "load_api_key", refuse)
    assert module.main(["--themes", "2"]) == 0


def test_the_answer_key_guard_refuses_a_key_file() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "name_themes_c1_guard", Path("scripts/name_themes_c1.py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="must not open"):
        module.assert_nothing_barred([Path("x/KEY_DO_NOT_SHARE_main.json")])
    module.assert_nothing_barred([Path("x/sample_and_confusables.json")])


def test_the_chars_per_token_anchor_is_the_measured_one() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "name_themes_c1_rate", Path("scripts/name_themes_c1.py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # 6,946 characters of v4 system prompt billed as 2,511 cached input tokens.
    assert module.CHARS_PER_TOKEN == pytest.approx(6946 / 2511)
    assert module.CHARS_PER_TOKEN == pytest.approx(2.766, abs=0.001)
