"""Account and Beneficiary models with multi-currency, balance locking, and ledger support."""

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


class Account(Base):
    """Core Banking Account with transactional balance and strict concurrency controls."""

    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True, index=True)
    
    account_number = Column(String(34), unique=True, nullable=False, index=True)  # Up to 34 char for IBAN / 11-16 digit Indian
    account_type = Column(String(30), default="SAVINGS", index=True)  # SAVINGS, CURRENT, SALARY, FIXED_DEPOSIT, RECURRING_DEPOSIT, BUSINESS, MULTI_CURRENCY
    currency = Column(String(3), default="INR", nullable=False, index=True)
    
    # Financial Balances (Decimals stored as Float with validation rules)
    balance = Column(Float, default=50000.0, nullable=False)
    available_balance = Column(Float, default=50000.0, nullable=False)
    hold_amount = Column(Float, default=0.0, nullable=False)
    ledger_balance = Column(Float, default=50000.0, nullable=False)
    
    # Interest & Limits
    interest_rate = Column(Float, default=3.5)  # Annual savings interest %
    daily_transfer_limit = Column(Float, default=100000.0)
    per_transaction_limit = Column(Float, default=50000.0)
    
    # UPI Virtual Payment Address (VPA) linked to this account
    upi_vpa = Column(String(100), unique=True, nullable=True, index=True)  # e.g. customer@fedbank
    
    # Operational Status
    status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, FROZEN, DORMANT, RESTRICTED, CLOSED
    freeze_reason = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=True)
    
    # Version for optimistic locking concurrency control
    version = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    bank = relationship("Bank", back_populates="accounts")
    branch = relationship("Branch", back_populates="accounts")
    cards = relationship("Card", back_populates="account", cascade="all, delete-orphan")
    source_transactions = relationship("Transaction", foreign_keys="Transaction.source_account_id", back_populates="source_account")
    destination_transactions = relationship("Transaction", foreign_keys="Transaction.destination_account_id", back_populates="destination_account")


class Beneficiary(Base):
    """Registered Payee / Beneficiary for Domestic (IMPS/NEFT/RTGS/UPI) and International (SWIFT/SEPA) transfers."""

    __tablename__ = "beneficiaries"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    nickname = Column(String(100), nullable=False)
    beneficiary_name = Column(String(255), nullable=False)
    
    # Clearing identifiers
    account_number = Column(String(50), nullable=True)
    ifsc_code = Column(String(11), nullable=True)  # Indian IFSC
    upi_vpa = Column(String(100), nullable=True)   # Indian UPI handle
    iban = Column(String(34), nullable=True)       # International IBAN
    swift_bic = Column(String(11), nullable=True)  # SWIFT BIC
    routing_number = Column(String(9), nullable=True)
    
    bank_name = Column(String(255), default="")
    country_code = Column(String(2), default="IN")
    currency = Column(String(3), default="INR")
    payment_rail = Column(String(30), default="UPI")  # UPI, IMPS, NEFT, RTGS, SWIFT, SEPA
    
    transfer_limit = Column(Float, default=50000.0)
    is_verified = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    customer = relationship("Customer", back_populates="beneficiaries")
