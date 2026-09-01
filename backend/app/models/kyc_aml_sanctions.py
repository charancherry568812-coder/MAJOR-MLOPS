"""KYC, AML, and Sanctions models for India and International compliance."""

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


class KYCCase(Base):
    """Customer KYC Verification case with sandbox verification adapters."""

    __tablename__ = "kyc_cases"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Status lifecycle
    status = Column(String(20), default="PENDING", index=True)  # NOT_STARTED, PENDING, VERIFIED, REJECTED, EXPIRED
    verification_tier = Column(String(20), default="TIER_2_FULL")  # TIER_1_MIN_KYC, TIER_2_FULL, TIER_3_VIDEO_KYC
    verification_provider = Column(String(100), default="SANDBOX_NSDL_UIDAI")
    
    # Verification scores & risk flags
    verification_score = Column(Float, default=98.5)
    pan_verified = Column(Boolean, default=True)
    aadhaar_verified = Column(Boolean, default=True)
    face_match_score = Column(Float, default=96.2)
    risk_flags = Column(String(255), default="NO_RISK_DETECTED")
    
    reviewer_id = Column(String(36), nullable=True)
    review_notes = Column(Text, default="Automated sandbox verification validated successfully")
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="kyc_cases")
    documents = relationship("KYCDocument", back_populates="kyc_case", cascade="all, delete-orphan")


class KYCDocument(Base):
    """Uploaded KYC Document Metadata with Hashed Identifiers."""

    __tablename__ = "kyc_documents"

    id = Column(String(36), primary_key=True, default=_uuid)
    kyc_case_id = Column(String(36), ForeignKey("kyc_cases.id"), nullable=False, index=True)
    
    document_type = Column(String(30), nullable=False)  # PAN, AADHAAR, PASSPORT, VOTER_ID, DRIVING_LICENSE, UTILITY_BILL
    document_number_masked = Column(String(50), nullable=False)
    document_hash = Column(String(64), nullable=False)  # SHA-256 hash for integrity
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=102400)
    mime_type = Column(String(50), default="application/pdf")
    verification_status = Column(String(20), default="VERIFIED")
    created_at = Column(DateTime, default=_utcnow)

    kyc_case = relationship("KYCCase", back_populates="documents")


class AMLAlert(Base):
    """Automated AML Suspicious Transaction & Activity Alerts."""

    __tablename__ = "aml_alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    alert_code = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    transaction_id = Column(String(36), nullable=True, index=True)
    
    # Rule / Pattern violation
    alert_type = Column(String(50), nullable=False, index=True)  # STRUCTURING, UNUSUAL_FREQUENCY, RAPID_MOVEMENT, VELOCITY_ANOMALY, HIGH_RISK_GEO, SHELL_COMPANY_PATTERN
    severity = Column(String(20), default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Float, default=65.0)
    
    # Case Management Status
    status = Column(String(30), default="OPEN", index=True)  # OPEN, UNDER_REVIEW, ESCALATED, RESOLVED, FALSE_POSITIVE
    assigned_to = Column(String(36), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    suspicious_activity_report_filed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=_utcnow, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer = relationship("Customer", back_populates="aml_alerts")


class AMLCase(Base):
    """Comprehensive AML Investigation Case for Compliance Officers."""

    __tablename__ = "aml_cases"

    id = Column(String(36), primary_key=True, default=_uuid)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    primary_alert_id = Column(String(36), nullable=True)
    
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(30), default="UNDER_REVIEW", index=True)  # OPEN, UNDER_REVIEW, ESCALATED, RESOLVED, SAR_FILED
    findings_summary = Column(Text, default="")
    created_by = Column(String(36), nullable=False)
    
    created_at = Column(DateTime, default=_utcnow)
    resolved_at = Column(DateTime, nullable=True)


class SanctionsWatchlist(Base):
    """Synthetic Sanctions & Watchlist Entities for Fuzzy Screening."""

    __tablename__ = "sanctions_watchlists"

    id = Column(String(36), primary_key=True, default=_uuid)
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(20), default="INDIVIDUAL")  # INDIVIDUAL, ENTITY, VESSEL, BANK
    country_code = Column(String(2), default="IR")
    list_source = Column(String(100), default="OFAC_SYNTHETIC")  # OFAC_SYNTHETIC, UN_SYNTHETIC, EU_SYNTHETIC, RBI_DEFAULTER_SYNTHETIC
    aliases = Column(Text, default="")
    date_of_birth = Column(String(20), nullable=True)
    passport_number = Column(String(50), nullable=True)
    remarks = Column(Text, default="")
    is_active = Column(Boolean, default=True)


class SanctionsMatch(Base):
    """Screening hit against sanctions database."""

    __tablename__ = "sanctions_matches"

    id = Column(String(36), primary_key=True, default=_uuid)
    customer_id = Column(String(36), nullable=True, index=True)
    transaction_id = Column(String(36), nullable=True, index=True)
    watchlist_id = Column(String(36), ForeignKey("sanctions_watchlists.id"), nullable=False)
    
    match_score = Column(Float, nullable=False)  # 0-100 fuzzy match score
    match_type = Column(String(20), default="FUZZY")  # EXACT, FUZZY
    status = Column(String(30), default="POTENTIAL_MATCH", index=True)  # POTENTIAL_MATCH, CONFIRMED_MATCH, FALSE_POSITIVE
    reviewer_id = Column(String(36), nullable=True)
    review_notes = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)

    watchlist_item = relationship("SanctionsWatchlist")
