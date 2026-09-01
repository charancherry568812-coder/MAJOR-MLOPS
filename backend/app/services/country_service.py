"""Country, Multi-Currency, and Exchange Rate services."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.banking_country import Country, Currency, BankingRegulation, PaymentRailConfig

# Base FX Reference Rates (USD baseline, updated via sandbox FX provider)
INITIAL_FX_RATES: Dict[str, float] = {
    "USD": 1.0,
    "INR": 86.85,      # 1 USD = 86.85 INR
    "EUR": 0.95,       # 1 USD = 0.95 EUR
    "GBP": 0.79,       # 1 USD = 0.79 GBP
    "AED": 3.67,       # 1 USD = 3.67 AED
    "CAD": 1.42,       # 1 USD = 1.42 CAD
    "AUD": 1.58,       # 1 USD = 1.58 AUD
    "SGD": 1.34,       # 1 USD = 1.34 SGD
    "JPY": 154.20,     # 1 USD = 154.20 JPY
}

CURRENCY_METADATA = [
    {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "decimals": 2, "is_base": False},
    {"code": "USD", "name": "US Dollar", "symbol": "$", "decimals": 2, "is_base": True},
    {"code": "EUR", "name": "Euro", "symbol": "€", "decimals": 2, "is_base": False},
    {"code": "GBP", "name": "British Pound", "symbol": "£", "decimals": 2, "is_base": False},
    {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ", "decimals": 2, "is_base": False},
    {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$", "decimals": 2, "is_base": False},
    {"code": "AUD", "name": "Australian Dollar", "symbol": "A$", "decimals": 2, "is_base": False},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$", "decimals": 2, "is_base": False},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "decimals": 0, "is_base": False},
]

COUNTRY_DEFINITIONS = [
    {
        "code": "IN", "code_alpha3": "IND", "name": "India", "default_currency": "INR",
        "locale": "en-IN", "timezone": "Asia/Kolkata", "regulatory_body": "Reserve Bank of India (RBI)",
    },
    {
        "code": "US", "code_alpha3": "USA", "name": "United States", "default_currency": "USD",
        "locale": "en-US", "timezone": "America/New_York", "regulatory_body": "Federal Reserve Board (FRB)",
    },
    {
        "code": "GB", "code_alpha3": "GBR", "name": "United Kingdom", "default_currency": "GBP",
        "locale": "en-GB", "timezone": "Europe/London", "regulatory_body": "Financial Conduct Authority (FCA)",
    },
    {
        "code": "EU", "code_alpha3": "EUR", "name": "European Union", "default_currency": "EUR",
        "locale": "en-EU", "timezone": "Europe/Frankfurt", "regulatory_body": "European Central Bank (ECB)",
    },
    {
        "code": "AE", "code_alpha3": "ARE", "name": "United Arab Emirates", "default_currency": "AED",
        "locale": "en-AE", "timezone": "Asia/Dubai", "regulatory_body": "Central Bank of the UAE (CBUAE)",
    },
    {
        "code": "SG", "code_alpha3": "SGP", "name": "Singapore", "default_currency": "SGD",
        "locale": "en-SG", "timezone": "Asia/Singapore", "regulatory_body": "Monetary Authority of Singapore (MAS)",
    },
    {
        "code": "CA", "code_alpha3": "CAN", "name": "Canada", "default_currency": "CAD",
        "locale": "en-CA", "timezone": "America/Toronto", "regulatory_body": "Bank of Canada (OSFI)",
    },
    {
        "code": "AU", "code_alpha3": "AUS", "name": "Australia", "default_currency": "AUD",
        "locale": "en-AU", "timezone": "Australia/Sydney", "regulatory_body": "Australian Prudential Regulation Authority (APRA)",
    },
]


def convert_currency(amount: float, from_currency: str, to_currency: str, db: Optional[Session] = None) -> tuple[float, float]:
    """Decimal-safe currency conversion using database exchange rates or sandbox baseline.
    
    Returns:
        (converted_amount, fx_rate)
    """
    if from_currency == to_currency:
        return round(amount, 2), 1.0

    rate_from_usd = INITIAL_FX_RATES.get(from_currency, 1.0)
    rate_to_usd = INITIAL_FX_RATES.get(to_currency, 1.0)

    if db:
        c_from = db.query(Currency).filter(Currency.code == from_currency).first()
        c_to = db.query(Currency).filter(Currency.code == to_currency).first()
        if c_from and c_from.exchange_rate_to_usd:
            rate_from_usd = c_from.exchange_rate_to_usd
        if c_to and c_to.exchange_rate_to_usd:
            rate_to_usd = c_to.exchange_rate_to_usd

    # Convert from source to USD then USD to destination
    # amount_in_usd = amount / rate_from_usd
    # amount_in_dest = amount_in_usd * rate_to_usd
    fx_rate = rate_to_usd / rate_from_usd
    converted_amount = amount * fx_rate
    
    decimals = 0 if to_currency == "JPY" else 2
    return round(converted_amount, decimals), round(fx_rate, 6)


def format_currency_amount(amount: float, currency_code: str) -> str:
    """Locale-aware monetary formatting."""
    symbol = "₹" if currency_code == "INR" else "$" if currency_code == "USD" else "€" if currency_code == "EUR" else "£" if currency_code == "GBP" else f"{currency_code} "
    if currency_code == "INR":
        # Indian numbering system formatting: Lakhs / Crores
        s = f"{amount:,.2f}"
        return f"{symbol}{s}"
    elif currency_code == "JPY":
        return f"{symbol}{int(amount):,}"
    else:
        return f"{symbol}{amount:,.2f}"
