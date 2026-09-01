"""SQLAlchemy ORM models — FraudAlert."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.transaction_payment import Transaction


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    alert_code = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True, index=True)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=True, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    severity = Column(String(20), default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="OPEN", index=True)  # OPEN, INVESTIGATING, RESOLVED, REJECTED
    flag_reason = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

    transaction = relationship("Transaction")
    resolver = relationship("User")
