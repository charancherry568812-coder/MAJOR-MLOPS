"""Tests for KYC Adapters, AML Transaction Screening, and Sanctions Watchlists."""

from __future__ import annotations

import uuid
import pytest


def test_kyc_pan_and_aadhaar_validation(client, auth_headers):
    # Valid PAN
    pan_res = client.post("/api/v1/kyc/verify-pan", json={"pan_number": "ABCDE1234F", "full_name": "Rohan Mehta"})
    assert pan_res.status_code == 200
    assert pan_res.json()["data"]["status"] == "VALID"
    assert pan_res.json()["data"]["is_sandbox"] is True

    # Invalid PAN format
    bad_pan = client.post("/api/v1/kyc/verify-pan", json={"pan_number": "INVALID123", "full_name": "Rohan Mehta"})
    assert bad_pan.status_code == 200
    assert bad_pan.json()["data"]["status"] == "INVALID_FORMAT"

    # Valid 12-digit Aadhaar
    aadhaar_res = client.post("/api/v1/kyc/verify-aadhaar", json={"aadhaar_number": "987654321099", "full_name": "Rohan Mehta"})
    assert aadhaar_res.status_code == 200
    assert aadhaar_res.json()["data"]["status"] == "VERIFIED"
    assert "XXXX-XXXX-1099" in aadhaar_res.json()["data"]["aadhaar_masked"]


def test_aml_structuring_and_velocity_alerts(client, auth_headers):
    # 1. Create a dedicated customer & account with high balance for clean AML test
    banks_res = client.get("/api/v1/banks", headers=auth_headers)
    bank_id = banks_res.json()["data"]["items"][0]["id"]

    cust_payload = {
        "bank_id": bank_id,
        "first_name": "AMLTest",
        "last_name": "Subject",
        "email": f"aml_{uuid.uuid4().hex[:4]}@example.com",
        "phone": f"97{uuid.uuid4().hex[:8]}",
        "country_code": "IN",
        "pan_number": "ABCDE1234F",
        "annual_income": 2000000.0,
    }
    c_res = client.post("/api/v1/customers", json=cust_payload, headers=auth_headers)
    assert c_res.status_code == 200
    cust_id = c_res.json()["data"]["id"]

    acc_payload = {
        "customer_id": cust_id,
        "bank_id": bank_id,
        "account_type": "CURRENT",
        "currency": "INR",
        "initial_deposit": 500000.0,
    }
    acc_res = client.post("/api/v1/accounts", json=acc_payload, headers=auth_headers)
    assert acc_res.status_code == 200
    account_id = acc_res.json()["data"]["id"]

    # 2. Execute transaction in structuring range (₹48,500)
    tx_payload = {
        "source_account_id": account_id,
        "amount": 48500.0,
        "payment_rail": "IMPS",
        "recipient_identifier": "payee@fedbank",
        "description": "Consulting fee payment",
    }
    tx_res = client.post("/api/v1/payments/transfer", json=tx_payload, headers=auth_headers)
    assert tx_res.status_code == 200

    # 3. Verify AML alert was generated
    aml_res = client.get("/api/v1/aml/alerts", headers=auth_headers)
    assert aml_res.status_code == 200
    alerts = aml_res.json()["data"]["items"]
    structuring_alerts = [a for a in alerts if a["alert_type"] == "STRUCTURING"]
    assert len(structuring_alerts) > 0

    first_alert = structuring_alerts[0]
    assert first_alert["status"] == "OPEN"

    # 4. Resolve AML alert
    resolve_payload = {"resolution": "RESOLVED", "notes": "Verified source of funds with tax declaration document"}
    res_alert = client.put(f"/api/v1/aml/alerts/{first_alert['id']}/resolve", json=resolve_payload, headers=auth_headers)
    assert res_alert.status_code == 200
    assert res_alert.json()["data"]["status"] == "RESOLVED"


def test_sanctions_fuzzy_screening(client, auth_headers):
    # Screen exact match
    res_exact = client.post("/api/v1/sanctions/screen?name=Viktor%20Chernov&threshold=70", headers=auth_headers)
    assert res_exact.status_code == 200
    data = res_exact.json()["data"]
    assert data["is_flagged"] is True
    assert len(data["matches"]) > 0

    # Screen clean name
    res_clean = client.post("/api/v1/sanctions/screen?name=Harish%20Narayan%20Venkatesh&threshold=85", headers=auth_headers)
    assert res_clean.status_code == 200
    assert res_clean.json()["data"]["is_flagged"] is False
