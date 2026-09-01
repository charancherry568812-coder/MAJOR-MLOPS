"""Transaction, Payment, and UPI Intent models with idempotency and lifecycle tracking."""

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


class Transaction(Base):
    """Core Banking Ledger Transaction with Idempotency and Full Risk Telemetry."""

    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=_uuid)
    transaction_reference = Column(String(64), unique=True, nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    request_id = Column(String(64), nullable=True, index=True)
    
    # Account & Client endpoints
    customer_id = Column(String(64), nullable=True, index=True)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=True, index=True)
    source_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    destination_account_id = Column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    
    # Financial details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    fee_amount = Column(Float, default=0.0)
    fx_rate = Column(Float, default=1.0)
    settlement_amount = Column(Float, default=0.0)
    settlement_currency = Column(String(3), default="INR")
    
    # Payment rail & Type
    payment_rail = Column(String(30), default="UPI", index=True)  # UPI, IMPS, NEFT, RTGS, SWIFT, SEPA, ACH, FEDWIRE, INTERNAL
    transaction_type = Column(String(50), default="TRANSFER", index=True)  # TRANSFER, PAYMENT, WITHDRAWAL, DEPOSIT, BILL_PAY, UPI_PAY, LOAN_DISBURSE, LOAN_EMI, CARD_TXN
    merchant_category = Column(String(100), default="General Retail")
    
    # Transaction Lifecycle
    status = Column(String(20), default="COMPLETED", index=True)  # INITIATED, VALIDATED, RISK_CHECK, PROCESSING, COMPLETED, FAILED, REVERSED, CANCELLED
    failure_reason = Column(String(255), nullable=True)
    
    # Risk, Fraud, & AML Scores
    velocity_score = Column(Float, default=25.0)
    amount_deviation = Column(Float, default=1.0)
    num_devices = Column(Integer, default=1)
    risk_score = Column(Float, default=5.0)  # 0-100 scale
    fraud_score = Column(Float, default=0.02)  # 0.0 - 1.0 probability
    risk_level = Column(String(20), default="LOW", index=True)  # LOW, MEDIUM, HIGH
    is_flagged = Column(Boolean, default=False, index=True)
    is_flagged_fraud = Column(Boolean, default=False)
    aml_flag = Column(Boolean, default=False)
    sanctions_check_passed = Column(Boolean, default=True)
    
    # Behavioral and Device Context
    ip_address = Column(String(45), default="127.0.0.1")
    device_id = Column(String(100), default="dev-primary-mobile")
    location_city = Column(String(100), default="Mumbai")
    description = Column(String(255), default="Funds transfer")
    
    created_at = Column(DateTime, default=_utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    source_account = relationship("Account", foreign_keys=[source_account_id], back_populates="source_transactions")
    destination_account = relationship("Account", foreign_keys=[destination_account_id], back_populates="destination_transactions")
    payment_record = relationship("Payment", back_populates="transaction", uselist=False, cascade="all, delete-orphan")


class Payment(Base):
    """External payment rail execution details for Domestic & Cross-Border routing."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=_uuid)
    payment_reference = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), unique=True, nullable=False)
    
    # Sender & Receiver information
    sender_name = Column(String(255), nullable=False)
    sender_identifier = Column(String(100), nullable=False)  # Account Number, VPA, IBAN
    receiver_name = Column(String(255), nullable=False)
    receiver_identifier = Column(String(100), nullable=False) # Account Number, VPA, IBAN
    
    # Specific Rail Clearing Identifiers
    upi_vpa = Column(String(100), nullable=True)
    upi_rrn = Column(String(12), nullable=True, index=True)  # 12-digit Retrieval Reference Number (NPCI)
    ifsc_code = Column(String(11), nullable=True)
    swift_bic = Column(String(11), nullable=True)
    iban = Column(String(34), nullable=True)
    routing_number = Column(String(9), nullable=True)
    
    source_country = Column(String(2), default="IN")
    destination_country = Column(String(2), default="IN")
    payment_rail = Column(String(30), default="UPI")
    
    # Provider metadata
    provider_name = Column(String(100), default="UPISandboxProvider")
    provider_transaction_id = Column(String(100), nullable=True)
    provider_status = Column(String(50), default="SUCCESS")
    is_sandbox = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    transaction = relationship("Transaction", back_populates="payment_record")


class UPIPaymentIntent(Base):
    """Dynamic UPI QR Code and intent generation for instant merchant/peer collections."""

    __tablename__ = "upi_payment_intents"

    id = Column(String(36), primary_key=True, default=_uuid)
    intent_reference = Column(String(64), unique=True, nullable=False, index=True)
    payee_vpa = Column(String(100), nullable=False)
    payee_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    note = Column(String(100), default="Payment via FedBank UPI")
    qr_payload = Column(Text, nullable=False)  # upi://pay?pa=...&pn=...&am=...
    status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, PAID, EXPIRED, CANCELLED
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
