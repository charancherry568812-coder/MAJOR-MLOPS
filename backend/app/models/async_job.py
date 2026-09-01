"""Async Job and background task tracking model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class AsyncJob(Base):
    """Background asynchronous task execution state."""

    __tablename__ = "async_jobs"

    id = Column(String(36), primary_key=True, default=_uuid)
    job_type = Column(String(50), nullable=False, index=True)  # ML_TRAINING, FEDERATED_TRAINING, DATASET_INGESTION, DRIFT_DETECTION, REPORT_GENERATION, BATCH_PREDICTION, AML_SCAN
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="QUEUED", index=True)  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    progress_percent = Column(Float, default=0.0)
    current_step = Column(String(255), default="Initialized")
    
    result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
