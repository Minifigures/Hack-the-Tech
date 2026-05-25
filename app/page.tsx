import Link from "next/link";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CockpitPage() {
  const health = await api.health().catch(() => null);
  const cfg = await api.config().catch(() => null);

  const kbTotal = health
    ? Object.values(health.kb_sources).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <div className="space-y-10">
      <section className="grid items-center gap-8 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <p className="panel-title text-forge-ice">AI Engineering, not just AI features</p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight text-ink-50 sm:text-5xl">
            CI/CD for{" "}
            <span className="bg-gradient-to-r from-forge-accent to-forge-ice bg-clip-text text-transparent">
              reliable AI agents
            </span>
            .
          </h1>
          <p className="mt-4 max-w-xl text-ink-300">
            EvalForge is a reliability cockpit for RAG and agent systems. It runs
            prompt regression evals, structured-output validation, guardrails, traces,
            cost and latency tracking, and a deploy gate that says{" "}
            <span className="font-mono text-forge-green">PASS</span> or{" "}
            <span className="font-mono text-forge-red">FAIL</span> based on measured
            results. Compare a baseline RAG chatbot against an engineered system and
            see the difference live.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/compare" className="btn btn-primary" data-testid="cta-compare">
              Run the side-by-side demo →
            </Link>
            <Link href="/deploy-gate" className="btn" data-testid="cta-gate">
              See the deploy gate
            </Link>
          </div>
          <div className="mt-6 flex flex-wrap gap-2 text-xs text-ink-400">
            <span className="chip">BAML-shaped typed output</span>
            <span className="chip">RAGAS-style metrics</span>
            <span className="chip">Langfuse-shape traces</span>
            <span className="chip">Pydantic schema enforcement</span>
            <span className="chip">Guardrails AI patterns</span>
            <span className="chip">HyDE + rerank</span>
          </div>
        </div>
        <div className="panel p-6">
          <p className="panel-title">System status</p>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-ink-400">API</dt>
              <dd className="font-mono">
                {health ? (
                  <span className="badge-pass">online</span>
                ) : (
                  <span className="badge-fail">offline</span>
                )}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-ink-400">Mode</dt>
              <dd className="font-mono text-ink-100">
                {health?.mock_mode ? "mock (deterministic)" : "live"}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-ink-400">Default model</dt>
              <dd className="font-mono text-ink-100">{health?.default_model ?? "—"}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-ink-400">Knowledge chunks</dt>
              <dd className="font-mono text-ink-100">{kbTotal}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-ink-400">Eval threshold (faithfulness)</dt>
              <dd className="font-mono text-ink-100">
                ≥ {cfg ? cfg.thresholds.faithfulness_mean : "—"}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-ink-400">Eval threshold (citation accuracy)</dt>
              <dd className="font-mono text-ink-100">
                ≥ {cfg ? cfg.thresholds.citation_accuracy_mean : "—"}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section>
        <p className="panel-title">The pipeline</p>
        <div className="mt-3 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <PipelineCard
            step="1"
            title="Retrieve"
            body="Baseline: weak hash-embedding cosine. Engineered: BM25 + HyDE union + lexical-semantic rerank."
          />
          <PipelineCard
            step="2"
            title="Generate"
            body="Baseline: bare prompt, raw string. Engineered: BAML-shape system prompt with typed JSON contract enforced by Pydantic parse + 1-shot retry."
          />
          <PipelineCard
            step="3"
            title="Guard"
            body="PII, prompt injection, jailbreak, refusal correctness, and citation-faithfulness guards run inline. Failures are visible on every trace."
          />
          <PipelineCard
            step="4"
            title="Gate"
            body="A run of 25 golden questions is scored on 10 metrics. The deploy gate emits PASS/FAIL and exact reasons."
          />
        </div>
      </section>

      <section>
        <p className="panel-title">Knowledge base</p>
        <div className="mt-3 grid gap-4 md:grid-cols-3">
          {health
            ? Object.entries(health.kb_sources).map(([domain, count]) => (
                <div key={domain} className="panel p-5">
                  <p className="font-mono text-xs text-ink-400">
                    data/kb/{domain}
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-ink-50">
                    {count} chunks
                  </p>
                  <p className="mt-2 text-sm text-ink-300">
                    {domainBlurb(domain)}
                  </p>
                </div>
              ))
            : null}
        </div>
      </section>
    </div>
  );
}

function PipelineCard({
  step,
  title,
  body,
}: {
  step: string;
  title: string;
  body: string;
}) {
  return (
    <div className="panel p-5">
      <div className="flex items-center gap-3">
        <span className="grid h-8 w-8 place-items-center rounded-md bg-ink-900 font-mono text-sm text-forge-ice">
          {step}
        </span>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-ink-100">
          {title}
        </h3>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-ink-300">{body}</p>
    </div>
  );
}

function domainBlurb(domain: string): string {
  if (domain === "healthcare") {
    return "Drug interactions, dosing, HIPAA, triage protocols.";
  }
  if (domain === "fintech") {
    return "AML, KYC, SOX, lending, FDIC, retirement rules.";
  }
  if (domain === "security") {
    return "IR, IAM, network attacks, NIST 800-53.";
  }
  return "Domain knowledge.";
}
