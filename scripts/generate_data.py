"""Synthetic banking data generator for FedBank MLOps.

Generates realistic, privacy-preserving synthetic banking data for 4 banks:
- BANK-001: Alpha National Bank (New York, NY) - 5,000 records
- BANK-002: Beta Federal Bank (Chicago, IL) - 4,500 records
- BANK-003: Gamma Trust Bank (Houston, TX) - 6,000 records
- BANK-004: Delta Savings Bank (San Francisco, CA) - 5,500 records
Total: 21,000 records (exceeds 10,000 requirement)

All data is 100% synthetically generated. No real customer PII is ever used.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

BANK_CONFIGS = [
    {
        "code": "BANK-001",
        "name": "Alpha National Bank",
        "branch": "Wall Street Financial Center",
        "n_customers": 5000,
        "seed": 42,
        "income_mean": 75000,
        "income_std": 25000,
        "credit_mean": 720,
        "credit_std": 60,
        "default_rate": 0.08,
        "fraud_rate": 0.02,
        "churn_rate": 0.15,
    },
    {
        "code": "BANK-002",
        "name": "Beta Federal Bank",
        "branch": "Midwest Regional HQ",
        "n_customers": 4500,
        "seed": 123,
        "income_mean": 55000,
        "income_std": 20000,
        "credit_mean": 650,
        "credit_std": 80,
        "default_rate": 0.15,
        "fraud_rate": 0.04,
        "churn_rate": 0.22,
    },
    {
        "code": "BANK-003",
        "name": "Gamma Trust Bank",
        "branch": "Southern Commercial Hub",
        "n_customers": 6000,
        "seed": 456,
        "income_mean": 48000,
        "income_std": 16000,
        "credit_mean": 625,
        "credit_std": 85,
        "default_rate": 0.12,
        "fraud_rate": 0.03,
        "churn_rate": 0.20,
    },
    {
        "code": "BANK-004",
        "name": "Delta Savings Bank",
        "branch": "Silicon Valley Branch",
        "n_customers": 5500,
        "seed": 789,
        "income_mean": 62000,
        "income_std": 22000,
        "credit_mean": 685,
        "credit_std": 70,
        "default_rate": 0.10,
        "fraud_rate": 0.035,
        "churn_rate": 0.18,
    },
]

LOAN_TYPES = ["MORTGAGE", "PERSONAL", "AUTO", "SMALL_BUSINESS", "EDUCATION"]
EMPLOYMENT_TYPES = ["SALARIED", "SELF_EMPLOYED", "BUSINESS_OWNER", "GOVERNMENT", "RETIRED"]


def generate_bank_dataset(config: dict) -> pd.DataFrame:
    """Generate synthetic customer credit risk and transaction dataset for a bank."""
    np.random.seed(config["seed"])
    n = config["n_customers"]

    age = np.clip(np.random.normal(42, 13, n), 18, 80).astype(int)
    employment_years = np.clip(np.random.normal(age * 0.35, 4, n), 0, 45).astype(int)
    income = np.clip(np.random.normal(config["income_mean"], config["income_std"], n), 18000, 450000).astype(int)
    credit_score = np.clip(np.random.normal(config["credit_mean"], config["credit_std"], n), 300, 850).astype(int)

    loan_amount = np.clip(income * np.random.uniform(0.4, 4.5, n), 5000, 750000).astype(int)
    loan_term = np.random.choice([12, 24, 36, 48, 60, 120, 180, 240, 360], n)
    existing_loans = np.random.poisson(1.4, n).clip(0, 8)
    debt_to_income = np.clip(np.random.beta(2, 5, n), 0.02, 0.90).round(3)
    account_balance = np.clip(income * np.random.uniform(0.1, 2.5, n), 250, 1500000).astype(int)

    transaction_count = np.clip(np.random.normal(28, 12, n), 2, 180).astype(int)
    transaction_amount = np.clip(np.random.lognormal(6.2, 1.1, n), 20, 45000).round(2)
    late_payments = np.random.poisson(0.5, n).clip(0, 12)
    default_history = (np.random.binomial(1, 0.08, n) * (late_payments > 0)).astype(int)

    loan_type = np.random.choice(LOAN_TYPES, n, p=[0.35, 0.25, 0.20, 0.12, 0.08])
    employment_type = np.random.choice(EMPLOYMENT_TYPES, n, p=[0.50, 0.20, 0.15, 0.10, 0.05])

    # Fraud & risk features
    amount_deviation = np.clip(np.random.exponential(0.6, n), 0, 10).round(3)
    velocity_score = np.clip(np.random.beta(2, 5, n) * 100, 0, 100).round(2)
    num_devices = np.random.poisson(2, n).clip(1, 6)
    account_age_months = np.clip(np.random.normal(55, 30, n), 1, 360).astype(int)
    merchant_category_diversity = np.random.randint(2, 25, n)

    # Compute target_default based on credit risk formulas
    risk_score_raw = (
        0.35 * (1.0 - credit_score / 850.0)
        + 0.25 * debt_to_income
        + 0.15 * (late_payments / 12.0)
        + 0.15 * default_history
        + 0.10 * (1.0 - np.minimum(income, 200000) / 200000.0)
        + np.random.normal(0, 0.04, n)
    )
    risk_score_raw = np.clip(risk_score_raw, 0, 1)
    threshold = np.quantile(risk_score_raw, 1.0 - config["default_rate"])
    target_default = (risk_score_raw >= threshold).astype(int)

    # Compute is_fraud
    fraud_score_raw = (
        0.35 * (amount_deviation / 10.0)
        + 0.30 * (velocity_score / 100.0)
        + 0.20 * (num_devices > 3).astype(float)
        + 0.15 * (transaction_amount > 10000).astype(float)
        + np.random.normal(0, 0.03, n)
    )
    fraud_threshold = np.quantile(fraud_score_raw, 1.0 - config["fraud_rate"])
    is_fraud = (fraud_score_raw >= fraud_threshold).astype(int)

    # Churn probability
    churn_probability = np.clip(
        0.35 * (1.0 - transaction_count / 180.0)
        + 0.25 * (1.0 - account_age_months / 360.0)
        + 0.20 * (1.0 - account_balance / (income + 1))
        + np.random.normal(0, 0.08, n),
        0.0,
        1.0,
    ).round(3)

    # Transaction risk score
    transaction_risk_score = np.clip(
        0.35 * (amount_deviation / 10.0)
        + 0.30 * (velocity_score / 100.0)
        + 0.20 * (1.0 - credit_score / 850.0)
        + 0.15 * (transaction_amount / 45000.0),
        0.0,
        1.0,
    ).round(3)

    customer_ids = [f"{config['code']}-{str(i).zfill(6)}" for i in range(1, n + 1)]

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "age": age,
        "income": income,
        "employment_years": employment_years,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "loan_term": loan_term,
        "existing_loans": existing_loans,
        "debt_to_income": debt_to_income,
        "account_balance": account_balance,
        "transaction_count": transaction_count,
        "transaction_amount": transaction_amount,
        "late_payments": late_payments,
        "default_history": default_history,
        "loan_type": loan_type,
        "employment_type": employment_type,
        "amount_deviation": amount_deviation,
        "velocity_score": velocity_score,
        "num_devices": num_devices,
        "account_age_months": account_age_months,
        "merchant_category_diversity": merchant_category_diversity,
        "target_default": target_default,
        "is_default": target_default,  # Alias for backward compatibility
        "is_fraud": is_fraud,
        "churn_probability": churn_probability,
        "transaction_risk_score": transaction_risk_score,
    })

    return df


def generate_all_datasets(output_dir: str) -> List[Dict[str, Any]]:
    """Generate datasets for all 4 banks and save as CSV."""
    os.makedirs(output_dir, exist_ok=True)
    results = []
    total_records = 0

    for config in BANK_CONFIGS:
        df = generate_bank_dataset(config)
        filename = f"{config['code'].lower()}_customers.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        total_records += len(df)
        results.append({
            "bank_code": config["code"],
            "bank_name": config["name"],
            "branch": config["branch"],
            "file_path": filepath,
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "default_rate": float(df["target_default"].mean()),
            "fraud_rate": float(df["is_fraud"].mean()),
        })
        print(f"[FedBank Synthesizer] Generated {len(df):,} records for {config['name']} ({config['code']}) -> {filepath}")

    print(f"[FedBank Synthesizer] Total synthetic customer records created: {total_records:,} across {len(BANK_CONFIGS)} banks.")
    return results


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "dataset_storage")
    generate_all_datasets(out_dir)
