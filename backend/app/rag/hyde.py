"""HyDE (Hypothetical Document Embeddings) query expansion.

Asks the LLM to produce a *plausible* answer to the user's question, then
embeds that hypothetical answer for retrieval. We union the HyDE retrieval set
with the original retrieval set in the engineered pipeline.
"""
from __future__ import annotations

from ..llm.client import chat
from ..traces import tracer


HYDE_SYSTEM = (
    "You are an expert in healthcare, financial compliance, and cybersecurity. "
    "Given a user question, write one concise hypothetical paragraph that would "
    "directly answer it if you had the source material. Use the same vocabulary "
    "the source documents would use. Do not say you are uncertain; produce the "
    "hypothetical answer text only, no preamble."
)


def expand(question: str) -> str:
    with tracer.span("hyde.expand") as attrs:
        result = chat(
            messages=[
                {"role": "system", "content": HYDE_SYSTEM},
                {"role": "user", "content": question},
            ],
            structured=False,
        )
        tracer.add_cost(result.cost_usd)
        attrs.update(
            {
                "tokens_in": result.input_tokens,
                "tokens_out": result.output_tokens,
                "cost_usd": result.cost_usd,
                "model": result.model,
                "hypothetical_len": len(result.content),
            }
        )
        return result.content
