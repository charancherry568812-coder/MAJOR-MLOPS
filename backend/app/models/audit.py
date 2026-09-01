"""SQLAlchemy ORM model — AuditLog."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    # LOGIN, LOGOUT, FAILED_LOGIN, CREATE, UPDATE, DELETE, UPLOAD, DOWNLOAD,
    # TRAIN, APPROVE, DEPLOY, ROLLBACK, PREDICT
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, default="{}")  # JSON
    ip_address = Column(String(45), nullable=True)
    status = Column(String(20), default="SUCCESS")  # SUCCESS, FAILURE
    created_at = Column(DateTime, default=_utcnow, index=True)
