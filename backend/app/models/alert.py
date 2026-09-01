"""SQLAlchemy ORM model — Alert."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    alert_type = Column(String(50), nullable=False, index=True)
    # MODEL_DEGRADATION, DATA_DRIFT, CLIENT_OFFLINE, TRAINING_FAILURE,
    # DEPLOYMENT_FAILURE, DATASET_QUALITY, SECURITY_EVENT
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, CRITICAL
    title = Column(String(255), nullable=False)
    message = Column(Text, default="")
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
