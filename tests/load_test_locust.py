"""Locust Load & Stress Testing Script for FedBank MLOps Platform."""

from __future__ import annotations

import random
import uuid
from locust import HttpUser, between, task


class FedBankUser(HttpUser):
    wait_time = between(0.1, 0.5)
    token = None

    def on_start(self):
        """Authenticate user on test worker start."""
        res = self.client.post("/api/v1/auth/login", json={
            "email": "admin@fedbank.com",
            "password": "Admin@123",
        })
        if res.status_code == 200:
            self.token = res.json().get("access_token")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def check_health(self):
        self.client.get("/health")

    @task(4)
    def list_countries_and_currencies(self):
        self.client.get("/api/v1/countries", headers=self._headers())
        self.client.get("/api/v1/currencies", headers=self._headers())

    @task(3)
    def list_accounts_and_rails(self):
        self.client.get("/api/v1/accounts", headers=self._headers())
        self.client.get("/api/v1/payment-rails", headers=self._headers())

    @task(3)
    def score_realtime_fraud(self):
        self.client.post("/api/v1/fraud/score", json={
            "customer_id": f"CUST-IN-00{random.randint(1, 4)}",
            "amount": float(random.randint(500, 75000)),
            "transaction_type": "TRANSFER",
            "merchant_category": "General Retail",
            "velocity_score": float(random.randint(10, 95)),
            "amount_deviation": float(random.uniform(0.5, 6.0)),
            "num_devices": random.randint(1, 3),
            "account_age_months": random.randint(6, 60),
        }, headers=self._headers())

    @task(2)
    def credit_prediction(self):
        self.client.post("/api/v1/predictions/single", json={
            "income": float(random.randint(300000, 2500000)),
            "debt_to_income": float(random.uniform(0.1, 0.6)),
            "credit_score": random.randint(550, 850),
            "loan_amount": float(random.randint(50000, 1000000)),
            "loan_purpose": "PERSONAL",
            "employment_years": random.randint(1, 20),
            "previous_defaults": random.randint(0, 2),
            "savings_balance": float(random.randint(10000, 500000)),
            "bank_id": "BANK-001",
        }, headers=self._headers())

    @task(1)
    def data_drift_telemetry(self):
        self.client.get("/api/v1/data-drift/psi", headers=self._headers())
        self.client.get("/api/v1/jobs", headers=self._headers())
