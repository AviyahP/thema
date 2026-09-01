"""The caching LLM client, and the only module in THEMA that imports a provider SDK.

``CLAUDE.md`` requires that every LLM call go through a caching client rather than the SDK directly,
and the 2026-08-29 dependency entry confines ``anthropic`` to this file so the rest of the package
stays stdlib and testable without it. ``tests/test_llm.py`` walks the sources and asserts that,
because a rule nothing checks is a rule that erodes.

Two things shape the design. Completions are cached by ``(pathway key, prompt version, model)``, so
a rerun regenerates nothing already done and a prompt-version bump invalidates cleanly instead of
mixing two prompts in one table. And the cache is an append-only JSONL ledger rather than the output
table, because 10,817 calls will be interrupted and because the table alone would discard the token
counts the summary needs to report what a run actually cost.
"""

import json
import os
import re
import time
from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import anthropic

#: Per-model request differences. These are API constraints, not preferences: Opus 5 and Sonnet 5
#: take adaptive thinking and an effort level; Haiku 4.5 accepts neither, so it runs with thinking
#: omitted. The three models are therefore not configured identically and cannot be, which is stated
#: wherever they are compared rather than buried here.
MODELS: dict[str, dict[str, object]] = {
    "claude-opus-5": {"thinking": {"type": "adaptive"}, "effort": "low"},
    "claude-sonnet-5": {"thinking": {"type": "adaptive"}, "effort": "low"},
    "claude-haiku-4-5": {},
}

#: Generous relative to a ~110-word answer, because on the thinking models the budget is shared with
#: reasoning tokens and a truncated description would be worse than a slightly expensive one.
MAX_TOKENS = 4000

#: Retries and capped backoff, the shape ``scripts/download_pathway_data.py`` already uses.
RETRIES = 6
BACKOFF_CAP = 30.0

#: Live calls run concurrently; batch runs do not need this.
CONCURRENCY = 8

#: A batch this size keeps a failure to one chunk rather than to a whole 24-hour window.
BATCH_CHUNK = 2000

BATCH_POLL_SECONDS = 30.0


def load_api_key(env_file: Path | None = None) -> str:
    """Find the API key, preferring the environment over the file.

    Nothing else in the repo reads an environment variable, and ``uv run`` does not load ``.env``
    unless told to, so the fallback read is what makes ``uv run scripts/normalize_descriptions.py``
    work the way every other script in this repo works.

    Args:
        env_file: The ``.env`` to fall back to. Defaults to the repo root's.

    Returns:
        The key.

    Raises:
        RuntimeError: If no key is set and none can be read.
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    path = env_file or Path(__file__).resolve().parents[2] / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "ANTHROPIC_API_KEY":
                key = value.strip().strip("'\"")
                if key:
                    return key
    raise RuntimeError(
        "no ANTHROPIC_API_KEY: export it, or put it in .env (see .env.example)",
    )


@dataclass(frozen=True, slots=True)
class Request:
    """One pathway's prompt, with the key its completion will be cached under.

    Attributes:
        key: The pathway key, for example ``go:GO:0000012``.
        system: The stable system prompt. Identical across every request in a run, which is what
            makes it worth caching at the provider.
        user: The per-pathway message.
    """

    key: str
    system: str
    user: str


@dataclass(frozen=True, slots=True)
class Completion:
    """One model response, with everything the summary needs to report the run.

    Attributes:
        key: The pathway key.
        model: The model id that produced it.
        prompt_version: The prompt version it was produced under.
        text: The description.
        input_tokens: Uncached input tokens billed.
        output_tokens: Output tokens billed, thinking included.
        cache_read_tokens: Input tokens served from the provider's prompt cache.
        cache_creation_tokens: Input tokens written to that cache.
        stop_reason: Why generation stopped. ``max_tokens`` here means a truncated description.
        request_id: The provider's request id, for reporting a failure.
        batch_id: The batch this came from, or None for a live call.
    """

    key: str
    model: str
    prompt_version: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    stop_reason: str = ""
    request_id: str | None = None
    batch_id: str | None = None


@dataclass
class Ledger:
    """The append-only completion cache for one ``(model, prompt version)`` pair.

    JSONL rather than one file per call: 10,817 small files is a slow directory on any filesystem,
    and an append is atomic enough for the failure that actually happens here, which is the process
    being killed part-way through a run.

    Attributes:
        path: The ledger file. Created on first write.
    """

    path: Path
    _seen: dict[str, Completion] = field(default_factory=dict, repr=False)

    @classmethod
    def open(cls, directory: Path, model: str, prompt_version: str) -> "Ledger":
        """Open (and read) the ledger for one model and prompt version.

        Args:
            directory: Where ledgers live.
            model: The model id.
            prompt_version: The prompt version.

        Returns:
            The ledger, with any existing completions already loaded.
        """
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{model}__{prompt_version}")
        ledger = cls(path=directory / f"{safe}.jsonl")
        ledger.reload()
        return ledger

    def reload(self) -> None:
        """Read every completion the ledger holds, ignoring a truncated final line."""
        self._seen.clear()
        if not self.path.is_file():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # A kill mid-append leaves at most one partial line; skip it.
            record["text"] = repair_escapes(record["text"])
            self._seen[record["key"]] = Completion(**record)

    def get(self, key: str) -> Completion | None:
        """Return the cached completion for a key, if there is one.

        Args:
            key: The pathway key.

        Returns:
            The completion, or None.
        """
        return self._seen.get(key)

    def append(self, completion: Completion) -> None:
        """Record one completion, on disk and in memory.

        Args:
            completion: What to record.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(completion), sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._seen[completion.key] = completion

    def __len__(self) -> int:
        """How many completions the ledger holds."""
        return len(self._seen)

    def __contains__(self, key: object) -> bool:
        """Whether a key has a cached completion."""
        return key in self._seen


def custom_id(key: str) -> str:
    """Render a pathway key as a batch ``custom_id``.

    Args:
        key: The pathway key, which contains colons the batch API does not accept.

    Returns:
        The key with every unacceptable character replaced by an underscore.
    """
    return re.sub(r"[^A-Za-z0-9_-]", "_", key)


class LLMClient:
    """A caching Claude adapter: ``complete(request) -> text``, with the cache in front.

    ``docs/brief.md`` D6 specifies a provider-agnostic surface with a Claude adapter first. The
    surface here is the four things this project needs -- complete one, complete many, count tokens,
    and run a batch -- and every one of them consults the ledger before the network.
    """

    def __init__(
        self,
        model: str,
        prompt_version: str,
        ledger: Ledger,
        *,
        api_key: str | None = None,
        response_format: dict[str, object] | None = None,
    ) -> None:
        """Build a client.

        Args:
            model: A key of :data:`MODELS`.
            prompt_version: The prompt version, part of the cache key.
            ledger: The completion cache for this model and prompt version.
            api_key: The key. Read from the environment or ``.env`` when omitted.
            response_format: A structured-output schema, or None for free text.

        Raises:
            ValueError: If the model is not one this module knows how to configure.
        """
        if model not in MODELS:
            raise ValueError(f"unknown model {model!r}; known: {', '.join(sorted(MODELS))}")
        self.model = model
        self.prompt_version = prompt_version
        self.ledger = ledger
        self.response_format = response_format
        self._api_key = api_key or load_api_key()
        self._client = anthropic.Anthropic(api_key=self._api_key, max_retries=0)
        self.calls = 0

    def _params(self, request: Request) -> dict[str, object]:
        """Build the request body for one prompt, shared by the live and batch paths."""
        config = MODELS[self.model]
        output_config: dict[str, object] = {}
        if "effort" in config:
            output_config["effort"] = config["effort"]
        if self.response_format is not None:
            output_config["format"] = self.response_format
        params: dict[str, object] = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "system": [
                {
                    "type": "text",
                    "text": request.system,
                    "cache_control": {"type": "ephemeral", "ttl": "1h"},
                }
            ],
            "messages": [{"role": "user", "content": request.user}],
        }
        if "thinking" in config:
            params["thinking"] = config["thinking"]
        if output_config:
            params["output_config"] = output_config
        return params

    def _send(self, params: dict[str, object]) -> object:
        """The network seam. Swapped by ``monkeypatch`` in the tests."""
        self.calls += 1
        return self._client.messages.create(**params)  # type: ignore[arg-type]

    def _send_with_retry(self, params: dict[str, object]) -> object:
        """Send, retrying the failures that are worth retrying.

        Raises:
            RuntimeError: If every attempt failed.
        """
        last: Exception | None = None
        for attempt in range(RETRIES):
            try:
                return self._send(params)
            except (anthropic.RateLimitError, anthropic.APIConnectionError) as exc:
                last = exc
            except anthropic.APIStatusError as exc:
                if exc.status_code < 500:
                    raise  # 400s are our bug; retrying just spends money on the same mistake.
                last = exc
            if attempt < RETRIES - 1:
                time.sleep(min(2.0**attempt, BACKOFF_CAP))
        raise RuntimeError(f"failed after {RETRIES} attempts: {last}")

    def _completion(self, request: Request, message: object, batch_id: str | None) -> Completion:
        """Turn a provider response into a :class:`Completion`."""
        text = extract_text(message)
        usage = getattr(message, "usage", None)
        return Completion(
            key=request.key,
            model=self.model,
            prompt_version=self.prompt_version,
            text=text,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            stop_reason=getattr(message, "stop_reason", "") or "",
            request_id=getattr(message, "_request_id", None),
            batch_id=batch_id,
        )

    def complete(self, request: Request) -> Completion:
        """Complete one prompt, from cache when possible.

        Args:
            request: The prompt.

        Returns:
            The completion.
        """
        cached = self.ledger.get(request.key)
        if cached is not None:
            return cached
        message = self._send_with_retry(self._params(request))
        completion = self._completion(request, message, None)
        self.ledger.append(completion)
        return completion

    def complete_all(self, requests: Sequence[Request]) -> tuple[Completion, ...]:
        """Complete many prompts concurrently, from cache when possible.

        Args:
            requests: The prompts.

        Returns:
            One completion per request, in request order.
        """
        pending = [r for r in requests if r.key not in self.ledger]
        if pending:
            with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
                for completion in pool.map(self._fetch, pending):
                    self.ledger.append(completion)
        return tuple(self.ledger.get(r.key) or self.complete(r) for r in requests)

    def _fetch(self, request: Request) -> Completion:
        """Complete one prompt without touching the ledger, for the concurrent path."""
        return self._completion(request, self._send_with_retry(self._params(request)), None)

    def count_tokens(self, request: Request) -> int:
        """Count the input tokens one prompt would cost.

        Args:
            request: The prompt.

        Returns:
            The provider's own input-token count.
        """
        response = self._client.messages.count_tokens(
            model=self.model,
            system=request.system,
            messages=[{"role": "user", "content": request.user}],
        )
        return response.input_tokens

    def submit_batch(self, requests: Sequence[Request]) -> str:
        """Submit one chunk of prompts as a batch.

        Args:
            requests: The prompts. Should be no larger than :data:`BATCH_CHUNK`.

        Returns:
            The batch id.
        """
        batch = self._client.messages.batches.create(
            requests=[
                {"custom_id": custom_id(r.key), "params": self._params(r)}  # type: ignore[misc]
                for r in requests
            ]
        )
        return batch.id

    def await_batch(self, batch_id: str, *, poll_seconds: float = BATCH_POLL_SECONDS) -> str:
        """Poll a batch until it ends.

        Args:
            batch_id: The batch.
            poll_seconds: How long to wait between polls.

        Returns:
            The terminal processing status.
        """
        while True:
            batch = self._client.messages.batches.retrieve(batch_id)
            if batch.processing_status == "ended":
                return batch.processing_status
            time.sleep(poll_seconds)

    def collect_batch(self, batch_id: str, requests: Sequence[Request]) -> tuple[Completion, ...]:
        """Read a finished batch's results into the ledger.

        Results arrive in any order, so they are keyed by ``custom_id`` rather than by position.

        Args:
            batch_id: The batch.
            requests: The prompts it was built from, for the id-to-key mapping.

        Returns:
            The completions collected, in the order the provider returned them.
        """
        by_id = {custom_id(r.key): r for r in requests}
        collected: list[Completion] = []
        for result in self._client.messages.batches.results(batch_id):
            request = by_id.get(result.custom_id)
            if request is None or result.result.type != "succeeded":
                continue
            completion = self._completion(request, result.result.message, batch_id)
            self.ledger.append(completion)
            collected.append(completion)
        return tuple(collected)


#: A model may emit ``\\uXXXX`` inside a structured-output JSON string, which survives parsing as a
#: literal backslash-u sequence rather than the character it names. Three of the first thirty-six
#: sampled descriptions did exactly this, so at full scale it would put visible escape sequences
#: into roughly one committed description in twelve.
_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def repair_escapes(text: str) -> str:
    r"""Decode escape sequences a model left literal in its own JSON output.

    Idempotent, and narrow by design: only ``\\uXXXX`` is touched, so a stray backslash in ordinary
    prose is left exactly where it is.

    Args:
        text: The description as parsed.

    Returns:
        The description with any literal ``\\uXXXX`` replaced by the character it names.
    """
    return _ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), text)


def extract_text(message: object) -> str:
    """Pull the description out of a response, structured or not.

    Structured output arrives as JSON in a text block rather than as a separate field, so the
    JSON is parsed here and the plain-text case falls through unchanged.

    Args:
        message: The provider's message object.

    Returns:
        The description, whitespace-collapsed.

    Raises:
        ValueError: If the response carries no text block at all.
    """
    blocks = getattr(message, "content", None) or []
    texts = [b.text for b in blocks if getattr(b, "type", None) == "text"]
    if not texts:
        raise ValueError(f"response carried no text block (stop_reason={
            getattr(message, 'stop_reason', '?')})")
    raw = "\n".join(texts).strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return repair_escapes(" ".join(raw.split()))
    if isinstance(parsed, dict) and "description" in parsed:
        return repair_escapes(" ".join(str(parsed["description"]).split()))
    return repair_escapes(" ".join(raw.split()))


def chunked(items: Sequence[Request], size: int = BATCH_CHUNK) -> Iterator[Sequence[Request]]:
    """Split requests into batch-sized chunks.

    Args:
        items: The requests.
        size: Chunk size.

    Yields:
        Each chunk, in order.
    """
    for start in range(0, len(items), size):
        yield items[start : start + size]


def spend(completions: Iterable[Completion], model: str) -> dict[str, float]:
    """Price a set of completions at the model's list rates.

    Cache reads bill at a tenth of the input rate and cache writes at 1.25x; both are counted
    separately here so a run's summary can show what caching actually saved.

    Args:
        completions: The completions.
        model: The model id, for the rate table.

    Returns:
        ``input``, ``output`` and ``total`` dollars, plus the token counts they came from.
    """
    rates = PRICES[model]
    totals = {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0}
    for completion in completions:
        totals["input"] += completion.input_tokens
        totals["cache_read"] += completion.cache_read_tokens
        totals["cache_write"] += completion.cache_creation_tokens
        totals["output"] += completion.output_tokens
    dollars_in = (
        totals["input"] * rates[0]
        + totals["cache_read"] * rates[0] * 0.1
        + totals["cache_write"] * rates[0] * 1.25
    ) / 1e6
    dollars_out = totals["output"] * rates[1] / 1e6
    return {
        **{f"{k}_tokens": float(v) for k, v in totals.items()},
        "input": dollars_in,
        "output": dollars_out,
        "total": dollars_in + dollars_out,
    }


#: List prices, dollars per million tokens, as ``(input, output)``. Sonnet 5's introductory rate
#: ($2/$10) runs through 2026-08-31; the standard rate is used here so no estimate silently expires.
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}
