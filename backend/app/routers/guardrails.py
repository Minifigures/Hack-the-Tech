from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..guardrails.runner import run_guardrails_on_raw
from ..models import TraceRecord
from ..rag import engineered
from ..traces import store

router = APIRouter(prefix="/api/guardrails", tags=["guardrails"])


class ProbeRequest(BaseModel):
    question: str


class ProbeResponse(BaseModel):
    trace: TraceRecord


@router.post("/probe", response_model=ProbeResponse)
def probe(req: ProbeRequest) -> ProbeResponse:
    """Run the engineered pipeline as an injection/jailbreak probe."""
    trace = engineered.answer(req.question)
    store.persist(trace)
    return ProbeResponse(trace=trace)


@router.post("/baseline-probe")
def baseline_probe(req: ProbeRequest) -> dict:
    """Run baseline guard heuristics on a hand-crafted raw answer.

    Used by the cockpit to show how a *bad* pipeline would have responded.
    """
    from ..llm import mock as _mock

    fake = _mock.chat([{"role": "user", "content": req.question}], structured=False)
    results = run_guardrails_on_raw(
        question=req.question,
        raw_answer_text=fake["content"],
        should_refuse=True,
    )
    return {
        "question": req.question,
        "raw_answer": fake["content"],
        "guards": [g.model_dump() for g in results],
    }
