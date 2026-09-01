"""Pydantic schemas for Countries, Currencies, Customers, Accounts, Transactions, Payments, Loans, Cards, KYC, AML, and Jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ─── Countries & Currencies ──────────────────────────────────
class CurrencyResponse(BaseModel):
    id: str
    code: str
    name: str
    symbol: str
    decimals: int
    exchange_rate_to_usd: float
    is_base: bool
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class CurrencyConvertRequest(BaseModel):
    amount: float = Field(..., gt=0)
    from_currency: str
    to_currency: str


class CurrencyConvertResponse(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    converted_amount: float
    fx_rate: float
    formatted: str


class CountryResponse(BaseModel):
    id: str
    code: str
    code_alpha3: str
    name: str
    default_currency: str
    locale: str
    timezone: str
    regulatory_body: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class PaymentRailConfigResponse(BaseModel):
    id: str
    rail_code: str
    rail_name: str
    country_code: str
    currency: str
    min_amount: float
    max_amount: float
    daily_limit: float
    per_txn_fee_flat: float
    per_txn_fee_percent: float
    is_instant: bool
    is_cross_border: bool
    sandbox_mode: bool
    model_config = ConfigDict(from_attributes=True)


# ─── Customers ───────────────────────────────────────────────
class CustomerCreateRequest(BaseModel):
    bank_id: str
    customer_type: str = "INDIVIDUAL"
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str = "1985-06-15"
    country_code: str = "IN"
    address_line1: str = ""
    city: str = "Mumbai"
    state: str = "Maharashtra"
    postal_code: str = "400001"
    employment_status: str = "SALARIED"
    annual_income: float = 750000.0
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    bank_id: str
    customer_number: str
    customer_type: str
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    country_code: str
    city: str
    state: str
    employment_status: str
    annual_income: float
    credit_score: int
    credit_risk_tier: str
    customer_segment: str
    kyc_status: str
    aml_status: str
    account_status: str
    pan_number: Optional[str] = None
    aadhaar_masked: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ─── Accounts & Beneficiaries ────────────────────────────────
class AccountCreateRequest(BaseModel):
    customer_id: str
    bank_id: str
    account_type: str = "SAVINGS"
    currency: str = "INR"
    initial_deposit: float = 10000.0
    branch_id: Optional[str] = None


class AccountResponse(BaseModel):
    id: str
    customer_id: str
    bank_id: str
    account_number: str
    account_type: str
    currency: str
    balance: float
    available_balance: float
    hold_amount: float
    interest_rate: float
    upi_vpa: Optional[str] = None
    status: str
    is_primary: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class BeneficiaryCreateRequest(BaseModel):
    customer_id: str
    nickname: str
    beneficiary_name: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_vpa: Optional[str] = None
    iban: Optional[str] = None
    swift_bic: Optional[str] = None
    bank_name: str = ""
    country_code: str = "IN"
    currency: str = "INR"
    payment_rail: str = "UPI"
    transfer_limit: float = 50000.0


# ─── Payments & Transfers ────────────────────────────────────
class TransferRequest(BaseModel):
    source_account_id: str
    destination_account_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    payment_rail: str = "UPI"  # UPI, IMPS, NEFT, RTGS, SWIFT, SEPA, ACH, FEDWIRE
    idempotency_key: Optional[str] = None
    recipient_identifier: Optional[str] = None  # VPA, Account number, IBAN
    recipient_name: Optional[str] = None
    description: str = "Funds Transfer"


class UPIIntentCreateRequest(BaseModel):
    payee_vpa: str
    payee_name: str
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    note: str = "Payment via FedBank UPI"


# ─── Loans ──────────────────────────────────────────────────
class EMICalculateRequest(BaseModel):
    principal_amount: float = Field(..., gt=0)
    interest_rate_annual: float = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0)


class EMICalculateResponse(BaseModel):
    principal_amount: float
    interest_rate_annual: float
    tenure_months: int
    monthly_emi: float
    total_interest: float
    total_payable: float
    amortization_preview: List[Dict[str, Any]]


class LoanApplyRequest(BaseModel):
    customer_id: str
    bank_id: str
    account_id: Optional[str] = None
    loan_type: str = "PERSONAL"  # PERSONAL, HOME, VEHICLE, EDUCATION, BUSINESS
    principal_amount: float = Field(..., gt=0)
    interest_rate_annual: float = 10.5
    tenure_months: int = 36


# ─── Cards ──────────────────────────────────────────────────
class CardIssueRequest(BaseModel):
    customer_id: str
    account_id: str
    bank_id: str
    card_type: str = "DEBIT"  # DEBIT, CREDIT, VIRTUAL
    card_network: str = "RUPAY"  # RUPAY, VISA, MASTERCARD
    cardholder_name: str
    credit_limit: float = 0.0


# ─── KYC & AML ──────────────────────────────────────────────
class PANVerifyRequest(BaseModel):
    pan_number: str
    full_name: str


class AadhaarVerifyRequest(BaseModel):
    aadhaar_number: str
    full_name: str


class AMLAlertResolveRequest(BaseModel):
    resolution: str  # RESOLVED, FALSE_POSITIVE, ESCALATED
    notes: str
