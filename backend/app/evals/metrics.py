"""Local, RAGAS-shape eval metrics.

Each metric returns a MetricResult(score in [0,1], justification). Definitions
match the upstream RAGAS library where practical, swapped to deterministic
local computations so the demo doesn't require a second eval LLM.
"""
from __future__ import annotations

import re

from ..models import AnswerSchema, MetricResult

_TOKEN = re.compile(r"[A-Za-z0-9]+")

# Common English words that aren't useful signal for grounding/relevance scoring.
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "are",
    "was", "were", "but", "any", "all", "can", "may", "must", "should", "shall",
    "will", "would", "could", "into", "than", "then", "when", "what", "which",
    "where", "who", "whom", "whose", "why", "how", "your", "their", "them",
    "they", "his", "her", "him", "its", "our", "you", "yourself", "ourselves",
    "themselves", "about", "above", "below", "between", "during", "before",
    "after", "under", "over", "such", "some", "many", "each", "every", "very",
    "also", "more", "most", "other", "another", "same", "few", "those", "these",
    "having", "been", "being", "does", "did", "doing", "done", "made", "make",
    "ought", "going", "good", "right", "wrong", "first", "second", "third",
    "let", "say", "said", "tell", "told", "want", "wants", "need", "needs",
    "include", "includes", "including", "across", "around", "among", "without",
    "within", "while", "however", "therefore", "because", "since", "still",
    "also", "just", "only", "even", "ever", "never", "always", "often",
    "sometimes", "actually", "really", "much", "many",
}


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


def _content_tokens(text: str) -> set[str]:
    return {t for t in _tokens(text) if len(t) > 3 and t not in _STOPWORDS}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def faithfulness(answer_text: str, contexts: list[str], *, is_refusal: bool = False) -> MetricResult:
    """Fraction of answer sentences supported by retrieved contexts.

    A sentence is "supported" if at least 40% of its *content* tokens (length > 3
    and not a stopword) appear in the union of context content tokens. This
    mirrors RAGAS' faithfulness in spirit (claim-level groundedness) without
    requiring a second LLM call.

    Refusal answers are vacuously faithful: they make no claims about the
    knowledge base. They are scored 1.0 (matches RAGAS' treatment).
    """
    if is_refusal:
        return MetricResult(
            metric="faithfulness",
            score=1.0,
            justification="refusal — no factual claims to ground",
        )
    sents = _sentences(answer_text)
    if not sents:
        return MetricResult(metric="faithfulness", score=0.0, justification="empty answer")
    ctx_tokens: set[str] = set()
    for c in contexts:
        ctx_tokens.update(_content_tokens(c))
    if not ctx_tokens:
        return MetricResult(
            metric="faithfulness",
            score=0.0,
            justification="no retrieved context tokens to ground against",
        )
    supported = 0
    for s in sents:
        toks = _content_tokens(s)
        if not toks:
            supported += 1
            continue
        hit = sum(1 for t in toks if t in ctx_tokens)
        if hit / len(toks) >= 0.4:
            supported += 1
    score = supported / len(sents)
    return MetricResult(
        metric="faithfulness",
        score=round(score, 3),
        justification=f"{supported}/{len(sents)} answer sentences supported by retrieved context",
    )


def answer_relevance(question: str, answer_text: str, *, is_refusal: bool = False) -> MetricResult:
    """Recall of the question's content tokens in the answer.

    RAGAS' canonical answer_relevance generates synthetic questions from the
    answer and measures embedding similarity to the original question, which
    requires a second LLM call. We approximate with token recall: how much of
    the question's meaningful vocabulary the answer actually addresses.

    Refusals are scored 1.0 because the design intent is to acknowledge the
    question without addressing its content. Penalising refusals here would
    contradict refusal_correctness.
    """
    if is_refusal:
        return MetricResult(
            metric="answer_relevance",
            score=1.0,
            justification="refusal — relevance not penalised",
        )
    q_tokens = _content_tokens(question)
    a_tokens = _content_tokens(answer_text)
    if not q_tokens:
        return MetricResult(metric="answer_relevance", score=1.0, justification="empty question")
    hit = sum(1 for t in q_tokens if t in a_tokens)
    score = hit / len(q_tokens)
    return MetricResult(
        metric="answer_relevance",
        score=round(score, 3),
        justification=f"{hit}/{len(q_tokens)} question content tokens appeared in answer",
    )


def context_precision(retrieved_ids: list[str], expected_ids: list[str]) -> MetricResult:
    if not retrieved_ids:
        return MetricResult(metric="context_precision", score=0.0, justification="no retrieved contexts")
    if not expected_ids:
        # nothing to be wrong about — call it 1.0 only if we retrieved nothing.
        return MetricResult(
            metric="context_precision",
            score=1.0,
            justification="no expected contexts; precision vacuously satisfied",
        )
    expected = set(expected_ids)
    hit = sum(1 for r in retrieved_ids if r in expected)
    score = hit / len(retrieved_ids)
    return MetricResult(
        metric="context_precision",
        score=round(score, 3),
        justification=f"{hit}/{len(retrieved_ids)} retrieved chunks were in expected set",
    )


def context_recall(retrieved_ids: list[str], expected_ids: list[str]) -> MetricResult:
    if not expected_ids:
        return MetricResult(metric="context_recall", score=1.0, justification="no expected contexts")
    expected = set(expected_ids)
    got = sum(1 for e in expected if e in set(retrieved_ids))
    score = got / len(expected)
    return MetricResult(
        metric="context_recall",
        score=round(score, 3),
        justification=f"{got}/{len(expected)} expected chunks present in retrieved set",
    )


def citation_accuracy(answer: AnswerSchema, expected_ids: list[str]) -> MetricResult:
    if answer.refusal_reason:
        # Refusal expected to have no citations; if expected_ids is empty this is satisfied.
        if not expected_ids:
            return MetricResult(
                metric="citation_accuracy",
                score=1.0,
                justification="refusal with no expected citations — satisfied",
            )
        return MetricResult(
            metric="citation_accuracy",
            score=0.0,
            justification="refused but expected to cite",
        )
    if not expected_ids:
        return MetricResult(
            metric="citation_accuracy",
            score=1.0 if not answer.citations else 0.5,
            justification="no expected citations; partial credit if any cited",
        )
    cited = {c.source_id for c in answer.citations}
    expected = set(expected_ids)
    overlap = cited & expected
    if not cited:
        return MetricResult(metric="citation_accuracy", score=0.0, justification="no citations produced")
    precision = len(overlap) / max(1, len(cited))
    recall = len(overlap) / max(1, len(expected))
    f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    return MetricResult(
        metric="citation_accuracy",
        score=round(f1, 3),
        justification=f"F1 of cited vs expected: precision={precision:.2f}, recall={recall:.2f}",
    )


def structured_output_validity(parsed_ok: bool) -> MetricResult:
    return MetricResult(
        metric="structured_output_validity",
        score=1.0 if parsed_ok else 0.0,
        justification="response parsed into typed schema" if parsed_ok else "schema parse failed",
    )


def refusal_correctness(should_refuse: bool, did_refuse: bool) -> MetricResult:
    correct = should_refuse == did_refuse
    return MetricResult(
        metric="refusal_correctness",
        score=1.0 if correct else 0.0,
        justification=f"should_refuse={should_refuse}, did_refuse={did_refuse}",
    )


def keyword_coverage(answer_text: str, expected_keywords: list[str]) -> MetricResult:
    if not expected_keywords:
        return MetricResult(metric="keyword_coverage", score=1.0, justification="no expected keywords")
    body = answer_text.lower()
    hits = sum(1 for k in expected_keywords if k.lower() in body)
    score = hits / len(expected_keywords)
    return MetricResult(
        metric="keyword_coverage",
        score=round(score, 3),
        justification=f"{hits}/{len(expected_keywords)} expected keywords appeared in answer",
    )
