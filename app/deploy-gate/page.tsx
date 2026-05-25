"use client";

import { useEffect, useState } from "react";
import { api, type DeployGateResponse, type GateResult } from "@/lib/api";
import { VerdictPill } from "@/components/verdict-pill";

export default function DeployGatePage() {
  const [data, setData] = useState<DeployGateResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .deployGateLatest()
      .then(setData)
      .catch(() => {});
  }, []);

  async function runGate() {
    setRunning(true);
    setError(null);
    try {
      const res = await api.deployGateRun();
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="panel-title">Ship or hold?</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink-50">Deploy gate</h1>
          <p className="mt-2 max-w-3xl text-sm text-ink-300">
            The deploy gate runs the full 25-question eval against both pipelines
            and applies the configured thresholds. It emits PASS/FAIL with the
            exact failing metrics. Wire this into CI and the build stops shipping
            if any gate trips.
          </p>
        </div>
        <button
          onClick={runGate}
          className="btn btn-primary"
          disabled={running}
          data-testid="run-gate"
        >
          {running ? "Evaluating both pipelines…" : "Run deploy gate"}
        </button>
      </header>

      {error ? (
        <p className="rounded-md border border-forge-red/40 bg-forge-red/10 px-3 py-2 text-sm text-forge-red">
          {error}
        </p>
      ) : null}

      {!data ? (
        <p className="text-sm text-ink-400">
          No verdict yet. Click <span className="kbd">Run deploy gate</span>.
        </p>
      ) : (
        <>
          <section className="grid gap-5 lg:grid-cols-2">
            <GateCard
              gate={data.baseline}
              title="Baseline pipeline"
              tone="danger"
            />
            <GateCard
              gate={data.engineered}
              title="Engineered pipeline"
              tone="ok"
            />
          </section>
          <section className="panel p-5">
            <p className="panel-title">Run ID</p>
            <p className="mt-1 font-mono text-sm text-ink-200">{data.run_id}</p>
            <p className="mt-3 text-xs text-ink-400">
              In a real CI pipeline this run_id is the artifact you attach to the
              deploy ticket. The summary markdown below can be posted to the PR.
            </p>
          </section>
        </>
      )}
    </div>
  );
}

function GateCard({
  gate,
  title,
  tone,
}: {
  gate: GateResult;
  title: string;
  tone: "danger" | "ok";
}) {
  const accent =
    gate.verdict === "PASS"
      ? "border-forge-green/40 shadow-[0_0_0_1px_rgba(34,197,94,0.2),0_8px_32px_-8px_rgba(34,197,94,0.25)]"
      : "border-forge-red/40 shadow-[0_0_0_1px_rgba(239,68,68,0.2),0_8px_32px_-8px_rgba(239,68,68,0.25)]";
  return (
    <div className={`panel p-5 ${accent}`} data-testid={`gate-${gate.pipeline}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="panel-title text-ink-300">
            {tone === "ok" ? "production candidate" : "naive baseline"}
          </p>
          <h3 className="mt-1 text-xl font-semibold text-ink-50">{title}</h3>
        </div>
        <VerdictPill verdict={gate.verdict} />
      </div>

      <div className="mt-5">
        <p className="panel-title">Failed gates ({gate.failed_gates.length})</p>
        {gate.failed_gates.length === 0 ? (
          <p className="mt-2 text-sm text-forge-green">
            ✓ all gates satisfied
          </p>
        ) : (
          <ul className="mt-2 space-y-1.5 text-xs">
            {gate.failed_gates.map((f) => (
              <li
                key={f.name}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-forge-red/30 bg-forge-red/10 px-2 py-1.5"
              >
                <span className="font-mono text-ink-100">{f.name}</span>
                <span className="font-mono text-ink-300">
                  observed <span className="text-forge-red">{f.observed}</span>{" "}
                  vs <span className="text-ink-100">{f.direction} {f.threshold}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <details className="mt-5">
        <summary className="cursor-pointer text-xs uppercase tracking-wider text-ink-400 hover:text-ink-200">
          Full summary
        </summary>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-md border border-ink-700/60 bg-ink-900/60 p-3 text-xs text-ink-200">
          {gate.summary_markdown}
        </pre>
      </details>
    </div>
  );
}
