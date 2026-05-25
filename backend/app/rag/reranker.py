"""Lexical-semantic rerank.

We blend the semantic score (already cosine-based) with a normalised lexical
overlap (BM25-flavoured) to demonstrate the reranker reordering the top-3.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .retrieval import Hit

_TOKEN = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


def _bm25ish(query: str, doc: str) -> float:
    q_terms = set(_tokens(query))
    if not q_terms:
        return 0.0
    d_tokens = _tokens(doc)
    if not d_tokens:
        return 0.0
    counts = Counter(d_tokens)
    overlap = sum(1 for t in q_terms if counts.get(t, 0) > 0)
    coverage = overlap / max(1, len(q_terms))
    avg_count = sum(counts.get(t, 0) for t in q_terms) / max(1, len(q_terms))
    saturation = avg_count / (avg_count + 1.5)
    length_norm = 1.0 / (1.0 + math.log(1 + len(d_tokens) / 80.0))
    return round(0.6 * coverage + 0.3 * saturation + 0.1 * length_norm, 4)


def rerank(query: str, hits: list[Hit], *, alpha: float = 0.6) -> list[Hit]:
    rescored: list[Hit] = []
    for h in hits:
        lex = _bm25ish(query, h.chunk.text)
        blended = round(alpha * h.score + (1 - alpha) * lex, 4)
        rescored.append(Hit(chunk=h.chunk, score=blended))
    rescored.sort(key=lambda h: h.score, reverse=True)
    return rescored
