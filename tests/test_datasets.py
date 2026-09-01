"""Data Management API Test Suite."""

def test_list_datasets(client, auth_headers):
    res = client.get("/api/v1/datasets", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 4
    for ds in data["items"]:
        assert ds["use_case"] == "credit_risk"
        assert ds["status"] in ("VALIDATED", "ACTIVE", "UPLOADED")


def test_dataset_detail_and_quality(client, auth_headers):
    list_res = client.get("/api/v1/datasets", headers=auth_headers)
    first_id = list_res.json()["data"]["items"][0]["id"]

    res = client.get(f"/api/v1/datasets/{first_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == first_id
    assert "versions" in data
    if len(data["versions"]) > 0:
        ver = data["versions"][0]
        assert ver["rows"] > 0
        assert ver["quality_score"] is not None
