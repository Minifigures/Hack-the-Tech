from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import TraceRecord
from ..traces import store

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("", response_model=list[TraceRecord])
def list_recent(limit: int = 50, pipeline: str | None = None) -> list[TraceRecord]:
    return store.list_recent(limit=limit, pipeline=pipeline)


@router.get("/{trace_id}", response_model=TraceRecord)
def get_trace(trace_id: str) -> TraceRecord:
    t = store.get(trace_id)
    if t is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return t
