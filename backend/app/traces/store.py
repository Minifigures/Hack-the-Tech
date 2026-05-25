from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import select

from ..db import get_session
from ..models import TraceRecord, TraceRow


def persist(trace: TraceRecord, run_id: Optional[str] = None) -> str:
    row = TraceRow(
        id=trace.trace_id,
        run_id=run_id,
        pipeline=trace.pipeline,
        question=trace.question,
        final_answer_json=json.dumps(trace.final_answer),
        total_ms=trace.total_ms,
        cost_usd=trace.cost_usd,
        spans_json=json.dumps([s.model_dump() for s in trace.spans]),
        guardrails_json=json.dumps(trace.guardrails),
    )
    with get_session() as s:
        s.add(row)
        s.commit()
    return trace.trace_id


def get(trace_id: str) -> TraceRecord | None:
    with get_session() as s:
        row = s.get(TraceRow, trace_id)
        if row is None:
            return None
        return _row_to_record(row)


def list_recent(limit: int = 50, pipeline: Optional[str] = None) -> list[TraceRecord]:
    with get_session() as s:
        stmt = select(TraceRow).order_by(TraceRow.created_at.desc()).limit(limit)
        if pipeline:
            stmt = select(TraceRow).where(TraceRow.pipeline == pipeline).order_by(
                TraceRow.created_at.desc()
            ).limit(limit)
        rows = s.exec(stmt).all()
        return [_row_to_record(r) for r in rows]


def _row_to_record(row: TraceRow) -> TraceRecord:
    spans = json.loads(row.spans_json or "[]")
    guards = json.loads(row.guardrails_json or "[]")
    return TraceRecord(
        trace_id=row.id,
        pipeline=row.pipeline,  # type: ignore[arg-type]
        question=row.question,
        final_answer=json.loads(row.final_answer_json or "{}"),
        total_ms=row.total_ms,
        cost_usd=row.cost_usd,
        spans=spans,
        guardrails=guards,
        created_at=row.created_at,
    )


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
