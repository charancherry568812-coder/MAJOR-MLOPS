"""SQLAlchemy ORM model — SystemEvent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    event_type = Column(String(50), nullable=False, index=True)  # SERVICE_START, SERVICE_STOP, HEALTH_CHECK, PIPELINE_STAGE, DRIFT_ALERT
    component = Column(String(50), nullable=False, index=True)   # API, DB, FLOWER, MLFLOW, PIPELINE
    status = Column(String(20), default="INFO", index=True)      # INFO, SUCCESS, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    details = Column(Text, default="{}")                         # JSON details
    created_at = Column(DateTime, default=_utcnow, index=True)
