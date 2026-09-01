"""Tests for Statistical Data Drift (PSI/KS) and Background Async Jobs."""

from __future__ import annotations

import time
import pytest
import numpy as np
from app.services.drift_service import StatisticalDriftService


def test_psi_and_ks_calculation():
    # Generate identical distributions -> PSI ~ 0.0
    rng = np.random.RandomState(42)
    base = rng.normal(loc=100.0, scale=15.0, size=1000)
    same_curr = rng.normal(loc=100.0, scale=15.0, size=1000)

    psi_same = StatisticalDriftService.calculate_psi(base, same_curr)
    assert psi_same < 0.10  # NO_DRIFT

    # Generate heavily shifted distribution -> PSI > 0.25
    shifted_curr = rng.normal(loc=140.0, scale=30.0, size=1000)
    psi_shifted = StatisticalDriftService.calculate_psi(base, shifted_curr)
    assert psi_shifted >= 0.25  # DRIFT

    # Test KS statistic
    stat, pval = StatisticalDriftService.calculate_ks_test(base, shifted_curr)
    assert stat > 0.3
    assert pval < 0.01


def test_data_drift_api_endpoint(client, auth_headers):
    # Trigger dataset drift calculation across bank-001 and bank-002
    res = client.post("/api/v1/data-drift/calculate", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["features_analyzed"] > 0
    assert "reports" in data

    # Verify PSI list
    list_res = client.get("/api/v1/data-drift/psi", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) > 0


def test_async_background_job_execution(client, auth_headers):
    # Trigger sample background task
    trig_res = client.post("/api/v1/jobs/trigger-sample-task?title=Test%20Async%20Worker", headers=auth_headers)
    assert trig_res.status_code == 200
    job_id = trig_res.json()["data"]["job_id"]
    assert bool(job_id)

    # Poll status until completed (timeout 5s)
    completed = False
    for _ in range(20):
        time.sleep(0.2)
        j_res = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
        assert j_res.status_code == 200
        job_data = j_res.json()["data"]
        if job_data["status"] == "COMPLETED":
            assert job_data["progress_percent"] == 100.0
            completed = True
            break

    assert completed is True
