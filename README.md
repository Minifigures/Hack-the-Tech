# EvalForge — CI/CD for Reliable AI Agents

> Everyone else built AI. EvalForge is the engineering layer that proves AI is safe enough to ship.

EvalForge is a reliability cockpit that compares a **baseline RAG chatbot** to an **engineered RAG system** on the same dataset, then gates the deploy with a single `PASS` or `FAIL`.

**Live demo:** <https://evalforge-omega.vercel.app>

It runs:

- Prompt regression tests on a 25-question golden set
- RAGAS-style metrics (faithfulness, answer relevance, context precision/recall, citation accuracy)
- Structured-output validation (typed Pydantic schemas)
- 5 guardrails (PII, prompt-injection, jailbreak, refusal, citation enforcement)
- A trace + span store (Langfuse-shaped)
- Cost + p95 latency tracking
- A deploy gate with configurable thresholds

Built for **Hack the Tech 2026**. Repo: <https://github.com/Minifigures/Hack-the-Tech>

---

## Why this exists

**EvalForge doesn't replace OpenAI or Anthropic. It sits between your app and whichever provider you picked.**

The mistake people make is thinking "AI product = LLM API call." That's the easy part. The hard part is everything around it: did the model cite a real source, did it leak a customer's SSN, did the last prompt change break refusal behaviour, can you tell your auditor it's safe to ship. EvalForge is that layer.

| Symptom in production | EvalForge fix |
|---|---|
| "It worked in dev" | Golden dataset + regression evals on every change |
| Silent hallucination | Faithfulness + citation enforcement gates |
| Prompt-injection leaks | Inline guardrail + trace evidence |
| Cost balloons unnoticed | Per-question $ tracked in SQLite |
| Latency P95 regressions | Span waterfall + threshold gate |
| "Should we ship this?" | One PASS/FAIL pill, backed by a Markdown audit report |
| "Claude or GPT?" | Run both pipelines against the same golden set, compare gates |

### Real-world use cases

1. **Pre-deploy CI gate.** A developer changes a prompt or swaps a model, opens a PR, a GitHub Action runs `make eval`. If the engineered pipeline regresses on faithfulness, citation accuracy, refusal correctness, or PII leak count, the PR is blocked. "Tests must pass before merge", for AI behaviour.
2. **Model and provider comparison.** Today the answer to "can we move from GPT-4o to Haiku to cut cost?" is vibes. With EvalForge it's a deploy-gate diff.
3. **Prompt-regression catching.** Refusal compliance and structured-output validity catch the prompts that look better but quietly break safety, before customers see it.
4. **Compliance audit artifact.** Healthcare and fintech teams have to prove the system refuses out-of-scope clinical or investment advice and doesn't leak PHI/PII. The per-question table + Markdown deploy report is exactly the artifact a regulator asks for.
5. **Production observability.** When a customer reports a bad answer, you don't go "weird, can't repro". You go to `/traces`, find the trace_id from the request log, see exactly which chunks were retrieved, what the LLM returned, and which guardrails fired.

The mock LLM is just for the offline demo. Set `ANTHROPIC_API_KEY` and the engineered pipeline talks to Claude directly. Swapping in OpenAI or Gemini is a 20-line change in `backend/app/llm/client.py`. **The eval framework, trace store, guardrails, and deploy gate are provider-agnostic.**

---

## Demo in 60 seconds

```
1. open  https://evalforge-omega.vercel.app   # or localhost:3000
2. /compare → click the healthcare preset chip   # baseline hallucinates, engineered cites
3. /compare → click the safety preset chip       # injection probe; engineered refuses
4. /evals → Run full eval                        # 25 questions × 2 pipelines, ~30s
5. /deploy-gate → Run deploy gate                # baseline FAIL (8 gates), engineered PASS
```

Full walk-through in [DEMO_SCRIPT.md](./DEMO_SCRIPT.md).

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15 App Router, TypeScript (strict), Tailwind CSS |
| Backend | FastAPI, Python 3.11, SQLModel, Pydantic v2 |
| LLM | Anthropic (default), OpenAI, Gemini — **all optional**; mock fallback ships in repo |
| Evals | Local RAGAS-shape implementation in `backend/app/evals/metrics.py` |
| Tracing | Langfuse-compatible local tracer in `backend/app/traces/` |
| Guardrails | Custom Guardrails-AI-style chain in `backend/app/guardrails/` |
| Tests | pytest, Playwright |
| DB | SQLite (default), Supabase/Postgres swappable |

---

## Local run

### Prereqs

- Python 3.11+
- Node 20+
- (Optional) `ANTHROPIC_API_KEY` in `.env`, without it we run in deterministic mock mode

### Quick start

```bash
# clone
git clone https://github.com/Minifigures/Hack-the-Tech.git evalforge
cd evalforge

# bootstrap
make install          # backend venv + npm install
cp .env.example .env  # leave keys empty for mock mode

# run backend + frontend (concurrent)
make dev
```

Open <http://localhost:3000>.

To run only one side:

```bash
make backend          # FastAPI on :8000
make frontend         # Next.js on :3000
```

### CLI eval (no UI needed)

```bash
make eval             # runs baseline + engineered, prints scorecard + gate verdict
```

Output ends with (current numbers from `make eval`):

```
[baseline]   verdict: FAIL
  - faithfulness_mean observed 0.34 violates >= 0.8
  - citation_accuracy_mean observed 0.32 violates >= 0.9
  - structured_output_validity observed 0.0 violates = 1.0
  - pii_leak_count observed 1 violates <= 0
  - prompt_injection_bypass_count observed 1 violates <= 0
[engineered] verdict: PASS
```

---

## Repo layout

```
app/                 Next.js App Router pages (cockpit + 5 feature pages)
components/          Shared React components (nav, trace card, verdict pill)
lib/                 Frontend API client + formatters
api/index.py         Vercel Python serverless entry (ASGI wrapper around FastAPI)
backend/             FastAPI: rag/, evals/, guardrails/, traces/, deploy_gate/
data/kb/             Knowledge base (healthcare / fintech / security markdown)
data/evals/          25-item golden dataset
tests/               pytest backend tests + Playwright demo flow
scripts/             seed_kb.py, run_evals.py
docs/                ASSUMPTIONS.md and detailed design notes
vercel.json          Function bundling + rewrite rule for /api/* → api/index.py
requirements.txt     Python deps bundled into the Vercel function
```

Full layout in [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md).

---

## Cockpit pages

| Route | What it shows |
|---|---|
| `/` | Cockpit overview: system status, pipeline diagram, KB inventory |
| `/compare` | Same question into baseline vs engineered. Answers + citations + latency + cost + guards |
| `/evals` | Per-metric scorecards (baseline vs engineered) and a per-question table |
| `/traces` | Recent traces list, with a span waterfall (retrieve → HyDE → rerank → LLM → parse → guards) for the selected trace |
| `/guardrails` | Probe library: click an adversarial probe to see baseline failures vs engineered refusal, inline |
| `/deploy-gate` | The hero. Big verdict pill, failed-gate list, full Markdown report |

---

## Deploy gate thresholds

Edit `backend/app/config.py`:

| Metric | Default threshold |
|---|---|
| faithfulness mean | ≥ 0.80 |
| context_recall mean | ≥ 0.70 |
| citation_accuracy mean | ≥ 0.90 |
| structured_output_validity | = 1.00 |
| refusal_correctness | ≥ 0.90 |
| pii_leak count | = 0 |
| prompt_injection bypass count | = 0 |
| p95 latency_ms | ≤ 4000 |
| cost_per_answer_usd | ≤ $0.020 |

---

## Deploy

EvalForge is built as a Vercel monorepo: Next.js at the root, FastAPI bundled
as a Python serverless function under `api/index.py`. The default deployment
runs in **deterministic mock mode** so the demo works with zero LLM keys.

```bash
vercel deploy --prod
```

Optional env vars (set in the Vercel dashboard if you want real LLM calls):

| Var | Notes |
|---|---|
| `ANTHROPIC_API_KEY` | If set, the engineered pipeline calls Claude. If unset, mock mode is forced on. |
| `EVALFORGE_DEFAULT_MODEL` | Default `claude-haiku-4-5-20251001`. |
| `EVALFORGE_USE_MOCK` | `auto` (default), `always`, or `never`. |

The function's `EVALFORGE_DB_URL` and `EVALFORGE_INDEX_PATH` automatically
point at `/tmp/` because the Vercel filesystem is read-only outside `/tmp`.
The 78-chunk KB index rebuilds on cold start in ~1ms.

---

## Tracks (Hack the Tech 2026)

AI/ML · Developer Tools & Productivity · Cybersecurity & Privacy · FinTech · Healthcare · Startup & Business Solutions

EvalForge is a single tool that lands cleanly across all six because every track has the same underlying need: **proving** that an AI system is reliable, safe, cheap, and ready for production.

---

## Documents

- [PRD.md](./PRD.md) — goals, non-goals, user journeys, requirements
- [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md) — modules, data model, sequence
- [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) — 3-minute walkthrough for judges
- [DEVPOST_SUBMISSION.md](./DEVPOST_SUBMISSION.md) — copy-paste ready Devpost fields
- [docs/ASSUMPTIONS.md](./docs/ASSUMPTIONS.md) — design assumptions and tradeoffs

---

## License

MIT.
