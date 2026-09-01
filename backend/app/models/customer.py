"""Customer and CustomerProfile models with India (PAN/Aadhaar) and Global identity attributes."""

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


class Customer(Base):
    """Enterprise Customer profile supporting Individual and Corporate banking."""

    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=_uuid)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    customer_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_type = Column(String(20), default="INDIVIDUAL", index=True)  # INDIVIDUAL, BUSINESS, CORPORATE, NRI
    
    first_name = Column(String(100), default="")
    last_name = Column(String(100), default="")
    company_name = Column(String(255), default="")  # For corporate/business accounts
    email = Column(String(255), index=True, nullable=False)
    phone = Column(String(50), index=True, default="")
    date_of_birth = Column(String(20), default="1985-01-01")
    gender = Column(String(20), default="NOT_SPECIFIED")
    
    # Address & Country
    country_code = Column(String(2), default="IN", index=True)  # IN, US, GB, etc.
    address_line1 = Column(String(255), default="")
    address_line2 = Column(String(255), default="")
    city = Column(String(100), default="Mumbai")
    state = Column(String(100), default="Maharashtra")
    postal_code = Column(String(20), default="400001")
    
    # Financial & Risk Profile
    employment_status = Column(String(50), default="SALARIED")  # SALARIED, SELF_EMPLOYED, BUSINESS, RETIRED, STUDENT
    employer_name = Column(String(255), default="")
    annual_income = Column(Float, default=750000.0)  # in base or local currency (INR 7.5L)
    credit_score = Column(Integer, default=740, index=True)  # CIBIL / FICO score 300-900
    credit_risk_tier = Column(String(20), default="LOW_RISK", index=True)  # LOW_RISK, MEDIUM_RISK, HIGH_RISK
    customer_segment = Column(String(30), default="RETAIL", index=True)  # RETAIL, PRIORITY, WEALTH, SME, CORPORATE
    
    # Regulatory & Compliance Statuses
    kyc_status = Column(String(20), default="VERIFIED", index=True)  # NOT_STARTED, PENDING, VERIFIED, REJECTED, EXPIRED
    aml_status = Column(String(20), default="CLEAR", index=True)      # CLEAR, UNDER_MONITORING, SUSPICIOUS, RESTRICTED
    account_status = Column(String(20), default="ACTIVE", index=True) # ACTIVE, DORMANT, FROZEN, CLOSED
    
    # Regional Identity Documents (Masked / Hashed for Privacy)
    pan_number = Column(String(20), index=True, nullable=True)        # Indian PAN (e.g. ABCDE1234F)
    aadhaar_masked = Column(String(20), nullable=True)                # Indian Aadhaar XXXX-XXXX-1234
    aadhaar_vault_token = Column(String(64), nullable=True)           # Secure hashed token for deduplication
    passport_number = Column(String(50), nullable=True)               # Passport for International / NRI
    ssn_tin_masked = Column(String(20), nullable=True)                # US SSN / TIN masked
    
    is_pep = Column(Boolean, default=False)  # Politically Exposed Person check
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    bank = relationship("Bank", back_populates="customers")
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="customer", cascade="all, delete-orphan")
    cards = relationship("Card", back_populates="customer", cascade="all, delete-orphan")
    beneficiaries = relationship("Beneficiary", back_populates="customer", cascade="all, delete-orphan")
    kyc_cases = relationship("KYCCase", back_populates="customer", cascade="all, delete-orphan")
    aml_alerts = relationship("AMLAlert", back_populates="customer", cascade="all, delete-orphan")
    profile = relationship("CustomerProfile", back_populates="customer", uselist=False, cascade="all, delete-orphan")


class CustomerProfile(Base):
    """Extended behavioral analytics, risk scoring, and preferences."""

    __tablename__ = "customer_profiles"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), unique=True, nullable=False)
    
    behavioral_risk_score = Column(Float, default=12.5)  # 0-100 scale
    total_assets = Column(Float, default=1200000.0)
    total_liabilities = Column(Float, default=350000.0)
    preferred_language = Column(String(10), default="en")  # en, hi, kn
    mfa_enabled = Column(Boolean, default=True)
    upi_autopay_limit = Column(Float, default=5000.0)
    international_payments_enabled = Column(Boolean, default=False)
    risk_notes = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer = relationship("Customer", back_populates="profile")
