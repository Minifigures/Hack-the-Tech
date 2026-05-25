"""Baseline RAG pipeline.

Naive top-k cosine retrieval, single instruction prompt, raw string output, no
citations, no guards. This is the "weekend chatbot" comparison point.
"""
from __future__ import annotations

from typing import Any

from ..llm.client import chat
from ..models import TraceRecord
from ..traces import tracer
from . import retrieval


BASELINE_SYSTEM = (
    "You are a friendly assistant. Answer the user's question briefly and confidently. "
    "Do not over-qualify. Do not include citations or footnotes."
)


def _build_prompt(question: str, hits: list[retrieval.Hit]) -> list[dict[str, str]]:
    # The baseline deliberately doesn't even surface the retrieved context to the
    # model in a structured way; it concatenates lightly. This mirrors a lot of
    # weekend RAG: retrieve + drop into prompt + hope.
    ctx = "\n".join(h.chunk.text[:300] for h in hits[:4])
    user = f"Background: {ctx}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": user},
    ]


def answer(question: str) -> TraceRecord:
    with tracer.start_trace(pipeline="baseline", question=question) as trace:
        with tracer.span("retrieve.topk") as attrs:
            hits = retrieval.topk(question, k=4)
            attrs.update({"k": 4, "hit_ids": [h.chunk.source_id for h in hits]})

        with tracer.span("prompt.build") as attrs:
            messages = _build_prompt(question, hits)
            attrs["prompt_len"] = sum(len(m["content"]) for m in messages)

        with tracer.span("llm.chat") as attrs:
            result = chat(messages, structured=False)
            tracer.add_cost(result.cost_usd)
            attrs.update(
                {
                    "model": result.model,
                    "tokens_in": result.input_tokens,
                    "tokens_out": result.output_tokens,
                    "cost_usd": result.cost_usd,
                    "latency_ms": result.latency_ms,
                }
            )

        final: dict[str, Any] = {
            "answer": result.content,
            "citations": [],
            "confidence": 0.5,
            "refusal_reason": None,
            "raw": True,
        }
        trace.set_final(final)
        return trace.finish()
