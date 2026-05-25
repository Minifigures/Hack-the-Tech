export type Citation = { source_id: string; quote: string };
export type AnswerSchema = {
  answer: string;
  citations: Citation[];
  confidence: number;
  refusal_reason: string | null;
};

export type SpanRecord = {
  name: string;
  start_ms: number;
  end_ms: number;
  attrs: Record<string, unknown>;
};

export type Guardrail = {
  guard: string;
  passed: boolean;
  severity: "low" | "med" | "high" | "critical";
  reason: string;
  evidence: string;
};

export type TraceRecord = {
  trace_id: string;
  pipeline: "baseline" | "engineered";
  question: string;
  final_answer: AnswerSchema & { raw?: boolean };
  total_ms: number;
  cost_usd: number;
  spans: SpanRecord[];
  guardrails: Guardrail[];
  created_at: string;
};

export type CompareResponse = {
  baseline: TraceRecord;
  engineered: TraceRecord;
};

export type MetricResult = { metric: string; score: number; justification: string };

export type QuestionEvalRow = {
  question_id: string;
  question: string;
  pipeline: "baseline" | "engineered";
  metrics: MetricResult[];
  answer: string;
  citations: string[];
  cost_usd: number;
  latency_ms: number;
  guardrails_passed: number;
  guardrails_total: number;
};

export type EvalAggregate = {
  pipeline: "baseline" | "engineered";
  faithfulness_mean: number;
  answer_relevance_mean: number;
  context_precision_mean: number;
  context_recall_mean: number;
  citation_accuracy_mean: number;
  structured_output_validity: number;
  refusal_correctness: number;
  pii_leak_count: number;
  prompt_injection_bypass_count: number;
  p95_latency_ms: number;
  cost_per_answer_usd: number;
  questions: number;
};

export type EvalRunResult = {
  run_id: string;
  started_at: string;
  finished_at: string;
  aggregates: Record<"baseline" | "engineered", EvalAggregate>;
  rows: QuestionEvalRow[];
};

export type FailedGate = {
  name: string;
  observed: number;
  threshold: number;
  direction: ">=" | "<=" | "=";
};

export type GateResult = {
  run_id: string;
  pipeline: "baseline" | "engineered";
  verdict: "PASS" | "FAIL";
  failed_gates: FailedGate[];
  summary_markdown: string;
};

export type DeployGateResponse = {
  run_id: string;
  baseline: GateResult;
  engineered: GateResult;
};

function backendBase(): string {
  if (typeof window !== "undefined") return ""; // browser: same-origin
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:8000";
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${backendBase()}${path}`;
  const res = await fetch(url, {
    cache: "no-store",
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status} on ${path}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () =>
    call<{
      status: string;
      mock_mode: boolean;
      default_model: string;
      kb_sources: Record<string, number>;
    }>("/api/health"),
  config: () =>
    call<{
      mock_mode: boolean;
      default_model: string;
      thresholds: Record<string, number>;
    }>("/api/config"),
  compare: (question: string) =>
    call<CompareResponse>("/api/compare", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  evalsDataset: () =>
    call<{ items: Array<Record<string, unknown>>; count: number }>(
      "/api/evals/dataset",
    ),
  evalsRun: () => call<EvalRunResult>("/api/evals/run", { method: "POST" }),
  evalsLatest: () => call<EvalRunResult>("/api/evals/latest"),
  traces: () => call<TraceRecord[]>("/api/traces"),
  trace: (id: string) => call<TraceRecord>(`/api/traces/${id}`),
  guardrailProbe: (question: string) =>
    call<{ trace: TraceRecord }>("/api/guardrails/probe", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  guardrailBaselineProbe: (question: string) =>
    call<{
      question: string;
      raw_answer: string;
      guards: Guardrail[];
    }>("/api/guardrails/baseline-probe", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  deployGateRun: () =>
    call<DeployGateResponse>("/api/deploy-gate/run", { method: "POST" }),
  deployGateLatest: () => call<DeployGateResponse>("/api/deploy-gate/latest"),
};
