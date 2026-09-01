"""SQLAlchemy ORM models — MLModel, ModelVersion, ModelMetrics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    use_case = Column(String(50), nullable=False, index=True)
    algorithm = Column(String(50), nullable=False)
    description = Column(Text, default="")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    versions = relationship("ModelVersion", back_populates="model", order_by="ModelVersion.created_at.desc()")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_id = Column(String(36), ForeignKey("ml_models.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    training_run_id = Column(String(36), ForeignKey("training_runs.id"), nullable=True)
    file_path = Column(String(500), nullable=True)
    preprocessor_path = Column(String(500), nullable=True)
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    auc = Column(Float, nullable=True)
    loss = Column(Float, nullable=True)
    training_round = Column(Integer, default=5)
    confusion_matrix = Column(Text, default="[]")  # JSON
    classification_report = Column(Text, default="{}")  # JSON
    feature_importance = Column(Text, default="{}")  # JSON
    status = Column(String(20), default="REGISTERED", index=True)
    # REGISTERED, VALIDATED, APPROVED, STAGING, PRODUCTION, ARCHIVED, FAILED
    deployment_status = Column(String(20), default="NONE")
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_reason = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    model = relationship("MLModel", back_populates="versions")
    metrics = relationship("ModelMetrics", back_populates="model_version")
    deployments = relationship("Deployment", back_populates="model_version")


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    model_version = relationship("ModelVersion", back_populates="metrics")
