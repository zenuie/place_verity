# veritas_app/models/schemas.py
from typing import Dict, Any, List, Literal

from pydantic import BaseModel, Field


class ManualFetchRequest(BaseModel):
    place_id: str


class ReviewApproveRequest(BaseModel):
    place_id: str
    updates: Dict[str, Any]


class LockStatusResponse(BaseModel):
    locked: bool
    start_time: str | None


class SuccessResponse(BaseModel):
    message: str


class Score(BaseModel):
    source_trust: float = Field(..., ge=0, le=1)
    freshness: float = Field(..., ge=0, le=1)
    consistency: float = Field(..., ge=0, le=1)
    impact: float = Field(..., ge=0, le=1)
    total: float = Field(..., ge=0, le=1)


class Difference(BaseModel):
    field: str
    old_value: Any
    new_value: Any
    evidence_url: str
    evidence_quote: str


class VerificationReport(BaseModel):
    decision_suggestion: Literal["review", "approve"]
    scores: Score
    differences: List[Difference]


class ErrorDetail(BaseModel):
    detail: str
