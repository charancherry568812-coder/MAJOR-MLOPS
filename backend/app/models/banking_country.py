"""Banking Countries, Currencies, Regulations, and Payment Rails configuration models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Country(Base):
    """Country configuration for global banking governance."""

    __tablename__ = "countries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(2), unique=True, index=True, nullable=False)  # ISO-2: IN, US, GB, etc.
    code_alpha3 = Column(String(3), unique=True, index=True, nullable=False)  # IND, USA, GBR
    name = Column(String(100), nullable=False)
    default_currency = Column(String(3), nullable=False, default="INR")
    locale = Column(String(10), default="en-IN")
    timezone = Column(String(50), default="Asia/Kolkata")
    regulatory_body = Column(String(100), default="Reserve Bank of India (RBI)")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    banks = relationship("Bank", back_populates="country_rel", cascade="all, delete-orphan")
    payment_rails = relationship("PaymentRailConfig", back_populates="country", cascade="all, delete-orphan")


class Currency(Base):
    """Multi-currency exchange rates and precision definitions."""

    __tablename__ = "currencies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(3), unique=True, index=True, nullable=False)  # INR, USD, EUR, GBP, AED, CAD, AUD, SGD, JPY
    name = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)  # ₹, $, €, £, د.إ, etc.
    decimals = Column(Integer, default=2)
    exchange_rate_to_usd = Column(Float, default=1.0)  # Reference FX rate
    is_base = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class BankingRegulation(Base):
    """Country-specific banking rules, statutory thresholds, and AML risk tiers."""

    __tablename__ = "banking_regulations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(String(2), ForeignKey("countries.code"), index=True, nullable=False)
    regulatory_framework = Column(String(100), nullable=False)  # e.g., RBI Master Directions, FCA, Fed
    cash_transaction_limit = Column(Float, default=50000.0)  # INR 50k / USD 10k CTR threshold
    suspicious_velocity_threshold = Column(Integer, default=5)  # 5 txn/min
    kyc_mandatory_threshold = Column(Float, default=10000.0)
    pan_mandatory_threshold = Column(Float, default=50000.0)  # Indian Section 139A requirement
    aml_structuring_threshold = Column(Float, default=1000000.0)  # INR 10 Lakhs (LCTR)
    financial_year_start_month = Column(Integer, default=4)  # April for India
    is_active = Column(Boolean, default=True)


class PaymentRailConfig(Base):
    """Domestic & International payment rails with limits and fee schedules."""

    __tablename__ = "payment_rail_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rail_code = Column(String(30), index=True, nullable=False)  # UPI, IMPS, NEFT, RTGS, SWIFT, SEPA, ACH, FEDWIRE, FASTER_PAYMENTS
    rail_name = Column(String(100), nullable=False)
    country_code = Column(String(2), ForeignKey("countries.code"), index=True, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    min_amount = Column(Float, default=1.0)
    max_amount = Column(Float, default=100000.0)  # e.g. UPI 1 Lakh limit
    daily_limit = Column(Float, default=100000.0)
    per_txn_fee_flat = Column(Float, default=0.0)
    per_txn_fee_percent = Column(Float, default=0.0)
    is_instant = Column(Boolean, default=True)
    is_cross_border = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sandbox_mode = Column(Boolean, default=True)

    country = relationship("Country", back_populates="payment_rails")
