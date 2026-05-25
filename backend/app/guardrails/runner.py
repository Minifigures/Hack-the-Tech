from __future__ import annotations

from typing import Optional

from ..models import AnswerSchema
from . import citation, injection, jailbreak, pii, refusal
from .base import GuardResult


def run_guardrails(
    *,
    question: str,
    answer: AnswerSchema,
    contexts: list[str],
    allowed_source_ids: set[str],
    should_refuse: Optional[bool] = None,
) -> list[GuardResult]:
    return [
        pii.check(answer.answer),
        injection.check(question, answer.refusal_reason),
        jailbreak.check(question, answer.refusal_reason),
        refusal.check(answer.answer, answer.refusal_reason, should_refuse),
        citation.check(answer, allowed_source_ids),
    ]


def run_guardrails_on_raw(
    *,
    question: str,
    raw_answer_text: str,
    should_refuse: Optional[bool] = None,
) -> list[GuardResult]:
    """For the baseline pipeline which has no structured output."""
    schema = AnswerSchema(answer=raw_answer_text, citations=[], confidence=0.5, refusal_reason=None)
    return [
        pii.check(raw_answer_text),
        injection.check(question, None),
        jailbreak.check(question, None),
        refusal.check(raw_answer_text, None, should_refuse),
        citation.check(schema, allowed_source_ids=set()),
    ]
