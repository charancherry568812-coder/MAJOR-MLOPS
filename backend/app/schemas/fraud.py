"""Schemas for Fraud Detection & Transaction Scoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TransactionScoreRequest(BaseModel):
    customer_id: str = Field(default="CUST-10492")
    bank_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(default="TRANSFER")  # TRANSFER, PAYMENT, WITHDRAWAL, DEPOSIT
    merchant_category: str = Field(default="General Retail")
    velocity_score: float = Field(default=35.0, ge=0, le=100)
    amount_deviation: float = Field(default=1.2, ge=0)
    num_devices: int = Field(default=1, ge=1)
    account_age_months: int = Field(default=48, ge=0)


class TransactionScoreResponse(BaseModel):
    transaction_reference: str
    customer_id: str
    amount: float
    fraud_probability: float
    risk_level: str  # LOW, MEDIUM, HIGH
    is_flagged: bool
    recommendation: str
    flag_reason: Optional[str] = None
    alert_code: Optional[str] = None
    alert_id: Optional[str] = None
    feature_contributions: Dict[str, float] = {}
    timestamp: str


class FraudAlertResponse(BaseModel):
    id: str
    alert_code: str
    transaction_id: Optional[str] = None
    bank_id: Optional[str] = None
    bank_name: Optional[str] = None
    customer_id: str
    risk_score: float
    fraud_probability: float
    severity: str
    status: str
    flag_reason: str
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: str


class ResolveAlertRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3)
    action: str = Field(default="RESOLVED")  # RESOLVED or REJECTED


class FraudSummaryResponse(BaseModel):
    total_transactions: int
    suspicious_transactions: int
    fraud_rate: float
    open_alerts: int
    resolved_alerts: int
    critical_alerts: int
