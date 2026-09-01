"""Credit Risk Prediction & Fraud Detection Test Suite."""

def test_single_prediction_api(client, auth_headers):
    payload = {
        "features": {
            "age": 42,
            "income": 78000,
            "employment_years": 6,
            "credit_score": 690,
            "loan_amount": 20000,
            "loan_term": 36,
            "existing_loans": 1,
            "debt_to_income": 0.25,
            "account_balance": 35000,
            "late_payments": 0,
            "transaction_count": 28,
        }
    }
    res = client.post("/api/v1/predictions/single", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "risk_category" in data
    assert data["risk_category"] in ("LOW_RISK", "MEDIUM_RISK", "HIGH_RISK")
    assert "probability" in data
    assert "risk_score" in data


def test_fraud_scoring_and_alerts(client, auth_headers):
    # Test scoring a high risk transaction
    payload = {
        "customer_id": "CUST-9999",
        "amount": 95000,
        "transaction_type": "TRANSFER",
        "merchant_category": "Cryptocurrency Exchange",
        "velocity_score": 95,
        "amount_deviation": 8.5,
        "num_devices": 5,
        "account_age_months": 2,
    }
    res = client.post("/api/v1/fraud/score-transaction", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in ("HIGH", "MEDIUM", "LOW")
    assert data["is_flagged"] is True
    assert "alert_id" in data

    # Test resolving the alert
    alert_id = data["alert_id"]
    if alert_id:
        resolve_res = client.put(
            f"/api/v1/fraud/alerts/{alert_id}/resolve",
            json={"resolution_notes": "Verified fraud event via customer telephone authorization", "action": "RESOLVED"},
            headers=auth_headers,
        )
        assert resolve_res.status_code == 200
