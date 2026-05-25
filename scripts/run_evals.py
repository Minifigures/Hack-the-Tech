"""CLI: run baseline + engineered evals and print the deploy-gate verdict."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.deploy_gate.gate import evaluate_run  # noqa: E402
from app.evals.runner import run_full_eval  # noqa: E402
from app.rag.index import build_index  # noqa: E402


def _fmt_pct(v: float) -> str:
    return f"{v * 100:5.1f}%"


def main() -> None:
    init_db()
    build_index()
    result = run_full_eval()
    print(f"\n=== EvalForge run {result.run_id} ===")
    for pipeline, agg in result.aggregates.items():
        print(f"\n[{pipeline}] over {agg.questions} questions")
        print(f"  faithfulness         : {_fmt_pct(agg.faithfulness_mean)}")
        print(f"  answer_relevance     : {_fmt_pct(agg.answer_relevance_mean)}")
        print(f"  context_precision    : {_fmt_pct(agg.context_precision_mean)}")
        print(f"  context_recall       : {_fmt_pct(agg.context_recall_mean)}")
        print(f"  citation_accuracy    : {_fmt_pct(agg.citation_accuracy_mean)}")
        print(f"  structured_validity  : {_fmt_pct(agg.structured_output_validity)}")
        print(f"  refusal_correctness  : {_fmt_pct(agg.refusal_correctness)}")
        print(f"  pii_leak_count       : {agg.pii_leak_count}")
        print(f"  injection_bypass_ct  : {agg.prompt_injection_bypass_count}")
        print(f"  p95_latency_ms       : {agg.p95_latency_ms}")
        print(f"  cost_per_answer_usd  : ${agg.cost_per_answer_usd:.4f}")

    gate = evaluate_run(result)
    print("\n=== Deploy Gate ===")
    for pipeline in ("baseline", "engineered"):
        g = getattr(gate, pipeline)
        marker = "PASS" if g.verdict == "PASS" else "FAIL"
        print(f"\n[{pipeline}] verdict: {marker}")
        if g.failed_gates:
            for fg in g.failed_gates:
                print(f"  - {fg.name} observed {fg.observed} violates {fg.direction} {fg.threshold}")
    print()


if __name__ == "__main__":
    main()
