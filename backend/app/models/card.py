"""Card management model with tokenized identifiers and RuPay / Visa / Mastercard network support."""

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


class Card(Base):
    """Debit, Credit, and Virtual Card product with tokenization security."""

    __tablename__ = "cards"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    
    # Secure Tokenized & Masked Attributes (NEVER store real plaintext PAN or CVV)
    card_number_masked = Column(String(20), nullable=False)   # e.g. 6071-XXXX-XXXX-8921
    card_token = Column(String(64), unique=True, nullable=False, index=True)  # PCI-DSS Vault Token
    card_type = Column(String(20), default="DEBIT", index=True)  # DEBIT, CREDIT, VIRTUAL, PREPAID
    card_network = Column(String(20), default="RUPAY", index=True)  # RUPAY, VISA, MASTERCARD, AMEX
    
    cardholder_name = Column(String(100), nullable=False)
    expiry_month = Column(Integer, default=12)
    expiry_year = Column(Integer, default=2029)
    
    # Financial Limits
    credit_limit = Column(Float, default=0.0)
    available_credit = Column(Float, default=0.0)
    daily_atm_limit = Column(Float, default=40000.0)
    daily_pos_limit = Column(Float, default=100000.0)
    daily_online_limit = Column(Float, default=100000.0)
    
    # Security & Feature Controls
    status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, FROZEN, BLOCKED, EXPIRED, CANCELLED
    international_enabled = Column(Boolean, default=False)
    contactless_enabled = Column(Boolean, default=True)
    online_transactions_enabled = Column(Boolean, default=True)
    atm_withdrawals_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="cards")
    account = relationship("Account", back_populates="cards")
