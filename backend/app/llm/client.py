"""Unified LLM client. Falls back to mock when no API key is present."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ..config import settings
from . import mock

# USD per 1M tokens (approximate; only used for cost-tracking display).
# Mock LLM uses these constants so cost is realistic in mock mode.
PRICING_PER_MTOK = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "mock-haiku-evalforge": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
}


@dataclass
class ChatResult:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float

    @property
    def cost_usd(self) -> float:
        price = PRICING_PER_MTOK.get(self.model, {"input": 1.0, "output": 5.0})
        return round(
            (self.input_tokens * price["input"] + self.output_tokens * price["output"]) / 1_000_000,
            6,
        )


def chat(messages: list[dict[str, str]], *, structured: bool = False, model: str | None = None) -> ChatResult:
    if settings.use_mock:
        out = mock.chat(messages, structured=structured)
        return ChatResult(
            content=out["content"],
            model=out["model"],
            input_tokens=out["usage"]["input_tokens"],
            output_tokens=out["usage"]["output_tokens"],
            latency_ms=out["latency_ms"],
        )

    # Real Anthropic call. Kept simple; we never reach this in mock mode.
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
    )


def is_mock() -> bool:
    return settings.use_mock


def supports_known(question: str) -> bool:
    return mock.slug_of(question) in mock.known_slugs()
