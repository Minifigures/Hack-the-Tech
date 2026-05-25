"""Pydantic + SQLModel schemas for EvalForge."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

Pipeline = Literal["baseline", "engineered"]
Verdict = Literal["PASS", "FAIL"]


# ---------- Pydantic (transport) ----------

class Citation(BaseModel):
    source_id: str
    quote: str = ""


class AnswerSchema(BaseModel):
    """The typed contract the engineered RAG enforces on the LLM."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    refusal_reason: Optional[str] = None


class SpanRecord(BaseModel):
    name: str
    start_ms: float
    end_ms: float
    attrs: dict[str, Any] = Field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return round(self.end_ms - self.start_ms, 2)


class TraceRecord(BaseModel):
    trace_id: str
    pipeline: Pipeline
    question: str
    final_answer: dict[str, Any]
    total_ms: float
    cost_usd: float
    spans: list[SpanRecord]
    guardrails: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CompareRequest(BaseModel):
    question: str


class CompareResponse(BaseModel):
    baseline: TraceRecord
    engineered: TraceRecord


class MetricResult(BaseModel):
    metric: str
    score: float
    justification: str = ""


class QuestionEvalRow(BaseModel):
    question_id: str
    question: str
    pipeline: Pipeline
    metrics: list[MetricResult]
    answer: str
    citations: list[str]
    cost_usd: float
    latency_ms: float
    guardrails_passed: int
    guardrails_total: int


class EvalAggregate(BaseModel):
    pipeline: Pipeline
    faithfulness_mean: float
    answer_relevance_mean: float
    context_precision_mean: float
    context_recall_mean: float
    citation_accuracy_mean: float
    structured_output_validity: float
    refusal_correctness: float
    pii_leak_count: int
    prompt_injection_bypass_count: int
    p95_latency_ms: float
    cost_per_answer_usd: float
    questions: int


class EvalRunResult(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    aggregates: dict[Pipeline, EvalAggregate]
    rows: list[QuestionEvalRow]


class FailedGate(BaseModel):
    name: str
    observed: float | int
    threshold: float | int
    direction: Literal[">=", "<=", "="]


class GateResult(BaseModel):
    run_id: str
    pipeline: Pipeline
    verdict: Verdict
    failed_gates: list[FailedGate]
    summary_markdown: str


class DeployGateResponse(BaseModel):
    run_id: str
    baseline: GateResult
    engineered: GateResult


# ---------- SQLModel (persistence) ----------

class RunRow(SQLModel, table=True):
    __tablename__ = "runs"
    id: str = SQLField(primary_key=True)
    pipeline: str = SQLField(default="batch")
    started_at: datetime = SQLField(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    status: str = SQLField(default="pending")
    payload_json: str = SQLField(default="{}")


class TraceRow(SQLModel, table=True):
    __tablename__ = "traces"
    id: str = SQLField(primary_key=True)
    run_id: Optional[str] = SQLField(default=None, index=True)
    pipeline: str = SQLField(index=True)
    question: str
    final_answer_json: str
    total_ms: float = 0.0
    cost_usd: float = 0.0
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    spans_json: str = SQLField(default="[]")
    guardrails_json: str = SQLField(default="[]")


class DeployGateRow(SQLModel, table=True):
    __tablename__ = "deploy_gate_runs"
    id: str = SQLField(primary_key=True)
    run_id: str = SQLField(index=True)
    pipeline: str
    verdict: str
    failed_gates_json: str
    summary_md: str
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
