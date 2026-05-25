from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .rag.index import build_index, sources_summary
from .routers import compare, deploy_gate, evals, guardrails, traces

app = FastAPI(title="EvalForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compare.router)
app.include_router(evals.router)
app.include_router(traces.router)
app.include_router(guardrails.router)
app.include_router(deploy_gate.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    # Ensure KB index exists. Cheap on a 25-chunk KB.
    build_index()


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "mock_mode": settings.use_mock,
        "provider": settings.active_provider,
        "default_model": (
            settings.EVALFORGE_GROQ_MODEL
            if settings.active_provider == "groq"
            else settings.EVALFORGE_DEFAULT_MODEL
        ),
        "db": "postgres" if not settings.EVALFORGE_DB_URL.startswith("sqlite") else "sqlite",
        "kb_sources": sources_summary(),
    }


@app.get("/api/config")
def config() -> dict:
    t = settings.thresholds
    return {
        "mock_mode": settings.use_mock,
        "provider": settings.active_provider,
        "default_model": (
            settings.EVALFORGE_GROQ_MODEL
            if settings.active_provider == "groq"
            else settings.EVALFORGE_DEFAULT_MODEL
        ),
        "thresholds": t.model_dump(),
    }
