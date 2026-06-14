"""Pydantic request/response contracts for the solver API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SolveParams(BaseModel):
    stack_bb: float = Field(10.0, gt=0, le=500, description="Effective stack in big blinds")


class SolveRequest(BaseModel):
    game: Literal["push_fold"] = "push_fold"
    params: SolveParams = SolveParams()
    iterations: int = Field(1500, ge=1, le=200_000)
    variant: Literal["cfr", "cfr_plus", "dcfr"] = "cfr_plus"


class SolveResponse(BaseModel):
    stack_bb: float
    sb_jam: dict[str, float]
    bb_call: dict[str, float]
    exploitability: float


class PreflopRequest(BaseModel):
    stack_bb: float = Field(50.0, gt=0, le=200, description="Effective stack in big blinds")
    iterations: int = Field(1000, ge=1, le=50_000)
