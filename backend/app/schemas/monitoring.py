"""Monitoring Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MonitoringOverview(BaseModel):
    model_metrics: List[Dict[str, Any]] = []
    data_metrics: List[Dict[str, Any]] = []
    system_metrics: Dict[str, Any] = {}
    drift_summary: Dict[str, Any] = {}


class DriftReportResponse(BaseModel):
    id: str
    feature_name: str
    drift_type: str
    drift_score: float
    threshold: float
    status: str
    method: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemMetricsResponse(BaseModel):
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    api_latency_avg: float = 0.0
    api_error_rate: float = 0.0
    request_count: int = 0
    db_connections: int = 0
