"""Tests for Loans, EMI Calculations, Amortization, and Cards Management."""

from __future__ import annotations

import pytest


def test_emi_calculation_formula(client, auth_headers):
    # ₹10,00,000 at 10.5% for 36 months
    payload = {
        "principal_amount": 1000000.0,
        "interest_rate_annual": 10.5,
        "tenure_months": 36,
    }
    res = client.post("/api/v1/loans/calculate-emi", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    # Standard banking EMI for 10L @ 10.5% for 36m is approx ₹32,502
    assert 32000.0 <= data["monthly_emi"] <= 33000.0
    assert data["total_payable"] > 1000000.0
    assert len(data["amortization_preview"]) > 0


def test_loan_origination_and_schedule(client, auth_headers):
    # Get first customer and bank
    cust_res = client.get("/api/v1/customers", headers=auth_headers)
    customer = cust_res.json()["data"]["items"][0]

    loan_payload = {
        "customer_id": customer["id"],
        "bank_id": customer["bank_id"],
        "loan_type": "HOME",
        "principal_amount": 2500000.0,
        "interest_rate_annual": 8.5,
        "tenure_months": 120,
    }
    res = client.post("/api/v1/loans/apply", json=loan_payload, headers=auth_headers)
    assert res.status_code == 200
    loan_id = res.json()["data"]["id"]

    # Verify Detail and Amortization Schedule
    detail_res = client.get(f"/api/v1/loans/{loan_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert detail["loan_type"] == "HOME"
    assert len(detail["amortization_schedule"]) == 120
    assert detail["amortization_schedule"][0]["installment_number"] == 1


def test_card_issuance_and_freeze(client, auth_headers):
    # Get first customer account
    acc_res = client.get("/api/v1/accounts", headers=auth_headers)
    account = acc_res.json()["data"]["items"][0]

    card_payload = {
        "customer_id": account["customer_id"],
        "account_id": account["id"],
        "bank_id": account["bank_id"],
        "card_type": "DEBIT",
        "card_network": "RUPAY",
        "cardholder_name": "KAVYA PATEL",
    }
    res = client.post("/api/v1/cards/issue", json=card_payload, headers=auth_headers)
    assert res.status_code == 200
    card_data = res.json()["data"]
    assert "6071-XXXX" in card_data["card_number_masked"]
    assert card_data["status"] == "ACTIVE"
    card_id = card_data["id"]

    # Toggle Freeze
    freeze_res = client.post(f"/api/v1/cards/{card_id}/toggle-freeze", headers=auth_headers)
    assert freeze_res.status_code == 200
    assert freeze_res.json()["data"]["status"] == "FROZEN"

    # Unfreeze
    unfreeze_res = client.post(f"/api/v1/cards/{card_id}/toggle-freeze", headers=auth_headers)
    assert unfreeze_res.status_code == 200
    assert unfreeze_res.json()["data"]["status"] == "ACTIVE"
