"""Audit, Report, Settings, Notification, Dashboard schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Audit ─────────────────────────────────────────────────────
class AuditLogResponse(BaseModel):
    id: str
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    status: str = "SUCCESS"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Report ────────────────────────────────────────────────────
class ReportGenerateRequest(BaseModel):
    report_type: str = "TRAINING"  # TRAINING, MODEL_PERFORMANCE, DRIFT, AUDIT
    format: str = "CSV"  # PDF, CSV
    filters: Dict[str, Any] = {}


class ReportResponse(BaseModel):
    id: str
    report_type: str
    format: str
    file_path: Optional[str] = None
    status: str = "GENERATING"
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Settings ──────────────────────────────────────────────────
class SettingResponse(BaseModel):
    id: str
    key: str
    value: str
    description: str
    category: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SettingUpdateRequest(BaseModel):
    value: str


# ── Notification ──────────────────────────────────────────────
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str = "INFO"
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────
class AdminDashboardResponse(BaseModel):
    total_banks: int = 0
    active_clients: int = 0
    total_training_runs: int = 0
    registered_models: int = 0
    production_models: int = 0
    average_accuracy: float = 0.0
    active_alerts: int = 0
    system_health: str = "HEALTHY"
    recent_activities: List[Dict[str, Any]] = []
    training_trend: List[Dict[str, Any]] = []
    model_performance: List[Dict[str, Any]] = []
    client_status_summary: Dict[str, int] = {}
    prediction_trend: List[Dict[str, Any]] = []
    risk_distribution: Dict[str, int] = {}


class BankDashboardResponse(BaseModel):
    bank_name: str = ""
    dataset_count: int = 0
    local_training_count: int = 0
    federated_participation_count: int = 0
    local_metrics: Dict[str, Any] = {}
    global_metrics: Dict[str, Any] = {}
    model_versions: List[Dict[str, Any]] = []
    recent_predictions: List[Dict[str, Any]] = []
    alerts: List[Dict[str, Any]] = []
