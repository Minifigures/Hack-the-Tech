from __future__ import annotations

import json
import statistics
from datetime import datetime
from typing import Any

from ..guardrails.runner import run_guardrails, run_guardrails_on_raw
from ..models import (
    AnswerSchema,
    EvalAggregate,
    EvalRunResult,
    MetricResult,
    Pipeline,
    QuestionEvalRow,
    RunRow,
    TraceRecord,
)
from ..rag import baseline, engineered
from ..traces.store import new_run_id, persist
from ..db import get_session
from . import metrics
from .dataset import load_golden


def _run_pipeline(pipeline: Pipeline, question: str) -> TraceRecord:
    if pipeline == "baseline":
        return baseline.answer(question)
    return engineered.answer(question)


def _parse_final(final: dict[str, Any]) -> tuple[AnswerSchema, bool]:
    try:
        schema = AnswerSchema(
            answer=final.get("answer", ""),
            citations=final.get("citations", []),
            confidence=final.get("confidence", 0.5),
            refusal_reason=final.get("refusal_reason"),
        )
        parsed_ok = not final.get("raw", False) and final.get("refusal_reason") != "parse_failure"
        return schema, parsed_ok
    except Exception:
        return AnswerSchema(answer=str(final), citations=[], confidence=0.0, refusal_reason="parse_failure"), False


def _retrieved_ids(trace: TraceRecord) -> list[str]:
    for span in trace.spans:
        if span.name == "rerank":
            return span.attrs.get("after_top", [])
        if span.name == "retrieve.topk" and "hit_ids" in span.attrs:
            return span.attrs.get("hit_ids", [])
    return []


def _retrieved_texts(trace: TraceRecord) -> list[str]:
    """Best-effort context texts for faithfulness scoring."""
    # We didn't persist full chunk text inside the span (would bloat traces).
    # Re-fetch from the index using the source_ids.
    from ..rag.index import load_index

    ids = set(_retrieved_ids(trace))
    out: list[str] = []
    for chunk in load_index():
        if chunk.source_id in ids:
            out.append(chunk.text)
    return out


def _row_for(item: dict[str, Any], trace: TraceRecord, pipeline: Pipeline) -> tuple[QuestionEvalRow, list[MetricResult]]:
    schema, parsed_ok = _parse_final(trace.final_answer)
    contexts = _retrieved_texts(trace)
    retrieved_ids = _retrieved_ids(trace)

    is_refusal = bool(schema.refusal_reason)
    metric_list = [
        metrics.faithfulness(schema.answer, contexts, is_refusal=is_refusal),
        metrics.answer_relevance(item["question"], schema.answer, is_refusal=is_refusal),
        metrics.context_precision(retrieved_ids, item.get("expected_citation_ids", [])),
        metrics.context_recall(retrieved_ids, item.get("expected_citation_ids", [])),
        metrics.citation_accuracy(schema, item.get("expected_citation_ids", [])),
        metrics.structured_output_validity(parsed_ok),
        metrics.refusal_correctness(item.get("should_refuse", False), is_refusal),
        metrics.keyword_coverage(schema.answer, item.get("expected_answer_keywords", [])),
    ]

    # Guardrails (engineered runs them inline; for baseline we run a lite version now).
    if pipeline == "engineered":
        guards = trace.guardrails
    else:
        guards = [g.model_dump() for g in run_guardrails_on_raw(
            question=item["question"],
            raw_answer_text=schema.answer,
            should_refuse=item.get("should_refuse", False),
        )]
    passed = sum(1 for g in guards if g["passed"])
    total = len(guards)

    row = QuestionEvalRow(
        question_id=item["id"],
        question=item["question"],
        pipeline=pipeline,
        metrics=metric_list,
        answer=schema.answer,
        citations=[c.source_id for c in schema.citations] if schema.citations else [],
        cost_usd=trace.cost_usd,
        latency_ms=trace.total_ms,
        guardrails_passed=passed,
        guardrails_total=total,
    )
    return row, metric_list


def _aggregate(pipeline: Pipeline, rows: list[QuestionEvalRow], traces: list[TraceRecord]) -> EvalAggregate:
    metric_by_name: dict[str, list[float]] = {}
    for r in rows:
        for m in r.metrics:
            metric_by_name.setdefault(m.metric, []).append(m.score)

    def mean(name: str, default: float = 0.0) -> float:
        vals = metric_by_name.get(name, [])
        return round(statistics.fmean(vals), 3) if vals else default

    # PII leaks across runs
    pii_leak_count = 0
    injection_bypass_count = 0
    for t in traces:
        for g in t.guardrails:
            if g["guard"] == "pii_leak" and not g["passed"]:
                pii_leak_count += 1
            if g["guard"] == "prompt_injection" and not g["passed"]:
                injection_bypass_count += 1
    # For baseline (which has no inline guardrails on the trace) count from rows
    if pipeline == "baseline":
        # Re-run guard checks on baseline outputs implicit in `rows.answer`.
        for r in rows:
            guards = run_guardrails_on_raw(
                question=r.question,
                raw_answer_text=r.answer,
                should_refuse=False,
            )
            for g in guards:
                if g.guard == "pii_leak" and not g.passed:
                    pii_leak_count += 1
                if g.guard == "prompt_injection" and not g.passed:
                    injection_bypass_count += 1

    latencies = [t.total_ms for t in traces]
    costs = [t.cost_usd for t in traces]
    latencies.sort()
    p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0

    return EvalAggregate(
        pipeline=pipeline,
        faithfulness_mean=mean("faithfulness"),
        answer_relevance_mean=mean("answer_relevance"),
        context_precision_mean=mean("context_precision"),
        context_recall_mean=mean("context_recall"),
        citation_accuracy_mean=mean("citation_accuracy"),
        structured_output_validity=mean("structured_output_validity"),
        refusal_correctness=mean("refusal_correctness"),
        pii_leak_count=pii_leak_count,
        prompt_injection_bypass_count=injection_bypass_count,
        p95_latency_ms=round(p95, 2),
        cost_per_answer_usd=round(statistics.fmean(costs), 6) if costs else 0.0,
        questions=len(rows),
    )


def run_full_eval() -> EvalRunResult:
    items = load_golden()
    run_id = new_run_id()
    started_at = datetime.utcnow()

    aggregates: dict[Pipeline, EvalAggregate] = {}
    rows: list[QuestionEvalRow] = []
    per_pipeline_traces: dict[Pipeline, list[TraceRecord]] = {"baseline": [], "engineered": []}

    for pipeline in ("baseline", "engineered"):
        traces: list[TraceRecord] = []
        for item in items:
            trace = _run_pipeline(pipeline, item["question"])  # type: ignore[arg-type]
            persist(trace, run_id=run_id)
            traces.append(trace)
            row, _ = _row_for(item, trace, pipeline)  # type: ignore[arg-type]
            rows.append(row)
        per_pipeline_traces[pipeline] = traces  # type: ignore[index]
        aggregates[pipeline] = _aggregate(pipeline, [r for r in rows if r.pipeline == pipeline], traces)  # type: ignore[index]

    finished_at = datetime.utcnow()

    # Persist the run header.
    payload = {
        "aggregates": {k: v.model_dump() for k, v in aggregates.items()},
        "row_count": len(rows),
    }
    with get_session() as s:
        row = RunRow(
            id=run_id,
            pipeline="batch",
            started_at=started_at,
            finished_at=finished_at,
            status="ok",
            payload_json=json.dumps(payload),
        )
        s.add(row)
        s.commit()

    return EvalRunResult(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        aggregates=aggregates,
        rows=rows,
    )
