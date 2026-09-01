"""Data Quality, Data Drift (PSI/KS), Model Drift, and Concept Drift models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class AdvancedDataDriftReport(Base):
    """Detailed statistical drift calculation (PSI, KS Test, Categorical, Missing Value)."""

    __tablename__ = "advanced_data_drift_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_id = Column(String(36), ForeignKey("ml_models.id"), nullable=True, index=True)
    dataset_version_id = Column(String(36), nullable=True)
    feature_name = Column(String(100), nullable=False, index=True)
    
    drift_method = Column(String(30), default="PSI")  # PSI, KS_TEST, CATEGORICAL_CHISQ, MISSING_VALUE_DELTA
    drift_score = Column(Float, nullable=False)
    threshold = Column(Float, default=0.10)
    status = Column(String(20), default="NO_DRIFT", index=True)  # NO_DRIFT, WARNING, DRIFT
    
    baseline_stats_json = Column(Text, default="{}")  # mean, std, quantiles
    current_stats_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=_utcnow, index=True)


class ModelDriftReport(Base):
    """Production Model Performance Degradation Tracking."""

    __tablename__ = "model_drift_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    
    baseline_accuracy = Column(Float, nullable=False)
    current_accuracy = Column(Float, nullable=False)
    accuracy_drop = Column(Float, default=0.0)
    
    baseline_f1 = Column(Float, nullable=False)
    current_f1 = Column(Float, nullable=False)
    f1_drop = Column(Float, default=0.0)
    
    baseline_auc = Column(Float, default=0.88)
    current_auc = Column(Float, default=0.87)
    
    status = Column(String(20), default="STABLE", index=True)  # STABLE, WARNING, DEGRADED, RETRAINING_TRIGGERED
    alert_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


class ConceptDriftReport(Base):
    """Ground truth vs prediction drift tracking when delayed labels arrive."""

    __tablename__ = "concept_drift_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    
    sample_size = Column(Integer, default=1000)
    brier_score = Column(Float, default=0.08)  # Probability calibration error
    expected_calibration_error = Column(Float, default=0.04)
    concept_drift_p_value = Column(Float, default=0.82)
    has_drifted = Column(Boolean, default=False)
    summary = Column(Text, default="Model input-to-label mapping remains statistically consistent.")
    created_at = Column(DateTime, default=_utcnow)
