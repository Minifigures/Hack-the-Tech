"""Tiny Langfuse-shape tracer.

Mirrors the Langfuse trace/span concept so a future swap to the SaaS is a single
adapter file. Stored locally in SQLite via traces/store.py.
"""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

from ..models import SpanRecord, TraceRecord

_current_trace: ContextVar["TraceBuilder | None"] = ContextVar("_current_trace", default=None)


class TraceBuilder:
    def __init__(self, pipeline: str, question: str):
        self.trace_id = uuid.uuid4().hex[:12]
        self.pipeline = pipeline
        self.question = question
        self.spans: list[SpanRecord] = []
        self.guardrails: list[dict[str, Any]] = []
        self.final_answer: dict[str, Any] = {}
        self.started_at = time.perf_counter() * 1000.0
        self.finished_at: float | None = None
        self.cost_usd = 0.0

    def add_span(self, name: str, start_ms: float, end_ms: float, attrs: dict[str, Any]) -> None:
        self.spans.append(SpanRecord(name=name, start_ms=start_ms, end_ms=end_ms, attrs=attrs))

    def set_final(self, answer: dict[str, Any]) -> None:
        self.final_answer = answer

    def add_cost(self, usd: float) -> None:
        self.cost_usd = round(self.cost_usd + usd, 6)

    def add_guardrails(self, items: list[dict[str, Any]]) -> None:
        self.guardrails.extend(items)

    def finish(self) -> TraceRecord:
        self.finished_at = time.perf_counter() * 1000.0
        return TraceRecord(
            trace_id=self.trace_id,
            pipeline=self.pipeline,  # type: ignore[arg-type]
            question=self.question,
            final_answer=self.final_answer,
            total_ms=round(self.finished_at - self.started_at, 2),
            cost_usd=round(self.cost_usd, 6),
            spans=self.spans,
            guardrails=self.guardrails,
        )


@contextmanager
def start_trace(pipeline: str, question: str) -> Iterator[TraceBuilder]:
    builder = TraceBuilder(pipeline=pipeline, question=question)
    token = _current_trace.set(builder)
    try:
        yield builder
    finally:
        _current_trace.reset(token)


def _current() -> TraceBuilder | None:
    return _current_trace.get()


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
    """Context manager for a single span. Mutate the yielded dict to attach attrs."""
    start = time.perf_counter() * 1000.0
    payload: dict[str, Any] = dict(attrs)
    try:
        yield payload
    finally:
        end = time.perf_counter() * 1000.0
        builder = _current()
        if builder is not None:
            builder.add_span(name=name, start_ms=start, end_ms=end, attrs=payload)


def add_cost(usd: float) -> None:
    builder = _current()
    if builder is not None:
        builder.add_cost(usd)


def record_guardrails(items: list[dict[str, Any]]) -> None:
    builder = _current()
    if builder is not None:
        builder.add_guardrails(items)
