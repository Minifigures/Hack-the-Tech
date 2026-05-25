"""Vercel Python serverless entry for the EvalForge FastAPI backend.

Vercel's filesystem routing maps this file to `/api/index`. We pair it with a
catch-all rewrite in `vercel.json` so any request under `/api/*` is forwarded
here. Vercel turns the captured path segment into a query parameter, so we
re-construct the original URL inside an ASGI wrapper before handing the
request to FastAPI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

# `settings.use_mock` already auto-detects mock mode when no provider key is
# present. We deliberately don't force EVALFORGE_USE_MOCK=always here, because
# that would override a Groq/Anthropic key the user set in Vercel env.

# The Vercel filesystem is read-only except for /tmp.
os.environ.setdefault("EVALFORGE_DB_URL", "sqlite:////tmp/evalforge.db")
os.environ.setdefault("EVALFORGE_INDEX_PATH", "/tmp/index.json")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app as _fastapi_app  # noqa: E402
from app.db import init_db  # noqa: E402
from app.rag.index import build_index  # noqa: E402

# Eagerly initialise the DB schema + rebuild the KB index in /tmp on cold start.
# On Vercel the function startup event also fires, but doing this at import
# time guarantees the state is ready before the first request hits FastAPI.
init_db()
build_index()


def _rewrite_scope(scope: dict) -> dict:
    """Re-derive the original `/api/...` path from the `evpath` query param."""
    if scope.get("type") != "http":
        return scope
    raw_qs = scope.get("query_string", b"").decode("latin-1")
    params = parse_qsl(raw_qs, keep_blank_values=True)
    evpath = None
    rest: list[tuple[str, str]] = []
    for k, v in params:
        if k == "evpath" and evpath is None:
            evpath = v
        else:
            rest.append((k, v))
    if evpath is None:
        return scope
    new_path = "/api/" + evpath.lstrip("/")
    new_qs = urlencode(rest)
    return {
        **scope,
        "path": new_path,
        "raw_path": new_path.encode("utf-8"),
        "query_string": new_qs.encode("latin-1"),
    }


async def app(scope, receive, send):  # noqa: D401 - ASGI3
    await _fastapi_app(_rewrite_scope(scope), receive, send)
