"""End-to-End Smoke Test Suite for FedBank MLOps Platform."""

def test_full_platform_e2e_flow(client, auth_headers):
    # 1. Health check
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] in ("ok", "HEALTHY")

    # 2. Main Dashboard Metrics
    dash_res = client.get("/api/v1/dashboard/admin", headers=auth_headers)
    assert dash_res.status_code == 200
    data = dash_res.json()["data"]
    assert data["total_banks"] >= 4
    assert data["global_model_accuracy"] > 70.0
    assert "accuracy_by_fl_round" in data
    assert "confusion_matrix" in data
    assert "data_drift" in data

    # 3. MLOps Pipeline Status & Actions
    pipeline_res = client.get("/api/v1/pipeline/status", headers=auth_headers)
    assert pipeline_res.status_code == 200
    pdata = pipeline_res.json()["data"]
    assert len(pdata["stages"]) == 11

    # 4. Bank Listing
    banks_res = client.get("/api/v1/banks", headers=auth_headers)
    assert banks_res.status_code == 200
    assert len(banks_res.json()["data"]["items"]) >= 4

    # 5. Datasets Listing
    ds_res = client.get("/api/v1/datasets", headers=auth_headers)
    assert ds_res.status_code == 200
    assert len(ds_res.json()["data"]["items"]) >= 4

    # 6. Registered Models
    models_res = client.get("/api/v1/models", headers=auth_headers)
    assert models_res.status_code == 200
    assert len(models_res.json()["data"]["items"]) >= 1

    # 7. Fraud Summary & Scoring
    fraud_sum = client.get("/api/v1/fraud/summary", headers=auth_headers)
    assert fraud_sum.status_code == 200

    # 8. Audit Logs
    audit_res = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert audit_res.status_code == 200
    assert audit_res.json()["data"]["total"] > 0

    # 9. Settings
    settings_res = client.get("/api/v1/settings", headers=auth_headers)
    assert settings_res.status_code == 200
    assert len(settings_res.json()["data"]) >= 5
