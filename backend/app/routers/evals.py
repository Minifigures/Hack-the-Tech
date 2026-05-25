from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db import get_session
from ..evals.dataset import load_golden
from ..evals.runner import run_full_eval
from ..models import EvalRunResult, RunRow

router = APIRouter(prefix="/api/evals", tags=["evals"])

# Cache of the last full run, so the eval dashboard remains fast.
_LAST: EvalRunResult | None = None


@router.get("/dataset")
def dataset() -> dict[str, Any]:
    return {"items": load_golden(), "count": len(load_golden())}


@router.post("/run", response_model=EvalRunResult)
def run() -> EvalRunResult:
    global _LAST
    _LAST = run_full_eval()
    return _LAST


@router.get("/latest", response_model=EvalRunResult)
def latest() -> EvalRunResult:
    global _LAST
    if _LAST is not None:
        return _LAST
    # try DB
    with get_session() as s:
        stmt = select(RunRow).where(RunRow.status == "ok").order_by(RunRow.started_at.desc()).limit(1)
        row = s.exec(stmt).first()
    if row is None:
        raise HTTPException(status_code=404, detail="No eval run found. Trigger /api/evals/run.")
    payload = json.loads(row.payload_json or "{}")
    # We only persist aggregates in the row; rebuild a thin response.
    aggregates = payload.get("aggregates", {})
    return EvalRunResult(
        run_id=row.id,
        started_at=row.started_at,
        finished_at=row.finished_at or row.started_at,
        aggregates=aggregates,
        rows=[],
    )


@router.get("/runs", response_model=list[dict[str, Any]])
def list_runs() -> list[dict[str, Any]]:
    with get_session() as s:
        rows = s.exec(select(RunRow).order_by(RunRow.started_at.desc()).limit(20)).all()
    return [
        {
            "run_id": r.id,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "status": r.status,
        }
        for r in rows
    ]
