"""Dataset Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DatasetResponse(BaseModel):
    id: str
    name: str
    bank_id: str
    bank_name: str = ""
    description: str = ""
    use_case: str = "credit_risk"
    file_size: int = 0
    status: str = "UPLOADED"
    current_version: str = "v1.0"
    rows: int = 0
    features: int = 0
    missing_values: int = 0
    duplicates: int = 0
    quality_score: float = 0.0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DatasetVersionResponse(BaseModel):
    id: str
    version: str
    rows: int = 0
    features: int = 0
    missing_values: int = 0
    duplicates: int = 0
    quality_score: float = 0.0
    statistics: Dict[str, Any] = {}
    feature_names: List[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataQualityResponse(BaseModel):
    overall_score: float = 0.0
    missing_value_report: Dict[str, Any] = {}
    duplicate_report: Dict[str, Any] = {}
    outlier_report: Dict[str, Any] = {}
    class_imbalance_report: Dict[str, Any] = {}
    recommendations: List[str] = []

    class Config:
        from_attributes = True
