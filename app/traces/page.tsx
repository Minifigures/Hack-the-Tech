"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type TraceRecord } from "@/lib/api";
import { fmtMs, fmtUsd } from "@/lib/format";

export default function TracesPage() {
  const [traces, setTraces] = useState<TraceRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "baseline" | "engineered">("all");

  useEffect(() => {
    setLoading(true);
    api
      .traces()
      .then((rows) => {
        setTraces(rows);
        if (rows.length && !selectedId) setSelectedId(rows[0].trace_id);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = useMemo(
    () => (filter === "all" ? traces : traces.filter((t) => t.pipeline === filter)),
    [filter, traces],
  );
  const selected = useMemo(
    () => traces.find((t) => t.trace_id === selectedId) ?? null,
    [selectedId, traces],
  );

  return (
    <div className="space-y-6">
      <header>
        <p className="panel-title">Observability</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50">Trace viewer</h1>
        <p className="mt-2 max-w-3xl text-sm text-ink-300">
          Every pipeline run is recorded as a Langfuse-shape trace: spans for
          retrieval, HyDE expansion, rerank, LLM call, schema parse, and the
          guardrail chain. Click any trace to see its timeline and attributes.
        </p>
      </header>

      <div className="flex items-center justify-between">
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
        <p className="text-xs text-ink-400">{filtered.length} traces</p>
      </div>

      {loading ? (
        <p className="text-sm text-ink-400">Loading traces…</p>
      ) : !traces.length ? (
        <p className="text-sm text-ink-400">
          No traces yet. Run the{" "}
          <a className="text-forge-ice underline" href="/compare">
            Compare
          </a>{" "}
          or{" "}
          <a className="text-forge-ice underline" href="/evals">
            Evals
          </a>{" "}
          flows to populate.
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_1.5fr]">
          <ul className="max-h-[70vh] space-y-1 overflow-y-auto pr-1">
            {filtered.map((t) => (
              <li key={t.trace_id}>
                <button
                  onClick={() => setSelectedId(t.trace_id)}
                  className={
                    "w-full rounded-lg border px-3 py-2 text-left transition " +
                    (t.trace_id === selectedId
                      ? "border-forge-accent bg-ink-800"
                      : "border-ink-700 bg-ink-900/40 hover:border-ink-500")
                  }
                  data-testid={`trace-row-${t.trace_id}`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span
                      className={
                        t.pipeline === "engineered" ? "badge-pass" : "badge-fail"
                      }
                    >
                      {t.pipeline}
                    </span>
                    <span className="font-mono text-ink-400">{t.trace_id}</span>
                  </div>
                  <p
                    className="mt-1 truncate text-sm text-ink-100"
                    title={t.question}
                  >
                    {t.question}
                  </p>
                  <p className="mt-1 flex items-center gap-3 text-[11px] text-ink-400">
                    <span>{fmtMs(t.total_ms)}</span>
                    <span>{fmtUsd(t.cost_usd)}</span>
                    <span>{t.spans.length} spans</span>
                  </p>
                </button>
              </li>
            ))}
          </ul>
          <TraceDetail trace={selected} />
        </div>
      )}
    </div>
  );
}

function TraceDetail({ trace }: { trace: TraceRecord | null }) {
  if (!trace) {
    return (
      <div className="panel grid place-items-center p-12 text-sm text-ink-400">
        Select a trace to inspect.
      </div>
    );
  }
  const minStart = Math.min(...trace.spans.map((s) => s.start_ms));
  const maxEnd = Math.max(...trace.spans.map((s) => s.end_ms));
  const span = Math.max(1, maxEnd - minStart);
  return (
    <div className="panel space-y-5 p-5" data-testid="trace-detail">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="panel-title">trace</p>
          <p className="mt-1 font-mono text-sm text-ink-200">{trace.trace_id}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-ink-400">
            {fmtMs(trace.total_ms)} • {fmtUsd(trace.cost_usd)}
          </p>
          <p className="text-[11px] font-mono text-ink-500">
            {trace.pipeline}
          </p>
        </div>
      </div>

      <div>
        <p className="panel-title">Question</p>
        <p className="mt-1 text-sm text-ink-100">{trace.question}</p>
      </div>

      <div>
        <p className="panel-title">Spans</p>
        <ul className="mt-2 space-y-1">
          {trace.spans.map((s) => {
            const left = ((s.start_ms - minStart) / span) * 100;
            const width = Math.max(2, ((s.end_ms - s.start_ms) / span) * 100);
            return (
              <li
                key={s.name + s.start_ms}
                className="rounded-md border border-ink-700/60 bg-ink-900/40 p-2"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-ink-200">{s.name}</span>
                  <span className="text-ink-400">
                    {(s.end_ms - s.start_ms).toFixed(0)} ms
                  </span>
                </div>
                <div className="relative mt-1 h-2 rounded-full bg-ink-900">
                  <div
                    className="absolute h-full rounded-full bg-gradient-to-r from-forge-accent to-forge-ice"
                    style={{ left: `${left}%`, width: `${width}%` }}
                  />
                </div>
                {Object.keys(s.attrs).length ? (
                  <details className="mt-1.5">
                    <summary className="cursor-pointer text-[10px] uppercase tracking-wider text-ink-500 hover:text-ink-300">
                      attributes
                    </summary>
                    <pre className="mt-1 overflow-x-auto rounded bg-ink-900/70 p-2 text-[11px] text-ink-300">
                      {JSON.stringify(s.attrs, null, 2)}
                    </pre>
                  </details>
                ) : null}
              </li>
            );
          })}
        </ul>
      </div>

      <div>
        <p className="panel-title">Final answer</p>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-md border border-ink-700/60 bg-ink-900/60 p-3 text-xs text-ink-200">
          {JSON.stringify(trace.final_answer, null, 2)}
        </pre>
      </div>

      {trace.guardrails.length ? (
        <div>
          <p className="panel-title">Guardrails</p>
          <ul className="mt-2 space-y-1 text-xs">
            {trace.guardrails.map((g) => (
              <li
                key={g.guard}
                className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/40 px-2 py-1.5"
              >
                <span className="font-mono text-ink-200">{g.guard}</span>
                {g.passed ? (
                  <span className="badge-pass">pass</span>
                ) : (
                  <span className="badge-fail">{g.severity}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
