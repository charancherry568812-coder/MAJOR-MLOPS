"""SQLAlchemy ORM model — FederatedClient."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class FederatedClient(Base):
    __tablename__ = "federated_clients"

    id = Column(String(36), primary_key=True, default=_uuid)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="IDLE", index=True)  # ONLINE,OFFLINE,TRAINING,IDLE,ERROR,DISABLED
    host = Column(String(255), default="localhost")
    port = Column(Integer, default=8081)
    last_heartbeat = Column(DateTime, nullable=True)
    current_round = Column(Integer, default=0)
    dataset_version = Column(String(50), nullable=True)
    local_accuracy = Column(Float, nullable=True)
    local_loss = Column(Float, nullable=True)
    training_status = Column(String(50), default="IDLE")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    bank = relationship("Bank", back_populates="federated_clients")
