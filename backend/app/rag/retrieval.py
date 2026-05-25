"""Retrieval.

`topk` is the baseline retrieval: cosine over the weak hash embedding. It's
roughly what a junior team gets when they grab the first vector store they
find. The engineered pipeline calls `bm25_topk` instead, which uses a real
lexical scoring function. The engineered pipeline also unions both candidate
pools and reranks them, so the difference shows clearly in traces.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from .index import Chunk, cosine, hash_embed, load_index

_TOKEN = re.compile(r"[A-Za-z0-9]+")
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "are",
    "was", "were", "but", "any", "all", "can", "may", "must", "should", "shall",
    "will", "would", "could", "into", "than", "then", "when", "what", "which",
    "where", "who", "whom", "whose", "why", "how", "your", "their", "them",
    "they", "his", "her", "him", "its", "our", "you", "yourself", "ourselves",
    "themselves", "about", "above", "below", "between", "during", "before",
    "after", "under", "over", "such", "some", "many", "each", "every", "very",
    "also", "more", "most", "other", "another", "same", "few", "those", "these",
    "having", "been", "being", "does", "did", "doing", "done", "made", "make",
    "ought", "going",
}


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text) if t.lower() not in _STOP]


@dataclass
class Hit:
    chunk: Chunk
    score: float


_CACHE: list[Chunk] | None = None


def _index() -> list[Chunk]:
    global _CACHE
    if _CACHE is None:
        _CACHE = load_index()
    return _CACHE


def reset_cache() -> None:
    global _CACHE, _BM25_STATE
    _CACHE = None
    _BM25_STATE = None


# ---------- baseline (weak) ----------

def topk(query: str, k: int = 8) -> list[Hit]:
    q_vec = hash_embed(query)
    scored = [(cosine(q_vec, c.embedding), c) for c in _index()]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [Hit(chunk=c, score=round(s, 4)) for s, c in scored[:k]]


# ---------- engineered (BM25) ----------

_BM25_STATE: dict | None = None


def _bm25_state() -> dict:
    global _BM25_STATE
    if _BM25_STATE is not None:
        return _BM25_STATE
    chunks = _index()
    docs = [_tokens(c.text) for c in chunks]
    n = len(docs)
    avgdl = (sum(len(d) for d in docs) / n) if n else 0.0
    df: Counter[str] = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    tf = [Counter(d) for d in docs]
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
    _BM25_STATE = {"tf": tf, "idf": idf, "len": [len(d) for d in docs], "avgdl": avgdl, "n": n}
    return _BM25_STATE


def bm25_topk(query: str, k: int = 8, *, k1: float = 1.5, b: float = 0.75) -> list[Hit]:
    state = _bm25_state()
    if state["n"] == 0:
        return []
    q_terms = _tokens(query)
    scores: list[tuple[float, int]] = []
    avgdl = state["avgdl"] or 1.0
    for i, tf in enumerate(state["tf"]):
        dl = state["len"][i]
        s = 0.0
        for t in q_terms:
            f = tf.get(t, 0)
            if f == 0:
                continue
            idf = state["idf"].get(t, 0.0)
            denom = f + k1 * (1 - b + b * dl / avgdl)
            s += idf * (f * (k1 + 1)) / denom
        if s > 0:
            scores.append((s, i))
    scores.sort(key=lambda t: t[0], reverse=True)
    chunks = _index()
    return [Hit(chunk=chunks[i], score=round(s, 4)) for s, i in scores[:k]]


def union(hits_a: list[Hit], hits_b: list[Hit], k: int) -> list[Hit]:
    """Merge two hit lists, keeping the highest score per source_id."""
    best: dict[str, Hit] = {}
    for h in [*hits_a, *hits_b]:
        prior = best.get(h.chunk.source_id)
        if prior is None or h.score > prior.score:
            best[h.chunk.source_id] = h
    merged = sorted(best.values(), key=lambda h: h.score, reverse=True)
    return merged[:k]
