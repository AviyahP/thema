import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from thema import llm
from thema.llm import Completion, Ledger, LLMClient, Request, custom_id, extract_text, spend

REPO_ROOT = Path(__file__).resolve().parents[1]


class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Usage:
    def __init__(self):
        self.input_tokens = 100
        self.output_tokens = 40
        self.cache_read_input_tokens = 900
        self.cache_creation_input_tokens = 0


class _Message:
    """What the SDK hands back, reduced to the fields the client reads."""

    def __init__(self, text='{"description": "Alpha pathway does a thing."}'):
        self.content = [_Block(text)]
        self.usage = _Usage()
        self.stop_reason = "end_turn"
        self._request_id = "req_test"


def _client(tmp_path, model="claude-opus-5", prompt_version="v1", monkeypatch=None, message=None):
    ledger = Ledger.open(tmp_path, model, prompt_version)
    client = LLMClient(model, prompt_version, ledger, api_key="test-key")
    if monkeypatch is not None:
        monkeypatch.setattr(client, "_send", lambda _p: _bump(client, message or _Message()))
    return client


def _bump(client, message):
    client.calls += 1
    return message


def _request(key="reactome:R-HSA-1"):
    return Request(key=key, system="SYSTEM", user="Input name: Alpha pathway")


# ------------------------------------------------ the one-module invariant


# The 2026-08-29 dependency entry confines the SDK to src/thema/llm.py so the rest of the package
# stays stdlib and testable without it. A rule nothing checks is a rule that erodes.
def test_anthropic_is_imported_by_exactly_one_file_in_the_repo():
    pattern = re.compile(r"^\s*(?:import anthropic|from anthropic\b)", re.MULTILINE)
    sources = sorted(
        path
        for directory in ("src", "scripts")
        for path in (REPO_ROOT / directory).rglob("*.py")
    )
    importers = [p.relative_to(REPO_ROOT) for p in sources if pattern.search(p.read_text())]
    assert [str(p) for p in importers] == ["src/thema/llm.py"], (
        "the SDK must stay confined to one module; found it in " f"{[str(p) for p in importers]}"
    )


# Stronger than grepping for the import: import the module with the SDK made unimportable, which
# is what "the rest of the package is testable without it" actually claims.
def test_the_rest_of_the_package_imports_with_the_sdk_made_unavailable():
    program = (
        "import builtins, sys\n"
        "real = builtins.__import__\n"
        "def block(name, *a, **k):\n"
        "    if name == 'anthropic' or name.startswith('anthropic.'):\n"
        "        raise ImportError('blocked for this test')\n"
        "    return real(name, *a, **k)\n"
        "builtins.__import__ = block\n"
        "import thema.normalize, thema.data.pathways, thema.data.tables\n"
        "print(thema.normalize.PROMPT_VERSION)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, f"importing without the SDK failed:\n{result.stderr}"
    assert result.stdout.strip() == "v1"


# -------------------------------------------------------------- the cache


def test_a_cache_hit_makes_zero_api_calls(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch=monkeypatch)
    client.complete(_request())
    assert client.calls == 1

    again = _client(tmp_path, monkeypatch=monkeypatch)
    again.complete(_request())
    assert again.calls == 0, "a completed pathway must never be paid for twice"


def test_a_cache_hit_returns_byte_identical_text(tmp_path, monkeypatch):
    first = _client(tmp_path, monkeypatch=monkeypatch).complete(_request())
    second = _client(tmp_path, monkeypatch=monkeypatch).complete(_request())
    assert first.text == second.text


def test_a_prompt_version_bump_misses_the_cache(tmp_path, monkeypatch):
    _client(tmp_path, prompt_version="v1", monkeypatch=monkeypatch).complete(_request())
    bumped = _client(tmp_path, prompt_version="v2", monkeypatch=monkeypatch)
    bumped.complete(_request())
    assert bumped.calls == 1, "a changed prompt must regenerate, not reuse the old answer"


def test_a_model_change_misses_the_cache(tmp_path, monkeypatch):
    _client(tmp_path, model="claude-opus-5", monkeypatch=monkeypatch).complete(_request())
    other = _client(tmp_path, model="claude-haiku-4-5", monkeypatch=monkeypatch)
    other.complete(_request())
    assert other.calls == 1


def test_two_pathways_do_not_share_a_cache_entry(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch=monkeypatch)
    client.complete(_request("reactome:R-HSA-1"))
    client.complete(_request("go:GO:0000012"))
    assert client.calls == 2
    assert len(client.ledger) == 2


# A kill part-way through an append leaves at most one partial line. Losing that one completion is
# correct; losing the ledger is not.
def test_a_truncated_final_line_costs_one_completion_and_not_the_ledger(tmp_path):
    ledger = Ledger.open(tmp_path, "claude-opus-5", "v1")
    ledger.append(Completion(key="a", model="claude-opus-5", prompt_version="v1", text="one"))
    ledger.append(Completion(key="b", model="claude-opus-5", prompt_version="v1", text="two"))
    with ledger.path.open("a", encoding="utf-8") as handle:
        handle.write('{"key": "c", "model": "clau')

    reopened = Ledger.open(tmp_path, "claude-opus-5", "v1")
    assert len(reopened) == 2
    assert reopened.get("a").text == "one"
    assert "c" not in reopened


def test_the_ledger_records_the_tokens_the_summary_needs(tmp_path, monkeypatch):
    completion = _client(tmp_path, monkeypatch=monkeypatch).complete(_request())
    assert completion.input_tokens == 100
    assert completion.output_tokens == 40
    assert completion.cache_read_tokens == 900
    assert completion.stop_reason == "end_turn"

    record = json.loads(
        Ledger.open(tmp_path, "claude-opus-5", "v1").path.read_text().splitlines()[0]
    )
    assert record["cache_read_tokens"] == 900, "token counts must survive a restart"


# ------------------------------------------------------- request shaping


# Opus 5 and Sonnet 5 take adaptive thinking and an effort level; Haiku 4.5 accepts neither. The
# asymmetry is an API constraint, and the client must not send a parameter that returns a 400.
def test_haiku_is_sent_neither_thinking_nor_effort(tmp_path):
    params = _client(tmp_path, model="claude-haiku-4-5")._params(_request())
    assert "thinking" not in params
    assert "effort" not in params.get("output_config", {})


def test_the_thinking_models_are_sent_adaptive_thinking_and_low_effort(tmp_path):
    for model in ("claude-opus-5", "claude-sonnet-5"):
        params = _client(tmp_path, model=model)._params(_request())
        assert params["thinking"] == {"type": "adaptive"}
        assert params["output_config"]["effort"] == "low"


# The system prompt is identical across all 10,817 requests, which is the only reason it is worth
# caching at the provider. A cache_control breakpoint that goes missing costs real money.
def test_the_system_prompt_carries_a_cache_breakpoint(tmp_path):
    system = _client(tmp_path)._params(_request())["system"]
    assert system[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


def test_an_unknown_model_is_refused_rather_than_sent(tmp_path):
    with pytest.raises(ValueError, match="unknown model"):
        LLMClient("gpt-4", "v1", Ledger.open(tmp_path, "x", "v1"), api_key="k")


# ---------------------------------------------------------- batch plumbing


# Pathway keys carry colons; batch custom_ids do not accept them. The mapping must stay injective
# or results would be attributed to the wrong pathway.
def test_custom_ids_stay_distinct_across_the_sources_that_share_an_id_shape():
    keys = ["go:GO:0000012", "reactome:R-HSA-109581", "hallmark:HALLMARK_APOPTOSIS", "btm:M1.0"]
    assert len({custom_id(k) for k in keys}) == len(keys)
    assert ":" not in "".join(custom_id(k) for k in keys)


def test_chunking_covers_every_request_exactly_once():
    requests = [_request(f"go:GO:{i:07d}") for i in range(4501)]
    chunks = list(llm.chunked(requests, size=2000))
    assert [len(c) for c in chunks] == [2000, 2000, 501]
    assert [r for chunk in chunks for r in chunk] == requests


# -------------------------------------------------------------- responses


def test_structured_output_is_unwrapped_to_the_bare_description():
    assert extract_text(_Message('{"description": "Alpha does a thing."}')) == "Alpha does a thing."


def test_a_plain_text_response_falls_through_unchanged():
    assert extract_text(_Message("Alpha does a thing.")) == "Alpha does a thing."


def test_whitespace_is_collapsed_so_the_text_survives_a_tsv_cell():
    assert extract_text(_Message("Alpha  does\na thing.")) == "Alpha does a thing."


def test_a_response_carrying_no_text_is_an_error_rather_than_an_empty_description():
    empty = _Message()
    empty.content = []
    with pytest.raises(ValueError, match="no text block"):
        extract_text(empty)


# ------------------------------------------------------------------ cost


def test_cache_reads_are_priced_at_a_tenth_of_the_input_rate():
    completion = Completion(
        key="a", model="claude-opus-5", prompt_version="v1", text="x",
        input_tokens=1_000_000, output_tokens=0, cache_read_tokens=1_000_000,
    )
    priced = spend([completion], "claude-opus-5")
    assert priced["input"] == pytest.approx(5.0 + 0.5)
    assert priced["output"] == 0.0


def test_every_model_the_client_accepts_has_a_price():
    assert set(llm.MODELS) == set(llm.PRICES)


# ------------------------------------------------------------------- key


def test_the_environment_wins_over_the_dotenv_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=from-file\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    assert llm.load_api_key(env) == "from-env"


def test_the_dotenv_file_is_read_when_the_environment_is_empty(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('ANTHROPIC_API_KEY="quoted-key"\n')
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.load_api_key(env) == "quoted-key"


def test_a_missing_key_names_the_two_ways_to_supply_one(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match=r"export it, or put it in .env"):
        llm.load_api_key(tmp_path / "absent")


# ------------------------------------------------------------- escaping


# Three of the first thirty-six sampled descriptions came back with a literal backslash-u sequence
# where an em dash belonged: the model escaped inside its own JSON string, so parsing left the
# escape standing. Unrepaired, that puts visible escape sequences into committed, embedded prose.
def test_a_literal_unicode_escape_is_decoded_to_the_character_it_names():
    assert llm.repair_escapes(r"patterns embryos — WNT and BMP") == "patterns embryos — WNT and BMP"


def test_repairing_is_idempotent():
    once = llm.repair_escapes(r"a — b")
    assert llm.repair_escapes(once) == once


# Narrow by design: a backslash that is not introducing a code point stays put.
def test_an_ordinary_backslash_is_left_alone():
    assert llm.repair_escapes(r"the \beta subunit") == r"the \beta subunit"


def test_a_stored_completion_written_before_the_fix_is_repaired_on_read(tmp_path):
    ledger = Ledger.open(tmp_path, "claude-opus-5", "v1")
    ledger.path.parent.mkdir(parents=True, exist_ok=True)
    ledger.path.write_text(
        json.dumps(
            {
                "key": "go:GO:1", "model": "claude-opus-5", "prompt_version": "v1",
                "text": r"embryos — WNT", "input_tokens": 0, "output_tokens": 0,
                "cache_read_tokens": 0, "cache_creation_tokens": 0, "stop_reason": "end_turn",
                "request_id": None, "batch_id": None,
            }
        )
        + "\n"
    )
    assert Ledger.open(tmp_path, "claude-opus-5", "v1").get("go:GO:1").text == "embryos — WNT"
