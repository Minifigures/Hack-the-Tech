"""Unified LLM client.

Provider selection happens at call time based on environment:

- `EVALFORGE_USE_MOCK=always` → deterministic mock (the demo default)
- `EVALFORGE_USE_MOCK=never` → real call, picks the first provider from
  `EVALFORGE_PROVIDER_ORDER` whose API key is set
- `EVALFORGE_USE_MOCK=auto` (default) → real call if any key is set,
  otherwise mock

For batch operations (eval runner, deploy gate) we also expose a
context-managed `mock_only_scope()` that forces mock inside the block,
because hitting a free-tier provider 50 times in one HTTP request exceeds
both Vercel Hobby's 60s function timeout and Groq's 30 RPM rate limit.

Adding a new provider is two functions: `_call_<provider>` and a branch in
`chat`. Each provider returns a `ChatResult` so the rest of the pipeline
(traces, cost tracking, guardrails) doesn't care which model produced the
answer.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Iterator

from ..config import settings
from . import mock


_force_mock: ContextVar[bool] = ContextVar("_force_mock", default=False)


@contextmanager
def mock_only_scope() -> Iterator[None]:
    """Force mock LLM inside this block. Used by the eval runner."""
    token = _force_mock.set(True)
    try:
        yield
    finally:
        _force_mock.reset(token)

# USD per 1M tokens (approximate; only used for cost-tracking display).
# Groq is currently free to call but we record a notional price so the cost
# panels still render a number for comparison purposes.
PRICING_PER_MTOK = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "mock-haiku-evalforge": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}


@dataclass
class ChatResult:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    provider: str = "mock"

    @property
    def cost_usd(self) -> float:
        price = PRICING_PER_MTOK.get(self.model, {"input": 1.0, "output": 5.0})
        return round(
            (self.input_tokens * price["input"] + self.output_tokens * price["output"]) / 1_000_000,
            6,
        )


# ---------- providers ----------

def _call_mock(messages: list[dict[str, str]], structured: bool) -> ChatResult:
    out = mock.chat(messages, structured=structured)
    return ChatResult(
        content=out["content"],
        model=out["model"],
        input_tokens=out["usage"]["input_tokens"],
        output_tokens=out["usage"]["output_tokens"],
        latency_ms=out["latency_ms"],
        provider="mock",
    )


def _call_anthropic(messages: list[dict[str, str]], structured: bool, model: str | None) -> ChatResult:
    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    system = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    user_msgs = [m for m in messages if m.get("role") != "system"]
    started = time.perf_counter()
    resp = client.messages.create(
        model=model or settings.EVALFORGE_DEFAULT_MODEL,
        max_tokens=1024,
        system=system or None,
        messages=user_msgs,  # type: ignore[arg-type]
    )
    latency_ms = (time.perf_counter() - started) * 1000.0
    text_parts: list[str] = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(getattr(block, "text", ""))
    return ChatResult(
        content="".join(text_parts),
        model=resp.model,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        latency_ms=latency_ms,
        provider="anthropic",
    )


def _call_groq(messages: list[dict[str, str]], structured: bool, model: str | None) -> ChatResult:
    """Call Groq's OpenAI-compatible Chat Completions API.

    Groq is genuinely free with rate limits and OpenAI-compatible, which
    makes it ideal for hackathon-grade real-LLM demos. When `structured` is
    true we ask the model for JSON output explicitly so the engineered
    pipeline's Pydantic parse still works.
    """
    from groq import Groq  # type: ignore

    client = Groq(api_key=settings.GROQ_API_KEY)
    chat_model = model or settings.EVALFORGE_GROQ_MODEL
    started = time.perf_counter()
    kwargs: dict[str, Any] = {
        "model": chat_model,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.2,
    }
    if structured:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    latency_ms = (time.perf_counter() - started) * 1000.0
    content = resp.choices[0].message.content or ""
    return ChatResult(
        content=content,
        model=chat_model,
        input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
        output_tokens=resp.usage.completion_tokens if resp.usage else 0,
        latency_ms=latency_ms,
        provider="groq",
    )


# ---------- public API ----------

def chat(
    messages: list[dict[str, str]],
    *,
    structured: bool = False,
    model: str | None = None,
    force_mock: bool = False,
) -> ChatResult:
    if force_mock or _force_mock.get() or settings.use_mock:
        return _call_mock(messages, structured)
    provider = settings.active_provider
    try:
        if provider == "groq":
            return _call_groq(messages, structured, model)
        if provider == "anthropic":
            return _call_anthropic(messages, structured, model)
    except Exception as exc:  # noqa: BLE001  any provider failure
        # Fall back to mock so the demo never crashes from a flaky provider.
        out = _call_mock(messages, structured)
        out.content = out.content or f"[fallback to mock after {provider} error: {exc}]"
        return out
    return _call_mock(messages, structured)


def is_mock() -> bool:
    return settings.use_mock


def supports_known(question: str) -> bool:
    return mock.slug_of(question) in mock.known_slugs()
