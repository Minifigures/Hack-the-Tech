"use client";

import { useEffect, useState } from "react";
import {
  api,
  type EvalAggregate,
  type EvalRunResult,
  type QuestionEvalRow,
} from "@/lib/api";
import { fmtMs, fmtScore, fmtUsd } from "@/lib/format";

const METRIC_KEYS: Array<{ key: keyof EvalAggregate; label: string; isCount?: boolean; lowerBetter?: boolean }> = [
  { key: "faithfulness_mean", label: "Faithfulness" },
  { key: "answer_relevance_mean", label: "Answer relevance" },
  { key: "context_precision_mean", label: "Context precision" },
  { key: "context_recall_mean", label: "Context recall" },
  { key: "citation_accuracy_mean", label: "Citation accuracy" },
  { key: "structured_output_validity", label: "Structured output validity" },
  { key: "refusal_correctness", label: "Refusal correctness" },
  { key: "pii_leak_count", label: "PII leaks", isCount: true, lowerBetter: true },
  { key: "prompt_injection_bypass_count", label: "Injection bypasses", isCount: true, lowerBetter: true },
];

export default function EvalsPage() {
  const [data, setData] = useState<EvalRunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "baseline" | "engineered">("all");

  useEffect(() => {
    setLoading(true);
    api
      .evalsLatest()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  async function runFull() {
    setRunning(true);
    setError(null);
    try {
      const res = await api.evalsRun();
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  const baseline = data?.aggregates?.baseline;
  const engineered = data?.aggregates?.engineered;
  const rows = (data?.rows ?? []).filter(
    (r) => filter === "all" || r.pipeline === filter,
  );

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="panel-title">Regression evals</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink-50">
            Eval dashboard
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-ink-300">
            25-item golden dataset spanning healthcare, fintech compliance,
            cybersecurity, and adversarial probes. Local RAGAS-shape metrics, with
            schema validity, refusal correctness, and safety counters.
          </p>
        </div>
        <button
          onClick={runFull}
          className="btn btn-primary"
          disabled={running}
          data-testid="evals-run"
        >
          {running ? "Running 25 × 2 = 50 trials…" : "Run full eval"}
        </button>
      </header>

      {error ? (
        <p className="rounded-md border border-forge-red/40 bg-forge-red/10 px-3 py-2 text-sm text-forge-red">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-ink-400">Loading latest run…</p>
      ) : !data ? (
        <p className="text-sm text-ink-400">
          No eval run yet. Click <span className="kbd">Run full eval</span> to score
          both pipelines.
        </p>
      ) : null}

      {baseline && engineered ? (
        <>
          <section className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {METRIC_KEYS.map((m) => (
              <MetricCard
                key={String(m.key)}
                label={m.label}
                baseline={Number(baseline[m.key])}
                engineered={Number(engineered[m.key])}
                isCount={m.isCount}
                lowerBetter={m.lowerBetter}
              />
            ))}
            <MetricCard
              label="p95 latency"
              baseline={baseline.p95_latency_ms}
              engineered={engineered.p95_latency_ms}
              format={fmtMs}
              lowerBetter
            />
            <MetricCard
              label="Cost / answer"
              baseline={baseline.cost_per_answer_usd}
              engineered={engineered.cost_per_answer_usd}
              format={fmtUsd}
              lowerBetter
            />
          </section>

          <section>
            <div className="flex items-center justify-between">
              <p className="panel-title">Per-question results</p>
              <div className="flex gap-1 text-xs">
                {(["all", "baseline", "engineered"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={
                      "rounded-md px-2 py-1 transition " +
                      (filter === f
                        ? "bg-ink-700 text-ink-50"
                        : "text-ink-400 hover:text-ink-100")
                    }
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-3 overflow-x-auto rounded-xl border border-ink-700/70">
              <table className="min-w-full divide-y divide-ink-700 text-xs">
                <thead className="bg-ink-800/60 text-ink-300">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">ID</th>
                    <th className="px-3 py-2 text-left font-medium">Pipeline</th>
                    <th className="px-3 py-2 text-left font-medium">Question</th>
                    <th className="px-3 py-2 text-right font-medium">Faith</th>
                    <th className="px-3 py-2 text-right font-medium">Relev</th>
                    <th className="px-3 py-2 text-right font-medium">Cite</th>
                    <th className="px-3 py-2 text-right font-medium">Refuse</th>
                    <th className="px-3 py-2 text-right font-medium">Guards</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-700/60">
                  {rows.map((r) => (
                    <Row key={r.question_id + r.pipeline} row={r} />
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function MetricCard({
  label,
  baseline,
  engineered,
  isCount,
  lowerBetter,
  format,
}: {
  label: string;
  baseline: number;
  engineered: number;
  isCount?: boolean;
  lowerBetter?: boolean;
  format?: (n: number) => string;
}) {
  const fmt = format ?? (isCount ? (n: number) => `${n}` : (n: number) => fmtScore(n));
  const delta = engineered - baseline;
  const improved = lowerBetter ? delta < 0 : delta > 0;
  const equal = delta === 0;
  return (
    <div className="panel p-4">
      <p className="panel-title">{label}</p>
      <div className="mt-2 grid grid-cols-2 gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-ink-400">baseline</p>
          <p className="font-mono text-lg text-forge-red">{fmt(baseline)}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-ink-400">engineered</p>
          <p className="font-mono text-lg text-forge-green">{fmt(engineered)}</p>
        </div>
      </div>
      <p
        className={
          "mt-2 text-[11px] font-medium " +
          (equal
            ? "text-ink-400"
            : improved
              ? "text-forge-green"
              : "text-forge-red")
        }
      >
        {equal ? "no change" : improved ? "✓ improved" : "✗ regressed"} ({delta > 0 ? "+" : ""}
        {fmt(delta)})
      </p>
    </div>
  );
}

function metricScore(row: QuestionEvalRow, name: string): number | null {
  const m = row.metrics.find((x) => x.metric === name);
  return m ? m.score : null;
}

function Row({ row }: { row: QuestionEvalRow }) {
  const faith = metricScore(row, "faithfulness");
  const relev = metricScore(row, "answer_relevance");
  const cite = metricScore(row, "citation_accuracy");
  const refuse = metricScore(row, "refusal_correctness");
  return (
    <tr className="bg-ink-900/40 hover:bg-ink-800/40">
      <td className="px-3 py-2 font-mono text-ink-300">{row.question_id}</td>
      <td className="px-3 py-2">
        {row.pipeline === "engineered" ? (
          <span className="badge-pass">eng</span>
        ) : (
          <span className="badge-fail">base</span>
        )}
      </td>
      <td className="max-w-[28rem] truncate px-3 py-2 text-ink-200" title={row.question}>
        {row.question}
      </td>
      <Cell v={faith} />
      <Cell v={relev} />
      <Cell v={cite} />
      <Cell v={refuse} />
      <td className="px-3 py-2 text-right font-mono text-ink-300">
        {row.guardrails_passed}/{row.guardrails_total}
      </td>
    </tr>
  );
}

function Cell({ v }: { v: number | null }) {
  if (v === null) return <td className="px-3 py-2 text-right text-ink-500">—</td>;
  const cls =
    v >= 0.9
      ? "text-forge-green"
      : v >= 0.6
        ? "text-ink-200"
        : "text-forge-red";
  return <td className={`px-3 py-2 text-right font-mono ${cls}`}>{fmtScore(v)}</td>;
}
