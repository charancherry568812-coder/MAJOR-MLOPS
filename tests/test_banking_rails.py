"""Tests for Countries, Currencies, Multi-Rail Payments, and Account Transactions."""

from __future__ import annotations

import uuid
import pytest


def test_list_countries_and_currencies(client, auth_headers):
    # Test Countries
    c_res = client.get("/api/v1/countries", headers=auth_headers)
    assert c_res.status_code == 200
    countries = c_res.json()["data"]
    assert len(countries) >= 4
    country_codes = [c["code"] for c in countries]
    assert "IN" in country_codes
    assert "US" in country_codes

    # Test Currencies
    cur_res = client.get("/api/v1/currencies", headers=auth_headers)
    assert cur_res.status_code == 200
    currencies = cur_res.json()["data"]
    codes = [c["code"] for c in currencies]
    assert "INR" in codes
    assert "USD" in codes
    assert "EUR" in codes


def test_currency_conversion(client, auth_headers):
    payload = {"amount": 1000.0, "from_currency": "USD", "to_currency": "INR"}
    res = client.post("/api/v1/currencies/convert", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["amount"] == 1000.0
    assert data["from_currency"] == "USD"
    assert data["to_currency"] == "INR"
    assert data["converted_amount"] > 80000.0  # ~86,850 INR
    assert "₹" in data["formatted"]


def test_list_payment_rails(client, auth_headers):
    res = client.get("/api/v1/payment-rails", headers=auth_headers)
    assert res.status_code == 200
    rails = res.json()["data"]
    rail_codes = [r["rail_code"] for r in rails]
    assert "UPI" in rail_codes
    assert "IMPS" in rail_codes
    assert "NEFT" in rail_codes
    assert "RTGS" in rail_codes
    assert "SWIFT" in rail_codes


def test_customer_account_and_transfer_flow(client, auth_headers):
    # 1. List Banks to get bank_id
    banks_res = client.get("/api/v1/banks", headers=auth_headers)
    bank_id = banks_res.json()["data"]["items"][0]["id"]

    # 2. Create New Customer
    cust_payload = {
        "bank_id": bank_id,
        "first_name": "Suresh",
        "last_name": "Raina",
        "email": f"suresh_{uuid.uuid4().hex[:4]}@example.com",
        "phone": f"98{uuid.uuid4().hex[:8]}",
        "country_code": "IN",
        "pan_number": "ABCDE1234F",
        "annual_income": 950000.0,
    }
    c_res = client.post("/api/v1/customers", json=cust_payload, headers=auth_headers)
    assert c_res.status_code == 200
    cust_id = c_res.json()["data"]["id"]

    # 3. Open Account for Customer with initial deposit
    acc_payload = {
        "customer_id": cust_id,
        "bank_id": bank_id,
        "account_type": "SAVINGS",
        "currency": "INR",
        "initial_deposit": 50000.0,
    }
    acc_res = client.post("/api/v1/accounts", json=acc_payload, headers=auth_headers)
    assert acc_res.status_code == 200
    acc_id = acc_res.json()["data"]["id"]
    assert acc_res.json()["data"]["balance"] == 50000.0

    # 4. Execute UPI Transfer
    idem_key = f"IDEM-{uuid.uuid4().hex}"
    tx_payload = {
        "source_account_id": acc_id,
        "amount": 5000.0,
        "payment_rail": "UPI",
        "idempotency_key": idem_key,
        "recipient_identifier": "merchant@fedbank",
        "recipient_name": "Star Supermarket",
        "description": "Weekly grocery purchase",
    }
    tx_res = client.post("/api/v1/payments/transfer", json=tx_payload, headers=auth_headers)
    assert tx_res.status_code == 200
    tx_data = tx_res.json()["data"]
    assert tx_data["status"] == "COMPLETED"
    assert tx_data["payment_rail"] == "UPI"
    assert tx_data["is_sandbox"] is True
    assert "UPI-" in tx_data["provider_reference"]

    # 5. Check Idempotency Replay
    replay_res = client.post("/api/v1/payments/transfer", json=tx_payload, headers=auth_headers)
    assert replay_res.status_code == 200
    assert replay_res.json()["data"]["transaction_reference"] == tx_data["transaction_reference"]

    # 6. Verify Updated Account Balance
    acc_check = client.get(f"/api/v1/accounts/{acc_id}", headers=auth_headers)
    assert acc_check.status_code == 200
    assert acc_check.json()["data"]["balance"] == 45000.0


def test_upi_qr_intent_creation(client, auth_headers):
    intent_payload = {
        "payee_vpa": "store@fedbank",
        "payee_name": "FedBank Express Mart",
        "amount": 250.0,
        "currency": "INR",
        "note": "Coffee & Snack",
    }
    res = client.post("/api/v1/payments/upi/create-intent", json=intent_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "upi://pay" in data["qr_payload"]
    assert data["amount"] == 250.0
    assert data["status"] == "ACTIVE"
