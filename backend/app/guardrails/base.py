from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Severity = Literal["low", "med", "high", "critical"]


class GuardResult(BaseModel):
    guard: str
    passed: bool
    severity: Severity
    reason: str = ""
    evidence: str = ""
