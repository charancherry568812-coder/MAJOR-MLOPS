"""SQLAlchemy ORM models — Bank and BankUser."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Bank(Base):
    __tablename__ = "banks"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    branch = Column(String(255), default="Main Branch")
    contact_person = Column(String(255), default="")
    email = Column(String(255), default="")
    phone = Column(String(50), default="")
    location = Column(String(255), default="")
    country_code = Column(String(2), ForeignKey("countries.code"), default="IN", index=True)
    status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, INACTIVE, SUSPENDED
    participation_status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, IDLE, TRAINING, OFFLINE
    num_customers = Column(Integer, default=5000)
    dataset_size = Column(Integer, default=0)
    last_training_time = Column(DateTime, nullable=True)
    current_model_version = Column(String(50), default="v1.0.0")
    accuracy = Column(Float, default=0.85)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    country_rel = relationship("Country", back_populates="banks")
    bank_users = relationship("BankUser", back_populates="bank")
    federated_clients = relationship("FederatedClient", back_populates="bank")
    datasets = relationship("Dataset", back_populates="bank")
    branches = relationship("Branch", back_populates="bank", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="bank", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="bank", cascade="all, delete-orphan")


class BankUser(Base):
    __tablename__ = "bank_users"

    id = Column(String(36), primary_key=True, default=_uuid)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), default="member")
    created_at = Column(DateTime, default=_utcnow)

    bank = relationship("Bank", back_populates="bank_users")
    user = relationship("User", back_populates="bank_users")
