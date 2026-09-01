"""SQLAlchemy ORM models — MonitoringMetric, DriftReport."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class MonitoringMetric(Base):
    __tablename__ = "monitoring_metrics"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True, index=True)
    metric_type = Column(String(20), nullable=False, index=True)  # MODEL, DATA, SYSTEM
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=True)
    status = Column(String(20), default="NORMAL")  # NORMAL, WARNING, CRITICAL
    details = Column(Text, default="{}")  # JSON
    created_at = Column(DateTime, default=_utcnow)


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True, index=True)
    feature_name = Column(String(100), nullable=False)
    drift_type = Column(String(20), nullable=False)  # DATA, MODEL, PREDICTION
    drift_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # NORMAL, WARNING, CRITICAL
    method = Column(String(20), nullable=False)  # PSI, KS, PERFORMANCE
    reference_distribution = Column(Text, default="{}")  # JSON
    current_distribution = Column(Text, default="{}")  # JSON
    created_at = Column(DateTime, default=_utcnow)
