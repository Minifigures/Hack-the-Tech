from __future__ import annotations

import re

from .base import GuardResult

# Conservative patterns. False-positive friendly because the cost of leaking
# real PII is much higher than the cost of refusing to echo a number.
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE = re.compile(r"\b(?:\+?1[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CREDIT_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
MRN = re.compile(r"\bMRN[:\s-]?\d{4,}\b", re.IGNORECASE)


def check(answer_text: str) -> GuardResult:
    leaks: list[str] = []
    for label, pat in (
        ("SSN", SSN),
        ("phone", PHONE),
        ("email", EMAIL),
        ("credit_card", CREDIT_CARD),
        ("MRN", MRN),
    ):
        if pat.search(answer_text):
            leaks.append(label)
    if leaks:
        return GuardResult(
            guard="pii_leak",
            passed=False,
            severity="high",
            reason=f"Answer contains PII patterns: {', '.join(leaks)}",
            evidence=", ".join(sorted(set(leaks))),
        )
    return GuardResult(guard="pii_leak", passed=True, severity="low", reason="No PII patterns detected.")
