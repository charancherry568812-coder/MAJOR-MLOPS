"""SQLAlchemy ORM model — Deployment."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String(36), primary_key=True, default=_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    status = Column(String(20), default="DEPLOYING", index=True)  # DEPLOYING,ACTIVE,INACTIVE,FAILED,ROLLED_BACK
    endpoint = Column(String(255), default="/api/v1/predict")
    deployed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)
    rolled_back_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    model_version = relationship("ModelVersion", back_populates="deployments")
