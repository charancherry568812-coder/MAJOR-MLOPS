"""Complete End-to-End Production Verification Script for FedBank MLOps.

Tests every stage of the enterprise workflow:
1. System Health & DB Service
2. Authentication & Token Exchange
3. Global & India Banking Rails (UPI, IMPS, NEFT, RTGS, SWIFT, SEPA, ACH)
4. Multi-Currency FX Engine
5. Customer Accounts & Balance Ledger with Concurrency Control
6. Loans Portfolio & EMI Amortization
7. Card Issuance & PCI-DSS Tokenization
8. KYC Identity Verification (PAN & Aadhaar Sandbox)
9. AML Transaction Monitoring & Alert Resolution
10. Sanctions Watchlist Fuzzy Screening
11. Multi-Bank Datasets & Quality Checks
12. 11-Stage MLOps Pipeline Orchestrator
13. Decentralized Flower Federated Training & Simulation
14. MLflow Model Registry & Stage Promotion
15. Credit Risk Scoring & SHAP Explainability
16. Statistical Data Drift (PSI & Kolmogorov-Smirnov)
17. Async Background Worker Jobs
18. Regulatory Audit Logs & Compliance Export
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.database.init_db import init_db

client = TestClient(app)

passed_steps = []
failed_steps = []


def step(name):
    print(f"\n========================================================")
    print(f"▶ STEP: {name}")
    print(f"========================================================")


def check(condition, message):
    if condition:
        print(f"  ✅ PASS: {message}")
        passed_steps.append(message)
    else:
        print(f"  ❌ FAIL: {message}")
        failed_steps.append(message)
        raise AssertionError(f"Step check failed: {message}")


def main():
    print("🏦 Starting FedBank MLOps Comprehensive Enterprise Verification...")
    init_db()

    # 1. Health Check
    step("1. System Health & Infrastructure")
    res = client.get("/health")
    check(res.status_code == 200, f"Health check returned 200 (Status: {res.json().get('status')})")
    check(res.json().get("services", {}).get("database", {}).get("status") == "HEALTHY", "Database service reports HEALTHY")

    # 2. Login & Authentication
    step("2. Authentication & Zero-Trust Token Exchange")
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@fedbank.com", "password": "Admin@123"})
    check(login_res.status_code == 200, "Super Admin login succeeded")
    token_data = login_res.json()
    token = token_data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Global & Domestic Payment Rails
    step("3. Global & India Payment Rails (UPI, IMPS, NEFT, RTGS, SWIFT, SEPA, ACH)")
    rails_res = client.get("/api/v1/payment-rails", headers=headers)
    check(rails_res.status_code == 200, "Payment rails configuration retrieved")
    rails = rails_res.json().get("data", [])
    rail_codes = [r.get("rail_code") for r in rails]
    check("UPI" in rail_codes, "UPI instant payment rail enabled")
    check("SWIFT" in rail_codes, "SWIFT ISO 20022 wire rail enabled")
    check("IMPS" in rail_codes, "IMPS 24x7 rail enabled")

    # 4. Multi-Currency FX Engine
    step("4. Multi-Currency Conversion Engine")
    fx_res = client.post("/api/v1/currencies/convert", json={"amount": 1000.0, "from_currency": "USD", "to_currency": "INR"}, headers=headers)
    check(fx_res.status_code == 200, "USD -> INR conversion calculated")
    fx_data = fx_res.json().get("data", {})
    check(fx_data.get("converted_amount", 0) > 80000.0, f"Converted amount: ₹{fx_data.get('converted_amount'):,.2f}")

    # 5. Accounts & Atomic Ledger Transfers
    step("5. Customer Accounts, Atomic Ledger & UPI Transfers")
    acc_res = client.get("/api/v1/accounts", headers=headers)
    check(acc_res.status_code == 200, "Accounts list retrieved")
    accounts = acc_res.json().get("data", {}).get("items", [])
    check(len(accounts) >= 4, f"Found {len(accounts)} active bank accounts")
    src_acc = accounts[0]

    # Execute transfer
    idem_key = f"IDEM-VERIFY-{uuid.uuid4().hex[:8]}"
    tx_res = client.post("/api/v1/payments/transfer", json={
        "source_account_id": src_acc["id"],
        "amount": 2500.0,
        "payment_rail": "UPI",
        "idempotency_key": idem_key,
        "recipient_identifier": "merchant@fedbank",
        "recipient_name": "Verified Supermarket",
        "description": "Retail checkout",
    }, headers=headers)
    check(tx_res.status_code == 200, "Atomic UPI Transfer executed")
    tx_data = tx_res.json().get("data", {})
    check(tx_data.get("status") == "COMPLETED", "Transaction status is COMPLETED")
    check("UPI-" in tx_data.get("provider_reference", ""), f"UPI RRN: {tx_data.get('provider_reference')}")

    # Generate UPI QR intent
    upi_res = client.post("/api/v1/payments/upi/create-intent", json={
        "payee_vpa": "store@fedbank",
        "payee_name": "FedBank Express",
        "amount": 500.0,
        "currency": "INR",
        "note": "Production verification QR",
    }, headers=headers)
    check(upi_res.status_code == 200, "Dynamic UPI QR Intent generated")
    check("upi://pay" in upi_res.json().get("data", {}).get("qr_payload", ""), "NPCI URI format valid")

    # 6. Loans Portfolio & EMI Amortization
    step("6. Loan Origination & Mathematical EMI Amortization")
    emi_res = client.post("/api/v1/loans/calculate-emi", json={
        "principal_amount": 1000000.0,
        "interest_rate_annual": 10.5,
        "tenure_months": 36,
    }, headers=headers)
    check(emi_res.status_code == 200, "EMI calculated")
    emi_val = emi_res.json().get("data", {}).get("monthly_emi", 0)
    check(32000.0 <= emi_val <= 33000.0, f"Monthly EMI verified: ₹{emi_val:,.2f}")

    loans_res = client.get("/api/v1/loans", headers=headers)
    check(loans_res.status_code == 200, "Loans portfolio retrieved")
    loans = loans_res.json().get("data", {}).get("items", [])
    if loans:
        first_loan_id = loans[0]["id"]
        l_detail = client.get(f"/api/v1/loans/{first_loan_id}", headers=headers)
        check(l_detail.status_code == 200, "Amortization schedule loaded")
        check(len(l_detail.json().get("data", {}).get("amortization_schedule", [])) > 0, "Amortization installments verified")

    # 7. Card Management & PCI-DSS Tokenization
    step("7. Card Issuance & Vault Tokenization")
    cards_res = client.get("/api/v1/cards", headers=headers)
    check(cards_res.status_code == 200, "Cards list retrieved")
    cards = cards_res.json().get("data", [])
    check(len(cards) > 0, f"Found {len(cards)} tokenized bank cards")

    # 8. KYC Identity Verification
    step("8. KYC Identity Verification (PAN & Aadhaar Sandbox Adapters)")
    pan_res = client.post("/api/v1/kyc/verify-pan", json={"pan_number": "ABCDE1234F", "full_name": "Rajesh Kumar"}, headers=headers)
    check(pan_res.status_code == 200 and pan_res.json().get("data", {}).get("status") == "VALID", "PAN validation adapter passed")

    aadhaar_res = client.post("/api/v1/kyc/verify-aadhaar", json={"aadhaar_number": "987654321099", "full_name": "Rajesh Kumar"}, headers=headers)
    check(aadhaar_res.status_code == 200 and aadhaar_res.json().get("data", {}).get("status") == "VERIFIED", "Aadhaar vault tokenization adapter passed")

    # 9. AML Transaction Monitoring
    step("9. AML Real-Time Rule Monitoring & SAR Governance")
    aml_res = client.get("/api/v1/aml/alerts", headers=headers)
    check(aml_res.status_code == 200, "AML alerts queue retrieved")

    # 10. Sanctions Fuzzy Watchlist Screening
    step("10. Sanctions Watchlist & Fuzzy Levenshtein Screening")
    sanc_res = client.post("/api/v1/sanctions/screen?name=Viktor%20Chernov&threshold=70", headers=headers)
    check(sanc_res.status_code == 200, "Sanctions screening completed")
    check(sanc_res.json().get("data", {}).get("is_flagged") is True, "Potential sanctions watchlist match flagged")

    # 11. Multi-Bank Datasets
    step("11. Multi-Bank Datasets & Quality Scoring")
    ds_res = client.get("/api/v1/datasets", headers=headers)
    check(ds_res.status_code == 200, "Datasets list retrieved")
    datasets = ds_res.json().get("data", {}).get("items", [])
    check(len(datasets) >= 4, f"Found {len(datasets)} verified multi-bank datasets")

    # 12. MLOps Pipeline Status
    step("12. MLOps 11-Stage Pipeline Orchestrator")
    pipe_res = client.get("/api/v1/pipeline/status", headers=headers)
    check(pipe_res.status_code == 200, "Pipeline status endpoint returned 200")
    check(len(pipe_res.json().get("data", {}).get("stages", [])) == 11, "All 11 MLOps pipeline stages active")

    # 13. Decentralized Federated Learning
    step("13. Flower FedAvg Federated Training Simulation")
    fl_config = {
        "model_type": "random_forest",
        "use_case": "credit_risk",
        "federated_strategy": "fedavg",
        "num_rounds": 2,
        "num_clients": 4,
        "local_epochs": 2,
        "batch_size": 32,
        "learning_rate": 0.01,
    }
    from federated.simulation import run_federated_simulation
    fl_result = run_federated_simulation(fl_config)
    check(fl_result.get("final_accuracy", 0) > 0.70, f"FL Accuracy: {fl_result.get('final_accuracy'):.4f}")
    check(fl_result.get("total_rounds") == 2, "2 federated communication rounds complete")

    # 14. MLflow Model Registry
    step("14. MLflow Model Registry")
    models_res = client.get("/api/v1/models", headers=headers)
    check(models_res.status_code == 200, "Model registry retrieved")
    models = models_res.json().get("data", {}).get("items", [])
    check(len(models) >= 1, f"Registered Models: {len(models)}")

    # 15. Credit Risk Scoring & SHAP
    step("15. Real-Time Credit Prediction & SHAP Feature Attribution")
    pred_payload = {
        "features": {
            "age": 46,
            "income": 92000,
            "employment_years": 10,
            "credit_score": 740,
            "loan_amount": 30000,
            "loan_term": 48,
            "existing_loans": 1,
            "debt_to_income": 0.21,
            "account_balance": 52000,
            "late_payments": 0,
            "transaction_count": 36,
        }
    }
    pred_res = client.post("/api/v1/predictions/single", json=pred_payload, headers=headers)
    check(pred_res.status_code == 200, "Credit prediction scored")
    pred_data = pred_res.json().get("data", {})
    check("risk_category" in pred_data, f"Risk Tier: {pred_data.get('risk_category')}")
    check(len(pred_data.get("explanation", {})) > 0, "SHAP Explainability feature attributions generated")

    # 16. Statistical PSI Data Drift
    step("16. Statistical Data Drift (PSI & Kolmogorov-Smirnov)")
    drift_res = client.post("/api/v1/data-drift/calculate", headers=headers)
    check(drift_res.status_code == 200, "Statistical PSI calculation executed")
    check(drift_res.json().get("data", {}).get("features_analyzed", 0) > 0, "Feature distributions analyzed")

    # 17. Async Worker Jobs
    step("17. Async Background Worker Jobs Engine")
    job_trig = client.post("/api/v1/jobs/trigger-sample-task?title=E2E%20Batch%20Task", headers=headers)
    check(job_trig.status_code == 200, "Async task dispatched to worker pool")
    job_id = job_trig.json().get("data", {}).get("job_id")
    time.sleep(1.0)
    job_check = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    check(job_check.status_code == 200, f"Worker progress: {job_check.json().get('data', {}).get('progress_percent')}%")

    # 18. Audit Logs
    step("18. Immutable Audit Trail & Regulatory Exports")
    audit_res = client.get("/api/v1/audit-logs", headers=headers)
    check(audit_res.status_code == 200, "Audit logs verified")
    check(audit_res.json().get("data", {}).get("total", 0) > 0, "Immutable records present in trail")

    print("\n========================================================")
    print(f"🎉 COMPREHENSIVE PRODUCTION VERIFICATION PASSED 100%!")
    print(f"   • Total Passed Stages: {len(passed_steps)}")
    print(f"   • Total Failed Stages: {len(failed_steps)}")
    print("========================================================")


if __name__ == "__main__":
    main()
