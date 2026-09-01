"""Prediction Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PredictionRequest(BaseModel):
    use_case: str = "credit_risk"
    model_version_id: Optional[str] = None
    features: Dict[str, Any]


class PredictionResponse(BaseModel):
    id: str
    prediction: str
    probability: float
    risk_score: float
    risk_category: str
    model_version: str = ""
    explanation: Dict[str, Any] = {}
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PredictionHistoryResponse(BaseModel):
    id: str
    use_case: str
    prediction_result: str
    probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    model_version: str = ""
    input_data: Dict[str, Any] = {}
    explanation: Dict[str, Any] = {}
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchPredictionResponse(BaseModel):
    id: str
    use_case: str
    total_records: int = 0
    processed_records: int = 0
    status: str = "QUEUED"
    result_file_path: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
