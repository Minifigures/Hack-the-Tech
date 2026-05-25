from __future__ import annotations

from ..models import AnswerSchema
from .base import GuardResult


def check(answer: AnswerSchema, allowed_source_ids: set[str]) -> GuardResult:
    # Refusals are exempt — they should not invent citations.
    if answer.refusal_reason:
        return GuardResult(
            guard="citation_enforcement",
            passed=True,
            severity="low",
            reason="Refusal — citations not required.",
        )

    if not answer.citations:
        return GuardResult(
            guard="citation_enforcement",
            passed=False,
            severity="high",
            reason="Non-refusal answer has zero citations.",
        )

    bad = [c.source_id for c in answer.citations if c.source_id not in allowed_source_ids]
    if bad:
        return GuardResult(
            guard="citation_enforcement",
            passed=False,
            severity="high",
            reason=f"Citation refers to source_id not in retrieved context: {bad[:3]}",
            evidence=", ".join(bad[:3]),
        )
    return GuardResult(
        guard="citation_enforcement",
        passed=True,
        severity="low",
        reason=f"All {len(answer.citations)} citations point at retrieved sources.",
    )
