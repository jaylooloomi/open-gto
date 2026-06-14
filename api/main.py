"""FastAPI app exposing the push/fold solver.

Run locally:  uvicorn api.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import SolveRequest, SolveResponse
from engine.games.push_fold import solve_push_fold

app = FastAPI(title="open-gto", version="0.1.0")

# Allow the Vite dev server to call the API during development (any local port).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> dict:
    return solve_push_fold(
        req.params.stack_bb, iterations=req.iterations, variant=req.variant
    )
