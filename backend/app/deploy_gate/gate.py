from __future__ import annotations

import json
import uuid
from datetime import datetime

from ..config import settings
from ..db import get_session
from ..models import (
    DeployGateRow,
    DeployGateResponse,
    EvalAggregate,
    EvalRunResult,
    FailedGate,
    GateResult,
    Pipeline,
)


def _check(name: str, observed: float | int, threshold: float | int, direction: str) -> FailedGate | None:
    ok = (
        (direction == ">=" and observed >= threshold)
        or (direction == "<=" and observed <= threshold)
        or (direction == "=" and observed == threshold)
    )
    if ok:
        return None
    return FailedGate(name=name, observed=observed, threshold=threshold, direction=direction)  # type: ignore[arg-type]


def _evaluate_pipeline(pipeline: Pipeline, agg: EvalAggregate) -> GateResult:
    t = settings.thresholds
    checks: list[FailedGate | None] = [
        _check("faithfulness_mean", agg.faithfulness_mean, t.faithfulness_mean, ">="),
        _check("answer_relevance_mean", agg.answer_relevance_mean, t.answer_relevance_mean, ">="),
        _check("context_recall_mean", agg.context_recall_mean, t.context_recall_mean, ">="),
        _check("citation_accuracy_mean", agg.citation_accuracy_mean, t.citation_accuracy_mean, ">="),
        _check(
            "structured_output_validity",
            agg.structured_output_validity,
            t.structured_output_validity,
            "=",
        ),
        _check("refusal_correctness", agg.refusal_correctness, t.refusal_correctness, ">="),
        _check("pii_leak_count", agg.pii_leak_count, t.pii_leak_count_max, "<="),
        _check(
            "prompt_injection_bypass_count",
            agg.prompt_injection_bypass_count,
            t.prompt_injection_bypass_count_max,
            "<=",
        ),
        _check("p95_latency_ms", agg.p95_latency_ms, t.p95_latency_ms_max, "<="),
        _check("cost_per_answer_usd", agg.cost_per_answer_usd, t.cost_per_answer_usd_max, "<="),
    ]
    failed = [c for c in checks if c is not None]
    verdict = "PASS" if not failed else "FAIL"
    md = _summary_markdown(pipeline, agg, failed, verdict)  # type: ignore[arg-type]
    return GateResult(
        run_id="",
        pipeline=pipeline,
        verdict=verdict,  # type: ignore[arg-type]
        failed_gates=failed,
        summary_markdown=md,
    )


def _summary_markdown(pipeline: Pipeline, agg: EvalAggregate, failed: list[FailedGate], verdict: str) -> str:
    lines = [
        f"# Deploy Gate — {pipeline}",
        f"**Verdict:** `{verdict}`",
        "",
        "## Aggregates",
        f"- Questions evaluated: {agg.questions}",
        f"- Faithfulness mean: {agg.faithfulness_mean}",
        f"- Answer relevance mean: {agg.answer_relevance_mean}",
        f"- Context precision mean: {agg.context_precision_mean}",
        f"- Context recall mean: {agg.context_recall_mean}",
        f"- Citation accuracy mean: {agg.citation_accuracy_mean}",
        f"- Structured output validity: {agg.structured_output_validity}",
        f"- Refusal correctness: {agg.refusal_correctness}",
        f"- PII leak count: {agg.pii_leak_count}",
        f"- Prompt injection bypass count: {agg.prompt_injection_bypass_count}",
        f"- p95 latency (ms): {agg.p95_latency_ms}",
        f"- Cost per answer (USD): {agg.cost_per_answer_usd}",
        "",
    ]
    if failed:
        lines.append("## Failed gates")
        for g in failed:
            lines.append(f"- `{g.name}` observed `{g.observed}` violates `{g.direction} {g.threshold}`")
    else:
        lines.append("## Failed gates")
        lines.append("- _none_")
    return "\n".join(lines)


def evaluate_run(eval_run: EvalRunResult) -> DeployGateResponse:
    baseline_gate = _evaluate_pipeline("baseline", eval_run.aggregates["baseline"])
    eng_gate = _evaluate_pipeline("engineered", eval_run.aggregates["engineered"])
    baseline_gate.run_id = eval_run.run_id
    eng_gate.run_id = eval_run.run_id

    # Persist both
    with get_session() as s:
        for gate in (baseline_gate, eng_gate):
            s.add(
                DeployGateRow(
                    id=uuid.uuid4().hex[:12],
                    run_id=eval_run.run_id,
                    pipeline=gate.pipeline,
                    verdict=gate.verdict,
                    failed_gates_json=json.dumps([f.model_dump() for f in gate.failed_gates]),
                    summary_md=gate.summary_markdown,
                    created_at=datetime.utcnow(),
                )
            )
        s.commit()

    return DeployGateResponse(run_id=eval_run.run_id, baseline=baseline_gate, engineered=eng_gate)
