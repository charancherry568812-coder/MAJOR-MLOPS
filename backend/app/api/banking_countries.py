"""Countries, Currencies, Regulations, and Payment Rails API Router."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.banking_country import Country, Currency, BankingRegulation, PaymentRailConfig
from app.schemas.banking import (
    CountryResponse,
    CurrencyConvertRequest,
    CurrencyConvertResponse,
    CurrencyResponse,
    PaymentRailConfigResponse,
)
from app.services.country_service import (
    COUNTRY_DEFINITIONS,
    CURRENCY_METADATA,
    INITIAL_FX_RATES,
    convert_currency,
    format_currency_amount,
)

countries_router = APIRouter(prefix="/countries", tags=["Banking Countries"])
currencies_router = APIRouter(prefix="/currencies", tags=["Currencies & FX"])
rails_router = APIRouter(prefix="/payment-rails", tags=["Payment Rails"])


def _ensure_countries_seeded(db: Session):
    if db.query(Country).count() == 0:
        for c in COUNTRY_DEFINITIONS:
            country = Country(
                code=c["code"],
                code_alpha3=c["code_alpha3"],
                name=c["name"],
                default_currency=c["default_currency"],
                locale=c["locale"],
                timezone=c["timezone"],
                regulatory_body=c["regulatory_body"],
            )
            db.add(country)
        db.commit()


def _ensure_currencies_seeded(db: Session):
    if db.query(Currency).count() == 0:
        for cur in CURRENCY_METADATA:
            c = Currency(
                code=cur["code"],
                name=cur["name"],
                symbol=cur["symbol"],
                decimals=cur["decimals"],
                exchange_rate_to_usd=INITIAL_FX_RATES.get(cur["code"], 1.0),
                is_base=cur["is_base"],
            )
            db.add(c)
        db.commit()


@countries_router.get("", response_model=Dict[str, Any])
def list_countries(db: Session = Depends(get_db)):
    _ensure_countries_seeded(db)
    items = db.query(Country).filter(Country.is_active == True).all()
    return {"success": True, "data": [CountryResponse.model_validate(c).model_dump() for c in items]}


@currencies_router.get("")
def list_currencies(db: Session = Depends(get_db)):
    _ensure_currencies_seeded(db)
    items = db.query(Currency).filter(Currency.is_active == True).all()
    return {"success": True, "data": [CurrencyResponse.model_validate(c).model_dump() for c in items]}


@currencies_router.post("/convert", response_model=Dict[str, Any])
def convert_currency_endpoint(req: CurrencyConvertRequest, db: Session = Depends(get_db)):
    _ensure_currencies_seeded(db)
    converted_amt, fx_rate = convert_currency(req.amount, req.from_currency.upper(), req.to_currency.upper(), db=db)
    formatted_str = format_currency_amount(converted_amt, req.to_currency.upper())

    return {
        "success": True,
        "data": CurrencyConvertResponse(
            amount=req.amount,
            from_currency=req.from_currency.upper(),
            to_currency=req.to_currency.upper(),
            converted_amount=converted_amt,
            fx_rate=fx_rate,
            formatted=formatted_str,
        ).model_dump(),
    }


@rails_router.get("")
def list_payment_rails(country: Optional[str] = None, db: Session = Depends(get_db)):
    _ensure_countries_seeded(db)
    query = db.query(PaymentRailConfig).filter(PaymentRailConfig.is_active == True)
    if country:
        query = query.filter(PaymentRailConfig.country_code == country.upper())
    rails = query.all()

    # If not seeded in DB, generate default standard rails
    if not rails:
        default_rails = [
            {"rail_code": "UPI", "rail_name": "Unified Payments Interface (UPI)", "country_code": "IN", "currency": "INR", "min_amount": 1.0, "max_amount": 100000.0, "daily_limit": 100000.0, "per_txn_fee_flat": 0.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "IMPS", "rail_name": "Immediate Payment Service (IMPS)", "country_code": "IN", "currency": "INR", "min_amount": 1.0, "max_amount": 500000.0, "daily_limit": 500000.0, "per_txn_fee_flat": 5.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "NEFT", "rail_name": "National Electronic Funds Transfer (NEFT)", "country_code": "IN", "currency": "INR", "min_amount": 1.0, "max_amount": 10000000.0, "daily_limit": 10000000.0, "per_txn_fee_flat": 2.5, "per_txn_fee_percent": 0.0, "is_instant": False, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "RTGS", "rail_name": "Real Time Gross Settlement (RTGS)", "country_code": "IN", "currency": "INR", "min_amount": 200000.0, "max_amount": 50000000.0, "daily_limit": 50000000.0, "per_txn_fee_flat": 25.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "SWIFT", "rail_name": "SWIFT Cross-Border Wire (ISO 20022)", "country_code": "US", "currency": "USD", "min_amount": 10.0, "max_amount": 10000000.0, "daily_limit": 10000000.0, "per_txn_fee_flat": 20.0, "per_txn_fee_percent": 0.001, "is_instant": False, "is_cross_border": True, "sandbox_mode": True},
            {"rail_code": "SEPA", "rail_name": "SEPA Instant Credit Transfer", "country_code": "EU", "currency": "EUR", "min_amount": 1.0, "max_amount": 100000.0, "daily_limit": 100000.0, "per_txn_fee_flat": 0.5, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "ACH", "rail_name": "Automated Clearing House (ACH)", "country_code": "US", "currency": "USD", "min_amount": 1.0, "max_amount": 250000.0, "daily_limit": 250000.0, "per_txn_fee_flat": 0.25, "per_txn_fee_percent": 0.0, "is_instant": False, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "FEDWIRE", "rail_name": "Fedwire Funds Service", "country_code": "US", "currency": "USD", "min_amount": 1.0, "max_amount": 50000000.0, "daily_limit": 50000000.0, "per_txn_fee_flat": 15.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
            {"rail_code": "FASTER_PAYMENTS", "rail_name": "UK Faster Payments (FPS)", "country_code": "GB", "currency": "GBP", "min_amount": 1.0, "max_amount": 1000000.0, "daily_limit": 1000000.0, "per_txn_fee_flat": 0.2, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
        ]
        return {"success": True, "data": default_rails}

    return {"success": True, "data": [PaymentRailConfigResponse.model_validate(r).model_dump() for r in rails]}
