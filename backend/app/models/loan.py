"""Loan and LoanPayment amortization models with EMI calculations."""

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


class Loan(Base):
    """Retail & Commercial Loan product with full amortization and risk scoring."""

    __tablename__ = "loans"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=True)  # Disbursement account
    
    loan_number = Column(String(50), unique=True, nullable=False, index=True)
    loan_type = Column(String(30), default="PERSONAL", index=True)  # PERSONAL, HOME, VEHICLE, EDUCATION, BUSINESS, CREDIT_LINE
    currency = Column(String(3), default="INR", nullable=False)
    
    # Financial Terms
    principal_amount = Column(Float, nullable=False)
    interest_rate_annual = Column(Float, nullable=False)  # Annual interest % (e.g. 10.5)
    tenure_months = Column(Integer, nullable=False)        # E.g. 36 months
    emi_amount = Column(Float, nullable=False)             # Calculated monthly installment
    total_interest_payable = Column(Float, default=0.0)
    total_amount_payable = Column(Float, default=0.0)
    
    # Outstanding balances
    outstanding_principal = Column(Float, nullable=False)
    paid_principal = Column(Float, default=0.0)
    paid_interest = Column(Float, default=0.0)
    overdue_amount = Column(Float, default=0.0)
    missed_installments = Column(Integer, default=0)
    
    # Lifecycle & Risk Status
    status = Column(String(30), default="ACTIVE", index=True)  # APPLICATION, ELIGIBILITY, CREDIT_CHECK, RISK_ASSESSMENT, REVIEW, APPROVED, DISBURSED, ACTIVE, DELINQUENT, CLOSED, REJECTED
    credit_score_at_origination = Column(Integer, default=750)
    risk_grade = Column(String(5), default="A", index=True)  # AAA, AA, A, BBB, BB, B, C, D
    probability_of_default = Column(Float, default=0.024)   # From ML credit model
    
    start_date = Column(DateTime, default=_utcnow)
    next_due_date = Column(DateTime, nullable=True)
    maturity_date = Column(DateTime, nullable=True)
    disbursed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="loans")
    payments = relationship("LoanPayment", back_populates="loan", cascade="all, delete-orphan")


class LoanPayment(Base):
    """Scheduled & Executed Loan EMI Installments."""

    __tablename__ = "loan_payments"

    id = Column(String(36), primary_key=True, default=_uuid)
    loan_id = Column(String(36), ForeignKey("loans.id"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    
    due_date = Column(DateTime, nullable=False)
    emi_amount = Column(Float, nullable=False)
    principal_component = Column(Float, nullable=False)
    interest_component = Column(Float, nullable=False)
    remaining_balance = Column(Float, nullable=False)
    
    status = Column(String(20), default="SCHEDULED", index=True)  # SCHEDULED, PAID, OVERDUE, WAIVED
    paid_date = Column(DateTime, nullable=True)
    penalty_fee = Column(Float, default=0.0)
    transaction_id = Column(String(36), nullable=True)

    loan = relationship("Loan", back_populates="payments")
