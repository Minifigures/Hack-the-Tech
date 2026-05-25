from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..deploy_gate.gate import evaluate_run
from ..evals.runner import run_full_eval
from ..models import DeployGateResponse
from . import evals as evals_router

router = APIRouter(prefix="/api/deploy-gate", tags=["deploy-gate"])


@router.post("/run", response_model=DeployGateResponse)
def run_gate() -> DeployGateResponse:
    """Run a full eval then evaluate the deploy gate against both pipelines."""
    result = run_full_eval()
    evals_router._LAST = result  # warm cache for the evals dashboard
    return evaluate_run(result)


@router.get("/latest", response_model=DeployGateResponse)
def latest() -> DeployGateResponse:
    cached = evals_router._LAST
    if cached is None:
        raise HTTPException(status_code=404, detail="No eval run cached. POST /api/deploy-gate/run first.")
    return evaluate_run(cached)
