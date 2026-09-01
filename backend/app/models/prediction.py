"""SQLAlchemy ORM models — Prediction, PredictionBatch."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    use_case = Column(String(50), nullable=False, index=True)
    input_data = Column(Text, nullable=False)  # JSON
    prediction_result = Column(String(50), nullable=False)
    probability = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_category = Column(String(50), nullable=True)
    explanation = Column(Text, default="{}")  # JSON - SHAP values
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class PredictionBatch(Base):
    __tablename__ = "prediction_batches"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    use_case = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    result_file_path = Column(String(500), nullable=True)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    status = Column(String(20), default="QUEUED", index=True)  # QUEUED,PROCESSING,COMPLETED,FAILED
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
