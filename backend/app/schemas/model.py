"""Model registry Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1)
    use_case: str = "credit_risk"
    algorithm: str = "random_forest"
    description: str = ""


class ModelResponse(BaseModel):
    id: str
    name: str
    use_case: str
    algorithm: str
    description: str
    versions_count: int = 0
    latest_version: Optional[str] = None
    production_version: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelVersionResponse(BaseModel):
    id: str
    model_id: str
    model_name: str = ""
    version: str
    algorithm: str = ""
    use_case: str = ""
    accuracy: Optional[float] = None
    precision_score: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    auc: Optional[float] = None
    confusion_matrix: List[List[int]] = []
    classification_report: Dict[str, Any] = {}
    feature_importance: Dict[str, float] = {}
    status: str = "REGISTERED"
    deployment_status: str = "NONE"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
    training_run_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelApproveRequest(BaseModel):
    reason: str = Field(default="Approved after review")
