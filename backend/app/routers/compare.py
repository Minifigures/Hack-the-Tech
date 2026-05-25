from __future__ import annotations

from fastapi import APIRouter

from ..models import CompareRequest, CompareResponse
from ..rag import baseline, engineered
from ..traces.store import persist

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
def compare(req: CompareRequest) -> CompareResponse:
    base_trace = baseline.answer(req.question)
    eng_trace = engineered.answer(req.question)
    persist(base_trace)
    persist(eng_trace)
    return CompareResponse(baseline=base_trace, engineered=eng_trace)
