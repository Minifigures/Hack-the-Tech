"use client";

import type { TraceRecord } from "@/lib/api";
import { fmtMs, fmtUsd } from "@/lib/format";

export function TraceCard({
  trace,
  tone,
  title,
  subtitle,
}: {
  trace: TraceRecord | null;
  tone: "danger" | "ok";
  title: string;
  subtitle: string;
}) {
  const accent =
    tone === "ok"
      ? "border-forge-green/40 shadow-[0_0_0_1px_rgba(34,197,94,0.2),0_8px_32px_-8px_rgba(34,197,94,0.25)]"
      : "border-forge-red/40 shadow-[0_0_0_1px_rgba(239,68,68,0.2),0_8px_32px_-8px_rgba(239,68,68,0.25)]";

  const finalAnswer = trace?.final_answer;
  const guards = trace?.guardrails ?? [];
  const passed = guards.filter((g) => g.passed).length;

  return (
    <div className={`panel p-5 ${accent}`} data-testid={`trace-card-${trace?.pipeline ?? "empty"}`}>
      <div className="flex items-baseline justify-between gap-2">
        <div>
          <p className="panel-title text-ink-300">{subtitle}</p>
          <h3 className="mt-1 text-lg font-semibold text-ink-50">{title}</h3>
        </div>
        {tone === "ok" ? (
          <span className="badge-pass">engineered</span>
        ) : (
          <span className="badge-fail">baseline</span>
        )}
      </div>

      {!trace ? (
        <p className="mt-6 text-sm text-ink-400">No run yet. Ask a question.</p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
            <Stat label="Latency" value={fmtMs(trace.total_ms)} />
            <Stat label="Cost" value={fmtUsd(trace.cost_usd)} />
            <Stat
              label="Guards"
              value={`${passed}/${guards.length || "—"}`}
              tone={
                guards.length === 0
                  ? "neutral"
                  : passed === guards.length
                    ? "ok"
                    : "danger"
              }
            />
          </div>

          <div className="mt-5 rounded-lg bg-ink-900/70 p-4">
            <p className="panel-title">Answer</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-ink-100">
              {finalAnswer?.answer || <em className="text-ink-400">(no answer)</em>}
            </p>
            {finalAnswer?.refusal_reason ? (
              <p className="mt-3 text-xs">
                <span className="badge-warn">
                  refusal: {finalAnswer.refusal_reason}
                </span>
              </p>
            ) : null}
            <div className="mt-3 flex items-center justify-between text-[11px] text-ink-400">
              <span>
                confidence{" "}
                <span className="font-mono text-ink-200">
                  {finalAnswer?.confidence?.toFixed(2) ?? "—"}
                </span>
              </span>
              <span>
                schema{" "}
                {finalAnswer?.raw ? (
                  <span className="badge-fail">unstructured</span>
                ) : (
                  <span className="badge-pass">typed</span>
                )}
              </span>
            </div>
          </div>

          <div className="mt-4">
            <p className="panel-title">Citations</p>
            <ul className="mt-2 space-y-2 text-xs">
              {!finalAnswer?.citations?.length ? (
                <li className="text-ink-400">
                  {tone === "ok" ? "—" : "no citations produced"}
                </li>
              ) : (
                finalAnswer.citations.map((c, i) => (
                  <li
                    key={c.source_id + i}
                    className="rounded-md border border-ink-700 bg-ink-900/60 p-2"
                  >
                    <p className="font-mono text-[11px] text-forge-ice">
                      {c.source_id}
                    </p>
                    {c.quote ? (
                      <p className="mt-1 text-ink-300">“{c.quote}”</p>
                    ) : null}
                  </li>
                ))
              )}
            </ul>
          </div>

          {guards.length ? (
            <div className="mt-4">
              <p className="panel-title">Guardrails</p>
              <ul className="mt-2 grid grid-cols-1 gap-1.5 text-xs">
                {guards.map((g) => (
                  <li
                    key={g.guard}
                    className="flex items-center justify-between rounded-md border border-ink-700 bg-ink-900/60 px-2 py-1.5"
                  >
                    <span className="font-mono text-ink-200">{g.guard}</span>
                    {g.passed ? (
                      <span className="badge-pass">pass</span>
                    ) : (
                      <span className="badge-fail">fail</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <details className="mt-4">
            <summary className="cursor-pointer text-xs uppercase tracking-wider text-ink-400 hover:text-ink-200">
              Trace spans ({trace.spans.length})
            </summary>
            <ul className="mt-2 space-y-1 text-[11px]">
              {trace.spans.map((s) => (
                <li
                  key={s.name}
                  className="flex items-center justify-between rounded-md border border-ink-700/60 bg-ink-900/60 px-2 py-1 font-mono text-ink-300"
                >
                  <span>{s.name}</span>
                  <span className="text-ink-400">
                    {(s.end_ms - s.start_ms).toFixed(0)} ms
                  </span>
                </li>
              ))}
            </ul>
          </details>
        </>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "ok" | "danger" | "neutral";
}) {
  const cls =
    tone === "ok"
      ? "text-forge-green"
      : tone === "danger"
        ? "text-forge-red"
        : "text-ink-100";
  return (
    <div className="rounded-md border border-ink-700 bg-ink-900/60 p-2">
      <p className="text-[10px] uppercase tracking-wider text-ink-400">{label}</p>
      <p className={`mt-1 font-mono text-sm ${cls}`}>{value}</p>
    </div>
  );
}
