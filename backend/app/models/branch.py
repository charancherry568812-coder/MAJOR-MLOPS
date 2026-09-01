"""Branch management with IFSC, MICR, SWIFT/BIC, Routing Number support."""

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


class Branch(Base):
    """Bank branch office with regional regulatory clearing codes."""

    __tablename__ = "branches"

    id = Column(String(36), primary_key=True, default=_uuid)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)  # Branch Code
    name = Column(String(255), nullable=False)
    
    # Regional clearing codes
    ifsc_code = Column(String(11), index=True, nullable=True)  # Indian IFSC: e.g. SBIN0001234
    micr_code = Column(String(9), nullable=True)   # Indian MICR 9-digit
    swift_bic = Column(String(11), nullable=True)  # SWIFT BIC 8/11 char
    routing_number = Column(String(9), nullable=True)  # US ABA Routing
    bsb_number = Column(String(6), nullable=True)  # Australian BSB
    sort_code = Column(String(6), nullable=True)   # UK Sort Code

    address = Column(String(255), default="")
    city = Column(String(100), default="Mumbai")
    state = Column(String(100), default="Maharashtra")
    postal_code = Column(String(20), default="400001")
    country_code = Column(String(2), default="IN")
    
    phone = Column(String(50), default="")
    email = Column(String(255), default="")
    manager_name = Column(String(100), default="")
    is_headquarters = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    bank = relationship("Bank", back_populates="branches")
    accounts = relationship("Account", back_populates="branch")
