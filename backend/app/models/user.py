"""SQLAlchemy ORM models — User and Role."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), default="")
    permissions = Column(Text, default="{}")  # JSON string
    created_at = Column(DateTime, default=_utcnow)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    role = relationship("Role", back_populates="users")
    bank_users = relationship("BankUser", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
