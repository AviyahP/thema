import csv
import json

import pytest

from run_prompt_experiment import Generated, name_conditions, text_key, unpack
from test_normalize_descriptions import _pathway
from thema.data.pathways import PATHWAY_COLUMNS
from thema.experiment import ARMS, PRE_CHECK_FORMAT
from thema.normalize import PROMPT_VERSION, RESPONSE_FORMAT, SYSTEM_PROMPT


def _row():
    """One pathway table row for a fixture."""
    return _pathway("reactome", "R-HSA-1", "Alpha pathway").to_row()


def test_the_three_arms_are_the_three_the_experiment_specifies():
    assert set(ARMS) == {"A plain", "B repair", "C pre-check"}


# B is A plus a repair pass. Sharing the generation cache namespace is what guarantees the two
# start from identical text rather than from two generations that could differ.
def test_a_and_b_share_a_generation_namespace_and_c_does_not():
    assert ARMS["A plain"].prompt_version == ARMS["B repair"].prompt_version == PROMPT_VERSION
    assert ARMS["C pre-check"].prompt_version != PROMPT_VERSION, (
        "arm C sends a different system prompt, so it must not share A's cache"
    )


def test_only_arm_b_repairs():
    assert [a.name for a in ARMS.values() if a.repairs] == ["B repair"]


# The arm is pre-writing verification, not self-critique: the checks are written before the
# description, so nothing is being critiqued. Calling it self-critique would later be read as
# evidence about a revision step that was never tested.
def test_arm_c_is_named_and_described_as_pre_writing_verification():
    assert "pre-check" in ARMS["C pre-check"].name
    assert "PRE-WRITING VERIFICATION, not self-critique" in ARMS["C pre-check"].caveat
    assert "self-critique" not in ARMS["C pre-check"].system.lower().replace(
        "not self-critique", ""
    )


# Arm B is scored by the same verifier it repaired against. That cannot be designed away, so it is
# carried on the arm itself and printed wherever the score is.
def test_arm_b_carries_the_circularity_caveat():
    assert "GRADED AGAINST WHAT IT WAS OPTIMISED FOR" in ARMS["B repair"].caveat
    assert "may not generalise" in ARMS["B repair"].caveat
    assert ARMS["A plain"].caveat == "", "arm A has no such caveat and must not imply one"


def test_arm_c_extends_the_v4_prompt_rather_than_replacing_it():
    assert ARMS["C pre-check"].system.startswith(SYSTEM_PROMPT)
    assert ARMS["A plain"].system == SYSTEM_PROMPT


# A string-valued `checks` would be extracted and the description discarded; a LIST makes the
# client store the whole envelope, which is the only reason both fields survive for inspection.
def test_arm_c_keys_on_a_list_so_the_whole_envelope_is_stored():
    assert ARMS["C pre-check"].response_key == "checks"
    schema = PRE_CHECK_FORMAT["schema"]["properties"]
    assert schema["checks"]["type"] == "array"
    assert schema["description"]["type"] == "string"
    assert ARMS["A plain"].response_format is RESPONSE_FORMAT


def test_arm_c_is_priced_with_a_larger_output_assumption_than_the_others():
    assert ARMS["C pre-check"].assumed_output > ARMS["A plain"].assumed_output, (
        "assuming A's output for C understates it by exactly the field that makes it different"
    )


# ------------------------------------------------------------- unpacking


def test_a_plain_arm_completion_is_the_description():
    assert unpack(ARMS["A plain"], "Alpha does a thing.") == ("Alpha does a thing.", "")


def test_arm_c_yields_the_description_and_its_scaffolding_separately():
    payload = json.dumps(
        {"checks": ["RAB3GAP1 is a GAP", "SIRT1 deacetylates"], "description": "x"}
    )
    description, checks = unpack(ARMS["C pre-check"], payload)
    assert description == "x"
    assert checks == "RAB3GAP1 is a GAP | SIRT1 deacetylates"


def test_an_unreadable_envelope_raises_rather_than_becoming_a_description():
    with pytest.raises(ValueError, match="unreadable"):
        unpack(ARMS["C pre-check"], "not json at all")
    with pytest.raises(ValueError, match="unreadable"):
        unpack(ARMS["C pre-check"], json.dumps({"checks": []}))


# ------------------------------------------------------- cache addressing


# Keying on the pathway alone is what lets a stale verdict be served for text that has changed.
def test_the_verification_key_changes_when_the_text_changes():
    assert text_key("go:GO:1", "one") != text_key("go:GO:1", "two")
    assert text_key("go:GO:1", "one") == text_key("go:GO:1", "one")
    assert text_key("go:GO:1", "one").startswith("go:GO:1#")


# --------------------------------------------------- name done-conditions


def test_shared_openings_and_verbatim_names_are_both_counted():
    a = _pathway("go", "GO:1", "alpha pathway")
    b = _pathway("go", "GO:2", "beta pathway")
    by_key = {a.key: a, b.key: b}
    same = "One two three four five six seven eight nine"
    produced = {
        a.key: Generated(a.key, f"{same} alpha pathway", ""),
        b.key: Generated(b.key, f"{same} something else", ""),
    }
    shared, verbatim = name_conditions(produced, by_key)
    assert shared.startswith("2/2"), "both share their first eight words"
    assert verbatim.startswith("1/2"), "only one contains its own name verbatim"


def test_name_conditions_on_an_empty_arm_report_nothing_rather_than_dividing_by_zero():
    assert name_conditions({}, {}) == ("-", "-")


# ------------------------------------------------------ batch recovery


# A batch is billed when the provider runs it, not when its results are read. A run killed between
# submission and collection strands paid-for results, and resubmitting pays for them twice. This
# happened twice on 2026-09-10 before --collect existed on the other two scripts.
def test_collect_takes_an_arm_and_a_batch_id_and_rejects_an_unknown_arm(tmp_path, capsys):
    from run_prompt_experiment import main

    # A typo'd arm name is a pure argument error and must be caught before any file is opened,
    # so the message names the mistake rather than a missing input the operator did not ask about.
    code = main(["--data", str(tmp_path), "--collect", "Z nonsense=msgbatch_x"])
    assert code == 1
    err = capsys.readouterr().err
    assert "unknown arm" in err
    assert "missing input" not in err, "the argument error must not be masked by a file check"

    code = main(["--data", str(tmp_path)])
    assert code == 1, "a missing input must still refuse rather than proceed"
    assert "missing input" in capsys.readouterr().err


def test_every_arm_name_is_usable_as_a_collect_target():
    for name in ARMS:
        assert "=" not in name, "an arm name containing '=' would break --collect ARM=BATCH_ID"


# write_tsv does no escaping -- cells must already be free of tabs and newlines, and `flatten` is
# normally applied when prose is LOADED rather than written. Text generated in-process has never
# been through that path, and arm C's multi-line checks turned 100 rows into 104.
def test_generated_text_is_flattened_before_it_reaches_a_tsv(tmp_path):
    from run_prompt_experiment import write_arm

    produced = {
        "go:GO:1": Generated("go:GO:1", "Line one.\nLine two.", "check A\ncheck B\twith a tab")
    }
    path = write_arm(tmp_path, ARMS["C pre-check"], produced, "claude-opus-5")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2, "a newline inside a cell must not become a new row"
    assert len(lines[1].split("\t")) == len(lines[0].split("\t")), "columns must line up"
    assert "\n" not in lines[1]


# Hand labels cost human attention and cannot be regenerated. write_worksheet runs on every step-3
# invocation, and once silently blanked all 27 of them.
def test_a_rerun_never_destroys_hand_labels(tmp_path, monkeypatch):
    from run_prompt_experiment import EXPERIMENT_DIR, write_worksheet

    data = tmp_path
    (data / EXPERIMENT_DIR).mkdir(parents=True)
    (data / "pathways.tsv").write_text(
        "\t".join(PATHWAY_COLUMNS) + "\n" + "\t".join(_row()) + "\n", encoding="utf-8"
    )
    (data / "pathway_verification_flags.tsv").write_text(
        "key\tkind\tquote\treason\nreactome:R-HSA-1\twrong\tA claim.\tA reason.\n", encoding="utf-8"
    )
    path, count = write_worksheet(data)
    assert count == 1

    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    fields = lines[1].split("\t")
    fields[header.index("label")] = "unambiguous"
    path.write_text("\n".join([lines[0], "\t".join(fields)]) + "\n", encoding="utf-8")

    write_worksheet(data)
    after = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
    assert after[0]["label"] == "unambiguous", "a rerun must carry hand labels forward"


def test_every_worksheet_row_records_where_its_label_came_from(tmp_path):
    from run_prompt_experiment import EXPERIMENT_DIR, LABEL_PROVENANCE, write_worksheet

    (tmp_path / EXPERIMENT_DIR).mkdir(parents=True)
    (tmp_path / "pathways.tsv").write_text(
        "\t".join(PATHWAY_COLUMNS) + "\n" + "\t".join(_row()) + "\n", encoding="utf-8"
    )
    (tmp_path / "pathway_verification_flags.tsv").write_text(
        "key\tkind\tquote\treason\nreactome:R-HSA-1\twrong\tA claim.\tA reason.\n", encoding="utf-8"
    )
    path, _count = write_worksheet(tmp_path)
    rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
    assert rows[0]["label_source"] == LABEL_PROVENANCE
    assert "not independent human labels" in rows[0]["label_source"]
